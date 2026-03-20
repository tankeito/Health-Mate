#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Weekly report controller for Health-Mate."""

import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta


def console_print(*args, sep=" ", end="\n", file=sys.stdout, flush=False):
    """Print safely even when the active terminal encoding cannot render CJK text."""
    text = sep.join(str(arg) for arg in args) + end
    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        buffer = getattr(file, "buffer", None)
        if buffer is not None:
            buffer.write(text.encode(encoding, errors="replace"))
        else:
            file.write(text.encode("ascii", errors="backslashreplace").decode("ascii"))
    if flush:
        file.flush()


print = console_print

from health_report_pro import (
    REPORTS_DIR,
    calculate_diet_score,
    get_condition_standards,
    load_user_config,
    parse_memory_file,
    validate_environment,
)
from i18n import (
    build_delivery_message,
    build_weekly_ai_prompt,
    build_weekly_ai_system_prompt,
    build_weekly_fallback,
    condition_name,
    format_weight_delta,
    resolve_locale,
    t,
)
from weekly_pdf_generator import generate_weekly_pdf_report

validate_environment()

MEMORY_DIR = os.environ.get("MEMORY_DIR", "/root/.openclaw/workspace/memory")


def get_week_dates(target_date_str):
    """Return the Monday-to-Sunday date list for the target date."""
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    monday = target_date - timedelta(days=target_date.weekday())
    return [(monday + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(7)]


def aggregate_weekly_data(week_dates, config):
    """Collect one week of metrics from the daily markdown files."""
    standards = get_condition_standards(config, config.get("user_profile", {}).get("condition", "balanced"))
    scoring_standards = config.get("scoring_standards", {})

    weekly_data = {
        "start_date": week_dates[0],
        "end_date": week_dates[-1],
        "dates": week_dates,
        "weights": [],
        "water_intakes": [],
        "steps": [],
        "calories": [],
        "protein": [],
        "fat": [],
        "carb": [],
        "symptoms_count": 0,
        "diet_scores": [],
    }

    first_weight = None
    last_weight = None

    for date_str in week_dates:
        file_path = os.path.join(MEMORY_DIR, f"{date_str}.md")
        daily_data = parse_memory_file(file_path)

        weight_value = daily_data.get("weight_morning")
        weekly_data["weights"].append(weight_value)
        if weight_value:
            if first_weight is None:
                first_weight = weight_value
            last_weight = weight_value

        weekly_data["water_intakes"].append(daily_data.get("water_total", 0))
        weekly_data["steps"].append(daily_data.get("steps", 0))
        weekly_data["calories"].append(daily_data.get("total_calories", 0))
        weekly_data["protein"].append(daily_data.get("total_protein", 0))
        weekly_data["fat"].append(daily_data.get("total_fat", 0))
        weekly_data["carb"].append(daily_data.get("total_carb", 0))

        if daily_data.get("symptom_keywords"):
            weekly_data["symptoms_count"] += len(daily_data["symptom_keywords"])
        if daily_data.get("meals"):
            weekly_data["diet_scores"].append(calculate_diet_score(daily_data, standards, scoring_standards))

    valid_weights = [value for value in weekly_data["weights"] if value]
    weekly_data["avg_weight"] = sum(valid_weights) / len(valid_weights) if valid_weights else 0
    weekly_data["weight_change"] = (last_weight - first_weight) if (last_weight is not None and first_weight is not None) else 0
    weekly_data["avg_calories"] = sum(weekly_data["calories"]) / 7
    weekly_data["avg_protein"] = sum(weekly_data["protein"]) / 7
    weekly_data["avg_fat"] = sum(weekly_data["fat"]) / 7
    weekly_data["avg_carb"] = sum(weekly_data["carb"]) / 7
    weekly_data["avg_diet_score"] = sum(weekly_data["diet_scores"]) / len(weekly_data["diet_scores"]) if weekly_data["diet_scores"] else 0
    return weekly_data


def get_ai_weekly_insights(weekly_data, profile, locale):
    """Generate weekly review text and action items."""
    prompt = build_weekly_ai_prompt(
        locale,
        {
            "condition_name": condition_name(locale, profile.get("condition", "balanced")),
            "step_target": profile.get("step_target", 8000),
            "weight_change": format_weight_delta(locale, weekly_data["weight_change"]),
            "avg_calories": weekly_data["avg_calories"],
            "avg_water": sum(weekly_data["water_intakes"]) / 7,
            "avg_steps": sum(weekly_data["steps"]) / 7,
            "symptoms_count": weekly_data["symptoms_count"],
        },
    )
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--local", "--to", "+860000000000", "--message", prompt],
            capture_output=True,
            text=True,
            timeout=90,
            env={**os.environ, "SYSTEM_PROMPT": build_weekly_ai_system_prompt(locale)},
        )
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            review_parts = output.split("---plan---")
            review = review_parts[0].replace("---review---", "").strip()
            plan = review_parts[1].strip() if len(review_parts) > 1 else ""
            if review:
                return review, plan
    except Exception as error:
        print(t(locale, "weekly_ai_failed", error=error), file=sys.stderr)
    return build_weekly_fallback(locale)


