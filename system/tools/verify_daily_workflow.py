"""Isolated, real HTTP/JDBC checks of daily scenarios, clock boundaries and waiting-list CRUD."""
import os,socket,secrets,subprocess,time,json,hashlib,sqlite3,urllib.parse
from pathlib import Path
from verify import Client
root=Path(__file__).resolve().parents[1]; data=root/'data'/('daily-'+secrets.token_hex(5));data.mkdir(parents=True)
clock=data/'clock.txt';clock.write_text('2026-11-14T23:50:00')
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
base=f'http://127.0.0.1:{port}';checks=[]
env={**os.environ,'APP_ENV':'TEST','DEMO_MODE':'true','DEMO_SCENARIO_MODE':'daily','ADC_TEST_FULL_DEMO':'true','ADC_TEST_NOW_FILE':str(clock),'DATA_DIR':str(data),'PORT':str(port),'BIND_ADDRESS':'127.0.0.1'}
env.pop('DATABASE_URL',None);env.pop('ADC_TEST_LEGACY_PATIENT_WEB',None)
pg=os.environ.get('ADC_DAILY_PG_URL')
if pg:
    uri=urllib.parse.urlparse(pg);assert uri.hostname in ('127.0.0.1','localhost') and uri.path.startswith('/adc_acceptance_');env['DATABASE_URL']=pg
def rows(sql,*args):
    if pg:
        for arg in args:sql=sql.replace('?',"'"+str(arg).replace("'","''")+"'",1)
        r=subprocess.run([os.environ.get('ADC_PSQL','C:/Program Files/PostgreSQL/18/bin/psql.exe'),pg,'-X','-t','-A','-v','ON_ERROR_STOP=1','-c',"SELECT COALESCE(json_agg(x),'[]') FROM ("+sql+") x"],capture_output=True,text=True,encoding='utf8',env={**os.environ,'PGCLIENTENCODING':'UTF8'},check=True);return json.loads(r.stdout)
    with sqlite3.connect(data/'adc-nexus.sqlite') as c:c.row_factory=sqlite3.Row;return [dict(r) for r in c.execute(sql,args)]
