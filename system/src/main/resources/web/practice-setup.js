/* Extensions of the existing resource workspace. Authorization remains server-side. */
export function renderSetupTab(data,tab,h){
  const {T,esc,badge,button,table,panel,money,can}=h;
  const named=(id,items)=>esc(items.find(x=>x.id===id)?.name_zh||id);
  const edit=(action,id,label=T('编辑资料','Edit details'))=>button(label,action,id,'small');
  const days=T(['周日','周一','周二','周三','周四','周五','周六'],['Sun','Mon','Tue','Wed','Thu','Fri','Sat']);
  if(tab==='clinics'){
    const list=table([T('诊所 / 代码','Clinic / code'),T('地址与联系','Address / contact'),T('牙椅配置','Chair capacity'),T('状态','Status'),T('操作','Actions')],data.clinics.map(c=>[
      `<strong>${esc(c.name_zh)}</strong><div class="second">${esc(c.name_en)} · ${esc(c.code)}</div>`,
      `${esc(c.city_zh)} · ${esc(c.address_zh)}<div class="second">${esc(c.phone||'—')} · ${esc(c.email||'—')}</div>`,
      `${data.chairs.filter(x=>x.clinic_id===c.id&&x.status!=='INACTIVE').length} / ${c.chair_capacity}`,
      badge(c.status),can('clinic.manage')?edit('setup-clinic',c.id):''
    ]));
    const hours=data.clinics.map(c=>`<details class="setup-hours"><summary>${esc(c.name_zh)} · ${T('营业时间','Opening hours')}</summary>${table([T('星期','Day'),T('营业时段','Hours'),T('预约粒度','Slot interval'),T('操作','Actions')],days.map((day,i)=>{
      const r=data.hours.find(r=>r.clinic_id===c.id&&Number(r.day_of_week)===i);
      return [day,r?(r.is_closed?T('休息','Closed'):`${esc(r.opens_at)} – ${esc(r.closes_at)}`):T('尚未设置','Not configured'),r?`${r.slot_minutes} min`:'—',can('resource.manage')?edit('setup-hours',`${c.id}|${i}`,T('设置时段','Set hours')):''];
    }))}</details>`).join('');
    return panel(T('诊所档案','Clinic directory'),list,can('clinic.manage')&&h.network?button(T('新增诊所','New clinic'),'setup-clinic','','primary','plus'):'')+hours;
  }
  if(tab==='workforce')return panel(T('医师档案','Clinician directory'),table([T('姓名 / 编号','Name / ID'),T('职称与联系','Title / contact'),T('任职诊所','Assignments'),T('状态','Status'),T('操作','Actions')],data.dentists.map(d=>[
    `<strong>${esc(d.name_zh)}</strong><div class="second">${esc(d.name_en)} · ${esc(d.employee_code)}</div>`,
    `${esc(d.title_zh)}<div class="second">${esc(d.email)}${d.phone?' · '+esc(d.phone):''}</div>`,
    data.assignments.filter(a=>a.dentist_id===d.id&&a.status==='ACTIVE').map(a=>named(a.clinic_id,data.clinics)).join('、')||T('待安排任职','No assignment'),
    badge(d.employment_status),can('workforce.manage')&&h.network?edit('setup-dentist',d.id):''
  ])),can('workforce.manage')&&h.network?button(T('新增医师档案','New clinician'),'setup-dentist','','primary','plus'):'',T('档案不授予登录权限。先登记任职与资质，再由管理员在内部员工名册中核验身份。','A clinician record does not grant access. Record assignments and credentials; an administrator separately verifies staff enrollment.'))+
  `<div class="gap">${panel(T('跨店任职记录','Clinic assignments'),table([T('医师','Clinician'),T('诊所','Clinic'),T('有效期','Effective dates'),T('周工时','Weekly hours'),T('状态','Status')],data.assignments.map(a=>[esc(a.dentist_name),esc(a.clinic_name),`${esc(a.effective_from)} – ${esc(a.effective_to||T('长期','Open-ended'))}`,a.weekly_hours,badge(a.status)])),can('workforce.manage')?button(T('追加任职','Add assignment'),'assignment-add','','small','plus'):'')}</div>`;
  if(tab==='chairs')return panel(T('牙椅与诊室','Chairs and operatories'),table([T('诊所 / 诊室','Clinic / room'),T('牙椅 / 代码','Chair / code'),T('设备与无障碍','Equipment / access'),T('状态','Status'),T('操作','Actions')],data.chairs.map(c=>[
    `${named(c.clinic_id,data.clinics)}<div class="second">${esc(c.room_name_zh)}</div>`,
    `<strong>${esc(c.name_zh)}</strong><div class="second">${esc(c.code)}</div>`,
    `${esc(readEquipment(c.equipment_json).join('、')||T('未登记设备','No equipment listed'))}${c.is_accessible?`<div class="second">${T('无障碍可达','Accessible')}</div>`:''}`,
    badge(c.status),can('resource.manage')?edit('setup-chair',c.id):''
  ])),can('resource.manage')?button(T('新增牙椅','New chair'),'setup-chair','','primary','plus'):'',T('牙椅数量受诊所容量约束；维护或停用前须协调有效预约。','Capacity limits apply. Coordinate active bookings before maintenance or deactivation.'));
  if(tab==='catalog')return panel(T('治疗项目与价格版本','Treatment catalog and fees'),table([T('项目 / 版本','Treatment / version'),T('类别 / 时长','Category / duration'),T('标准价格','Standard fee'),T('估算成本','Estimated cost'),T('有效期','Effective dates'),T('必需资质','Required qualifications'),T('状态 / 操作','Status / actions')],data.treatments.map(t=>[
    `<strong>${esc(t.name_zh)}</strong><div class="second">${esc(t.name_en)} · ${esc(t.code)} · v${t.version}</div>`,
    `${esc(t.category)}<div class="second">${t.duration_minutes} min</div>`,money(t.standard_price_fen),money(t.estimated_cost_fen),
    `${esc(t.effective_from)}<div class="second">${T('至','to')} ${esc(t.effective_to||T('长期','Open-ended'))}</div>`,
    data.requirements.filter(r=>r.treatment_id===t.id&&r.requirement_level==='REQUIRED').map(r=>named(r.qualification_type_id,h.qualifications)).join('、')||T('无额外专项要求','No additional specialty requirement'),
    badge(t.status)+(can('catalog.manage')&&h.network?`<div class="setup-row-actions">${Number(t.version)===Math.max(...data.treatments.filter(x=>x.code===t.code).map(x=>Number(x.version)))?edit('setup-catalog',t.id,T('追加版本','New version')):''}${t.status==='ACTIVE'?edit('setup-retire',t.id,T('停用','Retire')):''}</div>`:'')
  ])),can('catalog.manage')&&h.network?button(T('新增治疗项目','New treatment'),'setup-catalog','','primary','plus'):'',T('改价追加版本，不覆盖旧版。截止旧版前检查已约服务；实际治疗和已开单金额保持原快照。','Fees use new versions. Existing bookings are checked before retiring validity; performed and invoiced amounts retain their snapshots.'));
  return null;
}

