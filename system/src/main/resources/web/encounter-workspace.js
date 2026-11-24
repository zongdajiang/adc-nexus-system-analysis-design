// A clinician records the current encounter in place. Clinical facts and signatures
// remain separate persisted objects; the server commits combined actions atomically.
const drafts = new Map();
export const clearEncounterDrafts = () => drafts.clear();
export const hasEncounterDrafts = () => [...drafts.values()].some(d => d.dirty);

export function renderEncounter(d, {esc,T,badge,money,date,table,selectedTooth=''}) {
  const v=d.visit, draft=drafts.get(v.id)||{}, current=d.notes.find(n=>Number(n.version_number)===Number(n.current_version));
  const content=draft.content ?? current?.content_zh ?? '';
  const field=(name,label,control,full=false)=>`<label class="encounter-field ${full?'full':''}"><span>${label}</span>${control}</label>`;
  const area=(name,value='',rows=3,required=false)=>`<textarea class="field-input" name="${name}" rows="${rows}" ${required?'required':''}>${esc(value)}</textarea>`;
  const submit=(label)=>`<button class="btn primary" type="submit">${label}</button>`;
  const errors='<div class="encounter-error full" role="alert"></div>';
  const history=d.history?.[0];
  const currentFacts=`<details class="encounter-history"><summary>${T('本次病史与过敏核对','History and allergies for this visit')} ${badge(v.safety_gate_status)}</summary><p>${esc(history?.history_text||T('尚未登记病史，请当面询问患者。','No history recorded. Ask the patient.'))}</p><p>${esc(v.chief_complaint_zh||'')}</p>${d.acknowledgements.map(a=>`<p>${date(a.acknowledged_at)} · ${esc(a.precaution_zh)}</p>`).join('')}</details>`;
  if(['SAFETY_REVIEW','WAITING'].includes(v.status))return `<section class="encounter-sheet"><header><h2>${T('核对后开始接诊','Review and start care')}</h2><p>${T('核对本次病史与过敏，确认后直接进入治疗记录。','Review current history and allergies, then continue to treatment recording.')}</p></header>
    <div class="encounter-pad">${history?`<div class="encounter-history-text"><strong>${T('最近一次病史声明','Latest history declaration')}</strong><p>${esc(history.history_text||T('患者未补充说明','No additional statement'))}</p><small>${date(history.created_at)}</small></div>`:''}
    <form id="encounter-start" class="encounter-form">
      ${field('chief_complaint',T('本次主诉','Chief complaint'),area('chief_complaint',v.chief_complaint_zh||'',2,true),true)}
      ${field('evidence',T('病史核对与注意事项','Review findings and precautions'),area('evidence','',3,true),true)}
      <label class="check-label full"><input name="history_confirmed" type="checkbox" required><span>${T('已向患者核实病史变化、过敏及相关注意事项','I reviewed history changes, allergies and relevant precautions with this patient')}</span></label>
      <label class="check-label full"><input name="confirm" type="checkbox" required><span>${T('已核对患者身份，本人负责本次接诊','I verified this patient and am responsible for this encounter')}</span></label>${errors}
      <div class="encounter-form-footer full">${submit(T('确认并开始接诊','Confirm and start care'))}</div>
    </form></div></section>`;
  if(v.status!=='IN_PROGRESS')return `<section class="encounter-sheet"><header><h2>${T(v.status==='COMPLETED'?'本次接诊已完成':'本次接诊已撤销',v.status==='COMPLETED'?'Encounter complete':'Encounter cancelled')}</h2></header><div class="encounter-pad"><p>${v.status==='COMPLETED'?T('治疗记录已交收费岗位。病历如需补充，请在下方填写补记并说明原因。','The treatment record is ready for billing. Use a reasoned amendment below for further notes.'):T('原始记录已保留。','Original records are retained.')}</p>${current?`<div class="clinical-note-text">${esc(current.content_zh)}</div>`:''}</div></section>`;
  const accepted=d.requested.filter(r=>d.consents.some(c=>c.requested_treatment_item_id===r.id&&c.decision==='ACCEPTED')).map(r=>({...r,remaining:Number(r.units)-d.actual.filter(a=>a.status==='RECORDED'&&a.requested_treatment_item_id===r.id).reduce((sum,a)=>sum+Number(a.units),0)})).filter(r=>r.remaining>0);
  const treatmentOptions=(d.eligible_treatments||[]).map(t=>`<option value="${esc(t.id)}">${esc(t.name_zh)} · ${money(t.standard_price_fen)}</option>`).join('');
  const actual=d.actual.filter(a=>a.status==='RECORDED');
  const actualList=actual.length?table([T('已做项目','Recorded treatment'),T('牙位','Tooth'),T('数量','Units'),T('金额','Amount'),T('操作','Actions')],actual.map(a=>[esc(a.treatment_name),esc(a.tooth_code||T('全口 / 不分牙位','General')),esc(a.units),money(a.line_amount_fen),`<button type="button" class="btn small" data-void-actual="${esc(a.id)}">${T('撤销误录','Void mistaken entry')}</button>`])):`<p class="encounter-pad muted">${T('本次尚未登记治疗。请按实际完成内容填写。','No treatment recorded yet. Record only work actually performed.')}</p>`;
  const voided=d.actual.filter(a=>a.status==='VOIDED');
  const voidHistory=voided.length?`<details class="encounter-void-history"><summary>${T('已撤销的治疗记录','Voided treatment entries')} (${voided.length})</summary>${table([T('原项目','Original item'),T('牙位','Tooth'),T('原数量','Original units'),T('原金额（不计费）','Original amount (excluded)'),T('撤销依据','Correction')],voided.map(a=>{const correction=d.corrections?.find(c=>c.actual_id===a.id);return [esc(a.treatment_name),esc(a.tooth_code||'—'),esc(a.units),money(a.line_amount_fen),correction?esc(correction.reason)+`<div class="second">${esc(correction.actor_name)} · ${date(correction.occurred_at)}</div>`:'—'];}))}</details>`:'';
  const hasSignature=d.notes.some(n=>n.signed_at);
  const steps=`<ol class="encounter-progress" aria-label="${T('接诊进度','Encounter progress')}"><li class="done"><strong>${T('病史核对','History reviewed')}</strong>${T('已开始接诊','Care started')}</li><li class="${actual.length?'done':'current'}"><strong>${T('检查与治疗','Examination & treatment')}</strong>${actual.length?actual.length+T('项治疗已保存',' treatments saved'):T('填写检查与已做项目','Record findings and treatment')}</li><li class="${current?'done':actual.length?'current':''}"><strong>${T('病历','Clinical note')}</strong>${current?T('已保存，可继续核对','Saved for review'):T('填写主诉、检查及处置','Document the encounter')}</li><li><strong>${T('签署完成','Sign & complete')}</strong>${T('核对后结束本次接诊','Review and finish care')}</li></ol>`;
  return `${steps}${currentFacts}<section class="encounter-sheet" id="encounter-treatment-section"><header><h2>${T('检查与本次治疗','Examination and treatment')}</h2><span>${actual.length} ${T('项已登记','items recorded')}</span></header>${actualList}${voidHistory}
    <details class="encounter-add-treatment" ${actual.length?'':'open'}><summary>${T(actual.length?'追加治疗项目':'填写本次检查与治疗',actual.length?'Add another treatment':'Record examination and treatment')}</summary><div class="encounter-pad"><form id="encounter-treatment" class="encounter-form">
    ${field('item_id',T('治疗来源','Treatment source'),`<select class="field-input" name="item_id"><option value="">${T('新增本次治疗项目','Add a treatment for this encounter')}</option>${accepted.map(r=>`<option value="${esc(r.id)}">${esc(r.treatment_name)} · ${esc(r.tooth_code||T('不分牙位','General'))} · ${T('剩余','Remaining')} ${r.remaining}</option>`).join('')}</select>`,true)}
    ${field('treatment_id',T('治疗项目','Treatment'),`<select class="field-input" name="treatment_id" required><option value="">${T('选择项目','Select treatment')}</option>${treatmentOptions}</select>`)}
    ${field('tooth_code',T('牙位（不分牙位可留空）','Tooth (blank for general care)'),`<input class="field-input" name="tooth_code" value="${esc(selectedTooth)}" placeholder="${T('例如 16、36','e.g. 16, 36')}" pattern="[1-4][1-8]|[5-8][1-5]" maxlength="2">`)}
    ${field('units',T('本次完成数量','Units performed'),'<input class="field-input" name="units" type="number" min="1" max="32" step="1" value="1" required>')}
    ${field('finding',T('检查所见（可同时记录）','Examination finding (optional)'),area('finding','',2),true)}
    ${field('finding_severity',T('检查记录程度（填写所见时必选）','Finding severity (required with a finding)'),`<select class="field-input" name="finding_severity"><option value="">${T('请选择','Select')}</option><option value="NORMAL">${T('未见异常','No abnormality')}</option><option value="LOW">${T('轻','Mild')}</option><option value="MODERATE">${T('中','Moderate')}</option><option value="HIGH">${T('重','Severe')}</option></select>`)}
    <div class="encounter-new-plan full">
      ${field('rationale',T('治疗方案与说明','Treatment rationale and explanation'),area('rationale','',2,true),true)}
      ${field('consent_evidence',T('患者同意依据','Patient consent evidence'),area('consent_evidence','',2,true),true)}
      <label class="check-label"><input type="checkbox" name="patient_consented" required><span>${T('已说明本项治疗及费用，患者已同意；本次治疗已实际完成','The patient agreed after explanation of this treatment and fee; this treatment was actually performed')}</span></label>
    </div>${errors}<div class="encounter-form-footer full"><small>${T('保存后会保留方案、同意依据和实际治疗三项记录。','Saves linked proposal, consent evidence and actual treatment records.')}</small>${submit(T('保存本次治疗','Save treatment'))}</div>
    </form></div></details></section>
    <section class="encounter-sheet" id="encounter-note-section"><header><h2>${T('病历与结束接诊','Clinical note and completion')}</h2><button class="btn small" type="button" data-act="encounter-outline">${T('插入病历提纲','Insert blank outline')}</button></header><div class="encounter-pad">
    <form id="encounter-note" class="encounter-form">
      ${field('content',T('本次病历','Clinical note'),area('content',content,10,true),true)}
      ${hasSignature?field('reason',T('签署后更正原因','Reason for changing a signed record'),area('reason',draft.reason||'',2),true):''}
      <p class="encounter-draft-status full" role="status">${draft.dirty?T('有未保存内容，请保存后离开。','Unsaved content. Save before leaving.'):current?T('已保存的病历可继续核对。','Review the saved clinical note.'):T('请如实填写；提纲不会代填检查结论。','Record actual findings. The outline does not fill in clinical conclusions.')}</p>
      ${errors}<div class="encounter-form-footer full"><button class="btn" type="submit">${T('保存病历草稿','Save note draft')}</button><button class="btn primary" type="button" data-act="encounter-finish">${T('签署并完成就诊','Sign and complete encounter')}</button></div>
    </form></div></section>`;
}

