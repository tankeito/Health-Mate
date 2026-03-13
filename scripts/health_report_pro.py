#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康报告生成系统（专业版 v3.0 - 完整数据解析）
- 完整解析饮水时间轴、风险预警、次日方案
- 运动改为加分项（Bonus），基础分由饮食 + 饮水 + 体重构成
- 文本报告恢复完整排版（分项汇总、详情、风险、方案）
"""

import sys
import json
import re
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# ==================== 路径管理 ====================
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()
CONFIG_DIR = PROJECT_ROOT / 'config'
ASSETS_DIR = PROJECT_ROOT / 'assets'
LOGS_DIR = PROJECT_ROOT / 'logs'
REPORTS_DIR = PROJECT_ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPT_DIR))

from constants import DEFAULT_PORTIONS, FOOD_CALORIES
from pdf_generator import generate_pdf_report as generate_pdf_report_impl

# ==================== 配置加载 ====================
def load_user_config(config_path=None):
    if config_path is None:
        config_path = CONFIG_DIR / 'user_config.json'
    if not os.path.exists(config_path):
        return _get_default_config()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告：读取配置文件失败 - {e}", file=sys.stderr)
        return _get_default_config()

def _get_default_config():
    return {
        "user_profile": {
            "name": "东东", "gender": "男", "age": 34, "height_cm": 172,
            "current_weight_kg": 65, "target_weight_kg": 64, "condition": "胆结石", "activity_level": 1.2
        },
        "condition_standards": {"胆结石": {"fat_min_g": 40, "fat_max_g": 50, "fiber_min_g": 25, "water_min_ml": 2000}},
        "scoring_weights": {"diet": 0.45, "water": 0.35, "weight": 0.20, "exercise_bonus": 0.10},
        "exercise_standards": {"weekly_target_minutes": 150}
    }

def get_condition_standards(config, condition_name):
    standards = config.get('condition_standards', {})
    return standards.get(condition_name, standards.get('胆结石', {}))

def get_scoring_weights(config):
    """获取评分权重（运动作为 bonus，不参与基础分权重计算）"""
    weights = config.get('scoring_weights', {'diet': 0.45, 'water': 0.35, 'weight': 0.20})
    weights = {k: v for k, v in weights.items() if isinstance(v, (int, float)) and k != 'exercise_bonus'}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights

def get_exercise_bonus_weight(config):
    """获取运动加分权重（默认 10%）"""
    weights = config.get('scoring_weights', {})
    return weights.get('exercise_bonus', 0.10)

# ==================== 基础计算 ====================
def calculate_bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm: return 0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)

def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender == '男':
        return round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5, 1)
    return round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161, 1)

def calculate_tdee(bmr, activity_level):
    return round(bmr * activity_level, 1)

# ==================== 食物解析 ====================
def parse_food_entry(entry_text):
    entry = entry_text.strip()
    for portion_prefix, portion_grams in DEFAULT_PORTIONS.items():
        if entry.startswith(portion_prefix):
            food_name = entry[len(portion_prefix):].strip()
            return food_name if food_name else portion_prefix, portion_grams
    return entry, 100

def estimate_nutrition(food_name, portion_grams, calories_db):
    nutrition = None
    if food_name in calories_db:
        nutrition = calories_db[food_name]
    else:
        for db_name, db_nutrition in calories_db.items():
            if db_name in food_name or food_name in db_name:
                nutrition = db_nutrition
                break
    if nutrition is None:
        nutrition = {"calories": 100, "protein": 10, "fat": 5, "carb": 10, "fiber": 2}
    scale = portion_grams / 100.0
    return {k: round(nutrition.get(k, 0) * scale, 1) for k in ['calories', 'protein', 'fat', 'carb', 'fiber']}

# ==================== 评分计算 ====================
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

def calculate_exercise_score(exercise_data, exercise_standards, scoring_standards):
    try:
        if not exercise_data or not isinstance(exercise_data, list): return 0
        exercise_weights = scoring_standards.get('exercise', {'duration_score_weight': 0.40, 'frequency_score_weight': 0.30, 'calorie_score_weight': 0.30, 'daily_calorie_target': 300})
        total_minutes = sum(e.get('duration_min', 0) for e in exercise_data if isinstance(e, dict))
        daily_target = exercise_standards.get('weekly_target_minutes', 150) / 7
        duration_score = 100 if total_minutes >= daily_target else round((total_minutes / daily_target) * 100, 1) if daily_target > 0 else 0
        frequency_score = 100 if len(exercise_data) > 0 else 0
        total_calories = sum(e.get('calories', 0) for e in exercise_data if isinstance(e, dict))
        calorie_target = exercise_weights.get('daily_calorie_target', 300)
        calorie_score = 100 if total_calories >= calorie_target else round((total_calories / calorie_target) * 100, 1) if calorie_target > 0 else 0
        score = duration_score * exercise_weights.get('duration_score_weight', 0.40) + frequency_score * exercise_weights.get('frequency_score_weight', 0.30) + calorie_score * exercise_weights.get('calorie_score_weight', 0.30)
        return max(0, min(100, round(score, 1)))
    except Exception as e:
        print(f"警告：运动评分计算失败 - {e}", file=sys.stderr)
        return 0

# ==================== 核心修复：完整文件解析 ====================
def parse_memory_file(file_path):
    """完整解析健康记录文件（饮水时间轴、风险、方案全部解析）"""
    data = {
        'date': '', 'weight_morning': None, 'weight_evening': None,
        'water_records': [], 'meals': [], 'exercise_records': [],
        'symptoms': [], 'risks': [], 'plan': {},
        'water_total': 0, 'water_target': 2000,
        'total_calories': 0, 'total_protein': 0, 'total_fat': 0, 'total_carb': 0, 'total_fiber': 0,
        'steps': 0,
    }
    if not os.path.exists(file_path): return data
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析日期
    date_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    if date_match: data['date'] = date_match.group(1)
    
    # 解析晨起体重
    weight_match = re.search(r'\*\*晨起空腹\*\*：([\d.]+) 斤', content)
    if weight_match: data['weight_morning'] = float(weight_match.group(1)) / 2
    
    # 完整解析饮水记录（时间轴）- 使用简单可靠的正则（注意：选择操作符不能有空格！）
    water_matches = re.findall(r'### (晨起|上午|中午|下午|晚上)[^\n]*\n- 饮水量：(\d+)ml\n- 累计：(\d+)ml/(\d+)ml', content)
    for time_label, amount, cum, target in water_matches:
        data['water_records'].append({'time': time_label, 'amount_ml': int(amount), 'cumulative_ml': int(cum)})
    if water_matches:
        data['water_total'] = int(water_matches[-1][2])
        data['water_target'] = int(water_matches[-1][3])
    
    # 解析饮食记录（含详细食材）- 使用简单正则（选择操作符不能有空格！）
    meal_matches = re.findall(r'### (早餐|午餐|晚餐|加餐)[^\n]*\n(.*?)(?=\n## |\n### |\Z)', content, re.DOTALL)
    for meal_type, meal_content in meal_matches:
        # 提取时间（如果有）
        time_match = re.search(r'（([\d:]+)）', meal_content)
        meal_time = time_match.group(1) if time_match else ""
        
        meal_data = {
            'type': meal_type, 'time': meal_time, 'foods': [], 'food_nutrition': [],
            'total_calories': 0, 'total_protein': 0, 'total_fat': 0, 'total_carb': 0, 'total_fiber': 0,
        }
        
        food_lines = meal_content.split('\n')
        for line in food_lines:
            line = line.strip()
            # 只解析食物行（以 - 开头，包含→，且不包含总计/评估等关键字）
            if line.startswith('-') and '→' in line:
                if any(kw in line for kw in ['总计', '评估', '蛋白质：', '脂肪：', '碳水：', '纤维：']):
                    continue
                food_match = re.match(r'-\s*(.+?)\s*→', line)
                if food_match:
                    food_name = food_match.group(1).strip()
                    food_name_clean, portion = parse_food_entry(food_name)
                    nutrition = estimate_nutrition(food_name_clean, portion, FOOD_CALORIES)
                    meal_data['foods'].append(food_name)
                    meal_data['food_nutrition'].append({'name': food_name, 'portion_grams': portion, **nutrition})
                    for k in ['calories', 'protein', 'fat', 'carb', 'fiber']:
                        meal_data[f'total_{k}'] += nutrition[k]
        
        data['meals'].append(meal_data)
    
    # 解析运动记录
    exercise_matches = re.findall(r'### (骑行|散步|跑步|其他)[^\n]*\n(.*?)(?=\n## |\n### |\Z)', content, re.DOTALL)
    for exercise_type, exercise_content in exercise_matches:
        distance_match = re.search(r'距离：([\d.]+) 公里', exercise_content)
        duration_match = re.search(r'耗时：(\d+) 分', exercise_content)
        calories_match = re.search(r'消耗：(\d+) 千卡', exercise_content)
        data['exercise_records'].append({
            'type': exercise_type,
            'distance_km': float(distance_match.group(1)) if distance_match else 0,
            'duration_min': int(duration_match.group(1)) if duration_match else 0,
            'calories': int(calories_match.group(1)) if calories_match else 0,
        })
    
    # 解析步数
    steps_match = re.search(r'\*\*总步数\*\*：(\d+) 步', content)
    if steps_match:
        data['steps'] = int(steps_match.group(1))
    
    # 解析症状
    symptom_section = re.search(r'## 📝 症状/不适.*?\n(.*?)(?=\n## |$)', content, re.DOTALL)
    if symptom_section:
        symptom_text = symptom_section.group(1).strip()
        if symptom_text and symptom_text != '_（无记录）_' and symptom_text != '（待记录）':
            data['symptoms'] = [s.strip() for s in symptom_text.split('\n') if s.strip()]
    
    # 计算总计
    data['total_calories'] = sum(m.get('total_calories', 0) for m in data['meals'])
    data['total_protein'] = sum(m.get('total_protein', 0) for m in data['meals'])
    data['total_fat'] = sum(m.get('total_fat', 0) for m in data['meals'])
    data['total_carb'] = sum(m.get('total_carb', 0) for m in data['meals'])
    data['total_fiber'] = sum(m.get('total_fiber', 0) for m in data['meals'])
    
    # 生成风险预警
    standards = get_condition_standards(load_user_config(), '胆结石')
    fat_min, fat_max = standards.get('fat_min_g', 40), standards.get('fat_max_g', 50)
    fiber_min = standards.get('fiber_min_g', 25)
    
    if data['total_fat'] > 0 and data['total_fat'] < fat_min * 0.6:
        data['risks'].append({'level': '中风险', 'item': '脂肪摄入过低', 'risk': f'仅{data["total_fat"]:.1f}g（推荐{fat_min}-{fat_max}g），完全无脂可能导致胆汁淤积', 'action': f'明日适量增加健康脂肪（如橄榄油 5ml、坚果少量）'})
    elif data['total_fat'] > fat_max:
        data['risks'].append({'level': '高风险', 'item': '脂肪摄入超标', 'risk': f'{data["total_fat"]:.1f}g（上限{fat_max}g），可能诱发胆绞痛', 'action': '明日严格控油，避免油炸、红烧'})
    
    if data['total_fiber'] > 0 and data['total_fiber'] < fiber_min * 0.6:
        data['risks'].append({'level': '中风险', 'item': '膳食纤维不足', 'risk': f'仅{data["total_fiber"]:.1f}g（推荐≥{fiber_min}g），影响胆汁排泄', 'action': '明日增加蔬菜、粗粮摄入'})
    
    if data['water_total'] > 0 and data['water_total'] < data['water_target'] * 0.8:
        data['risks'].append({'level': '低风险', 'item': '饮水不足', 'risk': f'仅{data["water_total"]}ml（目标{data["water_target"]}ml）', 'action': '设置每小时饮水提醒'})
    
    if data.get('steps', 0) > 0 and data['steps'] < 3000:
        data['risks'].append({'level': '低风险', 'item': '活动量不足', 'risk': f'今日仅{data.get("steps", 0)}步', 'action': '明日增加散步或骑行'})
    
    # 生成次日方案
    data['plan'] = {
        'diet': [
            '早餐（5 分钟）：燕麦粥 + 煮蛋白 2 个 + 凉拌黄瓜 (300kcal)',
            '午餐（10 分钟）：米饭 + 卤牛肉 + 白灼青菜 (450kcal)',
            '晚餐（10 分钟）：杂粮粥 + 凉拌豆腐 + 炒蔬菜 (350kcal)',
        ],
        'water': [
            '⏰ 07:30 晨起温水 300ml', '⏰ 10:00 工作间隙 400ml',
            '⏰ 14:00 午后 400ml', '⏰ 17:00 下班前 400ml', '⏰ 20:00 晚间 300ml',
            f'📊 目标总量：{data["water_target"]}ml',
        ],
        'exercise': [
            '🚶 早餐后散步 15 分钟（促进胆汁排泄）',
            '🚶 晚餐后散步 20 分钟（帮助消化）',
            '💡 本周目标：累计运动 150 分钟',
        ],
        'notes': ['今日推荐水果：苹果，耙耙柑，香蕉，梨'],
    }
    
    if data['total_fat'] > 0 and data['total_fat'] < fat_min * 0.6:
        data['plan']['notes'].append('昨日脂肪过低，今日适量增加健康脂肪（橄榄油 5-10ml 或坚果 10g）')
    
    return data

# ==================== 文本报告生成（完整版） ====================
def get_star_string(score):
    stars_count = max(1, min(5, int(score / 20)))
    return "⭐" * stars_count

def generate_text_report(health_data, config, date):
    """生成完整文本报告（恢复昨日丰富度）"""
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', '胆结石')
    standards = get_condition_standards(config, condition)
    scoring_weights = get_scoring_weights(config)
    scoring_standards = config.get('scoring_standards', {})
    exercise_standards = config.get('exercise_standards', {})
    
    # 计算各项评分
    diet_score = calculate_diet_score(health_data, standards, scoring_standards)
    water_score = calculate_water_score(health_data.get('water_total', 0), health_data.get('water_target', 2000))
    weight_score = calculate_weight_score(health_data.get('weight_morning') is not None, user_profile.get('target_weight_kg', 64), health_data.get('weight_morning'))
    exercise_score = calculate_exercise_score(health_data.get('exercise_records', []), exercise_standards, scoring_standards)
    
    # 基础分（饮食 + 饮水 + 体重）
    base_score = round(diet_score * scoring_weights.get('diet', 0.45) + water_score * scoring_weights.get('water', 0.35) + weight_score * scoring_weights.get('weight', 0.20), 1)
    
    # 运动加分（Bonus，上限 10 分）
    exercise_bonus = round(exercise_score * get_exercise_bonus_weight(config), 1)
    total_score = min(100, round(base_score + exercise_bonus, 1))
    
    # 计算 BMI、BMR、TDEE
    weight_kg = health_data.get('weight_morning')
    bmi = calculate_bmi(weight_kg, user_profile.get('height_cm', 172)) if weight_kg else 0
    bmr = calculate_bmr(weight_kg if weight_kg else 65, user_profile.get('height_cm', 172), user_profile.get('age', 34), user_profile.get('gender', '男')) if weight_kg else 0
    tdee = calculate_tdee(bmr, user_profile.get('activity_level', 1.2)) if bmr else 0
    
    # 生成报告
    report = f"""✅ **晚间数据已记录！**

