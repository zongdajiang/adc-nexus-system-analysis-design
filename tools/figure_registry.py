"""Single figure order shared by TeX, native plates, companion atlases and QA."""

from pathlib import Path
import json
import re

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent.parent
FIGURE = re.compile(r"\\(fig[A-Za-z]+)\{([^{}]+)\}\{([^{}]+)\}\{([^{}]+)\}")


def expanded_source(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if path.name == "main.tex":
        source = source.split(r"\begin{document}", 1)[1]
    return re.sub(r"\\input\{([^{}]+)\}",
                  lambda m: expanded_source(path.parent / m.group(1)), source)


def figures() -> list[dict]:
    result = []
    for number, match in enumerate(FIGURE.finditer(expanded_source(ROOT / "report/main.tex")), 1):
        macro, base, title, label = match.groups()
        result.append(dict(number=number, macro=macro, base=base, title=title, label=label))
    assert len({item["label"] for item in result}) == len(result)
    assert len({item["base"] for item in result}) == len(result)
    return result


def by_base(base: str) -> dict:
    return next(item for item in figures() if item["base"] == base)


def register_caption_fonts() -> None:
    if "ADCCaption" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("ADCCaption", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))
        pdfmetrics.registerFont(TTFont("ADCCaptionNumber", r"C:\Windows\Fonts\simhei.ttf"))


def draw_caption(c, width: float, baseline: float, entry: dict, size: float = 18) -> None:
    register_caption_fonts()
    prefix = f"图 {entry['number']}"
    prefix_width = pdfmetrics.stringWidth(prefix, "ADCCaptionNumber", size)
    title_width = pdfmetrics.stringWidth(entry["title"], "ADCCaption", size)
    gap = size * .85
    left = (width - prefix_width - gap - title_width) / 2
    c.setFillColorRGB(0, 0, 0)
    c.setFont("ADCCaptionNumber", size)
    c.drawString(left, baseline, prefix)
    c.setFont("ADCCaption", size)
    c.drawString(left + prefix_width + gap, baseline, entry["title"])


if __name__ == "__main__":
    items = figures()
    out = ROOT / "qa/figure-order-manifest.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline='\n')
    rows = ["# 全文图号与顺序核对表", "", "| 图号 | 完整图名 | 引用标识 |", "|---|---|---|"]
    rows += [f"| {i['number']} | {i['title']} | `{i['label']}` |" for i in items]
    (ROOT / "qa/全文图号与顺序核对表.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline='\n')
    print(f"Registered {len(items)} consecutive figures")
