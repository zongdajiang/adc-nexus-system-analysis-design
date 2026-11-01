"""Disposable loopback browser fixture. Creates only a fresh data/browser-fixture-* database.

Run interactively; press Enter to stop the owned Java child. No local/hosted business DB is reused.
"""
import os
import pathlib
import secrets
import socket
import subprocess
import time
from verify import Client

root=pathlib.Path(__file__).resolve().parents[1]
run=secrets.token_hex(6)
folder=root/'data'/('browser-fixture-'+run)
folder.mkdir()
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
env={**os.environ,'DEMO_MODE':'true','APP_ENV':'TEST','ADC_TEST_NOW':'2026-12-31T08:00:00',
     'ADMIN_PASSWORD':'Fixture-'+secrets.token_urlsafe(22),'DATA_DIR':str(folder),
     'BIND_ADDRESS':'127.0.0.1','PORT':str(port)}
env.pop('DATABASE_URL',None)
with (folder/'server.log').open('w',encoding='utf-8') as log:
    child=subprocess.Popen([os.environ.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED',
                            '-Dfile.encoding=UTF-8','-jar','target/adc-nexus.jar'],cwd=root,
                           env=env,stdout=log,stderr=log,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:
        base='http://127.0.0.1:'+str(port)
        client=Client(base)
        for _ in range(200):
            try:
                client.request('/health')
                break
            except Exception:
                if child.poll() is not None:raise RuntimeError('Fixture Java failed; inspect its private log')
                time.sleep(.15)
        operator=Client(base).demo('REVIEWER')
        front=Client(base).demo('FRONT_DESK')
        boot=operator.request('/bootstrap')
        resource=operator.request('/resources')
        prohibited={r['treatment_id'] for r in resource['requirements'] if r['requirement_level']=='REQUIRED'}
        treatment=next(t for t in boot['treatments'] if t['status']=='ACTIVE' and t['id'] not in prohibited)
        patient=front.request('/patients',{'name_zh':'Browser fixture patient','date_of_birth':'1996-04-08',
             'gender':'UNKNOWN','phone':'139'+str(int(run,16))[-8:].zfill(8),
             'primary_clinic_id':'cln-tianhe','history_text':'Synthetic browser fixture only'})
        front.request('/patients/'+patient['id'],{'action':'history','history_status':'DECLARED_NONE',
              'history_text':'No related history declared in this synthetic fixture','reason':'Fixture'})
        chair=next(c for c in boot['chairs'] if c['clinic_id']=='cln-tianhe' and c['status']=='AVAILABLE')
        appointment=front.request('/appointments',{'patient_id':patient['id'],'clinic_id':'cln-tianhe',
              'dentist_id':'dnt-lin-wei','chair_id':chair['id'],'treatment_id':treatment['id'],
              'duration_minutes':30,'scheduled_start_at':'2026-12-31 10:00:00'})
        front.request('/appointments/'+appointment['id'],{'action':'check_in',
              'version':appointment['appointment_version'],'identity_confirmed':True,'declaration':'Synthetic identity verified'})
        visit=next(v for v in operator.request('/visits') if v['appointment_id']==appointment['id'])
        def care(action,**data):
            current=operator.request('/visits/'+visit['id'])
            return operator.request('/visits/'+visit['id'],{'action':action,'version':current['visit']['visit_version'],**data})
        care('safety',history_confirmed=True,evidence='Synthetic safety review only')
        care('start')
        care('observation',tooth_code='16',observation_type='EXAMINATION',severity='LOW',finding='Synthetic finding')
        planned=care('plan',treatment_id=treatment['id'],tooth_code='16',units=1,rationale='Synthetic proposal with explained fee')
        item=planned['requested'][-1]['id']
        care('consent',item_id=item,decision='ACCEPTED',evidence='Synthetic item-specific decision')
        care('actual',treatment_id=treatment['id'],requested_treatment_item_id=item,tooth_code='16',units=1,notes='Synthetic implementation')
        care('note',content='Synthetic signed note: complaint, findings, plan, actual and advice.',sign=True)
        care('complete')
        print('READY '+base+'/#/login',flush=True)
        print('Use the existing course-demo button. New database only; Enter stops this Java child.',flush=True)
        input()
    finally:
        child.terminate()
        try:child.wait(timeout=15)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        print('Fixture stopped; isolated data retained under ignored data/.',flush=True)
