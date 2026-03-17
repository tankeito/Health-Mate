#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每周健康总复盘控制器 (weekly_report_pro.py)
整合 7 天散列数据 -> AI 深度复盘 -> 生成多趋势图表 PDF 周报
用法：python3 weekly_report_pro.py 2026-03-15
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timedelta

# 复用原来的环境变量检查和基础配置
from health_report_pro import validate_environment, load_user_config, get_condition_standards, parse_memory_file, calculate_diet_score

validate_environment()

MEMORY_DIR = os.environ.get('MEMORY_DIR', '/root/.openclaw/workspace/memory')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)

from weekly_pdf_generator import generate_weekly_pdf_report

def get_week_dates(target_date_str):
    """获取指定日期所在周的周一至周日的日期列表"""
    dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    # weekday() 返回 0-6 代表周一到周日
    monday = dt - timedelta(days=dt.weekday())
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

def aggregate_weekly_data(week_dates, config):
    """遍历 7 天的 markdown 文件并提取聚合数据"""
    standards = get_condition_standards(config, config.get('user_profile', {}).get('condition', '胆结石'))
    scoring_standards = config.get('scoring_standards', {})
    
    weekly_data = {
        'start_date': week_dates[0],
        'end_date': week_dates[-1],
        'dates': week_dates,
        'weights': [],
        'water_intakes': [],
        'steps': [],
        'calories': [],
        'protein': [], # [新增] 蛋白质追踪
        'fat': [],     # [新增] 脂肪追踪
        'carb': [],    # [新增] 碳水追踪
        'symptoms_count': 0,
        'diet_scores': []
    }
    
    first_weight = None
    last_weight = None
    
    for date_str in week_dates:
        file_path = os.path.join(MEMORY_DIR, f"{date_str}.md")
        daily_data = parse_memory_file(file_path) # 复用你原来无比强大的散列抓取函数
        
        # 提取指标
        w = daily_data.get('weight_morning')
        weekly_data['weights'].append(w)
        if w:
            if first_weight is None: first_weight = w
            last_weight = w
            
        weekly_data['water_intakes'].append(daily_data.get('water_total', 0))
        weekly_data['steps'].append(daily_data.get('steps', 0))
        weekly_data['calories'].append(daily_data.get('total_calories', 0))
        
        # [新增] 提取每日的三大营养素
        weekly_data['protein'].append(daily_data.get('total_protein', 0))
        weekly_data['fat'].append(daily_data.get('total_fat', 0))
        weekly_data['carb'].append(daily_data.get('total_carb', 0))
        
        if daily_data.get('symptom_keywords'):
            weekly_data['symptoms_count'] += len(daily_data['symptom_keywords'])
            
        # 计算当天的饮食得分
        if daily_data.get('meals'):
            ds = calculate_diet_score(daily_data, standards, scoring_standards)
            weekly_data['diet_scores'].append(ds)
            
    # 计算统计均值
    valid_weights = [w for w in weekly_data['weights'] if w]
    weekly_data['avg_weight'] = sum(valid_weights)/len(valid_weights) if valid_weights else 0
    weekly_data['weight_change'] = (last_weight - first_weight) if (last_weight and first_weight) else 0
    weekly_data['avg_calories'] = sum(weekly_data['calories'])/7
    
    # [新增] 计算周均营养素
    weekly_data['avg_protein'] = sum(weekly_data['protein'])/7
    weekly_data['avg_fat'] = sum(weekly_data['fat'])/7
    weekly_data['avg_carb'] = sum(weekly_data['carb'])/7
    
    weekly_data['avg_diet_score'] = sum(weekly_data['diet_scores'])/len(weekly_data['diet_scores']) if weekly_data['diet_scores'] else 0

    return weekly_data

def get_ai_weekly_insights(weekly_data, profile):
    """调用大模型生成复盘和计划"""
    prompt = f"""你是一位专业的健康复盘专家。请根据用户以下 7 天的聚合健康数据，生成一份周报点评和下周计划。
用户病理：{profile.get('condition', '胆结石')}
目标步数：{profile.get('step_target', 8000)}

【本周数据摘要】
- 平均体重变化：{weekly_data['weight_change']*2:.1f} 斤
- 日均摄入热量：{weekly_data['avg_calories']:.0f} kcal
- 日均饮水量：{sum(weekly_data['water_intakes'])/7:.0f} ml
- 日均步数：{sum(weekly_data['steps'])/7:.0f} 步
- 发生不适症状次数：{weekly_data['symptoms_count']} 次

请严格按以下两部分输出（直接输出文字，不要带前缀和 Markdown 代码块）：

---复盘部分---
（在此处写 150 字左右的深度复盘，指出做得好的趋势和存在的隐患）

---计划部分---
- （在此处用无序列表列出针对下周的 3 条核心干预动作）
"""
    try:
        res = subprocess.run(
            ['openclaw', 'agent', '--local', '--to', '+860000000000', '--message', prompt],
            capture_output=True, text=True, timeout=90,
            env={**os.environ, 'SYSTEM_PROMPT': '你是专业健康数据分析师。'}
        )
        if res.returncode == 0 and res.stdout.strip():
            output = res.stdout.strip()
            # 简单清洗并拆分为复盘和计划
            parts = output.split('---计划部分---')
            review = parts[0].replace('---复盘部分---', '').strip()
            plan = parts[1].strip() if len(parts) > 1 else "继续保持本周良好习惯。"
            return review, plan
    except Exception as e:
        print(f"AI 调用失败: {e}")
        
    return "本周数据收集完整，整体趋势平稳。", "- 保持每日饮水 2000ml\n- 增加餐后轻度活动\n- 严格控制脂肪摄入"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python3 weekly_report_pro.py <YYYY-MM-DD>")
        sys.exit(1)
        
    target_date = sys.argv[1]
    config = load_user_config()
    
    print(f"🔄 正在收集 {target_date} 所在周的数据...")
    week_dates = get_week_dates(target_date)
    weekly_data = aggregate_weekly_data(week_dates, config)
    
    print("🧠 正在生成 AI 深度复盘与下周计划...")
    ai_review, ai_plan = get_ai_weekly_insights(weekly_data, config.get('user_profile', {}))
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_filename = f"weekly_report_{timestamp}.pdf"
    output_path = os.path.join(REPORTS_DIR, pdf_filename)
    
    print("🎨 正在绘制趋势图表并装配 PDF...")
    generate_weekly_pdf_report(weekly_data, config.get('user_profile', {}), ai_review, ai_plan, output_path)
    
    print(f"\n🎉 搞定！请在 {output_path} 查看你的周报。")
    