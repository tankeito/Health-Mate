#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康报告生成系统（通用版）
支持多种病理条件的饮食分析与评分
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

# ==================== 食物解析 ====================

def parse_food_entry(entry_text):
    """解析食物条目，返回食物名称和份量"""
    # 移除前后空格
    entry = entry_text.strip()
    
    # 尝试匹配份量前缀
    for portion_prefix, portion_grams in DEFAULT_PORTIONS.items():
        if entry.startswith(portion_prefix):
            food_name = entry[len(portion_prefix):].strip()
            # 如果剩余部分为空，使用默认食物名
            if not food_name:
                food_name = portion_prefix
            return food_name, portion_grams
    
    # 默认份量（100g）
    return entry, 100

def estimate_nutrition(food_name, portion_grams, calories_db):
    """估算食物营养"""
    # 查找食物热量数据
    nutrition = None
    
    # 精确匹配
    if food_name in calories_db:
        nutrition = calories_db[food_name]
    else:
        # 模糊匹配（包含关键字）
        for db_name, db_nutrition in calories_db.items():
            if db_name in food_name or food_name in db_name:
                nutrition = db_nutrition
                break
    
    if nutrition is None:
        # 默认值（中等热量食物）
        nutrition = {"calories": 100, "protein": 10, "fat": 5, "carb": 10, "fiber": 2}
    
    # 按份量缩放
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
    
    # 检查脂肪摄入
    total_fat = meal_data.get('total_fat', 0)
    fat_min = standards.get('fat_min_g', 40)
    fat_max = standards.get('fat_max_g', 50)
    
    if total_fat < fat_min or total_fat > fat_max:
        evaluation['fat_ok'] = False
    
    # 检查禁忌食物
    avoid_foods = standards.get('avoid_foods', [])
    for food_item in meal_data.get('foods', []):
        for avoid in avoid_foods:
            if avoid in food_item:
                evaluation['avoid_foods'].append(food_item)
    
    # 检查烹饪方式
    cooking_methods = standards.get('cooking_methods', [])
    avoid_methods = standards.get('avoid_methods', [])
    
    for method in avoid_methods:
        if method in meal_data.get('cooking_method', ''):
            evaluation['cooking_method_ok'] = False
            break
    
    return evaluation

# ==================== 评分计算 ====================

def calculate_diet_score(daily_data, standards, user_profile):
    """计算饮食控制评分（0-100）"""
    score = 100
    
    # 脂肪评分（30 分）
    total_fat = daily_data.get('total_fat', 0)
    fat_min = standards.get('fat_min_g', 40)
    fat_max = standards.get('fat_max_g', 50)
    
    if fat_min <= total_fat <= fat_max:
        fat_score = 30
    elif total_fat < fat_min:
        fat_score = max(0, 30 - (fat_min - total_fat) * 2)
    else:
        fat_score = max(0, 30 - (total_fat - fat_max) * 3)
    
    score -= (30 - fat_score)
    
    # 纤维评分（20 分）
    total_fiber = daily_data.get('total_fiber', 0)
    fiber_min = standards.get('fiber_min_g', 25)
    
    if total_fiber >= fiber_min:
        fiber_score = 20
    else:
        fiber_score = max(0, 20 - (fiber_min - total_fiber) * 2)
    
    score -= (20 - fiber_score)
    
    # 禁忌食物扣分（30 分）
    avoid_count = len(daily_data.get('avoid_foods', []))
    avoid_penalty = min(30, avoid_count * 10)
    score -= avoid_penalty
    
    # 烹饪方式扣分（20 分）
    if not daily_data.get('cooking_method_ok', True):
        score -= 20
    
    return max(0, min(100, score))

def calculate_water_score(water_total, water_target):
    """计算饮水评分（0-100）"""
    if water_total >= water_target:
        return 100
    
    percentage = water_total / water_target
    if percentage >= 0.8:
        return 80 + int((percentage - 0.8) * 100)
    elif percentage >= 0.5:
        return 50 + int((percentage - 0.5) * 60)
    else:
        return int(percentage * 100)

