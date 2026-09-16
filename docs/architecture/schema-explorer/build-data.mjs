import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../..');
const directory=path.join(root,'schema v0.0');
const schemas={};
for(const file of fs.readdirSync(directory).filter(f=>f.endsWith('.schema.json'))){
 const raw=fs.readFileSync(path.join(directory,file),'utf8');
 schemas[file.replace('.schema.json','')]={document:JSON.parse(raw),sha256:crypto.createHash('sha256').update(raw).digest('hex'),path:path.join(directory,file)};
}
const evidence={};
for(const file of ['src/agtxiv_v3/intake.py','src/agtxiv_v3/candidates.py','src/agtxiv_v3/vibefeld.py','src/agtxiv_v3/contracts.py','src/agtxiv_v3/dependencies.py','src/agtxiv_v3/storage.py','docs/roadmaps/v3-execution-status.md','database/README.md']){
 const raw=fs.readFileSync(path.join(root,file),'utf8');evidence[file]={path:path.join(root,file),text:raw,sha256:crypto.createHash('sha256').update(raw).digest('hex')};
}
fs.writeFileSync(path.join(here,'schema-data.js'),'window.ARCHITECTURE_DATA = '+JSON.stringify({schemas,evidence,reviewDate:'2026-09-11'})+';\n');
console.log(`Packed ${Object.keys(schemas).length} schema documents and ${Object.keys(evidence).length} evidence files.`);
