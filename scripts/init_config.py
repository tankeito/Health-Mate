#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive configuration wizard for Health-Mate."""

import json
from pathlib import Path

from i18n import LANGUAGE_LABELS, condition_name, wizard_text

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_DIR.mkdir(exist_ok=True)

LANGUAGE_OPTIONS = {"1": "zh-CN", "2": "en-US"}
GENDER_OPTIONS = {"1": "male", "2": "female"}
CONDITION_OPTIONS = {
    "1": "gallstones",
    "2": "diabetes",
    "3": "hypertension",
    "4": "fat_loss",
    "5": "balanced",
}
ACTIVITY_OPTIONS = {
    "1": 1.2,
    "2": 1.375,
    "3": 1.55,
    "4": 1.725,
    "5": 1.9,
}
def prompt_text(locale: str, key: str) -> str:
    return wizard_text(locale, key)


def ask(locale: str, key: str, retry_key: str, cast=str):
    while True:
        raw = input(f"{prompt_text(locale, key)}\n> ").strip()
        if cast is str and raw:
            return raw
        if cast is int:
            if raw.isdigit():
                return int(raw)
        if cast is float:
            try:
                return float(raw)
            except ValueError:
                pass
        print(prompt_text(locale, retry_key))


def ask_optional_list(locale: str, key: str):
    raw = input(f"{prompt_text(locale, key)}\n> ").strip()
    return [part.strip() for part in raw.split(",") if part.strip()]


print("=" * 60)
print("Health-Mate Setup / Health-Mate Configuration Wizard")
print("=" * 60)
print(f"1. Chinese / {LANGUAGE_LABELS['zh-CN']}")
print("2. English")

language_choice = input("> ").strip()
while language_choice not in LANGUAGE_OPTIONS:
    print(f"{wizard_text('zh-CN', 'language_retry')} / {wizard_text('en-US', 'language_retry')}")
    language_choice = input("> ").strip()

locale = LANGUAGE_OPTIONS[language_choice]
print()
print(prompt_text(locale, "title"))
print(prompt_text(locale, "intro"))
input(f"{prompt_text(locale, 'start')}\n")

name = ask(locale, "name", "name_retry")

gender_choice = input(f"{prompt_text(locale, 'gender')}\n> ").strip()
while gender_choice not in GENDER_OPTIONS:
    print(prompt_text(locale, "gender_retry"))
    gender_choice = input("> ").strip()

age = ask(locale, "age", "age_retry", cast=int)
height = ask(locale, "height", "height_retry", cast=int)
current_weight = ask(locale, "current_weight", "current_weight_retry", cast=float)
target_weight = ask(locale, "target_weight", "target_weight_retry", cast=float)

condition_choice = input(f"{prompt_text(locale, 'condition')}\n> ").strip()
while condition_choice not in CONDITION_OPTIONS:
    print(prompt_text(locale, "condition_retry"))
    condition_choice = input("> ").strip()

water_target = ask(locale, "water_target", "water_target_retry", cast=int)
step_target = ask(locale, "step_target", "step_target_retry", cast=int)

activity_choice = input(f"{prompt_text(locale, 'activity')}\n> ").strip()
while activity_choice not in ACTIVITY_OPTIONS:
    print(prompt_text(locale, "activity_retry"))
    activity_choice = input("> ").strip()

dislikes = ask_optional_list(locale, "dislike")
allergies = ask_optional_list(locale, "allergies")

config = {
    "language": locale,
    "user_profile": {
        "name": name,
        "gender": GENDER_OPTIONS[gender_choice],
        "age": age,
        "height_cm": height,
        "current_weight_kg": current_weight,
        "target_weight_kg": target_weight,
        "condition": CONDITION_OPTIONS[condition_choice],
        "activity_level": ACTIVITY_OPTIONS[activity_choice],
        "water_target_ml": water_target,
        "step_target": step_target,
        "dietary_preferences": {
            "dislike": dislikes,
            "allergies": allergies,
            "favorite_fruits": [],
        },
    },
    "condition_standards": {
        "gallstones": {"fat_min_g": 40, "fat_max_g": 50, "fiber_min_g": 25, "water_min_ml": 2000},
        "diabetes": {"fat_min_g": 40, "fat_max_g": 55, "fiber_min_g": 30, "water_min_ml": 2000},
        "hypertension": {"fat_min_g": 40, "fat_max_g": 55, "fiber_min_g": 25, "water_min_ml": 2000, "sodium_max_mg": 2000},
        "fat_loss": {"fat_min_g": 40, "fat_max_g": 60, "fiber_min_g": 25, "water_min_ml": 2500},
        "balanced": {"fat_min_g": 40, "fat_max_g": 60, "fiber_min_g": 25, "water_min_ml": 2000},
    },
    "scoring_weights": {
        "diet": 0.45,
        "water": 0.35,
        "weight": 0.20,
        "exercise_bonus": 0.10,
    },
    "exercise_standards": {
        "weekly_target_minutes": 150,
    },
}

config_path = CONFIG_DIR / "user_config.json"
with open(config_path, "w", encoding="utf-8") as handle:
    json.dump(config, handle, ensure_ascii=False, indent=4)

condition_label = condition_name(locale, CONDITION_OPTIONS[condition_choice])
print()
print(prompt_text(locale, "saved").format(path=config_path))
print(prompt_text(locale, "summary").format(language=LANGUAGE_LABELS[locale], condition=condition_label))
print(prompt_text(locale, "next_step"))
