"""
Predictor Module
================

Trains and runs FX rate movement prediction models.

Data Flow
---------
  prepare_training_data.py → per-pair CSVs (e.g., data/EUR_USD.csv)
  features.py              → engineer features (price + fundamental + COT)
  predictor.py             → train model, save, predict

Key Design Decisions
--------------------
1. **Auto-detect features**: The model automatically uses whatever features
   are available in the data — price-only (27 features), +FRED (up to +11),
   +COT (up to +4).  This means adding data streams improves predictions
   without any code changes.

2. **Predict returns, not levels**: Regime-independent. A model trained when
   EUR/CHF was at 1.60 works when it's at 0.91.

3. **Dual-horizon**: Separate 1-day and 3-day models (3-day typically has
   better signal for mean-reverting pairs).

4. **Walk-forward CV**: Calibrates confidence from honest out-of-sample
   directional accuracy — not inflated in-sample metrics.

5. **HistGradientBoostingRegressor**: Handles NaN natively (important when
   some fundamental columns have partial coverage), faster than RF.
"""

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from features import engineer_features, get_available_features, PRICE_FEATURES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(MODEL_DIR, exist_ok=True)

# HistGradientBoosting handles NaN natively — critical for columns where
# FRED or COT data has partial coverage.
MODEL_PARAMS = dict(
    max_iter=200,
    max_depth=4,        # slightly deeper to capture fundamental interactions
    learning_rate=0.01,
    l2_regularization=5.0,
    min_samples_leaf=40,
    random_state=42,
)

WF_TRAIN_YEARS = 5
WF_TEST_YEARS = 1


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_pair_data(pair_name: str) -> pd.DataFrame:
    """
    Load per-pair CSV from data/ directory.

    Falls back to filtering historical_rates.csv if per-pair file doesn't exist
    (backward compatibility with price-only workflow).
    """
    pair_csv = os.path.join(DATA_DIR, f"{pair_name}.csv")

    if os.path.exists(pair_csv):
        df = pd.read_csv(pair_csv)
        return df

    # Fallback: filter the big CSV
    big_csv = os.path.join(DATA_DIR, "historical_rates.csv")
    if not os.path.exists(big_csv):
        raise FileNotFoundError(
            f"Neither {pair_csv} nor {big_csv} found. "
            "Run prepare_training_data.py or fetch_historical.py first."
        )

    from_curr, to_curr = pair_name.split("_")
    df = pd.read_csv(big_csv)
    df = df[(df["from_currency"] == from_curr) & (df["to_currency"] == to_curr)].copy()
    if df.empty:
        raise ValueError(f"No data for {pair_name} in {big_csv}")
    return df[["date", "rate"]]


# ---------------------------------------------------------------------------
# Walk-forward cross-validation
# ---------------------------------------------------------------------------

