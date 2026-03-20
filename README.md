English | [中文](README_ZH.md)

# 🏥 Health-Mate

> **Personal Health Assistant for OpenClaw**
> 
> *Track your diet, hydration, exercise, and weight. Generate beautiful PDF reports with AI-powered insights.*

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## ⚠️ Privacy & Security Warning

**Health-Mate reads health data from your local `MEMORY_DIR` directory. Generated PDF reports may be delivered to external platforms (DingTalk, Feishu, Telegram) only if you explicitly configure webhook endpoints.**

**Security Recommendations**:
- ✅ Ensure you fully trust configured webhook endpoints
- ✅ Use in sandbox or isolated environments when testing
- ✅ Never commit `config/.env` or `config/user_config.json` to public repositories
- ✅ Regularly audit webhook access logs for unusual activity

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 📝 **Strict Memory Protocol** | Enforces consistent markdown structure for reliable parsing—no emoji, no commentary, just clean data |
| 🌐 **Bilingual Support** | Full Chinese/English parity in parsing, prompts, PDF rendering, and documentation |
| 📊 **Visual PDF Reports** | Daily & weekly reports with Matplotlib charts (nutrition rings, hydration bars, progress tracking) |
| 🤖 **AI Health Commentary** | LLM-generated insights and next-day action plans based on your recorded data |
| 📬 **Multi-Channel Delivery** | Optional push to DingTalk, Feishu, or Telegram via configurable webhooks |
| 🔒 **Local-First Processing** | All analysis and PDF generation happen locally—no data leaves your machine unless you configure webhooks |

---

## 🚀 Quick Start

### Step 1: Install

```bash
# Navigate to OpenClaw skills directory
cd ~/.openclaw/workspace/skills

# Clone the repository
git clone https://github.com/tankeito/Health-Mate.git health-mate

# Install Python dependencies
cd health-mate
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Navigate to config directory
cd config

# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Environment Variables**:
```bash
MEMORY_DIR="/root/.openclaw/workspace/memory"
```

**Optional (for report delivery)**:
```bash
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://your-domain.com"
```

### Step 3: Initialize User Profile

```bash
# Run the interactive initialization script
python3 scripts/init_config.py
```

The script will guide you through:
1. Name and gender
2. Height, current weight, and target weight
3. Health condition (gallstones, diabetes, hypertension, fat loss, etc.)
4. Daily water intake target
5. Daily step target
6. Report delivery preferences

### Step 4: Test Run

```bash
# Generate a daily report for a specific date
python3 scripts/health_report_pro.py /root/.openclaw/workspace/memory/2026-03-20.md 2026-03-20
```

---

## 📝 Memory Write Protocol

**Health-Mate enforces a strict markdown structure for health logs. The AI assistant must write data mechanically—no encouragement, no analysis, no emoji in the file.**

### Non-Negotiable Rules

1. **Meals, hydration, and exercise** must use level-3 headings only: `### ...`
2. **Food lines** must use the exact arrow format: `- Item portion → approx. XXXkcal`
3. **Hydration blocks** must contain exactly two lines:
   ```
   - Water intake: XXXml
   - Cumulative: XXXml/targetml
   ```
4. **Step tracking** must use one level-2 heading only:
   ```
   ## Today Steps
   - Total steps: XXXX steps
   ```
5. **Extra modules** (e.g., medication) are allowed under level-2 headings with raw bullet data only
6. **Never include** evaluation words like `Assessment`, `Status`, `Summary`, `评估`, `状态`, `总结`, or any emoji
7. **No chat-style comments**, LLM explanations, or motivational language in the file
8. **One language per block**—Chinese and English are both valid, but do not mix within the same block

### English Template (Required Format)

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

### Chinese Template (Supported Format)

```markdown
# 2026-03-20 健康记录

### 早餐（约 08:30）
- 燕麦片 50g → 约 190kcal
- 脱脂牛奶 250ml → 约 87kcal

### 上午（约 09:45）
- 饮水量：300ml
- 累计：300ml/2000ml

### 下午骑行（约 17:17）
- 距离：10 公里
- 耗时：47 分钟
- 消耗：约 300kcal

## 今日步数
- 总步数：8500 步
```

---

## 🤖 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/health` | Generate daily PDF report | `/health 2026-03-20` |
| `/health summary` | Generate weekly review report | `/health summary 2026-03-20` |

---

## ⚙️ Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MEMORY_DIR` | ✅ Yes | Directory containing markdown health logs | `/root/.openclaw/workspace/memory` |
| `TAVILY_API_KEY` | ❌ No | Tavily API key for recipe/exercise research | `tvly-dev-xxx` |
| `DINGTALK_WEBHOOK` | ❌ No | DingTalk bot webhook for report delivery | `https://oapi.dingtalk.com/...` |
| `FEISHU_WEBHOOK` | ❌ No | Feishu bot webhook for report delivery | `https://open.feishu.cn/...` |
| `TELEGRAM_BOT_TOKEN` | ❌ No | Telegram bot token for report delivery | `YOUR_BOT_TOKEN` |
| `TELEGRAM_CHAT_ID` | ❌ No | Telegram chat ID for report delivery | `YOUR_CHAT_ID` |
| `REPORT_WEB_DIR` | ❌ No | Local directory for PDF output | `/var/www/html/reports` |
| `REPORT_BASE_URL` | ❌ No | Public URL for PDF download links | `https://your-domain.com` |

