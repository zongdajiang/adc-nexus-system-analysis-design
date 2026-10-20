#!/usr/bin/env python3
"""Render a Drizzle SQLite snapshot as an academic ERD and data dictionary package."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import html
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as RLImage, KeepTogether,
    NotAtTopPageBreak, PageBreak, PageBreakIfNotEmpty, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from pypdf import PdfReader, PdfWriter


FONT_REGULAR_CANDIDATES = [
    Path(r"C:\Windows\Fonts\Deng.ttf"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path(r"C:\Windows\Fonts\Dengb.ttf"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\arialbd.ttf"),
]

TOKEN_CN = {
    "account": "账户", "action": "操作", "actual": "实际", "address": "地址",
    "adjustment": "调整", "allergy": "过敏", "amount": "金额", "appointment": "预约",
    "approved": "批准", "assumption": "假设", "attachment": "附件", "auth": "认证",
    "available": "可用", "basis": "基点", "biography": "简介", "booking": "预约渠道",
    "candidate": "候选", "category": "类别", "chair": "牙椅", "channel": "渠道",
    "checksum": "校验值", "clinic": "诊所", "clinical": "临床", "close": "关闭",
    "code": "编码", "communication": "沟通", "confirmation": "确认", "consent": "同意",
    "contact": "联系人", "content": "内容", "cost": "成本", "count": "数量",
    "created": "创建", "currency": "币种", "date": "日期", "default": "默认",
    "dentist": "牙医", "description": "说明", "display": "显示", "document": "文档",
    "duplicate": "重复", "duration": "时长", "effective": "生效", "email": "邮箱",
    "employee": "员工", "end": "结束", "entered": "录入", "event": "事件",
    "exception": "异常", "expires": "失效", "expansion": "扩张", "failed": "失败",
    "fen": "分", "financial": "财务", "flag": "标志", "forecast": "预测",
    "formula": "公式", "from": "开始", "gateway": "网关", "government": "证件",
    "hash": "哈希", "hire": "入职", "hours": "小时", "id": "标识",
    "incentive": "激励", "invoice": "结算单", "ip": "IP", "is": "是否",
    "issued": "签发", "item": "项目", "json": "JSON", "key": "键",
    "laboratory": "技工室", "language": "语言", "last": "最近", "line": "行",
    "locked": "锁定", "login": "登录", "materials": "材料", "max": "最大",
    "method": "方式", "minutes": "分钟", "name": "名称", "net": "净额",
    "note": "记录", "notification": "通知", "number": "编号", "observed": "观察",
    "odontogram": "牙位图", "offer": "邀约", "opened": "开业", "operating": "营业",
    "organization": "组织", "outcome": "结果", "parent": "父级", "patient": "患者",
    "payment": "收款", "permission": "权限", "period": "期间", "phone": "电话",
    "plan": "计划", "pool": "奖金池", "preferred": "偏好", "price": "价格",
    "primary": "主要", "priority": "优先级", "profit": "利润", "provider": "提供方",
    "qualification": "资质", "quarter": "季度", "rate": "比率", "reason": "原因",
    "received": "收款", "reference": "参考", "refund": "退款", "relationship": "关系",
    "requested": "申请", "result": "结果", "reopen": "重开", "risk": "风险",
    "role": "角色", "salt": "盐值", "scenario": "方案", "schedule": "排班",
    "scheduled": "计划", "scope": "范围", "severity": "严重度", "snapshot": "快照",
    "source": "来源", "start": "开始", "state": "状态", "status": "状态",
    "storage": "存储", "subject": "主体", "substance": "物质", "system": "系统",
    "text": "文本", "time": "时间", "timeline": "时间线", "timezone": "时区",
    "to": "结束", "token": "令牌", "tooth": "牙位", "total": "合计",
    "treatment": "治疗", "type": "类型", "unit": "单位", "updated": "更新",
    "user": "用户", "value": "值", "vendor": "供应商", "verification": "核实",
    "verified": "核实", "version": "版本", "visit": "就诊", "weekly": "每周",
    "waitlist": "候补", "workflow": "流程", "zh": "中文", "en": "英文",
}

# Extra vocabulary used by the ADC Nexus physical schema.  Keeping it here
# avoids machine-like descriptions such as "acceptedat" or "chiefcomplaint".
TOKEN_CN.update({
    "acceptable": "可接受", "acceptance": "验收", "accepted": "接受",
    "accessible": "无障碍可用", "acknowledged": "确认知悉", "actor": "操作主体", "advisory": "建议性",
    "after": "变更后", "agent": "客户端", "amendment": "修订",
    "appointments": "预约量", "attempt": "尝试", "attempts": "尝试次数",
    "author": "作者", "authorized": "授权", "authored": "编制",
    "balance": "余额", "before": "变更前", "birth": "出生",
    "body": "机构", "bytes": "字节", "by": "操作人", "calculated": "计算",
    "calculation": "计算", "cancellation": "取消", "capital": "资本",
    "capacity": "容量", "captured": "采集", "catalog": "目录",
    "chief": "主诉", "city": "城市", "checklist": "检查清单",
    "closed": "关闭", "closes": "闭诊", "complaint": "主诉",
    "compatibility": "兼容性", "completed": "完成", "composite": "综合",
    "constraint": "约束", "consumed": "使用", "coverage": "覆盖率",
    "current": "当前", "day": "星期", "delivered": "送达", "domain": "权限域",
    "demand": "需求", "dentition": "牙列", "disclaimer": "免责声明",
    "district": "区域", "due": "到期", "earliest": "最早",
    "eligible": "可计入", "employment": "任职", "ends": "结束",
    "entity": "业务实体", "equipment": "设备", "estimated": "估算", "expense": "费用",
    "evidence": "依据", "failure": "失败", "file": "文件",
    "finding": "发现", "fixed": "固定", "formula": "公式",
    "forecast": "预测", "gate": "校验门", "gateway": "支付网关", "gender": "性别",
    "granted": "授予", "horizon": "预测期", "idempotency": "幂等",
    "ids": "标识集合", "incurred": "发生", "initial": "初始",
    "inputs": "输入", "iterations": "迭代次数", "issued": "签发",
    "issuing": "签发", "label": "标签", "last4": "后四位",
    "languages": "语言集合", "latest": "最晚", "level": "级别", "locale": "区域语言",
    "margin": "利润率", "masked": "脱敏值", "match": "匹配",
    "metadata": "元数据", "mime": "媒体格式", "months": "月数",
    "network": "连锁网络", "notice": "提前通知", "notes": "备注",
    "observation": "观察记录", "occurred": "发生", "of": "的",
    "offered": "邀约", "open": "未关闭", "opens": "开诊",
    "override": "人工调整", "paid": "已收", "password": "密码",
    "payback": "回收期", "performed": "实施", "periods": "时段集合",
    "planned": "规划", "points": "基点", "policy": "策略",
    "precaution": "注意事项", "profile": "身份资料", "projected": "预测",
    "purpose": "用途", "qualifications": "资质集合", "quarterly": "季度",
    "queued": "排队", "rationale": "依据", "reaction": "反应",
    "readiness": "就绪度", "reasons": "原因集合", "recipient": "接收目标", "recognized": "确认",
    "refunded": "已退款", "revenue": "收入",
    "recorded": "登记", "recurrence": "重复规则", "released": "释放",
    "reopened": "重新打开", "reporting": "核算", "request": "请求",
    "required": "必需", "requirement": "要求", "resolution": "处理结果",
    "resolved": "解决", "responded": "响应", "return": "返回",
    "reviewed": "复核", "revoked": "撤销", "room": "诊室",
    "rule": "规则", "safety": "安全", "score": "评分", "seen": "访问",
    "sent": "发送", "sequence": "顺序", "set": "设置", "setting": "配置项",
    "sign": "登录", "signed": "签署", "simulated": "模拟",
    "size": "大小", "slot": "时段", "staff": "员工", "standard": "标准",
    "started": "开始", "starts": "开始", "subtotal": "小计",
    "support": "辅助", "supersedes": "替代", "surfaces": "牙面",
    "target": "目标", "tax": "税额", "template": "模板",
    "title": "职称", "travel": "通勤", "until": "截止时间",
    "units": "数量", "used": "使用", "username": "登录用户名",
    "valid": "有效", "vendor": "供应商", "void": "作废",
    "voided": "作废", "week": "周", "weekly": "每周",
})

SPECIAL_FIELDS = {
    "created_at": "记录创建时间。", "updated_at": "记录最后更新时间。",
    "status": "记录当前生命周期状态。", "name_zh": "面向中文界面的正式名称。",
    "name_en": "面向英文界面的正式名称。", "description_zh": "中文业务说明。",
    "description_en": "英文业务说明。", "effective_from": "规则或关系开始生效的日期。",
    "effective_to": "规则或关系停止生效的日期；为空表示持续有效。",
    "starts_on": "期间或规则的开始日期。", "ends_on": "期间或规则的结束日期。",
    "request_id": "贯穿一次请求和审计事件的关联标识。",
    "scope_key": "区分全网、诊所或其他核算范围的稳定键。",
}

SPECIAL_FIELDS.update({
    "username": "用于本地登录的唯一用户名。",
    "password_hash": "密码的单向哈希值；不保存明文密码。",
    "password_salt": "密码哈希使用的随机盐值。",
    "password_iterations": "密码派生算法的迭代次数。",
    "password_set_at": "最近一次设置密码的时间点。",
    "phone_e164": "符合 E.164 格式的标准化手机号码。",
    "email": "用于联系或登录通知的电子邮箱地址。",
    "accepted_by": "接受邀请时记录的操作主体。",
    "actor_subject": "执行操作的认证主体标识。",
    "auth_subject": "身份提供方返回的稳定认证主体标识。",
    "provider_subject": "外部身份提供方中的主体标识。",
    "return_to": "认证完成后允许返回的系统内路径。",
    "recipient_masked": "脱敏后的通知接收目标，用于审计展示。",
    "idempotency_key": "防止同一通知或交易重复处理的幂等键。",
    "request_id": "贯穿一次请求及其审计事件的关联标识。",
    "entity_id": "与实体类型配合使用的多态业务实体标识。",
    "reference_id": "与引用类型配合使用的外部或业务记录标识。",
    "supersedes_observation_id": "被当前记录替代的上一条牙位观察标识；目标设计建议增加自引用外键。",
    "clinic_id": "邀请限定的诊所标识；目标设计建议增加到 clinics.id 的可选外键。",
    "role_id": "邀请预授予的角色标识；目标设计建议增加到 roles.id 的可选外键。",
    "currency": "金额字段所使用的 ISO 4217 币种代码。",
    "timezone": "业务地点采用的 IANA 时区名称。",
    "locale": "通知或界面采用的区域语言代码。",
    "units": "实际实施项目的数量或计量单位数。",
    "units_snapshot": "结算时冻结的项目数量快照。",
    "unit": "治疗目录的计价或计量单位。",
    "from_status": "状态变更前的生命周期状态。",
    "to_status": "状态变更后的生命周期状态。",
    "value_text": "适用于文本型配置项的值。",
    "value_json": "适用于结构化配置项的 JSON 值。",
    "formula_evidence": "计算结果采用的公式、口径或人工复核依据。",
    "formula_evidence_json": "计算依据的结构化 JSON 快照。",
    "simulated_gateway_reference": "模拟支付网关返回的参考号；不代表真实清算凭证。",
    "is_accessible": "标识牙椅或服务位是否满足无障碍使用要求。",
    "safety_gate_status": "就诊进入临床处置前的安全校验状态。",
    "languages_json": "牙医可提供服务的语言集合，以结构化 JSON 保存。",
    "match_reasons_json": "重复患者候选的匹配依据集合，以结构化 JSON 保存。",
    "reasons_json": "候补邀约或处理结果的原因集合，以结构化 JSON 保存。",
    "domain": "权限所属的功能域，用于权限分组和授权校验。",
    "refunded_at": "退款实际完成的时间点。",
})

PALETTE = [
    "#DCEAF7", "#E7E1F3", "#DDEEDC", "#F5E8CF", "#D9ECEA",
    "#F1DFE3", "#E1E8F0", "#F4E7D7", "#E6E6D7", "#DDE7F4",
]


def pick_font(candidates: list[Path]) -> Path:
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("No usable font found")


FONT_REGULAR = pick_font(FONT_REGULAR_CANDIDATES)
FONT_BOLD = pick_font(FONT_BOLD_CANDIDATES)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def sql_default(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def human_tokens(name: str) -> str:
    tokens = [TOKEN_CN.get(token, token) for token in name.split("_") if token]
    return "".join(tokens)


def field_description(table_label: str, column: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    name = column["name"]
    if column["fk_targets"]:
        targets = "、".join(f"{target['label']}（{target['table']}.{target['column']}）" for target in column["fk_targets"])
        return f"关联{targets}的外键。"
    if name == "id":
        return f"{table_label}的内部唯一标识。"
    if name in SPECIAL_FIELDS:
        return SPECIAL_FIELDS[name]
    label = human_tokens(name)
    if name.endswith("_fen_snapshot"):
        return f"{human_tokens(name.removesuffix('_fen_snapshot'))}金额快照，以人民币分为最小存储单位。"
    if name.endswith("_fen"):
        return f"{human_tokens(name.removesuffix('_fen'))}金额，以人民币分为最小存储单位。"
    if name.endswith("_basis_points"):
        return f"{human_tokens(name.removesuffix('_basis_points'))}比率，以万分之一为单位。"
    if name.endswith("_json_snapshot"):
        return f"{human_tokens(name.removesuffix('_json_snapshot'))}的结构化 JSON 快照。"
    if name.endswith("_json"):
        return f"{human_tokens(name.removesuffix('_json'))}的结构化 JSON 数据。"
    if name.endswith("_hash"):
        return f"{human_tokens(name.removesuffix('_hash'))}的单向哈希值，不保存明文。"
    if name.endswith("_salt"):
        return f"{human_tokens(name.removesuffix('_salt'))}哈希使用的随机盐值。"
    if name.endswith("_at_snapshot"):
        return f"{human_tokens(name.removesuffix('_at_snapshot'))}时间快照。"
    if name.endswith("_at"):
        return f"{human_tokens(name.removesuffix('_at'))}时间点。"
    if name.endswith("_on"):
        return f"{human_tokens(name.removesuffix('_on'))}业务日期。"
    if name.endswith("_date"):
        return f"{human_tokens(name.removesuffix('_date'))}日期。"
    if name.endswith("_en_snapshot"):
        return f"{human_tokens(name.removesuffix('_en_snapshot'))}英文快照。"
    if name.endswith("_zh_snapshot"):
        return f"{human_tokens(name.removesuffix('_zh_snapshot'))}中文快照。"
    if name.endswith("_en"):
        return f"{human_tokens(name.removesuffix('_en'))}的英文内容。"
    if name.endswith("_zh"):
        return f"{human_tokens(name.removesuffix('_zh'))}的中文内容。"
    if name.endswith("_code_snapshot"):
        return f"{human_tokens(name.removesuffix('_code_snapshot'))}业务编码快照。"
    if name.endswith("_code"):
        return f"{human_tokens(name.removesuffix('_code'))}的稳定业务编码。"
    if name.endswith("_version") or name == "version":
        return f"{human_tokens(name.removesuffix('_version'))}的乐观锁或历史版本号。"
    if name.endswith("_version_number"):
        return f"{human_tokens(name.removesuffix('_version_number'))}的递增版本号。"
    if name.endswith("_count"):
        return f"{human_tokens(name.removesuffix('_count'))}数量。"
    if name.endswith("_minutes"):
        return f"{human_tokens(name.removesuffix('_minutes'))}时长，以分钟为单位。"
    if name.endswith("_hours"):
        return f"{human_tokens(name.removesuffix('_hours'))}时长，以小时为单位。"
    if name.endswith("_months"):
        return f"{human_tokens(name.removesuffix('_months'))}周期，以月为单位。"
    if name.endswith("_bytes"):
        return f"{human_tokens(name.removesuffix('_bytes'))}大小，以字节为单位。"
    if name.endswith("_number"):
        return f"{human_tokens(name.removesuffix('_number'))}编号。"
    if name.endswith("_status"):
        return f"{human_tokens(name.removesuffix('_status'))}状态。"
    if name.endswith("_state"):
        return f"{human_tokens(name.removesuffix('_state'))}状态。"
    if name.endswith("_type"):
        return f"{human_tokens(name.removesuffix('_type'))}类型。"
    if name.endswith("_method"):
        return f"{human_tokens(name.removesuffix('_method'))}方式。"
    if name.endswith("_reason"):
        return f"{human_tokens(name.removesuffix('_reason'))}原因。"
    if name.endswith("_key"):
        return f"{human_tokens(name.removesuffix('_key'))}稳定键。"
    if name.endswith("_id"):
        return f"{human_tokens(name.removesuffix('_id'))}标识。"
    if name.startswith(("is_", "has_")):
        return f"表示{label}的布尔标志。"
    return f"{label}。"


def read_model(snapshot_path: Path, config_path: Path) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    raw_tables = snapshot.get("tables", {})
    domain_for: dict[str, dict[str, Any]] = {}
    for position, domain in enumerate(config["domains"]):
        domain.setdefault("color", PALETTE[position % len(PALETTE)])
        for table in domain["tables"]:
            if table in domain_for:
                raise ValueError(f"table assigned to multiple domains: {table}")
            domain_for[table] = domain
    missing = sorted(set(raw_tables) - set(domain_for))
    extra = sorted(set(domain_for) - set(raw_tables))
    if missing or extra:
        raise ValueError(f"domain coverage mismatch; missing={missing}, extra={extra}")

    labels = config.get("table_labels", {})
    descriptions = config.get("table_descriptions", {})
    field_overrides = config.get("field_descriptions", {})
    tables: list[dict[str, Any]] = []
    table_map: dict[str, dict[str, Any]] = {}
    for table_name, raw in raw_tables.items():
        pk_columns = {c["name"] for c in raw.get("columns", {}).values() if c.get("primaryKey")}
        for composite in raw.get("compositePrimaryKeys", {}).values():
            pk_columns.update(composite.get("columns", []))
        fk_by_column: dict[str, list[dict[str, Any]]] = {}
        relationships = []
        for fk in raw.get("foreignKeys", {}).values():
            for source_column, target_column in zip(fk["columnsFrom"], fk["columnsTo"]):
                target = {
                    "constraint": fk["name"], "table": fk["tableTo"], "column": target_column,
                    "label": labels.get(fk["tableTo"], human_tokens(fk["tableTo"])),
                    "on_delete": fk.get("onDelete", "no action"), "on_update": fk.get("onUpdate", "no action"),
                }
                fk_by_column.setdefault(source_column, []).append(target)
            relationships.append({
                "name": fk["name"], "source_table": table_name,
                "source_columns": fk["columnsFrom"], "target_table": fk["tableTo"],
                "target_columns": fk["columnsTo"], "on_delete": fk.get("onDelete", "no action"),
                "on_update": fk.get("onUpdate", "no action"),
            })
        index_by_column: dict[str, list[str]] = {}
        indexes = []
        for idx in raw.get("indexes", {}).values():
            indexes.append(idx)
            prefix = "UQ" if idx.get("isUnique") else "IX"
            for column in idx.get("columns", []):
                index_by_column.setdefault(column, []).append(f"{prefix}:{idx['name']}")
        columns = []
        for ordinal, column in enumerate(raw.get("columns", {}).values(), 1):
            name = column["name"]
            item = {
                "ordinal": ordinal, "name": name, "type": column["type"].upper(),
                "pk": name in pk_columns, "nullable": not column.get("notNull", False),
                "autoincrement": bool(column.get("autoincrement", False)),
                "default": column.get("default"), "fk_targets": fk_by_column.get(name, []),
                "indexes": index_by_column.get(name, []),
            }
            item["description"] = field_description(
                labels.get(table_name, human_tokens(table_name)), item,
                field_overrides.get(f"{table_name}.{name}"),
            )
            columns.append(item)
        table = {
            "name": table_name, "label": labels.get(table_name, human_tokens(table_name)),
            "description": descriptions.get(table_name, f"保存{labels.get(table_name, human_tokens(table_name))}相关事实。"),
            "domain_id": domain_for[table_name]["id"], "domain_name": domain_for[table_name]["name"],
            "domain_color": domain_for[table_name]["color"], "columns": columns,
            "primary_key": sorted(pk_columns, key=lambda n: [c["name"] for c in columns].index(n)),
            "relationships": relationships, "indexes": indexes,
            "checks": list(raw.get("checkConstraints", {}).values()),
        }
        tables.append(table)
        table_map[table_name] = table
    relationships = [rel for table in tables for rel in table["relationships"]]
    model = {
        "project": config["project"], "domains": config["domains"], "tables": tables,
        "relationships": relationships, "business_rules": config.get("business_rules", []),
        "relationship_recommendations": config.get("relationship_recommendations", []),
        "source": {"snapshot": str(snapshot_path), "sha256": sha256(snapshot_path)},
    }
    model["counts"] = {
        "tables": len(tables), "columns": sum(len(t["columns"]) for t in tables),
        "foreign_keys": len(relationships), "indexes": sum(len(t["indexes"]) for t in tables),
        "domains": len(config["domains"]), "business_rules": len(model["business_rules"]),
        "relationship_recommendations": len(model["relationship_recommendations"]),
    }
    return model


def validate_model(model: dict[str, Any], minimum_tables: int) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    tables = {table["name"]: table for table in model["tables"]}
    if len(tables) < minimum_tables:
        issues.append(f"table count {len(tables)} is below configured minimum {minimum_tables}")
    for table in model["tables"]:
        columns = {column["name"]: column for column in table["columns"]}
        if not table["primary_key"]:
            issues.append(f"{table['name']}: no primary key")
        for key in table["primary_key"]:
            if key not in columns:
                issues.append(f"{table['name']}: PK column missing: {key}")
            elif columns[key]["nullable"]:
                issues.append(f"{table['name']}.{key}: PK cannot be nullable")
        indexed_sets = [tuple(idx.get("columns", [])) for idx in table["indexes"]]
        if table["primary_key"]:
            indexed_sets.append(tuple(table["primary_key"]))
        for rel in table["relationships"]:
            target = tables.get(rel["target_table"])
            if target is None:
                issues.append(f"{rel['name']}: target table missing")
                continue
            target_columns = {c["name"]: c for c in target["columns"]}
            for source_name, target_name in zip(rel["source_columns"], rel["target_columns"]):
                if source_name not in columns or target_name not in target_columns:
                    issues.append(f"{rel['name']}: missing source or target column")
                    continue
                if columns[source_name]["type"] != target_columns[target_name]["type"]:
                    issues.append(f"{rel['name']}: incompatible types {columns[source_name]['type']} and {target_columns[target_name]['type']}")
            if not any(tuple(rel["source_columns"]) == cols[:len(rel["source_columns"])] for cols in indexed_sets if cols):
                warnings.append(f"{rel['name']}: FK columns are not a leading index")
    return {"passed": not issues, "issues": issues, "warnings": warnings, "counts": model["counts"]}


def missing_fk_index_recommendations(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return reviewable index proposals without pretending they exist in the source schema."""
    recommendations: list[dict[str, Any]] = []
    for table in model["tables"]:
        indexed_sets = [tuple(idx.get("columns", [])) for idx in table["indexes"]]
        if table["primary_key"]:
            indexed_sets.append(tuple(table["primary_key"]))
        for rel in table["relationships"]:
            source_columns = tuple(rel["source_columns"])
            covered = any(source_columns == cols[:len(source_columns)] for cols in indexed_sets if cols)
            if covered:
                continue
            index_name = "idx_" + table["name"] + "_" + "_".join(rel["source_columns"])
            recommendations.append({
                "constraint": rel["name"],
                "table": table["name"],
                "columns": rel["source_columns"],
                "target_table": rel["target_table"],
                "index_name": index_name,
                "reason": "建议结合真实查询计划评估；常用于连接、筛选及父记录删除校验。",
            })
    return recommendations


