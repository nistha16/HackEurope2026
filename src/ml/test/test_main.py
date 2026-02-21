import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory (ml/) to sys.path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, MOCK_RATES, DEFAULT_RATE

# Create a TestClient instance using our FastAPI app
client = TestClient(app)


# ── Health check ─────────────────────────────────────────────────────────────

def test_health_check():
    """GET /health returns 200 and {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Response contract (matches PredictionResponse in src/types/index.ts) ─────

REQUIRED_FIELDS = {
    "from_currency",
    "to_currency",
    "predicted_rate_24h",
    "predicted_rate_72h",
    "confidence",
    "recommendation",
    "potential_savings",
    "reasoning",
    "predicted_rates",
}


def test_predict_returns_all_frontend_fields():
    """Response must include every field the Next.js route handler reads."""
    response = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    })
    assert response.status_code == 200
    data = response.json()
    missing = REQUIRED_FIELDS - data.keys()
    assert not missing, f"Missing fields that the frontend expects: {missing}"


def test_predict_field_types():
    """Verify each field has the type the frontend relies on."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()

    assert isinstance(data["predicted_rate_24h"], float)
    assert isinstance(data["predicted_rate_72h"], float)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["recommendation"], str)
    assert isinstance(data["potential_savings"], str)
    assert isinstance(data["reasoning"], str)
    assert isinstance(data["predicted_rates"], list)


def test_predict_recommendation_is_valid_enum():
    """Recommendation must be one of the three values the frontend switches on."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()
    assert data["recommendation"] in {"SEND_NOW", "WAIT", "NEUTRAL"}


def test_predicted_rates_structure():
    """predicted_rates entries must have {date, rate} for the chart component."""
    data = client.post("/predict", json={
        "from_currency": "GBP",
        "to_currency": "INR",
    }).json()

    assert len(data["predicted_rates"]) == 3
    for entry in data["predicted_rates"]:
        assert "date" in entry, "Each predicted rate needs a 'date' key"
        assert "rate" in entry, "Each predicted rate needs a 'rate' key"
        assert isinstance(entry["rate"], float)
        # ISO date format check
        assert len(entry["date"]) == 10 and entry["date"][4] == "-"


# ── Determinism ──────────────────────────────────────────────────────────────

def test_predict_is_deterministic():
    """Calling the endpoint twice with the same input returns identical output."""
    payload = {"from_currency": "EUR", "to_currency": "USD"}
    first = client.post("/predict", json=payload).json()
    second = client.post("/predict", json=payload).json()
    assert first == second, "Mock predictions must be deterministic for frontend debugging"


def test_known_corridor_rate():
    """EUR/USD mock should use the known rate from MOCK_RATES, not a random value."""
    data = client.post("/predict", json={
        "from_currency": "EUR",
        "to_currency": "USD",
    }).json()

    expected_base = MOCK_RATES["EUR/USD"]  # 1.0850
    expected_24h = round(expected_base * 1.001, 4)
    assert data["predicted_rate_24h"] == expected_24h


def test_unknown_corridor_uses_default_rate():
    """Corridors not in MOCK_RATES should fall back to DEFAULT_RATE."""
    data = client.post("/predict", json={
        "from_currency": "CHF",
        "to_currency": "NZD",
    }).json()

    expected_24h = round(DEFAULT_RATE * 1.001, 4)
    assert data["predicted_rate_24h"] == expected_24h


# ── Input normalisation ──────────────────────────────────────────────────────

def test_predict_normalises_to_uppercase():
    """Currency codes should be uppercased in the response."""
    data = client.post("/predict", json={
        "from_currency": "eur",
        "to_currency": "usd",
    }).json()
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "USD"


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