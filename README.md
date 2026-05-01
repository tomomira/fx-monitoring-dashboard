# FX Monitoring Dashboard (Slack統合版)

メキシコペソ／円（MXN/JPY）レートを24時間監視し、急変動時にAI（OpenAI GPT-4o-mini）が解説を生成、結果を **Slackへリアルタイム通知** する不労所得運用ダッシュボードです。Google Cloud Run Jobs + Cloud Schedulerで自動実行されます。

> 📝 解説記事:[【統合監視】AI市場監視BotをSlackへ接続せよ。エンジニアのための「不労所得・運用ダッシュボード」構築術](https://note.com/lively_hippo6176/n/n4e8e8e0b30d0)

## 主な機能

- **MXN/JPY の24時間監視**（yfinance経由）
- **変動率0.5%以上で自動アラート**
- **OpenAI GPT-4o-miniによるAI分析**（日本のFXスワップ投資家向けに最適化）
- **Slackへのリアルタイム通知**
  - 正常時: 緑色のハートビート信号（市場安定の確認）
  - アラート時: 赤色の警告メッセージ + AI解説
- **Cloud Run Jobs + Cloud Schedulerで毎時自動実行**

## ファイル構成

```
fx-monitoring-dashboard/
├── main.py                                 # メインプログラム（Slack連携機能含む）
├── requirements.txt                        # 依存ライブラリ
├── Dockerfile                              # GCPデプロイ用コンテナ定義
├── .env.example                            # 環境変数テンプレ
├── .gitignore
├── .gcloudignore
├── QUICKSTART.md                           # クイックスタート手順
├── README.md                               # このファイル
├── トラブルシューティング.md
├── 進捗_次回作業メモ.md
└── ID015_AI_FX市場監視Bot_実装・運用手順書_Slack統合版.md
```

## ローカル環境でのテスト

### 1. Python仮想環境の構築（Windows PowerShell）

```powershell
cd C:\Users\tomom\APP_DEV\fx-monitoring-dashboard
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を参考に、以下2つを設定:

```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key"
$env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/<WORKSPACE_ID>/<CHANNEL_ID>/<TOKEN>"
```

> Slack Webhook URL未設定の場合、Slack通知はスキップされコンソール出力のみになります。

### 3. テスト実行

```powershell
python main.py
```

期待される出力:

```
=== AI FX Market Watcher (MXN/JPY) Started ===
[*] Fetching data for MXNJPY=X...
MXN/JPY Rate: 8.97円 (Change: 0.00%)
✅ 異常なし（安定推移）
[✓] Slack notification sent successfully.
=== End of Process ===
```

## Slack Webhook URLの取得方法

1. [Slack](https://slack.com/) で対象ワークスペースにログイン
2. アプリ → 「Incoming Webhooks」を検索 → インストール
3. 通知先チャンネル（例: `#fx-market-alerts`）を選択
4. 発行された Webhook URL（`https://hooks.slack.com/services/...`）を環境変数 `SLACK_WEBHOOK_URL` に設定

## GCPへのデプロイ

```bash
# Cloud Run Jobsへデプロイ
gcloud run jobs deploy fx-mxn-watcher-slack \
  --source . \
  --region asia-northeast1

# 環境変数設定
gcloud run jobs update fx-mxn-watcher-slack \
  --set-env-vars OPENAI_API_KEY="<YOUR_KEY>",SLACK_WEBHOOK_URL="<YOUR_WEBHOOK_URL>" \
  --region asia-northeast1

# Cloud Scheduler（6時間毎実行、OAuth認証）
PROJECT_ID=$(gcloud config get-value project)
gcloud scheduler jobs create http fx-mxn-watcher-slack-schedule \
  --location=asia-northeast1 \
  --schedule="0 */6 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher-slack:run" \
  --http-method=POST \
  --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

詳細手順は [QUICKSTART.md](./QUICKSTART.md) と [ID015_AI_FX市場監視Bot_実装・運用手順書_Slack統合版.md](./ID015_AI_FX市場監視Bot_実装・運用手順書_Slack統合版.md) を参照。

> ⚠️ Cloud Run **Jobs** はOAuth認証が必須（OIDC不可）。

## Slack通知の例

### 正常時（ハートビート）
```
✅ 資産運用監視レポート: Normal | MXN/JPY: 8.97円 (+0.12%)
市場は安定推移しています。
```
カラー: 緑（#36a64f）

### アラート時
```
🚨 資産運用監視レポート: ALERT | MXN/JPY: 8.45円 (-0.68%)
MXNJPY=X が 急落（ペソ安） しました！

⚠️ スワップ投資家：含み損拡大の可能性

🤖 AIアナリストのコメント:
メキシコ中央銀行の利下げ示唆を受け、ペソが売られている。
スワップ投資家は維持率の確認が必要だ。短期的には8.40円付近が
サポートラインとなる可能性がある。
```
カラー: 赤（#eb4034）

## トラブルシューティング

### Slack通知が送信されない
- `SLACK_WEBHOOK_URL` が正しく設定されているか確認
- Webhook URL の有効期限・有効性を確認
- ログに `[!] SLACK_WEBHOOK_URL is not set.` と表示される場合は環境変数が未設定

### AI分析エラー
- `OPENAI_API_KEY` が正しく設定されているか確認
- OpenAI APIの残高を確認

### yfinanceでデータ取得エラー
- Python 3.11以上を使用しているか確認
- インターネット接続を確認

詳細は [トラブルシューティング.md](./トラブルシューティング.md) を参照。

## 運用コスト

- **GCP**: 無料枠内（月額 ¥0）
- **OpenAI API**: 月額数十円程度（GPT-4o-mini）
- **Slack**: 無料プランで利用可能

## 関連プロジェクト

- [ai-market-watchdog-mxn](https://github.com/tomomira/ai-market-watchdog-mxn) — Slack無し版（本プロジェクトのベース）

## ライセンス

MIT License — 詳細は [LICENSE](./LICENSE) を参照
