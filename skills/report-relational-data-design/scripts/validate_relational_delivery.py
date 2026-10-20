#!/usr/bin/env python3
"""Validate a generated relational-design delivery as data, diagrams, and PDFs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader


GENERATED_VALIDATION_FILES = {
    "output/validation-report.json",
    "output/validation-summary.md",
    "output/manifest.sha256",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(condition: bool, code: str, message: str,
          errors: list[dict[str, str]], passed: list[dict[str, str]]) -> None:
    item = {"code": code, "message": message}
    (passed if condition else errors).append(item)


def validate_sqlite(ddl_path: Path, model: dict[str, Any], errors: list[dict[str, str]],
                    passed: list[dict[str, str]]) -> dict[str, int]:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.executescript(ddl_path.read_text(encoding="utf-8-sig"))
    except sqlite3.Error as exc:
        errors.append({"code": "DDL_EXECUTION", "message": f"DDL 执行失败：{exc}"})
        connection.close()
        return {"tables": 0, "columns": 0, "foreign_keys": 0, "indexes": 0}

    table_names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    model_tables = sorted(table["name"] for table in model["tables"])
    check(table_names == model_tables, "DDL_TABLE_SET", "DDL 表集合与模型完全一致。", errors, passed)

    column_total = 0
    fk_total = 0
    for table in model["tables"]:
        info = list(connection.execute(f"PRAGMA table_info('{table['name']}')"))
        ddl_columns = [row[1] for row in info]
        model_columns = [column["name"] for column in table["columns"]]
        check(ddl_columns == model_columns, f"DDL_COLUMNS:{table['name']}",
              f"{table['name']} 的字段顺序与模型一致。", errors, passed)
        ddl_pk = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
        check(ddl_pk == table["primary_key"], f"DDL_PK:{table['name']}",
              f"{table['name']} 的主键与模型一致。", errors, passed)
        column_total += len(info)
        fk_total += len(list(connection.execute(f"PRAGMA foreign_key_list('{table['name']}')")))

    explicit_indexes = list(connection.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"
    ))
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    fk_check = list(connection.execute("PRAGMA foreign_key_check"))
    counts = {
        "tables": len(table_names),
        "columns": column_total,
        "foreign_keys": fk_total,
        "indexes": len(explicit_indexes),
    }
    for key, actual in counts.items():
        check(actual == model["counts"][key], f"DDL_COUNT:{key}",
              f"DDL 的 {key} 数量为 {actual}，与模型一致。", errors, passed)
    check(integrity == "ok", "SQLITE_INTEGRITY", "SQLite 完整性检查返回 ok。", errors, passed)
    check(not fk_check, "SQLITE_FK_CHECK", "空库外键检查无异常。", errors, passed)
    connection.close()
    return counts


def validate_pdf(path: Path, expected_pages: int | None, errors: list[dict[str, str]],
                 passed: list[dict[str, str]]) -> dict[str, Any]:
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        if expected_pages is not None:
            check(pages == expected_pages, f"PDF_PAGES:{path.name}",
                  f"{path.name} 页数为 {pages}。", errors, passed)
        else:
            check(pages > 0, f"PDF_PAGES:{path.name}", f"{path.name} 可以读取。", errors, passed)
        low_text_pages: list[int] = []
        box_glyph_pages: list[int] = []
        page_sizes: list[tuple[float, float]] = []
        for index, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            if len(text) < 25:
                low_text_pages.append(index)
            if "□" in text or "�" in text:
                box_glyph_pages.append(index)
            page_sizes.append((round(float(page.mediabox.width), 2), round(float(page.mediabox.height), 2)))
        check(not low_text_pages, f"PDF_BLANK:{path.name}",
              f"{path.name} 没有空白或异常低文本页。", errors, passed)
        check(not box_glyph_pages, f"PDF_GLYPH:{path.name}",
              f"{path.name} 未检测到方框字或替换字符。", errors, passed)
        return {"pages": pages, "low_text_pages": low_text_pages,
                "box_glyph_pages": box_glyph_pages,
                "page_sizes": sorted(set(page_sizes))}
    except Exception as exc:  # noqa: BLE001 - validator must report every parser failure
        errors.append({"code": f"PDF_PARSE:{path.name}", "message": str(exc)})
        return {"pages": 0, "low_text_pages": [], "box_glyph_pages": [], "page_sizes": []}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", required=True, help="Delivery root containing config, source, and output")
    args = parser.parse_args()

    root = Path(args.delivery).resolve()
    output = root / "output"
    config_path = root / "config" / "adc_nexus_relational_config.json"
    snapshot_path = root / "source" / "0007_snapshot.json"
    model_path = output / "schema-model.json"
    audit_path = output / "audit.json"
    ddl_path = output / "schema.sql"
    report_pdf = output / "ADC_Nexus_D部分_关系数据库设计_独立审阅稿.pdf"
    panorama_pdf = output / "ADC_Nexus_全景关系数据图.pdf"

    errors: list[dict[str, str]] = []
    passed: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    required = [
        config_path, snapshot_path, model_path, audit_path, ddl_path,
        output / "index_recommendations.sql", report_pdf, panorama_pdf,
        output / "ADC_Nexus_全景关系数据图.png",
        output / "ADC_Nexus_全景关系数据图.svg",
        output / "ADC_Nexus_全景关系数据图.drawio",
    ]
    for path in required:
        check(path.is_file() and path.stat().st_size > 0, f"FILE:{path.name}",
              f"必需文件存在且非空：{path.relative_to(root)}", errors, passed)
    if errors:
        raise SystemExit("Missing required delivery files")

    config = load_json(config_path)
    model = load_json(model_path)
    audit = load_json(audit_path)

    model_names = [table["name"] for table in model["tables"]]
    assigned = [table_name for domain in config["domains"] for table_name in domain["tables"]]
    check(Counter(assigned) == Counter(model_names), "DOMAIN_COVERAGE",
          "所有模型表恰好归入一个业务簇。", errors, passed)
    check(len(set(model_names)) == len(model_names), "UNIQUE_TABLES",
          "模型中没有重复表名。", errors, passed)
    check(len(config["domains"]) == model["counts"]["domains"], "DOMAIN_COUNT",
          "业务簇数量与模型统计一致。", errors, passed)

    table_map = {table["name"]: table for table in model["tables"]}
    relationship_names = [rel["name"] for rel in model["relationships"]]
    check(len(set(relationship_names)) == len(relationship_names), "UNIQUE_FK_NAMES",
          "外键约束名称没有重复。", errors, passed)
    for rule in config.get("business_rules", []):
        unknown = sorted(set(rule.get("tables", [])) - set(table_map))
        check(not unknown, f"RULE_TABLES:{rule['id']}",
              f"业务规则 {rule['id']} 引用的表均存在。", errors, passed)
    for recommendation in config.get("relationship_recommendations", []):
        source_table, source_column = recommendation["source"].split(".", 1)
        target_table, target_column = recommendation["target"].split(".", 1)
        source_columns = {column["name"] for column in table_map.get(source_table, {}).get("columns", [])}
        target_columns = {column["name"] for column in table_map.get(target_table, {}).get("columns", [])}
        check(source_column in source_columns and target_column in target_columns,
              f"RELATIONSHIP_RECOMMENDATION:{recommendation['id']}",
              f"关系增强候选 {recommendation['id']} 的源字段和目标字段均存在。", errors, passed)
    for table in model["tables"]:
        check(bool(table["primary_key"]), f"PK:{table['name']}",
              f"{table['name']} 已定义主键。", errors, passed)
        columns = {column["name"]: column for column in table["columns"]}
        for key in table["primary_key"]:
            check(key in columns and not columns[key]["nullable"], f"PK_NONNULL:{table['name']}.{key}",
                  f"{table['name']}.{key} 主键存在且非空。", errors, passed)

    check(audit.get("passed") is True and not audit.get("issues"), "GENERATOR_AUDIT",
          "生成器审计通过且无硬错误。", errors, passed)
    check(audit.get("counts") == model.get("counts"), "AUDIT_COUNTS",
          "生成器审计计数与模型一致。", errors, passed)
    index_recommendations = audit.get("index_recommendations", [])
    warnings.append({
        "code": "INDEX_RECOMMENDATIONS",
        "message": f"保留 {len(index_recommendations)} 条外键前导索引候选；它们是需结合查询计划评估的建议，不是完整性错误。",
    })

    ddl_counts = validate_sqlite(ddl_path, model, errors, passed)
    index_sql_count = (output / "index_recommendations.sql").read_text(encoding="utf-8-sig").count("CREATE INDEX")
    check(index_sql_count == len(index_recommendations), "INDEX_SQL_COUNT",
          "索引建议 SQL 与审计建议数量一致。", errors, passed)

    domain_dir = output / "domains"
    domain_files = list(domain_dir.glob("*"))
    for suffix in (".png", ".svg", ".drawio"):
        count = len([path for path in domain_files if path.suffix.lower() == suffix])
        check(count == len(config["domains"]), f"DOMAIN_FILES:{suffix}",
              f"{suffix} 分域图数量为 {count}，与业务簇数量一致。", errors, passed)

    xml_paths = list(output.rglob("*.svg")) + list(output.rglob("*.drawio"))
    for path in xml_paths:
        try:
            ET.parse(path)
            text = path.read_text(encoding="utf-8-sig")
            check("□" not in text and "�" not in text, f"XML_GLYPH:{path.name}",
                  f"{path.name} XML 可解析且无异常字形字符。", errors, passed)
        except Exception as exc:  # noqa: BLE001
            errors.append({"code": f"XML_PARSE:{path.name}", "message": str(exc)})

    png_dimensions: dict[str, list[int]] = {}
    for path in output.rglob("*.png"):
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                png_dimensions[str(path.relative_to(output))] = [image.width, image.height]
                if path.name == "ADC_Nexus_全景关系数据图.png":
                    resolution_ok = image.width >= 6000 and image.height >= 1800
                else:
                    resolution_ok = max(image.width, image.height) >= 1800 and min(image.width, image.height) >= 1100
                check(resolution_ok, f"PNG_SIZE:{path.name}",
                      f"{path.name} 分辨率为 {image.width}×{image.height} px，满足关系图高清交付要求。",
                      errors, passed)
        except Exception as exc:  # noqa: BLE001
            errors.append({"code": f"PNG_PARSE:{path.name}", "message": str(exc)})

    pdf_results = {
        "report": validate_pdf(report_pdf, None, errors, passed),
        "panorama": validate_pdf(panorama_pdf, 1, errors, passed),
    }
    check(50 <= pdf_results["report"]["pages"] <= 70, "REPORT_LENGTH",
          f"专项审阅稿共 {pdf_results['report']['pages']} 页，处于完整且可审阅的合理范围。",
          errors, passed)

    snapshot_hash = sha256(snapshot_path)
    check(snapshot_hash == model["source"]["sha256"], "SNAPSHOT_HASH",
          "交付快照哈希与模型记录一致。", errors, passed)
    check(sha256(config_path) == audit["source_hashes"]["config"], "CONFIG_HASH",
          "配置哈希与审计记录一致。", errors, passed)

    manifest_lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in GENERATED_VALIDATION_FILES:
            continue
        manifest_lines.append(f"{sha256(path)}  {relative}")
    (output / "manifest.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8", newline='\n')

    report = {
        "passed": not errors,
        "root": str(root),
        "counts": model["counts"],
        "ddl_counts": ddl_counts,
        "checks_passed": len(passed),
        "errors": errors,
        "warnings": warnings,
        "pdf": pdf_results,
        "png_dimensions": png_dimensions,
        "hashes": {"snapshot": snapshot_hash, "config": sha256(config_path)},
    }
    (output / "validation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    , newline='\n')
    summary = [
        "# ADC Nexus 关系数据库设计交付验证摘要",
        "",
        f"- 结论：{'通过' if not errors else '未通过'}",
        f"- 自动通过检查：{len(passed)} 项",
        f"- 硬错误：{len(errors)} 项",
        f"- 表／字段／外键／索引：{model['counts']['tables']}／{model['counts']['columns']}／{model['counts']['foreign_keys']}／{model['counts']['indexes']}",
        f"- 专项审阅稿页数：{pdf_results['report']['pages']}",
        f"- 全景关系图页数：{pdf_results['panorama']['pages']}",
        f"- 索引候选：{len(index_recommendations)} 条（仅为优化建议）",
        "",
        "## 结论说明",
        "",
        "DDL 已在内存 SQLite 中实际执行，并与模型逐表核对字段、主键、外键和显式索引数量。PNG、SVG、draw.io 和 PDF 均已完成结构解析；PDF 未发现空白页、方框字或替换字符。",
    ]
    if errors:
        summary.extend(["", "## 错误", ""] + [f"- {item['code']}：{item['message']}" for item in errors])
    summary.extend(["", "## 保留提示", ""] + [f"- {item['message']}" for item in warnings])
    (output / "validation-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8", newline='\n')

    print(json.dumps({
        "passed": not errors,
        "checks_passed": len(passed),
        "errors": len(errors),
        "warnings": len(warnings),
        "manifest_files": len(manifest_lines),
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
