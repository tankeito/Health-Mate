# OpenClaw Skill - Health Report

> 🏥 专业健康报告生成插件 | 支持多种病理条件 | 自定义评分权重 | 运动维度追踪
>
> **适用人群**：胆结石/糖尿病/高血压患者，健身减脂人群，健康管理者

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/tankeito/openclaw-skill-health-report/releases)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 功能亮点

| 功能 | 说明 | 适合人群 |
| :--- | :--- | :--- |
| **多维度评分** | 饮食/饮水/体重/运动 四大维度 | 全面健康管理 |
| **病理支持** | 胆结石/糖尿病/高血压/健身减脂 | 慢病管理人群 |
| **自定义权重** | 自由设定各维度评分权重 | 个性化需求 |
| **智能识别** | 自动解析食物份量，估算营养 | 懒人必备 |
| **多通道推送** | 钉钉/飞书/Telegram 自动发送 | 多平台用户 |
| **PDF 报告** | 专业格式，可存档分享 | 数据控 |

---

## 📦 快速开始（5 分钟上手）

### 🎉 方式一：对话式配置（推荐！零代码）

**无需编辑任何文件**，只需告诉机器人你的信息即可！

**示例对话**：
```
你：我是东东，男，34 岁，身高 172cm，现在 65kg，目标 64kg，有胆结石，不吃海鲜

机器人：✅ **配置已生成！**

已为您创建健康档案：
- 姓名：东东
- 性别：男
- 年龄：34 岁
- 身高：172cm
- 当前体重：65kg
- 目标体重：64kg
- 病理类型：胆结石
- 饮食禁忌：海鲜

使用 `/health` 命令查看今日报告！
```

**支持分步填写**（适合一次性记不住所有信息的用户）：
```
你：我想配置健康报告

机器人：好的！请告诉我您的姓名或昵称~

你：叫我东东就行

机器人：好的东东！接下来请告诉我您的性别和年龄？

你：男，34 岁

机器人：收到！您的身高是多少厘米？

...（继续问答直到配置完成）
```

**修改配置也支持对话**：
```
你：我的目标体重改成 63kg

机器人：✅ **配置已更新！** 新目标体重：63kg
```

---

### 方式二：手动配置文件（适合高级用户）

#### 步骤 1：克隆到 OpenClaw 的 skills 目录

**重要**：必须将本插件放到 OpenClaw 的 `skills/` 目录下！

```bash
# 进入 OpenClaw 工作区
cd /path/to/your/openclaw/workspace

# 克隆插件到 skills 目录
git clone git@github.com:tankeito/openclaw-skill-health-report.git skills/health_report

# 进入插件目录
cd skills/health_report
```

#### 步骤 2：复制配置文件

```bash
# 复制配置模板
cp user_config.example.json user_config.json
cp .env.example .env
```

#### 步骤 3：填写个人配置

**编辑 `user_config.json`**（这是你的健康档案）：

```json
{
    "user_profile": {
        "name": "东东",                    // 你的名字
        "gender": "男",                    // 男/女
        "age": 34,                         // 年龄
        "height_cm": 172,                  // 身高（厘米）
        "current_weight_kg": 65.2,         // 当前体重（公斤）
        "target_weight_kg": 64,            // 目标体重（公斤）
        "target_body_fat_percent": 15,     // 目标体脂率（健身人群填写）
        "condition": "胆结石",             // 病理类型：胆结石/糖尿病/高血压/健身减脂
        "activity_level": 1.2,             // 活动系数：1.2(久坐) ~ 1.9(重度运动)
        "dietary_preferences": {
            "dislike": ["鱼", "海鲜"],      // 不吃的食物
            "allergies": ["海鲜"],          // 过敏食物
            "favorite_fruits": ["苹果", "香蕉"]  // 喜欢的水果
        }
    },
    
    "scoring_weights": {
        "diet": 0.35,      // 饮食权重（0-1，总和应为 1.0）
        "water": 0.20,     // 饮水权重
        "weight": 0.15,    // 体重权重
        "exercise": 0.30   // 运动权重（健身人群可调高）
    }
}
```

**编辑 `.env`**（这是消息推送配置）：

