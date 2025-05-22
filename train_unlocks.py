from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.get("https://tokenomist.ai/unlocks")
time.sleep(5)  # 페이지 로딩 기다림

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

tokens = []
rows = soup.select("table tbody tr")
print(f"✅ 총 rows: {len(rows)}")

for row in rows:
    cols = row.find_all("td")

    # 심볼 텍스트가 포함된 td를 인덱스로 찾기 (ex: 1번째 td에 보통 있음)
    if len(cols) < 6:
        continue

    symbol_td = cols[1]  # 일반적으로 symbol + name이 있는 열
    text_lines = symbol_td.get_text("\n", strip=True).split("\n")
    if len(text_lines) < 2:
        continue
    symbol = text_lines[1].strip()  # 보통 두 번째 줄이 심볼

    # unlock까지 남은 시간 추출
    time_text = cols[-1].text.strip()
    days_match = re.search(r"(\d+)D", time_text)
    days = int(days_match.group(1)) if days_match else 0

    if days <= 7:
        unlock_date = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
        tokens.append({
            "symbol": symbol,
            "unlock_date": unlock_date
        })

# 저장
with open("unlock_schedule.json", "w", encoding="utf-8") as f:
    json.dump(tokens, f, indent=2, ensure_ascii=False)

print("✅ unlock_schedule.json 저장 완료")
