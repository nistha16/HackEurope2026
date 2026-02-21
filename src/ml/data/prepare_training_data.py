#!/usr/bin/env python3
"""
Prepare unified training data by merging all data streams.

Reads:
  - data/historical_rates.csv    (daily FX rates from Frankfurter)
  - data/fred_data.csv           (interest rates, VIX, etc. from FRED) [optional]
  - data/cot_data.csv            (CFTC positioning data)               [optional]

Outputs:
  - data/{FROM}_{TO}.csv per currency pair (e.g., data/EUR_USD.csv)

Each output CSV has all columns aligned to daily frequency:
  - FRED monthly data is forward-filled to daily
  - COT weekly data is forward-filled to daily
  - Interest rate differentials are computed per pair
  - COT net positioning is included for currencies with futures data

The output files are what features.py and the training pipeline consume.
If FRED or COT data is missing, the script still produces per-pair CSVs
with just the FX rate — the system degrades gracefully.

Usage:
  python data/prepare_training_data.py

Run the fetch scripts first for best results:
  python data/fetch_historical.py   # FX rates (required)
  python data/fetch_fred.py         # Interest rates, VIX (recommended)
  python data/fetch_cot.py          # Positioning data (recommended)
"""

import csv
import os
import sys
from datetime import datetime
from typing import Optional

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pandas and numpy are required.  pip install pandas numpy")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

FX_FILE = os.path.join(DATA_DIR, "historical_rates.csv")
FRED_FILE = os.path.join(DATA_DIR, "fred_data.csv")
COT_FILE = os.path.join(DATA_DIR, "cot_data.csv")

# Currency pairs to prepare (must exist in historical_rates.csv)
TARGET_PAIRS: list[tuple[str, str]] = [
    ("EUR", "USD"),
    ("GBP", "INR"),
    ("EUR", "TRY"),
    ("EUR", "CHF"),
    ("USD", "MXN"),
    # Additional pairs with good data coverage:
    ("EUR", "GBP"),
    ("EUR", "JPY"),
    ("GBP", "USD"),
    ("USD", "JPY"),
    ("EUR", "BRL"),
    ("USD", "BRL"),
    ("USD", "ZAR"),
]

# Map each currency to its relevant FRED interest rate column.
# These column names must match what fetch_fred.py outputs.
CURRENCY_TO_RATE_COL: dict[str, str] = {
    "USD": "fed_funds_rate",
    "EUR": "ecb_deposit_rate",
    "GBP": "uk_rate",
    "JPY": "jp_rate",
    "CHF": "ch_rate",
    "TRY": "tr_rate",
    "MXN": "mx_rate",
    "INR": "in_rate",
}

