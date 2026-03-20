# Health-Mate

> OpenClaw skill for bilingual health tracking, strict memory logging, localized daily and weekly PDF reports, and optional webhook delivery.
>
> 面向 OpenClaw 的健康管理 skill，支持中英双语、严格记忆落盘协议、本地日报/周报 PDF 生成，以及可选的 webhook 推送。

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://www.python.org/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-black.svg)](https://github.com/tankeito/Health-Mate)

## ✨ Highlights / 核心亮点

- `zh-CN` and `en-US` are both supported end-to-end, including config prompts, markdown parsing, text reports, PDF reports, and delivery messages.
- 全链路支持中文与英文，包括初始化配置、Markdown 解析、文字报告、PDF 报告和推送文案。

- Canonical config values now prefer English ids such as `gallstones`, `diabetes`, `hypertension`, `fat_loss`, and `balanced`, while legacy Chinese values remain compatible.
- 配置层优先使用英文规范值，同时继续兼容旧版中文配置。

- The parsing engine accepts both Chinese and English memory files, but each record block should stay in one language only.
- 解析器同时支持中文和英文记忆文件，但单个记录块必须保持单语，不要中英混写。

- The Memory Write Protocol is strict by design so LLM outputs stay machine-readable and report generation stays stable.
- 记忆落盘协议采用强约束设计，目标是让 LLM 写出的文件可稳定解析，避免日报/周报生成失败。

- Reports are generated locally first. External delivery only happens if DingTalk, Feishu, or Telegram is configured by the user.
- 报告优先在本地生成；只有用户显式配置了钉钉、飞书或 Telegram 时才会向外发送。

## 🆕 What Changed In v1.3.0 / 1.3.0 更新内容

- Added a shared language-pack architecture and removed scattered hard-coded UI/report strings from the main scripts.
- 新增统一语言包架构，主脚本中散落的中文展示文本已收口到共享语言层。

- Added bilingual parsing for meals, hydration, exercise, steps, symptoms, and custom monitoring sections.
- 新增中英双语解析能力，覆盖饮食、饮水、运动、步数、症状及自定义监测模块。

- Strengthened the Memory Write Protocol with bilingual templates and stricter formatting rules for `MEMORY_DIR`.
- 强化 `MEMORY_DIR` 的记忆落盘协议，补充了中英双语模板和更严格的结构约束。

- Updated `README.md`, `SKILL.md`, `_meta.json`, config examples, and shell runners for the bilingual release.
- 更新了 `README.md`、`SKILL.md`、`_meta.json`、示例配置与 Shell 入口脚本，使其与双语版本保持一致。

## 🔒 Privacy And Delivery Warning / 隐私与数据外发提醒

- `MEMORY_DIR` contains personal health records. Treat it as sensitive data.
- `MEMORY_DIR` 中存放的是个人健康记录，请按敏感数据对待。

- Generated reports may be sent to external services if a webhook is configured.
- 如果配置了 webhook，生成的报告可能会被发送到外部服务。

- Recommended safeguards:
- 推荐安全措施：

- Only use webhook receivers you fully trust.
- 只使用你完全信任的 webhook 接收端。

- Run in a sandbox or isolated environment when possible.
- 尽量在沙箱或隔离环境中运行。

- Protect API keys, bot tokens, and webhook URLs carefully.
- 妥善保护 API Key、Bot Token 和 webhook URL。

- Review delivery logs periodically.
- 定期检查推送日志。

## 🚀 Quick Start / 快速开始

### 1. Clone And Install / 克隆与安装

```bash
git clone https://github.com/tankeito/Health-Mate.git
cd Health-Mate
pip install -r requirements.txt
```

### 2. Prepare Environment Variables / 准备环境变量

Create `config/.env` and fill the values you need.

在 `config/.env` 中填写需要的环境变量。

```bash
MEMORY_DIR=/path/to/.openclaw/workspace/memory

# Optional delivery channels / 可选推送渠道
DINGTALK_WEBHOOK=
FEISHU_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Optional public PDF hosting / 可选 PDF 对外访问
REPORT_WEB_DIR=
REPORT_BASE_URL=

# Optional search support for richer AI planning / 可选搜索增强
TAVILY_API_KEY=
```

### 3. Run The Setup Wizard / 运行初始化向导

