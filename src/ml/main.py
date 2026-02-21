from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

# Initialize the FastAPI app
app = FastAPI(
    title="FX Rate Prediction Service",
    description="ML Microservice for predicting foreign exchange rates",
    version="1.0.0"
)

# Configure CORS for localhost:3000
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

# Define the request model for the /predict endpoint
class PredictionRequest(BaseModel):
    from_currency: str
    to_currency: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok"}

@app.post("/predict")
async def predict_rate(request: PredictionRequest):
    """
    Predicts the FX rate for a given currency pair.
    Currently returns a placeholder prediction.
    """
    # TODO: Load actual ML model and generate real prediction
    # For now, we return a placeholder mock prediction to meet acceptance criteria
    
    mock_rate = round(random.uniform(0.5, 15.0), 4) # Generates a random realistic-looking rate
    
    return {
        "from_currency": request.from_currency.upper(),
        "to_currency": request.to_currency.upper(),
        "predicted_rate": mock_rate,
        "status": "success"
    }

# To run the app, use the command:
# uvicorn ml.main:app --reload (if running from root directory)
# OR
# uvicorn main:app --reload (if running from inside the ml/ directory)