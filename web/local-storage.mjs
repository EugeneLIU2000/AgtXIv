/** Local development adapter for the same prepared-statement and object-store operations. */
import { DatabaseSync } from 'node:sqlite';
import { readFile,writeFile,mkdir,readdir } from 'node:fs/promises';
import path from 'node:path';
export async function localStorage(data,migrations) {
  await mkdir(data,{recursive:true});await mkdir(path.join(data,'objects'),{recursive:true});
  const sqlite=new DatabaseSync(path.join(data,'jobs.sqlite'));sqlite.exec('PRAGMA journal_mode=WAL');
  sqlite.exec('CREATE TABLE IF NOT EXISTS local_migrations (name TEXT PRIMARY KEY)');
  for(const name of (await readdir(migrations)).filter(x=>x.endsWith('.sql')).sort()) {
    if(!sqlite.prepare('SELECT name FROM local_migrations WHERE name=?').get(name)) {
      sqlite.exec('BEGIN');try{sqlite.exec(await readFile(path.join(migrations,name),'utf8'));sqlite.prepare('INSERT INTO local_migrations (name) VALUES (?)').run(name);sqlite.exec('COMMIT')}catch(e){sqlite.exec('ROLLBACK');throw e}
    }
  }
  const DB={prepare(sql){let args=[];return {bind(...a){args=a;return this},async run(){const r=sqlite.prepare(sql).run(...args);return {success:true,meta:{changes:Number(r.changes)}}},async first(){return sqlite.prepare(sql).get(...args)||null},async all(){return {results:sqlite.prepare(sql).all(...args)}}}}};
  const objectPath=key=>{if(!/^(sources|results)\/[a-f0-9]{64}(\.json)?$/.test(key))throw Error('Invalid object key');return path.join(data,'objects',key.replace('/','-'))};
  const ARTIFACTS={async put(key,value){await writeFile(objectPath(key),new Uint8Array(value))},async get(key){try{const bytes=await readFile(objectPath(key));return {async arrayBuffer(){return bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)}}}catch(e){if(e.code==='ENOENT')return null;throw e}}};
  return {env:{DB,ARTIFACTS},close:()=>sqlite.close()};
}
