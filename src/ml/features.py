"""
Feature Engineering Module
==========================

Transforms per-pair CSVs (from prepare_training_data.py) into ML-ready features.

Handles three data tiers gracefully:
  Tier 1 — Price only (columns: date, rate)
            27 features from technical analysis.
  Tier 2 — Price + FRED (adds: rate_differential, vix, usd_index, etc.)
            +10 fundamental features.
  Tier 3 — Price + FRED + COT (adds: cot_from_lev_net, etc.)
            +4 positioning features.

All features remain regime-independent (ratios, returns, z-scores, bounded
indicators).  No absolute levels are used as model inputs.

Feature Groups
--------------
PRICE-BASED (always available):
  1. Returns & Momentum — log_return, multi-day returns, 7d momentum
  2. MA Ratios — rate vs 7/14/30/90d SMA and EMA (normalised)
  3. Volatility — rolling std of returns, ATR
  4. Technical — RSI, MACD (normalised), Bollinger position/width
  5. Calendar — day_of_week, day_of_month, month, month boundaries

FUNDAMENTAL (when FRED data merged):
  6. Carry — rate_differential, its 30d change, 90d z-score
  7. Risk — VIX level, 5d change, 90d z-score
  8. Dollar — USD index 5d return, distance from 90d SMA
  9. Macro — yield curve slope, oil 30d return, HY spread z-score

POSITIONING (when COT data merged):
  10. Sentiment — COT net long z-score (52wk), week-over-week change
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score: (value - rolling_mean) / rolling_std."""
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std.replace(0, np.nan)


