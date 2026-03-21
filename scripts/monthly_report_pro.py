#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monthly report controller for Health-Mate."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def console_print(*args, sep=" ", end="\n", file=sys.stdout, flush=False):
    """Print safely even when the active terminal encoding cannot render CJK text."""
    text = sep.join(str(arg) for arg in args) + end
    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        buffer = getattr(file, "buffer", None)
        if buffer is not None:
            buffer.write(text.encode(encoding, errors="replace"))
        else:
            file.write(text.encode("ascii", errors="backslashreplace").decode("ascii"))
    if flush:
        file.flush()


print = console_print

from health_report_pro import (
    REPORTS_DIR,
    build_multi_condition_tip,
    build_score_report,
    find_custom_section_items,
    force_config_locale,
    generation_source_label,
    has_tavily_api_key,
    get_condition_standards,
    get_conditions_display_name,
    get_generation_settings,
    get_primary_condition,
    get_profile_conditions,
    get_scoring_modules,
    load_user_config,
    parse_memory_file,
    prepare_font_compatible_memory,
    resolve_report_locale,
    run_local_llm,
    tavily_search,
    validate_environment,
)
from i18n import build_delivery_message, format_weight, resolve_locale
from monthly_pdf_generator import generate_monthly_pdf_report

validate_environment()

MEMORY_DIR = os.environ.get("MEMORY_DIR", "")
CUSTOM_SECTION_IGNORE_HINTS = (
    "今日目标",
    "dailytarget",
    "目标",
    "review",
    "昨日回顾",
    "今日汇总",
    "summary",
    "系统开发与优化记录",
    "工作日志",
    "suggestion",
    "建议",
    "提醒",
    "note",
    "备注",
    "午餐建议记录",
    "午餐选择确认",
    "优化讨论",
    "工作地点",
)
MONITORING_SECTION_HINTS = (
    "血压",
    "bloodpressure",
    "bp",
    "血糖",
    "glucose",
    "bloodsugar",
    "体脂",
    "bodyfat",
    "bodycomposition",
    "生化",
    "化验",
    "检验",
    "实验室",
    "lab",
    "biochemistry",
    "monitor",
    "监测",
    "睡眠",
    "sleep",
    "心率",
    "heartrate",
)
SEARCH_NOISE_TERMS = (
    "返回顶部按钮",
    "返回顶部",
    "倍速",
    "播放",
    "收藏",
    "分享",
    "关注",
    "交流",
    "视频",
    "门诊好评",
    "累计挂号",
    "精选内容",
    "点击展开",
    "展开全文",
    "阅读全文",
    "相关推荐",
    "立即预约",
    "在线问诊",
    "广告",
)
SEARCH_BAD_PATTERNS = (
    r"(?:\[\d+\]){2,}",
    r"(?:表|图)\s*\d",
    r"(?:Table|Figure)\s*\d",
    r"注释[:：]",
    r"\bDOI\b",
    r"\bet al\.\b",
    r"[Α-Ωα-ω]",
    r"[Ѐ-ӿ]",
)


def localize(locale: str, zh_text: str, en_text: str) -> str:
    return zh_text if resolve_locale(locale=locale) == "zh-CN" else en_text


def safe_average(values: Iterable[Optional[float]]) -> float:
    cleaned = [value for value in values if value is not None]
    return sum(cleaned) / len(cleaned) if cleaned else 0.0


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        output.append(normalized)
        seen.add(normalized)
    return output


def get_month_dates(target_date_str: str) -> List[str]:
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    start_date = target_date.replace(day=1)
    if start_date.month == 12:
        next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
    else:
        next_month = start_date.replace(month=start_date.month + 1, day=1)
    day_count = (next_month - start_date).days
    return [(start_date + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(day_count)]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(text or "").lower()).strip("_") or "metric"


def build_custom_section_rollup(config: dict) -> Dict[str, dict]:
    rollup = {}
    for module in get_scoring_modules(config):
        if not module.get("enabled", True):
            continue
        if module.get("type") != "section_presence" or module.get("id") == "medication":
            continue
        section_title = module.get("section_title", module.get("title", module.get("id", ""))).strip()
        key = module.get("id", section_title)
        rollup[key] = {
            "id": key,
            "title": module.get("title", section_title),
            "section_title": section_title,
            "days_recorded": 0,
            "items": 0,
            "configured": True,
            "latest_items": [],
        }
    return rollup


def merge_dynamic_custom_sections(rollup: Dict[str, dict], custom_sections: dict) -> None:
    for header, items in (custom_sections or {}).items():
        matched = False
        for stats in rollup.values():
            if find_custom_section_items({header: items}, stats.get("section_title", stats.get("title", ""))):
                matched = True
                break
        if matched:
            continue
        key = f"dynamic::{header}".strip()
        if key not in rollup:
            rollup[key] = {
                "id": key,
                "title": header,
                "section_title": header,
                "days_recorded": 0,
                "items": 0,
                "configured": False,
                "latest_items": [],
            }


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def normalize_name(value: str) -> str:
    text = re.sub(r"[*_`]+", "", str(value or "")).strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text)
    return text


def should_ignore_custom_section(title: str) -> bool:
    normalized = normalize_name(title)
    return any(normalize_name(hint) in normalized for hint in CUSTOM_SECTION_IGNORE_HINTS if hint)


def is_monitoring_section_title(title: str, allowed_titles: Optional[set] = None) -> bool:
    normalized = normalize_name(title)
    if allowed_titles and normalized in allowed_titles:
        return True
    return any(normalize_name(hint) in normalized for hint in MONITORING_SECTION_HINTS if hint)


def section_matches(title: str, aliases: Iterable[str]) -> bool:
    normalized_title = normalize_name(title)
    return any(normalize_name(alias) in normalized_title for alias in aliases if alias)


def parse_numeric_item(item: str) -> Optional[dict]:
    text = str(item or "").strip()
    pattern = re.compile(
        r"(?P<label>[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff /%_-]{0,32})\s*[:：]\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z%/._\-\u4e00-\u9fff]*)"
    )
    match = pattern.search(text)
    if not match:
        return None
    label = match.group("label").strip()
    if normalize_name(label) in {"bmi", "kcal", "calories", "steps", "步数", "饮水量", "累计"}:
        return None
    return {
        "label": label,
        "value": float(match.group("value")),
        "unit": (match.group("unit") or "").strip(),
    }


def extract_structured_metrics(file_path: str, daily_data: dict) -> dict:
    content = read_text(file_path)
    custom_sections = daily_data.get("custom_sections", {})
    metrics = {
        "body_fat_percent": None,
        "blood_pressure": [],
        "glucose": [],
        "custom_numeric_metrics": [],
    }

    body_fat_match = re.search(r"(?:体脂率|body\s*fat(?:\s*percentage)?)\s*[:：]\s*(\d+(?:\.\d+)?)\s*%", content, re.IGNORECASE)
    if body_fat_match:
        metrics["body_fat_percent"] = float(body_fat_match.group(1))

    bp_aliases = ["血压", "blood pressure", "bp"]
    glucose_aliases = ["血糖", "blood sugar", "glucose"]
    bodyfat_aliases = ["体脂", "body fat", "body composition", "身体成分"]

    for header, items in custom_sections.items():
        if should_ignore_custom_section(header):
            continue
        if section_matches(header, bp_aliases):
            for item in items:
                bp_match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmhg)?", str(item), re.IGNORECASE)
                if not bp_match:
                    continue
                heart_rate_match = re.search(r"(?:心率|heart rate|hr)\s*[:：]?\s*(\d{2,3})", str(item), re.IGNORECASE)
                metrics["blood_pressure"].append(
                    {
                        "raw": item,
                        "systolic": int(bp_match.group(1)),
                        "diastolic": int(bp_match.group(2)),
                        "heart_rate": int(heart_rate_match.group(1)) if heart_rate_match else None,
                    }
                )
        elif section_matches(header, glucose_aliases):
            for item in items:
                glucose_match = re.search(r"(?:血糖|glucose|blood sugar)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(mmol/l|mg/dl)?", str(item), re.IGNORECASE)
                if not glucose_match:
                    continue
                metrics["glucose"].append(
                    {
                        "raw": item,
                        "value": float(glucose_match.group(1)),
                        "unit": (glucose_match.group(2) or "mmol/L").upper(),
                    }
                )
        elif section_matches(header, bodyfat_aliases):
            for item in items:
                bodyfat_match = re.search(r"(?:体脂率|body\s*fat(?:\s*percentage)?)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*%", str(item), re.IGNORECASE)
                if bodyfat_match:
                    metrics["body_fat_percent"] = float(bodyfat_match.group(1))
                numeric_item = parse_numeric_item(item)
                if numeric_item:
                    metrics["custom_numeric_metrics"].append({"section": header, **numeric_item})
        else:
            for item in items:
                numeric_item = parse_numeric_item(item)
                if numeric_item:
                    metrics["custom_numeric_metrics"].append({"section": header, **numeric_item})

    return metrics


def daily_symptom_count(daily_data: dict) -> int:
    symptoms = extract_relevant_symptom_lines(daily_data)
    if not symptoms:
        return 0
    symptom_text = " ".join(symptoms).lower()
    if any(token in symptom_text for token in ["无不适", "无症状", "none", "no symptom", "no discomfort"]):
        return 0
    labels = extract_symptom_labels(daily_data, "zh-CN")
    if labels:
        return len(labels)
    return len(symptoms)