---

## 📊 Report Output

### Daily Report Structure

1. **Cover Page** – Date, overall score, star rating
2. **Score Breakdown** – 6 dimensions (diet, water, weight, symptoms, exercise, adherence)
3. **Health Metrics** – BMI, BMR, TDEE calculations
4. **Nutrition Summary** – Calories and macronutrients (carbs, protein, fat, fiber)
5. **Hydration Timeline** – Water intake throughout the day
6. **Meal Details** – Food items with portions and calorie estimates
7. **Exercise Log** – Activity records with duration and calories burned
8. **AI Commentary** – Personalized health insights and suggestions
9. **Risk Alerts** – Health risk warnings based on recorded data
10. **Next-Day Action Plan** – Diet, water, exercise recommendations

### Weekly Report Structure

1. **Overview** – Weekly average score, best/worst days
2. **Trend Charts** – Weight fluctuations, daily calorie intake, step counts
3. **Nutrition Ring** – Average macronutrient distribution
4. **AI Deep Analysis** – Cross-day pattern recognition and intervention suggestions

---

## 📦 Project Structure

```
health-mate/
├── scripts/
│   ├── health_report_pro.py      # Daily report generator
│   ├── weekly_report_pro.py      # Weekly report generator
│   ├── pdf_generator.py          # PDF rendering engine
│   ├── weekly_pdf_generator.py   # Weekly PDF renderer
│   ├── i18n.py                   # Bilingual language layer
│   ├── constants.py              # Food calorie database
│   ├── init_config.py            # Interactive setup wizard
│   ├── daily_health_report_pro.sh    # Cron job script (daily)
│   └── weekly_health_report_pro.sh   # Cron job script (weekly)
├── config/
│   ├── user_config.json          # User health profile
│   ├── .env                      # Environment variables (gitignored)
│   ├── .env.example              # Environment template
│   ├── pdf_style_config.json     # PDF styling configuration
│   └── user_config.example.json  # Profile template
├── assets/
│   └── NotoSansSC-VF.ttf         # Chinese font (auto-downloaded)
├── logs/                         # Execution logs
├── reports/                      # Generated PDF reports
├── README.md                     # English documentation
├── README_ZH.md                  # Chinese documentation
├── SKILL.md                      # OpenClaw skill definition
└── requirements.txt              # Python dependencies
```

---

## 🔐 Privacy & Data Protection

### Files Protected by `.gitignore`

The following files **must never be committed** to public repositories:

- `config/user_config.json` – Personal health data
- `config/.env` – Webhook tokens and private configuration
- `reports/*.pdf` – Generated health reports
- `logs/*.log` – Execution logs

### Recommended Practices

1. **Private Repository** – Set as Private when forking
2. **Regular Backups** – Backup config files to secure storage
3. **Key Rotation** – Update webhook tokens every 3-6 months
4. **Sandbox Testing** – Test in isolated environments first
5. **Log Auditing** – Regularly review webhook access logs

---

## 🔄 Changelog

### v1.3.0 — 2026-03-20

- 🌐 **Bilingual Architecture**: Added i18n.py for unified Chinese/English language layer
- 📝 **Memory Protocol**: Hardened anti-commentary rules with CN/EN templates
- 🔧 **Parsing Improvements**: Enhanced bilingual meal, hydration, exercise block detection
- 🎨 **PDF Fixes**: Resolved emoji rendering issues (☒ squares) in PDF output
- 💊 **Medication Tracking**: Added support for custom modules (e.g., 用药记录)
- 📚 **Documentation**: Complete English/Chinese README restructuring

### v1.2.0 — 2026-03-20

- 🎯 **Dynamic Targets**: Refactored condition parameters for flexible health goals (e.g., fat loss)
- 🌍 **Multi-Language Docs**: Added bilingual documentation and custom module support
- 🧹 **Strict Protocol**: Rewrote Memory Write Protocol to lock down LLM output
- 🐛 **Bug Fixes**: Fixed PDF emoji rendering and parsing error tolerance

### v1.1.x — Earlier Releases

- Weekly report system with polar charts and trend analysis
- Matplotlib visualization (nutrition rings, hydration bars, progress tracking)
- Automated font download for Chinese character support
- Privacy compliance updates and security declarations

---

## 📄 License

MIT License – See [LICENSE](LICENSE) for details.

---

## 📞 Support

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **Email**: tqd354@gmail.com
- **Repository**: https://github.com/tankeito/Health-Mate
