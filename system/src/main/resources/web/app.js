import { renderAuthPage } from './auth-ui.js?v=1.4.0-rc1';
import { renderHomepage } from './homepage.js?v=1.4.0-rc1';
import { filterAppointments, buildCalendarModel, renderCalendar, shiftDay } from './clinic-calendar.js?v=1.4.0-rc1';
import {renderCareWorkspace,bindCareTabs,appointmentHistoryEvent} from './practice-workflow.js?v=1.4.0-rc1';
import {receptionContent,billingContent,orderedAgenda} from './worklists.js?v=1.4.0-rc1';
import {renderSetupTab,installSetupHandlers} from './practice-setup.js?v=1.5.0-rc1';
import {followupTabs,renderFollowups,installFollowupHandlers} from './followups.js?v=1.5.0-rc1';
const $ = (s) => document.querySelector(s);
const app = $("#app"),
  modalRoot = $("#modal-root");
let activeDialogClose = null;
const state = {
  lang: localStorage.getItem("adc-language") || "zh",
  principal: null,
  boot: null,
  csrf: "",
  config: null,
  clinic: sessionStorage.getItem("adc-clinic") || "",
  from: "2026-07-01",
  to: "2026-10-20",
  selectedTooth: "",
  view: "calendar",
  calendarGroup: "dentist",
  scheduleDentist: "",
  scheduleStatus: "",
  scheduleSearch: "",
  resourcesTab: "clinics",
  deskView:"", deskDoctor:"", deskSearch:"", billView:"", billSearch:"", careTab:"", careVisit:"",
};
const T = (zh, en) => (state.lang === "en" ? en || zh : zh);
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (v) =>
  new Intl.NumberFormat(state.lang === "en" ? "en-CN" : "zh-CN", {
    style: "currency",
    currency: "CNY",
    maximumFractionDigits: 2,
  }).format(Number(v || 0) / 100);
const date = (v) =>
  esc(
    String(v || "—")
      .slice(0, 16)
      .replace("T", " "),
  );
const pct = (v) =>
  v == null ? T("不适用", "N/A") : (Number(v) * 100).toFixed(1) + "%";
const num = (v) => new Intl.NumberFormat("en-US").format(Number(v || 0));
const paths = {
  dashboard: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  calendar:
    "M8 2v4 M16 2v4 M3 9h18 M4 4h16a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1 M7 13h3 M14 13h3 M7 17h3",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M16 3a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  tooth:
    "M7 3c-3 0-4 3-3 6l2 10c.5 3 3 3 3 0l1-5c.3-2 3-2 3 0l1 5c.5 3 3 3 3 0l3-10c1-3-1-6-4-6-2 0-3 1-4 1S9 3 7 3",
  receipt: "M6 3h12v18l-3-2-3 2-3-2-3 2z M9 7h6 M9 11h6 M9 15h3",
  chart: "M3 3v18h18 M7 16v-5 M12 16V7 M17 16V4",
  building:
    "M4 21V5l8-3 8 3v16 M8 7h1 M15 7h1 M8 11h1 M15 11h1 M8 15h1 M15 15h1 M10 21v-3h4v3",
  shield: "M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6z M8 12l3 3 5-6",
  clock: "M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  plus: "M12 5v14 M5 12h14",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  chevron: "M9 5l7 7-7 7",
  search: "M21 21l-5-5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  x: "M6 6l12 12 M6 18L18 6",
  check: "M5 12l4 4L19 6",
  logout: "M9 3H4v18h5 M12 12h9 M17 8l4 4-4 4",
  globe:
    "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M3 12h18 M12 3c5 5 5 13 0 18-5-5-5-13 0-18",
  leaf: "M20 3C9 2 2 8 5 16c4 6 14 2 15-13 M5 20l9-10",
  wallet: "M3 5h16v16H3z M3 5l13-3v3 M15 11h6v5h-6z",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  download: "M12 3v12 M7 10l5 5 5-5 M4 17v4h16v-4",
  file: "M14 2H4v20h16V8z M14 2v6h6 M8 12h8 M8 16h8",
  location:
    "M12 22s8-9 8-14a8 8 0 0 0-16 0c0 5 8 14 8 14 M15 8a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
  lock: "M6 10h12v11H6z M8 10V6a4 4 0 0 1 8 0v4",
  heart: "M20 4c-3-2-6 0-8 2-2-2-5-4-8-2-5 4 0 10 8 17 8-7 13-13 8-17",
};
const icon = (name = "file") =>
  `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.file}"/></svg>`;
const statusMap = {
  CONFIRMED: ["已确认", "Confirmed", "blue"],
  CHECKED_IN: ["已到诊", "Checked in", "amber"],
  IN_PROGRESS: ["诊疗中", "In progress", "blue"],
  COMPLETED: ["已完成", "Completed", "green"],
  CANCELLED: ["已取消", "Cancelled", ""],
  NO_SHOW: ["未到诊", "No-show", "red"],
  HOLD: ["暂留", "Hold", "amber"],
  WAITING: ["待诊疗", "Waiting", "amber"],
  SAFETY_REVIEW: ["安全复核", "Safety review", "red"],
  ISSUED: ["已开具", "Issued", "blue"],
  PARTIALLY_PAID: ["部分收款", "Part paid", "amber"],
  PAID: ["已结清", "Paid", "green"],
  VOID: ["已作废", "Void", ""],
  ACTIVE: ["有效", "Active", "green"],
  AVAILABLE: ["可用", "Available", "green"],
  MAINTENANCE: ["维护中", "Maintenance", "amber"],
  INACTIVE: ["停用", "Inactive", ""],
  DISABLED: ["已停用", "Disabled", ""],
  OPEN: ["开放", "Open", "blue"],
  CLOSED: ["已关闭", "Closed", "green"],
  APPROVED: ["已核定", "Approved", "green"],
  VERIFIED: ["已核实", "Verified", "green"],
  VERIFIED_MANUAL: ["已核实", "Verified", "green"],
  PENDING_VERIFICATION: ["待核实", "Pending review", "amber"],
  ACCEPTED: ["已接受", "Accepted", "green"],
  DECLINED: ["已拒绝", "Declined", "red"],
  DEFERRED: ["暂缓", "Deferred", "amber"],
  PROPOSED: ["拟议", "Proposed", "blue"],
  SIGNED: ["已签署", "Signed", "green"],
  DRAFT: ["草稿", "Draft", "amber"],
  OFFERED: ["待确认", "Offered", "blue"],
  EXPIRED: ["已过期", "Expired", ""],
  FULFILLED: ["已补位", "Fulfilled", "green"],
  DISTINCT: ["不同患者", "Distinct", "green"],
  PASSED: ["通过", "Passed", "green"],
  CLEARED: ["旧版复核记录", "Legacy review record", "amber"],
  DELIVERED: ["来源记录：已实施", "Legacy: delivered", ""],
  LEGACY_UNVERIFIED: ["来源状态待核验", "Legacy status unverified", "amber"],
  CRITICAL: ["严重风险", "Critical risk", "red"],
  PENDING: ["待复核", "Pending", "amber"],
  GRANTED: ["已同意", "Granted", "green"],
  WITHDRAWN: ["已撤回", "Withdrawn", "amber"],
  HIGH: ["高风险", "High", "red"],
  SEVERE: ["严重", "Severe", "red"],
  MODERATE: ["中等", "Moderate", "amber"],
  LOW: ["较低", "Low", "green"],
  SUCCESS: ["成功", "Success", "green"],
  DENIED: ["已拒绝", "Denied", "red"],
};
function badge(status) {
  const a = statusMap[status] || [status, status, ""];
  return `<span class="badge ${a[2]}"><i class="dot"></i>${esc(T(a[0], a[1]))}</span>`;
}
const can = (permission) => state.principal?.permissions.includes(permission);
const button = (label, action, id = "", style = "", ico = "") =>
  `<button type="button" class="btn ${style}" data-act="${esc(action)}" data-id="${esc(id)}">${ico ? icon(ico) : ""}${esc(label)}</button>`;
const link = (label, path) =>
  `<a class="text-link" href="#/${esc(path)}">${esc(label)}</a>`;
const empty = (message) =>
  `<div class="empty"><p>${esc(message || T("此范围内暂无记录", "No records in this scope"))}</p></div>`;
const panel = (title, body, action = "", subtitle = "") =>
  `<section class="card"><div class="card-head"><div><h2>${esc(title)}</h2>${subtitle ? `<p class="subline">${esc(subtitle)}</p>` : ""}</div>${action}</div>${body}</section>`;
