import { queueSummary, filterQueue, billSummary, filterBills } from "./practice-workflow.js?v=20261113-workflow";
import {appointmentBilling,demographics,readOnlyTag,invoiceActions,barChart,appointmentReview} from './staff-ux.js?v=20261121-review';

export function appointmentActions(a,{T,button,today,canManage=false,canBill=false,canClinical=false,ownDentist=null}) {
  let actions='';
  if(canManage&&a.status==='CONFIRMED') {
    if(String(a.scheduled_start_at).slice(0,10)===today)actions+=button(T('签到','Check in'),'desk-checkin',a.id,'small primary');
    actions+=button(T('改期','Reschedule'),'desk-reschedule',a.id,'small');
    actions+=button(T('更多操作','More actions'),'appointment-menu',a.id,'small');
  } else if(canManage&&a.status==='CHECKED_IN')actions+=button(T('撤销签到','Revoke check-in'),'desk-revoke',a.id,'small');
  const bill=canBill?appointmentBilling(a):null;
  if(bill)actions+=(bill.paid?'<span class="badge green">'+T('已结清','Paid')+'</span>':'')+button(T(bill.label,bill.en),'appointment-billing',a.id,'small '+(bill.primary?'primary':''));
  const ownCare=canClinical&&(!ownDentist||ownDentist===a.dentist_id);
  if(ownCare&&['CHECKED_IN','IN_PROGRESS'].includes(a.status))actions+=button(ownDentist?T(a.status==='IN_PROGRESS'?'继续接诊':'接诊',a.status==='IN_PROGRESS'?'Continue care':'Attend patient'):T('查看接诊','View encounter'),'appointment-care',a.id,'small '+(ownDentist?'primary':''));
  if(!canManage&&!canBill&&!ownCare)actions+=readOnlyTag(T);
  return `<div class="appointment-row-actions">${actions}${button(T('详情','Details'),'appointment-detail',a.id,'small ghost')}</div>`;
}

export function orderedAgenda(rows, limit = 6) {
  const time = row => String(row.scheduled_start_at || "9999").replace("T", " ");
  return [...rows].sort((a, b) => time(a).localeCompare(time(b)) || String(a.id || "").localeCompare(String(b.id || ""))).slice(0, limit);
}

