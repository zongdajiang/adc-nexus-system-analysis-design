"""Read-only comparison with an explicit local SQLite backup. Never prints credentials or rows."""
import argparse
import hashlib
import json
import pathlib
import sqlite3

root=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--backup',required=True)
args=parser.parse_args()
backup=pathlib.Path(args.backup).resolve()
current=(root/'data/adc-nexus.sqlite').resolve()
assert backup.is_file() and current.is_file() and backup!=current
def read_only(file): return sqlite3.connect(file.as_uri()+'?mode=ro',uri=True)
before,after=read_only(backup),read_only(current)
credentials='id,username,password_hash,password_salt,password_iterations'
old=dict((r[0],r[1:]) for r in before.execute('SELECT '+credentials+' FROM app_users'))
new=dict((r[0],r[1:]) for r in after.execute('SELECT '+credentials+' FROM app_users'))
assert all(new.get(uid)==row for uid,row in old.items()),'An existing account credential changed'
tables=[r[0] for r in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
results=[]
for table in tables:
    if table in ('auth_sessions','audit_events','request_receipts','schema_migrations'):continue
    assert table.replace('_','').isalnum()
    a=before.execute('SELECT count(*) FROM "'+table+'"').fetchone()[0]
    b=after.execute('SELECT count(*) FROM "'+table+'"').fetchone()[0]
    assert a==b,'Business row count changed: '+table
    results.append({'table':table,'rows_before':a,'rows_after':b,'passed':True})
assert not list(after.execute('PRAGMA foreign_key_check'))
assert after.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
evidence={'version':'1.4.0-rc1','passed':True,'read_only':True,'existing_credentials_unchanged':True,
          'foreign_keys_valid':True,'integrity':'ok','tables':results,
          'jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest()}
(root/'qa/local-preservation-v1-4.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
before.close();after.close()
print('PASS existing account credentials unchanged;',len(results),'business table counts preserved; integrity/FKs valid. No credential or row content was printed.')