```bash
python scripts/init_config.py
```

The wizard now asks for language first and writes canonical English config ids.

新版向导会先询问语言，并把疾病/目标、性别等关键字段写成英文规范值。

### 4. Generate Reports / 生成报告

Daily report / 日报：

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
```

Weekly report / 周报：

```bash
python scripts/weekly_report_pro.py 2026-03-20
```

Shell runners for scheduled jobs / 定时任务入口脚本：

```bash
bash scripts/daily_health_report_pro.sh
bash scripts/weekly_health_report_pro.sh
```

## ⚙️ Configuration / 配置说明

### Required / 必填

- `MEMORY_DIR`
  The OpenClaw memory directory that stores daily markdown files.
  OpenClaw 的记忆目录，里面保存按天组织的 Markdown 健康记录。

### Optional / 可选

- `DINGTALK_WEBHOOK`
  Push the final delivery message to DingTalk.
  将最终推送文案发送到钉钉。

- `FEISHU_WEBHOOK`
  Push the final delivery message to Feishu.
  将最终推送文案发送到飞书。

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
  Push the final delivery message to Telegram.
  将最终推送文案发送到 Telegram。

- `REPORT_WEB_DIR` and `REPORT_BASE_URL`
  Copy PDFs to a public directory and generate downloadable URLs.
  将 PDF 复制到公开目录，并生成可下载链接。

- `TAVILY_API_KEY`
  Optional search context for richer next-day action plans.
  为次日计划提供额外搜索上下文，可选。

### User Profile / 用户档案

`config/user_config.json` now prefers these canonical values:

`config/user_config.json` 现在优先使用以下规范值：

- `language`: `zh-CN` or `en-US`
- `gender`: `male` or `female`
- `condition`: `gallstones`, `diabetes`, `hypertension`, `fat_loss`, `balanced`

Example / 示例：

```json
{
  "language": "zh-CN",
  "user_profile": {
    "name": "Alex",
    "gender": "male",
    "age": 34,
    "height_cm": 172,
    "current_weight_kg": 65.2,
    "target_weight_kg": 64,
    "condition": "gallstones",
    "activity_level": 1.2,
    "water_target_ml": 2000,
    "step_target": 8000,
    "dietary_preferences": {
      "dislike": ["food-to-avoid-1"],
      "allergies": ["allergy-1"],
      "favorite_fruits": ["apple", "banana"]
    }
  }
}
```

## 🌐 Localization / 多语言设计

- The report locale follows `language` in `user_config.json`.
- 报告语言由 `user_config.json` 中的 `language` 字段决定。

- Chinese and English memory files are both accepted by the parser.
- 解析器同时支持中文和英文格式的记忆文件。

- English is the preferred internal canonical layer for config and code, but Chinese remains fully supported for parsing and display.
- 代码和配置内部优先使用英文规范层，但中文解析与中文展示仍然保持完整支持。

- Do not mix Chinese and English labels inside the same memory block.
- 不要在同一个记忆块内混用中文与英文字段标签。

## 💾 Memory Write Protocol / 记忆落盘铁律

This protocol should be written into `SKILL.md`. If your OpenClaw runtime supports `soul.md` or a dedicated system prompt, mirror the same protocol there as well.

这份协议应该写入 `SKILL.md`。如果你的 OpenClaw 运行环境支持 `soul.md` 或独立的 system prompt，也建议同步放进去。

Why / 为什么：

- `SKILL.md` is the stable contract for the skill itself.
- `SKILL.md` 是 skill 自身最稳定的约束载体。

- `soul.md` or the runtime system prompt gives the LLM an extra reminder at generation time.
- `soul.md` 或运行时 system prompt 能在生成时再次提醒 LLM。

- Using both reduces the chance of malformed memory files.
- 两处同时约束，可以进一步降低记忆文件写坏的概率。

### Non-Negotiable Rules / 强制规则

1. Meals, hydration blocks, and exercise blocks must use level-3 headings only: `### ...`
1. 餐次、饮水块、运动块必须使用三级标题：`### ...`

2. Food lines must use the exact arrow format: `- Item portion → approx. XXXkcal`
2. 饮食行必须严格使用箭头格式：`- 食物 份量 → 约 XXXkcal`

