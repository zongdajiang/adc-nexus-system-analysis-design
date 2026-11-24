// Clinic-local date/time strings deliberately avoid conversion through the browser's timezone.
export function filterAppointments(rows,{dentist='',status='',search=''}={}) {
  const q=search.trim().toLocaleLowerCase();
  return rows.filter(a=>(!dentist||a.dentist_id===dentist)&&(!status||a.status===status)&&(!q||[a.patient_name,a.appointment_code,a.treatment_name,a.dentist_name,a.chair_name].some(v=>String(v||'').toLocaleLowerCase().includes(q))));
}
export function shiftDay(day,delta) {
  const d=new Date(day+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+delta);return d.toISOString().slice(0,10);
}
function minute(value,day) {
  const d=String(value).slice(0,10), t=String(value).slice(11,16).split(':').map(Number);
  return d<day?0:d>day?1440:t[0]*60+t[1];
}
export function buildCalendarModel(rows,{day,group='dentist',resources={},clinic='',dentist=''}={}) {
  const active=rows.filter(a=>!['CANCELLED','NO_SHOW'].includes(a.status));
  const key=a=>group==='chair'?(a.chair_id||'unassigned'):(a.dentist_id||'unassigned');
  const columns=new Map();
  const add=(id,name,detail='')=>{if(!columns.has(id))columns.set(id,{id,name,detail,events:[]});};
  const clinicName=id=>resources.clinics?.find(c=>c.id===id)?.name_zh||'';
  if(group==='chair')for(const c of resources.chairs||[]) {
    if(clinic&&c.clinic_id!==clinic)continue;
    add(c.id,c.name_zh||c.code,`${clinicName(c.clinic_id)}${c.status==='AVAILABLE'?'':c.status==='MAINTENANCE'?' · 维护中':' · 已停用'}`);
  } else for(const d of resources.dentists||[]) {
    if(dentist&&d.id!==dentist)continue;
    const assigned=(resources.assignments||[]).filter(a=>a.status==='ACTIVE'&&a.dentist_id===d.id&&(!clinic||a.clinic_id===clinic)&&a.effective_from<=day&&(!a.effective_to||a.effective_to>=day));
    if(assigned.length)add(d.id,d.name_zh,assigned.map(a=>a.clinic_name||clinicName(a.clinic_id)).filter((v,i,s)=>v&&s.indexOf(v)===i).join(' / '));
  }
  let start=480,end=1140;
  for(const a of active) {
    const s=minute(a.scheduled_start_at,day),e=minute(a.scheduled_end_at,day);
    if(!Number.isFinite(s)||!Number.isFinite(e)||e<=s)continue;
    add(key(a),group==='chair'?(a.chair_name||'未分配牙椅'):(a.dentist_name||'未分配医师'),a.clinic_name||'');
    start=Math.min(start,Math.floor(s/60)*60);end=Math.max(end,Math.ceil(e/60)*60);
    columns.get(key(a)).events.push({...a,start:s,end:e});
  }
  for(const c of columns.values()) {
    c.events.sort((a,b)=>a.start-b.start||b.end-a.end||String(a.id).localeCompare(String(b.id)));
    // Each connected group of overlapping appointments receives independent equal-width lanes.
    let cluster=[],until=-1;
    const flush=()=>{const lanes=[];for(const e of cluster){let lane=lanes.findIndex(t=>t<=e.start);if(lane<0)lane=lanes.length;lanes[lane]=e.end;e.lane=lane;}for(const e of cluster)e.lanes=lanes.length;cluster=[];};
    for(const e of c.events){if(cluster.length&&e.start>=until){flush();until=-1;}cluster.push(e);until=Math.max(until,e.end);}flush();
  }
  return {start,end,group,columns:[...columns.values()],excluded:rows.length-active.length};
}
export function renderCalendar(model,{esc,T,badge}) {
  if(!model.columns.length)return `<div class="calendar-empty">${T('当前范围没有任职医师或已登记的预约。可切换日期或新建预约。','No assigned dentists or recorded appointments in this scope.')}</div>`;
  const time=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  const hours=[];for(let n=model.start;n<=model.end;n+=60)hours.push(n);
  const halfHours=[];for(let n=model.start+30;n<model.end;n+=60)halfHours.push(n);
  const widths=model.columns.map(c=>Math.max(1,...c.events.map(a=>a.lanes))*300);
  const statuses = ['CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED'];
  const position=n=>`calc(${n-model.start} * var(--minute-height))`;
  return `<div class="calendar-legend" aria-label="${T('预约状态','Appointment statuses')}">${statuses.map(badge).join('')}</div><div class="calendar-scroll" tabindex="0" role="region" aria-label="${T('预约时间表，可横向和纵向滚动','Appointment timeline; scroll horizontally and vertically')}">
    <div class="clinic-calendar" style="--minute-height:2.6px;--calendar-height:calc(${model.end-model.start} * var(--minute-height));grid-template-columns:64px ${widths.map(w=>`minmax(${w}px,1fr)`).join(' ')};min-width:${64+widths.reduce((a,b)=>a+b,0)}px">
    <div class="calendar-corner">${T('时间','Time')}</div>${model.columns.map(c=>`<div class="calendar-column-head"><strong>${esc(c.name)}</strong><small>${esc(c.detail)}</small><span>${c.events.length} ${T('项预约','appointments')}</span></div>`).join('')}
    <div class="calendar-time-rail">${hours.map(n=>`<span style="top:${position(n)}">${time(n)}</span>`).join('')}</div>
    ${model.columns.map(c=>`<div class="calendar-day-column">
      ${hours.map(n=>`<div class="calendar-hour-line" style="top:${position(n)}"></div>`).join('')}${halfHours.map(n=>`<div class="calendar-half-hour-line" style="top:${position(n)}"></div>`).join('')}
      ${c.events.map(a=>`<button type="button" class="calendar-event status-${esc(a.status.toLowerCase())}" data-act="appointment-detail" data-id="${esc(a.id)}" data-duration="${a.end-a.start}" style="top:calc(${a.start-model.start} * var(--minute-height) + 2px);height:calc(${a.end-a.start} * var(--minute-height) - 4px);left:calc(${a.lane/a.lanes*100}% + 4px);width:calc(${100/a.lanes}% - 8px)" aria-label="${esc(`${time(a.start)}—${time(a.end)} ${a.patient_name} ${a.treatment_name} ${a.dentist_name} ${a.chair_name||T('未分配牙椅','Chair unassigned')}`)}">
        <span class="calendar-event-content"><span class="calendar-event-time"><span>${time(a.start)}—${time(a.end)}</span>${badge(a.status)}</span>
        <span class="calendar-event-primary"><strong>${esc(a.patient_name)}</strong><span class="calendar-event-treatment">${esc(a.treatment_name)}</span></span>
        <span class="calendar-event-resource">${[a.clinic_name,a.dentist_name,a.chair_name||T('未分配牙椅','Chair unassigned')].filter(Boolean).map(esc).join(' · ')}</span></span>
      </button>`).join('')}
    </div>`).join('')}</div></div><div class="calendar-footnote">${T('诊所本地时间。空白不代表可预约；创建与改期须重新校验排班、资质和资源冲突。取消及未到诊记录保留在列表中。','Clinic local time. Blank space does not imply availability; scheduling rechecks shifts, credentials and conflicts. Cancelled/no-show records remain in the list.')}</div>`;
}

