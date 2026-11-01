"""Additional real HTTP/JDBC checks, run inside verify.py's isolated synthetic fixture."""
import datetime as dt


def run_upgrade(check, ensure, Client, base, people, owner, operator, patient, other, source_visit, run):
    front=people['FRONT_DESK'];ops=people['HQ_OPERATIONS'];manager=people['CLINIC_MANAGER'];dentist=people['DENTIST']
    cid='cln-tianhe'
    def resource(kind,id):
        return next(x for x in ops.request('/resources')[kind] if x['id']==id)
    clinic=resource('clinics',cid)
    clinic_body={k:clinic.get(k) or '' for k in ['id','fingerprint','name_zh','name_en','city_zh','city_en','address_zh','phone','email','chair_capacity','status']}
    clinic_body.update(action='clinic_profile',reason='Synthetic directory validation')
    check('UP01 receptionist cannot edit clinic master',lambda:front.request('/resources',clinic_body,expect=403))
    check('UP01 administrator is not automatically an operations editor',lambda:owner.request('/resources',clinic_body,expect=403))
    check('UP01 clinic manager edits own contact details',lambda:manager.request('/resources',{**clinic_body,'phone':'020-80000001'}))
    check('UP01 stale clinic fingerprint cannot overwrite an edit',lambda:manager.request('/resources',clinic_body,expect=409))
    foreign=next(x for x in ops.request('/resources')['clinics'] if x['id']!=cid)
    check('UP01 local manager cannot edit another clinic',lambda:manager.request('/resources',{**clinic_body,'id':foreign['id'],'fingerprint':foreign['fingerprint']},expect=403))
    new_clinic=check('UP01 operations creates an independent clinic',lambda:ops.request('/resources',{
        **clinic_body,'id':'','code':'QA-'+run[:8],'name_zh':'合成新诊所','status':'ACTIVE','chair_capacity':2}))
    ensure(not any(h['clinic_id']==new_clinic['id'] for h in ops.request('/resources')['hours']))
    check('UP01 new clinic has no invented opening hours',lambda:ensure(not any(h['clinic_id']==new_clinic['id'] for h in ops.request('/resources')['hours'])))
    chair=check('UP01 new chair persists equipment and accessibility',lambda:ops.request('/resources',{
        'action':'chair_profile','clinic_id':new_clinic['id'],'code':'ROOM-01','name_zh':'一号牙椅','room_name_zh':'综合诊室',
        'equipment':'综合治疗台，口内扫描仪','is_accessible':True,'status':'AVAILABLE','reason':'合成资源档案'}))
    check('UP01 equipment is stored as a structured list',lambda:ensure('口内扫描仪' in resource('chairs',chair['id'])['equipment_json']))
    new_doc=check('UP01 operations creates a physician profile without account',lambda:ops.request('/resources',{
        'action':'dentist_profile','employee_code':'ADC-DR-900001','name_zh':'测试医师','title_zh':'执业医师','email':'clinician-'+run+'@example.invalid',
        'hire_date':'2026-12-31','employment_status':'ACTIVE','reason':'合成医师档案'}))
    check('UP01 physician profile does not grant login',lambda:ensure(not any(u['username']=='ADC-DR-900001' for u in owner.request('/admin/access')['users'])))
    check('UP01 invalid physician staff code is rejected',lambda:ops.request('/resources',{
        'action':'dentist_profile','employee_code':'ADMIN-900001','name_zh':'拒绝案例','title_zh':'医师','email':'rejected-'+run+'@example.invalid',
        'hire_date':'2026-12-31','employment_status':'ACTIVE','reason':'合成拒绝案例'},expect=422))
    cat={'action':'catalog_version','code':'QA-TX-'+run[:8],'name_zh':'合成复查项目','name_en':'Synthetic review',
         'category':'诊断与复查','duration_minutes':30,'standard_price_fen':12345,'estimated_cost_fen':2000,
         'effective_from':'2026-12-31','qualification_ids':['qlf-general'],'reason':'合成目录发布'}
    check('UP02 clinic manager cannot change global fees',lambda:manager.request('/resources',cat,expect=403))
    tx=check('UP02 new treatment has explicit required qualification',lambda:ops.request('/resources',cat))
    t=resource('treatments',tx['id'])
    ensure(any(x['treatment_id']==tx['id'] and x['qualification_type_id']=='qlf-general' for x in ops.request('/resources')['requirements']))
    replacement={**cat,'id':t['id'],'fingerprint':t['fingerprint'],'effective_from':'2027-01-02','standard_price_fen':22222}
    tx2=check('UP02 fee change creates a new version',lambda:ops.request('/resources',replacement))
    old=resource('treatments',t['id']);new=resource('treatments',tx2['id'])
    check('UP02 previous price and identity remain unchanged',lambda:ensure(old['standard_price_fen']==12345 and old['effective_to']=='2027-01-01' and new['version']==2))
    check('UP02 invalid qualifications roll back catalog and prior validity',lambda:ops.request('/resources',{
        **cat,'fingerprint':new['fingerprint'],'effective_from':'2027-02-01','qualification_ids':['not-a-qualification']},expect=422))
    check('UP02 rejected replacement leaves latest catalog intact',lambda:ensure(resource('treatments',new['id'])['fingerprint']==new['fingerprint']))

    # Existing source visit belongs to Lin; only its responsible physician may recommend a recall.
    recommendation={'action':'recommend','visit_id':source_visit['id'],'due_on':'2027-01-10','priority':'ROUTINE',
                    'reason':'合成医师建议：复核本次治疗后的情况','contact_allowed':False}
    check('UP04 cashier cannot read recall information',lambda:people['CASHIER'].request('/followups',expect=403))
    check('UP04 front desk cannot invent clinician recall advice',lambda:front.request('/followups',recommendation,expect=403))
    no_permission=check('UP04 responsible dentist records recall advice',lambda:dentist.request('/followups',recommendation))
    rid=no_permission['id']
    def follow(id=rid): return front.request('/followups/'+id)['followup']
    check('UP04 duplicate active advice for same visit/date rejected',lambda:dentist.request('/followups',recommendation,expect=409))
    check('UP04 unauthorized outbound contact is blocked',lambda:front.request('/followups',{'action':'contact','id':rid,'version':1,'revision':1,'channel':'PHONE','outcome':'NO_ANSWER','next_contact_on':'2027-01-01','note':'合成联系'},expect=409))
    # The API uses the common optimistic version request field.
    check('UP04 patient may decline during in-person communication',lambda:front.request('/followups',{'action':'contact','id':rid,'version':1,'channel':'IN_PERSON','outcome':'DECLINED','note':'合成患者当面婉拒'}))
    check('UP04 declined recall retains advice and contact evidence',lambda:ensure(follow()['status']=='DECLINED' and len(front.request('/followups/'+rid)['events'])==2))
    active=check('UP04 new recall may be proposed after an ended recommendation',lambda:dentist.request('/followups',{**recommendation,'contact_allowed':True}))
    fid=active['id']
    check('UP04 unconfigured delivery is not simulated by a contact entry',lambda:front.request('/followups',{'action':'contact','id':fid,'version':1,'channel':'PHONE','outcome':'NO_ANSWER','note':'合成已完成电话联系','next_contact_on':'2027-01-01'}))
    check('UP04 stale follow-up version cannot replace contact history',lambda:front.request('/followups',{'action':'contact','id':fid,'version':1,'channel':'PHONE','outcome':'AGREED','note':'stale'},expect=409))
    original=operator.request('/visits/'+source_visit['id'])['visit']['appointment_id']
    check('UP04 source appointment cannot count as its own subsequent recall',lambda:front.request('/followups',{'action':'link','id':fid,'version':2,'appointment_id':original,'note':'合成错误关联'},expect=409))

    resources=ops.request('/resources');boot=operator.request('/bootstrap')
    prohibited={q['treatment_id'] for q in resources['requirements'] if q['requirement_level']=='REQUIRED'}
    simple=next(t for t in boot['treatments'] if t['status']=='ACTIVE' and t['id'] not in prohibited and t['effective_from']<='2026-12-31' and (not t['effective_to'] or t['effective_to']>='2026-12-31'))
    booking={'patient_id':patient['id'],'clinic_id':cid,'dentist_id':'dnt-lin-wei','treatment_id':simple['id'],'duration_minutes':30}
    for hour in ['16:00','15:00','14:00','17:00','11:00']:
        candidate={**booking,'scheduled_start_at':'2026-12-31 '+hour+':00'}
        if operator.request('/scheduling/validate',candidate)['valid']:booking=candidate;break
    else: raise AssertionError('No isolated recall fixture slot available')
    appointment=front.request('/appointments',booking)
    aid=appointment['id'];v=appointment['appointment_version']
    check('UP03 contact confirmation changes no reservation state',lambda:front.request('/appointments/'+aid,{'action':'confirmation','version':v,'confirmation_state':'CONFIRMED','channel':'PHONE','reason':'合成患者已确认'}))
    a=front.request('/appointments/'+aid)['appointment'];ensure(a['status']=='CONFIRMED' and a['confirmation_state']=='CONFIRMED')
    check('UP03 confirmation history has a separate structured event identity',lambda:ensure(any(__import__('json').loads(h['metadata_json']).get('event_type')=='PATIENT_CONFIRMATION' and h['reason_text']=='合成患者已确认' for h in front.request('/appointments/'+aid)['history'])))
    # Re-save this same slot to isolate confirmation reset from resource availability.
    front.request('/appointments/'+aid,{'action':'reschedule','version':a['appointment_version'],'reason':'合成再次核对同一方案'})
    a=front.request('/appointments/'+aid)['appointment']
    check('UP03 rescheduling resets contact confirmation',lambda:ensure(a['confirmation_state']=='PENDING'))
    blocked_clinic=resource('clinics',cid)
    check('UP01 cannot deactivate clinic with an active appointment',lambda:manager.request('/resources',{**clinic_body,'fingerprint':blocked_clinic['fingerprint'],'status':'INACTIVE'},expect=409))
    check('UP01 cannot deactivate physician with active care',lambda:ops.request('/resources',{
        **resource('dentists','dnt-lin-wei'),'action':'dentist_profile','employment_status':'INACTIVE','reason':'合成停用影响核查'},expect=409))
    day=(dt.date(2026,12,31).weekday()+1)%7
    hours=next(h for h in resources['hours'] if h['clinic_id']==cid and h['day_of_week']==day)
    check('UP01 opening-hour change cannot strand an active appointment',lambda:manager.request('/resources',{
        **hours,'action':'opening_hours','is_closed':True,'reason':'合成停诊影响核查'},expect=409))
    check('UP04 link an actual booked return appointment',lambda:front.request('/followups',{'action':'link','id':fid,'version':2,'appointment_id':aid,'note':'合成患者同意并已安排'}))
    check('UP04 an appointment alone does not prove completed care',lambda:front.request('/followups',{'action':'complete','id':fid,'version':3,'note':'合成完成核查'},expect=409))
    check('UP04 local scope remains enforced for recall lists',lambda:front.request('/followups?clinic_id='+foreign['id'],expect=403))
    # A new return visit is completed through the same safety/consent/signature guards.
    front.request('/appointments/'+aid,{'action':'check_in','version':a['appointment_version'],'identity_confirmed':True,'declaration':'合成复诊身份核实'})
    visit=next(v for v in operator.request('/visits') if v['appointment_id']==aid)
    def care(action,**data):
        detail=operator.request('/visits/'+visit['id'])
        return operator.request('/visits/'+visit['id'],{'action':action,'version':detail['visit']['visit_version'],**data})
    care('safety',history_confirmed=True,evidence='合成复诊风险再次核实');care('start')
    care('observation',tooth_code='16',observation_type='EXAMINATION',severity='LOW',finding='合成复诊观察')
    plan=care('plan',treatment_id=simple['id'],tooth_code='16',units=1,rationale='合成复诊方案')
    item=plan['requested'][-1]['id'];care('consent',item_id=item,decision='ACCEPTED',evidence='合成逐项同意')
    care('actual',treatment_id=simple['id'],requested_treatment_item_id=item,tooth_code='16',units=1,notes='合成复诊实施')
    care('note',content='合成复诊病历：检查、实施与后续建议。',sign=True);care('complete')
    check('UP04 recall closes only after linked care is actually complete',lambda:front.request('/followups',{'action':'complete','id':fid,'version':3,'note':'合成复诊及临床完成均已核对'}))
    check('UP04 all advice/contact/link/completion events are retained',lambda:ensure(front.request('/followups/'+fid)['followup']['status']=='COMPLETED' and len(front.request('/followups/'+fid)['events'])==4))
