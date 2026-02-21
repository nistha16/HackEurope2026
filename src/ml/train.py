"""
Training Script
===============

Trains per-corridor models and reports metrics.

Usage:
  python train.py                  # Train all target pairs
  python train.py EUR_USD GBP_INR  # Train specific pairs

Data prerequisites (run in order):
  1. python data/fetch_historical.py   # FX rates (required)
  2. python data/fetch_fred.py         # Interest rates, VIX (recommended)
  3. python data/fetch_cot.py          # CFTC positioning (recommended)
  4. python data/prepare_training_data.py  # Merge into per-pair CSVs

If step 4 hasn't been run, the trainer falls back to historical_rates.csv
(price-only mode — fewer features, weaker predictions).

Pair Selection
--------------
The spec asks for EUR/MAD, EUR/USD, GBP/INR.  EUR/MAD is NOT available from
Frankfurter (MAD is not ECB-tracked).  EUR/TRY substitutes as the closest
high-volatility emerging-market corridor.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predictor import train_and_evaluate

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DEFAULT_PAIRS = [
    "EUR_USD",
    "GBP_INR",
    "EUR_TRY",
    "EUR_CHF",
    "USD_MXN",
]

# Acceptance thresholds (walk-forward)
MIN_WF_DIR_ACC = 0.505
MIN_FOLDS_ABOVE_52_PCT = 0.25


def _status(m: dict) -> str:
    """PASS/WARN based on walk-forward metrics."""
    best_wf = max(m["wf_dir_acc_1d"], m["wf_dir_acc_3d"])
    best_folds = max(m.get("wf_folds_above_52_1d", 0), m.get("wf_folds_above_52_3d", 0))
    folds_pct = best_folds / m["wf_folds"] if m["wf_folds"] > 0 else 0
    return "PASS" if (best_wf >= MIN_WF_DIR_ACC and folds_pct >= MIN_FOLDS_ABOVE_52_PCT) else "WARN"


def _data_tier(m: dict) -> str:
    """Describe what data the model was trained on."""
    n_fund = m.get("n_fundamental_features", 0)
    if n_fund == 0:
        return "price-only"
    elif n_fund <= 11:
        return f"price+FRED ({n_fund})"
    else:
        return f"price+FRED+COT ({n_fund})"


def main():
    # Allow command-line pair selection
    if len(sys.argv) > 1:
        pairs = sys.argv[1:]
    else:
        pairs = DEFAULT_PAIRS

    print("=" * 72)
    print("  SendSmart ML Pipeline — Training")
    print("=" * 72)

    # Check what data is available
    has_per_pair = any(
        os.path.exists(os.path.join(DATA_DIR, f"{p}.csv")) for p in pairs
    )
    has_big_csv = os.path.exists(os.path.join(DATA_DIR, "historical_rates.csv"))

    if has_per_pair:
        print("  Data source: per-pair CSVs from prepare_training_data.py")
    elif has_big_csv:
        print("  Data source: historical_rates.csv (price-only fallback)")
        print("  ⚠  Run prepare_training_data.py for better results with fundamentals")
    else:
        print(f"\n  FATAL: No data found in {DATA_DIR}/")
        return

    results = []

    for pair in pairs:
        print(f"\n{'─' * 62}")
        print(f"  Training: {pair.replace('_', '/')}")
        print(f"{'─' * 62}")

        try:
            m = train_and_evaluate(pair)
            results.append(m)

            tier = _data_tier(m)
            print(f"  Data tier:  {tier}  ({m['n_features']} features)")
            print()

            # Held-out
            print(f"  Held-out split (80/20):")
            print(f"    {'':30s} {'1-day':>10s}  {'3-day':>10s}")
            print(f"    {'R² on returns':30s} {m['r2_return_1d']:>+10.4f}  {m['r2_return_3d']:>+10.4f}")
            print(f"    {'Directional accuracy':30s} {m['dir_acc_1d']:>9.1%}  {m['dir_acc_3d']:>9.1%}")
            print(f"    {'MAE on rate level':30s} {m['mae_rate']:>10.5f}")
            print()

            # Walk-forward
            print(f"  Walk-forward CV ({m['wf_folds']} folds):")
            print(f"    {'':30s} {'1-day':>10s}  {'3-day':>10s}")
            print(
                f"    {'Dir. accuracy (mean±std)':30s} "
                f"{m['wf_dir_acc_1d']:.1%}±{m['wf_dir_acc_1d_std']:.1%}  "
                f"{m['wf_dir_acc_3d']:.1%}±{m['wf_dir_acc_3d_std']:.1%}"
            )
            print(
                f"    {'Folds > 52%':30s} "
                f"{m.get('wf_folds_above_52_1d', '?'):>10}  "
                f"{m.get('wf_folds_above_52_3d', '?'):>10}"
            )
            print()

            status = _status(m)
            best_wf = max(m["wf_dir_acc_1d"], m["wf_dir_acc_3d"])
            marker = "✓" if status == "PASS" else "⚠"
            print(f"  {marker} {status}  (best walk-forward accuracy: {best_wf:.1%})")

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"pair": pair, "error": str(e)})

    # --- Summary ---
    print(f"\n{'=' * 72}")
    print("  Summary")
    print(f"{'=' * 72}")
    print(
        f"  {'Pair':<12}"
        f"  {'Feats':>5}"
        f"  {'Data tier':<18}"
        f"  {'WF 1d':>7}"
        f"  {'WF 3d':>7}"
        f"  {'Status':>7}"
    )
    print(f"  {'─' * 62}")

    for m in results:
        if "error" in m:
            print(f"  {m['pair']:<12}  {'—':>5}  {'—':<18}  {'—':>7}  {'—':>7}  {'ERROR':>7}")
        else:
            status = _status(m)
            tier = _data_tier(m)
            print(
                f"  {m['pair']:<12}"
                f"  {m['n_features']:>5}"
                f"  {tier:<18}"
                f"  {m['wf_dir_acc_1d']:>6.1%}"
                f"  {m['wf_dir_acc_3d']:>6.1%}"
                f"  {status:>7}"
            )

    # Data improvement suggestions
    print()
    any_price_only = any(
        m.get("n_fundamental_features", 0) == 0
        for m in results if "error" not in m
    )
    if any_price_only:
        print("  ⚠  Some pairs trained with price-only data.")
        print("     Run the data pipeline for better results:")
        print("       python data/fetch_fred.py")
        print("       python data/fetch_cot.py")
        print("       python data/prepare_training_data.py")
    print()


if __name__ == "__main__":
    main()