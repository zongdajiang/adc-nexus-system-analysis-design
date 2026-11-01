const labels={PENDING:['待安排','Pending'],SCHEDULED:['已约复诊','Scheduled'],COMPLETED:['已完成','Completed'],DECLINED:['患者婉拒','Declined'],CANCELLED:['已终止','Cancelled'],NO_ANSWER:['未接通','No answer'],REQUESTED_CALLBACK:['另约联系','Call back'],AGREED:['同意安排','Agreed'],RECOMMEND:['提出建议','Recommendation'],CONTACT:['联系登记','Contact'],LINK:['关联预约','Linked appointment'],COMPLETE:['核实完成','Completed'],REOPEN:['重新安排','Reopened'],CANCEL:['终止跟进','Cancelled'],RECORDED:['已登记','Recorded'],PHONE:['电话','Phone'],EMAIL:['邮箱','Email'],SMS:['短信','SMS'],IN_PERSON:['当面','In person'],INTERNAL:['内部核对','Internal review']};
export const followupLabel=(v,T)=>labels[v]?T(...labels[v]):v;
export function followupTabs(active,h){return `<div class="tabline">${h.button(h.T('空档候补','Waitlist'),'followup-tab','waitlist','small '+(active==='waitlist'?'on':''))}${h.can('followup.read')?h.button(h.T('复诊跟进','Recall follow-up'),'followup-tab','followups','small '+(active==='followups'?'on':'')):''}</div>`;}
export function filterFollowups(items,{status='OPEN',search='',due='ALL',today}={}){
  const q=search.trim().toLocaleLowerCase();
  return items.filter(f=>(status==='ALL'||(status==='OPEN'?['PENDING','SCHEDULED'].includes(f.status):f.status===status))&&(!q||[f.patient_name,f.patient_code,f.dentist_name,f.reason].some(v=>String(v||'').toLocaleLowerCase().includes(q)))&&
    (due==='ALL'||(due==='OVERDUE'?f.due_on<today:f.next_contact_on&&f.next_contact_on<=today)))
    .sort((a,b)=>a.due_on.localeCompare(b.due_on)||a.created_at.localeCompare(b.created_at));
}
export function renderFollowups(data,state,h){
  const {T,esc,table,button}=h,items=filterFollowups(data.items,{status:state.followupStatus||'OPEN',search:state.followupSearch||'',due:state.followupDue||'ALL',today:data.today});
  const options=[['OPEN',T('待跟进','Open follow-ups')],['PENDING',T('待安排','Pending')],['SCHEDULED',T('已约复诊','Scheduled')],['COMPLETED',T('已完成','Completed')],['DECLINED',T('患者婉拒','Declined')],['CANCELLED',T('已终止','Cancelled')],['ALL',T('全部','All')]];
  return `<section class="desk-register"><form id="followup-filter" class="setup-toolbar"><label>${T('检索患者或建议','Search patients or advice')}<input class="field-input" name="search" value="${esc(state.followupSearch||'')}" placeholder="${T('患者姓名、编号或医师','Patient name, code or clinician')}"></label><label>${T('跟进状态','Status')}<select class="field-input" name="status">${options.map(([v,l])=>`<option value="${v}" ${v===(state.followupStatus||'OPEN')?'selected':''}>${esc(l)}</option>`).join('')}</select></label><label>${T('联系安排','Contact schedule')}<select class="field-input" name="due">${[['ALL',T('全部日期','All dates')],['TODAY',T('今日应联系','Contact due')],['OVERDUE',T('复诊日期已过','Recall overdue')]].map(([v,l])=>`<option value="${v}" ${v===(state.followupDue||'ALL')?'selected':''}>${esc(l)}</option>`).join('')}</select></label><button class="btn" type="submit">${T('筛选','Filter')}</button></form>`+
    table([T('复诊日期 / 优先级','Due / priority'),T('患者','Patient'),T('建议与负责医师','Advice / clinician'),T('下次联系','Next contact'),T('状态 / 预约','Status / appointment'),T('操作','Actions')],items.map(f=>[
      `<strong>${esc(f.due_on)}</strong><div class="second">${f.priority==='PRIORITY'?T('优先联系','Priority contact'):T('常规','Routine')}${f.due_on<data.today&&['PENDING','SCHEDULED'].includes(f.status)?' · '+T('日期已过','Overdue'):''}</div>`,
      `<strong>${esc(f.patient_name)}</strong><div class="second">${esc(f.patient_code)} · ${esc(f.clinic_name)}</div>`,
      `<span class="setup-wrap">${esc(f.reason)}</span><div class="second">${esc(f.dentist_name)}</div>`,esc(f.next_contact_on||'—'),
      `${esc(followupLabel(f.status,T))}${f.appointment_code?`<div class="second">${esc(f.appointment_code)}${['CANCELLED','NO_SHOW'].includes(f.appointment_status)?' · '+T('预约已失效，需重新安排','Booking no longer active'):''}</div>`:''}`,
      button(T('查看与跟进','Review follow-up'),'followup-detail',f.id,'small')
    ]))+`<div class="worklist-footer">${items.length} ${T('条建议。医师根据本次就诊提出复诊日期，系统不自动推算医学间隔；联系登记不会发送短信或邮件。','recommendations. Recall dates come from the clinician; contact entries do not send messages.')}${data.items.length===600?' '+T('已达查询上限，请联系管理员分段核查。','Result limit reached; ask an administrator to review in batches.'):''}</div></section>`;
}
export function installFollowupHandlers(h){
  const {handlers,state,T,esc,api,modal,button,table,date,can}=h;
  const note={name:'note',label:T('联系结果或核对依据','Outcome or verification evidence'),type:'textarea'};
  handlers['followup-tab']=v=>{state.waitlistTab=v;h.refresh();};
  handlers['followup-recommend']=()=>{
    const v=state.visitDetail.visit;
    modal({name:T('提出复诊建议','Recommend recall'),description:T('仅记录负责医师基于本次就诊提出的建议；不会自动生成预约或触达患者。','Record advice from the responsible clinician. This does not create a booking or contact the patient.'),fields:[
      {name:'due_on',label:T('建议复诊日期','Recommended recall date'),type:'date',value:state.boot.today},
      {name:'priority',label:T('联系优先级','Contact priority'),type:'select',value:'ROUTINE',options:[{value:'ROUTINE',label:T('常规','Routine')},{value:'PRIORITY',label:T('优先','Priority')}]},
      {name:'reason',label:T('复诊目的与已交代事项','Recall purpose and agreed advice'),type:'textarea'},
      {name:'contact_allowed',label:T('患者已同意诊所为此项复诊进行联系','Patient agreed to clinic contact for this recall'),type:'checkbox',required:false}
    ],onSubmit:b=>api('/followups',{...b,action:'recommend',visit_id:v.id})});
  };
  handlers['followup-detail']=async id=>{
    const d=await api('/followups/'+encodeURIComponent(id)),f=d.followup;state.followupDetail=d;
    const open=['PENDING','SCHEDULED'].includes(f.status),manage=can('followup.manage');
    const actions=(manage&&open?button(T('登记联系','Record contact'),'followup-contact',id,'small primary'):'')+
      (manage&&f.status==='PENDING'?button(T('关联已有预约','Link appointment'),'followup-link',id,'small'):'')+
      (manage&&f.status==='SCHEDULED'?(f.appointment_status==='COMPLETED'?button(T('核实复诊完成','Confirm completed recall'),'followup-complete',id,'small'):['CANCELLED','NO_SHOW'].includes(f.appointment_status)?button(T('重新安排','Reopen follow-up'),'followup-reopen',id,'small'):''):'')+
      (manage&&open?button(T('终止跟进','End follow-up'),'followup-cancel',id,'small danger'):'');
    modal({name:f.patient_name+' · '+T('复诊跟进','Recall follow-up'),informational:true,wide:true,submit:T('关闭','Close'),description:`${f.patient_code} · ${f.dentist_name} · ${f.due_on}`,body:
      `<dl class="setup-facts"><div><dt>${T('建议目的','Purpose')}</dt><dd>${esc(f.reason)}</dd></div><div><dt>${T('来源就诊','Source visit')}</dt><dd>${esc(f.visit_code)}</dd></div><div><dt>${T('联系许可','Contact permission')}</dt><dd>${f.contact_allowed?T('已同意联系','Contact agreed'):T('未取得联系许可','Not recorded')}</dd></div>${d.phone?`<div><dt>${T('联系电话','Phone')}</dt><dd>${esc(d.phone)}</dd></div>`:''}<div><dt>${T('跟进状态','Status')}</dt><dd>${esc(followupLabel(f.status,T))}</dd></div></dl>`+
      `<div class="row wrap gap">${actions}</div><h3>${T('建议与联系记录','Advice and contact history')}</h3>`+
      table([T('时间 / 人员','Time / actor'),T('操作 / 方式','Action / channel'),T('结果与依据','Outcome / evidence')],d.events.map(e=>[`${date(e.occurred_at)}<div class="second">${esc(e.actor_name)}</div>`,`${esc(followupLabel(e.event_type,T))}<div class="second">${esc(followupLabel(e.channel,T))}</div>`,`${esc(followupLabel(e.outcome,T))}<p class="setup-wrap">${esc(e.note)}</p>${e.next_contact_on?`<div class="second">${T('下次联系','Next contact')}: ${esc(e.next_contact_on)}</div>`:''}`])),onSubmit:async()=>{}});
  };
  handlers['followup-contact']=()=>{
    const f=state.followupDetail.followup;
    modal({name:T('登记已发生的联系','Record completed contact'),description:T('请先完成实际联系，再记录方式、结果及下次时间。未获同意时仅允许登记当面沟通。','Record an actual contact, its result and next date. Without permission only in-person communication is allowed.'),fields:[
      {name:'channel',label:T('联系途径','Channel'),type:'select',options:(f.contact_allowed?['PHONE','EMAIL','SMS','IN_PERSON']:['IN_PERSON']).map(value=>({value,label:followupLabel(value,T)}))},
      {name:'outcome',label:T('联系结果','Outcome'),type:'select',options:['NO_ANSWER','REQUESTED_CALLBACK','AGREED','DECLINED'].map(value=>({value,label:followupLabel(value,T)}))},
      {name:'next_contact_on',label:T('下次联系日期（未接通/另约联系必填）','Next contact (required for unanswered/callback)'),type:'date',required:false},note
    ],onSubmit:b=>api('/followups',{...b,id:f.id,version:f.revision,action:'contact'})});
  };
  handlers['followup-link']=async()=>{
    const f=state.followupDetail.followup;
    const all=await api('/appointments?'+new URLSearchParams({patient_id:f.patient_id,clinic_id:f.clinic_id,from:f.created_at.slice(0,10)}));
    modal({name:T('关联正式预约','Link a booked appointment'),description:T('先在预约与到诊中安排该患者的服务，再在此关联。此操作不创建或修改预约。','Book the patient in Scheduling first. Linking does not create or change an appointment.'),fields:[
      {name:'appointment_id',label:T('本人同店有效预约','Patient booking in the same clinic'),type:'select',options:all.filter(a=>['CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED'].includes(a.status)).map(a=>({value:a.id,label:`${a.scheduled_start_at} · ${a.treatment_name} · ${a.appointment_code}`}))},note
    ],onSubmit:b=>api('/followups',{...b,id:f.id,version:f.revision,action:'link'})});
  };
  for(const action of ['complete','reopen','cancel'])handlers['followup-'+action]=()=>{
    const f=state.followupDetail.followup;
    modal({name:T(...({complete:['核实复诊已完成','Confirm completed recall'],reopen:['重新安排复诊','Reopen recall'],cancel:['终止本项跟进','End this follow-up']}[action])),description:action==='cancel'?T('终止建议跟进不会取消已关联预约。预约如需变更，请在预约详情另行处理并保留原因。','Ending follow-up does not cancel a booking. Manage that separately in Scheduling.'):T('提交时再次核对正式预约与就诊状态。','The booking and clinical state are checked again on submission.'),fields:[note],onSubmit:b=>api('/followups',{...b,id:f.id,version:f.revision,action})});
  };
}
