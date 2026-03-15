#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 报告生成器（现代 SaaS 高颜值版 v1.1.9 - 图表字体与统一步长版）
- 优化：饮水图表堆叠数值移至柱体外部并采用黑色字体，彻底解决白色看不清的问题
- 优化：运动条形图强制采用统一长条，内部嵌入“公里/时长”，外部尾随“卡路里”
- 保留：全局原版排版、空行、注释及基础逻辑
"""

import os
import re
import urllib.request
import tempfile 
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

try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm  
    import matplotlib.patheffects as path_effects  
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ 未安装 matplotlib，图表功能将被禁用。")

C_PRIMARY_STR = "#2563EB"
C_SUCCESS_STR = "#10B981"
C_WARNING_STR = "#F59E0B"
C_DANGER_STR  = "#EF4444"
C_TEXT_MAIN_STR = "#1E293B"
C_TEXT_MUTED_STR= "#64748B"
C_BG_HEAD_STR = "#F8FAFC"
C_BORDER_STR  = "#E2E8F0"

C_PRIMARY_LIGHT_STR = "#60A5FA" 

C_PRIMARY = HexColor(C_PRIMARY_STR)
C_SUCCESS = HexColor(C_SUCCESS_STR)
C_WARNING = HexColor(C_WARNING_STR)
C_DANGER  = HexColor(C_DANGER_STR)
C_TEXT_MAIN = HexColor(C_TEXT_MAIN_STR)
C_TEXT_MUTED= HexColor(C_TEXT_MUTED_STR)
C_BG_HEAD = HexColor(C_BG_HEAD_STR)
C_BORDER  = HexColor(C_BORDER_STR)
C_CARB, C_PROTEIN, C_FAT = "#3B82F6", "#10B981", "#F59E0B"     

def clean_html_tags(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    for emoji in ['⭐', '✅', '⚠️', '❌', '🎉', '💡', '🚶', '🍎', '🥗', '💧', '🏃', '📊', '📈', '📄', '📥', '🥣', '🍜', '🍽️', '🍲', '⏰', '🚴', '🧘', '🔴', '🥦', '🍚', '🍳', '🥤', '🕐', '🌙', '💪', '🎯', '📌', '👍', '💯']: text = text.replace(emoji, '')
    return re.sub(r'\s+', ' ', re.sub(r'[\ufffd]', '', re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text))).strip()

def stars_to_text(stars_str):
    if not stars_str: return ""
    star_count = stars_str.count('⭐')
    return f'<font color="{C_WARNING_STR}">{"★" * star_count}</font>' + f'<font color="{C_BORDER_STR}">{"★" * (5 - star_count)}</font>'

def register_chinese_font():
    try: pdfmetrics.getFont('Chinese'); return 'Chinese'
    except: pass
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "..", "assets")
    local_ttf = os.path.normpath(os.path.join(assets_dir, "NotoSansSC-VF.ttf"))
    if not os.path.exists(local_ttf):
        try:
            if not os.path.exists(assets_dir): os.makedirs(assets_dir, exist_ok=True)
            with urllib.request.urlopen("https://raw.githubusercontent.com/tankeito/Health-Mate/main/assets/NotoSansSC-VF.ttf", timeout=120) as response:
                with open(local_ttf, 'wb') as f: f.write(response.read())
        except: return 'Helvetica'
    if os.path.exists(local_ttf):
        try: pdfmetrics.registerFont(TTFont('Chinese', local_ttf)); return 'Chinese'
        except: pass
    return 'Helvetica'

def get_font_prop():
    local_ttf = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "NotoSansSC-VF.ttf"))
    return fm.FontProperties(fname=local_ttf) if os.path.exists(local_ttf) else None

def create_nutrition_chart(nutrition):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        carb_kcal, protein_kcal, fat_kcal = nutrition.get('carb', 0)*4, nutrition.get('protein', 0)*4, nutrition.get('fat', 0)*9
        if carb_kcal + protein_kcal + fat_kcal <= 0: return None
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        wedges, texts, autotexts = ax.pie([carb_kcal, protein_kcal, fat_kcal], labels=['碳水化合物', '蛋白质', '脂肪'], colors=[C_CARB, C_PROTEIN, C_FAT], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'))
        for t in texts:
            t.set_color(C_TEXT_MUTED_STR)
            t.set_fontsize(9)
            if my_font: t.set_fontproperties(my_font)
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontsize(9)
            at.set_fontweight("bold")
            at.set_path_effects([path_effects.withStroke(linewidth=2, foreground=C_TEXT_MAIN_STR)])
            if my_font: at.set_fontproperties(my_font)
            
        t_center = ax.text(0, 0, f"{int(nutrition.get('calories', 0))}\nkcal", ha='center', va='center', fontsize=12, fontweight='bold', color=C_TEXT_MAIN_STR)
        if my_font: t_center.set_fontproperties(my_font)
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        return temp_img.name
    except: return None

def create_water_chart(water_records, target_ml):
    """饮水图表：修复堆叠文字显示问题，全部外挂为黑色字体，刻度更精细"""
    if not MATPLOTLIB_AVAILABLE or not water_records: return None
    try:
        my_font = get_font_prop()
        total_drank = sum([int(r.get('amount_ml', 0)) for r in water_records])
        target = target_ml if target_ml > 0 else 2000
        remaining = max(0, target - total_drank)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={'width_ratios': [1, 1.5]})
        
        # --- 左侧：完成率环形图 ---
        vibrant_colors = ["#4A90E2", "#50E3C2", "#F5A623", "#F8E71C", "#FF4081", "#00BCD4", "#9013FE"]
        if total_drank == 0: 
            ax1.pie([1], colors=[C_BORDER_STR], startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'))
        else: 
            amounts_circle = [int(r.get('amount_ml', 0)) for r in water_records]
            sizes = amounts_circle + ([remaining] if remaining > 0 else [])
            c_list = [vibrant_colors[i % len(vibrant_colors)] for i in range(len(amounts_circle))]
            if remaining > 0: c_list.append(C_BORDER_STR)
            ax1.pie(sizes, colors=c_list, startangle=90, wedgeprops=dict(width=0.3, edgecolor='w', linewidth=1.5))
            
        t_center = ax1.text(0, 0, f"{total_drank}\n/ {target}ml", ha='center', va='center', fontsize=11, fontweight='bold', color=C_TEXT_MAIN_STR)
        if my_font: t_center.set_fontproperties(my_font)
        
        # --- 右侧：24 小时堆叠柱状图 ---
        hours = [0, 3, 6, 9, 12, 15, 18, 21, 24]
        ax2.set_xticks(hours)
        ax2.set_xticklabels(['0', '3', '6', '9', '12', '15', '18', '21', '0'])
        ax2.set_xlim(-1, 25) 
        
        bins = {} 
        for r in water_records:
            exact = r.get('exact_time', '')
            if exact:
                try:
                    h, m = map(int, exact.split(':'))
                    pos = h + m/60.0
                except: pos = -1
            else:
                mapping = {'晨起': 7, '上午': 10, '中午': 12.5, '下午': 16, '晚上': 20}
                pos = mapping.get(r.get('time_label', ''), -1)
            
            if pos >= 0:
                bin_key = round(pos / 1.5) * 1.5
                if bin_key not in bins: bins[bin_key] = []
                bins[bin_key].append(int(r.get('amount_ml', 0)))
                
        max_y = 0
        for bin_pos, amounts in bins.items():
            current_bottom = 0
            colors_stack = [C_PRIMARY_STR, C_PRIMARY_LIGHT_STR]
            for i, amt in enumerate(amounts):
                color = colors_stack[i % 2]
                bars = ax2.bar(bin_pos, amt, bottom=current_bottom, color=color, width=1.2, alpha=0.9, edgecolor='w', linewidth=0.5)
                
                # [1.1.9 修复] 无论是否堆叠，数字全部显示在柱子外部并采用深色字体
                if len(amounts) == 1:
                    t_bar = ax2.text(bin_pos, current_bottom + amt + 15, f"{amt}", ha='center', va='bottom', fontsize=8, color=C_TEXT_MAIN_STR)
                else:
                    # 堆叠的层级向右偏移输出，避免重叠
                    t_bar = ax2.text(bin_pos + 0.8, current_bottom + amt/2, f"{amt}", ha='left', va='center', fontsize=8, color=C_TEXT_MAIN_STR)
                if my_font: t_bar.set_fontproperties(my_font)
                current_bottom += amt
            
            if len(amounts) > 1:
                t_total = ax2.text(bin_pos, current_bottom + 15, f"总{current_bottom}", ha='center', va='bottom', fontsize=8, color=C_TEXT_MAIN_STR, fontweight='bold')
                if my_font: t_total.set_fontproperties(my_font)
            
            max_y = max(max_y, current_bottom)
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(True)
        ax2.spines['left'].set_color(C_BORDER_STR)
        ax2.spines['bottom'].set_color(C_BORDER_STR)
        
        ax2.set_yticks(range(100, 2200, 200))
        ax2.tick_params(axis='y', labelleft=True, colors=C_TEXT_MUTED_STR, labelsize=8)
        ax2.tick_params(axis='x', colors=C_TEXT_MUTED_STR)
        ax2.yaxis.grid(True, linestyle='--', alpha=0.4, color=C_BORDER_STR)
        ax2.set_ylim(0, 2200)
        
        if my_font:
            for label in ax2.get_xticklabels(): label.set_fontproperties(my_font)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 饮水图表生成失败：{e}")
        return None

def create_exercise_chart(exercise_data, steps, step_target=8000):
    """[1.1.9 修复] 运动条形图全部长度统一。内部写详情，尾端写热量，高度自适应。"""
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        labels, calories, targets, is_step, inner_texts = [], [], [], [], []
        
        if exercise_data:
            for e in exercise_data:
                ex_type = e.get('type', '运动')
                dist = e.get('distance_km', 0)
                dur = e.get('duration_min', 0)
                
                # 1. Y 轴仅保留“骑行”等类型名
                labels.append(ex_type)
                
                # 2. 准备条形图内部文字 "4.54km (22min)"
                in_str = []
                if dist > 0: in_str.append(f"{dist}km")
                if dur > 0: in_str.append(f"({dur}min)")
                inner_texts.append(" ".join(in_str))
                
                calories.append(e.get('calories', 0))
                targets.append(None) 
                is_step.append(False)
                
        if steps > 0:
            labels.append(f"今日步数")
            calories.append(steps)
            targets.append(step_target) 
            is_step.append(True)
            inner_texts.append("")
            
        if not labels or sum(calories) == 0: return None
            
        fig_height = max(1.2, len(labels) * 0.6 + 0.5)
        fig, ax = plt.subplots(figsize=(7, fig_height))
        
        y_pos = range(len(labels))
        
        chart_color = "#20D091" 
        track_color = "#F1F5F9"
        step_color = "#3B82F6" 
        
        # 定义全局长条长度（以步数目标或默认值 100 为基准）
        max_bg = max(step_target, steps) if steps > 0 else 100
        
        for i, (label, cal, tgt, is_s, in_txt) in enumerate(zip(labels, calories, targets, is_step, inner_texts)):
            if is_s:
                # 步数采用双轨进度条
                ax.plot([0, max_bg], [i, i], color=track_color, linewidth=12, solid_capstyle='round', zorder=1)
                ax.plot([0, cal], [i, i], color=step_color, linewidth=12, solid_capstyle='round', zorder=2)
                text_str = f"{int(cal)} / {int(tgt)} 步"
                t_val = ax.text(max_bg * 1.05, i, text_str, ha='left', va='center', fontsize=9, color=C_TEXT_MUTED_STR, zorder=3)
            else:
                # [核心修复] 所有运动长条填满全局长度
                ax.plot([0, max_bg], [i, i], color=chart_color, linewidth=12, solid_capstyle='round', zorder=1)
                # 内部嵌入公里/时长（白字粗体）
                if in_txt:
                    t_in = ax.text(max_bg * 0.02, i, in_txt, ha='left', va='center', fontsize=9, color='white', fontweight='bold', zorder=3)
                    if my_font: t_in.set_fontproperties(my_font)
                # 外部尾随热量（灰字）
                text_str = f"{int(cal)} kcal"
                t_val = ax.text(max_bg * 1.05, i, text_str, ha='left', va='center', fontsize=9, color=C_TEXT_MUTED_STR, zorder=3)

            if my_font: t_val.set_fontproperties(my_font)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()  
        ax.set_ylim(len(labels) - 0.5, -0.5)
        
        # 扩大 xlim 保证外部文字不被切除
        ax.set_xlim(0, max_bg * 1.35)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', colors=C_TEXT_MAIN_STR, length=0, pad=10) 
        ax.tick_params(axis='x', bottom=False, labelbottom=False) 
        
        if my_font:
            for label in ax.get_yticklabels(): label.set_fontproperties(my_font)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 运动图表生成失败：{e}")
        return None

def generate_pdf_report(data, profile, scores, nutrition, macros, risks, plan, output_path, water_records=None, meals=None, exercise_data=None, ai_comment=None):
    font_name = register_chinese_font()
    footer_text = f"{profile.get('condition', '健康')}专属健康管理 - Health-Mate"
    
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=C_PRIMARY, spaceAfter=10, alignment=TA_CENTER, fontName=font_name)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=13, textColor=C_PRIMARY, spaceBefore=15, spaceAfter=10, fontName=font_name)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=C_TEXT_MAIN, fontName=font_name, leading=15)
    cell_style_center = ParagraphStyle('CellCenter', parent=normal_style, alignment=TA_CENTER, leading=12)
    
    base_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), C_BG_HEAD), ('TEXTCOLOR', (0, 0), (-1, 0), C_TEXT_MUTED),
        ('TEXTCOLOR', (0, 1), (-1, -1), C_TEXT_MAIN), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")), 
    ]

    story = []
    
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
    
    if ai_comment:
        story.append(Paragraph("专家 AI 点评", heading_style))
        clean_comment = '\n'.join([l for l in ai_comment.split('\n') if not l.strip().startswith(('[plugins]', '[adp-', 'Hint:', 'error:'))]).strip()
        for para in re.split(r'(?<=[.!。!])\s+', clean_comment)[:5]:  
            if para.strip(): story.append(Paragraph(f"<font color='#1E293B'>{clean_html_tags(para)}</font>", normal_style))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("二、基础健康数据", heading_style))
    bmi_val = scores["weight"].get("bmi", 0) or 0
    weight_val = data.get("weight_morning")
    bmr_val = (10*(weight_val or 65) + 6.25*profile.get('height_cm',172) - 5*profile.get('age',34) + (5 if profile.get('gender')=='男' else -161))
    tdee_val = bmr_val * profile.get('activity_level', 1.2)
    
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
    
    temp_images = []

    story.append(Paragraph("三、当日营养摄入核算", heading_style))
    chart_path_nutrition = create_nutrition_chart(nutrition)
    if chart_path_nutrition:
        temp_images.append(chart_path_nutrition)
        img = Image(chart_path_nutrition, width=10*cm, height=6*cm)
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
    
    story.append(Paragraph("四、饮水详情", heading_style))
    if water_records and len(water_records) > 0:
        chart_path_water = create_water_chart(water_records, data.get('water_target', 2000))
        if chart_path_water:
            temp_images.append(chart_path_water)
            img_water = Image(chart_path_water, width=14*cm, height=5.25*cm)
            img_water.hAlign = 'CENTER'
            story.append(img_water)
            story.append(Spacer(1, 0.4*cm))
    else:
        story.append(Paragraph("<font color='#64748B'>今日无饮水记录</font>", normal_style))
        story.append(Spacer(1, 0.4*cm))
    
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
            
            meal_time_str = f" <font color='#64748B' size='9'>({meal_time})</font>" if meal_time else ""
            meal_title_text = f"<font color='{C_PRIMARY_STR}'>■</font> <b>{meal_type}</b>{meal_time_str} <font color='#64748B' size='9'>· 合计 {meal.get('total_calories', 0):.0f} kcal</font>"
            meal_title = Paragraph(meal_title_text, ParagraphStyle('MealTitle', parent=normal_style, spaceBefore=8, spaceAfter=4))
            meal_elements.append(meal_title)
            
            food_nutrition = meal.get("food_nutrition", [])
            if food_nutrition and len(food_nutrition) > 0:
                meal_data = [["食物名称", "份量", "热量", "蛋白质", "脂肪", "碳水"]]
                for food in food_nutrition:
                    name_raw = food.get("name", "").split('→')[0].strip() if '→' in food.get("name", "") else food.get("name", "").strip()
                    portion_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|g|个 | 碗 | 份 | 杯 | 片)', name_raw)
                    if portion_match:
                        name_simple = re.sub(r'\s*' + re.escape(portion_match.group(0)), '', name_raw).strip()
                        portion_display = f"{float(portion_match.group(1)):.0f}{portion_match.group(2)}"
                    else:
                        name_simple = name_raw
                        portion_display = f"{food.get('portion_grams', 100):.0f}g"
                    
                    name_simple = re.sub(r'\s*（约\d+g）$|\s*（约）$|\s*约$', '', name_simple).strip()
                    if len(name_simple) < 2: name_simple = name_raw
                    meal_data.append([clean_html_tags(name_simple), portion_display, f"{food.get('calories', 0):.0f}kcal", f"{food.get('protein', 0):.1f}g", f"{food.get('fat', 0):.1f}g", f"{food.get('carb', 0):.1f}g"])
                
                modern_meal_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), C_BG_HEAD), ('TEXTCOLOR', (0, 0), (-1, 0), C_TEXT_MUTED),  
                    ('TEXTCOLOR', (0, 1), (-1, -1), C_TEXT_MAIN), ('ALIGN', (0, 0), (0, -1), 'LEFT'),                   
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name), ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, C_BORDER), 
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
    
    story.append(Paragraph("六、运动详情", heading_style))
    steps = data.get("steps", 0)
    step_target = profile.get("step_target", 8000)
    if exercise_data or steps > 0:
        chart_path_exercise = create_exercise_chart(exercise_data, steps, step_target)
        if chart_path_exercise:
            temp_images.append(chart_path_exercise)
            img_ex = Image(chart_path_exercise, width=12*cm, height=4.2*cm)
            img_ex.hAlign = 'LEFT'
            story.append(img_ex)
            story.append(Spacer(1, 0.2*cm))
            
    else:
        story.append(Paragraph("<font color='#64748B'>今日无运动记录</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("七、风险预警", heading_style))
    if risks:
        for risk in risks:
            story.append(Paragraph(f"<font color='{C_DANGER_STR}'><b>{clean_html_tags(risk.get('level', '')).strip()} {clean_html_tags(risk.get('item', ''))}</b></font>", normal_style))
            story.append(Paragraph(f"<font color='#64748B'>风险：</font>{clean_html_tags(risk.get('risk', ''))}", normal_style))
            story.append(Paragraph(f"<font color='#64748B'>建议：</font>{clean_html_tags(risk.get('action', ''))}", normal_style))
            story.append(Spacer(1, 0.2*cm))
    else:
        story.append(Paragraph(f"<font color='{C_SUCCESS_STR}'>今日无明显风险，继续保持健康生活方式！</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("八、次日可执行方案", heading_style))
    for category, title in [("diet", "饮食计划"), ("water", "饮水计划"), ("exercise", "运动建议")]:
        if plan.get(category):
            story.append(Paragraph(f"<b>{title}</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
            for item in plan.get(category, []):
                if isinstance(item, dict):
                    time = item.get('time', item.get('period', item.get('time_range', '')))
                    content = item.get('menu', item.get('activity', item.get('amount', '')))
                    note = item.get('note', item.get('details', ''))
                    
                    if not content: content = '、'.join(str(i) for i in item.get('items', []))[:30]
                    
                    cal = item.get('calories', '')
                    if cal: note = f"{cal}kcal " + note
                    
                    clean_item = f"<b>{time}</b> {clean_html_tags(content)}"
                    if note: clean_item += f" <font color='#64748B'>({clean_html_tags(note)})</font>"
                else: 
                    clean_item = clean_html_tags(str(item))
                story.append(Paragraph(f"<font color='{C_PRIMARY_STR}'>■</font> {clean_item}", normal_style))
            story.append(Spacer(1, 0.2*cm))
            
    if plan.get("notes"):
        story.append(Paragraph("<b>特别关注</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("notes", []):
            story.append(Paragraph(f"<font color='{C_WARNING_STR}'>■</font> {clean_html_tags(item)}", normal_style))
    
    story.append(Spacer(1, 1.5*cm))
    footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    story.append(Paragraph(f"{footer_text}", footer_style))
    
    doc.build(story)
    for temp_img in temp_images:
        try: os.remove(temp_img)
        except: pass
    print(f"✅ 高颜值全图表 PDF 报告已生成：{output_path}")

if __name__ == "__main__":
    print("PDF 生成器模块，请通过 health_report_pro.py 调用")
