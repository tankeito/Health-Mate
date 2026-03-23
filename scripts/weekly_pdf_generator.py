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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader

from daily_pdf_generator import register_chinese_font, get_font_prop, clean_html_tags
from i18n import condition_name, format_weight, format_weight_delta, inline_localize, resolve_locale, t, weight_unit
from monthly_pdf_generator import create_macro_radar_chart, create_symptom_heatmap

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


def localize(locale, zh_text, en_text):
    return inline_localize(locale, zh_text, en_text)


def profile_condition_title(profile, locale):
    display = str((profile or {}).get("condition_display", "") or "").strip()
    if display:
        return display
    conditions = (profile or {}).get("conditions", [])
    if isinstance(conditions, list) and conditions:
        labels = [condition_name(locale, item) for item in conditions if item]
        labels = [item for item in labels if item]
        if labels:
            separator = "、" if resolve_locale(locale=locale) in {"zh-CN", "ja-JP"} else ", "
            return separator.join(labels)
    return condition_name(locale, (profile or {}).get("condition", "balanced"))


def _style_matplotlib_text(text_obj, font_prop=None, *, color=None, fontsize=None, fontweight="bold"):
    resolved_color = color if color is not None else text_obj.get_color()
    if color is not None:
        text_obj.set_color(color)
    if fontsize is not None:
        text_obj.set_fontsize(fontsize)
    if font_prop:
        text_obj.set_fontproperties(font_prop)
    if fontweight:
        text_obj.set_fontweight(fontweight)
    outline_color = C_TEXT_MAIN if str(resolved_color).lower() in {"#ffffff", "white"} else "white"
    text_obj.set_path_effects([path_effects.withStroke(linewidth=1.0, foreground=outline_color, alpha=0.65)])


def _apply_axis_tick_style(ax, font_prop=None, *, x_color=C_TEXT_MAIN, y_color=C_TEXT_MAIN, fontsize=8):
    for label in ax.get_xticklabels():
        _style_matplotlib_text(label, font_prop, color=x_color, fontsize=fontsize)
    for label in ax.get_yticklabels():
        _style_matplotlib_text(label, font_prop, color=y_color, fontsize=fontsize)


def _style_legend(legend, font_prop=None, fontsize=8):
    if not legend:
        return
    for text in legend.get_texts():
        _style_matplotlib_text(text, font_prop, fontsize=fontsize)


def _build_chart_image(path: str, max_width_cm: float, max_height_cm: float, h_align: str = "CENTER") -> Image:
    width_limit = max_width_cm * cm
    height_limit = max_height_cm * cm
    try:
        width_px, height_px = ImageReader(path).getSize()
        scale = min(width_limit / max(width_px, 1), height_limit / max(height_px, 1))
        width = width_px * scale
        height = height_px * scale
    except Exception:
        width = width_limit
        height = height_limit
    chart = Image(path, width=width, height=height)
    chart.hAlign = h_align
    return chart

def create_weekly_rings_chart(diet_pct, water_pct, exercise_pct, locale):
    """Create the weekly multi-ring overview chart."""
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop(locale)
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
        
        center = ax.text(0, 0, t(locale, 'weekly_rings_center'), ha='center', va='center', fontsize=12, color=C_TEXT_MAIN, fontweight='bold', fontproperties=my_font)
        _style_matplotlib_text(center, my_font, color=C_TEXT_MAIN, fontsize=12)

        diet_label = t(locale, 'weekly_ring_label', label=t(locale, 'weekly_ring_diet'), percent=diet_pct * 100)
        water_label = t(locale, 'weekly_ring_label', label=t(locale, 'weekly_ring_water'), percent=water_pct * 100)
        exercise_label = t(locale, 'weekly_ring_label', label=t(locale, 'weekly_ring_exercise'), percent=exercise_pct * 100)
        diet_patch = mpatches.Patch(color=C_PRIMARY, label=diet_label)
        water_patch = mpatches.Patch(color=C_SUCCESS, label=water_label)
        ex_patch = mpatches.Patch(color=C_WARNING, label=exercise_label)
        legend_kwargs = {
            "handles": [diet_patch, water_patch, ex_patch],
            "loc": "lower right",
            "bbox_to_anchor": (1.42, 0.02),
            "frameon": False,
        }
        if my_font:
            legend_kwargs["prop"] = my_font
        legend = ax.legend(**legend_kwargs)
        _style_legend(legend, my_font, fontsize=8)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: weekly ring chart generation failed: {e}")
        return None