def _has_col(df: pd.DataFrame, col: str) -> bool:
    """Check if column exists and has at least some non-NaN data."""
    return col in df.columns and df[col].notna().any()


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  DataFrame with at minimum columns ['date', 'rate'].
            May also have fundamental columns from prepare_training_data.py.
    Output: DataFrame with all engineered features and return targets.
    """
    df = df.copy()

    # --- 0. Prepare ---------------------------------------------------------
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    rate = df["rate"]

    # ===================================================================
    #  TIER 1 — PRICE-BASED FEATURES (always available)
    # ===================================================================

    # --- 1. Returns & Momentum ---------------------------------------------
    df["log_return"] = np.log(rate / rate.shift(1))
    for d in [2, 3, 5]:
        df[f"return_{d}d"] = rate / rate.shift(d) - 1
    df["momentum_7d"] = rate / rate.shift(7) - 1

    # --- 2. Ratio-based MA features ----------------------------------------
    for window in [7, 14, 30]:
        sma = rate.rolling(window=window).mean()
        ema = rate.ewm(span=window, adjust=False).mean()
        df[f"rate_vs_{window}d_sma"] = rate / sma - 1
        df[f"rate_vs_{window}d_ema"] = rate / ema - 1
    sma_90 = rate.rolling(window=90).mean()
    df["rate_vs_90d_sma"] = rate / sma_90 - 1

    # --- 3. Volatility -----------------------------------------------------
    log_ret = df["log_return"]
    for window in [7, 14, 30]:
        df[f"return_{window}d_std"] = log_ret.rolling(window=window).std()
    df["atr_14d_pct"] = log_ret.abs().rolling(window=14).mean()

    # --- 4. Technical Indicators -------------------------------------------
    # RSI (14-day)
    delta = rate.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14d"] = 100 - (100 / (1 + rs))

    # MACD (normalised by rate)
    ema_12 = rate.ewm(span=12, adjust=False).mean()
    ema_26 = rate.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    df["macd_pct"] = macd / rate
    df["macd_signal_pct"] = macd_signal / rate
    df["macd_histogram"] = (macd - macd_signal) / rate

    # Bollinger Bands
    sma_20 = rate.rolling(window=20).mean()
    std_20 = rate.rolling(window=20).std()
    bb_upper = sma_20 + (std_20 * 2)
    bb_lower = sma_20 - (std_20 * 2)
    df["bb_width"] = (bb_upper - bb_lower) / sma_20
    bb_range = bb_upper - bb_lower
    df["bb_position"] = (rate - bb_lower) / bb_range.replace(0, np.nan)

    # --- 5. Calendar -------------------------------------------------------
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)

    # ===================================================================
    #  TIER 2 — FUNDAMENTAL FEATURES (when FRED data present)
    # ===================================================================

    # --- 6. Carry (interest rate differential) -----------------------------
    if _has_col(df, "rate_differential"):
        rd = df["rate_differential"]
        df["carry_level"] = rd
        df["carry_change_30d"] = rd - rd.shift(30)
        df["carry_zscore_90d"] = _zscore(rd, 90)

    # --- 7. Risk sentiment (VIX) ------------------------------------------
    if _has_col(df, "vix"):
        vix = df["vix"]
        df["vix_level"] = vix
        df["vix_change_5d"] = vix / vix.shift(5) - 1
        df["vix_zscore_90d"] = _zscore(vix, 90)

    # --- 8. Dollar strength -----------------------------------------------
    if _has_col(df, "usd_index"):
        usd = df["usd_index"]
        df["usd_return_5d"] = usd / usd.shift(5) - 1
        df["usd_vs_90d_sma"] = usd / usd.rolling(90).mean() - 1

    # --- 9. Macro indicators ----------------------------------------------
    if _has_col(df, "us_yield_spread"):
        df["yield_curve"] = df["us_yield_spread"]

    if _has_col(df, "wti_crude"):
        oil = df["wti_crude"]
        df["oil_return_30d"] = oil / oil.shift(30) - 1

    if _has_col(df, "hy_spread"):
        df["hy_spread_zscore"] = _zscore(df["hy_spread"], 90)

    # ===================================================================
    #  TIER 3 — POSITIONING FEATURES (when COT data present)
    # ===================================================================

    # --- 10. COT speculative positioning -----------------------------------
    if _has_col(df, "cot_from_lev_net"):
        cot = df["cot_from_lev_net"]
        # Z-score over ~52 weeks (260 trading days) normalises across
        # different contract sizes and currencies
        df["cot_from_zscore"] = _zscore(cot, 260)
        # Week-over-week change (COT is weekly, so shift(5) ≈ 1 week)
        df["cot_from_change"] = cot - cot.shift(5)

    if _has_col(df, "cot_to_lev_net"):
        cot_to = df["cot_to_lev_net"]
        df["cot_to_zscore"] = _zscore(cot_to, 260)
        df["cot_to_change"] = cot_to - cot_to.shift(5)

    # ===================================================================
    #  TARGETS
    # ===================================================================

    df["target_return_24h"] = rate.shift(-1) / rate - 1
    df["target_return_72h"] = rate.shift(-3) / rate - 1
    df["target_24h"] = rate.shift(-1)
    df["target_72h"] = rate.shift(-3)

    # Drop rows with NaN from rolling windows / shifts
    df = df.dropna(subset=["target_return_24h"]).reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Feature column registry
# ---------------------------------------------------------------------------
# Used by predictor.py to know which columns to feed the model.
# Columns that don't exist in a given pair's data are automatically skipped.

PRICE_FEATURES = [
    "log_return", "return_2d", "return_3d", "return_5d", "momentum_7d",
    "rate_vs_7d_sma", "rate_vs_14d_sma", "rate_vs_30d_sma", "rate_vs_90d_sma",
    "rate_vs_7d_ema", "rate_vs_14d_ema", "rate_vs_30d_ema",
    "return_7d_std", "return_14d_std", "return_30d_std", "atr_14d_pct",
    "rsi_14d", "macd_pct", "macd_signal_pct", "macd_histogram",
    "bb_width", "bb_position",
    "day_of_week", "day_of_month", "month", "is_month_end", "is_month_start",
]

FUNDAMENTAL_FEATURES = [
    "carry_level", "carry_change_30d", "carry_zscore_90d",
    "vix_level", "vix_change_5d", "vix_zscore_90d",
    "usd_return_5d", "usd_vs_90d_sma",
    "yield_curve", "oil_return_30d", "hy_spread_zscore",
]

COT_FEATURES = [
    "cot_from_zscore", "cot_from_change",
    "cot_to_zscore", "cot_to_change",
]

ALL_POSSIBLE_FEATURES = PRICE_FEATURES + FUNDAMENTAL_FEATURES + COT_FEATURES


def get_available_features(df: pd.DataFrame) -> list[str]:
    """Return the subset of ALL_POSSIBLE_FEATURES that exist and have data in df."""
    available = []
    for col in ALL_POSSIBLE_FEATURES:
        if col in df.columns and df[col].notna().any():
            available.append(col)
    return available