"""Defines the predictor and decision """

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .features import engineer_features

# Ensure models directory exists
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = [
    'rate_1d_ago', 'rate_7d_avg', 'rate_30d_avg', 'rate_7d_volatility',
    'rate_momentum', 'day_of_week', 'day_of_month', 'month',
    'rate_vs_30d_avg', 'rate_vs_90d_avg'
]

def train_and_evaluate(csv_path: str, pair_name: str):
    """Loads historical CSV, engineers features, trains the RF models, and saves them."""
    df = pd.read_csv(csv_path)
    df = engineer_features(df)
    
    X = df[FEATURE_COLS]
    y_24h = df['target_24h']
    y_72h = df['target_72h']
    
    # Chronological split: 80% train, 20% test. CRITICAL: shuffle=False for time series!
    X_train, X_test, y_train_24, y_test_24 = train_test_split(X, y_24h, test_size=0.2, shuffle=False)
    _, _, y_train_72, y_test_72 = train_test_split(X, y_72h, test_size=0.2, shuffle=False)
    
    # Train 24h model
    rf_24h = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_24h.fit(X_train, y_train_24)
    
    # Train 72h model
    rf_72h = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_72h.fit(X_train, y_train_72)
    
    # Evaluate 24h model
    preds_24 = rf_24h.predict(X_test)
    r2_24 = r2_score(y_test_24, preds_24)
    mae_24 = mean_absolute_error(y_test_24, preds_24)
    rmse_24 = np.sqrt(mean_squared_error(y_test_24, preds_24))
    
    # Save models
    joblib.dump(rf_24h, os.path.join(MODEL_DIR, f"{pair_name}_24h.joblib"))
    joblib.dump(rf_72h, os.path.join(MODEL_DIR, f"{pair_name}_72h.joblib"))
    
    return {"pair": pair_name, "r2": r2_24, "mae": mae_24, "rmse": rmse_24}

def predict_rate_movement(from_currency: str, to_currency: str, recent_data_df: pd.DataFrame):
    """
    Predicts future rates and provides recommendations.
    recent_data_df needs at least 90 days of history to compute moving averages.
    """
    pair_name = f"{from_currency}_{to_currency}"
    model_24h_path = os.path.join(MODEL_DIR, f"{pair_name}_24h.joblib")
    model_72h_path = os.path.join(MODEL_DIR, f"{pair_name}_72h.joblib")
    
    if not os.path.exists(model_24h_path) or not os.path.exists(model_72h_path):
        raise FileNotFoundError(f"Models for {pair_name} not found. Please train first.")
        
    # Load Models (in memory - FastAPI will ideally load these once on startup)
    rf_24h = joblib.load(model_24h_path)
    rf_72h = joblib.load(model_72h_path)
    
    # Feature Engineering on latest data
    df = engineer_features(recent_data_df)
    latest_row = df.iloc[-1:] # Take the absolute most recent day's features
    current_rate = latest_row['rate'].values[0]
    
    X_pred = latest_row[FEATURE_COLS]
    
    pred_24h = rf_24h.predict(X_pred)[0]
    pred_72h = rf_72h.predict(X_pred)[0]
    
    # Confidence Score: Std dev of predictions from the 100 individual trees
    tree_preds_24h = np.array([tree.predict(X_pred.values)[0] for tree in rf_24h.estimators_])
    std_dev = np.std(tree_preds_24h)
    
    # Convert std dev to a 0-1 confidence score (exponential decay heuristic)
    confidence = float(np.exp(-10 * (std_dev / current_rate)))
    confidence = max(0.0, min(1.0, confidence)) # Clamp between 0 and 1
    
    # Decision Logic
    if pred_24h > current_rate * 1.003:
        recommendation = 'WAIT'
        improvement = round(((pred_24h - current_rate) / current_rate) * 100, 2)
        reasoning = f'Rate predicted to improve by {improvement}% in 24h'
    elif pred_24h < current_rate * 0.997:
        recommendation = 'SEND_NOW'
        drop = round(((current_rate - pred_24h) / current_rate) * 100, 2)
        reasoning = f'Rate may drop by {drop}% — send now to lock in current rate'
    else:
        recommendation = 'NEUTRAL'
        reasoning = 'Rate is stable. No strong signal either way.'
        
    return {
        "predicted_rate_24h": float(round(pred_24h, 5)),
        "predicted_rate_72h": float(round(pred_72h, 5)),
        "confidence_score": round(confidence, 2),
        "recommendation": recommendation,
        "reasoning": reasoning
    }