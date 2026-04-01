English | [中文](README_ZH.md) | [日本語](README_JP.md)

# 🏥 Health-Mate | Local-First Intelligent Health Reporting for OpenClaw

> A production-ready multilingual health reporting system with dual-engine architecture.
>
> Transform local Markdown health memories into polished Daily, Weekly, and Monthly PDF reports with condition-aware scoring, specialty charts, medical planning, and optional webhook delivery.

[![Version](https://img.shields.io/badge/version-1.5.4-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 Why Health-Mate

Health-Mate sits between a simple habit tracker and a clinical self-management dashboard.

- 🧠 **Condition-Aware**: Gallstones, hypertension, diabetes, fat loss, and mixed-condition management supported out of the box
- 📄 **Report-First**: Generates polished Daily, Weekly, and Monthly PDFs with charts, insights, and actionable guidance
- 🔒 **Local-First Privacy**: Parsing, scoring, fallback reasoning, and PDF rendering stay local by default
- 🧩 **Expandable**: Add blood pressure, glucose, body fat, biochemistry, medication, or custom numeric monitoring via `user_config.json`
- 🌐 **Multilingual Support**: Full support for Chinese, English, and Japanese (`zh-CN`, `en-US`, `ja-JP`) with automatic font fallback and locale-aware medical typesetting

---

## 📊 Three Report Types: What Problems Do They Solve

### 🌅 Daily Report — Same-Day Review & Next-Day Micro-Adjustment

**Answers**: *"How did today go, and what should I change tomorrow?"*

**Core Modules**:
- 📊 **Dynamic Nutrition Ring Chart**: Macro adherence visualization (protein, fat, carbs, fiber)
- 📈 **Intake Stacked Bar**: Meals, hydration, and exercise displayed in layered timeline
- ⚠️ **Risk Alerts**: Condition-specific warnings (e.g., fat too low for gallstones, sodium too high for hypertension)
- 📋 **Next-Day Action Plan**: Concrete, executable adjustments for tomorrow (specific foods, water targets, movement goals)

**When to Use**: Daily reflection, immediate behavior correction, maintaining momentum

---

### 🗓 Weekly Report — Habit Formation & Short-Term Fluctuation Analysis

**Answers**: *"Which behaviors stabilized, and which problems keep repeating?"*

**Core Modules**:
- 🎯 **Weekly Metrics Radar**: Multi-dimension overview (calories, macros, hydration, steps, sleep if tracked)
- 🔥 **Habit & Exercise Heatmap**: GitHub-style contribution graph for `balanced` / `fat_loss` modes
- 📉 **Dual-Axis Trend Charts**: Weight + calorie balance, steps + hydration, symptom frequency + trigger exposure
- 🏥 **Disease Mode**: Symptom-medication correlation heatmap for chronic conditions
- 💪 **Fitness Mode**: Four-week habit progression bars, energy balance waterfall chart
- 📝 **Strengths & Gaps**: What improved, what needs attention next week

**When to Use**: Weekly review, identifying patterns, adjusting strategy before monthly checkpoint

---

### 📊 Monthly Report — Deep Analysis & Long-Term Strategy

**Answers**: *"Is my current strategy effective? Do I need offline follow-up or escalated intervention?"*

**Core Modules**:
- 🎯 **Macro Adherence Radar**: 30-day nutritional pattern overview
- 🔥 **Activity Heatmap**: Full-month GitHub-style graph (lifestyle mode) or symptom-medication heatmap (disease mode)
- 📈 **30-Day Weight & BMR Trend**: Smoothed curve with annotations for significant events
- 🏥 **Specialty Charts**: Condition-specific deep-dive visualizations
- 🧠 **AI Monthly Review**: LLM-generated synthesis of trends, risks, and recommendations
- 🏥 **Medical Planning Section** (Disease Mode Only):
  - Hospital-first recommendations (top-tier tertiary > tertiary > regional center)
  - Department and doctor matching with specialty alignment
  - Follow-up reminders based on condition guidelines
- 🏃 **Lifestyle Intervention List** (Fitness Mode Only):
  - Next-month macro and training adjustments
  - Body composition goals (LBM vs fat mass)
  - Habit stacking recommendations

**When to Use**: Monthly strategic review, medical follow-up planning, major course corrections

---

## 🧬 Dual-Engine Dynamic Population Branching

Health-Mate intelligently switches its underlying report engine based on the `population_branch` setting in `user_config.json`.

### 🏥 Disease Management Mode

**Activated When**: `gallstones`, `hypertension`, `diabetes`, or other chronic conditions

**Report Characteristics**:
- 🩺 **Pathophysiology-Aligned Charts**: Fat intake vs symptom frequency (gallstones), BP boxplot (hypertension), glucose trend (diabetes)
- 💊 **Medication Adherence Analysis**: Dose timing, missed doses, correlation with symptoms
- ⚠️ **High-Risk Food Trigger Identification**: Foods correlated with symptom flare-ups
- 🏥 **Hospital & Doctor Recommendations** (Monthly Only):
  - LLM-generated structured suggestions (hospital → department → doctor)
  - Tavily retrieval fallback for evidence-based local candidates
  - Preference for public top-tier tertiary hospitals and university-affiliated centers
  - Real doctor names and titles when evidence is sufficient

**Example Output** (Gallstones Monthly Report):
- Fat intake vs symptom frequency dual-axis chart
- Fat/carb intake dispersion boxplot
- Symptom composition donut chart
- Hospital recommendation: "Sichuan Provincial People's Hospital → Hepatobiliary Surgery → Dr. Zhou Yongbi (Chief Physician)"

---

### 🏃 Fitness & Wellness Mode

**Activated When**: `balanced`, `fat_loss`, or general health optimization

**Report Characteristics**:
- 📊 **De-Medicalized Visualization**: No symptom tracking, no hospital recommendations
- 🔥 **Four-Week Habit Progression**: Stacked bar showing consistency across key behaviors
- ⚖️ **Energy Balance Waterfall**: Calorie intake vs expenditure vs deficit/surplus
- 💪 **Body Composition Deep-Dive**: LBM (Lean Body Mass) vs fat mass trend, body fat percentage smoothing
- 🎯 **Next-Month Macro & Training Plan**:
  - Protein target adjustment for muscle preservation
  - Carb timing around workouts
  - Training volume progression (sets, reps, intensity)

**Example Output** (Fat Loss Monthly Report):
- 30-day weight trend with smoothed curve
- Body fat percentage trend
- Energy balance waterfall chart
- Four-week habit progression (steps, workouts, protein intake, sleep)
- Next-month intervention: "Increase protein to 2.0g/kg, add 2 resistance sessions, maintain 500kcal deficit"

---

## ⚙️ Core Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **PDF Rendering** | ReportLab 4.0+ | Professional-grade PDF generation with custom styling, multi-language font support, and precise layout control |
| **Data Visualization** | Matplotlib 3.0+ | Statistical charts (radar, heatmap, boxplot, dual-axis trends) with condition-specific styling |
| **LLM Integration** | OpenClaw Local Agent + Tavily API | Hybrid reasoning: local LLM for AI commentary and hospital recommendations, Tavily for evidence-based web retrieval fallback |
| **Scheduling** | Cron + OpenClaw HEARTBEAT | Automated daily/weekly/monthly report generation with optional DingTalk/Feishu/Telegram push delivery |

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

ClawHub manual folder upload may omit `config/.env.example`. Open `config/user_config.example.json` and review the top-level `env` block as an upload-safe reference.

The setup wizard creates a commented project-local `config/.env` template when the file does not exist.

Direct Python entry points also auto-load project-local `config/.env` when present, so manual script runs stay aligned with the shell runners.

```bash
# ========== Cron Environment Variables (Required for scheduled tasks) ==========
NVM_DIR="/root/.nvm"
CRON_PATH="/root/.nvm/versions/node/v22.22.0/bin:/root/.local/bin:/root/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/usr/local/bin:/usr/bin:/bin:/root/.npm-global/bin"

# ========== Required Configuration ==========
MEMORY_DIR="/root/.openclaw/workspace/memory"

# ========== Optional Configuration ==========
OPENCLAW_BIN="/root/.nvm/versions/node/v22.22.0/bin/openclaw"  # Recommended for cron
LOG_FILE="/root/.openclaw/logs/health_report_pro.log"

# Messaging (Optional)
DINGTALK_WEBHOOK="https://..."
FEISHU_WEBHOOK="https://..."
TELEGRAM_BOT_TOKEN="..."
TELEGRAM_CHAT_ID="..."

# AI Features (Optional)
TAVILY_API_KEY="tvly-..."

# PDF Report (Optional)
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://example.com/reports"

# Font Download (Default: false)
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. Run the Setup Wizard

```bash
python scripts/init_config.py
```

The wizard writes all persistent settings into `config/user_config.json`:
- Profile basics
- Active conditions and primary condition
- Scoring modules and weights
- Medication settings
- Residence (used by monthly medical planning)
- Custom monitoring modules
- `report_preferences.population_branch` (lifestyle vs disease routing)
- Report and AI-generation preferences

### 4. Generate Reports

```bash
# Daily Report
python scripts/daily_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20

# Weekly Report
python scripts/weekly_report_pro.py 2026-03-20

# Monthly Report
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. Optional Shell Runners (for Cron)

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

**Cron Environment Note**: If your scheduled shell does not inherit the interactive Node/NVM `PATH`, set `OPENCLAW_BIN` in `config/.env`. The daily runner and Python controller both use it as the first-choice resolver for local LLM execution.

If `OPENCLAW_BIN` is not set, the Python runner tries common install locations:
- `/root/.nvm/versions/node/*/bin/openclaw`
- `/usr/local/bin/openclaw`
- `/usr/bin/openclaw`
- Windows standard Node.js path

### 6. Optional English Memory Mirror

```bash
python scripts/export_memory_en.py
```

Use this when you want:
- An English mirror of local memory files
- An English rendering path when Chinese fonts are unavailable
- Bilingual regression checks for report output

---

## ⚙️ Configuration Reference

### `config/user_config.json`

Main long-term profile file storing:
- User profile
- Active conditions and primary condition
- Enabled score modules and weights
- Medication settings
- Residence metadata
- Custom monitoring modules
- Report preferences
- AI-generation preferences

**Important**: `report_preferences.population_branch`
- Supported values: `lifestyle` / `disease`
- Example config starts with `lifestyle`
- Setup wizard auto-suggests `lifestyle` for `balanced` / `fat_loss`, and `disease` for disease-management goals

### Common Runtime Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `MEMORY_DIR` | Yes | Points to the health-memory directory |
| `TAVILY_API_KEY` | No | Enables Tavily retrieval fallback |
| `DINGTALK_WEBHOOK` | No | Pushes text summary and PDF link to DingTalk |
| `FEISHU_WEBHOOK` | No | Pushes text summary and PDF link to Feishu |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | No | Pushes text summary and PDF link to Telegram |
| `REPORT_WEB_DIR` | No | Copies generated PDFs to a web directory |
| `REPORT_BASE_URL` | No | Builds public PDF URLs for push messages |
| `ALLOW_RUNTIME_FONT_DOWNLOAD` | No | Allows runtime font download (default: false) |

---

## 📝 Memory Write Protocol

When an assistant writes into `MEMORY_DIR`, it must behave like a **strict recorder**.

### Hard Rules

- ❌ No commentary
- ❌ No encouragement
- ❌ No summaries
- ❌ No emoji
- ❌ No chat filler

### Structural Rules

- ✅ Meals, hydration, medication, and exercise events must use **level-3 headings** with time markers (e.g., `### Breakfast (around 08:50)`)
- ✅ Hydration blocks must stay minimal and stable (only intake + cumulative)
- ✅ Daily step totals must stay inside a **dedicated level-2 section** (`## Today Steps`)
- ✅ Custom monitoring modules must keep stable level-2 section names
- ✅ Avoid mixing languages inside one data block

### Minimal Example

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

### Expandable Monitoring Modules

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

### Forbidden Content

- `Assessment`
- `Status`
- `Summary`
- Motivational filler
- Debug logs
- System logs

---

## 🔤 Font Fallback

### Preferred CJK Fonts

- `assets/NotoSansSC-VF.ttf` (Chinese)
- `assets/NotoSansJP-VF.ttf` (Japanese)

### If Required Font is Missing

- The renderer switches to an English-safe rendering path
- The PDF adds a rendering notice
- **Chinese PDF users**: Place `NotoSansSC-VF.ttf` into `assets/`
- **Japanese PDF users**: Place `NotoSansJP-VF.ttf` into `assets/`

---

## 🧪 Troubleshooting

### `MEMORY_DIR` Missing

**Symptoms**: Shell runners stop immediately with error

**Solution**:
- Set `MEMORY_DIR` explicitly in `config/.env` or your runtime environment
- For ClawHub manual uploads, copy the `MEMORY_DIR` example from `config/user_config.example.json` → `env`

### Monthly Hospital Recommendations Are Too Generic

**Symptoms**: Hospital suggestions lack specific doctor names or feel templated

**Solution**:
1. Make sure residence is configured in `config/user_config.json`
2. Confirm local LLM execution is available (set `OPENCLAW_BIN` for cron)
3. Configure `TAVILY_API_KEY` for retrieval-enhanced fallback
4. If LLM is unavailable, the city-specific local-rule layer still tries to prefer real hospital + doctor combinations where curated data exists

### Chinese / Japanese PDF Falls Back to English

**Symptoms**: PDF renders in English despite Chinese/Japanese content

**Solution**:
- Required CJK font is missing
- Place `assets/NotoSansSC-VF.ttf` or `assets/NotoSansJP-VF.ttf` locally and regenerate

### Push Delivery Is Missing

**Symptoms**: Report generated but no DingTalk/Feishu/Telegram message received

**Solution**:
- Check whether the corresponding webhook variables are configured in `config/.env`
- Inspect `logs/` directory for runtime delivery output
- Verify webhook URLs are valid and not expired

---

## 🔒 Privacy & Local-First Design

Health-Mate is built around explicit privacy boundaries.


### What Stays Local (Default)

- 📁 **Markdown Parsing**: All health data extracted from local `MEMORY_DIR` files
- 📊 **Scoring & Charts**: Condition-aware scoring, statistical calculations, chart rendering
- 📄 **PDF Generation**: ReportLab renders PDFs entirely offline
- **LLM Commentary**: Local `openclaw agent --local` for AI insights (no cloud API required)
- **LLM Output Sanitization**: Plugin-registration logs are stripped before AI commentary is embedded into text pushes or PDFs

### What Requires Explicit Opt-In

- 🌐 **Tavily Retrieval**: Only when `TAVILY_API_KEY` is configured (for hospital recommendations or fallback guidance)
- 📤 **Webhook Delivery**: Only when DingTalk/Feishu/Telegram credentials are set
- ⬇️ **Runtime Font Download**: Disabled by default; set `ALLOW_RUNTIME_FONT_DOWNLOAD=true` only if you explicitly allow it

### Recommended Deployment

```bash
# Use virtual environment or container isolation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Explicitly set MEMORY_DIR to a private directory
export MEMORY_DIR="$HOME/.health-mate/memory"

# Do NOT configure webhook or Tavily unless needed
# Leave TAVILY_API_KEY and WEBHOOK_URLs unset for maximum privacy
```

---

## 📁 Project Structure

```text
health-mate/
├── scripts/
│   ├── daily_report_pro.py
│   ├── weekly_report_pro.py
│   ├── monthly_report_pro.py
│   ├── daily_pdf_generator.py
│   ├── weekly_pdf_generator.py
│   ├── monthly_pdf_generator.py
│   ├── i18n.py
│   ├── init_config.py
│   ├── export_memory_en.py
│   ├── export_memory_jp.py
│   ├── daily_health_report_pro.sh
│   ├── weekly_health_report_pro.sh
│   └── monthly_health_report_pro.sh
├── config/
│   ├── user_config.json
│   ├── user_config.example.json
│   ├── .env
│   └── pdf_style_config.json
├── assets/
│   ├── NotoSansSC-VF.ttf
│   └── NotoSansJP-VF.ttf
├── logs/
├── reports/
├── README.md
├── README_ZH.md
├── README_JP.md
├── SKILL.md
├── _meta.json
└── requirements.txt
```

---

## 📬 Support

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **Repository**: https://github.com/tankeito/Health-Mate
- **Email**: tqd354@gmail.com

---

**Health-Mate** | Local-First Multilingual Health Reporting System

**Developed by tankeito** | MIT License | 2026
