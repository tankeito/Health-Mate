[English](README.md) | 中文

# 🏥 Health-Mate | 个人智能健康管家

> 您的智能健康伴侣，专为 OpenClaw 打造
> *将日常习惯转化为临床级洞察。精准追踪营养、饮水、运动与病理指标，全自动渲染包含日报、周报、月报的 SaaS 级专业 PDF 报告——且所有数据 100% 本地私有。*

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 项目概述

Health-Mate 是一款**生产就绪的双语健康管理技能**，它填补了普通打卡 APP 与临床慢病监测系统之间的技术空白。

---

## ⚙️ 工作流与底层架构

采用高健壮性的三阶段本地处理管线：

1. **数据摄入 (NLP to Markdown)**：OpenClaw 大模型将日常对话式打卡，转化为符合严格正则规范的 Markdown 文本并落盘至 `MEMORY_DIR`。

2. **动态病理计算引擎 (Python)**：依靠高容错正则提取营养、饮水与运动向量。底层算法会根据您的**主病理目标**动态调整评分权重与红线阈值（例如：胆结石模式下严控 40g 脂肪上限，减脂模式下侧重热量缺口）。

3. **渲染与分发引擎**：`Matplotlib` 将枯燥矩阵渲染为精美高清 PDF（支持日报/周报/月报），并可通过 Webhook 自动推送至钉钉/飞书/Telegram。

---

## 📑 临床级 SaaS 报告展现

完全在本地离线渲染的商业级医疗可视化报表。Health-Mate 能将原始 Markdown 文本转化为结构严谨的高清 PDF：

- 📅 **健康日报 (细粒度追踪)**：将您的日常打卡转化为全景快照。包含多维度综合星级打分、精美的宏量营养素环形图、24 小时全天候饮水时间轴，以及 AI 靶向驱动的次日行动方案。

- 🗓 **健康周报 (趋势与复盘)**：专为中期健康复盘设计。引入了极具极客范的 GitHub 风格症状与用药热力图 (Heatmap)、7 天体重与热量趋势折线图，以及大模型深度的周度模式识别。

- 📊 **健康月报 (病理深度洞察)**：媲美顶级商业医疗 SaaS 的核心报表。涵盖宏观依从性雷达图、30 天基础代谢 (BMR) 平滑曲线、病理双轴对比图（直观呈现脂肪摄入与症状频次的因果关系）、营养素离散箱线图，以及基于常居地 (LBS) 的线下三甲/专科门诊智能规划建议。

---

## ⚠️ 隐私与安全闭环

Health-Mate 秉持绝对的"数据本地化"原则。

- 🔒 **无云端上传**：所有解析、AI 推理回退与 PDF 渲染默认在本地闭环完成。
- 📂 **内存严格隔离**：必须显式指定 `MEMORY_DIR`。为防止越权读取全局 Agent 记忆，未配置该路径时脚本将直接拦截退出，不再提供隐性兜底。
- 📡 **外网请求隔离**：仅在您主动配置 Webhook、Tavily API 或开启运行时字体下载时，才会触发对应外网请求。

---

## ✨ 核心特性

- 📈 **SaaS 级全景数据可视化**：一键生成排版精美的日报、周报、月报 PDF。
- 🏥 **LBS 医疗规划 (NEW)**：结合您的常居地配置与当前病历，AI 每月自动生成复查提醒与本地优选三甲/专科医院门诊建议。
- 🤖 **多病种联合管理**：内置胆结石、高血压、糖尿病、减脂方案，支持多并发症联合管理与动态靶向干预。
- 🧩 **模块高度自定义**：支持通过 `user_config.json` 动态挂载生化指标、血压、血糖等自定义监测与打分模块。
- 🌐 **双语与防乱码降级**：中文字体缺失时，自动生成临时英文 Memory 镜像并渲染带说明的英文 PDF 报告。

---

## 🚀 快速开始

### 1. 安装与依赖
```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 环境变量配置 (`config/.env`)
```bash
MEMORY_DIR="/您的绝对路径/memory" # 👈 必填项！
TAVILY_API_KEY="tvly-..." # 可选：增强型医学检索回退
DINGTALK_WEBHOOK="https://..." # 可选：多端推送
ALLOW_RUNTIME_FONT_DOWNLOAD="false" # 可选：允许自动下载缺失字体
```

### 3. 初始化档案
```bash
python scripts/init_config.py
```
*交互式向导：配置您的身高体重、多病种标签、用药打分及常居地（用于医院推荐）。*

### 4. 生成报告 (支持日/周/月)
```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

