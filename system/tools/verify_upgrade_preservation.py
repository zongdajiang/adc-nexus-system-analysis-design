"""Read-only checks across an explicit pre-upgrade SQLite backup and local database.

Checks original business row contents, not just counts. Runtime/session activity is excluded.
No credential, patient row or contact detail is printed or written into evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--backup',required=True)
backup=Path(parser.parse_args().backup).resolve()
current=root/'data/adc-nexus.sqlite'
assert backup.is_file() and backup!=current.resolve()
before=sqlite3.connect(backup.as_uri()+'?mode=ro',uri=True)
after=sqlite3.connect(current.resolve().as_uri()+'?mode=ro',uri=True)
results=[]
for (name,) in before.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
    assert name.replace('_','').isalnum()
    if name in ('auth_sessions','audit_events','request_receipts','schema_migrations'):continue
    fields=[r[1] for r in before.execute('PRAGMA table_info("'+name+'")')]
    if name=='app_users':
        fields=['id','username','password_hash','password_salt','password_iterations']
    query='SELECT '+','.join('"'+f+'"' for f in fields)+' FROM "'+name+'"'
    def digest(row):return hashlib.sha256(json.dumps(row,ensure_ascii=False,default=str).encode()).hexdigest()
    original={digest(row) for row in before.execute(query)}
    actual={digest(row) for row in after.execute(query)}
    assert original.issubset(actual),'Existing business rows or credentials changed: '+name
    results.append({'table':name,'original_rows':len(original),'current_rows':len(actual),'original_contents_preserved':True})
assert not list(after.execute('PRAGMA foreign_key_check'))
assert after.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
table_names=[r[0] for r in after.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
foreign_keys=sum(len(list(after.execute('PRAGMA foreign_key_list("'+n+'")'))) for n in table_names)
assert len(table_names)==71 and foreign_keys==146
evidence={'version':'1.5.0-rc1','passed':True,'read_only':True,'business_rows_checked':results,
          'existing_credentials_unchanged':True,'tables':71,'foreign_keys':146,'integrity':'ok',
          'jar_sha256':hashlib.sha256((root/'target/adc-nexus.jar').read_bytes()).hexdigest()}
(root/'qa/local-preservation-v1-5.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
before.close();after.close()
print('PASS original row contents and account credential hashes preserved; 71 tables / 146 foreign keys; no row contents exposed.')
