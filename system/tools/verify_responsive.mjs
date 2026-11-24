import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { setTimeout as pause } from "node:timers/promises";

const [base, out, mode] = process.argv.slice(2);
assert.equal(new URL(base).hostname, "127.0.0.1");
mkdirSync(out, { recursive: true });
const listener = net.createServer();
await new Promise(resolve => listener.listen(0, "127.0.0.1", resolve));
const { port } = listener.address();
await new Promise(resolve => listener.close(resolve));
const executable = process.env.ADC_CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const profile = mkdtempSync(path.join(os.tmpdir(), "adc-chrome-"));
const chrome = spawn(executable, [
  "--headless", "--disable-gpu", "--no-first-run", "--disable-background-networking",
  "--disable-features=Translate", "--remote-debugging-port=" + port, "--user-data-dir=" + profile,
  "about:blank",
], { windowsHide: true, stdio: "ignore" });

const expected = { CLINIC_MANAGER: 11, DENTIST: 5, FRONT_DESK: 7, CASHIER: 5, HQ_OPERATIONS: 9, HQ_FINANCE: 7, ADMIN: 5 };
const viewports = [
  [320, 720, true], [390, 844, true], [568, 320, true], [768, 1024, true],
  [1024, 768, true], [1280, 800, false], [1440, 900, false], [1920, 1080, false],
];
const snapshots = new Set(["#/dashboard", "#/appointments", "#/clinical", "#/periods", "#/resources", "#/analytics"]);
const keyWidths = new Set([320, 390, 768, 1024, 1440]);
const rows = [];
const exceptions = [];
const interactions = [];
const pending = new Map();
let connection, id = 0;

async function connect() {
  let target;
  for (let retries = 0; retries < 100 && !target; retries++) {
    try {
      target = (await (await fetch("http://127.0.0.1:" + port + "/json/list")).json()).find(item => item.type === "page");
    } catch {
      await pause(100);
    }
  }
  assert(target, "Chrome debugging endpoint did not start");
  connection = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(resolve => connection.addEventListener("open", resolve, { once: true }));
  connection.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails.text);
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    if (message.error) request.reject(Error(message.error.message));
    else request.resolve(message.result);
  });
}

function send(method, params = {}) {
  const request = ++id;
  return new Promise((resolve, reject) => {
    pending.set(request, { resolve, reject });
    connection.send(JSON.stringify({ id: request, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  assert(!result.exceptionDetails, result.exceptionDetails?.text);
  return result.result.value;
}

async function until(expression) {
  for (let retries = 0; retries < 140; retries++) {
    if (await evaluate(expression)) return;
    await pause(45);
  }
  throw Error("Timed out at " + await evaluate("location.hash") + ": " + expression);
}

async function viewport([width, height, touch]) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: touch });
  await send("Emulation.setTouchEmulationEnabled", { enabled: touch });
}

async function open(route, ready) {
  await send("Page.navigate", { url: base + "/" + route });
  await until(ready);
}

async function click(selector, touch = false) {
  const point = await evaluate("(" + ((selector) => {
    const target = document.querySelector(selector);
    if (!target) return null;
    target.scrollIntoView({ block: "nearest", inline: "nearest" });
    const rect = target.getBoundingClientRect();
    return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 };
  }).toString() + ")(" + JSON.stringify(selector) + ")");
  assert(point, selector);
  if (touch) {
    await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [point] });
    await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  } else {
    await send("Input.dispatchMouseEvent", { type: "mousePressed", ...point, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", ...point, button: "left", clickCount: 1 });
  }
}

async function capture(name) {
  const screenshot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(path.join(out, name + ".png"), Buffer.from(screenshot.data, "base64"));
}

function metrics(width) {
  const overflow = [];
  const clipped = [];
  const horizontalRegions = new Set();
  const root = document.querySelector("#modal-root .modal, #modal-root .drawer") || document.querySelector(".workspace, .auth-layout, .lp") || document.body;
  for (const node of root.querySelectorAll("h1,h2,h3,button,input:not([type=hidden]),select,textarea,.btn,.card,.mini-stat,.receipt-grid,.auth-credential-row")) {
    if (node.closest(".sidebar, [hidden], [aria-hidden=true], .calendar-grid, .lp-hero-images")) continue;
    const rect = node.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2 || getComputedStyle(node).visibility === "hidden") continue;
    let scrollRegion;
    for (let parent = node.parentElement; parent && parent !== root; parent = parent.parentElement) {
      if (/^(auto|scroll)$/.test(getComputedStyle(parent).overflowX) && parent.scrollWidth > parent.clientWidth + 2) {
        scrollRegion = parent;
        horizontalRegions.add(Array.from(parent.classList).slice(0, 2).join("."));
        break;
      }
    }
    if (scrollRegion) continue;
    if (rect.left < -2 || rect.right > width + 2) {
      if (overflow.length < 20) overflow.push({ tag: node.tagName, className: node.className, text: (node.innerText || node.getAttribute("aria-label") || "").trim().slice(0, 45), excess: Math.round(Math.max(-rect.left, rect.right - width)) });
    }
  }
  for (const node of root.querySelectorAll(".metric .value, #filter-form > input[type=date], #filter-form > select")) {
    const rect = node.getBoundingClientRect();
    if (rect.height < 2) continue;
    if ((node.classList.contains("value") && node.scrollWidth > node.clientWidth + 2) ||
        (node.type === "date" && rect.width < 120) ||
        (node.tagName === "SELECT" && rect.width < 110)) clipped.push(node.className);
  }
  return { viewport: innerWidth, rootOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - width,
    controlsOutside: overflow, clipped, horizontalRegions: [...horizontalRegions], shownError: !!document.querySelector("#page-content .callout.error") };
}