def generate_index_recommendations_sql(recommendations: list[dict[str, Any]]) -> str:
    lines = [
        "-- ADC Nexus 外键索引候选清单",
        "-- 这些语句是目标设计建议，不代表当前数据库已经实现。",
        "-- 上线前应以真实查询、写入开销与 EXPLAIN QUERY PLAN 结果复核。",
        "",
    ]
    for item in recommendations:
        columns = ", ".join(quote_identifier(column) for column in item["columns"])
        lines.append(
            f"CREATE INDEX IF NOT EXISTS {quote_identifier(item['index_name'])} "
            f"ON {quote_identifier(item['table'])} ({columns});"
        )
    return "\n".join(lines) + "\n"


def card_size(table: dict[str, Any], detailed: bool) -> tuple[int, int, int, int, int]:
    width = 760 if detailed else 690
    header = 54 if detailed else 40
    row = 28 if detailed else 19
    font = 17 if detailed else 12
    return width, header + row * len(table["columns"]) + 12, header, row, font


def pack_tables(tables: list[dict[str, Any]], x: int, y: int, columns: int, detailed: bool, gap_x: int = 36, gap_y: int = 36) -> tuple[dict[str, tuple[int, int, int, int]], int, int]:
    width = card_size(tables[0], detailed)[0] if tables else (760 if detailed else 690)
    cursors = [y] * columns
    positions: dict[str, tuple[int, int, int, int]] = {}
    for table in tables:
        column = min(range(columns), key=lambda index: cursors[index])
        card_w, card_h, _, _, _ = card_size(table, detailed)
        tx = x + column * (width + gap_x)
        ty = cursors[column]
        positions[table["name"]] = (tx, ty, card_w, card_h)
        cursors[column] = ty + card_h + gap_y
    return positions, columns * width + (columns - 1) * gap_x, max(cursors) - y


