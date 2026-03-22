[English](README.md) | 中文

# 🏥 Health-Mate | 面向 OpenClaw 的本地优先智能健康报告系统

> 一套真正用于长期健康管理的本地化报告工具。
>
> Health-Mate 读取本地 Markdown 健康记录，自动生成健康日报、周报、月报，并支持多病种管理、专项图表、复查提醒、医院医生推荐以及可选的文字推送与 PDF 推送。

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 为什么是 Health-Mate

Health-Mate 介于“普通打卡工具”和“临床自我管理仪表盘”之间。

- 🧠 **病种感知**：内置胆结石、高血压、糖尿病、健身减脂和多病种联合管理逻辑
- 📄 **报告优先**：不仅记录数据，更把数据整理为结构清晰、可复盘、可执行的 PDF 报告
- 🔒 **本地优先**：解析、评分、规则回退和 PDF 渲染默认都在本地完成
- 🧩 **高度可扩展**：支持血压、血糖、体脂、生化、用药和自定义监测模块
- 🌐 **双语支持**：支持中英文报告，并提供缺少中文字体时的英文安全渲染路径

---

## 📑 三类报告能解决什么问题

| 报告类型 | 主要用途 | 核心内容 | 主要回答的问题 |
| --- | --- | --- | --- |
| 🌅 健康日报 | 当日复盘、次日调整 | 综合评分、营养图、饮水详情、运动详情、风险预警、次日方案 | 今天做得怎么样？明天怎么改？ |
| 🗓 健康周报 | 周度趋势复盘 | 周核心指标、热力图、趋势图、亮点、待改进项、下周重点 | 这周哪些行为稳定了？哪些问题在重复出现？ |
| 📊 健康月报 | 病种深度分析、线下规划 | 雷达图、热力图、30 天趋势、专项图、AI 研判、复查提醒、医院医生建议 | 当前策略是否有效？是否需要门诊复查、进一步评估或升级干预？ |

---

## ⚙️ 工作流与底层架构

Health-Mate 采用分层本地处理链路：

1. **记忆写入层**
   OpenClaw 把日常对话式打卡整理为结构化 Markdown，并写入 `MEMORY_DIR`
2. **结构化解析层**
   Python 从 Markdown 中提取饮食、饮水、体重、运动、症状、用药、步数与自定义监测数据
3. **病种评分层**
   根据主病种和联合病种动态调整阈值、权重、风险判断与提示逻辑
4. **洞察与渲染层**
   优先使用 LLM 输出点评和建议；失败时回退到本地规则和可选 Tavily 检索，最后输出文字版摘要与 PDF

---

## 🧬 内置病种管理能力

当前支持：

- 胆结石 / 慢性胆囊炎
- 高血压
- 糖尿病
- 健身减脂 / 体成分管理
- 多病种联合管理

病种会影响：

- 热量、脂肪、纤维、饮水、运动等目标区间
- 评分模块与权重重点
- AI 点评与次日方案提示词
- 周报 / 月报复查提醒
- 月报专项图表选择
- 月报医院医生推荐逻辑

---

## 🏥 月报中的医院与医生推荐

月报中的医疗规划模块采用“医院优先”的推荐策略，而不是只给一个模糊科室。

推荐优先级：

1. **LLM 优先**
   优先让本地 LLM 生成“医院 → 科室 → 医生”的结构化建议，并尽量输出真实医生姓名与职称
2. **Tavily 检索兜底**
   如果 LLM 不可用或结果不足，再从 Tavily 收集本地权威医院候选
3. **本地规则回退**
   即使前两层都不可用，也会输出结构化建议；如果内置了城市级知识，会尽量优先输出真实的“医院 + 医生”组合，而不是泛化门诊占位词

排序原则：

- 顶级三甲医院 > 三甲医院 > 区域医疗中心
- 优先公立三甲、大学附属三甲、国家或区域医疗中心
- 先评估医院平台实力，再评估科室，再匹配医生
- 只要证据足够，就优先输出真实医生姓名与职称
- 结合症状频次、复查提醒、多病种风险做个体化匹配

月报中的推荐内容会尽量输出：

