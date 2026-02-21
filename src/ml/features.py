"""
Feature Engineering Module

This module transforms raw historical exchange rates into a rich dataset of financial
indicators suitable for machine learning. 

Engineered Features:
1. Stationarity (log_return):
   - What: The logarithmic percentage change between consecutive days.
   - Why: Financial prices are non-stationary (they drift). Log returns are stationary, making it easier for ML models to learn patterns rather than random walks.
   - How: np.log(current_rate / previous_rate)
   
2. Moving Averages (rate_Xd_sma, rate_Xd_ema):
   - What: Simple (SMA) and Exponential (EMA) Moving Averages for 7, 14, and 30 days.
   - Why: Smooths out daily noise to reveal underlying trends. EMAs place more weight on recent data, reacting faster to sudden market shifts.
   - How: df['rate'].rolling(window).mean() and df['rate'].ewm(span).mean()
   
3. Volatility (return_Xd_std):
   - What: Rolling standard deviation of log returns.
   - Why: Measures market turbulence. High volatility often precedes major price movements.
   - How: df['log_return'].rolling().std()
   
4. MACD (macd, macd_signal):
   - What: Moving Average Convergence Divergence.
   - Why: A trend-following momentum indicator that shows the relationship between two moving averages of a price.
   - How: 12-day EMA minus 26-day EMA. The 'signal' is a 9-day EMA of the MACD.
   
5. RSI (rsi_14d):
   - What: Relative Strength Index (14-day window).
   - Why: Momentum oscillator measuring the speed and change of price movements. Identifies "overbought" (>70) or "oversold" (<30) conditions.
   - How: 100 - (100 / (1 + (Average Gain / Average Loss)))
   
6. Bollinger Bands (bb_upper, bb_lower, bb_width):
   - What: Volatility bands placed above and below a moving average.
   - Why: Prices tend to bounce between bands. A narrow 'bb_width' (squeeze) often indicates an impending sharp price breakout.
   - How: 20-day SMA +/- (2 * 20-day standard deviation).
   
7. Temporal Features (day_of_week, is_month_end, is_month_start):
   - What: Calendar context.
   - Why: Forex markets exhibit seasonality (e.g., weekend closures, end-of-month institutional rebalancing).
   - How: Extracted directly from the pandas datetime properties.
   
8. Ratios (dist_from_30d_sma):
   - What: Normalized distance of current price from the 30-day moving average.
   - Why: Helps the model understand if the current price is relatively high or low compared to its recent historical baseline.
   - How: (current_rate / 30d_sma) - 1
   
Targets:
- target_24h / target_72h: Absolute future prices (shifted backwards).
- target_return_24h: Future 24h percentage return. Often easier for ML to predict than absolute price.
"""
import pandas as pd
import numpy as np

def engineer_features(df):
    """
    Input: DataFrame with columns ['date', 'rate']
    Output: DataFrame with advanced engineered time-series features and prediction targets
    """
    # 1. Ensure dataframe is sorted chronologically (Critical to prevent data leakage)
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # 2. Stationarity: Log Returns (Crucial for financial ML)
    # This tells the model the day-to-day percentage momentum rather than raw arbitrary prices.
    df['log_return'] = np.log(df['rate'] / df['rate'].shift(1))
    
    # 3. Moving Averages (Simple and Exponential) & Volatility
    for window in [7, 14, 30]:
        df[f'rate_{window}d_sma'] = df['rate'].rolling(window=window).mean()
        # Exponential Moving Average reacts faster to recent price changes than SMA
        df[f'rate_{window}d_ema'] = df['rate'].ewm(span=window, adjust=False).mean()
        # Volatility of returns (how crazy the market is acting)
        df[f'return_{window}d_std'] = df['log_return'].rolling(window=window).std()

    # 4. Advanced Technical Indicators (The "Hackathon Winning" features)
    
    # MACD (Moving Average Convergence Divergence)
    ema_12 = df['rate'].ewm(span=12, adjust=False).mean()
    ema_26 = df['rate'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # RSI (Relative Strength Index) - 14 Day
    delta = df['rate'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14d'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20-day window, 2 standard deviations)
    sma_20 = df['rate'].rolling(window=20).mean()
    std_20 = df['rate'].rolling(window=20).std()
    df['bb_upper'] = sma_20 + (std_20 * 2)
    df['bb_lower'] = sma_20 - (std_20 * 2)
    # Band width ratio: pinpoints "squeezes" before major price breakouts
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20

    # 5. Temporal / Context Features
    df['day_of_week'] = df['date'].dt.dayofweek
    # Markets often rebalance at the start/end of the month, creating predictable anomalies
    df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
    
    # Ratios (Normalized distance from recent averages)
    df['dist_from_30d_sma'] = (df['rate'] / df['rate_30d_sma']) - 1

    # --- 6. Targets ---
    # Your original targets (Predicting absolute price) - Kept for backwards compatibility
    df['target_24h'] = df['rate'].shift(-1)
    df['target_72h'] = df['rate'].shift(-3)
    
    # Advanced targets: Often, ML models perform better predicting the *return* rather than the price.
    # (e.g., predicting +0.005 instead of 1.085)
    df['target_return_24h'] = df['rate'].shift(-1) / df['rate'] - 1

    # Drop NaNs resulting from rolling windows and shifts at the start and end
    df = df.dropna().reset_index(drop=True)
    
    return df