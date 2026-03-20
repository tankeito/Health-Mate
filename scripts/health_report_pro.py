#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daily report generator for Health-Mate."""

import sys
import json
import re
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


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

# ==================== Environment validation ====================
def validate_environment():
    """Validate required runtime settings before execution."""
    errors = []
    warnings = []

    memory_dir = os.environ.get('MEMORY_DIR', '')
    if not memory_dir:
        errors.append(t(None, "env_missing_memory_dir"))
        errors.append(t(None, "env_set_memory_dir"))
    elif not os.path.exists(memory_dir):
        errors.append(t(None, "env_memory_dir_missing", path=memory_dir))
    elif not os.access(memory_dir, os.R_OK):
        errors.append(t(None, "env_memory_dir_unreadable", path=memory_dir))

    webhooks = {
        'DINGTALK_WEBHOOK': os.environ.get('DINGTALK_WEBHOOK', ''),
        'FEISHU_WEBHOOK': os.environ.get('FEISHU_WEBHOOK', ''),
        'TELEGRAM_BOT_TOKEN': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
    }
    configured_webhooks = [k for k, v in webhooks.items() if v]

    if not configured_webhooks:
        warnings.append(t(None, "env_no_webhooks"))
        warnings.append(t(None, "env_webhook_hint"))

    if warnings:
        print("=" * 60)
        print(t(None, "security_warning_title"))
        print("=" * 60)
        for w in warnings:
            print(w)
        print("=" * 60)

    if errors:
        print("=" * 60)
        print(t(None, "env_validation_failed"))
        print("=" * 60)
        for e in errors:
            print(e)
        print("=" * 60)
        print(f"\n{t(None, 'program_exit')}")
        sys.exit(1)

    return True

# ==================== Path setup ====================
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()
CONFIG_DIR = PROJECT_ROOT / 'config'
ASSETS_DIR = PROJECT_ROOT / 'assets'
LOGS_DIR = PROJECT_ROOT / 'logs'
REPORTS_DIR = PROJECT_ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPT_DIR))

from constants import DEFAULT_PORTIONS, FOOD_CALORIES, FOOD_NAME_ALIASES
from i18n import (
    CALORIE_BURN_ALIASES,
    CALORIE_UNIT_PATTERN,
    CUMULATIVE_ALIASES,
    DISTANCE_ALIASES,
    DISTANCE_UNIT_PATTERN,
    DURATION_ALIASES,
    EXERCISE_ALIASES,
    MEAL_ALIASES,
    MEAL_SKIP_KEYWORDS,
    MINUTE_UNIT_PATTERN,
    OVEREATING_PATTERN,
    PLACEHOLDER_TOKENS,
    PORTION_UNIT_PATTERN,
    STEP_LABEL_ALIASES,
    STEP_UNIT_PATTERN,
    SYMPTOM_KEYWORDS,
    SYMPTOM_SECTION_ALIASES,
    TIME_APPROX_PATTERN,
    WATER_AMOUNT_ALIASES,
    WATER_PERIOD_ALIASES,
    WEIGHT_MORNING_ALIASES,
    WEIGHT_UNIT_PATTERN,
    and_more,
    alias_pattern,
    build_ai_comment_prompt,
    build_ai_comment_system_prompt,
    build_ai_plan_prompt,
    build_ai_plan_system_prompt,
    build_condition_tip,
    build_delivery_message,
    build_fallback_plan,
    condition_key,
    condition_name,
    convert_weight_to_kg,
    exercise_key,
    exercise_name,
    extract_time_token,
    format_weight,
    gender_key,
    has_excluded_section_keyword,
    list_separator,
    localized_exercise_query,
    localized_recipe_query,
    meal_key,
    meal_name,
    resolve_locale,
    strip_parenthetical_details,
    t,
    water_period_key,
    water_period_name,
    weight_unit,
)
from pdf_generator import generate_pdf_report as generate_pdf_report_impl

validate_environment()

# ==================== Tavily configuration ====================
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '')

# ==================== Config loading ====================
def load_user_config(config_path=None):
    if config_path is None:
        config_path = CONFIG_DIR / 'user_config.json'
    if not os.path.exists(config_path):
        return _get_default_config()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(t(None, "config_load_failed", error=e), file=sys.stderr)
        return _get_default_config()

def _get_default_config():
    return {
        "language": "zh-CN",
        "user_profile": {
            "name": "Demo User",
            "gender": "male",
            "age": 34,
            "height_cm": 172,
            "current_weight_kg": 65,
            "target_weight_kg": 64,
            "condition": "fat_loss",
            "activity_level": 1.2,
            "water_target_ml": 2000,
            "step_target": 8000,
            "dietary_preferences": {
                "dislike": ["seafood"],
                "allergies": ["seafood"],
                "favorite_fruits": ["apple", "banana", "pear"],
            },
        },
        "condition_standards": {
            "fat_loss": {"fat_min_g": 30, "fat_max_g": 50, "fiber_min_g": 25, "water_min_ml": 2000},
            "balanced": {"fat_min_g": 40, "fat_max_g": 60, "fiber_min_g": 25, "water_min_ml": 2000},
        },
        "scoring_weights": {"diet": 0.45, "water": 0.35, "weight": 0.20, "exercise_bonus": 0.10},
        "exercise_standards": {"weekly_target_minutes": 150}
    }

def get_condition_standards(config, condition_name):
    standards = config.get('condition_standards', {})
    canonical = condition_key(condition_name)
    if canonical in standards:
        return standards[canonical]
    for key, value in standards.items():
        if condition_key(key) == canonical:
            return value
    return standards.get('fat_loss', standards.get('balanced', {}))

def get_scoring_weights(config):
    weights = config.get('scoring_weights', {'diet': 0.45, 'water': 0.35, 'weight': 0.20})
    weights = {k: v for k, v in weights.items() if isinstance(v, (int, float)) and k != 'exercise_bonus'}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights

def get_exercise_bonus_weight(config):
    weights = config.get('scoring_weights', {})
    return weights.get('exercise_bonus', 0.10)

# ==================== Core calculations ====================
def calculate_bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm: return 0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)

def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender_key(gender) == 'male':
        return round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5, 1)
    return round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161, 1)

def calculate_tdee(bmr, activity_level):
    return round(bmr * activity_level, 1)

# ==================== Food parsing ====================
SERVING_NUMBER_PATTERN = r"(?:半|一|二|三|四|五|六|七|八|九|十|两|\d+(?:\.\d+)?)"
SERVING_UNIT_PATTERN = r"(?:大个|小个|个|根|碗|份|杯|片|盒|盘|串|勺|块|张|slice|cup|serving|piece)"
COUNTABLE_UNIT_PATTERN = r"(?:个|根|碗|份|杯|片|盒|盘|串|勺|块|张|slice|cup|serving|piece)"
DECLARED_CALORIE_PATTERN = rf'→\s*(?:约\s*|approx\.?\s*)?(\d+(?:\.\d+)?)\s*{CALORIE_UNIT_PATTERN}'


