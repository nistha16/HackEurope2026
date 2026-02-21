"""
Global Predictor Module
=======================
"""

import os
import joblib
import pandas as pd
import numpy as np
from features import generate_features, FEATURE_COLS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

class GlobalPredictor:
    def __init__(self):
        self.model_24h = self._load_model("global_fx_24h.joblib")
        self.model_72h = self._load_model("global_fx_72h.joblib")
        
    def _load_model(self, filename):
        path = os.path.join(MODEL_DIR, filename)
        return joblib.load(path) if os.path.exists(path) else None

    def predict(self, from_curr: str, to_curr: str, history_df: pd.DataFrame) -> dict:
        if self.model_24h is None:
            return self._mock_response("Model files not found.")
        if len(history_df) < 60:
            return self._mock_response("Insufficient history.")

        eng = generate_features(history_df)
        latest = eng.iloc[-1:]
        current_rate = float(latest["rate"].values[0])
        
        X = latest[FEATURE_COLS]
        pred_ret_24h = float(self.model_24h.predict(X)[0])
        pred_ret_72h = float(self.model_72h.predict(X)[0])
        
        rate_24h = current_rate * (1 + pred_ret_24h)
        rate_72h = current_rate * (1 + pred_ret_72h)
        
        # Calibration
        recent_vol = latest["volatility_14d"].values[0]
        confidence = 0.70 - (recent_vol * 15) # Adjusted heuristic
        confidence = max(0.1, min(0.95, round(float(confidence), 2)))
        
        # 5. Conservative Recommendation Logic
        threshold = 0.005 # Increased to 0.5% move for higher conviction
        if pred_ret_24h > threshold:
            rec = "WAIT"
            reason = f"Strong momentum detected. Predicted {pred_ret_24h:.2%} improvement."
        elif pred_ret_24h < -threshold:
            rec = "SEND_NOW"
            reason = f"Downward trend predicted. Locking in current rate is safer."
        else:
            rec = "NEUTRAL"
            reason = "Market volatility is within expected levels. No strong signal."

        return {
            "predicted_rate_24h": round(rate_24h, 5),
            "predicted_rate_72h": round(rate_72h, 5),
            "confidence_score": confidence,
            "recommendation": rec,
            "reasoning": reason
        }

    def _mock_response(self, error_msg):
        return {"predicted_rate_24h": 0.0, "predicted_rate_72h": 0.0, 
                "confidence_score": 0.0, "recommendation": "NEUTRAL", "reasoning": error_msg}

_predictor = GlobalPredictor()

def predict_rate_movement(from_curr, to_curr, history_df):
    return _predictor.predict(from_curr, to_curr, history_df)