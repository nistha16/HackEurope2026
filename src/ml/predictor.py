"""
Global Predictor Module
=======================
Executes inference using the ensemble model (LogReg + XGBoost).
Blends model probability with the raw 60-day percentile.

Architecture:
  - Raw percentile answers "where is today's rate vs recent history?"
  - Model adds "are backward indicators aligned that this is a good day?"
  - Signal agreement drives confidence in the recommendation.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from features import engineer_features, FEATURE_COLS
from train import EnsembleModel

# Register EnsembleModel so joblib can unpickle it regardless of entry point
# (the model was pickled under __main__ via `python3 train.py`)
for _mod in ("__main__", "__mp_main__"):
    if _mod in sys.modules:
        setattr(sys.modules[_mod], "EnsembleModel", EnsembleModel)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

MODEL_WEIGHT = 0.40


class GlobalPredictor:
    def __init__(self):
        self.model = self._load_model("global_timing_model.joblib")
        self._data = self._load_data()

    def _load_model(self, filename):
        path = os.path.join(MODEL_DIR, filename)
        return joblib.load(path) if os.path.exists(path) else None

    def _load_data(self):
        path = os.path.join(DATA_DIR, "historical_rates.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"[GlobalPredictor] Loaded {len(df)} rows from historical_rates.csv")
            return df
        print("[GlobalPredictor] WARNING: historical_rates.csv not found")
        return pd.DataFrame()

    def get_corridor_data(self, from_ccy: str, to_ccy: str) -> pd.DataFrame:
        if self._data.empty:
            return pd.DataFrame()
        return self._data[
            (self._data["from_currency"] == from_ccy) &
            (self._data["to_currency"] == to_ccy)
        ]

    def predict(self, from_curr: str, to_curr: str, history_df: pd.DataFrame) -> dict:
        if self.model is None:
            raise RuntimeError("Model file not found. Run train.py.")
        if len(history_df) < 60:
            raise ValueError("Insufficient history (need >= 60 days).")

        # 1. Feature Engineering
        eng_df = engineer_features(history_df)
        latest = eng_df.iloc[-1]

        # 2. Model probability
        X = eng_df.iloc[-1:][FEATURE_COLS]
        model_prob = float(self.model.predict_proba(X)[0][1])

        # 3. Raw percentile
        raw_percentile = float(latest["range_position_60d"])

        # 4. Blended timing score
        timing_score = MODEL_WEIGHT * model_prob + (1 - MODEL_WEIGHT) * raw_percentile
        timing_score = float(np.clip(timing_score, 0.0, 1.0))

        # 5. Signal agreement (for reasoning)
        agreement = float(latest["signal_agreement"])

        # 6. Decision Logic — Task 2: tuned thresholds & Task 5: Natural reasoning
        if timing_score > 0.8:
            rec = "SEND_NOW"
            if agreement >= 0.7:
                reason = (
                    f"The {from_curr} to {to_curr} rate is exceptionally favorable right now compared to recent trends. "
                    f"Locking in your transfer is highly recommended ({int(agreement * 6)}/6 indicators confirm strong momentum)."
                )
            else:
                reason = (
                    f"The current {from_curr} to {to_curr} exchange rate is very strong. "
                    f"It's a great time to send money."
                )
        elif timing_score >= 0.5:
            rec = "NEUTRAL"
            if timing_score > 0.65:
                reason = (
                    f"The {from_curr} to {to_curr} rate is solid. You can send now, "
                    f"but waiting might yield slight improvements depending on market movement."
                )
            else:
                reason = (
                    f"The {from_curr} to {to_curr} rate is relatively average right now. "
                    f"No strong urgency to send immediately unless necessary."
                )
        else:
            rec = "WAIT"
            if timing_score > 0.3:
                reason = (
                    f"The {from_curr} to {to_curr} rate is dipping below recent averages. "
                    f"Consider holding off for a few days if your transfer isn't urgent."
                )
            else:
                reason = (
                    f"The {from_curr} to {to_curr} rate is currently unfavorable. "
                    f"We strongly suggest waiting for the market to recover before initiating your transfer."
                )

        # 7. Market Insights
        last_60 = history_df.tail(60)["rate"]
        two_month_avg = float(last_60.mean())

        last_avail = history_df.tail(365)["rate"] if len(history_df) >= 365 else last_60
        trend_direction = "UP" if latest["rate"] > last_avail.mean() else "DOWN"

        vol_ratio = last_60.std() / max(two_month_avg, 1e-9)
        if vol_ratio > 0.015:
            vol_label = "HIGH"
        elif vol_ratio > 0.008:
            vol_label = "MEDIUM"
        else:
            vol_label = "LOW"

        return {
            "timing_score": round(timing_score, 2),
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

_predictor = GlobalPredictor()

def score_today(from_currency: str, to_currency: str) -> dict:
    corridor_df = _predictor.get_corridor_data(from_currency, to_currency)
    if corridor_df.empty:
        raise FileNotFoundError(f"No historical data for {from_currency}/{to_currency}.")
    if len(corridor_df) < 60:
        raise ValueError(f"Not enough history for {from_currency}/{to_currency} (have {len(corridor_df)}, need 60).")
    return _predictor.predict(from_currency, to_currency, corridor_df)