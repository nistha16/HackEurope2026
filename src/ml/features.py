"""
Global Feature Engineering Module
=================================

Transforms raw historical FX rates into scale-invariant features.
Binary classification target: is today's rate >= the average of the next 14 days?

Key design choices:
  - Features are ratios/normalised → corridor-agnostic
  - Trimmed correlated features (e.g. only one of z_score / bollinger kept)
  - Sample weights emphasise extreme days where signal is strongest
"""

import pandas as pd
import numpy as np

FEATURE_COLS = [
    "range_position_60d",
    "rate_vs_10d_avg", "rate_vs_30d_avg",
    "rate_vs_60d_high", "rate_vs_60d_low",
    "volatility_14d", "vol_ratio_14_60",
    "return_1d_lag", "return_3d_lag", "return_7d_lag",
    "momentum_14d", "momentum_30d",
    "rsi_14d",
    "macd_signal",
    "sin_dow", "cos_dow", "sin_month", "cos_month",
    "day_of_month_norm",
]

FORWARD_WINDOW = 14


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0) / 100.0


def _compute_macd_signal(rate: pd.Series) -> pd.Series:
    ema_12 = rate.ewm(span=12, adjust=False).mean()
    ema_26 = rate.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return (histogram / rate).fillna(0.0).clip(-0.05, 0.05)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rate = df["rate"]

    # --- Returns (lagged by 1 day to prevent leakage) ---
    log_ret = np.log(rate / rate.shift(1))
    df["return_1d_lag"] = log_ret.shift(1).fillna(0)
    df["return_3d_lag"] = (rate / rate.shift(3) - 1).shift(1).fillna(0)
    df["return_7d_lag"] = (rate / rate.shift(7) - 1).shift(1).fillna(0)

    # --- Momentum ---
    df["momentum_14d"] = (rate / rate.shift(14) - 1).shift(1).fillna(0)
    df["momentum_30d"] = (rate / rate.shift(30) - 1).shift(1).fillna(0)

    # --- Volatility ---
    df["volatility_14d"] = log_ret.rolling(window=14).std().fillna(0)
    vol_60d = log_ret.rolling(window=60).std()
    df["vol_ratio_14_60"] = (
        df["volatility_14d"] / vol_60d.replace(0, np.nan)
    ).fillna(1.0)

    # --- MA ratios ---
    df["rate_vs_10d_avg"] = (rate / rate.rolling(10).mean()).fillna(1.0)
    df["rate_vs_30d_avg"] = (rate / rate.rolling(30).mean()).fillna(1.0)

    rolling_60d_high = rate.rolling(window=60).max()
    rolling_60d_low  = rate.rolling(window=60).min()
    df["rate_vs_60d_high"] = (rate / rolling_60d_high).fillna(1.0)
    df["rate_vs_60d_low"]  = (rate / rolling_60d_low).fillna(1.0)

    # --- Range position ---
    range_diff = (rolling_60d_high - rolling_60d_low).replace(0, np.nan)
    df["range_position_60d"] = ((rate - rolling_60d_low) / range_diff).fillna(0.5)

    # --- RSI & MACD ---
    df["rsi_14d"] = _compute_rsi(rate, period=14)
    df["macd_signal"] = _compute_macd_signal(rate)

    # --- Temporal ---
    dow = df["date"].dt.dayofweek
    df["sin_dow"] = np.sin(2 * np.pi * dow / 7)
    df["cos_dow"] = np.cos(2 * np.pi * dow / 7)
    month = df["date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month / 12)
    df["cos_month"] = np.cos(2 * np.pi * month / 12)
    df["day_of_month_norm"] = df["date"].dt.day / 31.0

    # --- Target: rate >= mean of next 14 days ---
    forward_avg = rate.shift(-1).rolling(window=FORWARD_WINDOW).mean().shift(-(FORWARD_WINDOW - 1))
    df["target_send_now"] = (rate >= forward_avg).astype(float)
    df.loc[df.index[-FORWARD_WINDOW:], "target_send_now"] = np.nan

    # --- Sample weight: upweight extremes where signal is strongest ---
    pctile = df["range_position_60d"]
    extremeness = (pctile - 0.5).abs()
    df["sample_weight"] = 1.0 + 4.0 * extremeness

    return df