# Sentiment columns from FRED that apply globally to all pairs
GLOBAL_FRED_COLS = ["vix", "usd_index", "wti_crude", "hy_spread",
                    "us_10y_yield", "us_2y_yield", "us_yield_spread"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_fx() -> pd.DataFrame:
    """Load FX rates. Required — exits if missing."""
    if not os.path.exists(FX_FILE):
        print(f"FATAL: {FX_FILE} not found. Run fetch_historical.py first.")
        sys.exit(1)

    df = pd.read_csv(FX_FILE)
    df["date"] = pd.to_datetime(df["date"])
    print(f"  FX data:   {len(df):>9,} rows  ({df['date'].min().date()} → {df['date'].max().date()})")
    return df


def load_fred() -> Optional[pd.DataFrame]:
    """Load FRED data. Optional — returns None if missing."""
    if not os.path.exists(FRED_FILE):
        print(f"  FRED data: not found ({FRED_FILE}) — skipping fundamentals")
        return None

    df = pd.read_csv(FRED_FILE)
    df["date"] = pd.to_datetime(df["date"])

    # Replace empty strings with NaN
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Forward-fill: monthly/event-based rates should persist until next observation
    df = df.sort_values("date")
    df = df.ffill()

    print(f"  FRED data: {len(df):>9,} rows  ({df['date'].min().date()} → {df['date'].max().date()})")
    avail = [c for c in df.columns if c != "date" and df[c].notna().sum() > 0]
    print(f"             {len(avail)} series with data: {', '.join(avail[:8])}{'...' if len(avail) > 8 else ''}")
    return df


def load_cot() -> Optional[pd.DataFrame]:
    """Load COT data. Optional — returns None if missing."""
    if not os.path.exists(COT_FILE):
        print(f"  COT data:  not found ({COT_FILE}) — skipping positioning")
        return None

    df = pd.read_csv(COT_FILE)
    df["report_date"] = pd.to_datetime(df["report_date"])

    currencies = sorted(df["currency"].unique())
    print(f"  COT data:  {len(df):>9,} rows  ({df['report_date'].min().date()} → {df['report_date'].max().date()})")
    print(f"             currencies: {', '.join(currencies)}")
    return df


# ---------------------------------------------------------------------------
# Per-pair data assembly
# ---------------------------------------------------------------------------

def prepare_pair(
    from_ccy: str,
    to_ccy: str,
    fx_df: pd.DataFrame,
    fred_df: Optional[pd.DataFrame],
    cot_df: Optional[pd.DataFrame],
) -> Optional[pd.DataFrame]:
    """
    Build a unified daily DataFrame for one currency pair.

    Columns produced:
      date, rate,
      rate_from_ir, rate_to_ir, rate_differential,    (from FRED)
      vix, usd_index, wti_crude, hy_spread, ...       (from FRED)
      cot_from_lev_net, cot_to_lev_net,               (from COT)
      cot_from_asset_net, cot_to_asset_net,            (from COT)
    """
    # Filter FX data for this pair
    pair_fx = fx_df[
        (fx_df["from_currency"] == from_ccy) & (fx_df["to_currency"] == to_ccy)
    ][["date", "rate"]].copy()

    if pair_fx.empty:
        return None

    pair_fx = pair_fx.sort_values("date").reset_index(drop=True)

    # --- Merge FRED data ---
    if fred_df is not None:
        pair_fx = pair_fx.merge(fred_df, on="date", how="left")

        # Compute interest rate differential (from - to)
        from_rate_col = CURRENCY_TO_RATE_COL.get(from_ccy)
        to_rate_col = CURRENCY_TO_RATE_COL.get(to_ccy)

        # Rename to generic names for the model
        if from_rate_col and from_rate_col in pair_fx.columns:
            pair_fx["rate_from_ir"] = pair_fx[from_rate_col]
        else:
            pair_fx["rate_from_ir"] = np.nan

        if to_rate_col and to_rate_col in pair_fx.columns:
            pair_fx["rate_to_ir"] = pair_fx[to_rate_col]
        else:
            pair_fx["rate_to_ir"] = np.nan

        pair_fx["rate_differential"] = pair_fx["rate_from_ir"] - pair_fx["rate_to_ir"]

        # Keep only the columns we need (drop raw per-country rate columns)
        keep_cols = ["date", "rate", "rate_from_ir", "rate_to_ir", "rate_differential"]
        for col in GLOBAL_FRED_COLS:
            if col in pair_fx.columns:
                keep_cols.append(col)
        pair_fx = pair_fx[keep_cols].copy()

        # Forward-fill any remaining gaps from the merge
        pair_fx = pair_fx.sort_values("date")
        for col in pair_fx.columns:
            if col not in ("date", "rate"):
                pair_fx[col] = pair_fx[col].ffill()

    # --- Merge COT data ---
    if cot_df is not None:
        # Get positioning for the "from" currency
        cot_from = cot_df[cot_df["currency"] == from_ccy][
            ["report_date", "lev_net", "asset_mgr_net", "open_interest"]
        ].rename(columns={
            "report_date": "date",
            "lev_net": "cot_from_lev_net",
            "asset_mgr_net": "cot_from_asset_net",
            "open_interest": "cot_from_oi",
        })

        if not cot_from.empty:
            pair_fx = pair_fx.merge(cot_from, on="date", how="left")
            pair_fx["cot_from_lev_net"] = pair_fx["cot_from_lev_net"].ffill()
            pair_fx["cot_from_asset_net"] = pair_fx["cot_from_asset_net"].ffill()
            pair_fx["cot_from_oi"] = pair_fx["cot_from_oi"].ffill()

        # Get positioning for the "to" currency
        cot_to = cot_df[cot_df["currency"] == to_ccy][
            ["report_date", "lev_net", "asset_mgr_net", "open_interest"]
        ].rename(columns={
            "report_date": "date",
            "lev_net": "cot_to_lev_net",
            "asset_mgr_net": "cot_to_asset_net",
            "open_interest": "cot_to_oi",
        })

        if not cot_to.empty:
            pair_fx = pair_fx.merge(cot_to, on="date", how="left")
            pair_fx["cot_to_lev_net"] = pair_fx["cot_to_lev_net"].ffill()
            pair_fx["cot_to_asset_net"] = pair_fx["cot_to_asset_net"].ffill()
            pair_fx["cot_to_oi"] = pair_fx["cot_to_oi"].ffill()

    return pair_fx


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  SendSmart — Preparing Training Data")
    print("=" * 60)
    print()

    fx_df = load_fx()
    fred_df = load_fred()
    cot_df = load_cot()

    print()
    print(f"{'─' * 60}")
    print(f"  Assembling per-pair datasets")
    print(f"{'─' * 60}")

    results = []

    for from_ccy, to_ccy in TARGET_PAIRS:
        pair_name = f"{from_ccy}_{to_ccy}"
        output_path = os.path.join(DATA_DIR, f"{pair_name}.csv")

        pair_df = prepare_pair(from_ccy, to_ccy, fx_df, fred_df, cot_df)

        if pair_df is None or pair_df.empty:
            print(f"  {pair_name:12s}  ✗ No FX data found — skipping")
            continue

        # Save
        pair_df.to_csv(output_path, index=False)

        # Summary
        n_rows = len(pair_df)
        n_cols = len(pair_df.columns)
        fundamental_cols = [c for c in pair_df.columns if c not in ("date", "rate")]
        n_fundamental = sum(1 for c in fundamental_cols if pair_df[c].notna().any())
        date_range = f"{pair_df['date'].min().date()} → {pair_df['date'].max().date()}"

        print(f"  {pair_name:12s}  ✓ {n_rows:>6,} rows  {n_cols:>2} cols  ({n_fundamental} fundamental)  {date_range}")
        results.append((pair_name, n_rows, n_cols, n_fundamental))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")

    total_pairs = len(results)
    has_fred = fred_df is not None
    has_cot = cot_df is not None

    print(f"  Pairs prepared:  {total_pairs}")
    print(f"  FRED data:       {'✓ merged' if has_fred else '✗ not available'}")
    print(f"  COT data:        {'✓ merged' if has_cot else '✗ not available'}")
    print()

    if not has_fred:
        print("  ⚠  Run `python data/fetch_fred.py` to add interest rates & VIX.")
        print("     This is the single biggest improvement for prediction accuracy.")
    if not has_cot:
        print("  ⚠  Run `python data/fetch_cot.py` to add speculative positioning.")
    print()

    print(f"  Output files (in {DATA_DIR}/):")
    for pair_name, n_rows, n_cols, n_fund in results:
        print(f"    {pair_name}.csv  ({n_rows:,} × {n_cols})")
    print()


if __name__ == "__main__":
    main()