---
name: health-mate
display_name: Health-Mate
version: 1.3.1
type: python/app
description: "Executable bilingual OpenClaw health-report skill with local Python scripts for markdown parsing, PDF generation, and optional webhook delivery."
install: pip install -r requirements.txt
capabilities:
  - file_read
  - file_write
  - pdf_generation
  - http_request
metadata:
  clawdbot:
    requires:
      env:
        - MEMORY_DIR
env:
  MEMORY_DIR: Required. Explicitly set this to the markdown health-memory directory to be read by the skill.
  TAVILY_API_KEY: Optional. Used only for extra recipe and exercise research when generating next-day suggestions.
  DINGTALK_WEBHOOK: Optional. If set, the final report payload can be sent to DingTalk.
  FEISHU_WEBHOOK: Optional. If set, the final report payload can be sent to Feishu.
  TELEGRAM_BOT_TOKEN: Optional. If set together with TELEGRAM_CHAT_ID, the final report payload can be sent to Telegram.
  TELEGRAM_CHAT_ID: Optional. Required only when Telegram delivery is enabled.
  REPORT_WEB_DIR: Optional. Local directory where generated PDFs can be copied for public serving.
  REPORT_BASE_URL: Optional. Public base URL used to build downloadable PDF links.
---

# Health-Mate

Health-Mate is an executable OpenClaw health-management skill for bilingual daily wellness tracking. It is not an instruction-only prompt bundle. The package includes Python scripts and shell runners that read structured markdown health logs, generate daily and weekly PDF reports, and optionally send report payloads to configured webhook endpoints.

## Purpose

- Read structured markdown health logs from `MEMORY_DIR`
- Parse meals, hydration, exercise, steps, symptoms, and custom monitoring sections
- Generate localized daily and weekly health reports
- Render local PDF files
- Optionally deliver final report payloads to DingTalk, Feishu, or Telegram

## Installation

Install the Python dependencies locally:

```bash
pip install -r requirements.txt
```

Main runtime libraries:

- `reportlab`
- `pillow`
- `matplotlib`

## Required Configuration

### Required

- `MEMORY_DIR`
  This skill expects an explicit `MEMORY_DIR` environment variable in normal deployment.
  The shell wrappers still contain a legacy fallback path for self-hosted Linux setups, but production deployment should always set `MEMORY_DIR` directly to avoid accidental file access.

### Optional

- `TAVILY_API_KEY`
  Enables extra search context for next-day planning only.

- `DINGTALK_WEBHOOK`
- `FEISHU_WEBHOOK`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
  These are used only when outbound delivery is intentionally enabled.

- `REPORT_WEB_DIR`
- `REPORT_BASE_URL`
  Used only when PDFs should be copied to a public directory and exposed with a downloadable URL.

## Local File-System Behavior

The skill writes local files during normal operation. This is expected behavior.

- Reads markdown logs from `MEMORY_DIR`
- Writes generated PDFs to the local `reports/` directory unless a different public copy target is configured
- Writes runtime logs to the local `logs/` directory
- May place the fallback font file in the local `assets/` directory if the font is not already bundled

## Runtime Network Behavior

Outbound network activity is limited and conditional:

- Webhook delivery is performed only if DingTalk, Feishu, or Telegram credentials are configured
- Tavily requests are performed only if `TAVILY_API_KEY` is configured
- If the required PDF font file is missing, the PDF generator may download `NotoSansSC-VF.ttf` from `raw.githubusercontent.com`

If you do not want any runtime font download, pre-populate `assets/NotoSansSC-VF.ttf` before deployment.

## AI Runtime Notes

- If `openclaw` is available in the runtime environment, the skill can request AI commentary and planning
- If `openclaw` is not available, the skill falls back to deterministic local logic so report generation still completes

## Command Intent

- `/health`
  Generate the localized daily report for today or for a specified date

- `/health summary`
  Generate the localized weekly review anchored to a specified date

## Agent Behavior

When this skill is active, the assistant may be natural and helpful in chat, but it must be strict and mechanical when writing files under `MEMORY_DIR`.

