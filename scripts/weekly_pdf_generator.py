#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Weekly PDF rendering for Health-Mate."""

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

from pdf_generator import register_chinese_font, get_font_prop, clean_html_tags
from i18n import condition_name, format_weight, format_weight_delta, resolve_locale, t, weight_unit

try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import matplotlib.patches as mpatches
    import matplotlib.patheffects as path_effects
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib is not installed, so weekly charts are disabled.")

C_PRIMARY = "#2563EB"
C_SUCCESS = "#10B981"
C_WARNING = "#F59E0B"
C_TEXT_MAIN = "#1E293B"
C_TEXT_MUTED = "#64748B"
C_BORDER = "#E2E8F0"
C_BG_HEAD = "#F8FAFC"

C_CARB, C_PROTEIN, C_FAT = "#3B82F6", "#10B981", "#F59E0B"

def create_weekly_rings_chart(diet_pct, water_pct, exercise_pct, locale):
    """Create the weekly multi-ring overview chart."""
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop()
        fig, ax = plt.subplots(figsize=(5, 4.5), subplot_kw=dict(polar=True))
        
        values = [min(1.0, v) for v in [exercise_pct, water_pct, diet_pct]]
        angles = [v * 2 * math.pi for v in values]
        
        ring_colors = [C_WARNING, C_SUCCESS, C_PRIMARY]
        y_positions = [0.8, 1.4, 2.0]  
        
        ax.barh(y_positions, [2 * math.pi]*3, color="#F1F5F9", height=0.4, zorder=0)
        ax.barh(y_positions, angles, color=ring_colors, height=0.4, zorder=1)
        
        ax.set_theta_zero_location('N') 
        ax.set_theta_direction(-1)      
        ax.axis('off')                  
        
        ax.text(0, 0, t(locale, 'weekly_rings_center'), ha='center', va='center', fontsize=12, color=C_TEXT_MAIN, fontweight='bold', fontproperties=my_font)

        if my_font:
            diet_patch = mpatches.Patch(color=C_PRIMARY, label=t(locale, 'weekly_ring_diet'))
            water_patch = mpatches.Patch(color=C_SUCCESS, label=t(locale, 'weekly_ring_water'))
            ex_patch = mpatches.Patch(color=C_WARNING, label=t(locale, 'weekly_ring_exercise'))
            ax.legend(handles=[diet_patch, water_patch, ex_patch], loc='lower right', bbox_to_anchor=(1.3, 0), prop=my_font, frameon=False)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: weekly ring chart generation failed: {e}")
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
        print(f"WARNING: trend line generation failed: {e}")
        return None

def create_bar_trend_chart(dates, values, target, color, title, ylabel):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop()
        fig, ax = plt.subplots(figsize=(8, 3))
        
        bars = ax.bar(dates, values, color=color, width=0.4, alpha=0.85, zorder=2)
        
        if target and target > 0:
            ax.axhline(y=target, color=C_WARNING, linestyle='--', alpha=0.8, linewidth=1.5, zorder=1)
            t_tgt = ax.text(len(dates)-0.5, target, f"{target}", color=C_WARNING, va='bottom', ha='right', fontsize=9)
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
        print(f"WARNING: bar chart generation failed: {e}")
        return None

