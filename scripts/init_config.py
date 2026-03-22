#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive configuration wizard for Health-Mate."""

from __future__ import annotations

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_DIR.mkdir(exist_ok=True)

LANGUAGE_OPTIONS = {"1": "zh-CN", "2": "en-US", "3": "ja-JP"}
LANGUAGE_LABELS = {"zh-CN": "中文", "en-US": "English", "ja-JP": "日本語"}
GENDER_OPTIONS = {"1": "male", "2": "female"}
GENDER_LABELS = {
    "zh-CN": {"male": "男", "female": "女"},
    "en-US": {"male": "Male", "female": "Female"},
    "ja-JP": {"male": "男性", "female": "女性"},
}
CONDITION_OPTIONS = {
    "1": "gallstones",
    "2": "diabetes",
    "3": "hypertension",
    "4": "fat_loss",
    "5": "balanced",
}
CONDITION_LABELS = {
    "zh-CN": {
        "gallstones": "胆结石 / 慢性胆囊炎管理",
        "diabetes": "糖代谢管理",
        "hypertension": "血压管理",
        "fat_loss": "健身减脂",
        "balanced": "综合健康管理",
    },
    "en-US": {
        "gallstones": "Gallstone / Cholecystitis Care",
        "diabetes": "Glucose Management",
        "hypertension": "Blood Pressure Management",
        "fat_loss": "Fat Loss / Fitness",
        "balanced": "Balanced Wellness",
    },
    "ja-JP": {
        "gallstones": "胆石 / 慢性胆嚢炎ケア",
        "diabetes": "血糖管理",
        "hypertension": "血圧管理",
        "fat_loss": "減量・ボディメイク",
        "balanced": "総合ヘルスケア",
    },
}
ACTIVITY_OPTIONS = {
    "1": 1.2,
    "2": 1.375,
    "3": 1.55,
    "4": 1.725,
    "5": 1.9,
}
ACTIVITY_LABELS = {
    "zh-CN": {
        "1": "久坐 / 很少运动",
        "2": "轻度活动",
        "3": "中度活动",
        "4": "高强度活动",
        "5": "训练期 / 重体力",
    },
    "en-US": {
        "1": "Sedentary",
        "2": "Light activity",
        "3": "Moderate activity",
        "4": "High activity",
        "5": "Training / heavy labor",
    },
    "ja-JP": {
        "1": "座りがち / 運動ほぼなし",
        "2": "軽い活動",
        "3": "中程度の活動",
        "4": "高い活動量",
        "5": "トレーニング期 / 重労働",
    },
}

DEFAULT_CONDITION_STANDARDS = {
    "gallstones": {"fat_min_g": 40, "fat_max_g": 50, "fiber_min_g": 25, "water_min_ml": 2000},
    "diabetes": {"fat_min_g": 40, "fat_max_g": 55, "fiber_min_g": 30, "water_min_ml": 2000},
    "hypertension": {"fat_min_g": 40, "fat_max_g": 55, "fiber_min_g": 25, "water_min_ml": 2000, "sodium_max_mg": 2000},
    "fat_loss": {"fat_min_g": 40, "fat_max_g": 60, "fiber_min_g": 25, "water_min_ml": 2500},
    "balanced": {"fat_min_g": 40, "fat_max_g": 60, "fiber_min_g": 25, "water_min_ml": 2000},
}


def localize(locale: str, zh_text: str, en_text: str, ja_text: str | None = None) -> str:
    if locale == "zh-CN":
        return zh_text
    if locale == "ja-JP":
        return ja_text or en_text
    return en_text


