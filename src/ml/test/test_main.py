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
    """
    Test the GET /health endpoint.
    Verifies it returns a 200 status code and the correct JSON response.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_predict_rate_success():
    """
    Test the POST /predict endpoint with a valid payload.
    Verifies it returns a 200 status code and the correct response schema.
    """
    payload = {
        "from_currency": "EUR",
        "to_currency": "MAD"
    }
    
    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check if the returned data matches the expected schema
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "MAD"
    assert "predicted_rate" in data
    assert isinstance(data["predicted_rate"], float)
    assert data["status"] == "success"

def test_predict_rate_invalid_payload():
    """
    Test the POST /predict endpoint with an invalid payload.
    Verifies it returns a 422 Unprocessable Entity error (Pydantic validation).
    """
    payload = {
        "from_currency": "EUR"
        # Missing 'to_currency'
    }
    
    response = client.post("/predict", json=payload)
    
    # FastAPI automatically handles validation errors with a 422 status
    assert response.status_code == 422

if __name__ == "__main__":
    # Run pytest on this file if executed directly
    pytest.main(["-v", __file__])