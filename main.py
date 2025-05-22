from fastapi import FastAPI
from datetime import datetime, timedelta
import requests
import xgboost as xgb
import pandas as pd
from bs4 import BeautifulSoup
import os
import re

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
MODEL_PATH = "model/xgb_model.json"
UNLOCK_URL = "https://token.unlocks.app/"

model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)

def extract_features(symbol: str) -> pd.DataFrame:
    return pd.DataFrame([{
        "rsi": 53,
        "volume": 1.5,
        "volatility": 0.3,
        "funding_rate": -0.01,
        "ma_5": 0.9
    }])

def predict_signal(symbol: str) -> dict:
    features = extract_features(symbol)
    pred = model.predict(features)[0]
    proba = model.predict_proba(features).max()
    return {
        "symbol": symbol,
        "direction": pred,
        "confidence": round(proba * 100, 2),
        "predicted_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def fetch_unlock_schedule():
    url = "https://tokenomist.ai/unlocks"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    rows = soup.select("table tbody tr")
    tokens = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        symbol = cols[0].text.strip().split("\n")[0]
        time_text = cols[5].text.strip()  # e.g. "0D 16H 43M 22S"

        # D만 추출
        days_match = re.search(r"(\d+)D", time_text)
        days = int(days_match.group(1)) if days_match else 0

        # 7일 이내만 추가
        if days <= 7:
            unlock_date = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
            tokens.append({
                "symbol": symbol,
                "unlock_date": unlock_date
            })

    return tokens

signals = []

@app.get("/api/signals")
def get_signals():
    return signals

@app.post("/api/generate")
def generate_signals():
    global signals
    unlock_list = fetch_unlock_schedule()
    results = []
    for token in unlock_list:
        result = predict_signal(token["symbol"])
        result["unlock_date"] = token["unlock_date"]
        results.append(result)
        msg = (
            f"📢 *[시그널 알림 - {result['symbol']}]\n"
            f"📈 포지션: {result['direction']}\n"
            f"📊 신뢰도: {result['confidence']}%\n"
            f"🔓 Unlock: {result['unlock_date']}"
        )
        send_telegram_message(msg)
    signals = results
    return {"status": "ok", "count": len(signals)}

@app.get("/api/debug-unlocks")
def debug_unlocks():
    tokens = fetch_unlock_schedule()
    return tokens