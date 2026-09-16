import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHandler } from './server.mjs';
import { localStorage } from './local-storage.mjs';

const root=path.dirname(fileURLToPath(import.meta.url));
const data=process.env.AGTXIV_WEB_DATA||path.join(root,'.local');
const storage=await localStorage(data,path.join(root,'drizzle'));const {env}=storage;
let engine;
try{engine=await import('./engine/intake.mjs')}catch{engine=await import('../src/agtxiv_web/intake.mjs')}
async function readAsset(name){if(!/^\/[A-Za-z0-9_./-]+$/.test(name)||name.split('/').includes('..'))return null;try{return {bytes:await readFile(path.join(root,'public',name))}}catch(e){if(e.code==='ENOENT'||e.code==='EISDIR')return null;throw e}}
const handler=createHandler({readAsset,engine});const running=new Set();
const ctx={waitUntil(promise){running.add(promise);promise.finally(()=>running.delete(promise)).catch(e=>process.stderr.write(`Worker: ${e.message}\n`))}};
const port=Number(process.env.AGTXIV_WEB_PORT||8787);
const server=http.createServer(async(req,res)=>{
  try{const request=new Request(`http://127.0.0.1:${port}${req.url}`,{method:req.method,headers:req.headers,...(!['GET','HEAD'].includes(req.method)?{body:req,duplex:'half'}:{})});const response=await handler(request,env,ctx);res.writeHead(response.status,Object.fromEntries(response.headers));res.end(new Uint8Array(await response.arrayBuffer()))}catch(e){res.writeHead(500);res.end('Local server error')}
});
server.listen(port,'127.0.0.1',()=>process.stdout.write(`AgtXIv Local: http://127.0.0.1:${port}\n`));
process.on('SIGTERM',()=>{server.close();Promise.allSettled(running).finally(()=>{storage.close();process.exit(0)})});
