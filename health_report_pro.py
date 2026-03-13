#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康报告生成系统（OpenClaw Skill 通用版）
支持多种病理条件的饮食分析与评分
支持自定义评分权重和运动维度
"""

import sys
import json
import re
import os
from datetime import datetime, timedelta

# 导入常量库
from constants import DEFAULT_PORTIONS, FOOD_CALORIES

# 导入 PDF 生成模块
from pdf_generator import generate_pdf_report as generate_pdf_report_impl

# ==================== 配置加载 ====================

def load_user_config(config_path=None):
    """加载用户配置文件"""
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'user_config.json')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_condition_standards(config, condition_name):
    """获取指定病理的饮食标准"""
    standards = config.get('condition_standards', {})
    return standards.get(condition_name, standards.get('胆结石', {}))

def get_scoring_weights(config):
    """获取评分权重配置"""
    weights = config.get('scoring_weights', {
        'diet': 0.40,
        'water': 0.30,
        'weight': 0.30,
        'exercise': 0.00
    })
    
    # 归一化权重（确保总和为 1.0）
    total = sum(weights.values())
    if total > 0:
        return {k: v / total for k, v in weights.items()}
    return weights

def get_scoring_standards(config):
    """获取评分标准配置"""
    return config.get('scoring_standards', {})

# ==================== 基础计算 ====================

def calculate_bmi(weight_kg, height_cm):
    """计算 BMI"""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)

def calculate_bmr(weight_kg, height_cm, age, gender):
    """计算基础代谢率（Mifflin-St Jeor 公式）"""
    if gender == '男':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 1)

def calculate_tdee(bmr, activity_level):
    """计算每日总能量消耗"""
    return round(bmr * activity_level, 1)

def calculate_body_fat(weight_kg, height_cm, age, gender):
    """估算体脂率（简化公式）"""
    bmi = calculate_bmi(weight_kg, height_cm)
    if gender == '男':
        body_fat = 1.20 * bmi + 0.23 * age - 16.2
    else:
        body_fat = 1.20 * bmi + 0.23 * age - 5.4
    return round(body_fat, 1)

# ==================== 食物解析 ====================

def parse_food_entry(entry_text):
    """解析食物条目，返回食物名称和份量"""
    entry = entry_text.strip()
    
    for portion_prefix, portion_grams in DEFAULT_PORTIONS.items():
        if entry.startswith(portion_prefix):
            food_name = entry[len(portion_prefix):].strip()
            if not food_name:
                food_name = portion_prefix
            return food_name, portion_grams
    
    return entry, 100

def estimate_nutrition(food_name, portion_grams, calories_db):
    """估算食物营养"""
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
    return {
        'calories': round(nutrition.get('calories', 100) * scale, 1),
        'protein': round(nutrition.get('protein', 10) * scale, 1),
        'fat': round(nutrition.get('fat', 5) * scale, 1),
        'carb': round(nutrition.get('carb', 10) * scale, 1),
        'fiber': round(nutrition.get('fiber', 2) * scale, 1),
    }

# ==================== 饮食评估 ====================

def evaluate_diet(meal_data, standards, user_profile):
    """评估饮食是否符合病理标准"""
    evaluation = {
        'fat_ok': True,
        'protein_ok': True,
        'fiber_ok': True,
        'avoid_foods': [],
        'cooking_method_ok': True,
    }
    
    total_fat = meal_data.get('total_fat', 0)
    fat_min = standards.get('fat_min_g', 40)
    fat_max = standards.get('fat_max_g', 50)
    
    if total_fat < fat_min or total_fat > fat_max:
        evaluation['fat_ok'] = False
    
    avoid_foods = standards.get('avoid_foods', [])
    for food_item in meal_data.get('foods', []):
        for avoid in avoid_foods:
            if avoid in food_item:
                evaluation['avoid_foods'].append(food_item)
    
    cooking_methods = standards.get('cooking_methods', [])
    avoid_methods = standards.get('avoid_methods', [])
    
    for method in avoid_methods:
        if method in meal_data.get('cooking_method', ''):
            evaluation['cooking_method_ok'] = False
            break
    
    return evaluation

# ==================== 评分计算 ====================

def calculate_diet_score(daily_data, standards, scoring_standards):
    """计算饮食控制评分（0-100）"""
    score = 100
    
    diet_weights = scoring_standards.get('diet', {
        'fat_score_weight': 0.30,
        'protein_score_weight': 0.25,
        'fiber_score_weight': 0.25,
        'avoid_food_penalty': 0.20
    })
    
    # 脂肪评分
    total_fat = daily_data.get('total_fat', 0)
    fat_min = standards.get('fat_min_g', 40)
    fat_max = standards.get('fat_max_g', 50)
    
    if fat_min <= total_fat <= fat_max:
        fat_score = 100
    elif total_fat < fat_min:
        fat_score = max(0, 100 - (fat_min - total_fat) * 5)
    else:
        fat_score = max(0, 100 - (total_fat - fat_max) * 8)
    
    # 纤维评分
    total_fiber = daily_data.get('total_fiber', 0)
    fiber_min = standards.get('fiber_min_g', 25)
    
    if total_fiber >= fiber_min:
        fiber_score = 100
    else:
        fiber_score = max(0, 100 - (fiber_min - total_fiber) * 4)
    
    # 禁忌食物扣分
    avoid_count = len(daily_data.get('avoid_foods', []))
    avoid_penalty = min(100, avoid_count * 25)
    
    # 计算总分
    score = (
        fat_score * diet_weights.get('fat_score_weight', 0.30) +
        fiber_score * diet_weights.get('fiber_score_weight', 0.25) +
        (100 - avoid_penalty) * diet_weights.get('avoid_food_penalty', 0.20) +
        100 * diet_weights.get('protein_score_weight', 0.25)
    )
    
    return max(0, min(100, round(score, 1)))

def calculate_water_score(water_total, water_target):
    """计算饮水评分（0-100）"""
    if water_total >= water_target:
        return 100
    
    percentage = water_total / water_target
    if percentage >= 0.8:
        return round(80 + (percentage - 0.8) * 100, 1)
    elif percentage >= 0.5:
        return round(50 + (percentage - 0.5) * 60, 1)
    else:
        return round(percentage * 100, 1)

def calculate_weight_score(weight_recorded, target_weight, current_weight):
    """计算体重监测评分（0-100）"""
    score = 0
    
    # 记录体重得分（50%）
    if weight_recorded:
        score += 50
    
    # 体重趋势得分（50%）
    if current_weight and target_weight:
        diff = abs(current_weight - target_weight)
        if diff <= 1:
            score += 50
        elif diff <= 3:
            score += 30
        elif diff <= 5:
            score += 15
    
    return max(0, min(100, score))

def calculate_exercise_score(exercise_data, exercise_standards, scoring_standards):
    """计算运动评分（0-100）"""
    if not exercise_data:
        return 0
    
    exercise_weights = scoring_standards.get('exercise', {
        'duration_score_weight': 0.40,
        'frequency_score_weight': 0.30,
        'calorie_score_weight': 0.30,
        'daily_calorie_target': 300,
        'weekly_minutes_target': 150
    })
    
    # 时长评分
    total_minutes = sum(e.get('duration_min', 0) for e in exercise_data)
    weekly_target = exercise_standards.get('weekly_target_minutes', 150)
    daily_target = weekly_target / 7
    
    if total_minutes >= daily_target:
        duration_score = 100
    else:
        duration_score = round((total_minutes / daily_target) * 100, 1) if daily_target > 0 else 0
    
    # 频率评分（今天是否运动）
    frequency_score = 100 if len(exercise_data) > 0 else 0
    
    # 热量消耗评分
    total_calories = sum(e.get('calories', 0) for e in exercise_data)
    calorie_target = exercise_weights.get('daily_calorie_target', 300)
    
    if total_calories >= calorie_target:
        calorie_score = 100
    else:
        calorie_score = round((total_calories / calorie_target) * 100, 1) if calorie_target > 0 else 0
    
    # 计算总分
    score = (
        duration_score * exercise_weights.get('duration_score_weight', 0.40) +
        frequency_score * exercise_weights.get('frequency_score_weight', 0.30) +
        calorie_score * exercise_weights.get('calorie_score_weight', 0.30)
    )
    
    return max(0, min(100, round(score, 1)))

# ==================== 文件解析 ====================

def parse_memory_file(file_path):
    """解析健康记录文件"""
    data = {
        'date': '',
        'weight_morning': None,
        'weight_evening': None,
        'water_records': [],
        'meals': [],
        'exercise_records': [],
        'symptoms': [],
    }
    
    if not os.path.exists(file_path):
        return data
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    date_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    if date_match:
        data['date'] = date_match.group(1)
    
    weight_match = re.search(r'\*\*晨起空腹\*\*：([\d.]+) 斤', content)
    if weight_match:
        data['weight_morning'] = float(weight_match.group(1)) / 2
    
    water_matches = re.findall(r'累计：(\d+)ml/(\d+)ml', content)
    if water_matches:
        last_record = water_matches[-1]
        data['water_total'] = int(last_record[0])
        data['water_target'] = int(last_record[1])
    
    meal_sections = re.findall(r'### (早餐 | 午餐 | 晚餐 | 加餐).*?-.*?\n(.*?)(?=\n## |\n### |$)', content, re.DOTALL)
    for meal_type, meal_content in meal_sections:
        meal_data = {
            'type': meal_type,
            'foods': [],
            'total_calories': 0,
            'total_protein': 0,
            'total_fat': 0,
            'total_carb': 0,
            'total_fiber': 0,
        }
        
        food_lines = meal_content.split('\n')
        for line in food_lines:
            line = line.strip()
            if line.startswith('-') and '→' in line:
                food_match = re.match(r'-\s*(.+?)\s*→', line)
                if food_match:
                    food_name = food_match.group(1).strip()
                    food_name, portion = parse_food_entry(food_name)
                    nutrition = estimate_nutrition(food_name, portion, FOOD_CALORIES)
                    
                    meal_data['foods'].append(food_name)
                    meal_data['total_calories'] += nutrition['calories']
                    meal_data['total_protein'] += nutrition['protein']
                    meal_data['total_fat'] += nutrition['fat']
                    meal_data['total_carb'] += nutrition['carb']
                    meal_data['total_fiber'] += nutrition['fiber']
        
        data['meals'].append(meal_data)
    
    exercise_matches = re.findall(r'### (骑行 | 散步 | 跑步| 其他).*?\n(.*?)(?=\n## |\n### |$)', content, re.DOTALL)
    for exercise_type, exercise_content in exercise_matches:
        distance_match = re.search(r'距离：([\d.]+) 公里', exercise_content)
        duration_match = re.search(r'耗时：(\d+) 分', exercise_content)
        calories_match = re.search(r'消耗：(\d+) 千卡', exercise_content)
        
        exercise_data = {
            'type': exercise_type,
            'distance_km': float(distance_match.group(1)) if distance_match else 0,
            'duration_min': int(duration_match.group(1)) if duration_match else 0,
            'calories': int(calories_match.group(1)) if calories_match else 0,
        }
        data['exercise_records'].append(exercise_data)
    
    data['total_calories'] = sum(m.get('total_calories', 0) for m in data['meals'])
    data['total_protein'] = sum(m.get('total_protein', 0) for m in data['meals'])
    data['total_fat'] = sum(m.get('total_fat', 0) for m in data['meals'])
    data['total_carb'] = sum(m.get('total_carb', 0) for m in data['meals'])
    data['total_fiber'] = sum(m.get('total_fiber', 0) for m in data['meals'])
    
    return data

# ==================== 报告生成 ====================

def generate_text_report(health_data, config, date):
    """生成文本报告"""
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', '胆结石')
    standards = get_condition_standards(config, condition)
    scoring_weights = get_scoring_weights(config)
    scoring_standards = get_scoring_standards(config)
    
    # 计算各项评分
    diet_score = calculate_diet_score(health_data, standards, scoring_standards)
    water_score = calculate_water_score(
        health_data.get('water_total', 0),
        health_data.get('water_target', 2000)
    )
    weight_score = calculate_weight_score(
        health_data.get('weight_morning') is not None,
        user_profile.get('target_weight_kg', 64),
        health_data.get('weight_morning')
    )
    exercise_score = calculate_exercise_score(
        health_data.get('exercise_records', []),
        config.get('exercise_standards', {}),
        scoring_standards
    )
    
    # 计算总分（动态权重）
    total_score = round(
        diet_score * scoring_weights.get('diet', 0.40) +
        water_score * scoring_weights.get('water', 0.30) +
        weight_score * scoring_weights.get('weight', 0.30) +
        exercise_score * scoring_weights.get('exercise', 0.00),
        1
    )
    
    # 生成评语
    diet_comment = "低脂高纤达标" if diet_score >= 80 else "需注意脂肪控制"
    water_comment = f"{health_data.get('water_total', 0)}ml/{health_data.get('water_target', 2000)}ml"
    weight_comment = "按时记录" if weight_score >= 80 else "需坚持记录"
    exercise_comment = f"运动{len(health_data.get('exercise_records', []))}次" if exercise_score >= 60 else "需增加运动"
    
    report = f"""✅ **晚间数据已记录！**

