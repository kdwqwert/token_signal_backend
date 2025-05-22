import os
import xgboost as xgb
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# 📁 model 폴더 없으면 생성
os.makedirs("model", exist_ok=True)

# 1. 데이터 준비
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. 모델 훈련
model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
model.fit(X_train, y_train)

# 3. 저장
model_path = "model/xgb_model.json"
model.save_model(model_path)

print(f"✅ 모델 저장 완료: {model_path} (크기: {os.path.getsize(model_path)} 바이트)")
