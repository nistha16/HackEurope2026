import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory (ml/) to sys.path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

# Create a TestClient instance using our FastAPI app
client = TestClient(app)

# ── Health check ─────────────────────────────────────────────────────────────

def test_health_check():
    """GET /health returns 200 and {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# ── Response contract (Matches new PredictionMLResponse in main.py) ──────────

REQUIRED_FIELDS = {
    "timing_score",
    "recommendation",
    "reasoning",
    "market_insights"
}

def test_predict_returns_all_ml_fields():
    """Response must include every field defined in PredictionMLResponse."""
    response = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    })
    assert response.status_code == 200
    data = response.json()
    missing = REQUIRED_FIELDS - data.keys()
    assert not missing, f"Missing fields expected by the ML response: {missing}"

def test_predict_field_types():
    """Verify each field has the correct type."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()

    assert isinstance(data["timing_score"], float)
    assert isinstance(data["recommendation"], str)
    assert isinstance(data["reasoning"], str)
    assert isinstance(data["market_insights"], dict)

def test_recommendation_is_valid_enum():
    """Recommendation must be one of the three threshold-based values."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()
    assert data["recommendation"] in {"SEND_NOW", "WAIT", "NEUTRAL"}

def test_timing_score_in_range():
    """Timing score must be between 0 and 1."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()
    assert 0.0 <= data["timing_score"] <= 1.0

def test_market_insights_structure():
    """Verify the nested MarketInsights schema."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()

    mi = data["market_insights"]
    assert "two_month_high" in mi
    assert isinstance(mi["two_month_high"], float)
    assert isinstance(mi["two_month_low"], float)
    assert isinstance(mi["two_month_avg"], float)
    assert isinstance(mi["one_year_trend"], str)
    assert isinstance(mi["volatility"], str)

# ── Validation ───────────────────────────────────────────────────────────────

def test_predict_missing_field_returns_422():
    """POST /predict with missing fields returns 422."""
    response = client.post("/predict", json={"from_currency": "EUR"})
    assert response.status_code == 422

def test_predict_empty_body_returns_422():
    """POST /predict with empty body returns 422."""
    response = client.post("/predict", json={})
    assert response.status_code == 422

# ── CORS ─────────────────────────────────────────────────────────────────────

def test_cors_headers():
    """CORS headers are set for the allowed origin."""
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