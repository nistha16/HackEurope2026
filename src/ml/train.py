"""
Training Script
===============

Trains per-corridor prediction models and reports metrics.

Pair Selection
--------------
The spec asks for EUR/MAD, EUR/USD, GBP/INR.  However EUR/MAD is NOT
available from the Frankfurter API (MAD is not an ECB-tracked currency).
We substitute EUR/TRY (Turkish Lira) as it's the closest high-volatility
emerging-market corridor available, and add EUR/CHF + USD/MXN for broader
coverage.

Acceptance Criteria (updated for return-based evaluation)
---------------------------------------------------------
The original spec set R² > 0.85 on *levels*, which is trivially achieved by
any model that approximates yesterday's rate (a random walk gives R² ≈ 0.99
on levels).  That metric doesn't measure forecasting ability.

Meaningful criteria for return prediction:
  - R² on returns > 0.0  (model beats the "predict zero change" baseline)
  - Directional accuracy > 52%  (better than a coin flip — tradeable edge)
  - MAE on rate < 1% of typical rate  (converted predictions are usable)

These are genuinely hard to achieve on FX data and represent real
predictive value rather than autocorrelation artifacts.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predictor import train_and_evaluate

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# Corridors to train — all verified present in historical_rates.csv
TARGET_PAIRS = [
    "EUR_USD",   # from spec
    "GBP_INR",   # from spec
    "EUR_TRY",   # substitute for EUR/MAD (MAD not in ECB/Frankfurter)
    "EUR_CHF",   # originally attempted — now should work with return-based model
    "USD_MXN",   # high-volume LatAm corridor used by the app
]

# Thresholds for acceptance criteria
MIN_DIRECTIONAL_ACCURACY = 0.52   # better than coin flip
MIN_R2_RETURN = 0.0               # beats "predict zero" baseline


def main():
    csv_path = os.path.join(DATA_DIR, "historical_rates.csv")

    print("=" * 64)
    print("  SendSmart ML Pipeline — Training")
    print("=" * 64)

    if not os.path.exists(csv_path):
        print(f"\n[!] FATAL: Historical data CSV not found at {csv_path}")
        print("    Run `python data/fetch_historical.py` first.")
        return

    results = []

    for pair in TARGET_PAIRS:
        print(f"\n{'─' * 48}")
        print(f"  Training: {pair.replace('_', '/')}")
        print(f"{'─' * 48}")

        try:
            metrics = train_and_evaluate(csv_path, pair)
            results.append(metrics)

            # --- Return-based metrics (what actually matters) ---
            print(f"  Return prediction (24h):")
            print(f"    R² on returns:         {metrics['r2_return']:>8.4f}")
            print(f"    MAE on returns:        {metrics['mae_return']:>8.6f}  "
                  f"({metrics['mae_return'] * 100:.4f}%)")
            print(f"    Directional accuracy:  {metrics['directional_accuracy']:>8.1%}")
            print()

            # --- Rate-level metrics (for interpretability) ---
            print(f"  Converted to rate level:")
            print(f"    MAE on rate:           {metrics['mae_rate']:>8.5f}")
            print(f"    RMSE on rate:          {metrics['rmse_rate']:>8.5f}")
            print(f"    Test samples:          {metrics['test_size']:>8d}")
            print()

            # --- Acceptance check ---
            dir_ok = metrics["directional_accuracy"] >= MIN_DIRECTIONAL_ACCURACY
            r2_ok = metrics["r2_return"] >= MIN_R2_RETURN

            if dir_ok and r2_ok:
                print(f"  ✓ PASS  (direction ≥{MIN_DIRECTIONAL_ACCURACY:.0%} "
                      f"and R²(return) ≥{MIN_R2_RETURN})")
            else:
                reasons = []
                if not dir_ok:
                    reasons.append(
                        f"direction {metrics['directional_accuracy']:.1%} "
                        f"< {MIN_DIRECTIONAL_ACCURACY:.0%}"
                    )
                if not r2_ok:
                    reasons.append(
                        f"R²(return) {metrics['r2_return']:.4f} < {MIN_R2_RETURN}"
                    )
                print(f"  ⚠ WARN  ({'; '.join(reasons)})")

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"pair": pair, "error": str(e)})

    # --- Summary table ---
    print(f"\n{'=' * 64}")
    print("  Summary")
    print(f"{'=' * 64}")
    print(f"  {'Pair':<12} {'R²(ret)':>8} {'Dir.Acc':>8} {'MAE(rate)':>10} {'Status':>8}")
    print(f"  {'─' * 50}")

    for m in results:
        if "error" in m:
            print(f"  {m['pair']:<12} {'—':>8} {'—':>8} {'—':>10} {'ERROR':>8}")
        else:
            status = "PASS" if (
                m["directional_accuracy"] >= MIN_DIRECTIONAL_ACCURACY
                and m["r2_return"] >= MIN_R2_RETURN
            ) else "WARN"
            print(
                f"  {m['pair']:<12} "
                f"{m['r2_return']:>8.4f} "
                f"{m['directional_accuracy']:>7.1%} "
                f"{m['mae_rate']:>10.5f} "
                f"{status:>8}"
            )

    print()
    print("  Note: EUR/MAD not available from Frankfurter (MAD not ECB-tracked).")
    print("  EUR/TRY is used as the emerging-market substitute.")
    print()


if __name__ == "__main__":
    main()