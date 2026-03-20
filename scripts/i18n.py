#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared locale helpers for Health-Mate."""

from __future__ import annotations

import os
import re
from typing import Dict, Iterable, Optional

DEFAULT_LOCALE = "zh-CN"
SUPPORTED_LOCALES = {"zh-CN", "en-US"}

LOCALE_ALIASES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_hans": "zh-CN",
    "zh-hans": "zh-CN",
    "cn": "zh-CN",
    "chinese": "zh-CN",
    "中文": "zh-CN",
    "简体中文": "zh-CN",
    "en": "en-US",
    "en-us": "en-US",
    "en_us": "en-US",
    "english": "en-US",
    "英文": "en-US",
}

TEXTS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        "security_warning_title": "安全警告",
        "env_validation_failed": "环境校验失败",
        "env_missing_memory_dir": "错误：MEMORY_DIR 环境变量未配置（必填）",
        "env_set_memory_dir": "请在 .env 文件中设置 MEMORY_DIR='/path/to/memory'。",
        "env_memory_dir_missing": "错误：MEMORY_DIR 目录不存在：{path}",
        "env_memory_dir_unreadable": "错误：MEMORY_DIR 目录无读取权限：{path}",
        "env_no_webhooks": "警告：未配置任何 Webhook，报告将仅在本地生成 PDF。",
        "env_webhook_hint": "如需推送，请配置 DINGTALK_WEBHOOK/FEISHU_WEBHOOK/TELEGRAM_*。",
        "program_exit": "程序已安全退出。请修复上述问题后重新运行。",
        "config_load_failed": "警告：读取配置文件失败 - {error}",
        "ai_comment_timeout": "AI 点评生成超时（第{attempt}次），重试中...",
        "ai_comment_failed": "AI 点评生成失败（第{attempt}次）：{error}",
        "ai_plan_timeout": "AI 方案生成超时（第{attempt}次），重试中...",
        "ai_plan_failed": "AI 方案生成失败（第{attempt}次）：{error}",
        "tavily_failed": "Tavily 搜索失败（第{attempt}次）：{error}",
        "exercise_score_failed": "警告：运动评分计算失败 - {error}",
        "daily_report_title": "健康日报",
        "weekly_report_title": "健康周报",
        "daily_report_heading": "{date} 健康报告",
        "weekly_text_heading": "{start_date} 至 {end_date} 健康周报",
        "overall_score_title": "{date} 今日综合评分",
        "item_summary_title": "分项汇总",
        "ai_comment_title": "AI 点评",
        "details_title": "今日详情汇总",
        "meal_section": "进食情况",
        "water_section": "饮水情况",
        "exercise_section": "运动情况",
        "next_day_plan_title": "次日优化方案（AI 动态生成）",
        "diet_label": "饮食合规性",
        "water_label": "饮水完成度",
        "weight_label": "体重管理",
        "symptom_label": "症状管理",
        "exercise_label": "运动管理",
        "adherence_label": "健康依从性",
        "score_total_label": "总分",
        "base_score_label": "基础分",
        "exercise_bonus_label": "运动加分",
        "fat_in_range": "脂肪摄入合理",
        "fat_low": "脂肪摄入过低 ({value:.1f}g)",
        "fat_high": "脂肪摄入超标 ({value:.1f}g)",
        "protein_ok": "蛋白质摄入充足",
        "protein_low": "蛋白质不足",
        "completion_status": "{current}ml/{target}ml，完成度 {percent}%",
        "weight_status": "晨起空腹：{weight}，BMI：{bmi:.1f}",
        "no_symptoms": "无不适症状",
        "symptoms_prefix": "症状：{symptoms}",
        "adherence_status": "完成 {meals} 餐，饮水{water_status}",
        "water_goal_met": "达标",
        "water_goal_not_met": "未达标",
        "no_record": "无记录",
        "no_detail_record": "无详细记录",
        "not_recorded": "未记录",
        "not_available": "-",
        "morning_fasting": "晨起空腹",
        "weight_target": "目标：{weight}",
        "bmi_reference": "18.5-24（正常）",
        "recommended_calories_reference": "{condition}安全范围",
        "fiber_reference": "促进胆汁排泄",
        "expert_ai_insights": "专家 AI 点评",
        "daily_baseline_data": "基础健康数据",
        "daily_nutrition_breakdown": "当日营养摄入核算",
        "daily_water_details": "饮水详情",
        "daily_meal_details": "进食详情",
        "daily_exercise_details": "运动详情",
        "extra_monitoring_records": "附加监测记录",
        "risk_alerts": "风险预警",
        "no_risk": "今日无明显风险，继续保持健康生活方式！",
        "action_plan": "次日可执行方案",
        "diet_plan": "饮食计划",
        "water_plan": "饮水计划",
        "exercise_plan": "运动建议",
        "special_attention": "特别关注",
        "generated_at": "报告生成时间：{timestamp}",
        "pdf_saved_local": "未配置公网域名，PDF 仅保存在本地。",
        "pdf_local_path": "本地路径：{path}",
        "pdf_copied": "PDF 已复制到 Web 目录：{path}",
        "pdf_download_url": "下载链接：{url}",
        "pdf_generation_failed": "PDF 生成失败 - {error}",
        "meal_total": "合计 {calories:.0f} kcal",
        "no_water_today": "今日无饮水记录",
        "no_meals_today": "今日无进食记录",
        "no_food_detail": "无详细食物记录",
        "no_exercise_today": "今日无运动记录",
        "risk_label": "风险：{value}",
        "advice_label": "建议：{value}",
        "nutrition_chart_center": "{calories}\nkcal",
        "water_chart_center": "{current}\n/ {target}ml",
        "water_chart_total": "总{amount}",
        "today_steps": "今日步数",
        "step_progress": "{current} / {target} 步",
        "calories_unit": "{value} kcal",
        "minutes_unit": "{value}分钟",
        "steps_unit": "{value}步",
        "distance_unit_km": "{value}km",
        "metric": "指标",
        "value": "数值",
        "reference_range": "参考范围",
        "height": "身高",
        "weight": "体重",
        "bmi": "BMI",
        "bmr": "基础代谢",
        "tdee": "每日消耗",
        "recommended_calories": "推荐热量",
        "protein": "蛋白质",
        "fat": "脂肪",
        "carb": "碳水",
        "fiber": "膳食纤维",
        "nutrient": "营养素",
        "actual_intake": "实际摄入",
        "recommended_intake": "推荐量",
        "food_name": "食物名称",
        "portion": "份量",
        "calories": "热量",
        "duration": "耗时",
        "distance": "距离",
        "burn": "消耗",
        "status": "状态",
        "dimension": "维度",
        "score": "得分",
        "stars": "星级",
        "achieved": "达标",
        "under_target": "未达标",
        "normal": "正常",
        "attention": "关注",
        "symptom_free": "无症状",
        "has_symptoms": "有症状",
        "needs_boost": "待加强",
        "excellent": "优秀",
        "fair": "一般",
        "good": "良好",
        "needs_improvement": "待改进",
        "average_weight": "平均体重",
        "average_calories": "日均摄入",
        "average_water": "日均饮水",
        "average_steps": "日均步数",
        "health_status": "健康状态",
        "stable": "稳定",
        "down": "下降",
        "up": "上升",
        "active": "活跃",
        "low": "偏低",
        "weekly_overview_title": "本周健康指标概览",
        "weekly_trend_title": "核心趋势分析",
        "weekly_ai_review_title": "专家 AI 深度复盘",
        "weekly_next_plan_title": "下周干预方案",
        "weekly_rings_center": "本周\n健康概览",
        "weekly_ring_diet": "饮食达标",
        "weekly_ring_water": "饮水达标",
        "weekly_ring_exercise": "运动达标",
        "target_line": "目标：{target}",
        "weight_trend_title": "本周体重波动趋势 ({unit})",
        "calorie_trend_title": "本周每日摄入热量 (kcal)",
        "step_trend_title": "本周每日步数分布 (步)",
        "water_trend_title": "本周每日饮水量分布 (ml)",
        "weekly_nutrition_center": "日均摄入\n{calories} kcal",
        "weekly_period": "评估周期：{start_date} 至 {end_date} | 监测人：{name}",
        "weekly_summary_title": "本周核心指标",
        "weekly_review_section": "本周复盘",
        "weekly_plan_section": "下周行动",
        "weekly_avg_weight_change": "平均体重变化：{value}",
        "weekly_avg_calories_line": "日均摄入热量：{value:.0f} kcal",
        "weekly_avg_water_line": "日均饮水量：{value:.0f} ml",
        "weekly_avg_steps_line": "日均步数：{value:.0f} 步",
        "weekly_symptom_count_line": "不适症状出现次数：{value} 次",
        "weekly_generated_at": "生成时间：{value}",
        "weekly_anchor_date": "锚点日期：{value}",
        "delivery_daily_pdf": "PDF 完整报告",
        "delivery_weekly_pdf": "PDF 完整周报",
        "delivery_download": "点击下载",
        "delivery_period": "报告周期：{start_date} 至 {end_date}",
        "condition_balanced": "均衡健康",
        "condition_gallstones": "胆结石管理",
        "condition_diabetes": "糖尿病管理",
        "condition_hypertension": "高血压管理",
        "condition_fat_loss": "健身减脂",
        "meal_breakfast": "早餐",
        "meal_lunch": "午餐",
        "meal_dinner": "晚餐",
        "meal_snack": "加餐",
        "water_wake_up": "晨起",
        "water_morning": "上午",
        "water_noon": "中午",
        "water_afternoon": "下午",
        "water_evening": "晚上",
        "exercise_cycling": "骑行",
        "exercise_walking": "散步",
        "exercise_running": "跑步",
        "exercise_workout": "健身",
        "exercise_yoga": "瑜伽",
        "exercise_swimming": "游泳",
        "exercise_other": "其他运动",
        "default_user": "用户",
        "default_name": "东东",
        "condition_tip_balanced": "均衡饮食、规律作息、稳定活动",
        "condition_tip_gallstones": "低脂（{fat_min}-{fat_max}g/天）、高纤维（≥{fiber_min}g/天）、规律进食",
        "condition_tip_diabetes": "控糖、控精制碳水、高纤维、少量多餐",
        "condition_tip_hypertension": "低盐（<2000mg/天）、高钾、高纤维",
        "condition_tip_fat_loss": "高蛋白、适量碳水、控制脂肪、保持训练",
        "fallback_comment_fat_ok": "脂肪摄入 {value:.1f}g 控制在理想范围内，这对你的健康目标很关键。",
        "fallback_comment_fat_low": "脂肪摄入仅 {value:.1f}g，略低于推荐值。适量健康脂肪仍然有必要。",
        "fallback_comment_fat_high": "脂肪摄入 {value:.1f}g 超标，明日需要严格控油。",
        "fallback_comment_fiber_ok": "膳食纤维 {value:.1f}g 达标，继续保持。",
        "fallback_comment_fiber_low": "膳食纤维仅 {value:.1f}g，建议明日增加蔬菜、豆类和粗粮。",
        "fallback_comment_water_ok": "饮水 {value}ml 已达标，做得很好。",
        "fallback_comment_water_low": "饮水仅 {value}ml，距离 {target}ml 目标还有差距。",
        "fallback_comment_steps_high": "今日 {value} 步，活动量充足。",
        "fallback_comment_steps_mid": "今日 {value} 步，基本合格，但仍有提升空间。",
        "fallback_comment_steps_low": "今日仅 {value} 步，活动量明显不足，建议明日增加步行或骑行。",
        "shortcoming_fat_low": "脂肪摄入过低",
        "shortcoming_fat_high": "脂肪摄入超标",
        "shortcoming_fiber_low": "膳食纤维不足",
        "shortcoming_water_low": "饮水不足",
        "shortcoming_exercise_low": "缺乏运动",
        "fallback_diet_1": "早餐（5 分钟）：燕麦粥 + 煮蛋白 2 个 + 凉拌黄瓜 (300kcal)",
        "fallback_diet_2": "午餐（10 分钟）：米饭 + 卤牛肉 + 白灼青菜 (450kcal)",
        "fallback_diet_3": "晚餐（10 分钟）：杂粮粥 + 凉拌豆腐 + 炒蔬菜 (350kcal)",
        "fallback_water_1": "07:30 晨起温水 300ml",
        "fallback_water_2": "10:00 工作间隙 400ml",
        "fallback_water_3": "14:00 午后 400ml",
        "fallback_water_4": "17:00 下班前 400ml",
        "fallback_water_5": "20:00 晚间 300ml",
        "fallback_water_target": "目标总量：{target}ml",
        "fallback_exercise_1": "早餐后散步 15 分钟（促进消化）",
        "fallback_exercise_2": "晚餐后散步 20 分钟（帮助代谢）",
        "fallback_exercise_3": "本周目标：累计运动 150 分钟",
        "fallback_note_fruits": "今日推荐水果：{fruits}",
        "fallback_note_overeat": "昨日有过饱迹象，今天建议控制到七分饱。",
        "fallback_note_fat_low": "昨日脂肪偏低，今天可适量增加健康脂肪，如橄榄油或坚果。",
        "fallback_note_fat_high": "昨日脂肪偏高，今天请避免油炸、重油和高脂甜点。",
        "fallback_note_fiber_low": "昨日纤维不足，今天请增加蔬菜、豆类和粗粮。",
        "fallback_note_exercise_low": "昨日活动量不足，今天建议安排一次轻中度运动。",
        "weekly_ai_failed": "AI 调用失败：{error}",
        "weekly_fallback_review": "本周数据收集完整，整体趋势平稳，请继续保持。",
        "weekly_fallback_plan_1": "保持每日饮水 2000ml",
        "weekly_fallback_plan_2": "增加餐后轻度活动",
        "weekly_fallback_plan_3": "继续控制脂肪摄入与饮食规律",
    },
    "en-US": {
        "security_warning_title": "Security Warning",
        "env_validation_failed": "Environment validation failed",
        "env_missing_memory_dir": "ERROR: MEMORY_DIR is not configured (required).",
        "env_set_memory_dir": "Set MEMORY_DIR='/path/to/memory' in your .env file.",
        "env_memory_dir_missing": "ERROR: MEMORY_DIR does not exist: {path}",
        "env_memory_dir_unreadable": "ERROR: MEMORY_DIR is not readable: {path}",
        "env_no_webhooks": "WARNING: No webhook is configured. Reports will only be generated locally as PDF.",
        "env_webhook_hint": "Configure DINGTALK_WEBHOOK/FEISHU_WEBHOOK/TELEGRAM_* if you want push delivery.",
        "program_exit": "The program exited safely. Fix the issues above and run it again.",
        "config_load_failed": "WARNING: Failed to read the config file - {error}",
        "ai_comment_timeout": "AI insight generation timed out (attempt {attempt}), retrying...",
        "ai_comment_failed": "AI insight generation failed (attempt {attempt}): {error}",
        "ai_plan_timeout": "AI plan generation timed out (attempt {attempt}), retrying...",
        "ai_plan_failed": "AI plan generation failed (attempt {attempt}): {error}",
        "tavily_failed": "Tavily search failed (attempt {attempt}): {error}",
        "exercise_score_failed": "WARNING: Exercise scoring failed - {error}",
        "daily_report_title": "Daily Health Report",
        "weekly_report_title": "Weekly Health Report",
        "daily_report_heading": "{date} Health Report",
        "weekly_text_heading": "Weekly Health Report ({start_date} to {end_date})",
        "overall_score_title": "Today's Overall Score",
        "item_summary_title": "Category Summary",
        "ai_comment_title": "AI Insight",
        "details_title": "Today's Breakdown",
        "meal_section": "Meals",
        "water_section": "Hydration",
        "exercise_section": "Exercise",
        "next_day_plan_title": "Action Plan For Tomorrow",
        "diet_label": "Diet Quality",
        "water_label": "Hydration",
        "weight_label": "Weight Management",
        "symptom_label": "Symptom Control",
        "exercise_label": "Exercise",
        "adherence_label": "Routine Adherence",
        "score_total_label": "Total",
        "base_score_label": "Base",
        "exercise_bonus_label": "Exercise Bonus",
        "fat_in_range": "Fat intake is on target",
        "fat_low": "Fat intake is low ({value:.1f}g)",
        "fat_high": "Fat intake is high ({value:.1f}g)",
        "protein_ok": "Protein intake is adequate",
        "protein_low": "Protein intake is low",
        "completion_status": "{current}ml/{target}ml, completion {percent}%",
        "weight_status": "Morning fasting weight: {weight}, BMI: {bmi:.1f}",
        "no_symptoms": "No symptoms recorded",
        "symptoms_prefix": "Symptoms: {symptoms}",
        "adherence_status": "{meals} meal blocks logged, hydration {water_status}",
        "water_goal_met": "on target",
        "water_goal_not_met": "below target",
        "no_record": "No record",
        "no_detail_record": "No detailed record",
        "not_recorded": "Not recorded",
        "not_available": "-",
        "morning_fasting": "Morning fasting",
        "weight_target": "Target: {weight}",
        "bmi_reference": "18.5-24 (normal)",
        "recommended_calories_reference": "{condition} target range",
        "fiber_reference": "Supports healthy digestion",
        "expert_ai_insights": "Expert AI Insight",
        "daily_baseline_data": "Baseline Health Data",
        "daily_nutrition_breakdown": "Nutrition Breakdown",
        "daily_water_details": "Hydration Details",
        "daily_meal_details": "Meal Details",
        "daily_exercise_details": "Exercise Details",
        "extra_monitoring_records": "Additional Tracking",
        "risk_alerts": "Risk Alerts",
        "no_risk": "No major risk was detected today. Keep the routine steady.",
        "action_plan": "Tomorrow's Action Plan",
        "diet_plan": "Diet Plan",
        "water_plan": "Hydration Plan",
        "exercise_plan": "Exercise Plan",
        "special_attention": "Special Attention",
        "generated_at": "Generated at: {timestamp}",
        "pdf_saved_local": "No public report URL is configured, so the PDF was kept locally.",
        "pdf_local_path": "Local file: {path}",
        "pdf_copied": "PDF copied to the web directory: {path}",
        "pdf_download_url": "Download URL: {url}",
        "pdf_generation_failed": "PDF generation failed - {error}",
        "meal_total": "{calories:.0f} kcal total",
        "no_water_today": "No hydration records today",
        "no_meals_today": "No meal records today",
        "no_food_detail": "No detailed food entries",
        "no_exercise_today": "No exercise records today",
        "risk_label": "Risk: {value}",
        "advice_label": "Advice: {value}",
        "nutrition_chart_center": "{calories}\nkcal",
        "water_chart_center": "{current}\n/ {target}ml",
        "water_chart_total": "Total {amount}",
        "today_steps": "Today's Steps",
        "step_progress": "{current} / {target} steps",
        "calories_unit": "{value} kcal",
        "minutes_unit": "{value} min",
        "steps_unit": "{value} steps",
        "distance_unit_km": "{value} km",
        "metric": "Metric",
        "value": "Value",
        "reference_range": "Reference",
        "height": "Height",
        "weight": "Weight",
        "bmi": "BMI",
        "bmr": "BMR",
        "tdee": "Daily Burn",
        "recommended_calories": "Target Calories",
        "protein": "Protein",
        "fat": "Fat",
        "carb": "Carbs",
        "fiber": "Fiber",
        "nutrient": "Nutrient",
        "actual_intake": "Actual",
        "recommended_intake": "Target",
        "food_name": "Food",
        "portion": "Portion",
        "calories": "Calories",
        "duration": "Duration",
        "distance": "Distance",
        "burn": "Burn",
        "status": "Status",
        "dimension": "Category",
        "score": "Score",
        "stars": "Stars",
        "achieved": "On target",
        "under_target": "Below target",
        "normal": "Normal",
        "attention": "Watch",
        "symptom_free": "Clear",
        "has_symptoms": "Symptoms",
        "needs_boost": "Needs work",
        "excellent": "Excellent",
        "fair": "Fair",
        "good": "Good",
        "needs_improvement": "Needs improvement",
        "average_weight": "Average weight",
        "average_calories": "Average calories",
        "average_water": "Average hydration",
        "average_steps": "Average steps",
        "health_status": "Status",
        "stable": "Stable",
        "down": "Down",
        "up": "Up",
        "active": "Active",
        "low": "Low",
        "weekly_overview_title": "Weekly Overview",
        "weekly_trend_title": "Trend Analysis",
        "weekly_ai_review_title": "Expert AI Weekly Review",
        "weekly_next_plan_title": "Plan For Next Week",
        "weekly_rings_center": "Weekly\nOverview",
        "weekly_ring_diet": "Diet goal",
        "weekly_ring_water": "Hydration goal",
        "weekly_ring_exercise": "Exercise goal",
        "target_line": "Target: {target}",
        "weight_trend_title": "Weight Trend This Week ({unit})",
        "calorie_trend_title": "Daily Calories This Week (kcal)",
        "step_trend_title": "Daily Steps This Week",
        "water_trend_title": "Daily Hydration This Week (ml)",
        "weekly_nutrition_center": "Daily avg\n{calories} kcal",
        "weekly_period": "Period: {start_date} to {end_date} | User: {name}",
        "weekly_summary_title": "Weekly Metrics",
        "weekly_review_section": "Weekly Review",
        "weekly_plan_section": "Next Week Actions",
        "weekly_avg_weight_change": "Average weight change: {value}",
        "weekly_avg_calories_line": "Average daily calories: {value:.0f} kcal",
        "weekly_avg_water_line": "Average daily hydration: {value:.0f} ml",
        "weekly_avg_steps_line": "Average daily steps: {value:.0f}",
        "weekly_symptom_count_line": "Symptom events: {value}",
        "weekly_generated_at": "Generated at: {value}",
        "weekly_anchor_date": "Anchor date: {value}",
        "delivery_daily_pdf": "Full PDF Report",
        "delivery_weekly_pdf": "Full Weekly PDF",
        "delivery_download": "Download",
        "delivery_period": "Report period: {start_date} to {end_date}",
        "condition_balanced": "Balanced Wellness",
        "condition_gallstones": "Gallstone Care",
        "condition_diabetes": "Diabetes Support",
        "condition_hypertension": "Blood Pressure Support",
        "condition_fat_loss": "Fat Loss",
        "meal_breakfast": "Breakfast",
        "meal_lunch": "Lunch",
        "meal_dinner": "Dinner",
        "meal_snack": "Snack",
        "water_wake_up": "Wake-up",
        "water_morning": "Morning",
        "water_noon": "Noon",
        "water_afternoon": "Afternoon",
        "water_evening": "Evening",
        "exercise_cycling": "Cycling",
        "exercise_walking": "Walking",
        "exercise_running": "Running",
        "exercise_workout": "Workout",
        "exercise_yoga": "Yoga",
        "exercise_swimming": "Swimming",
        "exercise_other": "Exercise",
        "default_user": "User",
        "default_name": "Demo User",
        "condition_tip_balanced": "Balanced meals, consistent routines, and steady daily movement",
        "condition_tip_gallstones": "Low fat ({fat_min}-{fat_max}g/day), high fiber (≥{fiber_min}g/day), and regular meals",
        "condition_tip_diabetes": "Moderate carbs, steady blood sugar, high fiber, and balanced portions",
        "condition_tip_hypertension": "Low sodium (<2000mg/day), high potassium, and high fiber",
        "condition_tip_fat_loss": "Higher protein, controlled fat, quality carbs, and regular training",
        "fallback_comment_fat_ok": "Fat intake at {value:.1f}g stayed within the target range, which supports your goal well.",
        "fallback_comment_fat_low": "Fat intake was only {value:.1f}g, a bit lower than planned. A modest amount of healthy fat would help.",
        "fallback_comment_fat_high": "Fat intake reached {value:.1f}g, which is above target. Keep tomorrow lower-fat and simpler.",
        "fallback_comment_fiber_ok": "Fiber reached {value:.1f}g, which is a strong result for today.",
        "fallback_comment_fiber_low": "Fiber was only {value:.1f}g. Add more vegetables, beans, and whole grains tomorrow.",
        "fallback_comment_water_ok": "Hydration hit {value}ml and met the target.",
        "fallback_comment_water_low": "Hydration was only {value}ml, still short of the {target}ml target.",
        "fallback_comment_steps_high": "You reached {value} steps today, which is a strong activity level.",
        "fallback_comment_steps_mid": "You reached {value} steps today. Solid progress, but there is still room to move more.",
        "fallback_comment_steps_low": "You only logged {value} steps today. Add a walk or a short ride tomorrow.",
        "shortcoming_fat_low": "fat too low",
        "shortcoming_fat_high": "fat too high",
        "shortcoming_fiber_low": "fiber too low",
        "shortcoming_water_low": "water intake too low",
        "shortcoming_exercise_low": "exercise too low",
        "fallback_diet_1": "Breakfast (5 min): oatmeal + 2 egg whites + cucumber salad (300kcal)",
        "fallback_diet_2": "Lunch (10 min): rice + lean beef + steamed greens (450kcal)",
        "fallback_diet_3": "Dinner (10 min): mixed-grain porridge + tofu salad + sauteed vegetables (350kcal)",
        "fallback_water_1": "07:30 warm water after waking, 300ml",
        "fallback_water_2": "10:00 work-break water, 400ml",
        "fallback_water_3": "14:00 afternoon water, 400ml",
        "fallback_water_4": "17:00 before leaving work, 400ml",
        "fallback_water_5": "20:00 evening water, 300ml",
        "fallback_water_target": "Daily target: {target}ml",
        "fallback_exercise_1": "15-minute walk after breakfast",
        "fallback_exercise_2": "20-minute walk after dinner",
        "fallback_exercise_3": "Weekly goal: reach 150 active minutes",
        "fallback_note_fruits": "Suggested fruit today: {fruits}",
        "fallback_note_overeat": "There were signs of overeating yesterday. Keep meals around 70% fullness today.",
        "fallback_note_fat_low": "Fat was low yesterday. Add a small amount of healthy fat such as olive oil or nuts.",
        "fallback_note_fat_high": "Fat was high yesterday. Avoid deep-fried food, rich sauces, and heavy desserts today.",
        "fallback_note_fiber_low": "Fiber was low yesterday. Add more vegetables, beans, and whole grains today.",
        "fallback_note_exercise_low": "Activity was low yesterday. Schedule one light-to-moderate session today.",
        "weekly_ai_failed": "AI call failed: {error}",
        "weekly_fallback_review": "Weekly data collection completed. The overall trend looks stable. Keep building consistency.",
        "weekly_fallback_plan_1": "Keep daily hydration at or above 2000ml",
        "weekly_fallback_plan_2": "Add light movement after meals",
        "weekly_fallback_plan_3": "Keep fat intake controlled and meals regular",
    },
}

