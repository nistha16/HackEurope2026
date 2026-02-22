"""
Global Training Script (Classification Framework)
=================================================
Trains ONE Global XGBoost Model on pooled datasets from all corridors.
Uses per-corridor time-based splitting to prevent cross-corridor temporal leakage.
"""

import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
from features import engineer_features, FEATURE_COLS

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_rates.csv")


def build_global_dataset():
    if not os.path.exists(HISTORICAL_CSV):
        raise FileNotFoundError(f"Missing {HISTORICAL_CSV}. Please ensure data is fetched.")

    df = pd.read_csv(HISTORICAL_CSV)
    train_slices, val_slices, test_slices = [], [], []

    print("Engineering features globally across all corridors...")
    for (f_curr, t_curr), group in df.groupby(["from_currency", "to_currency"]):
        if len(group) < 100:
            continue

        features = engineer_features(group)
        features = features.dropna(subset=["target_send_now"] + FEATURE_COLS)

        if len(features) < 30:
            continue

        # ---- Per-corridor time-based split ----
        # This prevents the global sort from mixing future data of one
        # corridor into the training set of another.
        features = features.sort_values("date").reset_index(drop=True)
        n = len(features)
        t_end = int(n * 0.70)
        v_end = int(n * 0.85)

        train_slices.append(features.iloc[:t_end])
        val_slices.append(features.iloc[t_end:v_end])
        test_slices.append(features.iloc[v_end:])

        print(f"  {f_curr}/{t_curr}: {n} rows  (train {t_end} | val {v_end - t_end} | test {n - v_end})")

    train = pd.concat(train_slices, ignore_index=True)
    val   = pd.concat(val_slices,   ignore_index=True)
    test  = pd.concat(test_slices,  ignore_index=True)
    return train, val, test


def train_global_model():
    print("--- Starting Single Global Model Pipeline ---")
    train_data, val_data, test_data = build_global_dataset()

    X_train, y_train = train_data[FEATURE_COLS], train_data["target_send_now"]
    X_val,   y_val   = val_data[FEATURE_COLS],   val_data["target_send_now"]
    X_test,  y_test  = test_data[FEATURE_COLS],  test_data["target_send_now"]

    print(f"\nDataset Size:")
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    print(f"  Target rate — Train: {y_train.mean():.1%} | Val: {y_val.mean():.1%} | Test: {y_test.mean():.1%}")

    # Handle class imbalance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    spw = neg_count / max(pos_count, 1)
    print(f"  scale_pos_weight: {spw:.3f}")

    # -----------------------------------------------------------------
    # Lighter regularization so the model can pick up the (weak) signal.
    # Moderate depth + column sampling keeps it generalizable.
    # -----------------------------------------------------------------
    model = XGBClassifier(
        n_estimators=800,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.75,
        colsample_bytree=0.75,
        reg_alpha=0.5,           # Lighter L1
        reg_lambda=1.0,          # Lighter L2
        min_child_weight=50,     # Forces leaves to cover enough samples
        scale_pos_weight=spw,
        n_jobs=-1,
        random_state=42,
        eval_metric=["logloss", "auc"],
        early_stopping_rounds=40,
    )

    print(f"\nTraining XGBoost (lighter regularization, balanced classes)...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=50,
    )

    # -----------------------------------------------------------------
    # Evaluation
    # -----------------------------------------------------------------
    preds_proba = model.predict_proba(X_test)[:, 1]
    preds_class = model.predict(X_test)

    auc = roc_auc_score(y_test, preds_proba)
    acc = accuracy_score(y_test, preds_class)

    print("\n--- Test Set Evaluation ---")
    print(f"  Global AUC:      {auc:.4f}")
    print(f"  Global Accuracy: {acc:.4f}")
    print(classification_report(y_test, preds_class, zero_division=0))

    # Feature importance
    importance = pd.Series(
        model.feature_importances_, index=FEATURE_COLS
    ).sort_values(ascending=False)
    print("Feature Importance (top 10):")
    for feat, imp in importance.head(10).items():
        print(f"  {feat:25s} {imp:.4f}")

    # -----------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "global_timing_model.joblib")
    joblib.dump(model, model_path)
    print(f"\nSuccess! Global model saved to {model_path}")
    print(f"Best iteration: {model.best_iteration}")


if __name__ == "__main__":
    train_global_model()