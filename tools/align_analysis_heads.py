"""Give the six internal analysis actors the same clear, aligned head height.

Actor, boundary, control and entity categories remain semantically distinct.
Only actor size and vertical placement change; messages and executions stay put.
"""

import json
import subprocess
import sys

from figure_registry import ROOT, figures

renderer=ROOT/"skills/report-uml-reconstruction/scripts/render_diagram.py"
for item in figures():
    if item["macro"]!="figanalysisplate":continue
    path=ROOT/"models/uml/sequence"/(item["base"]+".json")
    model=json.loads(path.read_text(encoding="utf-8"))
    for actor in model["participants"]:
        if actor.get("kind")=="actor":
            actor.update(actor_scale=1.0,actor_top=40,name_y=94)
    path.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8", newline='\n')
    subprocess.run([sys.executable,str(renderer),str(path),"--out",str(ROOT/"assets/uml"),"--scale","3","--strict"],check=True)
