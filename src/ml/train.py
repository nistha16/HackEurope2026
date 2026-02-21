"""
Global Training Script
======================
"""

import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from scipy.stats import spearmanr
from features import generate_features, FEATURE_COLS

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_rates.csv")

def build_global_dataset():
    if not os.path.exists(HISTORICAL_CSV):
        raise FileNotFoundError(f"Missing {HISTORICAL_CSV}. Run fetch_historical.py first.")
    
    df = pd.read_csv(HISTORICAL_CSV)
    processed_slices = []
    groups = df.groupby(["from_currency", "to_currency"])
    
    for (f, t), group in groups:
        if len(group) < 100: continue
        features = generate_features(group)
        # Drop rows where base features are missing (keep targets for horizon-specific filtering)
        features = features.dropna(subset=FEATURE_COLS)
        processed_slices.append(features)
        
    return pd.concat(processed_slices, ignore_index=True)

def train_global_model():
    print("--- Starting Improved Global FX Training Pipeline ---")
    data = build_global_dataset()
    data = data.sort_values("date").reset_index(drop=True)
    
    # 1. Target Winsorization
    for col in ["target_return_24h", "target_return_72h"]:
        lower, upper = data[col].quantile(0.01), data[col].quantile(0.99)
        data[col] = data[col].clip(lower, upper)
    
    n = len(data)
    train_data = data.iloc[:int(n * 0.7)]
    val_data = data.iloc[int(n * 0.7):int(n * 0.85)]
    test_data = data.iloc[int(n * 0.85):]
    
    horizons = [("24h", "target_return_24h"), ("72h", "target_return_72h")]
    
    for label, target_col in horizons:
        print(f"\nTraining Global Model [{label}]...")
        
        # 2. Horizon-Specific NaN Filtering (Fixes ValueError)
        train_subset = train_data.dropna(subset=[target_col])
        val_subset = val_data.dropna(subset=[target_col])
        test_subset = test_data.dropna(subset=[target_col])

        X_train, y_train = train_subset[FEATURE_COLS], train_subset[target_col]
        X_val, y_val = val_subset[FEATURE_COLS], val_subset[target_col]
        X_test, y_test = test_subset[FEATURE_COLS], test_subset[target_col]
        
        model = XGBRegressor(
            n_estimators=1000,
            max_depth=3,
            learning_rate=0.03,
            subsample=0.7,
            colsample_bytree=0.7,
            reg_alpha=10,
            reg_lambda=1,
            n_jobs=-1,
            random_state=42,
            early_stopping_rounds=50
        )
        
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        
        preds = model.predict(X_test)
        
        # 3. Evaluation
        mae = mean_absolute_error(y_test, preds)
        dir_acc = np.mean(np.sign(y_test) == np.sign(preds))
        spearman_corr, _ = spearmanr(y_test, preds)
        
        print(f"Results for {label}:")
        print(f"  Spearman Corr: {spearman_corr:.5f}")
        print(f"  MAE:           {mae:.5f}")
        print(f"  Dir Acc:       {dir_acc:.1%}")
        
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, os.path.join(MODEL_DIR, f"global_fx_{label}.joblib"))

if __name__ == "__main__":
    train_global_model()