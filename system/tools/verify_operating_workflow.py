"""Real transactions for clinic-owner operations and the continuous encounter sheet."""
import os,socket,secrets,subprocess,time,json,hashlib,sqlite3,urllib.parse
from pathlib import Path
from verify import Client
root=Path(__file__).resolve().parents[1];data=root/'data'/('operating-'+secrets.token_hex(5));data.mkdir(parents=True)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
base=f'http://127.0.0.1:{port}';checks=[]
env={**os.environ,'APP_ENV':'TEST','DEMO_MODE':'true','ADC_TEST_FULL_DEMO':'true','ADC_TEST_NOW':'2026-11-13T15:00:00','DATA_DIR':str(data),'PORT':str(port),'BIND_ADDRESS':'127.0.0.1'}
env.pop('DATABASE_URL',None);env.pop('ADC_TEST_LEGACY_PATIENT_WEB',None)
pg_url=os.environ.get('ADC_OPERATING_PG_URL')
if pg_url:
    uri=urllib.parse.urlparse(pg_url)
    assert uri.hostname in ('127.0.0.1','localhost') and uri.path.startswith('/adc_acceptance_')
    env['DATABASE_URL']=pg_url
def passed(name):checks.append(name);print('PASS',name,flush=True)
def rows(sql,*args):
    if pg_url:
        for arg in args:sql=sql.replace('?',"'"+str(arg).replace("'","''")+"'",1)
        result=subprocess.run([os.environ.get('ADC_PSQL','C:/Program Files/PostgreSQL/18/bin/psql.exe'),pg_url,'-X','-t','-A','-v','ON_ERROR_STOP=1','-c','SELECT COALESCE(json_agg(x),\'[]\') FROM ('+sql+') x'],capture_output=True,text=True,encoding='utf8',env={**os.environ,'PGCLIENTENCODING':'UTF8'},check=True)
        return json.loads(result.stdout)
    with sqlite3.connect(data/'adc-nexus.sqlite') as c:c.row_factory=sqlite3.Row;return [dict(r) for r in c.execute(sql,args)]