```bash
# 钉钉 Webhook（选填，不用就留空）
DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"

# 飞书 Webhook（选填）
FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK"

# Telegram（选填）
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

# 健康记录目录（必填，OpenClaw 的 memory 目录）
MEMORY_DIR="/path/to/your/openclaw/workspace/memory"

# PDF 报告存放目录（必填）
PUBLIC_DIR="/path/to/public/dir"
PUBLIC_URL="https://your-domain.com"
```

### 步骤 4：安装依赖

```bash
pip install reportlab pillow
```

### 步骤 5：测试运行

```bash
# 测试今日报告（替换日期为你的实际日期）
python3 health_report_pro.py /path/to/memory/2026-03-13.md 2026-03-13
```

**看到类似输出即成功**：
```
=== TEXT_REPORT_START ===
✅ **晚间数据已记录！**
### 🌟 2026-03-13 今日综合评分
...
=== TEXT_REPORT_END ===
=== PDF_URL ===
https://your-domain.com/health_report_2026-03-13.pdf
```

---

## 📖 详细配置说明

### 病理条件配置

在 `user_config.json` 的 `condition` 字段选择你的病理类型：

| 类型 | `condition` 值 | 说明 |
| :--- | :--- | :--- |
| **胆结石** | `"胆结石"` | 低脂高纤饮食，避免油腻 |
| **糖尿病** | `"糖尿病"` | 控制碳水，低 GI 饮食 |
| **高血压** | `"高血压"` | 低盐饮食，控制钠摄入 |
| **健身减脂** | `"健身减脂"` | 高蛋白，热量缺口，运动导向 |

### 评分权重配置

在 `user_config.json` 的 `scoring_weights` 中调整各维度权重：

```json
"scoring_weights": {
    "diet": 0.35,      // 饮食控制（默认 35%）
    "water": 0.20,     // 饮水完成（默认 20%）
    "weight": 0.15,    // 体重监测（默认 15%）
    "exercise": 0.30   // 运动消耗（默认 30%）
}
```

**权重之和必须为 1.0**，系统会自动归一化。

**示例场景**：

- **减脂人群**：提高运动权重 `{"exercise": 0.40, "diet": 0.35, "water": 0.15, "weight": 0.10}`
- **慢病管理**：提高饮食权重 `{"diet": 0.50, "water": 0.20, "weight": 0.20, "exercise": 0.10}`
- **均衡健康**：使用默认权重即可

### 运动目标配置

在 `exercise_standards` 中设定运动目标：

```json
"exercise_standards": {
    "weekly_target_minutes": 150,    // 每周目标分钟数（WHO 推荐 150 分钟）
    "daily_calorie_target": 300,     // 每日热量消耗目标（千卡）
    "weekly_cardio_days": 3,         // 每周有氧运动天数
    "weekly_strength_days": 2        // 每周力量训练天数
}
```

---

## 📋 健康记录格式

在 OpenClaw 的 `memory/YYYY-MM-DD.md` 文件中记录每日数据：

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

### 加餐
- 苹果 1 个 → 约 104kcal

### 晚餐
- 清蒸鲈鱼 → 约 150kcal
- 炒青菜 → 约 50kcal

