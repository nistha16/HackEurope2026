"""
Global Predictor Module
=======================

Uses a single XGBoost model trained on 40+ pairs to predict any corridor.
Handles scale-invariant inference.
"""

import os
import joblib
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from features import generate_features, FEATURE_COLS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

class GlobalPredictor:
    def __init__(self):
        self.model_24h = self._load_model("global_fx_24h.joblib")
        self.model_72h = self._load_model("global_fx_72h.joblib")
        
    def _load_model(self, filename):
        path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(path):
            return joblib.load(path)
        return None

    def predict(self, from_curr: str, to_curr: str, history_df: pd.DataFrame) -> dict:
        """
        history_df: DataFrame with ['date', 'rate']
        """
        if self.model_24h is None:
            return self._mock_response("Model files not found. Please run training.")

        if len(history_df) < 60:
            return self._mock_response("Insufficient history (min 60 days required).")

        # 1. Feature Engineering
        eng = generate_features(history_df)
        latest = eng.iloc[-1:]
        current_rate = float(latest["rate"].values[0])
        
        # 2. Prediction (returns)
        X = latest[FEATURE_COLS]
        pred_ret_24h = float(self.model_24h.predict(X)[0])
        pred_ret_72h = float(self.model_72h.predict(X)[0])
        
        # 3. Convert back to rates
        rate_24h = current_rate * (1 + pred_ret_24h)
        rate_72h = current_rate * (1 + pred_ret_72h)
        
        # 4. Calibration & Confidence
        # Higher volatility usually lowers confidence in the point estimate
        recent_vol = latest["volatility_14d"].values[0]
        confidence = 0.65 - (recent_vol * 10) # Simple heuristic
        confidence = max(0.1, min(0.9, round(float(confidence), 2)))
        
        # 5. Recommendation Logic
        threshold = 0.0025 # 0.25% move
        if pred_ret_24h > threshold:
            rec = "WAIT"
            reason = f"Model predicts {pred_ret_24h:.2%} improvement in 24h based on global momentum patterns."
        elif pred_ret_24h < -threshold:
            rec = "SEND_NOW"
            reason = f"Potential {abs(pred_ret_24h):.2%} drop predicted. Locking in current rate is recommended."
        else:
            rec = "NEUTRAL"
            reason = "Expected rate volatility is within normal bounds. No strong signal."

        return {
            "predicted_rate_24h": round(rate_24h, 5),
            "predicted_rate_72h": round(rate_72h, 5),
            "confidence_score": confidence,
            "recommendation": rec,
            "reasoning": reason
        }

    def _mock_response(self, error_msg):
        return {
            "predicted_rate_24h": 0.0,
            "predicted_rate_72h": 0.0,
            "confidence_score": 0.0,
            "recommendation": "NEUTRAL",
            "reasoning": error_msg
        }