"""Rebuild panoramas with exactly the renderer used by the existing figures.

Business workers/entities use the existing course/MYY heads and name boxes.
The visit and quarterly interactions remain independent academic subfigures.
"""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import cairosvg
from pypdf import PdfReader, PdfWriter

from figure_registry import ROOT, by_base

RENDERER = ROOT / "skills/report-uml-reconstruction/scripts/render_diagram.py"
spec = importlib.util.spec_from_file_location("adc_uml_renderer", RENDERER)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
MODELS = ROOT / "models/uml/overview"
ASSETS = ROOT / "assets/uml"
MASTERS = ASSETS / "overview_original_pages"


def render_model(base: str, model: dict):
    MODELS.mkdir(parents=True, exist_ok=True)
    path = MODELS / f"{base}.json"
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline='\n')
    r.render_file(path, ASSETS, scale=3, strict=True)
    return r.RENDERERS[model["type"]](model, dict(r.PROFILES[model["profile"]]))


def add_scene(target, source, dx: float, dy: float, prefix: str):
    for original in source.ops:
        op = deepcopy(original)
        for x, y in (("x", "y"), ("cx", "cy")):
            if x in op:
                op[x] += dx
                op[y] += dy
        if "points" in op:
            op["points"] = [[x + dx, y + dy] for x, y in op["points"]]
        if op.get("container"):
            a,b,c,d = op["container"]
            op["container"] = [a+dx,b+dy,c+dx,d+dy]
        target.ops.append(op)
    for box in source.boxes:
        a,b,c,d = box["box"]
        target.boxes.append(dict(id=prefix+box["id"], box=[a+dx,b+dy,c+dx,d+dy], kind=box["kind"]))


def save_scene(base: str, scene):
    audit = scene.audit()
    assert not audit["issues"], audit["issues"]
    audit["model"] = base
    audit["source_trace"] = False
    r.save_svg(scene, ASSETS / f"{base}.svg")
    r.save_png(scene, ASSETS / f"{base}.png", 3)
    r.save_drawio(scene, ASSETS / f"{base}.drawio")
    (ASSETS / f"{base}.scene.json").write_text(json.dumps(dict(width=scene.w,height=scene.h,ops=scene.ops),ensure_ascii=False,indent=2),encoding="utf-8", newline='\n')
    (ASSETS / f"{base}.audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8", newline='\n')
    MASTERS.mkdir(parents=True, exist_ok=True)
    raw = cairosvg.svg2pdf(url=str(ASSETS / f"{base}.svg"))
    from io import BytesIO
    writer = PdfWriter()
    writer.add_page(PdfReader(BytesIO(raw)).pages[0])
    writer.pdf_header = "%PDF-1.5"
    with (MASTERS / f"{base}.pdf").open("wb") as handle:
        writer.write(handle)
    print(f"{base}: {scene.w:.0f} x {scene.h:.0f}; layout issues=0")


def sequence_model(participants, messages, activations, title):
    ids = [f"p{i}" for i in range(len(participants))]
    gap=1480/(len(participants)-1)
    prepared=[]
    for a,b,label,kind in messages:
        if a!=b:
            label=r.wrap(label,abs(a-b)*gap-36,20,"Microsoft YaHei")
        prepared.append(dict(**{"from":ids[a],"to":ids[b]},label=label,kind=kind))
    return dict(type="sequence",profile="mayuyang",title=title,frame=False,
                font_size=20,message_top=190,message_gap=58,width=1680,
                first_lane=100,lane_gap=1480/(len(participants)-1),
                nested_self_activation=False,
                participants=[dict(id=ids[i],label=label,kind=kind,x=100+i*gap) for i,(label,kind) in enumerate(participants)],
                messages=prepared,
                activations=[dict(participant=ids[p],start_message=a,end_message=b,end_offset=24 if a==b else 14) for p,a,b in activations],
                basis="报告现状/改进分解序列与用例规约；单次就诊和季度核对分为独立交互。现状台账与资源核验仍须门店访谈确认。")


