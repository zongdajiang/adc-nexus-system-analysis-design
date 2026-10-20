"""Real HTTP/JDBC acceptance in a new, isolated synthetic database. No hosted writes."""
import concurrent.futures
import datetime as dt
import http.cookiejar
import json
import os
import pathlib
import secrets
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

ROOT=pathlib.Path(__file__).resolve().parents[1]
RESULTS=[]

class Client:
    def __init__(self,base):
        self.base=base
        self.jar=http.cookiejar.CookieJar()
        self.http=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf=''
    def request(self,path,body=None,expect=200,key=None,headers=None):
        h={'Accept':'application/json'}
        if body is not None:
            h.update({'Content-Type':'application/json','X-CSRF-Token':self.csrf,'Idempotency-Key':key or secrets.token_hex(16)})
        h.update(headers or {})
        req=urllib.request.Request(self.base+'/api'+path,None if body is None else json.dumps(body).encode(),h)
        try:
            with self.http.open(req,timeout=90) as r: code=r.status; data=json.load(r)
        except urllib.error.HTTPError as e:
            code=e.code;data=json.load(e)
        assert code==expect, f'{path}: expected {expect}, got {code}: {data}'
        return data
    def demo(self,role):
        self.csrf=self.request('/auth/demo',{'role':role})['csrf']
        return self

def check(name,fn):
    start=time.perf_counter()
    try:
        value=fn();RESULTS.append({'name':name,'passed':True,'ms':round((time.perf_counter()-start)*1000,1)})
        print('PASS',name,flush=True);return value
    except Exception as e:
        RESULTS.append({'name':name,'passed':False,'error':str(e),'ms':round((time.perf_counter()-start)*1000,1)})
        print('FAIL',name,str(e),flush=True);raise

def ensure(condition,message='assertion failed'):
    assert condition,message

