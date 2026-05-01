# AI FX市場監視Bot 実装・運用手順書（Slack統合版 - ID015）

**作業場所**: `C:\path\to\fx-monitoring-dashboard`
**最終更新**: 2026-01-10

---

## 📋 このドキュメントについて

このドキュメントは、**ID002（基本版）→ ID084（FX特化版）→ ID015（Slack統合版）** という進化の最終段階である、Slack統合版AI市場監視Botの実装・運用手順を記録したものです。

### 前提条件
- ID084（FXメキシコペソ版）の知識があること
- Windows環境でPowerShellを使用すること
- Google Cloudアカウントを持っていること

---

## 📂 フォルダ構成

作業フォルダ（ID002_ID084_ID015）の最終構成：

```text
ID002_ID084_ID015/
├── venv/                                          # [自動生成] Python仮想環境フォルダ
├── main.py                                        # プログラム本体 (Slack通知機能追加)
├── requirements.txt                               # 必要なライブラリ一覧 (requests追加)
├── Dockerfile                                     # コンテナ設計図 (Python 3.11)
├── .gcloudignore                                  # GCPアップロード除外設定 ⭐重要
├── README.md                                      # 完全セットアップガイド
├── QUICKSTART.md                                  # 最短10分デプロイガイド (PowerShell版)
├── ID015_AI_FX市場監視Bot_実装・運用手順書_Slack統合版.md  # このファイル
├── トラブルシューティング.md                        # 問題解決ガイド ⭐必読
└── 進捗_次回作業メモ.md                            # 進捗管理ファイル
```

> **⭐ 重要**: `.gcloudignore` ファイルがないと、venvフォルダがGCPにアップロードされてデプロイエラーになります。

---

## 📚 用語解説 (Glossary)

| 用語 | 解説 |
| :--- | :--- |
| **Slack Webhook** | SlackにメッセージをPOST送信するためのURL。Incoming Webhooksアプリで発行。 |
| **ハートビート信号** | システムが正常稼働していることを示す定期的な通知。異常検知だけでなく正常時も通知。 |
| **オブザーバビリティ** | システムの内部状態を外部から観察・監視できる度合い。Slack統合により向上。 |
| **OAuth認証** | Cloud Run Jobs用の認証方式。OIDC（Cloud Run Services用）とは異なる。 |
| **.gcloudignore** | GCPへのデプロイ時に除外するファイル/フォルダを指定するファイル。 |
| **PowerShell改行** | バックティック `` ` `` を使用。バックスラッシュ `\` は使えない。 |

---

## Part 1: 環境準備とファイル作成

### 1-1. ID084からのファイルコピー

既存のID084（ID002_PoC_Mexico）から必要なファイルをコピーします。

```powershell
# 作業フォルダに移動
cd C:\path\to\fx-monitoring-dashboard

# 必要なファイルをコピー
Copy-Item ..\ID002_PoC_Mexico\main.py .
Copy-Item ..\ID002_PoC_Mexico\requirements.txt .
Copy-Item ..\ID002_PoC_Mexico\Dockerfile .
```

### 1-2. requirements.txtにrequestsライブラリを追加

```text
yfinance
pandas
openai
requests
```

### 1-3. .gcloudignoreファイルの作成

⭐ **超重要**: このファイルがないと、venvフォルダがアップロードされてエラーになります。

`.gcloudignore` ファイルを作成し、以下の内容を記述：

```gitignore
# Python仮想環境を除外
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# エディタ・IDE設定ファイル
.vscode/
.idea/
*.swp
*.swo
*~

# OS生成ファイル
.DS_Store
Thumbs.db

# Git関連
.git/
.gitignore

# ドキュメント（デプロイ不要）
README.md
QUICKSTART.md