def strip_serving_descriptors(value):
    text = strip_parenthetical_details(value)
    text = re.sub(rf'^\s*{SERVING_NUMBER_PATTERN}\s*{SERVING_UNIT_PATTERN}\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(rf'\s*{SERVING_NUMBER_PATTERN}\s*{SERVING_UNIT_PATTERN}\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+\d+(?:\.\d+)?\s*(?:g|ml)\s*$', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_food_name(value):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    alias_key = text.lower()
    if alias_key in FOOD_NAME_ALIASES:
        return FOOD_NAME_ALIASES[alias_key]

    best_target = None
    best_len = 0
    for alias, target in FOOD_NAME_ALIASES.items():
        if alias == alias_key or alias in alias_key or alias_key in alias:
            if len(alias) > best_len:
                best_target = target
                best_len = len(alias)
    return best_target or text


def extract_explicit_portion(entry_text):
    entry = str(entry_text or "")
    for paren_content in re.findall(r'[（(]([^（）()]*)[)）]', entry):
        if '+' in paren_content or '＋' in paren_content:
            continue
        match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g)\b', paren_content, re.IGNORECASE)
        if match:
            return float(match.group(1))

    trailing = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g)\b', strip_parenthetical_details(entry), re.IGNORECASE)
    if trailing:
        return float(trailing.group(1))
    return None


def lookup_default_unit_portion(food_name):
    canonical_name = normalize_food_name(strip_serving_descriptors(food_name))
    best_match = None
    for portion_key, grams in DEFAULT_PORTIONS.items():
        base_name = normalize_food_name(strip_serving_descriptors(portion_key))
        if not base_name:
            continue
        if base_name == canonical_name or base_name in canonical_name or canonical_name in base_name:
            if best_match is None or len(base_name) > best_match[0]:
                best_match = (len(base_name), grams)
    return best_match[1] if best_match else None


def extract_declared_calories(line_text):
    match = re.search(DECLARED_CALORIE_PATTERN, str(line_text or ""), re.IGNORECASE)
    return round(float(match.group(1)), 1) if match else None


def parse_food_entry(entry_text):
    entry = re.split(r'\s*→', str(entry_text or '').strip())[0].strip()
    explicit_portion = extract_explicit_portion(entry)
    entry_without_notes = re.sub(r'[（(][^（）()]*[)）]', '', entry).strip()
    entry_without_notes = re.sub(r'\s+', ' ', entry_without_notes)

    alias_key = entry_without_notes.lower().strip()
    if alias_key in FOOD_NAME_ALIASES:
        entry_without_notes = FOOD_NAME_ALIASES[alias_key]

    for portion_prefix, portion_grams in DEFAULT_PORTIONS.items():
        if entry_without_notes.startswith(portion_prefix):
            food_name = entry_without_notes[len(portion_prefix):].strip()
            food_name = normalize_food_name(strip_serving_descriptors(food_name or portion_prefix))
            return food_name, explicit_portion or portion_grams

    food_name = normalize_food_name(strip_serving_descriptors(entry_without_notes))

    if explicit_portion:
        return food_name or normalize_food_name(entry_without_notes), explicit_portion

    count_match = re.search(rf'(.+?)\s*(\d+(?:\.\d+)?)\s*{COUNTABLE_UNIT_PATTERN}\s*$', entry_without_notes, re.IGNORECASE)
    if count_match:
        counted_name = normalize_food_name(strip_serving_descriptors(count_match.group(1)))
        per_unit_grams = lookup_default_unit_portion(counted_name)
        if per_unit_grams:
            return counted_name, round(float(count_match.group(2)) * per_unit_grams, 1)

    return food_name or normalize_food_name(entry_without_notes), 100


def estimate_composite_nutrition(food_name, calories_db):
    text = str(food_name or "")
    match = re.search(r'[（(]([^（）()]*)[)）]', text)
    if not match:
        return None

    ingredient_text = match.group(1)
    if '+' not in ingredient_text and '＋' not in ingredient_text:
        return None

    total = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carb': 0.0, 'fiber': 0.0}
    matched_items = 0
    for part in re.split(r'[+＋]', ingredient_text):
        item_match = re.search(r'(.+?)\s*(\d+(?:\.\d+)?)\s*(g|ml)\b', part.strip(), re.IGNORECASE)
        if not item_match:
            continue
        item_name = normalize_food_name(strip_serving_descriptors(item_match.group(1)))
        item_portion = float(item_match.group(2))
        item_nutrition = estimate_nutrition(item_name, item_portion, calories_db, allow_composite=False)
        if not item_nutrition:
            continue
        matched_items += 1
        for key in total:
            total[key] += item_nutrition.get(key, 0)

    if matched_items >= 2:
        return {key: round(value, 1) for key, value in total.items()}
    return None


def estimate_nutrition(food_name, portion_grams, calories_db, allow_composite=True):
    if allow_composite:
        composite_nutrition = estimate_composite_nutrition(food_name, calories_db)
        if composite_nutrition:
            return composite_nutrition

    nutrition = None
    lookup_name = normalize_food_name(strip_serving_descriptors(food_name))
    if lookup_name in calories_db:
        nutrition = calories_db[lookup_name]
    else:
        candidate_matches = []
        for db_name, db_nutrition in calories_db.items():
            if db_name in lookup_name or lookup_name in db_name:
                candidate_matches.append((len(db_name), db_nutrition))
        if candidate_matches:
            nutrition = max(candidate_matches, key=lambda item: item[0])[1]
    if nutrition is None:
        nutrition = {"calories": 100, "protein": 10, "fat": 5, "carb": 10, "fiber": 2}
    scale = portion_grams / 100.0
    return {k: round(nutrition.get(k, 0) * scale, 1) for k in ['calories', 'protein', 'fat', 'carb', 'fiber']}

# ==================== Scoring ====================
def calculate_diet_score(daily_data, standards, scoring_standards):
    diet_weights = scoring_standards.get('diet', {'fat_score_weight': 0.30, 'protein_score_weight': 0.25, 'fiber_score_weight': 0.25, 'avoid_food_penalty': 0.20})
    total_fat = daily_data.get('total_fat', 0)
    fat_min, fat_max = standards.get('fat_min_g', 40), standards.get('fat_max_g', 50)
    fat_score = 100 if fat_min <= total_fat <= fat_max else max(0, 100 - (fat_min - total_fat) * 5 if total_fat < fat_min else (total_fat - fat_max) * 8)
    total_fiber = daily_data.get('total_fiber', 0)
    fiber_min = standards.get('fiber_min_g', 25)
    fiber_score = 100 if total_fiber >= fiber_min else max(0, 100 - (fiber_min - total_fiber) * 4)
    avoid_count = len(daily_data.get('avoid_foods', []))
    avoid_penalty = min(100, avoid_count * 25)
    score = (fat_score * diet_weights.get('fat_score_weight', 0.30) + fiber_score * diet_weights.get('fiber_score_weight', 0.25) + (100 - avoid_penalty) * diet_weights.get('avoid_food_penalty', 0.20) + 100 * diet_weights.get('protein_score_weight', 0.25))
    return max(0, min(100, round(score, 1)))

