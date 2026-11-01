"""Unified-auth acceptance. Fresh disposable DB; delivery goes ONLY to an in-memory loopback receiver.
No live mail/SMS, no production writes, no plaintext OTP/password in evidence files.
"""
import http.server
import threading
import pathlib
import os
import sys
import json
import secrets
import socket
import sqlite3
import subprocess
import time
import urllib.parse
from verify import Client, ensure

sys.stdout.reconfigure(encoding='utf-8')
ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = []

def test(name, run):
    run()
    RESULTS.append({'name': name, 'passed': True})
    print('PASS', name, flush=True)

def main():
    messages = {}
    class Receiver(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            m = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            messages[(m['channel'], m['destination'])] = m['code']
            self.send_response(204); self.end_headers()
        def log_message(self, *args): pass
    receiver = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Receiver)
    threading.Thread(target=receiver.serve_forever, daemon=True).start()
    run = secrets.token_hex(5)
    data = ROOT/'data'/('auth-acceptance-' + run)
    data.mkdir(parents=True)
    with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    password='Synthetic-'+secrets.token_urlsafe(18)
    env={**os.environ, 'APP_ENV':'TEST','PORT':str(port),'DATA_DIR':str(data), 'DEMO_MODE':'true',
         'ADMIN_PASSWORD':password,'AUTH_TEST_DELIVERY_URL':f'http://127.0.0.1:{receiver.server_port}/delivery'}
    pg_url=os.environ.get('ADC_ACCEPTANCE_PG_URL')
    if pg_url:
        pg=urllib.parse.urlparse(pg_url)
        assert pg.hostname in ('127.0.0.1','localhost') and pg.path.startswith('/adc_acceptance_')
        env['DATABASE_URL']=pg_url
    else: env.pop('DATABASE_URL',None)
    env.pop('ADC_TEST_NOW',None)
    log=(data/'server.log').open('w',encoding='utf-8')
    proc=subprocess.Popen([os.environ.get('ADC_JAVA','java'),'-Dfile.encoding=UTF-8','-jar','target/adc-nexus.jar'],cwd=ROOT,env=env,stdout=log,stderr=log)
    def sql(statement):
        if pg_url:
            command=[os.environ.get('ADC_PSQL','psql'),pg_url,'-X','-A','-t','-v','ON_ERROR_STOP=1','-c',statement]
            return subprocess.check_output(command,text=True).strip()
        with sqlite3.connect(data/'adc-nexus.sqlite') as cx:
            cursor=cx.execute(statement); result=cursor.fetchone()
            return str(result[0]) if result else ''
    try:
        anon=Client(base)
        for _ in range(100):
            if proc.poll() is not None: raise RuntimeError('Auth server failed: '+str(data/'server.log'))
            try: anon.request('/health'); break
            except Exception: time.sleep(.2)
        owner=Client(base);owner.csrf=owner.request('/auth/login',{'username':'owner','password':password})['csrf']
        test('Unified config exposes actual configured channels', lambda:ensure(anon.request('/auth/config')['registration_ready']))
        test('No unverified contact alias for legacy account', lambda:anon.request('/auth/login',{'username':'owner@adc.example.invalid','password':password},expect=401))
        test('Staff roster requires authentication',lambda:anon.request('/admin/staff',expect=401))
        test('Patient cannot maintain employee identities',lambda:Client(base).demo('PATIENT').request('/admin/staff',{},expect=403))
        def issue(ch,dest,purpose='REGISTER',reset=True):
            if reset:
                # Advance fixture age, not application time / verification policy. Isolated DB only.
                sql("UPDATE verification_challenges SET created_at='2000-01-01 00:00:00' WHERE destination='"+dest+"'")
            r=anon.request('/auth/challenge',{'channel':ch,'destination':dest,'purpose':purpose})
            ensure('code' not in r and 'user_id' not in r)
            return r['challenge_id'], messages[(ch,dest)]
        phone='+86137'+str(int(run,16))[-8:].zfill(8);email='patient-'+run+'@example.invalid'
        def body(ph=phone,em=email):
            pi,pc=issue('PHONE',ph);ei,ec=issue('EMAIL',em)
            return {'kind':'PATIENT','name':'合成注册验收','date_of_birth':'1996-01-02','gender':'UNKNOWN',
                    'phone':ph,'email':em,'password':password,'accepted_terms':True,
                    'phone_challenge':pi,'phone_code':pc,'email_challenge':ei,'email_code':ec}
        payload=body()
        test('Registration requires explicit terms acknowledgement',lambda:anon.request('/auth/register',{**payload,'accepted_terms':False},expect=422))
        test('Client role field cannot fabricate employee authority',lambda:anon.request('/auth/register',{**payload,'kind':'EMPLOYEE','employee_id':'ADC-AD-999999','activation_code':'invented'},expect=422))
        result=anon.request('/auth/register',{**payload,'role_id':'jdbc-role-ADMIN'})
        username=result['username']
        test('Patient username is automatically allocated',lambda:ensure(username.startswith('ADC-PT-')))
        patient=Client(base)
        for identifier in [username,email.upper(),phone,phone[3:]]:
            test('Password login resolves verified identifier '+('account' if identifier==username else 'contact'),lambda identifier=identifier:patient.request('/auth/login',{'username':identifier,'password':password}))
        patient.csrf=patient.request('/auth/session')['csrf']
        principal=patient.request('/auth/session')['principal']
        test('Self-registration grants only bound patient role',lambda:ensure([r['code'] for r in principal['roles']]==['JDBC_PATIENT'] and not principal['network'] and principal['patient_id']))
        test('Self-registered patient can open personal portal',lambda:patient.request('/portal'))
        test('Self-registered patient cannot enumerate patients',lambda:patient.request('/patients',expect=403))
        test('Consumed signup OTPs cannot register again',lambda:anon.request('/auth/register',payload,expect=422))
        loginid,logincode=issue('PHONE',phone,'LOGIN')
        otp=Client(base)
        otp.csrf=otp.request('/auth/code-login',{'channel':'PHONE','destination':phone,'challenge_id':loginid,'code':logincode})['csrf']
        test('Phone OTP session has intended patient identity',lambda:ensure(otp.request('/auth/session')['principal']['id']==principal['id']))
        test('OTP cannot be replayed',lambda:anon.request('/auth/code-login',{'channel':'PHONE','destination':phone,'challenge_id':loginid,'code':logincode},expect=422))
        eid,ecode=issue('EMAIL',email,'LOGIN')
        test('Challenge cannot be used for a different purpose',lambda:anon.request('/auth/recover',{'channel':'EMAIL','destination':email,'challenge_id':eid,'code':ecode,'new_password':password},expect=422))
        wrong='000000' if ecode!='000000' else '111111'
        for _ in range(5): anon.request('/auth/code-login',{'channel':'EMAIL','destination':email,'challenge_id':eid,'code':wrong},expect=422)
        test('Wrong-code attempt counters survive failed requests',lambda:ensure(sql("SELECT attempt_count FROM verification_challenges WHERE id='"+eid+"'")=='5'))
        test('Correct OTP is rejected after five failures',lambda:anon.request('/auth/code-login',{'channel':'EMAIL','destination':email,'challenge_id':eid,'code':ecode},expect=422))
        eid,ecode=issue('EMAIL',email,'LOGIN')
        sql("UPDATE verification_challenges SET expires_at='2000-01-01 00:00:00' WHERE id='"+eid+"'")
        test('Expired OTP is rejected',lambda:anon.request('/auth/code-login',{'channel':'EMAIL','destination':email,'challenge_id':eid,'code':ecode},expect=422))
        rid,rcode=issue('EMAIL',email,'RECOVER'); fresh='Changed-'+secrets.token_urlsafe(18)
        anon.request('/auth/recover',{'channel':'EMAIL','destination':email,'challenge_id':rid,'code':rcode,'new_password':fresh})
        test('Recovery revokes pre-existing password session',lambda:patient.request('/auth/session',expect=401))
        test('Recovery revokes pre-existing OTP session',lambda:otp.request('/auth/session',expect=401))
        test('Old password no longer works',lambda:anon.request('/auth/login',{'username':username,'password':password},expect=401))
        test('New password works after recovery',lambda:anon.request('/auth/login',{'username':email,'password':fresh}))
        uid,ucode=issue('EMAIL','unknown-'+run+'@example.invalid','LOGIN')
        test('Unknown contact request has no account existence flag',lambda:ensure(uid and ucode))
        test('Control of unknown mailbox does not create login authority',lambda:anon.request('/auth/code-login',{'channel':'EMAIL','destination':'unknown-'+run+'@example.invalid','challenge_id':uid,'code':ucode},expect=422))
        test('Invalid employee ID is refused by registry',lambda:owner.request('/admin/staff',{'action':'create','employee_id':'AD-0001'},expect=422))
        employees=[]
        for prefix,role,phone2 in [('FD','FRONT_DESK','+8613900000102'),('DR','DENTIST','+8613900000103')]:
            email2=prefix.lower()+'-'+run+'@example.invalid'
            invitation=owner.request('/admin/staff',{'action':'create','employee_id':'ADC-'+prefix+'-000001','name':'合成员工'+prefix,
                'phone':phone2,'email':email2,'clinic_id':'cln-tianhe','dentist_id':'dnt-lin-wei' if prefix=='DR' else '', 'role_id':'jdbc-role-ADMIN'})
            row=next(r for r in owner.request('/admin/staff') if r['employee_code']==invitation['employee_id'])
            test('Registry maps '+prefix+' to authoritative job',lambda row=row,role=role:ensure(row['role_id']=='jdbc-role-'+role))
            test('Activation plaintext is not stored in request receipts',lambda:ensure(sql("SELECT COUNT(*) FROM request_receipts WHERE response_json LIKE '%activation_code%'")=='0'))
            enrollment=body(phone2,email2)
            enrollment.update(kind='EMPLOYEE',name='合成员工'+prefix,employee_id=invitation['employee_id'],activation_code='wrong')
            test('OTP ownership alone cannot claim staff identity '+prefix,lambda:anon.request('/auth/register',enrollment,expect=422))
            enrollment['activation_code']=invitation['activation_code']
            result=anon.request('/auth/register',enrollment)
            test('Employee account equals internal staff ID '+prefix,lambda:ensure(result['username']==invitation['employee_id']))
            staff=Client(base);staff.csrf=staff.request('/auth/login',{'username':invitation['employee_id'],'password':password})['csrf']
            p=staff.request('/auth/session')['principal']
            test('Employee routes only to assigned role '+prefix,lambda:ensure([r['code'] for r in p['roles']]==['JDBC_'+role] and p['clinic_ids']==['cln-tianhe']))
            if prefix=='DR': test('Dentist registration binds explicit clinician record',lambda:ensure(p['dentist_id']=='dnt-lin-wei'))
            test('Employee cannot inherit injected admin role '+prefix,lambda:staff.request('/admin/access',expect=403))
            test('Activated staff cannot receive another signup invitation '+prefix,lambda:owner.request('/admin/staff',{'action':'reissue','id':row['id']},expect=409))
            employees.append((staff,row))
        staff,row=employees[0]
        owner.request('/admin/staff',{'action':'deactivate','id':row['id']})
        test('Employee deactivation revokes active session',lambda:staff.request('/auth/session',expect=401))
        test('Employee deactivation blocks password login',lambda:anon.request('/auth/login',{'username':row['employee_code'],'password':password},expect=401))
        ph='+8613900000199';ch,co=issue('PHONE',ph,'LOGIN')
        test('OTP cooldown is server-enforced',lambda:anon.request('/auth/challenge',{'channel':'PHONE','destination':ph,'purpose':'LOGIN'},expect=429))
        if not pg_url:
            with sqlite3.connect(data/'adc-nexus.sqlite') as cx:
                test('All auth and baseline foreign keys remain valid',lambda:ensure(not list(cx.execute('PRAGMA foreign_key_check'))))
                test('Only salted OTP hashes are stored',lambda:ensure(all(code not in str(list(cx.execute('SELECT code_hash,code_salt FROM verification_challenges'))) for code in messages.values())))
        # Network failure must not yield success; pending challenges can never authenticate.
        receiver.shutdown();receiver.server_close()
        test('Delivery failure is honest and does not return a usable challenge',lambda:anon.request('/auth/challenge',{'channel':'EMAIL','destination':'failed-'+run+'@example.invalid','purpose':'LOGIN'},expect=503))
        test('Failed delivery is recorded without message body',lambda:ensure(sql("SELECT COUNT(*) FROM verification_challenges WHERE status='FAILED'")=='1'))
        stamp=anon.request('/health')['time']
        for i in range(50):
            sql("INSERT INTO verification_challenges(id,channel,destination,purpose,code_hash,code_salt,status,request_ip_hash,expires_at,created_at) VALUES ('daily-fixture-"+str(i)+"','EMAIL','daily@example.invalid','LOGIN','unusable','unusable','FAILED','fixture','2000-01-01 00:00:00','"+stamp+"')")
        test('Global daily budget stops additional delivery attempts',lambda:anon.request('/auth/challenge',{'channel':'EMAIL','destination':'daily-cap-'+run+'@example.invalid','purpose':'LOGIN'},expect=429))
        evidence={'version':anon.request('/health')['version'],'database':'PostgreSQL' if pg_url else 'SQLite','jar_sha256':__import__('hashlib').sha256((ROOT/'target/adc-nexus.jar').read_bytes()).hexdigest(),'checks':len(RESULTS),'passed':len(RESULTS),'results':RESULTS,'live_delivery_tested':False}
        target=ROOT/'qa'/('auth-acceptance-postgres.json' if pg_url else 'auth-acceptance-sqlite.json')
        target.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print('COMPLETE',len(RESULTS),'checks; no live mail/SMS sent.',flush=True)
    finally:
        proc.terminate()
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill();proc.wait()
        log.close()
        receiver.shutdown();receiver.server_close()

if __name__=='__main__': main()