CONDITION_ALIASES = {
    "balanced": {"balanced", "general health", "general wellness", "none", "均衡健康", "无特殊状况"},
    "gallstones": {"gallstones", "gallstone", "胆结石"},
    "diabetes": {"diabetes", "diabetic", "糖尿病"},
    "hypertension": {"hypertension", "blood pressure", "high blood pressure", "高血压"},
    "fat_loss": {"fat loss", "fitness", "cutting", "leaning", "健身减脂", "减脂"},
}
GENDER_ALIASES = {
    "male": {"male", "man", "m", "男"},
    "female": {"female", "woman", "f", "女"},
}
MEAL_ALIASES = {
    "breakfast": {"breakfast", "早餐"},
    "lunch": {"lunch", "午餐"},
    "dinner": {"dinner", "晚餐"},
    "snack": {"snack", "snacks", "加餐"},
}
WATER_PERIOD_ALIASES = {
    "wake_up": {"wake-up", "wake up", "morning wake-up", "晨起", "早晨", "晨间"},
    "morning": {"morning", "上午"},
    "noon": {"noon", "midday", "中午"},
    "afternoon": {"afternoon", "下午"},
    "evening": {"evening", "night", "晚上", "晚间"},
}
EXERCISE_ALIASES = {
    "cycling": {"cycling", "bike", "biking", "骑行", "骑车"},
    "walking": {"walking", "walk", "散步", "步行"},
    "running": {"running", "run", "跑步"},
    "workout": {"workout", "strength", "training", "健身"},
    "yoga": {"yoga", "瑜伽"},
    "swimming": {"swimming", "swim", "游泳"},
    "other": {"exercise", "其他", "其他运动"},
}
EXCLUDE_SECTION_KEYWORDS = {
    "weight",
    "体重",
    "water",
    "hydration",
    "饮水",
    "meal",
    "meals",
    "diet",
    "food",
    "饮食",
    "exercise",
    "workout",
    "运动",
    "symptom",
    "symptoms",
    "不适",
    "症状",
    "goal",
    "target",
    "目标",
    "steps",
    "步数",
}

