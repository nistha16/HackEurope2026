"""
Global Predictor Module
=======================
Executes inference using the single global model.
Blends model probability with the raw percentile for a robust timing score.
"""

import os
import joblib
import numpy as np
import pandas as pd
from features import engineer_features, FEATURE_COLS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

# Blending weight: how much the ML model influences the final score
# vs. the deterministic percentile.  0.6 means 60 % model, 40 % percentile.
MODEL_WEIGHT = 0.6


class GlobalPredictor:
    def __init__(self):
        self.model = self._load_model("global_timing_model.joblib")

    def _load_model(self, filename):
        path = os.path.join(MODEL_DIR, filename)
        return joblib.load(path) if os.path.exists(path) else None

    def predict(self, from_curr: str, to_curr: str, history_df: pd.DataFrame) -> dict:
        if self.model is None:
            return self._mock_response("Model file not found. Run train.py.")
        if len(history_df) < 60:
            return self._mock_response("Insufficient history (need >= 60 days).")

        # 1. Feature Engineering
        eng_df = engineer_features(history_df)
        latest_row = eng_df.iloc[-1]

        # 2. Model probability that sending now is the better choice
        X = eng_df.iloc[-1:][FEATURE_COLS]
        model_prob = float(self.model.predict_proba(X)[0][1])

        # 3. Raw percentile — deterministic, always meaningful
        raw_percentile = float(latest_row["range_position_60d"])

        # 4. Blended timing score
        timing_score = MODEL_WEIGHT * model_prob + (1 - MODEL_WEIGHT) * raw_percentile
        timing_score = np.clip(timing_score, 0.0, 1.0)

        # 5. Decision Logic
        if timing_score >= 0.70:
            rec = "SEND_NOW"
            reason = (
                f"Great timing — today's rate is in the top {int((1 - timing_score) * 100 + 1)}% "
                f"of recent history and the model expects it to weaken."
            )
        elif timing_score >= 0.45:
            rec = "NEUTRAL"
            reason = "Decent day. The rate is near its recent average — no strong signal either way."
        else:
            rec = "WAIT"
            reason = (
                "Below-average rate compared to recent weeks. "
                "Historical patterns suggest a better window may come soon."
            )

        # 6. Market Insights
        last_60 = history_df.tail(60)["rate"]
        two_month_avg = float(last_60.mean())

        last_365 = history_df.tail(365)["rate"] if len(history_df) >= 365 else last_60
        trend_direction = "UP" if latest_row["rate"] > last_365.mean() else "DOWN"

        vol_ratio = last_60.std() / max(two_month_avg, 1e-9)
        vol_label = "HIGH" if vol_ratio > 0.015 else "LOW"

        return {
            "timing_score": round(float(timing_score), 2),
            "recommendation": rec,
            "reasoning": reason,
            "market_insights": {
                "two_month_high": round(float(last_60.max()), 4),
                "two_month_low":  round(float(last_60.min()), 4),
                "two_month_avg":  round(two_month_avg, 4),
                "one_year_trend": trend_direction,
                "volatility": vol_label,
            },
        }

    def _mock_response(self, error_msg):
        return {
            "timing_score": 0.5,
            "recommendation": "NEUTRAL",
            "reasoning": error_msg,
            "market_insights": {
                "two_month_high": 0.0,
                "two_month_low": 0.0,
                "two_month_avg": 0.0,
                "one_year_trend": "FLAT",
                "volatility": "UNKNOWN",
            },
        }


_predictor = GlobalPredictor()


def score_today(from_currency: str, to_currency: str, history_df: pd.DataFrame) -> dict:
    """Wrapper to safely call the global predictor singleton."""
    return _predictor.predict(from_currency, to_currency, history_df)