<div align="center">

# Health-Mate

### OpenClaw Health Management Skill for Bilingual Memory Logging, Daily Reports, Weekly Reviews, and PDF Delivery

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://www.python.org/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-ready-black.svg)](https://github.com/tankeito/Health-Mate)
[![Language](https://img.shields.io/badge/language-English%20%7C%20%E4%B8%AD%E6%96%87-orange.svg)](https://github.com/tankeito/Health-Mate)
[![Reports](https://img.shields.io/badge/output-Daily%20%26%20Weekly%20PDF-purple.svg)](https://github.com/tankeito/Health-Mate)

**English** | [简体中文](#-简体中文) | [Quick Start](#-quick-start) | [Memory Write Protocol](#-memory-write-protocol) | [Server Checklist](#-server-deployment-checklist)

</div>

---

## 🇬🇧 English

### 🌟 Overview

Health-Mate is an OpenClaw-focused health management skill designed for LLM-assisted daily wellness tracking. It reads structured markdown memories from `MEMORY_DIR`, parses meals, hydration, exercise, weight, symptoms, and custom monitoring notes, then generates:

- a localized daily health report
- a localized weekly health review
- a styled PDF report for each workflow
- an optional delivery payload for DingTalk, Feishu, or Telegram

Version `1.3.0` keeps the existing workflow intact while adding an English-first bilingual architecture. Chinese remains fully supported for parsing and display, but the internal configuration layer now prefers canonical English ids for long-term maintainability.

### 💡 Why Health-Mate

- **Built for OpenClaw workflows**
  It is designed around `MEMORY_DIR`, skill prompts, and structured markdown memories rather than generic fitness app assumptions.

- **Bilingual by design**
  Both `zh-CN` and `en-US` are supported in config, parsing, text generation, PDF rendering, and delivery messages.

- **Strict enough for LLMs**
  The Memory Write Protocol is intentionally rigid so model-generated markdown stays machine-readable and stable.

- **Good fit for China-first and overseas users**
  Chinese users can keep existing habits, while overseas users can write and receive reports in English without changing the core workflow.

### 🧩 Core Capabilities

- **Daily reporting**
  Parse one day of records and produce a text summary plus a PDF report with scoring, nutrition, hydration, exercise, and next-day guidance.

- **Weekly review**
  Aggregate seven days of records, compute trends, and generate a weekly review PDF with charts and action items.

- **Bilingual parsing**
  Accept Chinese or English memory files for meals, hydration, exercise, steps, symptoms, and custom monitoring modules.

- **Nutrition estimation**
  Estimate calories and macros from food items, including common English food aliases mapped to the existing nutrition database.

- **Localized delivery**
  Build one final delivery message that can be sent through DingTalk, Feishu, or Telegram.

- **Graceful fallback**
  If `openclaw` or external AI calls are unavailable, report generation still works through deterministic fallback logic.

### 🏗️ Workflow

1. The user or LLM writes a structured markdown log into `MEMORY_DIR`.
2. Health-Mate parses the file using bilingual aliases and canonical internal keys.
3. The engine estimates calories, macros, hydration totals, exercise load, and step progress.
4. Daily or weekly scoring is calculated.
5. AI commentary and planning are attempted when runtime support is available.
6. A localized text report and PDF report are generated.
7. The delivery message is prepared and optionally pushed through configured webhooks.

### 🚀 Quick Start

#### 1. Clone and install

```bash
git clone https://github.com/tankeito/Health-Mate.git
cd Health-Mate
pip install -r requirements.txt
```

#### 2. Prepare environment variables

Create `config/.env` and fill what you need:

```bash
MEMORY_DIR=/path/to/.openclaw/workspace/memory

# Optional AI search support
TAVILY_API_KEY=

# Optional delivery channels
DINGTALK_WEBHOOK=
FEISHU_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Optional public PDF hosting
REPORT_WEB_DIR=
REPORT_BASE_URL=
```

#### 3. Initialize the user profile

```bash
python scripts/init_config.py
```

The setup wizard now asks for language first and writes canonical English ids such as:

- `language`: `zh-CN` or `en-US`
- `gender`: `male` or `female`
- `condition`: `gallstones`, `diabetes`, `hypertension`, `fat_loss`, `balanced`

#### 4. Generate reports

Daily:

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
```

Weekly:

```bash
python scripts/weekly_report_pro.py 2026-03-20
```

Scheduled shell entry points:

```bash
bash scripts/daily_health_report_pro.sh
bash scripts/weekly_health_report_pro.sh
```

### ⚙️ Configuration Guide

#### Environment variables

- `MEMORY_DIR`
  Required. Directory containing the markdown health logs.

- `TAVILY_API_KEY`
  Optional. Used to enrich next-day planning with external search context.

- `DINGTALK_WEBHOOK`
  Optional. Sends the final delivery message to DingTalk.

- `FEISHU_WEBHOOK`
  Optional. Sends the final delivery message to Feishu.

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
  Optional. Sends the final delivery message to Telegram.

- `REPORT_WEB_DIR` and `REPORT_BASE_URL`
  Optional. Copy PDFs to a public directory and build downloadable links.

#### User profile

Use [`config/user_config.example.json`](config/user_config.example.json) as the base template. The project now prefers English-first canonical values, but older Chinese config values are still accepted during parsing.

### 🧠 Memory Write Protocol

This is the most important rule set in the project.

Health-Mate depends on strict markdown structure because the report pipeline reads local memory files mechanically. If the LLM starts adding commentary, changing headings, or improvising formats, the parser becomes less reliable and the generated reports become unstable.

**Recommended placement**

- put the protocol in `SKILL.md`
- mirror the same protocol in `soul.md` or the runtime system prompt when available
- keep chat feedback outside the memory file

#### Non-negotiable rules

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
5. Extra modules such as medication are allowed, but they must stay under level-2 headings and contain raw bullet data only.
6. Never write evaluations, summaries, emojis, or chatty commentary into `MEMORY_DIR`.
7. Chinese and English are both valid, but do not mix field labels inside the same record block.

#### Chinese template

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

#### English template

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

### 📊 Report Outputs

#### Daily report

- overall score
- diet, hydration, weight, symptom, exercise, and adherence breakdown
- AI insight or deterministic fallback insight
- detailed meal, water, and exercise summaries
- next-day action plan
- PDF rendering with charts

#### Weekly report

- seven-day aggregation
- average calories, water, steps, and weight change
- trend charts for weight, calories, hydration, and steps
- weekly AI review or deterministic fallback review
- next-week action plan
- weekly PDF rendering

### 🔐 Privacy and Security

- `MEMORY_DIR` contains personal health data. Treat it as sensitive.
- Reports may be sent externally if webhook delivery is enabled.
- Use only webhook receivers you trust.
- Prefer sandboxed or isolated deployment when possible.
- Protect API keys, bot tokens, and webhook URLs carefully.

### 🧪 Server Deployment Checklist

Before moving to production, verify the following:

- dependencies are installed with `pip install -r requirements.txt`
- `MEMORY_DIR` exists and is readable
- the report output directory is writable
- `openclaw` is available if you want live AI commentary and planning
- webhook URLs and tokens are correct
- the system timezone matches your expected schedule
- the shell scripts run successfully under your server user

Recommended order:

1. run `python scripts/health_report_pro.py ...`
2. run `python scripts/weekly_report_pro.py ...`
3. run the two shell scripts manually
4. enable scheduled tasks or cron
5. enable external webhook delivery last

### ❓FAQ

#### Does Health-Mate require OpenClaw to be installed?

The parser and PDF generator do not. However, live AI commentary and planning expect `openclaw` to be available. Without it, the project falls back to local deterministic logic.

#### Can I keep my old Chinese config values?

Yes. The system is backward-compatible, but new config files should use canonical English ids.

#### Can I use only English memory files?

Yes. The current codebase supports full English parsing for daily and weekly report generation.

#### Should I update `SKILL.md` too?

At this stage, only if the runtime contract changes. `SKILL.md` already contains the correct English-first protocol and behavior expectations, so it does not need a structural rewrite just to match the README presentation style.

### 📁 Project Layout

- [`scripts/health_report_pro.py`](scripts/health_report_pro.py)
  Daily parsing, scoring, reporting, and delivery payload generation.

- [`scripts/weekly_report_pro.py`](scripts/weekly_report_pro.py)
  Weekly aggregation, weekly insights, and weekly delivery payload generation.

- [`scripts/pdf_generator.py`](scripts/pdf_generator.py)
  Daily PDF rendering.

- [`scripts/weekly_pdf_generator.py`](scripts/weekly_pdf_generator.py)
  Weekly PDF rendering.

- [`scripts/i18n.py`](scripts/i18n.py)
  Shared language packs, bilingual aliases, prompt builders, and locale helpers.

- [`scripts/init_config.py`](scripts/init_config.py)
  Interactive setup wizard.

- [`SKILL.md`](SKILL.md)
  Runtime contract for the skill and the strict memory protocol.

---

## 🇨🇳 简体中文

### 🌟 项目简介

Health-Mate 是一个围绕 OpenClaw 工作流设计的健康管理 skill，核心目标不是做一个泛化的健身应用，而是为“本地记忆记录 + LLM 辅助分析 + 日报/周报输出”这条链路提供一个稳定、严格、可长期维护的方案。

它会从 `MEMORY_DIR` 中读取结构化 Markdown 健康记录，解析饮食、饮水、运动、体重、症状与自定义监测信息，并生成：

- 本地化健康日报
- 本地化健康周报
- 美观的 PDF 报告
- 可选的钉钉 / 飞书 / Telegram 推送内容

`1.3.0` 版本重点是国际化与输出稳定性升级。当前仍然完整支持中文用户，但内部配置层已经优先采用英文规范值，便于后续继续扩展海外用户。

### 💡 为什么用它

- **专门适配 OpenClaw**
  不是泛用脚本，而是围绕 `MEMORY_DIR`、skill 提示词和本地记忆落盘来设计。

- **中英双语完整支持**
  中文和英文都能贯穿配置、解析、文字报告、PDF 报告和推送文案。

- **对 LLM 足够严格**
  Memory Write Protocol 的目标就是减少模型“自由发挥”，让落盘内容稳定可解析。

- **适合中国用户，也适合海外用户**
  中国用户可以继续保留原有输入习惯，海外用户可以直接使用英文写入与英文输出。

### 🧩 核心能力

- **日报生成**
  读取单日记录，输出文字总结和 PDF 报告，包含评分、营养估算、饮水与运动情况、次日建议等内容。

- **周报复盘**
  聚合七天数据，生成趋势分析、周度复盘与下周行动计划，并输出周报 PDF。

- **双语解析**
  同时支持中文和英文格式的饮食、饮水、运动、步数、症状与自定义模块。

- **营养估算**
  支持常见英文食物别名映射到现有营养数据库，尽量不破坏原始中文食物数据沉淀。

- **统一推送**
  日报和周报都会生成统一的最终推送文案，便于 webhook 渠道复用。

- **AI 不可用时自动降级**
  即使 `openclaw` 或外部 AI 调用不可用，报表生成主流程仍能继续运行。

### 🏗️ 工作流程

1. 用户或 LLM 把健康记录写入 `MEMORY_DIR`
2. Health-Mate 使用双语别名和内部规范键解析 Markdown
3. 估算热量、宏量营养素、饮水总量、运动负荷与步数完成度
4. 计算日报或周报评分
5. 如果运行环境可用，则尝试生成 AI 点评和计划
6. 输出本地化文字报告和 PDF 报告
7. 生成最终推送文案，并按配置发送到外部渠道

### 🚀 快速开始

#### 1. 克隆并安装依赖

```bash
git clone https://github.com/tankeito/Health-Mate.git
cd Health-Mate
pip install -r requirements.txt
```

#### 2. 配置环境变量

在 `config/.env` 中填写：

```bash
MEMORY_DIR=/path/to/.openclaw/workspace/memory

# 可选：搜索增强
TAVILY_API_KEY=

# 可选：推送渠道
DINGTALK_WEBHOOK=
FEISHU_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# 可选：PDF 外链
REPORT_WEB_DIR=
REPORT_BASE_URL=
```

#### 3. 初始化用户档案

```bash
python scripts/init_config.py
```

新版初始化向导会先询问语言，并把以下关键字段写成规范英文值：

- `language`: `zh-CN` 或 `en-US`
- `gender`: `male` 或 `female`
- `condition`: `gallstones`、`diabetes`、`hypertension`、`fat_loss`、`balanced`

#### 4. 生成报表

日报：

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
```

周报：

```bash
python scripts/weekly_report_pro.py 2026-03-20
```

定时任务脚本：

```bash
bash scripts/daily_health_report_pro.sh
bash scripts/weekly_health_report_pro.sh
```

### ⚙️ 配置说明

#### 环境变量

- `MEMORY_DIR`
  必填。用于存放每日健康 Markdown 记录的目录。

- `TAVILY_API_KEY`
  可选。为次日建议提供额外搜索上下文。

- `DINGTALK_WEBHOOK`
  可选。将最终推送文案发送到钉钉。

- `FEISHU_WEBHOOK`
  可选。将最终推送文案发送到飞书。

- `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID`
  可选。将最终推送文案发送到 Telegram。

- `REPORT_WEB_DIR` 与 `REPORT_BASE_URL`
  可选。把 PDF 复制到公开目录并生成可访问链接。

#### 用户档案

请参考 [`config/user_config.example.json`](config/user_config.example.json)。当前项目内部优先使用英文规范值，但仍兼容旧版中文配置。

### 🧠 记忆落盘铁律

这部分是整个项目里最关键的约束。

Health-Mate 的解析链路是机械式读取本地 Markdown 文件的。如果 LLM 开始插入点评、自由改标题、擅自改字段格式，就会直接影响解析稳定性，进而影响日报和周报的生成质量。

**推荐放置位置**

- 必须写进 `SKILL.md`
- 如果运行环境支持 `soul.md` 或 system prompt，建议再镜像一份
- 聊天中的分析、建议、安慰语不要写入记忆文件

#### 强制规则

1. 餐次、饮水块、运动块必须使用三级标题：`### ...`
2. 饮食行必须严格使用箭头格式：
   `- 食物 份量 → 约 XXXkcal`
3. 饮水块必须且只能包含两行：
   `- 饮水量：XXXml`
   `- 累计：XXXml/目标ml`
4. 步数记录必须单独使用二级标题：
   `## 今日步数`
   下方只能写：
   `- 总步数：XXXX 步`
5. 用药、补剂等额外模块可以存在，但必须在二级标题下，只保留原始项目符号数据。
6. `MEMORY_DIR` 中绝对禁止写入评估、总结、Emoji、聊天式说明或多余修辞。
7. 中文和英文都支持，但单个记录块内不要混用字段标签。

#### 中文模板

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

#### 英文模板

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

### 📊 报告输出内容

#### 日报包含

- 综合评分
- 饮食、饮水、体重、症状、运动、依从性等分项评分
- AI 点评或本地 fallback 点评
- 饮食、饮水、运动细节
- 次日优化方案
- 图表化 PDF 报告

#### 周报包含

- 七天聚合数据
- 平均热量、饮水、步数和体重变化
- 体重、热量、饮水、步数趋势图
- AI 周复盘或本地 fallback 周复盘
- 下周行动计划
- 周报 PDF

### 🔐 隐私与安全

- `MEMORY_DIR` 中是个人健康数据，请按敏感信息处理。
- 如果开启 webhook，报告会被发送到外部服务。
- 只使用你完全信任的 webhook 接收端。
- 尽量使用隔离环境部署。
- 妥善保护 API Key、Bot Token 和 webhook 地址。

### 🧪 服务器部署检查清单

正式上服务器前，建议逐项确认：

- 已执行 `pip install -r requirements.txt`
- `MEMORY_DIR` 目录存在且可读
- 报告输出目录可写
- 如果你希望生成 AI 点评和计划，服务器里要有 `openclaw`
- webhook 地址与 token 配置正确
- 系统时区与预期任务时间一致
- 两个 shell 脚本可以在服务器用户下正常执行

推荐测试顺序：

1. 先运行 `python scripts/health_report_pro.py ...`
2. 再运行 `python scripts/weekly_report_pro.py ...`
3. 再手动运行两个 shell 脚本
4. 最后再接入定时任务和 webhook

### ❓常见问题

#### 没装 OpenClaw 能用吗？

解析、打分和 PDF 生成可以继续工作。但如果你希望真的调用 AI 生成点评和计划，就需要运行环境中存在 `openclaw`。

#### 旧版中文配置还能继续用吗？

可以。当前版本兼容旧中文配置，但新配置建议统一写成英文规范值。

#### 英文记忆文件可以直接用吗？

可以。现在的代码已经支持英文日报和英文周报的完整解析与输出链路。

#### `SKILL.md` 还要不要跟着改？

如果只是为了让 README 更像正式开源项目首页，那暂时不需要。当前 `SKILL.md` 已经是英文主描述，并且包含了正确的 Memory Write Protocol 与运行约束。除非未来协议本身或命令行为发生变化，否则不必为了展示风格再重写一遍。

### 📁 项目结构

- [`scripts/health_report_pro.py`](scripts/health_report_pro.py)
  日报解析、打分、文字报告与推送内容生成。

- [`scripts/weekly_report_pro.py`](scripts/weekly_report_pro.py)
  周报聚合、周度复盘和推送内容生成。

- [`scripts/pdf_generator.py`](scripts/pdf_generator.py)
  日报 PDF 渲染器。

- [`scripts/weekly_pdf_generator.py`](scripts/weekly_pdf_generator.py)
  周报 PDF 渲染器。

- [`scripts/i18n.py`](scripts/i18n.py)
  共享语言包、双语别名、提示词生成和本地化辅助方法。

- [`scripts/init_config.py`](scripts/init_config.py)
  初始化配置向导。

- [`SKILL.md`](SKILL.md)
  Skill 的运行约束与记忆落盘协议。

---

## 📄 License

MIT