def module_defaults(locale: str) -> list[dict]:
    defaults = {
        "zh-CN": [
            {"id": "diet", "title": "饮食合规性", "enabled": True, "weight": 20, "description": "基于脂肪、纤维、餐次结构和病种饮食原则评分。"},
            {"id": "water", "title": "饮水完成度", "enabled": True, "weight": 15, "description": "基于饮水目标完成率评分。"},
            {"id": "weight", "title": "体重管理", "enabled": True, "weight": 15, "description": "基于体重记录完整度与目标方向评分。"},
            {"id": "symptom", "title": "症状管理", "enabled": True, "weight": 15, "description": "基于症状记录、稳定性和风险情况评分。"},
            {"id": "exercise", "title": "运动管理", "enabled": True, "weight": 20, "description": "基于运动、步数和活动量评分。"},
            {"id": "adherence", "title": "健康依从性", "enabled": True, "weight": 15, "description": "基于记录完整性和连续性评分。"},
            {"id": "medication", "title": "用药情况", "enabled": False, "weight": 0, "description": "启用后会参与评分，并在日报/周报/PDF 中同步输出。", "type": "section_presence", "section_title": "用药记录"},
        ],
        "en-US": [
            {"id": "diet", "title": "Diet Compliance", "enabled": True, "weight": 20, "description": "Scored from fat, fiber, meal structure, and condition-aware diet rules."},
            {"id": "water", "title": "Hydration", "enabled": True, "weight": 15, "description": "Scored from water intake against the daily target."},
            {"id": "weight", "title": "Weight Management", "enabled": True, "weight": 15, "description": "Scored from weight logging and goal direction."},
            {"id": "symptom", "title": "Symptom Management", "enabled": True, "weight": 15, "description": "Scored from symptom logging, stability, and risks."},
            {"id": "exercise", "title": "Exercise Management", "enabled": True, "weight": 20, "description": "Scored from exercise, steps, and activity volume."},
            {"id": "adherence", "title": "Health Adherence", "enabled": True, "weight": 15, "description": "Scored from completeness and consistency of logging."},
            {"id": "medication", "title": "Medication", "enabled": False, "weight": 0, "description": "When enabled, it joins scoring and appears in daily/weekly PDFs.", "type": "section_presence", "section_title": "Medication"},
        ],
        "ja-JP": [
            {"id": "diet", "title": "食事管理", "enabled": True, "weight": 20, "description": "脂質・食物繊維・食事構成と疾患別ルールで評価します。"},
            {"id": "water", "title": "水分管理", "enabled": True, "weight": 15, "description": "目標水分量に対する達成度で評価します。"},
            {"id": "weight", "title": "体重管理", "enabled": True, "weight": 15, "description": "体重記録の継続性と目標方向で評価します。"},
            {"id": "symptom", "title": "症状管理", "enabled": True, "weight": 15, "description": "症状記録、安定性、リスクで評価します。"},
            {"id": "exercise", "title": "運動管理", "enabled": True, "weight": 20, "description": "運動、歩数、活動量で評価します。"},
            {"id": "adherence", "title": "記録遵守", "enabled": True, "weight": 15, "description": "記録の完全性と継続性で評価します。"},
            {"id": "medication", "title": "服薬状況", "enabled": False, "weight": 0, "description": "有効にすると採点対象になり、日報・週報 PDF にも出力されます。", "type": "section_presence", "section_title": "服薬記録"},
        ],
    }
    return [dict(item) for item in defaults[locale]]


def prompt_input(message: str) -> str:
    return input(f"{message}\n> ").strip()


def ask_text(message: str, retry: str) -> str:
    while True:
        value = prompt_input(message)
        if value:
            return value
        print(retry)


def ask_number(message: str, retry: str, cast=float, min_value=None):
    while True:
        raw = prompt_input(message)
        try:
            value = cast(raw)
            if min_value is not None and value < min_value:
                raise ValueError
            return value
        except (TypeError, ValueError):
            print(retry)


def ask_choice(message: str, retry: str, options: dict):
    while True:
        raw = prompt_input(message)
        if raw in options:
            return options[raw]
        print(retry)


def ask_multi_choice(message: str, retry: str, options: dict) -> list[str]:
    while True:
        raw = prompt_input(message)
        values = []
        for part in re.split(r"[,\s，]+", raw):
            if not part:
                continue
            if part not in options:
                values = []
                break
            resolved = options[part]
            if resolved not in values:
                values.append(resolved)
        if values:
            return values
        print(retry)


def ask_optional_list(message: str) -> list[str]:
    raw = prompt_input(message)
    return [part.strip() for part in re.split(r"[，,]+", raw) if part.strip()]


