"""Export nine UML class figures as readable, source-size vector plates.

The existing PNGs and editable SVG/draw.io files are left untouched. The
`_vector.pdf` files are used in the A4 report; the atlas is a separate reading
edition for inspecting attributes, relationship ends and multiplicities.
"""

from io import BytesIO
from pathlib import Path

import cairosvg
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from figure_registry import by_base, draw_caption


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "uml"
OUTPUT = ROOT / "分析设计文档" / "UML_九张领域类图_原尺寸矢量图册.pdf"
FONT = r"C:\Windows\Fonts\simhei.ttf"
pdfmetrics.registerFont(TTFont("SimHeiADCClass", FONT))

FIGURES = [
    ("12_领域类图_患者与预约", "患者与预约", "Patient and appointment"),
    ("12E_领域类图_患者身份", "患者身份、过敏与绑定", "Patient identity and risk"),
    ("13_领域类图_人员资质与目录", "牙医任职、资质与治疗目录", "Workforce and care catalogue"),
    ("12B_领域类图_临床诊疗", "就诊与实际治疗", "Clinical encounter and performed care"),
    ("12D_领域类图_记录与风险", "临床记录版本与过敏复核", "Record version and risk review"),
    ("12C_领域类图_计划与同意", "治疗计划、项目与同意证据", "Treatment plan and consent"),
    ("13B_领域类图_收费与季度财务", "结算单、明细与收退款", "Billing, receipt and refund"),
    ("13C_领域类图_季度贡献", "季度结果与牙医贡献（目标设计）", "Quarterly contribution · target design"),
    ("13D_领域类图_费用归属", "期间费用与归属（目标设计）", "Period expense allocation · target design"),
]


def add_plate(writer: PdfWriter, base: str, title: str, subtitle: str, number: int) -> None:
    vector = SOURCE / f"{base}_vector.pdf"
    raw = PdfReader(BytesIO(cairosvg.svg2pdf(url=str(SOURCE / f"{base}.svg"))))
    compatible = PdfWriter()
    compatible.add_page(raw.pages[0])
    compatible.pdf_header = "%PDF-1.5"
    with vector.open("wb") as handle:
        compatible.write(handle)
    diagram = compatible.pages[0]
    dw = float(diagram.mediabox.width)
    dh = float(diagram.mediabox.height)
    width = dw + 92
    height = dh + 114
    page = PageObject.create_blank_page(width=width, height=height)

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=(width, height), pageCompression=1)
    entry=by_base(base)
    draw_caption(c, width, 42, entry, size=17)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, 15, f"{number} / {len(FIGURES)}")
    c.showPage()
    c.save()
    stream.seek(0)
    page.merge_page(PdfReader(stream).pages[0])
    diagram.add_transformation(Transformation().translate(46, 76), expand=True)
    page.merge_page(diagram)
    writer.add_page(page)
    print(f"Figure {entry['number']}: {width:.1f} x {height:.1f} pt")


if __name__ == "__main__":
    writer = PdfWriter()
    for number, (base, title, subtitle) in enumerate(FIGURES, 1):
        add_plate(writer, base, title, subtitle, number)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("wb") as handle:
        writer.write(handle)
    print(f"Saved class atlas: {len(writer.pages)} pages")