3. Hydration blocks must contain exactly two lines:
3. 饮水块必须且只能包含两行：

   `- Water intake: XXXml`

   `- Cumulative: XXXml/targetml`

   `- 饮水量：XXXml`

   `- 累计：XXXml/目标ml`

4. Step tracking must use a level-2 heading only:
4. 步数记录必须单独使用二级标题：

   `## Today Steps`

   `- Total steps: XXXX steps`

   `## 今日步数`

   `- 总步数：XXXX 步`

5. Extra modules such as medication are allowed, but they must stay under level-2 headings and contain raw bullet data only.
5. 额外模块如用药记录是允许的，但必须放在二级标题下，且内容只能是原始项目符号数据。

6. Never write evaluations, summaries, emojis, or chatty commentary into `MEMORY_DIR`.
6. 绝对不要把评估、总结、Emoji 或聊天式点评写进 `MEMORY_DIR`。

### Chinese Template / 中文模板

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

### English Template / 英文模板

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

## 📊 Report Flow / 报表流程

### Daily Report / 日报

- Parse one markdown memory file from `MEMORY_DIR`.
- 从 `MEMORY_DIR` 读取单日 Markdown 记录。

- Estimate calories and macronutrients from food entries.
- 根据食物条目估算热量与宏量营养素。

- Score diet, hydration, weight, symptoms, exercise, and adherence.
- 对饮食、饮水、体重、症状、运动和依从性进行评分。

- Generate a localized text summary and a localized PDF report.
- 生成本地化文字摘要与本地化 PDF 报告。

- Build one delivery payload for DingTalk, Feishu, or Telegram.
- 生成统一推送文案，供钉钉、飞书或 Telegram 使用。

### Weekly Report / 周报

- Aggregate seven days of memory data.
- 聚合最近七天的记忆数据。

- Compute trends for weight, calories, hydration, and steps.
- 计算体重、热量、饮水和步数趋势。

- Produce a weekly review, next-week actions, and a weekly PDF.
- 生成周度复盘、下周行动项以及周报 PDF。

## 🧪 Troubleshooting / 常见排查

- No report is generated:
  Check that `MEMORY_DIR` exists and contains a markdown file for the requested date.
- 没有生成报告：
  先确认 `MEMORY_DIR` 是否存在，并且目标日期的 Markdown 文件已经写入。

- PDF renders but charts are missing:
  Make sure `matplotlib` is installed and the runtime can write temporary files.
- PDF 正常但图表缺失：
  请确认 `matplotlib` 已安装，且运行环境允许写入临时文件。

- Chinese characters render incorrectly in PDF:
  Keep `assets/NotoSansSC-VF.ttf` available, or allow the script to download it automatically.
- PDF 中文字体异常：
  请确保 `assets/NotoSansSC-VF.ttf` 可用，或允许脚本自动下载。

- Delivery fails:
  Recheck webhook URLs, tokens, chat IDs, and outbound network access.
- 推送失败：
  重新检查 webhook 地址、Token、Chat ID 以及出站网络权限。

## 📁 Project Layout / 项目结构

- `scripts/health_report_pro.py`
  Daily report controller and bilingual parser.

- `scripts/weekly_report_pro.py`
  Weekly aggregation and weekly delivery pipeline.

- `scripts/pdf_generator.py`
  Daily PDF renderer.

- `scripts/weekly_pdf_generator.py`
  Weekly PDF renderer.

- `scripts/i18n.py`
  Shared language pack, aliases, prompt builders, and locale helpers.

- `scripts/init_config.py`
  Interactive setup wizard.

- `config/user_config.example.json`
  English-first sample profile configuration.

- `SKILL.md`
  Skill metadata and the strict Memory Write Protocol.

## 📌 Notes / 备注

- `SKILL.md` and `_meta.json` are intentionally English-first.
- `SKILL.md` 与 `_meta.json` 按要求采用英文主描述。

- `README.md` is bilingual by design so both Chinese and overseas users can onboard quickly.
- `README.md` 刻意做成双语，方便中文用户与海外用户都能快速上手。

- The current release focuses on internationalization and output stability, without changing the main product workflow.
- 当前版本重点在国际化与输出稳定性，核心功能流程不做大改。

## 📄 License / 许可证

MIT
