# クイックスタートガイド - ID015 Slack統合版

このガイドでは、最短でSlack統合版のAI市場監視Botをデプロイする手順を説明します。

> **💻 環境について**: このガイドは **Windows PowerShell** 向けに記載しています。Linux/Mac環境の方は、コマンド例の補足を参照してください。

## 📋 事前準備チェックリスト

以下を準備してから始めてください：

- [ ] Google Cloudアカウント（無料枠利用可能）
- [ ] OpenAI APIキー（`sk-`で始まる文字列）
- [ ] Slack Webhook URL（`https://hooks.slack.com/services/...`）
- [ ] gcloud CLIインストール済み

## 🚀 最短デプロイ手順（所要時間: 約10分）

### Step 1: Slack Webhook URLを取得（所要3分）

#### 1-1. Slackワークスペースにログイン
[https://slack.com/](https://slack.com/) からワークスペースを選択

#### 1-2. Incoming Webhooksアプリを追加
1. ワークスペース名 > 「その他」 > 「アプリを検索」をクリック
2. 検索バーに「**Incoming Webhooks**」と入力
3. 「Slackに追加」をクリック

#### 1-3. 通知チャンネルを選択してWebhook URLを発行
1. 通知先チャンネルを選択（例: `#fx-market-alerts`）
   - チャンネルがない場合は新規作成してください
2. 「Incoming Webhookインテグレーションの追加」をクリック
3. 表示された **Webhook URL** をコピー
   ```
   https://hooks.slack.com/services/<WORKSPACE_ID>/<CHANNEL_ID>/<TOKEN>
   ```
4. この URLをメモ帳などに保存（後で環境変数に設定します）

#### 1-4. 通知設定のカスタマイズ（オプション）
- アイコンの変更
- Bot名の変更（例: 「FX Market Watcher」）
- チャンネル固定の確認

---

### Step 2: GCP プロジェクトの設定（所要3分）

```powershell
# プロジェクトIDを設定（既存のプロジェクトを使う場合）
gcloud config set project YOUR_PROJECT_ID
```

<details>
<summary>📌 新規プロジェクトを作成する場合（クリックで展開）</summary>

```powershell
# タイムスタンプ付きプロジェクト名で作成
$timestamp = [int](Get-Date -UFormat %s)
gcloud projects create "fx-market-watcher-$timestamp" --name="FX Market Watcher"
gcloud config set project "fx-market-watcher-$timestamp"
```

</details>

#### 必要なAPIを有効化

**Windows PowerShell:**
```powershell
# 1行で実行（推奨）
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com
```

<details>
<summary>🐧 Linux/Mac環境の方はこちら</summary>

```bash
# 改行を使った記述（Bash/Zsh）
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com
```

</details>

---

### Step 3: Cloud Run Jobsにデプロイ（所要2分）

**Windows PowerShell:**
```powershell
# プロジェクトフォルダに移動
cd C:\path\to\fx-monitoring-dashboard

# デプロイ実行（初回は3-5分かかります）
gcloud run jobs deploy fx-mxn-watcher-slack --source . --region asia-northeast1
```

<details>
<summary>🐧 Linux/Mac環境の方はこちら</summary>

```bash
cd /path/to/fx-monitoring-dashboard

gcloud run jobs deploy fx-mxn-watcher-slack \
  --source . \
  --region asia-northeast1
```

</details>

> **注意**: `Allow unauthenticated invocations?` と聞かれたら **N** (No) を選択

---

### Step 4: 環境変数を設定（所要1分）

**Windows PowerShell:**
```powershell
# OpenAI APIキーとSlack Webhook URLを一括設定
gcloud run jobs update fx-mxn-watcher-slack --set-env-vars OPENAI_API_KEY="sk-あなたのAPIキー",SLACK_WEBHOOK_URL="https://hooks.slack.com/services/あなたのWebhookURL" --region asia-northeast1
```

<details>
<summary>🐧 Linux/Mac環境の方はこちら</summary>

```bash
gcloud run jobs update fx-mxn-watcher-slack \
  --set-env-vars OPENAI_API_KEY="sk-あなたのAPIキー",SLACK_WEBHOOK_URL="https://hooks.slack.com/services/あなたのWebhookURL" \
  --region asia-northeast1
```

</details>

> **重要**: 上記コマンドの `sk-...` と `https://hooks.slack.com/...` を、実際の値に置き換えてください

---

### Step 5: サービスアカウントの作成と権限付与（所要2分）

**Windows PowerShell:**
```powershell
# 1. サービスアカウント作成
gcloud iam service-accounts create cloud-scheduler-runner --display-name="Cloud Scheduler Runner"

# 2. プロジェクトIDを環境変数に保存
$PROJECT_ID = gcloud config get-value project

# 3. プロジェクト全体の権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.developer"

# 4. 個別Jobの実行権限を付与
gcloud run jobs add-iam-policy-binding fx-mxn-watcher-slack --region=asia-northeast1 --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.invoker"
```

<details>
<summary>🐧 Linux/Mac環境の方はこちら</summary>

```bash
# 1. サービスアカウント作成
gcloud iam service-accounts create cloud-scheduler-runner \
  --display-name="Cloud Scheduler Runner"

# 2. プロジェクトIDを環境変数に保存
PROJECT_ID=$(gcloud config get-value project)

# 3. プロジェクト全体の権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# 4. 個別Jobの実行権限を付与
gcloud run jobs add-iam-policy-binding fx-mxn-watcher-slack \
  --region=asia-northeast1 \
  --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

</details>

---

### Step 6: 毎時自動実行の設定（所要1分）

**Windows PowerShell:**
```powershell
# プロジェクトIDを再取得（念のため）
$PROJECT_ID = gcloud config get-value project

# Cloud Schedulerで毎時0分に実行
gcloud scheduler jobs create http fx-mxn-watcher-slack-schedule --location=asia-northeast1 --schedule="0 * * * *" --time-zone="Asia/Tokyo" --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher-slack:run" --http-method=POST --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

<details>
<summary>🐧 Linux/Mac環境の方はこちら</summary>

```bash
# プロジェクトIDを再取得（念のため）
PROJECT_ID=$(gcloud config get-value project)

# Cloud Schedulerで毎時0分に実行
gcloud scheduler jobs create http fx-mxn-watcher-slack-schedule \
  --location=asia-northeast1 \
  --schedule="0 * * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher-slack:run" \
  --http-method=POST \
  --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

</details>

> **重要**: `--oauth-service-account-email` を使用してください（`--oidc-...` ではありません）

---

### Step 7: 手動テスト実行（所要30秒）

```powershell
# 今すぐSchedulerを実行してテスト
gcloud scheduler jobs run fx-mxn-watcher-slack-schedule --location=asia-northeast1
```

#### 実行結果の確認

##### 方法1: ログで確認
```powershell
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher-slack" --limit 10 --format "table(timestamp, textPayload)"
```

期待される出力例：
```
TIMESTAMP                  TEXT_PAYLOAD
2025-01-10T12:05:00Z      === AI FX Market Watcher (MXN/JPY) Started ===
2025-01-10T12:05:01Z      [*] Fetching data for MXNJPY=X...
2025-01-10T12:05:03Z      MXN/JPY Rate: 8.74円 (Change: 0.12%)
2025-01-10T12:05:03Z      ✅ 異常なし（安定推移）
2025-01-10T12:05:04Z      [✓] Slack notification sent successfully.
2025-01-10T12:05:04Z      === End of Process ===
```

##### 方法2: Slackで確認
設定したチャンネル（例: `#fx-market-alerts`）に以下のようなメッセージが届いていればOKです：

```
✅ 資産運用監視レポート: Normal | MXN/JPY: 8.74円 (+0.12%)
市場は安定推移しています。
現在のレート: 8.74円 (変動率: +0.12%)

AI FX Watcher Bot (MXN/JPY)  |  2025年1月10日 12:05
```

---

## 🎉 デプロイ完了！

以上で、Slack統合版のAI市場監視Botが稼働開始しました。毎時0分に自動で市場をチェックし、Slackに通知が届きます。

---

## ⚙️ カスタマイズオプション

### 監視頻度を変更したい場合

```powershell
# 30分ごとに実行する場合
gcloud scheduler jobs update http fx-mxn-watcher-slack-schedule --schedule="*/30 * * * *" --location=asia-northeast1

# 6時間ごとに実行する場合
gcloud scheduler jobs update http fx-mxn-watcher-slack-schedule --schedule="0 */6 * * *" --location=asia-northeast1
```

### アラート閾値を変更したい場合

`main.py` の8行目を編集：
```python
ALERT_THRESHOLD = 0.5   # 0.5% → お好みの値に変更（例: 1.0）
```

変更後、再デプロイ：
```powershell
cd C:\path\to\fx-monitoring-dashboard
gcloud run jobs deploy fx-mxn-watcher-slack --source . --region asia-northeast1
```

---

## 🔧 トラブルシューティング

### Q1. Slack通知が届かない

**確認項目**:
1. Webhook URLが正しく設定されているか確認
   ```powershell
   gcloud run jobs describe fx-mxn-watcher-slack --region=asia-northeast1 --format="value(template.template.containers[0].env)"
   ```
2. ログに `[✓] Slack notification sent successfully.` が表示されているか確認
3. Slack Webhook が有効期限切れになっていないか確認

### Q2. Cloud Schedulerが403エラーで失敗する

**原因**: サービスアカウントの権限不足

**解決方法**: Step 5の権限付与コマンドを再実行してください。

### Q3. yfinanceでデータ取得エラーが出る

**確認項目**:
1. Dockerfileで `python:3.11-slim` が指定されているか確認
2. ログで具体的なエラーメッセージを確認

### Q4. PowerShellでコマンドがエラーになる

**症状**: `run.googleapis.com : 用語 'run.googleapis.com' は、コマンドレット、関数、スクリプト ファイル...`

**原因**: バックスラッシュ（`\`）を使った改行はPowerShellでは使えません

**解決方法**: このガイドのPowerShell版コマンド（1行形式）を使用してください

---

## 📊 運用コスト（参考）

- **GCP Cloud Run**: 無料枠内（月額 0円）
- **GCP Cloud Scheduler**: 無料枠内（月額 0円）
- **OpenAI API (GPT-4o-mini)**: 月額 数円〜数十円
- **Slack**: 無料プラン利用可能

**合計**: 月額 数円〜数十円程度

---

## 📚 詳細ドキュメント

より詳細な情報は以下を参照してください：

- [README.md](./README.md) - 完全なセットアップガイド
- [main.py](./main.py) - ソースコード
- [04_note/ID015_Note_*.md](../04_note/) - コンセプトと設計思想

---

**Happy Trading! 🚀📈**
