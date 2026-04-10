from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_get():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ts" in data

def test_health_head():
    response = client.head("/api/health")
    assert response.status_code == 200
    assert response.text == ""