def extract_relevant_symptom_lines(daily_data: dict) -> List[str]:
    raw_items = [str(item or "").strip() for item in daily_data.get("symptoms", []) if str(item or "").strip()]
    if not raw_items:
        return []

    skip_hints = [
        "无记录",
        "待记录",
        "--",
        "早餐",
        "午餐",
        "晚餐",
        "加餐",
        "饮水",
        "步数",
        "骑行",
        "运动",
        "千卡",
        "kcal",
        "膳食纤维",
        "蛋白质",
        "脂肪：",
        "碳水：",
        "评估：",
        "总计：",
        "状态：",
        "总消耗",
        "有氧运动",
        "少量多餐",
        "胆汁",
        "维生素",
        "全天步数",
        "可能缓解因素",
        "症状持续时长",
        "当前：待评估",
        "current status",
        "possible relieving factors",
        "duration",
        "source note",
        "source memory",
        "strict low-fat meals",
        "fiber target",
        "smaller, more frequent meals",
        "hydration",
        "cycling",
        "exercise",
        "steps",
    ]
    positive_hints = [
        "右上腹",
        "腹胀",
        "腹涨",
        "腹痛",
        "胀痛",
        "隐痛",
        "绞痛",
        "恶心",
        "不适",
        "pain",
        "bloating",
        "distension",
        "nausea",
        "discomfort",
    ]
    resolved_hints = ["无不适", "无症状", "无不适感", "完全缓解", "症状已完全缓解", "recovered", "resolved"]

    relevant = []
    for item in raw_items:
        lowered = item.lower()
        if any(hint.lower() in lowered for hint in skip_hints):
            continue
        if any(hint.lower() in lowered for hint in resolved_hints):
            continue
        if any(hint.lower() in lowered for hint in positive_hints):
            relevant.append(item)
    return dedupe_preserve_order(relevant)


def extract_symptom_labels(daily_data: dict, locale: str) -> List[str]:
    symptoms = extract_relevant_symptom_lines(daily_data)
    if not symptoms:
        return []

    symptom_text = " ".join(symptoms).lower()
    if any(token in symptom_text for token in ["无不适", "无症状", "none", "no symptom", "no discomfort"]):
        return []

    label_map = [
        (
            localize(locale, "右上腹隐痛", "Right upper abdominal pain"),
            [
                "右上腹隐痛",
                "右上腹痛",
                "右上腹疼",
                "右上腹不适",
                "右上腹胀",
                "右上腹胀痛",
                "right upper abdominal pain",
                "right upper quadrant pain",
                "ruq pain",
                "right upper abdominal discomfort",
                "right upper abdominal bloating",
                "post-meal right upper abdominal bloating",
                "post-meal right upper quadrant discomfort",
            ],
        ),
        (
            localize(locale, "餐后腹胀", "Post-meal bloating"),
            ["餐后腹胀", "饭后腹胀", "饭后发胀", "post-meal bloating", "postprandial bloating"],
        ),
        (
            localize(locale, "腹胀", "Bloating"),
            ["腹胀", "腹涨", "bloating", "distension"],
        ),
        (
            localize(locale, "恶心", "Nausea"),
            ["恶心", "nausea"],
        ),
        (
            localize(locale, "绞痛", "Colic"),
            ["绞痛", "colic"],
        ),
        (
            localize(locale, "腹痛", "Abdominal pain"),
            ["腹痛", "胃痛", "abdominal pain", "abdomen pain"],
        ),
        (
            localize(locale, "不适", "Discomfort"),
            ["不适", "discomfort"],
        ),
    ]

    matched = []
    for label, aliases in label_map:
        if any(alias in symptom_text for alias in aliases):
            matched.append(label)

    dominant_ruq_label = localize(locale, "右上腹隐痛", "Right upper abdominal pain")
    generic_bloating_label = localize(locale, "腹胀", "Bloating")
    generic_discomfort_label = localize(locale, "不适", "Discomfort")
    if dominant_ruq_label in matched:
        matched = [label for label in matched if label not in {generic_bloating_label, generic_discomfort_label}]
    elif len(matched) > 1 and generic_discomfort_label in matched:
        matched = [label for label in matched if label != generic_discomfort_label]

    if matched:
        return dedupe_preserve_order(matched)

    fallback_labels = []
    for item in symptoms:
        cleaned = re.sub(r"^[\-\s•*]+", "", item)
        cleaned = re.sub(r"[:：].*$", "", cleaned).strip()
        if 0 < len(cleaned) <= 24:
            fallback_labels.append(cleaned)
    return dedupe_preserve_order(fallback_labels)


def format_monthly_review_sections(locale: str, sections: Iterable[tuple[str, str, str]]) -> str:
    parts = []
    for zh_title, en_title, body in sections:
        clean_body = re.sub(r"\s+", " ", str(body or "")).strip()
        if not clean_body:
            continue
        title = f"【{zh_title}】" if resolve_locale(locale=locale) == "zh-CN" else f"[{en_title}]"
        parts.append(f"**{title}**\n{clean_body}")
    return "\n\n".join(parts).strip()


