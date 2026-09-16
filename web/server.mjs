/** Versioned web API. Candidate analysis is independent of V3 scientific approval. */
const API = '1.0';
export const RETRIEVAL_TIMEOUT_MS = 20000;
const STAGES = ['QUEUED', 'FETCHING', 'ANALYZING', 'COMPLETED'];
const MIME = {html:'text/html; charset=utf-8',css:'text/css; charset=utf-8',js:'text/javascript; charset=utf-8',json:'application/json; charset=utf-8',svg:'image/svg+xml',zip:'application/zip',pdf:'application/pdf',md:'text/markdown; charset=utf-8',txt:'text/plain; charset=utf-8',tex:'text/plain; charset=utf-8'};
const terminal = s => ['COMPLETED','FAILED'].includes(s);
const iso = () => new Date().toISOString();
export const digest = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
const json = (body,status=200,headers={}) => new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff',...headers}});
class ApiError extends Error {constructor(code,message,status=400){super(message);this.code=code;this.status=status}}
const error = (code,message,status=400,requestId) => json({api_version:API,error:{code,message,request_id:requestId}},status);

async function bodyJSON(request) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new ApiError('CONTENT_TYPE','Send application/json.',415);
  const reader=request.body?.getReader();let size=0;const chunks=[];
  if(!reader) throw new ApiError('INVALID_BODY','A JSON body is required.');
  try {while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>2048){await reader.cancel();throw new ApiError('BODY_TOO_LARGE','Request exceeds 2 KiB.',413)}chunks.push(value)}}finally{reader.releaseLock()}
  const all=new Uint8Array(size);let pos=0;for(const c of chunks){all.set(c,pos);pos+=c.length}
  let value;try{value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(all))}catch{throw new ApiError('INVALID_JSON','Request is not valid UTF-8 JSON.')}
  if(!value||Array.isArray(value)||typeof value!=='object')throw new ApiError('INVALID_BODY','Expected a JSON object.');
  return value;
}

function jobView(row) {
  const stale=!terminal(row.status)&&Date.now()-Date.parse(row.updated_at)>120000;
  return {api_version:API,id:row.id,arxiv:row.arxiv,status:stale?'INTERRUPTED':row.status,
    stages:STAGES,created_at:row.created_at,updated_at:row.updated_at,revision:row.revision,
    result_url:row.status==='COMPLETED'?`/api/v1/jobs/${row.id}/result`:null,
    analysis_id:row.analysis_id||null,parent_id:row.parent_id||null,
    error:stale?{code:'WORKER_INTERRUPTED',message:'No progress has been recorded for two minutes. The earlier worker may still finish; retry starts a separate retained attempt.'}:row.error_code?{code:row.error_code,message:row.error_message}:null,
    scientific_assessment:'NOT_PERFORMED'};
}

