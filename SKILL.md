---
name: health-mate
display_name: Health-Mate
version: 1.5.0
type: python/app
description: "Executable OpenClaw health-report skill with Chinese, English, and Japanese report flows. It reads Markdown logs from an explicitly configured MEMORY_DIR, generates daily, weekly, and monthly PDF reports, and only performs Tavily, webhook, or font-download network activity when the corresponding runtime options are enabled."
install: pip install -r requirements.txt
capabilities:
  - file_read
  - file_write
  - pdf_generation
  - http_request
metadata:
  openclaw:
    emoji: "🏥"
    homepage: "https://github.com/tankeito/Health-Mate"
  clawdbot:
    requires:
      env:
        - MEMORY_DIR
env:
  MEMORY_DIR: Required. Explicitly set this to the Markdown health-memory directory that the skill may read.
  OPENCLAW_BIN: Optional. Absolute path to the local `openclaw` binary, recommended for cron or minimal-PATH shells.
  HEALTH_MATE_LANG: Optional. Force the output locale such as `zh-CN`, `en-US`, or `ja-JP`.
  TAVILY_API_KEY: Optional. Enables Tavily-assisted fallback guidance and monthly clinic lookup hints.
  DINGTALK_WEBHOOK: Optional. Enables DingTalk delivery.
  FEISHU_WEBHOOK: Optional. Enables Feishu delivery.
  TELEGRAM_BOT_TOKEN: Optional. Enables Telegram delivery when paired with TELEGRAM_CHAT_ID.
  TELEGRAM_CHAT_ID: Optional. Required only for Telegram delivery.
  REPORT_WEB_DIR: Optional. Local directory used when generated PDFs should be copied for public download.
  REPORT_BASE_URL: Optional. Public base URL used for generated PDF links.
  ALLOW_RUNTIME_FONT_DOWNLOAD: Optional. Disabled by default. Set to true only if runtime fallback download of NotoSansSC-VF.ttf is explicitly allowed.
---

# Health-Mate

Health-Mate is an executable OpenClaw skill, not a prompt-only package.

It reads structured Markdown logs from `MEMORY_DIR`, generates localized PDF reports, and can optionally deliver the final message to external services.

## What It Does

- Parses meals, hydration, exercise, symptoms, medication, and custom monitoring sections
- Generates daily reports with scoring, detail sections, AI insight, risk alerts, and next-day actions
- Generates weekly reports with rings, heatmap, trend charts, nutrition chart, weekly review, and next-week plan
- Generates monthly reports with radar, heatmap, 30-day weight and BMR trend, specialty charts, follow-up reminders, and clinic suggestions
- Supports multi-condition management in both LLM and local fallback paths
- Keeps core parsing, scoring, and PDF rendering local

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:

- `reportlab`
- `pillow`
- `matplotlib`

## Required Runtime Setup

Required:

- `MEMORY_DIR`

Optional:

- `TAVILY_API_KEY`
- `DINGTALK_WEBHOOK`
- `FEISHU_WEBHOOK`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `REPORT_WEB_DIR`
- `REPORT_BASE_URL`
- `ALLOW_RUNTIME_FONT_DOWNLOAD`

## Upgrade And Backup Notice

Before upgrading or reinstalling this skill, back up:

- `config/user_config.json`
- `config/.env`
- any local font file you manually placed under `assets/`

Important:

- some platform upgrade or reinstall flows may overwrite, reset, or remove local configuration files
- after an upgrade, re-check `MEMORY_DIR`, report preferences, scoring modules, webhook settings, and Tavily settings before running scheduled jobs again

## Local And Network Behavior

Expected local file I/O:

- reads Markdown logs from `MEMORY_DIR`
- reads `config/.env` when shell runners are used
- writes PDFs into `reports/`
- writes logs into `logs/`
- may create a temporary English memory mirror for rendering fallback

Expected network I/O:

- Tavily only when `TAVILY_API_KEY` is configured
- webhook delivery only when the matching delivery credentials are configured
- runtime font download only when `ALLOW_RUNTIME_FONT_DOWNLOAD=true`

Important:

- there is no implicit default `MEMORY_DIR` fallback in the shell runners
- the skill exits if `MEMORY_DIR` is missing
- if `OPENCLAW_BIN` is configured, the shell runners expose its directory to `PATH`; if it is not configured, the Python layer still tries common install paths without hardcoding a fixed cron `PATH`