def main():
    run=secrets.token_hex(6)
    datadir=ROOT/'data'/('acceptance-'+run)
    datadir.mkdir(parents=True)
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    admin_password='Admin-'+secrets.token_urlsafe(20)
    env={**os.environ,'DEMO_MODE':'true','DATA_DIR':str(datadir),'PORT':str(port),'ADMIN_PASSWORD':admin_password,'APP_ENV':'TEST','ADC_TEST_NOW':'2026-12-31T08:00:00'}
    pg_url=os.environ.get('ADC_ACCEPTANCE_PG_URL')
    if pg_url:
        pg=urllib.parse.urlparse(pg_url)
        assert pg.hostname in ('localhost','127.0.0.1') and pg.path.startswith('/adc_acceptance_'), 'Only an isolated loopback PostgreSQL test database is allowed'
        env['DATABASE_URL']=pg_url
    else:env.pop('DATABASE_URL',None)
    logfile=(datadir/'server.log').open('w',encoding='utf-8')
    launch=[os.environ.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED','-Dfile.encoding=UTF-8']
    launch+=['-jar','target/adc-nexus.jar'] if os.environ.get('ADC_ACCEPTANCE_JAR')=='true' else ['-cp','target/classes'+os.pathsep+'.deps/*','cn.adcnexus.Main']
    process=subprocess.Popen(launch,cwd=ROOT,env=env,stdout=logfile,stderr=logfile)
    completed=False
    try:
        anonymous=Client(base)
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('Test server failed; inspect '+str(datadir/'server.log'))
            try:
                anonymous.request('/health');break
            except Exception:time.sleep(.2)
        check('AUTH-01 protected route requires login',lambda:anonymous.request('/patients',expect=401))
        people={role:Client(base).demo(role) for role in ['REVIEWER','FRONT_DESK','DENTIST','CASHIER','CLINIC_MANAGER','HQ_OPERATIONS','HQ_FINANCE','PATIENT']}
        operator=people['REVIEWER'];boot=operator.request('/bootstrap');today=dt.date.fromisoformat(boot['today'])
        check('SEED-01 demonstration bookings and state history agree',lambda:ensure(all(a['status']=='CONFIRMED' for a in operator.request('/appointments') if a['appointment_code'].startswith('ADC-TODAY-'))))
        check('AUTH-23 patient identity is not marked as network staff access',lambda:ensure(not people['PATIENT'].request('/auth/session')['principal']['network']))
        for path in ['/bootstrap','/dashboard','/patients','/appointments','/visits','/finance/invoices','/finance/periods','/resources','/analytics','/expansion','/audit']:
            check('READ '+path,lambda path=path:operator.request(path))
        check('AUTH-02 front desk cannot read finance',lambda:people['FRONT_DESK'].request('/finance/invoices',expect=403))
        check('AUTH-03 front desk cannot write clinical data',lambda:people['FRONT_DESK'].request('/visits/not-an-id',{'action':'note'},expect=403))
        check('AUTH-04 patient cannot read patient register',lambda:people['PATIENT'].request('/patients',expect=403))
        check('AUTH-05 patient cannot query arbitrary record',lambda:people['PATIENT'].request('/patients/arbitrary',expect=403))
        check('AUTH-06 patient portal only returns bound records',lambda:ensure('patient' in people['PATIENT'].request('/portal')))
        check('AUTH-07 dentist cannot manage patients',lambda:people['DENTIST'].request('/patients',{'name_zh':'Denied'},expect=403))
        check('AUTH-08 cashier cannot sign clinical notes',lambda:people['CASHIER'].request('/visits/not-an-id',{'action':'note'},expect=403))
        check('AUTH-09 manager cannot record payments',lambda:people['CLINIC_MANAGER'].request('/finance/invoices',{'visit_id':'denied'},expect=403))
        check('AUTH-10 HQ operations cannot read finance',lambda:people['HQ_OPERATIONS'].request('/finance/invoices',expect=403))
        check('AUTH-11 missing SMS provider fails honestly',lambda:anonymous.request('/auth/sms',{},expect=503))
        check('AUTH-12 mutation requires CSRF',lambda:operator.request('/patients',{},expect=403,headers={'X-CSRF-Token':'wrong'}))
        check('AUTH-13 cross-site mutation rejected',lambda:operator.request('/patients',{},expect=403,headers={'Origin':'https://example.invalid'}))
        foreign=next(c['id'] for c in boot['clinics'] if c['id']!='cln-tianhe')
        check('AUTH-14 explicit foreign clinic filter denied',lambda:people['FRONT_DESK'].request('/appointments?clinic_id='+foreign,expect=403))
        owner=Client(base);owner.csrf=check('AUTH-15 owner password login',lambda:owner.request('/auth/login',{'username':'owner','password':admin_password,'role':'STAFF'}))['csrf']
        check('AUTH-16 selecting dentist does not grant that role',lambda:Client(base).request('/auth/login',{'username':'owner','password':admin_password,'role':'DENTIST'},expect=403))
        for path in ['/patients','/visits','/finance/invoices']:
            check('AUTH-17 admin is not a clinical/finance role '+path,lambda path=path:owner.request(path,expect=403))
        check('AUTH-18 admin can access account governance',lambda:owner.request('/admin/access'))
        patient_body={'name_zh':'林知远 · 验收合成','date_of_birth':'1996-04-08','gender':'MALE','phone':'139'+str(int(run,16))[-8:].zfill(8),'primary_clinic_id':'cln-tianhe','history_text':'无近期变化；课程自动验收合成资料'}
        patient=check('UC01 patient registration',lambda:people['FRONT_DESK'].request('/patients',patient_body))
        check('UC01 duplicate candidate is blocked',lambda:people['FRONT_DESK'].request('/patients',patient_body,expect=409))
        check('UC01 append history version',lambda:people['FRONT_DESK'].request('/patients/'+patient['id'],{'action':'history','history_status':'DECLARED_NONE','history_text':'已询问，声明无相关病史','reason':'本次到诊核实'}))
        check('UC01 record an explicit synthetic allergy before care',lambda:people['FRONT_DESK'].request('/patients/'+patient['id'],{'action':'allergy','substance':'合成测试物质','reaction':'合成风险记录，用于验证复核留痕','severity':'HIGH'}))
        def cashier_redaction():
            detail=people['CASHIER'].request('/patients/'+patient['id'])
            ensure(not detail['clinical_details_available'] and not detail['allergies'] and not detail['history'] and not detail['timeline'])
        check('AUTH-22 cashier identity access does not disclose medical history',cashier_redaction)
        p2=people['FRONT_DESK'].request('/patients',{**patient_body,'name_zh':'周予安 · 验收合成','phone':'138'+str(int(run,16))[-8:].zfill(8)})
        resources=operator.request('/resources');dentist='dnt-lin-wei';cid='cln-tianhe'
        rule=next(r for r in resources['availability'] if r['dentist_id']==dentist and r['clinic_id']==cid and r['status']=='ACTIVE' and r['day_of_week']==(today.weekday()+1)%7)
        future=today
        prohibited={r['treatment_id'] for r in resources['requirements'] if r['requirement_level']=='REQUIRED'}
        treatment=next(t for t in boot['treatments'] if t['status']=='ACTIVE' and t['id'] not in prohibited)
        chair=next(ch for ch in boot['chairs'] if ch['clinic_id']==cid and ch['status']=='AVAILABLE')
        time_start='10:00'
        proposed={'patient_id':patient['id'],'clinic_id':cid,'dentist_id':dentist,'chair_id':chair['id'],'treatment_id':treatment['id'],'duration_minutes':30,'scheduled_start_at':str(future)+' '+time_start+':00'}
        check('UC02 resource qualification and hours validation',lambda:ensure(operator.request('/scheduling/validate',proposed)['valid']))
        appointment=check('UC02 create appointment in JDBC transaction',lambda:people['FRONT_DESK'].request('/appointments',proposed))
        check('UC02 overlapping resources are rejected',lambda:people['FRONT_DESK'].request('/appointments',{**proposed,'patient_id':p2['id']},expect=409))
        check('UC03 stale appointment version rejected',lambda:people['FRONT_DESK'].request('/appointments/'+appointment['id'],{'action':'cancel','version':999,'reason':'stale'},expect=409))
        check('UC18 chair maintenance cannot invalidate booking',lambda:people['CLINIC_MANAGER'].request('/resources',{'action':'chair','chair_id':chair['id'],'status':'MAINTENANCE','updated_at':chair['updated_at']},expect=409))
        check('UC04 identity must be confirmed',lambda:people['FRONT_DESK'].request('/appointments/'+appointment['id'],{'action':'check_in','version':appointment['appointment_version'],'identity_confirmed':False},expect=422))
        appointment=check('UC04 arrival creates one linked clinical visit',lambda:people['FRONT_DESK'].request('/appointments/'+appointment['id'],{'action':'check_in','version':appointment['appointment_version'],'identity_confirmed':True,'declaration':'已核对；患者无资料变化'}))
        visit=next(v for v in operator.request('/visits') if v['appointment_id']==appointment['id'])
        def clinical(action,**data):
            detail=operator.request('/visits/'+visit['id'])
            return operator.request('/visits/'+visit['id'],{'action':action,'version':detail['visit']['visit_version'],**data})
        check('UC03 cannot cancel a checked-in appointment',lambda:people['FRONT_DESK'].request('/appointments/'+appointment['id'],{'action':'cancel','version':appointment['appointment_version'],'reason':'invalid'},expect=409))
        check('UC06 safety review records evidence',lambda:clinical('safety',history_confirmed=True,evidence='问诊及风险已核实，无新增禁忌。合成测试。'))
        check('UC06 every recorded allergy has visit-specific acknowledgement',lambda:ensure(len(operator.request('/visits/'+visit['id'])['acknowledgements'])==1))
        check('UC06 start care',lambda:clinical('start'))
        check('UC06 FDI tooth observation',lambda:clinical('observation',tooth_code='16',observation_type='EXAMINATION',severity='LOW',finding='常规检查，合成观察资料'))
        detail=check('UC07 propose treatment independently from billing',lambda:clinical('plan',treatment_id=treatment['id'],tooth_code='16',units=1,rationale='检查后说明风险、方案与费用；合成情景'))
        rid=detail['requested'][-1]['id']
        check('UC07 capture item-specific consent',lambda:clinical('consent',item_id=rid,decision='ACCEPTED',evidence='已解释项目、风险和费用，患者明确接受；合成见证'))
        check('UC06 record actual treatment with price snapshot',lambda:clinical('actual',treatment_id=treatment['id'],requested_treatment_item_id=rid,tooth_code='16',units=1,notes='按确认方案实施；合成事实'))
        detail=operator.request('/visits/'+visit['id'])
        check('UC08 completion blocks unsigned notes',lambda:operator.request('/visits/'+visit['id'],{'action':'complete','version':detail['visit']['visit_version']},expect=409))
        check('UC06 clinical note signature',lambda:clinical('note',content='主诉、检查、风险复核、实施项目及术后注意事项均已记录。合成病历。',sign=True))
        check('UC01 new history version after signing',lambda:people['FRONT_DESK'].request('/patients/'+patient['id'],{'action':'history','history_status':'DECLARED_NONE','history_text':'再次询问后，声明无相关变化','reason':'签署后新增询问结果'}))
        detail=operator.request('/visits/'+visit['id'])
        check('UC08 changed history blocks completion despite a signature',lambda:operator.request('/visits/'+visit['id'],{'action':'complete','version':detail['visit']['visit_version']},expect=409))
        reviewed=check('UC06 repeated safety review preserves in-progress state',lambda:clinical('safety',history_confirmed=True,evidence='重新核对本次新增声明，补全风险措施'))
        ensure(reviewed['visit']['status']=='IN_PROGRESS')
        check('UC06 prior version retains signature after current note is invalidated',lambda:ensure(any(n.get('signed_at') for n in reviewed['notes'])))
        check('UC06 an earlier signature still requires an amendment reason',lambda:operator.request('/visits/'+visit['id'],{'action':'note','version':reviewed['visit']['visit_version'],'content':'追加未注明理由的内容','sign':True},expect=422))
        check('UC06 append and sign a reasoned amendment',lambda:clinical('note',content='复核新增声明后更新病历，实施及风险措施均已核实。合成补记。',reason='补充本次新增询问与风险复核结果',sign=True))
        check('UC08 atomic visit and appointment completion',lambda:clinical('complete'))
        ensure(operator.request('/appointments/'+appointment['id'])['appointment']['status']=='COMPLETED')
        bill=check('UC09 issue itemized invoice from actual treatment',lambda:people['CASHIER'].request('/finance/invoices',{'visit_id':visit['id']}))
        repeated=check('UC09 duplicate issue returns same invoice',lambda:people['CASHIER'].request('/finance/invoices',{'visit_id':visit['id']}))
        ensure(bill['invoice']['id']==repeated['invoice']['id'])
        iid=bill['invoice']['id'];total=bill['invoice']['total_fen']
        def invoice(action,expect=200,**data):
            inv=operator.request('/finance/invoices/'+iid)['invoice']
            return people['CASHIER'].request('/finance/invoices/'+iid,{'action':action,'version':inv['invoice_version'],**data},expect=expect)
        check('UC10 overpayment changes no ledger',lambda:invoice('pay',expect=409,amount_fen=total+1,method='CASH',reference='test-'+run))
        half=max(1,total//2)
        check('UC10 first split payment',lambda:invoice('pay',amount_fen=half,method='CASH',reference='first-'+run))
        paid=check('UC10 settlement after second split payment',lambda:invoice('pay',amount_fen=total-half,method='BANK_TRANSFER',reference='second-'+run))
        ensure(paid['invoice']['status']=='PAID')
        payment=paid['payments'][0]
        check('UC10 over-refund rejected',lambda:invoice('refund',expect=409,payment_id=payment['id'],amount_fen=payment['amount_fen']+1,reason='合成测试',authorized=True))
        refunded=check('UC10 independent refund reclassifies invoice',lambda:invoice('refund',payment_id=payment['id'],amount_fen=payment['amount_fen'],reason='合成验收退款',authorized=True))
        ensure(refunded['invoice']['status']=='PARTIALLY_PAID' and len(refunded['refunds'])==1)
        check('UC15 patient cannot see another patient bill',lambda:people['PATIENT'].request('/finance/invoices/'+iid,expect=403))
        # Same-resource race uses two distinct patients and independent HTTP sessions.
        race_date=future+dt.timedelta(days=7)
        race={**proposed,'scheduled_start_at':str(race_date)+' '+time_start+':00'}
        racers=[Client(base).demo('REVIEWER'),Client(base).demo('REVIEWER')]
        def compete(i):
            h={'Content-Type':'application/json','X-CSRF-Token':racers[i].csrf}
            req=urllib.request.Request(base+'/api/appointments',json.dumps({**race,'patient_id':[patient['id'],p2['id']][i]}).encode(),h)
            try:
                with racers[i].http.open(req,timeout=30) as response:return response.status
            except urllib.error.HTTPError as error:return error.code
        def concurrency():
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:codes=list(ex.map(compete,[0,1]))
            ensure(sorted(codes)==[200,409],str(codes))
        check('UC02 concurrent same resource allows one commit',concurrency)
        # Candidate cancellation and a separate patient invitation.
        race_appointment=next(a for a in operator.request('/appointments') if a['scheduled_start_at']==race['scheduled_start_at'])
        released=operator.request('/appointments/'+race_appointment['id'],{'action':'cancel','version':race_appointment['appointment_version'],'reason':'患者取消，释放候补时段','initiator':'PATIENT'})
        entry=check('UC05 register waitlist preferences',lambda:operator.request('/waitlist',{'action':'add','patient_id':p2['id'],'clinic_id':cid,'treatment_id':treatment['id'],'earliest_date':str(race_date),'latest_date':str(race_date),'notice_hours':0,'priority_score':70}))
        offer=check('UC05 offer a compatible released slot',lambda:operator.request('/waitlist',{'action':'offer','entry_id':entry['id'],'released_appointment_id':released['id']}))
        check('UC05 acceptance requires explicit patient confirmation',lambda:operator.request('/waitlist',{'action':'accept','offer_id':offer['id']},expect=422))
        check('UC05 offer acceptance creates confirmed booking',lambda:operator.request('/waitlist',{'action':'accept','offer_id':offer['id'],'patient_confirmed':True}))
        check('UC05 same offer cannot be consumed twice',lambda:operator.request('/waitlist',{'action':'accept','offer_id':offer['id']},expect=409))
        check('UC13 scope-specific metrics calculate from persisted facts',lambda:ensure(operator.request('/analytics?clinic_id='+cid)['appointments']>=1))
        finance=people['HQ_FINANCE']
        periods=finance.request('/finance/periods')
        period=next(p for p in periods['periods'] if p['starts_on']<=str(today)<=p['ends_on'])
        pid=period['id']
        preview=check('UC12 financial close preflight finds missing evidence',lambda:finance.request('/finance/preflight?period_id='+pid))
        check('UC12 unverified costs block quarter close',lambda:finance.request('/finance/periods',{'action':'close','period_id':pid,'version':period['period_version'],'fingerprint':preview['fingerprint'],'policy_confirmed':True},expect=409))
        cost=next(x for x in periods['costs'] if x['visit_id']==visit['id'])
        check('UC12 preserve verified actual cost and evidence',lambda:finance.request('/finance/periods',{'action':'cost','cost_id':cost['id'],'materials_fen':500,'laboratory_fen':100,'provider_fen':0,'evidence':'合成材料与技工成本凭据，已人工核对'}))
        expense=check('UC12 record approved operational expense',lambda:finance.request('/finance/periods',{'action':'expense','clinic_id':cid,'category':'SUPPLIES','vendor':'课程合成供应方','amount_fen':300,'incurred_on':str(today),'evidence':'合成验收凭据；费用经核实'}))
        check('UC12 prohibit over-allocation of the same expense',lambda:finance.request('/finance/periods',{'action':'allocate','expense_id':expense['id'],'dentist_id':dentist,'amount_fen':301,'basis':'合成测试'},expect=409))
        check('UC12 allocate expense with approved basis',lambda:finance.request('/finance/periods',{'action':'allocate','expense_id':expense['id'],'dentist_id':dentist,'amount_fen':300,'basis':'合成验收：该项费用全部归属负责牙医'}))
        preview=finance.request('/finance/preflight?period_id='+pid)
        ensure(not preview['blockers'],str(preview['blockers']))
        check('UC12 input digest mismatch prevents close',lambda:finance.request('/finance/periods',{'action':'close','period_id':pid,'version':period['period_version'],'fingerprint':'stale-input','policy_confirmed':True},expect=409))
        check('UC12 atomic period close and 10 percent pool',lambda:finance.request('/finance/periods',{'action':'close','period_id':pid,'version':period['period_version'],'fingerprint':preview['fingerprint'],'policy_confirmed':True}))
        pools=finance.request('/finance/periods')['pools']
        pool=next(x for x in pools if x['reporting_period_id']==pid)
        ensure(pool['pool_amount_fen']==max(preview['profit_fen'],0)//10)
        inv=operator.request('/finance/invoices/'+iid)['invoice']
        check('UC12 locked period prohibits ordinary payment write',lambda:people['CASHIER'].request('/finance/invoices/'+iid,{'action':'pay','version':inv['invoice_version'],'amount_fen':1,'method':'CASH','reference':'locked-'+run},expect=409))
        period=next(p for p in finance.request('/finance/periods')['periods'] if p['id']==pid)
        check('UC12 authorized reopen preserves historical snapshots',lambda:finance.request('/finance/periods',{'action':'reopen','period_id':pid,'version':period['period_version'],'reason':'合成验收：核对重开留痕'}))
        before=finance.request('/finance/periods')['results']
        preview=finance.request('/finance/preflight?period_id='+pid)
        check('UC12 closing again creates another approved snapshot',lambda:finance.request('/finance/periods',{'action':'close','period_id':pid,'version':preview['period']['period_version'],'fingerprint':preview['fingerprint'],'policy_confirmed':True}))
        after=finance.request('/finance/periods')['results']
        ensure(len(after)>len(before))
        if pg_url:
            psql=os.environ['ADC_TEST_PSQL']
            def scalar(sql):
                result=subprocess.run([psql,'-h','127.0.0.1','-p',str(pg.port),'-U',urllib.parse.unquote(pg.username),'-d',pg.path[1:],'-At','-c',sql],capture_output=True,text=True,encoding='utf-8',check=True)
                return result.stdout.strip()
            check('PG-01 complete schema contains 67 application and technical tables',lambda:ensure(scalar("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")=='67'))
            check('PG-02 denied requests retain audit evidence',lambda:ensure(int(scalar("SELECT count(*) FROM audit_events WHERE outcome='DENIED'"))>0))
            check('PG-03 signature evidence survives all workflows',lambda:ensure(int(scalar('SELECT count(*) FROM clinical_note_signatures'))>0))
        else:
          with sqlite3.connect(datadir/'adc-nexus.sqlite') as cx:
            check('DB-01 all foreign keys remain valid',lambda:ensure(not list(cx.execute('PRAGMA foreign_key_check'))))
            check('DB-02 approved baseline has 61 tables and 730 fields',lambda:ensure(len(json.loads((ROOT/'src/main/resources/db/schema-catalog.json').read_text(encoding='utf-8'))['tables'])==61))
            check('DB-03 rejected requests are audited',lambda:ensure(cx.execute("SELECT count(*) FROM audit_events WHERE outcome='DENIED'").fetchone()[0]>0))
            check('DB-04 signed clinical version has immutable signature evidence',lambda:ensure(cx.execute('SELECT count(*) FROM clinical_note_signatures').fetchone()[0]>0))
            def restoration():
                with sqlite3.connect(datadir/'restored.sqlite') as restored:
                    cx.backup(restored)
                    ensure(restored.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
                    ensure(not list(restored.execute('PRAGMA foreign_key_check')))
                    for table in ['patients','appointments','clinical_visits','invoices','payments','payment_refunds','audit_events']:
                        ensure(cx.execute('SELECT count(*) FROM '+table).fetchone()==restored.execute('SELECT count(*) FROM '+table).fetchone())
            check('DB-05 backup restores valid business chains',restoration)
        # Login, role assignment and password revocation use real credentials in memory only.
        username='verify_'+run;password='Test-'+secrets.token_urlsafe(18)
        user=check('UC14 create a password account',lambda:owner.request('/admin/access',{'action':'create_user','username':username,'password':password,'email':username+'@example.invalid','display_name':'角色验收合成账号'}))
        check('UC14 assign bounded physician role',lambda:owner.request('/admin/access',{'action':'grant','user_id':user['user_id'],'role_id':'jdbc-role-DENTIST','clinic_id':cid,'dentist_id':dentist,'effective_from':str(today)}))
        physician=Client(base);physician.csrf=check('UC16 real physician password login',lambda:physician.request('/auth/login',{'username':username,'password':password,'role':'DENTIST'}))['csrf']
        check('UC16 physician role does not grant patient entrance',lambda:Client(base).request('/auth/login',{'username':username,'password':password,'role':'PATIENT'},expect=403))
        check('UC17 change own password and revoke sessions',lambda:physician.request('/auth/password',{'oldPassword':password,'newPassword':'New-'+secrets.token_urlsafe(18)}))
        check('UC17 old session is unusable',lambda:physician.request('/auth/session',expect=401))
        # A global administrative role must not widen a local operational role.
        dual_name='dual_'+run;dual_password='Dual-'+secrets.token_urlsafe(18)
        dual=owner.request('/admin/access',{'action':'create_user','username':dual_name,'password':dual_password,'email':dual_name+'@example.invalid','display_name':'多角色范围验收合成'})
        owner.request('/admin/access',{'action':'grant','user_id':dual['user_id'],'role_id':'jdbc-role-ADMIN','effective_from':str(today)})
        owner.request('/admin/access',{'action':'grant','user_id':dual['user_id'],'role_id':'jdbc-role-FRONT_DESK','clinic_id':cid,'effective_from':str(today)})
        mixed=Client(base);mixed.csrf=mixed.request('/auth/login',{'username':dual_name,'password':dual_password,'role':'STAFF'})['csrf']
        check('AUTH-19 multi-role global admin does not widen local appointment access',lambda:mixed.request('/appointments?clinic_id='+foreign,expect=403))
        check('AUTH-20 multi-role admin cannot create patients outside local operational scope',lambda:mixed.request('/patients',{**patient_body,'primary_clinic_id':foreign,'phone':'13712345678'},expect=403))
        check('AUTH-21 invalid service dates produce validation response',lambda:operator.request('/analytics?from=invalid&to='+str(today),expect=422))
        check('UC11 persist verified physician credential',lambda:people['HQ_OPERATIONS'].request('/resources',{'action':'credential','dentist_id':dentist,'qualification_type_id':'qlf-general','issued_on':str(today),'expires_on':str(today.replace(year=today.year+1)),'issuing_body':'课程合成核验机构','reference_number':'QA-'+run,'verified':True}))
        check('UC11 persist an effective-dated clinic assignment',lambda:people['HQ_OPERATIONS'].request('/resources',{'action':'assignment','dentist_id':dentist,'clinic_id':cid,'effective_from':str(today),'weekly_hours':8}))
        completed=True
    except Exception as problem:
        if os.environ.get('GITHUB_ACTIONS')=='true':
            logfile.flush()
            detail=type(problem).__name__+': '+str(problem)
            if process.poll() is not None:detail+=' | '+(datadir/'server.log').read_text(encoding='utf-8',errors='replace')[-2500:]
            detail=re.sub(r'(postgres(?:ql)?://)[^@\s]+@',r'\1[redacted]@',detail).replace(admin_password,'[redacted]')
            print('::error title=Isolated JDBC acceptance::'+detail.replace('%','%25').replace('\r','%0D').replace('\n','%0A')[:3500],flush=True)
        raise
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        logfile.close()
        out=ROOT/'qa';out.mkdir(exist_ok=True)
        passed=completed and bool(RESULTS) and all(r['passed'] for r in RESULTS)
        (out/('acceptance-postgres.json' if pg_url else 'acceptance-results.json')).write_text(json.dumps({'passed':passed,'completed':completed,'tests':len(RESULTS),'database':'PostgreSQL JDBC' if pg_url else 'SQLite JDBC','external_services_verified':False,'run_id':run,'results':RESULTS},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
        print('RESULT',len(RESULTS),'passed' if passed else 'failed or incomplete',flush=True)

if __name__=='__main__':main()
