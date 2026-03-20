#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF rendering for the daily Health-Mate report."""

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
from i18n import (
    PORTION_UNIT_PATTERN,
    condition_name,
    exercise_name,
    format_weight,
    meal_name,
    resolve_locale,
    strip_approximate_phrase,
    strip_parenthetical_details,
    t,
)

try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm  
    import matplotlib.patheffects as path_effects  
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib is not installed, so chart rendering is disabled.")

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
    """Strip HTML and symbols that commonly break PDF rendering."""
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    for emoji in ['⭐', '✅', '⚠️', '⚠', '❌', '🎉', '💡', '🚶', '🍎', '🥗', '💧', '🏃', '📊', '📈', '📄', '📥', '🥣', '🍜', '🍽️', '🍲', '⏰', '🚴', '🧘', '🔴', '🥦', '🍚', '🍳', '🥤', '🕐', '🌙', '💪', '🎯', '📌', '👍', '💯', '💊', '☑', '☑️', '📝', '🤖', '🌟', '📋']: 
        text = text.replace(emoji, '')
    return re.sub(r'\s+', ' ', re.sub(r'[\ufffd]', '', re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text))).strip()

def stars_to_text(stars_str):
    if not stars_str: return ""
    star_count = str(stars_str).count('⭐')
    return f'<font color="{C_WARNING_STR}">{"★" * star_count}</font>' + f'<font color="{C_BORDER_STR}">{"★" * (5 - star_count)}</font>'


def simplify_food_name_for_pdf(value):
    text = strip_parenthetical_details(strip_approximate_phrase(value))
    return re.sub(r'\s+', ' ', text).strip()


def compact_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def build_exercise_detail_lines(exercise_data, steps, locale):
    lines = []
    for entry in exercise_data or []:
        label = exercise_name(locale, entry.get('type', 'other'))
        if entry.get('time'):
            label = f"{label} ({entry.get('time')})"

        details = []
        if entry.get('distance_km', 0) > 0:
            details.append(t(locale, 'distance_unit_km', value=compact_number(entry.get('distance_km', 0))))
        if entry.get('duration_min', 0) > 0:
            details.append(t(locale, 'minutes_unit', value=compact_number(entry.get('duration_min', 0))))
        if entry.get('calories', 0) > 0:
            details.append(t(locale, 'calories_unit', value=compact_number(entry.get('calories', 0))))

        lines.append(f"{label}: {' / '.join(details)}" if details else label)

    if steps > 0:
        lines.append(f"{t(locale, 'today_steps')}: {t(locale, 'steps_unit', value=steps)}")
    return lines

def register_chinese_font():
    try: pdfmetrics.getFont('Chinese'); return 'Chinese'
    except: pass
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "..", "assets")
    local_ttf = os.path.normpath(os.path.join(assets_dir, "NotoSansSC-VF.ttf"))
    if not os.path.exists(local_ttf):
        try:
            if not os.path.exists(assets_dir): os.makedirs(assets_dir, exist_ok=True)
            with urllib.request.urlopen("https://raw.githubusercontent.com/tankeito/Health-Mate/main/assets/NotoSansSC-VF.ttf", timeout=15) as response:
                with open(local_ttf, 'wb') as f: f.write(response.read())
        except: return 'Helvetica'
    if os.path.exists(local_ttf):
        try: pdfmetrics.registerFont(TTFont('Chinese', local_ttf)); return 'Chinese'
        except: pass
    return 'Helvetica'

def get_font_prop():
    local_ttf = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "NotoSansSC-VF.ttf"))
    return fm.FontProperties(fname=local_ttf) if os.path.exists(local_ttf) else None

def create_nutrition_chart(nutrition, locale):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop()
        carb_kcal, protein_kcal, fat_kcal = nutrition.get('carb', 0)*4, nutrition.get('protein', 0)*4, nutrition.get('fat', 0)*9
        if carb_kcal + protein_kcal + fat_kcal <= 0: return None
        
        fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
        _, texts, autotexts = ax.pie(
            [carb_kcal, protein_kcal, fat_kcal],
            labels=[t(locale, 'carb'), t(locale, 'protein'), t(locale, 'fat')],
            colors=[C_CARB, C_PROTEIN, C_FAT],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor='w'),
        )
        for label_text in texts:
            label_text.set_color(C_TEXT_MUTED_STR)
            label_text.set_fontsize(9)
            if my_font: label_text.set_fontproperties(my_font)
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontsize(9)
            at.set_fontweight("bold")
            at.set_path_effects([path_effects.withStroke(linewidth=2, foreground=C_TEXT_MAIN_STR)])
            if my_font: at.set_fontproperties(my_font)
            
        center_text = ax.text(
            0,
            0,
            t(locale, 'nutrition_chart_center', calories=int(nutrition.get('calories', 0))),
            ha='center',
            va='center',
            fontsize=12,
            fontweight='bold',
            color=C_TEXT_MAIN_STR,
        )
        if my_font: center_text.set_fontproperties(my_font)
        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        return temp_img.name
    except Exception:
        return None

