"""Role/API and retained-record lifecycle checks in a fresh synthetic JDBC database."""
from pathlib import Path
import os, socket, secrets, subprocess, time, json, hashlib, sqlite3, urllib.parse
from verify import Client
root=Path(__file__).resolve().parents[1];data=root/'data'/('responsibilities-'+secrets.token_hex(5));data.mkdir()
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
base=f'http://127.0.0.1:{port}';checks=[];matrix=[];admin_password=secrets.token_urlsafe(24)
env={**os.environ,'APP_ENV':'TEST','DEMO_MODE':'true','ADC_TEST_FULL_DEMO':'true','DEMO_SCENARIO_MODE':'daily',
     'ADC_TEST_NOW':'2026-11-14T15:00:00','PORT':str(port),'DATA_DIR':str(data),'BIND_ADDRESS':'127.0.0.1','ADMIN_PASSWORD':admin_password}
for name in ('DATABASE_URL','ADC_TEST_LEGACY_PATIENT_WEB','ADC_TEST_NOW_FILE'):env.pop(name,None)
pg=os.environ.get('ADC_REVIEW_PG_URL')
if pg:
    u=urllib.parse.urlparse(pg);assert u.hostname in ('127.0.0.1','localhost') and u.path.startswith('/adc_acceptance_');env['DATABASE_URL']=pg