export function createHandler({readAsset,engine,fetchImpl}) {
  async function runJob(id,env) {
    const db=env.DB;
    const lock=await db.prepare("UPDATE analysis_jobs SET status='FETCHING', updated_at=?, revision=revision+1 WHERE id=? AND status='QUEUED'").bind(iso(),id).run();
    if(!lock.meta?.changes)return;
    const row=await db.prepare('SELECT * FROM analysis_jobs WHERE id=?').bind(id).first();
    try {
      const fetched=await engine.fetchArxivSource(row.arxiv,{fetchImpl,limits:{timeoutMs:RETRIEVAL_TIMEOUT_MS}});
      const sourceHash=await digest(fetched.bytes);
      const sourceKey=`sources/${sourceHash}`;
      await env.ARTIFACTS.put(sourceKey,fetched.bytes,{httpMetadata:{contentType:fetched.contentType||'application/octet-stream'}});
      await db.prepare("UPDATE analysis_jobs SET status='ANALYZING',source_key=?,updated_at=?,revision=revision+1 WHERE id=? AND status='FETCHING'").bind(sourceKey,iso(),id).run();
      const result=await engine.analyzeSource(fetched.bytes,{arxiv:fetched.arxiv,metadata:fetched.metadata,sourceUrl:fetched.url,fetchedAt:fetched.fetchedAt,limits:{timeoutMs:RETRIEVAL_TIMEOUT_MS}});
      result.provenance={...result.provenance,sourceStored:true,sourceStorage:'PRIVATE_CONTENT_ADDRESSED_OBJECT_STORE'};
      if (result.frontier?.limitations) result.frontier.limitations=result.frontier.limitations.map(note=>note.includes('does not retain the archive')?'Original archive bytes are retained privately with a content hash; the public result contains bounded excerpts and exact byte ranges.':note);
      const encoded=new TextEncoder().encode(JSON.stringify({...result,transport:{requested_arxiv:row.arxiv,retrieved_url:fetched.url,retrieved_at:fetched.fetchedAt,archive_sha256:`sha256:${sourceHash}`},scientific_assessment:'NOT_PERFORMED'}));
      const resultHash=await digest(encoded),resultKey=`results/${resultHash}.json`;
      await env.ARTIFACTS.put(resultKey,encoded,{httpMetadata:{contentType:'application/json'}});
      await db.prepare("UPDATE analysis_jobs SET status='COMPLETED',result_key=?,analysis_id=?,updated_at=?,revision=revision+1 WHERE id=? AND status='ANALYZING'").bind(resultKey,result.analysisId||resultHash,iso(),id).run();
    } catch(e) {
      const safeCode=typeof e.code==='string'?e.code:'ANALYSIS_FAILED';
      const safeMessage=typeof e.code==='string'?e.message:'Source processing failed. The attempt was retained; retry or inspect the source format.';
      await db.prepare("UPDATE analysis_jobs SET status='FAILED',error_code=?,error_message=?,updated_at=?,revision=revision+1 WHERE id=? AND status IN ('FETCHING','ANALYZING')").bind(safeCode,safeMessage.slice(0,1000),iso(),id).run();
    }
  }

  async function submit(arxiv,env,ctx,parentId=null) {
    const parsed=engine.parseArxivId(arxiv);
    const now=Date.now(),cutoff=new Date(now-120000).toISOString();
    const active=await env.DB.prepare("SELECT COUNT(*) AS count FROM analysis_jobs WHERE status IN ('QUEUED','FETCHING','ANALYZING') AND updated_at>?").bind(cutoff).first();
    if(active.count>=3)throw new ApiError('CAPACITY','Three analyses are running. Please try again shortly.',429);
    await env.DB.prepare("INSERT OR IGNORE INTO intake_clock (id,last_started) VALUES ('arxiv',0)").run();
    const acquired=await env.DB.prepare("UPDATE intake_clock SET last_started=? WHERE id='arxiv' AND last_started<=?").bind(now,now-3500).run();
    if(!acquired.meta?.changes)throw new ApiError('RATE_LIMIT','Please wait at least four seconds before submitting another paper.',429);
    const id=crypto.randomUUID(),at=iso();
    const admitted=await env.DB.prepare("INSERT INTO analysis_jobs (id,arxiv,status,created_at,updated_at,parent_id,revision) SELECT ?,?,'QUEUED',?,?,?,0 WHERE (SELECT COUNT(*) FROM analysis_jobs WHERE status IN ('QUEUED','FETCHING','ANALYZING') AND updated_at>?)<3").bind(id,parsed.canonical,at,at,parentId,cutoff).run();
    if(!admitted.meta?.changes)throw new ApiError('CAPACITY','Three analyses are running. Please try again shortly.',429);
    ctx.waitUntil(runJob(id,env));
    return json(jobView({id,arxiv:parsed.canonical,status:'QUEUED',created_at:at,updated_at:at,revision:0,parent_id:parentId}),202,{location:`/api/v1/jobs/${id}`});
  }

  return async function handle(request,env,ctx) {
    const requestId=crypto.randomUUID();
    try {
      const url=new URL(request.url),path=url.pathname;
      if(request.method==='OPTIONS')return new Response(null,{status:204,headers:{allow:'GET, HEAD, POST, OPTIONS'}});
      if(request.method==='POST') {
        const origin=request.headers.get('origin');
        if(origin&&origin!==url.origin)throw new ApiError('CROSS_ORIGIN','Submit from this site or a same-origin client.',403);
        if(!env.DB||!env.ARTIFACTS)throw new ApiError('SERVICE_UNAVAILABLE','Paper analysis storage is not configured.',503);
        if(path==='/api/v1/jobs') {
          const body=await bodyJSON(request);
          if(Object.keys(body).some(k=>k!=='arxiv')||typeof body.arxiv!=='string')throw new ApiError('INVALID_BODY','Provide exactly one arxiv string.');
          return await submit(body.arxiv,env,ctx);
        }
        const retry=path.match(/^\/api\/v1\/jobs\/([a-f0-9-]{36})\/retry$/);
        if(retry) {
          const body=await bodyJSON(request);if(Object.keys(body).length)throw new ApiError('INVALID_BODY','Retry body must be an empty object.');
          const row=await env.DB.prepare('SELECT * FROM analysis_jobs WHERE id=?').bind(retry[1]).first();
          if(!row)throw new ApiError('NOT_FOUND','Analysis job not found.',404);
          if(!['FAILED','INTERRUPTED'].includes(jobView(row).status))throw new ApiError('NOT_RETRYABLE','Only failed or interrupted analyses can be retried.',409);
          return await submit(row.arxiv,env,ctx,row.id);
        }
        throw new ApiError('NOT_FOUND','Endpoint not found.',404);
      }
      if(!['GET','HEAD'].includes(request.method))throw new ApiError('METHOD_NOT_ALLOWED','Use GET, HEAD or the documented POST endpoints.',405);
      if(path==='/api/v1/health')return json({api_version:API,status:env.DB&&env.ARTIFACTS?'READY':'READ_ONLY',analysis_method:'BOUNDED_SOURCE_CANDIDATE_EXTRACTION',scientific_assessment:'NOT_PERFORMED'});
      const job=path.match(/^\/api\/v1\/jobs\/([a-f0-9-]{36})(\/result)?$/);
      if(job) {
        if(!env.DB||!env.ARTIFACTS)throw new ApiError('SERVICE_UNAVAILABLE','Paper analysis storage is not configured.',503);
        const row=await env.DB.prepare('SELECT * FROM analysis_jobs WHERE id=?').bind(job[1]).first();
        if(!row)throw new ApiError('NOT_FOUND','Analysis job not found.',404);
        if(!job[2])return json(jobView(row));
        if(row.status!=='COMPLETED')throw new ApiError('RESULT_NOT_READY','This analysis has no completed result.',409);
        const blob=await env.ARTIFACTS.get(row.result_key);
        if(!blob)throw new ApiError('ARTIFACT_MISSING','The retained result is unavailable.',503);
        const bytes=new Uint8Array(await blob.arrayBuffer());
        if(row.result_key!==`results/${await digest(bytes)}.json`)throw new ApiError('ARTIFACT_INTEGRITY','The retained result does not match its content identity.',503);
        return new Response(bytes,{headers:{'content-type':'application/json; charset=utf-8','cache-control':'private, max-age=0','etag':`"${row.result_key.slice(8,-5)}"`}});
      }
      if(path==='/api/v1/library'||path==='/api/v1/schemas'||path.startsWith('/api/v1/papers/')) {
        const asset=await readAsset('/data/library.json');const library=JSON.parse(new TextDecoder().decode(asset.bytes));
        if(path==='/api/v1/schemas')return json({api_version:API,schema_bundle_hash:library.schema_bundle_hash,records:library.schemas});
        if(path.startsWith('/api/v1/papers/')) {
          const slug=path.slice('/api/v1/papers/'.length);const paper=library.papers.find(p=>p.slug===slug);
          if(!paper)throw new ApiError('NOT_FOUND','Paper is not in the curated library. Submit its arXiv identifier to analyze it.',404);
          return json({api_version:API,paper});
        }
        const q=(url.searchParams.get('q')||'').toLowerCase();if(q.length>200)throw new ApiError('QUERY_TOO_LONG','Search is limited to 200 characters.');
        return json({...library,papers:library.papers.filter(p=>!q||`${p.title} ${p.arxiv} ${p.claims.map(c=>c.interpretation).join(' ')}`.toLowerCase().includes(q))});
      }
      const assetPath=path==='/'?'/index.html':path;
      const asset=await readAsset(assetPath);
      if(!asset)throw new ApiError('NOT_FOUND','Page or resource not found.',404);
      return new Response(request.method==='HEAD'?null:asset.bytes,{headers:{'content-type':asset.type||MIME[assetPath.split('.').at(-1)]||'application/octet-stream','x-content-type-options':'nosniff','referrer-policy':'strict-origin-when-cross-origin','cache-control':assetPath.endsWith('.html')?'no-cache':'public, max-age=300','content-security-policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"}});
    } catch(e) {
      return error(e.code||'INTERNAL_ERROR',e instanceof ApiError||e.code?e.message:'The service could not complete the request.',e.status||(e.code?400:500),requestId);
    }
  }
}