LANGUAGE_LABELS = {
    "zh-CN": "中文",
    "en-US": "English",
}

CONFIG_WIZARD_TEXTS = {
    "zh-CN": {
        "title": "欢迎使用 Health-Mate 配置向导",
        "intro": "这个向导会在几分钟内生成你的健康档案。",
        "start": "按 Enter 开始...",
        "language_prompt": "请选择语言（1 中文 / 2 English）",
        "language_retry": "请输入 1 或 2。",
        "name": "你的姓名或昵称？",
        "name_retry": "请输入姓名或昵称。",
        "gender": "性别（1 男 / 2 女）",
        "gender_retry": "请输入 1 或 2。",
        "age": "年龄",
        "age_retry": "请输入有效年龄数字。",
        "height": "身高（厘米，如 172）",
        "height_retry": "请输入有效身高数字。",
        "current_weight": "当前体重（公斤，如 65.5）",
        "current_weight_retry": "请输入有效体重数字。",
        "target_weight": "目标体重（公斤）",
        "target_weight_retry": "请输入有效目标体重数字。",
        "condition": "健康目标或状态（1 胆结石 / 2 糖尿病 / 3 高血压 / 4 健身减脂 / 5 均衡健康）",
        "condition_retry": "请输入 1-5。",
        "water_target": "每日饮水目标（ml）",
        "water_target_retry": "请输入有效的饮水目标数字。",
        "step_target": "每日步数目标",
        "step_target_retry": "请输入有效的步数目标数字。",
        "activity": "活动水平（1 久坐 / 2 轻度 / 3 中度 / 4 重度 / 5 运动员）",
        "activity_retry": "请输入 1-5。",
        "dislike": "不喜欢的食物（多个请用逗号分隔，没有可直接回车）",
        "allergies": "过敏食物（多个请用逗号分隔，没有可直接回车）",
        "saved": "配置完成，已写入：{path}",
        "summary": "已保存语言：{language}，健康目标：{condition}。",
        "next_step": "如需推送消息，请编辑 config/.env 填写 Webhook。",
    },
    "en-US": {
        "title": "Welcome to the Health-Mate setup wizard",
        "intro": "This wizard creates your health profile in a few minutes.",
        "start": "Press Enter to start...",
        "language_prompt": "Choose a language (1 Chinese / 2 English)",
        "language_retry": "Please enter 1 or 2.",
        "name": "Your name or nickname",
        "name_retry": "Please enter a name or nickname.",
        "gender": "Gender (1 Male / 2 Female)",
        "gender_retry": "Please enter 1 or 2.",
        "age": "Age",
        "age_retry": "Please enter a valid age.",
        "height": "Height in cm (for example 172)",
        "height_retry": "Please enter a valid height.",
        "current_weight": "Current weight in kg (for example 65.5)",
        "current_weight_retry": "Please enter a valid weight.",
        "target_weight": "Target weight in kg",
        "target_weight_retry": "Please enter a valid target weight.",
        "condition": "Condition or goal (1 Gallstones / 2 Diabetes / 3 Hypertension / 4 Fat Loss / 5 Balanced Wellness)",
        "condition_retry": "Please enter a number from 1 to 5.",
        "water_target": "Daily water target in ml",
        "water_target_retry": "Please enter a valid water target.",
        "step_target": "Daily step target",
        "step_target_retry": "Please enter a valid step target.",
        "activity": "Activity level (1 Sedentary / 2 Light / 3 Moderate / 4 Heavy / 5 Athlete)",
        "activity_retry": "Please enter a number from 1 to 5.",
        "dislike": "Foods to avoid (comma-separated, press Enter if none)",
        "allergies": "Allergies (comma-separated, press Enter if none)",
        "saved": "Configuration saved to: {path}",
        "summary": "Saved language: {language}, condition: {condition}.",
        "next_step": "If you want push delivery, edit config/.env and add your webhooks.",
    },
}

