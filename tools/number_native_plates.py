"""Synchronize native-plate captions and printed page numbers from TeX labels."""

from io import BytesIO
import re
import shutil
import zipfile

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject
from reportlab.pdfgen import canvas

from figure_registry import ROOT, figures, draw_caption


def aux_labels():
    source=(ROOT/"report/main.aux").read_text(encoding="utf-8")
    return {label:(int(number),int(page)) for label,number,page in re.findall(r"\\newlabel\{([^}]+)\}\{\{(\d+)\}\{(\d+)\}",source)}


def stamp(source, target, page_number, size=15):
    page=PdfReader(source).pages[0]
    stream=BytesIO()
    c=canvas.Canvas(stream,pagesize=(float(page.mediabox.width),float(page.mediabox.height)),pageCompression=1)
    c.setFillColorRGB(.32,.36,.39)
    c.setFont("Helvetica",size)
    c.drawCentredString(float(page.mediabox.width)/2,13,str(page_number))
    c.showPage();c.save();stream.seek(0)
    page.merge_page(PdfReader(stream).pages[0])
    writer=PdfWriter();writer.add_page(page)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("wb") as handle:writer.write(handle)


def prepare_erd(entry):
    source=ROOT/"assets/erd/original_pages"/(entry["base"]+".pdf")
    diagram=PdfReader(source).pages[0]
    w,h=float(diagram.mediabox.width),float(diagram.mediabox.height)
    band=min(170,max(88,w*.07))
    page=PageObject.create_blank_page(width=w,height=h+band)
    stream=BytesIO();c=canvas.Canvas(stream,pagesize=(w,h+band),pageCompression=1)
    draw_caption(c,w,band*.52,entry,size=min(52,max(20,w*.017)))
    c.showPage();c.save();stream.seek(0)
    page.merge_page(PdfReader(stream).pages[0])
    page.merge_transformed_page(diagram,Transformation().translate(0,band))
    target=ROOT/"assets/erd/captioned_original_pages"/(entry["base"]+".pdf")
    target.parent.mkdir(parents=True,exist_ok=True)
    writer=PdfWriter();writer.add_page(page)
    with target.open("wb") as handle:writer.write(handle)
    return target


def run(bootstrap=False):
    labels=aux_labels()
    items=figures()
    for entry in items:
        kind=entry["macro"]
        if kind not in ("figoverview","figanalysisplate","figerdplate"):continue
        if kind=="figerdplate":
            source=prepare_erd(entry)
            target=ROOT/"assets/erd/pages"/(entry["base"]+".pdf")
        else:
            stem="overview" if kind=="figoverview" else "analysis"
            source=ROOT/f"assets/uml/{stem}_original_pages"/(entry["base"]+".pdf")
            target=ROOT/f"assets/uml/{stem}_pages"/(entry["base"]+".pdf")
        if bootstrap:
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        else:
            actual,page_number=labels[entry["label"]]
            assert actual==entry["number"],(entry,actual)
            stamp(source,target,page_number,size=15 if kind!="figerdplate" else min(43,max(16,float(PdfReader(source).pages[0].mediabox.width)*.016)))
            print(f"Figure {actual}: printed page {page_number}")
    if not bootstrap:
        erd=[ROOT/"assets/erd/pages"/(i["base"]+".pdf") for i in items if i["macro"]=="figerdplate"]
        writer=PdfWriter()
        for path in erd:writer.add_page(PdfReader(path).pages[0])
        combined=ROOT/"分析设计文档/ERD_Overview_and_9_Domains.pdf"
        with combined.open("wb") as handle:writer.write(handle)
        shutil.copy2(combined,ROOT/"data-design/output/ADC_Nexus_D部分_全景与九分域_矢量审阅本.pdf")
        with zipfile.ZipFile(ROOT/"分析设计文档/ERD_10_Individual_PDFs.zip","w",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
            for path in erd:archive.write(path,arcname=path.name)


if __name__=="__main__":
    import sys
    run(bootstrap="--bootstrap" in sys.argv)
