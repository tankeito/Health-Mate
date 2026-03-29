[English](README.md) | [中文](README_ZH.md) | 日本語

# 🏥 Health-Mate | OpenClaw 向けローカル優先多言語ヘルスレポート基盤

> 多言語対応・双引擎アーキテクチャ（医療慢性疾患管理 vs 均衡減脂体态）を備えた本格的な健康報告システム。
>
> ローカル Markdown 健康メモリを、病態感知採点、専用チャート、医療計画、オプション Webhook 配信付きの日報・週報・月報 PDF へ変換します。

[![Version](https://img.shields.io/badge/version-1.5.3-blue.svg)](https://github.com/tankeito/Health-Mate/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai)

---

## 🌟 Health-Mate とは

Health-Mate は、単なる生活ログの蓄積で終わらず、振り返りと次の行動につながる「レポート中心」の健康管理ワークフローを目指しています。

- 🧠 **疾患感知型**: 胆石/慢性胆嚢炎、高血圧、糖尿病、減脂、複数疾患の同時管理に対応
- 📄 **レポート中心設計**: 日報・週報・月報を自動生成し、数値・図表・提案を一体化
- 🔒 **ローカル優先**: 解析、採点、PDF 描画、ローカル fallback は既定でローカル完結
- 🧩 **拡張可能**: 血圧、血糖、体脂肪、生化学、睡眠などを `user_config.json` で追加可能
- 🌐 **多言語対応**: 中国語・英語・日本語（`zh-CN`、`en-US`、`ja-JP`）の完全サポート。対象言語の医療排版習慣とフォントレンダリング fallback を自動適応

---

## 📊 3 種類のレポート：何が解決できるか

### 🌅 健康日報 —— 当日レビューと翌日マイクロ調整

**答える問い**：*「今日はどうだったか、明日何を変えるべきか？」*

**コアモジュール**：
- 📊 **動的栄養ドーナツチャート**: マクロ栄養素アドヒアランス可視化（タンパク質、脂肪、炭水化物、食物繊維）
- 📈 **摂取積み上げ棒グラフ**: 食事、飲水、運動をタイム軸上で層別表示
- ⚠️ **リスク警告**: 疾患固有の警告（例：胆石の脂肪低すぎ、高血圧のナトリウム高すぎ）
- 📋 **翌日実行可能アクションリスト**: 明日の具体的・実行可能な調整案（特定食品、水分目標、運動目標）

**使用シーン**: 毎日の振り返り、即時行動修正、モチベーション維持

---

### 🗓 健康週報 —— 習慣形成と短期変動分析

**答える問い**：*「どの行動が安定したか、どの問題が繰り返されているか？」*

**コアモジュール**：
- 🎯 **週次核心指標レーダー**: 多次元概要（カロリー、マクロ栄養素、飲水、歩数、睡眠など）
- 🔥 **習慣＆運動ヒートマップ**: `balanced` / `fat_loss` モード向け GitHub 風コントリビューショングラフ
- 📉 **二軸比較トレンドチャート**: 体重 + エネルギー収支、歩数 + 飲水、症状頻度 + トリガー曝露
- 🏥 **疾患モード**: 慢性疾患向け症状 - 服薬相関ヒートマップ
- 💪 **フィットネスモード**: 4 週間習慣進行バー、エネルギー収支ウォーターフォールチャート
- 📝 **良かった点と改善点**: 今週の進歩点、来週の注目事項

**使用シーン**: 週次レビュー、パターン特定、月次チェックポイント前の戦略調整

---

### 📊 健康月報 —— 深層分析と長期戦略

**答える問い**：*「現在の方針は有効か、通院またはエスカレーション介入が必要か？」*

**コアモジュール**：
- 🎯 **マクロアドヒアランスレーダー**: 30 日間栄養パターン概要
- 🔥 **アクティビティヒートマップ**: 月間 GitHub 風グラフ（ライフスタイルモード）または症状 - 服薬ヒートマップ（疾患モード）
- 📈 **30 日間体重＆BMR トレンド**: 重要なイベント注釈付き平滑曲線
- 🏥 **専用チャート**: 疾患固有の深掘り可視化
- 🧠 **AI 月次レビュー**: LLM 生成のトレンド・リスク・推奨事項の総合レポート
- 🏥 **医療計画セクション**（疾患モードのみ）：
  - 病院優先推奨（トップレベル三甲 > 三甲 > 地域医療センター）
  - 診療科と医師マッチング、専門領域説明付き
  - 診療ガイドラインに基づく受診リマインダー
- 🏃 **ライフスタイル介入リスト**（フィットネスモードのみ）：
  - 翌月のマクロ栄養とトレーニング調整案
  - 体組成目標（除脂肪体重 vs 脂肪量）
  - 習慣スタッキング推奨

**使用シーン**: 月次戦略レビュー、医療フォローアップ計画、大きな方向転換

---

## 🧬 双引擎動的集団分岐

Health-Mate は `user_config.json` の `population_branch` 設定に基づき、底层レポート引擎をインテリジェントに切り替えます。

### 🏥 慢性疾患管理モード（Disease Management）

**起動条件**: `gallstones`（胆石）、`hypertension`（高血圧）、`diabetes`（糖尿病）などの慢性疾患

**レポート特性**：
- 🩺 **病理所見アラインメントチャート**: 脂肪摂取 vs 症状頻度（胆石）、血圧ボックスプロット（高血圧）、血糖トレンド（糖尿病）
- 💊 **服薬アドヒアランス分析**: 服薬タイミング、飲み忘れ、症状との相関
- ⚠️ **高リスク食品トリガー識別**: 症状悪化と相関する食品の関連分析
- 🏥 **病院＆医師推奨**（月報のみ）：
  - LLM 生成の構造化推奨（病院 → 診療科 → 医師）
  - エビデンスに基づくローカル候補病院の Tavily 検索 fallback
  - 公立トップレベル三甲病院と大学附属医療センターを優先推奨
  - エビデンスが十分な場合、実在の医師名と职称を出力

**出力例**（胆石月報）：
- 脂肪摂取 vs 症状頻度二軸チャート
- 脂肪/炭水化物摂取分散ボックスプロット
- 症状構成ドーナツチャート
- 病院推奨：「四川省人民医院 → 肝胆外科 → 周永碧【主任医師】」

---

### 🏃 均衡＆体态管理モード（Fitness & Wellness）

**起動条件**: `balanced`（均衡健康）、`fat_loss`（減脂）または一般健康最適化

**レポート特性**：
- 📊 **非医療化可視化**: 症状追蹤なし、病院推奨なし
- 🔥 **4 週間習慣進行トレンド**: 主要行動の一貫性を示す積み上げ棒グラフ
- ⚖️ **エネルギー収支ウォーターフォール**: カロリー摂取 vs 消費 vs 不足/過剰
- 💪 **体組成深層分析**: 除脂肪体重（LBM）vs 脂肪量トレンド、体脂肪率平滑曲線
- 🎯 **翌月マクロ栄養＆トレーニング計画**:
  - タンパク質目標調整（筋肉維持）
  - トレーニング前後の炭水化物タイミング
  - トレーニング量進行（セット、レップ、強度）

**出力例**（減脂月報）:
- 30 日間体重トレンド平滑曲線
- 体脂肪率トレンド
- エネルギー収支ウォーターフォール
- 4 週間習慣進行（歩数、トレーニング、タンパク質摂取、睡眠）
- 翌月介入案：「タンパク質を 2.0g/kg に増量、レジスタンストレーニングを週 2 回追加、500kcal 不足を維持」

---

## ⚙️ コア技術スタック

| レイヤー | 技術 | 用途 |
|------|------|------|
| **PDF レンダリング** | ReportLab 4.0+ | プロフェッショナルグレード PDF 生成、カスタムスタイル、多言語フォントサポート、精密レイアウト制御 |
| **データ可視化** | Matplotlib 3.0+ | 統計チャート（レーダー、ヒートマップ、ボックスプロット、二軸トレンド）、疾患固有スタイリング |
| **LLM 統合** | OpenClaw Local Agent + Tavily API | ハイブリッド推論アーキテクチャ：ローカル LLM で AI コメントと病院推奨を生成、Tavily でエビデンスベースの Web 検索 fallback |
| **スケジューリング** | Cron + OpenClaw HEARTBEAT | 自動化された日報/週報/月報生成、DingTalk/Feishu/Telegram プッシュ配信対応 |

---

## 🚀 クイックスタート

### 1. インストール

```bash
git clone https://github.com/tankeito/Health-Mate.git health-mate
cd health-mate
pip install -r requirements.txt
```

### 2. 環境変数の設定

ClawHub 手動フォルダアップロードでは `config/.env.example` が同梱されない場合があります。`config/user_config.example.json` を開き、トップレベルの `env` ブロックをアップロード安全な参照テンプレートとして確認してください。

セットアップウィザードは、ファイルが存在しない場合にコメント付きプロジェクトローカル `config/.env` テンプレートを作成します。

Python の直接実行エントリーポイントも、プロジェクトローカル `config/.env` が存在すれば自動ロードするため、手動実行時も shell ランナーと挙動をそろえやすくなっています。

```bash
# ========== Cron 環境変数（定期タスクに必須） ==========
NVM_DIR="/root/.nvm"
CRON_PATH="/root/.nvm/versions/node/v22.22.0/bin:/root/.local/bin:/root/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/usr/local/bin:/usr/bin:/bin:/root/.npm-global/bin"

# ========== 必須設定 ==========
MEMORY_DIR="/root/.openclaw/workspace/memory"

# ========== オプション設定 ==========
OPENCLAW_BIN="/root/.nvm/versions/node/v22.22.0/bin/openclaw"  # Cron で推奨
LOG_FILE="/root/.openclaw/logs/health_report_pro.log"

# メッセージ推送（オプション）
DINGTALK_WEBHOOK="https://..."
FEISHU_WEBHOOK="https://..."
TELEGRAM_BOT_TOKEN="..."
TELEGRAM_CHAT_ID="..."

# AI 機能（オプション）
TAVILY_API_KEY="tvly-..."

# PDF レポート（オプション）
REPORT_WEB_DIR="/var/www/html/reports"
REPORT_BASE_URL="https://example.com/reports"

# フォントダウンロード（デフォルト：false）
ALLOW_RUNTIME_FONT_DOWNLOAD="false"
```

### 3. セットアップウィザードの実行

```bash
python scripts/init_config.py
```

ウィザードはすべての永続設定を `config/user_config.json` に書き込みます：
- 基本プロフィール
- 管理対象の病種一覧と主病種
- 採点モジュールと重み
- 服薬モジュール
- 常居地（月報医療計画で使用）
- 追加モニタリングモジュール
- `report_preferences.population_branch`（ライフスタイル vs 疾患管理の分岐制御）
- レポート設定と AI 生成設定

### 4. レポートの生成

```bash
# 日報
python scripts/daily_report_pro.py /path/to/memory/2026-03-20.md 2026-03-20

# 週報
python scripts/weekly_report_pro.py 2026-03-20

# 月報
python scripts/monthly_report_pro.py 2026-03-20
```

### 5. オプション Shell ランナー（Cron 用）

```bash
scripts/daily_health_report_pro.sh
scripts/weekly_health_report_pro.sh
scripts/monthly_health_report_pro.sh
```

**Cron 環境注釈**: スケジュール実行 Shell が対話的 Node/NVM `PATH` を継承しない場合、`config/.env` に `OPENCLAW_BIN` を設定してください。日報ランナーと Python コントローラーは両方とも、ローカル LLM 実行の第一選択レジゾルバーとしてこれを使用します。

`OPENCLAW_BIN` を未設定の場合、Python ランナーは以下の一般的なインストール場所を試行します：
- `/root/.nvm/versions/node/*/bin/openclaw`
- `/usr/local/bin/openclaw`
- `/usr/bin/openclaw`
- Windows 標準 Node.js パス

### 6. オプション英語メモリミラー

```bash
python scripts/export_memory_en.py
```

使用場面：
- ローカルメモリファイルの英語ミラーが必要な場合
- 中文字体がない場合の英語レンダリングパス
- レポート出力の二言語回帰テスト

---

## ⚙️ 設定リファレンス

### `config/user_config.json`

メインの長期プロフィールファイル。以下を保存：
- ユーザープロフィール
- 管理対象の病種一覧と主病種
- 採点モジュールと重み
- 服薬設定
- 常居地メタデータ
- 追加モニタリングモジュール
- レポート設定
- AI 生成設定

**重要**：`report_preferences.population_branch`
- サポート値：`lifestyle` / `disease`
- サンプル設定は `lifestyle` から開始
- セットアップウィザードは `balanced` / `fat_loss` なら `lifestyle`、疾病管理目標なら `disease` を自動提案

### 共通ランタイム変数

| 変数 | 必須 | 用途 |
|------|------|------|
| `MEMORY_DIR` | はい | 健康メモリディレクトリを指す |
| `TAVILY_API_KEY` | いいえ | Tavily 検索 fallback を有効化 |
| `DINGTALK_WEBHOOK` | いいえ | 要約と PDF リンクを DingTalk へ推送 |
| `FEISHU_WEBHOOK` | いいえ | 要約と PDF リンクを Feishu へ推送 |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | いいえ | 要約と PDF リンクを Telegram へ推送 |
| `REPORT_WEB_DIR` | いいえ | 生成 PDF を Web ディレクトリへコピー |
| `REPORT_BASE_URL` | いいえ | 推送メッセージ用公開 PDF URL を構築 |
| `ALLOW_RUNTIME_FONT_DOWNLOAD` | いいえ | ランタイムフォントダウンロードを許可（デフォルト：false） |

---

## 📝 メモリ書き込みプロトコル

アシスタントが `MEMORY_DIR` へ書き込む場合、**厳格なデータレコーダー**として動作する必要があります。

### 厳守ルール

- ❌ コメント禁止
- ❌ 励まし禁止
- ❌ まとめ禁止
- ❌ Emoji 使用禁止
- ❌ チャットフィラー禁止

### 構造ルール

- ✅ 食事、飲水、服薬、運動イベントは**レベル 3 見出し**を使用し、時間マーカーを付与（例：`### 朝食（約 08:50）`）
- ✅ 飲水ブロックは最小限かつ安定に保つ（飲水量 + 累計のみ）
- ✅ 1 日歩数合計は**専用レベル 2 セクション**内に配置（`## 今日歩数`）
- ✅ カスタムモニタリングモジュールは安定したレベル 2 セクション名を維持
- ✅ 1 つのデータブロック内で複数言語を混在させない

### 最小例

```markdown
# 2026-03-20 健康記録

## 体重記録
- 朝起床空腹時：64.4kg

## 飲水記録
### 午前（約 08:45）
- 飲水量：300ml
- 累計：300ml/2000ml

## 飲食記録
### 朝食（約 08:50）
- オートミール 50g → 約 190kcal
- 脱脂ミルク 250ml → 約 87kcal

## 運動記録
### 午後サイクリング（約 17:10）
- 距離：10.2km
- 時間：42 分
- 消費：約 290kcal

## 今日歩数
- 総歩数：8200 歩
```

### 拡張可能モニタリングモジュール

```markdown
## 血圧記録
### 朝（約 08:00）
- 血圧：128/82 mmHg
- 心拍数：72 bpm

## 血糖記録
### 食後（約 10:10）
- 血糖：7.1 mmol/L
- タイミング：朝食後 2 時間

## 体組成記録
- 体重：64.4kg
- 体脂肪率：18.6%

## 生化学指標
- ALT: 34 U/L
- AST: 28 U/L
```

### 禁止コンテンツ

- `評価`
- `状態`
- `まとめ`
- 動機付けフィラー
- デバッグログ
- システムログ

---

## 🔤 フォントフォールバック

### 推奨 CJK フォント

- `assets/NotoSansSC-VF.ttf`（中国語）
- `assets/NotoSansJP-VF.ttf`（日本語）

### 必須フォントが欠落している場合

- レンダラーは英語安全レンダリングパスに切り替え
- PDF にレンダリング注釈を追加
- **中国語 PDF ユーザー**: `NotoSansSC-VF.ttf` を `assets/` ディレクトリに配置
- **日本語 PDF ユーザー**: `NotoSansJP-VF.ttf` を `assets/` ディレクトリに配置

---

## 🧪 トラブルシューティング

### `MEMORY_DIR` が缺失

**症状**: Shell ランナーが即座にエラーで停止

**解決策**:
- `config/.env` またはランタイム環境で `MEMORY_DIR` を明示的に設定
- ClawHub 手動アップロードユーザー：`config/user_config.example.json` → `env` から `MEMORY_DIR` 例をコピー

### 月報病院推奨が一般的すぎる

**症状**: 病院推奨に具体的な医師名がない、またはテンプレート的に感じる

**解決策**:
1. `config/user_config.json` に常居地が設定されているか確認
2. ローカル LLM 実行が利用可能か確認（Cron の場合は `OPENCLAW_BIN` を設定）
3. 検索強化 fallback のために `TAVILY_API_KEY` を設定
4. LLM が一時的に利用できない場合でも、都市レベルローカルルール層は、策划データが存在する場所で実際の"病院 + 医師"組み合わせを優先出力

### 中国語/日本語 PDF が英語にフォールバック

**症状**: コンテンツは中国語/日本語なのに PDF が英語でレンダリングされる

**解決策**:
- 必須 CJK フォントが欠落
- `assets/NotoSansSC-VF.ttf` または `assets/NotoSansJP-VF.ttf` をローカルに配置して再生成

### 推送メッセージが缺失

**症状**: レポートは生成されたが、DingTalk/Feishu/Telegram メッセージを受信しない

**解決策**:
- `config/.env` に対応する webhook 変数が設定されているか確認
- `logs/` ディレクトリでランタイム推送出力を調査
- webhook URL が有効で期限切れでないか確認

---

## 🔒 プライバシー＆ローカル優先設計

Health-Mate は明示的なプライバシー境界を基に構築されています。

### デフォルトでローカル完結（ネット接続不要）

- 📁 **Markdown 解析**: すべての健康データをローカル `MEMORY_DIR` ファイルから抽出
- 📊 **採点＆チャート**: 疾患感知採点、統計計算、チャートレンダリング
- 📄 **PDF 生成**: ReportLab が完全にオフラインで PDF をレンダリング
- 📝 **LLM コメント**: ローカル `openclaw agent --local` で AI 洞察を生成（クラウド API 不要）
- 🧹 **LLM 出力クリーンアップ**: AI コメントをテキスト配信や PDF に埋め込む前に、`[qqbot-*]`、`[adp-*]`、`[openclaw*]` などのプラグイン登録ログノイズを除去します

### 明示的オプトインが必要（オプション）

- 🌐 **Tavily 検索**: `TAVILY_API_KEY` を設定した場合のみ（病院推奨または fallback 指導用）
- 📤 **Webhook 配信**: DingTalk/Feishu/Telegram 認証情報を設定した場合のみ
- ⬇️ **ランタイムフォントダウンロード**: デフォルトで無効化；`ALLOW_RUNTIME_FONT_DOWNLOAD=true` を明示的に設定した場合のみ許可

### 推奨デプロイ方法

```bash
# 仮想環境またはコンテナで分離
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# MEMORY_DIR をプライベートディレクトリに明示的に設定
export MEMORY_DIR="$HOME/.health-mate/memory"

# 必要でない限り webhook や Tavily を設定しない
# 最大限のプライバシー保護のため TAVILY_API_KEY と WEBHOOK_URLs を未設定に
```

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

## 📬 サポート

- **GitHub Issues**: https://github.com/tankeito/Health-Mate/issues
- **Repository**: https://github.com/tankeito/Health-Mate
- **Email**: tqd354@gmail.com

---

**Health-Mate** | ローカル優先多言語ヘルスレポートシステム

**Developed by tankeito** | MIT License | 2026
