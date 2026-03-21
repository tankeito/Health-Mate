English | [中文](README_ZH.md)

# 🏥 Health-Mate | Personal Intelligent Health Assistant

> Your intelligent health companion, exclusively designed for OpenClaw
> *Transform daily habits into clinical-grade insights. Precisely track nutrition, hydration, exercise, and pathology indicators. Automatically render SaaS-grade professional PDF reports including Daily, Weekly, and Monthly—while keeping all data 100% locally private.*

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 Project Overview

Health-Mate is a **production-ready bilingual health management skill** that bridges the gap between casual fitness tracking apps and clinical chronic disease monitoring systems.

---

## ⚙️ How It Works

A robust three-stage local processing pipeline:

1. **Data Ingestion (NLP to Markdown)**: OpenClaw LLM transforms daily conversational check-ins into strictly-formatted Markdown text that complies with regex patterns, saved to `MEMORY_DIR`.

2. **Dynamic Pathology Calculation Engine (Python)**: High-fault-tolerance regex extracts nutrition, hydration, and exercise vectors. underlying algorithms dynamically adjust scoring weights and red-line thresholds based on your **primary pathology goal** (e.g., gallstones mode enforces 40g fat cap, fat-loss mode emphasizes calorie deficit).

3. **Rendering & Distribution Engine**: `Matplotlib` renders dry matrices into beautiful HD PDFs (Daily/Weekly/Monthly), with optional auto-push to DingTalk/Feishu/Telegram via Webhook.

---

## 📑 Clinical-Grade SaaS Report Presentation

Fully offline-rendered commercial-grade medical visualization reports. Health-Mate transforms raw Markdown text into structurally rigorous HD PDFs:

- 📅 **Daily Health Report (Granular Tracking)**: Transforms your daily check-ins into a panoramic snapshot. Includes multi-dimensional star ratings, exquisite macronutrient ring charts, 24-hour hydration timelines, and AI-targeted next-day action plans.

- 🗓 **Weekly Health Report (Trends & Review)**: Designed for mid-term health review. Introduces geek-style GitHub-like symptom & medication heatmaps, 7-day weight & calorie trend lines, and deep LLM-powered weekly pattern recognition.

- 📊 **Monthly Health Report (Pathology Deep Dive)**: The crown jewel rivaling top commercial medical SaaS. Features macro-compliance radar charts, 30-day BMR smoothing curves, pathology dual-axis comparison charts (visually presenting fat intake vs. symptom frequency causality), nutrient dispersion box plots, and LBS-based intelligent local hospital/clinic planning recommendations.

---

## ⚠️ Privacy & Security Closed-Loop

Health-Mate adheres to an absolute "data localization" principle.

- 🔒 **No Cloud Upload**: All parsing, AI inference fallback, and PDF rendering complete locally by default.
- 📂 **Strict Memory Isolation**: `MEMORY_DIR` must be explicitly specified. To prevent unauthorized reading of global Agent memory, scripts will intercept and exit if this path is unconfigured—no implicit fallback.
- 📡 **Isolated External Requests**: External network requests only trigger when you actively configure Webhook, Tavily API, or enable runtime font download.

---

## ✨ Core Features

- 📈 **SaaS-Grade Visual Reports**: Powerful Daily, Weekly, and Monthly PDF generation powered by Matplotlib.
- 🏥 **Residence-Aware Medical Planning (NEW)**: Automatically generates follow-up reminders and local clinic/hospital suggestions based on your configured city and active conditions.
- 🤖 **Dynamic Pathology Engine**: Supports Gallstones, Hypertension, Diabetes, Fat loss, and mixed-condition management with customized LLM expert commentary.
- 🧩 **Custom Monitoring**: Seamlessly inject custom modules (e.g., Biochemistry, Blood Pressure) via user_config.json.
- 🌐 **Bilingual & Font-Safe**: Full EN/CN parity. Automatically renders an English fallback report with a notice if local Chinese fonts are missing.

---

## 🚀 Quick Start

