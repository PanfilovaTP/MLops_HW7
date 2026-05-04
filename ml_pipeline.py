import json
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
MODEL_PARAMS = {"n_estimators": 100, "random_state": RANDOM_STATE}

iris = load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y,
)

model = RandomForestClassifier(**MODEL_PARAMS)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

Path("artifacts").mkdir(exist_ok=True)
metrics = {
    "metric": "accuracy",
    "accuracy": round(float(accuracy), 4),
    "random_state": RANDOM_STATE,
    "model_params": MODEL_PARAMS,
}
Path("artifacts/metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Точность accuracy: {accuracy:.2f}")
print("Метрики сохранены в artifacts/metrics.json")
