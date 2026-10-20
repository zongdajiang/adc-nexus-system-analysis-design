"""Contact sheets for checking all final report pages after PDF rendering."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
FOLDER=ROOT/"qa/style_review"
pages=sorted(FOLDER.glob("page-*.png"))
font=ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf",16)
for start in range(0,len(pages),16):
    sheet=Image.new("RGB",(1160,1640),"#e4e7e9")
    draw=ImageDraw.Draw(sheet)
    for slot,path in enumerate(pages[start:start+16]):
        image=Image.open(path).convert("RGB")
        image.thumbnail((274,374),Image.Resampling.LANCZOS)
        x=slot%4*290+(290-image.width)//2
        y=slot//4*410+25
        sheet.paste(image,(x,y))
        draw.text((slot%4*290+12,slot//4*410+5),f"PDF page {int(path.stem.split('-')[-1])}",fill="#24292e",font=font)
    sheet.save(FOLDER/f"sheet-{start//16+1}.png")
print(f"Created {(len(pages)+15)//16} contact sheets for {len(pages)} pages")
