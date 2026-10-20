"""Restore an isolated loopback PostgreSQL acceptance DB; never a hosted database."""
import json
import os
import pathlib
import secrets
import subprocess
import sys
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path(__file__).resolve().parents[1]
uri=urllib.parse.urlparse(os.environ['ADC_ACCEPTANCE_PG_URL'])
assert uri.hostname in ('localhost','127.0.0.1') and uri.path.startswith('/adc_acceptance_')
tools=pathlib.Path(os.environ['ADC_TEST_PSQL']).parent
env={**os.environ,'PGPASSWORD':urllib.parse.unquote(uri.password or '')}
args=['-h',uri.hostname,'-p',str(uri.port or 5432),'-U',urllib.parse.unquote(uri.username or '')]
source=uri.path[1:]
destination='adc_acceptance_restore_'+secrets.token_hex(6)
folder=root/'data'/destination
folder.mkdir(parents=True)
dump=folder/'acceptance.dump'
def run(tool,*extra):
    executable=str(tools/(tool+('.exe' if os.name=='nt' else '')))
    return subprocess.run([executable,*args,*extra],cwd=root,env=env,check=True,capture_output=True,text=True,encoding='utf-8').stdout.strip()
run('pg_dump','-d',source,'-Fc','-f',str(dump.relative_to(root)))
run('createdb',destination)
run('pg_restore','-d',destination,'--no-owner',str(dump.relative_to(root)))
results=[]
for table in ['patients','appointments','clinical_visits','clinical_note_signatures','invoices','payments','payment_refunds','financial_period_results','incentive_pools','audit_events']:
    query='SELECT count(*) FROM '+table
    a=run('psql','-d',source,'-At','-c',query)
    b=run('psql','-d',destination,'-At','-c',query)
    assert a==b,(table,a,b)
    results.append({'table':table,'rows':int(a),'passed':True})
constraints=run('psql','-d',destination,'-At','-c',"SELECT count(*) FROM pg_constraint WHERE contype='f' AND connamespace='public'::regnamespace AND convalidated")
assert int(constraints)>=119
result={'passed':True,'method':'pg_dump custom archive + pg_restore into a separate isolated database','validated_foreign_keys':int(constraints),'checks':results,'hosted_database_verified':False}
(root/'qa'/'postgres-backup-restore.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('PASS PostgreSQL backup/restore:',len(results),'business-chain counts;',constraints,'validated foreign keys. Only the isolated restore database was created.')