def ask_yes_no(message: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    raw = prompt_input(f"{message} ({suffix})").lower()
    if not raw:
        return default
    return raw in {"y", "yes", "1", "true", "是", "はい"}


def build_ai_generation(ai_mode: str) -> dict:
    mode = "hybrid" if ai_mode == "hybrid" else "local_only"
    return {
        "expert_commentary": {"mode": mode, "max_attempts": 3, "timeout_seconds": 90},
        "next_day_plan": {"mode": mode, "max_attempts": 3, "timeout_seconds": 90},
        "risk_alerts": {"mode": "local"},
    }


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", text.lower()).strip("_") or "custom_section"


def build_display_name(locale: str, country: str, province: str, city: str, district: str) -> str:
    parts = [part for part in [province, city, district] if part]
    if locale == "zh-CN":
        return "".join(parts)
    if locale == "ja-JP":
        return " ".join(parts or [country]).strip()
    return ", ".join([part for part in [district, city, province, country] if part])


def main() -> None:
    print("=" * 60)
    print("Health-Mate Setup Wizard")
    print("=" * 60)
    print("1. 中文")
    print("2. English")
    print("3. 日本語")

    language_choice = input("> ").strip()
    while language_choice not in LANGUAGE_OPTIONS:
        print("Please enter 1, 2, or 3.")
        language_choice = input("> ").strip()

    locale = LANGUAGE_OPTIONS[language_choice]
    print()
    print(localize(locale, "欢迎使用 Health-Mate 初始化向导。", "Welcome to the Health-Mate setup wizard.", "Health-Mate の初期設定ウィザードへようこそ。"))
    print(localize(locale, "本向导会把完整配置写入 config/user_config.json。", "This wizard writes the full configuration into config/user_config.json.", "このウィザードは設定を config/user_config.json に保存します。"))
    print(localize(locale, "建议首次安装时把所有正在管理的疾病/目标一次性配置完整。", "For first-time setup, configure every active condition or goal together.", "初回設定では、管理中の疾患や目標をまとめて設定してください。"))
    input(f"{localize(locale, '按回车开始。', 'Press Enter to start.', 'Enter キーで開始します。')}\n")

    print(localize(locale, "\n[步骤 1/4] 基本档案", "\n[Step 1/4] Basic profile", "\n[手順 1/4] 基本プロフィール"))
    name = ask_text(localize(locale, "请输入姓名或昵称", "Your name or nickname", "名前またはニックネーム"), localize(locale, "请输入有效内容。", "Please enter a value.", "入力してください。"))
    gender = ask_choice(
        localize(locale, "性别：1 男 / 2 女", "Gender: 1 Male / 2 Female", "性別: 1 男性 / 2 女性"),
        localize(locale, "请输入 1 或 2。", "Please enter 1 or 2.", "1 または 2 を入力してください。"),
        GENDER_OPTIONS,
    )
    age = ask_number(localize(locale, "年龄（例如 34）", "Age (for example 34)", "年齢（例: 34）"), localize(locale, "请输入有效年龄。", "Please enter a valid age.", "有効な年齢を入力してください。"), cast=int, min_value=1)
    height = ask_number(localize(locale, "身高 cm（例如 172）", "Height in cm (for example 172)", "身長 cm（例: 172）"), localize(locale, "请输入有效身高。", "Please enter a valid height.", "有効な身長を入力してください。"), cast=int, min_value=50)
    current_weight = ask_number(localize(locale, "当前体重 kg（例如 65.5）", "Current weight in kg (for example 65.5)", "現在の体重 kg（例: 65.5）"), localize(locale, "请输入有效体重。", "Please enter a valid weight.", "有効な体重を入力してください。"), cast=float, min_value=1)
    target_weight = ask_number(localize(locale, "目标体重 kg", "Target weight in kg", "目標体重 kg"), localize(locale, "请输入有效目标体重。", "Please enter a valid target weight.", "有効な目標体重を入力してください。"), cast=float, min_value=1)

    print(localize(locale, "\n[步骤 2/4] 多疾病 / 多目标配置", "\n[Step 2/4] Multi-condition setup", "\n[手順 2/4] 複数疾患・複数目標の設定"))
    print(localize(locale, "请把当前正在管理的疾病、减脂目标或健康目标都勾上。系统会自动合并更严格的阈值。", "Select all active conditions and goals. Health-Mate will merge stricter thresholds automatically.", "現在管理中の疾患や目標をすべて選択してください。しきい値は自動的に厳しい方へ統合されます。"))
    for key, condition in CONDITION_OPTIONS.items():
        print(f"{key}. {CONDITION_LABELS[locale][condition]}")
    conditions = ask_multi_choice(
        localize(locale, "请输入一个或多个编号，逗号分隔（例如 1,3,4）", "Enter one or more numbers, separated by commas (for example 1,3,4)", "番号を 1 つ以上入力してください（例: 1,3,4）"),
        localize(locale, "请输入有效编号。", "Please enter valid numbers.", "有効な番号を入力してください。"),
        CONDITION_OPTIONS,
    )
    selected_map = {str(index + 1): value for index, value in enumerate(conditions)}
    print(localize(locale, "你已选择：", "You selected:", "選択内容:"))
    for index, condition in selected_map.items():
        print(f"{index}. {CONDITION_LABELS[locale][condition]}")
    primary_condition = ask_choice(
        localize(locale, "请选择主视图疾病 / 目标编号（标题和 AI 提示优先使用它）", "Choose the primary condition / goal number used for titles and AI prompts", "主表示に使う疾患 / 目標の番号を選択してください"),
        localize(locale, "请输入上面显示的编号。", "Please enter one of the numbers shown above.", "表示された番号を入力してください。"),
        selected_map,
    )

    water_target = ask_number(localize(locale, "每日饮水目标 ml", "Daily hydration target in ml", "1 日の水分目標 ml"), localize(locale, "请输入有效饮水目标。", "Please enter a valid target.", "有効な目標を入力してください。"), cast=int, min_value=500)
    step_target = ask_number(localize(locale, "每日步数目标", "Daily step target", "1 日の歩数目標"), localize(locale, "请输入有效步数目标。", "Please enter a valid target.", "有効な目標を入力してください。"), cast=int, min_value=500)
    print(localize(locale, "活动系数：", "Activity factor:", "活動係数:"))
    for key, label in ACTIVITY_LABELS[locale].items():
        print(f"{key}. {label}")
    activity_level = ask_choice(
        localize(locale, "请选择活动系数", "Choose the activity factor", "活動係数を選択してください"),
        localize(locale, "请输入 1-5。", "Please enter 1-5.", "1-5 を入力してください。"),
        ACTIVITY_OPTIONS,
    )
    dislikes = ask_optional_list(localize(locale, "尽量回避的食物（可选，逗号分隔）", "Foods to avoid when possible (optional, comma-separated)", "できるだけ避けたい食品（任意、カンマ区切り）"))
    allergies = ask_optional_list(localize(locale, "过敏食物（可选，逗号分隔）", "Food allergies (optional, comma-separated)", "アレルギー食品（任意、カンマ区切り）"))
    favorite_fruits = ask_optional_list(localize(locale, "常吃或偏好的水果（可选，逗号分隔）", "Favorite fruits (optional, comma-separated)", "よく食べる果物（任意、カンマ区切り）"))

    print(localize(locale, "为了支持月报中的医院推荐和复查建议，请填写常居地。", "To support monthly hospital recommendations and follow-up reminders, add your residence details.", "月報の病院推薦と受診リマインドのため、居住地を入力してください。"))
    residence_country = ask_text(localize(locale, "国家 / 地区", "Country / region", "国 / 地域"), localize(locale, "请输入有效国家 / 地区。", "Please enter a country / region.", "国 / 地域を入力してください。"))
    residence_province = ask_text(localize(locale, "省 / 州", "Province / state", "都道府県 / 州"), localize(locale, "请输入有效省 / 州。", "Please enter a province / state.", "都道府県 / 州を入力してください。"))
    residence_city = ask_text(localize(locale, "城市", "City", "市区町村"), localize(locale, "请输入有效城市。", "Please enter a city.", "市区町村を入力してください。"))
    residence_district = prompt_input(localize(locale, "区 / 县 / 地域（可选）", "District / area (optional)", "地区 / エリア（任意）"))

    print(localize(locale, "\n[步骤 3/4] AI、模块与权重", "\n[Step 3/4] AI, modules, and weights", "\n[手順 3/4] AI・モジュール・重み"))
    print(localize(locale, "- 权重不必手工凑满 100，运行时会自动归一化。", "- Weights do not need to add up to 100. Runtime normalization is automatic.", "- 重みを手動で 100 に合わせる必要はありません。実行時に自動で正規化されます。"))
    print(localize(locale, "- 如果填写 TAVILY_API_KEY，本地回退内容还能叠加 Tavily 检索结果。", "- If you provide TAVILY_API_KEY, local fallback content can be enriched with Tavily retrieval.", "- TAVILY_API_KEY を設定すると、ローカル回退に Tavily 検索を追加できます。"))
    print(localize(locale, "- 用药模块和自定义模块启用后，会参与评分，并在日报/周报/PDF 中同步输出。", "- Medication and custom modules can join scoring and also appear in daily/weekly PDF output.", "- 服薬モジュールとカスタムモジュールは、採点対象と PDF 出力の両方に反映されます。"))

    ai_mode_choice = ask_choice(
        localize(locale, "AI 模式：1 混合模式（推荐，先 LLM，再动态本地回退） / 2 仅动态本地规则", "AI mode: 1 Hybrid (recommended, LLM first then dynamic local fallback) / 2 Dynamic local rules only", "AI モード: 1 ハイブリッド（推奨。LLM 優先 + 動的ローカル回退） / 2 動的ローカルルールのみ"),
        localize(locale, "请输入 1 或 2。", "Please enter 1 or 2.", "1 または 2 を入力してください。"),
        {"1": "hybrid", "2": "local_only"},
    )
    tavily_api_key = prompt_input(localize(locale, "可选：输入 Tavily API Key（直接回车跳过）", "Optional: enter a Tavily API key (press Enter to skip)", "任意: Tavily API Key を入力してください（Enter でスキップ）"))
    append_custom_sections = ask_yes_no(localize(locale, "是否在报告中动态追加自定义监控模块？", "Append custom monitoring sections into reports?", "カスタム監視モジュールをレポートに追加しますか?"), default=True)

    modules = []
    for module in module_defaults(locale):
        enabled = ask_yes_no(f"{module['title']} - {module['description']}", default=module.get("enabled", True))
        weight = ask_number(
            localize(locale, f"为「{module['title']}」设置权重（0-100 任意数值都可以）", f"Set the weight for \"{module['title']}\" (any number from 0-100 is fine)", f"「{module['title']}」の重みを設定してください（0-100 の任意値）"),
            localize(locale, "请输入有效数字。", "Please enter a valid number.", "有効な数値を入力してください。"),
            cast=float,
            min_value=0,
        ) if enabled else 0
        module_data = {
            "id": module["id"],
            "type": module.get("type", "builtin"),
            "title": module["title"],
            "enabled": enabled,
            "weight": weight,
        }
        if module_data["type"] == "section_presence":
            module_data["section_title"] = module.get("section_title", module["title"])
            module_data["score_when_present"] = 100
            module_data["score_when_missing"] = 0
        modules.append(module_data)

    print(localize(locale, "\n你还可以追加血压、血糖、生化、体脂、睡眠等自定义监控模块。", "\nYou can also add custom monitoring modules such as blood pressure, glucose, biochemistry, body fat, or sleep.", "\n血圧、血糖、生化学、体脂肪、睡眠などのカスタム監視モジュールも追加できます。"))
    while ask_yes_no(localize(locale, "追加一个自定义模块？", "Add a custom module?", "カスタムモジュールを追加しますか?"), default=False):
        custom_title = ask_text(localize(locale, "显示标题（例如：生化情况）", "Display title (for example: Biochemistry)", "表示タイトル（例: 生化学）"), localize(locale, "请输入显示标题。", "Please enter a title.", "タイトルを入力してください。"))
        custom_section = ask_text(localize(locale, "匹配的 Markdown 二级标题（例如：生化情况）", "Matching Markdown level-2 heading (for example: Biochemistry)", "対応する Markdown の level-2 見出し（例: 生化学）"), localize(locale, "请输入标题名称。", "Please enter a heading name.", "見出し名を入力してください。"))
        custom_weight = ask_number(localize(locale, "为该模块设置权重", "Set the weight for this module", "このモジュールの重みを設定してください"), localize(locale, "请输入有效数字。", "Please enter a valid number.", "有効な数値を入力してください。"), cast=float, min_value=0)
        modules.append(
            {
                "id": slugify(custom_section),
                "type": "section_presence",
                "title": custom_title,
                "section_title": custom_section,
                "enabled": True,
                "weight": custom_weight,
                "score_when_present": 100,
                "score_when_missing": 0,
            }
        )

    config = {
        "config_version": "1.4.1",
        "language": locale,
        "user_profile": {
            "name": name,
            "gender": gender,
            "age": age,
            "height_cm": height,
            "current_weight_kg": current_weight,
            "target_weight_kg": target_weight,
            "condition": primary_condition,
            "primary_condition": primary_condition,
            "conditions": conditions,
            "activity_level": activity_level,
            "water_target_ml": water_target,
            "step_target": step_target,
            "residence": {
                "country": residence_country,
                "province": residence_province,
                "city": residence_city,
                "district": residence_district,
                "display_name": build_display_name(locale, residence_country, residence_province, residence_city, residence_district),
            },
            "dietary_preferences": {
                "dislike": dislikes,
                "allergies": allergies,
                "favorite_fruits": favorite_fruits,
            },
        },
        "condition_standards": DEFAULT_CONDITION_STANDARDS,
        "scoring": {"modules": modules},
        "exercise_standards": {"weekly_target_minutes": 150},
        "ai_generation": build_ai_generation(ai_mode_choice),
        "integrations": {"tavily_api_key": tavily_api_key},
        "report_preferences": {"append_custom_sections": append_custom_sections},
    }

    config_path = CONFIG_DIR / "user_config.json"
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=4)

    enabled_modules = [module["title"] for module in modules if module.get("enabled")]
    condition_summary = ", ".join(CONDITION_LABELS[locale][item] for item in conditions)

    print(localize(locale, "\n[步骤 4/4] 已保存", "\n[Step 4/4] Saved", "\n[手順 4/4] 保存完了"))
    print(localize(locale, f"配置文件已写入：{config_path}", f"Configuration written to: {config_path}", f"設定を書き込みました: {config_path}"))
    print(localize(locale, f"主目标：{CONDITION_LABELS[locale][primary_condition]}", f"Primary goal: {CONDITION_LABELS[locale][primary_condition]}", f"主目標: {CONDITION_LABELS[locale][primary_condition]}"))
    print(localize(locale, f"已选目标：{condition_summary}", f"Selected goals: {condition_summary}", f"選択した目標: {condition_summary}"))
    print(localize(locale, f"已启用模块：{', '.join(enabled_modules) if enabled_modules else '无'}", f"Enabled modules: {', '.join(enabled_modules) if enabled_modules else 'None'}", f"有効なモジュール: {', '.join(enabled_modules) if enabled_modules else 'なし'}"))

    print()
    for line in [
        localize(locale, "后续建议：", "Next steps:", "次のステップ:"),
        localize(locale, "1. 从今天开始按固定 Markdown 结构写入 MEMORY_DIR。多疾病场景下，请持续记录所有相关症状、用药和监控指标。", "1. Start writing structured Markdown logs into MEMORY_DIR. In mixed-condition mode, keep logging all relevant symptoms, medication, and monitoring metrics.", "1. MEMORY_DIR に構造化 Markdown を記録してください。複数疾患の管理では、症状・服薬・監視指標を継続記録してください。"),
        localize(locale, "2. 如果启用了“用药情况”，请使用稳定的二级标题，例如：## 用药记录。", "2. If Medication is enabled, keep a stable level-2 heading such as: ## Medication.", "2. 服薬モジュールを有効にした場合は、安定した level-2 見出しを使ってください。例: ## 服薬記録"),
        localize(locale, "3. 自定义模块也必须使用稳定的二级标题，例如：## 生化情况 / ## 血压记录。", "3. Custom modules must also use stable level-2 headings such as: ## Biochemistry or ## Blood Pressure.", "3. カスタムモジュールも安定した level-2 見出しを使ってください。例: ## 生化学 / ## 血圧記録"),
        localize(locale, "4. 当前向导已经覆盖 user_config.json 的主要运行逻辑：多疾病、AI 模式、评分模块、用药、自定义监控、居住地、Tavily 与报告偏好。", "4. This wizard now covers the main runtime logic in user_config.json: multi-condition setup, AI mode, scoring modules, medication, custom monitoring, residence, Tavily, and report preferences.", "4. このウィザードは user_config.json の主要な実行設定をほぼカバーしています。"),
        localize(locale, "5. 技能升级或重新安装前，请务必备份 config/user_config.json 和 config/.env。部分平台升级流程可能会重置本地配置。", "5. Before upgrading or reinstalling the skill, back up config/user_config.json and config/.env. Some platform upgrade flows may reset local config files.", "5. スキルの更新や再インストール前に、config/user_config.json と config/.env を必ずバックアップしてください。"),
    ]:
        print(line)


if __name__ == "__main__":
    main()
