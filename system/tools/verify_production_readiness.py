"""Run production startup and auth checks against a fresh, disposable loopback PostgreSQL database."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parents[1]
url = os.environ["ADC_PRODUCTION_TEST_URL"]
uri = urllib.parse.urlsplit(url)
assert uri.hostname in ("127.0.0.1","localhost") and uri.path.startswith("/adc_acceptance_prod")
with socket.socket() as sock:
    sock.bind(("127.0.0.1",0))
    port = sock.getsockname()[1]
origin = f"http://127.0.0.1:{port}"
public = "https://clinic.example.test"
folder = root/"data"/("production-probe-"+secrets.token_hex(5))
folder.mkdir()
password = secrets.token_urlsafe(25)
env = {**os.environ,"APP_ENV":"PRODUCTION","SEED_DATA":"false","DEMO_MODE":"false",
       "PUBLIC_ORIGIN":public,"ORGANIZATION_NAME":"ADC production QA","ADMIN_PASSWORD":password,
       "DATABASE_URL":url,"DATA_DIR":str(folder),"PORT":str(port),"BIND_ADDRESS":"127.0.0.1"}
java = [os.environ.get("ADC_JAVA","java"),"--enable-native-access=ALL-UNNAMED",
        "-Dfile.encoding=UTF-8","-Dsun.stderr.encoding=UTF-8","-jar","target/adc-nexus.jar"]
psql = os.environ.get("ADC_TEST_PSQL","psql")
checks = []
def passed(message):
    checks.append(message)
    print("PASS",message,flush=True)

def reject(variables, message):
    result = subprocess.run(java,cwd=root,env=variables,capture_output=True,encoding="utf-8",timeout=60)
    assert result.returncode != 0 and message in result.stderr, message
    passed(message)

def request(path, method="GET", values=None, headers=None, expected=200):
    request_headers = {"Content-Type":"application/json"} if values is not None else {}
    request_headers.update(headers or {})
    body = None if values is None else json.dumps(values).encode()
    req = urllib.request.Request(origin+"/api"+path,body,headers=request_headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            actual, data, metadata = response.status,json.load(response),response.headers
    except urllib.error.HTTPError as e:
        actual,data,metadata = e.status,json.load(e),e.headers
    assert actual == expected, f"{path}: {actual} != {expected}"
    return data,metadata

@contextmanager
def running(variables):
    with (folder/"startup.log").open("ab") as log:
        process = subprocess.Popen(java,cwd=root,env=variables,stdout=log,stderr=log)
        try:
            for _ in range(180):
                assert process.poll() is None, "Production server failed to start; see isolated startup log"
                try:
                    h,_=request("/health")
                    if h["ok"]: break
                except OSError: pass
                time.sleep(.2)
            else: raise AssertionError("Production readiness timed out")
            yield h
        finally:
            if process.poll() is None: process.terminate()
            process.wait(timeout=20)

def sql(statement):
    return subprocess.check_output([psql,url,"-X","-At","-v","ON_ERROR_STOP=1","-c",statement],
        encoding="utf-8").strip()
reject({**env,"DEMO_MODE":"true"},"生产环境不得开启演示账号或样例初始化")
reject({**env,"DATABASE_URL":""},"生产环境必须配置 PostgreSQL")
reject({**env,"ADMIN_PASSWORD":""},"首次初始化需提供")
with running(env) as health:
    assert health["database"]=="PostgreSQL" and not health["demo_mode"] and not health["synthetic"]
    config,_ = request("/auth/config")
    assert not config.get("demo_accounts") and not config.get("demo_password")
    request("/auth/demo","POST",{"role":"DENTIST"},expected=404)
    assert sql("SELECT (SELECT count(*) FROM patients)||','||(SELECT count(*) FROM app_users)||','||(SELECT count(*) FROM schema_migrations)") == "0,1,10"
    assert not (folder/"setup-credentials.txt").exists()
    passed("Fresh production migrates with one administrator and no sample patients or secrets in public config")
    request("/auth/login","POST",{"username":"owner","password":password},{"Origin":"https://outside.example.test"},403)
    login,metadata = request("/auth/login","POST",{"username":"owner","password":password},{"Origin":public})
    cookie = metadata["Set-Cookie"]
    assert all(flag in cookie for flag in ("HttpOnly","SameSite=Lax","; Secure"))
    auth = {"Cookie":cookie.split(";",1)[0],"Origin":public,"X-CSRF-Token":login["csrf"]}
    session,_ = request("/auth/session",headers=auth)
    assert "access.manage" in session["principal"]["permissions"] and "clinical.write" not in session["principal"]["permissions"]
    request("/patients",headers=auth,expected=403)
    request("/auth/logout","POST",{},{"Cookie":auth["Cookie"],"Origin":public},403)
    _,logout = request("/auth/logout","POST",{},auth)
    assert "Max-Age=0" in logout["Set-Cookie"] and "; Secure" in logout["Set-Cookie"]
    request("/auth/session",headers=auth,expected=401)
    passed("Production verifies origin, issues secure cookies, requires CSRF, enforces least privilege and revokes logout session")
with running({**env,"ADMIN_PASSWORD":""}):
    assert sql("SELECT count(*) FROM schema_migrations") == "10"
    request("/auth/login","POST",{"username":"owner","password":password})
    passed("Second production start preserves migrations and password without bootstrap secret")
reject({**env,"APP_ENV":"DEMO","DEMO_MODE":"true","SEED_DATA":"true"},"演示环境须使用专用样例数据库")
demo_url = os.environ.get("ADC_DEMO_TEST_URL")
if demo_url:
    demo_uri = urllib.parse.urlsplit(demo_url)
    assert demo_uri.hostname in ("127.0.0.1", "localhost") and demo_uri.path.startswith("/adc_acceptance_demo")
    with running({**env, "APP_ENV": "DEMO", "DEMO_MODE": "true", "SEED_DATA": "true", "DATABASE_URL": demo_url,
                  "SMTP_HOST": "127.0.0.1", "SMTP_USER": "fixture", "SMTP_PASSWORD": "fixture",
                  "SMTP_FROM": "fixture@example.test", "TWILIO_ACCOUNT_SID": "fixture",
                  "TWILIO_AUTH_TOKEN": "fixture", "TWILIO_FROM": "fixture"}):
        config, _ = request("/auth/config")
        assert config["demo_accounts"] and not config["email"] and not config["sms"]
        passed("An isolated demo can use sample accounts and ignores real verification provider configuration")
    reject({**env, "DATABASE_URL": demo_url}, "检测到样例数据库")
(root/"qa"/"production-readiness-postgres.json").write_text(
    json.dumps({"passed":True,"checks":checks},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