export function readEquipment(value){try{const result=JSON.parse(value);return Array.isArray(result)?result.map(String):[];}catch{return [];}}

export function installSetupHandlers(h){
  const {handlers,state,T,api,modal,can}=h;
  const text=(name,label,value='',required=true)=>({name,label,value,required});
  const select=(name,label,values,value)=>({name,label,type:'select',options:values.map(([value,label])=>({value,label})),value});
  const reason={name:'reason',label:T('修改原因与核对依据','Reason and evidence'),type:'textarea'};
  const status=[['ACTIVE',T('有效','Active')],['INACTIVE',T('停用','Inactive')]];
  async function save(action,row,b){
    await api('/resources',{...b,action,id:row?.id||'',fingerprint:row?.fingerprint||''});
    state.boot=await api('/bootstrap');
  }
  handlers['setup-clinic']=id=>{
    if(!can('clinic.manage'))return;
    const c=state.resources.clinics.find(x=>x.id===id);
    modal({name:T(c?'编辑诊所档案':'新增诊所',c?'Edit clinic':'New clinic'),description:T('修改前核对容量和有效预约；新诊所需另行配置营业时间、牙椅及人员任职。','Check capacity and bookings. New clinics separately require hours, chairs and assignments.'),fields:[
      ...(!c?[text('code',T('诊所代码','Clinic code'))]:[]),text('name_zh',T('诊所名称','Clinic name'),c?.name_zh),text('name_en',T('英文名称','English name'),c?.name_en,false),
      text('city_zh',T('城市','City'),c?.city_zh),text('city_en',T('英文城市','City in English'),c?.city_en,false),
      text('address_zh',T('地址','Address'),c?.address_zh),text('phone',T('联系电话','Phone'),c?.phone,false),{...text('email',T('联系邮箱','Email'),c?.email,false),type:'email'},
      {name:'chair_capacity',label:T('牙椅容量','Chair capacity'),type:'number',value:c?.chair_capacity||1,min:1,max:100},select('status',T('状态','Status'),status,c?.status||'ACTIVE'),reason
    ],onSubmit:b=>save('clinic_profile',c,b)});
  };
  handlers['setup-dentist']=id=>{
    const d=state.resources.dentists.find(x=>x.id===id);
    modal({name:T(d?'编辑医师档案':'新增医师档案',d?'Edit clinician':'New clinician'),description:T('医师档案、机构任职、有效资质和系统账号分别核验。新增档案不会生成登录授权。','Profiles, assignments, credentials and login grants are verified separately.'),fields:[
      ...(!d?[text('employee_code',T('内部医师编号（ADC-DR-六位数字）','Staff ID (ADC-DR-six digits)'),'ADC-DR-')]:[]),text('name_zh',T('姓名','Full name'),d?.name_zh),text('name_en',T('英文姓名','English name'),d?.name_en,false),
      text('title_zh',T('职称','Professional title'),d?.title_zh),{...text('email',T('机构邮箱','Work email'),d?.email),type:'email'},text('phone',T('联系电话','Phone'),d?.phone,false),
      {name:'hire_date',label:T('入职日期','Hire date'),type:'date',value:d?.hire_date||state.boot.today},select('employment_status',T('任职状态','Employment status'),status,d?.employment_status||'ACTIVE'),
      {...text('biography_zh',T('专业背景','Professional background'),d?.biography_zh,false),type:'textarea'},reason
    ],onSubmit:b=>save('dentist_profile',d,b)});
  };
  handlers['setup-chair']=id=>{
    const c=state.resources.chairs.find(x=>x.id===id);
    modal({name:T(c?'编辑牙椅资料':'新增牙椅',c?'Edit chair':'New chair'),description:T('已有预约引用时不能直接维护或停用；牙椅不能借编辑迁移到另一诊所。','Active bookings prevent maintenance or deactivation. A chair cannot move between clinics through an edit.'),fields:[
      ...(!c?[h.clinicField(),text('code',T('牙椅代码','Chair code'))]:[]),text('name_zh',T('牙椅名称','Chair name'),c?.name_zh),text('name_en',T('英文名称','English name'),c?.name_en,false),text('room_name_zh',T('诊室名称','Operatory name'),c?.room_name_zh),
      {...text('equipment',T('设备配置（用逗号分隔）','Equipment (comma separated)'),readEquipment(c?.equipment_json||'[]').join('，'),false),type:'textarea'},
      {name:'is_accessible',label:T('无障碍可达','Accessible'),type:'checkbox',value:!!c?.is_accessible,required:false},select('status',T('状态','Status'),[['AVAILABLE',T('可用','Available')],['MAINTENANCE',T('维护中','Maintenance')],['INACTIVE',T('停用','Inactive')]],c?.status||'AVAILABLE'),reason
    ],onSubmit:b=>save('chair_profile',c,b)});
  };
  handlers['setup-hours']=key=>{
    const [clinic,day]=key.split('|'),r=state.resources.hours.find(x=>x.clinic_id===clinic&&Number(x.day_of_week)===Number(day));
    modal({name:T('设置营业时间','Set clinic hours'),description:state.resources.clinics.find(c=>c.id===clinic)?.name_zh+' · '+T(['周日','周一','周二','周三','周四','周五','周六'],['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])[Number(day)],fields:[
      {name:'opens_at',label:T('开始营业','Opens'),type:'time',value:r?.opens_at||'09:00'},{name:'closes_at',label:T('结束营业','Closes'),type:'time',value:r?.closes_at||'18:00'},
      select('slot_minutes',T('排程粒度（分钟）','Slot interval (minutes)'),[5,10,15,20,30,60].map(n=>[String(n),String(n)]),String(r?.slot_minutes||10)),
      {name:'is_closed',label:T('每周此日休息','Closed on this weekday'),type:'checkbox',required:false,value:!!r?.is_closed},reason
    ],onSubmit:b=>save('opening_hours',r,{...b,clinic_id:clinic,day_of_week:Number(day),slot_minutes:Number(b.slot_minutes)})});
  };
  handlers['setup-catalog']=id=>{
    const t=state.resources.treatments.find(x=>x.id===id),required=state.resources.requirements.filter(r=>r.treatment_id===id&&r.requirement_level==='REQUIRED').map(r=>r.qualification_type_id);
    const tomorrow=new Date(state.boot.today+'T12:00:00Z');tomorrow.setUTCDate(tomorrow.getUTCDate()+1);
    modal({name:T(t?'追加目录版本':'新增治疗项目',t?'New catalog version':'New treatment'),wide:true,description:T('历史价格不覆盖。新版本从未来日期生效；若旧版仍有受影响预约，提交会被阻止。请明确资质要求。','Historical fees remain intact. Replacement versions start on a future date; affected bookings block publication. Review qualification requirements.'),fields:[
      {...text('code',T('项目代码','Treatment code'),t?.code),readonly:!!t},text('name_zh',T('项目名称','Treatment name'),t?.name_zh),text('name_en',T('英文名称','English name'),t?.name_en,false),text('category',T('专业分类','Category'),t?.category),
      {name:'duration_minutes',label:T('预计时长（分钟）','Duration (minutes)'),type:'number',value:t?.duration_minutes||30,min:10,max:480},
      {name:'standard_price_fen',label:T('标准价格（元）','Standard fee (CNY)'),type:'money',value:t?.standard_price_fen||0},
      {name:'estimated_cost_fen',label:T('目录估算成本（元）','Estimated cost (CNY)'),type:'money',value:t?.estimated_cost_fen||0},
      {name:'effective_from',label:T('生效日期','Effective from'),type:'date',value:t?tomorrow.toISOString().slice(0,10):state.boot.today},
      {name:'effective_to',label:T('截止日期（可空）','Effective to (optional)'),type:'date',required:false},
      {...text('description_zh',T('项目说明','Description'),t?.description_zh,false),type:'textarea'},reason
    ],body:`<fieldset class="setup-qualifications"><legend>${h.esc(T('必需资质（逐项核对）','Required qualifications'))}</legend>${state.boot.qualifications.map(q=>`<label><input type="checkbox" name="setup-qualification" value="${h.esc(q.id)}" ${required.includes(q.id)?'checked':''}>${h.esc(q.name_zh)}</label>`).join('')}</fieldset>`,
      onReady:()=>{const group=document.querySelector('.setup-qualifications');document.querySelector('.modal-fields')?.after(group);},
      onSubmit:b=>save('catalog_version',t,{...b,qualification_ids:[...document.querySelectorAll('[name="setup-qualification"]:checked')].map(n=>n.value)})});
  };
  handlers['setup-retire']=id=>{
    const t=state.resources.treatments.find(x=>x.id===id);
    modal({name:T('停用目录版本','Retire catalog version'),description:`${t.name_zh} · v${t.version} · `+T('保留历史引用。存在有效预约或未结束治疗计划时不能停用。','Historical references remain. Active bookings or open plans prevent retirement.'),fields:[reason],onSubmit:b=>save('catalog_retire',t,b)});
  };
}