const table = (headers, rows) =>
  rows.length
    ? `<div class="table-scroll-note">${T("左右滑动查看完整表格", "Swipe horizontally for all columns")}</div><div class="table-wrap" tabindex="0" role="region" aria-label="${T("业务表格，可横向滚动", "Scrollable business table")}"><table><thead><tr>${headers.map((h) => `<th scope="col">${esc(h||T("操作","Actions"))}</th>`).join("")}</tr></thead><tbody>${rows.map((cells) => `<tr>${cells.map((cell) => `<td>${cell ?? "—"}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
    : empty();
const metric = (label, value, note = "", ico = "chart", featured = false) =>
  `<article class="metric ${featured ? "featured" : ""}"><span class="metric-icon">${icon(ico)}</span><div class="label">${esc(label)}</div><div class="value num">${esc(value)}</div><div class="note">${esc(note)}</div></article>`;
const pageNames = {
  "NETWORK COMMAND CENTER": ["工作台", "Workspace"], "PATIENT 360": ["患者管理", "Patients"],
  "SMART SCHEDULING": ["预约管理", "Appointments"], "CLINICAL STUDIO": ["临床工作台", "Clinical workspace"],
  "CAPACITY RECOVERY": ["候补管理", "Waitlist"], "REVENUE CONTROL": ["诊疗结算", "Billing"],
  "FINANCIAL GOVERNANCE": ["期间核算", "Financial periods"], "NETWORK & CAPABILITY": ["组织与资源", "Resources"],
  "PERFORMANCE INTELLIGENCE": ["经营统计", "Performance"], "NETWORK PLANNING": ["扩张测算", "Expansion planning"],
  "ACCESS ADMINISTRATION": ["账号与权限", "Accounts and access"], "ACCOUNTABILITY": ["操作审计", "Audit history"],
  "ACCOUNT SECURITY": ["账号安全", "Account security"],
};
const title = (kicker, name, description, actions = "") =>
  `<div class="title-row row between"><div><h1>${esc(pageNames[kicker] ? T(...pageNames[kicker]) : name)}</h1><p>${esc(description)}</p></div><div class="row wrap push">${actions}</div></div>`;
const opts = (list, label = "name_zh", value = "id") =>
  list.map((r) => ({
    value: r[value],
    label: r[label] || r.name_en || r[value],
  }));
const selectedClinic = () => state.clinic || state.boot?.clinics?.[0]?.id || "";
const query = (object = {}) => {
  const p = new URLSearchParams(object);
  if (state.clinic && !p.has("clinic_id")) p.set("clinic_id", state.clinic);
  return p.toString() ? "?" + p : "";
};
function toast(message) {
  $("#toast-root").innerHTML = `<div class="toast">${esc(message)}</div>`;
  setTimeout(() => ($("#toast-root").innerHTML = ""), 4200);
}
async function api(path, body, options = {}) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    headers["X-CSRF-Token"] = state.csrf;
    headers["Idempotency-Key"] = options.idempotency || crypto.randomUUID();
  }
  const request = {
    method: body === undefined ? "GET" : "POST",
    headers,
    credentials: "same-origin",
    cache: "no-store",
    body: body === undefined ? undefined : JSON.stringify(body),
  };
  let response;
  try {
    response = await fetch("/api" + path, request);
  } catch {
    if (body !== undefined && path === "/admin/staff")
      throw new Error("员工名册请求响应中断，请先重新读取名册核对。激活码可由管理员重新签发。");
    // Retry a business request once with the SAME receipt key. Never blindly
    // repeat password login or demo-session creation after a lost response.
    if (body !== undefined && path.startsWith("/auth/"))
      throw new Error(
        T("登录连接中断，请重新登录。", "Sign-in was interrupted. Please sign in again."),
      );
    await new Promise((resolve) => setTimeout(resolve, 600));
    try {
      response = await fetch("/api" + path, request);
    } catch {
      const e = new Error(
        T(
          body === undefined
            ? "暂时无法连接服务，请检查网络后重新读取。"
            : "暂时无法确认保存结果。请先重新读取记录核对，避免重复登记。",
          body === undefined
            ? "Cannot connect. Check your network and reload the records."
            : "The save result is uncertain. Reload the records before submitting again.",
        ),
      );
      e.code = "CONNECTION_INTERRUPTED";
      throw e;
    }
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      T(
        "服务正在启动或响应中断，请稍候重试。",
        "The service is starting or the response was interrupted. Please retry.",
      ),
    );
  }
  if (!response.ok) {
    const e = new Error(
      data.error?.message || T("操作未完成", "Request failed"),
    );
    e.code = data.error?.code;
    e.details = data.error?.details || [];
    e.status = response.status;
    e.requestId = data.error?.request_id || response.headers.get("X-Request-ID");
    throw e;
  }
  return data;
}
function errorBox(e) {
  return `<div class="callout error"><strong>${esc(e.message)}</strong>${e.details?.length ? `<ul>${e.details.map((d) => `<li>${esc(typeof d === "object" ? JSON.stringify(d) : d)}</li>`).join("")}</ul>` : ""}${e.code ? `<div class="mono" style="margin-top:7px">${esc(e.code)}</div>` : ""}${e.requestId ? `<div class="field-help">${T("请求编号", "Request ID")} <span class="mono">${esc(e.requestId)}</span></div>` : ""}</div>`;
}
function modal({
  name,
  description = "",
  fields = [],
  submit = T("确认保存", "Save"),
  onSubmit,
  body = "",
  wide = false,
  onReady,
  onSuccess,
  successMessage = T("已保存，记录已更新", "Saved. Records updated."),
  informational = false,
}) {
  if(activeDialogClose && activeDialogClose() === false)return activeDialogClose;
  const fieldHtml = fields
    .map((f) => {
      let control;
      const common = `id="f-${esc(f.name)}" name="${esc(f.name)}" ${f.required === false ? "" : "required"} ${f.readonly ? "readonly" : ""}`;
      if (f.type === "select")
        control = `<select class="field-input" ${common}><option value="">${f.required === false ? T("不指定 / 留空", "Unassigned / blank") : T("请选择", "Select")}</option>${(f.options || []).map((o) => `<option value="${esc(o.value)}" ${String(o.value) === String(f.value) ? "selected" : ""}>${esc(o.label)}</option>`).join("")}</select>`;
      else if (f.type === "textarea")
        control = `<textarea class="field-input" rows="${f.rows || 3}" ${common}>${esc(f.value || "")}</textarea>`;
      else if (f.type === "checkbox")
        control = `<label class="check-label"><input type="checkbox" ${common} ${f.value ? "checked" : ""}><span>${esc(f.label)}</span></label>`;
      else
        control = `<input class="field-input" type="${f.type === "money" ? "number" : f.type || "text"}" ${common} value="${esc(f.type === "money" && f.value != null ? Number(f.value) / 100 : (f.value ?? ""))}" ${f.type === "money" ? 'step="0.01" min="0"' : ""} ${f.min != null ? `min="${f.min}"` : ""} ${f.max != null ? `max="${f.max}"` : ""} autocomplete="${f.type === "password" ? "new-password" : "off"}">`;
      return `<div class="field-wrap ${f.full || f.type === "textarea" || f.type === "checkbox" ? "full" : ""}">${f.type === "checkbox" ? "" : `<label class="field-label" for="f-${esc(f.name)}">${esc(f.label)}</label>`}${control}${f.help ? `<p class="field-help">${esc(f.help)}</p>` : ""}</div>`;
    })
    .join("");
  const previousFocus = document.activeElement;
  const wasInert = app.inert;
  app.inert = true;
  let pending = false;
  document.body.classList.add("dialog-open");
  modalRoot.innerHTML = `<div class="modal-overlay"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" ${description?'aria-describedby="modal-description"':''} ${wide ? 'style="width:850px"' : ""}><div class="modal-head"><div><h2 id="modal-title" tabindex="-1">${esc(name)}</h2>${description?`<p id="modal-description">${esc(description)}</p>`:''}</div><button class="modal-close" type="button" aria-label="${T("关闭弹窗","Close dialog")}">${icon("x")}</button></div><form id="dialog-form"><div class="modal-body">${body}<div class="modal-fields">${fieldHtml}</div><div id="modal-error" class="modal-error" role="alert"></div></div><div class="modal-footer"><button type="button" class="btn" id="modal-cancel" ${informational?'hidden':''}>${T("取消", "Cancel")}</button><button type="submit" class="btn primary" id="modal-submit">${esc(submit)}</button></div></form></section></div>`;
  const close = () => {
    if (pending) return false;
    modalRoot.innerHTML = "";
    document.body.classList.remove("dialog-open");
    app.inert = wasInert;
    if(previousFocus?.isConnected)previousFocus.focus({preventScroll:true});
    document.removeEventListener("keydown", trap);
    if(activeDialogClose===close)activeDialogClose=null;
    return true;
  };
  const trap = (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
    }
    if (e.key === "Tab") {
      const all = [
        ...modalRoot.querySelectorAll("button,input,select,textarea,a"),
      ].filter((n) => !n.disabled && n.getClientRects().length && n.tabIndex >= 0);
      if (e.shiftKey && document.activeElement === all[0]) {
        e.preventDefault();
        all.at(-1)?.focus();
      } else if (!e.shiftKey && document.activeElement === all.at(-1)) {
        e.preventDefault();
        all[0]?.focus();
      }
    }
  };
  document.addEventListener("keydown", trap);
  activeDialogClose = close;
  $(".modal-close").onclick = close;
  $("#modal-cancel").onclick = close;
  $("#dialog-form").onsubmit = async (e) => {
    e.preventDefault();
    if (pending) return;
    const form = e.currentTarget;
    if (!form.reportValidity()) return;
    if (informational) { close(); return; }
    const values = {};
    for (const f of fields) {
      const node = form.elements.namedItem(f.name);
      let value = f.type === "checkbox" ? node.checked : node.value;
      if (f.type === "money") {
        if (!/^\d+(\.\d{1,2})?$/.test(value)) {
          $("#modal-error").innerHTML = errorBox(
            new Error(
              T("金额最多保留两位小数", "Use at most two decimal places"),
            ),
          );
          return;
        }
        const parts = value.split(".");
        value = Number(
          BigInt(parts[0]) * 100n + BigInt((parts[1] || "").padEnd(2, "0")),
        );
      } else if (f.type === "number") value = value === "" ? 0 : Number(value);
      values[f.name] = value;
    }
    const save = $("#modal-submit");
    const controls = [...form.elements, $(".modal-close")].map((node) => [node, node.disabled]);
    const saveLabel = save.innerHTML;
    pending = true;
    controls.forEach(([node]) => (node.disabled = true));
    save.textContent = T("正在保存…", "Saving…");
    form.setAttribute("aria-busy", "true");
    $("#modal-error").innerHTML = "";
    try {
      const result = await onSubmit(values);
      pending = false;
      close();
      if(successMessage) toast(successMessage);
      if(onSuccess) await onSuccess(result); else await refresh();
    } catch (err) {
      if(form.isConnected){$("#modal-error").innerHTML = errorBox(err);$("#modal-error").scrollIntoView({ block: "nearest" });}
      else toast(err.message);
    } finally {
      pending = false;
      if (form.isConnected) {
        controls.forEach(([node, disabled]) => (node.disabled = disabled));
        save.innerHTML = saveLabel;
        form.removeAttribute("aria-busy");
      }
    }
  };
  onReady?.(close);
  requestAnimationFrame(() => {
    if(activeDialogClose!==close)return;
    const first=[...modalRoot.querySelectorAll('.modal-body input,.modal-body select,.modal-body textarea,.modal-body button')].find(n=>!n.disabled&&n.getClientRects().length&&n.type!=='hidden');
    (first||$("#modal-title"))?.focus({preventScroll:true});
  });
  return close;
}
const clinicField = () => ({
  name: "clinic_id",
  label: T("诊所", "Clinic"),
  type: "select",
  options: opts(state.boot.clinics),
  value: selectedClinic(),
});
const patientField = async () => {
  const d = await api("/patients" + query());
  return {
    name: "patient_id",
    label: T(
      "患者（可先在患者中心按姓名检索）",
      "Patient (search Patient 360 first if needed)",
    ),
    type: "select",
    options: d.items.map((p) => ({
      value: p.id,
      label: p.patient_code + " · " + p.name_zh,
    })),
  };
};
const treatmentField = () => ({
  name: "treatment_id",
  label: T("治疗项目", "Treatment"),
  type: "select",
  options: state.boot.treatments.filter((t) => t.status === "ACTIVE").map(t=>({value:t.id,label:`${t.name_zh} · ${t.code} · v${t.version} · ${t.effective_from} – ${t.effective_to||T('长期','open-ended')}`})),
});
const dentistField = () => ({
  name: "dentist_id",
  label: T("牙医", "Dentist"),
  type: "select",
  options: opts(
    state.boot.dentists.filter((d) => d.employment_status === "ACTIVE"),
  ),
});
const chairField = () => ({
  name: "chair_id",
  label: T("牙椅（允许暂不指定）", "Chair (optional)"),
  type: "select",
  required: false,
  options: state.boot.chairs
    .filter((c) => c.status === "AVAILABLE")
    .map((c) => ({
      value: c.id,
      label:
        (state.boot.clinics.find((x) => x.id === c.clinic_id)?.name_zh || "") +
        " · " +
        c.name_zh,
    })),
});
const reasonField = () => ({
  name: "reason",
  label: T("原因与依据", "Reason and evidence"),
  type: "textarea",
});
const roleHomes = {
  JDBC_DENTIST: "clinical",
  JDBC_PATIENT: "portal",
  JDBC_FRONT_DESK: "reception",
  JDBC_CASHIER: "billing",
  JDBC_CLINIC_MANAGER: "dashboard",
  JDBC_HQ_OPERATIONS: "dashboard",
  JDBC_HQ_FINANCE: "periods",
  JDBC_ADMIN: "access",
  JDBC_REVIEWER: "dashboard",
};
function home() {
  for (const r of state.principal?.roles || [])
    if (roleHomes[r.code]) return roleHomes[r.code];
  return can("portal.read")
    ? "portal"
    : can("dashboard.read")
      ? "dashboard"
      : "security";
}
const navItems = [
  [
    "dashboard",
    "dashboard",
    () => T("工作台", "Overview"),
    "dashboard.read",
    "WORKSPACE",
  ],
  ["reception","users",()=>T("门诊工作台","Daily clinic desk"),"appointment.read","CARE OPERATIONS"],
  [
    "appointments",
    "calendar",
    () => T("预约与到诊", "Scheduling"),
    "appointment.read",
    "",
  ],
  ["patients", "users", () => T("患者管理", "Patients"), "patient.read", ""],
  [
    "clinical",
    "tooth",
    () => T("临床工作台", "Clinical workspace"),
    "clinical.read",
    "",
  ],
  [
    "waitlist",
    "clock",
    () => T("候补与复诊", "Waitlist & recalls"),
    "appointment.read",
    "",
  ],
  [
    "resources",
    "building",
    () => T("组织与资源", "Network resources"),
    "clinic.read",
    "NETWORK",
  ],
  [
    "billing",
    "receipt",
    () => T("诊疗结算", "Billing"),
    "finance.read",
    "FINANCE & INSIGHT",
  ],
  [
    "periods",
    "wallet",
    () => T("期间核算", "Financial close"),
    "finance.read",
    "",
  ],
  [
    "analytics",
    "chart",
    () => T("经营统计", "Business analytics"),
    "analytics.read",
    "",
  ],
  [
    "expansion",
    "location",
    () => T("扩张测算", "Network planning"),
    "analytics.read",
    "",
  ],
  ["portal", "heart", () => T("我的诊疗", "My care"), "portal.read", "PATIENT"],
  [
    "access",
    "shield",
    () => T("账号与权限", "Access administration"),
    "access.manage",
    "GOVERNANCE",
  ],
  ["audit", "file", () => T("操作审计", "Audit history"), "audit.read", ""],
  ["security", "lock", () => T("账号安全", "Account security"), null, ""],
];
const smallWorkspace = matchMedia("(max-width:760px)");
function setSidebar(open = false, focus = false) {
  const side = $(".sidebar"), toggle = $(".mobile-nav");
  if (!side || !toggle) return;
  open = smallWorkspace.matches && open;
  side.classList.toggle("open", open);
  side.inert = smallWorkspace.matches && !open;
  $(".sidebar-backdrop").hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
  toggle.setAttribute("aria-label",open?T("收起导航","Close navigation"):T("展开导航","Open navigation"));
  document.body.classList.toggle("drawer-open", open);
  if(focus) (open ? side.querySelector('.nav-item') : toggle)?.focus();
}
smallWorkspace.addEventListener("change", () => setSidebar(false));
function shell(content = "", active = "") {
  const p = state.principal;
  let lastGroup = "";
  const nav = navItems
    .filter((n) => !n[3] || can(n[3]))
    .map((n) => {
      const group =
        n[4] && n[4] !== lastGroup
          ? `<div class="nav-label">${state.lang === "en" ? n[4] : ({WORKSPACE:"工作空间", "CARE OPERATIONS":"诊疗服务",NETWORK:"组织管理","FINANCE & INSIGHT":"经营管理",PATIENT:"患者服务",GOVERNANCE:"系统管理"})[n[4]] || n[4]}</div>`
          : "";
      if (n[4]) lastGroup = n[4];
      return (
        group +
        `<a class="nav-item ${active === n[0] ? "active" : ""}" ${active === n[0] ? 'aria-current="page"' : ''} href="#/${n[0]}">${icon(n[1])}<span>${n[2]()}</span></a>`
      );
    })
    .join("");
  const role = p.roles[0];
  const name =
    navItems.find((n) => n[0] === active)?.[2]() || T("工作区", "Workspace");
  const scope = p.network ? T("全网授权", "Network scope") : state.boot.clinics.map(c=>c.name_zh).join(" · ");
  app.innerHTML = `<div class="app-shell"><a class="workspace-skip" href="#page-content">${T("跳至工作内容", "Skip to content")}</a><button type="button" class="sidebar-backdrop" data-act="mobile-menu" aria-label="${T("关闭导航", "Close navigation")}" hidden></button><aside class="sidebar" aria-label="${T("工作区导航", "Workspace navigation")}"><a class="brand" href="#/${home()}"><img src="/mark.svg" width="35" height="35" alt=""><div><h2>ADC Nexus</h2><div class="sub">诊疗与运营管理</div></div></a><nav class="nav-list">${nav}</nav><div class="sidebar-foot"><div class="scope-card"><div class="eyebrow">${T("当前授权范围", "AUTHORIZED SCOPE")}</div><strong>${esc(scope || T("按本人绑定授权", "Personal scope"))}</strong><p>${T("每次操作均经服务端校验", "Every request is authorized")}</p></div><div class="user-card"><span class="avatar">${esc(p.name.slice(0, 1))}</span><div><strong>${esc(p.name)}</strong><small>${esc(state.lang === "en" ? role?.name_en : role?.name_zh) || T("机构成员", "Member")}</small></div><button class="btn ghost push" data-act="logout" aria-label="${T("退出登录", "Sign out")}">${icon("logout")}</button></div></div></aside><div class="workspace"><header class="topbar"><div class="breadcrumb"><button class="btn ghost mobile-nav" data-act="mobile-menu" aria-label="${T("展开导航", "Open navigation")}" aria-expanded="false">${icon("menu")}</button><span>${T("工作空间", "Workspace")}</span>${icon("chevron")}<strong>${name}</strong></div><div class="topbar-meta">${can("patient.read")?`<button type="button" class="patient-search" data-act="patient-search">${icon("users")}<span>${T("查找患者","Find patient")}</span></button>`:""}<button type="button" class="workspace-search" data-act="workspace-search" aria-label="${T("查找功能", "Find a page")}">${icon("search")}<span>${T("查找功能", "Find a page")}</span><kbd>Ctrl K</kbd></button><a class="workspace-home" href="#/home" aria-label="${T("返回网站首页", "Website home")}">${icon("globe")}<span>${T("网站首页", "Website")}</span></a><button class="btn ghost small" data-act="language" aria-label="${T("切换到英语", "Switch to Chinese")}">${state.lang === "en" ? "中文" : "EN"}</button></div></header><main class="workspace-main animate-in" id="page-content" tabindex="-1">${content}</main></div></div>`;
  $(".workspace-skip").onclick = e => { e.preventDefault(); $("#page-content").focus(); };
  $(".patient-search")?.setAttribute("aria-label",T("查找患者","Find patient"));
  setSidebar(false);
  if (p.patient_id && p.roles.every((r) => r.code === "JDBC_PATIENT"))
    $(".scope-card strong").textContent = T(
      "仅限绑定本人",
      "Bound patient only",
    );
}
function foot() {
  return `<footer class="page-foot"><span>ADC Nexus · ${T("安德鲁牙科连锁运营管理系统", "Dental chain operations")}</span><span>${T("课程合成数据 · 不执行支付划转", "Synthetic course data · No payment processing")}</span></footer>`;
}
function filters({ range = false, search = false } = {}) {
  if (!range && !search && state.boot.clinics.length <= 1) return "";
  return `<form class="toolbar" id="filter-form">${state.boot.clinics.length > 1 ? `<select class="field-input" name="clinic_id" aria-label="${T("诊所筛选", "Clinic filter")}"><option value="">${T("所有授权诊所", "All authorized clinics")}</option>${state.boot.clinics.map((c) => `<option value="${esc(c.id)}" ${state.clinic === c.id ? "selected" : ""}>${esc(c.name_zh)}</option>`).join("")}</select>` : ""}${range ? `<input class="field-input" type="date" name="from" value="${esc(state.from)}" aria-label="From"><span class="muted">—</span><input class="field-input" type="date" name="to" value="${esc(state.to)}" aria-label="To">` : ""}${search ? `<div class="search-box">${icon("search")}<input name="q" class="field-input" value="${esc(state.search || "")}" placeholder="${T("姓名、患者编号或电话", "Name, patient code or phone")}"></div>` : ""}<button class="btn" type="submit">${T("应用筛选", "Apply")}</button></form>`;
}
function bindFilters() {
  const form = $("#filter-form");
  if (!form) return;
  form.onsubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    state.clinic = String(fd.get("clinic_id") ?? state.clinic);
    sessionStorage.setItem("adc-clinic", state.clinic);
    if (fd.has("from")) state.from = fd.get("from");
    if (fd.has("to")) state.to = fd.get("to");
    if (fd.has("q")) state.search = fd.get("q");
    refresh();
  };
}
let renderId = 0;
let cleanupPublic = () => {};
let workspaceRoute = "";
async function refresh() {
  if (!state.principal) return;
  if (location.hash.startsWith("#/home")) return publicPage();
  cleanupPublic();
  cleanupPublic = () => {};
  const rid = ++renderId;
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  let page = parts[0] || home(),
    id = parts[1];
  const routeKey = page + "/" + (id || "");
  if (workspaceRoute !== routeKey) { scrollTo({top:0, behavior:"instant"}); workspaceRoute = routeKey; }
  const nav = navItems.find((n) => n[0] === page);
  if (!nav || (nav[3] && !can(nav[3]))) {
    page = home();
    location.hash = "#/" + page;
    return;
  }
  shell(
    `<div class="loader"><span class="spinner"></span><p>${T("正在读取授权工作区…", "Loading your workspace…")}</p></div>`,
    page,
  );
  try {
    let content;
    switch (page) {
      case "dashboard":
        content = await overviewPage();
        break;
      case "patients":
        content = id ? await patientPage(id) : await patientsPage();
        break;
      case "reception":
        content = await receptionPage();
        break;
      case "appointments":
        content = await appointmentsPage();
        break;
      case "clinical":
        content = id ? await visitPage(id) : await clinicalPage();
        break;
      case "waitlist":
        content = await waitlistPage();
        break;
      case "billing":
        content = id ? await invoicePage(id) : await billingPage();
        break;
      case "periods":
        content = await periodsPage();
        break;
      case "resources":
        content = await resourcesPage();
        break;
      case "analytics":
        content = await analyticsPage();
        break;
      case "expansion":
        content = await expansionPage();
        break;
      case "access":
        content = await accessPage();
        break;
      case "audit":
        content = await auditPage();
        break;
      case "portal":
        content = await portalPage();
        break;
      case "security":
        content = securityPage();
        break;
      default:
        content = empty();
    }
    if (rid !== renderId) return;
    $("#page-content").innerHTML = content + foot();
    bindFilters();
    bindLocal(page);
    document.title = `${navItems.find((n) => n[0] === page)?.[2]()} · ADC Nexus`;
  } catch (e) {
    if (rid !== renderId) return;
    if (e.status === 401) {
      state.principal = null;
      loginPage();
      return;
    }
    $("#page-content").innerHTML =
      errorBox(e) +
      `<div style="margin-top:18px">${button(T("重新读取", "Retry"), "refresh")}</div>`;
  }
}
async function loginPage() {
  const rid = ++renderId;
  document.body.classList.remove("drawer-open");
  cleanupPublic();
  cleanupPublic = () => {};
  state.config = state.config || (await api("/auth/config"));
  if (rid !== renderId) return;
  cleanupPublic = renderAuthPage({ app, config: state.config, api, enter, esc, errorBox, modal });
  scrollTo({top:0, behavior:"instant"});
}
async function publicPage() {
  const rid = ++renderId;
  document.body.classList.remove("drawer-open");
  state.config = state.config || (await api("/auth/config"));
  if (rid !== renderId) return;
  cleanupPublic();
  cleanupPublic = renderHomepage({app, esc, icon, config:state.config,
    workspaceHref:state.principal ? "#/" + home() : null,
    onDemo:async () => { await api("/auth/demo", {role:"REVIEWER"}); await enter(); }
  });
}
async function route() {
  const page = location.hash.replace(/^#\/?/, "").split("/")[0];
  if (!page || page === "home") return publicPage();
  if (state.principal) return refresh();
  return loginPage();
}
async function enter(preserveRoute = false) {
  const session = await api("/auth/session");
  state.principal = session.principal;
  state.csrf = session.csrf;
  state.boot = await api("/bootstrap");
  if(!preserveRoute){state.scheduleDentist='';state.scheduleStatus='';state.scheduleSearch='';state.serviceDate='';state.view='calendar';state.calendarGroup='dentist';state.deskView='';state.deskDoctor='';state.deskSearch='';state.billView='';state.billSearch='';state.careTab='';state.careVisit='';state.careQueue='ACTIVE';state.careSearch='';}
  state.to = state.boot.today;
  state.from = new Date(
    new Date(state.to + "T12:00:00Z").getTime() - 90 * 86400000,
  )
    .toISOString()
    .slice(0, 10);
  if (state.clinic && !state.boot.clinics.some((c) => c.id === state.clinic)) {
    state.clinic = "";
    sessionStorage.removeItem("adc-clinic");
  }
  if (!preserveRoute || !location.hash || location.hash === "#")
    history.replaceState(null, "", "#/" + home());
  await refresh();
}
const handlers = {
  refresh: () => refresh(),
  "mobile-menu": () => setSidebar(!$(".sidebar").classList.contains("open"), true),
  language: () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    localStorage.setItem("adc-language", state.lang);
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    state.principal ? refresh() : loginPage();
  },
  "demo-login": async (id) => {
    const d = await api("/auth/demo", { role: id });
    state.csrf = d.csrf;
    await enter();
  },
  logout: async () => {
    await api("/auth/logout", {});
    state.principal = null;
    state.boot = null;
    state.staffInvitation = null;
    state.staff = null;
    state.access = null;
    history.replaceState(null, "", "#/login");
    await loginPage();
  },
};
document.addEventListener("click", async (e) => {
  const target = e.target.closest("[data-act]");
  if (!target) return;
  const handler = handlers[target.dataset.act];
  if (!handler) return;
  try {
    await handler(target.dataset.id, target);
  } catch (error) {
    toast(error.message);
  }
});
window.addEventListener("hashchange", () => route().catch(e => { app.innerHTML = `<div class="initial-load">${errorBox(e)}${button("重新连接", "reload")}</div>`; }));
window.addEventListener("beforeunload", (e) => {
  if ($("#dialog-form")) {
    e.preventDefault();
    e.returnValue = "";
  }
});
async function start() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  if (!location.hash || location.hash === "#") history.replaceState(null, "", "#/home");
  try {
    await enter(true);
  } catch (e) {
    if (e.status === 401) await route();
    else {
      app.innerHTML = `<div class="initial-load"><h1>ADC Nexus</h1>${errorBox(e)}${button(T("重试连接", "Retry connection"), "reload")}</div>`;
    }
  }
}
handlers.reload = () => location.reload();
handlers["workspace-search"] = () => {
  if (!state.principal || $("#dialog-form")) return;
  const available = navItems.filter(n => !n[3] || can(n[3]));
  modal({name:T("查找工作区功能", "Find a workspace page"), description:T("仅查找您有权访问的功能，不搜索患者资料。", "Only your authorized pages are listed; no patient data is searched."), informational:true, submit:T("关闭", "Close"),
    body:`<label class="field-label" for="workspace-query">${T("功能名称", "Page name")}</label><input id="workspace-query" class="field-input" type="search" autocomplete="off" placeholder="${T("例如：预约、病历、结算", "Scheduling, care, billing…")}"><div class="command-results"></div>`,
    onReady:close => {
      const input = $("#workspace-query"), results = $(".command-results");
      const paint = () => {
        const needle = input.value.trim().toLowerCase();
        const found = available.filter(n => (n[2]() + " " + n[0]).toLowerCase().includes(needle));
        results.innerHTML = found.length ? found.map(n=>`<a href="#/${n[0]}" class="command-result">${icon(n[1])}<span>${esc(n[2]())}</span>${icon("chevron")}</a>`).join("") : `<p class="muted">${T("没有匹配的已授权功能", "No matching authorized page")}</p>`;
        results.querySelectorAll('a').forEach(a=>a.onclick=close);
      };
      input.oninput = paint;
      input.onkeydown = e => { if(e.key === "Enter"){e.preventDefault(); results.querySelector('a')?.click();} if(e.key === "ArrowDown"){e.preventDefault();results.querySelector('a')?.focus();} };
      paint(); input.focus();
    }
  });
};
document.addEventListener("keydown", e => {
  if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k" && state.principal && $(".app-shell")){ e.preventDefault(); if(!activeDialogClose) handlers["workspace-search"](); }
  if(e.key === "Escape" && $(".sidebar.open")) handlers["mobile-menu"]();
  if(e.key === "Tab" && $(".sidebar.open")) {
    const focusable = [...$(".sidebar").querySelectorAll('a,button')].filter(n=>!n.disabled);
    if(e.shiftKey && document.activeElement===focusable[0]){e.preventDefault();focusable.at(-1)?.focus();}
    if(!e.shiftKey && document.activeElement===focusable.at(-1)){e.preventDefault();focusable[0]?.focus();}
  }
});