export function receptionContent({ rows, day, today=day, clinic, clinics, selection, canManage, canCreatePatient, search, doctor, recentDate }, { esc, T, button, badge, table, link }) {
  const totals = queueSummary(rows);
  const waitingForReply = a => a.status === "CONFIRMED" && a.confirmation_state !== "CONFIRMED";
  const reviewCount = rows.filter(a => Boolean(a.review_state)).length;
  const status = selection === "CONTACT" ? "CONFIRMED" : selection === "REVIEW" ? "" : selection;
  const shown = filterQueue(rows, { status, dentist: doctor, search })
    .filter(a => selection === "CONTACT" ? waitingForReply(a) : selection !== "REVIEW" || Boolean(a.review_state));
  const views = [
    ["", T("全部", "All"), totals.all],
    ["CONFIRMED", T("待签到", "Expected"), totals.expected],
    ["CONTACT", T("待确认", "To confirm"), rows.filter(waitingForReply).length],
    ["CHECKED_IN", T("候诊", "Waiting"), totals.waiting],
    ["IN_PROGRESS", T("诊疗中", "In care"), totals.care],
    ["COMPLETED", T("已完成", "Completed"), totals.complete],
    ["EXCEPTIONS", T("取消 / 未到诊", "Cancelled / no-show"), totals.exceptions],
    ...(reviewCount || selection === "REVIEW" ? [["REVIEW", T("待核实", "Needs review"), reviewCount]] : []),
  ];
  const doctors = [...new Map(rows.map(a => [a.dentist_id, a.dentist_name]))];
  const actions = link(T("预约日历", "Appointment calendar"), "appointments") +
    (canCreatePatient ? button(T("新建患者", "New patient"), "new-patient", "", "", "users") : "") +
    (canManage ? button(T("新建预约", "New appointment"), "new-appointment", "", "primary", "plus") : "");
  const list = shown.length
    ? table([T("时间", "Time"), T("患者", "Patient"), T("医师 / 项目", "Clinician / treatment"), T("状态", "Status"), ""], shown.map(a => [
        `<strong class="desk-time">${esc(a.scheduled_start_at.slice(11, 16))}</strong><div class="second">${esc(a.scheduled_end_at.slice(11, 16))}</div>`,
        `<strong class="name">${esc(a.patient_name)}</strong><span class="patient-demographics">${esc(demographics(a,today,T))}</span><div class="second">${esc(a.appointment_code)}</div>`,
        `${esc(a.dentist_name)}<div class="second">${esc(a.treatment_name)} · ${esc(a.chair_name || T("未分配牙椅", "Chair unassigned"))}</div>`,
        badge(a.status) + appointmentReview(a,T) + (a.status === "CONFIRMED" ? `<div class="second">${a.confirmation_state === "CONFIRMED"
          ? T("患者已确认", "Patient confirmed")
          : a.confirmation_state === "UNREACHABLE" ? T("未联系上", "Unreachable") : T("待联系", "Contact pending")}</div>` : ""),
        appointmentActions(a,{T,button,today,canManage}),
      ]))
    : `<div class="desk-empty"><h3>${rows.length ? T("没有符合条件的预约", "No matching appointments") : T("这一天没有预约", "No appointments on this date")}</h3>${rows.length
      ? button(T("清除筛选", "Clear filters"), "desk-reset", "", "small")
      : recentDate ? button(T("查看最近有预约的日期", "View latest booked date"), "desk-reference", recentDate, "small") : ""}</div>`;
  return `<div class="desk-heading"><div><h1>${T("前台接待", "Reception")}</h1><p class="desk-date-context"><time datetime="${esc(day)}">${esc(day)}</time></p></div><div class="row wrap">${actions}</div></div>
    <div class="reception-controls"><div class="desk-daybar"><div class="row wrap">${button(T("前一天", "Previous"), "desk-day", "-1", "small")}${button(T("今天", "Today"), "desk-day", "today", "small")}${button(T("后一天", "Next"), "desk-day", "1", "small")}</div></div>
    <form id="desk-filter" class="desk-filter">
      ${clinics.length > 1 ? `<label><span>${T("诊所", "Clinic")}</span><select name="clinic_id" class="field-input"><option value="">${T("全部诊所", "All clinics")}</option>${clinics.map(c => `<option value="${esc(c.id)}" ${c.id === clinic ? "selected" : ""}>${esc(c.name_zh)}</option>`).join("")}</select></label>` : ""}
      <label><span>${T("日期", "Date")}</span><input type="date" name="day" class="field-input" value="${esc(day)}" required></label>
      <label><span>${T("医师", "Clinician")}</span><select class="field-input" name="doctor"><option value="">${T("全部医师", "All clinicians")}</option>${doctors.map(([id, name]) => `<option value="${esc(id)}" ${doctor === id ? "selected" : ""}>${esc(name)}</option>`).join("")}</select></label>
      <label class="desk-search"><span>${T("搜索预约", "Search appointments")}</span><input class="field-input" name="search" value="${esc(search)}" placeholder="${T("患者姓名、预约编号或项目", "Patient, appointment number or treatment")}"></label>
      <button class="btn" type="submit">${T("查询", "Search")}</button>${search || doctor || selection ? button(T("清除筛选", "Clear filters"), "desk-reset", "", "ghost") : ""}
    </form></div>
    <section class="desk-register reception-register">
      <div class="reception-register-bar">
        <div class="worklist-tabs" aria-label="${T("预约状态", "Appointment status")}">${views.map(([id, label, count]) => `<button type="button" data-act="desk-view" data-id="${id}" aria-pressed="${selection === id}" class="${selection === id ? "selected" : ""}">${label}<span>${count}</span></button>`).join("")}</div>
        <div class="worklist-caption" role="status"><span>${shown.length} / ${rows.length} ${T("条预约", "appointments")}</span>${rows.length === 600 ? `<span>${T("请按诊所缩小查询范围", "Filter by clinic to see all results")}</span>` : ""}</div>
      </div>
      ${selection === "REVIEW" ? `<div class="worklist-caption">${T(
        "这里显示已过预约日期但尚未登记结果的记录，以及预约与就诊记录不一致的记录。可打开详情核对。",
        "Here are past appointments without a recorded outcome and appointments whose visit records need checking. Open Details to review.",
      )}</div>` : ""}
      ${list}
    </section>`;
}