# その他
*.log
.env
```

### 1-4. main.pyにSlack通知機能を追加

既存のmain.pyに以下を追加：

#### インポート追加
```python
import requests
import json
from datetime import datetime
```

#### Slack通知関数の追加
```python
def send_to_slack(text, status="Normal", price=None, change_rate=None):
    """Slack Webhookへ通知を送信する"""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[!] SLACK_WEBHOOK_URL is not set. Skipping Slack notification.")
        return

    # ステータスに応じたカラー設定
    color = "#36a64f" if status == "Normal" else "#eb4034"
    emoji = "✅" if status == "Normal" else "🚨"

    # メッセージのタイトル作成
    if price and change_rate is not None:
        title = f"{emoji} 資産運用監視レポート: {status} | MXN/JPY: {price:.2f}円 ({change_rate:+.2f}%)"
    else:
        title = f"{emoji} 資産運用監視レポート: {status}"

    # Slack Attachments形式でペイロード作成
    payload = {
        "attachments": [{
            "fallback": f"Market Report: {status}",
            "color": color,
            "title": title,
            "text": text,
            "footer": "AI FX Watcher Bot (MXN/JPY)",
            "ts": int(datetime.now().timestamp())
        }]
    }

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            print("[✓] Slack notification sent successfully.")
        else:
            print(f"[!] Slack notification failed: {response.status_code}")
    except Exception as e:
        print(f"[!] Error sending to Slack: {e}")
```

#### analyze_market関数の修正
```python
def analyze_market(df):
    if df is None or len(df) == 0: return

    latest = df.iloc[-1]
    open_price = latest['Open']
    close_price = latest['Close']
    change_rate = ((close_price - open_price) / open_price) * 100

    print(f"MXN/JPY Rate: {close_price:.2f}円 (Change: {change_rate:.2f}%)")

    if abs(change_rate) >= ALERT_THRESHOLD:
        if change_rate > 0:
            direction = "急騰（ペソ高）"
            impact = "✨ スワップ投資家：含み益拡大の可能性"
        else:
            direction = "急落（ペソ安）"
            impact = "⚠️ スワップ投資家：含み損拡大の可能性"

        print(f"🚨 ALERT: {TARGET_TICKER} が {direction} しました！")
        print(f"{impact}")

        # AI分析を実行
        ai_comment = get_ai_analysis(change_rate, close_price)
        print(f"\n🤖 AIアナリストのコメント:\n{ai_comment}")

        # Slack通知（アラート）
        slack_message = f"*{TARGET_TICKER} が {direction} しました！*\n\n{impact}\n\n🤖 *AIアナリストのコメント:*\n{ai_comment}"
        send_to_slack(slack_message, status="ALERT", price=close_price, change_rate=change_rate)
    else:
        print("✅ 異常なし（安定推移）")

        # Slack通知（正常・ハートビート）
        slack_message = f"市場は安定推移しています。\n現在のレート: {close_price:.2f}円 (変動率: {change_rate:+.2f}%)"
        send_to_slack(slack_message, status="Normal", price=close_price, change_rate=change_rate)
```

---

## Part 2: Slack Webhook URLの取得

### 2-1. Slackワークスペースにログイン
[https://slack.com/](https://slack.com/) からワークスペースを選択

### 2-2. Incoming Webhooksアプリを追加
1. ワークスペース名 > 「その他」 > 「アプリを検索」
2. 「**Incoming Webhooks**」を検索してインストール
3. 「Slackに追加」をクリック

### 2-3. Webhook URLを発行
1. 通知先チャンネルを選択（例: `#fx-market-alerts`）
2. 「Incoming Webhookインテグレーションの追加」をクリック
3. 表示されたWebhook URL（`https://hooks.slack.com/services/...`）をコピー
4. メモ帳などに保存

---

## Part 3: ローカル環境でのテスト

### 3-1. Python仮想環境の構築

```powershell
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# ライブラリをインストール
pip install -r requirements.txt
```

### 3-2. 環境変数を設定（テスト用）

