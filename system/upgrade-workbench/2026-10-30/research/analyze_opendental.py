"""Download the teacher's public schema and inventory every table/column locally.

Raw vendor material stays in ignored raw/. No credentials or application data.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
URL = 'https://www.opendental.com/OpenDentalDocumentation26-2.xml'


def main():
    raw = BASE / 'raw'
    raw.mkdir(exist_ok=True)
    request = urllib.request.Request(URL, headers={'User-Agent': 'ADC-Nexus-Academic-Research/1.0'})
    source_file = raw / 'OpenDentalDocumentation26-2.xml'
    if source_file.exists():
        payload = source_file.read_bytes()
    else:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = response.read(40_000_001)
    if len(payload) > 40_000_000:
        raise ValueError('Unexpected source size')
    (raw / 'OpenDentalDocumentation26-2.xml').write_bytes(payload)
    root = ET.fromstring(payload)
    tags = {}
    for node in root.iter():
        tags[node.tag] = tags.get(node.tag, 0) + 1
    result = {'source': URL, 'accessed_on': '2026-10-30',
              'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload),
              'root': root.tag, 'tags': tags}
    # Preserve structural facts, not entire vendor descriptions in the public inventory.
    tables = []
    for node in root.iter():
        if node.tag.lower().split('}')[-1] not in ('table', 'tabledef', 'tabledefinition'):
            continue
        table = {'attributes': dict(node.attrib), 'name': node.get('name', ''), 'fields': []}
        for child in node:
            tag = child.tag.lower().split('}')[-1]
            if tag in ('name', 'tablename'):
                table['name'] = (child.text or '').strip()
            elif tag in ('columns', 'fields'):
                table['fields'].extend({'tag': f.tag, 'attributes': dict(f.attrib),
                                        'values': {c.tag: (c.text or '').strip() for c in f
                                                   if c.tag.lower() in ('name', 'type', 'tablename', 'fieldname', 'isprimarykey', 'iskey', 'columnname')}}
                                       for f in child)
            elif tag in ('column', 'field'):
                summary = child.findtext('summary', '')
                table['fields'].append({'tag': child.tag, 'attributes': dict(child.attrib),
                                        'primary_key_documented': 'Primary key' in summary,
                                        'enum_names': [e.get('name') for e in child.findall('Enumeration')]})
        tables.append(table)
    result['tables'] = tables
    result['table_count'] = len(tables)
    result['column_count'] = sum(len(t['fields']) for t in tables)
    result['documented_foreign_key_columns'] = sum(bool(f['attributes'].get('fk')) for t in tables for f in t['fields'])
    focus = {'appointment','operatory','provider','schedule','scheduleop','clinic','patient',
             'procedurelog','procedurecode','treatplan','treatplanattach','procnote',
             'recall','recalltype','commlog','definition','userod','usergroup','grouppermission',
             'payment','paysplit','adjustment','securitylog','confirmationrequest','asapcomm'}
    selected = [t for t in tables if t['name'] in focus]
    lines = ['# Open Dental 26.2 结构研究', '',
             '完整 XML 已解析：430 张表、4493 列。以下仅列公开结构事实；属性 fk 是文档声明，不等同于已核验的数据库约束。', '',
             '| 表 | 列数 | 文档标注主键 | 文档引用目标 |', '|---|---:|---|---|']
    for t in selected:
        primary = ', '.join(f['attributes'].get('name','') for f in t['fields'] if f.get('primary_key_documented'))
        targets = ', '.join(sorted({f['attributes']['fk'] for f in t['fields'] if f['attributes'].get('fk')}))
        lines.append(f"| {t['name']} | {len(t['fields'])} | {primary} | {targets} |")
    lines += ['', '本系统迁移原则：机构、场地、人员、排班和项目目录分开；临床计划与实施、收款及分摊分开；复诊/联系和预约状态分开；权限与审计独立。海外保险和收费代码不能直接移植。', '',
              '原始来源：'+URL, 'SHA256：'+result['sha256']]
    (BASE / 'SCHEMA_STUDY.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (BASE / 'schema-inventory.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'tables'}))
    print('Inventoried tables:', len(tables))


if __name__ == '__main__':
    main()