### 🌟 {date} 今日综合评分
- 📌 **饮食控制**：⭐⭐⭐⭐⭐ {diet_score}/100
  - 评语：{diet_comment}
- 📌 **饮水完成**：⭐⭐⭐⭐ {water_score}/100
  - 评语：{water_comment}
- 📌 **体重监测**：⭐⭐⭐⭐⭐ {weight_score}/100
  - 评语：{weight_comment}
- 🏃 **运动消耗**：⭐⭐⭐⭐ {exercise_score}/100
  - 评语：{exercise_comment}

🎯 **总分：{total_score}/100**

---
### 📈 详细分析
- ✅ **做得好的地方**：
  - 低脂：{'达标' if diet_score >= 80 else '需改进'}
  - 高纤：{'达标' if health_data.get('total_fiber', 0) >= standards.get('fiber_min_g', 25) else '需增加蔬菜摄入'}
  - 运动：{'达标' if exercise_score >= 60 else '需增加运动量'}
- ⚠️ **需要改进**：
  - {'无，继续保持！' if total_score >= 90 else '饮水/饮食/体重记录需加强'}

---
"""
    return report

def generate_report(memory_file, date):
    """主报告生成函数"""
    config = load_user_config()
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', '胆结石')
    standards = get_condition_standards(config, condition)
    
    health_data = parse_memory_file(memory_file)
    text_report = generate_text_report(health_data, config, date)
    
    try:
        pdf_url = generate_pdf_report_impl(
            data=health_data,
            profile=user_profile,
            scores={
                'diet': calculate_diet_score(health_data, standards, config.get('scoring_standards', {})),
                'water': calculate_water_score(health_data.get('water_total', 0), health_data.get('water_target', 2000)),
                'weight': calculate_weight_score(health_data.get('weight_morning') is not None, user_profile.get('target_weight_kg', 64), health_data.get('weight_morning')),
                'exercise': calculate_exercise_score(health_data.get('exercise_records', []), config.get('exercise_standards', {}), config.get('scoring_standards', {}))
            },
            nutrition={
                'calories': health_data.get('total_calories', 0),
                'protein': health_data.get('total_protein', 0),
                'fat': health_data.get('total_fat', 0),
                'carb': health_data.get('total_carb', 0),
                'fiber': health_data.get('total_fiber', 0),
            },
            macros={'protein_p': 15, 'fat_p': 25, 'carb_p': 60},
            risks=[],
            plan={'calorie_target': 1500, 'meals': 3},
            output_path=f"/tmp/health_report_{date}.pdf",
            water_records=health_data.get('water_records', []),
            meals=health_data.get('meals', []),
            exercise_data=health_data.get('exercise_records', []),
        )
    except Exception as e:
        pdf_url = f"https://agent.btc354.com/health_report_{date}.pdf"
    
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