def business(improved: bool):
    base = "05A_改进业务序列全景" if improved else "02A_现状业务序列全景"
    if improved:
        people=[("患者","actor"),("前台接待","business-worker"),("ADC Nexus","business-entity"),("排班表","business-entity"),("牙椅资源","business-entity"),("牙医","business-worker"),("收费员","business-worker")]
        messages=[
            (0,1,"提出就诊诉求","call"),(1,2,"查找患者与需求()","call"),
            (2,3,"查询服务日排班\n与例外()","call"),(3,2,"返回可行牙医时段","return"),
            (2,4,"核验牙椅可用性()","call"),(4,2,"返回牙椅状态","return"),
            (2,1,"给出候选方案","return"),(1,0,"说明诊所、牙医与时段","call"),
            (0,1,"确认方案","call"),(1,2,"提交预约并复核占用()","call"),
            (2,1,"返回预约编号","return"),(0,1,"到诊并申报变化","call"),
            (1,2,"登记到诊与声明()","call"),(2,5,"提供待复核资料","call"),
            (5,2,"记录风险、实际治疗并签署()","call"),(2,6,"提供可结算治疗清单","call"),
            (6,2,"建立结算单并登记收款()","call"),(6,0,"交付逐项结算凭据","call")]
        acts=[(1,0,10),(1,11,12),(2,1,6),(2,9,10),(2,12,13),(2,14,15),(2,16,16),(3,2,3),(4,4,5),(5,13,14),(6,15,17)]
        periodic=[("诊所经理","business-worker"),("ADC Nexus","business-entity"),("总部财务","business-worker"),("负责人","business-worker")]
        quarter=[(0,1,"提交成本与费用归属()","call"),(2,1,"发起季度核对()","call"),(1,2,"返回异常清单和结果版本","return"),(2,1,"确认口径并关闭期间()","call"),(1,3,"提供核定绩效快照","call"),(3,1,"查询牙医贡献依据()","call"),(1,3,"返回指标与口径标识","return")]
        qacts=[(1,0,0),(1,1,2),(1,3,4),(1,5,6),(2,1,3),(3,4,6)]
    else:
        people=[("患者","actor"),("前台接待","business-worker"),("本店排班表","business-entity"),("牙医","business-worker"),("牙椅","business-entity"),("收费员","business-worker")]
        messages=[(0,1,"提出就诊诉求","call"),(1,2,"查阅本店排班","call"),(2,1,"反馈时段记录","return"),(1,3,"核实可接诊项目与时段","call"),(3,4,"查看牙椅现场占用","call"),(4,3,"反馈可用状态","return"),(3,1,"告知可接诊安排","return"),(1,0,"提出预约方案","call"),(0,1,"确认诊所、牙医和时间","call"),(1,2,"登记预约台账","call"),(0,1,"到诊并提供身份资料","call"),(1,3,"移交病史变化与预约资料","call"),(3,0,"复核风险并说明方案","call"),(0,3,"表达治疗决定","call"),(3,5,"移交实际治疗清单","call"),(5,0,"出示逐项费用","call"),(0,5,"提交付款凭据","call"),(5,0,"交付结算凭据","call")]
        acts=[(1,0,9),(1,10,11),(2,1,2),(2,9,9),(3,3,6),(3,11,14),(4,4,5),(5,14,17)]
        periodic=[("诊所经理","business-worker"),("总部财务","business-worker"),("负责人","business-worker")]
        quarter=[(0,1,"提交本店收入和费用汇总","call"),(1,0,"要求补充凭据","call"),(0,1,"提交更正与依据","call"),(1,1,"人工核算利润与贡献","call"),(1,2,"提交季度结果","call"),(2,1,"询问牙医贡献来源","call"),(1,2,"说明统计口径与依据","call")]
        qacts=[(0,1,2),(1,0,4),(1,5,6),(2,4,6)]
    first=render_model(base+"_单次就诊",sequence_model(people,messages,acts,base+"：单次就诊"))
    second=render_model(base+"_季度复核",sequence_model(periodic,quarter,qacts,base+"：季度复核"))
    height=35+first.h+95+second.h+150
    scene=r.Scene(1800,height,dict(r.PROFILES["mayuyang"]))
    add_scene(scene,first,60,35,"visit_")
    add_scene(scene,second,60,35+first.h+95,"quarter_")
    scene.text(900,35+first.h+22,"（a）单次就诊主路径",size=23,family="SimSun")
    scene.text(900,height-122,"（b）季度经营复核（独立周期）",size=23,family="SimSun")
    entry=by_base(base)
    scene.text(900,height-77,f"图 {entry['number']}　{entry['title']}",size=27,family="SimSun")
    scene.counts=dict(participants=len(people)+len(periodic),messages=len(messages)+len(quarter),independent_interactions=2)
    save_scene(base,scene)


