import yfinance as yf
import pandas as pd
from openai import OpenAI
import os
import requests
import json
from datetime import datetime

# --- 設定 (Configuration) ---
TARGET_TICKER = "MXNJPY=X"      # 監視対象: MXN/JPY (メキシコペソ/円)
ALERT_THRESHOLD = 0.5           # 変動率アラート閾値 (%)

# OpenAI設定 (環境変数からキーを取得)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def fetch_market_data(ticker_symbol):
    """Yahoo Financeからデータを取得する"""
    print(f"[*] Fetching data for {ticker_symbol}...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d", interval="1h")
        return df
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def get_ai_analysis(change_rate, price):
    """AIに相場解説を依頼する"""
    print("[*] Asking AI for analysis...")
    direction = "急騰（ペソ高・円安）" if change_rate > 0 else "急落（ペソ安・円高）"

    prompt = f"""
    あなたは新興国通貨FXで20年の経験を持つベテラン機関投資家です。
    MXN/JPY（メキシコペソ/円）が直近1時間で {change_rate:.2f}% {direction}しました。
    現在のレートは {price:.2f}円 です。

    この値動きに対し、以下の観点から短いコメント（150文字以内）を
    「だ・である」調で、冷静かつ客観的に作成してください：
    - 日本のFXスワップ投資家への影響（円でペソを買うポジション保有者）
    - 市場センチメント
    - 短期的な見通し
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたはプロのFXアナリストで、特に新興国通貨とスワップ投資に精通しています。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI分析エラー: {e}"

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

if __name__ == "__main__":
    print("=== AI FX Market Watcher (MXN/JPY) Started ===")
    df = fetch_market_data(TARGET_TICKER)
    analyze_market(df)
    print("=== End of Process ===")