def create_water_chart(water_records, target_ml, locale):
    if not MATPLOTLIB_AVAILABLE or not water_records: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop()
        total_drank = sum([int(r.get('amount_ml', 0)) for r in water_records])
        target = target_ml if target_ml > 0 else 2000
        remaining = max(0, target - total_drank)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={'width_ratios': [1, 1.5]})
        vibrant_colors = ["#4A90E2", "#50E3C2", "#F5A623", "#F8E71C", "#FF4081", "#00BCD4", "#9013FE"]
        if total_drank == 0: 
            ax1.pie([1], colors=[C_BORDER_STR], startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'))
        else: 
            amounts_circle = [int(r.get('amount_ml', 0)) for r in water_records]
            sizes = amounts_circle + ([remaining] if remaining > 0 else [])
            c_list = [vibrant_colors[i % len(vibrant_colors)] for i in range(len(amounts_circle))]
            if remaining > 0: c_list.append(C_BORDER_STR)
            ax1.pie(sizes, colors=c_list, startangle=90, wedgeprops=dict(width=0.3, edgecolor='w', linewidth=1.5))
            
        t_center = ax1.text(0, 0, t(locale, 'water_chart_center', current=total_drank, target=target), ha='center', va='center', fontsize=11, fontweight='bold', color=C_TEXT_MAIN_STR)
        if my_font: t_center.set_fontproperties(my_font)
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
                mapping = {'wake_up': 7, 'morning': 10, 'noon': 12.5, 'afternoon': 16, 'evening': 20}
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
                
                if len(amounts) == 1:
                    t_bar = ax2.text(bin_pos, current_bottom + amt + 15, f"{amt}", ha='center', va='bottom', fontsize=8, color=C_TEXT_MAIN_STR)
                else:
                    t_bar = ax2.text(bin_pos + 0.8, current_bottom + amt/2, f"{amt}", ha='left', va='center', fontsize=8, color=C_TEXT_MAIN_STR)
                if my_font: t_bar.set_fontproperties(my_font)
                current_bottom += amt
            
            if len(amounts) > 1:
                t_total = ax2.text(bin_pos, current_bottom + 15, t(locale, 'water_chart_total', amount=current_bottom), ha='center', va='bottom', fontsize=8, color=C_TEXT_MAIN_STR, fontweight='bold')
                if my_font: t_total.set_fontproperties(my_font)
            
            max_y = max(max_y, current_bottom)
        
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(True)
        ax2.spines['left'].set_color(C_BORDER_STR)
        ax2.spines['bottom'].set_color(C_BORDER_STR)
        
        if max_y == 0:
            y_limit, step = 500, 100
        else:
            y_limit = int(max_y * 1.2)
            step = max(100, int((max_y / 5) / 100) * 100)
            
        ax2.set_yticks(range(step, y_limit + step, step))
        ax2.set_ylim(0, max_y + (step if max_y < 800 else max_y * 0.3))
        
        ax2.tick_params(axis='y', labelleft=True, colors=C_TEXT_MUTED_STR, labelsize=8)
        ax2.tick_params(axis='x', colors=C_TEXT_MUTED_STR)
        ax2.yaxis.grid(True, linestyle='--', alpha=0.4, color=C_BORDER_STR)
        
        if my_font:
            for label in ax2.get_xticklabels(): label.set_fontproperties(my_font)

        plt.tight_layout()
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_img.name, transparent=True, dpi=150)
        plt.close(fig)
        return temp_img.name
    except Exception as e:
        print(f"WARNING: water chart generation failed: {e}")
        return None

