# OpenClaw Skill - Health Report

> 基于 OpenClaw 的专业健康报告生成插件  
> 支持多种病理条件（胆结石/糖尿病/高血压）的饮食分析与评分

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://openclaw.ai)

---

## 🌟 功能特性

- **多维度健康评分** - 饮食控制、饮水完成、体重监测
- **病理条件支持** - 胆结石/糖尿病/高血压饮食标准
- **智能食物识别** - 自动解析份量，估算热量和营养
- **多通道推送** - 钉钉/飞书/Telegram 自动发送
- **PDF 报告导出** - 专业格式，可存档分享
- **隐私保护** - 配置与代码分离，敏感数据不上传

---

## 📦 安装与配置

### 1. 克隆仓库

```bash
git clone git@github.com:tankeito/openclaw-skill-health-report.git
cd openclaw-skill-health-report
```

### 2. 复制配置文件

```bash
cp .env.example .env
cp user_config.example.json user_config.json
```

### 3. 编辑配置

**编辑 `.env`** - 填写消息推送配置：

```bash
# 钉钉 Webhook
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"

# 飞书 Webhook
FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK"

# Telegram
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

# 健康记录目录（OpenClaw memory 目录）
MEMORY_DIR="/path/to/your/memory"

# PDF 报告存放目录
PUBLIC_DIR="/path/to/public/dir"
PUBLIC_URL="https://your-domain.com"
```

**编辑 `user_config.json`** - 填写个人健康档案：

```json
{
    "user_profile": {
        "name": "你的名字",
        "gender": "男",
        "age": 34,
        "height_cm": 172,
        "current_weight_kg": 65.2,
        "target_weight_kg": 64,
        "condition": "胆结石",
        "activity_level": 1.2,
        "dietary_preferences": {
            "dislike": ["鱼", "海鲜"],
            "allergies": ["海鲜"],
            "favorite_fruits": ["苹果", "香蕉"]
        }
    }
}
```

### 4. 安装依赖

```bash
pip install reportlab pillow
```

### 5. 配置 Crontab

```bash
crontab -e
```

添加每日报告任务（每天 22:00 执行）：

```cron
# 每日健康报告 - 每天 22:00
0 22 * * * /path/to/health_report/daily_health_report_pro.sh
```

---

## 📖 使用说明

### 手动测试

```bash
# 测试今日报告
python3 health_report_pro.py /path/to/memory/2026-03-13.md 2026-03-13

# 查看输出
# === TEXT_REPORT_START ===
# ✅ **晚间数据已记录！**
# ### 🌟 2026-03-13 今日综合评分
# ...
```

### 健康记录格式

在 OpenClaw 的 `memory/YYYY-MM-DD.md` 文件中记录：

```markdown
# 2026-03-13 健康记录

## 📊 体重记录
- **晨起空腹**：130.4 斤

## 💧 饮水记录
### 晨起
- 饮水量：250ml
- 累计：250ml/2000ml

## 🥗 饮食记录
### 早餐
- 清汤牛肉面 → 约 350kcal
- 安佳脱脂纯牛奶 250ml → 约 87kcal

### 午餐
- 半碗米饭 → 约 87kcal
- 凉拌土豆牛肉 → 约 180kcal

## 🏃 运动记录
### 骑行
- 距离：11.59 公里
- 耗时：54 分 31 秒
```

---

## 🔬 支持的病理条件

### 胆结石
- **脂肪控制**：40-50g/天
- **烹饪方式**：蒸、煮、炖、白灼
- **禁忌食物**：动物内脏、辛辣刺激、海鲜

### 糖尿病
- **碳水控制**：45-50% 总热量
- **烹饪方式**：蒸、煮、炖、凉拌
- **禁忌食物**：精制糖、白米饭、白面包

### 高血压
- **钠摄入**：<2000mg/天
- **烹饪方式**：蒸、煮、炖、凉拌
- **禁忌食物**：咸菜、腊肉、高盐零食

---

## 📊 评分标准

| 维度 | 权重 | 评分标准 |
| :--- | :--- | :--- |
| 饮食控制 | 40% | 脂肪/纤维摄入、禁忌食物、烹饪方式 |
| 饮水完成 | 30% | 实际饮水量/目标饮水量 |
| 体重监测 | 30% | 按时记录、体重趋势 |

**总分** = 饮食×0.4 + 饮水×0.3 + 体重×0.3

---

## 🔐 安全与隐私

### 敏感文件保护

以下文件已加入 `.gitignore`，**切勿手动上传**：

- `.env` - 包含 Webhook、API Token
- `user_config.json` - 包含个人健康数据
- `reports/*.pdf` - 个人健康报告

### 推荐实践

1. **使用私有仓库** - 如包含个人配置，建议 Fork 为私有仓库
2. **定期轮换密钥** - Webhook Token 建议每 3-6 个月更新
3. **备份配置** - 将 `.env` 和 `user_config.json` 备份到安全位置

---

## 🛠️ 故障排查

### 报告生成失败

```bash
# 检查配置文件
ls -la .env user_config.json

# 测试配置加载
python3 -c "from health_report_pro import load_user_config; print(load_user_config())"

# 查看日志
tail -f /var/log/health_report_pro.log
```

### 消息推送失败

```bash
# 测试 Webhook
curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","content":{"text":"测试"}}'
```

### PDF 生成失败

```bash
# 检查依赖
pip install reportlab pillow

# 检查字体文件
ls -la *.ttf
```

---

## 📦 项目结构

```
health_report/
├── health_report_pro.py      # 主脚本（业务逻辑）
├── constants.py              # 常量库（食物份量/热量）
├── pdf_generator.py          # PDF 生成模块
├── daily_health_report_pro.sh # Shell 包装脚本
├── user_config.json          # 用户配置（⚠️ 勿上传）
├── .env                      # 环境变量（⚠️ 勿上传）
├── .env.example              # 环境变量模板
├── user_config.example.json  # 用户配置模板
├── .gitignore                # Git 忽略规则
├── README.md                 # 使用说明
└── reports/                  # PDF 报告输出目录
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 添加新的病理条件

在 `user_config.json` 的 `condition_standards` 中添加：

```json
"高血脂": {
    "fat_min_g": 40,
    "fat_max_g": 55,
    "fat_percent": "20-25%",
    "protein_g_per_kg": 1.2,
    "carb_percent": "50-55%",
    "fiber_min_g": 30,
    "water_min_ml": 2000,
    "cooking_methods": ["蒸", "煮", "炖", "凉拌"],
    "avoid_methods": ["油炸", "红烧"],
    "avoid_foods": ["动物内脏", "肥肉", "油炸食品"]
}
```

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🔗 相关项目

- **[OpenClaw](https://openclaw.ai)** - AI 个人助理框架
- **[openclaw-cron-jobs](https://github.com/tankeito/openclaw-cron-jobs)** - 服务器运维定时任务（SSL/喝水/Gmail）

---

## 📧 联系方式

- 作者：tankeito
- Email：tqd354@gmail.com
- GitHub：[@tankeito](https://github.com/tankeito)