## 🏃 运动记录
### 骑行
- 距离：11.59 公里
- 耗时：54 分 31 秒
- 消耗：334 千卡
```

**说明**：
- 食物格式：`食物名称 → 约 XXXkcal`（热量可选，系统会自动估算）
- 运动格式：记录类型、时长、消耗热量
- 饮水格式：记录单次饮水量和累计进度

---

## 🤖 OpenClaw 集成

### 命令触发

本插件支持以下 OpenClaw 命令：

| 命令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `/health` | 生成今日健康报告 | `/health` |
| `/health score` | 查看评分详情 | `/health score` |
| `/health summary` | 查看本周总结 | `/health summary` |
| `/health config` | 查看/修改配置 | `/health config target_weight_kg 63` |

### 定时任务

在 Crontab 中添加每日报告任务：

```cron
# 每日健康报告 - 每天 22:00
0 22 * * * /path/to/skills/health_report/daily_health_report_pro.sh
```

---

## 📊 评分标准详解

### 饮食评分（100 分）

| 指标 | 权重 | 评分标准 |
| :--- | :--- | :--- |
| 脂肪摄入 | 30% | 在目标范围内得满分，超出/不足按比例扣分 |
| 膳食纤维 | 25% | 达到最低纤维量得满分 |
| 禁忌食物 | 20% | 每摄入一种禁忌食物扣 25 分 |
| 蛋白质 | 25% | 达到推荐量得满分 |

### 饮水评分（100 分）

| 完成率 | 得分 |
| :--- | :--- |
| ≥100% | 100 分 |
| 80-99% | 80-99 分 |
| 50-79% | 50-79 分 |
| <50% | 按比例得分 |

### 体重评分（100 分）

| 指标 | 权重 | 评分标准 |
| :--- | :--- | :--- |
| 按时记录 | 50% | 记录了晨起体重得 50 分 |
| 体重趋势 | 50% | 接近目标体重得高分 |

### 运动评分（100 分）

| 指标 | 权重 | 评分标准 |
| :--- | :--- | :--- |
| 运动时长 | 40% | 达到每日目标分钟数得满分 |
| 运动频率 | 30% | 今天运动了得满分 |
| 热量消耗 | 30% | 达到每日消耗目标得满分 |

---

## 🔐 隐私与安全

### 敏感文件保护

以下文件**已加入 `.gitignore`**，切勿手动上传到 GitHub：

- `.env` - 包含 Webhook、API Token
- `user_config.json` - 包含个人健康数据
- `reports/*.pdf` - 个人健康报告
- `*.log` - 日志文件

### 推荐实践

1. **私有仓库** - 如果 Fork 本仓库，建议设置为 Private
2. **定期备份** - 将 `.env` 和 `user_config.json` 备份到安全位置
3. **密钥轮换** - Webhook Token 建议每 3-6 个月更新一次

---

## 🛠️ 故障排查

### 问题 1：配置文件找不到

```
错误：配置文件不存在：/path/to/user_config.json
```

**解决**：
```bash
cd /path/to/skills/health_report
cp user_config.example.json user_config.json
# 编辑 user_config.json 填写真实配置
```

### 问题 2：依赖库缺失

```
ModuleNotFoundError: No module named 'reportlab'
```

**解决**：
```bash
pip install reportlab pillow
```

### 问题 3：PDF 生成失败

**解决**：
1. 检查中文字体文件是否存在
2. 检查输出目录是否有写权限
3. 查看日志文件：`tail -f /var/log/health_report_pro.log`

### 问题 4：消息推送失败

**解决**：
```bash
# 测试 Webhook
curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","content":{"text":"测试"}}'
```

---

## 📦 项目结构

```
skills/health_report/
├── _meta.json                  # OpenClaw Skill 元数据
├── skill.md                    # 机器人指令说明
├── README.md                   # 使用说明（本文件）
├── health_report_pro.py        # 主脚本（报告生成逻辑）
├── constants.py                # 常量库（食物份量/热量）
├── pdf_generator.py            # PDF 生成模块
├── daily_health_report_pro.sh  # Shell 包装脚本（定时任务用）
├── user_config.json            # 用户配置（⚠️ 勿上传）
├── .env                        # 环境变量（⚠️ 勿上传）
├── .env.example                # 环境变量模板
├── user_config.example.json    # 用户配置模板
├── .gitignore                  # Git 忽略规则
└── reports/                    # PDF 报告输出目录
```

---

## 🤝 贡献指南

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

### 添加新的食物数据

在 `constants.py` 的 `FOOD_CALORIES` 中添加：

```python
"你的食物": {"calories": 100, "protein": 10, "fat": 5, "carb": 10, "fiber": 2},
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

- **作者**：tankeito
- **Email**：tqd354@gmail.com
- **GitHub**：[@tankeito](https://github.com/tankeito)
- **Issue**：[提交问题](https://github.com/tankeito/openclaw-skill-health-report/issues)

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
| :--- | :--- | :--- |
| **v2.0.0** | 2026-03-13 | 添加运动维度评分，支持自定义权重，OpenClaw Skill 标准化 |
| **v1.0.0** | 2026-03-10 | 初始版本（饮食/饮水/体重三维度） |