WEIGHT_MORNING_ALIASES = {
    "weight_morning": {
        "晨起空腹",
        "早晨空腹",
        "晨起体重",
        "空腹体重",
        "morning fasting",
        "fasting weight",
        "morning weight",
        "fasting body weight",
    }
}

WATER_AMOUNT_ALIASES = {
    "water_amount": {"饮水量", "water intake", "intake"},
}

CUMULATIVE_ALIASES = {
    "cumulative": {"累计", "cumulative"},
}

DISTANCE_ALIASES = {
    "distance": {"距离", "公里数", "distance"},
}

DURATION_ALIASES = {
    "duration": {"时间", "耗时", "时长", "duration", "time"},
}

CALORIE_BURN_ALIASES = {
    "burn": {"热量消耗", "消耗", "总消耗", "burn", "calories"},
}

STEP_LABEL_ALIASES = {
    "steps": {"总步数", "步数", "total steps", "steps"},
}

SYMPTOM_SECTION_ALIASES = {
    "symptoms": {"症状", "不适", "symptom", "symptoms"},
}

TIME_APPROX_PATTERN = r"[\(（](?:约|around)?\s*([\d:]+)[\)）]"
OVEREATING_PATTERN = r"(?:吃|感觉).{0,20}?(?:有点饱|过饱|吃撑|吃太饱)|(?:too full|overeat|overate|stuffed)"
SYMPTOM_KEYWORDS = [
    "右上腹涨",
    "腹涨",
    "腹胀",
    "腹痛",
    "涨痛",
    "不舒服",
    "恶心",
    "bloating",
    "nausea",
    "pain",
    "discomfort",
]
PLACEHOLDER_TOKENS = {
    "(待记录)",
    "（待记录）",
    "(pending)",
    "_（无记录）_",
}
MEAL_SKIP_KEYWORDS = {
    "总计",
    "评估",
    "蛋白质：",
    "脂肪：",
    "碳水：",
    "纤维：",
    "维生素",
    "total",
    "assessment",
    "protein:",
    "fat:",
    "carbs:",
    "fiber:",
}
PORTION_UNIT_PATTERN = r"(ml|g|个|碗|份|杯|片|slice|cup|serving|piece)"
WEIGHT_UNIT_PATTERN = r"(斤|kg|公斤|jin|lbs?|pounds?)"
DISTANCE_UNIT_PATTERN = r"(?:公里|km)"
MINUTE_UNIT_PATTERN = r"(?:分|分钟|min|minutes?)"
CALORIE_UNIT_PATTERN = r"(?:千卡|kcal|卡)"
STEP_UNIT_PATTERN = r"(?:步|steps?)"
APPROXIMATE_MARKERS = {"约", "approx.", "approx"}