async function overviewPage() {
  const d = await api("/dashboard" + query({ from: state.from, to: state.to }));
  state.dashboard = d;
  const total = d.appointment_states.reduce((n, r) => n + Number(r.value), 0),
    completed = Number(
      d.appointment_states.find((r) => r.status === "COMPLETED")?.value || 0,
    );
  const charts = d.daily.slice(-22),
    max = Math.max(1, ...charts.map((x) => Number(x.total)));
  const role = state.principal.roles[0]?.name_zh || "";
  const chart = charts.length
    ? `<div class="card-pad"><div class="chart">${charts.map((r, i) => `<div class="chart-column" title="${esc(r.day)}: ${r.total}"><span class="num">${num(r.total)}</span><div class="chart-bar ${i === charts.length - 1 ? "strong" : ""}" style="height:${Math.max(3, (Number(r.total) / max) * 140)}px"></div><small>${esc(r.day.slice(5))}</small></div>`).join("")}</div><div class="legend"><span><i class="key"></i>${T("计划服务日预约数", "Appointments by scheduled date")}</span><span>${T("最近 22 个有业务记录的日期", "Last 22 dates with records")}</span></div></div>`
    : empty();
  const agenda = orderedAgenda(d.today_agenda)
    .map(
      (a) =>
        `<div class="list-row"><div class="time-box num">${esc(a.scheduled_start_at.slice(11, 16))}</div><div class="list-main"><strong>${esc(a.patient_name)}</strong><small>${esc(a.treatment_name)} · ${esc(a.dentist_name)}</small></div>${badge(a.status)}</div>`,
    )
    .join("");
  return (
    title(
      "NETWORK COMMAND CENTER",
      T("运营工作台", "Operations overview"),
      T(
        "按授权诊所和服务日期查看预约、到诊及经营统计。",
        "Review appointments, arrivals and operating figures by authorized clinic and service date.",
      ),
    ) +
    `<div class="hero-strip"><div><h2>${T("你好，", "Hello, ")}${esc(state.principal.name)}</h2><p>${esc(role)} · ${T("数据范围", "Data range")} ${esc(state.from)} — ${esc(state.to)} · ${T("更新于", "Updated")} ${date(d.generated_at)}</p></div><div class="hero-emblem">${icon("leaf")}</div></div>` +
    filters({ range: true }) +
    `<div class="metric-grid gap">${metric(T("授权患者", "Patients in scope"), num(d.patient_count), T("当前可查看的患者档案", "Patient records within your scope"), "users", true)}${metric(T("期间预约", "Appointments"), num(total), T("按计划服务日统计", "By scheduled service date"), "calendar")}${metric(T("完成预约", "Completed visits"), num(completed), T("所选期间已完成的预约", "Completed in the selected period"), "check")}${d.finance ? metric(T("期间净收款", "Net cash received"), money(d.finance.net_cash_fen), T("收款 − 退款；非核定利润", "Receipts less refunds, not approved profit"), "wallet") : metric(T("授权诊所", "Authorized clinics"), num(d.clinics.length), T("范围由机构授权确定", "Access is assigned by the organization"), "building")}</div><div class="wide-main gap"><div class="stack">${panel(T("预约量趋势", "Appointment volume"), chart, "", T("授权范围内的预约业务量", "Appointment activity within your authorized scope"))}${panel(
      T("诊所运营概览", "Clinic operations"),
      table(
        [
          T("诊所", "Clinic"),
          T("城市", "City"),
          T("预约数", "Appointments"),
          T("完成就诊", "Completed visits"),
          T("牙椅", "Chairs"),
        ],
        d.clinics.map((c) => [
          `<div class="name">${esc(c.name_zh)}</div><div class="second mono">${esc(c.code)}</div>`,
          esc(c.city_zh),
          num(c.appointments),
          num(c.completed),
          num(c.chair_capacity),
        ]),
      ),
    )}</div><div class="stack">${panel(T("今日日程", "Today’s agenda"), `<div class="card-pad">${agenda || empty(T("今日暂无安排", "No appointments today"))}</div>`, can("appointment.read") ? `<a class="btn ghost small" href="#/appointments" aria-label="${T("查看预约日程","Open appointment schedule")}">${icon("arrow")}</a>` : "")}${panel(T("预约状态分布", "Appointment status"), `<div class="card-pad">${d.appointment_states.map((r) => `<div class="list-row">${badge(r.status)}<strong class="push num">${num(r.value)}</strong></div>`).join("") || empty()}</div>`)}<div class="callout">${T("预约按计划服务日统计，净收款按收退款发生日统计。核定利润与基金以期间核算结果为准。", "Appointments follow service dates; net cash follows receipt and refund dates. Approved profit and funds follow the financial close.")}</div></div></div>`
  );
}
async function patientsPage() {
  const d = await api("/patients" + query({ q: state.search || "" }));
  state.patientList = d.items;
  return (
    title(
      "PATIENT 360",
      T("患者管理", "Patient management"),
      T(
        "检索授权范围内的患者档案，核实联系方式、风险与既往就诊。",
        "Find a stable patient identity and review care, contact and risk information.",
      ),
      can("patient.manage")
        ? button(
            T("建立患者档案", "New patient"),
            "new-patient",
            "",
            "primary",
            "plus",
          )
        : "",
    ) +
    filters({ search: true }) +
    panel(
      T("患者主档", "Patient register"),
      table(
        [
          T("患者", "Patient"),
          T("联系电话", "Phone"),
          T("所属诊所", "Primary clinic"),
          T("风险提示", "Risk"),
          T("最近更新", "Updated"),
          "",
        ],
        d.items.map((p) => [
          `<div class="name">${link(p.name_zh, "patients/" + p.id)}</div><div class="second mono">${esc(p.patient_code)}</div>`,
          esc(p.phone),
          esc(p.clinic_name),
          p.allergy_count == null
            ? `<span class="muted">${T("按岗位隐藏临床信息", "Clinical information restricted")}</span>`
            : Number(p.allergy_count) > 0
              ? `<span class="badge amber">${p.allergy_count} ${T("条过敏提示", "allergy records")}</span>`
              : `<span class="muted">${T("未见已登记过敏", "No recorded allergies")}</span>`,
          date(p.updated_at),
          `<a class="btn ghost small" href="#/patients/${esc(p.id)}">${icon("arrow")}</a>`,
        ]),
      ),
      `<span class="badge">${num(d.total)} ${T("位患者", "patients")}</span>`,
    ) +
    `<p class="subline" style="margin-top:12px">${T("每次最多显示 60 位患者；请用姓名、编号或电话缩小范围。未登记过敏不等于无已知过敏。", "Up to 60 patients per search. Use a name, code or phone to narrow results. An empty register does not mean no known allergies.")}</p>`
  );
}
async function patientPage(id) {
  const d = await api("/patients/" + encodeURIComponent(id));
  state.patientDetail = d;
  const p = d.patient;
  if (!d.clinical_details_available)
    return (
      title("PATIENT IDENTITY", p.name_zh, p.patient_code) +
      `<div class="callout gap">${T("当前岗位仅展示身份与服务安排。过敏、病史、联系人及临床时间线已按权限隐藏；这不表示没有风险记录。", "This role can view identity and service arrangements only. Clinical and contact information is withheld, not absent.")}</div>` +
      panel(
        T("身份摘要", "Identity summary"),
        `<div class="card-pad kv-grid"><div class="kv"><small>${T("患者编号", "Patient code")}</small><strong>${esc(p.patient_code)}</strong></div><div class="kv"><small>${T("联系电话（掩码）", "Masked phone")}</small><strong>${esc(p.phone)}</strong></div></div>`,
      ) +
      `<div class="gap">${panel(T("服务安排", "Service arrangements"), appointmentTable(d.appointments))}</div>`
    );
  const actions = can("patient.manage")
    ? button(T("更新资料", "Edit profile"), "edit-patient", id, "", "users") +
      button(
        T("记录病史声明", "History update"),
        "patient-history",
        id,
        "primary",
        "plus",
      )
    : "";
  return (
    title(
      "PATIENT RECORD",
      p.name_zh,
      `${p.patient_code} · ${T("患者档案与跨次照护信息", "Patient identity and longitudinal care")}`,
      actions,
    ) +
    `<div class="grid2 gap">${panel(
      T("基本资料", "Identity"),
      `<div class="card-pad kv-grid">${[
        [T("患者编号", "Patient code"), p.patient_code],
        [T("出生日期", "Date of birth"), p.date_of_birth],
        [T("联系电话", "Phone"), p.phone],
        [T("邮箱", "Email"), p.email || "—"],
        [T("状态", "Status"), p.status],
        [T("最近就诊", "Last visit"), p.last_visit_at || "—"],
      ]
        .map(
          ([k, v]) =>
            `<div class="kv"><small>${k}</small><strong>${esc(v)}</strong></div>`,
        )
        .join("")}</div>`,
    )}${panel(T("过敏与风险", "Allergies and risk"), `<div class="card-pad">${d.allergies.map((a) => `<div class="list-row"><div class="tone-box amber">${icon("shield")}</div><div class="list-main"><strong>${esc(a.substance_zh || a.substance_en)}</strong><small>${esc(a.reaction_zh || a.reaction_en)}</small></div>${badge(a.severity)}</div>`).join("") || empty(T("尚未登记过敏资料；请在诊疗前核实。", "No allergy history recorded. Verify before care."))}</div>`, can("patient.manage") ? button(T("追加", "Add"), "patient-allergy", id, "small", "plus") : "")}</div><div class="grid2 gap">${panel(T("病史声明版本", "History versions"), `<div class="card-pad">${d.history.map((h) => `<div class="timeline-item"><strong>v${h.version_number} · ${esc(h.history_status)}</strong><p>${esc(h.history_text || T("尚未提供病史信息", "History not provided"))}</p><p>${date(h.created_at)} · ${esc(h.reason)}</p></div>`).join("") || empty(T("尚无版本记录", "No version records"))}</div>`)}${panel(T("紧急联系人", "Emergency contacts"), `<div class="card-pad">${d.contacts.map((c) => `<div class="list-row"><div class="list-main"><strong>${esc(c.contact_name)}</strong><small>${esc(c.relationship_zh)} · ${esc(c.phone)}</small></div></div>`).join("") || empty()}</div>`, can("patient.manage") ? button(T("追加", "Add"), "patient-contact", id, "small", "plus") : "")}</div>${panel(
      T("预约与服务记录", "Appointments and services"),
      table(
        [
          T("服务时间", "Scheduled service"),
          T("诊所", "Clinic"),
          T("牙医与项目", "Dentist & treatment"),
          T("状态", "Status"),
        ],
        d.appointments.map((a) => [
          date(a.scheduled_start_at),
          esc(a.clinic_name),
          `${esc(a.dentist_name)}<div class="second">${esc(a.treatment_name)}</div>`,
          badge(a.status),
        ]),
      ),
    )}<div class="grid2" style="margin-top:22px">${panel(T("照护时间线", "Care timeline"), `<div class="card-pad timeline">${d.timeline.map((e) => `<div class="timeline-item"><strong>${esc(e.title_zh)}</strong><p>${date(e.occurred_at)} · ${esc(e.description_zh)}</p></div>`).join("") || empty()}</div>`)}${panel(T("资料共享同意", "Data sharing consent"), `<div class="card-pad">${d.consents.map((c) => `<div class="list-row"><div class="list-main"><strong>${esc(c.consent_type)}</strong><small>${date(c.captured_at)} · ${esc(c.policy_version)}</small></div>${badge(c.status)}</div>`).join("") || empty()}<p class="subline">${T("通用资料同意不替代具体治疗的知情同意。", "Data-sharing consent does not replace treatment-specific consent.")}</p></div>`, can("patient.manage") ? button(T("追加决定", "Record decision"), "privacy-consent", id, "small") : "")}</div>`
  );
}
async function receptionPage(){
  const day=state.serviceDate||state.boot.today;
  const rows=await api("/appointments"+query({from:day,to:day}));
  const recent=rows.length?null:(await api("/appointments"+query()))[0];
  return receptionContent({rows,day,clinic:state.clinic,clinics:state.boot.clinics,selection:state.deskView,canManage:can("appointment.manage"),search:state.deskSearch,doctor:state.deskDoctor,recentDate:recent?.scheduled_start_at?.slice(0,10)},{esc,T,button,badge,table,link});
}
async function appointmentsPage() {
  const day = state.serviceDate || state.boot.today;
  const to =
    state.view === "week"
      ? new Date(new Date(day + "T12:00:00").getTime() + 6 * 86400000)
          .toISOString()
          .slice(0, 10)
      : day;
  const all = await api("/appointments" + query({ from: day, to }));
  const list = filterAppointments(all,{dentist:state.scheduleDentist,status:state.scheduleStatus,search:state.scheduleSearch});
  state.appointments = list;
  const resources=await api('/resources');
  const calendar=state.view==='calendar'?(state.scheduleStatus&&['CANCELLED','NO_SHOW'].includes(state.scheduleStatus)?`<div class="calendar-footnote">${T('取消与未到诊不占用日程时段，完整记录如下。','Cancelled/no-show records do not occupy the timeline and are listed below.')}</div>`+appointmentTable(list):renderCalendar(buildCalendarModel(list,{day,group:state.calendarGroup,resources,clinic:state.clinic,dentist:state.scheduleDentist}),{esc,T,badge})):'';
  const doctorOptions=(state.boot.dentists||[]).filter(d=>all.some(a=>a.dentist_id===d.id)||resources.assignments.some(a=>a.dentist_id===d.id&&a.status==='ACTIVE'&&(!state.clinic||a.clinic_id===state.clinic)&&a.effective_from<=to&&(!a.effective_to||a.effective_to>=day)));
  const appointmentStatuses=['CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW'];
  const controls=`<div class="schedule-date-nav">${button(T('前一天','Previous day'),'schedule-day','-1','small')}${button(T('今天','Today'),'schedule-day','today','small')}${button(T('后一天','Next day'),'schedule-day','1','small')}<strong>${esc(day)}</strong><span>${T('诊所本地时间','Clinic local time')}</span></div><form class="toolbar schedule-controls" id="schedule-filter">${state.boot.clinics.length>1?`<select name="clinic_id" class="field-input" aria-label="${T('诊所','Clinic')}"><option value="">${T('所有授权诊所','All authorized clinics')}</option>${state.boot.clinics.map(c=>`<option value="${esc(c.id)}" ${c.id===state.clinic?'selected':''}>${esc(c.name_zh)}</option>`).join('')}</select>`:''}<input class="field-input" type="date" name="service_date" value="${esc(day)}" aria-label="Service date"><select name="dentist_id" class="field-input" aria-label="${T('医师筛选','Dentist filter')}"><option value="">${T('全部医师','All dentists')}</option>${doctorOptions.map(d=>`<option value="${esc(d.id)}" ${d.id===state.scheduleDentist?'selected':''}>${esc(d.name_zh)}</option>`).join('')}</select><select name="status" class="field-input" aria-label="${T('预约状态','Appointment status')}"><option value="">${T('全部状态','All statuses')}</option>${appointmentStatuses.map(s=>`<option value="${s}" ${s===state.scheduleStatus?'selected':''}>${state.lang==='en'?statusMap[s][1]:statusMap[s][0]}</option>`).join('')}</select><input class="field-input schedule-keyword" name="search" value="${esc(state.scheduleSearch)}" placeholder="${T('患者姓名 / 预约编号 / 项目','Patient / appointment / treatment')}" aria-label="${T('预约检索','Appointment search')}"><button type="submit" class="btn">${T('查询','Apply')}</button>${button(T('重置','Reset'),'schedule-reset','','small')}</form><div class="schedule-viewbar"><div class="row">${[['calendar',T('时间表','Timeline')],['board',T('状态看板','Status board')],['list',T('日列表','Day list')],['week',T('周列表','Week list')]].map(([id,name])=>button(name,'schedule-view',id,'small '+(state.view===id?'on':''))).join('')}</div>${state.view==='calendar'?`<div class="row"><span>${T('按','Group by')}</span>${button(T('医师','Dentist'),'schedule-group','dentist','small '+(state.calendarGroup==='dentist'?'on':''))}${button(T('牙椅','Chair'),'schedule-group','chair','small '+(state.calendarGroup==='chair'?'on':''))}</div>`:''}<span class="subline">${T('当前筛选','Filtered')}: ${list.length} / ${all.length}${all.length===600?T(' · 已达查询上限，请缩小范围',' · Query limit reached; narrow the scope'):''}</span></div>`;
  const cols = [
    ["CONFIRMED", T("已确认 · 待到诊", "Confirmed")],
    ["CHECKED_IN", T("已到诊 · 待接诊", "Checked in")],
    ["IN_PROGRESS", T("诊疗中", "In progress")],
    ["COMPLETED", T("已完成", "Completed")],
  ];
  const recent = list.length ? null : (await api("/appointments" + query()))[0];
  const board =
    (!list.length
      ? `<div class="callout gap row between"><span>${T("所选日期暂无预约。可安排新预约，或查阅已有服务记录；历史记录不会伪装成今日业务。", "No appointments on this date. Schedule care or review existing records; historical data stays on its actual service date.")}</span>${recent ? button(T("查看最近有记录的日期", "View latest recorded date"), "schedule-reference", recent.scheduled_start_at.slice(0, 10), "small") : ""}</div>`
      : "") +
    `<div class="schedule-board">${cols
      .map(([status, name]) => {
        const rows = list.filter((a) => a.status === status);
        return `<section class="schedule-column"><h3>${name}<span>${rows.length}</span></h3>${
          rows
            .slice(0, 12)
            .map(
              (a) =>
                `<article class="schedule-item" data-act="appointment-detail" data-id="${esc(a.id)}" tabindex="0"><div class="schedule-time num">${esc(a.scheduled_start_at.slice(11, 16))} — ${esc(a.scheduled_end_at.slice(11, 16))}</div><strong>${esc(a.patient_name)}</strong><small>${esc(a.treatment_name)}</small><small>${esc(a.dentist_name)} · ${esc(a.chair_name || T("未指定牙椅", "Chair unassigned"))}</small></article>`,
            )
            .join("") || `<p class="subline">${T("暂无", "None")}</p>`
        }${rows.length > 12 ? `<p class="subline">+ ${rows.length - 12} ${T("条，请切换列表", "more; switch to list")}</p>` : ""}</section>`;
      })
      .join("")}</div>`;
  return (
    title(
      "SMART SCHEDULING",
      T("预约日程", "Appointment schedule"),
      T(
        "查看患者到诊、医师接诊与牙椅安排。选中预约查看详情；新建或改期时核验资源。",
        "Review arrivals, clinicians and chair assignments. Select an appointment for details; scheduling validates resources.",
      ),
      can("appointment.manage")
        ? button(
            T("安排预约", "New appointment"),
            "new-appointment",
            "",
            "primary",
            "plus",
          )
        : "",
    ) +
    controls + `<div class="schedule-summary">${[['CONFIRMED',T('待到诊','Expected')],['CHECKED_IN',T('待接诊','Waiting')],['IN_PROGRESS',T('诊疗中','In progress')],['COMPLETED',T('已完成','Completed')]].map(([s,label])=>`<button type="button" data-act="schedule-status" data-id="${s}"><span>${label}</span><strong>${list.filter(a=>a.status===s).length}</strong></button>`).join('')}<div><span>${T('未分配牙椅','Chair unassigned')}</span><strong>${list.filter(a=>!a.chair_id&&!['CANCELLED','NO_SHOW','COMPLETED'].includes(a.status)).length}</strong></div><div><span>${T('取消 / 未到诊','Cancelled / no-show')}</span><strong>${list.filter(a=>['CANCELLED','NO_SHOW'].includes(a.status)).length}</strong></div></div>${!all.length&&state.view!=='board'?board.split('<div class="schedule-board">')[0]:''}${state.view==='calendar'?panel(T('预约时间表','Appointment timeline'),calendar):state.view === 'board' ? board : panel(T('服务日程','Service agenda'),appointmentTable([...list].sort((a,b)=>a.scheduled_start_at.localeCompare(b.scheduled_start_at))))}`
  );
}
function appointmentTable(list) {
  return table(
    [
      T("时间", "Time"),
      T("患者", "Patient"),
      T("诊所 / 牙椅", "Clinic / chair"),
      T("牙医 / 项目", "Dentist / treatment"),
      T("状态", "Status"),
      "",
    ],
    list.map((a) => [
      date(a.scheduled_start_at),
      `<span class="name">${esc(a.patient_name)}</span><div class="second mono">${esc(a.appointment_code)}</div>`,
      esc(a.clinic_name) +
        `<div class="second">${esc(a.chair_name || T("未指定", "Unassigned"))}</div>`,
      esc(a.dentist_name) +
        `<div class="second">${esc(a.treatment_name)}</div>`,
      badge(a.status),
      button(T("查看", "Details"), "appointment-detail", a.id, "small"),
    ]),
  );
}
async function clinicalPage() {
  let all=await api("/visits"+query());
  if(state.clinic)all=all.filter(v=>v.clinic_id===state.clinic);
  if(state.principal.dentist_id)all=all.filter(v=>v.dentist_id===state.principal.dentist_id);
  state.visits=all;
  const selected=state.careQueue||"ACTIVE",q=(state.careSearch||"").trim().toLocaleLowerCase();
  const active=v=>!["COMPLETED","CANCELLED"].includes(v.status);
  const list=all.filter(v=>(selected==="ALL"||(selected==="ACTIVE"?active(v):v.status===selected))&&(!q||[v.patient_name,v.patient_code,v.visit_code].some(s=>String(s||"").toLocaleLowerCase().includes(q)))).sort((a,b)=>String(a.scheduled_start_at).localeCompare(String(b.scheduled_start_at)));
  return title("CLINICAL CARE",T("临床接诊","Clinical care"),T("按预约服务时间查看接诊记录。旧记录保留原日期，不计作今日就诊；进入本次就诊后核实风险并补齐记录。","Review care by scheduled service time. Historical records keep their actual date. Open a visit to review safety and record treatment."))+filters()+
    '<section class="desk-register"><div class="worklist-tabs">'+[["ACTIVE",T("未完成","Active")],["SAFETY_REVIEW",T("待安全复核","Safety review")],["WAITING",T("待接诊","Waiting")],["IN_PROGRESS",T("诊疗中","In care")],["COMPLETED",T("已完成","Completed")],["ALL",T("全部记录","All records")]].map(([id,label])=>`<button type="button" data-act="care-queue" data-id="${id}" class="${selected===id?"selected":""}" aria-pressed="${selected===id}">${label}<span>${all.filter(v=>id==="ALL"||(id==="ACTIVE"?active(v):v.status===id)).length}</span></button>`).join("")+
    `</div><form id="care-search" class="worklist-search"><label for="care-keyword">${T("检索就诊","Find visit")}</label><input class="field-input" id="care-keyword" name="q" value="${esc(state.careSearch||"")}" placeholder="${T("患者姓名 / 患者或就诊编号","Patient name / code / visit")}"><button class="btn" type="submit">${T("检索","Search")}</button><span>${list.length} ${T("条记录","records")}</span></form>`+
    table([T("服务时间","Service time"),T("患者","Patient"),T("负责医师 / 诊所","Clinician / clinic"),T("风险复核","Safety review"),T("就诊状态","Visit status"),""],list.map(v=>[date(v.scheduled_start_at),`<strong>${esc(v.patient_name)}</strong><div class="second">${esc(v.patient_code)} · ${esc(v.visit_code)}</div>`,esc(v.dentist_name)+`<div class="second">${esc(v.clinic_name)}</div>`,badge(v.safety_gate_status),badge(v.status),`<a class="btn small" href="#/clinical/${esc(v.id)}">${T("打开就诊","Open visit")}</a>`]))+
    `<div class="worklist-footer">${T("记录状态不代替本次复核结果。完成条件在就诊内逐项列示，并在提交时由服务端重新核验。","Record status does not replace the current review. Completion checks are listed inside the visit and revalidated on submission.")}${all.length===300?T(" 已达查询上限，请缩小范围。"," Query limit reached; narrow scope."):""}</div></section>`;
}
async function visitPage(id) {
  const d=await api("/visits/"+encodeURIComponent(id));
  state.visitDetail=d;
  if(state.careVisit!==id){state.careVisit=id;state.careTab="";state.selectedTooth="";}
  const writable=can("clinical.write")&&(!state.principal.dentist_id||state.principal.dentist_id===d.visit.dentist_id);
  return (can('followup.recommend')&&writable&&d.visit.status!=='CANCELLED'?`<div class="setup-care-actions">${button(T('提出复诊建议','Recommend recall'),'followup-recommend',id,'small')}</div>`:'')+renderCareWorkspace(d,{esc,T,badge,button,link,table,money,date,selectedTooth:state.selectedTooth,selectedTab:state.careTab,writable});
}
function bindLocal(page) {
  const followup=document.querySelector('#followup-filter');
  if(followup)followup.onsubmit=e=>{e.preventDefault();const f=new FormData(followup);state.followupSearch=String(f.get('search')||'');state.followupStatus=String(f.get('status'));state.followupDue=String(f.get('due'));refresh();};
  const care=$("#care-search");
  if(care)care.onsubmit=e=>{e.preventDefault();state.careSearch=String(new FormData(care).get("q")||"").trim();refresh();};
  if(page==="clinical") bindCareTabs($("#page-content"),tab=>{state.careTab=tab;});
  const desk=$("#desk-filter");
  if(desk)desk.onsubmit=e=>{e.preventDefault();const f=new FormData(desk);state.serviceDate=String(f.get("day"));state.clinic=String(f.get("clinic_id")??state.clinic);state.deskDoctor=String(f.get("doctor")||"");state.deskSearch=String(f.get("search")||"").trim();sessionStorage.setItem("adc-clinic",state.clinic);refresh();};
  const bill=$("#billing-search");
  if(bill)bill.onsubmit=e=>{e.preventDefault();state.billSearch=String(new FormData(bill).get("search")||"").trim();refresh();};
  if (page === "appointments")
    $("#schedule-filter").onsubmit = (e) => {
      e.preventDefault();
      const f = new FormData(e.currentTarget);
      state.serviceDate = f.get("service_date");
      state.clinic = String(f.get("clinic_id") ?? state.clinic);
      state.scheduleDentist=String(f.get('dentist_id')||'');
      state.scheduleStatus=String(f.get('status')||'');
      state.scheduleSearch=String(f.get('search')||'').trim();
      sessionStorage.setItem("adc-clinic", state.clinic);
      refresh();
    };
}
handlers["care-queue"]=v=>{state.careQueue=v;refresh();};
handlers["desk-day"]=v=>{state.serviceDate=v==="today"?state.boot.today:shiftDay(state.serviceDate||state.boot.today,Number(v));state.deskDoctor="";refresh();};
handlers["desk-reference"]=v=>{state.serviceDate=v;state.deskDoctor="";refresh();};
handlers["desk-view"]=v=>{state.deskView=v;refresh();};
handlers["desk-reset"]=()=>{state.deskView="";state.deskDoctor="";state.deskSearch="";refresh();};
handlers["desk-checkin"]=async id=>{state.appointmentDetail=await api("/appointments/"+encodeURIComponent(id));handlers["appointment-checkin"](id);};
handlers["billing-view"]=v=>{state.billView=v;refresh();};
handlers["billing-reset"]=()=>{state.billSearch="";state.billView="";refresh();};
handlers["patient-search"]=()=>modal({
  name:T("查找患者","Find a patient"),description:T("按姓名、患者编号或电话检索当前授权范围。","Search the authorized scope by name, patient code or phone."),
  fields:[{name:"q",label:T("患者姓名 / 编号 / 电话","Name / code / phone"),value:state.search||""}],
  submit:T("查看匹配档案","View matches"), successMessage:"",
  onSubmit:async b=>{state.search=b.q.trim();},
  onSuccess:async()=>{history.replaceState(null,"","#/patients");await refresh();}
});
handlers["schedule-view"] = (v) => {
  state.view = v;
  refresh();
};
handlers['schedule-day'] = v=>{state.serviceDate=v==='today'?state.boot.today:shiftDay(state.serviceDate||state.boot.today,Number(v));refresh();};
handlers['schedule-group'] = v=>{state.calendarGroup=v;refresh();};
handlers['schedule-status'] = v=>{state.scheduleStatus=state.scheduleStatus===v?'':v;refresh();};
handlers['schedule-reset'] = ()=>{state.scheduleDentist='';state.scheduleStatus='';state.scheduleSearch='';refresh();};
handlers["schedule-reference"] = (v) => {
  state.serviceDate = v;
  refresh();
};
handlers["tooth-select"] = (id, target) => {
  state.selectedTooth = id;
  document
    .querySelectorAll(".tooth")
    .forEach((t) => t.classList.toggle("selected", t.dataset.id === id));
};
handlers["new-patient"] = () =>
  modal({
    name: T("建立患者档案", "New patient"),
    description: T(
      "先检索既有身份，避免重复建档。",
      "Search existing identities before creating a record.",
    ),
    fields: [
      { name: "name_zh", label: T("姓名", "Full name") },
      {
        name: "name_en",
        label: T("英文姓名（可选）", "English name (optional)"),
        required: false,
      },
      {
        name: "date_of_birth",
        label: T("出生日期", "Date of birth"),
        type: "date",
      },
      {
        name: "gender",
        label: T("性别", "Gender"),
        type: "select",
        options: [
          { value: "FEMALE", label: T("女", "Female") },
          { value: "MALE", label: T("男", "Male") },
          { value: "UNKNOWN", label: T("未知 / 未提供", "Not provided") },
        ],
      },
      { name: "phone", label: T("联系电话", "Phone") },
      { ...clinicField(), name: "primary_clinic_id" },
      {
        name: "history_text",
        label: T(
          "病史声明（未提供请留空）",
          "History statement (leave blank if unknown)",
        ),
        type: "textarea",
        required: false,
      },
      {
        name: "duplicate_reviewed",
        label: T(
          "若提示相似档案，我已人工核对并确认不同患者",
          "If a duplicate warning appears, I have verified a distinct patient",
        ),
        type: "checkbox",
        required: false,
      },
      {
        name: "duplicate_reason",
        label: T(
          "相似身份区分依据（无提示可空）",
          "Evidence for a distinct identity (when warned)",
        ),
        type: "textarea",
        required: false,
      },
    ],
    onSubmit: (b) => api("/patients", b),
  });