export function bindEncounter(root,d,{api,refresh,errorBox,T,toast,modal}) {
  if(!root.querySelector('.encounter-sheet'))return;
  const vid=d.visit.id;
  const note=root.querySelector('#encounter-note');
  const remember=()=>{if(note){drafts.set(vid,{content:note.elements.content.value,reason:note.elements.reason?.value||'',dirty:true});note.querySelector('.encounter-draft-status').textContent=T('有未保存内容，请保存后离开。','Unsaved content. Save before leaving.');}};
  note?.addEventListener('input',remember);
  const save=async(form,action,extra={})=>{
    if(!form.reportValidity())return;
    const controls=[...form.elements],buttons=controls.filter(n=>n.tagName==='BUTTON');
    const values=Object.fromEntries(new FormData(form));
    for(const c of controls)if(c.type==='checkbox')values[c.name]=c.checked;
    const error=form.querySelector('.encounter-error');error.replaceChildren();
    buttons.forEach(b=>b.disabled=true);form.setAttribute('aria-busy','true');
    try {await api('/visits/'+vid,{...values,...extra,action,version:d.visit.visit_version});if(action==='note')drafts.delete(vid);toast(T('已保存','Saved'));await refresh();}
    catch(e){error.innerHTML=errorBox(e);error.scrollIntoView({block:'nearest'});}
    finally{buttons.forEach(b=>b.disabled=false);form.removeAttribute('aria-busy');}
  };
  const start=root.querySelector('#encounter-start');if(start)start.onsubmit=e=>{e.preventDefault();save(start,'review_start');};
  root.querySelectorAll('[data-void-actual]').forEach(button=>button.onclick=()=>{
    const item=d.actual.find(a=>a.id===button.dataset.voidActual);
    modal({name:T('撤销误录的治疗项目','Void a mistaken treatment entry'),description:item.treatment_name+' · '+d.visit.patient_name,
      body:`<p>${T('仅撤销尚未完成就诊中的误录项目。原记录保留，不参与开单；已有病历需重新核对后签署。','Retains the original entry and excludes it from billing. Review and re-sign the note after this correction.')}</p>`,
      fields:[{name:'reason',label:T('撤销原因','Reason'),type:'textarea'}],submit:T('确认撤销误录','Confirm correction'),
      onSubmit:b=>api('/visits/'+vid,{...b,actual_id:item.id,action:'void_actual',version:d.visit.visit_version})});
  });
  const treatment=root.querySelector('#encounter-treatment');
  if(treatment){
    treatment.onsubmit=e=>{e.preventDefault();save(treatment,'record_treatment');};
    treatment.elements.finding.oninput=()=>{treatment.elements.finding_severity.required=!!treatment.elements.finding.value.trim();};
    treatment.elements.item_id.onchange=()=>{
      const item=d.requested.find(r=>r.id===treatment.elements.item_id.value),existing=!!item;
      for(const n of ['treatment_id','tooth_code']){treatment.elements[n].disabled=existing;if(item)treatment.elements[n].value=item[n]||'';}
      treatment.querySelector('.encounter-new-plan').hidden=existing;
      for(const n of ['rationale','consent_evidence','patient_consented'])treatment.elements[n].required=!existing;
      const done=d.actual.filter(a=>a.requested_treatment_item_id===item?.id&&a.status==='RECORDED').reduce((n,a)=>n+Number(a.units),0);
      treatment.elements.units.max=existing?Number(item.units)-done:32;treatment.elements.units.value='1';
    };
  }
  if(note)note.onsubmit=e=>{e.preventDefault();save(note,'note',{sign:false});};
  root.querySelector('[data-act="encounter-outline"]')?.addEventListener('click',()=>{
    const box=note.elements.content;
    if(box.value.trim()){box.focus();toast(T('已填写病历，未替换内容。可在原文继续补充。','Existing note retained. Continue editing it.'));return;}
    box.value='主诉：\n现病史：\n检查：\n诊断：\n处置：\n医嘱与复诊：';remember();box.focus();
  });
  root.querySelector('[data-act="encounter-finish"]')?.addEventListener('click',()=>{
    if(!note.reportValidity())return;
    const content=note.elements.content.value,reason=note.elements.reason?.value||'';
    const blockers=d.blockers.filter(b=>!/病历.*签署/.test(b));
    if(blockers.length){note.querySelector('.encounter-error').innerHTML=errorBox({message:T('请先补齐以下记录，再签署完成。','Complete these records before signing.'),details:blockers});return;}
    modal({name:T('签署并完成本次接诊','Sign and complete this encounter'),description:d.visit.patient_name+' · '+d.visit.visit_code,
      body:`<p>${T('将保存并签署当前病历，同时完成就诊并交收费岗位。提交时会重新检查病史、检查记录、治疗与同意依据。','Saves and signs the note, completes the encounter and releases it for billing. All prerequisites are rechecked.')}</p>`,
      fields:[{name:'signature_confirmed',label:T('本人已核对病历内容、实际治疗及患者同意依据，确认签署','I reviewed the note, actual treatment and patient consent, and confirm my signature'),type:'checkbox'}],
      submit:T('确认签署并完成','Confirm signature and completion'),
      onSubmit:b=>api('/visits/'+vid,{...b,content,reason,action:'sign_complete',version:d.visit.visit_version}),
      onSuccess:async()=>{drafts.delete(vid);toast(T('本次就诊已完成，已交收费岗位。','Encounter completed and ready for billing.'));await refresh();}
    });
  });
}