def passed(name):checks.append(name);print('PASS',name,flush=True)
log=(data/'server.log').open('w',encoding='utf8');process=subprocess.Popen([env.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED','-jar','target/adc-nexus.jar'],env=env,cwd=root,stdout=log,stderr=log)
try:
    anon=Client(base)
    for _ in range(200):
        try:anon.request('/health');break
        except Exception:
            if process.poll() is not None:raise RuntimeError((data/'server.log').read_text(encoding='utf8'))
            time.sleep(.1)
    m=Client(base).demo('CLINIC_MANAGER');d=Client(base).demo('DENTIST')
    boot=m.request('/bootstrap');assert boot['today']=='2026-11-14' and boot['business_now']=='2026-11-14 15:00:00' and boot['wall_now'].endswith('23:50:00')
    passed('Business workday clock is explicit and separate from real security time')
    agenda=m.request('/appointments?from=2026-11-14&to=2026-11-14')
    assert len(agenda)==11 and len({a['patient_id'] for a in agenda})==11
    assert len({a['dentist_id'] for a in agenda})==2
    assert {a['status'] for a in agenda}>={'CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW'}
    passed('Saturday provides 11 distinct patients, two clinicians and a complete six-state appointment scenario')
    previous=m.request('/appointments?from=2026-11-13&to=2026-11-13')
    future=m.request('/appointments?from=2026-11-15&to=2026-11-15')
    assert 5<=len(previous)<len(agenda) and 3<=len(future)<len(agenda)
    assert {a['status'] for a in previous}=={'COMPLETED','CANCELLED','NO_SHOW'}
    assert {a['status'] for a in future}=={'CONFIRMED'}
    assert all(a['chair_id'] for a in previous+future)
    for day, appointments in [('2026-11-13',previous),('2026-11-14',agenda),('2026-11-15',future)]:
        dashboard=m.request('/dashboard?from='+day+'&to='+day)
        expected_states={a['status']:sum(b['status']==a['status'] for b in appointments) for a in appointments}
        assert {a['status']:a['value'] for a in dashboard['appointment_states']}==expected_states
    assert len(rows("""SELECT i.id FROM appointments a JOIN clinical_visits v ON v.appointment_id=a.id
        JOIN invoices i ON i.visit_id=v.id JOIN payments p ON p.invoice_id=i.id
        WHERE a.appointment_code LIKE 'DEMO-PRIOR-%' AND a.patient_id=v.patient_id AND v.patient_id=i.patient_id
          AND v.status='COMPLETED' AND i.status='PAID' AND p.amount_fen=i.total_fen"""))==2
    passed('Three adjacent days agree with operating totals; earlier care and receipts link to real stored demo encounters')
    visits=d.request('/visits');assert {'SAFETY_REVIEW','WAITING','IN_PROGRESS','COMPLETED'}<={v['status'] for v in visits if v['started_at'].startswith(boot['today'])}
    assert len(m.request('/finance/invoices'))>=10 and len(m.request('/finance/unbilled'))>=2
    assert len(m.request('/finance/periods')['expenses'])>=1
    passed('Doctor queues, completed encounters, bills, refunds, unbilled work and period expenses are populated')
    assert not rows("SELECT id FROM appointments WHERE appointment_code LIKE 'ADC-TODAY-%'")
    for h in rows('SELECT * FROM appointment_status_history'):
        assert '08:30'<=h['occurred_at'][11:16]<='18:30' and h['occurred_at']<=boot['business_now'],h
        assert not(h['from_status']=='CHECKED_IN' and h['to_status']=='CANCELLED')
    assert not rows("SELECT h.id FROM appointment_status_history h JOIN appointments a ON a.id=h.appointment_id WHERE h.occurred_at<a.created_at")
    passed('No legacy cleanup records, night-time clinical events, future clinical events or checked-in-to-cancelled histories')
    historical=rows("SELECT DISTINCT patient_id FROM appointments WHERE appointment_code LIKE 'DEMO-CARE-%'")
    assert len(historical)==14
    assert not rows("SELECT a.id FROM actual_treatment_items a JOIN treatment_item_consents tc ON tc.requested_treatment_item_id=a.requested_treatment_item_id WHERE a.performed_at<tc.captured_at")
    passed('Historical care is distributed across 14 patients and actual treatment does not precede consent')
    assert not rows("SELECT id FROM patients WHERE email LIKE '%@example.test' AND phone NOT LIKE '0000000%'")
    passed('Seeded patient contacts are reserved for demonstration and cannot route to real phones')
    completed=next(a for a in agenda if a['status']=='COMPLETED')
    patient=m.request('/patients/'+completed['patient_id'])
    care=next(v for v in patient['visits'] if v['scheduled_start_at']==completed['scheduled_start_at'])
    assert care['status']=='COMPLETED' and care['signed_notes']>0
    assert not any(v['status']=='CANCELLED' for v in patient['visits'])
    passed('Dossier surfaces the actual signed, completed encounter and excludes cancelled encounters')
    expected=next(a for a in agenda if a['status']=='CONFIRMED' and a['dentist_id']=='dnt-lin-wei')
    m.request('/appointments/'+expected['id'],{'action':'no_show','version':expected['appointment_version']},expect=409)
    checked=next(a for a in agenda if a['status']=='CHECKED_IN' and a['scheduled_start_at'].endswith('15:00:00'))
    oldvid=next(v['id'] for v in visits if v['appointment_id']==checked['id'])
    m.request('/appointments/'+checked['id'],{'action':'cancel','version':checked['appointment_version'],'reason':'不能取消已签到患者'},expect=409)
    undone=m.request('/appointments/'+checked['id'],{'action':'revoke_arrival','version':checked['appointment_version'],'reason':'前台误点，患者尚未到店'})
    assert undone['status']=='CONFIRMED'
    history=m.request('/appointments/'+checked['id'])['history'];assert json.loads(history[-1]['metadata_json'])['event_type']=='REVOKE_ARRIVAL'
    m.request('/appointments/'+checked['id'],{'action':'check_in','version':undone['appointment_version'],'identity_confirmed':True,'declaration':'患者现已到店，已核对身份'})
    assert len(rows('SELECT id FROM clinical_visits WHERE appointment_id=?',checked['id']))==1
    assert d.request('/visits/'+oldvid)['visit']['status']=='SAFETY_REVIEW'
    passed('Revoke check-in restores the booking, retains its audit, and a later check-in safely reopens the encounter')
    v=d.request('/visits/'+oldvid)['visit'];d.request('/visits/'+oldvid,{'action':'review_start','version':v['visit_version'],'history_confirmed':True,'confirm':True,'evidence':'已当面核对病史和过敏情况'})
    a=m.request('/appointments/'+checked['id'])['appointment'];m.request('/appointments/'+a['id'],{'action':'revoke_arrival','version':a['appointment_version'],'reason':'不可撤销已开始接诊'},expect=409)
    passed('Appointment cancellation and arrival revocation cannot bypass clinical work already in progress')
    assert 'waitlist.manage' in d.request('/bootstrap')['principal']['permissions'] and 'appointment.manage' not in d.request('/bootstrap')['principal']['permissions']
    d.request('/appointments',{},expect=403)
    entries=d.request('/waitlist')['entries'];entry=entries[0]
    edited=d.request('/waitlist',{'action':'edit','entry_id':entry['id'],'fingerprint':entry['fingerprint'],'earliest_date':'2026-11-14','latest_date':'2026-11-22','notice_hours':2,'reason':'患者可接受周末安排'})
    d.request('/waitlist',{'action':'withdraw','entry_id':entry['id'],'fingerprint':entry['fingerprint'],'reason':'旧信息不得覆盖'},expect=409)
    slots=d.request('/waitlist/candidates?entry_id='+entry['id'])['slots'];assert len(slots)==1 and slots[0]['dentist_id']=='dnt-lin-wei'
    passed('Doctor has scoped waitlist operations; edits reject stale information and candidates satisfy real scheduling rules')
    other=next(a for a in agenda if a['dentist_id']!='dnt-lin-wei')
    other=m.request('/appointments/'+other['id'],{'action':'cancel','version':other['appointment_version'],'reason':'患者请假改约','initiator':'PATIENT'})
    d.request('/waitlist',{'action':'offer','entry_id':entry['id'],'released_appointment_id':other['id']},expect=403)
    passed('Doctor cannot offer another clinician’s slot, even with a forged request')
    offer=d.request('/waitlist',{'action':'offer','entry_id':entry['id'],'released_appointment_id':slots[0]['id']})
    lease=rows('SELECT * FROM waitlist_offers WHERE id=?',offer['id'])[0];assert lease['expires_at']=='2026-11-15 00:05:00'
    d.request('/waitlist',{'action':'offer','entry_id':entry['id'],'released_appointment_id':slots[0]['id']},expect=409)
    d.request('/waitlist',{'action':'accept','offer_id':offer['id'],'patient_confirmed':False},expect=422)
    booked=d.request('/waitlist',{'action':'accept','offer_id':offer['id'],'patient_confirmed':True});assert booked['patient_id']==entry['patient_id'] and booked['status']=='CONFIRMED'
    d.request('/waitlist',{'action':'accept','offer_id':offer['id'],'patient_confirmed':True},expect=409)
    passed('Real-time 15-minute lease, explicit patient agreement, resource protection and one-time acceptance all work')
    fresh=next(e for e in d.request('/waitlist')['entries'] if e['status']=='WAITING')
    d.request('/waitlist',{'action':'withdraw','entry_id':fresh['id'],'fingerprint':fresh['fingerprint'],'reason':'患者已另行安排就诊'})
    assert rows("SELECT reason FROM audit_events WHERE action='WAITLIST_WITHDRAW' AND entity_id=?",fresh['id'])[0]['reason']=='患者已另行安排就诊'
    passed('Withdrawal stops further offers and retains the actual reason in the audit trail')
    count_before=len(rows('SELECT id FROM appointments'));m.request('/bootstrap');assert len(rows('SELECT id FROM appointments'))==count_before
    passed('Repeated reads and login preserve user edits and do not duplicate the day’s scenarios')
    clock.write_text('2026-11-15T00:10:00')
    nextboot=m.request('/bootstrap');assert nextboot['today']=='2026-11-15' and nextboot['business_now']=='2026-11-15 15:00:00'
    nextagenda=m.request('/appointments?from=2026-11-15&to=2026-11-15');assert len(nextagenda)==10
    for booking in future:
        retained=next(a for a in nextagenda if a['id']==booking['id'])
        assert retained['appointment_version']==booking['appointment_version'] and retained['status']==booking['status']
    passed('Prebooked appointments preserve their IDs, status and version when the next workday becomes current')
    saturday_patients={a['patient_id'] for a in agenda}
    sunday_patients={a['patient_id'] for a in nextagenda}
    assert len(saturday_patients & sunday_patients)<=4
    assert {a['scheduled_start_at'][11:16] for a in agenda}!={a['scheduled_start_at'][11:16] for a in nextagenda}
    assert {'CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW'}=={a['status'] for a in nextagenda}
    passed('Adjacent generated workdays vary patient cohorts, appointment times and volume while retaining all six states')
    waiting=[e for e in m.request('/waitlist')['entries'] if e['status']=='WAITING' and e['latest_date']>=nextboot['today']];assert len(waiting)==3
    assert booked['id'] in {r['id'] for r in m.request('/appointments?from=2026-11-14&to=2026-11-14')}
    carried=m.request('/appointments/'+checked['id'])['appointment']
    assert carried['status']=='IN_PROGRESS' and carried['review_state']=='HISTORICAL_OPEN'
    assert rows('SELECT status FROM appointments WHERE id=?',checked['id'])[0]['status']=='IN_PROGRESS'
    passed('A historical open appointment is flagged without inventing a completed outcome')
    passed('Midnight rollover works without restart or logout, seeds Sunday once and preserves previous operations')
    clock.write_text('2026-12-15T02:27:00');m=Client(base).demo('CLINIC_MANAGER')
    monthboot=m.request('/bootstrap');assert monthboot['business_now']=='2026-12-15 15:00:00'
    assert len(m.request('/appointments?from=2026-12-15&to=2026-12-15'))==12
    m.request('/auth/session');m.request('/bootstrap')
    passed('Next-month 02:27 login still provides complete daytime business without expiring the real login session')
    clock.write_text('2027-01-14T02:27:00');m=Client(base).demo('CLINIC_MANAGER')
    assert len(m.request('/appointments?from=2027-01-14&to=2027-01-14'))==13
    periods=m.request('/finance/periods');assert any(p['period_code']=='2027-Q1' for p in periods['periods']) and any(e['incurred_on']=='2027-01-14' for e in periods['expenses'])
    passed('Two-month and new-quarter rollover preserves a full scenario and supplies the new financial period and expenses')
    if not pg:assert rows('PRAGMA foreign_key_check')==[] and rows('PRAGMA integrity_check')[0]['integrity_check']=='ok'
    else:assert rows('SELECT COUNT(*) AS n FROM actual_treatment_items a LEFT JOIN requested_treatment_items r ON r.id=a.requested_treatment_item_id WHERE r.id IS NULL')[0]['n']==0
    passed('Database referential and linkage integrity remains valid')
    proof={'passed':True,'count':len(checks),'checks':checks,'adjacent_days':{'prior':len(previous),'current':len(agenda),'next':len(future),'after_rollover':len(nextagenda),'shared_patients':len(saturday_patients & sunday_patients)},'jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest(),'database':'PostgreSQL' if pg else 'SQLite','data_directory':str(data)}
    (root/('qa/daily-workflow-postgres.json' if pg else 'qa/daily-workflow.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
finally:process.terminate();process.wait(timeout=20);log.close()
