#!/usr/bin/env python3
"""
Fetch CFTC Commitments of Traders (COT) data for currency futures.

The COT report shows how different trader categories are positioned in
futures markets.  For FX prediction, the key signal is:

  **Net speculative positioning** (Leveraged Money net longs)
  - When speculators are extremely long a currency → contrarian bearish signal
  - When speculators are extremely short → contrarian bullish signal
  - Week-over-week changes in positioning signal shifting sentiment

This is a documented and widely-used FX predictor that is NOT captured by
price history alone.

Data source: CFTC Disaggregated Futures-Only Reports
  - Historical bulk downloads (annual ZIP files of CSV)
  - URL: https://www.cftc.gov/files/dea/history/fut_disagg_txt_{YEAR}.zip
  - Updated weekly (Tuesday report date, released Friday)
  - Available from 2006 onward in disaggregated format

CME currency futures mapped to ISO codes:
  - "EURO FX"           → EUR
  - "BRITISH POUND"     → GBP
  - "JAPANESE YEN"      → JPY
  - "SWISS FRANC"       → CHF
  - "CANADIAN DOLLAR"   → CAD
  - "AUSTRALIAN DOLLAR" → AUD
  - "MEXICAN PESO"      → MXN
  - "NEW ZEALAND DOLLAR"→ NZD
  - "BRAZILIAN REAL"     → BRL
  - "SO AFRICAN RAND"   → ZAR
  - "U.S. DOLLAR INDEX" → USD (ICE, not CME)

Setup:
  No API key needed — CFTC data is freely downloadable.
  Run:  python data/fetch_cot.py

Output: data/cot_data.csv
  Columns: report_date, currency, lev_long, lev_short, lev_net,
           asset_mgr_long, asset_mgr_short, asset_mgr_net,
           dealer_long, dealer_short, dealer_net, open_interest
"""

import csv
import io
import os
import sys
import time
import urllib.request
import zipfile
from datetime import date
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# CFTC disaggregated futures report (includes financial futures with
# Dealer, Asset Manager, Leveraged Money breakdowns)
CFTC_URL_TEMPLATE = (
    "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
)

# Map CME/ICE contract names (as they appear in CFTC data) to ISO currency codes.
# The CFTC name field contains the exchange, so we match on substrings.
CONTRACT_TO_CURRENCY: dict[str, str] = {
    "EURO FX": "EUR",
    "BRITISH POUND": "GBP",
    "JAPANESE YEN": "JPY",
    "SWISS FRANC": "CHF",
    "CANADIAN DOLLAR": "CAD",
    "AUSTRALIAN DOLLAR": "AUD",
    "MEXICAN PESO": "MXN",
    "NEW ZEALAND DOLLAR": "NZD",
    "BRAZILIAN REAL": "BRL",
    "SO AFRICAN RAND": "ZAR",
    "U.S. DOLLAR INDEX": "USD",
    "RUSSIAN RUBLE": "RUB",
}

# We need these columns from the CFTC CSV (column names vary slightly by year)
# Disaggregated report column name patterns:
#   Dealer_Positions_Long_All, Dealer_Positions_Short_All
#   Asset_Mgr_Positions_Long_All, Asset_Mgr_Positions_Short_All
#   Lev_Money_Positions_Long_All, Lev_Money_Positions_Short_All
#   Open_Interest_All