def calculate_water_score(water_total, water_target):
    if water_total >= water_target: return 100
    percentage = water_total / water_target
    if percentage >= 0.8: return round(80 + (percentage - 0.8) * 100, 1)
    elif percentage >= 0.5: return round(50 + (percentage - 0.5) * 60, 1)
    else: return round(percentage * 100, 1)

def calculate_weight_score(weight_recorded, target_weight, current_weight):
    score = 50 if weight_recorded else 0
    if current_weight and target_weight:
        diff = abs(current_weight - target_weight)
        score += 50 if diff <= 1 else (30 if diff <= 3 else (15 if diff <= 5 else 0))
    return max(0, min(100, score))

def calculate_exercise_score(exercise_data, steps, exercise_standards, scoring_standards):
    try:
        exercise_weights = scoring_standards.get('exercise', {'duration_score_weight': 0.40, 'frequency_score_weight': 0.30, 'calorie_score_weight': 0.30, 'daily_calorie_target': 300})
        total_minutes = sum(e.get('duration_min', 0) for e in exercise_data if isinstance(e, dict)) if exercise_data else 0
        daily_target = exercise_standards.get('weekly_target_minutes', 150) / 7
        duration_score = 100 if total_minutes >= daily_target else round((total_minutes / daily_target) * 100, 1) if daily_target > 0 else 0

        frequency_score = 100 if (exercise_data and len(exercise_data) > 0) or steps > 3000 else 0

        total_calories = sum(e.get('calories', 0) for e in exercise_data if isinstance(e, dict)) if exercise_data else 0
        total_calories += int(steps * 0.035)
        calorie_target = exercise_weights.get('daily_calorie_target', 300)
        calorie_score = 100 if total_calories >= calorie_target else round((total_calories / calorie_target) * 100, 1) if calorie_target > 0 else 0
        score = duration_score * exercise_weights.get('duration_score_weight', 0.40) + frequency_score * exercise_weights.get('frequency_score_weight', 0.30) + calorie_score * exercise_weights.get('calorie_score_weight', 0.30)
        return max(0, min(100, round(score, 1)))
    except Exception as e:
        print(t(None, "exercise_score_failed", error=e), file=sys.stderr)
        return 0

