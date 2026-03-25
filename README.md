English | [中文](README_ZH.md) | [日本語](README_JP.md)

# 🏥 Health-Mate | Local-First Intelligent Health Reporting for OpenClaw

> A production-ready multilingual health reporting system with dual-engine architecture.
>
> Transform local Markdown health memories into polished Daily, Weekly, and Monthly PDF reports with condition-aware scoring, specialty charts, medical planning, and optional webhook delivery.

[![Version](https://img.shields.io/badge/version-1.5.2-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
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

## 🚀 Automated Tracking Engine

Health-Mate integrates seamlessly with OpenClaw's scheduling system for zero-friction habit tracking.

### HEARTBEAT.md Integration

Configure proactive check-ins in `HEARTBEAT.md`:

```cron
# Daily health check-in reminder (8:00 - 21:00)
0 10,14,20 * * * /path/to/health_mate/scripts/heartbeat_reminder.sh
```

### Features:
- 🕐 **Smart Timing**: Reminders during natural break points (mid-morning, post-lunch, evening)
- 🔕 **Non-Intrusive**: Single consolidated message instead of multiple pings
- 📱 **Multi-Channel**: DingTalk, Feishu, Telegram, or Slack webhook delivery
- 📊 **Auto-Logging**: Check-ins automatically written to `MEMORY_DIR/YYYY-MM-DD.md`

### Example Heartbeat Flow:
1. **10:00** → Hydration reminder ("Current: 300ml/2000ml, keep going!")
2. **14:00** → Lunch check-in ("What did you eat? I'll review fat content")
3. **20:00** → Dinner + medication reminder
4. **22:00** → Daily PDF report auto-generated and pushed

---

## 🔒 Privacy & Local-First Design

Health-Mate is built around explicit privacy boundaries.

### What Stays Local (Default):
- 📁 **Markdown Parsing**: All health data extracted from local `MEMORY_DIR` files
- 📊 **Scoring & Charts**: Condition-aware scoring, statistical calculations, chart rendering
- 📄 **PDF Generation**: ReportLab renders PDFs entirely offline
- 📝 **LLM Commentary**: Local `openclaw agent --local` for AI insights (no cloud API required)

### What Requires Explicit Opt-In:
- 🌐 **Tavily Retrieval**: Only when `TAVILY_API_KEY` is configured (for hospital recommendations or fallback guidance)
- 📤 **Webhook Delivery**: Only when DingTalk/Feishu/Telegram credentials are set
- ⬇️ **Runtime Font Download**: Disabled by default; set `ALLOW_RUNTIME_FONT_DOWNLOAD=true` only if you explicitly allow it

### Recommended Deployment:
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

## 📥 Installation

```bash
# Clone repository
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate

# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python scripts/init_config.py
```

---

## 📄 Documentation

- [English README](README.md)
- [中文说明](README_ZH.md)
- [日本語ドキュメント](README_JP.md)
- [SKILL.md](SKILL.md) — OpenClaw skill specification

---

## 📞 Support

- **GitHub**: https://github.com/tankeito/Health-Mate
- **Issues**: https://github.com/tankeito/Health-Mate/issues
- **Email**: tqd354@gmail.com

---

**Health-Mate** | Local-First Multilingual Health Reporting System

**Developed by tankeito** | MIT License | 2026