def create_exercise_chart(exercise_data, steps, step_target=8000, locale="zh-CN"):
    if not MATPLOTLIB_AVAILABLE: return None
    try:
        locale = resolve_locale(locale=locale)
        my_font = get_font_prop()
        labels, calories, targets, is_step, inner_texts = [], [], [], [], []
        
        if exercise_data:
            for e in exercise_data:
                ex_type = exercise_name(locale, e.get('type', 'other'))
                dist = e.get('distance_km', 0)
                dur = e.get('duration_min', 0)
                
                labels.append(ex_type)
                
                in_str = []
                if dist > 0: in_str.append(t(locale, 'distance_unit_km', value=dist))
                if dur > 0: in_str.append(f"({t(locale, 'minutes_unit', value=dur)})")
                inner_texts.append(" ".join(in_str))
                
                calories.append(e.get('calories', 0))
                targets.append(None) 
                is_step.append(False)
                
        if steps > 0:
            labels.append(t(locale, 'today_steps'))
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
        
        max_bg = max(step_target, steps) if steps > 0 else 100
        
        for i, (label, cal, tgt, is_s, in_txt) in enumerate(zip(labels, calories, targets, is_step, inner_texts)):
            if is_s:
                ax.plot([0, max_bg], [i, i], color=track_color, linewidth=12, solid_capstyle='round', zorder=1)
                ax.plot([0, cal], [i, i], color=step_color, linewidth=12, solid_capstyle='round', zorder=2)
                text_str = t(locale, 'step_progress', current=int(cal), target=int(tgt))
                t_val = ax.text(max_bg * 1.05, i, text_str, ha='left', va='center', fontsize=9, color=C_TEXT_MUTED_STR, zorder=3)
            else:
                ax.plot([0, max_bg], [i, i], color=chart_color, linewidth=12, solid_capstyle='round', zorder=1)
                if in_txt:
                    t_in = ax.text(max_bg * 0.02, i, in_txt, ha='left', va='center', fontsize=9, color=C_TEXT_MAIN_STR, fontweight='bold', zorder=3)
                    if my_font: t_in.set_fontproperties(my_font)
                text_str = t(locale, 'calories_unit', value=int(cal))
                t_val = ax.text(max_bg * 1.05, i, text_str, ha='left', va='center', fontsize=9, color=C_TEXT_MUTED_STR, zorder=3)

            if my_font: t_val.set_fontproperties(my_font)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()  
        ax.set_ylim(len(labels) - 0.5, -0.5)
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
        print(f"WARNING: exercise chart generation failed: {e}")
        return None