def parse_memory_file(file_path):
    """Parse one markdown memory file with bilingual heading support."""
    data = {
        'date': '', 'weight_morning': None, 'weight_evening': None,
        'water_records': [], 'meals': [], 'exercise_records': [],
        'symptoms': [], 'symptom_keywords': [], 'risks': [], 'plan': {}, 'ai_comment': '',
        'water_total': 0, 'water_target': 2000,
        'total_calories': 0, 'total_protein': 0, 'total_fat': 0, 'total_carb': 0, 'total_fiber': 0,
        'steps': 0, 'overeating_factor': 1.0,
        'custom_sections': {}
    }
    if not os.path.exists(file_path):
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    date_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    if date_match:
        data['date'] = date_match.group(1)

    weight_match = re.search(
        rf'({alias_pattern(WEIGHT_MORNING_ALIASES)})[^\n:：-]*[：:\-]?\s*([\d.]+)\s*{WEIGHT_UNIT_PATTERN}?',
        content,
        re.IGNORECASE,
    )
    if weight_match:
        raw_label = weight_match.group(1)
        raw_value = float(weight_match.group(2))
        raw_unit = weight_match.group(3) if weight_match.lastindex and weight_match.lastindex >= 3 else None
        assume_jin = any(ord(char) > 127 for char in raw_label)
        unit = raw_unit or (weight_unit("zh-CN") if assume_jin else weight_unit("en-US"))
        data['weight_morning'] = convert_weight_to_kg(raw_value, unit, assume_jin=assume_jin)

    section_blocks = re.finditer(r'^##\s+([^\n]+)\n(.*?)(?=\n##\s|\Z)', content, re.MULTILINE | re.DOTALL)
    for match in section_blocks:
        header_raw = match.group(1).strip()
        if not has_excluded_section_keyword(header_raw):
            lines = []
            for line in match.group(2).split('\n'):
                line_value = line.strip()
                if line_value and line_value not in PLACEHOLDER_TOKENS and not line_value.startswith('_'):
                    lines.append(line_value)
            if lines:
                data['custom_sections'][header_raw] = lines

    water_heading_aliases = {
        re.sub(r'[\s（）():：\-]', '', alias.lower()): canonical
        for canonical, aliases in WATER_PERIOD_ALIASES.items()
        for alias in aliases
    }
    level3_blocks = list(re.finditer(r'^###\s+([^\n]+)\n(.*?)(?=^###\s|^##\s|\Z)', content, re.MULTILINE | re.DOTALL))
    for match in level3_blocks:
        title = match.group(1).strip()
        title_without_time = re.sub(TIME_APPROX_PATTERN, '', title, flags=re.IGNORECASE)
        title_key = re.sub(r'[\s（）():：\-]', '', title_without_time.lower())
        water_key = water_heading_aliases.get(title_key)
        if not water_key:
            continue

        water_content = match.group(2)
        amount_match = re.search(
            rf'-\s*(?:{alias_pattern(WATER_AMOUNT_ALIASES)})[：:]\s*(\d+)\s*ml',
            water_content,
            re.IGNORECASE,
        )
        cumulative_match = re.search(
            rf'-\s*(?:{alias_pattern(CUMULATIVE_ALIASES)})[：:]\s*(\d+)\s*ml/\s*(\d+)\s*ml',
            water_content,
            re.IGNORECASE,
        )
        if not amount_match or not cumulative_match:
            continue

        exact_time = extract_time_token(title)
        data['water_records'].append({
            'time_label': water_key,
            'exact_time': exact_time,
            'time': exact_time or water_key,
            'amount_ml': int(amount_match.group(1)),
            'cumulative_ml': int(cumulative_match.group(1)),
        })

    if data['water_records']:
        data['water_total'] = data['water_records'][-1]['cumulative_ml']
        last_match = re.search(
            rf'-\s*(?:{alias_pattern(CUMULATIVE_ALIASES)})[：:]\s*\d+\s*ml/\s*(\d+)\s*ml',
            content,
            re.IGNORECASE,
        )
        if last_match:
            data['water_target'] = int(last_match.group(1))

    overeating_matches = re.findall(OVEREATING_PATTERN, content, re.IGNORECASE)
    data['overeating_factor'] = 1.25 if overeating_matches else 1.0

    data['symptom_keywords'] = [keyword for keyword in SYMPTOM_KEYWORDS if keyword.lower() in content.lower()]

    meal_pattern = rf'###\s+({alias_pattern(MEAL_ALIASES)})[^\n]*'
    meal_starts = [(match.group(1), match.start(), match.end()) for match in re.finditer(meal_pattern, content, re.IGNORECASE)]

    for index, (meal_type_raw, start, end) in enumerate(meal_starts):
        title_line = content[start:end]
        meal_time = extract_time_token(title_line)

        next_start = meal_starts[index + 1][2] if index + 1 < len(meal_starts) else len(content)
        next_boundary = len(content)
        next_hash3 = content.find('\n### ', end)
        next_hash2 = content.find('\n## ', end)
        if next_hash3 != -1:
            next_boundary = min(next_boundary, next_hash3)
        if next_hash2 != -1:
            next_boundary = min(next_boundary, next_hash2)
        if next_boundary < next_start:
            next_start = next_boundary

        meal_content = content[end:next_start]
        meal_overeating = 1.25 if re.search(OVEREATING_PATTERN, meal_content, re.IGNORECASE) else 1.0
        meal_data = {
            'type': meal_key(meal_type_raw),
            'time': meal_time,
            'foods': [],
            'food_nutrition': [],
            'total_calories': 0, 'total_protein': 0, 'total_fat': 0, 'total_carb': 0, 'total_fiber': 0,
            'overeating_factor': meal_overeating,
        }

        for line in meal_content.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('-') and '→' in line_stripped:
                lowered_line = line_stripped.lower()
                if any(kw.lower() in lowered_line for kw in MEAL_SKIP_KEYWORDS):
                    continue
                food_match = re.match(r'-\s*(.+?)\s*→', line_stripped)
                if food_match:
                    food_name = food_match.group(1).strip()
                    _, portion = parse_food_entry(food_name)
                    nutrition = estimate_nutrition(food_name, portion, FOOD_CALORIES)
                    if meal_overeating > 1.0:
                        nutrition = {k: v * meal_overeating for k, v in nutrition.items()}
                    declared_calories = extract_declared_calories(line_stripped)
                    if declared_calories is not None:
                        nutrition['calories'] = declared_calories
                    meal_data['foods'].append(food_name)
                    meal_data['food_nutrition'].append({'name': food_name, 'portion_grams': portion, **nutrition})
                    for k in ['calories', 'protein', 'fat', 'carb', 'fiber']:
                        meal_data[f'total_{k}'] += nutrition[k]

        if meal_data['foods']:
            data['meals'].append(meal_data)

    exercise_blocks = re.finditer(r'### ([^\n]+)\n(.*?)(?=\n### |\n## |\Z)', content, re.DOTALL)
    for match in exercise_blocks:
        title = match.group(1).strip()
        exercise_content = match.group(2)
        exercise_type = None
        lowered_title = title.lower()
        for canonical, aliases in EXERCISE_ALIASES.items():
            if any(alias.lower() in lowered_title for alias in aliases):
                exercise_type = canonical
                break

        if exercise_type:
            distance_match = re.search(
                rf'(?:{alias_pattern(DISTANCE_ALIASES)}).*?[：:]\s*([\d.]+)\s*{DISTANCE_UNIT_PATTERN}',
                exercise_content,
                re.IGNORECASE,
            )
            duration_match = re.search(
                rf'(?:{alias_pattern(DURATION_ALIASES)}).*?[：:]\s*(\d+)\s*{MINUTE_UNIT_PATTERN}',
                exercise_content,
                re.IGNORECASE,
            )
            calories_match = re.search(
                rf'(?:{alias_pattern(CALORIE_BURN_ALIASES)}).*?[：:]\s*(?:约\s*|approx\.?\s*)?(\d+(?:\.\d+)?)\s*{CALORIE_UNIT_PATTERN}',
                exercise_content,
                re.IGNORECASE,
            )
            if duration_match or calories_match:
                data['exercise_records'].append({
                    'type': exercise_type,
                    'time': extract_time_token(title),
                    'distance_km': float(distance_match.group(1)) if distance_match else 0,
                    'duration_min': int(duration_match.group(1)) if duration_match else 0,
                    'calories': round(float(calories_match.group(1)), 1) if calories_match else 0,
                })

    steps_match = re.search(
        rf'(?:{alias_pattern(STEP_LABEL_ALIASES)}).*?[：:]\s*(\d+)\s*{STEP_UNIT_PATTERN}?',
        content,
        re.IGNORECASE,
    )
    if steps_match:
        data['steps'] = int(steps_match.group(1))

    symptom_section = re.search(
        rf'##\s*(?:📝\s*)?(?:{alias_pattern(SYMPTOM_SECTION_ALIASES)})[^\n]*\n(.*?)(?=\n## |\Z)',
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if symptom_section:
        symptom_text = symptom_section.group(1).strip()
        if symptom_text and not any(token in symptom_text for token in PLACEHOLDER_TOKENS):
            data['symptoms'] = [s.strip() for s in symptom_text.split('\n') if s.strip() and not s.startswith('_')]

    data['total_calories'] = sum(m.get('total_calories', 0) for m in data['meals'])
    data['total_protein'] = sum(m.get('total_protein', 0) for m in data['meals'])
    data['total_fat'] = sum(m.get('total_fat', 0) for m in data['meals'])
    data['total_carb'] = sum(m.get('total_carb', 0) for m in data['meals'])
    data['total_fiber'] = sum(m.get('total_fiber', 0) for m in data['meals'])

    return data

# ==================== AI insight generation ====================
def generate_ai_comment(health_data, config):
    """Generate an AI insight, with a local fallback when LLM is unavailable."""
    locale = resolve_locale(config)
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', 'fat_loss')
    user_name = user_profile.get('name', t(locale, 'default_user'))
    standards = get_condition_standards(config, condition)

    fat_min, fat_max = standards.get('fat_min_g', 40), standards.get('fat_max_g', 50)
    fiber_min = standards.get('fiber_min_g', 25)
    prompt_context = {
        'user_name': user_name,
        'condition_name': condition_name(locale, condition),
        'diet_principle': build_condition_tip(locale, condition, fat_min, fat_max, fiber_min),
        'calories': health_data.get('total_calories', 0),
        'protein': health_data.get('total_protein', 0),
        'fat': health_data.get('total_fat', 0),
        'fat_min': fat_min,
        'fat_max': fat_max,
        'carb': health_data.get('total_carb', 0),
        'fiber': health_data.get('total_fiber', 0),
        'fiber_min': fiber_min,
        'water_total': health_data.get('water_total', 0),
        'water_target': health_data.get('water_target', user_profile.get('water_target_ml', 2000)),
        'exercise_count': len(health_data.get('exercise_records', [])),
        'steps': health_data.get('steps', 0),
        'overeating_factor': health_data.get('overeating_factor', 1.0),
        'symptom_keywords': health_data.get('symptom_keywords', []),
    }
    prompt = build_ai_comment_prompt(locale, prompt_context)

    for attempt in range(3):
        try:
            result = subprocess.run(
                ['openclaw', 'agent', '--local', '--to', '+860000000000', '--message', prompt],
                capture_output=True,
                text=True,
                timeout=90,
                env={**os.environ, 'SYSTEM_PROMPT': build_ai_comment_system_prompt(locale, condition)},
            )
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                if '[plugins]' in output:
                    lines = output.split('\n')
                    output = '\n'.join([line for line in lines if not line.startswith('[plugins]') and not line.startswith('[adp-')]).strip()
                return output
        except subprocess.TimeoutExpired:
            print(t(locale, "ai_comment_timeout", attempt=attempt + 1), file=sys.stderr)
        except Exception as e:
            print(t(locale, "ai_comment_failed", attempt=attempt + 1, error=e), file=sys.stderr)
        if attempt < 2:
            import time
            time.sleep(2)

    comments = []
    fat_val = health_data.get('total_fat', 0)
    if fat_min <= fat_val <= fat_max:
        comments.append(t(locale, "fallback_comment_fat_ok", value=fat_val))
    elif fat_val < fat_min:
        comments.append(t(locale, "fallback_comment_fat_low", value=fat_val))
    else:
        comments.append(t(locale, "fallback_comment_fat_high", value=fat_val))

    fiber_val = health_data.get('total_fiber', 0)
    if fiber_val >= fiber_min:
        comments.append(t(locale, "fallback_comment_fiber_ok", value=fiber_val))
    else:
        comments.append(t(locale, "fallback_comment_fiber_low", value=fiber_val))

    water_val = health_data.get('water_total', 0)
    water_target = health_data.get('water_target', user_profile.get('water_target_ml', 2000))
    if water_val >= water_target:
        comments.append(t(locale, "fallback_comment_water_ok", value=water_val))
    else:
        comments.append(t(locale, "fallback_comment_water_low", value=water_val, target=water_target))

    steps = health_data.get('steps', 0)
    if steps >= 6000:
        comments.append(t(locale, "fallback_comment_steps_high", value=steps))
    elif steps >= 3000:
        comments.append(t(locale, "fallback_comment_steps_mid", value=steps))
    else:
        comments.append(t(locale, "fallback_comment_steps_low", value=steps))

    return " ".join(comments)

# ==================== AI next-day planning ====================
def tavily_search(query, max_results=3):
    """Call Tavily for external context when the API key is available."""
    import urllib.request
    url = "https://api.tavily.com/search"

    for attempt in range(3):
        try:
            data = json.dumps({
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('results', [])
        except Exception as e:
            print(t(None, "tavily_failed", attempt=attempt + 1, error=e), file=sys.stderr)
            if attempt < 2:
                import time
                time.sleep(2)
    return []

def generate_ai_plan(health_data, config):
    """Generate the next-day plan with bilingual prompts and a local fallback."""
    locale = resolve_locale(config)
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', 'fat_loss')
    standards = get_condition_standards(config, condition)
    fat_min, fat_max = standards.get('fat_min_g', 40), standards.get('fat_max_g', 50)
    fiber_min = standards.get('fiber_min_g', 25)

    shortcomings = []
    fat_val = health_data.get('total_fat', 0)
    fiber_val = health_data.get('total_fiber', 0)
    water_val = health_data.get('water_total', 0)
    steps = health_data.get('steps', 0)

    if fat_val < fat_min * 0.8:
        shortcomings.append(t(locale, "shortcoming_fat_low"))
    elif fat_val > fat_max:
        shortcomings.append(t(locale, "shortcoming_fat_high"))
    if fiber_val < fiber_min * 0.8:
        shortcomings.append(t(locale, "shortcoming_fiber_low"))
    water_threshold = user_profile.get('water_target_ml', health_data.get('water_target', 2000)) * 0.75
    if water_val < water_threshold:
        shortcomings.append(t(locale, "shortcoming_water_low"))
    if steps < 3000:
        shortcomings.append(t(locale, "shortcoming_exercise_low"))

    recipes = []
    exercises = []

    if TAVILY_API_KEY and any(item in shortcomings for item in [t(locale, "shortcoming_fat_low"), t(locale, "shortcoming_fat_high")]):
        recipe_query = localized_recipe_query(locale, condition_name(locale, condition))
        recipe_results = tavily_search(recipe_query, max_results=2)
        recipes = [r.get('content', '') for r in recipe_results[:2]]

    if TAVILY_API_KEY and t(locale, "shortcoming_exercise_low") in shortcomings:
        exercise_query = localized_exercise_query(locale, condition_name(locale, condition))
        exercise_results = tavily_search(exercise_query, max_results=2)
        exercises = [r.get('content', '') for r in exercise_results[:2]]

    preferences = user_profile.get('dietary_preferences', {})
    prompt = build_ai_plan_prompt(
        locale,
        {
            'user_name': user_profile.get('name', t(locale, 'default_user')),
            'condition_name': condition_name(locale, condition),
            'diet_principle': build_condition_tip(locale, condition, fat_min, fat_max, fiber_min),
            'avoid_foods': ', '.join(preferences.get('dislike', []) + preferences.get('allergies', [])),
            'favorite_fruits': ', '.join(preferences.get('favorite_fruits', [])),
            'shortcomings': shortcomings,
            'recipe_reference': recipes[:1] if recipes else 'none',
            'exercise_reference': exercises[:1] if exercises else 'none',
        },
    )

    for attempt in range(3):
        try:
            result = subprocess.run(
                ['openclaw', 'agent', '--local', '--to', '+860000000000', '--message', prompt],
                capture_output=True, text=True, timeout=90,
                env={**os.environ, 'SYSTEM_PROMPT': build_ai_plan_system_prompt(locale)}
            )
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                if '[plugins]' in output:
                    lines = output.split('\n')
                    output = '\n'.join([line for line in lines if not line.startswith('[plugins]') and not line.startswith('[adp-')]).strip()
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except subprocess.TimeoutExpired:
            print(t(locale, "ai_plan_timeout", attempt=attempt + 1), file=sys.stderr)
        except Exception as e:
            print(t(locale, "ai_plan_failed", attempt=attempt + 1, error=e), file=sys.stderr)
        if attempt < 2:
            import time
            time.sleep(2)

    plan = build_fallback_plan(
        locale,
        int(user_profile.get('water_target_ml', health_data.get('water_target', 2000))),
        ', '.join(preferences.get('favorite_fruits', [])),
    )
    if health_data.get('overeating_factor', 1.0) > 1.0:
        plan['notes'].append(t(locale, "fallback_note_overeat"))
    if t(locale, "shortcoming_fat_low") in shortcomings:
        plan['notes'].append(t(locale, "fallback_note_fat_low"))
    elif t(locale, "shortcoming_fat_high") in shortcomings:
        plan['notes'].append(t(locale, "fallback_note_fat_high"))
    if t(locale, "shortcoming_fiber_low") in shortcomings:
        plan['notes'].append(t(locale, "fallback_note_fiber_low"))
    if t(locale, "shortcoming_exercise_low") in shortcomings:
        plan['notes'].append(t(locale, "fallback_note_exercise_low"))
    return plan

def get_star_string(score):
    stars_count = max(1, min(5, int(score / 20)))
    return "⭐" * stars_count


TEXT_REPORT_ICONS = {
    'daily_report_heading': '📄',
    'overall_score_title': '🏆',
    'item_summary_title': '📊',
    'diet_label': '🥗',
    'water_label': '💧',
    'weight_label': '⚖️',
    'symptom_label': '🩺',
    'exercise_label': '🚴',
    'adherence_label': '✅',
    'ai_comment_title': '🤖',
    'details_title': '📋',
    'meal_section': '🍽️',
    'water_section': '🥤',
    'exercise_section': '🏃',
    'next_day_plan_title': '🎯',
    'diet_plan': '🍱',
    'water_plan': '💧',
    'exercise_plan': '🏋️',
    'special_attention': '📌',
}


def with_text_icon(key, text):
    icon = TEXT_REPORT_ICONS.get(key, '')
    return f"{icon} {text}".strip() if icon else text


def compact_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value

def generate_text_report(health_data, config, date):
    """Generate the localized markdown text report."""
    locale = resolve_locale(config)
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', 'fat_loss')
    standards = get_condition_standards(config, condition)
    scoring_weights = get_scoring_weights(config)
    scoring_standards = config.get('scoring_standards', {})
    exercise_standards = config.get('exercise_standards', {})

    diet_score = calculate_diet_score(health_data, standards, scoring_standards)
    water_score = calculate_water_score(health_data.get('water_total', 0), health_data.get('water_target', 2000))
    weight_score = calculate_weight_score(health_data.get('weight_morning') is not None, user_profile.get('target_weight_kg', 64), health_data.get('weight_morning'))
    exercise_score = calculate_exercise_score(health_data.get('exercise_records', []), health_data.get('steps', 0), exercise_standards, scoring_standards)
    base_score = round(diet_score * scoring_weights.get('diet', 0.45) + water_score * scoring_weights.get('water', 0.35) + weight_score * scoring_weights.get('weight', 0.20), 1)
    exercise_bonus = round(exercise_score * get_exercise_bonus_weight(config), 1)
    total_score = min(100, round(base_score + exercise_bonus, 1))

    symptom_penalty = len(health_data.get('symptom_keywords', [])) * 20 if health_data.get('symptom_keywords') else 0
    symptom_score = max(0, 100 - symptom_penalty)
    weight_kg = health_data.get('weight_morning')
    bmi = calculate_bmi(weight_kg, user_profile.get('height_cm', 172)) if weight_kg else 0
    bmr = calculate_bmr(weight_kg if weight_kg else 65, user_profile.get('height_cm', 172), user_profile.get('age', 34), user_profile.get('gender', 'male')) if weight_kg else 0
    ai_comment = health_data.get('ai_comment', '') or generate_ai_comment(health_data, config)
    ai_plan = health_data.get('plan', {}) or generate_ai_plan(health_data, config)

    fat_min, fat_max = standards.get('fat_min_g', 40), standards.get('fat_max_g', 50)
    water_target = health_data.get('water_target', 2000)
    water_target = water_target if water_target > 0 else 2000
    water_percent = int(health_data.get('water_total', 0) * 100 // water_target)

    fat_val = health_data.get('total_fat', 0)
    if fat_val > fat_max:
        fat_status = t(locale, "fat_high", value=fat_val)
    elif fat_val < fat_min:
        fat_status = t(locale, "fat_low", value=fat_val)
    else:
        fat_status = t(locale, "fat_in_range")
    protein_status = t(locale, "protein_ok") if health_data.get('total_protein', 0) >= 60 else t(locale, "protein_low")

    compact_ai_comment = re.sub(r'[☑✅]', '', ai_comment).replace('\n', ' ').strip()
    adherence_raw = 100 if len(health_data.get('meals', [])) >= 3 else 50
    symptom_text = t(locale, "no_symptoms") if not health_data.get('symptom_keywords') else t(locale, "symptoms_prefix", symptoms='; '.join(health_data.get('symptom_keywords', [])))

    custom_text = ""
    for header, items in health_data.get('custom_sections', {}).items():
        custom_text += f"\n**{header}**\n" + '\n'.join(items) + "\n"

    report = f"""## {with_text_icon('daily_report_heading', t(locale, 'daily_report_heading', date=date))}
### {with_text_icon('overall_score_title', t(locale, 'overall_score_title', date=date))}
**{t(locale, 'score_total_label')}: {get_star_string(total_score)} {total_score}/100** ({t(locale, 'base_score_label')} {base_score:.1f} + {t(locale, 'exercise_bonus_label')} {exercise_bonus:.1f})

### {with_text_icon('item_summary_title', t(locale, 'item_summary_title'))}
- {with_text_icon('diet_label', t(locale, 'diet_label'))}: {get_star_string(diet_score)} {diet_score}/100
  {fat_status} | {protein_status}
- {with_text_icon('water_label', t(locale, 'water_label'))}: {get_star_string(water_score)} {water_score}/100
  {t(locale, 'completion_status', current=health_data.get('water_total', 0), target=water_target, percent=water_percent)}
- {with_text_icon('weight_label', t(locale, 'weight_label'))}: {get_star_string(weight_score)} {weight_score}/100
  {t(locale, 'weight_status', weight=format_weight(locale, health_data.get('weight_morning')), bmi=bmi)}
- {with_text_icon('symptom_label', t(locale, 'symptom_label'))}: {get_star_string(symptom_score)} {symptom_score}/100
  {symptom_text}
- {with_text_icon('exercise_label', t(locale, 'exercise_label'))}: {get_star_string(exercise_score)} {exercise_score}/100
  {generate_exercise_summary(health_data, locale)}
- {with_text_icon('adherence_label', t(locale, 'adherence_label'))}: {get_star_string(adherence_raw)} {adherence_raw}/100
  {t(locale, 'adherence_status', meals=len(health_data.get('meals', [])), water_status=t(locale, 'water_goal_met') if health_data.get('water_total', 0) >= water_target else t(locale, 'water_goal_not_met'))}

### {with_text_icon('ai_comment_title', t(locale, 'ai_comment_title'))}
{compact_ai_comment}

### {with_text_icon('details_title', t(locale, 'details_title'))}
**{with_text_icon('meal_section', t(locale, 'meal_section'))}**
{generate_meal_summary(health_data, locale)}

**{with_text_icon('water_section', t(locale, 'water_section'))}**
{generate_water_summary(health_data, locale)}

**{with_text_icon('exercise_section', t(locale, 'exercise_section'))}**
{generate_exercise_detail(health_data, locale)}{custom_text}

### {with_text_icon('next_day_plan_title', t(locale, 'next_day_plan_title'))}
{generate_plan_text(ai_plan, locale)}"""
    return report


def generate_meal_summary(health_data, locale):
    meals = health_data.get('meals', [])
    if not meals:
        return t(locale, 'no_record')
    lines = []
    for meal in meals:
        foods = list_separator(locale).join(meal.get('foods', []))
        time_suffix = f" ({meal.get('time', '')})" if meal.get('time') else ""
        lines.append(f"{meal_name(locale, meal.get('type', ''))}{time_suffix}: {foods} - {meal.get('total_calories', 0):.0f}kcal")
    return '\n'.join(lines)


def generate_water_summary(health_data, locale):
    water_target = health_data.get('water_target', 2000)
    water_target = water_target if water_target > 0 else 2000
    return t(locale, 'completion_status', current=health_data.get('water_total', 0), target=water_target, percent=int(health_data.get('water_total', 0) * 100 // water_target))


def generate_exercise_summary(health_data, locale):
    exercises = health_data.get('exercise_records', [])
    steps = health_data.get('steps', 0)
    if not exercises and steps == 0:
        return t(locale, 'no_record')
    parts = []
    for e in exercises:
        exercise_label = exercise_name(locale, e.get('type'))
        if e.get('time'):
            exercise_label = f"{exercise_label} ({e.get('time')})"
        details = []
        if e.get('distance_km', 0) > 0:
            details.append(t(locale, 'distance_unit_km', value=compact_number(e.get('distance_km', 0))))
        if e.get('duration_min', 0) > 0:
            details.append(t(locale, 'minutes_unit', value=compact_number(e.get('duration_min', 0))))
        if e.get('calories', 0) > 0:
            details.append(t(locale, 'calories_unit', value=compact_number(e.get('calories', 0))))
        parts.append(f"{exercise_label}: {' / '.join(details)}")
    if steps > 0:
        parts.append(f"{t(locale, 'today_steps')}: {t(locale, 'steps_unit', value=steps)}")
    return '; '.join(parts) if parts else t(locale, 'no_record')


def generate_exercise_detail(health_data, locale):
    exercises = health_data.get('exercise_records', [])
    steps = health_data.get('steps', 0)
    if not exercises and steps == 0:
        return t(locale, 'no_record')
    lines = []
    for exercise in exercises:
        exercise_label = exercise_name(locale, exercise.get('type'))
        if exercise.get('time'):
            exercise_label = f"{exercise_label} ({exercise.get('time')})"
        details = []
        if exercise.get('distance_km', 0) > 0:
            details.append(t(locale, 'distance_unit_km', value=compact_number(exercise.get('distance_km', 0))))
        if exercise.get('duration_min', 0) > 0:
            details.append(t(locale, 'minutes_unit', value=compact_number(exercise.get('duration_min', 0))))
        if exercise.get('calories', 0) > 0:
            details.append(t(locale, 'calories_unit', value=compact_number(exercise.get('calories', 0))))
        lines.append(f"{exercise_label}: {' / '.join(details)}")
    if steps > 0:
        lines.append(f"{t(locale, 'today_steps')}: {t(locale, 'steps_unit', value=steps)}")
    return '\n'.join(lines) if lines else t(locale, 'no_detail_record')


def generate_plan_text(plan, locale):
    """Render the next-day plan in localized markdown."""
    lines = []
    if plan.get('diet'):
        lines.append(f"**{with_text_icon('diet_plan', t(locale, 'diet_plan'))}**")
        for item in plan.get('diet', []):
            if isinstance(item, dict):
                meal = item.get('meal', item.get('meal_name', ''))
                time = item.get('time', item.get('time_range', item.get('period', '')))
                menu = item.get('menu', '')
                if not menu:
                    items = item.get('items', [])
                    if items:
                        menu = list_separator(locale).join(str(i) for i in items[:3])
                        if len(items) > 3:
                            menu += f" {and_more(locale)}"
                if not menu:
                    menu = item.get('dishes', item.get('menu_detail', item.get('food', item.get('content', ''))))
                calories = item.get('calories', item.get('kcal', ''))
                fat = item.get('fat', item.get('fat_g', ''))
                fiber = item.get('fiber', item.get('fiber_g', ''))
                if menu:
                    nutrition = f"({calories}kcal"
                    if fat:
                        nutrition += f", {t(locale, 'fat')}{fat}g"
                    if fiber:
                        nutrition += f", {t(locale, 'fiber')}{fiber}g"
                    nutrition += ")"
                    lines.append(f"* {time} {menu} {nutrition}")
                elif meal and time:
                    lines.append(f"* {meal} ({time})")
                else:
                    lines.append(f"* {item}")
            else:
                lines.append(f'* {item}')
        lines.append('')
    if plan.get('water'):
        lines.append(f"**{with_text_icon('water_plan', t(locale, 'water_plan'))}**")
        for item in plan.get('water', []):
            if isinstance(item, dict):
                time = item.get('time', item.get('period', ''))
                amount = item.get('amount', item.get('amount_ml', item.get('volume', '')))
                if amount and not any(unit in str(amount) for unit in ['ml', 'L']):
                    amount = f"{amount}ml"
                note = item.get('note', item.get('tip', item.get('remark', '')))
                lines.append(f"* {time} {amount} ({note})")
            else:
                lines.append(f'* {item}')
        lines.append('')
    if plan.get('exercise'):
        lines.append(f"**{with_text_icon('exercise_plan', t(locale, 'exercise_plan'))}**")
        for item in plan.get('exercise', []):
            if isinstance(item, dict):
                time = item.get('time', item.get('time_range', item.get('period', '')))
                activity = item.get('activity', item.get('type', item.get('name', '')))
                duration = item.get('duration', item.get('duration_min', item.get('time_length', '')))
                details = item.get('details', item.get('description', item.get('desc', item.get('content', ''))))
                if activity and duration and details:
                    lines.append(f"* {time} {activity} ({duration}): {details}")
                elif activity and duration:
                    lines.append(f"* {time} {activity} ({duration})")
                elif activity:
                    lines.append(f"* {time} {activity}")
                else:
                    lines.append(f"* {time}")
            else:
                lines.append(f'* {item}')
        lines.append('')
    if plan.get('notes'):
        lines.append(f"**{with_text_icon('special_attention', t(locale, 'special_attention'))}**")
        for item in plan.get('notes', []):
            lines.append(f'* {item}')
    return '\n'.join(lines).strip()

def generate_report(memory_file, date):
    """Generate the localized text report and PDF path."""
    config = load_user_config()
    locale = resolve_locale(config)
    user_profile = config.get('user_profile', {})
    if 'step_target' not in user_profile:
        user_profile['step_target'] = 8000

    condition = user_profile.get('condition', 'fat_loss')
    standards = get_condition_standards(config, condition)
    scoring_standards = config.get('scoring_standards', {})
    exercise_standards = config.get('exercise_standards', {})

    health_data = parse_memory_file(memory_file)
    diet_score = calculate_diet_score(health_data, standards, scoring_standards)
    water_score = calculate_water_score(health_data.get('water_total', 0), health_data.get('water_target', 2000))
    weight_score = calculate_weight_score(health_data.get('weight_morning') is not None, user_profile.get('target_weight_kg', 64), health_data.get('weight_morning'))
    exercise_score = calculate_exercise_score(health_data.get('exercise_records', []), health_data.get('steps', 0), exercise_standards, scoring_standards)
    scoring_weights = get_scoring_weights(config)
    base_score = round(diet_score * scoring_weights.get('diet', 0.45) + water_score * scoring_weights.get('water', 0.35) + weight_score * scoring_weights.get('weight', 0.20), 1)
    exercise_bonus = round(exercise_score * get_exercise_bonus_weight(config), 1)
    total_score = min(100, round(base_score + exercise_bonus, 1))

    ai_comment = generate_ai_comment(health_data, config)
    ai_plan = generate_ai_plan(health_data, config)
    health_data['ai_comment'] = ai_comment
    health_data['plan'] = ai_plan
    bmi = calculate_bmi(health_data.get('weight_morning'), user_profile.get('height_cm', 172)) if health_data.get('weight_morning') else 0
    pdf_scores_dict = {
        'diet': {'raw': diet_score, 'stars': get_star_string(diet_score)},
        'water': {'raw': water_score, 'stars': get_star_string(water_score)},
        'weight': {'raw': weight_score, 'stars': get_star_string(weight_score), 'bmi': bmi},
        'exercise': {'raw': exercise_score, 'stars': get_star_string(exercise_score)},
        'symptom': {'raw': 100 if not health_data.get('symptom_keywords') else max(0, 100 - len(health_data['symptom_keywords']) * 20), 'stars': get_star_string(100 if not health_data.get('symptom_keywords') else max(0, 100 - len(health_data['symptom_keywords']) * 20)), 'has_symptoms': bool(health_data.get('symptom_keywords'))},
        'adherence': {'raw': 100 if len(health_data.get('meals', [])) >= 3 else 50, 'stars': get_star_string(100 if len(health_data.get('meals', [])) >= 3 else 50)},
        'total': total_score,
        'total_stars': get_star_string(total_score)
    }

    tdee = calculate_tdee(calculate_bmr(health_data.get('weight_morning') or 65, user_profile.get('height_cm', 172), user_profile.get('age', 34), user_profile.get('gender', 'male')), user_profile.get('activity_level', 1.2))
    macros = {
        'protein_p': 15, 'fat_p': 25, 'carb_p': 60,
        'protein_g': round(user_profile.get('current_weight_kg', 65) * 1.2),
        'fat_g': round(standards.get('fat_max_g', 50)),
        'carb_g': round(tdee * 0.60 / 4),
        'fiber_min_g': standards.get('fiber_min_g', 25)
    }

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_filename = f"health_report_{timestamp}.pdf"
    local_pdf_path = str(REPORTS_DIR / pdf_filename)
    web_dir = os.environ.get("REPORT_WEB_DIR", "")
    base_url = os.environ.get("REPORT_BASE_URL", "").rstrip('/')

    try:
        generate_pdf_report_impl(
            data=health_data,
            profile=user_profile,
            locale=locale,
            scores=pdf_scores_dict,
            nutrition={
                'calories': health_data.get('total_calories', 0),
                'protein': health_data.get('total_protein', 0),
                'fat': health_data.get('total_fat', 0),
                'carb': health_data.get('total_carb', 0),
                'fiber': health_data.get('total_fiber', 0),
            },
            macros=macros,
            risks=[],
            plan=ai_plan,
            output_path=local_pdf_path,
            water_records=health_data.get('water_records', []),
            meals=health_data.get('meals', []),
            exercise_data=health_data.get('exercise_records', []),
            ai_comment=ai_comment,
            custom_sections=health_data.get('custom_sections', {})
        )
        if web_dir and os.path.exists(web_dir) and base_url:
            web_pdf_path = os.path.join(web_dir, pdf_filename)
            shutil.copy2(local_pdf_path, web_pdf_path)
            pdf_url = f"{base_url}/{pdf_filename}"
            print(t(locale, "pdf_copied", path=web_pdf_path), file=sys.stderr)
            print(t(locale, "pdf_download_url", url=pdf_url), file=sys.stderr)
        else:
            print(t(locale, "pdf_saved_local"), file=sys.stderr)
            print(t(locale, "pdf_local_path", path=local_pdf_path), file=sys.stderr)
            pdf_url = local_pdf_path
    except Exception as e:
        print(t(locale, "pdf_generation_failed", error=e), file=sys.stderr)
        import traceback
        traceback.print_exc()
        pdf_url = local_pdf_path

    text_report = generate_text_report(health_data, config, date)
    delivery_message = build_delivery_message(
        locale=locale,
        body=text_report,
        pdf_url=pdf_url,
        report_kind="daily",
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )
    return text_report, pdf_url, delivery_message

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 health_report_pro.py <memory_file> <date>")
        sys.exit(1)

    memory_file = sys.argv[1]
    date = sys.argv[2]

    try:
        text_report, pdf_url, delivery_message = generate_report(memory_file, date)
        print("=== TEXT_REPORT_START ===")
        print(text_report)
        print("=== TEXT_REPORT_END ===")
        print("=== PDF_URL ===")
        print(pdf_url)
        print("=== DELIVERY_MESSAGE_START ===")
        print(delivery_message)
        print("=== DELIVERY_MESSAGE_END ===")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
