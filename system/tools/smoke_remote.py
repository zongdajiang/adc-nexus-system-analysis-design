"""Read-only checks against an HTTPS deployment; no authentication or business writes."""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
base=sys.argv[1].rstrip('/')
uri=urllib.parse.urlparse(base)
assert uri.scheme=='https' and uri.hostname and not uri.username and not uri.query and not uri.fragment,'Use the public HTTPS origin, without credentials or query parameters'
results=[]
def get(path,expected=200):
    try:
        with urllib.request.urlopen(base+path,timeout=120) as response:status=response.status;body=response.read();headers=response.headers
    except urllib.error.HTTPError as error:status=error.code;body=error.read();headers=error.headers
    assert status==expected,(path,status)
    results.append({'path':path,'status':status,'passed':True})
    return body,headers
health=json.loads(get('/api/health')[0])
assert health['ok'] and health['database']=='PostgreSQL' and health['data_access']=='JAVA_JDBC'
assert health['version']=='1.0.0-rc1'
html,headers=get('/')
assert b'app.js' in html and headers.get('X-Frame-Options')=='DENY' and headers.get('Content-Security-Policy')
for path in ['/app.js','/app.css','/mark.svg','/api/auth/config']:get(path)
for path in ['/api/patients','/api/visits','/api/finance/invoices','/api/admin/access','/api/portal']:get(path,401)
out=pathlib.Path(__file__).resolve().parents[1]/'qa'/'remote-readonly-smoke.json'
out.write_text(json.dumps({'passed':True,'public_origin':base,'checks':results,'health':health,'business_write_acceptance':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('PASS',len(results),'read-only remote checks. Business writes and hosted restoration are not covered.')
