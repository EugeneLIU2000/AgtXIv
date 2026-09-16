import { readFile, writeFile, mkdir, readdir, cp, rm, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openapi,jobSchema } from './api-spec.mjs';
import { RETRIEVAL_TIMEOUT_MS } from './server.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const exists=async p=>stat(p).then(()=>true,()=>false);
await mkdir(path.join(root,'engine'),{recursive:true});
const upstream=path.resolve(root,'../src/agtxiv_web/intake.mjs');
if(await exists(upstream))await cp(upstream,path.join(root,'engine/intake.mjs'));
if(!await exists(path.join(root,'engine/intake.mjs')))throw Error('Missing source-analysis engine.');
const api=path.join(root,'public/api/v1');await mkdir(api,{recursive:true});
const {DEFAULT_LIMITS}=await import('./engine/intake.mjs');
const publishedOpenAPI={...openapi,'x-agtxiv-processing-limits':{...DEFAULT_LIMITS,timeoutMs:RETRIEVAL_TIMEOUT_MS}};
await writeFile(path.join(api,'openapi.json'),JSON.stringify(publishedOpenAPI,null,2)+'\n');
await writeFile(path.join(api,'job.schema.json'),JSON.stringify(jobSchema,null,2)+'\n');
const analysisSchema=path.resolve(root,'../src/agtxiv_web/analysis.schema.json');
if(await exists(analysisSchema))await cp(analysisSchema,path.join(api,'analysis.schema.json'));
if(!await exists(path.join(api,'analysis.schema.json')))throw Error('Missing analysis response schema.');
const output=path.join(root,'dist');await rm(output,{recursive:true,force:true});await mkdir(path.join(output,'server'),{recursive:true});
const assets={};
async function collect(folder,prefix=''){
 for(const entry of await readdir(folder,{withFileTypes:true})){
  if(entry.isSymbolicLink())throw Error('Public assets cannot contain symlinks.');
  const filename=path.join(folder,entry.name),name=prefix+'/'+entry.name;
  if(entry.isDirectory())await collect(filename,name);else{const bytes=await readFile(filename);assets[name]=bytes.toString('base64');}
 }
}
await collect(path.join(root,'public'));
for(const required of ['/index.html','/app.js','/styles.css','/assets/logo.svg','/data/library.json','/data/robustness-records.json','/api/v1/openapi.json','/api/v1/job.schema.json','/api/v1/analysis.schema.json','/docs/technical-report.pdf','/docs/technical-report.tex','/docs/technical-report-source.zip']) {
 if(!Object.hasOwn(assets,required))throw Error('Required publication resource missing: '+required);
}
await writeFile(path.join(output,'server/assets.mjs'),'export default '+JSON.stringify(assets)+';\n');
await cp(path.join(root,'server.mjs'),path.join(output,'server/server.mjs'));
await cp(path.join(root,'engine/intake.mjs'),path.join(output,'server/intake.mjs'));
await writeFile(path.join(output,'server/index.js'),`import assets from './assets.mjs';\nimport * as engine from './intake.mjs';\nimport {createHandler} from './server.mjs';\nconst readAsset=async path=>{const value=assets[path];if(value===undefined)return null;return {bytes:Uint8Array.from(atob(value),c=>c.charCodeAt(0))}};\nexport default {fetch:createHandler({readAsset,engine})};\n`);
await mkdir(path.join(output,'.openai'),{recursive:true});await cp(path.join(root,'.openai/hosting.json'),path.join(output,'.openai/hosting.json'));
await cp(path.join(root,'drizzle'),path.join(output,'.openai/drizzle'),{recursive:true});
await cp(path.join(root,'public'),path.join(output,'client'),{recursive:true});
process.stdout.write(`Built ${Object.keys(assets).length} public resources and a Cloudflare Worker.\n`);