export function billingContent({ invoices, unbilled, view, search, canManage }, { esc, T, title, button, link, badge, table, money, date, filters }) {
  const totals = billSummary(invoices);
  const keyword = search.trim().toLocaleLowerCase();
  const selected = view || (unbilled.length ? "UNBILLED" : totals.outstanding ? "OUTSTANDING" : "ALL");
  const pending = unbilled.filter(v => !keyword || [v.patient_name, v.visit_code, v.dentist_name].some(value => String(value || "").toLocaleLowerCase().includes(keyword)));
  const bills = filterBills(invoices, { status: selected === "UNBILLED" ? "ALL" : selected, search });
  const tabs = [
    ["UNBILLED", T("待开单", "Unbilled"), unbilled.length],
    ["OUTSTANDING", T("待收款", "Outstanding"), totals.outstanding],
    ["ALL", T("全部单据", "All bills"), invoices.length],
    ["PAID", T("已结清", "Paid"), invoices.filter(i => i.status === "PAID").length],
    ["VOID", T("已作废", "Void"), invoices.filter(i => i.status === "VOID").length],
  ];
  const shown = selected === "UNBILLED" ? pending : bills;
  let list;
  if (!shown.length) {
    const message = keyword ? T("没有符合条件的记录", "No matching records") :
      selected === "UNBILLED" ? T("暂无待开单就诊", "No unbilled visits") :
      selected === "OUTSTANDING" ? T("暂无待收款单据", "No outstanding bills") : T("暂无单据", "No bills");
    list = `<div class="desk-empty"><h3>${message}</h3>${keyword ? button(T("清除搜索", "Clear search"), "billing-reset", "", "small") : ""}</div>`;
  } else if (selected === "UNBILLED") {
    list = table([T("患者", "Patient"), T("就诊编号", "Visit number"), T("医师", "Clinician"), T("完成时间", "Completed"), ""], pending.map(v => [
      `<strong>${esc(v.patient_name)}</strong>`, esc(v.visit_code), esc(v.dentist_name), date(v.completed_at),
      canManage ? button(v.source_period_status==='OPEN'?T("核对并开单", "Review & issue"):T("查看收费项目", "View bill items"), "invoice-issue", v.id, "small "+(v.source_period_status==='OPEN'?'primary':''))+(v.source_period_status!=='OPEN'?`<span class="record-lock">${T('期间未开放','Period not open')}</span>`:'') : readOnlyTag(T),
    ]));
  } else {
    list = table([T("单据 / 患者", "Bill / patient"), T("诊所", "Clinic"), T("应收", "Due"), T("已收（扣退款）", "Net received"), T("待收", "Balance"), T("状态", "Status"), ""], bills.map(i => [
      `<strong>${link(i.invoice_code, "billing/" + i.id)}</strong><div class="second">${esc(i.patient_name)} · ${esc(i.visit_code)}</div>`,
      esc(i.clinic_name), money(i.total_fen), money(Number(i.paid_fen) - Number(i.refunded_fen)), money(i.balance_fen), badge(i.status),
      invoiceActions(i,canManage).pay
        ? button(T("登记收款", "Record payment"), "invoice-pay", i.id, "small primary")
        : (!canManage?readOnlyTag(T):'')+link(T("查看单据", "Open bill"), "billing/" + i.id),
    ]));
  }
  return title("REVENUE CONTROL", T("收费", "Billing"), "", button(T("导出台账", "Export ledger"), "billing-export", "", "", "download")) +
    filters() + `<div class="billing-overview">${barChart([{label:T('应收','Billed'),value:totals.issued},{label:T('已收（扣退款）','Net received'),value:totals.net,tone:'received'},{label:T('待收','Outstanding'),value:totals.balance,tone:'outstanding'}],{esc,T,money,title:T('当前单据汇总','Current bill totals')})}<div class="billing-shortcuts"><h2>${T('收费待办','Billing work')}</h2><button type="button" data-act="billing-view" data-id="UNBILLED"><span>${T('待核对开单','Review unbilled care')}</span><strong>${unbilled.length}</strong></button><button type="button" data-act="billing-view" data-id="OUTSTANDING"><span>${T('待收款单据','Bills with a balance')}</span><strong>${totals.outstanding}</strong></button><p>${T('先核对实际治疗，再开单收款。已结清账单可查看明细和办理授权退款。','Review actual treatment before issuing a bill. Paid bills remain available for review and authorized refunds.')}</p></div></div>` +
    `<section class="desk-register billing-worklist">
      <div class="worklist-tabs" aria-label="${T("收费清单", "Billing lists")}">${tabs.map(([id, name, count]) => `<button type="button" data-act="billing-view" data-id="${id}" aria-pressed="${selected === id}" class="${selected === id ? "selected" : ""}">${name}<span>${count}</span></button>`).join("")}</div>
      <form id="billing-search" class="worklist-search"><label for="bill-keyword">${T("搜索", "Search")}</label><input id="bill-keyword" name="search" class="field-input" value="${esc(search)}" placeholder="${T("患者姓名、单据或就诊编号", "Patient, bill or visit number")}"><button class="btn" type="submit">${T("查询", "Search")}</button>${keyword ? button(T("清除", "Clear"), "billing-reset", "", "ghost") : ""}<span>${shown.length} ${T("条", "records")}</span></form>
      ${list}
      ${invoices.length === 400 || unbilled.length === 300 ? `<div class="worklist-footer">${T("结果已达上限。请选择诊所缩小范围。", "Filter by clinic to see more results.")}</div>` : ""}
    </section>
    <details class="billing-summary"><summary>${T("收费汇总", "Billing totals")}</summary>
      <div class="billing-balance-band">
        <div><span>${T("应收合计", "Total due")}</span><strong>${money(totals.issued)}</strong></div>
        <div><span>${T("已收（扣退款）", "Receipts less refunds")}</span><strong>${money(totals.net)}</strong></div>
        <div><span>${T("待收合计", "Outstanding")}</span><strong>${money(totals.balance)}</strong></div>
      </div>
    </details>`;
}
