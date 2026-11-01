// Local, read-only HTTP and source-contract checks; real interaction evidence is recorded separately.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const base=process.env.ADC_PUBLIC_TEST_ORIGIN || 'http://127.0.0.1:8087';
assert(['localhost','127.0.0.1','[::1]'].includes(new URL(base).hostname),'Local loopback only');
const checks=[];
async function check(name,test){await test();checks.push({name,passed:true});console.log('PASS',name);}
const homepage=fs.readFileSync(path.join(root,'src/main/resources/web/homepage.js'),'utf8');
const app=fs.readFileSync(path.join(root,'src/main/resources/web/app.js'),'utf8');
const carousel=fs.readFileSync(path.join(root,'src/main/resources/web/carousel.js'),'utf8');
const loadable=homepage.replace("'./carousel.js?v=1.4.0-rc1'",JSON.stringify('data:text/javascript;base64,'+Buffer.from(carousel).toString('base64')));
const {slides,rolePreviews}=await import('data:text/javascript;base64,'+Buffer.from(loadable).toString('base64'));
await check('Three distinct original scenes, including reception',()=>{assert.equal(slides.length,3);assert.equal(new Set(slides.map(s=>s.image)).size,3);const hashes=[];for(const s of slides){assert(s.title.length===2);assert(s.alt);const asset=fs.readFileSync(path.join(root,'src/main/resources/web/images',s.image));hashes.push(createHash('sha256').update(asset).digest('hex'));}assert.equal(new Set(hashes).size,3);});
await check('Seven illustrative business roles; preview cannot grant an identity',()=>{assert.equal(rolePreviews.length,7);assert(new Set(rolePreviews.map(r=>r.name)).size===7);assert(!homepage.includes('/auth/login'));assert(!homepage.includes('api('));});
await check('Motion controls, keyboard tabs and cleanup are supplied',()=>{for(const s of ['prefers-reduced-motion','visibilitychange','ArrowRight','dispose','removeEventListener','aria-pressed','aria-controls'])assert(homepage.includes(s));assert(carousel.includes('clearInterval'));});
await check('Only known sections are used for deep-link scrolling',()=>assert(homepage.includes('["features","journey","roles","trust","faq"].includes(section)')));
await check('Public home and protected workspace are separate routes',()=>{assert(app.includes('renderHomepage'));assert(app.includes('if (!page || page === "home") return publicPage()'));assert(app.includes('if (state.principal) return refresh()'));});
await check('Page search is restricted to authorized navigation',()=>assert(app.includes('const available = navItems.filter(n => !n[3] || can(n[3]))')));
const health=await (await fetch(base+'/api/health')).json();
await check('Expected Java JDBC release is serving',()=>{assert.equal(health.version,'1.5.0-rc1');assert.equal(health.data_access,'JAVA_JDBC');assert.equal(health.ok,true);});
for(const [name,type] of [['/','text/html'],['/homepage.js','text/javascript'],['/homepage.css','text/css'],['/studio.css','text/css'],['/practice.css','text/css'],['/practice-workflow.js','text/javascript'],['/worklists.js','text/javascript'],['/images/workspace-reception-v14.jpg','image/jpeg'],['/images/workspace-clinical-v14.jpg','image/jpeg'],['/images/workspace-billing-v14.jpg','image/jpeg'],['/auth-ui.js','text/javascript'],['/carousel.js','text/javascript'],['/clinic-calendar.js','text/javascript'],['/images/home-care-v1.png','image/png'],['/images/home-clinic-v1.png','image/png'],['/images/home-reception-v1.png','image/png']]){
 await check('GET and HEAD '+name,async()=>{const r=await fetch(base+name);assert.equal(r.status,200);assert(r.headers.get('content-type').startsWith(type));assert(r.headers.get('x-content-type-options')==='nosniff');const bytes=Buffer.from(await r.arrayBuffer());assert(bytes.length>100);if(type==='image/png'){assert.equal(bytes.subarray(1,4).toString(),'PNG');assert.equal(createHash('sha256').update(bytes).digest('hex'),createHash('sha256').update(fs.readFileSync(path.join(root,'src/main/resources/web',name))).digest('hex'));}const h=await fetch(base+name,{method:'HEAD'});assert.equal(h.status,200);assert.equal((await h.arrayBuffer()).byteLength,0);});
}
for(const resource of ['/practice-setup.js','/followups.js','/setup.css'])await check('Management and follow-up module is served: '+resource,async()=>{const r=await fetch(base+resource);assert.equal(r.status,200);assert((await r.text()).length>100);const head=await fetch(base+resource,{method:'HEAD'});assert.equal(head.status,200);assert.equal((await head.arrayBuffer()).byteLength,0);});
for(const resource of ['/data/setup-credentials.txt','/.env','/images/unknown.png','/tools/local-server.ps1'])await check('Unlisted static file is unavailable: '+resource,async()=>assert.equal((await fetch(base+resource)).status,404));
for(const resource of ['/api/patients','/api/visits','/api/portal','/api/admin/access','/api/followups'])await check('Public page does not expose '+resource,async()=>assert.equal((await fetch(base+resource)).status,401));
await check('Static resource POST is rejected',async()=>assert.equal((await fetch(base+'/homepage.js',{method:'POST'})).status,405));
fs.writeFileSync(path.join(root,'qa/homepage-contract-tests.json'),JSON.stringify({version:health.version,passed:true,tests:checks.length,checks,jar_sha256:createHash('sha256').update(fs.readFileSync(path.join(root,'target/adc-nexus.jar'))).digest('hex'),browser_interaction_verified:false},null,2)+'\n');
console.log('COMPLETE',checks.length,'local HTTP/source checks; not a browser substitute.');
