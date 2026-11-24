// Shared display rules. Financial writes and clinical eligibility are rechecked by Java.
export function ageAt(birth, day) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(birth || '') || !/^\d{4}-\d{2}-\d{2}$/.test(day || '') || birth > day) return null;
  const [y,m,d] = birth.split('-').map(Number), [cy,cm,cd] = day.split('-').map(Number);
  const probe = new Date(Date.UTC(y,m-1,d));
  if (probe.getUTCMonth() !== m-1 || probe.getUTCDate() !== d) return null;
  return cy-y-Number(cm<m || (cm===m && cd<d));
}
export function demographics(p, day, T) {
  const birth=p.date_of_birth || p.patient_date_of_birth, gender=p.gender || p.patient_gender;
  const sex = {FEMALE:T('女','Female'),MALE:T('男','Male'),OTHER:T('其他','Other')}[gender] || T('性别待补充','Gender not recorded');
  const age=ageAt(birth,day);
  return sex+' · '+(age===null?T('生日待补充','Birthdate not recorded'):age+T('岁',' years'));
}
export const readOnlyTag = T => `<span class="readonly-tag">${T('只读','Read only')}</span>`;
export function invoiceActions(i, manage) {
  const active=i.status!=='VOID', net=Number(i.paid_fen)-Number(i.refunded_fen);
  // Missing explicit period state is never treated as permission to write.
  return {
    pay:!!manage && active && Number(i.balance_fen)>0 && i.cash_period_status==='OPEN',
    refund:!!manage && active && net>0 && i.cash_period_status==='OPEN',
    void:!!manage && active && net===0 && i.source_period_status==='OPEN',
  };
}
export function appointmentBilling(a) {
  if(a.status!=='COMPLETED')return null;
  if(a.billing_state==='UNBILLED')return a.billing_source_period_status==='OPEN'?{label:'核对开单',en:'Review & issue',primary:true}:{label:'查看收费项目',en:'Review bill items',primary:false};
  if(a.billing_state==='PAID')return {label:'查看账单',en:'View bill',primary:false,paid:true};
  if(a.billing_state==='VOID')return {label:'查看作废单',en:'View void bill',primary:false};
  if(Number(a.billing_balance_fen)>0)return a.billing_cash_period_status==='OPEN'?{label:'收款',en:'Take payment',primary:true}:{label:'查看账单',en:'View bill',primary:false};
  return a.billing_state ? {label:'查看收费',en:'View billing',primary:false} : null;
}
export function barChart(items,{esc,T,money,title}) {
  const max=Math.max(1,...items.map(i=>Math.abs(Number(i.value)||0)));
  return `<figure class="business-chart"><figcaption>${esc(title)}</figcaption><div class="business-bars">${items.map(i=>`<div class="business-bar"><span>${esc(i.label)}</span><div class="business-track" aria-hidden="true"><i class="${i.tone||''}" style="width:${Math.max(0,Math.min(100,Math.abs(Number(i.value)||0)/max*100))}%"></i></div><strong>${esc(money(i.value))}</strong></div>`).join('')}</div></figure>`;
}

const pastAppointmentLabels = {
  CONFIRMED: ["到诊结果待核实", "Attendance to verify"],
  CHECKED_IN: ["未登记开始接诊", "Visit start not recorded"],
  IN_PROGRESS: ["未登记诊疗完成", "Completion not recorded"],
};

export function appointmentReview(a, T) {
  if (a.review_state === "HISTORICAL_OPEN") {
    const [zh, en] = pastAppointmentLabels[a.status] ?? ["预约结果待核实", "Appointment outcome to verify"];
    return `<span class="badge amber appointment-review">${T(zh,en)}</span>`;
  }
  if (a.review_state === "VISIT_MISMATCH")
    return `<span class="badge red appointment-review">${T("关联待核实","Link requires review")}</span>`;
  return "";
}