def create_trend_line_chart(dates, values, title, locale):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop(locale)
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
        ax.tick_params(axis='x', colors=C_TEXT_MAIN, labelsize=8)
        ax.tick_params(axis='y', colors=C_TEXT_MAIN, labelsize=8)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=C_BORDER, zorder=1)
        _apply_axis_tick_style(ax, my_font)
        
        for d, v in valid_data:
            t = ax.text(d, v + (max_val - min_val)*0.05, f"{v:.1f}", ha='center', va='bottom', fontsize=9, color=C_TEXT_MAIN, fontweight='bold')
            _style_matplotlib_text(t, my_font, color=C_TEXT_MAIN, fontsize=9)
            
        title_obj = ax.set_title(title, color=C_TEXT_MAIN, loc='left', pad=15, fontweight='bold')
        _style_matplotlib_text(title_obj, my_font, color=C_TEXT_MAIN)
             
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: trend line generation failed: {e}")
        return None

def create_bar_trend_chart(dates, values, target, color, title, ylabel, locale):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        my_font = get_font_prop(locale)
        fig, ax = plt.subplots(figsize=(8, 3))
        
        bars = ax.bar(dates, values, color=color, width=0.4, alpha=0.85, zorder=2)
        
        if target and target > 0:
            ax.axhline(y=target, color=C_WARNING, linestyle='--', alpha=0.8, linewidth=1.5, zorder=1)
            t_tgt = ax.text(len(dates)-0.5, target, f"{target}", color=C_WARNING, va='bottom', ha='right', fontsize=9, fontweight='bold')
            _style_matplotlib_text(t_tgt, my_font, color=C_WARNING, fontsize=9)
            
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(C_BORDER)
        ax.tick_params(axis='y', colors=C_TEXT_MAIN, labelsize=8)
        ax.tick_params(axis='x', colors=C_TEXT_MAIN, labelsize=8)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=C_BORDER, zorder=0)
        _apply_axis_tick_style(ax, my_font)
        
        max_val = max(values + [target if target else 0])
        ax.set_ylim(0, max_val * 1.2)
        
        title_obj = ax.set_title(title, color=C_TEXT_MAIN, loc='left', pad=15, fontweight='bold')
        _style_matplotlib_text(title_obj, my_font, color=C_TEXT_MAIN)

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
        my_font = get_font_prop(locale)
        carb_kcal, protein_kcal, fat_kcal = carb * 4, protein * 4, fat * 9
        if carb_kcal + protein_kcal + fat_kcal <= 0: return None
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        wedges, texts, autotexts = ax.pie([carb_kcal, protein_kcal, fat_kcal], labels=[t(locale, 'carb'), t(locale, 'protein'), t(locale, 'fat')], colors=[C_CARB, C_PROTEIN, C_FAT], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'))
        
        for label_text in texts:
            _style_matplotlib_text(label_text, my_font, color=C_TEXT_MAIN, fontsize=9)
        for auto_text in autotexts:
            auto_text.set_color("#FFFFFF")
            auto_text.set_fontsize(9)
            auto_text.set_fontweight("bold")
            auto_text.set_path_effects([path_effects.withStroke(linewidth=2, foreground=C_TEXT_MAIN)])
            if my_font:
                auto_text.set_fontproperties(my_font)

        center_text = ax.text(0, 0, t(locale, 'weekly_nutrition_center', calories=int(calories)), ha='center', va='center', fontsize=10, fontweight='bold', color=C_TEXT_MAIN)
        _style_matplotlib_text(center_text, my_font, color=C_TEXT_MAIN, fontsize=10)
        
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=200)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: weekly nutrition chart generation failed: {e}")
        return None