```powershell
# OpenAI APIキーを設定
$env:OPENAI_API_KEY="sk-..."

# Slack Webhook URLを設定（オプション）
$env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

> **注意**: Slack Webhook URLが未設定の場合、Slack通知はスキップされますが、プログラムは正常に動作します。

### 3-3. ローカルでテスト実行

```powershell
python main.py
```

**期待される出力**:
```
=== AI FX Market Watcher (MXN/JPY) Started ===
[*] Fetching data for MXNJPY=X...
MXN/JPY Rate: 8.77円 (Change: 0.12%)
✅ 異常なし（安定推移）
[✓] Slack notification sent successfully.
=== End of Process ===
```

---

## Part 4: Google Cloud へのデプロイ

### 4-1. GCPプロジェクトの設定

```powershell
# プロジェクトIDを設定（既存のプロジェクトを使用）
gcloud config set project fx-mxn-watcher-bot
```

### 4-2. 必要なAPIを有効化

```powershell
# 1行で実行（PowerShell用）
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com
```

> **重要**: PowerShellでは改行にバックティック `` ` `` を使用します。バックスラッシュ `\` は使えません。

### 4-3. Cloud Run Jobsへのデプロイ

```powershell
# プロジェクトフォルダに移動
cd C:\path\to\fx-monitoring-dashboard

# デプロイ実行（.gcloudignoreが必須）
gcloud run jobs deploy fx-mxn-watcher-slack --source . --region asia-northeast1
```

> **注意**: `Allow unauthenticated invocations?` と聞かれたら **N** (No) を選択

### 4-4. 環境変数の設定（重要）

⭐ **環境変数設定の罠**: `gcloud run jobs deploy` 実行後、環境変数が消える場合があります。以下の手順で確実に設定します。

```powershell
# Step 1: 既存の環境変数をクリア
gcloud run jobs update fx-mxn-watcher-slack --clear-env-vars --region asia-northeast1

# Step 2: OpenAI APIキーを設定
gcloud run jobs update fx-mxn-watcher-slack --update-env-vars OPENAI_API_KEY="sk-..." --region asia-northeast1

# Step 3: Slack Webhook URLを設定
gcloud run jobs update fx-mxn-watcher-slack --update-env-vars SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..." --region asia-northeast1

# Step 4: 設定を確認
gcloud run jobs describe fx-mxn-watcher-slack --region asia-northeast1
```

**確認ポイント**: `Env vars:` セクションに2つの環境変数が表示されること。

---

## Part 5: サービスアカウントと権限設定

### 5-1. サービスアカウントの作成（既存の場合はスキップ）

```powershell
# サービスアカウント作成
gcloud iam service-accounts create cloud-scheduler-runner --display-name="Cloud Scheduler Runner"
```

> **注意**: 既に存在する場合は `Resource ... already exists` エラーが出ますが、問題ありません。

### 5-2. 権限の付与

```powershell
# プロジェクトIDを取得
$PROJECT_ID = gcloud config get-value project

# プロジェクト全体の権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.developer"

# 個別Jobの実行権限を付与
gcloud run jobs add-iam-policy-binding fx-mxn-watcher-slack --region=asia-northeast1 --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.invoker"
```

---

## Part 6: Cloud Schedulerの設定

### 6-1. 毎時自動実行の設定

```powershell
# プロジェクトIDを取得
$PROJECT_ID = gcloud config get-value project

# Cloud Schedulerで毎時0分に実行
gcloud scheduler jobs create http fx-mxn-watcher-slack-schedule --location=asia-northeast1 --schedule="0 * * * *" --time-zone="Asia/Tokyo" --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher-slack:run" --http-method=POST --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

> **重要**: `--oauth-service-account-email` を使用します（`--oidc-...` ではありません）。

---

## Part 7: 動作確認とテスト

### 7-1. 手動実行テスト

```powershell
# 直接実行（最新の設定が反映される）
gcloud run jobs execute fx-mxn-watcher-slack --region=asia-northeast1 --wait
```

### 7-2. ログ確認

```powershell
# 最新10件のログを表示
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher-slack" --limit 10 --format="table(timestamp, textPayload)"
```

**期待される出力**:
```
TIMESTAMP                    TEXT_PAYLOAD
2026-01-10T09:17:33.594554Z  === End of Process ===
2026-01-10T09:17:33.593526Z  [✓] Slack notification sent successfully.  ← 重要！
2026-01-10T09:17:33.364902Z  ✅ 異常なし（安定推移）
2026-01-10T09:17:33.364885Z  MXN/JPY Rate: 8.77円 (Change: 0.00%)
2026-01-10T09:17:31.306253Z  [*] Fetching data for MXNJPY=X...
2026-01-10T09:17:31.306223Z  === AI FX Market Watcher (MXN/JPY) Started ===
```