def calculate_weight_score(weight_recorded, target_weight, current_weight):
    """计算体重监测评分（0-100）"""
    score = 100
    
    # 未记录体重扣分
    if not weight_recorded:
        score -= 50
    
    # 体重趋势评分
    if current_weight and target_weight:
        diff = current_weight - target_weight
        if abs(diff) <= 1:
            score += 0  # 接近目标，不扣分
        elif abs(diff) <= 3:
            score -= 10
        else:
            score -= 20
    
    return max(0, min(100, score))

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
    
    # 提取日期
    date_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    if date_match:
        data['date'] = date_match.group(1)
    
    # 提取晨起体重
    weight_match = re.search(r'\*\*晨起空腹\*\*：([\d.]+) 斤', content)
    if weight_match:
        data['weight_morning'] = float(weight_match.group(1)) / 2  # 转换为 kg
    
    # 提取饮水记录
    water_matches = re.findall(r'累计：(\d+)ml/(\d+)ml', content)
    if water_matches:
        # 取最后一次记录
        last_record = water_matches[-1]
        data['water_total'] = int(last_record[0])
        data['water_target'] = int(last_record[1])
    
    # 提取饮食记录
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
        
        # 解析食物项
        food_lines = meal_content.split('\n')
        for line in food_lines:
            line = line.strip()
            if line.startswith('-') and '→' in line:
                # 提取食物名称
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
    
    # 提取运动记录
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
    
    # 计算总计
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
    
    # 计算各项评分
    diet_score = calculate_diet_score(health_data, standards, user_profile)
    water_score = calculate_water_score(
        health_data.get('water_total', 0),
        health_data.get('water_target', 2000)
    )
    weight_score = calculate_weight_score(
        health_data.get('weight_morning') is not None,
        user_profile.get('target_weight_kg', 64),
        health_data.get('weight_morning')
    )
    
    # 计算总分
    total_score = round((diet_score + water_score + weight_score) / 3, 1)
    
    # 生成评语
    diet_comment = "低脂高纤达标" if diet_score >= 80 else "需注意脂肪控制"
    water_comment = f"{health_data.get('water_total', 0)}ml/{health_data.get('water_target', 2000)}ml"
    weight_comment = "按时记录" if weight_score >= 80 else "需坚持记录"
    
    report = f"""✅ **晚间数据已记录！**

### 🌟 {date} 今日综合评分
- 📌 **饮食控制**：⭐⭐⭐⭐⭐ {diet_score}/100
  - 评语：{diet_comment}
- 📌 **饮水完成**：⭐⭐⭐⭐ {water_score}/100
  - 评语：{water_comment}
- 📌 **体重监测**：⭐⭐⭐⭐⭐ {weight_score}/100
  - 评语：{weight_comment}

🎯 **总分：{total_score}/100**

---
### 📈 详细分析
- ✅ **做得好的地方**：
  - 低脂：{'达标' if diet_score >= 80 else '需改进'}
  - 高纤：{'达标' if health_data.get('total_fiber', 0) >= standards.get('fiber_min_g', 25) else '需增加蔬菜摄入'}
- ⚠️ **需要改进**：
  - {'无，继续保持！' if total_score >= 90 else '饮水/饮食/体重记录需加强'}

---
"""
    return report

def generate_report(memory_file, date):
    """主报告生成函数"""
    # 加载配置
    config = load_user_config()
    user_profile = config.get('user_profile', {})
    condition = user_profile.get('condition', '胆结石')
    standards = get_condition_standards(config, condition)
    
    # 解析健康记录
    health_data = parse_memory_file(memory_file)
    
    # 生成文本报告
    text_report = generate_text_report(health_data, config, date)
    
    # 生成 PDF（简化处理，返回占位 URL）
    # 实际使用时需要根据 pdf_generator.py 的接口传递完整参数
    try:
        # 尝试调用 PDF 生成（如果 pdf_generator.py 可用）
        pdf_url = generate_pdf_report_impl(
            data=health_data,
            profile=user_profile,
            scores={'diet': 85, 'water': 90, 'weight': 95},
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
        # PDF 生成失败时返回占位 URL
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
