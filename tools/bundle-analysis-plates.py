"""Bundle the six numbered native-size analysis-sequence plates for review."""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent.parent
PLATES = ROOT / "assets" / "uml" / "analysis_pages"
OUTPUT = ROOT / "分析设计文档" / "UML_六张内部分析序列_原尺寸矢量图册.pdf"
NAMES = [
    "18_分析序列_安排预约",
    "18B_分析序列_维护排班与牙椅",
    "20_分析序列_完成临床就诊",
    "19_分析序列_完成就诊并开票",
    "20C_分析序列_季度期间关闭",
    "20B_分析序列_经营绩效查询",
]

writer = PdfWriter()
for name in NAMES:
    reader = PdfReader(PLATES / f"{name}.pdf")
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected one page: {name}")
    writer.add_page(reader.pages[0])
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("wb") as handle:
    writer.write(handle)
print(f"Saved analysis atlas: {len(writer.pages)} pages")