export function appointmentBreakdown(rows) {
  const known = [
    ["CONFIRMED", "待签到", "Expected", "expected"],
    ["CHECKED_IN", "候诊", "Waiting", "waiting"],
    ["IN_PROGRESS", "诊疗中", "In care", "care"],
    ["COMPLETED", "已完成", "Completed", "complete"],
    ["CANCELLED", "已取消", "Cancelled", "cancelled"],
    ["NO_SHOW", "未到诊", "No-show", "no-show"],
  ];
  const counts = new Map(rows.map(row => [row.status, Number(row.value)]));
  const extra = [...counts.keys()].filter(status => !known.some(([id]) => id === status))
    .map(status => [status, status, status, "other"]);
  const states = [...known, ...extra].map(([id, zh, en, tone]) => ({id, zh, en, tone, count: counts.get(id) || 0}));
  return {states,total:states.reduce((sum,state)=>sum+state.count,0)};
}

function visitDonut({states,total},selection,{T,esc,num}) {
  let offset = 0;
  const rings = states.filter(s=>s.count>0).map(s=>{
    const segment = s.count / total * 100;
    const ring = `<circle class="donut-segment ${s.tone}" data-count="${s.count}" cx="75" cy="75" r="61" pathLength="100" stroke-dasharray="${segment} 100" stroke-dashoffset="${-offset}"/>`;
    offset += segment;
    return ring;
  }).join("");
  return `<div class="day-status-layout">
    <div class="day-status-grid">${states.map(s=>`<button type="button" class="day-status ${s.tone}" data-act="operations-status" data-id="${esc(s.id)}" aria-pressed="${s.id===selection}"><span class="day-status-label"><i></i>${esc(T(s.zh,s.en))}</span><strong>${num(s.count)}</strong><small>${total ? new Intl.NumberFormat(undefined,{style:'percent',maximumFractionDigits:1}).format(s.count/total) : "0%"}</small></button>`).join("")}</div>
    <div class="day-donut" data-total="${total}"><svg viewBox="0 0 150 150" aria-hidden="true"><circle class="donut-track" cx="75" cy="75" r="61"/><g transform="rotate(-90 75 75)">${rings}</g></svg><div class="day-donut-center"><strong>${num(total)}</strong><span>${T("预约总数","Total bookings")}</span></div></div>
  </div>`;
}

