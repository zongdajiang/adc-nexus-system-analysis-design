"""Copy the approved logical baseline; derive PostgreSQL with identical columns/FKs."""
import argparse
import hashlib
import json
import pathlib
import re
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=pathlib.Path, required=True)
parser.add_argument('--seed', type=pathlib.Path, required=True)
args = parser.parse_args()
out = ROOT / 'src/main/resources/db'
out.mkdir(parents=True, exist_ok=True)
sql = args.source.read_text(encoding='utf-8')
(out / 'baseline-sqlite.sql').write_text(sql, encoding='utf-8', newline='\n')
cx = sqlite3.connect(':memory:')
cx.executescript(sql)
tables = [r[0] for r in cx.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
model = []
for table in tables:
    model.append(dict(name=table, columns=[dict(zip(('cid','name','type','notnull','default','pk'),r)) for r in cx.execute(f'PRAGMA table_info("{table}")')], foreignKeys=[dict(zip(('id','seq','table','from','to','on_update','on_delete','match'),r)) for r in cx.execute(f'PRAGMA foreign_key_list("{table}")')]))
(out / 'schema-catalog.json').write_text(json.dumps(dict(baselineSha256=hashlib.sha256(sql.encode()).hexdigest(), tables=model), ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
foreign = []
def table_pg(match):
    name, body = match.group(1), match.group(2)
    kept = []
    for line in body.strip().splitlines():
        if line.strip().startswith('FOREIGN KEY'):
            foreign.append(f'ALTER TABLE "{name}" ADD {line.strip().rstrip(",")};')
        else:
            kept.append(line)
    body = '\n'.join(kept).rstrip().rstrip(',')
    body = re.sub(r'INTEGER PRIMARY KEY AUTOINCREMENT', 'BIGSERIAL PRIMARY KEY', body)
    body = re.sub(r'INTEGER', 'BIGINT', body)
    body = body.replace('DEFAULT CURRENT_TIMESTAMP', 'DEFAULT (CURRENT_TIMESTAMP::text)')
    return f'CREATE TABLE "{name}" (\n{body}\n);'
pg = re.sub(r'PRAGMA[^;]+;\s*', '', sql)
pg = re.sub(r'CREATE TABLE "([^"]+)" \((.*?)\n\);', table_pg, pg, flags=re.S)
pg += '\n' + '\n'.join(foreign) + '\n'
(out / 'baseline-postgres.sql').write_text(pg, encoding='utf-8', newline='\n')
seed = args.seed.read_text(encoding='utf-8')
(out / 'seed.sql').write_text(seed, encoding='utf-8', newline='\n')
# Resolve the synthetic fixture using its original SQLite semantics once. Export
# literal values in FK order, not brittle replacements of printf/date/CTE syntax.
fixture = sqlite3.connect(':memory:')
fixture.executescript(sql.replace('DEFAULT CURRENT_TIMESTAMP', "DEFAULT '2026-09-23 12:00:00'"))
fixture.executescript(seed)
assert not fixture.execute('PRAGMA foreign_key_check').fetchall()
pending = {t['name']: {fk['table'] for fk in t['foreignKeys'] if fk['table'] != t['name']} for t in model}
ordered = []
while pending:
    ready = sorted(t for t, deps in pending.items() if not deps.intersection(pending))
    if not ready:
        raise RuntimeError('Synthetic fixture contains cyclic foreign keys: ' + ', '.join(pending))
    for table in ready:
        ordered.append(table)
        del pending[table]
def literal(value):
    if value is None: return 'NULL'
    if isinstance(value, (int, float)): return str(value)
    return "'" + str(value).replace("'", "''") + "'"
statements = ['-- Generated synthetic fixture; no SQLite-only functions or personal data.']
for table in ordered:
    columns = [r[1] for r in fixture.execute(f'PRAGMA table_info("{table}")')]
    if table == 'audit_events': columns.remove('id') # PostgreSQL owns its sequence.
    names = ','.join('"'+name+'"' for name in columns)
    values = fixture.execute(f'SELECT {names} FROM "{table}"').fetchall()
    for offset in range(0, len(values), 100):
        batch = ',\n'.join('('+','.join(map(literal, row))+')' for row in values[offset:offset+100])
        statements.append(f'INSERT INTO "{table}" ({names}) VALUES {batch} ON CONFLICT DO NOTHING;')
(out / 'seed-postgres.sql').write_text('\n'.join(statements)+'\n', encoding='utf-8', newline='\n')
print(json.dumps(dict(tables=len(tables),fields=sum(len(x['columns']) for x in model),foreignKeys=len(foreign)),ensure_ascii=False))