### 7-3. Slack通知の確認

設定したSlackチャンネルに以下のような通知が届いていることを確認：

```
✅ 資産運用監視レポート: Normal | MXN/JPY: 8.77円 (+0.00%)
市場は安定推移しています。
現在のレート: 8.77円 (変動率: +0.00%)

AI FX Watcher Bot (MXN/JPY)  |  2026年1月10日 18:17
```

---

## Part 8: 自動実行の確認

### 8-1. 次の毎時0分まで待機

次の毎時0分（例: 18:00, 19:00など）の数分後にログとSlackを確認します。

### 8-2. 自動実行後の確認

```powershell
# ログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher-slack" --limit 10 --format="table(timestamp, textPayload)"

# 実行履歴確認
gcloud run jobs executions list --job=fx-mxn-watcher-slack --region=asia-northeast1 --limit=10
```

---

## 運用コマンド集

### 監視頻度の変更

```powershell
# 30分ごとに実行
gcloud scheduler jobs update http fx-mxn-watcher-slack-schedule --schedule="*/30 * * * *" --location=asia-northeast1

# 1時間ごと（デフォルト）
gcloud scheduler jobs update http fx-mxn-watcher-slack-schedule --schedule="0 * * * *" --location=asia-northeast1

# 6時間ごと
gcloud scheduler jobs update http fx-mxn-watcher-slack-schedule --schedule="0 */6 * * *" --location=asia-northeast1
```

### アラート閾値の変更

main.pyの8行目を編集して再デプロイ：
```python
ALERT_THRESHOLD = 0.5   # 例: 1.0 に変更
```

再デプロイ：
```powershell
gcloud run jobs deploy fx-mxn-watcher-slack --source . --region asia-northeast1
```

### 状態確認コマンド

```powershell
# Jobの状態確認
gcloud run jobs describe fx-mxn-watcher-slack --region=asia-northeast1

# Schedulerの状態確認
gcloud scheduler jobs describe fx-mxn-watcher-slack-schedule --location=asia-northeast1

# 実行履歴確認（最新10件）
gcloud run jobs executions list --job=fx-mxn-watcher-slack --region=asia-northeast1 --limit=10
```

---

## トラブルシューティング

詳細は `トラブルシューティング.md` を参照してください。

### よくある問題

1. **venvフォルダがアップロードされてエラー**
   - 解決: `.gcloudignore` ファイルを作成

2. **PowerShellでコマンドがエラーになる**
   - 症状: `run.googleapis.com : 用語 'run.googleapis.com' は、コマンドレット...`
   - 解決: 改行にバックティック `` ` `` を使用、または1行で記述

3. **環境変数が反映されない**
   - 解決: `--clear-env-vars` → `--update-env-vars` で個別に設定

4. **Slack通知が届かない**
   - 確認: ログに `[✓] Slack notification sent successfully.` が表示されているか
   - 確認: Webhook URLが正しく設定されているか

---

## 付録：PowerShell vs Bash コマンド対応表

| 操作 | PowerShell (Windows) | Bash (Linux/Mac) |
|------|---------------------|------------------|
| **改行** | バックティック `` ` `` | バックスラッシュ `\` |
| **環境変数取得** | `$PROJECT_ID = gcloud ...` | `PROJECT_ID=$(gcloud ...)` |
| **環境変数設定** | `$env:KEY="value"` | `export KEY="value"` |
| **複数行コマンド** | 1行で記述を推奨 | `\` で改行可能 |

---

## まとめ

✅ **ID015 Slack統合版の完成**
- Slack通知機能の追加
- ハートビート信号の実装
- オブザーバビリティの向上

✅ **運用コスト**
- GCP: 無料枠内（月額 0円）
- OpenAI API: 月額 数円〜数十円

✅ **次のステップ**
- 毎時自動実行の確認
- 必要に応じてSchedulerの再作成

---

**作成日**: 2026-01-10
**バージョン**: ID015 - Slack統合版
**前バージョン**: ID084 - FXメキシコペソ特化版
