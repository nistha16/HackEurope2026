"""
Global Training Script
======================

Aggregates all available FX pairs into one scale-invariant dataset.
Trains a single XGBoost model for universal zero-shot inference.
"""

import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from features import generate_features, FEATURE_COLS

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_rates.csv")

def build_global_dataset():
    if not os.path.exists(HISTORICAL_CSV):
        raise FileNotFoundError(f"Missing {HISTORICAL_CSV}. Run fetch_historical.py first.")
    
    df = pd.read_csv(HISTORICAL_CSV)
    print(f"Loading {len(df)} rows from historical data...")
    
    processed_slices = []
    
    # Group by corridor to calculate features correctly
    groups = df.groupby(["from_currency", "to_currency"])
    print(f"Processing {len(groups)} currency pairs...")
    
    for (f, t), group in groups:
        if len(group) < 100: continue
        
        features = generate_features(group)
        # Drop rows where we can't calculate targets or long-window features
        features = features.dropna(subset=FEATURE_COLS + ["target_return_24h"])
        processed_slices.append(features)
        
    master_df = pd.concat(processed_slices, ignore_index=True)
    return master_df

def train_global_model():
    print("--- Starting Global FX Training Pipeline ---")
    
    data = build_global_dataset()
    print(f"Unified dataset built: {len(data)} training samples across {len(FEATURE_COLS)} features.")
    
    # Shuffle for training
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # 80/20 Split
    split = int(len(data) * 0.8)
    train_data = data.iloc[:split]
    test_data = data.iloc[split:]
    
    X_train = train_data[FEATURE_COLS]
    X_test = test_data[FEATURE_COLS]
    
    horizons = [
        ("24h", "target_return_24h"),
        ("72h", "target_return_72h")
    ]
    
    for label, target_col in horizons:
        print(f"\nTraining Global Model [{label}]...")
        
        y_train = train_data[target_col].dropna()
        X_train_clean = X_train.loc[y_train.index]
        
        model = XGBRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=42
        )
        
        model.fit(X_train_clean, y_train)
        
        # Evaluation
        y_test = test_data[target_col].dropna()
        X_test_clean = X_test.loc[y_test.index]
        preds = model.predict(X_test_clean)
        
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        dir_acc = np.mean(np.sign(y_test) == np.sign(preds))
        
        print(f"Results for {label}:")
        print(f"  R² Score: {r2:.5f}")
        print(f"  MAE:      {mae:.5f}")
        print(f"  Directional Acc: {dir_acc:.1%}")
        
        # Save
        save_path = os.path.join(MODEL_DIR, f"global_fx_{label}.joblib")
        joblib.dump(model, save_path)
        print(f"Saved: {save_path}")

if __name__ == "__main__":
    train_global_model()