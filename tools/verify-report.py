"""Structural QA for the assembled professional edition.

Rendered-page visual review and business-semantic review remain separate.
"""

from pathlib import Path
import json
import re
from io import BytesIO
import zipfile

from PIL import Image
from pypdf import PdfReader
from figure_registry import figures as figure_registry


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "report" / "main.pdf"
SOURCE = ROOT / "report" / "main.tex"
MODEL = ROOT / "data-design" / "output" / "schema-model.json"
ERD_DIR = ROOT / "assets" / "erd" / "pages"
UML_DIR = ROOT / "assets" / "uml"

source = SOURCE.read_text(encoding="utf-8")
figure_names = re.findall(
    r"\\fig(?:full|short|uc|dbportrait|db|vectorlong|vector|classvector|compact|statevector|state)\{([^}]+)\}",
    source,
)
assert len(figure_names) >= 35, f"Too few referenced figures: {len(figure_names)}"
assert len(figure_names) == len(set(figure_names)), "Repeated figure filename in main.tex"

figures = []
for name in figure_names:
    png = UML_DIR / f"{name}.png"
    svg = UML_DIR / f"{name}.svg"
    assert png.exists() and svg.exists(), f"Missing PNG/SVG pair: {name}"
    if f"\\figclassvector{{{name}}}" in source:
        assert (UML_DIR / f"{name}_vector.pdf").exists(), f"Missing vector class PDF: {name}"
    with Image.open(png) as image:
        width, height = image.size
    assert max(width, height) >= 700, f"Undersized figure: {name} ({width}x{height})"
    figures.append((name, width, height))

schema = json.loads(MODEL.read_text(encoding="utf-8"))
assert schema["counts"]["tables"] == 61
assert schema["counts"]["columns"] == 730
assert schema["counts"]["foreign_keys"] == 119
audit = json.loads((ROOT / "data-design" / "output" / "audit.json").read_text(encoding="utf-8"))
assert audit["passed"] is True and not audit["issues"]

plates = sorted(ERD_DIR.glob("*.pdf"))
assert len(plates) == 10, f"Expected panorama and nine domain plates, got {len(plates)}"
assert len(list((ROOT / "data-design" / "output" / "domains").glob("*.drawio"))) == 9
for plate in plates:
    reader = PdfReader(plate)
    assert len(reader.pages) == 1, f"ERD plate is not one page: {plate.name}"
    assert plate.stat().st_size > 20_000, f"ERD plate too small: {plate.name}"

analysis_plates = re.findall(r"\\figanalysisplate\{([^}]+)\}", source)
assert len(analysis_plates) == 6 and len(set(analysis_plates)) == 6
for name in analysis_plates:
    assert len(PdfReader(UML_DIR / "analysis_pages" / f"{name}.pdf").pages) == 1
assert len([item for item in figure_registry() if item["macro"]=="figoverview"]) == 3
assert len(PdfReader(ROOT / "分析设计文档" / "UML_九张领域类图_原尺寸矢量图册.pdf").pages) == 9
assert len(PdfReader(ROOT / "分析设计文档" / "UML_六张内部分析序列_原尺寸矢量图册.pdf").pages) == 6

assert "\\input{d_erd_overviews.tex}" in source
assert "\\input{d_erd_portrait_pages.tex}" not in source
for token in ("25_部署边界图", "23_预约界面导航状态", "21_持久化映射类图", "22_预约数据访问序列"):
    assert token in source

report = PdfReader(REPORT)
assert len(report.pages) == 83, f"Unexpected page count: {len(report.pages)}"
large_pages = 0
native_page_numbers = []
for page_number, page in enumerate(report.pages, 1):
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    if width > 900 or height > 900:
        large_pages += 1
        native_page_numbers.append(page_number)
    extracted = page.extract_text() or ""
    assert len(extracted.strip()) >= 8, f"Unexpectedly blank page {page_number}"
    if page_number >= 4:
        lines = [line.strip() for line in extracted.splitlines() if line.strip()]
        expected = str(page_number - 3)
        assert lines[0] == expected or lines[-1] == expected or lines[-1].endswith(" " + expected), (
            f"Missing or nonsequential printed page number: PDF page {page_number}, expected {expected}"
        )
    for forbidden in ("TODO", "Lorem ipsum", "ChatGPT", "AI生成", "�"):
        assert forbidden not in extracted, f"Placeholder text on page {page_number}: {forbidden}"
