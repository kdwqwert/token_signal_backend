from fastapi import FastAPI
from datetime import datetime
import requests
import xgboost as xgb
import pandas as pd
import os
import json

# FastAPI 앱 인스턴스
app = FastAPI()

# 환경 변수에서 텔레그램 정보 가져오기
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
MODEL_PATH = "model/xgb_model.json"
UNLOCK_JSON_PATH = "data/unlock_schedule.json"

# XGBoost 모델 로드
model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)

# 특성 추출 함수 (현재는 더미 데이터)
def extract_features(symbol: str) -> pd.DataFrame:
    return pd.DataFrame([{
        "rsi": 53,
        "volume": 1.5,
        "volatility": 0.3,
        "funding_rate": -0.01,
        "ma_5": 0.9
    }])

# 예측 함수
def predict_signal(symbol: str) -> dict:
    features = extract_features(symbol)
    pred = model.predict(features)[0]
    proba = model.predict_proba(features).max()
    return {
        "symbol": symbol,
        "direction": int(pred),
        "confidence": round(proba * 100, 2),
        "predicted_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

# 텔레그램 메시지 발송 함수
def send_telegram_message(message: str):
    print(f"[텔레그램 전송 시도] → {message}")  # 로그 추가
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)  # response 정의 누락되어 있었음
    print(f"[텔레그램 응답] {response.status_code} - {response.text}")  # 응답 확인


# 수동 입력된 unlock 일정 불러오기
def fetch_unlock_schedule():
    with open(UNLOCK_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# 전역 시그널 저장용 리스트
signals = []

# 시그널 확인용 엔드포인트
@app.get("/api/signals")
def get_signals():
    return signals

# unlock JSON 디버그 확인용
@app.get("/api/debug-unlocks")
def debug_unlocks():
    return fetch_unlock_schedule()

# 시그널 생성 + 텔레그램 전송
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
            f"📢 *[시그널 알림 - {result['symbol']}]*\n"
            f"📈 포지션: {'롱' if result['direction'] == 1 else '숏'}\n"
            f"📊 신뢰도: {result['confidence']}%\n"
            f"🔓 Unlock: {result['unlock_date']}"
        )
        send_telegram_message(msg)

    signals = results
    return {"status": "ok", "count": len(signals)}
