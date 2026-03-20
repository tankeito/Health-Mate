---
name: health-mate
display_name: Health-Mate
version: 1.2.0
type: python/app
description: "专业健康报告生成插件。【安全与隐私透明度声明】：1. 数据不出域：仅以只读方式解析 MEMORY_DIR 记录，只有在您主动配置 Webhook 时才会向对应端点推送报告。2. 断网支持：PDF 引擎首次运行会自动下载开源字体，若需纯离线无网络请求运行，请预先放置字体到 assets/ 目录。3. 代理隔离：文档推荐的「记忆落盘铁律 (Prompt)」建议仅在专用的健康助手实例中配置，按需隔离以避免影响全局 Agent 行为。"
install: pip install -r requirements.txt
capabilities:
 - file_read
 - pdf_generation
 - http_request
metadata:
 clawdbot:
 requires:
 env:
 - MEMORY_DIR
homepage: https://github.com/tankeito/Health-Mate
repository: https://github.com/tankeito/Health-Mate.git
source: https://github.com/tankeito/Health-Mate
env:
 MEMORY_DIR: OpenClaw 记忆文件目录路径（必填，仅执行只读操作）
 TAVILY_API_KEY: Tavily 搜索 API 密钥（可选）
 DINGTALK_WEBHOOK: 钉钉群机器人 Webhook 地址（可选，仅向您信任的端点发数据）
 FEISHU_WEBHOOK: 飞书群机器人 Webhook 地址（可选，仅向您信任的端点发数据）
 TELEGRAM_BOT_TOKEN: Telegram Bot API Token（可选）
 TELEGRAM_CHAT_ID: Telegram 接收者 Chat ID（可选）
 REPORT_WEB_DIR: PDF 报表存放的本地 Web 目录（可选）
 REPORT_BASE_URL: PDF 报告对外下载域名（可选）
 REPORT_TIME: 每日推送时间（可选，默认 22）
 WEEKLY_REPORT_TIME: 每周健康周报推送时间（可选，默认每周一 09:00）
---

# Health-Mate 个人健康管家 / Personal Health Assistant / 個人の健康アシスタント

> 本技能为 OpenClaw 原生设计的专属健康插件
> A native skill exclusively designed for OpenClaw
> OpenClaw 専用に設計されたネイティブ健康管理プラグイン

🇨🇳 中文**：Health-Mate 是一款专为 OpenClaw 设计的健康管理插件。通过自然语言对话，自动收集饮食、饮水、运动及体重数据，并一键生成媲美高级智能手表的数据可视化 PDF 报告（支持推送到钉钉/飞书/TG）。
🇺🇸 **English: Health-Mate automatically collects your diet, water, exercise, and weight data through natural language conversations, generating highly-visualized PDF reports comparable to advanced smartwatches.
🇯🇵 日本語：自然な会話を通じて、食事、水分補給、運動、体重データを自動的に収集し、スマートウォッチに匹敵する高度に視覚化された PDF レポートを生成します。

---

## ⚠️ 隐私与安全声明 (Security & Privacy)

本插件严格遵守数据安全底线：
1. 本地只读 (Read-Only)**：插件仅以只读权限扫描 `MEMORY_DIR` 本地健康日志。
2. **数据不出域 (Local Processing)**：所有分析与 PDF 生成均在本地完成，绝不上传私有数据（除非主动配置 Webhook）。

---

## 🤖 给 AI 助理的操作指南 (Agent Instructions - Strictly Follow)

作为接入了 Health-Mate 的 AI 助理，当用户记录日常饮食、运动时，你只需执行**极简互动与数据落盘**；当用户需要看报告时，调用底层指令。

### 1. 核心触发指令
- /health：生成今日数据 PDF 报告。
- /health summary：生成健康周报复盘。

### 2. 📝 记忆落盘铁律 (Memory Write Protocol - 最高优先级)
当用户记录饮食、饮水或运动时，你必须将其写入 `MEMORY_DIR` 下的 Markdown 日志中。
⚠️ 警告：写入文件时，你只是"无情的数据记录仪"。所有的关心、点评和建议只能发在聊天框里，绝对禁止写入 Markdown 文件！**

【标准存储模板示例】（照此抄写，严禁增减多余字段，禁止出现"评估"、"✅"等废话）：
\```markdown
# 2026-03-20 健康记录

### 早餐（约 08:30）
- 燕麦片 50g → 约 190kcal
- 脱脂牛奶 250ml → 约 87kcal

### 上午饮水（约 09:45）
- 饮水量：300ml
- 累计：300ml/2000ml

### 下午骑行（约 17:17）
- 距离：10 公里
- 耗时：47 分钟
- 消耗：约 300kcal

## 今日步数
- 总步数：8500 步

## 💊 用药记录
- 胆舒胶囊：1 粒
\```

---

## 🔄 版本历史 (Changelog)
| 版本号 | 更新日期 | 更新内容 |
| :--- | :--- | :--- |
| v1.2.0 | 2026-03-20 | 1. 核心：重构病理参数支持动态健康目标（如健身减脂）；<br>2. 新增：支持多语言文档及自定义模块记录；<br>3. 优化：统一极简排版，重写记忆落盘铁律以锁死 LLM 输出；<br>4. 修复：彻底解决 PDF 的 Emoji 方块乱码 (☒) 与解析容错问题。 |
