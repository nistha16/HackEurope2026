#!/usr/bin/env python3
"""
Fetch macroeconomic and financial data from the FRED API.

FRED (Federal Reserve Economic Data) provides free access to hundreds of
thousands of economic time series.  We fetch the series most relevant to
FX rate prediction:

  1. US interest rates & yields (daily)
     - Federal Funds Rate, 2Y/10Y Treasury yields, yield curve slope
  2. ECB & non-US central bank rates (event-based or monthly)
     - Forward-filled to daily frequency in prepare_training_data.py
  3. Market sentiment indicators (daily)
     - VIX, trade-weighted dollar index, oil, high-yield spread

Why these matter for FX:
  - Interest rate differentials are the #1 documented FX predictor
    (carry trade: capital flows toward higher-yielding currencies)
  - VIX measures risk appetite — drives safe-haven flows (USD, CHF, JPY)
  - Dollar index captures broad USD strength independent of any single pair
  - Oil prices affect commodity currencies (MXN, BRL, ZAR, NOK)
  - High-yield spread proxies credit stress / risk-off sentiment

Setup:
  1. Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
  2. Set environment variable:  export FRED_API_KEY=your_key_here
  3. Run:  python data/fetch_fred.py

Output: data/fred_data.csv
  Columns: date, fed_funds_rate, us_2y_yield, us_10y_yield, us_yield_spread,
           ecb_deposit_rate, uk_rate, jp_rate, ch_rate, tr_rate, mx_rate,
           in_rate, vix, usd_index, wti_crude, hy_spread
"""

import csv
import json
import os
import sys
import time
import urllib.request
from datetime import date, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# {FRED series ID: output column name}
# Grouped by category for documentation; all fetched the same way.
SERIES: dict[str, str] = {
    # ── US monetary policy & yields (daily) ──────────────────────────────
    "DFF": "fed_funds_rate",          # Federal Funds Effective Rate
    "DGS2": "us_2y_yield",           # 2-Year Treasury Constant Maturity
    "DGS10": "us_10y_yield",         # 10-Year Treasury Constant Maturity
    "T10Y2Y": "us_yield_spread",     # 10-Year minus 2-Year Spread

    # ── ECB rate (changes ~8x/year — forward-fill in prepare step) ───────
    "ECBDFR": "ecb_deposit_rate",    # ECB Deposit Facility Rate

    # ── Non-US short-term rates (monthly OECD MEI series on FRED) ────────
    # These are Immediate Rates / Short-term rates from OECD via FRED.
    # Monthly frequency — forward-filled to daily in prepare step.
    "IR3TIB01GBM156N": "uk_rate",    # UK 3-Month Interbank Rate
    "IR3TIB01JPM156N": "jp_rate",    # Japan 3-Month Interbank Rate
    "IR3TIB01CHM156N": "ch_rate",    # Switzerland 3-Month Rate
    "INTDSRTRM193N": "tr_rate",      # Turkey Central Bank Discount Rate
    "IR3TIB01MXM156N": "mx_rate",    # Mexico 3-Month Rate
    "IR3TIB01INM156N": "in_rate",    # India 3-Month Rate

    # ── Market sentiment (daily) ─────────────────────────────────────────
    "VIXCLS": "vix",                 # CBOE Volatility Index
    "DTWEXBGS": "usd_index",         # Trade-Weighted USD Index (Broad)
    "DCOILWTICO": "wti_crude",       # WTI Crude Oil ($/barrel)
    "BAMLH0A0HYM2": "hy_spread",    # ICE BofA US High Yield OAS
}

START_DATE = "1999-01-01"  # Match FX data start
REQUEST_DELAY = 0.25       # Seconds between requests (FRED rate limit: 120/min)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fred_data.csv")


# ---------------------------------------------------------------------------
# HTTP helpers (same pattern as fetch_historical.py)
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Read FRED API key from environment."""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        print("ERROR: FRED_API_KEY environment variable is not set.")
        print("Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("Then:  export FRED_API_KEY=your_key_here")
        sys.exit(1)
    return key


def _fetch_json(url: str, retries: int = 3) -> Optional[dict]:
    """Fetch JSON with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sendsmart-fred/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            print(f"  [attempt {attempt + 1}/{retries}] Error: {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------

def fetch_series(
    series_id: str,
    api_key: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """
    Fetch a single FRED series.

    Returns list of {date, value} dicts.  FRED returns "." for missing values
    (weekends, holidays) — these are skipped.
    """
    url = (
        f"{FRED_BASE_URL}"
        f"?series_id={series_id}"
        f"&api_key={api_key}"
        f"&file_type=json"
        f"&observation_start={start_date}"
        f"&observation_end={end_date}"
    )

    data = _fetch_json(url)
    if not data or "observations" not in data:
        return []

    rows = []
    for obs in data["observations"]:
        val_str = obs.get("value", ".")
        if val_str == "." or val_str == "":
            continue  # Missing observation
        try:
            rows.append({
                "date": obs["date"],
                "value": float(val_str),
            })
        except (ValueError, KeyError):
            continue

    return rows


def main():
    api_key = _get_api_key()
    today = date.today().isoformat()

    print("=" * 60)
    print("  SendSmart — Fetching FRED Data")
    print("=" * 60)

    # Fetch each series and store in a dict: {column_name: {date: value}}
    all_data: dict[str, dict[str, float]] = {}
    all_dates: set[str] = set()

    total = len(SERIES)
    for i, (series_id, col_name) in enumerate(SERIES.items(), 1):
        print(f"\n[{i}/{total}] {series_id} → {col_name}")
        rows = fetch_series(series_id, api_key, START_DATE, today)

        if not rows:
            print(f"  ⚠ No data returned (series may not exist or require different access)")
            all_data[col_name] = {}
            continue

        date_val = {r["date"]: r["value"] for r in rows}
        all_data[col_name] = date_val
        all_dates.update(date_val.keys())
        print(f"  ✓ {len(rows):,} observations ({rows[0]['date']} → {rows[-1]['date']})")

        time.sleep(REQUEST_DELAY)

    if not all_dates:
        print("\n✗ No data fetched. Check your API key and network.")
        sys.exit(1)

    # Build wide-format CSV: one row per date, one column per series
    sorted_dates = sorted(all_dates)
    col_names = list(SERIES.values())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date"] + col_names)

        for d in sorted_dates:
            row = [d]
            for col in col_names:
                val = all_data.get(col, {}).get(d, "")
                row.append(val)
            writer.writerow(row)

    # Count non-empty cells per column
    print(f"\n{'=' * 60}")
    print(f"  Saved {len(sorted_dates):,} dates to {OUTPUT_FILE}")
    print(f"  Date range: {sorted_dates[0]} → {sorted_dates[-1]}")
    print(f"\n  Column coverage:")
    for col in col_names:
        count = len(all_data.get(col, {}))
        print(f"    {col:25s} {count:>7,} observations")
    print()


if __name__ == "__main__":
    main()