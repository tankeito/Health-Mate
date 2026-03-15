#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 报告生成器（现代 SaaS 高颜值版 v1.1.9 - 全局扁平化 UI 统一版）
- 引入 HexColor 现代网页级配色（蓝/绿/橙/红）
- 新增：Matplotlib 生成中文化营养环形图，带深色描边解决文字泛白问题
- 优化：全局表格统一采用 SaaS 级扁平化无边框列表布局（移除所有生硬网格）
- 保留：KeepTogether 防止表格跨页断裂
"""

import os
import re
import urllib.request
import tempfile  # 用于生成临时图表文件
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==================== 可视化库初始化 ====================
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm  # 用于加载外部中文字体
    import matplotlib.patheffects as path_effects  # 用于为文字添加描边
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ 未安装 matplotlib，营养环形图功能将被禁用。")

# ==================== 现代 UI 配色板 ====================
C_PRIMARY = HexColor("#2563EB")   # 科技蓝 (主标题/重要标识)
C_SUCCESS = HexColor("#10B981")   # 达标绿 (正常/优秀)
C_WARNING = HexColor("#F59E0B")   # 警告橙 (关注/待改进)
C_DANGER  = HexColor("#EF4444")   # 危险红 (超标/有症状)
C_TEXT_MAIN = HexColor("#1E293B") # 主文本色 (深灰)
C_TEXT_MUTED= HexColor("#64748B") # 辅助文本色 (浅灰)
C_BG_HEAD = HexColor("#F8FAFC")   # 表头背景色(极浅灰)
C_BORDER  = HexColor("#E2E8F0")   # 表格边框色

# 营养素专属配色（用于图表）
C_CARB = "#3B82F6"    # 碳水 - 蓝
C_PROTEIN = "#10B981" # 蛋白 - 绿
C_FAT = "#F59E0B"     # 脂肪 - 橙


def clean_html_tags(text):
    """移除 HTML 标签及复杂字符"""
    if not text: return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    emojis_to_remove = ['⭐', '✅', '⚠️', '❌', '🎉', '💡', '🚶', '🍎', '🥗', '💧', '🏃', '📊', '📈', '📄', '📥', '🥣', '🍜', '🍽️', '🍲', '⏰', '🚴', '🧘', '🔴', '🥦', '🍚', '🍳', '🥤', '🕐', '🌙', '💪', '🎯', '📌', '👍', '💯']
    for emoji in emojis_to_remove: text = text.replace(emoji, '')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  
    text = re.sub(r'[\ufffd]', '', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()

def stars_to_text(stars_str):
    """利用富文本实现美观的彩色星级"""
    if not stars_str: return ""
    star_count = stars_str.count('⭐')
    active = f'<font color="#F59E0B">{"★" * star_count}</font>'
    inactive = f'<font color="#E2E8F0">{"★" * (5 - star_count)}</font>'
    return active + inactive

def register_chinese_font():
    """注册 ReportLab 中文字体（带自动下载机制）"""
    try:
        pdfmetrics.getFont('Chinese')
        return 'Chinese'
    except:
        pass
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "..", "assets")
    local_ttf = os.path.join(assets_dir, "NotoSansSC-VF.ttf")
    local_ttf = os.path.normpath(local_ttf)
    
    if not os.path.exists(local_ttf):
        print("⚠️ 未检测到中文字体文件，正在尝试自动下载...")
        try:
            if not os.path.exists(assets_dir): os.makedirs(assets_dir, exist_ok=True)
            font_url = "https://raw.githubusercontent.com/tankeito/Health-Mate/main/assets/NotoSansSC-VF.ttf"
            with urllib.request.urlopen(font_url, timeout=120) as response:
                with open(local_ttf, 'wb') as out_file:
                    out_file.write(response.read())
            print("✅ 字体自动下载成功！")
        except Exception as e:
            print(f"❌ 字体下载失败：{e}")
            return 'Helvetica'
            
    if os.path.exists(local_ttf):
        try:
            pdfmetrics.registerFont(TTFont('Chinese', local_ttf))
            return 'Chinese'
        except Exception as e:
            print(f"⚠️ 字体加载失败：{e}")
    
    return 'Helvetica'

def create_nutrition_chart(nutrition):
    """
    生成每日三大营养素占比环形图
    - 支持中文图例
    - 增加文字描边提高可读性
    """
    if not MATPLOTLIB_AVAILABLE: return None
        
    try:
        # 获取本地字体路径供 matplotlib 使用
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_ttf = os.path.normpath(os.path.join(script_dir, "..", "assets", "NotoSansSC-VF.ttf"))
        # 如果存在字体，则创建一个字体属性对象
        my_font = fm.FontProperties(fname=local_ttf) if os.path.exists(local_ttf) else None

        # 将克数转换为热量(kcal)，以体现真实的能量占比
        carb_kcal = nutrition.get('carb', 0) * 4
        protein_kcal = nutrition.get('protein', 0) * 4
        fat_kcal = nutrition.get('fat', 0) * 9
        total_kcal = carb_kcal + protein_kcal + fat_kcal
        
        if total_kcal <= 0: return None
            
        # 中文标签
        labels = ['碳水化合物', '蛋白质', '脂肪']
        sizes = [carb_kcal, protein_kcal, fat_kcal]
        colors = [C_CARB, C_PROTEIN, C_FAT]
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        
        # 绘制环形图 (wedgeprops 设置环的宽度和白色描边间隔)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90, 
                                          wedgeprops=dict(width=0.4, edgecolor='w'))
        
        # 调整图例文字样式（外部文本）
        for text in texts:
            text.set_color("#64748B") # 浅灰色
            text.set_fontsize(9)
            if my_font: text.set_fontproperties(my_font) # 应用中文字体
            
        # 调整百分比文字样式（内部文本）
        for autotext in autotexts:
            autotext.set_color("#FFFFFF") # 白色字体
            autotext.set_fontsize(9)
            autotext.set_fontweight("bold")
            # 核心修复：为白色文字添加深蓝色描边，确保在黄色脂肪切片上也清晰可见
            autotext.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#1E293B')])
            if my_font: autotext.set_fontproperties(my_font)
        
        # 中心总热量文本
        total_cal_int = int(nutrition.get('calories', 0))
        t_center = ax.text(0, 0, f"{total_cal_int}\nkcal", ha='center', va='center', 
                           fontsize=12, fontweight='bold', color="#1E293B")
        if my_font: t_center.set_fontproperties(my_font)
        
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 图表生成失败：{e}")
        return None

def generate_pdf_report(data, profile, scores, nutrition, macros, risks, plan, output_path, water_records=None, meals=None, exercise_data=None, ai_comment=None):
    """生成高颜值 PDF 报告，整合图表与无边框 SaaS 级排版"""
    font_name = register_chinese_font()
    
    condition = profile.get('condition', '健康')
    footer_text = f"{condition}专属健康管理 - Health-Mate"
    
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=C_PRIMARY, spaceAfter=10, alignment=TA_CENTER, fontName=font_name)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=13, textColor=C_PRIMARY, spaceBefore=15, spaceAfter=10, fontName=font_name)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=C_TEXT_MAIN, fontName=font_name, leading=15)
    cell_style_center = ParagraphStyle('CellCenter', parent=normal_style, alignment=TA_CENTER, leading=12)
    
    # ==================== 核心重构：全局基础表格样式扁平化 ====================
    base_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), C_BG_HEAD),          # 表头极浅灰背景
        ('TEXTCOLOR', (0, 0), (-1, 0), C_TEXT_MUTED),        # 表头文字颜色变淡 (SaaS风格)
        ('TEXTCOLOR', (0, 1), (-1, -1), C_TEXT_MAIN),        # 正文文字保持深灰
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),               # 全局居中对齐
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),                   # 统一字号
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        # 取消全封闭网格线，仅保留底部的浅色分隔线
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")), 
    ]

    story = []
    
    # 一、综合评分等头部区块
    story.append(Paragraph("<b>胆结石健康日报</b>", title_style))
    story.append(Paragraph(f"<font color='#64748B'>{data['date']} | 监测人：{profile.get('name', '默认用户')}</font>", ParagraphStyle('Date', parent=normal_style, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("一、今日综合评分", heading_style))
    score_data = [
        ["维度", "得分", "星级", "状态"],
        ["饮食合规性", f"{scores['diet']['raw']:.0f}/100", Paragraph(stars_to_text(scores['diet']['stars']), cell_style_center), "达标" if scores['diet']['raw']>=80 else "待改进"],
        ["饮水完成度", f"{scores['water']['raw']:.0f}/100", Paragraph(stars_to_text(scores['water']['stars']), cell_style_center), "达标" if scores['water']['raw']>=100 else "未达标"],
        ["体重管理", f"{scores['weight']['raw']:.0f}/100", Paragraph(stars_to_text(scores['weight']['stars']), cell_style_center), "正常" if scores['weight'].get('bmi') and 18.5<=scores['weight']['bmi']<24 else "关注"],
        ["症状管理", f"{scores['symptom']['raw']:.0f}/100", Paragraph(stars_to_text(scores['symptom']['stars']), cell_style_center), "无症状" if not scores['symptom']['has_symptoms'] else "有症状"],
        ["运动管理", f"{scores['exercise']['raw']:.0f}/100", Paragraph(stars_to_text(scores['exercise']['stars']), cell_style_center), "达标" if scores['exercise']['raw']>=60 else "待加强"],
        ["健康依从性", f"{scores['adherence']['raw']:.0f}/100", Paragraph(stars_to_text(scores['adherence']['stars']), cell_style_center), "优秀" if scores['adherence']['raw']>=80 else "一般"],
        ["总分", f"{scores['total']:.0f}/100", Paragraph(stars_to_text(scores['total_stars']), cell_style_center), "优秀" if scores['total']>=80 else "良好" if scores['total']>=60 else "待改进"],
    ]
    
    score_table = Table(score_data, colWidths=[4*cm, 3*cm, 3.5*cm, 3.5*cm])
    score_style = list(base_table_style)
    for i in range(1, len(score_data)):
        status = score_data[i][3]
        if status in ["达标", "优秀", "正常", "无症状"]: score_style.append(('TEXTCOLOR', (3, i), (3, i), C_SUCCESS))
        elif status in ["待改进", "未达标", "关注", "有症状", "待加强", "一般"]: score_style.append(('TEXTCOLOR', (3, i), (3, i), C_WARNING if status in ["关注", "待加强", "一般", "待改进"] else C_DANGER))
    
    score_table.setStyle(TableStyle(score_style))
    story.append(score_table)
    story.append(Spacer(1, 0.4*cm))
    
    # AI 点评
    if ai_comment:
        story.append(Paragraph("专家 AI 点评", heading_style))
        clean_comment = ai_comment
        for prefix in ['[plugins]', '[adp-', 'Hint:', 'error:']:
            clean_comment = '\n'.join([l for l in clean_comment.split('\n') if not l.strip().startswith(prefix)])
        
        paragraphs = re.split(r'(?<=[.!。!])\s+', clean_comment.strip())
        for para in paragraphs[:5]:  
            if para.strip(): story.append(Paragraph(f"<font color='#1E293B'>{clean_html_tags(para)}</font>", normal_style))
        story.append(Spacer(1, 0.3*cm))
    
    # 二、基础健康数据
    story.append(Paragraph("二、基础健康数据", heading_style))
    from health_report_pro import calculate_bmr, calculate_tdee
    bmi_val = scores["weight"].get("bmi", 0) or 0
    weight_val = data.get("weight_morning")
    bmr_val = calculate_bmr(weight_val if weight_val else 65, profile["height_cm"], profile["age"], profile["gender"])
    tdee_val = calculate_tdee(bmr_val, profile["activity_level"])
    
    health_data = [
        ["指标", "数值", "参考范围"],
        ["身高", f"{profile['height_cm']}cm", "-"],
        ["体重", f"{weight_val*2:.1f}斤" if weight_val else "未记录", f"目标：{profile.get('target_weight_kg', 64)*2:.1f} 斤"],
        ["BMI", f"{bmi_val:.1f}", "18.5-24（正常）"],
        ["基础代谢", f"{bmr_val:.0f} kcal", "-"],
        ["每日消耗", f"{tdee_val:.0f} kcal", "-"],
        ["推荐热量", f"{tdee_val:.0f} kcal/天", "胆结石安全范围"],
        ["蛋白质", f"{macros.get('protein_g', 0)}g/天", f"{macros.get('protein_p', 0)}%总热量"],
        ["脂肪", f"{macros.get('fat_g', 0)}g/天", f"{macros.get('fat_p', 0)}%（低脂）"],
        ["碳水", f"{macros.get('carb_g', 0)}g/天", f"{macros.get('carb_p', 0)}%总热量"],
        ["膳食纤维", f">={macros.get('fiber_min_g', 25)}g/天", "促进胆汁排泄"],
    ]
    
    health_table = Table(health_data, colWidths=[5*cm, 4*cm, 5*cm])
    health_style = list(base_table_style)
    if 18.5 <= bmi_val < 24: health_style.append(('TEXTCOLOR', (1, 3), (1, 3), C_SUCCESS))
    elif bmi_val > 0: health_style.append(('TEXTCOLOR', (1, 3), (1, 3), C_DANGER if bmi_val >= 28 or bmi_val < 18.5 else C_WARNING))
    health_table.setStyle(TableStyle(health_style))
    story.append(health_table)
    story.append(Spacer(1, 0.4*cm))
    
    # 三、当日营养摄入 (带环形图)
    story.append(Paragraph("三、当日营养摄入核算", heading_style))
    
    chart_path = create_nutrition_chart(nutrition)
    if chart_path:
        img = Image(chart_path, width=10*cm, height=6*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.2*cm))
    
    nutrition_data = [
        ["营养素", "实际摄入", "推荐量"],
        ["总热量", f"{nutrition['calories']:.0f} kcal", f"{tdee_val:.0f} kcal"],
        ["蛋白质", f"{nutrition['protein']:.1f}g", f"{macros.get('protein_g', 0)}g"],
        ["脂肪", f"{nutrition['fat']:.1f}g", f"{macros.get('fat_g', 0)}g"],
        ["碳水", f"{nutrition['carb']:.1f}g", f"{macros.get('carb_g', 0)}g"],
        ["膳食纤维", f"{nutrition['fiber']:.1f}g", f">={macros.get('fiber_min_g', 25)}g"],
    ]
    nutri_table = Table(nutrition_data, colWidths=[5*cm, 4*cm, 5*cm])
    nutri_table.setStyle(TableStyle(base_table_style))
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
        water_table.setStyle(TableStyle(base_table_style))
        story.append(water_table)
    else:
        story.append(Paragraph("<font color='#64748B'>今日无饮水记录</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 五、进食详情
    story.append(Paragraph("五、进食详情", heading_style))
    if meals and len(meals) > 0:
        seen_meals = set()
        for meal in meals:
            meal_elements = [] 
            meal_type = meal.get("type", "")
            meal_time = meal.get("time", "")
            meal_key = f"{meal_type}_{meal_time}"
            
            if meal_key in seen_meals: continue
            seen_meals.add(meal_key)
            
            food_nutrition = meal.get("food_nutrition", [])
            total_calories = meal.get("total_calories", 0)
            
            meal_title_text = f"<font color='{C_PRIMARY}'>■</font> <b>{meal_type}</b> <font color='#64748B' size='9'>({meal_time}) · 合计 {total_calories:.0f} kcal</font>"
            meal_title = Paragraph(meal_title_text, ParagraphStyle('MealTitle', parent=normal_style, spaceBefore=8, spaceAfter=4))
            meal_elements.append(meal_title)
            
            if food_nutrition and len(food_nutrition) > 0:
                meal_data = [["食物名称", "份量", "热量", "蛋白质", "脂肪", "碳水"]]
                for food in food_nutrition:
                    name = food.get("name", "")
                    name_raw = name.split('→')[0].strip() if '→' in name else name.strip()
                    
                    portion_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|个 | 碗 | 份 | 杯 | 片)', name_raw)
                    if portion_match:
                        portion_value = float(portion_match.group(1))
                        portion_unit = portion_match.group(2)
                        name_simple = re.sub(r'\s*' + re.escape(portion_match.group(0)), '', name_raw).strip()
                        portion_display = f"{portion_value:.0f}{portion_unit}"
                    else:
                        name_simple = name_raw
                        portion_display = f"{food.get('portion_grams', 100):.0f}g"
                    
                    name_simple = re.sub(r'\s*（约\d+g）$|\s*（约）$|\s*约$', '', name_simple).strip()
                    if len(name_simple) < 2: name_simple = name_raw
                    
                    meal_data.append([
                        clean_html_tags(name_simple), 
                        portion_display, 
                        f"{food.get('calories', 0):.0f}kcal", 
                        f"{food.get('protein', 0):.1f}g", 
                        f"{food.get('fat', 0):.1f}g", 
                        f"{food.get('carb', 0):.1f}g"
                    ])
                
                # 进食明细保留居左样式，底线采用与全局一致的配置
                modern_meal_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#F8FAFC")), 
                    ('TEXTCOLOR', (0, 0), (-1, 0), C_TEXT_MUTED),  
                    ('TEXTCOLOR', (0, 1), (-1, -1), C_TEXT_MAIN),         
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),                   
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),                
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")), 
                ]
                meal_table = Table(meal_data, colWidths=[4.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
                meal_table.setStyle(TableStyle(modern_meal_style))
                meal_elements.append(meal_table)
            else:
                meal_elements.append(Paragraph("<font color='#64748B'>无详细食物记录</font>", normal_style))
            
            meal_elements.append(Spacer(1, 0.4*cm))
            story.append(KeepTogether(meal_elements))
    else:
        story.append(Paragraph("<font color='#64748B'>今日无进食记录</font>", normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 六、运动详情
    story.append(Paragraph("六、运动详情", heading_style))
    if exercise_data:
        cycling_list = exercise_data.get("cycling", []) if isinstance(exercise_data, dict) else [e for e in exercise_data if e.get("type") == "骑行"]
        walking = exercise_data.get("walking", {}) if isinstance(exercise_data, dict) else {}
        steps = walking.get("steps", 0)
        
        total_cycling_km = sum(c.get("distance_km", 0) for c in cycling_list)
        total_cycling_min = sum(c.get("duration_min", 0) for c in cycling_list)
        
        exercise_table_data = [["项目", "详情"]]
        if cycling_list:
            cycling_details = [f"{c.get('distance_km', 0)}km/{c.get('duration_min', 0)}分钟" for c in cycling_list]
            exercise_table_data.append(["骑行", "；".join(cycling_details) + f"\n（合计 {total_cycling_km}km / {total_cycling_min:.0f}分钟）"])
        if steps > 0: exercise_table_data.append(["步数", f"{steps}步"])
            
        exercise_raw = scores.get("exercise", {}).get("raw", 0)
        exercise_status = "达标" if exercise_raw >= 60 else "待加强"
        exercise_table_data.append(["运动评分", f"{exercise_raw:.0f}/100"])
        exercise_table_data.append(["状态", Paragraph(f"<font color='#10B981'><b>达标</b></font>" if exercise_status == "达标" else f"<font color='#F59E0B'><b>待加强</b></font>", cell_style_center)])
        
        exercise_table = Table(exercise_table_data, colWidths=[5*cm, 9*cm])
        exercise_table.setStyle(TableStyle(base_table_style))
        story.append(exercise_table)
    else:
        story.append(Paragraph("<font color='#64748B'>今日无运动记录</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 七、风险预警
    story.append(Paragraph("七、风险预警", heading_style))
    if risks:
        for risk in risks:
            level = clean_html_tags(risk.get('level', '')).strip()
            item_text = clean_html_tags(risk.get('item', ''))
            story.append(Paragraph(f"<font color='#EF4444'><b>{level} {item_text}</b></font>", normal_style))
            story.append(Paragraph(f"<font color='#64748B'>风险：</font>{clean_html_tags(risk.get('risk', ''))}", normal_style))
            story.append(Paragraph(f"<font color='#64748B'>建议：</font>{clean_html_tags(risk.get('action', ''))}", normal_style))
            story.append(Spacer(1, 0.2*cm))
    else:
        story.append(Paragraph("<font color='#10B981'>今日无明显风险，继续保持健康生活方式！</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    # 八、次日方案
    story.append(Paragraph("八、次日可执行方案", heading_style))
    
    if plan.get("diet"):
        story.append(Paragraph("<b>饮食计划</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("diet", []):
            if isinstance(item, dict):
                meal = item.get('meal', item.get('meal_name', ''))
                time = item.get('time', item.get('time_range', item.get('period', '')))
                menu = item.get('menu', '')
                if not menu:
                    items = item.get('items', [])
                    if items:
                        menu = '、'.join(str(i) for i in items[:3])  
                        if len(items) > 3: menu += ' 等'
                if not menu:
                    menu = item.get('dishes', item.get('menu_detail', item.get('food', item.get('content', ''))))
                calories = item.get('calories', item.get('kcal', ''))
                fat = item.get('fat', item.get('fat_g', ''))
                fiber = item.get('fiber', item.get('fiber_g', ''))
                if menu:
                    nutrition_info = f"({calories}kcal"
                    if fat: nutrition_info += f", 脂肪{fat}g"
                    if fiber: nutrition_info += f", 纤维{fiber}g"
                    nutrition_info += ")"
                    clean_item = f"{time} {clean_html_tags(menu)} {nutrition_info}"
                elif meal and time: clean_item = f"{meal} ({time})"
                else: clean_item = f"{meal} {time}"
            else: clean_item = clean_html_tags(str(item))
            story.append(Paragraph(f"<font color='#2563EB'>■</font> {clean_item}", normal_style))
        story.append(Spacer(1, 0.2*cm))
        
    if plan.get("water"):
        story.append(Paragraph("<b>饮水计划</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("water", []):
            if isinstance(item, dict):
                time = item.get('time', item.get('period', ''))
                amount = item.get('amount', item.get('amount_ml', item.get('volume', '')))
                if amount and not any(unit in str(amount) for unit in ['ml', 'L']): amount = f"{amount}ml"
                note = item.get('note', item.get('tip', item.get('remark', item.get('description', ''))))
                clean_item = f"⏰ {time} {clean_html_tags(str(amount))} ({clean_html_tags(note)})"
            else: clean_item = clean_html_tags(str(item))
            story.append(Paragraph(f"<font color='#2563EB'>■</font> {clean_item}", normal_style))
        story.append(Spacer(1, 0.2*cm))

    if plan.get("exercise"):
        story.append(Paragraph("<b>运动建议</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("exercise", []):
            if isinstance(item, dict):
                time = item.get('time', item.get('time_range', item.get('period', '')))
                activity = item.get('activity', item.get('type', item.get('name', '')))
                duration = item.get('duration', item.get('duration_min', item.get('time_length', '')))
                details = item.get('details', item.get('description', item.get('desc', item.get('content', ''))))
                if activity and duration and details: clean_item = f"{time} {clean_html_tags(activity)} ({clean_html_tags(duration)}): {clean_html_tags(details)}"
                elif activity and duration: clean_item = f"{time} {clean_html_tags(activity)} ({clean_html_tags(duration)})"
                elif activity: clean_item = f"{time} {clean_html_tags(activity)}"
                else: clean_item = f"{time}"
            else: clean_item = clean_html_tags(str(item))
            story.append(Paragraph(f"<font color='#2563EB'>■</font> {clean_item}", normal_style))
            
    if plan.get("notes"):
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("<b>特别关注</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("notes", []):
            story.append(Paragraph(f"<font color='#F59E0B'>■</font> {clean_html_tags(item)}", normal_style))
    
    # 页脚
    story.append(Spacer(1, 1.5*cm))
    footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    story.append(Paragraph(f"{condition}专属健康管理 - Health-Mate", footer_style))
    
    # 构建 PDF
    doc.build(story)
    
    # 清理临时图表
    if chart_path and os.path.exists(chart_path):
        try: os.remove(chart_path)
        except: pass
            
    print(f"✅ 高颜值 PDF 报告已生成：{output_path}")

if __name__ == "__main__":
    print("PDF 生成器模块，请通过 health_report_pro.py 调用")
    