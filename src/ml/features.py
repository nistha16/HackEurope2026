"""
Feature Engineering Module
==========================

Transforms raw historical exchange rates into regime-independent features
suitable for ML prediction of rate *movements* (returns), not levels.

Design Principle — No Absolute Levels as Features
--------------------------------------------------
FX rates drift across regimes (EUR/CHF went from 1.61→0.91 over 27 years).
A model trained on features like "rate_7d_sma = 1.55" cannot generalise to
a test period where the SMA is 0.95.  Every feature here is expressed as a
*ratio*, *return*, or *bounded indicator* so the model learns market dynamics
that transfer across any rate level.

Feature Groups
--------------
1. Returns & Momentum
   - log_return:        ln(rate_t / rate_{t-1}) — daily log return (stationary)
   - return_2d … 5d:    cumulative 2-to-5 day returns (short-term momentum)
   - momentum_7d:       (rate / rate_7d_ago) - 1  — weekly momentum from spec

2. Ratio-based Moving-Average Features
   - rate_vs_Xd_sma:    rate / SMA(X) - 1  for X in {7, 14, 30, 90}
   - rate_vs_Xd_ema:    rate / EMA(X) - 1  for X in {7, 14, 30}
   These tell the model whether the current rate is above/below its trend,
   without encoding the trend's absolute level.

3. Volatility
   - return_Xd_std:     rolling std of log returns for X in {7, 14, 30}
   - atr_14d_pct:       14-day Average True Range as a % of rate

4. Technical Indicators (already bounded / normalised)
   - rsi_14d:           Relative Strength Index (0–100)
   - macd_pct:          MACD / rate  (normalised so it's regime-independent)
   - macd_signal_pct:   MACD signal / rate
   - macd_histogram:    (MACD - signal) / rate
   - bb_width:          Bollinger Band width / SMA  (already a ratio)
   - bb_position:       (rate - bb_lower) / (bb_upper - bb_lower)  (0–1 range)

5. Temporal / Calendar
   - day_of_week:       0=Mon … 4=Fri  (from spec)
   - day_of_month:      1–31  (from spec)
   - month:             1–12  (from spec)
   - is_month_end:      binary
   - is_month_start:    binary

Targets
-------
- target_return_24h:  rate_{t+1} / rate_t - 1   (PRIMARY target for training)
- target_return_72h:  rate_{t+3} / rate_t - 1
- target_24h:         absolute next-day rate (kept for back-conversion only)
- target_72h:         absolute 3-day rate  (kept for back-conversion only)
"""

import pandas as pd
import numpy as np


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  DataFrame with columns ['date', 'rate']
            (may also have 'from_currency', 'to_currency' — ignored here)
    Output: DataFrame with regime-independent features and return targets.
    """
    df = df.copy()

    # --- 0. Prepare ---------------------------------------------------------
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rate = df["rate"]

    # --- 1. Returns & Momentum ----------------------------------------------
    df["log_return"] = np.log(rate / rate.shift(1))

    # Multi-day cumulative returns (captures short-term momentum patterns)
    for d in [2, 3, 5]:
        df[f"return_{d}d"] = rate / rate.shift(d) - 1

    # 7-day momentum (from spec: "rate_momentum — Rate change over 7d")
    df["momentum_7d"] = rate / rate.shift(7) - 1

    # --- 2. Ratio-based MA features (regime-independent) --------------------
    for window in [7, 14, 30]:
        sma = rate.rolling(window=window).mean()
        ema = rate.ewm(span=window, adjust=False).mean()
        df[f"rate_vs_{window}d_sma"] = rate / sma - 1
        df[f"rate_vs_{window}d_ema"] = rate / ema - 1

    # 90-day SMA ratio (from spec: "rate_vs_90d_avg")
    sma_90 = rate.rolling(window=90).mean()
    df["rate_vs_90d_sma"] = rate / sma_90 - 1

    # --- 3. Volatility ------------------------------------------------------
    log_ret = df["log_return"]
    for window in [7, 14, 30]:
        df[f"return_{window}d_std"] = log_ret.rolling(window=window).std()

    # ATR as percentage of rate (14-day) — captures intraday-like range info
    # For daily data without high/low, we approximate ATR from absolute returns
    abs_ret = log_ret.abs()
    df["atr_14d_pct"] = abs_ret.rolling(window=14).mean()

    # --- 4. Technical Indicators (normalised) --------------------------------

    # RSI (14-day) — already bounded 0–100
    delta = rate.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14d"] = 100 - (100 / (1 + rs))

    # MACD — normalised by rate so it's regime-independent
    ema_12 = rate.ewm(span=12, adjust=False).mean()
    ema_26 = rate.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    df["macd_pct"] = macd / rate
    df["macd_signal_pct"] = macd_signal / rate
    df["macd_histogram"] = (macd - macd_signal) / rate

    # Bollinger Bands — width is already a ratio; add position within bands
    sma_20 = rate.rolling(window=20).mean()
    std_20 = rate.rolling(window=20).std()
    bb_upper = sma_20 + (std_20 * 2)
    bb_lower = sma_20 - (std_20 * 2)
    df["bb_width"] = (bb_upper - bb_lower) / sma_20
    bb_range = bb_upper - bb_lower
    df["bb_position"] = (rate - bb_lower) / bb_range.replace(0, np.nan)

    # --- 5. Temporal / Calendar ---------------------------------------------
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day          # from spec
    df["month"] = df["date"].dt.month                # from spec
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)

    # --- 6. Targets ---------------------------------------------------------
    # Return targets (PRIMARY — what the model trains on)
    df["target_return_24h"] = rate.shift(-1) / rate - 1
    df["target_return_72h"] = rate.shift(-3) / rate - 1

    # Absolute targets (kept for back-conversion: pred_rate = current * (1 + pred_return))
    df["target_24h"] = rate.shift(-1)
    df["target_72h"] = rate.shift(-3)

    # --- 7. Drop rows with NaN from rolling windows / shifts ----------------
    df = df.dropna().reset_index(drop=True)

    return df