def panorama_layout(model: dict[str, Any]) -> dict[str, Any]:
    tables = {table["name"]: table for table in model["tables"]}
    # A three-by-three sheet keeps table text legible when the vector PDF is
    # inspected at the page level and matches the reference ERD aspect ratio.
    panel_w, cols, outer, panel_gap = 2260, 3, 70, 65
    domain_specs = []
    for domain in model["domains"]:
        domain_tables = [tables[name] for name in domain["tables"]]
        positions, _, needed = pack_tables(domain_tables, 0, 0, 3, False, 38, 30)
        # Keep enough clearance for cross-domain routing without leaving the
        # very large empty colour blocks produced by a fixed 1750 px floor.
        domain_specs.append((domain, positions, max(needed + 130, 950)))
    row_heights = []
    for row in range(math.ceil(len(domain_specs) / cols)):
        row_heights.append(max(spec[2] for spec in domain_specs[row * cols:(row + 1) * cols]))
    global_positions: dict[str, tuple[int, int, int, int]] = {}
    panels = []
    y = 180
    for row, row_h in enumerate(row_heights):
        for col in range(cols):
            index = row * cols + col
            if index >= len(domain_specs):
                break
            domain, local, needed = domain_specs[index]
            px = outer + col * (panel_w + panel_gap)
            py = y
            panel_h = row_h
            panels.append({"domain": domain, "rect": (px, py, panel_w, panel_h)})
            for table_name, (tx, ty, tw, th) in local.items():
                global_positions[table_name] = (px + 58 + tx, py + 78 + ty, tw, th)
        y += row_h + panel_gap
    width = outer * 2 + cols * panel_w + (cols - 1) * panel_gap
    height = y + 155
    return {"width": width, "height": height, "positions": global_positions, "panels": panels, "detailed": False}


