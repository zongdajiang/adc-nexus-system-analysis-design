"""Align all referenced use-case slashes to exact lower-right ellipse chords.

The SVG, PNG, draw.io and scene source are regenerated together. Text, actor
heads, actor associations and all use-case semantics stay in the original scene.
"""

import importlib.util
import json
import math

from figure_registry import ROOT, figures

spec=importlib.util.spec_from_file_location("adc_slash_renderer",ROOT/"skills/report-uml-reconstruction/scripts/render_diagram.py")
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
assets=ROOT/"assets/uml"


for entry in figures():
    if entry["macro"]!="figuc" and entry["base"]!="01_业务用例图":continue
    base=entry["base"]
    data=json.loads((assets/(base+".scene.json")).read_text(encoding="utf-8"))
    count=0
    for i,ellipse in enumerate(data["ops"][:-1]):
        if ellipse["type"]!="ellipse" or ellipse["rx"]<50:continue
        stroke=data["ops"][i+1]
        if stroke["type"]!="line" or stroke.get("color")!="#555555":continue
        x,y,rx,ry=[ellipse[k] for k in ("cx","cy","rx","ry")]
        stroke["points"]=[[x+rx*math.cos(math.radians(a)),y+ry*math.sin(math.radians(a))] for a in (35,0)]
        count+=1
    assert count>0,base
    scene=r.Scene(data["width"],data["height"],dict(r.PROFILES["mayuyang"]))
    scene.ops=data["ops"]
    audit=scene.audit();assert not audit["issues"],audit["issues"]
    old=json.loads((assets/(base+".audit.json")).read_text(encoding="utf-8"))
    audit.update(model=base,source_trace=False,counts=old.get("counts",{}),ellipse_chords=count)
    (assets/(base+".scene.json")).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8", newline='\n')
    (assets/(base+".audit.json")).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8", newline='\n')
    r.save_svg(scene,assets/(base+".svg"));r.save_png(scene,assets/(base+".png"),4);r.save_drawio(scene,assets/(base+".drawio"))
    print(f"Figure {entry['number']}: {count} ellipse chords aligned")
