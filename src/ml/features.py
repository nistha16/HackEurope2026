"""
Global Feature Engineering Module
=================================

Philosophy: The model is a learned BACKWARD-LOOKING analyst, not a future
predictor.  It synthesises range position, momentum, volatility, RSI, MA
crossovers, and seasonality into a timing score.

The forward target is used only for TRAINING — it teaches the model which
backward signal combinations historically coincided with genuinely good days.
The product value is proved by backtesting, not by forward AUC.

Target: "Is today in the top 3 out of the next 10 trading days?"
  - ~30% positive rate (cleaner than 50/50 above-mean)
  - Positive class = days that were CLEARLY good timing
  - Much more learnable than "slightly above the forward mean"
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
    "signal_agreement",
    "sin_dow", "cos_dow", "sin_month", "cos_month",
    "day_of_month_norm",
]

FORWARD_WINDOW = 10
TOP_K = 3  # "top 3 out of 10" = ~30% positive rate


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

    # --- Returns (lagged) ---
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

    # -----------------------------------------------------------------
    # SIGNAL AGREEMENT: how many backward indicators say "good rate"?
    # This is the key feature — it captures your intuition of
    # "confidence comes from multiple signals lining up."
    #
    # Each sub-signal votes 1 (good) or 0 (bad), then we average.
    # -----------------------------------------------------------------
    votes = pd.DataFrame(index=df.index)
    votes["range_high"]     = (df["range_position_60d"] > 0.5).astype(float)
    votes["above_10d_ma"]   = (df["rate_vs_10d_avg"] > 1.0).astype(float)
    votes["above_30d_ma"]   = (df["rate_vs_30d_avg"] > 1.0).astype(float)
    votes["rsi_bullish"]    = (df["rsi_14d"] > 0.5).astype(float)
    votes["macd_positive"]  = (df["macd_signal"] > 0).astype(float)
    votes["momentum_up"]    = (df["momentum_14d"] > 0).astype(float)

    df["signal_agreement"] = votes.mean(axis=1)  # 0..1, 1 = all agree "good"

    # --- Temporal ---
    dow = df["date"].dt.dayofweek
    df["sin_dow"] = np.sin(2 * np.pi * dow / 7)
    df["cos_dow"] = np.cos(2 * np.pi * dow / 7)
    month = df["date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month / 12)
    df["cos_month"] = np.cos(2 * np.pi * month / 12)
    df["day_of_month_norm"] = df["date"].dt.day / 31.0

    # -----------------------------------------------------------------
    # TARGET: Is today in the top K of the next N trading days?
    #
    # For each day, look at the window [today, +1, +2, ..., +N-1].
    # If today's rate ranks in the top K of that window → 1 (good day).
    # Otherwise → 0.
    #
    # This is cleaner than "above the forward mean" because:
    #   - ~30% positive rate (not 50/50 coin-flip noise)
    #   - Positive class = genuinely good timing (top 3 of 10)
    #   - The model learns "what does a clearly good day look like?"
    # -----------------------------------------------------------------
    rate_values = rate.values
    n = len(rate_values)
    target = np.full(n, np.nan)

    for i in range(n - FORWARD_WINDOW + 1):
        window = rate_values[i : i + FORWARD_WINDOW]
        rank_from_top = np.sum(window >= rate_values[i])  # 1=lowest, N=highest
        target[i] = 1.0 if rank_from_top >= (FORWARD_WINDOW - TOP_K + 1) else 0.0

    df["target_send_now"] = target

    # -----------------------------------------------------------------
    # SAMPLE WEIGHT: quadratic upweighting of extremes
    # -----------------------------------------------------------------
    pctile = df["range_position_60d"].values
    extremeness = np.abs(pctile - 0.5) * 2
    df["sample_weight"] = 1.0 + 9.0 * (extremeness ** 2)

    return df