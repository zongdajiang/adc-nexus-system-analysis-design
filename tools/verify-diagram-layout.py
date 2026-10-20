"""Fail when a current UML rendering audit reports a layout problem."""

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parent.parent
RENDERED = ROOT / "assets" / "uml"


def main() -> int:
    audits = sorted(RENDERED.glob("*.audit.json"))
    if not audits:
        raise FileNotFoundError(f"No UML layout audits in {RENDERED}")
    results = {}
    for path in audits:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        issues = data.get("issues", [])
        if issues:
            results[path.name.removesuffix(".audit.json")] = issues
    print(json.dumps({
        "passed": not results,
        "diagrams": len(audits),
        "diagrams_with_layout_issues": len(results),
        "issues": results,
        "limitations": "布局审计不替代业务语义与最终 PDF 目视检查。",
    }, ensure_ascii=False, indent=2))
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
