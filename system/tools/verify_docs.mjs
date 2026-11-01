// Read-only local documentation/asset checks; does not contact referenced websites.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
function files(folder){return fs.readdirSync(folder,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(folder,e.name)):[path.join(folder,e.name)]);}
const documents=[path.join(root,'README.md'),...files(path.join(root,'docs')).filter(f=>f.endsWith('.md')),...fs.readdirSync(path.join(root,'qa')).filter(f=>f.endsWith('.md')).map(f=>path.join(root,'qa',f))];
let links=0;
const missing=[];
for(const file of documents){const source=fs.readFileSync(file,'utf8');for(const match of source.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)){let target=match[1].trim().split(/\s+"/)[0].replace(/^<|>$/g,'');if(/^(?:[a-z][a-z\d+.-]*:|#|\/)/i.test(target))continue;target=decodeURIComponent(target.split('#')[0]);if(!target)continue;links++;if(!fs.existsSync(path.resolve(path.dirname(file),target)))missing.push({document:path.relative(root,file),target});}}
assert.deepEqual(missing,[],'Local document links are broken: '+JSON.stringify(missing));
const sha=createHash('sha256').update(fs.readFileSync(path.join(root,'target/adc-nexus.jar'))).digest('hex');
const expected={'acceptance-results.json':178,'acceptance-postgres.json':176,'auth-acceptance-sqlite.json':51,'auth-acceptance-postgres.json':49,'homepage-contract-tests.json':36,'clinic-ui-tests.json':20,'practice-ui-tests.json':33,'ui-refinement-tests.json':33,'setup-ui-tests.json':21};
for(const [name,count]of Object.entries(expected)){const proof=JSON.parse(fs.readFileSync(path.join(root,'qa',name)));assert(proof.passed===true||proof.passed===count);assert.equal(proof.tests||proof.checks,count);assert.equal(proof.artifact?.sha256||proof.jar_sha256,sha,'Wrong JAR proof: '+name);}
const requestProof=JSON.parse(fs.readFileSync(path.join(root,'qa/web-request-tests.json')));assert.equal(requestProof.tests,10);assert(requestProof.passed);assert.equal(requestProof.source_sha256,createHash('sha256').update(fs.readFileSync(path.join(root,'src/main/resources/web/app.js'))).digest('hex'));
const browser=JSON.parse(fs.readFileSync(path.join(root,'qa/browser-review-v1-5.json')));assert.equal(browser.jar_sha256,sha);assert.equal(browser.roles.length,8);assert(browser.roles.every(x=>x.passed));assert(browser.interactions.every(x=>x.passed));
const preserved=JSON.parse(fs.readFileSync(path.join(root,'qa/local-preservation-v1-5.json')));assert(preserved.passed);assert.equal(preserved.jar_sha256,sha);assert.equal(preserved.tables,71);assert.equal(preserved.foreign_keys,146);
assert(fs.readFileSync(path.join(root,'docs/RELEASE_READINESS.md'),'utf8').includes(sha));
for(const file of ['home-care-v1.png','home-clinic-v1.png','home-reception-v1.png']){const image=fs.readFileSync(path.join(root,'src/main/resources/web/images',file));assert.equal(image.subarray(1,4).toString(),'PNG');assert.equal(image.readUInt32BE(16),1672);assert.equal(image.readUInt32BE(20),941);}
const result={version:'1.5.0-rc1',passed:true,automated_checks:Object.values(expected).reduce((a,b)=>a+b,10),documents:documents.length,local_links:links,jar_sha256:sha,missing_links:[],original_asset_dimensions:[1672,941],external_links_checked:false,ci_run_verified:false};
fs.writeFileSync(path.join(root,'qa/documentation-release-check.json'),JSON.stringify(result,null,2)+'\n');
console.log('PASS',documents.length,'documents;',links,'local links; release evidence and original asset dimensions agree.');
