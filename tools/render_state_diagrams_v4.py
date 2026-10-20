"""Four state plates with measured, unmasked labels and explicit clearances.

All formats derive from one Scene. The semantic model retains the report's
transition IDs and guards; the drawing never invents a terminal state for paid
invoices. Native PDF is generated from the same SVG and uses embedded glyphs.
"""
from pathlib import Path
from io import BytesIO
import importlib.util
import json
import math
import shutil
import cairosvg
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/uml"
MODEL_OUT = ROOT / "models/uml"
spec = importlib.util.spec_from_file_location(
    "adc_scene", ROOT / "skills/report-uml-reconstruction/scripts/render_diagram.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)

INK, LINE, TEAL = "#20313B", "#53656F", "#2D6E73"
PALE, AMBER, GREEN, MUTED = "#F3F8F8", "#FFF7E8", "#EDF7F1", "#64747C"
STYLE = dict(renderer.PROFILES["mayuyang"], font="Microsoft YaHei", size=18,
             stroke=LINE, line=1.8)


class Plate:
    def __init__(self, name, title, height=530):
        self.name = name
        self.title = title
        self.scene = renderer.Scene(1040, height, STYLE)
        self.nodes = []
        self.transitions = []

    def state(self, id, x, y, title, note, fill=PALE, w=210, h=88):
        s = self.scene
        box = [x-w/2, y-h/2, x+w/2, y+h/2]
        s.rect(box[0], box[1], w, h, fill=fill, stroke=LINE, sw=1.8, rx=12)
        s.rect(box[0], box[1]+3, 5, h-6, fill=TEAL, stroke="none", rx=2)
        s.box(id, box[0], box[1], w, h)
        s.text(x, y-29, title, size=28, color=INK, container=box, role="state-title")
        s.text(x, y+16, note, size=17, color=MUTED, container=box, role="state-note")
        self.nodes.append(dict(id=id, kind="state", title=title, note=note, box=box))

    def initial(self, x, y):
        self.scene.ellipse(x, y, 10, 10, fill=INK, stroke="none")
        self.nodes.append(dict(id="initial", kind="initial", center=[x, y]))

    def choice(self, x, y, r=25):
        self.scene.polygon([(x, y-r), (x+r, y), (x, y+r), (x-r, y)],
                           fill="white", stroke=LINE, sw=1.8)
        self.scene.box("risk_choice", x-r, y-r, 2*r, 2*r, kind="choice")
        self.scene.text(x, y-83, "风险分流", size=18, color=TEAL, role="choice-note")
        self.nodes.append(dict(id="risk_choice", kind="choice", center=[x, y], radius=r))

    def edge(self, id, src, dst, trigger, points, label, lx, ly,
             guard, anchor="middle"):
        self.scene.line(points, arrow="filled", color=LINE, sw=1.8)
        # No white panel is ever painted over the nodes or connectors.
        self.scene.text(lx, ly, label, size=18, color=INK,
                        anchor=anchor, role="transition-label")
        self.transitions.append(dict(id=id, source=src, target=dst, trigger=trigger,
                                     guard=guard, points=points, display=label))

    def note(self, x, y, value, anchor="middle"):
        self.scene.text(x, y, value, size=17, color=MUTED,
                        anchor=anchor, role="diagram-note")

    def save(self):
        s = self.scene
        audit = s.audit()
        issues = audit["issues"]
        clearances = []
        labels = [a for a in audit["text_bounds"]
                  if s.ops[a["op"]].get("role") in
                  ("transition-label", "choice-note", "diagram-note")]
        for label in labels:
            b = label["box"]
            for node in s.boxes:
                distance = rect_distance(b, node["box"])
                clearances.append(distance)
                if distance < 7:
                    issues.append(dict(type="label-node-clearance", text=label["text"],
                                       node=node["id"], distance=distance))
            for op in s.ops:
                if op["type"] != "line":
                    continue
                for p, q in zip(op["points"], op["points"][1:]):
                    if p[0] != q[0] and p[1] != q[1]:
                        issues.append(dict(type="nonorthogonal-connector", points=[p, q]))
                    # Text boxes use actual font metrics; expand by 5 px for
                    # line clearance. Arrowhead envelopes are checked as well.
                    pad = 5
                    expanded = [b[0]-pad, b[1]-pad, b[2]+pad, b[3]+pad]
                    if segment_hits_rect(p, q, expanded):
                        issues.append(dict(type="connector-label-clearance", text=label["text"],
                                           segment=[p, q]))
                head = renderer.arrow_polygon(op["points"], op["arrow"], op["sw"])
                if head:
                    hb = [min(p[0] for p in head), min(p[1] for p in head),
                          max(p[0] for p in head), max(p[1] for p in head)]
                    if rect_distance(b, hb) < 5:
                        issues.append(dict(type="arrow-label-clearance", text=label["text"]))
        # Connectors may touch only their own end nodes, never cross foreign states.
        for edge in self.transitions:
            for node in s.boxes:
                if node["id"] in (edge["source"], edge["target"]):
                    continue
                inner = [node["box"][0]+2, node["box"][1]+2,
                         node["box"][2]-2, node["box"][3]-2]
                if any(segment_hits_rect(p, q, inner)
                       for p, q in zip(edge["points"], edge["points"][1:])):
                    issues.append(dict(type="edge-crosses-foreign-node", edge=edge["id"],
                                       node=node["id"]))
        audit.update(label_node_min_clearance=round(min(clearances), 2),
                     white_mask_panels=0, orthogonal_connectors=True,
                     semantic_transition_count=len(self.transitions),
                     scope="文字、节点、连线及箭头净空；业务语义另与正文守卫表逐条核对。")
        model = dict(type="state", renderer="tools/render_state_diagrams_v4.py",
                     title=self.title, width=s.w, height=s.h,
                     caption_location="report-below", nodes=self.nodes,
                     transitions=self.transitions,
                     notation="UML state, initial pseudostate, choice; filled transition arrows")
        svg = OUT / f"{self.name}.svg"
        renderer.save_svg(s, svg)
        renderer.save_png(s, OUT / f"{self.name}.png", scale=3)
        renderer.save_drawio(s, OUT / f"{self.name}.drawio")
        for path, data in [(OUT/f"{self.name}.scene.json", dict(width=s.w, height=s.h, ops=s.ops)),
                           (OUT/f"{self.name}.audit.json", audit),
                           (MODEL_OUT/f"{self.name}.json", model),
                           (MODEL_OUT/f"{self.name}.state.json", model)]:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline='\n')
        raw = cairosvg.svg2pdf(url=str(svg))
        writer = PdfWriter()
        writer.add_page(PdfReader(BytesIO(raw)).pages[0])
        writer.pdf_header = "%PDF-1.5"
        writer.add_metadata({"/Title": self.title, "/Author": "蒋宗达"})
        pdf_buffer = BytesIO()
        writer.write(pdf_buffer)
        for folder in (OUT, OUT/"state_sources"):
            (folder/f"{self.name}.pdf").write_bytes(pdf_buffer.getvalue())
        writer.close()
        uml = ["@startuml", "!include _state_style.puml"]
        for node in self.nodes:
            if node["kind"] == "state":
                uml.append(f'state "{node["title"]}" as {node["id"]}')
            elif node["kind"] == "choice":
                uml.append(f'state {node["id"]} <<choice>>')
        for e in self.transitions:
            src = "[*]" if e["source"] == "initial" else e["source"]
            uml.append(f'{src} --> {e["target"]} : {e["id"]} {e["trigger"]} [{e["guard"]}]')
        uml.append("@enduml")
        for folder in (OUT, OUT/"state_sources"):
            (folder/f"{self.name}.puml").write_text("\n".join(uml)+"\n", encoding="utf-8", newline='\n')
        for suffix in (".svg", ".png", ".drawio"):
            # Buffered copying also works when a Windows font/image provider
            # retains a read handle and CopyFile2 requests incompatible access.
            with (OUT/f"{self.name}{suffix}").open("rb") as source, \
                 (OUT/"state_sources"/f"{self.name}{suffix}").open("wb") as target:
                shutil.copyfileobj(source, target)
        print(f"{self.name}: {len(self.transitions)} transitions; {len(issues)} layout issues")
        assert not issues, json.dumps(issues, ensure_ascii=False)


