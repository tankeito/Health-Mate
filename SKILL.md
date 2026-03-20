---
name: health-mate
display_name: Health-Mate
version: 1.3.0
type: python/app
description: "A bilingual OpenClaw health-management skill for strict markdown memory logging, localized daily and weekly PDF reports, and optional webhook delivery."
install: pip install -r requirements.txt
capabilities:
 - file_read
 - pdf_generation
 - http_request
metadata:
 clawdbot:
  requires:
env:
 MEMORY_DIR: Required. Read-only directory that stores markdown health memories.
 TAVILY_API_KEY: Optional. Tavily key used for recipe and exercise research.
 DINGTALK_WEBHOOK: Optional. DingTalk webhook for report delivery.
 FEISHU_WEBHOOK: Optional. Feishu webhook for report delivery.
 TELEGRAM_BOT_TOKEN: Optional. Telegram bot token for report delivery.
 TELEGRAM_CHAT_ID: Optional. Telegram chat id for report delivery.
 REPORT_WEB_DIR: Optional. Local directory that receives copied PDFs.
 REPORT_BASE_URL: Optional. Public base URL for PDF links.
---

# Health-Mate

Health-Mate is an OpenClaw-native health-management skill for LLM-assisted diet, hydration, exercise, symptom, and weight tracking. Version `1.3.0` introduces an English-first bilingual architecture while preserving full Chinese compatibility for parsing, reporting, and memory logging.

## Command Intent

- `/health`
  Generate the localized daily report for today or for a specified date.

- `/health summary`
  Generate the localized weekly review anchored to a specified date.

## Runtime Principles

- `MEMORY_DIR` is a read-only source of structured health records.
- Report assembly and PDF generation happen locally.
- Outbound delivery only happens if the user configures DingTalk, Feishu, or Telegram.
- Config files should prefer canonical English ids such as `gallstones`, `diabetes`, `hypertension`, `fat_loss`, and `balanced`.
- Chinese legacy values must remain compatible during parsing and report generation.

## Agent Behavior

When this skill is active, the assistant may be warm and expressive in chat, but it must be strict and mechanical when writing files under `MEMORY_DIR`.

- Never write encouragement, analysis, commentary, or summaries into the memory file.
- Use one language per record block. Chinese and English are both supported, but do not mix field labels inside the same block.
- If time or calories are uncertain, estimate conservatively, but keep the structure exact.
- If the user asks for advice, keep the advice in chat. The file should contain only raw structured data.

## Memory Write Protocol

This protocol must be written in `SKILL.md`. If the OpenClaw runtime also supports `soul.md` or a dedicated system prompt, mirror the exact same protocol there too. The goal is to constrain the LLM at both the skill layer and the runtime layer.

### Non-Negotiable Rules

1. Meals, hydration blocks, and exercise blocks must use level-3 headings only: `### ...`
2. Food lines must use the exact arrow format:
   `- Item portion → approx. XXXkcal`
3. Hydration blocks must contain exactly two lines:
   `- Water intake: XXXml`
   `- Cumulative: XXXml/targetml`
4. Step tracking must use one level-2 heading only:
   `## Today Steps`
   followed by:
   `- Total steps: XXXX steps`
5. Extra modules such as medication are allowed, but they must stay under level-2 headings and contain only raw bullet data.
6. File output must never include evaluation words such as `Assessment`, `Status`, `Summary`, `评估`, `状态`, `总结`, or any emoji.
7. The memory file must never contain chat-style comments, LLM explanations, or motivational language.
8. Chinese and English templates are both valid, but the model must not mix them in the same record block.

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

- Daily and weekly reports may be generated from either the Chinese template or the English template.
- File headings and field labels are parsed bilingually.
- Internal code and config should prefer canonical English values.
- Chinese display output remains fully supported when `language` is set to `zh-CN`.

## Changelog

### v1.3.0 — 2026-03-20

- Added a shared bilingual language layer for prompts, parsing, PDF rendering, and shell delivery.
- Added bilingual markdown parsing for meals, hydration, exercise, steps, symptoms, and custom sections.
- Hardened the Memory Write Protocol with Chinese and English templates and stronger anti-commentary rules.
- Updated metadata, config examples, and documentation to align with the bilingual release.