export function renderClinicDay(m,h) {
  const {esc,T,button,link,icon,money,num,table,badge,can,appointmentActions,demographics}=h;
  const {day,today,data,all,agenda,selection}=m;
  const breakdown = appointmentBreakdown(data.appointment_states);
  const total = breakdown.total;
  const n = id => breakdown.states.find(s=>s.id===id)?.count || 0;
  const contact=all.filter(a=>a.status==='CONFIRMED'&&a.confirmation_state!=='CONFIRMED').length;
  const unbilled=m.unbilledCount;
  const tasks=[...(can('appointment.manage')?[{label:T('预约待联系确认','Patient confirmations'),value:contact,action:'operations-contact',id:''}]:[]),
    {label:T('候诊患者','Patients waiting'),value:n('CHECKED_IN'),action:'operations-status',id:'CHECKED_IN'},
    ...(can('finance.read')?[{label:T('就诊待核对开单','Care ready for billing'),value:unbilled,action:'operations-billing',id:''}]:[])];
  const dateNav=`<div class="day-date-control"><div class="day-date-buttons">${button(T('前一天','Previous'),'operations-day','-1','small')}${button(T('今天','Today'),'operations-day','today','small')}${button(T('后一天','Next'),'operations-day','1','small')}</div><label><span class="sr-only">${T('业务日期','Service date')}</span><input id="operations-date" class="field-input" type="date" value="${esc(day)}"></label></div>`;
  const queue=table([T('时间','Time'),T('患者 / 项目','Patient / treatment'),T('医师 / 牙椅','Clinician / chair'),T('状态','Status'),T('操作','Actions')],agenda.map(a=>[
    `<time class="day-time">${esc(a.scheduled_start_at.slice(11,16))}</time><span class="second">${a.duration_minutes} ${T('分钟','min')}</span>`,
    `<div class="register-person"><span class="person-mark" aria-hidden="true">${esc(a.patient_name.slice(0,1))}</span><div><div class="person-heading"><strong>${esc(a.patient_name)}</strong><span>${esc(demographics(a,today,T))}</span></div><div class="second">${esc(a.treatment_name)}</div></div></div>`,
    `<span>${esc(a.dentist_name)}</span><div class="second">${esc(a.chair_name||T('未分配牙椅','Chair unassigned'))}</div>`,badge(a.status)+appointmentReview(a,T),
    appointmentActions(a),
  ]));
  const cash=data.finance;
  return `<div class="day-page-heading"><div><h1>${T('诊所运营','Clinic operations')}</h1><p>${esc(data.clinics.map(c=>c.name_zh).join(' · '))}</p></div><div class="day-heading-actions">${dateNav}${can('patient.manage')?button(T('新建患者','New patient'),'new-patient','','','users'):''}${can('appointment.manage')?button(T('新建预约','New appointment'),'new-appointment','','primary','plus'):''}</div></div>
    <section class="clinic-day-overview metric-strip" aria-label="${T('门诊进度','Clinic progress')}"><div class="day-overview-heading"><h2>${T('门诊进度','Clinic progress')}</h2></div>${visitDonut(breakdown,selection,{T,esc,num})}</section>
    <div class="day-work-layout"><section class="day-register"><header><div><h2>${T('当日预约与接待','Appointments and reception')}</h2><span>${agenda.length} / ${total} ${T('条预约','bookings')}${selection?' · '+T('已按状态筛选','Filtered by status'):''}</span></div><div class="row">${selection?button(T('全部状态','All statuses'),'operations-status','','small'):''}${button(T('前台队列','Reception'),'operations-desk','','small')}${button(T('预约日历','Calendar'),'operations-calendar','','small')}</div></header>${agenda.length?queue:`<div class="empty"><p>${T('当前日期和状态下暂无预约。可更换日期或安排新预约。','No bookings for this date and state. Change the date or book an appointment.')}</p></div>`}</section>
    <aside class="day-rail"><section class="day-tasks"><h2>${T('需要处理','To attend')}</h2>${tasks.map(t=>`<button type="button" data-act="${t.action}" data-id="${t.id}"><span>${t.label}</span><strong>${num(t.value)}</strong>${icon('chevron')}</button>`).join('')}</section>
    ${cash?`<section class="day-cash"><div class="row between"><h2>${day===today?T('今日收款','Receipts today'):T('当日收款','Receipts on date')}</h2>${link(T('账单','Bills'),'billing')}</div><strong class="day-cash-amount">${money(cash.net_cash_fen)}</strong><p>${T('净收款，已扣除当日退款','Net receipts, less refunds on this date')}</p><div class="day-receivable"><span>${T('当前待收','Outstanding')}</span><strong>${money(cash.receivable_fen)}</strong></div></section>`:''}
    <section class="day-quicklinks"><h2>${T('日常管理','Practice management')}</h2>${can('resource.manage')?`<button type="button" data-act="operations-resources" data-id="schedule">${T('排班与停诊','Schedules & closures')}${icon('chevron')}</button><button type="button" data-act="operations-resources" data-id="chairs">${T('牙椅与设备','Chairs & equipment')}${icon('chevron')}</button>`:''}${can('followup.read')?link(T('复诊与候补','Recalls and waitlist'),'waitlist'):''}${can('analytics.read')?link(T('经营统计','Analytics'),'analytics'):''}</section></aside></div>`;
}

