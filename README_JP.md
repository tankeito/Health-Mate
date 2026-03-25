[English](README.md) | [中文](README_ZH.md) | 日本語

# 🏥 Health-Mate | OpenClaw 向けローカル優先ヘルスレポート基盤

> OpenClaw の Markdown 健康メモリを、日報・週報・月報の PDF と文字版サマリーへ変換するローカル優先スキルです。
>
> 食事、飲水、体重、運動、症状、服薬、独自モニタリング項目を継続的に記録し、慢性疾患管理や減量の振り返りに使える見やすいレポートへ整形します。

[![Version](https://img.shields.io/badge/version-1.5.1-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 Health-Mate とは

Health-Mate は、単なる生活ログの蓄積で終わらず、振り返りと次の行動につながる「レポート中心」の健康管理ワークフローを目指しています。

- 🧠 **疾患感知型**: 胆石 / 慢性胆嚢炎、高血圧、糖尿病、減脂、複数疾患の同時管理に対応
- 📄 **レポート中心設計**: 日報・週報・月報を自動生成し、数値・図表・提案を一体化
- 🔒 **ローカル優先**: 解析、採点、PDF 描画、ローカル fallback は既定でローカル完結
- 🧩 **拡張可能**: 血圧、血糖、体脂肪、生化学、睡眠などを `user_config.json` で追加可能
- 🌐 **多言語対応**: 中国語・英語・日本語のレポート系ロケールをサポート

---

## 📑 3 種類のレポート

| レポート | 主な役割 | 代表的な内容 | 答える問い |
| --- | --- | --- | --- |
| 🌅 日報 | 当日レビュー | 総合採点、栄養ドーナツ、飲水 / 運動詳細、リスク警告、翌日プラン | 今日どうだったか、明日何を変えるか |
| 🗓️ 週報 | 中期トレンド確認 | 週次サマリー、熱力図、体重 / 飲水 / 歩数 / 栄養トレンド、AI 振り返り | 今週の良かった点と繰り返す課題は何か |
| 📊 月報 | 病態別の深掘り | レーダー、30 日熱力図、体重 / BMR 推移、病態別図表、医療計画 | 現在の方針は有効か、受診や追加評価が必要か |

---

## ⚙️ 処理パイプライン

Health-Mate は以下の多層ローカル処理で動作します。

1. **記録入力層**
   OpenClaw が会話ベースの打刻を構造化 Markdown に整形し、`MEMORY_DIR` に保存します。

2. **解析層**
   Python が食事、飲水、体重、歩数、運動、症状、服薬、追加モジュールを正規表現ベースで抽出します。

3. **評価層**
   主病種・複数病種・ユーザー設定の重みに応じて、目標値、達成率、リスク判定を調整します。

4. **洞察生成層**
   可能ならローカル LLM を優先し、失敗時はローカルルール、必要に応じて Tavily 検索を組み合わせて補強します。

5. **レンダリング / 配信層**
   Matplotlib + ReportLab で PDF を描画し、必要なら DingTalk / Feishu / Telegram に文字版と PDF リンクを送ります。

---

## 🧭 AI 出力ソースの見方

レポート内の AI セクションには、どの経路で文面が作られたかを示す出典ラベルが付きます。

| 表示ラベル | 意味 |
| --- | --- |
| `出典: LLM 動的生成` | ローカル `openclaw agent --local` が成功 |
| `出典: Tavily 検索 + ローカルルール` | ローカル LLM が失敗し、検索補強付き fallback を使用 |
| `出典: ローカルルール` | ローカル LLM が使えず、純粋なローカル fallback を使用 |

---

## 🚀 クイックスタート

### 1. インストール

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 環境変数を設定する

ClawHub の現在の手動アップロード方式では `config/.env.example` が同梱されない場合があります。
そのため `config/user_config.example.json` を開き、トップレベルの `env` ブロックを参照して `config/.env` を手動作成してください。
実行ロジック自体は変えておらず、Python エントリーポイントと shell ランナーは引き続き `config/.env` を読み込みます。

```bash
MEMORY_DIR="/absolute/path/to/health-memory"
OPENCLAW_BIN="/root/.nvm/versions/node/v22.22.0/bin/openclaw" # cron では特に推奨
TAVILY_API_KEY="tvly-..."                  # Optional
DINGTALK_WEBHOOK="https://..."             # Optional
FEISHU_WEBHOOK="https://..."               # Optional
TELEGRAM_BOT_TOKEN="..."                   # Optional
TELEGRAM_CHAT_ID="..."                     # Optional
REPORT_WEB_DIR="/var/www/html/reports"     # Optional
REPORT_BASE_URL="https://example.com/reports"
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. 初期設定ウィザードを実行する

```bash
python scripts/init_config.py
```

このウィザードは `config/user_config.json` の主要項目を作成します。

- 基本プロフィール
- 管理対象の病種一覧と主病種
- 採点モジュールと重み
- 服薬モジュール
- 常居地
- AI 生成設定
- 追加モニタリングモジュール
- レポート設定

### 4. レポートを生成する

```bash
python scripts/daily_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. shell ランナーを使う

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

cron や最小 PATH の shell 環境では、`openclaw` が見つからずローカル LLM がスキップされることがあります。`OPENCLAW_BIN` は `config/.env` に設定してください。ClawHub 手動アップロード時は `config/user_config.example.json` の `env` ブロックを参照すると安全です。日次ランナーと Python 側の両方で優先的に利用されます。
`OPENCLAW_BIN` を未設定でも、Python 側では `/root/.nvm/versions/node/*/bin/openclaw`、`/usr/local/bin/openclaw`、`/usr/bin/openclaw`、Windows 標準 Node.js パスなどの代表的な場所を順に探索します。shell ランナー自体には固定 PATH を埋め込んでいません。

---

## 🇯🇵 日本語レポートについて

### 日本語フォント

日本語 PDF を安定表示するには、以下のフォントが推奨です。

- `assets/NotoSansJP-VF.ttf`

このファイルが存在する場合、`ja-JP` ロケールの PDF は日本語フォントで描画されます。

### 日本語フォントが無い場合

- 日本語 PDF は英語フォールバック経路で生成されます
- レポート内にレンダリング説明を追加し、フォント不足を明示します
- 中国語フォントしか無い場合でも、日本語の完全表示は保証されません

必要ならリポジトリからフォントを取得してください。

- GitHub: [https://github.com/tankeito/Health-Mate](https://github.com/tankeito/Health-Mate)

### 日本語 memory ミラー

既存の中国語 memory から日本語ミラーを生成して、日本語 PDF の検証に使えます。

```bash
python scripts/export_memory_jp.py
```

生成先:

- `memory_jp/`

---

## 📝 Memory Write Protocol

OpenClaw が `MEMORY_DIR` に書き込む Markdown は、解析器が壊れないよう厳格な形を守る必要があります。コメント、雑談、絵文字、評価文はファイルに書かないでください。

必須ルール:

- 食事 / 飲水 / 運動は必ず `### ラベル（約 HH:MM）` または `### Label (around HH:MM)` を使う
- 食事行は `- 食品名 量 -> approx XXX kcal` 形式を守る
- 飲水ブロックは `- 飲水量: XXml` と `- 累計: XXml / 目標ml` の 2 行だけにする
- 歩数は `## 今日の歩数` または `## Today Steps` の下に `- 総歩数: XXXX` / `- Total steps: XXXX`
- `**評価**`、`状态`、`总结` のような解析に不要な説明文を入れない

最小テンプレート:

```markdown
# 2026-03-20 健康記録

## 体重記録
**朝の空腹時**: 64.4kg

## 飲水記録
### 午前 (around 08:45)
- 飲水量: 300ml
- 累計: 300ml / 2000ml

## 食事記録
### 朝食 (around 08:50)
- oatmeal 50g -> approx 190 kcal
- skim milk 250ml -> approx 87 kcal

## 運動記録
### サイクリング (around 17:10)
- 距離: 10.2 km
- 時間: 42 min
- 消費: approx 290 kcal

## 今日の歩数
- 総歩数: 8200
```

---

## 🧪 日本語版を検証する手順

1. `assets/NotoSansJP-VF.ttf` が存在することを確認
2. `memory_jp/` を生成
3. `HEALTH_MATE_LANG=ja-JP` を付けるか、日本語 memory から locale 推定させる
4. 日報 / 週報 / 月報を生成
5. PDF の見出し、表、図表ラベル、フッター、レンダリング説明を確認

例:

```bash
python scripts/export_memory_jp.py
python scripts/daily_report_pro.py memory_jp/2026-03-20.md 2026-03-20
python scripts/weekly_report_pro.py 2026-03-20
python scripts/monthly_report_pro.py 2026-03-20
```

---

## 🔒 セキュリティ境界

Health-Mate はローカル優先ですが、以下は明示的に理解しておく必要があります。

- `MEMORY_DIR` は必須で、暗黙のグローバル fallback パスはありません
- shell ランナーは `config/.env` を読み込みます
- ClawHub 手動アップロード時は `config/user_config.example.json` の `env` ブロックを参照して `.env` を手動作成してください
- レポートとログはローカルに書き込みます
- 外部通信は必要な設定を入れた時だけ発生します
  - Tavily 検索
  - Webhook 配信
  - 実行時フォントダウンロード

推奨:

- 仮想環境またはコンテナで運用する
- `MEMORY_DIR` を明示的に限定する
- 不要な Webhook や API キーは設定しない

---

## 📁 プロジェクト構成

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

## 📌 変更履歴

### v1.5.1 — 2026-03-24

- ⏰ cron 定期タスク向け環境設定を最適化し、スケジュール実行時に LLM を正常に呼び出せるよう改善
- 🔧 ClawHub 手動アップロード向けに、env 参照テンプレートを `config/user_config.example.json` の `env` ブロックへ統合
- 📝 実行ロジックは変更せず、`daily_health_report_pro.sh`、`weekly_health_report_pro.sh`、`monthly_health_report_pro.sh` は引き続き `.env` から環境変数を読み込み
- 🌐 シェルスクリプトのコメントを全て英語化し、国際対応を強化
- ✅ 定期実行の日報・週報・月報でローカル LLM を使用し、AI 分析と提案を正常に生成可能に

### v1.5.0 — 2026-03-23

- 🧹 旧ラッパー `scripts/health_report_pro.py` と `scripts/pdf_generator.py` を削除し、日報の正式エントリーポイントを `daily_health_report_pro.py` / `daily_pdf_generator.py` に一本化
- 🇯🇵 `ja-JP` を初期設定ウィザードまで通し、`NotoSansJP-VF.ttf` 不在時は英語フォールバックと説明文を明示
- ⏰ cron 向けのローカル LLM 解決を `OPENCLAW_BIN` 優先 + 代表パス自動探索として整理

### v1.4.1 — 2026-03-22

- 🇯🇵 `ja-JP` ロケール、`NotoSansJP-VF.ttf`、`export_memory_jp.py` を追加
- 🛠 日報の正式エントリーポイントを `daily_health_report_pro.py` / `daily_pdf_generator.py` に統一
- ⏰ `OPENCLAW_BIN` と多段 fallback により cron 環境でもローカル LLM を解決しやすく改善

### v1.4.0 — 2026-03-21

- 📊 月報ワークフローと病態別図表を追加
- 🏥 常居地ベースの受診提案を追加
- 🌡 週報 / 月報に症状・服薬熱力図を追加

---

## 📄 License

MIT License。詳細は [LICENSE](LICENSE) を参照してください。
