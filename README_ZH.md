[English](README.md) | 中文 | [日本語](README_JP.md)

# 🏥 Health-Mate

> 面向 OpenClaw 的本地优先智能健康报告技能。
>
> 将结构化 Markdown 健康记录自动转换为专业化的日报、周报、月报 PDF，并可选推送文字版摘要到外部 Webhook。

[![Version](https://img.shields.io/badge/version-1.4.1-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## ✨ Health-Mate 是什么

Health-Mate 介于“习惯打卡工具”和“慢病自我管理面板”之间。

- 🧠 病种感知：内置胆结石 / 慢性胆囊炎、糖尿病、高血压、健身减脂，以及多疾病并行管理逻辑。
- 📄 报告优先：日报、周报、月报是核心产物，不只是顺带导出。
- 🔒 本地优先：解析、评分、本地回退、PDF 渲染默认都在本地完成。
- 🧩 可扩展：支持用药、血压、血糖、生化、体脂、睡眠等自定义监控模块。
- 🌏 多语言准备：中英文报告链路稳定可用，`1.4.1` 新增了日文说明文档和日文字体资源。

---

## 📦 报告矩阵

| 报告 | 关注重点 | 常见输出 |
| --- | --- | --- |
| 日报 | 当日复盘 | 综合评分、营养环图、饮水详情、运动详情、AI 点评、风险预警、次日方案 |
| 周报 | 趋势回顾 | 周指标总览、热力图、趋势图、周复盘、下周方案、自定义监控汇总 |
| 月报 | 专科深挖 | 雷达图、健康热力图、30 天体重/BMR 趋势、专科图表、月度 AI 研判、医院医生建议 |

---

## ⚙️ 工作原理

1. **结构化记忆写入**
   OpenClaw 把每日对话整理成固定结构的 Markdown，并写入 `MEMORY_DIR`。
2. **本地健壮解析**
   Python 从 Markdown 中提取饮食、饮水、体重、症状、用药、运动、步数和自定义监控模块。
3. **病种感知评分**
   目标值、预警阈值和评分重点会根据主疾病和多疾病组合自动调整。
4. **洞察生成与渲染**
   先尝试本地 OpenClaw LLM；若失败，则回退到本地规则，并在启用 Tavily 时叠加检索内容，最后生成 PDF 和可选文字推送。

---

## 🧭 AI 来源标签说明

报告中的 AI 相关内容会明确标注来源。

| 标签 | 含义 |
| --- | --- |
| `来源：LLM 动态生成` | 本地 `openclaw agent --local` 成功返回结果 |
| `来源：Tavily 检索 + 本地规则` | 本地 LLM 失败或不可用，且启用了 Tavily 增强回退 |
| `来源：本地规则` | 本地 LLM 失败或不可用，最终使用纯本地规则 |

为什么“定时任务”和“你在 OpenClaw 里手动测试”可能出现不同来源：

- 定时任务走的是 shell 运行环境，并由 `config/.env` 提供环境变量
- 手动测试往往运行在更完整的交互式环境里
- shell 环境里只要本地 LLM 无法成功执行，日报就会退回 `Tavily 检索 + 本地规则` 或 `本地规则`

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 配置运行环境

至少需要在 `config/.env` 中设置：

```bash
MEMORY_DIR="/absolute/path/to/health-memory"
```

可选项：

```bash
TAVILY_API_KEY="tvly-..."
DINGTALK_WEBHOOK="https://..."
FEISHU_WEBHOOK="https://..."
TELEGRAM_BOT_TOKEN="..."
TELEGRAM_CHAT_ID="..."
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://example.com/reports"
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. 运行初始化向导

```bash
python scripts/init_config.py
```

现在的向导已经覆盖 `user_config.json` 的主要运行逻辑：

- 基本档案
- 多疾病 / 多目标配置
- 饮水和步数目标
- 常居地
- AI 模式
- 评分模块与权重
- 用药模块
- 自定义监控模块
- Tavily 配置
- 报告偏好

### 4. 生成报告

```bash
python scripts/daily_health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. 使用 shell 定时脚本

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

### 6. 可选：导出英文 memory 镜像

```bash
python scripts/export_memory_en.py /path/to/memory /path/to/output
```

适用场景：

- 生成英文版 memory
- 缺少中文字体时，走英文安全渲染路径
- 中英文输出回归验证

---

## 🧪 日报 / 周报 / 月报亮点

### 日报

- 支持自定义模块的综合评分表
- 营养摄入环形图与明细表
- 饮水详情与运动详情
- 启用后同步输出用药情况
- AI 点评、风险预警、次日可执行清单

### 周报

- 带状态 Badge 的周指标总览
- 健康 / 用药热力图
- 体重、热量、饮水、步数、营养趋势图
- 本周亮点、风险点、下周方案
- 自定义监控汇总

### 月报

- 宏观依从性雷达图
- 健康热力图
- 30 天体重与 BMR 趋势
- 按主疾病动态切换的专科图表
- AI 月度病情研判
- 复查提醒
- 医院优先、医生细化的就医规划

---

## 🏥 月报医疗规划

月报医疗推荐优先级：

1. LLM 先生成“医院优先”的推荐
2. 若不足，再走 Tavily 辅助检索
3. 再不足，最后走结构化本地规则

月报中的医疗规划尽量输出：

- 医院名称
- 推荐科室
- 医生姓名与职称
- 医院优势
- 医生擅长
- 与当前病情的契合理由

优先顺序：

- 顶级三甲医院
- 三甲医院
- 区域医疗中心

---

## 🔐 隐私与运行边界

预期本地文件行为：

- 从 `MEMORY_DIR` 读取 Markdown 健康记录
- 使用 shell 运行器时读取 `config/.env`
- 向 `reports/` 写入 PDF
- 向 `logs/` 写入运行日志
- 在字体回退时，临时创建英文 memory 镜像

预期网络行为：

- 只有配置了 `TAVILY_API_KEY` 才会使用 Tavily
- 只有配置了 Webhook 才会对外推送
- 只有显式启用 `ALLOW_RUNTIME_FONT_DOWNLOAD=true` 才允许运行时下载字体

重要提醒：

- `MEMORY_DIR` 必须显式配置
- shell 运行器没有隐式默认 memory 路径
- 升级或重装前，请务必备份 `config/user_config.json` 和 `config/.env`
- 某些平台升级流程可能会重置本地配置文件

---

## 🔤 字体与语言说明

项目内置字体：

- `assets/NotoSansSC-VF.ttf`：中文渲染
- `assets/NotoSansJP-VF.ttf`：日文字形覆盖与日文文档支持

当前行为：

- 如果请求中文报告且缺少 `assets/NotoSansSC-VF.ttf`，系统会自动导出英文 memory 镜像，并生成带提示的英文回退报告
- `1.4.1` 已新增 `ja-JP` 语言别名和日文字体资源
- 目前解析模板和完整报告文案仍以中文 / 英文链路最稳定

项目主页：

- [Health-Mate GitHub 仓库](https://github.com/tankeito/Health-Mate)

---

## 📝 MEMORY 写入协议

当 LLM 向 `MEMORY_DIR` 写入时，必须像“严格的数据记录仪”。

强制规则：

1. 禁止写入点评、建议、总结、Emoji 或聊天废话。
2. 餐次、饮水、用药事件、运动事件必须使用带时间的三级标题。
3. 步数只能放在一个固定的二级标题块里。
4. 自定义监控模块必须保持稳定的二级标题，不能今天一个名字、明天一个名字。

英文模板：

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

中文模板：

```markdown
# 2026-03-20 健康记录

## 饮食记录
### 早餐（约 08:30）
- 燕麦片 50g -> 约 190kcal
- 脱脂牛奶 250ml -> 约 87kcal

## 饮水记录
### 上午（约 09:45）
- 饮水量：300ml
- 累计：300ml/2000ml

## 运动记录
### 下午骑行（约 17:17）
- 距离：10km
- 耗时：47分钟
- 消耗：约 300kcal

## 今日步数
- 总步数：8500 步
```

监控模块示例：

```markdown
## 血压记录
### 上午（约 08:00）
- Blood Pressure: 128/82 mmHg
- Heart Rate: 72 bpm

## 血糖记录
### 早餐后（约 10:10）
- Glucose: 7.1 mmol/L
- Timing: 2h after breakfast

## 生化情况
- ALT: 34 U/L
- AST: 28 U/L
```

---

## 🗂️ 项目结构

```text
health-mate/
├── assets/
│   ├── NotoSansSC-VF.ttf
│   └── NotoSansJP-VF.ttf
├── config/
│   ├── user_config.example.json
│   ├── user_config.json
│   ├── .env
│   └── pdf_style_config.json
├── reports/
├── scripts/
│   ├── daily_health_report_pro.py
│   ├── daily_pdf_generator.py
│   ├── weekly_report_pro.py
│   ├── weekly_pdf_generator.py
│   ├── monthly_report_pro.py
│   ├── monthly_pdf_generator.py
│   ├── export_memory_en.py
│   └── init_config.py
├── README.md
├── README_ZH.md
├── README_JP.md
├── SKILL.md
└── _meta.json
```

---

## 🆕 更新记录

### v1.4.1 — 2026-03-22

- 将 `health_report_pro.py` 重命名为 `daily_health_report_pro.py`
- 将 `pdf_generator.py` 重命名为 `daily_pdf_generator.py`
- 修正所有导入、shell 调用、usage 文案与文档引用
- 扩展 `init_config.py`，覆盖主要运行配置项
- 新增日文说明文档与 `assets/NotoSansJP-VF.ttf`
- 增加 `ja-JP` 语言别名与更安全的语言回退逻辑
- 同步 README、`SKILL.md`、`_meta.json` 到 `1.4.1`

### v1.4.0 — 2026-03-21

- 新增月报生成链路
- 新增医院 / 医生推荐规划
- 新增健康热力图和专科图表
- 强化 `MEMORY_DIR` 显式配置要求

---

## 📄 License

MIT。详见 [LICENSE](LICENSE)。
