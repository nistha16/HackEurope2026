import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from predictor import score_today

app = FastAPI(
    title="Global FX Rate Prediction Service",
    description="Single Global ML Microservice for predicting foreign exchange rate timing",
    version="1.0.0",
)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic Schemas complying exactly with the Assignment
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    from_currency: str
    to_currency: str

class MarketInsights(BaseModel):
    two_month_high: float
    two_month_low: float
    two_month_avg: float
    one_year_trend: str
    volatility: str

class PredictionMLResponse(BaseModel):
    timing_score: float
    recommendation: str
    reasoning: str
    market_insights: MarketInsights

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/predict", response_model=PredictionMLResponse)
def predict_rate_movement_endpoint(request: PredictionRequest):
    from_ccy = request.from_currency.upper()
    to_ccy = request.to_currency.upper()

    data_path = os.path.join(os.path.dirname(__file__), "data", "historical_rates.csv")

    try:
        if not os.path.exists(data_path):
            raise FileNotFoundError("Missing historical data.")

        df = pd.read_csv(data_path)
        corridor_df = df[(df["from_currency"] == from_ccy) & (df["to_currency"] == to_ccy)]

        if len(corridor_df) < 60:
            raise ValueError("Not enough historical data for this corridor.")

        ml_result = score_today(from_ccy, to_ccy, corridor_df)

        return PredictionMLResponse(
            timing_score=ml_result["timing_score"],
            recommendation=ml_result["recommendation"],
            reasoning=ml_result["reasoning"],
            market_insights=MarketInsights(**ml_result["market_insights"])
        )

    except Exception as e:
        print(f"Prediction failed for {from_ccy}_{to_ccy}: {e}")

        return PredictionMLResponse(
            timing_score=0.50,
            recommendation="NEUTRAL",
            reasoning=f"System fallback engaged. ({str(e)})",
            market_insights=MarketInsights(
                two_month_high=0.0, two_month_low=0.0, two_month_avg=0.0,
                one_year_trend="UNKNOWN", volatility="UNKNOWN"
            )
        )