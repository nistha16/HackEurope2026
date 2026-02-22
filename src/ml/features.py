"""
Global Feature Engineering Module
=================================

Transforms raw historical FX rates into scale-invariant features.
Supports universal prediction by framing it as a classification & scoring problem.
All returned features are ratios or normalized values to be corridor-agnostic.
"""

import pandas as pd
import numpy as np

# These strictly defined columns ensure the model trains and predicts on the exact same structure.
FEATURE_COLS = [
    "range_position_60d", "z_score_60d",
    "rate_vs_30d_avg", "rate_vs_60d_high", "rate_vs_60d_low",
    "volatility_14d", "volatility_60d", "vol_ratio_14_60",
    "return_1d_lag", "return_3d_lag", "return_7d_lag",
    "momentum_14d", "momentum_30d",
    "rsi_14d",
    "bollinger_position",
    "sin_dow", "cos_dow", "sin_month", "cos_month",
    "day_of_month_norm",
]

def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index — classic mean-reversion signal."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0) / 100.0  # Normalize to 0-1


def engineer_features(df: pd.DataFrame, corridor_label: str = None) -> pd.DataFrame:
    """
    Transforms a DataFrame with ['date', 'rate'] into normalized ML features.
    """
    df = df.copy()

    # 0. Preparation
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rate = df["rate"]

    # -----------------------------------------------------------------
    # 1. Scale-Invariant Returns (Lags)
    #    shift(1) ensures today's feature relies strictly on yesterday
    # -----------------------------------------------------------------
    df["log_return"] = np.log(rate / rate.shift(1))
    df["return_1d_lag"] = df["log_return"].shift(1).fillna(0)
    df["return_3d_lag"] = (rate / rate.shift(3) - 1).shift(1).fillna(0)
    df["return_7d_lag"] = (rate / rate.shift(7) - 1).shift(1).fillna(0)

    # -----------------------------------------------------------------
    # 2. Momentum (longer-horizon directional pressure)
    # -----------------------------------------------------------------
    df["momentum_14d"] = (rate / rate.shift(14) - 1).shift(1).fillna(0)
    df["momentum_30d"] = (rate / rate.shift(30) - 1).shift(1).fillna(0)

    # -----------------------------------------------------------------
    # 3. Volatility
    # -----------------------------------------------------------------
    df["volatility_14d"] = df["log_return"].rolling(window=14).std().fillna(0)
    df["volatility_60d"] = df["log_return"].rolling(window=60).std().fillna(0)
    df["vol_ratio_14_60"] = (
        df["volatility_14d"] / df["volatility_60d"].replace(0, np.nan)
    ).fillna(1.0)

    # -----------------------------------------------------------------
    # 4. Moving Averages / Ratios
    # -----------------------------------------------------------------
    rolling_30d_mean = rate.rolling(window=30).mean()
    df["rate_vs_30d_avg"] = (rate / rolling_30d_mean).fillna(1.0)

    rolling_60d_high = rate.rolling(window=60).max()
    rolling_60d_low  = rate.rolling(window=60).min()
    df["rate_vs_60d_high"] = (rate / rolling_60d_high).fillna(1.0)
    df["rate_vs_60d_low"]  = (rate / rolling_60d_low).fillna(1.0)

    # -----------------------------------------------------------------
    # 5. Range Position & Z-Score
    # -----------------------------------------------------------------
    range_diff = (rolling_60d_high - rolling_60d_low).replace(0, np.nan)
    df["range_position_60d"] = ((rate - rolling_60d_low) / range_diff).fillna(0.5)

    rolling_mean = rate.rolling(window=60).mean()
    rolling_std  = rate.rolling(window=60).std().replace(0, np.nan)
    df["z_score_60d"] = ((rate - rolling_mean) / rolling_std).fillna(0.0)

    # -----------------------------------------------------------------
    # 6. RSI & Bollinger Band Position
    # -----------------------------------------------------------------
    df["rsi_14d"] = _compute_rsi(rate, period=14)

    bb_mid = rate.rolling(window=20).mean()
    bb_std = rate.rolling(window=20).std().replace(0, np.nan)
    df["bollinger_position"] = ((rate - bb_mid) / (2 * bb_std)).fillna(0.0)
    # Clip extreme values for stability
    df["bollinger_position"] = df["bollinger_position"].clip(-1.5, 1.5)

    # -----------------------------------------------------------------
    # 7. Temporal Features (Cyclical)
    # -----------------------------------------------------------------
    dow = df["date"].dt.dayofweek
    df["sin_dow"] = np.sin(2 * np.pi * dow / 7)
    df["cos_dow"] = np.cos(2 * np.pi * dow / 7)

    month = df["date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month / 12)
    df["cos_month"] = np.cos(2 * np.pi * month / 12)

    dom = df["date"].dt.day
    df["day_of_month_norm"] = dom / 31.0  # month-end flow effects

    # -----------------------------------------------------------------
    # 8. Classification Target
    #    IMPROVED: compare today's rate against the AVERAGE of the next
    #    7 days instead of a single point.  This smooths out daily noise
    #    and creates a more learnable, stable label.
    #
    #    1 = Current rate >= avg of next 7 days → "Send now"
    #    0 = Current rate <  avg of next 7 days → "Wait"
    # -----------------------------------------------------------------
    forward_7d_avg = rate.shift(-1).rolling(window=7).mean().shift(-6)
    # shift(-1) so the window starts *tomorrow*, rolling(7) covers days +1..+7,
    # and shift(-6) re-aligns the result back to today's row.

    df["target_send_now"] = (rate >= forward_7d_avg).astype(float)

    # PREVENT LEAKAGE: Nullify target for the final 7 days
    df.loc[df.index[-7:], "target_send_now"] = np.nan

    return df