def generate_weekly_pdf_report(weekly_data, profile, ai_review, ai_plan, output_path, locale="zh-CN", review_source="fallback", plan_source="fallback"):
    locale = resolve_locale(locale=locale)
    font_name = register_chinese_font(locale)
    render_notice = str(weekly_data.get("render_notice") or "").strip()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title=t(locale, 'weekly_report_title'))
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=HexColor(C_PRIMARY), spaceAfter=5, alignment=TA_CENTER, fontName=font_name)
    sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MUTED), spaceAfter=16, alignment=TA_CENTER, fontName=font_name)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=HexColor(C_PRIMARY), spaceBefore=18, spaceAfter=12, fontName=font_name)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, textColor=HexColor(C_TEXT_MAIN), fontName=font_name, leading=18)
    muted_style = ParagraphStyle('Muted', parent=normal_style, textColor=HexColor(C_TEXT_MUTED), fontSize=9, leading=13)
    footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=HexColor(C_TEXT_MUTED), alignment=TA_CENTER, leading=13)
    source_note_style = ParagraphStyle('SourceNote', parent=muted_style, alignment=TA_RIGHT, spaceBefore=4, spaceAfter=0)
    notice_style = ParagraphStyle(
        'RenderNotice',
        parent=normal_style,
        backColor=HexColor("#FFF7ED"),
        borderColor=HexColor(C_WARNING),
        borderWidth=0.8,
        borderPadding=8,
        leading=14,
        spaceAfter=10,
    )
    chart_label_style = ParagraphStyle('ChartLabel', parent=normal_style, textColor=HexColor(C_TEXT_MUTED), fontSize=10, leading=14, spaceBefore=4, spaceAfter=6)

    def source_text(source):
        labels = {
            "llm": localize(locale, "来源：LLM 动态生成", "Source: LLM generated"),
            "fallback": localize(locale, "来源：本地规则", "Source: local rules"),
            "fallback_tavily": localize(locale, "来源：Tavily 检索 + 本地规则", "Source: Tavily retrieval + local rules"),
        }
        return labels.get(source or "fallback", labels["fallback"])

    def append_lines(text):
        for para in str(text or "").split("\n"):
            clean = clean_html_tags(para).strip()
            if not clean or clean.startswith("["):
                continue
            if clean.startswith("-") or clean.startswith("*"):
                clean = clean[1:].strip()
                story.append(Paragraph(f"<font color='{C_PRIMARY}'>■</font> {clean}", normal_style))
            else:
                story.append(Paragraph(clean, normal_style))
            story.append(Spacer(1, 0.08*cm))

    story = []
    temp_images = []

    story.append(Paragraph(f"<b>{profile_condition_title(profile, locale)} · {t(locale, 'weekly_report_title')}</b>", title_style))
    story.append(Paragraph(t(locale, 'weekly_period', start_date=weekly_data['start_date'], end_date=weekly_data['end_date'], name=profile.get('name', t(locale, 'default_name'))), sub_title))
    if render_notice:
        story.append(Paragraph(f"<b>{t(locale, 'render_notice_title')}</b><br/>{clean_html_tags(render_notice)}", notice_style))
        story.append(Spacer(1, 0.15*cm))

    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor(C_BG_HEAD)),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor(C_TEXT_MUTED)),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor(C_TEXT_MAIN)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, HexColor(C_BORDER)),
    ]

    story.append(Paragraph(f"1. {localize(locale, '个人信息', 'Profile')}", heading_style))
    profile_rows = [
        [localize(locale, '项目', 'Item'), localize(locale, '内容', 'Value')],
        [localize(locale, '监测人', 'Name'), profile.get('name', t(locale, 'default_name'))],
        [localize(locale, '管理目标', 'Conditions'), profile_condition_title(profile, locale)],
        [localize(locale, '年龄/身高', 'Age / Height'), f"{profile.get('age', '-')} / {profile.get('height_cm', '-')}cm"],
        [localize(locale, '当前/目标体重', 'Current / Target weight'), f"{format_weight(locale, weekly_data.get('latest_weight') or profile.get('current_weight_kg'))} / {format_weight(locale, profile.get('target_weight_kg'))}"],
        [localize(locale, '饮水/步数目标', 'Hydration / Step target'), f"{profile.get('water_target_ml', 2000)}ml / {profile.get('step_target', 8000)}"],
    ]
    profile_table = Table(profile_rows, colWidths=[4.5*cm, 10.5*cm])
    profile_table.setStyle(TableStyle(table_style))
    story.append(profile_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(f"2. {t(locale, 'weekly_overview_title')}", heading_style))
    macro_scores = weekly_data.get('macro_scores', {})
    radar_chart = create_macro_radar_chart(macro_scores, locale)
    heatmap_chart = create_symptom_heatmap(weekly_data.get('daily_records', []), locale, min_weeks=1)
    if radar_chart:
        temp_images.append(radar_chart)
    if heatmap_chart:
        temp_images.append(heatmap_chart)
    if radar_chart and heatmap_chart:
        chart_table = Table(
            [[_build_chart_image(radar_chart, 7.2, 6.2), _build_chart_image(heatmap_chart, 10.0, 5.2)]],
            colWidths=[7.4*cm, 10.2*cm],
        )
        chart_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        story.append(chart_table)
    elif radar_chart:
        img = _build_chart_image(radar_chart, 10.2, 8.0)
        story.append(img)
    elif heatmap_chart:
        story.append(_build_chart_image(heatmap_chart, 16.0, 5.5))
    if heatmap_chart:
        story.append(Paragraph(localize(locale, "热力图右上角 M 表示该日有用药记录。", "In the heatmap, the corner marker M indicates a medication day."), muted_style))
        story.append(Spacer(1, 0.12*cm))

    summary_rows = [
        [t(locale, 'dimension'), t(locale, 'value'), t(locale, 'health_status')],
        [localize(locale, '周均综合评分', 'Average overall score'), f"{weekly_data.get('avg_total_score', 0):.1f}/100", t(locale, 'excellent') if weekly_data.get('avg_total_score', 0) >= 80 else t(locale, 'needs_improvement')],
        [t(locale, 'average_weight'), format_weight(locale, weekly_data.get('avg_weight')), t(locale, 'stable') if abs(weekly_data.get('weight_change', 0)) <= 0.3 else (t(locale, 'down') if weekly_data.get('weight_change', 0) < 0 else t(locale, 'up'))],
        [t(locale, 'average_calories'), f"{weekly_data.get('avg_calories', 0):.0f} kcal", t(locale, 'normal')],
        [t(locale, 'average_water'), f"{weekly_data.get('avg_water', 0):.0f} ml", t(locale, 'achieved') if weekly_data.get('water_goal_days', 0) >= 5 else t(locale, 'under_target')],
        [t(locale, 'average_steps'), f"{weekly_data.get('avg_steps', 0):.0f}", t(locale, 'active') if weekly_data.get('step_goal_days', 0) >= 4 else t(locale, 'low')],
        [localize(locale, '症状/用药记录', 'Symptoms / medication'), f"{weekly_data.get('symptom_days', 0)} / {weekly_data.get('medication_days', 0)}", localize(locale, '需结合复盘', 'Review together')],
    ]
    summary_table = Table(summary_rows, colWidths=[4.5*cm, 4.5*cm, 6*cm])
    summary_table.setStyle(TableStyle(table_style))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(f"3. {localize(locale, '本周亮点与重点', 'Highlights And Focus')}", heading_style))
    story.append(Paragraph(f"<b>{localize(locale, '本周亮点', 'Strengths This Week')}</b>", normal_style))
    append_lines("\n".join(f"- {item}" for item in weekly_data.get("strengths", [])[:4]))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(f"<b>{localize(locale, '待改进项', 'Needs Attention')}</b>", normal_style))
    append_lines("\n".join(f"- {item}" for item in weekly_data.get("gaps", [])[:4]))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(f"<b>{localize(locale, '下周重点', 'Focus For Next Week')}</b>", normal_style))
    append_lines("\n".join(f"- {item}" for item in weekly_data.get("next_focus", [])[:4]))

    custom_rows = [section for section in weekly_data.get("custom_section_stats", []) if section.get("days_recorded", 0) > 0]
    if custom_rows:
        story.append(Spacer(1, 0.1*cm))
        story.append(Paragraph(f"<b>{localize(locale, '额外监测项目', 'Additional Monitoring')}</b>", normal_style))
        custom_table_data = [[localize(locale, '项目', 'Item'), localize(locale, '记录天数', 'Days'), localize(locale, '条目数', 'Items')]]
        for section in custom_rows[:6]:
            custom_table_data.append([section.get("title", "-"), str(section.get("days_recorded", 0)), str(section.get("items", 0))])
        custom_table = Table(custom_table_data, colWidths=[8*cm, 3*cm, 3*cm])
        custom_table.setStyle(TableStyle(table_style))
        story.append(custom_table)
        story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph(f"4. {t(locale, 'weekly_trend_title')}", heading_style))
    short_dates = [d[5:] for d in weekly_data['dates']]
    weight_values = [w * 2 if w else None for w in weekly_data['weights']] if locale == "zh-CN" else weekly_data['weights']
    weight_chart = create_trend_line_chart(short_dates, weight_values, t(locale, 'weight_trend_title', unit=weight_unit(locale)), locale)
    if weight_chart:
        temp_images.append(weight_chart)
        story.append(Paragraph(f"<b>{t(locale, 'weekly_chart_weight_label')}</b>", chart_label_style))
        story.append(_build_chart_image(weight_chart, 14.0, 5.25))
        story.append(Spacer(1, 0.2*cm))

    bmr_val = (10 * (profile.get('current_weight_kg', 65)) + 6.25 * profile.get('height_cm', 172) - 5 * profile.get('age', 34) + (5 if str(profile.get('gender', 'male')).lower() == 'male' else -161))
    tdee_val = int(bmr_val * profile.get('activity_level', 1.2))
    cal_chart = create_bar_trend_chart(short_dates, weekly_data['calories'], tdee_val, C_WARNING, t(locale, 'calorie_trend_title'), t(locale, 'calories'), locale)
    if cal_chart:
        temp_images.append(cal_chart)
        story.append(Paragraph(f"<b>{t(locale, 'weekly_chart_calorie_label')}</b>", chart_label_style))
        story.append(_build_chart_image(cal_chart, 14.0, 5.25))
        story.append(Spacer(1, 0.2*cm))

    nutri_chart = create_weekly_nutrition_chart(weekly_data['avg_calories'], weekly_data['avg_protein'], weekly_data['avg_fat'], weekly_data['avg_carb'], locale)
    if nutri_chart:
        temp_images.append(nutri_chart)
        story.append(Paragraph(f"<b>{t(locale, 'weekly_chart_nutrition_label')}</b>", chart_label_style))
        img = _build_chart_image(nutri_chart, 10.0, 6.0)
        story.append(img)
        story.append(Spacer(1, 0.2*cm))

    step_chart = create_bar_trend_chart(short_dates, weekly_data['steps'], profile.get('step_target', 8000), C_PRIMARY, t(locale, 'step_trend_title'), t(locale, 'average_steps'), locale)
    if step_chart:
        temp_images.append(step_chart)
        story.append(Paragraph(f"<b>{t(locale, 'weekly_chart_step_label')}</b>", chart_label_style))
        story.append(_build_chart_image(step_chart, 14.0, 5.25))
        story.append(Spacer(1, 0.2*cm))

    water_chart = create_bar_trend_chart(short_dates, weekly_data['water_intakes'], profile.get('water_target_ml', 2000), C_SUCCESS, t(locale, 'water_trend_title'), t(locale, 'average_water'), locale)
    if water_chart:
        temp_images.append(water_chart)
        story.append(Paragraph(f"<b>{t(locale, 'weekly_chart_water_label')}</b>", chart_label_style))
        story.append(_build_chart_image(water_chart, 14.0, 5.25))
        story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph(f"5. {t(locale, 'weekly_ai_review_title')}", heading_style))
    append_lines(ai_review)
    story.append(Paragraph(source_text(review_source), source_note_style))

    story.append(Paragraph(f"6. {t(locale, 'weekly_next_plan_title')}", heading_style))
    append_lines(ai_plan)
    story.append(Paragraph(source_text(plan_source), source_note_style))

    story.append(Spacer(1, 0.16*cm))
    story.append(Paragraph(localize(locale, f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"), footer_style))
    story.append(Paragraph(f"{profile_condition_title(profile, locale)} - Health-Mate", footer_style))

    doc.build(story)
    for img in temp_images:
        try:
            os.remove(img)
        except Exception:
            pass
    print(f"Weekly PDF generated: {output_path}")