handlers["edit-patient"] = () => {
  const p = state.patientDetail.patient;
  modal({
    name: T("更新患者资料", "Edit patient"),
    fields: [
      { name: "name_zh", label: T("姓名", "Name"), value: p.name_zh },
      {
        name: "name_en",
        label: T("英文姓名", "English name"),
        value: p.name_en,
        required: false,
      },
      {
        name: "date_of_birth",
        label: T("出生日期", "Date of birth"),
        type: "date",
        value: p.date_of_birth,
      },
      { name: "phone", label: T("联系电话", "Phone"), value: p.phone },
      {
        name: "email",
        label: T("邮箱", "Email"),
        value: p.email,
        type: "email",
        required: false,
      },
    ],
    onSubmit: (b) =>
      api("/patients/" + p.id, {
        ...b,
        action: "update",
        updated_at: p.updated_at,
      }),
  });
};
handlers["patient-history"] = (id) =>
  modal({
    name: T("追加病史声明版本", "History update"),
    fields: [
      {
        name: "history_status",
        label: T("患者声明状态", "Statement status"),
        type: "select",
        options: [
          {
            value: "UNKNOWN",
            label: T("未提供 / 待核实", "Not provided / unknown"),
          },
          {
            value: "DECLARED_NONE",
            label: T("经询问，声明无相关病史", "Asked and declared none"),
          },
          {
            value: "DECLARED",
            label: T("已声明相关病史", "Relevant history declared"),
          },
        ],
      },
      {
        name: "history_text",
        label: T("病史与变化", "History and changes"),
        type: "textarea",
        required: false,
      },
      reasonField(),
    ],
    onSubmit: (b) => api("/patients/" + id, { ...b, action: "history" }),
  });
handlers["patient-allergy"] = (id) =>
  modal({
    name: T("追加过敏资料", "Add allergy"),
    fields: [
      { name: "substance", label: T("物质 / 药物", "Substance / medication") },
      { name: "reaction", label: T("已知反应", "Known reaction") },
      {
        name: "severity",
        label: T("风险级别", "Severity"),
        type: "select",
        options: ["LOW", "MODERATE", "HIGH", "SEVERE"].map((v) => ({
          value: v,
          label: T(statusMap[v][0], statusMap[v][1]),
        })),
      },
    ],
    onSubmit: (b) => api("/patients/" + id, { ...b, action: "allergy" }),
  });
handlers["patient-contact"] = (id) =>
  modal({
    name: T("追加紧急联系人", "Emergency contact"),
    fields: [
      { name: "name", label: T("姓名", "Name") },
      { name: "relationship", label: T("与患者关系", "Relationship") },
      { name: "phone", label: T("电话", "Phone") },
    ],
    onSubmit: (b) => api("/patients/" + id, { ...b, action: "contact" }),
  });
handlers["privacy-consent"] = (id) =>
  modal({
    name: T("记录资料共享决定", "Data sharing decision"),
    description: T(
      "此记录不替代治疗项目同意。",
      "This does not replace treatment-specific consent.",
    ),
    fields: [
      {
        name: "status",
        label: T("患者决定", "Decision"),
        type: "select",
        options: ["GRANTED", "DECLINED", "WITHDRAWN"].map((v) => ({
          value: v,
          label: T(statusMap[v][0], statusMap[v][1]),
        })),
      },
    ],
    onSubmit: (b) =>
      api("/patients/" + id, { ...b, action: "privacy_consent" }),
  });
