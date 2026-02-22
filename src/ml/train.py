"""
Global Training Script (Classification + Ensemble)
===================================================
Trains a stacked ensemble on pooled data from all corridors:
  1. Logistic Regression — captures linear mean-reversion cleanly
  2. XGBoost Classifier  — captures nonlinear calendar/vol interactions

Final model outputs calibrated probability = simple average of both.
Sample weights emphasise extreme-position days where signal is strongest.
"""

import os
import warnings
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
from features import engineer_features, FEATURE_COLS, FORWARD_WINDOW

warnings.filterwarnings("ignore", category=UserWarning)

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_rates.csv")

PURGE_DAYS = FORWARD_WINDOW  # 14-day gap between splits


def build_global_dataset():
    if not os.path.exists(HISTORICAL_CSV):
        raise FileNotFoundError(f"Missing {HISTORICAL_CSV}.")

    df = pd.read_csv(HISTORICAL_CSV)
    train_sl, val_sl, test_sl = [], [], []

    print("Engineering features across all corridors...")
    for (fc, tc), group in df.groupby(["from_currency", "to_currency"]):
        if len(group) < 120:
            continue

        feat = engineer_features(group)
        feat = feat.dropna(subset=["target_send_now"] + FEATURE_COLS)
        if len(feat) < 80:
            continue

        feat = feat.sort_values("date").reset_index(drop=True)
        n = len(feat)

        tr_end = int(n * 0.70)
        va_start = tr_end + PURGE_DAYS
        va_end = int(n * 0.85)
        te_start = va_end + PURGE_DAYS

        if te_start >= n - 20:
            continue

        train_sl.append(feat.iloc[:tr_end])
        val_sl.append(feat.iloc[va_start:va_end])
        test_sl.append(feat.iloc[te_start:])

        print(f"  {fc}/{tc}: {n} usable rows")

    train = pd.concat(train_sl, ignore_index=True)
    val   = pd.concat(val_sl,   ignore_index=True)
    test  = pd.concat(test_sl,  ignore_index=True)
    return train, val, test


class EnsembleModel:
    """Simple average ensemble of LogReg + XGBoost."""

    def __init__(self, logreg, xgb, weight_lr=0.4, weight_xgb=0.6):
        self.logreg = logreg
        self.xgb = xgb
        self.w_lr = weight_lr
        self.w_xgb = weight_xgb

    def predict_proba(self, X):
        p_lr  = self.logreg.predict_proba(X)[:, 1]
        p_xgb = self.xgb.predict_proba(X)[:, 1]
        p_avg = self.w_lr * p_lr + self.w_xgb * p_xgb
        return np.column_stack([1 - p_avg, p_avg])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def train_global_model():
    print("--- Starting Ensemble Model Pipeline ---")
    train_data, val_data, test_data = build_global_dataset()

    X_train = train_data[FEATURE_COLS]
    y_train = train_data["target_send_now"]
    w_train = train_data["sample_weight"]

    X_val = val_data[FEATURE_COLS]
    y_val = val_data["target_send_now"]

    X_test = test_data[FEATURE_COLS]
    y_test = test_data["target_send_now"]

    print(f"\nDataset Size:")
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    print(f"  Target rate — Train: {y_train.mean():.3f} | Val: {y_val.mean():.3f} | Test: {y_test.mean():.3f}")

    # ==================================================================
    # MODEL 1: Logistic Regression (linear mean-reversion detector)
    # ==================================================================
    print("\n[1/2] Training Logistic Regression...")
    logreg = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(
            C=0.1,
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
        ))
    ])
    logreg.fit(X_train, y_train, lr__sample_weight=w_train.values)

    lr_proba = logreg.predict_proba(X_test)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_proba)
    print(f"  LogReg Test AUC: {lr_auc:.4f}")

    # ==================================================================
    # MODEL 2: XGBoost (nonlinear interactions)
    # ==================================================================
    print("\n[2/2] Training XGBoost...")

    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    spw = neg / max(pos, 1)

    xgb = XGBClassifier(
        n_estimators=600,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.75,
        colsample_bytree=0.70,
        reg_alpha=0.1,
        reg_lambda=0.5,
        min_child_weight=20,
        scale_pos_weight=spw,
        n_jobs=-1,
        random_state=42,
        eval_metric=["logloss", "auc"],
        early_stopping_rounds=40,
    )
    xgb.fit(
        X_train, y_train,
        sample_weight=w_train.values,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=50,
    )

    xgb_proba = xgb.predict_proba(X_test)[:, 1]
    xgb_auc = roc_auc_score(y_test, xgb_proba)
    print(f"  XGBoost Test AUC: {xgb_auc:.4f}")

    # ==================================================================
    # ENSEMBLE: tune blend weights on validation set
    # ==================================================================
    print("\n[Ensemble] Tuning blend weights on validation set...")
    lr_val  = logreg.predict_proba(X_val)[:, 1]
    xgb_val = xgb.predict_proba(X_val)[:, 1]

    best_auc, best_w = 0, 0.5
    for w_xgb in np.arange(0.3, 0.8, 0.05):
        blended = (1 - w_xgb) * lr_val + w_xgb * xgb_val
        auc = roc_auc_score(y_val, blended)
        if auc > best_auc:
            best_auc, best_w = auc, w_xgb

    print(f"  Best val AUC: {best_auc:.4f} at XGB weight={best_w:.2f}")

    ensemble = EnsembleModel(logreg, xgb, weight_lr=1 - best_w, weight_xgb=best_w)

    # ==================================================================
    # Final Evaluation
    # ==================================================================
    ens_proba = ensemble.predict_proba(X_test)[:, 1]
    ens_pred  = ensemble.predict(X_test)
    ens_auc   = roc_auc_score(y_test, ens_proba)
    ens_acc   = accuracy_score(y_test, ens_pred)

    print(f"\n--- Test Set Evaluation ---")
    print(f"  LogReg AUC:   {lr_auc:.4f}")
    print(f"  XGBoost AUC:  {xgb_auc:.4f}")
    print(f"  Ensemble AUC: {ens_auc:.4f}")
    print(f"  Ensemble Acc: {ens_acc:.4f}")
    print(classification_report(y_test, ens_pred, zero_division=0))

    # Feature importance (from XGBoost component)
    importance = pd.Series(
        xgb.feature_importances_, index=FEATURE_COLS
    ).sort_values(ascending=False)
    print("XGBoost Feature Importance (top 10):")
    for feat, imp in importance.head(10).items():
        print(f"  {feat:25s} {imp:.4f}")

    # LogReg coefficients
    lr_coefs = pd.Series(
        logreg.named_steps["lr"].coef_[0], index=FEATURE_COLS
    ).sort_values(key=abs, ascending=False)
    print("\nLogReg Coefficients (top 10 by magnitude):")
    for feat, c in lr_coefs.head(10).items():
        print(f"  {feat:25s} {c:+.4f}")

    # ==================================================================
    # Save
    # ==================================================================
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "global_timing_model.joblib")
    joblib.dump(ensemble, model_path)
    print(f"\nSuccess! Ensemble saved to {model_path}")
    print(f"XGBoost best iteration: {xgb.best_iteration}")


if __name__ == "__main__":
    train_global_model()