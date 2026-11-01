// Read-only projections of persisted records. The Java services remain authoritative for all writes.
const working=['CONFIRMED','CHECKED_IN','IN_PROGRESS'];
export function appointmentHistoryEvent(record,T){
  let metadata={};
  try{const value=JSON.parse(record.metadata_json||'{}');if(value&&typeof value==='object'&&!Array.isArray(value))metadata=value;}catch{}
  let evidence=String(record.reason_text||''),channel=metadata.channel,result=metadata.confirmation_state;
  // Earlier 1.5 review builds encoded these three values in the reason. Present them
  // without rewriting the retained evidence in storage.
  const legacy=evidence.match(/^(PHONE|EMAIL|SMS|IN_PERSON) · (PENDING|CONFIRMED|UNREACHABLE) · ([\s\S]*)$/);
  if(legacy){channel=legacy[1];result=legacy[2];evidence=legacy[3];}
  if(metadata.event_type==='PATIENT_CONFIRMATION'||legacy){
    const channels={PHONE:['电话','Phone'],EMAIL:['邮箱','Email'],SMS:['短信','SMS'],IN_PERSON:['当面','In person']};
    const results={PENDING:['待确认','Pending'],CONFIRMED:['患者已确认','Patient confirmed'],UNREACHABLE:['未联系上','Unreachable']};
    return {title:T('患者联系确认','Patient contact confirmation'),detail:`${channels[channel]?T(...channels[channel]):T('联系途径待核对','Channel requires review')} · ${results[result]?T(...results[result]):T('结果待核对','Result requires review')}`,evidence};
  }
  const statuses={CONFIRMED:['已预约','Booked'],CHECKED_IN:['已到诊','Checked in'],IN_PROGRESS:['诊疗中','In care'],COMPLETED:['已完成','Completed'],CANCELLED:['已取消','Cancelled'],NO_SHOW:['未到诊','No-show'],HOLD:['暂留','On hold']};
  const status=v=>statuses[v]?T(...statuses[v]):T('历史状态待核对','Historical state requires review');
  if(!record.from_status)return {title:T('预约建立','Booking created'),detail:status(record.to_status),evidence};
  if(metadata.event_type==='RESCHEDULE')return {title:T('预约改期','Booking rescheduled'),detail:T('患者联系确认已重置为待确认','Patient confirmation reset to pending'),evidence};
  return {title:record.from_status===record.to_status?T('预约记录更新','Booking record updated'):T('预约状态变更','Booking state changed'),detail:record.from_status===record.to_status?status(record.to_status):`${status(record.from_status)} → ${status(record.to_status)}`,evidence};
}
export function appointmentTask(a) {
  return ({CONFIRMED:{code:'arrival',zh:'核对身份并办理到诊',en:'Verify identity and check in'},CHECKED_IN:{code:'waiting',zh:'等候负责医师接诊',en:'Waiting for the responsible clinician'},IN_PROGRESS:{code:'care',zh:'诊疗中，由医师记录本次实施',en:'Care in progress; clinician records treatment'},COMPLETED:{code:'handoff',zh:'诊疗已完成，交收费岗位核对',en:'Care complete; hand off for billing review'},CANCELLED:{code:'closed',zh:'已取消，保留发起方与原因',en:'Cancelled; reason and initiator retained'},NO_SHOW:{code:'closed',zh:'未到诊，查看核实记录',en:'No-show; review the recorded evidence'}})[a.status]||{code:'review',zh:'来源状态待核实，不直接办理到诊',en:'Legacy status needs review before check-in'};
}
export function queueSummary(rows) {
  const count=s=>rows.filter(a=>a.status===s).length;
  return {all:rows.length,expected:count('CONFIRMED'),waiting:count('CHECKED_IN'),care:count('IN_PROGRESS'),complete:count('COMPLETED'),exceptions:rows.filter(a=>['CANCELLED','NO_SHOW'].includes(a.status)).length,unassigned:rows.filter(a=>working.includes(a.status)&&!a.chair_id).length,legacy:rows.filter(a=>appointmentTask(a).code==='review').length};
}
export function filterQueue(rows,{status='',dentist='',search=''}={}) {
  const q=search.trim().toLocaleLowerCase();
  return rows.filter(a=>(!status||(status==='EXCEPTIONS'?['CANCELLED','NO_SHOW'].includes(a.status):a.status===status))&&(!dentist||a.dentist_id===dentist)&&(!q||[a.patient_name,a.appointment_code,a.treatment_name].some(v=>String(v||'').toLocaleLowerCase().includes(q)))).sort((a,b)=>String(a.scheduled_start_at).localeCompare(String(b.scheduled_start_at))||String(a.id).localeCompare(String(b.id)));
}
export function billSummary(invoices) {
  const live=invoices.filter(i=>i.status!=='VOID');
  return {issued:live.reduce((s,i)=>s+Number(i.total_fen),0),balance:live.reduce((s,i)=>s+Number(i.balance_fen),0),net:invoices.reduce((s,i)=>s+Number(i.paid_fen)-Number(i.refunded_fen),0),outstanding:live.filter(i=>Number(i.balance_fen)>0).length};
}
export function filterBills(invoices,{status='ALL',search=''}={}) {
  const q=search.trim().toLocaleLowerCase();
  return invoices.filter(i=>(status==='ALL'||(status==='OUTSTANDING'?i.status!=='VOID'&&Number(i.balance_fen)>0:i.status===status))&&(!q||[i.patient_name,i.invoice_code,i.visit_code].some(v=>String(v||'').toLocaleLowerCase().includes(q))));
}
export const careTopics=[['safety','风险核实','Safety'],['exam','检查记录','Examination'],['plan','方案与同意','Plan & consent'],['actual','实施项目','Actual treatment'],['notes','病历与签署','Notes & signatures']];
export function initialCareTopic(d) {
  if(d.visit.status==='COMPLETED')return 'notes';
  if(d.blockers.some(b=>/风险|病史|过敏/.test(b)))return 'safety';
  if(!d.observations.length)return 'exam';
  if(!d.requested.length||d.blockers.some(b=>/同意|关联|方案/.test(b)))return 'plan';
  if(!d.actual.some(a=>a.status==='RECORDED'))return 'actual';
  return 'notes';
}
export function renderCareWorkspace(d,{esc,T,badge,button,link,table,money,date,selectedTooth='',selectedTab='',writable=false}) {
  const v=d.visit,active=!['COMPLETED','CANCELLED'].includes(v.status),edit=writable&&active;
  const tab=careTopics.some(t=>t[0]===selectedTab)?selectedTab:initialCareTopic(d);
  const frame=(name,body,action='')=>`<section class="care-card"><header><h2>${name}</h2>${action}</header>${body}</section>`;
  const add=(label,action,id=v.id,style='')=>button(label,action,id,style);
  const teeth=[18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
  const alert=d.allergies.length?`<div class="care-medical-alert"><strong>${T('已登记过敏','Recorded allergies')}</strong><span>${d.allergies.map(a=>esc(a.substance_zh||a.substance_en)).join('、')}</span><small>${T('请查看本次复核，不以提示代替询问','Review current safety checks; alerts do not replace an assessment')}</small></div>`:`<div class="care-medical-neutral">${T('未登记活动过敏；接诊时仍需询问并核实。','No active allergies recorded. Ask and verify at the visit.')}</div>`;
  const safety=frame(T('本次风险与病史核实','Current safety review'),`<div class="care-pad"><dl class="care-key-values"><div><dt>${T('本次主诉 / 到诊声明','Chief complaint / arrival declaration')}</dt><dd>${esc(v.chief_complaint_zh||'—')}</dd></div><div><dt>${T('风险复核状态','Safety status')}</dt><dd>${badge(v.safety_gate_status)}</dd></div></dl>${d.allergies.map(a=>`<div class="risk-entry"><strong>${esc(a.substance_zh||a.substance_en)}</strong>${badge(a.severity)}<p>${esc(a.reaction_zh||a.reaction_en||'—')}</p></div>`).join('')}${d.acknowledgements.map(a=>`<div class="risk-review-entry"><span>${date(a.acknowledged_at)}</span><p>${esc(a.precaution_zh)}</p></div>`).join('')||`<p class="subline">${T('暂无逐项复核记录。','No item-level review recorded.')}</p>`}<p class="care-note">${T('病史更新、新增过敏或风险变化后，需要重新核实并按服务端要求重新签署。','Updated history or risk information requires a renewed review and, where required, a new signature.')}</p></div>`,edit?add(T('核实病史与风险','Review safety'),'clinical-safety',v.id,'primary'):'');
  const exam=frame(T('FDI 恒牙牙位与检查所见','FDI permanent dentition and findings'),`<div class="care-pad"><div class="odontogram"><div class="tooth-label">${T('上颌 · FDI 恒牙编码','Upper arch · FDI')}</div>${teeth.map((tooth,i)=>`${i===16?`<div class="tooth-label">${T('下颌 · FDI 恒牙编码','Lower arch · FDI')}</div>`:''}<button type="button" class="tooth ${d.observations.some(o=>String(o.tooth_code)===String(tooth))?'marked':''} ${String(selectedTooth)===String(tooth)?'selected':''}" data-act="tooth-select" data-id="${tooth}" aria-label="${T('牙位','Tooth')} ${tooth}"><svg viewBox="0 0 30 36" aria-hidden="true"><path d="M7 2C2 2 1 6 3 12l4 19c1 5 4 4 4 0l2-11c.3-2 3-2 3 0l2 11c1 4 3 5 4 0l5-19c2-6 0-10-5-10-3 0-5 2-7 2S10 2 7 2Z"/></svg><span>${tooth}</span></button>`).join('')}</div><p class="care-note">${T('点选牙位后记录检查所见。颜色仅表示已有记录，不代表诊断或严重程度。','Select a tooth to record a finding. Colour indicates a record, not a diagnosis or severity.')}</p></div>${table([T('牙位','Tooth'),T('观察类型','Type'),T('检查所见','Finding'),T('记录时间','Recorded')],d.observations.map(o=>[esc(o.tooth_code),esc(o.observation_type),esc(o.finding_zh),date(o.observed_at)]))}`,edit?add(T('记录检查所见','Add finding'),'clinical-observation',v.id,'primary'):'');
  const plan=frame(T('治疗方案与患者决定','Treatment proposals and patient decisions'),`<div class="care-pad"><p class="care-note">${T('方案不直接计费。只有实际实施项目进入后续结算；同意依据须对应具体方案项目。','Proposals are not billed. Only recorded actual treatment proceeds to billing; consent evidence relates to the specific proposal.')}</p>${d.requested.map(r=>{const cons=d.consents.filter(c=>c.requested_treatment_item_id===r.id),performed=d.actual.filter(a=>a.requested_treatment_item_id===r.id&&a.status==='RECORDED').reduce((n,a)=>n+Number(a.units),0);return `<article class="care-plan-row"><div><strong>${esc(r.treatment_name)}</strong>${badge(r.status)}<p>${r.tooth_code?'FDI '+esc(r.tooth_code)+' · ':''}${esc(r.units)} ${T('单位','units')} · ${esc(r.rationale_zh||'—')}</p>${cons.map(c=>`<div class="consent-evidence">${badge(c.decision)}<span>${esc(c.evidence)}</span></div>`).join('')||`<small>${T('尚未记录项目决定与依据','No item decision/evidence recorded')}</small>`}</div><div class="care-inline-actions">${edit&&!cons.length?add(T('记录患者决定','Record decision'),'clinical-consent',r.id):''}${edit&&v.status==='IN_PROGRESS'&&cons.some(c=>c.decision==='ACCEPTED')&&performed<Number(r.units)?add(T('登记本次实施','Record treatment'),'clinical-actual',r.id):''}${performed?'<small>'+T('已登记实施','Recorded actual')+' '+performed+' / '+esc(r.units)+'</small>':''}</div></article>`;}).join('')||`<div class="care-empty">${T('本次尚无治疗方案项目。','No proposed treatment for this visit.')}</div>`}</div>`,edit?add(T('新增方案项目','Add proposal'),'clinical-plan',v.id,'primary'):'');
  const actual=frame(T('本次实际实施项目','Actual treatment at this visit'),`${table([T('项目','Treatment'),T('牙位','Tooth'),T('数量','Units'),T('单价快照','Price snapshot'),T('行金额','Amount'),T('实施时间','Performed')],d.actual.map(a=>[esc(a.treatment_name),esc(a.tooth_code||'—'),esc(a.units),money(a.effective_unit_price_fen),money(a.line_amount_fen),date(a.performed_at)]))}<div class="care-pad care-note">${T('与方案的关联、数量、同意及医师资格在完成时重新核验；价格保留实施时快照。','Completion rechecks proposal linkage, quantities, consent and clinician qualifications. Prices retain the treatment-time snapshot.')}</div>`,edit&&v.status==='IN_PROGRESS'?add(T('追加实施项目','Add actual treatment'),'clinical-actual','','primary'):'');
  const noteRow=n=>`<article class="clinical-note-entry"><div class="row between"><strong>${T('病历版本','Version')} ${esc(n.version_number)}</strong>${n.signed_at?badge('SIGNED'):badge(n.status==='SIGNED'?'LEGACY_UNVERIFIED':'DRAFT')}</div><p class="second">${date(n.created_at)}${n.signed_at?' · '+T('签署','Signed')+' '+esc(n.signer_dentist||'')+' '+date(n.signed_at):' · '+T('无本版本签署证据','No signature evidence for this version')}</p><div class="clinical-note-text">${esc(n.content_zh)}</div>${n.amendment_reason?`<p class="amendment-reason">${T('补记原因','Amendment reason')}: ${esc(n.amendment_reason)}</p>`:''}</article>`;
  const current=d.notes.filter(n=>Number(n.version_number)===Number(n.current_version)),history=d.notes.filter(n=>Number(n.version_number)!==Number(n.current_version));
  const notes=frame(T('病历记录与签署','Clinical notes and signatures'),`<div class="care-pad">${current.map(noteRow).join('')||`<div class="care-empty">${T('尚无病历记录。','No clinical notes recorded.')}</div>`}${history.length?`<details class="note-history"><summary>${T('历史版本','Historical versions')} (${history.length})</summary>${history.map(noteRow).join('')}</details>`:''}<p class="care-note">${T('已签署版本保留。完成后只能附理由补记，不覆盖原文；系统账号签署不等同第三方法律电子签章。','Signed versions are retained. Post-completion amendments require a reason and do not overwrite the original. Account signatures are not third-party certified legal e-signatures.')}</p></div>`,writable?add(T(v.status==='COMPLETED'?'附理由补记':'记录 / 签署',v.status==='COMPLETED'?'Amend with reason':'Write / sign'),'clinical-note',v.id,'primary'):'');
  const panels={safety,exam,plan,actual,notes};
  const start=edit&&v.status==='WAITING'?add(T('开始诊疗','Start care'),'clinical-start',v.id,'primary'):'';
  let finish=edit&&v.status==='IN_PROGRESS'?add(T('完成就诊','Complete visit'),'clinical-complete',v.id,'primary'):'';
  if(finish&&d.blockers.length)finish=finish.replace('<button','<button disabled aria-describedby="care-blockers"');
  const readyCopy = v.status==='COMPLETED'
    ? T('本次就诊已完成。病历与实施项目按历史版本保留；需要更正时请附理由补记。','This visit is complete. Notes and actual treatment retain their historical versions; corrections require a reasoned amendment.')
    : v.status==='CANCELLED'
      ? T('本次就诊已取消，原有记录保留。','This visit is cancelled; existing records are retained.')
      : T('当前完成条件已满足。提交时仍会重新核验。','Current completion checks are satisfied; submission revalidates them.');
  return `<div class="care-patient-header"><div class="care-patient-monogram">${esc(v.patient_name.slice(0,1))}</div><div><div class="row wrap"><h1>${esc(v.patient_name)}</h1>${badge(v.status)}</div><p>${esc(v.patient_code)} <span>·</span> ${esc(v.visit_code)}</p></div><div class="care-patient-meta"><strong>${esc(v.dentist_name)} · ${esc(v.clinic_name)}</strong><span>${date(v.scheduled_start_at)} · ${T('诊所本地时间','Clinic local time')}</span></div>${link(T('患者档案','Patient record'),'patients/'+v.patient_id)}</div>${alert}<div class="care-work-layout"><section class="care-work-main"><div class="care-tabs" role="tablist" aria-label="${T('本次就诊分区','Visit sections')}">${careTopics.map(([id,zh,en],i)=>`<button type="button" role="tab" id="care-tab-${id}" data-care-tab="${id}" aria-controls="care-panel-${id}" aria-selected="${tab===id}" tabindex="${tab===id?0:-1}"><span>${i+1}</span>${T(zh,en)}</button>`).join('')}</div>${careTopics.map(([id])=>`<div id="care-panel-${id}" role="tabpanel" aria-labelledby="care-tab-${id}" ${tab===id?'':'hidden'}>${panels[id]}</div>`).join('')}</section><aside class="care-completion"><header><h2>${T('本次完成核查','Completion review')}</h2><span>${T('服务端核验结果','Server-validated')}</span></header><div id="care-blockers">${d.blockers.length?`<p>${T(v.status==='COMPLETED'?'历史记录按当前规则仍有待核对项；不自动回写原事实。':'完成前仍需处理以下项目：',v.status==='COMPLETED'?'Historical record needs review under current rules; original facts are retained.':'Resolve these items before completion:')}</p><ul>${d.blockers.map(b=>`<li>${esc(b)}</li>`).join('')}</ul>`:`<p class="care-ready">${readyCopy}</p>`}</div><div class="care-completion-actions">${start}${finish}${edit&&v.status==='IN_PROGRESS'?add(T('补全项目关联','Reconcile linkage'),'clinical-reconcile',v.id):''}</div><dl><div><dt>${T('记录版本','Record version')}</dt><dd>${esc(v.visit_version)}</dd></div><div><dt>${T('已登记观察','Findings')}</dt><dd>${d.observations.length}</dd></div><div><dt>${T('实际项目','Actual items')}</dt><dd>${d.actual.length}</dd></div></dl></aside></div>`;
}
export function bindCareTabs(root,onChange=()=>{}) {
  const tabs=[...root.querySelectorAll('[data-care-tab]')];
  const select=(n,focus=false)=>{tabs.forEach((t,i)=>{t.setAttribute('aria-selected',String(i===n));t.tabIndex=i===n?0:-1;root.querySelector('#'+t.getAttribute('aria-controls')).hidden=i!==n;});onChange(tabs[n].dataset.careTab);if(focus)tabs[n].focus();};
  tabs.forEach((t,i)=>{t.onclick=()=>select(i);t.onkeydown=e=>{let n=i;if(e.key==='ArrowRight')n=(i+1)%tabs.length;else if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=tabs.length-1;else return;e.preventDefault();select(n,true);};});
}
