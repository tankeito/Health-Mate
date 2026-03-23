English | [中文](README_ZH.md) | [日本語](README_JP.md)

# 🏥 Health-Mate | Local-First Intelligent Health Reporting for OpenClaw

> A production-ready bilingual health reporting skill for OpenClaw.
>
> Track meals, hydration, exercise, symptoms, medication, and custom monitoring modules from local Markdown memories, then turn them into Daily, Weekly, and Monthly PDF reports with optional text push delivery.

[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 Why Health-Mate

Health-Mate sits between a simple habit tracker and a clinical self-management dashboard.

- 🧠 **Condition-aware**: Gallstones, hypertension, diabetes, fat loss, and mixed-condition management are supported out of the box.
- 📄 **Report-first**: It does not stop at logging. It generates polished Daily, Weekly, and Monthly reports with charts, summaries, and actionable follow-up guidance.
- 🔒 **Local-first privacy**: Parsing, scoring, fallback reasoning, and PDF rendering stay local by default.
- 🧩 **Expandable**: Add modules such as blood pressure, glucose, body fat, biochemistry, medication, or custom numeric monitoring through `user_config.json`.
- 🌐 **Multi-language**: Chinese, English, and Japanese report flows are supported, including an English-safe rendering path when Chinese or Japanese fonts are unavailable.

---

## 📑 Report Matrix

| Report | Focus | Key Output | Primary Question |
| --- | --- | --- | --- |
| 🌅 Daily Report | Same-day review | weighted scores, nutrition ring chart, hydration and exercise detail, risk alerts, next-day plan | How did today go, and what should change tomorrow? |
| 🗓 Weekly Report | Mid-cycle trend review | weekly overview, heatmaps, trend charts, strengths, gaps, next-week focus | What improved this week, and what keeps repeating? |
| 📊 Monthly Report | Deep condition review | macro radar, 30-day heatmap, weight/BMR trend, specialty charts, AI review, follow-up planning | Is the strategy working, and is offline follow-up or escalation needed? |

---

## ⚙️ How It Works

Health-Mate uses a layered local pipeline:

1. **Memory ingestion**
   OpenClaw converts daily conversational check-ins into structured Markdown and writes them into `MEMORY_DIR`.
2. **Robust parsing**
   Python extracts meals, hydration, weight, exercise, symptoms, medication, steps, and custom monitoring sections from that Markdown.
3. **Condition-aware scoring**
   Targets, weights, and warning thresholds adapt to the user’s primary condition and mixed-condition constraints.
4. **Insight and delivery**
   LLM output is used when available. If it fails, Health-Mate falls back to local rules and optional Tavily retrieval, then renders PDF and optional text push messages.

---

## 🧬 Supported Management Modes

- Gallstones / chronic cholecystitis
- Hypertension
- Diabetes
- Fat loss / body-composition management
- Mixed-condition management with a primary condition and multiple active constraints

What changes by mode:

- nutrition and hydration targets
- scoring emphasis and weight distribution
- AI prompts and fallback rules
- weekly / monthly follow-up logic
- specialty chart selection
- monthly clinic and hospital recommendation strategy

---

## 🏥 Monthly Medical Planning

The Monthly Report contains a dedicated medical-planning section.

Recommendation priority:

1. **LLM-first recommendation**
   The system first asks the local LLM for hospital-first recommendations in this order:
   top-tier tertiary hospital > tertiary hospital > regional medical center.
2. **Tavily evidence fallback**
   If LLM output is missing or too weak, Tavily is used to collect local hospital candidates.
3. **Local-rule fallback**
   If both LLM and Tavily are unavailable, the report still outputs a structured local fallback. Where curated city-level knowledge exists, it still prefers real hospital plus doctor combinations instead of generic clinic placeholders.

What the monthly recommendation block aims to include:

- hospital name
- department
- doctor name and title
- hospital strengths
- doctor specialty
- patient-fit reason

Design goals:

- hospital-first routing rather than vague department-only suggestions
- strong preference for public top-tier tertiary hospitals
- stronger prioritization of university-affiliated and nationally recognized centers
- prefer real named doctors and titles whenever enough evidence exists
- condition-fit reasoning that references symptoms, follow-up needs, and mixed-condition risk

---

## 📊 Report Highlights

### Daily PDF

- weighted overall score and module breakdown
- nutrition intake chart
- hydration detail
- exercise detail
- medication and custom monitoring sections when enabled
- AI commentary, risk alerts, and next-day plan

### Weekly PDF

- weekly metrics overview
- symptom and medication heatmap
- weight, calorie, nutrition, hydration, and step trends
- strengths, attention points, and next-week focus
- custom monitoring summary

### Monthly PDF

- macro adherence radar
- symptom and medication heatmap
- 30-day weight and BMR trend
- condition-specific specialty charts
- AI monthly review
- follow-up reminders
- hospital and clinic recommendations

Specialty chart examples:

- gallstones: fat intake vs symptom frequency, intake spread, and a symptom-composition donut chart
- hypertension: blood-pressure boxplot
- diabetes: glucose trend
- fat loss: smoothed weight and body-fat trend
- custom monitoring: numeric trend charts from user-defined modules

---

## 🔒 Privacy and Security

Health-Mate is built around explicit boundaries.

- `MEMORY_DIR` is required and must be set explicitly
- there is no implicit fallback memory path
- parsing, scoring, and PDF rendering are local by default
- outbound requests happen only when you explicitly enable:
  - webhook delivery
  - Tavily retrieval
  - runtime font download

Recommended operational posture:

- run inside a virtual environment or container
- point `MEMORY_DIR` only to the intended health-memory directory
- keep webhook and Tavily credentials unset if you do not need them
- pre-install the Chinese font to avoid runtime font download

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Recommended in `config/.env`:

```bash
MEMORY_DIR="/absolute/path/to/health-memory"
OPENCLAW_BIN="/root/.nvm/versions/node/v22.22.0/bin/openclaw" # Optional but recommended for cron
TAVILY_API_KEY="tvly-..."                  # Optional
DINGTALK_WEBHOOK="https://..."             # Optional
FEISHU_WEBHOOK="https://..."               # Optional
TELEGRAM_BOT_TOKEN="..."                   # Optional
TELEGRAM_CHAT_ID="..."                     # Optional
REPORT_WEB_DIR="/var/www/html/reports"     # Optional
REPORT_BASE_URL="https://example.com/reports"
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. Run the Setup Wizard

```bash
python scripts/init_config.py
```

The wizard writes all persistent settings into `config/user_config.json`, including:

- profile basics
- active conditions and primary condition
- scoring modules and weights
- medication participation
- residence used by monthly medical planning
- custom monitoring modules
- report and AI-generation preferences

### 4. Generate Reports

```bash
python scripts/daily_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. Optional Shell Runners

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

If your scheduled shell does not inherit the interactive Node/NVM `PATH`, set `OPENCLAW_BIN` in `config/.env`. The daily runner and Python controller both use it as the first-choice resolver for local LLM execution.
If `OPENCLAW_BIN` is not set, the Python runner still tries common install locations such as `/root/.nvm/versions/node/*/bin/openclaw`, `/usr/local/bin/openclaw`, `/usr/bin/openclaw`, and the standard Windows Node.js path. The shell runners themselves do not hardcode any fixed PATH.

### 6. Optional English Memory Mirror

```bash
python scripts/export_memory_en.py
```

Use this when you want:

- an English mirror of local memory files
- an English rendering path when Chinese fonts are unavailable
- bilingual regression checks for report output

---

## ⚙️ Configuration Reference

### `config/user_config.json`

This is the main long-term profile file. It stores:

- user profile
- active conditions and primary condition
- enabled score modules and weights
- medication settings
- residence metadata
- custom monitoring modules
- report preferences
- AI-generation preferences

### Common Runtime Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `MEMORY_DIR` | Yes | Points to the health-memory directory |
| `TAVILY_API_KEY` | No | Enables Tavily retrieval fallback |
| `DINGTALK_WEBHOOK` | No | Pushes text summary and PDF link to DingTalk |
| `FEISHU_WEBHOOK` | No | Pushes text summary and PDF link to Feishu |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | No | Pushes text summary and PDF link to Telegram |
| `REPORT_WEB_DIR` | No | Copies generated PDFs to a web directory |
| `REPORT_BASE_URL` | No | Builds public PDF URLs for push messages |
| `ALLOW_RUNTIME_FONT_DOWNLOAD` | No | Allows runtime font download |

---

## 📝 Memory Write Protocol

When an assistant writes into `MEMORY_DIR`, it must behave like a strict recorder.

Hard rules:

- no commentary
- no encouragement
- no summaries
- no emoji
- no chat filler

Structural rules:

- meals, hydration, medication, and exercise events must use level-3 headings with time markers
- hydration blocks must stay minimal and stable
- daily step totals must stay inside a dedicated level-2 section
- custom monitoring modules must keep stable level-2 section names
- avoid mixing languages inside one data block

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

Forbidden content:

- `Assessment`
- `Status`
- `Summary`
- motivational filler
- debug logs
- system logs

---

## 🔤 Font Fallback

Preferred CJK fonts:

- `assets/NotoSansSC-VF.ttf`
- `assets/NotoSansJP-VF.ttf`

If one of the required fonts is missing:

- the renderer can switch to an English-safe rendering path
- the PDF adds a rendering notice
- Chinese PDF users should place `NotoSansSC-VF.ttf` into `assets/`
- Japanese PDF users should place `NotoSansJP-VF.ttf` into `assets/`

Repository:

- [Health-Mate on GitHub](https://github.com/tankeito/Health-Mate)

---

## 🧪 Troubleshooting

### `MEMORY_DIR` missing

- shell runners now stop immediately
- set `MEMORY_DIR` explicitly in `config/.env` or your runtime environment

### Monthly hospital recommendations are too generic

- make sure residence is configured in `config/user_config.json`
- confirm local LLM execution is available if you want doctor-level planning
- configure `TAVILY_API_KEY` if you want retrieval-enhanced fallback
- if LLM is temporarily unavailable, the city-specific local-rule layer will still try to prefer real hospital plus doctor combinations where curated data exists

### Chinese / Japanese PDF falls back to English

- the required CJK font is probably missing
- place `assets/NotoSansSC-VF.ttf` or `assets/NotoSansJP-VF.ttf` locally and regenerate

### Push delivery is missing

- check whether the corresponding webhook variables are configured
- inspect `logs/` for runtime delivery output

---

## 📌 Changelog

### v1.5.0 — 2026-03-23

- 🧹 Removed the legacy `scripts/health_report_pro.py` and `scripts/pdf_generator.py` wrappers. `daily_health_report_pro.py` and `daily_pdf_generator.py` are now the only daily entry points.
- 🇯🇵 Completed the Japanese setup/reporting path, including `ja-JP` setup-wizard support and English-fallback notices when `NotoSansJP-VF.ttf` is missing.
- ⏰ Clarified cron-safe local LLM resolution through `OPENCLAW_BIN` with env-first behavior and common-path auto-discovery.

### v1.4.1 — 2026-03-22

- 🇯🇵 Added `ja-JP` locale wiring, Japanese font support, and the `export_memory_jp.py` helper.
- 🛠 Renamed the canonical daily entry points to `daily_health_report_pro.py` and `daily_pdf_generator.py`.
- ⏰ Hardened local LLM resolution for cron-style shells through `OPENCLAW_BIN` and fallback binary discovery.

### v1.4.0 — 2026-03-21

- 📊 Added the Monthly Report workflow with specialty deep-dive charts
- 🏥 Added residence-aware follow-up reminders and clinic / hospital planning
- 🌡 Added weekly and monthly symptom / medication heatmaps
- 🔒 Removed implicit `MEMORY_DIR` fallback behavior
- 🧠 Improved local-rule fallback for failed LLM generation
- 🌐 Strengthened bilingual rendering and English-safe fallback

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

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

## 📬 Support

- GitHub Issues: [https://github.com/tankeito/Health-Mate/issues](https://github.com/tankeito/Health-Mate/issues)
- Repository: [https://github.com/tankeito/Health-Mate](https://github.com/tankeito/Health-Mate)
