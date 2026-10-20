#!/usr/bin/env python3
"""Re-render source reconstructions and different-domain models, checking observable outputs."""
from pathlib import Path
import argparse, json, hashlib, sys, copy
import xml.etree.ElementTree as ET
from PIL import Image
from render_diagram import render_file, validate_model, get_font

BASE=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,help='Use a disposable directory, outside the skill folder.');args=ap.parse_args();dest=Path(args.out).resolve()
    if dest==BASE or BASE in dest.parents:raise ValueError('验证输出请放到 skill 文件夹之外。')
    expected=json.loads((BASE/'references/expected-structure.json').read_text(encoding='utf8'))
    models=sorted((BASE/'assets/models').glob('*.json'));transfer=sorted((BASE/'assets/transfer-tests').glob('*.json'));results=[]
    for path in models+transfer:
        model=json.loads(path.read_text(encoding='utf8'))
        result=render_file(path,dest,scale=1,strict=True)
        if path.stem in expected:
            for key,value in expected[path.stem].items():
                assert result['counts'].get(key)==value,(path.name,key,value,result['counts'])
        # XML must contain editable elements, not a single screenshot.
        svg=ET.parse(dest/(path.stem+'.svg'));assert len(svg.getroot())>2
        mx=ET.parse(dest/(path.stem+'.drawio'));cells=mx.findall('.//mxCell');assert len(cells)>3
        assert not any('data:image' in c.get('style','') for c in cells)
        if model['type'] in ('usecase','sequence','class'):
            puml=(dest/(path.stem+'.puml')).read_text(encoding='utf8')
            assert puml.startswith('@startuml\n') and puml.rstrip().endswith('@enduml'),path.name
        with Image.open(dest/(path.stem+'.png')) as im:
            assert im.size==tuple(round(v) for v in result['canvas']);assert im.getbbox()
        results.append({'model':path.stem,'counts':result['counts'],'layout_issues':len(result['issues']),'xml_and_png':'passed'})
    source=json.loads((BASE/'references/source-catalog.json').read_text(encoding='utf8'))
    for e in source:
        data=(BASE/'references'/e['source_file']).read_bytes();assert hashlib.sha256(data).hexdigest()==e['sha256'],e['id']
    # Representative non-Latin glyphs must differ from the missing-glyph box.
    font=get_font(18);missing=bytes(font.getmask('\uffff'))
    for glyph in '用例序列实体控制边界图':assert bytes(font.getmask(glyph))!=missing,'中文字体缺字 '+glyph
    # Invalid references and cyclic inheritance should be rejected, not silently drawn.
    invalid=[{'type':'class','classes':[{'id':'a','name':'A','parent':'b'},{'id':'b','name':'B','parent':'a'}]},
             {'type':'sequence','participants':[{'id':'a','label':'A'}],'messages':[{'from':'a','to':'missing','label':'invalid'}]}]
    rejected=0
    for m in invalid:
        try:validate_model(m)
        except ValueError:rejected+=1
    assert rejected==len(invalid)
    # New classes must not acquire a fabricated constructor, and inheritance must infer ranks.
    import render_diagram as rd
    m={'type':'class','profile':'b-enterprise','classes':[{'id':'p','name':'Base','center_over':True,'attributes':[]},{'id':'c','name':'Specific','parent':'p','attributes':[]}]}
    sc=rd.render_classes(m,dict(rd.PROFILES['b-enterprise']));assert not sc.audit()['issues'];assert sc.counts['constructors_or_methods']==0
    # These are negative controls: a validator that never reports a collision
    # would pass every real image while providing no protection at all.
    collision=rd.Scene(200,100,dict(rd.PROFILES['b-enterprise']))
    collision.text(55,40,'消息标注',size=14,role='message-label')
    collision.protected_segments.append({'name':'alt:top','line':(10,46,180,46)})
    assert any(i['type']=='fragment-border-crosses-label' for i in collision.audit()['issues'])
    crossing=rd.Scene(200,100,dict(rd.PROFILES['b-enterprise']))
    crossing.box('a',0,35,25,25);crossing.box('obstacle',80,35,30,25);crossing.box('b',175,35,25,25)
    crossing.routes.append({'from':'a','to':'b','points':[(25,48),(175,48)]})
    assert any(i['type']=='class-relation-crosses-class' for i in crossing.audit()['issues'])
    library=json.loads((BASE/'assets/transfer-tests/library-sequence.json').read_text(encoding='utf8'))
    library_scene=rd.render_sequence(library,dict(rd.PROFILES['b-enterprise']))
    assert any(o['type']=='text' and o['text']=='borrowing' for o in library_scene.ops),'新图实体标签不得拆断英文单词'
    report={'source_models':len(models),'source_fragments':len(source),'transfer_models':len(transfer),'rejected_invalid_models':rejected,'audit_negative_controls':3,'layout_issues':sum(r['layout_issues'] for r in results),'results':results,'scope':'结构计数、源图哈希、渲染布局、输出XML及PNG、代表中文字形、无效输入和三项反例审计；不等价于业务语义或像素级复原率。'}
    dest.mkdir(parents=True,exist_ok=True);(dest/'bundle-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8', newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['results']},ensure_ascii=False))
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
    main()