export function renderAnalytics(d,m,h) {
  const {esc,T,button,table,num,pct,date}=h;
  const maxUnits=Math.max(1,...d.treatments.map(t=>Number(t.units)));
  const active=d.dentists.filter(p=>Number(p.appointments)>0),inactive=d.dentists.filter(p=>!Number(p.appointments));
  const dentistTable=rows=>table([T('医师','Clinician'),T('同期预约','Bookings'),T('已完成','Completed'),T('已取消','Cancelled')],rows.map(p=>[esc(p.name_zh),num(p.appointments),num(p.completed),num(p.cancelled)]));
  const kpis=[{name:T('同期计划服务','Scheduled services'),value:num(d.appointments),note:T('按计划服务日','By scheduled date')},
    {name:T('主动取消率','Cancellation rate'),value:pct(d.cancellation_rate),note:`${num(d.cancellations)} / ${num(d.appointments)}`},
    {name:T('未到诊率','No-show rate'),value:pct(d.no_show_rate),note:`${num(d.no_shows)} / ${num(Number(d.appointments)-Number(d.cancellations))}`},
    {name:T('临床完成率','Clinical completion'),value:pct(d.clinical_completion_rate),note:T('完成 / 有效已建立就诊','Completed / valid encounters')}];
  return `<section class="analysis-metrics metric-strip" aria-label="${T('关键指标','Key metrics')}">${kpis.map((k,i)=>`<div class="analysis-metric ${i===0?'primary':''}"><span>${k.name}</span><strong>${k.value}</strong><small>${k.note}</small></div>`).join('')}</section>
    <div class="analysis-top"><section class="analysis-treatment"><header><h2>${T('实际治疗结构','Treatment mix')}</h2><span>${T('按实施单位数对比','By recorded units')}</span></header>${d.treatments.length?`<div class="treatment-comparison">${d.treatments.map(t=>`<div class="treatment-comparison-row"><div><strong>${esc(t.name_zh)}</strong><span>${num(t.treatments)} ${T('条实施记录','recorded entries')}</span></div><div class="treatment-chart-track" aria-hidden="true"><i style="width:${Number(t.units)/maxUnits*100}%"></i></div><strong class="treatment-unit">${num(t.units)}<small>${T('单位','units')}</small></strong></div>`).join('')}</div>`:`<div class="empty">${T('所选期间暂无已实施治疗','No treatments in this period')}</div>`}</section>
    <section class="analysis-capacity"><header><h2>${T('牙椅使用情况','Chair utilization')}</h2><span>${T('已占用 / 可用时长','Occupied / available time')}</span></header><div class="capacity-comparison">${d.utilization.map(c=>`<article><div class="capacity-heading"><strong>${esc(c.clinic_name)}</strong><span>${pct(c.rate)}</span></div><div class="capacity-track" aria-hidden="true"><i style="width:${Math.min(100,Math.max(0,Number(c.rate||0)*100))}%"></i></div><div class="capacity-axis" aria-hidden="true"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div><div class="capacity-facts"><span>${num(c.occupied_chair_minutes)} ${T('分钟已占用','minutes occupied')}</span><span>${num(c.available_chair_minutes)} ${T('分钟可用','minutes available')}</span></div></article>`).join('')||`<p>${T('暂无可用时长数据','No capacity data')}</p>`}</div></section></div>
    <section class="analysis-doctors"><header><div><h2>${T('医师预约履约','Clinician appointment outcomes')}</h2><p>${T('按预约的计划服务日期统计。','By the scheduled service date.')}</p></div><span>${active.length} ${T('位医师有预约','clinicians with bookings')}</span></header>${dentistTable(active)}${inactive.length?`<details class="inactive-clinicians"><summary>${T('查看无同期预约的医师','View clinicians with no bookings')} (${inactive.length})</summary>${dentistTable(inactive)}</details>`:''}</section>
    <section class="analysis-coverage"><header><h2>${T('服务日资质覆盖','Service-date qualification coverage')}</h2><span>${T('按有效资质及任职核对','Effective credentials and assignments')}</span></header>${table([T('诊所','Clinic'),T('治疗项目','Treatment'),T('合格医师','Qualified clinicians'),T('判定日期','Service date')],d.coverage.map(c=>[esc(c.clinic_name),esc(c.treatment_name),Number(c.qualified_dentists)===0?`<span class="badge red">${T('暂无覆盖','Coverage gap')}</span>`:num(c.qualified_dentists),esc(c.service_date)]))}</section>
    <details class="analysis-definitions"><summary>${T('统计口径与生成时间','Metric definitions and generation time')}</summary><ul>${d.definitions.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>${T('生成于','Generated at')} ${date(d.generated_at)}</p></details>`;
}
