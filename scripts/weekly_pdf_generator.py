#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报 PDF 渲染引擎 (weekly_pdf_generator.py) 
- 修复：为三环概览图添加图例，明确各颜色代表的含义
- 修复：为生成的 PDF 注入 Title 元数据，解决浏览器标签页显示 (anonymous) 的问题
- 追加：每日摄入热量柱状趋势图、日均三大营养成分环形图
"""

import os
import math
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# 导入复用的字体配置
from pdf_generator import register_chinese_font, get_font_prop, clean_html_tags

try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import matplotlib.patches as mpatches # [1.1.21 修复] 引入 patches 用于自定义图例
    import matplotlib.patheffects as path_effects # [新增] 引入用于营养图表中心数字的描边特效
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ 未安装 matplotlib，图表功能将被禁用。")

C_PRIMARY = "#2563EB"
C_SUCCESS = "#10B981"
C_WARNING = "#F59E0B"
C_TEXT_MAIN = "#1E293B"
C_TEXT_MUTED = "#64748B"
C_BORDER = "#E2E8F0"
C_BG_HEAD = "#F8FAFC"

# [新增] 营养成分专属颜色
C_CARB, C_PROTEIN, C_FAT = "#3B82F6", "#10B981", "#F59E0B"

def create_weekly_rings_chart(diet_pct, water_pct, exercise_pct):
    """复刻智能手表的三环概览图，带图例"""
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        fig, ax = plt.subplots(figsize=(5, 4.5), subplot_kw=dict(polar=True)) # 稍微加宽一点留给图例
        
        values = [min(1.0, v) for v in [exercise_pct, water_pct, diet_pct]]
        angles = [v * 2 * math.pi for v in values]
        
        # 内、中、外的颜色 (橙-运动, 绿-饮水, 蓝-饮食)
        ring_colors = [C_WARNING, C_SUCCESS, C_PRIMARY]
        y_positions = [0.8, 1.4, 2.0]  
        
        ax.barh(y_positions, [2 * math.pi]*3, color="#F1F5F9", height=0.4, zorder=0)
        ax.barh(y_positions, angles, color=ring_colors, height=0.4, zorder=1)
        
        ax.set_theta_zero_location('N') 
        ax.set_theta_direction(-1)      
        ax.axis('off')                  
        
        ax.text(0, 0, "本周\n健康概览", ha='center', va='center', fontsize=12, color=C_TEXT_MAIN, fontweight='bold', fontproperties=my_font)
        
        # [1.1.21 修复] 添加自定义图例
        if my_font:
            diet_patch = mpatches.Patch(color=C_PRIMARY, label='饮食达标')
            water_patch = mpatches.Patch(color=C_SUCCESS, label='饮水达标')
            ex_patch = mpatches.Patch(color=C_WARNING, label='运动达标')
            # 将图例放在图表右下角区域外侧
            ax.legend(handles=[diet_patch, water_patch, ex_patch], loc='lower right', bbox_to_anchor=(1.3, 0), prop=my_font, frameon=False)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 三环图生成失败：{e}")
        return None

def create_trend_line_chart(dates, values, title):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        fig, ax = plt.subplots(figsize=(8, 3))
        
        valid_data = [(d, v) for d, v in zip(dates, values) if v is not None and v > 0]
        if not valid_data: return None
        v_dates, v_vals = zip(*valid_data)
        
        ax.plot(v_dates, v_vals, color=C_SUCCESS, marker='o', markersize=6, linewidth=2, zorder=3)
        
        min_val = min(v_vals) - 1
        max_val = max(v_vals) + 1
        ax.fill_between(v_dates, v_vals, min_val, color=C_SUCCESS, alpha=0.15, zorder=2)
        
        ax.set_ylim(min_val, max_val)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(C_BORDER)
        ax.spines['bottom'].set_color(C_BORDER)
        ax.tick_params(axis='x', colors=C_TEXT_MUTED)
        ax.tick_params(axis='y', colors=C_TEXT_MUTED)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=C_BORDER, zorder=1)
        
        for d, v in valid_data:
            t = ax.text(d, v + (max_val - min_val)*0.05, f"{v:.1f}", ha='center', va='bottom', fontsize=9, color=C_TEXT_MAIN, fontweight='bold')
            if my_font: t.set_fontproperties(my_font)
            
        if my_font:
            for label in ax.get_xticklabels(): label.set_fontproperties(my_font)
            ax.set_title(title, fontproperties=my_font, color=C_TEXT_MAIN, loc='left', pad=15, fontweight='bold')
            
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 折线图生成失败：{e}")
        return None

def create_bar_trend_chart(dates, values, target, color, title, ylabel):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        fig, ax = plt.subplots(figsize=(8, 3))
        
        bars = ax.bar(dates, values, color=color, width=0.4, alpha=0.85, zorder=2)
        
        if target and target > 0:
            ax.axhline(y=target, color=C_WARNING, linestyle='--', alpha=0.8, linewidth=1.5, zorder=1)
            t_tgt = ax.text(len(dates)-0.5, target, f"目标: {target}", color=C_WARNING, va='bottom', ha='right', fontsize=9)
            if my_font: t_tgt.set_fontproperties(my_font)
            
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(C_BORDER)
        ax.tick_params(axis='y', colors=C_TEXT_MUTED)
        ax.tick_params(axis='x', colors=C_TEXT_MUTED)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=C_BORDER, zorder=0)
        
        max_val = max(values + [target if target else 0])
        ax.set_ylim(0, max_val * 1.2)
        
        if my_font:
            for label in ax.get_xticklabels(): label.set_fontproperties(my_font)
            ax.set_title(title, fontproperties=my_font, color=C_TEXT_MAIN, loc='left', pad=15, fontweight='bold')

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 柱状图生成失败：{e}")
        return None

# [新增] 专门用于周报的日均营养成分环形图
def create_weekly_nutrition_chart(calories, protein, fat, carb):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        carb_kcal, protein_kcal, fat_kcal = carb * 4, protein * 4, fat * 9
        if carb_kcal + protein_kcal + fat_kcal <= 0: return None
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        wedges, texts, autotexts = ax.pie([carb_kcal, protein_kcal, fat_kcal], labels=['碳水化合物', '蛋白质', '脂肪'], colors=[C_CARB, C_PROTEIN, C_FAT], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'))
        
        for t in texts:
            t.set_color(C_TEXT_MUTED)
            t.set_fontsize(9)
            if my_font: t.set_fontproperties(my_font)
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontsize(9)
            at.set_fontweight("bold")
            at.set_path_effects([path_effects.withStroke(linewidth=2, foreground=C_TEXT_MAIN)])
            if my_font: at.set_fontproperties(my_font)
            
        t_center = ax.text(0, 0, f"日均摄入\n{int(calories)} kcal", ha='center', va='center', fontsize=10, fontweight='bold', color=C_TEXT_MAIN)
        if my_font: t_center.set_fontproperties(my_font)
        
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"⚠️ 营养环形图生成失败：{e}")
        return None

def generate_weekly_pdf_report(weekly_data, profile, ai_review, ai_plan, output_path):
    font_name = register_chinese_font()
    
    # [1.1.21 修复] 在此处添加 title 属性，解决浏览器预览显示 anonymous 的问题
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title="健康周报")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=HexColor(C_PRIMARY), spaceAfter=5, alignment=TA_CENTER, fontName=font_name)
    sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MUTED), spaceAfter=20, alignment=TA_CENTER, fontName=font_name)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=HexColor(C_PRIMARY), spaceBefore=20, spaceAfter=15, fontName=font_name)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MAIN), fontName=font_name, leading=18)
    
    story = []
    
    date_range = f"{weekly_data['start_date']} 至 {weekly_data['end_date']}"
    story.append(Paragraph("<b>胆结石健康周报 (Weekly Report)</b>", title_style))
    story.append(Paragraph(f"评估周期：{date_range} | 监测人：{profile.get('name', '东东')}", sub_title))
    
    temp_images = []
    
    story.append(Paragraph("一、本周健康指标概览", heading_style))
    
    diet_pct = weekly_data['avg_diet_score'] / 100
    water_pct = sum([1 for w in weekly_data['water_intakes'] if w >= profile.get('water_target', 2000)]) / 7.0
    exercise_pct = sum([1 for s in weekly_data['steps'] if s >= profile.get('step_target', 8000)]) / 7.0
    
    ring_chart = create_weekly_rings_chart(diet_pct, water_pct, exercise_pct)
    if ring_chart:
        temp_images.append(ring_chart)
        # 因为加了图例，图表稍微变宽了一点，所以宽度这里从 7cm 调整为 8cm 保证不被拉伸变形
        img = Image(ring_chart, width=8*cm, height=7*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        
    summary_data = [
        ["维度", "本周平均/累计", "健康状态"],
        ["平均体重", f"{weekly_data['avg_weight']*2:.1f}斤", "稳定" if weekly_data['weight_change'] == 0 else ("下降" if weekly_data['weight_change'] < 0 else "上升")],
        ["日均摄入", f"{weekly_data['avg_calories']:.0f} kcal", "正常"],
        ["日均饮水", f"{sum(weekly_data['water_intakes'])/7:.0f} ml", "达标" if sum(weekly_data['water_intakes'])/7 >= 2000 else "未达标"],
        ["日均步数", f"{sum(weekly_data['steps'])/7:.0f} 步", "活跃" if sum(weekly_data['steps'])/7 >= 8000 else "偏低"]
    ]
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor(C_BG_HEAD)),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor(C_TEXT_MUTED)),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor(C_TEXT_MAIN)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor(C_BORDER)),
    ]
    t = Table(summary_data, colWidths=[4.5*cm, 5*cm, 4.5*cm])
    t.setStyle(TableStyle(table_style))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("二、核心趋势分析", heading_style))
    
    short_dates = [d[5:] for d in weekly_data['dates']] 
    
    weight_chart = create_trend_line_chart(short_dates, [w*2 if w else None for w in weekly_data['weights']], "本周体重波动趋势 (斤)")
    if weight_chart:
        temp_images.append(weight_chart)
        img = Image(weight_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    # [新增] 饮食热量柱状图
    bmr_val = (10*(profile.get('current_weight_kg', 65)) + 6.25*profile.get('height_cm',172) - 5*profile.get('age',34) + (5 if profile.get('gender')=='男' else -161))
    tdee_val = int(bmr_val * profile.get('activity_level', 1.2))
    
    cal_chart = create_bar_trend_chart(short_dates, weekly_data['calories'], tdee_val, C_WARNING, "本周每日摄入热量 (kcal)", "热量")
    if cal_chart:
        temp_images.append(cal_chart)
        img = Image(cal_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    # [新增] 营养成分环形图 (日均)
    nutri_chart = create_weekly_nutrition_chart(weekly_data['avg_calories'], weekly_data['avg_protein'], weekly_data['avg_fat'], weekly_data['avg_carb'])
    if nutri_chart:
        temp_images.append(nutri_chart)
        img = Image(nutri_chart, width=10*cm, height=6*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    step_chart = create_bar_trend_chart(short_dates, weekly_data['steps'], profile.get('step_target', 8000), C_PRIMARY, "本周每日步数分布 (步)", "步数")
    if step_chart:
        temp_images.append(step_chart)
        img = Image(step_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    water_chart = create_bar_trend_chart(short_dates, weekly_data['water_intakes'], 2000, C_SUCCESS, "本周每日饮水量分布 (ml)", "饮水量")
    if water_chart:
        temp_images.append(water_chart)
        img = Image(water_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    story.append(Paragraph("三、专家 AI 深度复盘", heading_style))
    for para in ai_review.split('\n'):
        if para.strip() and not para.startswith('['):
            story.append(Paragraph(clean_html_tags(para), normal_style))
            story.append(Spacer(1, 0.1*cm))
            
    story.append(Paragraph("四、下周干预方案", heading_style))
    for para in ai_plan.split('\n'):
        if para.strip() and not para.startswith('['):
            if para.startswith('-') or para.startswith('*') or para.startswith('1.'):
                story.append(Paragraph(f"<font color='{C_PRIMARY}'>■</font> {clean_html_tags(para[1:].strip())}", normal_style))
            else:
                story.append(Paragraph(f"<b>{clean_html_tags(para)}</b>", normal_style))
            story.append(Spacer(1, 0.1*cm))

    doc.build(story)
    for img in temp_images:
        try: os.remove(img)
        except: pass
    print(f"✅ 专属健康周报已生成：{output_path}")