handlers["new-appointment"] = async () => {
  const resources = await api("/resources");
  modal({
    name: T("安排诊疗预约", "Schedule appointment"),
    description: T(
      "先检索患者，再协商项目、医师与时段。检查方案不会占位，保存时再次核验。",
      "Find the patient, then agree on care and resources. Validation does not reserve a slot.",
    ),
    body: `<div class="callout gap"><label class="field-label" for="booking-patient-search">${T("检索已有患者", "Find an existing patient")}</label><div class="row"><input class="field-input" id="booking-patient-search" placeholder="${T("姓名、患者编号或电话", "Name, code or phone")}"><button type="button" class="btn" id="booking-search">${T("检索", "Search")}</button></div><p id="booking-search-result" class="subline"></p></div>`,
    fields: [
      await patientField(),
      clinicField(),
      dentistField(),
      treatmentField(),
      chairField(),
      {
        name: "scheduled_start_at",
        label: T("开始时间（诊所本地）", "Start (clinic local time)"),
        type: "datetime-local",
        value: (state.serviceDate || state.boot.today) + "T09:00",
      },
      {
        name: "duration_minutes",
        label: T(
          "时长（分钟，留 0 使用项目默认）",
          "Duration (minutes; 0 uses catalog)",
        ),
        type: "number",
        value: 0,
        min: 0,
        max: 480,
      },
      {
        name: "notes",
        label: T("患者诉求与说明", "Patient request and notes"),
        type: "textarea",
        required: false,
      },
    ],
    onSubmit: (b) => api("/appointments", b),
    onReady: () => wireBookingForm(resources),
  });
};
function wireBookingForm(resources) {
  const form = $("#dialog-form"),
    clinic = form.elements.namedItem("clinic_id");
  const updateOptions = (name, options) => {
    const node = form.elements.namedItem(name),
      old = node.value;
    node.innerHTML =
      `<option value="">${name === "chair_id" ? T("不指定", "Unassigned") : T("请选择", "Select")}</option>` +
      options
        .map((o) => `<option value="${esc(o.value)}">${esc(o.label)}</option>`)
        .join("");
    if (options.some((o) => o.value === old)) node.value = old;
  };
  const filterResources = () => {
    const day =
      form.elements.namedItem("scheduled_start_at").value.slice(0, 10) ||
      state.boot.today;
    const assigned = new Set(
      resources.assignments
        .filter(
          (a) =>
            a.clinic_id === clinic.value &&
            a.status === "ACTIVE" &&
            a.effective_from <= day &&
            (!a.effective_to || a.effective_to >= day),
        )
        .map((a) => a.dentist_id),
    );
    updateOptions('treatment_id',state.boot.treatments.filter(t=>t.status==='ACTIVE'&&t.effective_from<=day&&(!t.effective_to||t.effective_to>=day)).map(t=>({value:t.id,label:`${t.name_zh} · ${t.code} · v${t.version}`})));
    updateOptions(
      "dentist_id",
      opts(
        state.boot.dentists.filter(
          (d) => assigned.has(d.id) && d.employment_status === "ACTIVE",
        ),
      ),
    );
    updateOptions(
      "chair_id",
      opts(
        state.boot.chairs.filter(
          (c) => c.clinic_id === clinic.value && c.status === "AVAILABLE",
        ),
      ),
    );
  };
  clinic.addEventListener("change", filterResources);
  form.elements
    .namedItem("scheduled_start_at")
    .addEventListener("change", filterResources);
  filterResources();
  const search = async () => {
    try {
      const d = await api(
        "/patients?" +
          new URLSearchParams({ q: $("#booking-patient-search").value }),
      );
      updateOptions(
        "patient_id",
        d.items.map((p) => ({
          value: p.id,
          label: p.patient_code + " · " + p.name_zh,
        })),
      );
      $("#booking-search-result").textContent = T(
        "匹配 " + d.total + " 条；请选择下方患者。",
        "Matched " + d.total + " record(s); select the patient below.",
      );
    } catch (e) {
      $("#booking-search-result").textContent = e.message;
    }
  };
  $("#booking-search").onclick = search;
  $("#booking-patient-search").onkeydown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      search();
    }
  };
  const check = document.createElement("button");
  check.type = "button";
  check.className = "btn";
  check.textContent = T("检查当前方案", "Validate proposal");
  $(".modal-footer").insertBefore(check, $("#modal-submit"));
  check.onclick = async () => {
    if (!form.reportValidity()) return;
    const b = Object.fromEntries(new FormData(form));
    b.duration_minutes = Number(b.duration_minutes || 0);
    check.disabled = true;
    try {
      const d = await api("/scheduling/validate", b);
      $("#modal-error").innerHTML = d.valid
        ? `<div class="callout">${T("当前方案可执行；保存时仍将再次校验。", "Proposal currently valid; saving revalidates it.")}</div>`
        : errorBox({
            message: T("请调整以下条件", "Please resolve these conditions"),
            details: d.issues,
          });
    } catch (e) {
      $("#modal-error").innerHTML = errorBox(e);
    } finally {
      check.disabled = false;
      $("#modal-error").scrollIntoView({ block: "nearest" });
    }
  };
}
function renderAppointmentHistoryEntry(h){
  const event=appointmentHistoryEvent(h,T);
  return `<div class="timeline-item"><strong>${esc(event.title)}</strong><p>${esc(event.detail)}</p><p>${date(h.occurred_at)} · ${esc(h.actor_name||'—')}</p>${event.evidence?`<p>${esc(event.evidence)}</p>`:''}</div>`;
}
handlers["appointment-detail"] = async (id) => {
  const d = await api("/appointments/" + id);
  state.appointmentDetail = d;
  const a = d.appointment;
  modal({
    name: a.patient_name + " · " + T("预约详情", "Appointment"),
    description: a.appointment_code,
    informational: true,
    fields: [],
    submit: T("关闭", "Close"),
    body: `<div class="kv-grid gap">${[
      [
        T("时间", "Time"),
        a.scheduled_start_at + " — " + a.scheduled_end_at.slice(11, 16),
      ],
      [T("诊所", "Clinic"), a.clinic_name],
      [T("牙医", "Dentist"), a.dentist_name],
      [T("牙椅", "Chair"), a.chair_name || T("未指定", "Unassigned")],
      [T("项目", "Treatment"), a.treatment_name],
      [T("版本", "Version"), a.appointment_version],
      [T("患者联系确认", "Patient confirmation"), a.confirmation_state==='CONFIRMED'?T('患者已确认','Patient confirmed'):a.confirmation_state==='UNREACHABLE'?T('暂未联系上','Unreachable'):T('待联系确认','Pending contact')],
    ]
      .map(
        ([k, v]) =>
          `<div class="kv"><small>${k}</small><strong>${esc(v)}</strong></div>`,
      )
      .join(
        "",
      )}</div><div class="row wrap gap">${badge(a.status)}${can("appointment.manage") && a.status === "CONFIRMED" ? button(T("办理到诊", "Check in"), "appointment-checkin", id, "small primary") + button(T("改期", "Reschedule"), "appointment-reschedule", id, "small") + button(T("取消", "Cancel"), "appointment-cancel", id, "small danger") + button(T("未到诊", "No-show"), "appointment-no-show", id, "small") : ""}${can("appointment.manage") && a.status === "CHECKED_IN" ? button(T("撤销到诊", "Revoke arrival"), "appointment-revoke", id, "small danger") : ""}</div><div class="timeline">${d.history.map(renderAppointmentHistoryEntry).join("")}</div>`,
    onSubmit: async () => {},
    onReady:()=>{
      if(can('appointment.manage')&&a.status==='CONFIRMED')modalRoot.querySelector('.row.wrap.gap')?.insertAdjacentHTML('beforeend',button(T('登记联系确认','Record confirmation'),'appointment-confirmation',id,'small'));
    },
  });
};
handlers['appointment-confirmation']=id=>{
  const a=state.appointmentDetail.appointment;
  modal({name:T('登记预约联系确认','Record patient confirmation'),description:T('占位预约与患者确认分开。请登记已发生的实际联系；系统不会发送消息。改期后须重新确认。','Reservation and patient confirmation are separate. Record an actual contact; no message is sent. Rescheduling resets confirmation.'),fields:[
    {name:'confirmation_state',label:T('患者确认结果','Confirmation result'),type:'select',value:a.confirmation_state,options:[['PENDING',T('待确认','Pending')],['CONFIRMED',T('患者已确认','Patient confirmed')],['UNREACHABLE',T('未联系上','Unreachable')]].map(([value,label])=>({value,label}))},
    {name:'channel',label:T('实际联系途径','Contact channel'),type:'select',options:[['PHONE',T('电话','Phone')],['EMAIL',T('邮箱','Email')],['SMS',T('短信','SMS')],['IN_PERSON',T('当面','In person')]].map(([value,label])=>({value,label}))},reasonField()
  ],onSubmit:b=>api('/appointments/'+id,{...b,action:'confirmation',version:a.appointment_version})});
};
handlers["appointment-checkin"] = (id) => {
  const a = state.appointmentDetail.appointment;
  modal({
    name: T("核实身份并办理到诊", "Verify identity and check in"),
    description: a.patient_name + " · " + a.appointment_code,
    fields: [
      {
        name: "identity_confirmed",
        label: T(
          "我已核对患者身份与预约一致",
          "I verified that the arriving patient matches the appointment",
        ),
        type: "checkbox",
      },
      {
        name: "declaration",
        label: T(
          "资料或病史变化声明（如无变化请注明）",
          "History/contact changes (state none if unchanged)",
        ),
        type: "textarea",
      },
    ],
    onSubmit: (b) =>
      api("/appointments/" + id, {
        ...b,
        action: "check_in",
        version: a.appointment_version,
      }),
  });
};
handlers["appointment-reschedule"] = (id) => {
  const a = state.appointmentDetail.appointment;
  modal({
    name: T("改期并复核资源", "Reschedule with resource validation"),
    fields: [
      { ...clinicField(), value: a.clinic_id },
      { ...dentistField(), value: a.dentist_id },
      { ...treatmentField(), value: a.treatment_id },
      { ...chairField(), value: a.chair_id },
      {
        name: "scheduled_start_at",
        label: T("新开始时间", "New start"),
        type: "datetime-local",
        value: a.scheduled_start_at.slice(0, 16).replace(" ", "T"),
      },
      {
        name: "duration_minutes",
        label: T("时长（分钟）", "Duration (minutes)"),
        type: "number",
        value: a.duration_minutes,
      },
      reasonField(),
    ],
    onSubmit: (b) =>
      api("/appointments/" + id, {
        ...b,
        action: "reschedule",
        version: a.appointment_version,
      }),
  });
};
handlers["appointment-cancel"] = (id) => {
  const a = state.appointmentDetail.appointment;
  modal({
    name: T("取消预约", "Cancel appointment"),
    fields: [
      {
        name: "initiator",
        label: T("发起方", "Initiator"),
        type: "select",
        options: [
          { value: "PATIENT", label: T("患者", "Patient") },
          { value: "CLINIC", label: T("机构", "Clinic") },
        ],
      },
      reasonField(),
    ],
    onSubmit: (b) =>
      api("/appointments/" + id, {
        ...b,
        action: "cancel",
        version: a.appointment_version,
      }),
  });
};
handlers["appointment-no-show"] = (id) => {
  const a = state.appointmentDetail.appointment;
  modal({
    name: T("确认未到诊", "Confirm no-show"),
    description: T(
      "只允许在结束及 15 分钟宽限后标记。",
      "Allowed after appointment end and the 15-minute grace period.",
    ),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/appointments/" + id, {
        ...b,
        action: "no_show",
        version: a.appointment_version,
      }),
  });
};
handlers["appointment-revoke"] = (id) => {
  const a = state.appointmentDetail.appointment;
  modal({
    name: T("撤销尚未实施治疗的到诊", "Revoke an arrival before treatment"),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/appointments/" + id, {
        ...b,
        action: "revoke_arrival",
        version: a.appointment_version,
      }),
  });
};
const clinicalModal = (name, fields, action, extra = {}) => {
  const v = state.visitDetail.visit;
  modal({
    name,
    fields,
    onSubmit: (b) =>
      api("/visits/" + v.id, {
        ...b,
        ...extra,
        action,
        version: v.visit_version,
      }),
  });
};
handlers["clinical-safety"] = () =>
  clinicalModal(
    T("本次安全复核", "Review safety"),
    [
      {
        name: "history_confirmed",
        label: T(
          "已询问本次病史变化，核实过敏与必要风险",
          "I reviewed history changes, allergies and relevant risks",
        ),
        type: "checkbox",
      },
      {
        name: "evidence",
        label: T(
          "核实结论、预防措施与依据",
          "Review conclusion, precautions and evidence",
        ),
        type: "textarea",
      },
    ],
    "safety",
  );
handlers["clinical-start"] = () =>
  clinicalModal(
    T("开始诊疗", "Start care"),
    [
      {
        name: "confirm",
        label: T(
          "我已确认患者、项目与本次服务资格",
          "I confirmed patient identity, care purpose and eligibility",
        ),
        type: "checkbox",
      },
    ],
    "start",
  );
handlers["clinical-observation"] = () =>
  clinicalModal(
    T("记录检查所见", "Record observation"),
    [
      {
        name: "tooth_code",
        label: T(
          "牙位（FDI，整体检查用 GENERAL）",
          "Tooth (FDI, GENERAL for overall exam)",
        ),
        value: state.selectedTooth || "GENERAL",
      },
      {
        name: "observation_type",
        label: T("观察类型", "Type"),
        type: "select",
        options: [
          "EXAMINATION",
          "CARIES",
          "RESTORATION",
          "MISSING",
          "PERIODONTAL",
          "NORMAL",
        ].map((v) => ({ value: v, label: v })),
      },
      {
        name: "severity",
        label: T("程度", "Severity"),
        type: "select",
        options: ["NORMAL", "LOW", "MODERATE", "HIGH"].map((v) => ({
          value: v,
          label: statusMap[v] ? T(statusMap[v][0], statusMap[v][1]) : v,
        })),
      },
      {
        name: "finding",
        label: T("检查所见与描述", "Finding"),
        type: "textarea",
      },
    ],
    "observation",
  );
handlers["clinical-plan"] = () =>
  clinicalModal(
    T("拟定治疗项目", "Propose treatment"),
    [
      treatmentField(),
      {
        name: "tooth_code",
        label: T("牙位（可选）", "Tooth (optional)"),
        value: state.selectedTooth,
        required: false,
      },
      {
        name: "units",
        label: T("数量", "Units"),
        type: "number",
        value: 1,
        min: 1,
        max: 32,
      },
      {
        name: "rationale",
        label: T(
          "理由、风险与费用说明",
          "Rationale, risks and cost explanation",
        ),
        type: "textarea",
      },
    ],
    "plan",
  );
handlers["clinical-consent"] = (id) =>
  clinicalModal(
    T("记录患者对项目的决定", "Record a treatment decision"),
    [
      {
        name: "decision",
        label: T("患者决定", "Decision"),
        type: "select",
        options: ["ACCEPTED", "DECLINED", "DEFERRED"].map((v) => ({
          value: v,
          label: T(statusMap[v][0], statusMap[v][1]),
        })),
      },
      {
        name: "evidence",
        label: T(
          "说明过程、证明材料或见证依据",
          "Explanation, evidence or witness details",
        ),
        type: "textarea",
      },
    ],
    "consent",
    { item_id: id },
  );
handlers["clinical-actual"] = (id) => {
  const r = state.visitDetail.requested.find((r) => r.id === id);
  clinicalModal(
    T("如实登记本次实施", "Record actual treatment"),
    [
      { ...treatmentField(), value: r?.treatment_id },
      {
        name: "requested_treatment_item_id",
        label: T(
          "计划来源（可空；完成前须补齐同意依据）",
          "Plan item (optional; consent is required for completion)",
        ),
        type: "select",
        required: false,
        value: id || "",
        options: state.visitDetail.requested.map((x) => ({
          value: x.id,
          label: x.treatment_name + " · " + x.status,
        })),
      },
      {
        name: "tooth_code",
        label: T("牙位（可选）", "Tooth (optional)"),
        value: r?.tooth_code || state.selectedTooth,
        required: false,
      },
      {
        name: "units",
        label: T("实施数量", "Actual units"),
        type: "number",
        value: r?.units || 1,
        min: 1,
        max: 32,
      },
      {
        name: "notes",
        label: T(
          "实施说明 / 无计划或偏离计划的原因",
          "Notes / reason for an unplanned treatment",
        ),
        type: "textarea",
        required: false,
      },
    ],
    "actual",
  );
};
handlers["clinical-note"] = () => {
  const d = state.visitDetail,
    last = d.notes.at(-1);
  clinicalModal(
    T("保存或签署病历", "Save or sign clinical note"),
    [
      {
        name: "content",
        label: T("病历内容", "Clinical note"),
        type: "textarea",
        rows: 9,
        value: last?.content_zh || "",
      },
      {
        name: "reason",
        label: T(
          "签署后补记原因（首次可空）",
          "Amendment reason (required after signature)",
        ),
        type: "textarea",
        required: false,
      },
      {
        name: "sign",
        label: T(
          "本人核对内容并签署本版本",
          "I verified the content and sign this version",
        ),
        type: "checkbox",
        required: false,
      },
    ],
    "note",
  );
};
handlers["clinical-reconcile"] = () =>
  clinicalModal(
    T("补全实施与同意的关联", "Reconcile actual treatment and consent"),
    [
      {
        name: "actual_id",
        label: T("已记录的实施项目", "Recorded actual treatment"),
        type: "select",
        options: state.visitDetail.actual
          .filter((a) => a.status === "RECORDED")
          .map((a) => ({
            value: a.id,
            label:
              a.treatment_name +
              " · FDI " +
              (a.tooth_code || "—") +
              " · " +
              a.units,
          })),
      },
      {
        name: "item_id",
        label: T("患者已接受的计划项目", "Accepted plan item"),
        type: "select",
        options: state.visitDetail.requested
          .filter((r) =>
            state.visitDetail.consents.some(
              (c) =>
                c.requested_treatment_item_id === r.id &&
                c.decision === "ACCEPTED",
            ),
          )
          .map((r) => ({
            value: r.id,
            label:
              r.treatment_name +
              " · FDI " +
              (r.tooth_code || "—") +
              " · " +
              r.units,
          })),
      },
      reasonField(),
    ],
    "reconcile_actual",
  );
handlers["clinical-complete"] = () => {
  const d = state.visitDetail;
  modal({
    name: T("核对完成条件", "Check completion"),
    description: T(
      "通过后同步保存就诊与预约完成状态。",
      "The visit and appointment complete in the same transaction.",
    ),
    body: d.blockers.length
      ? `<div class="callout warn gap"><ul>${d.blockers.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></div>`
      : `<div class="callout gap">${T("当前未发现缺项。提交时再次检查。", "No missing evidence detected. Checks run again at commit.")}</div>`,
    fields: [
      {
        name: "confirmed",
        label: T(
          "我已核对实施项目、必要同意与签署版本",
          "I reviewed actual treatment, consent and the signed version",
        ),
        type: "checkbox",
      },
    ],
    onSubmit: (b) =>
      api("/visits/" + d.visit.id, {
        ...b,
        action: "complete",
        version: d.visit.visit_version,
      }),
  });
};

async function waitlistPage() {
  const active=state.waitlistTab||'waitlist';
  const followupNavigation=followupTabs(active,{button,T,can});
  if(active==='followups'&&can('followup.read')){
    const f=await api('/followups'+query());
    return title('',T('复诊跟进','Recall follow-up'),T('按医师建议安排复诊，保留每次联系结果和正式预约。','Follow clinician advice, retain contacts, and link a booked appointment.'))+filters()+followupNavigation+renderFollowups(f,state,{T,esc,table,button});
  }
  const d = await api("/waitlist" + query());
  state.waitlist = d;
  return (
    title(
      "CAPACITY RECOVERY",
      T("让释放的时间，回到照护中。", "Turn released capacity into care."),
      T(
        "患者接受候补后才发起邀请，确认时再次校验。有效确认窗口不重复占用。",
        "Invite patients who opted in. Revalidate resources at confirmation; an active offer holds one confirmation window.",
      ),
      can("appointment.manage")
        ? button(
            T("登记候补", "New waitlist entry"),
            "waitlist-add",
            "",
            "primary",
            "plus",
          )
        : "",
    ) +
    filters() + followupNavigation +
    `<div class="metric-grid gap">${metric(T("等待安排", "Waiting"), d.entries.filter((w) => w.status === "WAITING").length, T("已登记的患者意愿", "Patient preferences recorded"), "users", true)}${metric(T("有效邀请", "Active offers"), d.offers.filter((o) => o.status === "OFFERED" && o.expires_at > state.boot.today + " 00:00:00").length, T("提交确认时检查有效期", "Expiry checked at confirmation"), "clock")}${metric(T("已确认补位", "Fulfilled"), d.entries.filter((w) => w.status === "FULFILLED").length, T("对应真实预约", "Backed by a real appointment"), "check")}${metric(T("邀请历史", "Offer history"), d.offers.length, T("拒绝与过期均保留", "Declines and expiry retained"), "file")}</div>${panel(
      T("患者候补意愿", "Patient waitlist"),
      table(
        [
          T("患者", "Patient"),
          T("治疗项目", "Treatment"),
          T("可接受日期", "Date window"),
          T("提前通知", "Notice"),
          T("优先级", "Priority"),
          T("状态", "Status"),
          "",
        ],
        d.entries.map((w) => [
          esc(w.patient_name),
          esc(w.treatment_name),
          esc(w.earliest_date) + " — " + esc(w.latest_date),
          `${w.notice_hours} h`,
          w.priority_score,
          badge(w.status),
          can("appointment.manage") && w.status === "WAITING"
            ? button(
                T("匹配释放时段", "Offer a released slot"),
                "waitlist-offer",
                w.id,
                "small",
              )
            : "",
        ]),
      ),
    )}<div style="margin-top:22px">${panel(
      T("邀请与结果", "Offers and outcomes"),
      table(
        [
          T("患者", "Patient"),
          T("邀请时段", "Offered slot"),
          T("到期时间", "Expires"),
          T("状态", "Status"),
          "",
        ],
        d.offers.map((o) => [
          esc(o.patient_name),
          date(o.offered_start_at),
          date(o.expires_at),
          badge(o.status),
          can("appointment.manage") && o.status === "OFFERED"
            ? `<div class="row">${button(T("患者接受", "Accept"), "offer-accept", o.id, "small primary")}${button(T("患者拒绝", "Decline"), "offer-decline", o.id, "small")}</div>`
            : "",
        ]),
      ),
    )}</div>`
  );
}
handlers["waitlist-add"] = async () =>
  modal({
    name: T("登记候补意愿", "Join the waitlist"),
    fields: [
      await patientField(),
      clinicField(),
      treatmentField(),
      {
        name: "earliest_date",
        label: T("最早日期", "Earliest date"),
        type: "date",
        value: state.boot.today,
      },
      {
        name: "latest_date",
        label: T("最晚日期", "Latest date"),
        type: "date",
        value: new Date(
          new Date(state.boot.today + "T12:00:00").getTime() + 30 * 86400000,
        )
          .toISOString()
          .slice(0, 10),
      },
      {
        name: "notice_hours",
        label: T("最少提前通知（小时）", "Minimum notice (hours)"),
        type: "number",
        value: 2,
        min: 0,
        max: 168,
      },
      {
        name: "priority_score",
        label: T("经核实优先级（0–100）", "Verified priority (0–100)"),
        type: "number",
        value: 50,
        min: 0,
        max: 100,
      },
    ],
    onSubmit: (b) => api("/waitlist", { ...b, action: "add" }),
  });
handlers["waitlist-offer"] = async (id) => {
  const released = await api(
    "/appointments" + query({ status: "CANCELLED", from: state.boot.today }),
  );
  modal({
    name: T("发起候补邀请", "Offer a released slot"),
    description: T(
      "将核对日期、诊所偏好、通知时限、资质和资源。确认窗口为 15 分钟。",
      "Dates, location, notice, qualifications and resources are checked. Confirmation window: 15 minutes.",
    ),
    fields: [
      {
        name: "released_appointment_id",
        label: T("已取消的未来时段", "Released future appointment"),
        type: "select",
        options: released.map((a) => ({
          value: a.id,
          label:
            a.scheduled_start_at +
            " · " +
            a.clinic_name +
            " · " +
            a.dentist_name,
        })),
      },
    ],
    onSubmit: (b) => api("/waitlist", { ...b, action: "offer", entry_id: id }),
  });
};
handlers["offer-accept"] = (id) =>
  modal({
    name: T("确认患者接受并建立预约", "Confirm acceptance and book"),
    fields: [
      {
        name: "patient_confirmed",
        label: T(
          "患者已明确同意该诊所、牙医及时间",
          "The patient confirmed the clinic, dentist and time",
        ),
        type: "checkbox",
      },
    ],
    onSubmit: (b) => api("/waitlist", { ...b, action: "accept", offer_id: id }),
  });
handlers["offer-decline"] = (id) =>
  modal({
    name: T("记录患者拒绝", "Record decline"),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/waitlist", { ...b, action: "decline", offer_id: id }),
  });