def generate_pdf_report(data, profile, scores, nutrition, macros, risks, plan, output_path, locale="zh-CN", water_records=None, meals=None, exercise_data=None, ai_comment=None, custom_sections=None):
    locale = resolve_locale(locale=locale)
    font_name = register_chinese_font()
    footer_text = f"{condition_name(locale, profile.get('condition', 'balanced'))} - Health-Mate"

    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm, title=t(locale, "daily_report_title"))
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
    
    condition_title = condition_name(locale, profile.get('condition', 'balanced'))
    story.append(Paragraph(f"<b>{condition_title} · {t(locale, 'daily_report_title')}</b>", title_style))
    story.append(Paragraph(f"<font color='#64748B'>{data['date']} | {profile.get('name', t(locale, 'default_name'))}</font>", ParagraphStyle('Date', parent=normal_style, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"1. {t(locale, 'overall_score_title', date=data.get('date', ''))}", heading_style))
    score_data = [
        [t(locale, 'dimension'), t(locale, 'score'), t(locale, 'stars'), t(locale, 'status')],
        [t(locale, 'diet_label'), f"{scores['diet']['raw']:.0f}/100", Paragraph(stars_to_text(scores['diet']['stars']), cell_style_center), t(locale, 'achieved') if scores['diet']['raw']>=80 else t(locale, 'needs_improvement')],
        [t(locale, 'water_label'), f"{scores['water']['raw']:.0f}/100", Paragraph(stars_to_text(scores['water']['stars']), cell_style_center), t(locale, 'achieved') if scores['water']['raw']>=100 else t(locale, 'under_target')],
        [t(locale, 'weight_label'), f"{scores['weight']['raw']:.0f}/100", Paragraph(stars_to_text(scores['weight']['stars']), cell_style_center), t(locale, 'normal') if scores['weight'].get('bmi') and 18.5<=scores['weight']['bmi']<24 else t(locale, 'attention')],
        [t(locale, 'symptom_label'), f"{scores['symptom']['raw']:.0f}/100", Paragraph(stars_to_text(scores['symptom']['stars']), cell_style_center), t(locale, 'symptom_free') if not scores['symptom']['has_symptoms'] else t(locale, 'has_symptoms')],
        [t(locale, 'exercise_label'), f"{scores['exercise']['raw']:.0f}/100", Paragraph(stars_to_text(scores['exercise']['stars']), cell_style_center), t(locale, 'achieved') if scores['exercise']['raw']>=60 else t(locale, 'needs_boost')],
        [t(locale, 'adherence_label'), f"{scores['adherence']['raw']:.0f}/100", Paragraph(stars_to_text(scores['adherence']['stars']), cell_style_center), t(locale, 'excellent') if scores['adherence']['raw']>=80 else t(locale, 'fair')],
        [t(locale, 'score_total_label'), f"{scores['total']:.0f}/100", Paragraph(stars_to_text(scores['total_stars']), cell_style_center), t(locale, 'excellent') if scores['total']>=80 else t(locale, 'good') if scores['total']>=60 else t(locale, 'needs_improvement')],
    ]
    score_table = Table(score_data, colWidths=[4*cm, 3*cm, 3.5*cm, 3.5*cm])
    score_style = list(base_table_style)
    for i in range(1, len(score_data)):
        status = score_data[i][3]
        if status in [t(locale, 'achieved'), t(locale, 'excellent'), t(locale, 'normal'), t(locale, 'symptom_free')]:
            score_style.append(('TEXTCOLOR', (3, i), (3, i), C_SUCCESS))
        elif status in [t(locale, 'needs_improvement'), t(locale, 'under_target'), t(locale, 'attention'), t(locale, 'has_symptoms'), t(locale, 'needs_boost'), t(locale, 'fair')]:
            score_style.append(('TEXTCOLOR', (3, i), (3, i), C_WARNING if status in [t(locale, 'attention'), t(locale, 'needs_boost'), t(locale, 'fair'), t(locale, 'needs_improvement')] else C_DANGER))
    score_table.setStyle(TableStyle(score_style))
    story.append(score_table)
    story.append(Spacer(1, 0.4*cm))
    
    if ai_comment:
        story.append(Paragraph(t(locale, 'expert_ai_insights'), heading_style))
        clean_comment = '\n'.join([l for l in ai_comment.split('\n') if not l.strip().startswith(('[plugins]', '[adp-', 'Hint:', 'error:'))]).strip()
        for para in clean_comment.split('\n'):  
            if para.strip(): 
                story.append(Paragraph(f"<font color='#1E293B'>{clean_html_tags(para)}</font>", normal_style))
                story.append(Spacer(1, 0.15*cm)) 
        story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph(f"2. {t(locale, 'daily_baseline_data')}", heading_style))
    bmi_val = scores["weight"].get("bmi", 0) or 0
    weight_val = data.get("weight_morning")
    bmr_val = (10*(weight_val or 65) + 6.25*profile.get('height_cm',172) - 5*profile.get('age',34) + (5 if str(profile.get('gender', 'male')).lower() == 'male' else -161))
    tdee_val = bmr_val * profile.get('activity_level', 1.2)
    
    health_data = [
        [t(locale, 'metric'), t(locale, 'value'), t(locale, 'reference_range')],
        [t(locale, 'height'), f"{profile['height_cm']}cm", t(locale, 'not_available')],
        [t(locale, 'weight'), format_weight(locale, weight_val), t(locale, 'weight_target', weight=format_weight(locale, profile.get('target_weight_kg', 64)))],
        [t(locale, 'bmi'), f"{bmi_val:.1f}", t(locale, 'bmi_reference')],
        [t(locale, 'bmr'), f"{bmr_val:.0f} kcal", t(locale, 'not_available')],
        [t(locale, 'tdee'), f"{tdee_val:.0f} kcal", t(locale, 'not_available')],
        [t(locale, 'recommended_calories'), f"{tdee_val:.0f} kcal/day", t(locale, 'recommended_calories_reference', condition=condition_title)],
        [t(locale, 'protein'), f"{macros.get('protein_g', 0)}g/day", f"{macros.get('protein_p', 0)}%"],
        [t(locale, 'fat'), f"{macros.get('fat_g', 0)}g/day", f"{macros.get('fat_p', 0)}%"],
        [t(locale, 'carb'), f"{macros.get('carb_g', 0)}g/day", f"{macros.get('carb_p', 0)}%"],
        [t(locale, 'fiber'), f">={macros.get('fiber_min_g', 25)}g/day", t(locale, 'fiber_reference')],
    ]
    health_table = Table(health_data, colWidths=[5*cm, 4*cm, 5*cm])
    health_style = list(base_table_style)
    if 18.5 <= bmi_val < 24: health_style.append(('TEXTCOLOR', (1, 3), (1, 3), C_SUCCESS))
    elif bmi_val > 0: health_style.append(('TEXTCOLOR', (1, 3), (1, 3), C_DANGER if bmi_val >= 28 or bmi_val < 18.5 else C_WARNING))
    health_table.setStyle(TableStyle(health_style))
    story.append(health_table)
    story.append(Spacer(1, 0.4*cm))
    
    temp_images = []

    story.append(Paragraph(f"3. {t(locale, 'daily_nutrition_breakdown')}", heading_style))
    chart_path_nutrition = create_nutrition_chart(nutrition, locale)
    if chart_path_nutrition:
        temp_images.append(chart_path_nutrition)
        img = Image(chart_path_nutrition, width=10*cm, height=6*cm)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.2*cm))
    
    nutrition_data = [
        [t(locale, 'nutrient'), t(locale, 'actual_intake'), t(locale, 'recommended_intake')],
        [t(locale, 'calories'), f"{nutrition['calories']:.0f} kcal", f"{tdee_val:.0f} kcal"],
        [t(locale, 'protein'), f"{nutrition['protein']:.1f}g", f"{macros.get('protein_g', 0)}g"],
        [t(locale, 'fat'), f"{nutrition['fat']:.1f}g", f"{macros.get('fat_g', 0)}g"],
        [t(locale, 'carb'), f"{nutrition['carb']:.1f}g", f"{macros.get('carb_g', 0)}g"],
        [t(locale, 'fiber'), f"{nutrition['fiber']:.1f}g", f">={macros.get('fiber_min_g', 25)}g"],
    ]
    nutri_table = Table(nutrition_data, colWidths=[5*cm, 4*cm, 5*cm])
    nutri_table.setStyle(TableStyle(base_table_style))
    story.append(nutri_table)
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph(f"4. {t(locale, 'daily_water_details')}", heading_style))
    if water_records and len(water_records) > 0:
        chart_path_water = create_water_chart(water_records, data.get('water_target', 2000), locale)
        if chart_path_water:
            temp_images.append(chart_path_water)
            img_water = Image(chart_path_water, width=14*cm, height=5.25*cm)
            img_water.hAlign = 'CENTER'
            story.append(img_water)
            story.append(Spacer(1, 0.4*cm))
    else:
        story.append(Paragraph(f"<font color='#64748B'>{t(locale, 'no_water_today')}</font>", normal_style))
        story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph(f"5. {t(locale, 'daily_meal_details')}", heading_style))
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
            meal_title_text = f"<font color='{C_PRIMARY_STR}'>■</font> <b>{meal_name(locale, meal_type)}</b>{meal_time_str} <font color='#64748B' size='9'>· {t(locale, 'meal_total', calories=meal.get('total_calories', 0))}</font>"
            meal_title = Paragraph(meal_title_text, ParagraphStyle('MealTitle', parent=normal_style, spaceBefore=8, spaceAfter=4))
            meal_elements.append(meal_title)
            
            food_nutrition = meal.get("food_nutrition", [])
            if food_nutrition and len(food_nutrition) > 0:
                meal_data = [[t(locale, 'food_name'), t(locale, 'portion'), t(locale, 'calories'), t(locale, 'protein'), t(locale, 'fat'), t(locale, 'carb')]]
                for food in food_nutrition:
                    name_raw = food.get("name", "").split('→')[0].strip() if '→' in food.get("name", "") else food.get("name", "").strip()
                    portion_match = re.search(rf'(\d+(?:\.\d+)?)\s*{PORTION_UNIT_PATTERN}', name_raw, re.IGNORECASE)
                    if portion_match:
                        name_simple = re.sub(r'\s*' + re.escape(portion_match.group(0)), '', name_raw).strip()
                        portion_display = f"{float(portion_match.group(1)):.0f}{portion_match.group(2)}"
                    else:
                        name_simple = name_raw
                        portion_display = f"{food.get('portion_grams', 100):.0f}g"
                    
                    name_simple = simplify_food_name_for_pdf(name_simple)
                    
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
                meal_elements.append(Paragraph(f"<font color='#64748B'>{t(locale, 'no_food_detail')}</font>", normal_style))
            meal_elements.append(Spacer(1, 0.4*cm))
            story.append(KeepTogether(meal_elements))
    else:
        story.append(Paragraph(f"<font color='#64748B'>{t(locale, 'no_meals_today')}</font>", normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph(f"6. {t(locale, 'daily_exercise_details')}", heading_style))
    steps = data.get("steps", 0)
    step_target = profile.get("step_target", 8000)
    exercise_lines = build_exercise_detail_lines(exercise_data, steps, locale)
    if exercise_data or steps > 0:
        chart_path_exercise = create_exercise_chart(exercise_data, steps, step_target, locale)
        if chart_path_exercise:
            temp_images.append(chart_path_exercise)
            img_ex = Image(chart_path_exercise, width=12*cm, height=4.2*cm)
            img_ex.hAlign = 'LEFT'
            story.append(img_ex)
            story.append(Spacer(1, 0.2*cm))

        for line in exercise_lines:
            story.append(Paragraph(clean_html_tags(line), normal_style))
        if exercise_lines:
            story.append(Spacer(1, 0.2*cm))
        elif not chart_path_exercise:
            story.append(Paragraph(f"<font color='#64748B'>{t(locale, 'no_exercise_today')}</font>", normal_style))
    else:
        story.append(Paragraph(f"<font color='#64748B'>{t(locale, 'no_exercise_today')}</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    section_idx = 7
    
    if custom_sections:
        story.append(Paragraph(f"{section_idx}. {t(locale, 'extra_monitoring_records')}", heading_style))
        section_idx += 1
        for header, items in custom_sections.items():
            story.append(Paragraph(f"<b>{header}</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=4)))
            for item in items:
                item_text = re.sub(r'^\s*[-*]\s*', '', str(item or '')).strip()
                story.append(Paragraph(f"- {clean_html_tags(item_text)}", normal_style))
            story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(f"{section_idx}. {t(locale, 'risk_alerts')}", heading_style))
    section_idx += 1
    if risks:
        for risk in risks:
            story.append(Paragraph(f"<font color='{C_DANGER_STR}'><b>{clean_html_tags(risk.get('level', '')).strip()} {clean_html_tags(risk.get('item', ''))}</b></font>", normal_style))
            story.append(Paragraph(t(locale, 'risk_label', value=clean_html_tags(risk.get('risk', ''))), normal_style))
            story.append(Paragraph(t(locale, 'advice_label', value=clean_html_tags(risk.get('action', ''))), normal_style))
            story.append(Spacer(1, 0.2*cm))
    else:
        story.append(Paragraph(f"<font color='{C_SUCCESS_STR}'>{t(locale, 'no_risk')}</font>", normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph(f"{section_idx}. {t(locale, 'action_plan')}", heading_style))
    for category, title in [("diet", t(locale, 'diet_plan')), ("water", t(locale, 'water_plan')), ("exercise", t(locale, 'exercise_plan'))]:
        if plan.get(category):
            story.append(Paragraph(f"<b>{title}</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
            for item in plan.get(category, []):
                if isinstance(item, dict):
                    time = item.get('time', item.get('period', item.get('time_range', '')))
                    content = item.get('menu', item.get('activity', item.get('amount', '')))
                    note = item.get('note', item.get('details', ''))
                    
                    if not content: content = ('、' if locale == 'zh-CN' else ', ').join(str(i) for i in item.get('items', []))[:30]
                    
                    cal = item.get('calories', '')
                    if cal: note = f"{cal}kcal " + note
                    
                    clean_item = f"<b>{time}</b> {clean_html_tags(content)}"
                    if note: clean_item += f" <font color='#64748B'>({clean_html_tags(note)})</font>"
                else: 
                    clean_item = clean_html_tags(str(item))
                story.append(Paragraph(f"<font color='{C_PRIMARY_STR}'>■</font> {clean_item}", normal_style))
            story.append(Spacer(1, 0.2*cm))
            
    if plan.get("notes"):
        story.append(Paragraph(f"<b>{t(locale, 'special_attention')}</b>", ParagraphStyle('Sub', parent=normal_style, textColor=C_TEXT_MAIN, spaceAfter=6)))
        for item in plan.get("notes", []):
            story.append(Paragraph(f"<font color='{C_WARNING_STR}'>■</font> {clean_html_tags(item)}", normal_style))
    
    story.append(Spacer(1, 1.5*cm))
    footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    story.append(Paragraph(t(locale, 'generated_at', timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), footer_style))
    story.append(Paragraph(f"{footer_text}", footer_style))
    
    doc.build(story)
    for temp_img in temp_images:
        try: os.remove(temp_img)
        except: pass
    print(f"PDF report generated: {output_path}")

if __name__ == "__main__":
    print("Use this module via health_report_pro.py.")
    