def rect_distance(a, b):
    return math.hypot(max(a[0]-b[2], b[0]-a[2], 0),
                      max(a[1]-b[3], b[1]-a[3], 0))


def segment_hits_rect(p, q, r):
    if p[0] == q[0]:
        return r[0] < p[0] < r[2] and max(min(p[1], q[1]), r[1]) < min(max(p[1], q[1]), r[3])
    if p[1] == q[1]:
        return r[1] < p[1] < r[3] and max(min(p[0], q[0]), r[0]) < min(max(p[0], q[0]), r[2])
    return False


def appointment():
    p = Plate("14_状态机_预约", "预约状态机")
    p.initial(35, 150)
    for id, x, title, note, fill in [
        ("confirmed", 230, "已确认", "资源已复核", PALE),
        ("arrived", 560, "已到诊", "身份已核对", PALE),
        ("in_care", 890, "诊疗中", "正在提供服务", PALE),
        ("no_show", 230, "未到诊", "超过保留时限", AMBER),
        ("cancelled", 560, "已取消", "保留发起方与原因", AMBER),
        ("completed", 890, "已完成", "临床完成条件满足", GREEN)]:
        p.state(id, x, 150 if id in ("confirmed", "arrived", "in_care") else 430,
                title, note, fill)
    p.edge("T1", "initial", "confirmed", "创建预约", [(45,150),(125,150)],
           "T1\n创建预约", 80, 96, "患者、牙医、诊所、时段及必要资质校验通过")
    p.edge("T2", "confirmed", "arrived", "登记到诊", [(335,150),(455,150)],
           "T2 登记到诊",395,116,"身份与预约匹配，预约尚有效")
    p.edge("T3", "arrived", "in_care", "开始诊疗", [(665,150),(785,150)],
           "T3 开始诊疗",725,116,"到诊交接和待处理风险已核对")
    p.edge("T4", "in_care", "completed", "完成就诊", [(890,194),(890,386)],
           "T4 完成就诊",910,275,"实施项目、病历签署及必要同意材料已核对",anchor="start")
    p.edge("T5", "confirmed", "cancelled", "取消预约", [(282,194),(282,290),(505,290),(505,386)],
           "T5 取消预约",395,254,"尚未到诊，保留取消原因与操作人")
    p.edge("T6", "arrived", "cancelled", "撤销到诊", [(592,194),(592,386)],
           "T6 撤销到诊",615,320,"尚未实施治疗，授权人员记录更正原因",anchor="start")
    p.edge("T7", "confirmed", "no_show", "标记未到诊", [(178,194),(178,386)],
           "T7 标记未到诊",157,274,"已超过约定时点及保留时限，未办理到诊",anchor="end")
    return p


