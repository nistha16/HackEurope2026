"""To engineer features from data before training"""
import pandas as pd
import numpy as np

def engineer_features(df):
    """
    Input: DataFrame with columns ['date', 'rate']
    Output: DataFrame with engineered time-series features and prediction targets
    """
    # Ensure dataframe is sorted chronologically
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Historical lookback features
    df['rate_1d_ago'] = df['rate'].shift(1)
    df['rate_7d_avg'] = df['rate'].rolling(window=7).mean()
    df['rate_30d_avg'] = df['rate'].rolling(window=30).mean()
    df['rate_90d_avg'] = df['rate'].rolling(window=90).mean() 
    
    df['rate_7d_volatility'] = df['rate'].rolling(window=7).std()
    df['rate_momentum'] = df['rate'] - df['rate'].shift(7)
    
    # Time-based features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_month'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    
    # Ratios
    df['rate_vs_30d_avg'] = df['rate'] / df['rate_30d_avg']
    df['rate_vs_90d_avg'] = df['rate'] / df['rate_90d_avg']

    # --- Create Targets (Shift backwards to align future prices with current row) ---
    df['target_24h'] = df['rate'].shift(-1)
    df['target_72h'] = df['rate'].shift(-3)

    # Drop NaNs resulting from rolling windows and shifts
    df = df.dropna()
    
    return df