def generate_weekly_text_report(weekly_data, profile, ai_review, ai_plan, locale):
    """Render the weekly text message body."""
    avg_water = sum(weekly_data["water_intakes"]) / 7
    avg_steps = sum(weekly_data["steps"]) / 7
    summary_lines = [
        f"## {t(locale, 'weekly_text_heading', start_date=weekly_data['start_date'], end_date=weekly_data['end_date'])}",
        "",
        f"### {t(locale, 'weekly_summary_title')}",
        f"- {t(locale, 'weekly_avg_weight_change', value=format_weight_delta(locale, weekly_data['weight_change']))}",
        f"- {t(locale, 'weekly_avg_calories_line', value=weekly_data['avg_calories'])}",
        f"- {t(locale, 'weekly_avg_water_line', value=avg_water)}",
        f"- {t(locale, 'weekly_avg_steps_line', value=avg_steps)}",
        f"- {t(locale, 'weekly_symptom_count_line', value=weekly_data['symptoms_count'])}",
        "",
        f"### {t(locale, 'weekly_review_section')}",
        ai_review.strip(),
        "",
        f"### {t(locale, 'weekly_plan_section')}",
        ai_plan.strip() if ai_plan.strip() else f"- {t(locale, 'weekly_fallback_plan_1')}",
    ]
    return "\n".join(summary_lines).strip()


def publish_weekly_pdf(local_pdf_path):
    """Copy the weekly PDF to the optional web directory and return the delivery URL."""
    web_dir = os.environ.get("REPORT_WEB_DIR", "")
    base_url = os.environ.get("REPORT_BASE_URL", "").rstrip("/")
    if web_dir and os.path.exists(web_dir) and base_url:
        filename = os.path.basename(local_pdf_path)
        web_pdf_path = os.path.join(web_dir, filename)
        shutil.copy2(local_pdf_path, web_pdf_path)
        return f"{base_url}/{filename}"
    return local_pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 weekly_report_pro.py <YYYY-MM-DD>")
        sys.exit(1)

    target_date = sys.argv[1]
    config = load_user_config()
    locale = resolve_locale(config)
    profile = config.get("user_profile", {})

    week_dates = get_week_dates(target_date)
    weekly_data = aggregate_weekly_data(week_dates, config)
    ai_review, ai_plan = get_ai_weekly_insights(weekly_data, profile, locale)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_filename = f"weekly_report_{timestamp}.pdf"
    local_output_path = os.path.join(REPORTS_DIR, pdf_filename)

    generate_weekly_pdf_report(weekly_data, profile, ai_review, ai_plan, local_output_path, locale=locale)
    pdf_url = publish_weekly_pdf(local_output_path)
    text_report = generate_weekly_text_report(weekly_data, profile, ai_review, ai_plan, locale)
    delivery_message = build_delivery_message(
        locale=locale,
        body=text_report,
        pdf_url=pdf_url,
        report_kind="weekly",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        start_date=weekly_data["start_date"],
        end_date=weekly_data["end_date"],
    )

    print("=== TEXT_REPORT_START ===")
    print(text_report)
    print("=== TEXT_REPORT_END ===")
    print("=== PDF_URL ===")
    print(pdf_url)
    print("=== DELIVERY_MESSAGE_START ===")
    print(delivery_message)
    print("=== DELIVERY_MESSAGE_END ===")