async function measure(role, route, width) {
  const result = await evaluate("(" + metrics.toString() + ")(" + width + ")");
  rows.push({ role, route, width, ...result });
  return result;
}

async function login(role) {
  await send("Network.clearBrowserCookies");
  await open("?" + Date.now() + "#/login", "!!document.querySelector('#unified-auth-form')");
  const credentials = role === "ADMIN" ? { name: "owner", password: process.env.ADC_RESPONSIVE_ADMIN } :
    await evaluate("(async()=>{const c=await(await fetch('/api/auth/config')).json();return {name:c.demo_accounts.find(a=>a.role===" + JSON.stringify(role) + ").username,password:c.demo_password}})()");
  assert(credentials.password);
  await evaluate("document.querySelector('#auth-username').value=" + JSON.stringify(credentials.name) + ";document.querySelector('#auth-password').value=" + JSON.stringify(credentials.password) + ";document.querySelector('#unified-auth-form').requestSubmit()");
  await until("!!document.querySelector('#page-content h1') && !document.querySelector('#page-content .loader')");
}

try {
  await connect();
  for (const domain of ["Page", "Network", "Runtime"]) await send(domain + ".enable");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  for (const size of viewports) {
    await viewport(size);
    for (const [route, selector] of [["#/home", ".lp-hero h1"], ["#/login", "#unified-auth-form"]]) {
      await open("?" + Date.now() + route, "!!document.querySelector(" + JSON.stringify(selector) + ")");
      if (route === "#/home") await until("document.querySelector('.lp-hero-image.active')?.naturalWidth > 0");
      await measure("PUBLIC", route, size[0]);
      if (keyWidths.has(size[0])) await capture("public-" + route.slice(2) + "-" + size[0]);
    }
  }
  for (const [role, count] of Object.entries(expected)) {
    if (mode === "baseline" && !["CLINIC_MANAGER", "DENTIST", "HQ_FINANCE", "ADMIN"].includes(role)) continue;
    await viewport(viewports[5]);
    await login(role);
    const routes = await evaluate("[...document.querySelectorAll('a.nav-item')].map(a=>a.getAttribute('href'))");
    assert.equal(routes.length, count, role);
    for (const route of routes) {
      await open(route, "!!document.querySelector('#page-content h1') && !document.querySelector('#page-content .loader') && document.querySelector('a.nav-item.active')?.getAttribute('href')===" + JSON.stringify(route));
      for (const size of viewports) {
        await viewport(size);
        await pause(55);
        await measure(role, route, size[0]);
        if (snapshots.has(route) && keyWidths.has(size[0]) &&
            (role === "CLINIC_MANAGER" || (role === "DENTIST" && route === "#/clinical") ||
             (role === "HQ_FINANCE" && ["#/dashboard", "#/periods"].includes(route)))) {
          await capture(role.toLowerCase() + "-" + route.slice(2) + "-" + size[0]);
        }
      }
    }
    console.log("Checked", role, routes.length);
  }
  if (mode !== "baseline") {
    await viewport(viewports[1]);
    await login("CLINIC_MANAGER");
    await click(".mobile-nav", true);
    await until("document.querySelector('.sidebar').classList.contains('open')");
    await click('a.nav-item[href="#/appointments"]', true);
    await until("location.hash==='#/appointments' && !document.querySelector('.sidebar').classList.contains('open') && !document.querySelector('#page-content .loader')");
    interactions.push("Touch menu opens, changes page and closes");
    await click('#page-content button[data-act="new-appointment"]', true);
    await until("!!document.querySelector('#modal-root .modal')");
    await measure("CLINIC_MANAGER", "appointment dialog", 390);
    await pause(250);
    await capture("appointment-dialog-390");
    await viewport(viewports[2]);
    await measure("CLINIC_MANAGER", "appointment dialog", 568);
    assert(await evaluate("document.querySelector('#modal-root .modal').getBoundingClientRect().bottom <= innerHeight + 1"));
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
    await until("!document.querySelector('#modal-root .modal')");
    interactions.push("Appointment dialog fits a short landscape viewport and closes with Escape");
    await viewport(viewports[3]);
    await click(".mobile-nav", true);
    await until("document.querySelector('.sidebar').classList.contains('open')");
    await click('a.nav-item[href="#/patients"]', true);
    await until("location.hash==='#/patients' && !document.querySelector('.sidebar').classList.contains('open')");
    interactions.push("Portrait tablet drawer opens and closes after navigation");

    await viewport(viewports[0]);
    await login("HQ_FINANCE");
    await open("#/dashboard", "!!document.querySelector('#page-content .chart')");
    await evaluate("document.querySelector('.chart').focus()");
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
    await until("document.querySelector('.chart').scrollLeft>0");
    interactions.push("Appointment trend charts keep all dates horizontally accessible by keyboard");
  }
} finally {
  writeFileSync(path.join(out, "responsive.json"), JSON.stringify({ rows, exceptions, interactions }, null, 2));
  connection?.close();
  chrome.kill();
}
const failures = rows.filter(row => row.rootOverflow > 2 || row.viewport !== row.width || row.controlsOutside.length || row.clipped.length || row.shownError);
console.log(rows.length + " layout checks; " + failures.length + " findings; " + exceptions.length + " uncaught exceptions");
for (const row of failures.slice(0, 30)) {
  console.log(row.role, row.route, row.width, row.rootOverflow, JSON.stringify(row.controlsOutside.slice(0, 3)), row.clipped);
}
if (mode !== "baseline") assert.equal(failures.length + exceptions.length, 0);