def domain_layout(model: dict[str, Any], domain: dict[str, Any]) -> dict[str, Any]:
    table_map = {table["name"]: table for table in model["tables"]}
    tables = [table_map[name] for name in domain["tables"]]
    cols = 3 if len(tables) >= 5 else 2
    positions, content_w, content_h = pack_tables(tables, 80, 165, cols, True, 90, 54)
    return {
        "width": max(content_w + 160, 1900), "height": content_h + 270,
        "positions": positions, "panels": [{"domain": domain, "rect": (25, 110, max(content_w + 110, 1850), content_h + 100)}],
        "detailed": True, "domain_id": domain["id"],
    }


def route_relation(source: tuple[int, int, int, int], target: tuple[int, int, int, int], offset: int = 0) -> list[tuple[float, float]]:
    sx, sy, sw, sh = source
    tx, ty, tw, th = target
    scx, scy = sx + sw / 2, sy + sh / 2
    tcx, tcy = tx + tw / 2, ty + th / 2
    if abs(tcx - scx) >= abs(tcy - scy):
        start = (sx + sw, scy) if tcx >= scx else (sx, scy)
        end = (tx, tcy) if tcx >= scx else (tx + tw, tcy)
        mid = (start[0] + end[0]) / 2 + offset
        return [start, (mid, start[1]), (mid, end[1]), end]
    start = (scx, sy + sh) if tcy >= scy else (scx, sy)
    end = (tcx, ty) if tcy >= scy else (tcx, ty + th)
    mid = (start[1] + end[1]) / 2 + offset
    return [start, (start[0], mid), (end[0], mid), end]


