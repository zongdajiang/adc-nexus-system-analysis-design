"""Real password verification for public synthetic staff identities, including disabled mode."""
from pathlib import Path
import os,socket,secrets,subprocess,time,json,hashlib,sqlite3,urllib.parse
from verify import Client
root=Path(__file__).resolve().parents[1];data=root/'data'/('demo-passwords-'+secrets.token_hex(5));data.mkdir(parents=True)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
base=f'http://127.0.0.1:{port}';checks=[]
env={**os.environ,'APP_ENV':'TEST','DEMO_MODE':'true','DEMO_SCENARIO_MODE':'daily','ADC_TEST_FULL_DEMO':'true','ADC_TEST_NOW':'2026-11-14T02:27:00','DATA_DIR':str(data),'PORT':str(port),'BIND_ADDRESS':'127.0.0.1'}
env.pop('DATABASE_URL',None);env.pop('ADC_TEST_NOW_FILE',None)
pg=os.environ.get('ADC_LOGIN_PG_URL')
if pg:
    uri=urllib.parse.urlparse(pg);assert uri.hostname in ('127.0.0.1','localhost') and uri.path.startswith('/adc_acceptance_');env['DATABASE_URL']=pg
def passed(name):checks.append(name);print('PASS',name,flush=True)
def rows(sql):
    if pg:
        r=subprocess.run([os.environ.get('ADC_PSQL','C:/Program Files/PostgreSQL/18/bin/psql.exe'),pg,'-X','-t','-A','-v','ON_ERROR_STOP=1','-c',"SELECT COALESCE(json_agg(x),'[]') FROM ("+sql+") x"],capture_output=True,text=True,encoding='utf8',env={**os.environ,'PGCLIENTENCODING':'UTF8'},check=True);return json.loads(r.stdout)
    with sqlite3.connect(data/'adc-nexus.sqlite') as c:c.row_factory=sqlite3.Row;return [dict(r) for r in c.execute(sql)]
log=(data/'server.log').open('w',encoding='utf8');process=None
def launch(enabled=True):
    global process
    process=subprocess.Popen([env.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED','-jar','target/adc-nexus.jar'],env={**env,'DEMO_MODE':str(enabled).lower()},cwd=root,stdout=log,stderr=log)
    for _ in range(180):
        try:Client(base).request('/health');return
        except Exception:
            if process.poll() is not None:raise RuntimeError((data/'server.log').read_text(encoding='utf8'))
            time.sleep(.15)
    raise RuntimeError('Server did not start')
try:
    launch();config=Client(base).request('/auth/config');accounts=config['demo_accounts'];password=config['demo_password']
    assert len(accounts)==6 and len({a['username'] for a in accounts})==6 and len(password)>=12
    assert {a['role'] for a in accounts}=={'CLINIC_MANAGER','DENTIST','FRONT_DESK','CASHIER','HQ_OPERATIONS','HQ_FINANCE'}
    assert not any(k in a for a in accounts for k in ['password_hash','password_salt','email','phone','permissions'])
    passed('Only six named synthetic staff accounts have published copyable credentials; no admin or patient account is exposed')
    clients={}
    for a in accounts:
        c=Client(base);result=c.request('/auth/login',{'username':a['username'],'password':password});c.csrf=result['csrf'];clients[a['role']]=c
        session=c.request('/auth/session');p=session['principal'];boot=c.request('/bootstrap')
        assert p['name']==a['person_name'] and [r['code'] for r in p['roles']]==['JDBC_'+a['role']]
        assert session['demo_session'] is True and boot['business_now']=='2026-11-14 15:00:00'
        assert p['network']==a['role'].startswith('HQ_')
        assert not {'access.manage','portal.read'}&set(p['permissions'])
    methods=rows("SELECT DISTINCT auth_method FROM auth_sessions WHERE revoked_at IS NULL")
    assert methods==[{'auth_method':'PASSWORD'}],methods
    passed('All six roles authenticate through PBKDF2 password login, retain their named role/scope, and use the daily business scene')
    doctor=clients['DENTIST'];doctor.request('/finance/invoices',expect=403);doctor.request('/admin/access',expect=403)
    Client(base).request('/auth/login',{'username':accounts[1]['username'],'password':password,'role':'CLINIC_MANAGER'},expect=403)
    passed('A supplied role cannot promote a physician to manager, finance or administrator')
    Client(base).request('/auth/login',{'username':accounts[0]['username'],'password':'WrongPassword2026!'},expect=401)
    Client(base).request('/auth/login',{'username':'jdbc-demo-admin','password':password},expect=401)
    passed('Wrong passwords and unpublished elevated identities are rejected')
    doctor.request('/auth/password',{'oldPassword':password,'newPassword':'NotAValidPublicChange2026!'},expect=403)
    repeat=Client(base).request('/auth/login',{'username':accounts[1]['username'],'password':password});assert repeat['csrf']
    passed('Shared demo passwords cannot be changed by an evaluator; subsequent reviewers can still sign in')
    records=rows("SELECT username,password_hash,password_salt,password_iterations FROM app_users WHERE id IN ('jdbc-demo-clinic_manager','jdbc-demo-dentist','jdbc-demo-front_desk','jdbc-demo-cashier','jdbc-demo-hq_operations','jdbc-demo-hq_finance')")
    assert len(records)==6 and len({r['password_salt'] for r in records})==6
    assert all(r['password_hash']!=password and r['password_iterations']==600000 for r in records)
    digest=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()
    passed('Even public demonstration passwords are stored as separate salted hashes, never plaintext in the user table')
    before=len(rows('SELECT id FROM appointments'));process.terminate();process.wait(timeout=20);launch()
    assert hashlib.sha256(json.dumps(rows("SELECT username,password_hash,password_salt,password_iterations FROM app_users WHERE id IN ('jdbc-demo-clinic_manager','jdbc-demo-dentist','jdbc-demo-front_desk','jdbc-demo-cashier','jdbc-demo-hq_operations','jdbc-demo-hq_finance')"),sort_keys=True).encode()).hexdigest()==digest
    assert len(rows('SELECT id FROM appointments'))==before
    passed('Restart preserves provisioned hashes and all appointment records without resetting the dataset')
    old_client=clients['CLINIC_MANAGER'];process.terminate();process.wait(timeout=20);launch(False)
    hidden=Client(base).request('/auth/config');assert hidden['demo_accounts']==[] and hidden['demo_password'] is None
    Client(base).request('/auth/login',{'username':accounts[0]['username'],'password':password},expect=401)
    old_client.request('/bootstrap',expect=403)
    passed('Turning off demo mode hides credentials and blocks new and retained demo sessions')
    if not pg:assert rows('PRAGMA foreign_key_check')==[]
    proof={'passed':True,'count':len(checks),'checks':checks,'database':'PostgreSQL' if pg else 'SQLite','jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest()}
    (root/('qa/demo-passwords-postgres.json' if pg else 'qa/demo-passwords-sqlite.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
finally:
    if process and process.poll() is None:process.terminate();process.wait(timeout=20)
    log.close()
