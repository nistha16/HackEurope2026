import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from train import EnsembleModel 
from predictor import score_today

# ---------------------------------------------------------------------------
# Pre-computed cache for demo corridors
# ---------------------------------------------------------------------------
PRECOMPUTED_CACHE = {}
DEMO_CORRIDORS = [
    ("EUR", "MAD"),  # Primary demo
    ("EUR", "USD"),
    ("GBP", "INR"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-compute timing scores for demo corridors on startup."""
    print("Pre-computing timing scores for demo corridors...")
    for src, tgt in DEMO_CORRIDORS:
        try:
            result = score_today(src, tgt)
            PRECOMPUTED_CACHE[f"{src}_{tgt}"] = result
            print(f"Cached {src}->{tgt}: Score={result['timing_score']} Action={result['recommendation']}")
        except Exception as e:
            print(f"Failed to precompute {src}->{tgt} (data might be missing): {e}")
    yield


app = FastAPI(
    title="Global FX Rate Prediction Service",
    description="Single Global ML Microservice for predicting foreign exchange rate timing",
    version="1.0.0",
    lifespan=lifespan,
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
    cache_key = f"{from_ccy}_{to_ccy}"

    try:
        # Check cache first for instant demo response
        if cache_key in PRECOMPUTED_CACHE:
            ml_result = PRECOMPUTED_CACHE[cache_key]
            print(f"Cache hit for {cache_key}")
        else:
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