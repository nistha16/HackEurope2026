"""
Global Training Script (Classification + Ensemble + Backtest)
=============================================================
Trains ensemble on pooled data from all corridors.

KEY ADDITION: Backtest that proves product value.
Simulates a user who must send money once every 2 weeks.
Compares: "pick the day our model scores highest" vs "pick a random day."
The improvement % is the real metric — not raw AUC.
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

PURGE_DAYS = FORWARD_WINDOW


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
    """Weighted average ensemble of LogReg + XGBoost."""

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


def evaluate_model(name, y_true, y_proba, range_positions=None):
    y_pred = (y_proba >= 0.5).astype(int)
    auc = roc_auc_score(y_true, y_proba)
    acc = accuracy_score(y_true, y_pred)
    print(f"\n  [{name}] All Days — AUC: {auc:.4f} | Acc: {acc:.4f}")

    if range_positions is not None:
        extreme_mask = (range_positions < 0.25) | (range_positions > 0.75)
        if extreme_mask.sum() > 100:
            y_ext = y_true[extreme_mask]
            p_ext = y_proba[extreme_mask]
            auc_ext = roc_auc_score(y_ext, p_ext)
            acc_ext = accuracy_score(y_ext, (p_ext >= 0.5).astype(int))
            print(f"  [{name}] Extreme Days ({extreme_mask.sum():,} samples) — "
                  f"AUC: {auc_ext:.4f} | Acc: {acc_ext:.4f}")
    return auc


def backtest_timing_value(test_data, model, blend_weight=0.40):
    """
    Simulate: user sends money once every 2-week window.
    Compare rates achieved by:
      1. Random day (expected = window average)
      2. Best day by our blended score (model + percentile)
      3. Oracle (best day in hindsight — upper bound)

    This is the REAL metric for the product.
    """
    print("\n" + "=" * 60)
    print("BACKTEST: Timing value simulation")
    print("=" * 60)

    # Need rate + features in test data
    if "rate" not in test_data.columns:
        print("  [Backtest] Skipped — 'rate' not in test data.")
        return

    X_test = test_data[FEATURE_COLS]
    model_proba = model.predict_proba(X_test)[:, 1]
    raw_pctile  = test_data["range_position_60d"].values
    rates       = test_data["rate"].values

    # Blended score (same as predictor.py)
    blended_score = blend_weight * model_proba + (1 - blend_weight) * raw_pctile

    window_size = 10  # ~2 weeks of trading days
    n = len(rates)

    random_rates, scored_rates, pctile_rates, oracle_rates = [], [], [], []

    for start in range(0, n - window_size, window_size):
        end = start + window_size
        window_rates = rates[start:end]
        window_scores = blended_score[start:end]
        window_pctile = raw_pctile[start:end]

        random_rates.append(np.mean(window_rates))
        scored_rates.append(window_rates[np.argmax(window_scores)])
        pctile_rates.append(window_rates[np.argmax(window_pctile)])
        oracle_rates.append(np.max(window_rates))

    avg_random  = np.mean(random_rates)
    avg_scored  = np.mean(scored_rates)
    avg_pctile  = np.mean(pctile_rates)
    avg_oracle  = np.mean(oracle_rates)

    # Improvement as % of the possible improvement (random → oracle)
    possible_gain = avg_oracle - avg_random
    model_gain    = avg_scored - avg_random
    pctile_gain   = avg_pctile - avg_random

    print(f"\n  Windows: {len(random_rates)} (each ~{window_size} trading days)")
    print(f"  Avg rate — Random day:      {avg_random:.6f}")
    print(f"  Avg rate — Percentile pick:  {avg_pctile:.6f}  ({pctile_gain/avg_random*100:+.3f}%)")
    print(f"  Avg rate — Model+Pctile:     {avg_scored:.6f}  ({model_gain/avg_random*100:+.3f}%)")
    print(f"  Avg rate — Oracle (best):    {avg_oracle:.6f}  ({possible_gain/avg_random*100:+.3f}%)")

    if possible_gain > 0:
        capture_pctile = pctile_gain / possible_gain * 100
        capture_model  = model_gain / possible_gain * 100
        print(f"\n  Value capture (% of oracle gain):")
        print(f"    Percentile alone: {capture_pctile:.1f}%")
        print(f"    Model + Pctile:   {capture_model:.1f}%")

    # Per-window: how often does model pick a better day than random median?
    wins = sum(1 for s, r in zip(scored_rates, random_rates) if s > r)
    print(f"\n  Model picks better-than-average day: {wins}/{len(random_rates)} "
          f"({wins/len(random_rates)*100:.1f}% of windows)")


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
    rp_test = test_data["range_position_60d"].values

    print(f"\nDataset Size:")
    print(f"  Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")
    print(f"  Target rate — Train: {y_train.mean():.3f} | Val: {y_val.mean():.3f} | Test: {y_test.mean():.3f}")

    # Baseline: raw percentile as classifier
    raw_auc = roc_auc_score(y_test, rp_test)
    print(f"\n  Baseline (raw range_position_60d): AUC = {raw_auc:.4f}")

    # Signal agreement as classifier
    sa_test = test_data["signal_agreement"].values
    sa_auc = roc_auc_score(y_test, sa_test)
    print(f"  Baseline (signal_agreement):        AUC = {sa_auc:.4f}")

    # ==================================================================
    # MODEL 1: Logistic Regression
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
    evaluate_model("LogReg", y_test, lr_proba, rp_test)

    # ==================================================================
    # MODEL 2: XGBoost
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
    evaluate_model("XGBoost", y_test, xgb_proba, rp_test)

    # ==================================================================
    # ENSEMBLE: tune weights on validation
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
    # Final Classification Evaluation
    # ==================================================================
    ens_proba = ensemble.predict_proba(X_test)[:, 1]
    print("\n--- Final Test Set Evaluation ---")
    evaluate_model("Ensemble", y_test, ens_proba, rp_test)
    print(classification_report(y_test, ensemble.predict(X_test), zero_division=0))

    # Feature importance
    importance = pd.Series(
        xgb.feature_importances_, index=FEATURE_COLS
    ).sort_values(ascending=False)
    print("XGBoost Feature Importance (top 10):")
    for feat, imp in importance.head(10).items():
        print(f"  {feat:25s} {imp:.4f}")

    lr_coefs = pd.Series(
        logreg.named_steps["lr"].coef_[0], index=FEATURE_COLS
    ).sort_values(key=abs, ascending=False)
    print("\nLogReg Coefficients (top 10 by magnitude):")
    for feat, c in lr_coefs.head(10).items():
        print(f"  {feat:25s} {c:+.4f}")

    # ==================================================================
    # BACKTEST: The metric that actually matters
    # ==================================================================
    backtest_timing_value(test_data, ensemble)

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