async function billingPage() {
  const invoices=await api("/finance/invoices"+query()),unbilled=await api("/finance/unbilled"+query());
  state.invoices=invoices;state.unbilled=unbilled;
  return billingContent({invoices,unbilled,view:state.billView,search:state.billSearch,canManage:can("finance.manage")},{esc,T,title,button,link,badge,table,money,date,filters});
}
async function invoicePage(id) {
  const d = await api("/finance/invoices/" + encodeURIComponent(id));
  state.invoiceDetail = d;
  const i = d.invoice;
  return `<div class="screen-only">${title("ITEMIZED SETTLEMENT", i.invoice_code, i.patient_name + " · " + i.clinic_name, button(T("打印结算单", "Print bill"), "print-invoice", "", "", "file") + (can("finance.manage") && i.status !== "VOID" ? button(T("登记收款", "Record payment"), "invoice-pay", id, "primary", "plus") + button(T("授权退款", "Authorized refund"), "invoice-refund", id, "", "wallet") + button(T("作废", "Void"), "invoice-void", id, "danger") : ""))}</div><div class="invoice-print"><section class="card card-pad gap"><div class="row between gap"><div><div class="invoice-brand">ADC Nexus</div><p class="subline">${T("安德鲁牙科连锁 · 诊疗结算单", "Andrew’s Dental Chain · Itemized care bill")}</p></div>${badge(i.status)}</div><div class="kv-grid gap">${[
    [T("患者", "Patient"), i.patient_name],
    [T("结算单号", "Bill no."), i.invoice_code],
    [T("诊所", "Clinic"), i.clinic_name],
    [T("来源就诊", "Source visit"), i.visit_code],
    [T("开具时间", "Issued"), i.issued_at],
    [T("负责牙医", "Dentist"), i.dentist_name],
  ]
    .map(
      ([k, v]) =>
        `<div class="kv"><small>${k}</small><strong>${esc(v)}</strong></div>`,
    )
    .join("")}</div>${table(
    [
      T("实施项目", "Actual treatment"),
      T("牙位", "Tooth"),
      T("数量", "Units"),
      T("单价", "Unit price"),
      T("金额", "Amount"),
    ],
    d.lines.map((l) => [
      esc(l.description_zh_snapshot) +
        `<div class="second mono">${esc(l.treatment_code_snapshot)} · ${date(l.performed_at_snapshot)}</div>`,
      esc(l.tooth_code_snapshot || "—"),
      l.units_snapshot,
      money(l.unit_price_fen_snapshot),
      money(l.amount_fen_snapshot),
    ]),
  )}<div style="max-width:320px;margin:22px 0 0 auto"><div class="total-row"><span>${T("应收合计", "Total due")}</span><strong class="num">${money(i.total_fen)}</strong></div><div class="total-row"><span>${T("已收 / 已退", "Received / refunded")}</span><span class="num">${money(i.paid_fen)} / ${money(i.refunded_fen)}</span></div><div class="total-row grand"><span>${T("待收", "Balance")}</span><span class="num">${money(i.balance_fen)}</span></div></div><p class="subline" style="margin-top:22px">${T("本单非税务发票。已实施项目、目录版本及金额快照供核对。", "Not a statutory tax invoice. Actual treatments and price snapshots are retained for verification.")}</p></section></div><div class="grid2 screen-only">${panel(
    T("收款流水", "Payment ledger"),
    table(
      [
        T("流水", "Reference"),
        T("金额", "Amount"),
        T("已退", "Refunded"),
        T("时间", "Received"),
      ],
      d.payments.map((p) => [
        `<div class="mono">${esc(p.payment_code)}</div><div class="second">${esc(p.method)} · ${esc(p.simulated_gateway_reference)}</div>`,
        money(p.amount_fen),
        money(p.refunded_amount_fen),
        date(p.received_at),
      ]),
    ),
  )}${panel(
    T("退款流水", "Refund ledger"),
    table(
      [
        T("流水", "Reference"),
        T("金额", "Amount"),
        T("理由", "Reason"),
        T("时间", "Refunded"),
      ],
      d.refunds.map((r) => [
        `<span class="mono">${esc(r.refund_code)}</span>`,
        money(r.amount_fen),
        esc(r.reason_text),
        date(r.refunded_at),
      ]),
    ),
  )}</div>`;
}
async function reviewBill(visitId){
  const d=await api("/finance/unbilled/"+encodeURIComponent(visitId));
  const v=d.visit,locked=d.period_status!=="OPEN";
  return modal({
    name:T("核对本次结算项目","Review bill items"),
    description:v.patient_name+" · "+v.patient_code+" · "+v.visit_code,
    wide:true, informational:locked,
    submit:locked?T("关闭预览","Close preview"):T("确认并生成结算单","Confirm & issue"),
    body:`<p class="subline">${esc(v.clinic_name)} · ${esc(v.dentist_name)} · ${T("完成时间","Completed")} ${date(v.completed_at)}</p>`+
      table([T("项目","Treatment"),T("牙位","Tooth"),T("数量","Units"),T("单价快照","Price snapshot"),T("金额","Amount")],d.lines.map(l=>[esc(l.treatment_name),esc(l.tooth_code||"—"),esc(l.units),money(l.effective_unit_price_fen),money(l.line_amount_fen)]))+
      `<div class="row between gap" style="margin-top:20px"><strong>${T("本次应收合计","Total due")}</strong><strong class="num">${money(d.total_fen)}</strong></div><p class="field-help">${T("预览不建立单据，也不更改临床记录；确认提交时重新检查期间、项目和重复开单。","Preview creates no bill and changes no clinical record. Confirmation rechecks the period, actual items and duplicate bills.")}</p>`+
      (locked?`<div class="callout warn">${T("服务期间已锁定。请按授权流程核实，不在此绕过锁定。","The service period is locked. Review through the authorized process; this screen cannot bypass the lock.")}</div>`:""),
    fields:locked?[]:[{name:"confirmed",type:"checkbox",label:T("已核对患者、实际项目、数量与金额","I checked patient identity, actual items, quantities and amounts")}],
    onSubmit:()=>api("/finance/invoices",{visit_id:visitId}),
    onSuccess:async result=>{history.replaceState(null,"","#/billing/"+encodeURIComponent(result.invoice.id));await refresh();}
  });
}
handlers["invoice-issue"]=id=>{
  if(id&&state.unbilled.some(v=>v.id===id))return reviewBill(id);
  return modal({name:T("选择待开单就诊","Select unbilled visit"),
    description:T("下一步只预览实际项目，不会立即开单。","The next step previews actual items; it does not issue a bill."),
    fields:[{name:"visit_id",label:T("已完成且未开单的就诊","Completed unbilled visit"),type:"select",options:state.unbilled.map(v=>({value:v.id,label:v.visit_code+" · "+v.patient_name+" · "+v.dentist_name}))}],
    submit:T("查看项目与合计","Review items and total"),successMessage:"",
    onSubmit:async b=>b.visit_id,onSuccess:reviewBill});
};
handlers["invoice-pay"] = () => {
  const i = state.invoiceDetail.invoice;
  modal({
    name: T("登记已核实收款", "Record a verified payment"),
    description: T("未收余额：", "Outstanding: ") + money(i.balance_fen),
    fields: [
      {
        name: "amount_fen",
        label: T("本次收款金额（元）", "Amount (CNY)"),
        type: "money",
        value: i.balance_fen,
      },
      {
        name: "method",
        label: T("核实收款方式", "Verified payment method"),
        type: "select",
        options: [
          ["CASH", "现金", "Cash"],
          ["BANK_CARD", "银行卡", "Bank card"],
          ["WECHAT", "微信凭据", "WeChat evidence"],
          ["ALIPAY", "支付宝凭据", "Alipay evidence"],
          ["BANK_TRANSFER", "银行转账", "Bank transfer"],
        ].map(([value, zh, en]) => ({ value, label: T(zh, en) })),
      },
      {
        name: "reference",
        label: T(
          "唯一收款凭据 / 经核实流水号",
          "Unique verified payment reference",
        ),
      },
      {
        name: "notes",
        label: T("核实说明", "Verification notes"),
        type: "textarea",
        required: false,
      },
    ],
    onSubmit: (b) =>
      api("/finance/invoices/" + i.id, {
        ...b,
        action: "pay",
        version: i.invoice_version,
      }),
  });
};
handlers["invoice-refund"] = () => {
  const d = state.invoiceDetail,
    i = d.invoice;
  modal({
    name: T("登记授权退款", "Record an authorized refund"),
    description: T(
      "退款保留原收款与独立流水；不能超过原款剩余可退额。",
      "The original payment is retained. Refunds cannot exceed its remaining amount.",
    ),
    fields: [
      {
        name: "payment_id",
        label: T("原收款流水", "Original payment"),
        type: "select",
        options: d.payments
          .filter((p) => Number(p.amount_fen) > Number(p.refunded_amount_fen))
          .map((p) => ({
            value: p.id,
            label:
              p.payment_code +
              " · " +
              T("可退 ", "Available ") +
              money(Number(p.amount_fen) - Number(p.refunded_amount_fen)),
          })),
      },
      {
        name: "amount_fen",
        label: T("退款金额（元）", "Refund amount (CNY)"),
        type: "money",
      },
      reasonField(),
      {
        name: "authorized",
        label: T(
          "已核实原凭据并取得退款授权",
          "Original payment verified and refund authorized",
        ),
        type: "checkbox",
      },
    ],
    onSubmit: (b) =>
      api("/finance/invoices/" + i.id, {
        ...b,
        action: "refund",
        version: i.invoice_version,
      }),
  });
};
handlers["invoice-void"] = () => {
  const i = state.invoiceDetail.invoice;
  modal({
    name: T("授权作废结算单", "Void an unpaid bill"),
    description: T(
      "仅净收款为零且原服务期间开放时允许；原单据与明细保留。",
      "Allowed only for zero net receipts in an open source period. Original records remain.",
    ),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/finance/invoices/" + i.id, {
        ...b,
        action: "void",
        version: i.invoice_version,
      }),
  });
};
handlers["print-invoice"] = () => window.print();
function csvCell(value) {
  let text = String(value ?? "");
  const leading = text.replace(/^[\s\u0000-\u001f\u007f]*/u, "").normalize("NFKC");
  // Human-viewing CSV: neutralize formula prefixes, including full-width and
  // control/whitespace-prefixed input. Numeric values keep their numeric form.
  // This is not a lossless machine-import format or a guarantee across editors.
  if (typeof value !== "number" && /^[=+\-@]/.test(leading)) text = "\t" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}