---

## 📝 AI 记忆落盘铁律

当助手往 `MEMORY_DIR` 写入内容时，必须像"无情的机器记录仪"一样工作。严禁写入点评、建议、总结、Emoji 或聊天腔调。

<details>
<summary><b>👉 点击展开：大模型必须严格遵守的 Markdown 落地模板</b></summary>

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
</details>

---

## 🔗 更新履历

### v1.4.0 — 2026-03-21
- 📅 **月度深度复盘**：全新上线月报 PDF 流程，包含宏观依从性雷达图、30 天体重/BMR 趋势图、脂肪/碳水箱线图及专科病理图表。
- 🗺 **LBS 门诊规划**：新增基于配置常居地的复查提醒与医院/门诊智能推荐建议。
- 🌡 **热力图引擎**：周报与月报全面引入 GitHub 风格的症状与用药热力图 (Heatmap)。
- 🔒 **安全加固**：彻底移除隐性 MEMORY_DIR 兜底路径，必须显式配置以防止越权。
- 🛡 **高可用回退**：增强了 LLM 失败时的本地断网回退逻辑，确保报告仍能基于真实数据生成输出。

### v1.3.0 — 2026-03-20
- 🌐 双语架构：新增 i18n.py 统一中英文语言层
- 📝 记忆协议：强化反点评规则，提供中英双模板
- 🔧 解析增强：改进双语餐次/饮水/运动块检测
- 🎨 PDF 修复：解决 PDF 中 Emoji 渲染方块乱码 (☒) 问题
- 💊 用药追踪：支持自定义模块（如用药记录）

### v1.2.0 — 2026-03-20
- 🎯 动态目标：重构病理参数支持灵活健康目标（如减脂）
- 🌍 多语言文档：新增双语文档和自定义模块支持
- 🧹 严格协议：重写记忆落盘铁律锁定 LLM 输出
- 🐛 Bug 修复：修复 PDF Emoji 渲染和解析容错问题

---

## 📦 项目结构

```
health-mate/
├── scripts/
│   ├── health_report_pro.py          # 日报生成器
│   ├── weekly_report_pro.py          # 周报生成器
│   ├── monthly_report_pro.py         # 月报生成器 (NEW)
│   ├── pdf_generator.py              # 日报 PDF 渲染引擎
│   ├── weekly_pdf_generator.py       # 周报 PDF 渲染
│   ├── monthly_pdf_generator.py      # 月报 PDF 渲染 (NEW)
│   ├── i18n.py                       # 双语语言层
│   ├── constants.py                  # 食物热量数据库
│   ├── init_config.py                # 交互式配置向导
│   ├── daily_health_report_pro.sh    # 定时任务脚本（日报）
│   ├── weekly_health_report_pro.sh   # 定时任务脚本（周报）
│   └── monthly_health_report_pro.sh  # 定时任务脚本（月报）(NEW)
├── config/
│   ├── user_config.json              # 用户健康档案
│   ├── .env                          # 环境变量（已加入 gitignore）
│   ├── .env.example                  # 环境变量模板
│   ├── pdf_style_config.json         # PDF 样式配置
│   └── user_config.example.json      # 档案模板
├── assets/
│   └── NotoSansSC-VF.ttf             # 中文字体（自动下载）
├── logs/                             # 执行日志
├── reports/                          # 生成的 PDF 报告
├── README.md                         # 英文文档
├── README_ZH.md                      # 中文文档
├── SKILL.md                          # OpenClaw 技能定义
└── requirements.txt                  # Python 依赖
```

---

## 📄 许可证

MIT License – 详见 [LICENSE](LICENSE) 文件。

---

## 📞 支持与资源

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **Maton 文档**: https://maton.ai/docs
- **Google Docs API**: https://developers.google.com/workspace/docs/api
- **电子邮箱**: tqd354@gmail.com

---

## 🙏 致谢

- **Maton** – 提供 OAuth 托管的 API 网关
- **Google Workspace** – 提供强大的 Docs API
- **OpenClaw** – 提供 AI 助手平台
