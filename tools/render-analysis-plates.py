"""Create large, vector analysis-sequence plates from the checked SVG sources.

The source SVGs remain editable. Plates are unnumbered masters; a later pass
adds the printed report page number without rescaling the diagram.
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
TARGET = SOURCE / "analysis_original_pages"
FONT = r"C:\Windows\Fonts\simhei.ttf"
pdfmetrics.registerFont(TTFont("SimHeiADCPlate", FONT))

PLATES = ["18_分析序列_安排预约", "18B_分析序列_维护排班与牙椅", "20_分析序列_完成临床就诊",
          "19_分析序列_完成就诊并开票", "20C_分析序列_季度期间关闭", "20B_分析序列_经营绩效查询"]


def plate(base: str) -> None:
    svg = SOURCE / f"{base}.svg"
    diagram = PdfReader(BytesIO(cairosvg.svg2pdf(url=str(svg)))).pages[0]
    drawing_width = float(diagram.mediabox.width)
    drawing_height = float(diagram.mediabox.height)
    width = drawing_width + 88
    height = drawing_height + 112
    page = PageObject.create_blank_page(width=width, height=height)

    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=(width, height), pageCompression=1)
    draw_caption(c, width, 43, by_base(base), size=17)
    c.showPage()
    c.save()
    stream.seek(0)
    page.merge_page(PdfReader(stream).pages[0])
    diagram.add_transformation(Transformation().translate(44, 76), expand=True)
    page.merge_page(diagram)
    writer = PdfWriter()
    writer.add_page(page)
    TARGET.mkdir(parents=True, exist_ok=True)
    with (TARGET / f"{base}.pdf").open("wb") as handle:
        writer.write(handle)
    print(f"{base}: {width:.1f} x {height:.1f} pt")


if __name__ == "__main__":
    for base in PLATES:
        plate(base)