function downloadCSV(filename, headers, rows) {
  const csv =
    "\ufeff" +
    [headers, ...rows].map((r) => r.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(
    new Blob([csv], { type: "text/csv;charset=utf-8" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
handlers["billing-export"] = () =>
  downloadCSV(
    "ADC_Nexus_billing_" + state.boot.today + ".csv",
    [
      "Invoice",
      "Patient",
      "Clinic",
      "Status",
      "Total CNY",
      "Paid CNY",
      "Refunded CNY",
      "Balance CNY",
    ],
    state.invoices.map((i) => [
      i.invoice_code,
      i.patient_name,
      i.clinic_name,
      i.status,
      Number(i.total_fen) / 100,
      Number(i.paid_fen) / 100,
      Number(i.refunded_fen) / 100,
      Number(i.balance_fen) / 100,
    ]),
  );
async function periodsPage() {
  const d = await api("/finance/periods" + query());
  state.periods = d;
  let review = null;
  if (state.periodId && can("period.manage"))
    review = await api(
      "/finance/preflight?period_id=" + encodeURIComponent(state.periodId),
    );
  state.periodReview = review;
  const summary = review
    ? `<div class="metric-grid gap">${metric(T("期间净收款", "Period net receipts"), money(review.revenue_fen), T("按收退款发生日", "By cash event date"), "wallet", true)}${metric(T("治疗成本", "Treatment costs"), money(review.cost_fen), T("实际成本需核实", "Actual costs require verification"), "tooth")}${metric(T("运营费用", "Operating expenses"), money(review.expense_fen), T("费用归属与批准依据", "Allocated with approved evidence"), "receipt")}${metric(T("课程口径净利润", "Profit, course basis"), money(review.profit_fen), T("基金总额 ", "Pool: ") + money(review.pool_fen), "chart")}</div><div class="callout ${review.blockers.length ? "warn" : ""} gap"><strong>${T("核算口径与提交条件", "Accounting basis and close conditions")}</strong><p>${esc(review.policy)}</p>${review.blockers.length ? `<ul>${review.blockers.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>` : `<p>${T("未发现阻断项。关闭时将重新核对输入摘要与版本。", "No blockers detected. Version and input digest are rechecked at close.")}</p>`}<div class="row wrap" style="margin-top:12px">${badge(review.period.status)}${review.period.status === "OPEN" ? button(T("核对并关闭期间", "Confirm and close"), "period-close", "", "primary small") : button(T("授权重开", "Authorized reopen"), "period-reopen", "", "small")}<span class="mono">${review.fingerprint.slice(0, 16)}…</span></div></div>`
    : "";
  return (
    title(
      "FINANCIAL GOVERNANCE",
      T("期间核算", "Financial close"),
      T(
        "核实成本与费用归属，保存输入摘要和核定快照。个人贡献不等于个人奖金。",
        "Verify costs and allocation, preserve the input digest and approved snapshot. Contribution is not a personal bonus.",
      ),
      can("expense.manage")
        ? button(
            T("登记核实费用", "Record verified expense"),
            "expense-add",
            "",
            "primary",
            "plus",
          )
        : "",
    ) +
    filters() +
    panel(
      T("财务期间", "Reporting periods"),
      table(
        [
          T("期间", "Period"),
          T("日期范围", "Dates"),
          T("状态", "Status"),
          T("版本", "Version"),
          T("核定时间", "Locked at"),
          "",
        ],
        d.periods.map((p) => [
          esc(p.name_zh),
          esc(p.starts_on) + " — " + esc(p.ends_on),
          badge(p.status),
          p.period_version,
          date(p.locked_at),
          can("period.manage")
            ? button(
                T("预检 / 查看", "Review"),
                "period-preview",
                p.id,
                "small",
              )
            : "",
        ]),
      ),
    ) +
    `<div style="margin-top:22px">${summary}</div>${
      review
        ? panel(
            T("牙医贡献核对", "Dentist contribution review"),
            table(
              [
                T("牙医", "Dentist"),
                T("收入", "Revenue"),
                T("成本", "Costs"),
                T("费用归属", "Allocated expenses"),
                T("贡献", "Contribution"),
              ],
              review.dentists.map((d) => [
                esc(d.name_zh),
                money(d.revenue_fen),
                money(d.cost_fen),
                money(d.expense_fen),
                money(d.profit_fen),
              ]),
            ),
          )
        : ""
    }<div class="gap" style="margin-top:22px">${panel(
      T("运营费用与归属", "Expenses and allocation"),
      table(
        [
          T("费用 / 诊所", "Expense / clinic"),
          T("类别", "Category"),
          T("金额", "Amount"),
          T("已归属", "Allocated"),
          T("核实状态", "Status"),
          "",
        ],
        d.expenses.map((e) => {
          const assigned = (d.allocations || [])
            .filter((a) => a.expense_id === e.id)
            .reduce((n, a) => n + Number(a.amount_fen), 0);
          return [
            `<div class="name">${esc(e.vendor_name)}</div><div class="second">${esc(e.clinic_name)} · ${esc(e.incurred_on)}</div>`,
            esc(e.category),
            money(e.amount_fen),
            money(assigned),
            badge(e.status),
            can("expense.manage")
              ? button(T("分摊", "Allocate"), "expense-allocate", e.id, "small")
              : "",
          ];
        }),
      ),
    )}</div>${panel(
      T("治疗成本核实", "Treatment cost verification"),
      table(
        [
          T("实施项目", "Treatment"),
          T("实施日", "Cost date"),
          T("目录估算", "Catalog estimate"),
          T("核实成本", "Verified costs"),
          T("依据状态", "Evidence status"),
          "",
        ],
        d.costs.map((x) => [
          esc(x.treatment_name),
          esc(x.cost_date),
          money(x.catalog_estimated_cost_fen),
          money(x.total_cost_fen),
          badge(x.source),
          can("expense.manage")
            ? button(T("核实", "Verify"), "cost-verify", x.id, "small")
            : "",
        ]),
      ),
    )}<div style="margin-top:22px">${panel(
      T("历史核定快照", "Approved snapshots"),
      table(
        [
          T("范围", "Scope"),
          T("核定收入", "Revenue"),
          T("净利润", "Profit"),
          T("核定时间", "Approved"),
        ],
        d.results.map((r) => [
          esc(r.scope_key),
          money(r.recognized_revenue_fen),
          money(r.net_profit_fen),
          date(r.approved_at),
        ]),
      ),
    )}</div>`
  );
}
handlers["period-preview"] = (id) => {
  state.periodId = id;
  refresh();
};
handlers["period-close"] = () => {
  const r = state.periodReview;
  modal({
    name: T("关闭季度财务期间", "Close the financial period"),
    description: r.period.name_zh,
    body: `<div class="callout gap">${esc(r.policy)}</div>`,
    fields: [
      {
        name: "policy_confirmed",
        label: T(
          "已核对本次课程口径、全部输入及分摊依据；核定后按授权流程重开",
          "I reviewed the stated course basis, all inputs and allocations; subsequent correction requires reopening",
        ),
        type: "checkbox",
      },
    ],
    onSubmit: (b) =>
      api("/finance/periods", {
        ...b,
        action: "close",
        period_id: r.period.id,
        version: r.period.period_version,
        fingerprint: r.fingerprint,
      }),
  });
};
handlers["period-reopen"] = () => {
  const r = state.periodReview;
  modal({
    name: T("授权重开期间", "Reopen the period"),
    description: T(
      "历史核定快照保留，新关闭产生新版本。",
      "Existing snapshots remain; closing again creates a new version.",
    ),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/finance/periods", {
        ...b,
        action: "reopen",
        period_id: r.period.id,
        version: r.period.period_version,
      }),
  });
};
handlers["expense-add"] = () =>
  modal({
    name: T("登记经核实运营费用", "Record a verified expense"),
    fields: [
      clinicField(),
      {
        name: "category",
        label: T("费用类别", "Category"),
        type: "select",
        options: [
          "RENT",
          "SALARY",
          "UTILITIES",
          "SUPPLIES",
          "MARKETING",
          "OTHER",
        ].map((value) => ({ value, label: value })),
      },
      { name: "vendor", label: T("收款方 / 供应商", "Vendor / payee") },
      {
        name: "amount_fen",
        label: T("金额（元）", "Amount (CNY)"),
        type: "money",
      },
      {
        name: "incurred_on",
        label: T("发生日期", "Incurred on"),
        type: "date",
        value: state.boot.today,
      },
      {
        name: "evidence",
        label: T("凭据、用途与核实依据", "Evidence and verification basis"),
        type: "textarea",
      },
    ],
    onSubmit: (b) => api("/finance/periods", { ...b, action: "expense" }),
  });
handlers["expense-allocate"] = (id) => {
  const e = state.periods.expenses.find((e) => e.id === id),
    assigned = (state.periods.allocations || [])
      .filter((a) => a.expense_id === id)
      .reduce((n, a) => n + Number(a.amount_fen), 0);
  modal({
    name: T("记录牙医费用归属", "Allocate expense to a dentist"),
    description:
      e.vendor_name +
      " · " +
      T("尚未归属 ", "Remaining ") +
      money(Number(e.amount_fen) - assigned),
    fields: [
      dentistField(),
      {
        name: "amount_fen",
        label: T("归属金额（元）", "Allocated amount (CNY)"),
        type: "money",
        value: Number(e.amount_fen) - assigned,
      },
      {
        name: "basis",
        label: T(
          "已批准的分摊办法与依据",
          "Approved allocation rule and evidence",
        ),
        type: "textarea",
      },
    ],
    onSubmit: (b) =>
      api("/finance/periods", { ...b, action: "allocate", expense_id: id }),
  });
};
handlers["cost-verify"] = (id) => {
  const x = state.periods.costs.find((x) => x.id === id);
  modal({
    name: T("核实实施项目成本", "Verify actual treatment costs"),
    description: x.treatment_name + " · " + x.cost_date,
    fields: [
      {
        name: "materials_fen",
        label: T("用品材料成本（元）", "Materials (CNY)"),
        type: "money",
        value: x.materials_cost_fen,
      },
      {
        name: "laboratory_fen",
        label: T("技工成本（元）", "Laboratory (CNY)"),
        type: "money",
        value: x.laboratory_cost_fen,
      },
      {
        name: "provider_fen",
        label: T("其他直接成本（元）", "Other direct costs (CNY)"),
        type: "money",
        value: x.provider_cost_fen,
      },
      {
        name: "evidence",
        label: T("核实凭据与说明", "Evidence and explanation"),
        type: "textarea",
      },
    ],
    onSubmit: (b) =>
      api("/finance/periods", { ...b, action: "cost", cost_id: id }),
  });
};

async function resourcesPage() {
  const d = await api("/resources" + query());
  state.resources = d;
  const tabs = [
    ["clinics", T("诊所网络", "Clinics")],
    ["workforce", T("牙医与任职", "Workforce")],
    ["credentials", T("资质证明", "Credentials")],
    ["catalog", T("治疗目录", "Catalog")],
    ["schedule", T("排班与例外", "Schedules")],
    ["chairs", T("牙椅配置", "Chairs")],
  ];
  let content = "";
  const name = (id, list) => esc(list.find((r) => r.id === id)?.name_zh || id);
  const setup=renderSetupTab(d,state.resourcesTab,{T,esc,badge,button,table,panel,money,can,qualifications:state.boot.qualifications,network:state.principal.network});
  if(setup!==null)return title('',T('组织与资源','Organization & resources'),T('维护诊所、医师、牙椅与服务目录；变更前核对现有预约和生效日期。','Maintain clinics, clinicians, chairs and services; check current bookings and effective dates.'))+filters()+`<div class="tabline">${tabs.map(([value,label])=>button(label,'resources-tab',value,'small '+(state.resourcesTab===value?'on':''))).join('')}</div>`+setup;
  if (state.resourcesTab === "clinics")
    content = `<div class="grid3">${d.clinics.map((c) => `<article class="card card-pad"><div class="row between"><span class="eyebrow">${esc(c.code)}</span>${badge(c.status)}</div><h2 style="margin:15px 0 5px">${esc(c.name_zh)}</h2><p class="subline">${esc(c.name_en)}</p><div class="divider"></div><div class="row between"><span class="subline">${esc(c.city_zh)} · ${esc(c.address_zh)}</span><span class="badge">${c.chair_capacity} ${T("牙椅", "chairs")}</span></div><p class="subline">${esc(c.phone || "")}</p></article>`).join("")}</div>`;
  else if (state.resourcesTab === "workforce")
    content = panel(
      T("牙医及跨店任职", "Dentists and assignments"),
      table(
        [
          T("牙医", "Dentist"),
          T("任职诊所", "Clinic"),
          T("生效期", "Effective dates"),
          T("周工时", "Weekly hours"),
          T("状态", "Status"),
        ],
        d.assignments.map((a) => [
          esc(a.dentist_name),
          esc(a.clinic_name),
          esc(a.effective_from) +
            " — " +
            esc(a.effective_to || T("长期", "Open-ended")),
          a.weekly_hours,
          badge(a.status),
        ]),
      ),
      can("workforce.manage")
        ? button(
            T("追加任职", "Add assignment"),
            "assignment-add",
            "",
            "small",
            "plus",
          )
        : "",
    );
  else if (state.resourcesTab === "credentials")
    content = panel(
      T("资质与核验依据", "Credentials and verification"),
      table(
        [
          T("牙医 / 资质", "Dentist / qualification"),
          T("颁发机构", "Issuing body"),
          T("证明编号", "Reference"),
          T("颁发 / 到期", "Validity"),
          T("核验状态", "Verification"),
        ],
        d.credentials.map((q) => [
          `${esc(q.dentist_name)}<div class="second">${esc(q.qualification_name)}</div>`,
          esc(q.issuing_body),
          `<span class="mono">${esc(q.reference_number)}</span>`,
          esc(q.issued_on) +
            " — " +
            esc(q.expires_on || T("无固定到期日", "No fixed expiry")) +
            (q.expires_on && q.expires_on < state.boot.today
              ? `<div class="second" style="color:var(--red)">${T("已到期", "Expired")}</div>`
              : ""),
          badge(q.verification_status),
        ]),
      ),
      can("workforce.manage")
        ? button(
            T("登记资质", "Add credential"),
            "credential-add",
            "",
            "small",
            "plus",
          )
        : "",
    );
  else if (state.resourcesTab === "catalog")
    content = panel(
      T("治疗目录与价格版本", "Versioned treatment catalog"),
      table(
        [
          T("代码 / 项目", "Code / treatment"),
          T("类别", "Category"),
          T("时长", "Duration"),
          T("标准价格", "Price"),
          T("目录估算成本", "Estimated costs"),
          T("生效期", "Effective dates"),
          T("状态", "Status"),
        ],
        d.treatments.map((t) => [
          `<div class="name">${esc(t.name_zh)}</div><div class="second mono">${esc(t.code)} · v${t.version}</div>`,
          esc(t.category),
          t.duration_minutes + " min",
          money(t.standard_price_fen),
          money(t.estimated_cost_fen),
          esc(t.effective_from) + " — " + esc(t.effective_to || "∞"),
          badge(t.status),
        ]),
      ),
      "",
      T(
        "目录成本仅供估算，期间核定需要实际凭据。",
        "Catalog costs are estimates; financial close requires actual evidence.",
      ),
    );
  else if (state.resourcesTab === "chairs")
    content = panel(
      T("牙椅与可用状态", "Chair availability"),
      table(
        [
          T("诊所", "Clinic"),
          T("牙椅", "Chair"),
          T("诊室", "Room"),
          T("设备配置", "Equipment"),
          T("状态", "Status"),
          "",
        ],
        d.chairs.map((c) => [
          name(c.clinic_id, d.clinics),
          esc(c.name_zh) + `<div class="second mono">${esc(c.code)}</div>`,
          esc(c.room_name_zh),
          esc(c.equipment_json),
          badge(c.status),
          can("resource.manage")
            ? button(
                T("调整状态", "Change status"),
                "chair-change",
                c.id,
                "small",
              )
            : "",
        ]),
      ),
    );
  else
    content = `${panel(
      T("牙医排班", "Dentist schedules"),
      table(
        [
          T("牙医", "Dentist"),
          T("诊所", "Clinic"),
          T("星期", "Weekday"),
          T("时段", "Hours"),
          T("生效日期", "Effective from"),
          "",
        ],
        d.availability.map((r) => [
          name(r.dentist_id, d.dentists),
          name(r.clinic_id, d.clinics),
          T(
            ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][
              r.day_of_week
            ],
            ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][r.day_of_week],
          ),
          esc(r.starts_at) + " — " + esc(r.ends_at),
          esc(r.effective_from),
          can("resource.manage")
            ? button(T("调整", "Edit"), "schedule-edit", r.id, "small")
            : "",
        ]),
      ),
      can("resource.manage")
        ? button(
            T("新增班次", "New schedule"),
            "schedule-add",
            "",
            "small",
            "plus",
          )
        : "",
    )}<div class="grid2" style="margin-top:22px">${panel(
      T("诊所停诊", "Clinic closures"),
      table(
        [T("诊所", "Clinic"), T("开始 / 结束", "Time"), T("原因", "Reason")],
        d.closures.map((r) => [
          name(r.clinic_id, d.clinics),
          date(r.starts_at) + "<br>" + date(r.ends_at),
          esc(r.reason_zh),
        ]),
      ),
      can("resource.manage")
        ? button(T("登记", "Add"), "closure-add", "", "small", "plus")
        : "",
    )}${panel(
      T("牙医停诊例外", "Dentist exceptions"),
      table(
        [T("牙医", "Dentist"), T("开始 / 结束", "Time"), T("原因", "Reason")],
        d.exceptions.map((r) => [
          name(r.dentist_id, d.dentists),
          date(r.starts_at) + "<br>" + date(r.ends_at),
          esc(r.reason_zh),
        ]),
      ),
      can("resource.manage")
        ? button(T("登记", "Add"), "exception-add", "", "small", "plus")
        : "",
    )}</div>`;
  return (
    title(
      "NETWORK & CAPABILITY",
      T("组织与资源", "Organization & resources"),
      T(
        "任职、有效证书、排班与牙椅共同决定可执行的服务能力。",
        "Assignments, valid credentials, schedules and chairs define executable care capacity.",
      ),
    ) +
    filters() +
    `<div class="tabline">${tabs.map(([value, label]) => button(label, "resources-tab", value, "small " + (state.resourcesTab === value ? "on" : ""))).join("")}</div>` +
    content
  );
}
handlers["resources-tab"] = (id) => {
  state.resourcesTab = id;
  refresh();
};
handlers["chair-change"] = (id) => {
  const c = state.resources.chairs.find((c) => c.id === id);
  modal({
    name: T("调整牙椅状态", "Change chair availability"),
    description: T(
      "存在受影响预约时不允许直接停用。",
      "An active booking prevents deactivation until it is coordinated.",
    ),
    fields: [
      {
        name: "status",
        label: T("目标状态", "New state"),
        type: "select",
        value: c.status,
        options: ["AVAILABLE", "MAINTENANCE", "INACTIVE"].map((v) => ({
          value: v,
          label: T(statusMap[v][0], statusMap[v][1]),
        })),
      },
    ],
    onSubmit: (b) =>
      api("/resources", {
        ...b,
        action: "chair",
        chair_id: id,
        updated_at: c.updated_at,
      }),
  });
};
const validityFields = () => [
  {
    name: "effective_from",
    label: T("生效日期", "Effective from"),
    type: "date",
    value: state.boot.today,
  },
  {
    name: "effective_to",
    label: T("失效日期（可空）", "Effective to (optional)"),
    type: "date",
    required: false,
  },
];
function scheduleForm(rule) {
  modal({
    name: T("牙医班次", "Dentist schedule"),
    description: T(
      "需有效任职；调整不得静默影响已确认预约。",
      "Requires an active assignment. Confirmed appointments cannot be silently affected.",
    ),
    fields: [
      { ...clinicField(), value: rule?.clinic_id || selectedClinic() },
      { ...dentistField(), value: rule?.dentist_id },
      {
        name: "day_of_week",
        label: T("星期", "Weekday"),
        type: "select",
        value: rule?.day_of_week ?? 1,
        options: [
          "Sunday",
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
        ].map((en, value) => ({
          value,
          label: T(
            ["周日", "周一", "周二", "周三", "周四", "周五", "周六"][value],
            en,
          ),
        })),
      },
      {
        name: "starts_at",
        label: T("开始时间", "Starts at"),
        type: "time",
        value: rule?.starts_at || "09:00",
      },
      {
        name: "ends_at",
        label: T("结束时间", "Ends at"),
        type: "time",
        value: rule?.ends_at || "18:00",
      },
      ...validityFields().map((f) => ({
        ...f,
        value: rule?.[f.name] || f.value,
      })),
    ],
    onSubmit: (b) =>
      api("/resources", {
        ...b,
        action: "availability",
        rule_id: rule?.id || "",
        fingerprint: rule?.fingerprint || "",
      }),
  });
}
handlers["schedule-add"] = () => scheduleForm();
handlers["schedule-edit"] = (id) =>
  scheduleForm(state.resources.availability.find((r) => r.id === id));
for (const action of ["closure", "exception"])
  handlers[action + "-add"] = () =>
    modal({
      name: T(
        action === "closure" ? "登记诊所停诊" : "登记牙医例外",
        action === "closure" ? "Clinic closure" : "Dentist exception",
      ),
      fields: [
        clinicField(),
        ...(action === "exception" ? [dentistField()] : []),
        {
          name: "starts_at",
          label: T("开始", "Starts at"),
          type: "datetime-local",
          value: state.boot.today + "T09:00",
        },
        {
          name: "ends_at",
          label: T("结束", "Ends at"),
          type: "datetime-local",
          value: state.boot.today + "T18:00",
        },
        reasonField(),
      ],
      onSubmit: (b) => api("/resources", { ...b, action }),
    });
handlers["credential-add"] = () =>
  modal({
    name: T("登记并核实资质", "Register a credential"),
    fields: [
      dentistField(),
      {
        name: "qualification_type_id",
        label: T("资质类型", "Qualification type"),
        type: "select",
        options: opts(state.boot.qualifications),
      },
      { name: "issuing_body", label: T("颁发机构", "Issuing body") },
      { name: "reference_number", label: T("证明编号", "Reference number") },
      {
        name: "issued_on",
        label: T("颁发日期", "Issued on"),
        type: "date",
        value: state.boot.today,
      },
      {
        name: "expires_on",
        label: T("到期日期（可空）", "Expires on (optional)"),
        type: "date",
        required: false,
      },
      {
        name: "verified",
        label: T(
          "已核验原件与颁发方信息",
          "Original evidence and issuing authority verified",
        ),
        type: "checkbox",
        required: false,
      },
    ],
    onSubmit: (b) => api("/resources", { ...b, action: "credential" }),
  });
handlers["assignment-add"] = () =>
  modal({
    name: T("登记跨店任职", "Record a clinic assignment"),
    fields: [
      clinicField(),
      dentistField(),
      ...validityFields(),
      {
        name: "weekly_hours",
        label: T("周工时", "Weekly hours"),
        type: "number",
        value: 20,
        min: 1,
        max: 168,
        help: T("记录实际约定工时；范围校验不代表劳动制度或合规审批。", "Record agreed hours. Validation is not labor-policy approval."),
      },
    ],
    onSubmit: (b) => api("/resources", { ...b, action: "assignment" }),
  });
async function analyticsPage() {
  const d = await api("/analytics" + query({ from: state.from, to: state.to }));
  state.analytics = d;
  return (
    title(
      "PERFORMANCE INTELLIGENCE",
      T("经营统计", "Business analytics"),
      T(
        "让分子、分母、日期依据和资源条件一起呈现。",
        "Read every measure alongside its denominator, service dates and capacity assumptions.",
      ),
      button(
        T("导出指标", "Export metrics"),
        "analytics-export",
        "",
        "",
        "download",
      ),
    ) +
    filters({ range: true }) +
    `<div class="metric-grid gap">${metric(T("同期计划服务", "Scheduled services"), num(d.appointments), T("按计划服务日", "By scheduled service date"), "calendar", true)}${metric(T("主动取消率", "Cancellation rate"), pct(d.cancellation_rate), `${d.cancellations} / ${d.appointments}`, "clock")}${metric(T("未到诊率", "No-show rate"), pct(d.no_show_rate), `${d.no_shows} / ${Number(d.appointments) - Number(d.cancellations)}`, "users")}${metric(T("临床完成率", "Clinical completion"), pct(d.clinical_completion_rate), T("完成 / 有效已建立就诊", "Completed / valid visits"), "check")}</div><div class="grid2 gap">${panel(T("诊所牙椅利用", "Chair utilization"), `<div class="card-pad">${d.utilization.map((c) => `<div style="margin-bottom:17px"><div class="row between" style="margin-bottom:7px"><strong style="font-size:12px">${esc(c.clinic_name)}</strong><span class="mono">${pct(c.rate)}</span></div><div class="mini-progress"><span style="width:${Math.min(100, Math.max(0, Number(c.rate || 0) * 100))}%"></span></div><p class="subline">${num(c.occupied_chair_minutes)} / ${num(c.available_chair_minutes)} ${T("分钟", "minutes")}</p></div>`).join("")}</div>`)}${panel(
      T("实际治疗结构", "Treatment mix"),
      table(
        [T("项目", "Treatment"), T("实施行数", "Rows"), T("单位数", "Units")],
        d.treatments.map((t) => [
          esc(t.name_zh) + `<div class="second mono">${esc(t.code)}</div>`,
          num(t.treatments),
          num(t.units),
        ]),
      ),
    )}</div>${panel(
      T("牙医预约履约", "Dentist appointment outcomes"),
      table(
        [
          T("牙医", "Dentist"),
          T("同期预约", "Appointments"),
          T("完成", "Complete"),
          T("取消", "Cancelled"),
        ],
        d.dentists.map((r) => [
          esc(r.name_zh),
          num(r.appointments),
          num(r.completed),
          num(r.cancelled),
        ]),
      ),
    )}<div style="margin-top:22px">${panel(
      T("服务日资质覆盖", "Qualification coverage"),
      table(
        [
          T("诊所", "Clinic"),
          T("治疗项目", "Treatment"),
          T("有效合格牙医数", "Qualified dentists"),
          T("判定日期", "As of"),
        ],
        d.coverage.map((c) => [
          esc(c.clinic_name),
          esc(c.treatment_name),
          Number(c.qualified_dentists) === 0
            ? `<span class="badge red">0 · ${T("覆盖缺口", "Gap")}</span>`
            : num(c.qualified_dentists),
          esc(c.service_date),
        ]),
      ),
    )}</div><div class="callout" style="margin-top:22px"><strong>${T("指标口径", "Metric definitions")}</strong><ul>${d.definitions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul><p>${T("生成于", "Generated at")} ${date(d.generated_at)}</p></div>`
  );
}
handlers["analytics-export"] = () =>
  downloadCSV(
    "ADC_Nexus_capacity_" + state.boot.today + ".csv",
    [
      "Clinic",
      "Occupied minutes",
      "Available minutes",
      "Utilization",
      "From",
      "To",
    ],
    state.analytics.utilization.map((r) => [
      r.clinic_name,
      r.occupied_chair_minutes,
      r.available_chair_minutes,
      r.rate ?? "N/A",
      state.from,
      state.to,
    ]),
  );
async function expansionPage() {
  const d = await api("/expansion" + query());
  state.expansion = d;
  return (
    title(
      "NETWORK PLANNING",
      T("扩张测算", "Expansion planning"),
      T(
        "情景假设、候选地点与计算结果相互对应，不改变实际业务。",
        "Scenario inputs, candidate locations and calculations stay traceable without changing live operations.",
      ),
      can("expansion.manage")
        ? button(
            T("建立新情景", "New scenario"),
            "scenario-add",
            "",
            "primary",
            "plus",
          )
        : "",
    ) +
    `<div class="callout gap">${T("预测仅用于课程决策分析，不代表收入承诺。资格覆盖、需求与选址须另行核验；未核实的输入明确保留。", "Forecasts support course decision analysis, not revenue commitments. Demand, locations and qualification coverage require separate verification.")}</div><div class="grid3 gap">${d.scenarios
      .map((s) => {
        const r = d.results.find((r) => r.scenario_id === s.id),
          candidates = d.candidates.filter((c) => c.scenario_id === s.id);
        return `<section class="card card-pad"><div class="row between"><span class="eyebrow">${esc(s.scenario_code)} · V${s.version}</span>${badge(s.status)}</div><h2 style="margin-top:18px">${esc(s.name_zh)}</h2><p class="subline">${esc(s.description_zh)}</p><div class="divider"></div>${r ? `<div class="total-row"><span>${T("预测季度收入", "Quarterly revenue")}</span><strong>${money(r.projected_quarter_revenue_fen)}</strong></div><div class="total-row"><span>${T("预测净利润", "Projected profit")}</span><strong>${money(r.projected_net_profit_fen)}</strong></div><div class="total-row"><span>${T("测算回收期", "Estimated payback")}</span><strong>${Number(r.payback_months) > 0 ? r.payback_months + " " + T("月", "months") : T("无法回收 / 不适用", "Not applicable")}</strong></div>` : empty()}<p class="subline">${candidates.length} ${T("个候选地点", "candidate locations")}</p></section>`;
      })
      .join("")}</div>${panel(
      T("候选诊所与投入条件", "Candidate clinics and requirements"),
      table(
        [
          T("候选地点", "Candidate"),
          T("城市 / 区域", "Location"),
          T("牙椅 / 牙医", "Chairs / dentists"),
          T("初始投入", "Initial capital"),
          T("季度固定成本", "Quarter fixed costs"),
          T("资格覆盖", "Qualification coverage"),
        ],
        d.candidates.map((c) => [
          esc(c.name_zh) +
            `<div class="second mono">${esc(c.candidate_code)}</div>`,
          esc(c.city_zh) + " · " + esc(c.district_zh),
          c.planned_chair_count + " / " + c.planned_dentist_count,
          money(c.initial_capital_fen),
          money(c.quarterly_fixed_cost_fen),
          Number(c.qualification_coverage_basis_points) === 0
            ? T("待核实", "Unreviewed")
            : pct(Number(c.qualification_coverage_basis_points) / 10000),
        ]),
      ),
    )}<div style="margin-top:22px">${panel(
      T("假设与资料依据", "Assumptions and sources"),
      table(
        [
          T("假设", "Assumption"),
          T("值 / 单位", "Value / unit"),
          T("依据", "Source"),
        ],
        d.assumptions.map((a) => [
          esc(a.label_zh),
          `<span class="mono">${esc(a.value_text.length > 150 ? a.value_text.slice(0, 150) + "…" : a.value_text)}</span><div class="second">${esc(a.unit)}</div>`,
          esc(a.source_zh),
        ]),
      ),
    )}</div>`
  );
}
handlers["scenario-add"] = () =>
  modal({
    name: T("建立参数化扩张情景", "Create an expansion scenario"),
    fields: [
      {
        name: "name",
        label: T("情景 / 候选诊所名称", "Scenario / candidate name"),
      },
      { name: "city", label: T("候选城市", "Candidate city") },
      {
        name: "chairs",
        label: T("计划牙椅数", "Planned chairs"),
        type: "number",
        value: 8,
        min: 1,
        max: 50,
      },
      {
        name: "appointments",
        label: T("季度诊疗量假设", "Assumed quarterly appointments"),
        type: "number",
        value: 2400,
        min: 1,
        max: 100000,
      },
      {
        name: "average_price_fen",
        label: T("平均诊疗价格（元）", "Average price (CNY)"),
        type: "money",
        value: 60000,
      },
      {
        name: "cost_basis_points",
        label: T(
          "变动成本比例（基点；3000=30%）",
          "Variable cost (basis points; 3000=30%)",
        ),
        type: "number",
        value: 3000,
        min: 0,
        max: 9999,
      },
      {
        name: "fixed_cost_fen",
        label: T("季度固定费用（元）", "Quarterly fixed costs (CNY)"),
        type: "money",
        value: 30000000,
      },
      {
        name: "capital_fen",
        label: T("初始投资（元）", "Initial capital (CNY)"),
        type: "money",
        value: 180000000,
      },
      {
        name: "basis",
        label: T(
          "需求、成本及选址假设依据",
          "Demand, cost and location evidence",
        ),
        type: "textarea",
      },
    ],
    onSubmit: (b) => api("/expansion", b),
  });
async function accessPage() {
  const [d, staff] = await Promise.all([api("/admin/access"), api("/admin/staff")]);
  state.access = d;
  state.staff = staff;
  return (
    title(
      "ACCESS ADMINISTRATION",
      T("账号与权限", "Accounts & access"),
      T(
        "账户、岗位、诊所和生效期共同确定访问；授权变化撤销旧会话。",
        "Accounts, roles, clinics and validity define access. Authorization changes revoke existing sessions.",
      ),
      button(
        T("创建维护账号", "Create maintenance account"),
        "user-add",
        "",
        "primary",
        "plus",
      ) +
        button("登记内部员工", "staff-add", "", "primary", "plus") +
        button(T("授予岗位", "Assign role"), "role-grant", "", "", "shield") +
        button(
          T("核实患者绑定", "Verify patient link"),
          "patient-link",
          "",
          "",
          "users",
        ),
    ) +
    staffRosterPanel() +
    `<div class="callout gap">${T("管理员身份不自动授予临床签署或收退款权限。医师账号还必须绑定牙医档案，患者账号必须核实绑定本人资料。", "Administrators do not automatically receive clinical or payment permissions. Dentist accounts need a clinician link; patient accounts need a verified personal link.")}</div>${panel(
      T("账户", "Accounts"),
      table(
        [
          T("姓名 / 账号", "Name / username"),
          T("邮箱", "Email"),
          T("状态", "Status"),
          T("最近登录", "Last login"),
          "",
        ],
        d.users.map((u) => [
          `<div class="name">${esc(u.display_name)}</div><div class="second mono">${esc(u.username || "—")}</div>`,
          esc(u.email),
          badge(u.status),
          date(u.last_sign_in_at),
          u.id !== state.principal.id
            ? button(
                T(
                  u.status === "ACTIVE" ? "停用" : "启用",
                  u.status === "ACTIVE" ? "Disable" : "Enable",
                ),
                "user-toggle",
                u.id,
                "small",
              )
            : T("当前账号", "Current account"),
        ]),
      ),
    )}<div style="margin-top:22px">${panel(
      T("岗位与诊所授权", "Role and clinic assignments"),
      table(
        [
          T("账户", "Account"),
          T("角色", "Role"),
          T("诊所范围", "Clinic scope"),
          T("生效期", "Validity"),
          T("状态", "Status"),
          "",
        ],
        d.assignments.map((a) => [
          esc(a.display_name),
          esc(a.role_name),
          esc(
            state.boot.clinics.find((c) => c.id === a.clinic_id)?.name_zh ||
              T("全网", "Network"),
          ),
          esc(a.effective_from) + " — " + esc(a.effective_to || "∞"),
          badge(a.status),
          a.status === "ACTIVE" && a.user_id !== state.principal.id
            ? button(T("撤销", "Revoke"), "role-revoke", a.id, "small danger")
            : "",
        ]),
      ),
    )}</div><div style="margin-top:22px">${panel(
      T("机构核实的患者绑定", "Verified patient links"),
      table(
        [
          T("账号", "Account"),
          T("患者", "Patient"),
          T("核实方式", "Method"),
          T("核实时间", "Verified at"),
        ],
        d.links.map((l) => [
          esc(l.display_name),
          esc(l.patient_name),
          esc(l.verification_method),
          date(l.verified_at),
        ]),
      ),
    )}</div>`
  );
}
function staffRosterPanel() {
  const invite = state.staffInvitation;
  return `${invite ? `<div class="callout gap"><strong>${esc(invite.employee_id)} · 一次性激活码</strong><p class="mono" style="overflow-wrap:anywhere;margin:10px 0">${esc(invite.activation_code)}</p><p>请当面或经机构认可渠道交给本人。有效期至 ${esc(invite.expires_at)}；本页不永久保存明文激活码。</p>${button("已记录，隐藏激活码", "staff-hide-code", "", "small")}</div>` : ""}<div class="gap">${panel("内部员工身份名册", table(["员工编号 / 姓名", "岗位与诊所", "预登记联系方式", "账号状态", "操作"], state.staff.map(s => [
    `<div class="name mono">${esc(s.employee_code)}</div><div class="second">${esc(s.display_name)}</div>`,
    `${esc(s.role_name)}<div class="second">${esc(s.clinic_name || "总部 / 全网")}</div>`,
    `${esc(s.phone_e164)}<div class="second">${esc(s.email)}</div>`,
    badge(s.status) + `<div class="second">${s.claimed_user_id ? "已激活" : "待本人注册激活"}</div>`,
    s.status === "ACTIVE" ? (!s.claimed_user_id ? button("重签激活码", "staff-reissue", s.id, "small") : "") + button("停用", "staff-deactivate", s.id, "small danger") : "—",
  ])), button("登记内部员工", "staff-add", "", "", "plus"), "岗位代码：FD 前台 · DR 医师 · CS 收费 · MG 店长 · OP 总部运营 · FN 总部财务 · AD 管理员")}</div>`;
}
handlers["staff-hide-code"] = () => { state.staffInvitation = null; refresh(); };
handlers["staff-add"] = () => modal({
  name: "登记内部员工", description: "只登记已核实的在职人员。岗位从编号识别，权限以机构名册授权为准。",
  fields: [
    {name:"employee_id",label:"员工编号",help:"ADC-岗位代码-六位数字，例如 ADC-DR-000001"},
    {name:"name",label:"姓名"}, {name:"phone",label:"预登记手机号",type:"tel",help:"建议填写 +86 国家区号"},
    {name:"email",label:"预登记邮箱",type:"email"}, {...clinicField(),required:false,help:"诊所岗位必选；总部岗位留空"},
    {name:"dentist_id",label:"医师档案（仅 DR 岗位）",type:"select",required:false,options:opts(state.boot.dentists)},
  ], onSubmit: async b => { state.staffInvitation = await api("/admin/staff", {...b,action:"create"}); }
});
handlers["staff-reissue"] = async id => { state.staffInvitation = await api("/admin/staff",{action:"reissue",id}); await refresh(); };
handlers["staff-deactivate"] = id => modal({name:"停用员工身份",description:"将撤销未使用的激活码；如已激活，将停用账号并撤销其全部会话。",fields:[{name:"confirmed",label:"确认已完成机构离职/停用核实",type:"checkbox"}],onSubmit:async b => { if(!b.confirmed) throw new Error("请先确认机构核实结果"); await api("/admin/staff",{action:"deactivate",id}); }});
const userField = () => ({
  name: "user_id",
  label: T("目标账号", "Account"),
  type: "select",
  options: state.access.users.map((u) => ({
    value: u.id,
    label: u.display_name + " · " + (u.username || u.email),
  })),
});
handlers["user-add"] = () =>
  modal({
    name: T("创建机构账号", "Create an account"),
    fields: [
      { name: "display_name", label: T("姓名", "Name") },
      {
        name: "username",
        label: T(
          "登录账号（英文数字，3–60位）",
          "Username (3–60 letters/digits)",
        ),
      },
      { name: "email", label: T("邮箱", "Email"), type: "email" },
      {
        name: "password",
        label: T("初始密码（至少12位）", "Initial password (12+ characters)"),
        type: "password",
      },
    ],
    onSubmit: (b) => api("/admin/access", { ...b, action: "create_user" }),
  });
handlers["role-grant"] = () =>
  modal({
    name: T("授予岗位与有效范围", "Assign a role and scope"),
    fields: [
      userField(),
      {
        name: "role_id",
        label: T("岗位", "Role"),
        type: "select",
        options: state.access.roles.map((r) => ({
          value: r.id,
          label: r.name_zh,
        })),
      },
      {
        ...clinicField(),
        required: false,
        help: T(
          "门店岗位必须指定诊所；总部岗位可留空。",
          "Clinic roles require a clinic; network roles can leave blank.",
        ),
      },
      {
        ...dentistField(),
        required: false,
        help: T(
          "授予医师角色时必须选择对应医师档案。",
          "Required when assigning the dentist role.",
        ),
      },
      ...validityFields(),
    ],
    onSubmit: (b) => api("/admin/access", { ...b, action: "grant" }),
  });
handlers["user-toggle"] = (id) => {
  const u = state.access.users.find((u) => u.id === id);
  modal({
    name: T("调整账号状态", "Change account status"),
    description: u.display_name,
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/admin/access", {
        ...b,
        action: "status",
        user_id: id,
        status: u.status === "ACTIVE" ? "DISABLED" : "ACTIVE",
      }),
  });
};
handlers["role-revoke"] = (id) =>
  modal({
    name: T("撤销岗位授权", "Revoke role assignment"),
    description: T(
      "相关账号的旧会话将失效。",
      "Existing sessions for the account will be revoked.",
    ),
    fields: [reasonField()],
    onSubmit: (b) =>
      api("/admin/access", { ...b, action: "revoke", assignment_id: id }),
  });
handlers["patient-link"] = () =>
  modal({
    name: T("机构核实本人绑定", "Verify a personal patient link"),
    fields: [
      userField(),
      {
        name: "patient_id",
        label: T(
          "前台核实提供的患者内部编号",
          "Verified patient internal ID from the front desk",
        ),
      },
      {
        name: "identity_verified",
        label: T(
          "已核对账号持有人与患者为同一人",
          "The account holder and patient were verified as the same person",
        ),
        type: "checkbox",
      },
      {
        name: "evidence",
        label: T("核实方式与依据", "Verification method and evidence"),
        type: "textarea",
      },
    ],
    onSubmit: (b) => api("/admin/access", { ...b, action: "patient_link" }),
  });
async function auditPage() {
  const d = await api("/audit" + query());
  return (
    title(
      "ACCOUNTABILITY",
      T("操作审计", "Audit history"),
      T(
        "成功操作与拒绝路径分别留痕。日志不复制明文密码、验证码或完整病历。",
        "Successful and denied actions are recorded without passwords, OTPs or full clinical text.",
      ),
    ) +
    filters() +
    panel(
      T("最近操作事件", "Recent audit events"),
      table(
        [
          T("时间", "Time"),
          T("操作者", "Actor"),
          T("操作", "Action"),
          T("对象", "Entity"),
          T("结果", "Outcome"),
          T("请求编号", "Request"),
        ],
        d.map((e) => [
          date(e.occurred_at),
          esc(e.actor_name || T("系统", "System")),
          `<span class="mono">${esc(e.action)}</span>`,
          esc(e.entity_type) +
            `<div class="second mono">${esc(e.entity_id)}</div>`,
          badge(e.outcome) +
            (e.reason ? `<div class="second">${esc(e.reason)}</div>` : ""),
          `<span class="mono">${esc(e.request_id.slice(0, 13))}…</span>`,
        ]),
      ),
    )
  );
}
async function portalPage() {
  const d = await api("/portal");
  state.portal = d;
  const p = d.patient;
  return (
    title(
      "YOUR CARE",
      T("您好，", "Hello, ") + p.name_zh,
      T(
        "这里汇集您本人经机构核实的预约、就诊摘要与诊疗账单。",
        "Your verified appointments, care summaries and dental bills in one place.",
      ),
    ) +
    `<div class="hero-strip"><div><h2>${T("照护，从清楚了解开始。", "Good care begins with clarity.")}</h2><p>${esc(p.patient_code)} · ${T("如需变更预约，请联系服务诊所。", "Contact your clinic to change an appointment.")}</p></div><div class="hero-emblem">${icon("heart")}</div></div><div class="metric-grid gap">${metric(T("本人预约", "My appointments"), d.appointments.length, T("仅显示已核实绑定的本人", "Verified personal records only"), "calendar", true)}${metric(T("就诊记录", "Care visits"), d.visits.length, T("临床摘要，不含内部备注", "Summaries without internal notes"), "tooth")}${metric(T("诊疗账单", "Care bills"), d.invoices.length, T("逐项结算，可向诊所核对", "Contact the clinic with billing questions"), "receipt")}${metric(T("待付余额", "Outstanding"), money(d.invoices.reduce((n, i) => n + Number(i.balance_fen), 0)), T("以诊所核实单据为准", "Subject to verified clinic records"), "wallet")}</div>${panel(
      T("我的预约", "My appointments"),
      table(
        [
          T("预约", "Appointment"),
          T("时间", "Time"),
          T("诊所", "Clinic"),
          T("牙医 / 项目", "Dentist / treatment"),
          T("状态", "Status"),
        ],
        d.appointments.map((a) => [
          `<span class="mono">${esc(a.appointment_code)}</span>`,
          date(a.scheduled_start_at),
          esc(a.clinic_name),
          esc(a.dentist_name) +
            `<div class="second">${esc(a.treatment_name)}</div>`,
          badge(a.status),
        ]),
      ),
    )}<div class="grid2" style="margin-top:22px">${panel(
      T("就诊摘要", "Care summaries"),
      table(
        [T("就诊编号", "Visit"), T("开始", "Started"), T("状态", "Status")],
        d.visits.map((v) => [
          `<span class="mono">${esc(v.visit_code)}</span>`,
          date(v.started_at),
          badge(v.status),
        ]),
      ),
    )}${panel(
      T("本人账单", "My bills"),
      table(
        [
          T("单据", "Bill"),
          T("金额", "Amount"),
          T("余额", "Balance"),
          T("状态", "Status"),
        ],
        d.invoices.map((i) => [
          `<span class="mono">${esc(i.invoice_code)}</span>`,
          money(i.total_fen),
          money(i.balance_fen),
          badge(i.status),
        ]),
      ),
    )}</div><div class="callout" style="margin-top:22px">${T("本入口不能通过输入他人编号查阅资料。如身份信息有误，请联系机构核实；涉及诊疗判断或身体不适，请联系专业医护人员。", "You cannot access another person’s records by entering an identifier. Contact the clinic to correct identity details or discuss any clinical concerns.")}</div>`
  );
}
function securityPage() {
  return (
    title(
      "ACCOUNT SECURITY",
      T("账号安全", "Account security"),
      T(
        "岗位与访问范围由机构授权，密码更新后旧会话将失效。",
        "Roles are assigned by the organization. Changing a password revokes existing sessions.",
      ),
    ) +
    `<div class="grid2">${panel(T("当前身份", "Current identity"), `<div class="card-pad"><div class="person-heading"><span class="avatar">${esc(state.principal.name.slice(0, 1))}</span><div><h2 style="margin:0">${esc(state.principal.name)}</h2><p>${esc(state.principal.roles.map((r) => r.name_zh).join(" · "))}</p></div></div><div class="divider"></div><p class="subline">${T("授权诊所：", "Authorized clinics: ")}${esc(state.boot.clinics.map((c) => c.name_zh).join(" · "))}</p><div class="rights-list">${state.principal.permissions.map((p) => `<span class="badge mono">${esc(p)}</span>`).join("")}</div></div>`)}${panel(T("密码与登录", "Password and sign-in"), `<div class="card-pad"><p class="muted">${T("密码至少 12 个字符，仅保存单向摘要。合成演示身份不设置公开密码；真实账号可由管理员创建并分配岗位。", "Passwords use a one-way hash and at least 12 characters. Synthetic demo identities have no public password; administrators create real accounts and assign roles.")}</p>${button(T("更改本人密码", "Change my password"), "change-password", "", "primary", "lock")}<div class="divider"></div><p class="subline">${T("支持账号、已验证手机号或邮箱登录。验证码与找回密码使用机构配置的真实发送服务；未验证的联系方式不会作为登录凭据。", "Mobile recovery, SMS and WeChat require organization configuration. Unconfigured providers never report simulated success.")}</p></div>`)}</div>`
  );
}
handlers["change-password"] = () =>
  modal({
    name: T("更改本人密码", "Change your password"),
    description: T(
      "保存后须重新登录，所有旧会话失效。",
      "Sign in again after saving. All existing sessions will be revoked.",
    ),
    fields: [
      {
        name: "oldPassword",
        label: T("原密码", "Current password"),
        type: "password",
      },
      {
        name: "newPassword",
        label: T("新密码（12–128位）", "New password (12–128 characters)"),
        type: "password",
      },
    ],
    onSubmit: async (b) => {
      await api("/auth/password", b);
      state.principal = null;
      state.boot = null;
      await loginPage();
    },
  });
installSetupHandlers({handlers,state,T,esc,api,modal,can,clinicField});
installFollowupHandlers({handlers,state,T,esc,api,modal,button,table,date,can,refresh});
start();
