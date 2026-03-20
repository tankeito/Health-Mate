[English](README.md) | 中文

# 🏥 Health-Mate 个人健康管家

> **您的智能健康伴侣，专为 OpenClaw 打造**
> 
> *将日常健康习惯转化为可执行的洞察。精准追踪营养、饮水、运动与体重变化。生成 AI 驱动的专业 PDF 报告—所有数据 100% 私有，完全本地运行。*

[![Version](https://img.shields.io/badge/version-1.3.1-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 项目概述

Health-Mate 是一款**生产就绪的双语健康管理技能**，专为 OpenClaw AI 助手平台独家打造。源于让个人健康追踪既**强大又隐私优先**的愿景，Health-Mate 填补了休闲健身应用与临床健康监测系统之间的空白。

### Health-Mate 的独特之处

与那些收割用户数据的云端健康追踪器不同，Health-Mate 完全在您的本地机器上运行。每一次热量计算、每一次饮水提醒、每一条 AI 生成的健康洞察，都在**您的硬件上离线完成**。您拥有健康旅程的完全所有权，同时享受企业级功能：

- **🔒 隐私至上设计**：除非您显式配置 Webhook 端点用于报告推送，否则数据永远不会离开您的机器
- **🧠 AI 驱动洞察**：大语言模型集成提供个性化健康点评和次日行动方案
- **📊 专业可视化**：Matplotlib 渲染图表（营养环形图、饮水柱状图、趋势线）媲美高端智能手表应用
- **🌐 双语卓越体验**：从解析逻辑到 PDF 输出再到文档，中文/英文完全对等
- **⚙️ 病理智能协议**：预配置的胆结石、糖尿病、高血压、减脂目标专用方案
- **📬 灵活推送**：支持钉钉、飞书、Telegram，或纯本地运行

### Health-Mate 适合谁？

- **慢性病管理者**：需要精准宏量营养素追踪的胆结石、糖尿病、高血压患者
- **健身爱好者**：追求结构化减脂或增肌计划的运动员和健身人群
- **隐私倡导者**：拒绝将个人数据拱手让给云端公司的健康意识用户
- **OpenClaw 高级用户**：构建个性化 AI 助手生态系统的开发者和爱好者

---

## ⚠️ 隐私与安全警告

**Health-Mate 从本地 `MEMORY_DIR` 目录读取健康数据。仅在您显式配置 Webhook 端点时，生成的 PDF 报告才会推送至外部平台（钉钉/飞书/Telegram）。**

**安全建议**：
- ✅ 确保完全信任所配置的 Webhook 接收端
- ✅ 测试时建议在沙箱或隔离环境中使用
- ✅ 切勿将 `config/.env` 或 `config/user_config.json` 提交到公开仓库
- ✅ 定期检查 Webhook 访问日志，发现异常调用

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 📝 **记忆落盘铁律** | 强制执行标准化 Markdown 结构，无 Emoji、无点评、仅纯净数据，确保解析可靠性 |
| 🌐 **双语支持** | 中文/英文完全对等，支持双语解析、提示词、PDF 渲染及文档 |
| 📊 **可视化 PDF 报告** | 日报 + 周报双系统，Matplotlib 图表（营养环形图、饮水柱状图、趋势追踪） |
| 🤖 **AI 健康点评** | 基于大模型的个性化健康洞察与次日行动方案 |
| 📬 **多通道推送** | 支持钉钉/飞书/Telegram，通过可配置 Webhook 可选推送 |
| 🔒 **本地优先处理** | 所有分析与 PDF 生成均在本地完成—除非配置 Webhook，否则数据不出域 |

---

## 🚀 快速开始

### 步骤 1：安装

```bash
# 进入 OpenClaw skills 目录
cd ~/.openclaw/workspace/skills

# 克隆仓库
git clone https://github.com/tankeito/Health-Mate.git health-mate

# 安装 Python 依赖
cd health-mate
pip install -r requirements.txt
```

### 步骤 2：配置环境变量

```bash
# 进入配置目录
cd config

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**必填环境变量**：
```bash
MEMORY_DIR="/root/.openclaw/workspace/memory"
```

**可选（用于报告推送）**：
```bash
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://your-domain.com"
```

### 步骤 3：初始化用户档案

```bash
# 运行交互式初始化脚本
python3 scripts/init_config.py
```

脚本将引导您完成：
1. 姓名与性别
2. 身高、当前体重、目标体重
3. 健康状况（胆结石/糖尿病/高血压/减脂等）
4. 每日饮水目标
5. 每日步数目标
6. 报告推送偏好设置

### 步骤 4：测试运行

```bash
# 生成指定日期的日报
python3 scripts/health_report_pro.py /root/.openclaw/workspace/memory/2026-03-20.md 2026-03-20
```

---

## 📝 记忆落盘铁律

**Health-Mate 强制执行严格的健康日志 Markdown 结构。写入 `MEMORY_DIR` 时，AI 助理必须像“无情的数据记录仪”一样工作。点评与建议只能出现在聊天框里，绝不能写入文件。**

### 强制规则

1. **餐次/饮水/运动** 必须且只能使用带时间的三级标题：`### 标签（约 HH:MM）` 或 `### Label (around HH:MM)`
2. **食物行** 必须使用标准箭头格式：`- 食物 份量 → 约 XXXkcal`
3. **饮水块** 必须且只能包含两行，不能额外追加任何状态或说明：
   ```
   - 饮水量：XXml
   - 累计：XXml/目标ml
   ```
4. **单次运动** 必须使用带运动类型的三级标题，例如 `### 下午骑行（约 17:17）`，其下只列距离、耗时、消耗
5. **步数记录** 必须且只能使用一个二级标题：
   ```
   ## 今日步数
   - 总步数：XXXX 步
   ```
6. **扩展模块**（如用药记录）允许使用二级标题，但仅包含原始列表数据
7. **禁止出现** `评估`、`状态`、`总结`、`Assessment`、`Status`、`Summary` 或任何 Emoji
8. **禁止聊天式评论**、LLM 解释、鼓励性语言或模板外字段出现在文件中
9. **单块单语言**：中文和英文均有效，但同一块内禁止混用

建议将同一份协议同时写入 `soul.md` 与 `SKILL.md`，确保运行时提示与技能说明完全一致。

### 中文模板（标准格式）

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

## 🤖 命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `/health` | 生成日报 PDF | `/health 2026-03-20` |
| `/health summary` | 生成周报 PDF | `/health summary 2026-03-20` |

---

## ⚙️ 环境变量清单

| 变量名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| `MEMORY_DIR` | ✅ 是 | 存放 Markdown 健康日志的目录 | `/root/.openclaw/workspace/memory` |
| `TAVILY_API_KEY` | ❌ 否 | Tavily API 密钥，用于菜谱/运动研究 | `tvly-dev-xxx` |
| `DINGTALK_WEBHOOK` | ❌ 否 | 钉钉机器人 Webhook，用于报告推送 | `https://oapi.dingtalk.com/...` |
| `FEISHU_WEBHOOK` | ❌ 否 | 飞书机器人 Webhook，用于报告推送 | `https://open.feishu.cn/...` |
| `TELEGRAM_BOT_TOKEN` | ❌ 否 | Telegram Bot Token，用于报告推送 | `YOUR_BOT_TOKEN` |
| `TELEGRAM_CHAT_ID` | ❌ 否 | Telegram Chat ID，用于报告推送 | `YOUR_CHAT_ID` |
| `REPORT_WEB_DIR` | ❌ 否 | PDF 输出的本地目录 | `/var/www/html/reports` |
| `REPORT_BASE_URL` | ❌ 否 | PDF 下载链接的公共域名 | `https://your-domain.com` |

---

## 📊 报告结构

### 日报结构

1. **封面页** – 日期、综合评分、星级
2. **分项评分** – 6 维度（饮食/饮水/体重/症状/运动/依从性）
3. **健康指标** – BMI、BMR、TDEE 计算
4. **营养汇总** – 热量与四大营养素（碳水/蛋白质/脂肪/纤维）
5. **饮水时间轴** – 全天饮水记录
6. **三餐明细** – 食物项、份量、热量估算
7. **运动记录** – 活动类型、时长、消耗
8. **AI 点评** – 个性化健康洞察与建议
9. **风险预警** – 基于记录数据的健康风险评估
10. **次日方案** – 饮食/饮水/运动建议清单

### 周报结构

1. **核心概览** – 周平均分、最佳/最差日
2. **趋势图表** – 体重波动、每日热量摄入、步数统计
3. **营养环形图** – 平均宏量营养素分布
4. **AI 深度分析** – 跨天模式识别与干预建议

---

## 📦 项目结构

```
health-mate/
├── scripts/
│   ├── health_report_pro.py      # 日报生成器
│   ├── weekly_report_pro.py      # 周报生成器
│   ├── pdf_generator.py          # PDF 渲染引擎
│   ├── weekly_pdf_generator.py   # 周报 PDF 渲染
│   ├── i18n.py                   # 双语语言层
│   ├── constants.py              # 食物热量数据库
│   ├── init_config.py            # 交互式配置向导
│   ├── daily_health_report_pro.sh    # 定时任务脚本（日报）
│   └── weekly_health_report_pro.sh   # 定时任务脚本（周报）
├── config/
│   ├── user_config.json          # 用户健康档案
│   ├── .env                      # 环境变量（已加入 gitignore）
│   ├── .env.example              # 环境变量模板
│   ├── pdf_style_config.json     # PDF 样式配置
│   └── user_config.example.json  # 档案模板
├── assets/
│   └── NotoSansSC-VF.ttf         # 中文字体（自动下载）
├── logs/                         # 执行日志
├── reports/                      # 生成的 PDF 报告
├── README.md                     # 英文文档
├── README_ZH.md                  # 中文文档
├── SKILL.md                      # OpenClaw 技能定义
└── requirements.txt              # Python 依赖
```

---

## 🔐 隐私与数据保护

### 受 `.gitignore` 保护的文件

以下文件**严禁提交**到公开仓库：

- `config/user_config.json` – 个人健康数据
- `config/.env` – Webhook Token 和私密配置
- `reports/*.pdf` – 生成的健康报告
- `logs/*.log` – 执行日志

### 推荐实践

1. **私有仓库** – Fork 时设置为 Private
2. **定期备份** – 备份配置文件到安全存储
3. **密钥轮换** – 每 3-6 个月更新 Webhook Token
4. **沙箱测试** – 先在隔离环境中测试
5. **日志审计** – 定期检查 Webhook 访问日志

---

## 🔄 版本历史

### v1.3.1 — 2026-03-20

- 🔐 **协议同步**：将 `README`、`SKILL.md` 与 `soul.md` 的记忆落盘规则同步为同一强约束版本
- 🧾 **解析安全**：明确饮水块只能有两行，禁止在模板外追加状态、点评或说明字段
- 🏷️ **版本更新**：文档与技能元数据统一升级到 `1.3.1`

### v1.3.0 — 2026-03-20

- 🌐 **双语架构**：新增 i18n.py 统一中英文语言层
- 📝 **记忆协议**：强化反点评规则，提供中英双模板
- 🔧 **解析增强**：改进双语餐次/饮水/运动块检测
- 🎨 **PDF 修复**：解决 PDF 中 Emoji 渲染方块乱码 (☒) 问题
- 💊 **用药追踪**：支持自定义模块（如用药记录）
- 📚 **文档重构**：完成中英文 README 专业化重写

### v1.2.0 — 2026-03-20

- 🎯 **动态目标**：重构病理参数支持灵活健康目标（如减脂）
- 🌍 **多语言文档**：新增双语文档和自定义模块支持
- 🧹 **严格协议**：重写记忆落盘铁律锁定 LLM 输出
- 🐛 **Bug 修复**：修复 PDF Emoji 渲染和解析容错问题

### v1.1.x — 早期版本

- 周报系统上线（极坐标图表 + 趋势分析）
- Matplotlib 可视化（营养环形图、饮水柱状图、进度追踪）
- 中文字体自动下载支持
- 隐私合规更新与安全声明

---

## 📄 许可证

MIT License – 详见 [LICENSE](LICENSE) 文件。

---

## 📞 技术支持

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **电子邮箱**: tqd354@gmail.com
- **项目仓库**: https://github.com/tankeito/Health-Mate