- 医院名称
- 推荐科室
- 推荐医生
- 医院优势
- 医生擅长
- 与当前患者情况的契合理由

---

## 📊 月报专项图表示例

月报会根据病种与已有数据动态选择图表。

典型输出包括：

- 胆结石：脂肪摄入 vs 症状频次双轴图
- 胆结石：脂肪 / 碳水摄入离散度箱线图
- 胆结石：症状占比环形图
- 高血压：30 天血压箱线图
- 糖尿病：血糖监测趋势图
- 健身减脂：体重与体脂率平滑趋势图
- 自定义监测：血压、血糖、生化等数值型趋势图

---

## 🔒 隐私与安全边界

Health-Mate 默认遵循“本地优先”的安全边界。

- `MEMORY_DIR` 必须显式配置，不再存在隐式默认目录
- Markdown 解析、评分和 PDF 渲染默认在本地完成
- 报告与日志写入当前项目目录
- 只有在你显式启用时，才会发生出站请求：
  - Webhook 推送
  - Tavily 检索
  - 运行时字体下载

推荐部署方式：

- 使用虚拟环境或容器隔离运行
- 严格指定 `MEMORY_DIR`
- 不需要的 webhook / Tavily key 就不要配置
- 预先放好中文字体，避免运行时下载

---

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 配置环境变量

建议在 `config/.env` 中显式配置：

```bash
MEMORY_DIR="/绝对路径/health-memory"
TAVILY_API_KEY="tvly-..."                  # 可选
DINGTALK_WEBHOOK="https://..."             # 可选
FEISHU_WEBHOOK="https://..."               # 可选
TELEGRAM_BOT_TOKEN="..."                   # 可选
TELEGRAM_CHAT_ID="..."                     # 可选
REPORT_WEB_DIR="/var/www/html/reports"     # 可选
REPORT_BASE_URL="https://example.com/reports"
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. 初始化档案

```bash
python scripts/init_config.py
```

初始化向导会把长期配置写入 `config/user_config.json`，包括：

- 用户档案
- 活跃病种与主病种
- 评分模块与权重
- 用药模块开关
- 常居地
- 自定义监测模块
- 报告偏好与 AI 生成偏好

### 4. 生成报告

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. 可选的定时 shell 入口

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

### 6. 可选的英文镜像记忆

```bash
python scripts/export_memory_en.py
```

适用于：

- 需要英文版 memory 镜像
- 当前环境缺少中文字体，需要英文渲染路径
- 想验证中英文日报 / 周报 / 月报的一致性

---

## ⚙️ 配置说明

### `config/user_config.json`

这是最核心的长期配置文件，负责保存：

- 用户基础信息
- 病种列表与主病种
- 启用的评分模块及其权重
- 用药设置
- 常居地与地理信息
- 自定义监测模块
- 报告偏好
- AI 生成偏好

### 常见环境变量

| 变量名 | 是否必填 | 作用 |
| --- | --- | --- |
| `MEMORY_DIR` | 是 | 指向健康 Markdown 目录 |
| `TAVILY_API_KEY` | 否 | 启用 Tavily 检索兜底 |
| `DINGTALK_WEBHOOK` | 否 | 推送文字摘要与 PDF 到钉钉 |
| `FEISHU_WEBHOOK` | 否 | 推送文字摘要与 PDF 到飞书 |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | 否 | 推送文字摘要与 PDF 到 Telegram |
| `REPORT_WEB_DIR` | 否 | 把 PDF 同步到 Web 目录 |
| `REPORT_BASE_URL` | 否 | 生成公开访问的 PDF 链接 |
| `ALLOW_RUNTIME_FONT_DOWNLOAD` | 否 | 允许运行时下载字体 |

---

## 📝 MEMORY 写入协议

Health-Mate 的解析依赖稳定格式。写入 `MEMORY_DIR` 时，LLM 必须像数据记录仪一样克制。

硬性要求：

- 不写点评
- 不写鼓励语
- 不写总结
- 不写 emoji
- 不写聊天废话

结构要求：

- 饮食、饮水、用药、运动事件必须使用带时间的三级标题
- 饮水块必须保持简洁稳定
- 步数必须写在单独的二级标题中
- 自定义监测模块必须保持稳定标题
- 避免在同一数据块中混写多种语言

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
- 燕麦片 50g -> 约 190kcal
- 脱脂牛奶 250ml -> 约 87kcal

## 运动记录
### 下午骑行（约 17:10）
- 距离：10.2km
- 耗时：42min
- 消耗：约 290kcal

## 今日步数
- 总步数：8200 步
```

