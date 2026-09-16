import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHandler} from '../server.mjs';
import {localStorage} from '../local-storage.mjs';
import * as engine from '../engine/intake.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const tex=String.raw`\documentclass{article}
\title{An explicit synthetic source for API tests}
\begin{document}
\begin{theorem}\label{t}Every positive square is nonnegative.\end{theorem}
\begin{equation}\label{eq}x^2\geq0\end{equation}
We show that Eq.~\ref{eq} supports the statement.
\end{document}`;
async function fixture(t,{fetchImpl}={}){
 const dir=await mkdtemp(path.join(tmpdir(),'agtxiv-api-'));let store=await localStorage(dir,path.join(root,'drizzle'));
 const pending=[];const ctx={waitUntil(p){pending.push(p)}};
 const handler=createHandler({engine,fetchImpl:fetchImpl||(async()=>new Response(tex,{headers:{'content-type':'text/plain'}})),readAsset:async name=>{try{return {bytes:await readFile(path.join(root,'public',name))}}catch{return null}}});
 const request=(route,body,headers={})=>handler(new Request('https://example.test'+route,body===undefined?{}:{method:'POST',headers:{'content-type':'application/json',...headers},body:typeof body==='string'?body:JSON.stringify(body)}),store.env,ctx);
 t.after(async()=>{await Promise.allSettled(pending);store.close();await rm(dir,{recursive:true,force:true})});
 return {request,env:store.env,pending,dir,reopen:async()=>{await Promise.all(pending);store.close();store=await localStorage(dir,path.join(root,'drizzle'))},finish:()=>Promise.all(pending)};
}
test('a new submission executes the real extractor and remains readable after storage reopen',async t=>{
 const f=await fixture(t);const submitted=await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'});assert.equal(submitted.status,202);const job=await submitted.json();assert.equal(job.status,'QUEUED');await f.finish();
 const finished=await (await f.request('/api/v1/jobs/'+job.id)).json();assert.equal(finished.status,'COMPLETED');assert.equal(finished.revision,3);const first=await (await f.request(finished.result_url)).text();const result=JSON.parse(first);assert.ok(result.candidates.length>=2);assert.equal(result.provenance.sourceStored,true);assert.equal(result.scientific_assessment,'NOT_PERFORMED');assert.ok(result.candidates.every(c=>Object.values(c.assessments).every(x=>x==='NO_ASSESSMENT')));
 await f.reopen();const second=await (await f.request(finished.result_url)).text();assert.equal(second,first);assert.equal((await (await f.request('/api/v1/jobs/'+job.id)).json()).revision,3);
});
test('failed source retrieval is retained; retry creates a distinct linked attempt',async t=>{
 const f=await fixture(t,{fetchImpl:async()=>new Response('missing',{status:404})});const j=await (await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'})).json();await f.finish();
 const failed=await (await f.request('/api/v1/jobs/'+j.id)).json();assert.equal(failed.status,'FAILED');assert.equal(failed.error.code,'UPSTREAM_ERROR');assert.equal((await f.request(`/api/v1/jobs/${j.id}/result`)).status,409);
 await f.env.DB.prepare("UPDATE intake_clock SET last_started=0 WHERE id='arxiv'").run();const retry=await f.request(`/api/v1/jobs/${j.id}/retry`,{});assert.equal(retry.status,202);const next=await retry.json();assert.notEqual(next.id,j.id);assert.equal(next.parent_id,j.id);await f.finish();assert.equal((await (await f.request('/api/v1/jobs/'+j.id)).json()).revision,2);
});
test('invalid, oversized, foreign-origin and unsupported requests do not start work',async t=>{
 const f=await fixture(t);for(const [body,expected] of [[{arxiv:'https://evil.test/src/2405.08863v1'},400],[{arxiv:'2405.08863v1',accept:true},400],['{broken',400],[{arxiv:'x'.repeat(2100)},413]])assert.equal((await f.request('/api/v1/jobs',body)).status,expected);
 assert.equal((await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'},{origin:'https://evil.test'})).status,403);
 assert.equal((await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'},{'content-type':'text/plain'})).status,415);assert.equal(f.pending.length,0);
});
test('rate and capacity limits reject work before scheduling it',async t=>{
 const f=await fixture(t);const first=await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'});assert.equal(first.status,202);assert.equal((await f.request('/api/v1/jobs',{arxiv:'1706.03762v7'})).status,429);await f.finish();
 for(let i=0;i<3;i++)await f.env.DB.prepare("INSERT INTO analysis_jobs(id,arxiv,status,created_at,updated_at,revision) VALUES (?,?,'FETCHING',?,?,0)").bind(crypto.randomUUID(),'2405.08863v1',new Date().toISOString(),new Date().toISOString()).run();
 await f.env.DB.prepare("UPDATE intake_clock SET last_started=0 WHERE id='arxiv'").run();const cap=await f.request('/api/v1/jobs',{arxiv:'1706.03762v7'});assert.equal(cap.status,429);assert.equal((await cap.json()).error.code,'CAPACITY');assert.equal(f.pending.length,1);
});
test('interrupted is a read-only stale view; missing and corrupt results fail closed',async t=>{
 const f=await fixture(t);const id=crypto.randomUUID(),old='2000-01-01T00:00:00.000Z';await f.env.DB.prepare("INSERT INTO analysis_jobs(id,arxiv,status,created_at,updated_at,revision) VALUES (?,?,'FETCHING',?,?,1)").bind(id,'2405.08863v1',old,old).run();
 assert.equal((await (await f.request('/api/v1/jobs/'+id)).json()).status,'INTERRUPTED');assert.equal((await f.env.DB.prepare('SELECT status FROM analysis_jobs WHERE id=?').bind(id).first()).status,'FETCHING');
 const j=await (await f.request('/api/v1/jobs',{arxiv:'2405.08863v1'})).json();await f.finish();const row=await f.env.DB.prepare('SELECT * FROM analysis_jobs WHERE id=?').bind(j.id).first();await f.env.ARTIFACTS.put(row.result_key,new TextEncoder().encode('{}'));const corrupt=await f.request(`/api/v1/jobs/${j.id}/result`);assert.equal(corrupt.status,503);assert.equal((await corrupt.json()).error.code,'ARTIFACT_INTEGRITY');assert.equal((await f.request('/api/v1/jobs/'+crypto.randomUUID())).status,404);
});
test('library filtering and selected paper preserve the original record identities',async t=>{
 const f=await fixture(t);const all=await (await f.request('/api/v1/library')).json();const one=await (await f.request('/api/v1/library?q=1609.07488')).json();assert.equal(one.papers.length,1);assert.equal(all.schemas.length,64);assert.equal(one.papers[0].claims.length,6);assert.equal(one.scientific_acceptance,false);const r3=one.papers[0].claims.find(c=>c.id==='R3');assert.deepEqual(r3.dependencies,['definition','contraction']);assert.deepEqual(one.papers[0].claims.find(c=>c.id==='postselection').dependencies,[]);assert.equal((await f.request('/api/v1/papers/missing')).status,404);
});

test('the root document is served as HTML with executable same-origin assets',async t=>{
 const f=await fixture(t);const page=await f.request('/');assert.equal(page.status,200);assert.equal(page.headers.get('content-type'),'text/html; charset=utf-8');assert.equal(page.headers.get('cache-control'),'no-cache');assert.match(await page.text(),/id="intake-form"/);
 for(const [url,type] of [['/app.js','text/javascript'],['/styles.css','text/css'],['/api/v1/openapi.json','application/json']]){const r=await f.request(url);assert.equal(r.status,200);assert.ok(r.headers.get('content-type').startsWith(type));}
});
