import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory (ml/) to sys.path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Create a TestClient instance using our FastAPI app
client = TestClient(app)


def test_health_check():
    """GET /health returns 200 and {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_rate_success():
    """POST /predict with valid payload returns 200 and correct schema."""
    payload = {
        "from_currency": "EUR",
        "to_currency": "MAD"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "MAD"
    assert "predicted_rate" in data
    assert isinstance(data["predicted_rate"], float)
    assert data["status"] == "success"


def test_predict_rate_lowercase_input():
    """POST /predict normalises currency codes to uppercase."""
    payload = {"from_currency": "eur", "to_currency": "usd"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "USD"


def test_predict_rate_invalid_payload():
    """POST /predict with missing fields returns 422."""
    payload = {"from_currency": "EUR"}  # Missing 'to_currency'
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rate_empty_body():
    """POST /predict with empty body returns 422."""
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_cors_headers():
    """CORS headers are set for allowed origin."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


if __name__ == "__main__":
    pytest.main(["-v", __file__])