### 可扩展监测模块示例

```markdown
## 血压记录
### 上午（约 08:00）
- 血压：128/82 mmHg
- 心率：72 bpm

## 血糖记录
### 早餐后（约 10:10）
- 血糖：7.1 mmol/L
- 时点：早餐后 2 小时

## 体成分
- 体重：64.4kg
- 体脂：18.6%

## 生化记录
- ALT：34 U/L
- AST：28 U/L
```

禁止写入的内容：

- `评估`
- `状态`
- `总结`
- 鼓励性废话
- 调试日志
- 系统日志

---

## 🔤 字体与双语渲染

推荐中文字体路径：

- `assets/NotoSansSC-VF.ttf`

如果中文字体缺失：

- 系统会切换到英文兼容渲染路径
- PDF 中会追加渲染说明
- 若要恢复中文 PDF，请把字体放入 `assets/`

项目地址：

- [Health-Mate GitHub 仓库](https://github.com/tankeito/Health-Mate)

---

## 🧪 常见问题排查

### 1. 提示 `MEMORY_DIR` 未设置

- 当前 shell 入口已不再允许隐式默认目录
- 请在 `config/.env` 或运行环境里显式设置 `MEMORY_DIR`

### 2. 月报医院医生推荐不够具体

- 先确认 `user_config.json` 中已配置常居地
- 若想看到医生级推荐，请确认本地 LLM 可用
- 如需检索增强，请配置 `TAVILY_API_KEY`
- 如果 LLM 暂时不可用，系统也会优先尝试使用城市级本地规则输出真实医院与医生组合

### 3. 中文 PDF 变成英文版

- 一般说明缺少中文字体
- 把 `NotoSansSC-VF.ttf` 放入 `assets/` 后重新生成即可

### 4. 没有收到 Webhook 推送

- 检查对应 webhook 环境变量是否已配置
- 查看 `logs/` 中的执行日志

---

## 📌 更新记录

### v1.4.0 — 2026-03-21

- 📊 新增完整健康月报工作流与专项图表
- 🏥 新增基于常居地的复查提醒与医院 / 门诊规划
- 🌡 新增周报 / 月报的症状与用药热力图
- 🔒 移除 `MEMORY_DIR` 的隐式回退逻辑
- 🧠 增强 LLM 失败时的本地规则回退能力
- 🌐 强化中英文双语输出与英文安全渲染路径

---

## 📁 项目结构

```text
health-mate/
├── scripts/
│   ├── health_report_pro.py
│   ├── weekly_report_pro.py
│   ├── monthly_report_pro.py
│   ├── pdf_generator.py
│   ├── weekly_pdf_generator.py
│   ├── monthly_pdf_generator.py
│   ├── i18n.py
│   ├── init_config.py
│   ├── export_memory_en.py
│   ├── daily_health_report_pro.sh
│   ├── weekly_health_report_pro.sh
│   └── monthly_health_report_pro.sh
├── config/
│   ├── user_config.json
│   ├── user_config.example.json
│   ├── .env
│   └── pdf_style_config.json
├── assets/
│   └── NotoSansSC-VF.ttf
├── logs/
├── reports/
├── README.md
├── README_ZH.md
├── SKILL.md
├── _meta.json
└── requirements.txt
```

---

## 📄 License

MIT License，详见 [LICENSE](LICENSE)。

---

## 📬 支持与反馈

- GitHub Issues: [https://github.com/tankeito/Health-Mate/issues](https://github.com/tankeito/Health-Mate/issues)
- GitHub 仓库: [https://github.com/tankeito/Health-Mate](https://github.com/tankeito/Health-Mate)
