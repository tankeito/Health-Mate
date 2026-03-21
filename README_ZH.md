[English Guide](README.md)

# Health-Mate

> 面向 OpenClaw 的本地优先双语健康报告工具。

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

## 项目概览

Health-Mate 会把结构化 Markdown 健康记录转换成更适合阅读和存档的 PDF 报告。

- 日报：综合评分、饮食、饮水、运动、用药、AI 点评、风险预警、次日方案
- 周报：3 环概览、症状与用药热力图、趋势图、营养结构图、本周复盘、下周行动
- 月报：宏观依从性雷达图、热力图、30 天体重与基础代谢趋势、专科图表、AI 月度研判、复查提醒、门诊建议
- 多病种支持：胆结石、高血压、糖尿病、健身减脂，以及多病种联合管理
- 自定义模块：用药记录、监测模块、自定义评分模块都可以写入 `user_config.json`
- 字体兜底：缺少中文字体时，可自动走英文兼容渲染，并在 PDF 中附加说明

## 1.4.0 版本重点

- 新增月报 PDF 流程
- 新增周报症状与用药热力图
- 新增月报 30 天体重与基础代谢趋势图
- 新增月报症状分布图与脂肪/碳水箱线图
- 新增基于常居地的月报复查提醒与门诊建议
- 增强了 LLM 失败时的本地回退逻辑，确保输出仍基于真实数据
- shell 运行脚本不再内置 `MEMORY_DIR` 兜底路径，必须显式配置

## 报告内容

### 健康日报

- 今日综合评分与权重模块评分
- 进食、饮水、运动、用药详情
- AI 点评与本地规则回退
- 风险预警
- 次日可执行方案

### 健康周报

- 本周健康指标概览
- 症状与用药热力图
- 体重、热量、营养、步数、饮水趋势图
- 本周亮点、待改进项、下周重点
- 附加监测模块汇总

### 健康月报

- 第 1 页：宏观依从性雷达图、症状与用药热力图、30 天体重与基础代谢趋势图
- 第 2 页：病种专项图表，如胆结石脂肪/症状关系、高血压箱线图、血糖趋势、体脂趋势、自定义指标图
- 第 3 页：AI 月度病情研判、复查提醒、医院与门诊建议

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 配置运行环境

可以新建 `config/.env`，也可以在你自己的运行环境里直接设置：

```bash
MEMORY_DIR="/你的健康记录目录绝对路径"
```

可选能力：

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

注意：

- `MEMORY_DIR` 必填
- shell 脚本在 `MEMORY_DIR` 缺失时会直接退出
- 只有显式配置了 Tavily、Webhook，或明确允许运行时字体下载时，才会发生外网请求

### 3. 首次运行配置向导

```bash
python scripts/init_config.py
```

向导会把配置统一写入 `config/user_config.json`，包括：

- 用户基础信息
- 多病种选择与主病种
- 评分模块与权重
- 用药是否参与评分
- 自定义监测模块
- 月报门诊建议用到的常居地配置

### 4. 生成报告

```bash
python scripts/health_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

shell 运行脚本：

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

### 5. 英文镜像与英文报告

如果你需要英文版 memory 或英文版 PDF 渲染链路，可以使用：

```bash
python scripts/export_memory_en.py
```

这个脚本属于项目的一部分，建议纳入 Git 管理。

## 字体说明

推荐把中文字体放在：

- `assets/NotoSansSC-VF.ttf`

如果该字体缺失：

- 报告会自动切换到英文兼容渲染路径
- PDF 会追加渲染说明
- 如果你需要中文 PDF，请从项目仓库下载字体并放到 `assets/NotoSansSC-VF.ttf`

仓库地址：

- [Health-Mate GitHub](https://github.com/tankeito/Health-Mate)

## Memory 写入协议

当助手往 `MEMORY_DIR` 写入内容时，必须像“严格记录仪”一样工作。

硬性规则：

- 不允许写点评、建议、总结、Emoji 或聊天腔内容
- 餐次、饮水、用药、运动事件必须使用三级标题并带时间
- 饮水块必须保持极简
- 步数必须固定写在一个二级标题块里
- 监测模块必须使用稳定的二级标题
- 同一个记录块里不要混用中英文

示例：

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

扩展监测模块示例：

```markdown
## 血压记录
### 上午（约 08:00）
- 血压：128/82 mmHg
- 心率：72 bpm

## 血糖记录
### 早餐后（约 10:10）
- 血糖：7.1 mmol/L
- 时点：早餐后 2 小时

## 身体成分
- 体重：64.4kg
- 体脂率：18.6%

## 生化记录
- ALT：34 U/L
- AST：28 U/L
```

禁止内容：

- `评估`
- `状态`
- `总结`
- 鼓励型废话
- 调试日志
- 系统日志
- 日常记录文件里的表格

## 运行时安全说明

本地行为：

- 从 `MEMORY_DIR` 读取 Markdown 记录
- shell 脚本模式下会读取 `config/.env`
- 将 PDF 输出到 `reports/`
- 将日志写入 `logs/`
- 在需要时可能生成临时英文 memory 镜像

联网行为：

- 仅在配置了 `TAVILY_API_KEY` 时调用 Tavily
- 仅在配置了对应凭据时推送 Webhook
- 仅在 `ALLOW_RUNTIME_FONT_DOWNLOAD=true` 时允许运行时下载字体

## 更新日志

### v1.4.0 - 2026-03-21

- 新增月报
- 周报与月报新增症状/用药热力图
- 新增月报病种专项图表与体重/BMR 趋势图
- 新增基于常居地的医疗规划输出
- 更新 README、README_ZH、SKILL 元数据与包元数据