# Weekly average nutrition donut chart.
def create_weekly_nutrition_chart(calories, protein, fat, carb, locale):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop()
        carb_kcal, protein_kcal, fat_kcal = carb * 4, protein * 4, fat * 9
        if carb_kcal + protein_kcal + fat_kcal <= 0: return None
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        wedges, texts, autotexts = ax.pie([carb_kcal, protein_kcal, fat_kcal], labels=[t(locale, 'carb'), t(locale, 'protein'), t(locale, 'fat')], colors=[C_CARB, C_PROTEIN, C_FAT], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'))
        
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
            
        t_center = ax.text(0, 0, t(locale, 'weekly_nutrition_center', calories=int(calories)), ha='center', va='center', fontsize=10, fontweight='bold', color=C_TEXT_MAIN)
        if my_font: t_center.set_fontproperties(my_font)
        
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: weekly nutrition chart generation failed: {e}")
        return None

def generate_weekly_pdf_report(weekly_data, profile, ai_review, ai_plan, output_path, locale="zh-CN"):
    locale = resolve_locale(locale=locale)
    font_name = register_chinese_font()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title=t(locale, 'weekly_report_title'))
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=HexColor(C_PRIMARY), spaceAfter=5, alignment=TA_CENTER, fontName=font_name)
    sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MUTED), spaceAfter=20, alignment=TA_CENTER, fontName=font_name)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=HexColor(C_PRIMARY), spaceBefore=20, spaceAfter=15, fontName=font_name)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MAIN), fontName=font_name, leading=18)
    
    story = []
    
    story.append(Paragraph(f"<b>{condition_name(locale, profile.get('condition', 'balanced'))} · {t(locale, 'weekly_report_title')}</b>", title_style))
    story.append(Paragraph(t(locale, 'weekly_period', start_date=weekly_data['start_date'], end_date=weekly_data['end_date'], name=profile.get('name', t(locale, 'default_name'))), sub_title))
    
    temp_images = []
    
    story.append(Paragraph(f"1. {t(locale, 'weekly_overview_title')}", heading_style))
    
    diet_pct = weekly_data['avg_diet_score'] / 100
    water_pct = sum([1 for w in weekly_data['water_intakes'] if w >= profile.get('water_target_ml', 2000)]) / 7.0
    exercise_pct = sum([1 for s in weekly_data['steps'] if s >= profile.get('step_target', 8000)]) / 7.0
    
    ring_chart = create_weekly_rings_chart(diet_pct, water_pct, exercise_pct, locale)
    if ring_chart:
        temp_images.append(ring_chart)
        img = Image(ring_chart, width=8*cm, height=7*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        
    summary_data = [
        [t(locale, 'dimension'), t(locale, 'value'), t(locale, 'health_status')],
        [t(locale, 'average_weight'), format_weight(locale, weekly_data['avg_weight']), t(locale, 'stable') if weekly_data['weight_change'] == 0 else (t(locale, 'down') if weekly_data['weight_change'] < 0 else t(locale, 'up'))],
        [t(locale, 'average_calories'), f"{weekly_data['avg_calories']:.0f} kcal", t(locale, 'normal')],
        [t(locale, 'average_water'), f"{sum(weekly_data['water_intakes'])/7:.0f} ml", t(locale, 'achieved') if sum(weekly_data['water_intakes'])/7 >= profile.get('water_target_ml', 2000) else t(locale, 'under_target')],
        [t(locale, 'average_steps'), f"{sum(weekly_data['steps'])/7:.0f}", t(locale, 'active') if sum(weekly_data['steps'])/7 >= 8000 else t(locale, 'low')]
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
    summary_table = Table(summary_data, colWidths=[4.5*cm, 5*cm, 4.5*cm])
    summary_table.setStyle(TableStyle(table_style))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph(f"2. {t(locale, 'weekly_trend_title')}", heading_style))
    
    short_dates = [d[5:] for d in weekly_data['dates']] 
    
    weight_values = [w * 2 if w else None for w in weekly_data['weights']] if locale == "zh-CN" else weekly_data['weights']
    weight_chart = create_trend_line_chart(short_dates, weight_values, t(locale, 'weight_trend_title', unit=weight_unit(locale)))
    if weight_chart:
        temp_images.append(weight_chart)
        img = Image(weight_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    bmr_val = (10*(profile.get('current_weight_kg', 65)) + 6.25*profile.get('height_cm',172) - 5*profile.get('age',34) + (5 if str(profile.get('gender', 'male')).lower() == 'male' else -161))
    tdee_val = int(bmr_val * profile.get('activity_level', 1.2))
    
    cal_chart = create_bar_trend_chart(short_dates, weekly_data['calories'], tdee_val, C_WARNING, t(locale, 'calorie_trend_title'), t(locale, 'calories'))
    if cal_chart:
        temp_images.append(cal_chart)
        img = Image(cal_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    nutri_chart = create_weekly_nutrition_chart(weekly_data['avg_calories'], weekly_data['avg_protein'], weekly_data['avg_fat'], weekly_data['avg_carb'], locale)
    if nutri_chart:
        temp_images.append(nutri_chart)
        img = Image(nutri_chart, width=10*cm, height=6*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    step_chart = create_bar_trend_chart(short_dates, weekly_data['steps'], profile.get('step_target', 8000), C_PRIMARY, t(locale, 'step_trend_title'), t(locale, 'average_steps'))
    if step_chart:
        temp_images.append(step_chart)
        img = Image(step_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    water_chart = create_bar_trend_chart(short_dates, weekly_data['water_intakes'], profile.get('water_target_ml', 2000), C_SUCCESS, t(locale, 'water_trend_title'), t(locale, 'average_water'))
    if water_chart:
        temp_images.append(water_chart)
        img = Image(water_chart, width=14*cm, height=5.25*cm)
        story.append(img)
        story.append(Spacer(1, 0.3*cm))
        
    story.append(Paragraph(f"3. {t(locale, 'weekly_ai_review_title')}", heading_style))
    for para in ai_review.split('\n'):
        if para.strip() and not para.startswith('['):
            story.append(Paragraph(clean_html_tags(para), normal_style))
            story.append(Spacer(1, 0.1*cm))
            
    story.append(Paragraph(f"4. {t(locale, 'weekly_next_plan_title')}", heading_style))
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
    print(f"Weekly PDF generated: {output_path}")