## Commands

- `/health`
  Daily report

- `/health summary`
  Weekly report

- `/health month`
  Monthly report

## Memory Write Protocol

When writing into `MEMORY_DIR`, the model must act like a strict recorder.

Hard rules:

1. Never write commentary, advice, summaries, emoji, or chat filler into the file.
2. Meals, hydration, medication events, and exercise events must use level-3 headings with time markers.
3. Hydration blocks must remain minimal and structured.
4. Step totals must stay in one dedicated level-2 block.
5. Monitoring modules must use stable level-2 headings.
6. Use one language per block.

Core template:

```markdown
# 2026-03-20 Health Log

## Meals
### Breakfast (around 08:30)
- Oatmeal 50g -> approx. 190kcal
- Skim milk 250ml -> approx. 87kcal

## Hydration
### Morning (around 09:45)
- Water intake: 300ml
- Cumulative: 300ml/2000ml

## Exercise
### Afternoon Cycling (around 17:17)
- Distance: 10km
- Duration: 47min
- Burn: approx. 300kcal

## Today Steps
- Total steps: 8500 steps
```

Chinese core template:

```markdown
# 2026-03-20 健康记录

## 体重记录
- 晨起空腹：64.4kg

## 饮水记录
### 上午（约 08:45）
- 饮水量：300ml
- 累计：300ml/2000ml

## 饮食记录
### 早餐（约 08:50）
- 燕麦片 50g -> 约 190kcal
- 脱脂牛奶 250ml -> 约 87kcal

## 运动记录
### 下午骑行（约 17:10）
- 距离：10.2km
- 耗时：42min
- 消耗：约 290kcal

## 今日步数
- 总步数：8200 步

## 用药记录
- 胆舒胶囊：1 粒
```

Chinese monitoring-module constraints:

- `## 血压记录` / `## 血糖记录` / `## 体成分` / `## 生化记录` must stay as stable level-2 titles
- numeric monitoring blocks should use stable item labels such as `- 血压：128/82 mmHg`, `- 血糖：7.1 mmol/L`, `- ALT：34 U/L`
- do not mix commentary into monitoring blocks
- do not turn monitoring blocks into tables
- do not rename the same monitoring module on different days unless the user intentionally changed the module name

Recommended LLM instruction:

- paste the English or Chinese template above directly into your system prompt, `soul.md`, or memory-write policy so the model stays inside the parser-safe structure
- if custom modules are enabled in `user_config.json`, add their exact section titles to the LLM write protocol and keep those titles stable across days

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
- debug notes
- system logs
- tables inside daily memory files

## Monthly Report Expectations

The monthly report now includes:

- macro adherence radar
- healthy-day donut chart based on the full calendar month
- symptom and medication heatmap
- 30-day weight and BMR trend
- condition-specific specialty charts
- AI monthly review
- follow-up reminders
- residence-aware hospital-and-doctor suggestions with grouped recommendations, grades, booking hints, and optional fee / schedule fields

If the user manages multiple conditions, the monthly report should combine them instead of collapsing to a single narrow perspective.

## Font Fallback

Preferred CJK font paths:

- `assets/NotoSansSC-VF.ttf`
- `assets/NotoSansJP-VF.ttf`

If one of them is missing:

- the skill may switch to an English-compatible rendering path
- the output adds a rendering notice
- users who need Chinese PDF output should place `NotoSansSC-VF.ttf` into `assets/`
- users who need Japanese PDF output should place `NotoSansJP-VF.ttf` into `assets/`

## Changelog

### v1.5.0 - 2026-03-23

- Removed the legacy `scripts/health_report_pro.py` and `scripts/pdf_generator.py` wrappers
- Extended `init_config.py` to cover `ja-JP`
- Clarified env-first local LLM resolution through `OPENCLAW_BIN` and common-path auto-discovery
- Added explicit Japanese font fallback guidance and English-fallback notice behavior

### v1.4.0 - 2026-03-21

- Added monthly reporting
- Added weekly and monthly symptom and medication heatmaps
- Added monthly weight and BMR trend output
- Added residence-aware monthly medical planning
- Refreshed README, README_ZH, SKILL metadata, and package metadata
