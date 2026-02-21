import os
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
from predictor import predict_rate_movement

# Initialize the FastAPI app
app = FastAPI(
    title="FX Rate Prediction Service",
    description="ML Microservice for predicting foreign exchange rates",
    version="1.0.0",
)

# Configure CORS
# Read allowed origins from an environment variable (comma-separated) for production (e.g., Vercel),
# fallback to localhost defaults for local development (Sprints 1-3).
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")

if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    from_currency: str
    to_currency: str


class PredictedRate(BaseModel):
    date: str
    rate: float


class PredictionMLResponse(BaseModel):
    """
    Fields the Next.js frontend expects from the ML service.

    See src/app/api/predict/route.ts — the route handler reads these keys
    from the ML JSON and merges them into the PredictionResponse sent to the
    browser.  current_rate and historical_rates come from Frankfurter, so the
    ML service does NOT need to return them.
    """

    from_currency: str
    to_currency: str
    predicted_rate_24h: float
    predicted_rate_72h: float
    confidence: float
    recommendation: str  # "SEND_NOW" | "WAIT" | "NEUTRAL"
    potential_savings: str
    reasoning: str
    predicted_rates: list[PredictedRate]


# ---------------------------------------------------------------------------
# Deterministic mock rates (used until the real model is trained)
# ---------------------------------------------------------------------------

# Representative mid-market rates for corridors the app supports.
# Using fixed values so the endpoint is fully deterministic and easy to
# assert against during frontend integration testing.
MOCK_RATES: dict[str, float] = {
    "EUR/USD": 1.0850,
    "EUR/GBP": 0.8560,
    "EUR/MAD": 10.8500,
    "EUR/NGN": 1750.00,
    "EUR/BDT": 128.50,
    "EUR/EGP": 52.75,
    "EUR/KES": 165.00,
    "EUR/JPY": 162.50,
    "EUR/INR": 90.50,
    "EUR/TRY": 35.20,
    "EUR/BRL": 5.95,
    "EUR/MXN": 18.70,
    "EUR/ZAR": 19.85,
    "EUR/CNY": 7.85,
    "GBP/INR": 105.80,
    "GBP/PKR": 380.00,
    "GBP/GHS": 17.50,
    "GBP/USD": 1.2670,
    "GBP/JPY": 189.80,
    "GBP/ZAR": 23.15,
    "USD/PHP": 56.20,
    "USD/MXN": 17.25,
    "USD/BRL": 5.48,
    "USD/JPY": 149.80,
    "USD/INR": 83.40,
    "USD/TRY": 32.45,
    "USD/THB": 35.60,
    "USD/IDR": 15750.00,
    "USD/ZAR": 18.30,
    "USD/KRW": 1345.00,
}

DEFAULT_RATE = 1.0000


def _mock_rate_for(from_ccy: str, to_ccy: str) -> float:
    """Return a deterministic mock rate for a corridor."""
    key = f"{from_ccy}/{to_ccy}"
    return MOCK_RATES.get(key, DEFAULT_RATE)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionMLResponse)
async def predict_rate(request: PredictionRequest):
    """
    Predict the FX rate for a given currency pair.

    Attempts to use the trained ML model first. If models or data 
    are missing, it safely falls back to deterministic placeholder 
    values to keep the Next.js frontend functional.
    """
    from_ccy = request.from_currency.upper()
    to_ccy = request.to_currency.upper()
    
    # 1. Try ML Prediction First
    pair_filename = f"{from_ccy}_{to_ccy}"
    data_path = os.path.join(os.path.dirname(__file__), "data", f"{pair_filename}.csv")
    
    try:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"No historical data CSV found at {data_path}")
        
        df = pd.read_csv(data_path)
        
        # Call the ML predictor logic
        ml_result = predict_rate_movement(from_ccy, to_ccy, df)

        pred_24h = ml_result["predicted_rate_24h"]
        pred_72h = ml_result["predicted_rate_72h"]
        
        # Interpolate a 3-day chart array for the frontend
        today = date.today()
        pred_48h = round((pred_24h + pred_72h) / 2, 4) 
        
        predicted_rates = [
            PredictedRate(date=(today + timedelta(days=1)).isoformat(), rate=pred_24h),
            PredictedRate(date=(today + timedelta(days=2)).isoformat(), rate=pred_48h),
            PredictedRate(date=(today + timedelta(days=3)).isoformat(), rate=pred_72h),
        ]

        return PredictionMLResponse(
            from_currency=from_ccy,
            to_currency=to_ccy,
            predicted_rate_24h=pred_24h,
            predicted_rate_72h=pred_72h,
            confidence=ml_result["confidence_score"],
            recommendation=ml_result["recommendation"],
            potential_savings=f"0.00 {to_ccy}",
            reasoning=ml_result["reasoning"],
            predicted_rates=predicted_rates,
        )

    except Exception as e:
        print(f"ML Prediction fallback triggered for {pair_filename}: {e}")
        
        # 2. Fallback to Mock Data
        base_rate = _mock_rate_for(from_ccy, to_ccy)

        # Simulate a slight upward trend for the 24h / 72h predictions
        predicted_24h = round(base_rate * 1.001, 4)
        predicted_72h = round(base_rate * 1.003, 4)

        # Build 3-day predicted_rates array (what the frontend charts)
        today = date.today()
        predicted_rates = [
            PredictedRate(
                date=(today + timedelta(days=d)).isoformat(),
                rate=round(base_rate * (1 + 0.001 * d), 4),
            )
            for d in range(1, 4)
        ]

        return PredictionMLResponse(
            from_currency=from_ccy,
            to_currency=to_ccy,
            predicted_rate_24h=predicted_24h,
            predicted_rate_72h=predicted_72h,
            confidence=0.75,
            recommendation="NEUTRAL",
            potential_savings=f"0.00 {to_ccy}",
            reasoning=(
                f"Fallback prediction for {from_ccy}/{to_ccy}. "
                "The ML model is not yet trained or data is missing — this mock "
                "returns a fixed rate with a slight upward trend."
            ),
            predicted_rates=predicted_rates,
        )