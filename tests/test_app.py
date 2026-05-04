from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"].startswith("v")


def test_predict_short_input_is_accepted():
    response = client.post("/predict", json={"x": [1, 2, 3]})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "prediction" in body
    assert len(body["features_used"]) == 4