def _walk_forward_cv(eng: pd.DataFrame, feature_cols: list[str], horizon_shift: int) -> dict:
    """Walk-forward CV → aggregate directional accuracy + R²."""
    target_col = f"_wf_target_{horizon_shift}d"
    eng = eng.copy()
    eng[target_col] = eng["rate"].shift(-horizon_shift) / eng["rate"] - 1
    eng = eng.dropna(subset=[target_col])

    eng_dates = eng["date"]
    fold_dir_accs: list[float] = []
    fold_r2s: list[float] = []

    min_year = int(eng_dates.dt.year.min())
    max_year = int(eng_dates.dt.year.max())

    for test_start_year in range(min_year + WF_TRAIN_YEARS, max_year + 1):
        train_start = pd.Timestamp(f"{test_start_year - WF_TRAIN_YEARS}-01-01")
        train_end = pd.Timestamp(f"{test_start_year}-01-01")
        test_end = pd.Timestamp(f"{test_start_year + WF_TEST_YEARS}-01-01")

        train_mask = (eng_dates >= train_start) & (eng_dates < train_end)
        test_mask = (eng_dates >= train_end) & (eng_dates < test_end)

        if train_mask.sum() < 200 or test_mask.sum() < 50:
            continue

        m = HistGradientBoostingRegressor(**MODEL_PARAMS)
        m.fit(eng.loc[train_mask, feature_cols], eng.loc[train_mask, target_col])
        preds = m.predict(eng.loc[test_mask, feature_cols])
        y_test = eng.loc[test_mask, target_col].values

        fold_dir_accs.append(float(np.mean(np.sign(y_test) == np.sign(preds))))
        fold_r2s.append(float(r2_score(y_test, preds)))

    if not fold_dir_accs:
        return {"mean_dir_acc": 0.50, "std_dir_acc": 0.0, "mean_r2": 0.0,
                "n_folds": 0, "folds_above_52": 0}

    return {
        "mean_dir_acc": float(np.mean(fold_dir_accs)),
        "std_dir_acc": float(np.std(fold_dir_accs)),
        "mean_r2": float(np.mean(fold_r2s)),
        "n_folds": len(fold_dir_accs),
        "folds_above_52": int(sum(1 for d in fold_dir_accs if d > 0.52)),
    }


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_and_evaluate(pair_name: str, csv_path: str = None) -> dict:
    """
    Full training pipeline for one currency pair.

    Parameters
    ----------
    pair_name : str like "EUR_USD"
    csv_path : optional override; if None, loads from data/{pair_name}.csv

    Returns metrics dict.
    """
    # Load data
    if csv_path:
        df = pd.read_csv(csv_path)
        if "from_currency" in df.columns:
            from_curr, to_curr = pair_name.split("_")
            df = df[(df["from_currency"] == from_curr) & (df["to_currency"] == to_curr)].copy()
    else:
        df = load_pair_data(pair_name)

    if df.empty:
        raise ValueError(f"No data for {pair_name}")

    eng = engineer_features(df)

    # Auto-detect which features are available
    feature_cols = get_available_features(eng)
    n_price = len([f for f in feature_cols if f in PRICE_FEATURES])
    n_fundamental = len(feature_cols) - n_price

    # Prepare targets
    eng["target_return_3d"] = eng["rate"].shift(-3) / eng["rate"] - 1
    eng = eng.dropna(subset=["target_return_24h", "target_return_3d"]).reset_index(drop=True)

    # Drop rows where ALL feature columns are NaN (early rows before FRED data)
    eng = eng.dropna(subset=feature_cols, how="all").reset_index(drop=True)

    X = eng[feature_cols]
    y_1d = eng["target_return_24h"]
    y_3d = eng["target_return_3d"]
    current_rates = eng["rate"]

    split_idx = int(len(eng) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train_1d, y_test_1d = y_1d.iloc[:split_idx], y_1d.iloc[split_idx:]
    y_train_3d, y_test_3d = y_3d.iloc[:split_idx], y_3d.iloc[split_idx:]
    test_rates = current_rates.iloc[split_idx:]

    # --- Train ---
    model_1d = HistGradientBoostingRegressor(**MODEL_PARAMS)
    model_1d.fit(X_train, y_train_1d)

    model_3d = HistGradientBoostingRegressor(**MODEL_PARAMS)
    model_3d.fit(X_train, y_train_3d)

    # --- Evaluate held-out ---
    pred_ret_1d = model_1d.predict(X_test)
    pred_ret_3d = model_3d.predict(X_test)

    metrics_1d = {
        "r2_return": float(r2_score(y_test_1d, pred_ret_1d)),
        "mae_return": float(mean_absolute_error(y_test_1d, pred_ret_1d)),
        "dir_acc": float(np.mean(np.sign(y_test_1d.values) == np.sign(pred_ret_1d))),
    }
    metrics_3d = {
        "r2_return": float(r2_score(y_test_3d, pred_ret_3d)),
        "mae_return": float(mean_absolute_error(y_test_3d, pred_ret_3d)),
        "dir_acc": float(np.mean(np.sign(y_test_3d.values) == np.sign(pred_ret_3d))),
    }

    # Level MAE
    pred_rates_1d = test_rates.values * (1 + pred_ret_1d)
    actual_rates_1d = eng["target_24h"].iloc[split_idx:].values
    valid = ~np.isnan(actual_rates_1d)
    mae_rate = float(mean_absolute_error(actual_rates_1d[valid], pred_rates_1d[valid]))

    # --- Walk-forward CV ---
    wf_1d = _walk_forward_cv(eng, feature_cols, horizon_shift=1)
    wf_3d = _walk_forward_cv(eng, feature_cols, horizon_shift=3)

    # --- Save models + metadata ---
    joblib.dump(model_1d, os.path.join(MODEL_DIR, f"{pair_name}_24h.joblib"))
    joblib.dump(model_3d, os.path.join(MODEL_DIR, f"{pair_name}_72h.joblib"))

    metadata = {
        "pair": pair_name,
        "feature_cols": feature_cols,   # Which features this model was trained on
        "n_price_features": n_price,
        "n_fundamental_features": n_fundamental,
        "wf_dir_acc_1d": wf_1d["mean_dir_acc"],
        "wf_dir_acc_3d": wf_3d["mean_dir_acc"],
        "wf_r2_1d": wf_1d["mean_r2"],
        "wf_r2_3d": wf_3d["mean_r2"],
        "wf_folds": wf_1d["n_folds"],
    }
    with open(os.path.join(MODEL_DIR, f"{pair_name}_meta.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return {
        "pair": pair_name,
        "n_features": len(feature_cols),
        "n_price_features": n_price,
        "n_fundamental_features": n_fundamental,
        # Held-out
        "r2_return_1d": metrics_1d["r2_return"],
        "dir_acc_1d": metrics_1d["dir_acc"],
        "r2_return_3d": metrics_3d["r2_return"],
        "dir_acc_3d": metrics_3d["dir_acc"],
        "mae_rate": mae_rate,
        # Walk-forward
        "wf_dir_acc_1d": wf_1d["mean_dir_acc"],
        "wf_dir_acc_1d_std": wf_1d["std_dir_acc"],
        "wf_dir_acc_3d": wf_3d["mean_dir_acc"],
        "wf_dir_acc_3d_std": wf_3d["std_dir_acc"],
        "wf_folds": wf_1d["n_folds"],
        "wf_folds_above_52_1d": wf_1d["folds_above_52"],
        "wf_folds_above_52_3d": wf_3d["folds_above_52"],
        "test_size": len(X_test),
    }


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def predict_rate_movement(
    from_currency: str,
    to_currency: str,
    recent_data_df: pd.DataFrame,
) -> dict:
    """
    Predict future rates and provide a recommendation.

    Parameters
    ----------
    recent_data_df : DataFrame with columns matching the per-pair CSV schema
        (at minimum: 'date', 'rate'; ideally includes fundamental columns).
        Needs >= 90 rows of history.

    Returns
    -------
    dict matching PredictionMLResponse: predicted_rate_24h, predicted_rate_72h,
        confidence_score, recommendation, reasoning
    """
    pair_name = f"{from_currency}_{to_currency}"
    model_1d_path = os.path.join(MODEL_DIR, f"{pair_name}_24h.joblib")
    model_3d_path = os.path.join(MODEL_DIR, f"{pair_name}_72h.joblib")
    meta_path = os.path.join(MODEL_DIR, f"{pair_name}_meta.json")

    if not os.path.exists(model_1d_path) or not os.path.exists(model_3d_path):
        raise FileNotFoundError(f"Models for {pair_name} not found. Run train.py first.")

    model_1d = joblib.load(model_1d_path)
    model_3d = joblib.load(model_3d_path)

    # Load metadata (feature list + walk-forward accuracy)
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        feature_cols = meta.get("feature_cols", PRICE_FEATURES)
        backtested_acc_1d = meta.get("wf_dir_acc_1d", 0.50)
        backtested_acc_3d = meta.get("wf_dir_acc_3d", 0.50)
    else:
        feature_cols = PRICE_FEATURES
        backtested_acc_1d = 0.50
        backtested_acc_3d = 0.50

    # Engineer features
    eng = engineer_features(recent_data_df)
    latest_row = eng.iloc[-1:]
    current_rate = float(latest_row["rate"].values[0])

    # Use the same features the model was trained on.
    # HistGradientBoosting handles NaN natively, so missing fundamental
    # columns are OK — they'll just be treated as missing.
    available = [c for c in feature_cols if c in eng.columns]
    X_pred = latest_row[available]

    pred_return_1d = float(model_1d.predict(X_pred)[0])
    pred_return_3d = float(model_3d.predict(X_pred)[0])

    pred_rate_24h = current_rate * (1 + pred_return_1d)
    pred_rate_72h = current_rate * (1 + pred_return_3d)

    # --- Confidence: calibrated from walk-forward accuracy ---
    best_acc = max(backtested_acc_1d, backtested_acc_3d)
    confidence = 0.15 + (best_acc - 0.50) * 7.0
    confidence = max(0.10, min(0.90, confidence))

    # Attenuate for extreme predictions
    vol_col = "return_14d_std"
    if vol_col in eng.columns and not pd.isna(latest_row[vol_col].values[0]):
        recent_vol = float(latest_row[vol_col].values[0])
        if recent_vol > 0:
            z = abs(pred_return_1d) / recent_vol
            if z > 2.0:
                confidence *= 0.70
            elif z > 1.0:
                confidence *= 0.85
    confidence = round(max(0.10, min(0.90, confidence)), 2)

    # --- Recommendation ---
    has_edge = best_acc > 0.51

    if has_edge and pred_rate_24h > current_rate * 1.003:
        recommendation = "WAIT"
        improvement = round(pred_return_1d * 100, 2)
        reasoning = (
            f"Rate predicted to improve by {improvement}% in 24h "
            f"(model backtested at {best_acc:.0%} directional accuracy)."
        )
    elif has_edge and pred_rate_24h < current_rate * 0.997:
        recommendation = "SEND_NOW"
        drop = round(abs(pred_return_1d) * 100, 2)
        reasoning = (
            f"Rate may drop by {drop}% — send now to lock in current rate "
            f"(model backtested at {best_acc:.0%} directional accuracy)."
        )
    else:
        recommendation = "NEUTRAL"
        if not has_edge:
            reasoning = (
                "Rate is stable. The model does not have a statistically "
                "significant edge for this pair on a daily horizon. "
                "Consider other factors like provider fees and speed."
            )
        else:
            reasoning = "Rate is stable. No strong signal either way."

    return {
        "predicted_rate_24h": round(pred_rate_24h, 5),
        "predicted_rate_72h": round(pred_rate_72h, 5),
        "confidence_score": confidence,
        "recommendation": recommendation,
        "reasoning": reasoning,
    }