def _compress_orthogonal(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    cleaned: list[tuple[float, float]] = []
    for point in points:
        if not cleaned or point != cleaned[-1]:
            cleaned.append(point)
    result: list[tuple[float, float]] = []
    for point in cleaned:
        if len(result) >= 2:
            a, b = result[-2], result[-1]
            if (a[0] == b[0] == point[0]) or (a[1] == b[1] == point[1]):
                result[-1] = point
                continue
        result.append(point)
    return result


def route_relation_avoiding(
    source: tuple[int, int, int, int],
    target: tuple[int, int, int, int],
    obstacles: list[tuple[int, int, int, int]],
    offset: int = 0,
) -> list[tuple[float, float]]:
    """Find a clean orthogonal route that does not pass through table cards."""
    clearance = 18

    def ports(rect: tuple[int, int, int, int], spread: int) -> list[tuple[tuple[float, float], tuple[float, float], str]]:
        x, y, w, h = rect
        cy = min(y + h - 24, max(y + 24, y + h / 2 + spread))
        cx = min(x + w - 24, max(x + 24, x + w / 2 + spread))
        return [
            ((x, cy), (x - clearance, cy), "H"),
            ((x + w, cy), (x + w + clearance, cy), "H"),
            ((cx, y), (cx, y - clearance), "V"),
            ((cx, y + h), (cx, y + h + clearance), "V"),
        ]

    inflated = [(x - clearance, y - clearance, w + 2 * clearance, h + 2 * clearance) for x, y, w, h in obstacles]

    def blocked_point(point: tuple[float, float]) -> bool:
        px, py = point
        return any(x < px < x + w and y < py < y + h for x, y, w, h in inflated)

    def blocked_segment(a: tuple[float, float], b: tuple[float, float]) -> bool:
        x1, y1 = a; x2, y2 = b
        for x, y, w, h in inflated:
            if x1 == x2 and x < x1 < x + w and max(min(y1, y2), y) < min(max(y1, y2), y + h):
                return True
            if y1 == y2 and y < y1 < y + h and max(min(x1, x2), x) < min(max(x1, x2), x + w):
                return True
        return False

    best: tuple[float, list[tuple[float, float]]] | None = None
    for start, start_out, start_dir in ports(source, offset):
        for end, end_out, end_dir in ports(target, -offset):
            xs = {start_out[0], end_out[0]}
            ys = {start_out[1], end_out[1]}
            for x, y, w, h in inflated:
                xs.update((x, x + w)); ys.update((y, y + h))
            nodes = {(x, y) for x in xs for y in ys if not blocked_point((x, y))}
            nodes.update((start_out, end_out))
            graph: dict[tuple[float, float], list[tuple[tuple[float, float], str, float]]] = {node: [] for node in nodes}
            by_y: dict[float, list[tuple[float, float]]] = {}
            by_x: dict[float, list[tuple[float, float]]] = {}
            for node in nodes:
                by_y.setdefault(node[1], []).append(node)
                by_x.setdefault(node[0], []).append(node)
            for row in by_y.values():
                row.sort()
                for a, b in zip(row, row[1:]):
                    if not blocked_segment(a, b):
                        distance = abs(b[0] - a[0]); graph[a].append((b, "H", distance)); graph[b].append((a, "H", distance))
            for column in by_x.values():
                column.sort(key=lambda point: point[1])
                for a, b in zip(column, column[1:]):
                    if not blocked_segment(a, b):
                        distance = abs(b[1] - a[1]); graph[a].append((b, "V", distance)); graph[b].append((a, "V", distance))

            queue: list[tuple[float, tuple[float, float], str]] = [(0.0, start_out, start_dir)]
            distances = {(start_out, start_dir): 0.0}
            previous: dict[tuple[tuple[float, float], str], tuple[tuple[float, float], str]] = {}
            finish: tuple[tuple[float, float], str] | None = None
            while queue:
                cost, node, direction = heapq.heappop(queue)
                if cost != distances.get((node, direction)):
                    continue
                if node == end_out:
                    finish = (node, direction)
                    break
                for neighbour, next_dir, length in graph[node]:
                    next_cost = cost + length + (70 if next_dir != direction else 0)
                    state = (neighbour, next_dir)
                    if next_cost < distances.get(state, float("inf")):
                        distances[state] = next_cost
                        previous[state] = (node, direction)
                        heapq.heappush(queue, (next_cost, neighbour, next_dir))
            if finish is None:
                continue
            route_nodes = [finish[0]]
            state = finish
            while state[0] != start_out:
                state = previous[state]
                route_nodes.append(state[0])
            route_nodes.reverse()
            total = distances[finish] + (70 if finish[1] != end_dir else 0)
            candidate = _compress_orthogonal([start, start_out, *route_nodes[1:-1], end_out, end])
            if best is None or total < best[0]:
                best = (total, candidate)
    return best[1] if best else route_relation(source, target, offset)


def scene_data(model: dict[str, Any], layout: dict[str, Any], table_names: set[str] | None = None) -> dict[str, Any]:
    selected = table_names or set(layout["positions"])
    tables = [table for table in model["tables"] if table["name"] in selected]
    rels = [rel for rel in model["relationships"] if rel["source_table"] in selected and rel["target_table"] in selected]
    domain_by_table = {table["name"]: table["domain_id"] for table in model["tables"]}
    routes = []
    for index, rel in enumerate(rels):
        route_obstacles = list(layout["positions"].values())
        points = (
            route_relation_avoiding(
                layout["positions"][rel["source_table"]],
                layout["positions"][rel["target_table"]],
                route_obstacles,
                ((index % 7) - 3) * 7,
            )
            if layout["detailed"] else
            route_relation(layout["positions"][rel["source_table"]], layout["positions"][rel["target_table"]], ((index % 7) - 3) * 7)
        )
        routes.append({
            "relation": rel,
            "points": points,
            "cross_domain": domain_by_table[rel["source_table"]] != domain_by_table[rel["target_table"]],
        })
    return {**layout, "tables": tables, "routes": routes}


def svg_text(x: float, y: float, text: str, size: int, weight: str = "400", fill: str = "#263238", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Microsoft YaHei,sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{html.escape(text)}</text>'


def ellipsize(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:max(1, limit - 1)] + "…"


def column_type_label(column: dict[str, Any]) -> str:
    """Compact field constraints for print-readable table cards."""
    flags = ["NULL" if column["nullable"] else "NN"]
    if column.get("indexes"):
        flags.append("IDX")
    if column.get("default") is not None:
        flags.append("DEF")
    return column["type"] + " · " + " · ".join(flags)


def render_svg(scene: dict[str, Any], model: dict[str, Any], output: Path, title: str) -> None:
    width, height = scene["width"], scene["height"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5F6B76"/></marker></defs>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#F4F5F6"/>',
        svg_text(70, 72, title, 36 if not scene["detailed"] else 32, "700", "#1F2A33"),
        svg_text(70, 112, f"{model['counts']['tables']} 张表 · {model['counts']['columns']} 个字段 · {model['counts']['foreign_keys']} 条外键", 19, "400", "#58636D"),
    ]
    for panel in scene["panels"]:
        x, y, w, h = panel["rect"]
        domain = panel["domain"]
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="38" fill="{domain["color"]}" fill-opacity="0.72" stroke="#87929B" stroke-width="2" stroke-dasharray="12 8"/>')
        parts.append(svg_text(x + 28, y + 42, domain["name"], 25 if scene["detailed"] else 21, "700", "#27323A"))
    for route in scene["routes"]:
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in route["points"])
        stroke = "#A1AAB2" if route["cross_domain"] else "#5F6B76"
        opacity = ".65" if route["cross_domain"] else ".88"
        parts.append(f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="2.2" opacity="{opacity}" marker-end="url(#arrow)"/>')
    table_map = {table["name"]: table for table in scene["tables"]}
    for table_name, (x, y, w, h) in scene["positions"].items():
        if table_name not in table_map:
            continue
        table = table_map[table_name]
        _, _, header, row_h, font_size = card_size(table, scene["detailed"])
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#FFFFFF" stroke="#35414A" stroke-width="1.8"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{header}" rx="3" fill="#E8EEF3" stroke="#35414A" stroke-width="1.8"/>')
        title_text = f"{table['name'].upper()}（{table['label']}）"
        parts.append(svg_text(x + 12, y + header * .68, ellipsize(title_text, 54 if scene["detailed"] else 45), font_size + 2, "700", "#172129"))
        for index, column in enumerate(table["columns"]):
            ry = y + header + index * row_h
            if index:
                parts.append(f'<line x1="{x}" y1="{ry}" x2="{x+w}" y2="{ry}" stroke="#E6E9EB" stroke-width="1"/>')
            marker = "PK/FK" if column["pk"] and column["fk_targets"] else "PK" if column["pk"] else "FK" if column["fk_targets"] else ""
            marker_color = "#A46F00" if column["pk"] else "#087EA4"
            if marker:
                parts.append(svg_text(x + 10, ry + row_h * .72, marker, font_size - 1, "700", marker_color))
            name_x = x + (72 if scene["detailed"] else 58)
            field = column["name"]
            target = ""
            if column["fk_targets"]:
                target = " → " + ",".join(t["table"] for t in column["fk_targets"])
            parts.append(svg_text(name_x, ry + row_h * .72, ellipsize(field + target, 49 if scene["detailed"] else 42), font_size, "400", "#27323A"))
            parts.append(svg_text(x + w - 10, ry + row_h * .72, column_type_label(column), font_size - 1, "400", "#62717D", "end"))
    parts.append(svg_text(70, height - 60, "图例：PK 主键｜FK 外键｜NN 不可空｜NULL 可空｜IDX 索引｜DEF 默认值｜箭头指向被引用父表", 18, "400", "#43515C"))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8", newline='\n')


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size=size)


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def scaled_point(point: tuple[float, float], scale: float) -> tuple[int, int]:
    return round(point[0] * scale), round(point[1] * scale)


def render_png(scene: dict[str, Any], model: dict[str, Any], output: Path, title: str) -> None:
    max_width = 8200 if not scene["detailed"] else 5200
    scale = min(1.0, max_width / scene["width"])
    image = Image.new("RGB", (round(scene["width"] * scale), round(scene["height"] * scale)), "#F4F5F6")
    draw = ImageDraw.Draw(image)
    def rect(box, fill, outline=None, width=1, radius=0):
        b = tuple(round(v * scale) for v in box)
        if radius:
            draw.rounded_rectangle(b, radius=round(radius * scale), fill=fill, outline=outline, width=max(1, round(width * scale)))
        else:
            draw.rectangle(b, fill=fill, outline=outline, width=max(1, round(width * scale)))
    def text_xy(x, y, value, size, fill="#263238", bold=False, anchor=None):
        draw.text((round(x * scale), round(y * scale)), value, font=font(max(8, round(size * scale)), bold), fill=fill, anchor=anchor)
    text_xy(70, 30, title, 36 if not scene["detailed"] else 32, "#1F2A33", True)
    text_xy(70, 82, f"{model['counts']['tables']} 张表 · {model['counts']['columns']} 个字段 · {model['counts']['foreign_keys']} 条外键", 19, "#58636D")
    for panel in scene["panels"]:
        x, y, w, h = panel["rect"]
        rect((x, y, x + w, y + h), panel["domain"]["color"], "#87929B", 2, 38)
        text_xy(x + 28, y + 14, panel["domain"]["name"], 25 if scene["detailed"] else 21, "#27323A", True)
    for route in scene["routes"]:
        pts = [scaled_point(p, scale) for p in route["points"]]
        color = "#A1AAB2" if route["cross_domain"] else "#5F6B76"
        draw.line(pts, fill=color, width=max(1, round(2.2 * scale)), joint="curve")
        if len(pts) >= 2:
            x2, y2 = pts[-1]; x1, y1 = pts[-2]
            angle = math.atan2(y2 - y1, x2 - x1); length = max(7, round(10 * scale))
            left = (x2 - length * math.cos(angle - .55), y2 - length * math.sin(angle - .55))
            right = (x2 - length * math.cos(angle + .55), y2 - length * math.sin(angle + .55))
            draw.polygon([(x2, y2), left, right], fill=color)
    table_map = {table["name"]: table for table in scene["tables"]}
    for table_name, (x, y, w, h) in scene["positions"].items():
        table = table_map.get(table_name)
        if not table:
            continue
        _, _, header, row_h, font_size = card_size(table, scene["detailed"])
        rect((x, y, x + w, y + h), "#FFFFFF", "#35414A", 2)
        rect((x, y, x + w, y + header), "#E8EEF3", "#35414A", 2)
        text_xy(x + 12, y + 10, ellipsize(f"{table['name'].upper()}（{table['label']}）", 54 if scene["detailed"] else 45), font_size + 2, "#172129", True)
        for index, column in enumerate(table["columns"]):
            ry = y + header + index * row_h
            if index:
                draw.line((round(x * scale), round(ry * scale), round((x + w) * scale), round(ry * scale)), fill="#E6E9EB", width=1)
            marker = "PK/FK" if column["pk"] and column["fk_targets"] else "PK" if column["pk"] else "FK" if column["fk_targets"] else ""
            if marker:
                text_xy(x + 10, ry + 2, marker, font_size - 1, "#A46F00" if column["pk"] else "#087EA4", True)
            target = " → " + ",".join(t["table"] for t in column["fk_targets"]) if column["fk_targets"] else ""
            text_xy(x + (72 if scene["detailed"] else 58), ry + 2, ellipsize(column["name"] + target, 49 if scene["detailed"] else 42), font_size, "#27323A")
            text_xy(x + w - 10, ry + 2, column_type_label(column), font_size - 1, "#62717D", anchor="ra")
    text_xy(70, scene["height"] - 85, "图例：PK 主键｜FK 外键｜NN 不可空｜NULL 可空｜IDX 索引｜DEF 默认值｜箭头指向被引用父表", 18, "#43515C")
    image.save(output, optimize=True)


def register_pdf_fonts() -> None:
    if "CN" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CN", str(FONT_REGULAR)))
        pdfmetrics.registerFont(TTFont("CN-Bold", str(FONT_BOLD)))


def render_scene_to_pdf(scene: dict[str, Any], model: dict[str, Any], output: Path, title: str) -> None:
    register_pdf_fonts()
    scale = min(0.62, 7200 / scene["width"])
    page_size = (scene["width"] * scale, scene["height"] * scale)
    c = pdfcanvas.Canvas(str(output), pagesize=page_size, pageCompression=1)
    c.scale(scale, scale)
    c.setFillColor(colors.HexColor("#F4F5F6")); c.rect(0, 0, scene["width"], scene["height"], fill=1, stroke=0)
    def txt(x, y_top, value, size, color="#263238", bold=False, align="left"):
        c.setFont("CN-Bold" if bold else "CN", size); c.setFillColor(colors.HexColor(color))
        baseline = scene["height"] - y_top - size
        if align == "right": c.drawRightString(x, baseline, value)
        else: c.drawString(x, baseline, value)
    txt(70, 28, title, 36 if not scene["detailed"] else 32, "#1F2A33", True)
    txt(70, 82, f"{model['counts']['tables']} 张表 · {model['counts']['columns']} 个字段 · {model['counts']['foreign_keys']} 条外键", 19, "#58636D")
    for panel in scene["panels"]:
        x, y, w, h = panel["rect"]
        c.setFillColor(colors.HexColor(panel["domain"]["color"])); c.setStrokeColor(colors.HexColor("#87929B")); c.setLineWidth(2)
        c.roundRect(x, scene["height"] - y - h, w, h, 38, fill=1, stroke=1)
        txt(x + 28, y + 14, panel["domain"]["name"], 25 if scene["detailed"] else 21, "#27323A", True)
    for route in scene["routes"]:
        pts = route["points"]; c.setStrokeColor(colors.HexColor("#A1AAB2" if route["cross_domain"] else "#5F6B76")); c.setLineWidth(2.2)
        path = c.beginPath(); path.moveTo(pts[0][0], scene["height"] - pts[0][1])
        for x, y in pts[1:]: path.lineTo(x, scene["height"] - y)
        c.drawPath(path, fill=0, stroke=1)
        if len(pts) >= 2:
            x2, y2 = pts[-1]; x1, y1 = pts[-2]; angle = math.atan2(y2 - y1, x2 - x1); length = 10
            left = (x2 - length * math.cos(angle - .55), y2 - length * math.sin(angle - .55))
            right = (x2 - length * math.cos(angle + .55), y2 - length * math.sin(angle + .55))
            p = c.beginPath(); p.moveTo(x2, scene["height"] - y2); p.lineTo(left[0], scene["height"] - left[1]); p.lineTo(right[0], scene["height"] - right[1]); p.close()
            c.drawPath(p, fill=1, stroke=0)
    table_map = {table["name"]: table for table in scene["tables"]}
    for table_name, (x, y, w, h) in scene["positions"].items():
        table = table_map.get(table_name)
        if not table: continue
        _, _, header, row_h, font_size = card_size(table, scene["detailed"])
        bottom = scene["height"] - y - h
        c.setFillColor(colors.white); c.setStrokeColor(colors.HexColor("#35414A")); c.setLineWidth(1.8); c.rect(x, bottom, w, h, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#E8EEF3")); c.rect(x, scene["height"] - y - header, w, header, fill=1, stroke=1)
        txt(x + 12, y + 10, ellipsize(f"{table['name'].upper()}（{table['label']}）", 54 if scene["detailed"] else 45), font_size + 2, "#172129", True)
        for index, column in enumerate(table["columns"]):
            ry = y + header + index * row_h
            if index:
                c.setStrokeColor(colors.HexColor("#E6E9EB")); c.setLineWidth(1); c.line(x, scene["height"] - ry, x + w, scene["height"] - ry)
            marker = "PK/FK" if column["pk"] and column["fk_targets"] else "PK" if column["pk"] else "FK" if column["fk_targets"] else ""
            if marker: txt(x + 10, ry + 2, marker, font_size - 1, "#A46F00" if column["pk"] else "#087EA4", True)
            target = " → " + ",".join(t["table"] for t in column["fk_targets"]) if column["fk_targets"] else ""
            txt(x + (72 if scene["detailed"] else 58), ry + 2, ellipsize(column["name"] + target, 49 if scene["detailed"] else 42), font_size, "#27323A")
            txt(x + w - 10, ry + 2, column_type_label(column), font_size - 1, "#62717D", align="right")
    txt(70, scene["height"] - 85, "图例：PK 主键｜FK 外键｜NN 不可空｜NULL 可空｜IDX 索引｜DEF 默认值｜箭头指向被引用父表", 18, "#43515C")
    c.showPage(); c.save()


def drawio_label(table: dict[str, Any]) -> str:
    rows = []
    for column in table["columns"]:
        marker = "PK/FK" if column["pk"] and column["fk_targets"] else "PK" if column["pk"] else "FK" if column["fk_targets"] else ""
        color = "#A46F00" if column["pk"] else "#087EA4"
        target = " → " + ",".join(t["table"] for t in column["fk_targets"]) if column["fk_targets"] else ""
        rows.append(f'<tr><td style="color:{color};font-weight:bold;width:52px">{marker}</td><td>{html.escape(column["name"] + target)}</td><td style="color:#62717D;text-align:right">{html.escape(column_type_label(column))}</td></tr>')
    return f'<table style="width:100%;border-collapse:collapse;font-family:Arial,Microsoft YaHei;font-size:12px"><tr><th colspan="3" style="text-align:left;background:#E8EEF3;padding:6px">{html.escape(table["name"].upper())}（{html.escape(table["label"])}）</th></tr>{"".join(rows)}</table>'


def render_drawio(scene: dict[str, Any], output: Path, title: str) -> None:
    mxfile = ET.Element("mxfile", host="app.diagrams.net", modified="2026-10-14T00:00:00.000Z", agent="Codex relational data design", version="24.7.17")
    diagram = ET.SubElement(mxfile, "diagram", name=title, id="erd")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="900", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="0", pageScale="1", pageWidth=str(scene["width"]), pageHeight=str(scene["height"]), math="0", shadow="0")
    root = ET.SubElement(model, "root"); ET.SubElement(root, "mxCell", id="0"); ET.SubElement(root, "mxCell", id="1", parent="0")
    for index, panel in enumerate(scene["panels"]):
        x, y, w, h = panel["rect"]
        cell = ET.SubElement(root, "mxCell", id=f"domain-{index}", value=panel["domain"]["name"], style=f"rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingTop=12;spacingLeft=16;fontStyle=1;fontSize=20;fillColor={panel['domain']['color']};opacity=72;strokeColor=#87929B;dashed=1;dashPattern=8 6;", vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})
    table_map = {table["name"]: table for table in scene["tables"]}
    for table_name, (x, y, w, h) in scene["positions"].items():
        if table_name not in table_map: continue
        cell = ET.SubElement(root, "mxCell", id=f"table-{table_name}", value=drawio_label(table_map[table_name]), style="shape=rectangle;html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#35414A;align=left;verticalAlign=top;spacing=0;", vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})
    for index, route in enumerate(scene["routes"]):
        rel = route["relation"]
        edge = ET.SubElement(root, "mxCell", id=f"edge-{index}", value="", style=f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={'#A1AAB2' if route['cross_domain'] else '#5F6B76'};strokeWidth=2;endArrow=block;endFill=1;", edge="1", parent="1", source=f"table-{rel['source_table']}", target=f"table-{rel['target_table']}")
        ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})
    output.write_bytes(ET.tostring(mxfile, encoding="utf-8", xml_declaration=True))


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def generate_ddl(model: dict[str, Any]) -> str:
    statements = ["PRAGMA foreign_keys = ON;", ""]
    for table in model["tables"]:
        lines = []
        simple_pk = len(table["primary_key"]) == 1
        for column in table["columns"]:
            parts = [quote_identifier(column["name"]), column["type"]]
            if simple_pk and column["pk"]:
                parts.append("PRIMARY KEY")
                if column["autoincrement"]: parts.append("AUTOINCREMENT")
            if not column["nullable"]: parts.append("NOT NULL")
            if column["default"] is not None: parts.append("DEFAULT " + sql_default(column["default"]))
            lines.append("  " + " ".join(parts))
        if len(table["primary_key"]) > 1:
            lines.append("  PRIMARY KEY (" + ", ".join(quote_identifier(c) for c in table["primary_key"]) + ")")
        for rel in table["relationships"]:
            lines.append(
                "  FOREIGN KEY (" + ", ".join(quote_identifier(c) for c in rel["source_columns"]) + ") REFERENCES " +
                quote_identifier(rel["target_table"]) + " (" + ", ".join(quote_identifier(c) for c in rel["target_columns"]) + ")" +
                f" ON UPDATE {rel['on_update'].upper()} ON DELETE {rel['on_delete'].upper()}"
            )
        statements.append(f"CREATE TABLE {quote_identifier(table['name'])} (\n" + ",\n".join(lines) + "\n);")
        for idx in table["indexes"]:
            unique = "UNIQUE " if idx.get("isUnique") else ""
            statements.append(f"CREATE {unique}INDEX {quote_identifier(idx['name'])} ON {quote_identifier(table['name'])} (" + ", ".join(quote_identifier(c) for c in idx.get("columns", [])) + ");")
        statements.append("")
    return "\n".join(statements)


def paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(html.escape(safe(text)).replace("\n", "<br/>"), style)


class ReportDoc(BaseDocTemplate):
    pass


def build_report(model: dict[str, Any], domain_pngs: dict[str, Path], output: Path,
                 index_recommendations: list[dict[str, Any]]) -> None:
    register_pdf_fonts()
    margin = 15 * mm
    portrait_frame = Frame(margin, 17 * mm, A4[0] - 2 * margin, A4[1] - 34 * mm, id="portrait")
    a4l = landscape(A4); landscape_frame = Frame(margin, 15 * mm, a4l[0] - 2 * margin, a4l[1] - 30 * mm, id="landscape")
    a3l = landscape(A3); a3_frame = Frame(15 * mm, 15 * mm, a3l[0] - 30 * mm, a3l[1] - 30 * mm, id="a3")
    project = model["project"]
    def page_decor(c, doc):
        width, height = c._pagesize
        c.saveState(); c.setStrokeColor(colors.HexColor("#BCC4CA")); c.setLineWidth(.4)
        c.line(15 * mm, height - 12 * mm, width - 15 * mm, height - 12 * mm)
        c.setFont("CN", 8); c.setFillColor(colors.HexColor("#4E5A63"))
        c.drawString(15 * mm, height - 9 * mm, project["system_name"])
        c.drawRightString(width - 15 * mm, height - 9 * mm, project["subtitle"])
        c.drawString(15 * mm, 8 * mm, f"{project.get('author','')}  {project.get('student_id','')}")
        c.drawCentredString(width / 2, 8 * mm, str(doc.page)); c.restoreState()
    doc = ReportDoc(str(output), pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=17 * mm, bottomMargin=17 * mm, title=f"{project['system_name']} {project['subtitle']}", author=project.get("author", ""))
    doc.addPageTemplates([
        PageTemplate(id="A4P", pagesize=A4, frames=[portrait_frame], onPage=page_decor),
        PageTemplate(id="A4L", pagesize=a4l, frames=[landscape_frame], onPage=page_decor),
        PageTemplate(id="A3L", pagesize=a3l, frames=[a3_frame], onPage=page_decor),
    ])
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCN", parent=styles["Title"], fontName="CN-Bold", fontSize=25, leading=34, textColor=colors.HexColor("#1F2A33"), alignment=TA_CENTER, spaceAfter=10 * mm)
    subtitle = ParagraphStyle("SubtitleCN", parent=styles["Normal"], fontName="CN", fontSize=13, leading=20, textColor=colors.HexColor("#54616B"), alignment=TA_CENTER)
    h1 = ParagraphStyle("H1CN", parent=styles["Heading1"], fontName="CN-Bold", fontSize=17, leading=23, textColor=colors.HexColor("#20384C"), spaceBefore=6 * mm, spaceAfter=4 * mm)
    h2 = ParagraphStyle("H2CN", parent=styles["Heading2"], fontName="CN-Bold", fontSize=12, leading=17, textColor=colors.HexColor("#2F4F65"), spaceBefore=4 * mm, spaceAfter=2 * mm)
    body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="CN", fontSize=9.5, leading=15, textColor=colors.HexColor("#2A333A"), firstLineIndent=18, spaceAfter=2 * mm)
    small = ParagraphStyle("SmallCN", parent=body, fontSize=7.2, leading=9, firstLineIndent=0, spaceAfter=0)
    tiny = ParagraphStyle("TinyCN", parent=body, fontSize=6.4, leading=7.7, firstLineIndent=0, spaceAfter=0)
    story = [Spacer(1, 30 * mm), Paragraph(project["system_name"], title), Paragraph(project["subtitle"], subtitle), Spacer(1, 18 * mm)]
    summary_data = [
        ["作者", project.get("author", ""), "学号", project.get("student_id", "")],
        ["数据库", project.get("database", "SQLite / D1"), "建模日期", project.get("as_of", "")],
        ["表数量", str(model["counts"]["tables"]), "字段数量", str(model["counts"]["columns"])],
        ["外键数量", str(model["counts"]["foreign_keys"]), "业务簇", str(model["counts"]["domains"])],
        ["现有索引", str(model["counts"]["indexes"]), "索引候选", str(len(index_recommendations))],
    ]
    summary = Table([[paragraph(v, small) for v in row] for row in summary_data], colWidths=[25 * mm, 50 * mm, 25 * mm, 50 * mm])
    summary.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#AEB7BE")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF3")), ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E8EEF3")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [summary, Spacer(1, 20 * mm), Paragraph("独立审阅稿：确认后再并入最终系统分析与设计报告", subtitle), PageBreak()]
    story += [Paragraph("1 参考图方法与本系统取舍", h1), Paragraph("两份参考 ERD 采用超宽单页、白色表卡、键标记、正交关系线和浅色业务簇，适合展示大型 schema 的覆盖范围。其不足是未显示数据类型、可空性、默认值、唯一约束和删除策略。因此本稿保留其全景组织方式，同时以字段级网格和关系清单补全数据库语义。", body), Paragraph("本模型直接读取 ADC Nexus 当前 Drizzle SQLite 快照。61 张表均已存在于当前实现快照，并按真实职责分为九个业务簇；没有为了达到数量要求而增加空壳表。现有结构与目标增强严格分开：当前快照中的 119 条外键按原样呈现，另外三条可证明的关系仅列为约束增强候选，不伪装成已经实施。保险理赔、法定税务开票和器械灭菌追踪仍在报告范围之外。", body), Paragraph("2 统计与业务簇目录", h1)]
    domain_rows = [["序号", "业务簇", "表数", "主要责任"]]
    table_map = {table["name"]: table for table in model["tables"]}
    for idx, domain in enumerate(model["domains"], 1):
        domain_rows.append([str(idx), domain["name"], str(len(domain["tables"])), domain.get("description", "")])
    dt = Table([[paragraph(v, small) for v in row] for row in domain_rows], colWidths=[12 * mm, 37 * mm, 15 * mm, 100 * mm], repeatRows=1)
    dt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#AEB7BE")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [dt, Paragraph("2.1 物理字段与命名约定", h2)]
    convention_rows = [
        ["主题", "约定", "说明"],
        ["主键", "id 或稳定复合键", "内部主键保持稳定；业务编号另设唯一约束。"],
        ["外键", "<父概念>_id", "子表字段指向父表主键；可空性与删除策略以关系清单为准。"],
        ["金额", "*_fen / INTEGER", "以人民币分为最小单位，避免浮点舍入误差。"],
        ["时间点", "*_at / TEXT", "保存可排序的 ISO 8601 时间；展示时按诊所时区转换。"],
        ["业务日期", "*_on、*_date / TEXT", "仅表示当地业务日期，不与瞬时时间混用。"],
        ["结构化快照", "*_json / TEXT", "只用于不可稳定预定义的载荷或核算快照；可查询关系仍使用正规表。"],
        ["双语文本", "*_zh、*_en", "中文与英文内容分列，物理字段名保持英文 snake_case。"],
    ]
    ct = Table([[paragraph(v, small) for v in row] for row in convention_rows],
               colWidths=[25 * mm, 49 * mm, 90 * mm], repeatRows=1)
    ct.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#AEB7BE")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 3),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [ct, Paragraph("2.2 数据表目录", h2)]
    domain_names = {table_name: domain["name"] for domain in model["domains"] for table_name in domain["tables"]}
    catalog_rows = [["序", "业务簇", "物理表", "字段", "外键", "职责"]]
    for index, table in enumerate(model["tables"], 1):
        catalog_rows.append([
            str(index), domain_names[table["name"]], table["name"], str(len(table["columns"])),
            str(len(table["relationships"])), f"{table['label']}：{table['description']}",
        ])
    catalog = Table([[paragraph(v, tiny) for v in row] for row in catalog_rows],
                    colWidths=[9 * mm, 28 * mm, 39 * mm, 12 * mm, 12 * mm, 64 * mm],
                    repeatRows=1, splitByRow=1)
    catalog.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")),
                                 ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                 ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#AEB7BE")),
                                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8F9")]),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                 ("TOPPADDING", (0, 0), (-1, -1), 2),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [catalog, Paragraph("3 跨表业务完整性规则", h1)]
    rule_rows = [["编号", "规则", "关联表", "执行层", "说明"]]
    for rule in model["business_rules"]:
        rule_rows.append([rule["id"], rule["name"], "、".join(rule.get("tables", [])), rule["enforcement"], rule["statement"]])
    rt = Table([[paragraph(v, tiny) for v in row] for row in rule_rows], colWidths=[15 * mm, 32 * mm, 45 * mm, 27 * mm, 48 * mm], repeatRows=1)
    rt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#AEB7BE")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [rt, Paragraph("3.1 当前结构与关系增强候选", h2),
              Paragraph("下列关系具有明确的主数据指向，但当前实现快照尚未声明数据库外键。为避免把目标设计冒充成现状，本稿不把它们计入 119 条现有外键，也不直接改写现有 DDL；在后续迁移中应单独评审数据清洗、删除策略和兼容性。", body)]
    recommendation_rows = [["编号", "当前字段", "建议目标", "基数", "建议动作", "依据"]]
    for item in model.get("relationship_recommendations", []):
        recommendation_rows.append([
            item["id"], item["source"], item["target"], item["cardinality"],
            item["suggested_action"], item["reason"],
        ])
    rr = Table([[paragraph(v, tiny) for v in row] for row in recommendation_rows],
               colWidths=[13 * mm, 33 * mm, 30 * mm, 21 * mm, 39 * mm, 31 * mm],
               repeatRows=1, splitByRow=1)
    rr.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#AEB7BE")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF9EF")]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    migration_rows = [
        ["阶段", "核验项目", "验收要求"],
        ["1 数据盘点", "孤儿值与重复业务键", "新增约束前完成全量扫描；异常记录必须有清洗或豁免依据。"],
        ["2 删除策略", "CASCADE／RESTRICT／SET NULL", "按业务生命周期逐条确认，禁止为便于迁移统一使用级联删除。"],
        ["3 访问性能", "外键前导索引与真实查询", "结合 EXPLAIN QUERY PLAN 和写入成本选择索引，不把候选清单视为已实施结构。"],
        ["4 迁移执行", "备份、回填与事务边界", "迁移可重复执行；失败时可回滚，批量回填不得产生半完成状态。"],
        ["5 数据验证", "foreign_key_check 与关键计数", "迁移后外键检查为零异常，并核对主表、子表及金额汇总计数。"],
        ["6 回归验收", "预约、临床、结算与核算链路", "覆盖正常、并发、取消、退款和期间重开场景，审计轨迹必须连续。"],
    ]
    mt = Table([[paragraph(v, small) for v in row] for row in migration_rows],
               colWidths=[25 * mm, 48 * mm, 94 * mm], repeatRows=1)
    mt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#AEB7BE")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 3),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [rr, Paragraph("3.2 关系约束实施与验收清单", h2), mt]
    for domain_index, domain in enumerate(model["domains"], 1):
        story += [NotAtTopPageBreak(nextTemplate="A3L"), Paragraph(f"{domain_index + 3} {domain['name']}关系图", h1)]
        img = Image.open(domain_pngs[domain["id"]]); iw, ih = img.size
        # Reserve space for the section heading and caption.  Without this
        # allowance ReportLab can push only the caption to a nearly blank page.
        max_w, max_h = a3l[0] - 35 * mm, a3l[1] - 80 * mm
        factor = min(max_w / iw, max_h / ih)
        story += [KeepTogether([
            RLImage(str(domain_pngs[domain["id"]]), width=iw * factor, height=ih * factor),
            Spacer(1, 2 * mm),
            Paragraph(f"图 {domain_index}  {domain['name']}分域关系数据图", subtitle),
        ])]
        story += [NotAtTopPageBreak(nextTemplate="A4L"), Paragraph(f"{domain['name']}字段级数据字典", h1), Paragraph(domain.get("description", ""), body)]
        for table_position, table_name in enumerate(domain["tables"]):
            table = table_map[table_name]
            story.append(KeepTogether([Paragraph(f"{table['name']}（{table['label']}）", h2), Paragraph(table["description"], body)]))
            rows = [["序", "字段名", "类型", "PK", "FK 目标", "可空", "默认值", "索引／约束", "业务含义"]]
            for column in table["columns"]:
                fk = "；".join(f"{t['table']}.{t['column']}" for t in column["fk_targets"])
                constraints = []
                if column["autoincrement"]: constraints.append("AUTO")
                constraints.extend(column["indexes"])
                rows.append([str(column["ordinal"]), column["name"], column["type"], "是" if column["pk"] else "", fk, "是" if column["nullable"] else "否", safe(column["default"]) or "—", "；".join(constraints) or "—", column["description"]])
            data = [[paragraph(v, tiny) for v in row] for row in rows]
            table_flow = Table(data, colWidths=[8 * mm, 31 * mm, 18 * mm, 9 * mm, 39 * mm, 11 * mm, 24 * mm, 45 * mm, 76 * mm], repeatRows=1, splitByRow=1)
            table_flow.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#AEB7BE")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8F9")]), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]))
            story.append(table_flow)
            if table_position < len(domain["tables"]) - 1:
                story.append(Spacer(1, 4 * mm))
    story += [NotAtTopPageBreak(nextTemplate="A4L"), Paragraph("外键关系清单", h1)]
    fk_rows = [["序", "外键约束", "子表字段", "父表字段", "可选性", "ON DELETE", "说明"]]
    for index, rel in enumerate(model["relationships"], 1):
        source_table = table_map[rel["source_table"]]
        column_map = {column["name"]: column for column in source_table["columns"]}
        optional = "可选" if any(column_map[c]["nullable"] for c in rel["source_columns"]) else "必选"
        fk_rows.append([str(index), rel["name"], f"{rel['source_table']}.{'/'.join(rel['source_columns'])}", f"{rel['target_table']}.{'/'.join(rel['target_columns'])}", optional, rel["on_delete"].upper(), "子表外键指向父表；删除策略按现有快照。"])
    ft = Table([[paragraph(v, tiny) for v in row] for row in fk_rows], colWidths=[9 * mm, 64 * mm, 52 * mm, 52 * mm, 18 * mm, 24 * mm, 50 * mm], repeatRows=1, splitByRow=1)
    ft.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#AEB7BE")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8F9")]), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [ft, PageBreakIfNotEmpty(), Paragraph("外键索引优化建议", h1),
              Paragraph("下表列出当前实现中尚未以外键字段作为前导列的索引候选。它们属于目标设计建议，并不表示数据库已经建立这些索引；实施时应结合真实查询频率、写入成本与 SQLite EXPLAIN QUERY PLAN 结果逐项复核。", body)]
    index_rows = [["序", "数据表", "外键字段", "关联父表", "建议索引名", "设计理由"]]
    for index, item in enumerate(index_recommendations, 1):
        index_rows.append([
            str(index), item["table"], " / ".join(item["columns"]), item["target_table"],
            item["index_name"], item["reason"],
        ])
    it = Table([[paragraph(v, tiny) for v in row] for row in index_rows],
               colWidths=[9 * mm, 43 * mm, 46 * mm, 42 * mm, 66 * mm, 62 * mm],
               repeatRows=1, splitByRow=1)
    it.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B5F")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#AEB7BE")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8F9")]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [it, Spacer(1, 4 * mm), Paragraph("范围说明", h1), Paragraph("本稿描述当前关系数据库快照和现有报告范围。短信、微信身份通道仍需正式供应商配置；保险理赔、法定税务开票、自动诊断及器械灭菌追踪未纳入。本稿中的表结构不替代真实诊所的制度确认、隐私影响评估、并发验收和财务口径批准。", body)]
    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    snapshot = Path(args.snapshot).resolve(); config_path = Path(args.config).resolve(); out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True); (out / "domains").mkdir(exist_ok=True)
    model = read_model(snapshot, config_path)
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    audit = validate_model(model, int(config.get("minimum_table_count", 1)))
    if not audit["passed"]:
        raise ValueError("; ".join(audit["issues"]))
    (out / "schema-model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8", newline='\n')
    (out / "schema.sql").write_text(generate_ddl(model), encoding="utf-8", newline='\n')
    index_recommendations = missing_fk_index_recommendations(model)
    (out / "index_recommendations.sql").write_text(
        generate_index_recommendations_sql(index_recommendations), encoding="utf-8"
    , newline='\n')
    panorama = scene_data(model, panorama_layout(model))
    title = f"{model['project']['system_name']} · 全景关系数据图"
    render_svg(panorama, model, out / "ADC_Nexus_全景关系数据图.svg", title)
    render_png(panorama, model, out / "ADC_Nexus_全景关系数据图.png", title)
    render_scene_to_pdf(panorama, model, out / "ADC_Nexus_全景关系数据图.pdf", title)
    render_drawio(panorama, out / "ADC_Nexus_全景关系数据图.drawio", title)
    domain_pngs: dict[str, Path] = {}
    domain_pdfs: list[Path] = []
    for domain in model["domains"]:
        layout = domain_layout(model, domain)
        scene = scene_data(model, layout, set(domain["tables"]))
        base = out / "domains" / f"{domain['id']}_{domain['name']}"
        domain_title = f"{model['project']['system_name']} · {domain['name']}关系数据图"
        render_svg(scene, model, base.with_suffix(".svg"), domain_title)
        render_png(scene, model, base.with_suffix(".png"), domain_title)
        render_scene_to_pdf(scene, model, base.with_suffix(".pdf"), domain_title)
        render_drawio(scene, base.with_suffix(".drawio"), domain_title)
        domain_pngs[domain["id"]] = base.with_suffix(".png")
        domain_pdfs.append(base.with_suffix(".pdf"))
    report_path = out / "ADC_Nexus_D部分_全景与九分域_矢量审阅本.pdf"
    writer = PdfWriter()
    for plate in [out / "ADC_Nexus_全景关系数据图.pdf", *domain_pdfs]:
        # Windows indexing/preview services can briefly lock a newly written
        # PDF. Retry only this read; never accept a missing or partial plate.
        for attempt in range(12):
            try:
                page = PdfReader(plate).pages[0]
                break
            except PermissionError:
                if attempt == 11:
                    raise
                time.sleep(0.25)
        writer.add_page(page)
    with report_path.open("wb") as stream:
        writer.write(stream)
    audit["index_recommendations"] = index_recommendations
    audit["outputs"] = {
        "panorama": ["ADC_Nexus_全景关系数据图.pdf", "ADC_Nexus_全景关系数据图.svg", "ADC_Nexus_全景关系数据图.png", "ADC_Nexus_全景关系数据图.drawio"],
        "domain_diagrams": len(model["domains"]), "domain_vector_pdfs": len(model["domains"]), "report": report_path.name,
        "ddl": "schema.sql", "index_recommendations": "index_recommendations.sql",
    }
    audit["source_hashes"] = {"snapshot": sha256(snapshot), "config": sha256(config_path)}
    (out / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8", newline='\n')
    print(json.dumps({"out": str(out), **model["counts"], "audit_issues": len(audit["issues"]), "audit_warnings": len(audit["warnings"]), "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