def _normalize_token(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def resolve_locale(config: Optional[dict] = None, locale: Optional[str] = None) -> str:
    raw = locale or os.environ.get("HEALTH_MATE_LANG")
    if not raw and config:
        raw = (
            config.get("language")
            or config.get("locale")
            or config.get("user_profile", {}).get("language")
            or config.get("user_profile", {}).get("locale")
        )
    normalized = _normalize_token(raw)
    return LOCALE_ALIASES.get(normalized, raw if raw in SUPPORTED_LOCALES else DEFAULT_LOCALE)


def t(locale: Optional[str], key: str, **kwargs) -> str:
    resolved = resolve_locale(locale=locale)
    template = TEXTS.get(resolved, {}).get(key) or TEXTS[DEFAULT_LOCALE].get(key) or key
    return template.format(**kwargs)


def _canonicalize(value: Optional[str], mapping: Dict[str, Iterable[str]], default: str) -> str:
    token = _normalize_token(value)
    if not token:
        return default
    for canonical, aliases in mapping.items():
        if token == _normalize_token(canonical):
            return canonical
        if any(token == _normalize_token(alias) for alias in aliases):
            return canonical
    return default


def condition_key(value: Optional[str]) -> str:
    return _canonicalize(value, CONDITION_ALIASES, "balanced")


def gender_key(value: Optional[str]) -> str:
    return _canonicalize(value, GENDER_ALIASES, "male")


def meal_key(value: Optional[str]) -> str:
    return _canonicalize(value, MEAL_ALIASES, "snack")


def water_period_key(value: Optional[str]) -> str:
    return _canonicalize(value, WATER_PERIOD_ALIASES, "morning")


def exercise_key(value: Optional[str]) -> str:
    return _canonicalize(value, EXERCISE_ALIASES, "other")


def condition_name(locale: Optional[str], value: Optional[str]) -> str:
    return t(locale, f"condition_{condition_key(value)}")


def meal_name(locale: Optional[str], value: Optional[str]) -> str:
    return t(locale, f"meal_{meal_key(value)}")


def water_period_name(locale: Optional[str], value: Optional[str]) -> str:
    return t(locale, f"water_{water_period_key(value)}")


def exercise_name(locale: Optional[str], value: Optional[str]) -> str:
    return t(locale, f"exercise_{exercise_key(value)}")


def alias_pattern(mapping: Dict[str, Iterable[str]]) -> str:
    values = set()
    for canonical, aliases in mapping.items():
        values.add(canonical)
        values.update(aliases)
    return "|".join(sorted((re.escape(value) for value in values if value), key=len, reverse=True))


def has_excluded_section_keyword(header: str) -> bool:
    token = _normalize_token(header)
    return any(keyword in token for keyword in EXCLUDE_SECTION_KEYWORDS)


def wizard_text(locale: Optional[str], key: str) -> str:
    resolved = resolve_locale(locale=locale)
    return CONFIG_WIZARD_TEXTS.get(resolved, CONFIG_WIZARD_TEXTS[DEFAULT_LOCALE])[key]


def list_separator(locale: Optional[str]) -> str:
    return "、" if resolve_locale(locale=locale) == "zh-CN" else ", "


def and_more(locale: Optional[str]) -> str:
    return "等" if resolve_locale(locale=locale) == "zh-CN" else "and more"


def localized_recipe_query(locale: Optional[str], condition_display: str) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return f"{condition_display} quick low fat high protein meals 2026"
    return f"{condition_display} 低脂高蛋白快手菜谱 2026"


def localized_exercise_query(locale: Optional[str], condition_display: str) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return "desk stretching routine for sedentary workers 2026"
    return f"久坐人群办公室拉伸动作 {condition_display} 适合的运动 2026"


def extract_time_token(text: str) -> str:
    match = re.search(TIME_APPROX_PATTERN, text or "", re.IGNORECASE)
    return match.group(1) if match else ""


def strip_approximate_phrase(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"[(（]\s*(?:约|approx\.?)\s*[)）]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(?:约|approx\.?)$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"[，,]\s*(?:约|approx\.?)\s*[）)]", "）", text, flags=re.IGNORECASE)
    return re.sub(r"[(（]$", "", text).strip()


def strip_parenthetical_details(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"\s*[（(][^（）()]*[)）]\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def markdown_to_plain_text(text: str) -> str:
    plain = str(text or "").replace("\r\n", "\n")
    plain = re.sub(r"(?m)^\s*#{1,6}\s*", "", plain)
    plain = plain.replace("**", "")
    plain = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1: \2", plain)
    plain = re.sub(r"(?m)^\*\s+", "• ", plain)
    return plain.strip()


def weight_unit(locale: Optional[str]) -> str:
    return "斤" if resolve_locale(locale=locale) == "zh-CN" else "kg"


def format_weight(locale: Optional[str], kg_value: Optional[float], precision: int = 1) -> str:
    if kg_value is None:
        return t(locale, "not_recorded")
    if resolve_locale(locale=locale) == "zh-CN":
        return f"{kg_value * 2:.{precision}f}斤"
    return f"{kg_value:.{precision}f}kg"


def format_weight_delta(locale: Optional[str], kg_value: float, precision: int = 1) -> str:
    if resolve_locale(locale=locale) == "zh-CN":
        return f"{kg_value * 2:.{precision}f}斤"
    return f"{kg_value:.{precision}f}kg"


def convert_weight_to_kg(value: float, unit: str, assume_jin: bool = False) -> float:
    token = _normalize_token(unit)
    if token in {"斤", "jin"}:
        return value / 2
    if token in {"lb", "lbs", "pound", "pounds"}:
        return value / 2.2046226218
    if token in {"kg", "kilogram", "kilograms", "公斤"}:
        return value
    return value / 2 if assume_jin else value


def build_condition_tip(locale: Optional[str], condition: Optional[str], fat_min: float, fat_max: float, fiber_min: float) -> str:
    return t(locale, f"condition_tip_{condition_key(condition)}", fat_min=int(fat_min), fat_max=int(fat_max), fiber_min=int(fiber_min))


def build_ai_comment_prompt(locale: Optional[str], context: dict) -> str:
    resolved = resolve_locale(locale=locale)
    if resolved == "en-US":
        return f"""You are a professional personal nutrition coach. Review the following daily health data and write a warm but rigorous insight.

[Profile]
- Name: {context['user_name']}
- Condition / goal: {context['condition_name']}
- Nutrition principle: {context['diet_principle']}

[Today's data]
- Calories: {context['calories']:.0f} kcal
- Protein: {context['protein']:.1f}g
- Fat: {context['fat']:.1f}g (target: {context['fat_min']}-{context['fat_max']}g)
- Carbs: {context['carb']:.1f}g
- Fiber: {context['fiber']:.1f}g (target: >= {context['fiber_min']}g)
- Water: {context['water_total']}ml (target: {context['water_target']}ml)
- Exercise sessions: {context['exercise_count']}
- Steps: {context['steps']}
- Overeating factor: {context['overeating_factor']}
- Symptom keywords: {context['symptom_keywords']}

[Requirements]
1. Sound like a professional private nutrition coach.
2. Start with what went well, then call out the main health risks clearly.
3. Write at least 120 words.
4. Tie the advice to the user's condition or goal.
5. If there was overeating or symptoms, emphasize it.

Output only the insight text with no title or code block."""
    return f"""你是一位专业的私人营养师。请根据以下每日健康数据，输出一段专业但温暖的健康点评。

【用户档案】
- 称呼：{context['user_name']}
- 病理/目标：{context['condition_name']}
- 饮食原则：{context['diet_principle']}

【今日数据】
- 总热量：{context['calories']:.0f} kcal
- 蛋白质：{context['protein']:.1f}g
- 脂肪：{context['fat']:.1f}g（目标：{context['fat_min']}-{context['fat_max']}g）
- 碳水：{context['carb']:.1f}g
- 膳食纤维：{context['fiber']:.1f}g（目标：≥{context['fiber_min']}g）
- 饮水：{context['water_total']}ml（目标：{context['water_target']}ml）
- 运动次数：{context['exercise_count']}
- 步数：{context['steps']}
- 过饱系数：{context['overeating_factor']}
- 症状关键词：{context['symptom_keywords']}

【要求】
1. 语气专业、温暖、明确。
2. 先肯定亮点，再指出主要隐患。
3. 不少于 120 字。
4. 必须结合用户病理或目标。
5. 如果出现过饱或症状，需要重点提醒。

请直接输出点评正文，不要加标题或代码块。"""


def build_ai_comment_system_prompt(locale: Optional[str], condition: Optional[str]) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return f"You are a professional nutrition coach specialized in {condition_name(locale, condition)}."
    return f"你是一位专业营养师，擅长为{condition_name(locale, condition)}用户提供指导。"


def build_ai_plan_prompt(locale: Optional[str], context: dict) -> str:
    shortcomings = ", ".join(context["shortcomings"]) if context["shortcomings"] else ("none" if resolve_locale(locale=locale) == "en-US" else "无")
    if resolve_locale(locale=locale) == "en-US":
        return f"""You are a professional health planner. Build tomorrow's action plan for the user below.

[Profile]
- Name: {context['user_name']}
- Condition / goal: {context['condition_name']}
- Nutrition principle: {context['diet_principle']}
- Foods to avoid: {context['avoid_foods'] or 'none'}
- Preferred fruits: {context['favorite_fruits'] or 'none'}

[Today's gaps]
- {shortcomings}

[Search references]
- Recipe notes: {context['recipe_reference']}
- Exercise notes: {context['exercise_reference']}

[Output rules]
Return one valid JSON object only. Do not add markdown or commentary.
The JSON schema must be:
{{
  "diet": [{{"time": "08:00-09:00", "meal": "Breakfast", "menu": "Oatmeal and fruit", "calories": 300, "fat": 6, "fiber": 7}}],
  "water": [{{"time": "07:00-08:00", "amount": "300ml", "note": "Warm water after waking"}}],
  "exercise": [{{"time": "After dinner", "activity": "Walk", "duration": "20 minutes", "details": "Light digestion walk"}}],
  "notes": ["One key reminder"]
}}
Write the plan for {context['condition_name']} and keep it realistic and actionable."""
    return f"""你是一位专业健康规划师。请根据以下信息生成用户明日优化方案。

【用户档案】
- 称呼：{context['user_name']}
- 病理/目标：{context['condition_name']}
- 饮食原则：{context['diet_principle']}
- 不爱吃/过敏：{context['avoid_foods'] or '无'}
- 喜欢水果：{context['favorite_fruits'] or '无'}

【今日短板】
- {shortcomings}

【搜索参考】
- 菜谱参考：{context['recipe_reference']}
- 运动参考：{context['exercise_reference']}

【输出规则】
必须只输出一个合法 JSON 对象，绝对不要输出 Markdown 或解释。
格式必须如下：
{{
  "diet": [{{"time": "08:00-09:00", "meal": "早餐", "menu": "燕麦粥等", "calories": 300, "fat": 6, "fiber": 7}}],
  "water": [{{"time": "07:00-08:00", "amount": "300ml", "note": "晨起温水"}}],
  "exercise": [{{"time": "晚餐后", "activity": "散步", "duration": "20分钟", "details": "轻度助消化活动"}}],
  "notes": ["一条重点提醒"]
}}
请输出适用于{context['condition_name']}的明日方案。"""


def build_ai_plan_system_prompt(locale: Optional[str]) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return "You are a professional nutrition coach. Output one pure JSON object only."
    return "你是一位专业营养师。你只能输出一个纯 JSON 对象。"


def build_weekly_ai_prompt(locale: Optional[str], context: dict) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return f"""You are a professional weekly health reviewer. Based on the aggregated 7-day health data below, write a weekly review and next-week action plan.

Condition / goal: {context['condition_name']}
Step target: {context['step_target']}

[Weekly summary]
- Weight change: {context['weight_change']}
- Average daily calories: {context['avg_calories']:.0f} kcal
- Average daily water: {context['avg_water']:.0f} ml
- Average daily steps: {context['avg_steps']:.0f}
- Symptom events: {context['symptoms_count']}

Output in exactly two parts with no markdown code fence:

---review---
Write about 120-180 words. Mention what improved and what still needs work.

---plan---
- List 3 concrete actions for next week
"""
    return f"""你是一位专业的周度健康复盘专家。请根据以下 7 天聚合数据，输出一份周报复盘和下周计划。

病理/目标：{context['condition_name']}
目标步数：{context['step_target']}

【本周摘要】
- 体重变化：{context['weight_change']}
- 日均摄入热量：{context['avg_calories']:.0f} kcal
- 日均饮水量：{context['avg_water']:.0f} ml
- 日均步数：{context['avg_steps']:.0f}
- 不适症状次数：{context['symptoms_count']}

请严格按以下两部分输出，不要加代码块：

---review---
写 120-180 字左右的复盘，说明亮点和风险。

---plan---
- 列出 3 条下周可执行动作
"""


def build_weekly_ai_system_prompt(locale: Optional[str]) -> str:
    if resolve_locale(locale=locale) == "en-US":
        return "You are a professional health data analyst."
    return "你是一位专业健康数据分析师。"


def build_fallback_plan(locale: Optional[str], target_water: int, fruits: str) -> dict:
    return {
        "diet": [t(locale, "fallback_diet_1"), t(locale, "fallback_diet_2"), t(locale, "fallback_diet_3")],
        "water": [
            t(locale, "fallback_water_1"),
            t(locale, "fallback_water_2"),
            t(locale, "fallback_water_3"),
            t(locale, "fallback_water_4"),
            t(locale, "fallback_water_5"),
            t(locale, "fallback_water_target", target=target_water),
        ],
        "exercise": [t(locale, "fallback_exercise_1"), t(locale, "fallback_exercise_2"), t(locale, "fallback_exercise_3")],
        "notes": [t(locale, "fallback_note_fruits", fruits=fruits or "-")],
    }


def build_weekly_fallback(locale: Optional[str]) -> tuple[str, str]:
    return (
        t(locale, "weekly_fallback_review"),
        "\n".join(
            [
                f"- {t(locale, 'weekly_fallback_plan_1')}",
                f"- {t(locale, 'weekly_fallback_plan_2')}",
                f"- {t(locale, 'weekly_fallback_plan_3')}",
            ]
        ),
    )


def build_delivery_message(
    locale: Optional[str],
    body: str,
    pdf_url: str,
    report_kind: str,
    generated_at: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    pdf_label = t(locale, "delivery_daily_pdf" if report_kind == "daily" else "delivery_weekly_pdf")
    body_text = markdown_to_plain_text(body)
    lines = [body_text, "", "━━━━━━━━━━━━━━━━━━", "", pdf_label, pdf_url]
    if report_kind == "weekly" and start_date and end_date:
        lines.extend(["", "---", t(locale, "delivery_period", start_date=start_date, end_date=end_date)])
    if generated_at:
        lines.append(t(locale, "weekly_generated_at", value=generated_at))
    return "\n".join(lines).strip()