def passed(name):checks.append(name);print('PASS',name,flush=True)
def must(value):assert value
log=(data/'server.log').open('w',encoding='utf8');process=subprocess.Popen([env.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED','-jar','target/adc-nexus.jar'],cwd=root,env=env,stdout=log,stderr=log)
try:
    for _ in range(180):
        try:Client(base).request('/health');break
        except Exception:time.sleep(.1)
    roles=['CLINIC_MANAGER','DENTIST','FRONT_DESK','CASHIER','HQ_OPERATIONS','HQ_FINANCE']
    conf=Client(base).request('/auth/config');users={}
    for role in roles:
        user=Client(base);account=next(a for a in conf['demo_accounts'] if a['role']==role)
        user.csrf=user.request('/auth/login',{'username':account['username'],'password':conf['demo_password']})['csrf'];users[role]=user
    definitions={
        '/dashboard':set(roles),'/patients':set(roles)-{'HQ_FINANCE'},'/appointments':set(roles)-{'HQ_FINANCE'},
        '/visits':{'CLINIC_MANAGER','DENTIST'},'/finance/invoices':{'CLINIC_MANAGER','CASHIER','HQ_FINANCE'},
        '/finance/unbilled':{'CLINIC_MANAGER','CASHIER','HQ_FINANCE'},'/finance/periods':{'CLINIC_MANAGER','HQ_FINANCE'},
        '/resources':set(roles),'/analytics':{'CLINIC_MANAGER','HQ_OPERATIONS','HQ_FINANCE'},
        '/expansion':{'HQ_OPERATIONS','HQ_FINANCE'},'/followups':{'CLINIC_MANAGER','DENTIST','FRONT_DESK','HQ_OPERATIONS'},
        '/admin/access':set(),'/audit':set(),'/portal':set()}
    for role,user in users.items():
        for route,allowed in definitions.items():
            code=200 if role in allowed else 403;user.request(route,expect=code);matrix.append({'role':role,'route':route,'status':code})
        passed(role+' matches all 14 collection read boundaries, including direct URLs')
    mutations=[('/patients',{},'patient.manage'),('/appointments',{},'appointment.manage'),('/visits/denied',{'action':'note'},'clinical.write'),
        ('/finance/invoices',{},'finance.manage'),('/finance/periods',{'action':'expense'},'expense.manage'),('/finance/periods',{'action':'close'},'period.manage'),
        ('/resources',{'action':'credential'},'workforce.manage'),('/resources',{'action':'catalog_version'},'catalog.manage'),
        ('/resources',{'action':'withdraw_schedule'},'resource.manage'),('/admin/access',{'action':'status'},'access.manage'),('/expansion',{},'expansion.manage')]
    denials=0
    for role,user in users.items():
        permissions=user.request('/bootstrap')['principal']['permissions']
        for route,body,permission in mutations:
            if permission not in permissions:user.request(route,body,expect=403);denials+=1
    passed(str(denials)+' unauthorized mutations are rejected before record validation or writes')
    manager,doctor,front,cash,ops,finance=(users[r] for r in roles)
    local=manager.request('/resources');network=ops.request('/resources');cid='cln-tianhe'
    assigned={a['dentist_id'] for a in network['assignments'] if a['clinic_id']==cid}
    assert {d['id'] for d in local['dentists']}<=assigned
    assert {q['dentist_id'] for q in local['credentials']}<=assigned
    assert len(local['dentists'])<len(network['dentists'])
    passed('Local resource and bootstrap directories exclude other-clinic clinicians and credentials')
    for role in ('CASHIER','FRONT_DESK','DENTIST'):
        user=users[role];assert all('estimated_cost_fen' not in t for t in user.request('/resources')['treatments'])
        assert all('estimated_cost_fen' not in t for t in user.request('/bootstrap')['treatments'])
    assert cash.request('/resources')['credentials']==[] and finance.request('/resources')['credentials']==[]
    assert all(not any(k in d for k in ('phone','email','hire_date')) for d in cash.request('/resources')['dentists'])
    passed('Clinical/reception/cash roles do not receive internal estimated costs; non-workforce roles receive no credential details or private clinician contacts')
    foreign=next(c for c in network['clinics'] if c['id']!=cid)
    for role in ('CLINIC_MANAGER','DENTIST','FRONT_DESK','CASHIER'):
        users[role].request('/appointments?clinic_id='+foreign['id'],expect=403)
    passed('Four local roles reject forged foreign-clinic appointment filters')
    unbilled=cash.request('/finance/unbilled');bills=cash.request('/finance/invoices');assert unbilled and bills
    assert all(a.get('appointment_id') for a in unbilled+bills)
    assert not any(k in a for a in unbilled+bills for k in ('history_text','content_zh','password_hash'))
    passed('Cash desk receives a minimal appointment-to-bill link without clinical record access')
    # Local schedule cancellation and safe removal of coverage preserve the source row and audit reason.
    body={'action':'closure','clinic_id':cid,'starts_at':'2026-11-23 18:00:00','ends_at':'2026-11-23 18:30:00','reason':'设备检查临时停诊'}
    manager.request('/resources',body)
    closure=next(r for r in manager.request('/resources')['closures'] if r['reason_zh']==body['reason'])
    withdrawal={'action':'withdraw_schedule','kind':'closure','id':closure['id'],'fingerprint':closure['fingerprint'],'reason':'检查结束，恢复接诊'}
    front.request('/resources',withdrawal,expect=403)
    manager.request('/resources',{**withdrawal,'fingerprint':'outdated'},expect=409)
    manager.request('/resources',{**withdrawal,'reason':''},expect=422)
    manager.request('/resources',withdrawal)
    assert next(r for r in manager.request('/resources')['closures'] if r['id']==closure['id'])['status']=='CANCELLED'
    manager.request('/resources',withdrawal,expect=409)
    passed('Closure create/read/withdraw retains history, requires a reason and rejects stale, repeated or unauthorized commands')
    manager.request('/resources',{**body,'action':'exception','dentist_id':'dnt-lin-wei','reason':'医师临时请假'})
    row=next(r for r in manager.request('/resources')['exceptions'] if r['reason_zh']=='医师临时请假')
    manager.request('/resources',{'action':'withdraw_schedule','kind':'exception','id':row['id'],'fingerprint':row['fingerprint'],'reason':'请假取消，恢复接诊'})
    assert next(r for r in manager.request('/resources')['exceptions'] if r['id']==row['id'])['status']=='CANCELLED'
    passed('Clinician time off can be withdrawn without deleting its original facts')
    manager.request('/resources',{'action':'availability','clinic_id':cid,'dentist_id':'dnt-lin-wei','day_of_week':1,'starts_at':'18:00','ends_at':'18:30','effective_from':'2026-11-23','effective_to':'2026-11-23'})
    row=next(r for r in manager.request('/resources')['availability'] if r['starts_at']=='18:00' and r['effective_from']=='2026-11-23')
    manager.request('/resources',{'action':'withdraw_schedule','kind':'schedule','id':row['id'],'fingerprint':row['fingerprint'],'reason':'班次登记有误'})
    assert next(r for r in manager.request('/resources')['availability'] if r['id']==row['id'])['status']=='INACTIVE'
    passed('An unused schedule may be deactivated and remains in the directory')
    appt=next(a for a in manager.request('/appointments?from=2026-11-14&to=2026-11-14') if a['status']=='CONFIRMED' and a['dentist_id']=='dnt-lin-wei')
    day=6
    cover=next(r for r in manager.request('/resources')['availability'] if r['dentist_id']=='dnt-lin-wei' and r['clinic_id']==cid and r['status']=='ACTIVE' and r['day_of_week']==day and r['starts_at']<=appt['scheduled_start_at'][11:16] and r['ends_at']>=appt['scheduled_end_at'][11:16])
    manager.request('/resources',{'action':'withdraw_schedule','kind':'schedule','id':cover['id'],'fingerprint':cover['fingerprint'],'reason':'不应影响预约'},expect=409)
    assert next(r for r in manager.request('/resources')['availability'] if r['id']==cover['id'])['fingerprint']==cover['fingerprint']
    passed('Removing required booking coverage is rejected and the full schedule transaction rolls back')
    foreign_row=next(r for r in network['availability'] if r['clinic_id']!=cid)
    manager.request('/resources',{'action':'withdraw_schedule','kind':'schedule','id':foreign_row['id'],'fingerprint':foreign_row['fingerprint'],'reason':'越权测试'},expect=403)
    passed('Schedule record ownership is checked even when an attacker submits an authentic foreign fingerprint')
    # Combination of a network technical role and a local workforce role must not widen sensitive directory access.
    admin=Client(base);admin.csrf=admin.request('/auth/login',{'username':'owner','password':admin_password})['csrf']
    pwd=secrets.token_urlsafe(24);username='review.'+secrets.token_hex(4)
    uid=admin.request('/admin/access',{'action':'create_user','username':username,'password':pwd,'email':username+'@example.invalid','display_name':'权限组合核验'})['user_id']
    for role,clinic in [('ADMIN',''),('FRONT_DESK',cid)]:admin.request('/admin/access',{'action':'grant','user_id':uid,'role_id':'jdbc-role-'+role,'clinic_id':clinic,'effective_from':'2026-01-01'})
    mixed=Client(base);mixed.csrf=mixed.request('/auth/login',{'username':username,'password':pwd})['csrf']
    assert {r['dentist_id'] for r in mixed.request('/resources')['credentials']}<=assigned
    assert all(not d.get('email') for d in mixed.request('/resources')['dentists'] if d['id'] not in assigned)
    passed('A network administrator plus local receptionist cannot inherit network-wide private workforce fields')
    # A physician role alone is not a responsible-clinician identity.
    loose=admin.request('/admin/access',{'action':'create_user','username':username+'.dr','password':pwd,'email':username+'.dr@example.invalid','display_name':'未关联医师核验'})['user_id']
    admin.request('/admin/access',{'action':'grant','user_id':loose,'role_id':'jdbc-role-DENTIST','clinic_id':cid,'effective_from':'2026-01-01'},expect=422)
    admin.request('/admin/access',{'action':'grant','user_id':loose,'role_id':'jdbc-role-DENTIST','clinic_id':cid,'effective_from':'2026-01-01','dentist_id':'dnt-lin-wei'})
    # Simulate a damaged historical account binding only inside this isolated fixture.
    if pg:
        sql="DELETE FROM system_settings WHERE setting_key='dentist_user:"+loose+"'"
        subprocess.run([os.environ.get('ADC_PSQL','C:/Program Files/PostgreSQL/18/bin/psql.exe'),pg,'-X','-v','ON_ERROR_STOP=1','-c',sql],capture_output=True,check=True)
    else:
        with sqlite3.connect(data/'adc-nexus.sqlite') as c:c.execute('DELETE FROM system_settings WHERE setting_key=?',('dentist_user:'+loose,))
    loose_client=Client(base);loose_client.csrf=loose_client.request('/auth/login',{'username':username+'.dr','password':pwd})['csrf'];loose_client.request('/visits',expect=403)
    passed('An unlinked physician role cannot turn a missing identity into all-clinician record access')
    audit=admin.request('/audit');assert any(e.get('reason')=='检查结束，恢复接诊' and e['entity_id']==closure['id'] for e in audit)
    passed('Withdrawal history retains the actual actor, affected record and stated reason')
    if not pg:
        with sqlite3.connect(data/'adc-nexus.sqlite') as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and c.execute('PRAGMA foreign_key_check').fetchall()==[]
    result={'passed':True,'count':len(checks),'checks':checks,'read_matrix':matrix,'read_route_checks':len(matrix),'denied_mutations':denials,'database':'PostgreSQL' if pg else 'SQLite','jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest(),'data_directory':str(data),'business_mutations_in_isolated_fixture_only':True}
    (root/('qa/responsibilities-postgres.json' if pg else 'qa/responsibilities.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
finally:
    process.terminate();process.wait(timeout=20);log.close()