def usecases():
    base="08_系统用例全景"
    left=[("UC-01","建立并维护患者档案",["reception"]),("UC-02","安排诊疗预约",["reception"]),("UC-03","变更诊疗预约",["reception"]),("UC-04","办理患者到诊",["reception"]),("UC-05","安排候补预约",["reception"]),("UC-06","记录临床就诊",["dentist"]),("UC-07","制定治疗计划",["dentist"]),("UC-08","完成临床就诊",["dentist"]),("UC-09","生成诊疗结算单",["cashier"]),("UC-10","处理收款与退款",["cashier"])]
    right=[("UC-11","维护牙医资质与任职",["ops"]),("UC-18","维护排班与牙椅资源",["manager_resource"]),("UC-12","关闭季度财务期间",["finance"]),("UC-13","分析经营绩效与资质覆盖",["ops","finance","manager_performance"]),("UC-14","管理账户与访问范围",["admin"]),("UC-15","查阅本人诊疗信息",["patient"]),("UC-16","验证登录身份",["user"]),("UC-17","管理账号密码",["user"])]
    actor_specs=[("reception","前台接待",200,351),("dentist","牙医",200,783),("cashier","收费员",200,1053),("ops","总部运营",1580,135),("manager_resource","诊所经理",1580,275),("finance","总部财务",1580,415),("manager_performance","诊所经理",1580,555),("admin","系统管理员",1580,695),("patient","患者",1580,835),("user","用户",1580,1045)]
    model=dict(type="usecase",profile="mayuyang",system="安德鲁牙科连锁运营管理系统",system_bold=True,
               font_size=22,system_font_size=26,width=1800,height=1260,
               boundary=[400,25,990,1195],system_position=[895,48],
               ellipse_width=410,ellipse_height=72,ellipse_slash=True,ellipse_slash_angles=[35,0],
               directed_associations=True,association_arrow="open",
               association_routes={"ops:UC13":[[1440,127],[1440,504],[1400,504]]},
               actors=[dict(id=key,label=label,center=[x,y],top=y-50,scale=1.5,font_size=24,face_slash=True) for key,label,x,y in actor_specs],
               usecases=[dict(id=code.replace("-",""),label=code+"  "+label,actors=actors,center=[645,135+108*i]) for i,(code,label,actors) in enumerate(left)]+[dict(id=code.replace("-",""),label=code+"  "+label,actors=actors,center=[1125,135+140*i]) for i,(code,label,actors) in enumerate(right)],
               basis="报告 UC-01 至 UC-18 及岗位权限表。重复的诊所经理表示同一角色；微信与短信辅助关联见身份认证分图。")
    drawing=render_model(base+"_模型",model)
    scene=r.Scene(1800,1380,dict(r.PROFILES["mayuyang"]))
    add_scene(scene,drawing,0,20,"uc_")
    entry=by_base(base)
    scene.text(900,1303,f"图 {entry['number']}　{entry['title']}",size=27,family="SimSun")
    scene.counts=drawing.counts
    save_scene(base,scene)


if __name__=="__main__":
    business(False)
    business(True)
    usecases()