### 1. Install & Configure
```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. Environment Variables (config/.env)
```bash
MEMORY_DIR="/absolute/path/to/health-memory" # 👈 REQUIRED!
TAVILY_API_KEY="tvly-..." # Optional: Enhanced AI search
DINGTALK_WEBHOOK="https://..." # Optional: Push delivery
ALLOW_RUNTIME_FONT_DOWNLOAD="false" # Optional: Font fallback
```

### 3. Setup Wizard
```bash
python scripts/init_config.py
```
*Generates user_config.json including your profile, active conditions, custom scoring modules, and residence for hospital planning.*

### 4. Generate Reports
```bash
# Daily, Weekly, and Monthly triggers
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

---

## 📝 Memory Write Protocol

When an assistant writes into MEMORY_DIR, it must behave like a strict, emotionless data recorder. No commentary, no emoji, no chat filler.

<details>
<summary><b>👉 Click to expand the exact Markdown template the LLM must generate</b></summary>

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

## Medication
- Medicine A: 1 pill
```
</details>

---

## 🔗 Changelog

### v1.4.0 — 2026-03-21
- 📅 **Monthly System**: Added full monthly PDF workflow with radar charts, 30-day BMR/Weight trends, and condition-specific deep dives.
- 🗺 **Medical Planning**: Added residence-aware hospital suggestions and follow-up reminders.
- 🌡 **Heatmaps**: Introduced GitHub-style symptom & medication heatmaps for weekly/monthly overviews.
- 🔒 **Security**: Removed implicit MEMORY_DIR fallback; paths must now be explicitly declared.
- 🛡 **Robustness**: Enhanced local fallback logic for when LLM generation fails.

### v1.3.0 — 2026-03-20
- 🌐 Bilingual Architecture: Added i18n.py for unified Chinese/English language layer
- 📝 Memory Protocol: Hardened anti-commentary rules with CN/EN templates
- 🔧 Parsing Improvements: Enhanced bilingual meal, hydration, exercise block detection
- 🎨 PDF Fixes: Resolved emoji rendering issues (☒ squares) in PDF output
- 💊 Medication Tracking: Added support for custom modules (e.g., 用药记录)

### v1.2.0 — 2026-03-20
- 🎯 Dynamic Targets: Refactored condition parameters for flexible health goals (e.g., fat loss)
- 🌍 Multi-Language Docs: Added bilingual documentation and custom module support
- 🧹 Strict Protocol: Rewrote Memory Write Protocol to lock down LLM output
- 🐛 Bug Fixes: Fixed PDF emoji rendering and parsing error tolerance

---

## 📦 Project Structure

```
health-mate/
├── scripts/
│   ├── health_report_pro.py          # Daily report generator
│   ├── weekly_report_pro.py          # Weekly report generator
│   ├── monthly_report_pro.py         # Monthly report generator (NEW)
│   ├── pdf_generator.py              # Daily PDF rendering engine
│   ├── weekly_pdf_generator.py       # Weekly PDF renderer
│   ├── monthly_pdf_generator.py      # Monthly PDF renderer (NEW)
│   ├── i18n.py                       # Bilingual language layer
│   ├── constants.py                  # Food calorie database
│   ├── init_config.py                # Interactive setup wizard
│   ├── daily_health_report_pro.sh    # Cron job script (daily)
│   ├── weekly_health_report_pro.sh   # Cron job script (weekly)
│   └── monthly_health_report_pro.sh  # Cron job script (monthly) (NEW)
├── config/
│   ├── user_config.json              # User health profile
│   ├── .env                          # Environment variables (gitignored)
│   ├── .env.example                  # Environment template
│   ├── pdf_style_config.json         # PDF styling configuration
│   └── user_config.example.json      # Profile template
├── assets/
│   └── NotoSansSC-VF.ttf             # Chinese font (auto-downloaded)
├── logs/                             # Execution logs
├── reports/                          # Generated PDF reports
├── README.md                         # English documentation
├── README_ZH.md                      # Chinese documentation
├── SKILL.md                          # OpenClaw skill definition
└── requirements.txt                  # Python dependencies
```

---

## 📄 License

MIT License – See [LICENSE](LICENSE) for details.

---

## 📞 Support & Resources

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **Maton Documentation**: https://maton.ai/docs
- **Google Docs API**: https://developers.google.com/workspace/docs/api
- **Email**: tqd354@gmail.com

---

## 🙏 Acknowledgments

- **Maton** – For providing the OAuth-managed API gateway
- **Google Workspace** – For the powerful Docs API
- **OpenClaw** – For the AI assistant platform