def ensure_monthly_review_sections(text: str, monthly_data: dict, locale: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""

    if any(token in cleaned for token in ["核心发现", "风险提示", "下月调整", "Key Findings", "Risk Watch", "Next-Month Actions"]):
        return cleaned

    sentences = [item.strip() for item in re.split(r"(?<=[。！？!?])\s+|(?<=\.)\s+", cleaned) if item.strip()]
    findings = " ".join(sentences[:2]) or cleaned
    risk = " ".join(sentences[2:4]).strip()
    plan = " ".join(sentences[4:]).strip()

    if not risk:
        low_scores = [
            label
            for key, label in [
                ("diet", localize(locale, "饮食", "diet")),
                ("water", localize(locale, "饮水", "hydration")),
                ("exercise", localize(locale, "运动", "exercise")),
                ("monitoring", localize(locale, "监测", "monitoring")),
            ]
            if monthly_data.get("macro_scores", {}).get(key, 0) < 70
        ]
        if low_scores:
            risk = localize(locale, f"当前仍需重点关注：{'、'.join(low_scores)}。", f"The main watch-outs remain: {', '.join(low_scores)}.")
        else:
            risk = localize(locale, "本月整体风险信号不高，但仍需继续保持记录完整性。", "Overall risk signals stayed modest this month, but tracking consistency still matters.")

    if not plan:
        plan = localize(
            locale,
            "下月建议继续优先稳定饮食节奏、补齐专项监测，并把高风险触发因素写进每日记录，便于继续做趋势对照。",
            "Next month, prioritize steadier meal timing, more complete specialty monitoring, and explicit trigger notes in daily logs so trends stay comparable.",
        )

    return format_monthly_review_sections(
        locale,
        [
            ("核心发现", "Key Findings", findings),
            ("风险提示", "Risk Watch", risk),
            ("下月调整", "Next-Month Actions", plan),
        ],
    )


def get_profile_residence(profile: dict, locale: str) -> dict:
    residence = profile.get("residence", {}) if isinstance(profile.get("residence"), dict) else {}
    country = str(residence.get("country") or profile.get("country") or "").strip()
    province = str(residence.get("province") or profile.get("province") or "").strip()
    city = str(residence.get("city") or profile.get("city") or "").strip()
    district = str(residence.get("district") or profile.get("district") or "").strip()
    display_name = str(residence.get("display_name") or "").strip()
    parts = [part for part in [province, city, district] if part]
    if not display_name and parts:
        display_name = "".join(parts) if locale == "zh-CN" else ", ".join(parts)
    return {
        "country": country,
        "province": province,
        "city": city,
        "district": district,
        "display_name": display_name,
    }


def extract_gallstone_ultrasound_summary(memory_dir: str) -> dict:
    path = os.path.join(memory_dir, "gallstone_ultrasound_records.md")
    content = read_text(path)
    if not content:
        return {}

    records = []
    for date_str, size_str in re.findall(r"(\d{4}-\d{2}-\d{2}).*?(\d+(?:\.\d+)?)\s*cm", content):
        try:
            records.append((date_str, float(size_str)))
        except ValueError:
            continue
    if not records:
        return {}
    records.sort(key=lambda item: item[0])
    latest_date, latest_size = records[-1]
    return {
        "latest_date": latest_date,
        "latest_size_cm": latest_size,
        "max_size_cm": max(size for _, size in records),
        "wall_warning": any(token in content for token in ["毛糙", "增厚", "壁厚", "炎症"]),
    }


def aggregate_monthly_data(month_dates: List[str], config: dict, locale: Optional[str] = None, memory_dir: Optional[str] = None) -> dict:
    locale = resolve_locale(config, locale=locale)
    memory_dir = memory_dir or MEMORY_DIR
    profile = config.get("user_profile", {})
    conditions = get_profile_conditions(profile)
    primary_condition = get_primary_condition(profile)
    condition_text = get_conditions_display_name(locale, conditions)
    standards = get_condition_standards(config, conditions)
    custom_rollup = build_custom_section_rollup(config)
    allowed_monitoring_titles = {
        normalize_name(module.get("section_title", module.get("title", "")))
        for module in get_scoring_modules(config)
        if module.get("enabled", True) and module.get("type") == "section_presence" and module.get("id") != "medication"
    }
    residence = get_profile_residence(profile, locale)
    medication_enabled = any(
        module.get("id") == "medication" and module.get("enabled", True)
        for module in get_scoring_modules(config)
    )

    monthly_data = {
        "start_date": month_dates[0],
        "end_date": month_dates[-1],
        "month_key": month_dates[0][:7],
        "dates": month_dates,
        "conditions": conditions,
        "condition_text": condition_text,
        "primary_condition": primary_condition,
        "diet_principle": build_multi_condition_tip(locale, conditions, standards),
        "residence_text": residence.get("display_name", ""),
        "weights": [],
        "body_fat_percent": [],
        "water_intakes": [],
        "steps": [],
        "calories": [],
        "protein": [],
        "fat": [],
        "carb": [],
        "fiber": [],
        "daily_records": [],
        "blood_pressure_records": [],
        "glucose_records": [],
        "custom_numeric_metrics": defaultdict(lambda: {"label": "", "unit": "", "section": "", "points": []}),
        "symptom_distribution": defaultdict(int),
        "observed_days": 0,
        "recorded_meal_days": 0,
        "valid_weight_days": 0,
        "water_goal_days": 0,
        "step_goal_days": 0,
        "diet_goal_days": 0,
        "exercise_days": 0,
        "symptom_days": 0,
        "symptom_events": 0,
        "medication_days": 0,
        "monitoring_days": 0,
        "medication_enabled": medication_enabled,
        "residence": residence,
    }

    first_weight = None
    last_weight = None
    water_target = int(profile.get("water_target_ml", 2000) or 2000)
    step_target = int(profile.get("step_target", 8000) or 8000)

    for date_str in month_dates:
        file_path = os.path.join(memory_dir, f"{date_str}.md")
        daily_data = parse_memory_file(file_path)
        daily_data["date"] = daily_data.get("date") or date_str
        filtered_custom_sections = {
            header: items
            for header, items in (daily_data.get("custom_sections", {}) or {}).items()
            if not should_ignore_custom_section(header) and is_monitoring_section_title(header, allowed_monitoring_titles)
        }
        daily_data["custom_sections"] = filtered_custom_sections

        merge_dynamic_custom_sections(custom_rollup, filtered_custom_sections)
        monitoring_items_today = 0
        for stats in custom_rollup.values():
            items = find_custom_section_items(filtered_custom_sections, stats.get("section_title", stats.get("title", "")))
            if items:
                stats["days_recorded"] += 1
                stats["items"] += len(items)
                stats["latest_items"] = items[-4:]
                monitoring_items_today += len(items)

        structured = extract_structured_metrics(file_path, daily_data)
        score_report = build_score_report(daily_data, config)
        water_total = int(daily_data.get("water_total", 0) or 0)
        steps = int(daily_data.get("steps", 0) or 0)
        symptom_count = daily_symptom_count(daily_data)
        symptom_labels = extract_symptom_labels(daily_data, locale)
        medication_records = daily_data.get("medication_records", [])
        weight_value = daily_data.get("weight_morning")
        body_fat_percent = structured.get("body_fat_percent")

        monitoring_present = any(
            [
                weight_value is not None,
                body_fat_percent is not None,
                monitoring_items_today > 0,
                bool(structured.get("blood_pressure")),
                bool(structured.get("glucose")),
                bool(structured.get("custom_numeric_metrics")),
            ]
        )
        has_data = any(
            [
                bool(daily_data.get("meals")),
                bool(daily_data.get("water_records")),
                bool(daily_data.get("exercise_records")),
                bool(daily_data.get("custom_sections")),
                bool(medication_records),
                symptom_count > 0,
                water_total > 0,
                steps > 0,
                weight_value is not None,
                monitoring_present,
            ]
        )

        if has_data:
            monthly_data["observed_days"] += 1
        if daily_data.get("meals"):
            monthly_data["recorded_meal_days"] += 1
        if daily_data.get("exercise_records") or steps > 0:
            monthly_data["exercise_days"] += 1
        if symptom_count > 0:
            monthly_data["symptom_days"] += 1
            monthly_data["symptom_events"] += symptom_count
        for label in symptom_labels:
            monthly_data["symptom_distribution"][label] += 1
        if medication_records:
            monthly_data["medication_days"] += 1
        if monitoring_present:
            monthly_data["monitoring_days"] += 1
        if water_total >= water_target:
            monthly_data["water_goal_days"] += 1
        if steps >= step_target:
            monthly_data["step_goal_days"] += 1

        diet_score = score_report.get("module_map", {}).get("diet", {}).get("raw", 0)
        if diet_score >= 80:
            monthly_data["diet_goal_days"] += 1

        monthly_data["weights"].append(weight_value)
        monthly_data["body_fat_percent"].append(body_fat_percent)
        if weight_value is not None:
            monthly_data["valid_weight_days"] += 1
            if first_weight is None:
                first_weight = weight_value
            last_weight = weight_value

        for item in structured.get("blood_pressure", []):
            monthly_data["blood_pressure_records"].append({"date": date_str, **item})
        for item in structured.get("glucose", []):
            monthly_data["glucose_records"].append({"date": date_str, **item})
        for item in structured.get("custom_numeric_metrics", []):
            key = f"{slugify(item.get('section'))}:{slugify(item.get('label'))}:{item.get('unit', '')}"
            monthly_data["custom_numeric_metrics"][key]["label"] = item.get("label", "")
            monthly_data["custom_numeric_metrics"][key]["unit"] = item.get("unit", "")
            monthly_data["custom_numeric_metrics"][key]["section"] = item.get("section", "")
            monthly_data["custom_numeric_metrics"][key]["points"].append(
                {
                    "date": date_str,
                    "value": item.get("value"),
                }
            )

        monthly_data["water_intakes"].append(water_total)
        monthly_data["steps"].append(steps)
        monthly_data["calories"].append(daily_data.get("total_calories", 0))
        monthly_data["protein"].append(daily_data.get("total_protein", 0))
        monthly_data["fat"].append(daily_data.get("total_fat", 0))
        monthly_data["carb"].append(daily_data.get("total_carb", 0))
        monthly_data["fiber"].append(daily_data.get("total_fiber", 0))
        monthly_data["daily_records"].append(
            {
                "date": date_str,
                "has_data": has_data,
                "score": score_report.get("total", 0),
                "diet_score": diet_score,
                "water_total": water_total,
                "steps": steps,
                "calories": daily_data.get("total_calories", 0),
                "protein": daily_data.get("total_protein", 0),
                "carb": daily_data.get("total_carb", 0),
                "fiber": daily_data.get("total_fiber", 0),
                "weight": weight_value,
                "body_fat_percent": body_fat_percent,
                "fat": daily_data.get("total_fat", 0),
                "symptom_count": symptom_count,
                "symptom_labels": symptom_labels,
                "medication_count": len(medication_records),
                "monitoring_count": monitoring_items_today + len(structured.get("blood_pressure", [])) + len(structured.get("glucose", [])),
            }
        )

    divisor = max(1, monthly_data["observed_days"])
    valid_weights = [value for value in monthly_data["weights"] if value is not None]
    valid_bodyfat = [value for value in monthly_data["body_fat_percent"] if value is not None]
    scored_days = [record["score"] for record in monthly_data["daily_records"] if record.get("has_data")]
    diet_days = [record["diet_score"] for record in monthly_data["daily_records"] if record.get("diet_score", 0) > 0]

    monthly_data["avg_weight"] = safe_average(valid_weights)
    monthly_data["latest_weight"] = last_weight
    monthly_data["weight_change"] = (last_weight - first_weight) if (last_weight is not None and first_weight is not None) else 0
    monthly_data["avg_body_fat_percent"] = safe_average(valid_bodyfat)
    monthly_data["avg_calories"] = sum(monthly_data["calories"]) / divisor
    monthly_data["avg_water"] = sum(monthly_data["water_intakes"]) / divisor
    monthly_data["avg_steps"] = sum(monthly_data["steps"]) / divisor
    monthly_data["avg_protein"] = sum(monthly_data["protein"]) / divisor
    monthly_data["avg_fat"] = sum(monthly_data["fat"]) / divisor
    monthly_data["avg_carb"] = sum(monthly_data["carb"]) / divisor
    monthly_data["avg_fiber"] = sum(monthly_data["fiber"]) / divisor
    monthly_data["avg_total_score"] = safe_average(scored_days)
    monthly_data["avg_diet_score"] = safe_average(diet_days)
    monthly_data["custom_section_stats"] = sorted(custom_rollup.values(), key=lambda item: (item.get("days_recorded", 0), item.get("items", 0), item.get("title", "")), reverse=True)
    monthly_data["symptom_distribution"] = dict(
        sorted(monthly_data["symptom_distribution"].items(), key=lambda item: (-item[1], item[0]))
    )

    medication_expected = medication_enabled or monthly_data["medication_days"] > 0
    monthly_data["macro_scores"] = {
        "diet": round(monthly_data["diet_goal_days"] / divisor * 100, 1),
        "water": round(monthly_data["water_goal_days"] / divisor * 100, 1),
        "exercise": round(((monthly_data["step_goal_days"] / divisor) * 0.65 + (monthly_data["exercise_days"] / divisor) * 0.35) * 100, 1),
        "medication": 100.0 if not medication_expected else round(monthly_data["medication_days"] / divisor * 100, 1),
        "monitoring": round(monthly_data["monitoring_days"] / divisor * 100, 1),
    }

    monthly_data["ultrasound_summary"] = extract_gallstone_ultrasound_summary(memory_dir)
    return monthly_data


def build_monthly_highlights(monthly_data: dict, profile: dict, locale: str) -> List[str]:
    highlights = []
    macro_scores = monthly_data.get("macro_scores", {})
    score_pairs = [
        ("diet", localize(locale, "饮食", "diet")),
        ("water", localize(locale, "饮水", "hydration")),
        ("exercise", localize(locale, "运动", "exercise")),
        ("medication", localize(locale, "用药", "medication")),
        ("monitoring", localize(locale, "监测", "monitoring")),
    ]
    best_key, best_label = max(score_pairs, key=lambda item: macro_scores.get(item[0], 0))
    highlights.append(
        localize(
            locale,
            f"本月 {best_label} 维度完成度最高，约 {macro_scores.get(best_key, 0):.0f}%。",
            f"{best_label.capitalize()} was the strongest adherence dimension this month at about {macro_scores.get(best_key, 0):.0f}%.",
        )
    )

    if monthly_data.get("symptom_days", 0) == 0:
        highlights.append(localize(locale, "本月未记录明显症状，整体状态比较平稳。", "No clear symptom day was recorded this month, suggesting a steady overall state."))
    else:
        highlights.append(
            localize(
                locale,
                f"本月有 {monthly_data['symptom_days']} 天出现不适，共 {monthly_data['symptom_events']} 次，需重点复盘诱因。",
                f"Symptoms were logged on {monthly_data['symptom_days']} days ({monthly_data['symptom_events']} events) and deserve closer trigger review.",
            )
        )

    weight_change = monthly_data.get("weight_change", 0)
    primary_condition = monthly_data.get("primary_condition")
    if monthly_data.get("latest_weight") is not None:
        if primary_condition == "fat_loss" and weight_change < 0:
            highlights.append(localize(locale, f"体重较月初下降 {abs(weight_change):.2f}kg，方向与减脂目标一致。", f"Weight moved down by {abs(weight_change):.2f}kg from the start of the month, which aligns with fat-loss goals."))
        elif abs(weight_change) <= 0.6:
            highlights.append(localize(locale, f"体重月内波动约 {abs(weight_change):.2f}kg，整体比较稳定。", f"Weight fluctuated by about {abs(weight_change):.2f}kg this month and stayed relatively stable."))
        else:
            highlights.append(localize(locale, f"体重月内波动达到 {abs(weight_change):.2f}kg，建议和饮食、活动一起复盘。", f"Weight fluctuated by {abs(weight_change):.2f}kg this month, so meals and activity deserve a joint review."))

    if monthly_data.get("medication_enabled"):
        highlights.append(
            localize(
                locale,
                f"用药记录覆盖 {monthly_data.get('medication_days', 0)} 天，月报已纳入依从性与风险评估。",
                f"Medication was logged on {monthly_data.get('medication_days', 0)} days and is now part of the adherence and risk review.",
            )
        )

    if monthly_data.get("monitoring_days", 0) > 0:
        highlights.append(
            localize(
                locale,
                f"监测模块有 {monthly_data.get('monitoring_days', 0)} 天记录，可用于联合判断趋势。",
                f"Monitoring modules were logged on {monthly_data.get('monitoring_days', 0)} days, which gives us cross-metric trend visibility.",
            )
        )

    return dedupe_preserve_order(highlights)[:5]


def build_specialty_charts(monthly_data: dict, config: dict, locale: str) -> List[dict]:
    charts = []
    standards = get_condition_standards(config, monthly_data.get("conditions", []))
    daily_records = monthly_data.get("daily_records", [])
    conditions = monthly_data.get("conditions", [])

    if "gallstones" in conditions:
        symptom_days = [record for record in daily_records if record.get("symptom_count", 0) > 0]
        fat_on_symptom = safe_average([record.get("fat") for record in symptom_days]) if symptom_days else 0
        fat_on_calm = safe_average([record.get("fat") for record in daily_records if record.get("symptom_count", 0) == 0 and record.get("fat", 0) > 0])
        charts.append(
            {
                "type": "gallstones",
                "title": localize(locale, "胆结石：脂肪摄入 vs 症状频次", "Gallstones: Fat intake vs symptom frequency"),
                "subtitle": localize(locale, "双轴对照：左轴为每日脂肪克数，右轴为当天症状次数。", "Dual-axis view: daily fat grams on the left axis, symptom count on the right."),
                "records": daily_records,
                "fat_target": standards.get("fat_max_g"),
                "summary": localize(
                    locale,
                    f"症状日的平均脂肪摄入约 {fat_on_symptom:.1f}g，平稳日约 {fat_on_calm:.1f}g。若两者差距持续扩大，说明油脂控制与症状关系更值得重点关注。",
                    f"Average fat intake was about {fat_on_symptom:.1f}g on symptom days versus {fat_on_calm:.1f}g on calmer days. If that gap keeps widening, fat control is likely a major trigger to review.",
                ),
            }
        )
        intake_records = [record for record in daily_records if record.get("fat", 0) > 0 or record.get("carb", 0) > 0]
        if len(intake_records) >= 3:
            fat_values = [float(record.get("fat", 0) or 0) for record in intake_records if record.get("fat", 0) > 0]
            carb_values = [float(record.get("carb", 0) or 0) for record in intake_records if record.get("carb", 0) > 0]
            if len(fat_values) >= 3 and len(carb_values) >= 3:
                charts.append(
                    {
                        "type": "intake_boxplot",
                        "title": localize(locale, "胆结石：脂肪 / 碳水摄入离散度", "Gallstones: Fat and carb intake spread"),
                        "subtitle": localize(locale, "用箱线图识别“平时很稳、偶尔暴冲”的摄入异常日。", "A boxplot helps spot unusually high-intake days that averages can hide."),
                        "records": intake_records,
                        "summary": localize(
                            locale,
                            f"本月脂肪均值约 {safe_average(fat_values):.1f}g，碳水均值约 {safe_average(carb_values):.1f}g。若离群点明显偏高，建议回看对应日期的晚餐和加餐。",
                            f"Typical fat intake stayed around {safe_average(fat_values):.1f}g and carbs around {safe_average(carb_values):.1f}g. If outliers rise far above the box, revisit those dinner and snack days.",
                        ),
                    }
                )

    symptom_distribution = monthly_data.get("symptom_distribution", {})
    if symptom_distribution:
        top_labels = list(symptom_distribution.items())[:5]
        distribution_text = "、".join(f"{label} {count}次" for label, count in top_labels) if locale == "zh-CN" else ", ".join(f"{label} {count}x" for label, count in top_labels)
        charts.append(
            {
                "type": "symptom_distribution",
                "title": localize(locale, "症状分布：本月不适类型占比", "Symptom mix: monthly discomfort distribution"),
                "subtitle": localize(locale, "帮助区分“什么时候不舒服”与“具体是怎么不舒服”。", "This complements the timeline by showing what kinds of symptoms appeared most often."),
                "distribution": symptom_distribution,
                "summary": localize(
                    locale,
                    f"本月记录到的症状类型主要集中在：{distribution_text}。如果症状从腹胀逐步转向明显疼痛，建议把诱因和持续时间记得更细。",
                    f"The recorded symptom mix was led by: {distribution_text}. If the pattern shifts from bloating toward clearer pain, log triggers and duration in more detail next month.",
                ),
            }
        )

    if "hypertension" in conditions and monthly_data.get("blood_pressure_records"):
        bp_records = monthly_data.get("blood_pressure_records", [])
        systolic = [item["systolic"] for item in bp_records if item.get("systolic")]
        diastolic = [item["diastolic"] for item in bp_records if item.get("diastolic")]
        charts.append(
            {
                "type": "hypertension",
                "title": localize(locale, "高血压：30 天血压波动箱线图", "Hypertension: 30-day blood pressure boxplot"),
                "subtitle": localize(locale, "观察收缩压与舒张压的中位数、离散度与极值范围。", "This highlights median values, spread, and outlier range for systolic and diastolic pressure."),
                "bp_records": bp_records,
                "summary": localize(
                    locale,
                    f"本月收缩压均值约 {safe_average(systolic):.0f} mmHg，舒张压均值约 {safe_average(diastolic):.0f} mmHg。箱体越宽，说明波动越大，越需要结合作息、盐分和服药时间复盘。",
                    f"Average systolic pressure was about {safe_average(systolic):.0f} mmHg and average diastolic pressure was about {safe_average(diastolic):.0f} mmHg. A wider box means greater variability and a stronger need to review sleep, sodium, and medication timing.",
                ),
            }
        )

    if "diabetes" in conditions and monthly_data.get("glucose_records"):
        glucose_records = monthly_data.get("glucose_records", [])
        avg_glucose = safe_average([item.get("value") for item in glucose_records])
        charts.append(
            {
                "type": "diabetes",
                "title": localize(locale, "糖尿病：血糖监测趋势", "Diabetes: Glucose monitoring trend"),
                "subtitle": localize(locale, "用于观察月内血糖波动与高值出现频率。", "Use this to inspect intra-month glucose swings and the frequency of elevated readings."),
                "glucose_records": glucose_records,
                "summary": localize(
                    locale,
                    f"本月已记录 {len(glucose_records)} 次血糖，均值约 {avg_glucose:.1f} mmol/L。建议结合餐后时点和主食份量一起看高值出现的位置。",
                    f"{len(glucose_records)} glucose readings were logged this month with an average of about {avg_glucose:.1f} mmol/L. Elevated points should be reviewed together with meal timing and carb portions.",
                ),
            }
        )

    if "fat_loss" in conditions and any(record.get("weight") is not None for record in daily_records):
        bodyfat_days = sum(1 for record in daily_records if record.get("body_fat_percent") is not None)
        charts.append(
            {
                "type": "fat_loss",
                "title": localize(locale, "健身减脂：体重与体脂率平滑趋势", "Fat loss: Smoothed weight and body-fat trend"),
                "subtitle": localize(locale, "粗线表示平滑后的趋势，便于识别真实变化方向。", "The thicker line shows a smoothed trend so the real direction is easier to read."),
                "records": daily_records,
                "summary": localize(
                    locale,
                    f"本月共有 {monthly_data.get('valid_weight_days', 0)} 天体重记录，{bodyfat_days} 天体脂记录。若体重下降但体脂不降，说明仍需优化蛋白、力量训练与恢复。",
                    f"There were {monthly_data.get('valid_weight_days', 0)} weight days and {bodyfat_days} body-fat days this month. If weight drops but body fat does not, protein intake, strength training, and recovery still need work.",
                ),
            }
        )

    for metric in sorted(monthly_data.get("custom_numeric_metrics", {}).values(), key=lambda item: len(item.get("points", [])), reverse=True):
        if len(metric.get("points", [])) < 2:
            continue
        charts.append(
            {
                "type": "custom_metric",
                "title": localize(locale, f"附加监测：{metric.get('section')} · {metric.get('label')}", f"Additional monitoring: {metric.get('section')} · {metric.get('label')}"),
                "subtitle": localize(locale, "来自自定义监测模块的数值趋势。", "Numeric trend extracted from a custom monitoring module."),
                "section": metric.get("section"),
                "label": metric.get("label"),
                "unit": metric.get("unit"),
                "points": metric.get("points", []),
                "summary": localize(locale, f"该指标来自“{metric.get('section')}”模块，当前已累计 {len(metric.get('points', []))} 个数值点，后续可继续用于月度趋势分析。", f"This metric comes from the '{metric.get('section')}' module and already has {len(metric.get('points', []))} numeric points for monthly trend analysis."),
            }
        )
    return charts[:6]


def build_follow_up_reminders(monthly_data: dict, profile: dict, locale: str) -> List[str]:
    reminders = []
    conditions = monthly_data.get("conditions", [])
    symptom_days = monthly_data.get("symptom_days", 0)
    ultrasound = monthly_data.get("ultrasound_summary", {})

    if "gallstones" in conditions:
        reminders.append(localize(locale, "肝胆胰脾彩超（空腹）+ 肝功能，建议按季度完成一次复查。", "A fasting hepatobiliary ultrasound plus liver-function labs should be reviewed at least once per quarter."))
        if symptom_days >= 3 or ultrasound.get("latest_size_cm", 0) >= 2 or ultrasound.get("wall_warning"):
            reminders.append(localize(locale, "本月已出现较高风险信号，建议尽快预约肝胆外科或普外科专家门诊评估是否需要进一步干预。", "Higher-risk signals appeared this month, so a hepatobiliary or general-surgery specialist visit should be arranged soon to evaluate further intervention."))
        elif ultrasound.get("latest_size_cm"):
            reminders.append(localize(locale, f"最近一次超声记录最大结石约 {ultrasound.get('latest_size_cm'):.1f}cm，若症状重新增多，不要拖到下季度再评估。", f"The latest ultrasound recorded a largest stone of about {ultrasound.get('latest_size_cm'):.1f}cm. If symptoms pick up again, do not wait until next quarter to re-evaluate."))

    if "hypertension" in conditions:
        reminders.append(localize(locale, "建议保留连续 7 天晨起和睡前家庭血压记录，复诊时一并带给医生。", "Keep a 7-day home blood-pressure log with morning and bedtime readings and bring it to follow-up visits."))
        high_bp_count = sum(1 for item in monthly_data.get("blood_pressure_records", []) if item.get("systolic", 0) >= 140 or item.get("diastolic", 0) >= 90)
        if high_bp_count >= 3:
            reminders.append(localize(locale, "本月多次出现偏高血压，建议 2-4 周内复诊心内科或高血压门诊。", "Repeated high blood-pressure readings were logged this month, so a cardiology or hypertension-clinic follow-up within 2-4 weeks is reasonable."))

    if "diabetes" in conditions:
        reminders.append(localize(locale, "建议至少每 3 个月复查 HbA1c，并结合空腹血糖与餐后血糖一起判断。", "Review HbA1c at least every 3 months and interpret it together with fasting and post-meal glucose readings."))
        high_glucose_count = sum(1 for item in monthly_data.get("glucose_records", []) if item.get("value", 0) >= 10)
        if high_glucose_count >= 3:
            reminders.append(localize(locale, "本月已多次出现高血糖点位，建议尽快和内分泌门诊讨论饮食、运动与用药方案。", "Multiple high glucose readings appeared this month, so an endocrinology follow-up to review meals, activity, and medication is worth arranging soon."))

    if "fat_loss" in conditions:
        reminders.append(localize(locale, "减脂管理建议每 4-6 周复盘一次体重、体脂率、围度和训练恢复情况。", "For fat-loss management, review weight, body fat, measurements, and recovery every 4-6 weeks."))
        if abs(monthly_data.get("weight_change", 0)) < 0.2:
            reminders.append(localize(locale, "如果体重和体脂连续平台超过 4 周，可考虑营养门诊或运动康复门诊做一次结构化复盘。", "If both weight and body fat plateau for more than 4 weeks, a structured review with a nutrition or sports-medicine clinic may help."))

    if monthly_data.get("monitoring_days", 0) < max(5, monthly_data.get("observed_days", 0) // 3):
        reminders.append(localize(locale, "关键监测记录偏少，建议下个月优先补齐体重、症状和专项指标，再看月报会更有参考价值。", "Key monitoring data were still sparse. Next month, prioritize weight, symptoms, and specialty metrics so the monthly report becomes more actionable."))

    return dedupe_preserve_order(reminders)[:6]


def extract_doctor_name(text: str) -> str:
    raw_text = str(text or "")
    patterns = [
        r"([\u4e00-\u9fff]{2,3})(主任医师|副主任医师|主任|教授|医生)",
        r"(Dr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            if len(match.groups()) == 2:
                return "".join(match.groups())
            return match.group(1)
    return ""


def extract_hospital_name(text: str) -> str:
    raw_text = str(text or "")
    patterns = [
        r"([\u4e00-\u9fff]{2,24}(?:大学附属医院|附属医院|医院|医学中心|中医院|人民医院|妇幼保健院|医疗中心))",
        r"([A-Z][A-Za-z\s]+(?:Hospital|Medical Center|Clinic))",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            hospital = match.group(1).strip()
            hospital = re.sub(r"^[\u4e00-\u9fff]{1,12}(?:主任医师|副主任医师|医生|医师)", "", hospital).strip()
            return hospital
    return ""


def trim_text(value: str, max_length: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_length:
        return text
    clipped = text[: max_length - 1].rstrip(" ,.;，；、")
    return f"{clipped}…"


def strip_search_noise(text: str) -> str:
    raw = str(text or "")
    if not raw:
        return ""
    raw = re.sub(r"https?://\S+|www\.\S+", "", raw)
    raw = re.sub(r"(?:\b\d+:\d+\b\s*){1,3}", " ", raw)
    raw = re.sub(r"^\s*(?:\d+[.)、]\s*)+", "", raw)
    raw = re.sub(r"^\s*\d+\s+", "", raw)
    raw = re.sub(r"\[\d+\]", "", raw)
    raw = re.sub(r"(?:表|图|Table|Figure)\s*[-\d.]+", " ", raw, flags=re.IGNORECASE)
    raw = re.sub("|".join(re.escape(term) for term in SEARCH_NOISE_TERMS), " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"[|<>#@]+", " ", raw)
    raw = re.sub(r"[•·]{2,}", " ", raw)
    raw = re.sub(r"[.。…]{4,}", "…", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" |，,.;；、-")
    return raw


def matches_locale_text(text: str, locale: str) -> bool:
    cleaned = str(text or "").strip()
    if not cleaned:
        return False
    if resolve_locale(locale=locale) == "zh-CN":
        return len(re.findall(r"[\u4e00-\u9fff]", cleaned)) >= 8
    return len(re.findall(r"[A-Za-z]{3,}", cleaned)) >= 5


def is_readable_text(value: str, locale: str) -> bool:
    text = strip_search_noise(value)
    if not text:
        return False
    if text.lstrip().startswith(("+", "•")):
        return False
    if text.rstrip().endswith(("e.g.", "e.g", "for example", "for exampl…")):
        return False
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 14:
        return False
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in SEARCH_BAD_PATTERNS):
        return False
    useful_chars = len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", compact))
    weird_chars = len(re.findall(r"[^A-Za-z0-9\u4e00-\u9fff.,;:!?%()（）/+℃ \\-]", text))
    if useful_chars / max(1, len(compact)) < 0.62:
        return False
    if weird_chars > max(3, len(compact) // 16):
        return False
    if re.search(r"(?:\b\d{2,3}\b[\s,.;]*){3,}", text):
        return False
    if len(re.findall(r"[，、, ]", text)) >= 6 and not re.search(r"[。！？.!?；;:：]", text):
        return False
    if re.search(r"(好评率|接诊量|平均响应|福報購|人間福報|蔬食譜|蔬知識|蔬新聞|蔬視頻)", text, re.IGNORECASE):
        return False
    return matches_locale_text(text, locale)


def clean_search_excerpt(text: str, locale: str, max_length: int = 120) -> str:
    raw = strip_search_noise(text)
    if not raw:
        return ""

    sentences = re.split(r"(?<=[。！？!?])\s+|(?<=[.;；])\s+", raw)
    for sentence in sentences:
        candidate = sentence.strip(" -")
        if candidate and is_readable_text(candidate, locale):
            return trim_text(candidate, max_length)

    return trim_text(raw, max_length) if is_readable_text(raw, locale) else ""


def is_valid_hospital_name(name: str) -> bool:
    hospital = str(name or "").strip()
    if not hospital:
        return False
    if any(token in hospital for token in ["推荐医院", "推荐专家", "精选内容", "在线问诊", "科室动态"]):
        return False
    if re.search(r"^(?:那么|如果|还是|最好|建议|需要|可以|先去|应当|应该|是否|先到)", hospital):
        return False
    if re.search(r"(?:去医院|去门诊|看医生|挂号|就诊)$", hospital):
        return False
    if len(re.findall(r"[\u4e00-\u9fffA-Za-z]", hospital)) < 4:
        return False
    return bool(re.search(r"(医院|医学中心|中医院|医疗中心|Hospital|Medical Center|Clinic)", hospital, re.IGNORECASE))


def clean_hospital_reason(text: str, locale: str, max_length: int = 100) -> str:
    raw = clean_search_excerpt(text, locale, max_length=max_length)
    if not raw:
        return ""
    if len(raw) > 42 and not re.search(r"[。！？.!?；;:：]", raw):
        return ""
    if re.search(r"(好评率|接诊量|平均响应|国内一流|全国领先|top\s*ranked)", raw, re.IGNORECASE):
        return ""
    sentences = re.split(r"(?<=[。！？!?])\s+|(?<=[.;；])\s+", raw)
    clean = sentences[0].strip() if sentences else raw
    return trim_text(clean, max_length)


def clean_hospital_doctor(text: str, locale: str) -> str:
    doctor = trim_text(strip_search_noise(extract_doctor_name(text) or ""), 24)
    if doctor and not re.search(r"(外科|内科|门诊|中心|肝胆|心内|内分泌|营养科|运动医学).*(医生|医师|专家)$", doctor):
        return doctor
    cleaned = strip_search_noise(text)
    if re.search(r"(专家|specialist|主任医师|副主任医师)", cleaned, re.IGNORECASE):
        name_match = re.search(r"([\u4e00-\u9fff]{2,3}(?:主任医师|副主任医师|教授))", cleaned)
        if name_match:
            return trim_text(name_match.group(1), 24)
    return localize(locale, "优先预约专家门诊", "Prioritize specialist clinic")


def build_condition_hospital_reason(hospital: str, primary_condition: str, locale: str) -> str:
    name = str(hospital or "")
    lowered = name.lower()
    teaching = any(token in name for token in ("大学", "附属")) or "teaching" in lowered
    medical_center = any(token in name for token in ("医学中心", "医疗中心")) or "medical center" in lowered
    peoples_hospital = "人民医院" in name or "people" in lowered

    if primary_condition == "gallstones":
        if teaching:
            return localize(locale, "教学医院通常具备更完整的肝胆影像与多学科协作资源，适合结合彩超、肝功能和手术时机一起评估。", "Teaching hospitals usually offer stronger hepatobiliary imaging and multidisciplinary support for ultrasound, liver tests, and surgical-timing review.")
        if peoples_hospital or medical_center:
            return localize(locale, "综合检查资源较全，适合先完成肝胆彩超、肝功能和症状复盘，再决定是否需要外科进一步评估。", "Broader diagnostic access makes this a practical place to complete ultrasound, liver tests, and symptom review before deciding on surgical follow-up.")
        return localize(locale, "适合先做肝胆专科门诊评估，并结合症状频次与影像结果判断后续复查或治疗节奏。", "This is a sensible option for an initial hepatobiliary clinic review tied to symptom frequency and imaging results.")
    if primary_condition == "hypertension":
        if teaching:
            return localize(locale, "教学医院更适合联合评估血压波动、用药副作用和靶器官风险，便于后续长期随访。", "Teaching hospitals are a stronger fit for blood-pressure variability, medication side effects, and target-organ risk over longer follow-up.")
        return localize(locale, "适合完成血压波动、并发症风险和长期降压方案的系统复盘。", "This is suitable for a structured review of blood-pressure variability, complication risk, and longer-term medication planning.")
    if primary_condition == "diabetes":
        if teaching:
            return localize(locale, "教学医院更利于把 HbA1c、血糖监测、营养管理和并发症筛查放在一次复盘里完成。", "Teaching hospitals are better suited to combine HbA1c, glucose logs, nutrition planning, and complication screening in one review.")
        return localize(locale, "适合联合复盘血糖趋势、饮食结构和后续并发症筛查安排。", "This option fits a combined review of glucose trends, meal structure, and complication-screening plans.")
    if primary_condition == "fat_loss":
        return localize(locale, "适合结合体重、体脂和训练恢复状态进行结构化复盘，必要时再追加营养或运动医学评估。", "This clinic can support a structured review of weight, body fat, and recovery before escalating to nutrition or sports medicine when needed.")
    return localize(locale, "适合先完成门诊评估，再根据检查结果决定后续复查或转诊。", "This is appropriate for an initial clinic review before deciding on further follow-up or referral.")


def normalize_hospital_recommendation(
    item: dict,
    primary_condition: str,
    default_department: str,
    locale: str,
    fallback_reason: str = "",
) -> Optional[dict]:
    hospital = extract_hospital_name(item.get("hospital", "")) or str(item.get("hospital", "")).strip()
    if not is_valid_hospital_name(hospital):
        return None

    department = trim_text(
        strip_search_noise(item.get("department") or default_department or localize(locale, "肝胆外科 / 普外科", "Hepatobiliary surgery / general surgery")),
        28,
    )
    doctor = clean_hospital_doctor(item.get("doctor", "") or item.get("source_excerpt", ""), locale)
    source_excerpt = clean_search_excerpt(item.get("source_excerpt", ""), locale, max_length=140)
    reason = clean_hospital_reason(item.get("reason", "") or source_excerpt, locale, max_length=100)
    if not reason:
        reason = fallback_reason or build_condition_hospital_reason(hospital, primary_condition, locale)

    return {
        "hospital": trim_text(hospital, 32),
        "department": department,
        "doctor": doctor,
        "reason": reason,
        "url": "",
        "source_excerpt": source_excerpt,
    }


def refine_hospital_recommendations_with_llm(
    candidates: List[dict], monthly_data: dict, config: dict, locale: str
) -> List[dict]:
    if not candidates:
        return []

    payload = [
        {
            "hospital": item.get("hospital", ""),
            "department": item.get("department", ""),
            "doctor": item.get("doctor", ""),
            "reason": item.get("reason", ""),
            "source_excerpt": item.get("source_excerpt", ""),
        }
        for item in candidates[:4]
    ]
    prompt = localize(
        locale,
        f"""请把以下医院候选严格清洗成 JSON 数组，字段只能保留 hospital、department、doctor、reason。

要求：
1. 你在推荐医院时，必须进行严格的数据清洗。
2. 严禁输出网页导航文本、视频时间轴或冗长的追踪链接。
3. 推荐格式必须严格固定为：
- 医院名称
- 推荐科室：xxx
- 推荐医生：xxx
- 推荐理由：用一句话概括其在肝胆专科的优势，不超过100字。
4. 只返回 JSON 数组，不要返回 Markdown，不要解释。
5. 如果医生信息不可靠，请写“优先预约专家门诊”。
6. 管理目标：{monthly_data.get('condition_text', '')}；常居地：{monthly_data.get('residence_text', '')}。

候选数据：
{json.dumps(payload, ensure_ascii=False, indent=2)}""",
        f"""Clean the following hospital candidates into a strict JSON array. Allowed keys: hospital, department, doctor, reason.

Rules:
1. You must aggressively clean the data.
2. Never output navigation text, video timeline text, or long tracking links.
3. Keep the final structure equivalent to:
- Hospital name
- Department: xxx
- Doctor: xxx
- Reason: one concise sentence on specialty fit, under 100 characters.
4. Return JSON only. No markdown. No explanation.
5. If the doctor field is unreliable, use "Prioritize specialist clinic".
6. Condition focus: {monthly_data.get('condition_text', '')}; residence: {monthly_data.get('residence_text', '')}.

Candidate data:
{json.dumps(payload, ensure_ascii=False, indent=2)}""",
    )
    output = run_local_llm(
        prompt=prompt,
        system_prompt=localize(
            locale,
            "你是医疗信息清洗助手。你只做结构化提取和数据去噪，不添加宣传语，不输出链接，不编造信息。",
            "You are a medical data-cleaning assistant. Only extract and denoise structured data. No links, no hype, no fabrication.",
        ),
        settings=get_generation_settings(config, "expert_commentary"),
        locale=locale,
        timeout_key="ai_comment_timeout",
        failure_key="ai_comment_failed",
    )
    if not output:
        return []

    try:
        match = re.search(r"\[.*\]", output, re.DOTALL)
        parsed = json.loads(match.group(0) if match else output)
    except Exception:
        return []

    cleaned = []
    primary_condition = monthly_data.get("primary_condition") or monthly_data.get("conditions", ["gallstones"])[0]
    for item in parsed if isinstance(parsed, list) else []:
        if not isinstance(item, dict):
            continue
        normalized = normalize_hospital_recommendation(
            item,
            primary_condition,
            item.get("department") or localize(locale, "肝胆外科 / 普外科", "Hepatobiliary surgery / general surgery"),
            locale,
            fallback_reason=build_condition_hospital_reason(item.get("hospital", ""), primary_condition, locale),
        )
        if normalized:
            cleaned.append(normalized)
    return cleaned[:4]


def build_hospital_recommendations(monthly_data: dict, profile: dict, locale: str, config: Optional[dict] = None) -> tuple[List[dict], str]:
    residence = monthly_data.get("residence", {}) or {}
    residence_text = residence.get("display_name", "")
    residence_label = residence.get("city") or residence_text
    if not residence_text:
        return [], "fallback"
    location_hints = [str(item or "").strip() for item in [residence.get("province"), residence.get("city"), residence_text] if str(item or "").strip()]

    condition_queries = {
        "gallstones": {
            "department": localize(locale, "肝胆外科 / 普外科", "Hepatobiliary surgery / general surgery"),
            "query": localize(locale, f"{residence_text} 胆结石 慢性胆囊炎 三甲医院 肝胆外科 专家门诊", f"{residence_text} gallstones chronic cholecystitis top hospital hepatobiliary surgery specialist clinic"),
            "reason": localize(locale, "适合需要结合彩超、症状频次和胆囊炎风险一起评估的情况。", "This fits cases that need combined review of ultrasound, symptom frequency, and chronic gallbladder inflammation risk."),
        },
        "hypertension": {
            "department": localize(locale, "心内科 / 高血压门诊", "Cardiology / hypertension clinic"),
            "query": localize(locale, f"{residence_text} 高血压 三甲医院 心内科 高血压门诊 专家", f"{residence_text} hypertension top hospital cardiology hypertension clinic specialist"),
            "reason": localize(locale, "更适合评估血压波动、靶器官风险和长期用药调整。", "This is a better fit for blood-pressure variability, target-organ risk, and long-term medication adjustment."),
        },
        "diabetes": {
            "department": localize(locale, "内分泌科 / 糖尿病门诊", "Endocrinology / diabetes clinic"),
            "query": localize(locale, f"{residence_text} 糖尿病 三甲医院 内分泌科 专家门诊", f"{residence_text} diabetes top hospital endocrinology specialist clinic"),
            "reason": localize(locale, "更适合联合评估血糖、HbA1c、并发症筛查与饮食用药方案。", "This fits combined review of glucose, HbA1c, complication screening, and treatment planning."),
        },
        "fat_loss": {
            "department": localize(locale, "临床营养科 / 运动医学门诊", "Clinical nutrition / sports medicine"),
            "query": localize(locale, f"{residence_text} 临床营养科 运动医学 减脂 门诊 医院", f"{residence_text} clinical nutrition sports medicine fat loss clinic hospital"),
            "reason": localize(locale, "更适合平台期、体脂管理和训练恢复问题的结构化复盘。", "This is a stronger fit for plateau review, body-fat management, and training recovery."),
        },
    }

    recommendations = []
    if has_tavily_api_key(config):
        seen = set()
        for condition in monthly_data.get("conditions", []):
            meta = condition_queries.get(condition)
            if not meta:
                continue
            results = tavily_search(meta["query"], max_results=4, config=config)
            for result in results:
                raw_title = str(result.get("title") or "").strip()
                content = strip_search_noise(str(result.get("content", "") or ""))
                hospital = extract_hospital_name(f"{raw_title} {content}") or raw_title or localize(locale, f"{residence_text} 重点医院", f"{residence_text} key hospital")
                raw_blob = f"{raw_title} {content} {hospital}"
                if location_hints and not any(hint in raw_blob for hint in location_hints):
                    continue
                if not is_valid_hospital_name(hospital):
                    continue
                dedupe_key = hospital.lower()
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                cleaned_excerpt = clean_search_excerpt(content, locale, max_length=180)
                normalized = normalize_hospital_recommendation(
                    {
                        "hospital": hospital,
                        "department": meta["department"],
                        "doctor": f"{hospital} {content}",
                        "reason": cleaned_excerpt,
                        "source_excerpt": cleaned_excerpt,
                    },
                    condition,
                    meta["department"],
                    locale,
                    fallback_reason=build_condition_hospital_reason(hospital, condition, locale),
                )
                if normalized:
                    recommendations.append(normalized)
                if len(recommendations) >= 6:
                    break

        llm_cleaned = refine_hospital_recommendations_with_llm(recommendations, monthly_data, config or {}, locale)
        if llm_cleaned:
            recommendations = llm_cleaned

    primary_condition = monthly_data.get("primary_condition")
    meta = condition_queries.get(primary_condition, next(iter(condition_queries.values())))
    fallback = [
        {
            "hospital": localize(locale, f"{residence_label} 三甲综合医院", f"Tertiary general hospital in {residence_label}"),
            "department": meta["department"],
            "doctor": localize(locale, "优先预约专家门诊", "Prioritize specialist clinic"),
            "reason": build_condition_hospital_reason(localize(locale, f"{residence_label} 三甲综合医院", f"Tertiary general hospital in {residence_label}"), primary_condition, locale),
            "url": "",
        },
        {
            "hospital": localize(locale, f"{residence_label} 医学院附属医院", f"Teaching hospital in {residence_label}"),
            "department": meta["department"],
            "doctor": localize(locale, "复诊或联合门诊", "Return visit or joint clinic"),
            "reason": build_condition_hospital_reason(localize(locale, f"{residence_label} 医学院附属医院", f"Teaching hospital in {residence_label}"), primary_condition, locale),
            "url": "",
        },
        {
            "hospital": localize(locale, f"{residence_label} 区域医疗中心", f"Regional medical center in {residence_label}"),
            "department": meta["department"],
            "doctor": localize(locale, "先做门诊评估，再决定是否转上级医院", "Start with clinic evaluation and escalate if needed"),
            "reason": build_condition_hospital_reason(localize(locale, f"{residence_label} 区域医疗中心", f"Regional medical center in {residence_label}"), primary_condition, locale),
            "url": "",
        },
    ]
    if has_tavily_api_key(config):
        existing = {item.get("hospital", "").lower() for item in recommendations}
        blended = list(recommendations)
        for item in fallback:
            dedupe_key = item.get("hospital", "").lower()
            if dedupe_key in existing:
                continue
            blended.append(item)
            existing.add(dedupe_key)
            if len(blended) >= 4:
                break
        if blended:
            return blended, "fallback_tavily"
    return fallback, "fallback"


def build_monthly_fallback_review(monthly_data: dict, profile: dict, locale: str, config: Optional[dict] = None) -> tuple[str, str]:
    macro_scores = monthly_data.get("macro_scores", {})
    low_dims = [
        label
        for key, label in [
            ("diet", localize(locale, "饮食", "diet")),
            ("water", localize(locale, "饮水", "hydration")),
            ("exercise", localize(locale, "运动", "exercise")),
            ("monitoring", localize(locale, "监测", "monitoring")),
        ]
        if macro_scores.get(key, 0) < 70
    ]
    symptom_distribution = monthly_data.get("symptom_distribution", {})
    top_symptoms = list(symptom_distribution.items())[:2]
    symptom_text = (
        "、".join(f"{label} {count}次" for label, count in top_symptoms)
        if resolve_locale(locale=locale) == "zh-CN"
        else ", ".join(f"{label} {count}x" for label, count in top_symptoms)
    )

    findings = localize(
        locale,
        f"本月围绕 {monthly_data.get('condition_text')} 进行管理，月均综合评分 {monthly_data.get('avg_total_score', 0):.1f}/100。饮食、饮水、运动、用药、监测完成度分别为 {macro_scores.get('diet', 0):.0f}% / {macro_scores.get('water', 0):.0f}% / {macro_scores.get('exercise', 0):.0f}% / {macro_scores.get('medication', 0):.0f}% / {macro_scores.get('monitoring', 0):.0f}%。",
        f"This month focused on {monthly_data.get('condition_text')} management, with an average overall score of {monthly_data.get('avg_total_score', 0):.1f}/100. Diet, hydration, exercise, medication, and monitoring completion landed at {macro_scores.get('diet', 0):.0f}% / {macro_scores.get('water', 0):.0f}% / {macro_scores.get('exercise', 0):.0f}% / {macro_scores.get('medication', 0):.0f}% / {macro_scores.get('monitoring', 0):.0f}%.",
    )

    risk_parts = [
        localize(
            locale,
            f"本月记录到 {monthly_data.get('symptom_days', 0)} 天症状、{monthly_data.get('medication_days', 0)} 天用药、{monthly_data.get('monitoring_days', 0)} 天监测。",
            f"This month included {monthly_data.get('symptom_days', 0)} symptom days, {monthly_data.get('medication_days', 0)} medication days, and {monthly_data.get('monitoring_days', 0)} monitoring days.",
        )
    ]
    if symptom_text:
        risk_parts.append(localize(locale, f"症状以 {symptom_text} 为主。", f"The symptom mix was led by {symptom_text}."))

    primary_condition = monthly_data.get("primary_condition")
    if primary_condition == "gallstones":
        risk_parts.append(
            localize(
                locale,
                f"胆结石专项上，月均脂肪摄入约 {monthly_data.get('avg_fat', 0):.1f}g。若高脂日与不适日重叠，需要重点复盘晚餐和加餐。",
                f"For gallstone care, average fat intake was about {monthly_data.get('avg_fat', 0):.1f}g. If higher-fat days overlap with symptoms, dinner and snack patterns need closer review.",
            )
        )
    elif primary_condition == "hypertension":
        risk_parts.append(
            localize(
                locale,
                "若血压箱线图离散度偏大，说明波动仍明显，需要回看作息、盐分与服药时间。",
                "If the blood-pressure boxplot stays wide, variability remains meaningful and sleep, sodium, and medication timing deserve review.",
            )
        )
    elif primary_condition == "fat_loss":
        risk_parts.append(
            localize(
                locale,
                f"体重月变化约 {monthly_data.get('weight_change', 0):.2f}kg，若下降过快也要警惕恢复不足与胆囊刺激。",
                f"Monthly weight change was about {monthly_data.get('weight_change', 0):.2f}kg; if the drop is too fast, recovery strain and gallbladder irritation are still worth watching.",
            )
        )

    plan_parts = [
        localize(
            locale,
            "下月建议优先把低分维度拉稳，再继续做病种专项对照。",
            "Next month should first stabilize the weaker adherence dimensions, then continue disease-specific comparisons.",
        )
    ]
    if low_dims:
        gap_text = "、".join(low_dims) if resolve_locale(locale=locale) == "zh-CN" else ", ".join(low_dims)
        plan_parts.append(localize(locale, f"当前优先级最高的是：{gap_text}。", f"The highest-priority gaps now are: {gap_text}."))
    plan_parts.append(
        localize(
            locale,
            "建议把诱因、症状持续时间、复查结果继续写进日记，月报中的趋势图会更有判断价值。",
            "Keep logging triggers, symptom duration, and follow-up results so next month's charts become more clinically useful.",
        )
    )

    sections = [
        ("核心发现", "Key Findings", " ".join(findings.split())),
        ("风险提示", "Risk Watch", " ".join(" ".join(risk_parts).split())),
        ("下月调整", "Next-Month Actions", " ".join(" ".join(plan_parts).split())),
    ]

    source = "fallback"
    gap_topics = []
    for key, label in [("diet", "diet"), ("water", "hydration"), ("exercise", "exercise"), ("monitoring", "monitoring")]:
        if macro_scores.get(key, 0) < 70:
            gap_topics.append(label)
    if has_tavily_api_key(config) and gap_topics:
        query = localize(
            locale,
            f"{monthly_data.get('condition_text')} 患者教育 月度管理 {' '.join(gap_topics[:3])} 复盘建议",
            f"{monthly_data.get('condition_text')} patient education monthly self-management review {' '.join(gap_topics[:3])}",
        )
        search_results = tavily_search(query, max_results=2, config=config)
        snippets = []
        for result in search_results:
            content = clean_search_excerpt(str(result.get("content", "") or ""), locale, max_length=150)
            if content:
                snippets.append(content)
        if snippets:
            sections.append(("检索补充", "Retrieved Note", snippets[0]))
            source = "fallback_tavily"

    return format_monthly_review_sections(locale, sections), source


def get_ai_monthly_review(monthly_data: dict, profile: dict, config: dict, locale: str) -> tuple[str, str]:
    prompt = localize(
        locale,
        f"""请根据以下 30 天健康数据生成一段约 260-320 字的月度病情研判，并严格按以下结构输出，不要添加其他标题或前言：
**【核心发现】**
2-3 句，总结本月整体状态、依从性、关键趋势。

**【风险提示】**
2 句，指出本月最需要警惕的触发因素或监测不足。

**【下月调整】**
2-3 句，给出下个月最可执行的调整方向。

用户：{profile.get('name', '用户')}
病种/目标：{monthly_data.get('condition_text')}
月均综合评分：{monthly_data.get('avg_total_score', 0):.1f}
饮食/饮水/运动/用药/监测达标率：{json.dumps(monthly_data.get('macro_scores', {}), ensure_ascii=False)}
月均热量：{monthly_data.get('avg_calories', 0):.0f} kcal
月均饮水：{monthly_data.get('avg_water', 0):.0f} ml
月均步数：{monthly_data.get('avg_steps', 0):.0f}
症状天数：{monthly_data.get('symptom_days', 0)}
症状次数：{monthly_data.get('symptom_events', 0)}
用药天数：{monthly_data.get('medication_days', 0)}
监测天数：{monthly_data.get('monitoring_days', 0)}
专项亮点：{" | ".join(monthly_data.get('macro_highlights', []))}
症状分布：{json.dumps(monthly_data.get('symptom_distribution', {}), ensure_ascii=False)}
请务必按上述 3 个小标题输出。""",
        f"""Write an approximately 180-230 word monthly clinical-style review and follow this exact structure with no extra intro:
**[Key Findings]**
2-3 sentences on overall status, adherence, and trend direction.

**[Risk Watch]**
2 sentences on the biggest watch-outs or missing monitoring.

**[Next-Month Actions]**
2-3 sentences on the most actionable adjustments for next month.

User: {profile.get('name', 'User')}
Conditions/goals: {monthly_data.get('condition_text')}
Average overall score: {monthly_data.get('avg_total_score', 0):.1f}
Goal rates: {json.dumps(monthly_data.get('macro_scores', {}), ensure_ascii=False)}
Average calories: {monthly_data.get('avg_calories', 0):.0f} kcal
Average hydration: {monthly_data.get('avg_water', 0):.0f} ml
Average steps: {monthly_data.get('avg_steps', 0):.0f}
Symptom days: {monthly_data.get('symptom_days', 0)}
Symptom events: {monthly_data.get('symptom_events', 0)}
Medication days: {monthly_data.get('medication_days', 0)}
Monitoring days: {monthly_data.get('monitoring_days', 0)}
Highlights: {" | ".join(monthly_data.get('macro_highlights', []))}
Symptom mix: {json.dumps(monthly_data.get('symptom_distribution', {}), ensure_ascii=False)}
Return the review with those exact three section headings.""",
    )

    output = run_local_llm(
        prompt=prompt,
        system_prompt=localize(locale, "你是一位谨慎、专业的健康数据分析师。", "You are a careful and professional health data analyst."),
        settings=get_generation_settings(config, "expert_commentary"),
        locale=locale,
        timeout_key="ai_comment_timeout",
        failure_key="weekly_ai_failed",
    )
    if output and len(output.strip()) > 60:
        return ensure_monthly_review_sections(output.strip(), monthly_data, locale), "llm"
    return build_monthly_fallback_review(monthly_data, profile, locale, config=config)


def build_custom_monitoring_summary(monthly_data: dict, locale: str) -> List[dict]:
    summary = []
    for section in monthly_data.get("custom_section_stats", []):
        if section.get("days_recorded", 0) <= 0:
            continue
        lines = [
            localize(locale, f"记录天数：{section.get('days_recorded', 0)} 天", f"Recorded on {section.get('days_recorded', 0)} days"),
            localize(locale, f"累计条目：{section.get('items', 0)} 条", f"Total items: {section.get('items', 0)}"),
        ]
        for item in section.get("latest_items", [])[:2]:
            lines.append(localize(locale, f"最近记录：{item}", f"Latest entry: {item}"))
        summary.append({"title": section.get("title", ""), "lines": lines})
    return summary[:4]


def generate_monthly_text_report(monthly_data: dict, profile: dict, ai_review: str, locale: str, review_source: str, recommendation_source: str) -> str:
    def section(title: str, icon: str) -> str:
        return f"{icon} {title}"

    profile_lines = [
        f"- 👤 {localize(locale, '姓名', 'Name')}: {profile.get('name', '-')}",
        f"- 🎯 {localize(locale, '管理目标', 'Conditions')}: {monthly_data.get('condition_text', '-')}",
        f"- 🗓️ {localize(locale, '周期', 'Period')}: {monthly_data.get('start_date')} ~ {monthly_data.get('end_date')}",
        f"- 📍 {localize(locale, '常居地', 'Residence')}: {monthly_data.get('residence_text') or localize(locale, '未配置', 'Not configured')}",
    ]
    summary_lines = [
        f"- 🏆 {localize(locale, '月均综合评分', 'Average overall score')}: {monthly_data.get('avg_total_score', 0):.1f}/100",
        f"- 🍽️ {localize(locale, '饮食达标率', 'Diet goal rate')}: {monthly_data.get('macro_scores', {}).get('diet', 0):.0f}%",
        f"- 💧 {localize(locale, '饮水达标率', 'Hydration goal rate')}: {monthly_data.get('macro_scores', {}).get('water', 0):.0f}%",
        f"- 🏃 {localize(locale, '运动达标率', 'Exercise goal rate')}: {monthly_data.get('macro_scores', {}).get('exercise', 0):.0f}%",
        f"- 💊 {localize(locale, '用药覆盖率', 'Medication coverage')}: {monthly_data.get('macro_scores', {}).get('medication', 0):.0f}%",
        f"- 🧪 {localize(locale, '监测覆盖率', 'Monitoring coverage')}: {monthly_data.get('macro_scores', {}).get('monitoring', 0):.0f}%",
        f"- 🩺 {localize(locale, '症状天数', 'Symptom days')}: {monthly_data.get('symptom_days', 0)}",
        f"- 💊 {localize(locale, '用药天数', 'Medication days')}: {monthly_data.get('medication_days', 0)}",
        f"- 🧪 {localize(locale, '监测天数', 'Monitoring days')}: {monthly_data.get('monitoring_days', 0)}",
    ]
    specialty_lines = [f"- 📈 {chart.get('title')}: {chart.get('summary')}" for chart in monthly_data.get("specialty_charts", [])[:4]]
    followup_lines = [f"- 🗓️ {item}" for item in monthly_data.get("follow_up_reminders", [])]
    recommendation_lines = []
    for item in monthly_data.get("hospital_recommendations", [])[:3]:
        recommendation_lines.extend(
            [
                f"- 🏥 {item.get('hospital')}",
                localize(locale, f"  🧭 推荐科室：{item.get('department')}", f"  🧭 Recommended department: {item.get('department')}"),
                localize(locale, f"  👨‍⚕️ 推荐医生：{item.get('doctor')}", f"  👨‍⚕️ Recommended doctor: {item.get('doctor')}"),
                localize(locale, f"  ✨ 推荐理由：{item.get('reason')}", f"  ✨ Recommendation reason: {item.get('reason')}"),
                "",
            ]
        )

    report_heading = f"{localize(locale, '健康月报', 'Monthly Health Report')} ({monthly_data.get('month_key')})"
    lines = [
        f"## {section(report_heading, '🗓️')}",
        "",
        f"### {section(localize(locale, '个人信息', 'Profile'), '👤')}",
        *profile_lines,
        "",
        f"### {section(localize(locale, '月度概览', 'Monthly Overview'), '🌐')}",
        *summary_lines,
        "",
        f"### {section(localize(locale, '本月亮点', 'Highlights'), '✨')}",
        *[f"- 🌟 {item}" for item in monthly_data.get("macro_highlights", [])],
        "",
        f"### {section(localize(locale, '专项趋势', 'Specialty Trends'), '📈')}",
        *(specialty_lines or [f"- 📉 {localize(locale, '当前专项图表数据仍不足，后续可通过血压/血糖/体脂/生化模块自动补齐。', 'Specialty chart data are still limited this month. Blood pressure, glucose, body-fat, and lab modules will automatically enrich future reports.')}"]),
        "",
        f"### {section(localize(locale, 'AI 月度病情研判', 'AI Monthly Review'), '🧠')}",
        ai_review.strip(),
        f"_{generation_source_label(locale, review_source)}_",
        "",
        f"### {section(localize(locale, '复查提醒', 'Follow-up Reminders'), '📌')}",
        *(followup_lines or [f"- 📭 {localize(locale, '当前没有额外复查提醒。', 'There are no extra follow-up reminders for now.')}"]),
        "",
        f"### {section(localize(locale, '医院与门诊建议', 'Hospital and Clinic Suggestions'), '🏥')}",
        *(recommendation_lines or [f"- 📍 {localize(locale, '请先在 user_config.json 中补充常居地后再生成更具体的医院推荐。', 'Add residence details to user_config.json to unlock more specific hospital recommendations.')}"]),
        f"_{generation_source_label(locale, recommendation_source)}_",
    ]
    render_notice = str(monthly_data.get("render_notice") or "").strip()
    if render_notice:
        lines.extend(["", f"### {section(localize(locale, '渲染说明', 'Rendering Notice'), 'ℹ️')}", render_notice])
    return "\n".join(lines).strip()


def publish_monthly_pdf(local_pdf_path: str) -> str:
    web_dir = os.environ.get("REPORT_WEB_DIR", "")
    base_url = os.environ.get("REPORT_BASE_URL", "").rstrip("/")
    if web_dir and os.path.exists(web_dir) and base_url:
        filename = os.path.basename(local_pdf_path)
        web_pdf_path = os.path.join(web_dir, filename)
        shutil.copy2(local_pdf_path, web_pdf_path)
        return f"{base_url}/{filename}"
    return local_pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 monthly_report_pro.py <YYYY-MM-DD>")
        sys.exit(1)

    target_date = sys.argv[1]
    base_config = load_user_config()
    month_dates = get_month_dates(target_date)
    month_files = [os.path.join(MEMORY_DIR, f"{date_str}.md") for date_str in month_dates]
    requested_locale = resolve_report_locale(base_config, month_files)
    fallback_context = prepare_font_compatible_memory(requested_locale=requested_locale, source_dir=MEMORY_DIR)
    temp_memory_dir = fallback_context.get("temp_dir")

    try:
        locale = fallback_context.get("locale") or requested_locale
        config = force_config_locale(base_config, locale)
        profile = config.get("user_profile", {})
        memory_dir = fallback_context.get("memory_dir") or MEMORY_DIR
        render_notice = str(fallback_context.get("render_notice") or "").strip()

        conditions = get_profile_conditions(profile)
        profile_payload = dict(profile)
        profile_payload["condition"] = get_primary_condition(profile)
        profile_payload["conditions"] = conditions
        profile_payload["condition_display"] = get_conditions_display_name(locale, conditions)

        monthly_data = aggregate_monthly_data(month_dates, config, locale=locale, memory_dir=memory_dir)
        monthly_data["macro_highlights"] = build_monthly_highlights(monthly_data, profile_payload, locale)
        monthly_data["specialty_charts"] = build_specialty_charts(monthly_data, config, locale)
        monthly_data["follow_up_reminders"] = build_follow_up_reminders(monthly_data, profile_payload, locale)
        monthly_data["hospital_recommendations"], recommendation_source = build_hospital_recommendations(monthly_data, profile_payload, locale, config=config)
        monthly_data["custom_monitoring_summary"] = build_custom_monitoring_summary(monthly_data, locale)
        if render_notice:
            monthly_data["render_notice"] = render_notice

        ai_review, review_source = get_ai_monthly_review(monthly_data, profile_payload, config, locale)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"monthly_report_{timestamp}.pdf"
        local_output_path = os.path.join(REPORTS_DIR, pdf_filename)

        generate_monthly_pdf_report(
            monthly_data,
            profile_payload,
            ai_review,
            local_output_path,
            locale=locale,
            review_source=review_source,
            recommendation_source=recommendation_source,
        )
        pdf_url = publish_monthly_pdf(local_output_path)
        text_report = generate_monthly_text_report(monthly_data, profile_payload, ai_review, locale, review_source, recommendation_source)
        delivery_message = build_delivery_message(
            locale=locale,
            body=text_report,
            pdf_url=pdf_url,
            report_kind="monthly",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            start_date=monthly_data["start_date"],
            end_date=monthly_data["end_date"],
        )

        print("=== TEXT_REPORT_START ===")
        print(text_report)
        print("=== TEXT_REPORT_END ===")
        print("=== PDF_URL ===")
        print(pdf_url)
        print("=== DELIVERY_MESSAGE_START ===")
        print(delivery_message)
        print("=== DELIVERY_MESSAGE_END ===")
    finally:
        if temp_memory_dir:
            temp_memory_dir.cleanup()