- Never write encouragement, analysis, commentary, summaries, or conversational filler into the memory file
- Use one language per record block
- Chinese and English are both supported, but field labels must not be mixed inside the same block
- If time or calories are uncertain, estimate conservatively while preserving the exact structure

## Memory Write Protocol

When writing into `MEMORY_DIR`, the model must behave like a mechanical data recorder. Advice, commentary, and conversational guidance belong in chat only and must never be written into the memory file. The following structure must be preserved exactly because downstream parsing depends on fixed regex patterns.

If an LLM is used to write local health memories, the same rules should be mirrored into `soul.md` or the runtime system prompt so the runtime layer and the skill layer do not drift apart.

### Non-Negotiable Rules

1. Meals, hydration blocks, and exercise blocks must and may only use level-3 headings with time markers: `### Label (around HH:MM)` or `### 标签（约 HH:MM）`
2. Food lines must use the exact arrow format:
   `- Item portion → approx. XXXkcal`
3. Hydration blocks must contain exactly two lines and nothing else:
   `- Water intake: XXXml`
   `- Cumulative: XXXml/targetml`
4. Single exercise records must use an exercise-specific level-3 heading such as `### Afternoon Cycling (around 17:17)` or `### 下午骑行（约 17:17）`, then list distance, duration, and burn only
5. Step tracking must use one level-2 heading only:
   `## Today Steps`
   followed by:
   `- Total steps: XXXX steps`
6. Extra modules such as medication are allowed, but they must stay under level-2 headings and contain raw bullet data only
7. File output must never include evaluation words such as `Assessment`, `Status`, `Summary`, `评估`, `状态`, `总结`, or any emoji
8. The memory file must never contain chat-style comments, LLM explanations, motivational language, or extra fields that are not part of the template
9. Chinese and English templates are both valid, but the model must not mix them in the same record block

### Chinese Template

```markdown
# 2026-03-20 健康记录

### 早餐（约 08:30）
- 燕麦片 50g → 约 190kcal
- 脱脂牛奶 250ml → 约 87kcal

### 上午（约 09:45）
- 饮水量：300ml
- 累计：300ml/2000ml

### 下午骑行（约 17:17）
- 距离：10公里
- 耗时：47分钟
- 消耗：约 300kcal

## 今日步数
- 总步数：8500 步
```

### English Template

```markdown
# 2026-03-20 Health Log

### Breakfast (around 08:30)
- Oatmeal 50g → approx. 190kcal
- Skim milk 250ml → approx. 87kcal

### Morning (around 09:45)
- Water intake: 300ml
- Cumulative: 300ml/2000ml

### Afternoon Cycling (around 17:17)
- Distance: 10km
- Duration: 47min
- Burn: approx. 300kcal

## Today Steps
- Total steps: 8500 steps
```

## Bilingual Parsing Rules

- Daily and weekly reports may be generated from either the Chinese template or the English template
- File headings and field labels are parsed bilingually
- Internal code and config prefer canonical English values
- Chinese display output remains fully supported when `language` is set to `zh-CN`

## Operational Review Notes

For security and deployment review, the following should be considered expected behavior rather than hidden behavior:

- local PDF and log file creation
- optional webhook delivery
- optional Tavily search usage
- optional fallback font download when the local font file is missing

## Changelog

### v1.3.1 — 2026-03-20

- Synchronized the Memory Write Protocol with the stricter `soul.md` rules used at runtime
- Clarified that hydration blocks must contain exactly two lines and that no extra commentary fields are allowed
- Updated release metadata and documentation versioning for the 1.3.1 release

### v1.3.0 — 2026-03-20

- Added a shared bilingual language layer for prompts, parsing, PDF rendering, and shell delivery
- Added bilingual markdown parsing for meals, hydration, exercise, steps, symptoms, and custom sections
- Hardened the Memory Write Protocol with Chinese and English templates and stronger anti-commentary rules
- Updated metadata, config examples, and documentation to align with the bilingual release
