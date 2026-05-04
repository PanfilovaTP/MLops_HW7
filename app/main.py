import os
from typing import List

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))

app = FastAPI(title="HW7 ML Service", version=MODEL_VERSION)

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data,
    iris.target,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=iris.target,
)

model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
model.fit(X_train, y_train)


class PredictRequest(BaseModel):
    x: List[float] = Field(..., description="Input features. If fewer than 4 values are passed, zeros are appended.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": MODEL_VERSION}


@app.post("/predict")
def predict(payload: PredictRequest) -> dict:
    features = list(payload.x[:4])
    if len(features) < 4:
        features.extend([0.0] * (4 - len(features)))

    arr = np.array(features, dtype=float).reshape(1, -1)
    prediction = int(model.predict(arr)[0])
    probabilities = model.predict_proba(arr)[0].round(4).tolist()

    return {
        "status": "ok",
        "version": MODEL_VERSION,
        "prediction": prediction,
        "class_name": iris.target_names[prediction].item(),
        "probabilities": probabilities,
        "features_used": features,
    }