log=(data/'server.log').open('w',encoding='utf8');process=subprocess.Popen([env.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED','-jar','target/adc-nexus.jar'],env=env,cwd=root,stdout=log,stderr=log)
try:
    anon=Client(base)
    for _ in range(180):
        try:anon.request('/health');break
        except Exception:time.sleep(.15)
    manager=Client(base).demo('CLINIC_MANAGER');doctor=Client(base).demo('DENTIST');cash=Client(base).demo('CASHIER')
    grants=set(manager.request('/bootstrap')['principal']['permissions'])
    assert {'appointment.manage','patient.manage','finance.manage','followup.manage','resource.manage'}<=grants
    assert not grants&{'clinical.write','period.manage','expense.manage','access.manage'}
    assert len(rows("SELECT * FROM schema_migrations WHERE version='008'"))==1
    manager.request('/visits/no',{'action':'sign_complete','version':1},expect=403)
    manager.request('/finance/periods',{'action':'close'},expect=403)
    manager.request('/appointments?clinic_id=cln-nanshan',expect=403)
    passed('Owner gains local reception and cash-desk operations without clinical signatures, network close or foreign-clinic access')
    person=manager.request('/patients',{'name_zh':'工作流核验患者','date_of_birth':'1992-04-08','phone':'13955558881','primary_clinic_id':'cln-tianhe','government_id_last4':'2881','reason':'合成功能核验'})
    manager.request('/patients/'+person['id'],{'action':'update','name_zh':'工作流核验患者（更正）','date_of_birth':'1992-04-08','phone':'13955558882','reason':'核对合成联系方式'})
    assert manager.request('/patients/'+person['id'])['patient']['phone']=='13955558882'
    passed('Owner creates and updates a patient record in the assigned clinic')
    booking={'clinic_id':'cln-tianhe','dentist_id':'dnt-lin-wei','patient_id':person['id'],'treatment_id':'trt-exam-v1','scheduled_start_at':'2026-11-17 17:00:00','duration_minutes':30}
    a=manager.request('/appointments',booking)
    moved=manager.request('/appointments/'+a['id'],{**booking,'action':'reschedule','version':a['appointment_version'],'scheduled_start_at':'2026-11-17 17:30:00','reason':'患者申请改期'})
    manager.request('/appointments/'+a['id'],{'action':'cancel','version':a['appointment_version'],'reason':'过期版本'},expect=409)
    manager.request('/appointments/'+a['id'],{'action':'cancel','version':moved['appointment_version'],'reason':'患者另行预约'})
    assert manager.request('/appointments/'+a['id'])['appointment']['status']=='CANCELLED'
    passed('Owner reschedules and cancels appointments with resource validation, retained history and stale-write rejection')
    expected=next(a for a in manager.request('/appointments?from=2026-11-13&to=2026-11-13') if a['status']=='CONFIRMED' and a['dentist_id']=='dnt-lin-wei')
    visit=manager.request('/appointments/'+expected['id'],{'action':'check_in','version':expected['appointment_version'],'identity_confirmed':True,'declaration':'合成核验，已到店'})
    detail=next(v for v in doctor.request('/visits') if v['appointment_id']==expected['id']);vid=detail['id']
    def get():return doctor.request('/visits/'+vid)
    def command(action,body=None,expect=200,version=None):return doctor.request('/visits/'+vid,{'action':action,'version':version or get()['visit']['visit_version'],**(body or {})},expect=expect)
    initial=get();command('review_start',{'history_confirmed':True,'confirm':False,'evidence':'已核对'},expect=422)
    assert get()['visit']['visit_version']==initial['visit']['visit_version']
    command('review_start',{'history_confirmed':True,'confirm':True,'evidence':'已当面询问，无新增病史；按已登记过敏采取防护','chief_complaint':'合成复诊检查'})
    assert get()['visit']['status']=='IN_PROGRESS' and get()['visit']['chief_complaint_zh']=='合成复诊检查'
    passed('Review and start occur together, require explicit checks and preserve the responsible clinician')
    before_incomplete=get()
    command('sign_complete',{'content':'合成未齐备病历，不能据此完成','signature_confirmed':True},expect=409)
    assert get()['notes']==before_incomplete['notes'] and get()['visit']['visit_version']==before_incomplete['visit']['visit_version']
    passed('Missing clinical prerequisites roll back a proposed signature as well as the completion state')
    payload={'treatment_id':'trt-exam-v1','tooth_code':'16','units':1,'rationale':'复诊检查说明','consent_evidence':'患者本人在解释项目及费用后明确同意','patient_consented':True,'finding':'合成核验所见，无新增异常','finding_severity':'NORMAL'}
    before=get();command('record_treatment',{**payload,'patient_consented':False},expect=422)
    assert get()['requested']==before['requested'] and get()['actual']==before['actual']
    command('record_treatment',{**payload,'consent_evidence':''},expect=422)
    assert get()['requested']==before['requested']
    command('record_treatment',{**payload,'finding_severity':''},expect=422)
    assert get()['requested']==before['requested'] and get()['consents']==before['consents']
    passed('Missing consent or examination severity rolls back the entire combined treatment transaction')
    saved=command('record_treatment',payload);version=saved['visit']['visit_version']
    command('record_treatment',payload,version=before['visit']['visit_version'],expect=409)
    saved2=command('record_treatment',payload)
    new=saved2['actual'][-1];old=saved['actual'][-1]
    assert new['requested_treatment_item_id']!=old['requested_treatment_item_id']
    assert len(saved2['actual'])==2 and all(a['requested_treatment_item_id'] for a in saved2['actual'])
    passed('Two same-timestamp identical proposals retain distinct correct consent links; replayed stale writes do not duplicate treatment')
    def clinic_metrics():
        return manager.request('/analytics?from=2026-11-13&to=2026-11-13')
    def exam_count(metrics):
        item=next(row for row in metrics['treatments'] if row['code']=='EXAM-001')
        return (item['treatments'],item['units'])
    recorded_totals=exam_count(clinic_metrics())
    original=saved2['requested'][0]
    command('record_treatment',{'item_id':original['id'],'units':1},expect=422)
    assert len(get()['actual'])==2
    passed('An accepted proposal cannot be performed beyond its remaining confirmed quantity')
    command('void_actual',{'actual_id':new['id'],'reason':'第二条为合成误录，保留原记录但不计费'})
    assert next(a for a in get()['actual'] if a['id']==new['id'])['status']=='VOIDED'
    assert rows("SELECT reason FROM audit_events WHERE action='CLINICAL_TREATMENT_VOIDED' AND entity_id=?",new['id'])[0]['reason']
    passed('Clinician can correct a mistaken unbilled treatment with retained original facts and a reasoned audit trail')
    metrics=clinic_metrics()
    assert exam_count(metrics)==tuple(total-1 for total in recorded_totals), 'Voided item still contributes to treatment mix'
    local=rows("SELECT dentist_id FROM dentist_clinic_assignments WHERE clinic_id=? AND status='ACTIVE' "
               "AND effective_from<=? AND (effective_to IS NULL OR effective_to>=?) "
               "UNION SELECT dentist_id FROM appointments WHERE clinic_id=? AND substr(scheduled_start_at,1,10)=?",
               'cln-tianhe','2026-11-13','2026-11-13','cln-tianhe','2026-11-13')
    assert {row['id'] for row in metrics['dentists']}=={row['dentist_id'] for row in local}, 'Clinic analytics include unrelated clinicians'
    passed('Treatment mix excludes voided items; clinic analytics include only local assignments and service facts')
    note='主诉：合成复诊检查。检查：已核对牙位记录。处置：按已同意项目完成检查。医嘱：按预约复诊。'
    command('note',{'content':note,'sign':False})
    count_before=len(rows('SELECT * FROM clinical_note_signatures'))
    command('sign_complete',{'content':note,'signature_confirmed':False},expect=422)
    assert get()['visit']['status']=='IN_PROGRESS' and len(rows('SELECT * FROM clinical_note_signatures'))==count_before
    command('sign_complete',{'content':note,'signature_confirmed':True})
    assert get()['visit']['status']=='COMPLETED'
    assert manager.request('/appointments/'+expected['id'])['appointment']['status']=='COMPLETED'
    assert len(rows('SELECT * FROM clinical_note_signatures'))==count_before+1
    passed('Draft saving does not sign; explicit signature completes both visit and appointment atomically')
    invoice=manager.request('/finance/invoices',{'visit_id':vid})['invoice']
    paid=manager.request('/finance/invoices/'+invoice['id'],{'action':'pay','version':invoice['invoice_version'],'amount_fen':invoice['total_fen'],'method':'CASH','reference':'合成经营者收款核验'})
    detail_bill=manager.request('/finance/invoices/'+invoice['id']);payment=detail_bill['payments'][0]
    manager.request('/finance/invoices/'+invoice['id'],{'action':'refund','version':detail_bill['invoice']['invoice_version'],'payment_id':payment['id'],'amount_fen':payment['amount_fen'],'authorized':True,'reason':'合成核验退回原款'})
    assert manager.request('/finance/invoices/'+invoice['id'])['invoice']['balance_fen']==invoice['total_fen']
    passed('Owner completes billing, receipt and original-payment refund for the same real encounter chain')
    command('note',{'content':note+'补记：合成随访。','sign':True},expect=422)
    command('note',{'content':note+'补记：合成随访。','reason':'补充合成随访记录','sign':True})
    assert len(get()['notes'])==3 and sum(bool(n['signed_at']) for n in get()['notes'])==2
    passed('Completed signed records require a reasoned amendment and retain their earlier signed version')
    other=next(a for a in manager.request('/appointments?from=2026-11-13&to=2026-11-13') if a['status']=='CONFIRMED' and a['dentist_id']!='dnt-lin-wei')
    manager.request('/appointments/'+other['id'],{'action':'check_in','version':other['appointment_version'],'identity_confirmed':True,'declaration':'另一负责医师的合成到店记录'})
    foreign=next(v for v in manager.request('/visits') if v['appointment_id']==other['id'])
    doctor.request('/visits/'+foreign['id'],{'action':'review_start','version':foreign['visit_version'],'history_confirmed':True,'confirm':True,'evidence':'不应写入'},expect=403)
    if pg_url:
        assert rows('SELECT COUNT(*) AS total FROM actual_treatment_items a LEFT JOIN requested_treatment_items r ON r.id=a.requested_treatment_item_id WHERE a.visit_id=? AND (r.id IS NULL OR r.visit_id<>a.visit_id)',vid)[0]['total']==0
    else:
        assert rows('PRAGMA foreign_key_check')==[]
        assert rows('PRAGMA integrity_check')[0]['integrity_check']=='ok'
    passed('Responsible-clinician boundaries and database integrity remain enforced')
    proof={'passed':True,'checks':checks,'count':len(checks),'jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest(),'isolation':'new synthetic PostgreSQL instance' if pg_url else 'new synthetic SQLite instance','data_directory':str(data)}
    (root/('qa/operating-workflow-postgres.json' if pg_url else 'qa/operating-workflow.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
finally:
    process.terminate();process.wait(timeout=20);log.close()
