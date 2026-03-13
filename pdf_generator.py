#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 报告生成器（最终修复版 v2）
- 星级改为文字（三星、四星等）
- 表头和关键指标加粗显示
- 文字颜色加深（纯黑色）
- 无 HTML 标签，无特殊符号
"""

import os
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def clean_html_tags(text):
    """移除所有 HTML 标签和特殊符号"""
    if not text:
        return ""
    text = str(text)
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除特殊符号（星级、表情等）
    text = text.replace('⭐', '')
    text = text.replace('✅', '')
    text = text.replace('⚠️', '')
    text = text.replace('❌', '')
    text = text.replace('🎉', '')
    text = text.replace('💡', '')
    text = text.replace('🚶', '')
    text = text.replace('🍎', '')
    text = text.replace('🥗', '')
    text = text.replace('💧', '')
    text = text.replace('🏃', '')
    text = text.replace('📊', '')
    text = text.replace('📈', '')
    text = text.replace('📄', '')
    text = text.replace('📥', '')
    return text.strip()

def stars_to_text(stars_str):
    """将星级符号转换为★符号"""
    if not stars_str:
        return ""
    star_count = stars_str.count('⭐')
    return "★" * star_count

def register_chinese_font():
    """注册中文字体"""
    try:
        pdfmetrics.getFont('Chinese')
        return 'Chinese'
    except:
        pass
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_ttf = os.path.join(script_dir, "NotoSansSC-VF.ttf")
    
    if os.path.exists(local_ttf):
        try:
            pdfmetrics.registerFont(TTFont('Chinese', local_ttf))
            return 'Chinese'
        except Exception as e:
            print(f"⚠️ 字体加载失败：{e}")
    
    return 'Helvetica'

def generate_pdf_report(data, profile, scores, nutrition, macros, risks, plan, output_path, water_records=None, meals=None, exercise_data=None):
    """生成 PDF 报告"""
    font_name = register_chinese_font()
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # 自定义样式 - 使用纯黑色，加深对比度
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=font_name,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.black,
        spaceAfter=12,
        fontName=font_name,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName=font_name,
        leading=13,
    )
    
    story = []
    
    # 标题
    story.append(Paragraph("胆结石健康日报", title_style))
    story.append(Paragraph(data['date'], ParagraphStyle('Date', parent=normal_style, alignment=TA_CENTER, fontSize=11)))
    story.append(Spacer(1, 0.4*cm))
    
    # 一、综合评分
    story.append(Paragraph("一、今日综合评分", heading_style))
    
    score_data = [
        ["维度", "得分", "星级", "状态"],
        ["饮食合规性", f"{scores['diet']['raw']:.0f}/100", stars_to_text(scores["diet"]["stars"]), "达标" if scores["diet"]["raw"]>=80 else "待改进"],
        ["饮水完成度", f"{scores['water']['raw']:.0f}/100", stars_to_text(scores["water"]["stars"]), "达标" if scores["water"]["raw"]>=100 else "未达标"],
        ["体重管理", f"{scores['weight']['raw']:.0f}/100", stars_to_text(scores["weight"]["stars"]), "正常" if scores["weight"].get("bmi") and 18.5<=scores["weight"]["bmi"]<24 else "关注"],
        ["症状管理", f"{scores['symptom']['raw']:.0f}/100", stars_to_text(scores["symptom"]["stars"]), "无症状" if not scores["symptom"]["has_symptoms"] else "有症状"],
        ["运动管理", f"{scores['exercise']['raw']:.0f}/100", stars_to_text(scores["exercise"]["stars"]), "达标" if scores["exercise"]["raw"]>=60 else "待加强"],
        ["健康依从性", f"{scores['adherence']['raw']:.0f}/100", stars_to_text(scores["adherence"]["stars"]), "优秀" if scores["adherence"]["raw"]>=80 else "一般"],
        ["总分", f"{scores['total']:.0f}/100", stars_to_text(scores["total_stars"]), "优秀" if scores["total"]>=80 else "良好" if scores["total"]>=60 else "待改进"],
    ]
    
    score_table = Table(score_data, colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
    score_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),  # 表头稍大
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 加粗边框
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ]
    # 所有行使用白色背景
    for i in range(len(score_data)-1):
        score_style.append(('BACKGROUND', (0, i+1), (-1, i+1), colors.white))
        # 状态列根据状态上色
        status = score_data[i+1][3] if len(score_data[i+1]) > 3 else ""
        if status in ["达标", "优秀", "正常", "无症状"]:
            score_style.append(('TEXTCOLOR', (3, i+1), (3, i+1), colors.green))
        elif status in ["待改进", "未达标", "关注", "有症状", "待加强"]:
            score_style.append(('TEXTCOLOR', (3, i+1), (3, i+1), colors.orange))
    score_table.setStyle(TableStyle(score_style))
    story.append(score_table)
    story.append(Spacer(1, 0.4*cm))
    
    # 二、基础健康数据
    story.append(Paragraph("二、基础健康数据", heading_style))
    
    from health_report_pro import calculate_bmr, calculate_tdee
    bmi_val = scores["weight"].get("bmi", 0) or 0
    bmr_val = calculate_bmr(data["weight_morning"], profile["height_cm"], profile["age"], profile["gender"])
    tdee_val = calculate_tdee(bmr_val, profile["activity_level"])
    
    health_data = [
        ["指标", "数值", "参考范围"],
        ["身高", f"{profile['height_cm']}cm", "-"],
        ["体重", f"{data['weight_morning']*2:.1f}斤", f"目标：128 斤"],
        ["BMI", f"{bmi_val:.1f}", "18.5-24（正常）"],
        ["基础代谢", f"{bmr_val:.0f} kcal", "-"],
        ["每日消耗", f"{tdee_val:.0f} kcal", "-"],
        ["推荐热量", f"{tdee_val:.0f} kcal/天", "胆结石安全范围"],
        ["蛋白质", f"{macros['protein_g']}g/天", f"{macros['protein_percent']}%总热量"],
        ["脂肪", f"{macros['fat_g']}g/天", f"{macros['fat_percent']}%（低脂）"],
        ["碳水", f"{macros['carb_g']}g/天", f"{macros['carb_percent']}%总热量"],
        ["膳食纤维", f">={macros['fiber_min_g']}g/天", "促进胆汁排泄"],
    ]
    
    health_table = Table(health_data, colWidths=[5*cm, 4*cm, 5*cm])
    health_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ]
    # 所有行使用白色背景 + BMI 数值颜色标注
    for i in range(len(health_data)-1):
        health_style.append(('BACKGROUND', (0, i+1), (-1, i+1), colors.white))
        # BMI 数值颜色标注
        if health_data[i+1][0] == "BMI":
            if 18.5 <= bmi_val < 24:
                health_style.append(('TEXTCOLOR', (1, i+1), (1, i+1), colors.green))
            elif bmi_val < 18.5 or bmi_val >= 28:
                health_style.append(('TEXTCOLOR', (1, i+1), (1, i+1), colors.red))
            else:
                health_style.append(('TEXTCOLOR', (1, i+1), (1, i+1), colors.orange))
    health_table.setStyle(TableStyle(health_style))
    story.append(health_table)
    story.append(Spacer(1, 0.4*cm))
    
    # 三、当日营养摄入
    story.append(Paragraph("三、当日营养摄入核算", heading_style))
    
    nutrition_data = [
        ["营养素", "实际摄入", "推荐量"],
        ["总热量", f"{nutrition['total']['calories']:.0f} kcal", f"{tdee_val:.0f} kcal"],
        ["蛋白质", f"{nutrition['total']['protein']:.1f}g", f"{macros['protein_g']}g"],
        ["脂肪", f"{nutrition['total']['fat']:.1f}g", f"{macros['fat_g']}g"],
        ["碳水", f"{nutrition['total']['carb']:.1f}g", f"{macros['carb_g']}g"],
        ["膳食纤维", f"{nutrition['total']['fiber']:.1f}g", f">={macros['fiber_min_g']}g"],
    ]
    
    nutri_table = Table(nutrition_data, colWidths=[5*cm, 4*cm, 5*cm])
    nutri_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]
    nutri_table.setStyle(TableStyle(nutri_style))
    story.append(nutri_table)
    story.append(Spacer(1, 0.4*cm))
    
    # 四、饮水详情
    story.append(Paragraph("四、饮水详情", heading_style))
    if water_records and len(water_records) > 0:
        water_data = [["时间", "饮水量", "累计进度"]]
        for record in water_records:
            time_str = record.get("time", "")
            amount = record.get("amount_ml", 0)
            cumulative = record.get("cumulative_ml", 0)
            progress = f"{cumulative}/2000ml ({cumulative//20}%)"
            water_data.append([time_str, f"{amount}ml", progress])
        
        water_table = Table(water_data, colWidths=[4*cm, 3*cm, 7*cm])
        water_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]
        water_table.setStyle(TableStyle(water_style))
        story.append(water_table)
    else:
        story.append(Paragraph("今日无饮水记录", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 五、进食详情
    story.append(Paragraph("五、进食详情", heading_style))
    if meals and len(meals) > 0:
        seen_meals = set()  # 去重：记录已处理的餐次
        for meal in meals:
            meal_type = meal.get("type", "")
            meal_time = meal.get("time", "")
            meal_key = f"{meal_type}_{meal_time}"
            
            # 去重：如果已处理过这个餐次，跳过
            if meal_key in seen_meals:
                continue
            seen_meals.add(meal_key)
            
            food_nutrition = meal.get("food_nutrition", [])
            total_calories = meal.get("total_calories", 0)
            
            story.append(Paragraph(f"{meal_type}（{meal_time}）- 总计{total_calories:.0f}kcal", ParagraphStyle('MealTitle', parent=normal_style, fontSize=11, textColor=colors.black)))
            
            if food_nutrition and len(food_nutrition) > 0:
                meal_data = [["食物", "份量", "热量", "蛋白质", "脂肪", "碳水"]]
                for food in food_nutrition:
                    name = food.get("name", "")
                    # 简化食物名称：
                    # 1. 去掉"→"及之后的所有内容（卡路里和备注）
                    name_simple = name.split('→')[0].strip() if '→' in name else name
                    # 2. 去掉括号内的备注（如"250g"、"约 150g"等）
                    name_simple = re.sub(r'.*?）', '', name_simple)
                    name_simple = re.sub(r'\(.*?\)', '', name_simple)
                    # 3. 去掉末尾的份量标注（如"250g"、"100ml"）
                    name_simple = re.sub(r'\s*\d+g$', '', name_simple)
                    name_simple = re.sub(r'\s*\d+ml$', '', name_simple)
                    # 4. 去掉常见数量词
                    name_simple = re.sub(r'^\d+\s*个\s*', '', name_simple)
                    name_simple = re.sub(r'^\d+\s*碗\s*', '', name_simple)
                    name_simple = re.sub(r'^\d+\s*份\s*', '', name_simple)
                    name_simple = name_simple.strip()
                    
                    portion = food.get("portion_grams", 0)
                    calories = food.get("calories", 0)
                    protein = food.get("protein", 0)
                    fat = food.get("fat", 0)
                    carb = food.get("carb", 0)
                    meal_data.append([
                        clean_html_tags(name_simple),
                        f"{portion:.0f}g" if portion > 0 else "-",
                        f"{calories:.0f}kcal",
                        f"{protein:.1f}g",
                        f"{fat:.1f}g",
                        f"{carb:.1f}g"
                    ])
                
                meal_table = Table(meal_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
                meal_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.8, 0.8, 0.8)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ]
                meal_table.setStyle(TableStyle(meal_style))
                story.append(meal_table)
            else:
                story.append(Paragraph("无详细食物记录", normal_style))
            story.append(Spacer(1, 0.2*cm))
    else:
        story.append(Paragraph("今日无进食记录", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 六、运动详情
    story.append(Paragraph("六、运动详情", heading_style))
    if exercise_data:
        # 从 exercise_data 中提取骑行和步数
        cycling_list = exercise_data.get("cycling", [])
        walking = exercise_data.get("walking", {})
        steps = walking.get("steps", 0)
        
        # 计算骑行总计
        total_cycling_km = sum(c.get("distance_km", 0) for c in cycling_list)
        total_cycling_min = sum(c.get("duration_min", 0) for c in cycling_list)
        
        # 构建运动详情表格
        exercise_table_data = [
            ["项目", "详情"],
        ]
        
        # 骑行数据
        if cycling_list:
            cycling_details = []
            for c in cycling_list:
                cycling_details.append(f"{c.get('distance_km', 0)}km/{c.get('duration_min', 0)}分钟")
            exercise_table_data.append(["骑行", "；".join(cycling_details) + f"\n（合计{total_cycling_km}km/{total_cycling_min:.0f}分钟）"])
        
        # 步数数据
        if steps > 0:
            exercise_table_data.append(["步数", f"{steps}步"])
        
        # 运动评分（从 scores 中获取）
        exercise_raw = scores.get("exercise", {}).get("raw", 0)
        exercise_status = "达标" if exercise_raw >= 60 else "待加强"
        exercise_table_data.append(["运动评分", f"{exercise_raw:.0f}/100"])
        exercise_table_data.append(["状态", exercise_status])
        
        exercise_table = Table(exercise_table_data, colWidths=[5*cm, 9*cm])
        exercise_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ]
        # 状态列颜色标注
        if exercise_status == "达标":
            exercise_style.append(('TEXTCOLOR', (1, -1), (1, -1), colors.green))
        else:
            exercise_style.append(('TEXTCOLOR', (1, -1), (1, -1), colors.orange))
        
        exercise_table.setStyle(TableStyle(exercise_style))
        story.append(exercise_table)
    else:
        story.append(Paragraph("今日无运动记录", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 七、风险预警
    story.append(Paragraph("六、风险预警", heading_style))
    if risks:
        for risk in risks:
            # 清理风险等级前的图标和文字
            level = clean_html_tags(risk['level']).strip()
            risk_text = f"{level} {risk['item']}"
            story.append(Paragraph(risk_text, ParagraphStyle('Risk', parent=normal_style, fontSize=10, textColor=colors.black)))
            story.append(Paragraph(f"风险：{clean_html_tags(risk['risk'])}", normal_style))
            story.append(Paragraph(f"建议：{clean_html_tags(risk['action'])}", normal_style))
            story.append(Spacer(1, 0.2*cm))
    else:
        story.append(Paragraph("今日无明显风险，继续保持健康生活方式！", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 八、次日方案
    story.append(Paragraph("七、次日可执行方案", heading_style))
    
    # 居家方案
    story.append(Paragraph("居家简易版", heading_style))
    for item in plan.get("diet", []):
        clean_item = clean_html_tags(item)
        # 删除餐次前面的图标
        clean_item = re.sub(r'^[\s]*[🥣🍜🥗🍎]\s*', '', clean_item)
        story.append(Paragraph(f"- {clean_item}", normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 外出就餐
    if plan.get("dining_out"):
        story.append(Paragraph("外出就餐推荐", heading_style))
        for item in plan["dining_out"]:
            clean_item = clean_html_tags(item)
            # 删除图标
            clean_item = re.sub(r'^[\s]*[🍜🍽️🍲]\s*', '', clean_item)
            story.append(Paragraph(f"- {clean_item}", normal_style))
        story.append(Spacer(1, 0.2*cm))
    
    # 饮水计划
    story.append(Paragraph("饮水计划", heading_style))
    for item in plan.get("water", []):
        clean_item = clean_html_tags(item)
        # 删除时间前面的图标
        clean_item = re.sub(r'^[\s]*[⏰📊]\s*', '', clean_item)
        story.append(Paragraph(f"- {clean_item}", normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 运动建议
    story.append(Paragraph("运动建议", heading_style))
    for item in plan.get("exercise", []):
        clean_item = clean_html_tags(item)
        # 删除图标
        clean_item = re.sub(r'^[\s]*[🚶🚴🧘💡]\s*', '', clean_item)
        story.append(Paragraph(f"- {clean_item}", normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 特别关注
    if plan.get("notes"):
        story.append(Paragraph("特别关注", heading_style))
        for item in plan["notes"]:
            clean_item = clean_html_tags(item)
            # 删除图标
            clean_item = re.sub(r'^[\s]*[✅🍎⚠️]\s*', '', clean_item)
            story.append(Paragraph(f"- {clean_item}", normal_style))
    
    # 页脚
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=colors.black, alignment=TA_CENTER)
    story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    story.append(Paragraph("胆结石专属健康管理 - 西西小帮手", footer_style))
    
    # 构建 PDF
    doc.build(story)
    print(f"✅ PDF 报告已生成：{output_path}")

if __name__ == "__main__":
    print("PDF 生成器模块，请通过 health_report_pro.py 调用")
