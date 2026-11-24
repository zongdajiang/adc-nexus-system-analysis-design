"""Run independent isolated suites; PostgreSQL mode uses only local disposable databases."""
from pathlib import Path
import sys, os, secrets, subprocess, concurrent.futures, json, hashlib
root=Path(__file__).resolve().parents[1];postgres='--postgres' in sys.argv
suites=[('baseline','verify.py','ADC_ACCEPTANCE_PG_URL'),('operating','verify_operating_workflow.py','ADC_OPERATING_PG_URL'),
        ('daily','verify_daily_workflow.py','ADC_DAILY_PG_URL'),('passwords','verify_demo_passwords.py','ADC_LOGIN_PG_URL'),
        ('responsibilities','verify_responsibilities.py','ADC_REVIEW_PG_URL'),('auth','verify_auth.py','ADC_ACCEPTANCE_PG_URL')]
only=sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
if only:suites=[s for s in suites if s[0]==only];assert suites
def run(entry):
    name,script,key=entry;env={**os.environ,'ADC_JAVA':'C:/Users/Jiangzongda/java/jdk-21.0.11+10/bin/java.exe','ADC_TEST_PSQL':'C:/Program Files/PostgreSQL/18/bin/psql.exe','ADC_ACCEPTANCE_JAR':'true','PYTHONUTF8':'1'}
    for k in ('DATABASE_URL','ADC_ACCEPTANCE_PG_URL','ADC_OPERATING_PG_URL','ADC_DAILY_PG_URL','ADC_LOGIN_PG_URL','ADC_REVIEW_PG_URL'):env.pop(k,None)
    if postgres:
        dbname='adc_acceptance_review180_'+name+'_'+secrets.token_hex(4)
        result=subprocess.run(['C:/Program Files/PostgreSQL/18/bin/createdb.exe','-h','127.0.0.1','-p','5432','-U','adc_acceptance',dbname],capture_output=True)
        assert result.returncode==0,result.stderr.decode(errors='replace')
        env[key]='postgresql://adc_acceptance@127.0.0.1:5432/'+dbname+'?sslmode=disable'
    path=root/'qa'/('review180-'+('postgres-' if postgres else 'sqlite-')+name+'.log')
    with path.open('w',encoding='utf8') as log:
        result=subprocess.run([sys.executable,str(root/'tools'/script)],cwd=root,env=env,stdout=log,stderr=log)
    print(('PASS' if result.returncode==0 else 'FAIL')+' '+('PostgreSQL' if postgres else 'SQLite')+' '+name,flush=True)
    if result.returncode:print('\n'.join(path.read_text(encoding='utf8',errors='replace').splitlines()[-14:]),flush=True)
    return {'suite':name,'passed':result.returncode==0,'log':path.name}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,suites))
proof=root/('qa/regressions-postgres.json' if postgres else 'qa/regressions-sqlite.json')
if only and proof.exists():
    previous=json.loads(proof.read_text(encoding='utf8'));names={r['suite'] for r in results};results=[r for r in previous['suites'] if r['suite'] not in names]+results
proof.write_text(json.dumps({'passed':all(r['passed'] for r in results),'jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest(),'suites':results},indent=2)+'\n',encoding='utf8')
assert all(r['passed'] for r in results)