START_YEAR = 2006   # Disaggregated format starts here
REQUEST_DELAY = 1.0  # Be polite to CFTC servers

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cot_data.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download_zip(url: str, retries: int = 3) -> Optional[bytes]:
    """Download a ZIP file, return raw bytes."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sendsmart-cot/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except Exception as exc:
            print(f"  [attempt {attempt + 1}/{retries}] Error: {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def _identify_currency(market_name: str) -> Optional[str]:
    """Extract currency code from the CFTC market name field."""
    upper = market_name.upper()
    for contract_substr, currency in CONTRACT_TO_CURRENCY.items():
        if contract_substr in upper:
            return currency
    return None


def _find_column(headers: list[str], patterns: list[str]) -> Optional[int]:
    """Find the index of a column matching any of the given patterns (case-insensitive)."""
    for i, h in enumerate(headers):
        h_lower = h.strip().lower().replace(" ", "_")
        for p in patterns:
            if p.lower().replace(" ", "_") in h_lower:
                return i
    return None


def _safe_int(val: str) -> int:
    """Parse an integer from a CSV value, handling commas and whitespace."""
    try:
        return int(val.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return 0


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------

def parse_cot_csv(csv_text: str) -> list[dict]:
    """
    Parse a CFTC disaggregated CSV and extract currency futures positioning.

    Returns list of dicts with standardised column names.
    """
    reader = csv.reader(io.StringIO(csv_text))
    headers = next(reader)

    # Find required column indices (CFTC column names can vary slightly)
    col_market = _find_column(headers, ["market_and_exchange_names", "market and exchange names"])
    col_date = _find_column(headers, ["report_date_as_yyyy-mm-dd", "report_date_as_yyyy_mm_dd", "as_of_date_in_form_yyyy-mm-dd"])
    col_oi = _find_column(headers, ["open_interest_all", "open interest (all)"])
    col_dealer_long = _find_column(headers, ["dealer_positions_long_all", "dealer positions long (all)"])
    col_dealer_short = _find_column(headers, ["dealer_positions_short_all", "dealer positions short (all)"])
    col_asset_long = _find_column(headers, ["asset_mgr_positions_long_all", "asset mgr positions long (all)"])
    col_asset_short = _find_column(headers, ["asset_mgr_positions_short_all", "asset mgr positions short (all)"])
    col_lev_long = _find_column(headers, ["lev_money_positions_long_all", "lev money positions long (all)"])
    col_lev_short = _find_column(headers, ["lev_money_positions_short_all", "lev money positions short (all)"])

    if col_market is None or col_date is None:
        print(f"  ⚠ Could not find market/date columns. Headers: {headers[:5]}...")
        return []

    rows = []
    for line in reader:
        if len(line) <= max(col_market, col_date):
            continue

        currency = _identify_currency(line[col_market])
        if currency is None:
            continue  # Not a currency futures contract

        report_date = line[col_date].strip()
        if not report_date or len(report_date) < 10:
            continue

        lev_long = _safe_int(line[col_lev_long]) if col_lev_long is not None else 0
        lev_short = _safe_int(line[col_lev_short]) if col_lev_short is not None else 0
        asset_long = _safe_int(line[col_asset_long]) if col_asset_long is not None else 0
        asset_short = _safe_int(line[col_asset_short]) if col_asset_short is not None else 0
        dealer_long = _safe_int(line[col_dealer_long]) if col_dealer_long is not None else 0
        dealer_short = _safe_int(line[col_dealer_short]) if col_dealer_short is not None else 0
        oi = _safe_int(line[col_oi]) if col_oi is not None else 0

        rows.append({
            "report_date": report_date,
            "currency": currency,
            "lev_long": lev_long,
            "lev_short": lev_short,
            "lev_net": lev_long - lev_short,
            "asset_mgr_long": asset_long,
            "asset_mgr_short": asset_short,
            "asset_mgr_net": asset_long - asset_short,
            "dealer_long": dealer_long,
            "dealer_short": dealer_short,
            "dealer_net": dealer_long - dealer_short,
            "open_interest": oi,
        })

    return rows


def fetch_year(year: int) -> list[dict]:
    """Fetch and parse COT data for a single year."""
    url = CFTC_URL_TEMPLATE.format(year=year)
    print(f"  Downloading {year}...")

    zip_bytes = _download_zip(url)
    if zip_bytes is None:
        print(f"  ⚠ Failed to download {year}")
        return []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # The ZIP typically contains a single .txt file
            txt_names = [n for n in zf.namelist() if n.endswith(".txt")]
            if not txt_names:
                print(f"  ⚠ No .txt file found in ZIP for {year}")
                return []

            csv_text = zf.read(txt_names[0]).decode("utf-8", errors="replace")
            rows = parse_cot_csv(csv_text)
            return rows
    except Exception as exc:
        print(f"  ⚠ Error parsing {year}: {exc}")
        return []


def main():
    print("=" * 60)
    print("  SendSmart — Fetching CFTC COT Data")
    print("=" * 60)

    current_year = date.today().year
    all_rows: list[dict] = []

    for year in range(START_YEAR, current_year + 1):
        rows = fetch_year(year)
        all_rows.extend(rows)
        if rows:
            currencies = set(r["currency"] for r in rows)
            print(f"  ✓ {len(rows):,} rows — currencies: {', '.join(sorted(currencies))}")
        time.sleep(REQUEST_DELAY)

    if not all_rows:
        print("\n✗ No COT data fetched. Check your network connection.")
        sys.exit(1)

    # Sort by date then currency
    all_rows.sort(key=lambda r: (r["report_date"], r["currency"]))

    # Write CSV
    fieldnames = [
        "report_date", "currency",
        "lev_long", "lev_short", "lev_net",
        "asset_mgr_long", "asset_mgr_short", "asset_mgr_net",
        "dealer_long", "dealer_short", "dealer_net",
        "open_interest",
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary
    currencies_found = set(r["currency"] for r in all_rows)
    date_range = (all_rows[0]["report_date"], all_rows[-1]["report_date"])

    print(f"\n{'=' * 60}")
    print(f"  Saved {len(all_rows):,} rows to {OUTPUT_FILE}")
    print(f"  Date range: {date_range[0]} → {date_range[1]}")
    print(f"  Currencies: {', '.join(sorted(currencies_found))}")

    # Per-currency counts
    from collections import Counter
    counts = Counter(r["currency"] for r in all_rows)
    print(f"\n  Per-currency report counts:")
    for ccy, n in sorted(counts.items()):
        print(f"    {ccy:5s}  {n:>5,} weekly reports")
    print()


if __name__ == "__main__":
    main()