assert native_page_numbers == [6, 12, 20, 46, 47, 48, 49, 50, 51, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68], (
    f"Unexpected native-size plate locations: {native_page_numbers}"
)
log = (ROOT / "report" / "main.log").read_text(encoding="utf-8", errors="replace")
for forbidden in ("Overfull ", "Underfull ", "undefined references", "Undefined control sequence", "Missing character"):
    assert forbidden not in log, f"TeX layout or reference warning: {forbidden}"

registry=figure_registry()
assert len(registry)==55
aux=(ROOT/"report/main.aux").read_text(encoding="utf-8")
labels={name:(int(number),int(page)) for name,number,page in re.findall(r"\\newlabel\{([^}]+)\}\{\{(\d+)\}\{(\d+)\}",aux)}
previous_page=0
for item in registry:
    actual,printed_page=labels[item["label"]]
    assert actual==item["number"],f"Figure counter mismatch: {item} vs {actual}"
    assert printed_page>=previous_page,f"Nonsequential figure placement: {item}"
    previous_page=printed_page
    page=report.pages[printed_page+2]
    normalized=re.sub(r"\s+","",page.extract_text() or "")
    expected=re.sub(r"\s+","",f"图{actual}{item['title']}")
    assert expected in normalized,f"Missing full caption on printed page {printed_page}: {expected}"
    if item["macro"] in ("figoverview","figanalysisplate","figerdplate"):
        caption_heights=[]
        def inspect_caption(text,cm,tm,font_dict,font_size):
            if text.strip()=="图" or re.match(r"^图\s*\d+",text.strip()):
                caption_heights.append(cm[1]*tm[4]+cm[3]*tm[5]+cm[5])
        page.extract_text(visitor_text=inspect_caption)
        assert any(0<y<float(page.mediabox.height)*.18 for y in caption_heights),f"Native caption not at bottom: {item}"

for item in registry:
    if item["macro"] not in ("figuc","figoverview") and item["base"]!="01_业务用例图":continue
    if item["macro"]=="figoverview" and item["base"]!="08_系统用例全景":continue
    scene=json.loads((UML_DIR/(item["base"]+".scene.json")).read_text(encoding="utf-8"))
    chords=0
    for i,ellipse in enumerate(scene["ops"][:-1]):
        if ellipse["type"]!="ellipse" or ellipse["rx"]<50:continue
        stroke=scene["ops"][i+1]
        assert stroke["type"]=="line" and stroke.get("color")=="#555555",f"Missing use-case slash: {item}"
        for x,y in stroke["points"]:
            ellipse_error=((x-ellipse["cx"])/ellipse["rx"])**2+((y-ellipse["cy"])/ellipse["ry"])**2
            assert abs(ellipse_error-1)<1e-6,f"Floating ellipse slash endpoint: {item}"
        chords+=1
    assert chords>0

def check_companion(path,entries):
    pages=PdfReader(path).pages
    assert len(pages)==len(entries)
    for page,item in zip(pages,entries):
        actual=re.sub(r"\s+","",page.extract_text() or "")
        expected=re.sub(r"\s+","",f"图{item['number']}{item['title']}")
        assert expected in actual,f"Companion caption mismatch: {path}, {item}"

check_companion(ROOT/"分析设计文档/UML_九张领域类图_原尺寸矢量图册.pdf",[i for i in registry if i["macro"]=="figclassvector"])
check_companion(ROOT/"分析设计文档/UML_六张内部分析序列_原尺寸矢量图册.pdf",[i for i in registry if i["macro"]=="figanalysisplate"])
erd_entries=[i for i in registry if i["macro"]=="figerdplate"]
check_companion(ROOT/"分析设计文档/ERD_Overview_and_9_Domains.pdf",erd_entries)
with zipfile.ZipFile(ROOT/"分析设计文档/ERD_10_Individual_PDFs.zip") as archive:
    assert len(archive.namelist())==10
    for item in erd_entries:
        check_companion(BytesIO(archive.read(item["base"]+".pdf")),[item])

result={
    "passed": True,
    "report_pages": len(report.pages),
    "native_size_vector_pages": large_pages,
    "native_size_erd_pages": len(plates),
    "native_size_analysis_pages": len(analysis_plates),
    "native_size_interaction_overviews": 3,
    "class_atlas_pages": 9,
    "figures": len(figures),
    "numbered_figures": len(registry),
    "figure_numbers": [1,len(registry)],
    "native_captions_at_bottom": 19,
    "database_tables": schema["counts"]["tables"],
    "database_columns": schema["counts"]["columns"],
    "foreign_keys": schema["counts"]["foreign_keys"],
    "domain_drawio_sources": 9,
    "smallest_figure_long_side_px": min(max(width, height) for _, width, height in figures),
}
(ROOT/"qa/结构检查结果.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8", newline='\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