### 🌟 {date} 今日综合评分

🎯 **总分：{get_star_string(total_score)} {total_score}/100**

---

📊 **分项汇总**

* **饮食合规性** {get_star_string(diet_score)} {diet_score}/100
  {'✅ 脂肪摄入合理' if 40 <= health_data.get('total_fat', 0) <= 50 else '⚠️ 脂肪摄入过低' if health_data.get('total_fat', 0) < 40 else '⚠️ 脂肪摄入超标'} ({health_data.get('total_fat', 0):.1f}g) | {'✅ 蛋白质摄入充足' if health_data.get('total_protein', 0) >= 60 else '⚠️ 蛋白质不足'}

* **饮水完成度** {get_star_string(water_score)} {water_score}/100
  {health_data.get('water_total', 0)}ml/{health_data.get('water_target', 2000)}ml，{health_data.get('water_total', 0) // 20}% 完成度

* **体重管理** {get_star_string(weight_score)} {weight_score}/100
  晨起空腹：{health_data.get('weight_morning', 0) * 2:.1f}斤，BMI：{bmi:.1f}

* **症状管理** {get_star_string(100 if not health_data.get('symptoms') else 50)} {100 if not health_data.get('symptoms') else 50}/100
  {'✅ 无不适症状' if not health_data.get('symptoms') else '⚠️ ' + '；'.join(health_data.get('symptoms', []))}

* **运动管理** {get_star_string(exercise_score)} {exercise_score}/100
  {generate_exercise_summary(health_data)}

* **健康依从性** {get_star_string(100 if len(health_data.get('meals', [])) >= 3 else 50)} {100 if len(health_data.get('meals', [])) >= 3 else 50}/100
  完成{len(health_data.get('meals', []))}餐，饮水{'达标' if health_data.get('water_total', 0) >= health_data.get('water_target', 2000) else '未达标'}

---

### 📝 今日详情汇总

**🥗 进食情况**
{generate_meal_summary(health_data)}

**💧 饮水情况**
{generate_water_summary(health_data)}

**🏃 运动情况**
{generate_exercise_detail(health_data)}

---

### 📈 基础健康数据

**身体指标**
* 身高：{user_profile.get('height_cm', 172)}cm
* 体重：{health_data.get('weight_morning', 0) * 2:.1f}斤（{weight_kg if weight_kg else '未记录'}kg）
* BMI：{bmi:.1f}
* 基础代谢 (BMR)：{bmr:.0f} kcal
* 每日消耗 (TDEE)：{tdee:.0f} kcal

**热量与营养素**
* 当日摄入热量：{health_data.get('total_calories', 0):.0f} kcal
* 蛋白质：{health_data.get('total_protein', 0):.1f}g（推荐{user_profile.get('current_weight_kg', 65) * 1.2:.0f}g）
* 脂肪：{health_data.get('total_fat', 0):.1f}g（推荐{standards.get('fat_min_g', 40)}-{standards.get('fat_max_g', 50)}g）
* 碳水：{health_data.get('total_carb', 0):.1f}g（推荐{(tdee * 0.55 / 4):.0f}g）
* 膳食纤维：{health_data.get('total_fiber', 0):.1f}g（推荐≥{standards.get('fiber_min_g', 25)}g）

---

### ⚠️ 风险预警

{generate_risk_alerts(health_data)}

---

### 📋 次日优化方案

{generate_next_day_plan(health_data, user_profile)}

---
"""
    return report

def generate_meal_summary(health_data):
    meals = health_data.get('meals', [])
    if not meals: return '无记录'
    lines = []
    for meal in meals:
        foods = '、'.join(meal.get('foods', [])[:3])
        if len(meal.get('foods', [])) > 3: foods += ' 等'
        lines.append(f"{meal.get('type', '')}({meal.get('time', '')}): {foods} - {meal.get('total_calories', 0):.0f}kcal")
    return '\n'.join(lines) if lines else '无详细记录'

def generate_water_summary(health_data):
    records = health_data.get('water_records', [])
    if not records: return '无记录'
    lines = []
    for r in records[:6]:
        lines.append(f"{r.get('time', '')}({r.get('time', '')}): {r.get('amount_ml', 0)}ml")
    lines.append(f"→ 总计：{health_data.get('water_total', 0)}ml/{health_data.get('water_target', 2000)}ml")
    return '\n'.join(lines)

def generate_exercise_summary(health_data):
    exercises = health_data.get('exercise_records', [])
    steps = health_data.get('steps', 0)
    if not exercises and steps == 0: return '无记录'
    parts = []
    for e in exercises:
        if e.get('type') == '骑行':
            parts.append(f"骑行：{e.get('distance_km', 0)}km/{e.get('duration_min', 0)}分钟")
    if steps > 0:
        parts.append(f"步数：{steps}步")
    return '；'.join(parts) if parts else '无记录'

def generate_exercise_detail(health_data):
    exercises = health_data.get('exercise_records', [])
    steps = health_data.get('steps', 0)
    if not exercises and steps == 0: return '无记录'
    lines = []
    cycling = [e for e in exercises if e.get('type') == '骑行']
    if cycling:
        total_km = sum(e.get('distance_km', 0) for e in cycling)
        total_min = sum(e.get('duration_min', 0) for e in cycling)
        details = [f"{e.get('distance_km', 0)}km/{e.get('duration_min', 0)}分钟" for e in cycling]
        lines.append(f"骑行：{'、'.join(details)}（合计{total_km:.2f}km/{total_min:.1f}分钟）")
    if steps > 0:
        lines.append(f"步数：{steps}步")
    return '\n'.join(lines) if lines else '无详细记录'

def generate_risk_alerts(health_data):
    risks = health_data.get('risks', [])
    if not risks: return '* ✅ 今日无明显风险，继续保持！'
    lines = []
    for r in risks:
        lines.append(f"* {r.get('level', '风险')} {r.get('item', '')}：{r.get('risk', '')}")
        lines.append(f"  → {r.get('action', '')}")
    return '\n'.join(lines)

def generate_next_day_plan(health_data, user_profile):
    plan = health_data.get('plan', {})
    lines = []
    
    if plan.get('diet'):
        lines.append('**🥗 饮食建议**')
        lines.append('* 【居家简易版】')
        for item in plan.get('diet', []):
            lines.append(f'* {item}')
        lines.append('')
    
    if plan.get('water'):
        lines.append('**💧 饮水计划**')
        for item in plan.get('water', []):
            lines.append(f'* {item}')
        lines.append('')
    
    if plan.get('exercise'):
        lines.append('**🏃 运动建议**')
        lines.append('* 【久坐人群专属运动方案】')
        for item in plan.get('exercise', []):
            lines.append(f'* {item}')
        lines.append('')
    
    if plan.get('notes'):
        lines.append('**⚠️ 特别关注**')
        lines.append('* 【易买食材清单（便利店/超市）】')
        lines.append('* 蛋白质：即食鸡胸肉、卤牛肉（真空包装）、蛋白粉、脱脂奶')
        lines.append('* 主食：即食燕麦、玉米（真空包装）、全麦面包、杂粮粥料')
        lines.append('* 蔬菜：黄瓜、西红柿、生菜（可生吃或简单焯水）')
        lines.append(f"* 水果：{', '.join(user_profile.get('dietary_preferences', {}).get('favorite_fruits', ['苹果', '耙耙柑', '香蕉', '梨']))}")
        lines.append('* 调料：橄榄油、醋、生抽（少盐）')
        for item in plan.get('notes', []):
            lines.append(f'* {item}')
    
    return '\n'.join(lines)

# ==================== PDF 报告生成（完整数据） ====================
def generate_report(memory_file, date):
    """主报告生成函数（完整数据解析 + Web 目录分发）"""
    config = load_user_config()
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', '胆结石')
    standards = get_condition_standards(config, condition)
    scoring_standards = config.get('scoring_standards', {})
    exercise_standards = config.get('exercise_standards', {})
    
    # 解析健康记录
    health_data = parse_memory_file(memory_file)
    
    # 计算各项评分
    diet_score = calculate_diet_score(health_data, standards, scoring_standards)
    water_score = calculate_water_score(health_data.get('water_total', 0), health_data.get('water_target', 2000))
    weight_score = calculate_weight_score(health_data.get('weight_morning') is not None, user_profile.get('target_weight_kg', 64), health_data.get('weight_morning'))
    exercise_score = calculate_exercise_score(health_data.get('exercise_records', []), exercise_standards, scoring_standards)
    
    # 基础分 + 运动加分
    scoring_weights = get_scoring_weights(config)
    base_score = round(diet_score * scoring_weights.get('diet', 0.45) + water_score * scoring_weights.get('water', 0.35) + weight_score * scoring_weights.get('weight', 0.20), 1)
    exercise_bonus = round(exercise_score * get_exercise_bonus_weight(config), 1)
    total_score = min(100, round(base_score + exercise_bonus, 1))
    
    # 生成文本报告
    text_report = generate_text_report(health_data, config, date)
    
    # 准备 PDF 数据
    bmi = calculate_bmi(health_data.get('weight_morning'), user_profile.get('height_cm', 172)) if health_data.get('weight_morning') else 0
    
    pdf_scores_dict = {
        'diet': {'raw': diet_score, 'stars': get_star_string(diet_score)},
        'water': {'raw': water_score, 'stars': get_star_string(water_score)},
        'weight': {'raw': weight_score, 'stars': get_star_string(weight_score), 'bmi': bmi},
        'exercise': {'raw': exercise_score, 'stars': get_star_string(exercise_score)},
        'symptom': {'raw': 100 if not health_data.get('symptoms') else 50, 'stars': get_star_string(100 if not health_data.get('symptoms') else 50), 'has_symptoms': bool(health_data.get('symptoms'))},
        'adherence': {'raw': 100 if len(health_data.get('meals', [])) >= 3 else 50, 'stars': get_star_string(100 if len(health_data.get('meals', [])) >= 3 else 50)},
        'total': total_score,
        'total_stars': get_star_string(total_score)
    }
    
    # 计算 macros
    tdee = calculate_tdee(calculate_bmr(health_data.get('weight_morning') or 65, user_profile.get('height_cm', 172), user_profile.get('age', 34), user_profile.get('gender', '男')), user_profile.get('activity_level', 1.2))
    macros = {
        'protein_p': 15, 'fat_p': 25, 'carb_p': 60,
        'protein_g': round(user_profile.get('current_weight_kg', 65) * 1.2),
        'fat_g': round(standards.get('fat_max_g', 50)),
        'carb_g': round(tdee * 0.60 / 4),
        'fiber_min_g': standards.get('fiber_min_g', 25)
    }
    
    pdf_filename = f"health_report_{date}.pdf"
    local_pdf_path = str(REPORTS_DIR / pdf_filename)
    web_dir = os.environ.get("REPORT_WEB_DIR", "")
    base_url = os.environ.get("REPORT_BASE_URL", "https://agent.btc354.com").rstrip('/')
    
    # 生成 PDF（传入真实数据！）
    try:
        generate_pdf_report_impl(
            data=health_data,
            profile=user_profile,
            scores=pdf_scores_dict,
            nutrition={
                'calories': health_data.get('total_calories', 0),
                'protein': health_data.get('total_protein', 0),
                'fat': health_data.get('total_fat', 0),
                'carb': health_data.get('total_carb', 0),
                'fiber': health_data.get('total_fiber', 0),
            },
            macros=macros,
            risks=health_data.get('risks', []),  # 真实风险数据
            plan=health_data.get('plan', {}),  # 真实方案数据
            output_path=local_pdf_path,
            water_records=health_data.get('water_records', []),
            meals=health_data.get('meals', []),
            exercise_data=health_data.get('exercise_records', [])
        )
        
        # 复制到 Web 目录
        if web_dir and os.path.exists(web_dir):
            web_pdf_path = os.path.join(web_dir, pdf_filename)
            shutil.copy2(local_pdf_path, web_pdf_path)
            pdf_url = f"{base_url}/{pdf_filename}"
        else:
            print(f"提示：未配置 REPORT_WEB_DIR 或目录不存在，PDF 仅保存在本地 {local_pdf_path}", file=sys.stderr)
            pdf_url = f"{base_url}/{pdf_filename}"
    except Exception as e:
        print(f"警告：PDF 生成失败 - {e}", file=sys.stderr)
        pdf_url = f"{base_url}/{pdf_filename}"
    
    return text_report, pdf_url

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法：python3 health_report_pro.py <memory_file> <date>")
        sys.exit(1)
    
    memory_file = sys.argv[1]
    date = sys.argv[2]
    
    try:
        text_report, pdf_url = generate_report(memory_file, date)
        print("=== TEXT_REPORT_START ===")
        print(text_report)
        print("=== TEXT_REPORT_END ===")
        print("=== PDF_URL ===")
        print(pdf_url)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
