"""
Global Feature Engineering Module
=================================

Transforms raw historical FX rates (Close only) into scale-invariant features.
Supports universal prediction by removing all absolute price levels.
"""

import pandas as pd
import numpy as np

def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a DataFrame with ['date', 'rate'] into features.
    Works for any currency pair.
    """
    df = df.copy()
    
    # 0. Preparation
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    rate = df["rate"]
    
    # 1. Returns (Scale-Invariant)
    df["log_return"] = np.log(rate / rate.shift(1))
    df["return_1d_lag"] = df["log_return"].shift(1)
    df["return_2d"] = rate / rate.shift(2) - 1
    df["return_5d"] = rate / rate.shift(5) - 1
    
    # 2. Volatility (Replaces ATR since we lack High/Low)
    # Normalized by current rate or based on returns
    for w in [7, 14, 30]:
        df[f"volatility_{w}d"] = df["log_return"].rolling(window=w).std()
        
    # 3. Momentum & Trend (Ratio-based)
    for w in [7, 21, 50]:
        sma = rate.rolling(window=w).mean()
        df[f"rate_vs_sma_{w}d"] = rate / sma - 1
        
    # 4. Technical Oscillators (Bounded)
    # RSI implementation using pure pandas
    delta = rate.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["rsi_14"] = df["rsi_14"].fillna(50) / 100.0 # Bounded 0-1
    
    # MACD normalized by rolling volatility
    ema12 = rate.ewm(span=12, adjust=False).mean()
    ema26 = rate.ewm(span=26, adjust=False).mean()
    macd = (ema12 - ema26) / rate
    df["macd_norm"] = macd
    df["macd_signal"] = df["macd_norm"].ewm(span=9, adjust=False).mean()
    
    # 5. Temporal Features (Cyclical)
    # Day of week (0-6)
    dow = df["date"].dt.dayofweek
    df["sin_dow"] = np.sin(2 * np.pi * dow / 7)
    df["cos_dow"] = np.cos(2 * np.pi * dow / 7)
    
    # Month (1-12)
    month = df["date"].dt.month
    df["sin_month"] = np.sin(2 * np.pi * month / 12)
    df["cos_month"] = np.cos(2 * np.pi * month / 12)

    # 6. Targets (Returns)
    df["target_return_24h"] = rate.shift(-1) / rate - 1
    df["target_return_72h"] = rate.shift(-3) / rate - 1
    
    # 7. Metadata (Used for grouping, not features)
    # We keep date and any pair identifiers for the training script
    
    return df

# registry for the model
FEATURE_COLS = [
    "log_return", "return_1d_lag", "return_2d", "return_5d",
    "volatility_7d", "volatility_14d", "volatility_30d",
    "rate_vs_sma_7d", "rate_vs_sma_21d", "rate_vs_sma_50d",
    "rsi_14", "macd_norm", "macd_signal",
    "sin_dow", "cos_dow", "sin_month", "cos_month"
]