def clinical():
    p = Plate("15_状态机_临床就诊", "临床就诊状态机", 550)
    p.initial(40,160); p.choice(180,160)
    p.state("waiting",500,160,"待诊疗","待牙医接诊",w=220)
    p.state("in_care",900,160,"诊疗中","实际治疗留痕",w=220)
    p.state("review",500,440,"安全复核","人工核实并签认",AMBER,w=220)
    p.state("completed",900,440,"已完成","病历签署与项目核对",GREEN,w=220)
    p.edge("T1","initial","risk_choice","建立就诊",[(50,160),(155,160)],
           "T1 建立就诊",96,126,"到诊及预约资料有效")
    p.edge("T2","risk_choice","waiting","进入待诊疗",[(205,160),(390,160)],
           "T2 无待处理风险",297,126,"无待处理的过敏、同意或资质风险")
    p.edge("T3","risk_choice","review","进入安全复核",[(180,185),(180,440),(390,440)],
           "T3 存在待处理风险",202,290,"存在需要人工确认的风险事项",anchor="start")
    p.edge("T4","review","waiting","完成安全复核",[(500,396),(500,204)],
           "T4 完成复核",522,290,"复核结论、处理人及时间已留痕",anchor="start")
    p.edge("T5","waiting","in_care","开始诊疗",[(610,160),(790,160)],
           "T5 开始诊疗",700,126,"牙医任职与项目资质有效")
    p.edge("T6","in_care","completed","完成就诊",[(900,204),(900,396)],
           "T6 完成就诊",922,290,"实施项目和病历版本均已核对",anchor="start")
    return p


