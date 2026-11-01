"""Generate implementation metadata and source change inventory without exporting business rows."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--backup',required=True)
backup=(root/parser.parse_args().backup).resolve()
assert backup.parent==root/'data' and backup.name.startswith('before-upgrade-')
output=root/'upgrade-workbench/2026-10-30'

def files(base):
    result={}
    for folder in ['src','docs','tools']:
        for p in (base/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                result[p.relative_to(base).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ['pom.xml','README.md']:
        if (base/name).is_file():result[name]=hashlib.sha256((base/name).read_bytes()).hexdigest()
    return result

original,current=files(backup),files(root)
changes=[]
for name in sorted(set(original)|set(current)):
    if original.get(name)==current.get(name):continue
    changes.append({'path':name,'change':'added' if name not in original else 'removed' if name not in current else 'modified',
                    'before_sha256':original.get(name),'after_sha256':current.get(name)})
(output/'SOURCE_CHANGES.json').write_text(json.dumps({'baseline_backup':backup.name,'changes':changes},ensure_ascii=False,indent=2),encoding='utf-8')
connection=sqlite3.connect((root/'data/adc-nexus.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
tables=[]
for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
    assert name.replace('_','').isalnum()
    tables.append({'name':name,'columns':[dict(zip(['position','name','type','not_null','default','primary_key_order'],r)) for r in connection.execute('PRAGMA table_info("'+name+'")')],
        'foreign_keys':[dict(zip(['id','sequence','target_table','from','to','on_update','on_delete','match'],r)) for r in connection.execute('PRAGMA foreign_key_list("'+name+'")')]})
model={'date':'2026-10-30','version':'1.5.0-rc1','table_count':len(tables),'column_count':sum(len(t['columns']) for t in tables),
       'foreign_key_columns':sum(len(t['foreign_keys']) for t in tables),'tables':tables,'business_rows_exported':False}
(output/'IMPLEMENTED_SCHEMA.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
connection.close()
print('Generated source inventory and schema metadata only:',len(changes),'changed files;',len(tables),'tables;',model['column_count'],'columns;',model['foreign_key_columns'],'FK columns.')
