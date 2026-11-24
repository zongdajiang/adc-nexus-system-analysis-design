import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import http from "node:http";
import net from "node:net";
import { pathToFileURL } from "node:url";
import { spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";

const prototype = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const fixture = JSON.parse(fs.readFileSync(path.join(path.dirname(prototype), "04_合成场景.json"), "utf8"));
const a = fixture.scenarios.bound, b = fixture.scenarios.alternate;
const samples = {appointment:a.upcoming.items[0].appointment_code,
 cancelled:a.history.items.find(item=>item.status==="CANCELLED").appointment_code,
 visit:a.visits.items.find(item=>item.status==="COMPLETED").visit_code,
 refund:a.bills.items.find(item=>item.status==="PARTIALLY_PAID" && item.refunded_fen>0),
 void:a.bills.items.find(item=>item.status==="VOID")};
const keySelector=code=>`[data-key="${code}"]`;
fs.mkdirSync(output, { recursive: true });
const browserDirectory = fs.mkdtempSync(path.join(output, "patient-chrome-"));
const server = http.createServer((request, response) => {
  if (request.url !== "/") {
    response.writeHead(404).end();
    return;
  }
  response.setHeader("Content-Type", "text/html; charset=utf-8");
  response.end(fs.readFileSync(prototype));
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const origin = "http://127.0.0.1:" + server.address().port;
const probe = net.createServer();
await new Promise(resolve => probe.listen(0, "127.0.0.1", resolve));
const port = probe.address().port;
await new Promise(resolve => probe.close(resolve));
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless", "--disable-gpu", "--no-first-run", "--disable-background-networking",
  "--no-default-browser-check", "--user-data-dir=" + browserDirectory,
  "--remote-debugging-port=" + port, "about:blank",
], { windowsHide: true, stdio: "ignore" });
let socket;
const results = [];
try {
  let target;
  for (let attempt = 0; attempt < 80; attempt++) {
    try {
      target = await (await fetch("http://127.0.0.1:" + port + "/json/list")).json();
      target = target.find(item => item.type === "page");
      if (target) break;
    } catch {}
    await sleep(100);
  }
  assert(target?.webSocketDebuggerUrl, "Headless Chrome did not open a page");
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  let serial = 0;
  const pending = new Map();
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    const handler = pending.get(message.id);
    if (!handler) return;
    pending.delete(message.id);
    if (message.error) handler.reject(new Error(message.error.message));
    else handler.resolve(message.result);
  });
  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++serial;
      pending.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params }));
    });
  }
  async function evaluate(expression) {
    const result = await send("Runtime.evaluate", {
      expression, awaitPromise: true, returnByValue: true,
    });
    assert(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  async function waitFor(expression) {
    for (let attempt = 0; attempt < 70; attempt++) {
      if (await evaluate(expression)) return;
      await sleep(30);
    }
    throw new Error("Timed out waiting for " + expression);
  }
  async function click(selector) {
    await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
  }
  async function page(code) {
    await waitFor(`document.documentElement.dataset.ready === ${JSON.stringify(code)}`);
  }
  async function check(name, fn) {
    await fn();
    results.push(name);
    process.stdout.write("PASS " + name + "\n");
  }
  async function choose(identity) {
    await evaluate(`document.getElementById("scenario").value=${JSON.stringify(identity)};
      document.getElementById("scenario").dispatchEvent(new Event("change"))`);
    await page("MP-01");
    await click('[data-action="login"]');
    await page(identity === "unbound" || identity === "pending" ? "MP-02" : "MP-03");
  }
  async function capture(name) {
    const result = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(output, name + ".png"), Buffer.from(result.data, "base64"));
  }
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false,
  });
  await send("Page.navigate", { url: origin });
  await waitFor('document.documentElement.dataset.ready === "MP-01"');
  await check("MP-01 login and MP-03 own next appointment", async () => {
    await choose("bound");
    assert(await evaluate('screen.textContent.includes(fixtures.scenarios.bound.me.name_zh) && screen.textContent.includes("全面口腔检查")'));
    await capture("patient-desktop");
  });
  await check("MP-04 and MP-05 upcoming and cancelled history", async () => {
    await click('[data-action="appointment"]');
    await page("MP-05");
    assert(await evaluate('screen.textContent.includes(fixtures.scenarios.bound.upcoming.items[0].appointment_code)'));
    await click("#back");
    await page("MP-04");
    await click('[data-action="group"][data-key="history"]');
    await waitFor('screen.textContent.includes("已取消")');
    await click(keySelector(samples.cancelled));
    await page("MP-05");
    assert(await evaluate('screen.textContent.includes("已取消")'));
  });
  await check("MP-06 visit list and public summary", async () => {
    await click('[data-route="MP-03"]');
    await page("MP-03");
    await click('[data-action="visits"]');
    await page("MP-06");
    await click(keySelector(samples.visit));
    await waitFor('screen.textContent.includes("登记时间")');
    assert(await evaluate('!screen.textContent.includes("病史正文")'));
  });
  await check("MP-07 refund balance and void history", async () => {
    await click('[data-route="MP-07"]');
    await page("MP-07");
    await click(keySelector(samples.refund.invoice_code));
    await waitFor('screen.textContent.includes("累计退款")');
    assert.equal(await evaluate('document.querySelector(".total").textContent'), new Intl.NumberFormat("zh-CN",{style:"currency",currency:"CNY"}).format(samples.refund.balance_fen/100));
    await click("#back");
    await waitFor('document.querySelectorAll("[data-action=bill]").length === fixtures.scenarios.bound.bills.items.length');
    await click(keySelector(samples.void.invoice_code));
    await waitFor('screen.textContent.includes("已作废") && screen.textContent.includes("累计退款")');
    assert.equal(await evaluate('document.querySelector(".total").textContent'), "¥0.00");
  });
  await check("MP-08 logout clears identity and old visible data", async () => {
    await click('[data-route="MP-08"]');
    await page("MP-08");
    assert(await evaluate('screen.textContent.includes(fixtures.scenarios.bound.me.masked_phone)'));
    await click('[data-action="logout"]');
    await page("MP-01");
    assert(await evaluate('!screen.textContent.includes(fixtures.scenarios.bound.me.name_zh) && state.session === null && Object.keys(state.cache).length === 0'));
  });
  await check("A-to-B switch and foreign record rejection in mock adapter", async () => {
    await choose("alternate");
    assert(await evaluate('screen.textContent.includes(fixtures.scenarios.alternate.me.name_zh) && !screen.textContent.includes(fixtures.scenarios.bound.me.name_zh)'));
    await click("#foreign");
    await waitFor('screen.textContent.includes("无法查看此记录")');
    assert(await evaluate('!screen.textContent.includes(fixtures.scenarios.bound.bills.items[0].invoice_code)'));
    await click('[data-action="back"]');
    await page("MP-07");
    assert(await evaluate('screen.textContent.includes(fixtures.scenarios.alternate.bills.items[0].invoice_code) && !screen.textContent.includes(fixtures.scenarios.bound.bills.items[0].invoice_code)'));
  });
  await check("Unbound request and pending verification remain gated", async () => {
    await choose("unbound");
    assert(await evaluate('!document.getElementById("bottom").hidden === false'));
    if(fixture.selfService)await evaluate(`var f=document.getElementById('binding-form');f.elements.name_zh.value='合成身份核验';f.elements.phone.value='13900000001';f.elements.date_of_birth.value='1994-05-12';f.elements.privacy_confirmed.checked=true;f.requestSubmit()`);
    else await evaluate('document.getElementById("clinic-code").value="ADC-DEMO";document.getElementById("verification-reference").value="SYNTHETIC";document.getElementById("binding-form").requestSubmit()');
    await waitFor('screen.textContent.includes("资料核实中")');
    assert.equal(await evaluate('(async()=>{try{await mockRequest("/bills");return 0}catch(e){return e.status}})()'), 403);
  });
  await check("Bound empty pages offer a next action", async () => {
    await choose("empty");
    assert(await evaluate('screen.textContent.includes("暂无待到诊预约")'));
    await click('[data-route="MP-07"]');
    await page("MP-07");
    assert(await evaluate('screen.textContent.includes("暂无账单")'));
  });
  await check("Network retry retains location and session expiry clears identity", async () => {
    await choose("bound");
    await click('[data-route="MP-07"]');
    await page("MP-07");
    await evaluate('document.getElementById("failure").value="network";document.getElementById("failure").dispatchEvent(new Event("change"))');
    await waitFor('screen.textContent.includes("暂时无法加载")');
    await click('[data-action="retry"]');
    await waitFor('screen.textContent.includes(fixtures.scenarios.bound.bills.items[0].invoice_code)');
    await evaluate('document.getElementById("failure").value="expired";document.getElementById("failure").dispatchEvent(new Event("change"))');
    await page("MP-01");
    assert(await evaluate('document.getElementById("toast").textContent.includes("已过期") && state.session === null'));
  });
  await check("390px mobile layout and 200 percent text stay readable", async () => {
    await send("Emulation.setDeviceMetricsOverride", {
      width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
    });
    await choose("bound");
    assert(await evaluate('innerWidth === 390 && document.documentElement.scrollWidth <= innerWidth'));
    await capture("patient-mobile");
    await click('[data-route="MP-07"]');
    await page("MP-07");
    await click(keySelector(samples.refund.invoice_code));
    await waitFor('screen.textContent.includes("累计退款")');
    await capture("patient-bill-mobile");
    await evaluate('document.querySelector("main").style.fontSize="200%"');
    assert(await evaluate('screen.scrollWidth <= screen.clientWidth + 1'));
  });
  await send("Page.navigate", { url: pathToFileURL(prototype).href });
  await waitFor('document.documentElement.dataset.ready === "MP-01"');
  await click('[data-action="login"]');
  await page("MP-03");
  assert(await evaluate('screen.textContent.includes(fixtures.scenarios.bound.me.name_zh)'));
  if(fixture.selfService){
    await check('MP-09 to MP-10 books a confirmed own appointment and returns the saved details',async()=>{
      await click('[data-action="book"]');await page('MP-09');await capture('patient-booking-slots');
      assert(await evaluate('document.querySelectorAll("[data-action=select-slot]").length>0'));
      await click('[data-action=select-slot]');await page('MP-10');await capture('patient-booking-confirm');
      await evaluate(`document.querySelector('#booking-confirm [name=patient_confirmed]').checked=true;document.querySelector('#booking-confirm').requestSubmit()`);
      await page('MP-05');assert(await evaluate('screen.textContent.includes("MP-MOCK-1")'));
      await evaluate('window.patientV04={code:state.key,body:{slot_token:state.booking.token,patient_confirmed:true,visit_need:""},key:state.booking.requestKey};');
    });
    await check('Patient mock idempotency replays the original result and rejects changed payloads',async()=>{
      assert(await evaluate(`(async()=>{const a=await mockRequest('/appointments','POST',patientV04.body,{idempotencyKey:patientV04.key});return a.appointment_code===patientV04.code && allAppointments(storeForIdentity()).filter(x=>x.appointment_code===a.appointment_code).length===1})()`));
      assert.equal(await evaluate(`(async()=>{try{await mockRequest('/appointments','POST',{...patientV04.body,visit_need:'changed'},{idempotencyKey:patientV04.key});return 0}catch(e){return e.status}})()`),409);
    });
    await check('Patient rescheduling preserves appointment identity and updates the chosen clinician/time',async()=>{
      await click('[data-action=reschedule]');await page('MP-09');
      await evaluate(`document.querySelectorAll('[data-action=select-slot]')[1].click()`);await page('MP-10');
      await evaluate(`document.querySelector('#booking-confirm [name=reason]').value='患者申请调整合成预约';document.querySelector('#booking-confirm [name=patient_confirmed]').checked=true;document.querySelector('#booking-confirm').requestSubmit()`);
      await page('MP-05');assert(await evaluate('state.key===patientV04.code && state.cache.appointment.appointment_version===2'));
    });
    await check('Patient cancellation retains history and removes ordinary change controls',async()=>{
      await click('[data-action=cancel-booking]');await page('MP-11');
      await evaluate(`document.querySelector('#cancel-confirm [name=reason]').value='患者更改个人安排';document.querySelector('#cancel-confirm [name=patient_confirmed]').checked=true;document.querySelector('#cancel-confirm').requestSubmit()`);
      await page('MP-05');assert(await evaluate(`state.cache.appointment.status==='CANCELLED' && !document.querySelector('[data-action=reschedule]') && storeForIdentity().history.items.some(a=>a.appointment_code===patientV04.code)`));
      await capture('patient-cancelled');
    });
    await check('Stale versions, missing confirmation and completed appointments cannot be changed',async()=>{
      assert.equal(await evaluate(`(async()=>{const a=storeForIdentity().upcoming.items[0];try{await mockRequest('/appointments/'+a.appointment_code+'/cancel','POST',{appointment_version:-1,patient_confirmed:true,reason:'stale'},{idempotencyKey:'stale-check'});return 0}catch(e){return e.status}})()`),409);
      assert.equal(await evaluate(`(async()=>{try{await mockRequest('/appointments','POST',{slot_token:selfService.slots[0].slot_token,patient_confirmed:false},{idempotencyKey:'missing-confirmation'});return 0}catch(e){return e.status}})()`),422);
      assert.equal(await evaluate(`(async()=>{const a=storeForIdentity().history.items.find(a=>a.status==='COMPLETED');try{await mockRequest('/appointments/'+a.appointment_code+'/cancel','POST',{appointment_version:a.appointment_version,patient_confirmed:true,reason:'invalid'},{idempotencyKey:'completed-check'});return 0}catch(e){return e.status}})()`),409);
    });
    await check('Patient mock rejects resource conflicts and foreign-patient mutations without leaking details',async()=>{
      await evaluate(`(async()=>{const q=new URLSearchParams({clinic_code:selfService.clinic.clinic_code,treatment_code:selfService.treatments[0].treatment_code,date:selfService.slots[0].scheduled_start_at.slice(0,10)});const slot=(await mockRequest('/booking/slots?'+q)).items[0];const a=await mockRequest('/appointments','POST',{slot_token:slot.slot_token,patient_confirmed:true},{idempotencyKey:'conflict-A'});window.patientConflict={slot:slot.slot_token,code:a.appointment_code}})()`);
      await choose('alternate');
      assert.equal(await evaluate(`(async()=>{try{await mockRequest('/appointments','POST',{slot_token:patientConflict.slot,patient_confirmed:true},{idempotencyKey:'conflict-B'});return 0}catch(e){return e.status}})()`),409);
      assert.equal(await evaluate(`(async()=>{try{await mockRequest('/appointments/'+patientConflict.code+'/cancel','POST',{appointment_version:1,patient_confirmed:true,reason:'not mine'},{idempotencyKey:'foreign-B'});return 0}catch(e){return e.status}})()`),404);
    });
    await check('Unbound identities cannot book; contact page clearly labels synthetic contact details',async()=>{
      await choose('unbound');assert.equal(await evaluate(`(async()=>{try{await mockRequest('/appointments','POST',{slot_token:selfService.slots[0].slot_token,patient_confirmed:true},{idempotencyKey:'unbound-write'});return 0}catch(e){return e.status}})()`),403);
      await choose('bound');await click('[data-route="MP-08"]');await page('MP-08');await click('[data-action=contact]');await page('MP-12');
      assert(await evaluate('screen.textContent.includes("合成地址与电话") && document.documentElement.scrollWidth<=innerWidth'));
      await capture('patient-contact');
    });
  }
  fs.writeFileSync(path.join(output, "patient-prototype.json"), JSON.stringify({
    passed: true, mode: "local interactive prototype and mock adapter",
    production_patient_api_tested: false, tests: results.length, results,
    direct_file_open_verified: true,
    viewport: [390, 844],
  }, null, 2) + "\n");
} finally {
  if (socket) socket.close();
  chrome.kill();
  await new Promise(resolve => server.close(resolve));
}