def invoice():
    p = Plate("16_状态机_发票", "诊疗结算单收款状态机", 550)
    p.initial(35,195)
    p.state("issued",230,195,"已开具","尚无有效净收款")
    p.state("partial",560,195,"部分收款","0 < 净收款 < 应收")
    p.state("paid",890,195,"已结清","净收款 = 应收",GREEN)
    p.state("voided",230,455,"已作废","净收款 = 0 且已授权",AMBER)
    p.edge("T1","initial","issued","生成结算单",[(45,195),(125,195)],
           "T1\n生成结算单",68,137,"同一就诊未重复开单，明细来自实际治疗")
    p.edge("T2","issued","partial","部分收款",[(335,195),(455,195)],
           "T2 部分收款",395,161,"净收款大于零且小于应收金额")
    p.edge("T3","issued","paid","全额收款",[(230,151),(230,80),(890,80),(890,151)],
           "T3 一次全额收款",560,42,"一次收款后净收款等于应收金额")
    p.edge("T4","partial","paid","结清尾款",[(665,195),(785,195)],
           "T4 结清尾款",725,161,"追加收款后净收款等于应收金额")
    p.edge("T5","issued","voided","授权作废",[(230,239),(230,411)],
           "T5 授权作废",252,315,"净收款为零，记录作废原因与审批人",anchor="start")
    p.note(515,432,"净收款按有效收款扣减退款计算。\n退款后的状态转换见下一图。",anchor="start")
    return p


def refund():
    p = Plate("16B_状态机_退款", "退款后结算状态判定", 550)
    p.state("paid",230,190,"已结清","退款前净收款 = 应收",GREEN,w=220)
    p.state("partial",810,190,"部分收款","0 < 净收款 < 应收",w=220)
    p.state("issued",520,450,"已开具","退款后净收款 = 0",AMBER,w=220)
    p.edge("T1","paid","partial","已结清后部分退款",[(340,190),(700,190)],
           "T1 部分退款",520,150,"0 < 净收款 < 应收")
    p.edge("T2","paid","issued","已结清后全额退款",[(230,234),(230,450),(410,450)],
           "T2 全额退款",252,318,"净收款为零，单据仍保留",anchor="start")
    p.edge("T3","partial","issued","部分收款后退至零",[(810,234),(810,450),(630,450)],
           "T3 退至零",788,318,"净收款为零",anchor="end")
    p.edge("T4","partial","partial","部分收款后继续退款",[(920,190),(990,190),(990,80),(810,80),(810,146)],
           "T4 退款后仍部分收款",850,42,"退款后净收款仍大于零且小于应收")
    p.note(520,515,"每笔退款均关联原收款；原始流水与凭据保留不变。")
    return p


if __name__ == "__main__":
    for builder in (appointment,clinical,invoice,refund):
        builder().save()