/** A shared minute scale keeps every card readable without changing its time or extending into its neighbour. */
export function fitCalendar(root) {
  const calendar=root?.querySelector('.clinic-calendar');
  if(!calendar)return()=>{};
  const cards=[...calendar.querySelectorAll('.calendar-event')],scroller=calendar.closest('.calendar-scroll');
  let frame=0,disposed=false;
  const fit=()=>{
    frame=0;if(disposed||!calendar.isConnected)return;
    let scale=2.6;
    for(const card of cards){
      const content=card.querySelector('.calendar-event-content'),style=getComputedStyle(card);
      const frameHeight=['paddingTop','paddingBottom','borderTopWidth','borderBottomWidth'].reduce((sum,key)=>sum+parseFloat(style[key]||0),0);
      const natural=Math.max(content.scrollHeight,content.getBoundingClientRect().height);
      scale=Math.max(scale,(natural+frameHeight+6)/Number(card.dataset.duration));
    }
    scale=Math.ceil(scale*100)/100;
    const previous=parseFloat(calendar.style.getPropertyValue('--minute-height'))||2.6;
    if(Math.abs(scale-previous)<.01)return;
    const anchor=scroller.scrollTop;
    calendar.style.setProperty('--minute-height',scale+'px');
    scroller.scrollTop=anchor*scale/previous;
  };
  const schedule=()=>{if(!disposed&&!frame)frame=requestAnimationFrame(fit);};
  // Intrinsic content observation handles wrapped names, font loading and text enlargement.
  const observer=typeof ResizeObserver==='function'?new ResizeObserver(schedule):null;
  cards.forEach(card=>observer?.observe(card.querySelector('.calendar-event-content')));
  window.addEventListener('resize',schedule);document.fonts?.ready.then(schedule);fit();
  if (cards.length && scroller.scrollTop === 0) {
    const firstStart = Math.min(...cards.map(card => card.offsetTop));
    const scale = parseFloat(calendar.style.getPropertyValue('--minute-height')) || 2.6;
    scroller.scrollTop = Math.max(0, firstStart - 30 * scale);
  }
  return()=>{disposed=true;observer?.disconnect();window.removeEventListener('resize',schedule);if(frame)cancelAnimationFrame(frame);};
}
