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
# Health check — required by Railway for deployment readiness
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Pydantic Schemas
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
# Prediction endpoint
# ---------------------------------------------------------------------------
@app.post("/predict", response_model=PredictionMLResponse)
def predict_rate_movement_endpoint(request: PredictionRequest):
    from_ccy = request.from_currency.upper()
    to_ccy = request.to_currency.upper()

    try:
        ml_result = score_today(from_ccy, to_ccy)

        return PredictionMLResponse(
            timing_score=ml_result["timing_score"],
            recommendation=ml_result["recommendation"],
            reasoning=ml_result["reasoning"],
            market_insights=MarketInsights(**ml_result["market_insights"]),
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Prediction failed for {from_ccy}/{to_ccy}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")