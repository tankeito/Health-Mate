[English](README.md) | 中文 | [日本語](README_JP.md)

# 🏥 Health-Mate | 面向 OpenClaw 的本地优先智能健康报告系统

> 一套支持多语种、具备"双引擎架构"（医疗慢病管理 vs 均衡减脂体态）的高级健康报告生成系统。
>
> 将本地 Markdown 健康记录转化为专业的日报、周报、月报 PDF，支持病种感知评分、专项图表、医疗规划及可选的消息推送。

[![Version](https://img.shields.io/badge/version-1.5.2-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 为什么选择 Health-Mate

Health-Mate 介于"普通打卡工具"和"临床自我管理仪表盘"之间。

- 🧠 **病种感知**：内置胆结石、高血压、糖尿病、健身减脂和多病种联合管理逻辑
- 📄 **报告优先**：生成结构清晰的日报、周报、月报 PDF，包含图表、洞察和可执行建议
- 🔒 **本地优先**：解析、评分、规则回退和 PDF 渲染默认都在本地完成
- 🧩 **高度可扩展**：支持血压、血糖、体脂、生化、用药和自定义监测模块
- 🌐 **多语言支持**：全面支持中文、英文、日文（`zh-CN`、`en-US`、`ja-JP`），自动适配目标语言的医疗排版习惯与字体渲染回退机制

---

## 📊 三类报告能解决什么问题

### 🌅 健康日报 —— 当日复盘与次日微调

**解答**：*"今天做得怎么样？明天怎么改？"*

**核心模块**：
- 📊 **动态营养环形图**：宏观营养素依从性可视化（蛋白质、脂肪、碳水、纤维）
- 📈 **摄入堆叠柱状图**：进食、饮水、运动在时间轴上的分层展示
- ⚠️ **风险预警**：基于病种的专项警告（如胆结石脂肪过低、高血压钠摄入过高）
- 📋 **次日可执行干预清单**：具体、可执行的明日调整方案（具体食物、饮水目标、运动目标）

**使用场景**：每日复盘、即时行为纠正、保持执行动力

---

### 🗓 健康周报 —— 习惯养成与短期波动分析

**解答**：*"哪些行为稳定了？哪些问题在重复出现？"*

**核心模块**：
- 🎯 **周核心指标雷达图**：多维度概览（热量、宏观营养素、饮水、步数、睡眠等）
- 🔥 **习惯与运动热力图**：`balanced` / `fat_loss` 模式的 GitHub 风格贡献图
- 📉 **双轴对比趋势图**：体重 + 能量平衡、步数 + 饮水、症状频次 + 诱因暴露
- 🏥 **疾病模式**：症状 - 用药关联热力图（慢性病专用）
- 💪 **健身模式**：四周习惯养成趋势条、能量收支瀑布图
- 📝 **亮点与待改进**：本周进步点、下周关注重点

**使用场景**：周度复盘、识别行为模式、在月度检查点前调整策略

---

### 📊 健康月报 —— 深度分析与长期策略

**解答**：*"当前策略是否有效？是否需要线下转诊或升级干预？"*

**核心模块**：
- 🎯 **宏观依从性雷达图**：30 天营养模式概览
- 🔥 **活动热力图**：整月 GitHub 风格图表（生活方式模式）或症状 - 用药热力图（疾病模式）
- 📈 **30 天体重与基础代谢趋势**：平滑曲线 + 重大事件标注
- 🏥 **专项图表**：基于病种的深度分析可视化
- 🧠 **AI 月度研判**：LLM 生成的趋势、风险和建议综合报告
- 🏥 **医疗规划模块**（仅疾病模式）：
  - 医院优先推荐（顶级三甲 > 三甲 > 区域医疗中心）
  - 科室与医生匹配，附带擅长领域说明
  - 基于诊疗指南的复查提醒
- 🏃 **生活方式干预清单**（仅健身模式）：
  - 次月宏观营养与训练调整方案
  - 体成分目标（去脂体重 vs 脂肪量）
  - 习惯叠加建议

**使用场景**：月度战略复盘、医疗随访规划、重大方向调整

---

## 🧬 双引擎动态人群分层

Health-Mate 根据 `user_config.json` 中的 `population_branch` 设置，智能切换底层报告引擎。

### 🏥 慢病与专科管理模式（Disease Management）

**触发条件**：`gallstones`（胆结石）、`hypertension`（高血压）、`diabetes`（糖尿病）等慢性病

**报告特征**：
- 🩺 **病理体征深度对齐图**：脂肪摄入 vs 症状频次（胆结石）、血压箱线图（高血压）、血糖趋势（糖尿病）
- 💊 **用药依从性分析**：服药时机、漏服记录、与症状的相关性
- ⚠️ **高危饮食诱因识别**：与症状发作相关的食物关联分析
- 🏥 **医院与医生推荐**（仅月报）：
  - LLM 生成的结构化建议（医院 → 科室 → 医生）
  - Tavily 检索兜底，获取循证医学支持的本地候选医院
  - 优先推荐公立顶级三甲医院和大学附属医疗中心
  - 证据充足时输出真实医生姓名与职称

**输出示例**（胆结石月报）：
- 脂肪摄入 vs 症状频次双轴图
- 脂肪/碳水摄入离散度箱线图
- 症状占比环形图
- 医院推荐："四川省人民医院 → 肝胆外科 → 周永碧【主任医师】"

---

### 🏃 均衡与体态管理模式（Fitness & Wellness）

**触发条件**：`balanced`（均衡健康）、`fat_loss`（减脂）或一般健康优化

**报告特征**：
- 📊 **去医疗化可视化**：无症状追踪、无医院推荐
- 🔥 **四周习惯养成趋势**：堆叠柱状图展示关键行为一致性
- ⚖️ **能量收支瀑布图**：热量摄入 vs 消耗 vs 缺口/盈余
- 💪 **体成分深度分析**：去脂体重（LBM）vs 脂肪量趋势、体脂率平滑曲线
- 🎯 **次月宏观营养与训练计划**：
  - 蛋白质目标调整（肌肉保留）
  - 训练前后碳水时机
  - 训练量进阶（组数、次数、强度）

**输出示例**（减脂月报）：
- 30 天体重趋势平滑曲线
- 体脂率趋势图
- 能量收支瀑布图
- 四周习惯养成（步数、训练、蛋白质摄入、睡眠）
- 次月干预方案："蛋白质提升至 2.0g/kg，增加 2 次抗阻训练，维持 500kcal 缺口"

---

## ⚙️ 核心技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **PDF 渲染** | ReportLab 4.0+ | 专业级 PDF 生成，支持自定义样式、多语言字体、精确布局控制 |
| **数据可视化** | Matplotlib 3.0+ | 统计图表（雷达图、热力图、箱线图、双轴趋势），支持病种专属样式 |
| **LLM 集成** | OpenClaw Local Agent + Tavily API | 混合研判架构：本地 LLM 生成 AI 点评和医院推荐，Tavily 用于循证医学 web 检索兜底 |
| **任务调度** | Cron + OpenClaw HEARTBEAT | 自动化日报/周报/月报生成，支持钉钉/飞书/Telegram 推送 |

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 配置环境变量

ClawHub 手动上传文件夹可能不包含 `config/.env.example`。请打开 `config/user_config.example.json`，查看顶层 `env` 块作为上传安全参考。

设置向导会在 `config/.env` 不存在时自动创建带注释的项目本地模板。

```bash
# ========== Cron 环境变量（定时任务必需） ==========
NVM_DIR="/root/.nvm"
CRON_PATH="/root/.nvm/versions/node/v22.22.0/bin:/root/.local/bin:/root/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/usr/local/bin:/usr/bin:/bin:/root/.npm-global/bin"

# ========== 必需配置 ==========
MEMORY_DIR="/root/.openclaw/workspace/memory"

# ========== 可选配置 ==========
OPENCLAW_BIN="/root/.nvm/versions/node/v22.22.0/bin/openclaw"  # 定时任务推荐设置
LOG_FILE="/root/.openclaw/logs/health_report_pro.log"

# 消息推送（可选）
DINGTALK_WEBHOOK="https://..."
FEISHU_WEBHOOK="https://..."
TELEGRAM_BOT_TOKEN="..."
TELEGRAM_CHAT_ID="..."

# AI 功能（可选）
TAVILY_API_KEY="tvly-..."

# PDF 报告（可选）
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://example.com/reports"

# 字体下载（默认：false）
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. 运行配置向导

```bash
python scripts/init_config.py
```

向导会将所有持久化设置写入 `config/user_config.json`：
- 基本信息档案
- 活跃病种列表与主病种
- 评分模块与权重配置
- 用药模块设置
- 常居地（用于月报医疗规划）
- 自定义监测模块
- `report_preferences.population_branch`（生活方式 vs 疾病管理路由）
- 报告与 AI 生成偏好

### 4. 生成报告

```bash
# 日报
python scripts/daily_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20

# 周报
python scripts/weekly_report_pro.py 2026-03-20

# 月报
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. 可选 Shell 运行器（用于 Cron）

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

**Cron 环境说明**：如果您的定时 Shell 不继承交互式 Node/NVM `PATH`，请在 `config/.env` 中设置 `OPENCLAW_BIN`。日报运行器和 Python 控制器都将其作为本地 LLM 执行的首选解析器。

如果未设置 `OPENCLAW_BIN`，Python 运行器会尝试常见安装位置：
- `/root/.nvm/versions/node/*/bin/openclaw`
- `/usr/local/bin/openclaw`
- `/usr/bin/openclaw`
- Windows 标准 Node.js 路径

### 6. 可选英文记忆镜像

```bash
python scripts/export_memory_en.py
```

使用场景：
- 创建本地记忆文件的英文镜像
- 中文字体不可用时的英文渲染路径
- 报告输出的双语回归测试

---

## ⚙️ 配置参考

### `config/user_config.json`

主长期档案文件，存储：
- 用户基本信息
- 活跃病种与主病种
- 启用的评分模块与权重
- 用药设置
- 常居地元数据
- 自定义监测模块
- 报告偏好
- AI 生成偏好

**重要**：`report_preferences.population_branch`
- 支持值：`lifestyle` / `disease`
- 示例配置默认从 `lifestyle` 开始
- 设置向导对 `balanced` / `fat_loss` 自动建议 `lifestyle`，对疾病管理目标建议 `disease`

### 常用运行时变量

| 变量 | 必需 | 用途 |
|------|------|------|
| `MEMORY_DIR` | 是 | 指向健康记忆目录 |
| `TAVILY_API_KEY` | 否 | 启用 Tavily 检索兜底 |
| `DINGTALK_WEBHOOK` | 否 | 推送文字摘要和 PDF 链接到钉钉 |
| `FEISHU_WEBHOOK` | 否 | 推送文字摘要和 PDF 链接到飞书 |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | 否 | 推送文字摘要和 PDF 链接到 Telegram |
| `REPORT_WEB_DIR` | 否 | 将生成的 PDF 复制到 Web 目录 |
| `REPORT_BASE_URL` | 否 | 构建推送消息中的公开 PDF URL |
| `ALLOW_RUNTIME_FONT_DOWNLOAD` | 否 | 允许运行时字体下载（默认：false） |

---

## 📝 记忆写入协议

当助手写入 `MEMORY_DIR` 时，必须表现得像**严格的数据记录仪**。

### 硬性规则

- ❌ 禁止点评
- ❌ 禁止鼓励
- ❌ 禁止总结
- ❌ 禁止使用 Emoji
- ❌ 禁止聊天填充词

### 结构规则

- ✅ 进食、饮水、用药、运动事件必须使用**三级标题**并附带时间标记（如 `### 早餐（约 08:50）`）
- ✅ 饮水块必须保持最小化和稳定（仅饮水量 + 累计）
- ✅ 每日步数总计必须放在**专用的二级章节**内（`## 今日步数`）
- ✅ 自定义监测模块必须保持稳定的二级章节名称
- ✅ 避免在一个数据块内混合使用多种语言

### 最小示例

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
- 燕麦片 50g → 约 190kcal
- 脱脂牛奶 250ml → 约 87kcal

## 运动记录
### 下午骑行（约 17:10）
- 距离：10.2km
- 耗时：42 分钟
- 消耗：约 290kcal

## 今日步数
- 总步数：8200 步
```

### 可扩展监测模块

```markdown
## 血压记录
### 早晨（约 08:00）
- 血压：128/82 mmHg
- 心率：72 bpm

## 血糖记录
### 早餐后（约 10:10）
- 血糖：7.1 mmol/L
- 时机：早餐后 2 小时

## 体成分记录
- 体重：64.4kg
- 体脂率：18.6%

## 生化指标
- ALT: 34 U/L
- AST: 28 U/L
```

### 禁止内容

- `评估`
- `状态`
- `总结`
- 激励性填充词
- 调试日志
- 系统日志

---

## 🔤 字体回退

### 推荐 CJK 字体

- `assets/NotoSansSC-VF.ttf`（中文）
- `assets/NotoSansJP-VF.ttf`（日文）

### 如果必需字体缺失

- 渲染器切换到英文安全渲染路径
- PDF 添加渲染说明
- **中文 PDF 用户**：将 `NotoSansSC-VF.ttf` 放入 `assets/` 目录
- **日文 PDF 用户**：将 `NotoSansJP-VF.ttf` 放入 `assets/` 目录

---

## 🧪 故障排查

### `MEMORY_DIR` 缺失

**症状**：Shell 运行器立即停止并报错

**解决方案**：
- 在 `config/.env` 或运行时环境中显式设置 `MEMORY_DIR`
- ClawHub 手动上传用户：从 `config/user_config.example.json` → `env` 复制 `MEMORY_DIR` 示例

### 月报医院推荐过于泛化

**症状**：医院推荐缺少具体医生姓名或感觉像模板

**解决方案**：
1. 确保 `config/user_config.json` 中配置了常居地
2. 确认本地 LLM 执行可用（定时任务请设置 `OPENCLAW_BIN`）
3. 配置 `TAVILY_API_KEY` 以启用检索增强兜底
4. 如果 LLM 暂时不可用，城市级本地规则层仍会尝试在存在策划数据时优先输出真实的"医院 + 医生"组合

### 中文/日文 PDF 回退到英文

**症状**：PDF 渲染为英文，尽管内容是中文/日文

**解决方案**：
- 必需 CJK 字体缺失
- 将 `assets/NotoSansSC-VF.ttf` 或 `assets/NotoSansJP-VF.ttf` 放入本地并重新生成

### 推送消息缺失

**症状**：报告已生成但未收到钉钉/飞书/Telegram 消息

**解决方案**：
- 检查 `config/.env` 中是否配置了对应的 webhook 变量
- 查看 `logs/` 目录中的运行时推送输出
- 验证 webhook URL 是否有效且未过期

---

## 🔒 隐私与本地优先设计

Health-Mate 围绕明确的隐私边界构建。

### 默认本地完成（无需联网）

- 📁 **Markdown 解析**：所有健康数据从本地 `MEMORY_DIR` 文件提取
- 📊 **评分与图表**：病种感知评分、统计计算、图表渲染
- 📄 **PDF 生成**：ReportLab 完全离线渲染 PDF
- 📝 **LLM 点评**：本地 `openclaw agent --local` 生成 AI 洞察（无需云端 API）

### 需要显式启用（可选）

- 🌐 **Tavily 检索**：仅当配置 `TAVILY_API_KEY` 时（用于医院推荐或兜底指导）
- 📤 **Webhook 推送**：仅当配置钉钉/飞书/Telegram 凭证时
- ⬇️ **运行时字体下载**：默认禁用；仅当显式设置 `ALLOW_RUNTIME_FONT_DOWNLOAD=true` 时允许

### 推荐部署方式

```bash
# 使用虚拟环境或容器隔离
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 显式设置 MEMORY_DIR 为私有目录
export MEMORY_DIR="$HOME/.health-mate/memory"

# 除非需要，否则不要配置 webhook 或 Tavily
# 不设置 TAVILY_API_KEY 和 WEBHOOK_URLs 以最大化隐私保护
```

---

## 📁 项目结构

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

## 📬 技术支持

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **仓库**: https://github.com/tankeito/Health-Mate
- **邮箱**: tqd354@gmail.com

---

**Health-Mate** | 本地优先多语言健康报告系统

**Developed by tankeito** | MIT License | 2026
