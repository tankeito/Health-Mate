[Chinese Guide](README_ZH.md)

# Health-Mate

> Local-first bilingual health reporting for OpenClaw.

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

## Overview

Health-Mate turns structured Markdown health logs into polished PDF reports.

- Daily report: scoring, nutrition, hydration, exercise, medication, AI insight, risk alerts, next-day plan
- Weekly report: summary rings, symptom and medication heatmap, trend charts, nutrition chart, weekly review, next-week actions
- Monthly report: macro radar, symptom heatmap, 30-day weight and BMR trend, specialty charts, AI monthly review, follow-up reminders, clinic suggestions
- Multi-condition support: gallstones, hypertension, diabetes, fat loss, and mixed-condition management
- Custom modules: medication tracking, monitoring sections, and user-defined scoring modules from `user_config.json`
- Font fallback: when the bundled Chinese font is missing, the project can render an English fallback report with an explicit notice

## What Changed In 1.4.0

- Added monthly PDF reporting with specialty deep-dive charts
- Added weekly symptom and medication heatmap output
- Added monthly 30-day weight and estimated BMR trend output
- Added monthly symptom distribution and fat/carb boxplot output
- Added residence-aware monthly follow-up reminders and hospital planning
- Added stronger local fallback logic so reports still react to the real data when LLM generation fails
- Removed implicit `MEMORY_DIR` fallback behavior from the shell runners; the directory must now be set explicitly

## Report Output

### Daily PDF

- Overall score and weighted module scores
- Meal, hydration, exercise, and medication detail sections
- AI insight with local fallback
- Risk alerts
- Action plan for tomorrow

### Weekly PDF

- Weekly overview rings
- Symptom and medication heatmap
- Weight, calorie, nutrition, step, and hydration charts
- Strengths, gaps, and next-week focus
- Additional monitoring summary

### Monthly PDF

- Page 1: macro adherence radar, symptom and medication heatmap, 30-day weight and BMR trend
- Page 2: condition-specific charts such as gallstone fat-vs-symptom trend, blood-pressure boxplot, glucose trend, body-fat trend, or custom metric charts
- Page 3: AI monthly review, follow-up reminders, and residence-aware hospital suggestions

## Quick Start

### 1. Install

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. Configure Runtime Environment

Create `config/.env` or set environment variables in your own runtime:

```bash
MEMORY_DIR="/absolute/path/to/health-memory"
```

Optional integrations:

```bash
TAVILY_API_KEY="tvly-..."
DINGTALK_WEBHOOK="https://..."
FEISHU_WEBHOOK="https://..."
TELEGRAM_BOT_TOKEN="..."
TELEGRAM_CHAT_ID="..."
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://example.com/reports"
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

Important:

- `MEMORY_DIR` is required
- shell runners stop immediately if `MEMORY_DIR` is missing
- outbound requests happen only when Tavily or webhook credentials are configured, or when runtime font download is explicitly enabled

### 3. Run The Setup Wizard

```bash
python scripts/init_config.py
```

The wizard writes all persistent settings into `config/user_config.json`, including:

- profile basics
- multiple conditions and primary condition
- scoring modules and weights
- medication participation
- custom monitoring modules
- residence fields used by monthly follow-up and clinic planning

### 4. Generate Reports

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

Shell runners:

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

### 5. Optional English Mirror

If you want an English memory mirror or an English-only rendering path, use:

```bash
python scripts/export_memory_en.py
```

This script is part of the project and should stay under version control.

## Font Behavior

Preferred Chinese font path:

- `assets/NotoSansSC-VF.ttf`

If the font is missing:

- the report can switch to an English-compatible rendering path
- the PDF adds a rendering notice
- users who need Chinese PDF output should download the font from the project repository and place it at `assets/NotoSansSC-VF.ttf`

Repository:

- [Health-Mate on GitHub](https://github.com/tankeito/Health-Mate)

## Memory Write Protocol

When an assistant writes into `MEMORY_DIR`, it must behave like a strict recorder.

Hard rules:

- never write commentary, coaching, summaries, emoji, or chat filler into the memory file
- meals, hydration, medication events, and exercise events must use level-3 headings with time markers
- hydration blocks must stay minimal
- step totals must stay inside one dedicated level-2 block
- monitoring modules must use stable level-2 section headings
- keep one language per block

Example:

```markdown
# 2026-03-20 Health Log

## Weight Record
- Morning fasting: 64.4kg

## Hydration
### Morning (around 08:45)
- Water intake: 300ml
- Cumulative: 300ml/2000ml

## Meals
### Breakfast (around 08:50)
- Oatmeal 50g -> approx. 190kcal
- Skim milk 250ml -> approx. 87kcal

## Exercise
### Afternoon Cycling (around 17:10)
- Distance: 10.2km
- Duration: 42min
- Burn: approx. 290kcal

## Today Steps
- Total steps: 8200 steps
```

Expandable monitoring modules:

```markdown
## Blood Pressure
### Morning (around 08:00)
- Blood Pressure: 128/82 mmHg
- Heart Rate: 72 bpm

## Glucose Record
### After Breakfast (around 10:10)
- Glucose: 7.1 mmol/L
- Timing: 2h after breakfast

## Body Composition
- Weight: 64.4kg
- Body Fat: 18.6%

## Biochemistry
- ALT: 34 U/L
- AST: 28 U/L
```

Forbidden content:

- `Assessment`
- `Status`
- `Summary`
- motivational filler
- debug logs
- system logs
- tables inside daily memory files

## Runtime Safety

Expected local behavior:

- reads Markdown logs from `MEMORY_DIR`
- reads `config/.env` when shell runners are used
- writes PDFs into `reports/`
- writes logs into `logs/`
- may create a temporary English memory mirror for rendering fallback

Expected network behavior:

- Tavily only when `TAVILY_API_KEY` is configured
- webhook delivery only when the corresponding webhook credentials are configured
- runtime font download only when `ALLOW_RUNTIME_FONT_DOWNLOAD=true`

## Changelog

### v1.4.0 - 2026-03-21

- Added monthly reporting
- Added symptom and medication heatmaps to weekly and monthly reports
- Added monthly specialty charts and weight/BMR trend output
- Added residence-aware medical planning
- Refreshed README, README_ZH, SKILL metadata, and package metadata
