"""Read-only publication verification; --write-manifest refreshes QA/hashes."""
from pathlib import Path
from hashlib import sha256
from io import BytesIO
import argparse
import json
import re
import sqlite3
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pypdf import PdfReader
from figure_registry import figures

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "SHA256SUMS.txt"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def published_files():
    raw = subprocess.check_output(
        ["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT)
    return sorted({name for name in raw.decode("utf-8").split("\0")
                   if name and name != "SHA256SUMS.txt" and (ROOT/name).is_file()})


def canonicalize_text():
    """Match .gitattributes before hashing; Git stores these text files as LF."""
    endings = {".md",".tex",".json",".sql",".svg",".drawio",".puml",
               ".py",".ps1",".txt",".yml",".yaml"}
    for name in published_files():
        path = ROOT/name
        if path.suffix in endings or path.name in (".gitignore",".gitattributes"):
            data = path.read_bytes()
            if b"\r\n" in data:
                path.write_bytes(data.replace(b"\r\n",b"\n"))


def verify():
    registry = figures()
    assert len(registry) == 55
    assert registry == json.loads((ROOT/"qa/figure-order-manifest.json").read_text(encoding="utf-8"))
    reader = PdfReader(ROOT/"分析设计文档/ADC_Nexus_主文档.pdf")
    assert len(reader.pages) == 83
    for index,page in enumerate(reader.pages):
        content = page.extract_text() or ""
        assert len(content.strip()) >= 8, f"Blank PDF page {index+1}"
        if index >= 3:
            lines = [x.strip() for x in content.splitlines() if x.strip()]
            number = str(index-2)
            assert lines[0] == number or lines[-1] == number or lines[-1].endswith(" "+number)
    for number,title,printed_page in [(30,"预约状态机",38),(31,"临床就诊状态机",39),
                                      (32,"诊疗结算单收款状态机",40),(33,"退款后结算状态判定",41)]:
        text = re.sub(r"\s+","",reader.pages[printed_page+2].extract_text())
        assert f"图{number}{title}" in text
    assert "参考文献" in reader.pages[-1].extract_text()
    for item in registry:
        base,macro = item["base"],item["macro"]
        if macro == "figerdplate":
            assert (ROOT/f"assets/erd/pages/{base}.pdf").is_file()
        else:
            for suffix in (".png",".svg"):
                assert (ROOT/f"assets/uml/{base}{suffix}").is_file()
            if macro == "figclassvector":
                assert digest(ROOT/f"assets/uml/{base}.pdf") == digest(ROOT/f"assets/uml/{base}_vector.pdf")
    for name in ("schema-model.json","schema.sql","index_recommendations.sql",
                 "audit.json","validation-report.json","validation-summary.md"):
        assert digest(ROOT/"database"/name) == digest(ROOT/"data-design/output"/name)
    model = json.loads((ROOT/"database/schema-model.json").read_text(encoding="utf-8"))
    assert model["counts"]["tables"] == 61 and model["counts"]["columns"] == 730
    assert model["counts"]["foreign_keys"] == 119
    connection = sqlite3.connect(":memory:")
    connection.executescript((ROOT/"database/schema.sql").read_text(encoding="utf-8"))
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    assert len(tables) == 61
    fk_count = sum(len(connection.execute('PRAGMA foreign_key_list("'+name.replace('"','""')+'")').fetchall()) for name in tables)
    assert fk_count == 119
    named_indexes = connection.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
    assert named_indexes == 124
    connection.close()
    atlases = [("UML_九张领域类图_原尺寸矢量图册.pdf",9),
               ("UML_六张内部分析序列_原尺寸矢量图册.pdf",6),
               ("ERD_Overview_and_9_Domains.pdf",10)]
    for name,count in atlases:
        assert len(PdfReader(ROOT/"分析设计文档"/name).pages) == count
    with zipfile.ZipFile(ROOT/"分析设计文档/ERD_10_Individual_PDFs.zip") as archive:
        assert len(archive.namelist()) == 10
        for name in archive.namelist():
            data = archive.read(name)
            assert len(PdfReader(BytesIO(data)).pages) == 1
            assert sha256(data).hexdigest() == digest(ROOT/"assets/erd/pages"/name)
    audits = list((ROOT/"assets/uml").glob("*.audit.json"))
    assert len(audits) == 45
    assert all(not json.loads(p.read_text(encoding="utf-8")).get("issues") for p in audits)
    links = 0
    for path in [ROOT/"README.md",ROOT/"NOTICE.md",*sorted((ROOT/"docs").glob("*.md"))]:
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)",path.read_text(encoding="utf-8")):
            if re.match(r"^[a-zA-Z]+:",target) or target.startswith("#"): continue
            local = target.split("#",1)[0]
            resolved = (path.parent/local).resolve()
            assert resolved.exists() or resolved == MANIFEST, f"Broken local link: {path.name} -> {target}"
            links += 1
    files = published_files()
    total = 0
    for name in files:
        path = ROOT/name
        total += path.stat().st_size
        assert path.stat().st_size < 100*1024*1024, f"Oversized file: {name}"
        assert not any(part in (".git","__pycache__","source-images","history","node_modules")
                       for part in path.relative_to(ROOT).parts), f"Non-public file: {name}"
        assert path.name != ".env" and path.suffix not in (".key",".pem",".db",".sqlite")
        if path.suffix in (".json",".svg",".drawio"):
            if path.suffix == ".json": json.loads(path.read_text(encoding="utf-8-sig"))
            else: ET.parse(path)
        if path.suffix in (".md",".py",".json",".tex",".sql",".ps1",".txt"):
            content = path.read_text(encoding="utf-8-sig")
            for pattern in (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
                            r"gh[pousr]_[A-Za-z0-9]{30,}",r"sk-(?:proj-)?[A-Za-z0-9_-]{35,}"):
                assert not re.search(pattern,content), f"Secret-like literal; review file: {name}"
    return dict(passed=True,version="2026-10-20",report_pages=83,numbered_figures=55,
                usecases=18,database_tables=61,database_columns=730,foreign_keys=119,
                existing_named_indexes=124,class_atlas_pages=9,analysis_atlas_pages=6,
                erd_atlas_pages=10,independent_erd_pdfs=10,uml_audits=45,
                local_links_checked=links,publication_files_before_qa=len(files),
                file_bytes_before_qa=total,
                report_sha256=digest(ROOT/"分析设计文档/ADC_Nexus_主文档.pdf"),
                scope="文件完整性、当前报告结构、DDL、图册及链接；不替代目视或业务验收。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest",action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        canonicalize_text()
    result = verify()
    if args.write_manifest:
        (ROOT/"qa/仓库发布校验.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8", newline='\n')
        files = published_files()
        MANIFEST.write_text("".join(f"{digest(ROOT/name)}  {name}\n" for name in files),encoding="utf-8", newline='\n')
    else:
        expected = {line[66:]:line[:64] for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line}
        assert set(expected) == set(published_files()), "Publication file list changed; refresh manifest after review"
        for name,checksum in expected.items():
            assert digest(ROOT/name) == checksum, f"Checksum mismatch: {name}"
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
