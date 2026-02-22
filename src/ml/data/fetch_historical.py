#!/usr/bin/env python3
"""
Fetch 25+ years of daily FX rates from the Frankfurter API and save to CSV.

The Frankfurter API serves ECB reference rates, so only ECB-tracked currencies
are available. We fetch in yearly chunks and concatenate into a single CSV.

Usage:
    python data/fetch_historical.py
    # Outputs: data/historical_rates.csv

API docs: https://frankfurter.dev/
  - Base URL: https://api.frankfurter.dev/v1/
  - Time series: GET /v1/{start}..{end}?base=EUR&symbols=USD
  - Params: base (source currency), symbols (target currencies)
  - Supported currencies: AUD, BRL, CAD, CHF, CNY, CZK, DKK, EUR, GBP, HKD,
    HUF, IDR, ILS, INR, ISK, JPY, KRW, MXN, MYR, NOK, NZD, PHP, PLN, RON,
    SEK, SGD, THB, TRY, USD, ZAR

NOTE: Some corridors used in the FiberTransfer app (EUR/MAD, EUR/NGN, GBP/PKR,
EUR/BDT, EUR/EGP, EUR/KES, GBP/GHS) are NOT available on Frankfurter because
those currencies are not published by the ECB. For ML training we fetch all
available corridors that overlap with the app's provider data, plus extra
high-volume pairs for better model generalisation.
"""

import csv
import os
import sys
import time
from datetime import date, timedelta
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

import urllib.request
import json

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://api.frankfurter.dev/v1"

# ECB-supported currencies (as of 2025)
SUPPORTED_CURRENCIES = frozenset({
    "AUD", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP", "HKD",
    "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PLN", "RON", "SEK", "SGD", "THB", "TRY", "USD", "ZAR",
})

# Corridors to fetch. All currencies MUST be in SUPPORTED_CURRENCIES.
# Includes:
#   - App corridors that Frankfurter supports: EUR/USD, GBP/INR, USD/PHP,
#     USD/MXN, USD/BRL
#   - Extra high-volume pairs for ML training coverage
CORRIDORS: dict[str, list[str]] = {
    "EUR": ["USD", "GBP", "JPY", "CHF", "TRY", "PLN", "SEK", "INR", "BRL", "ZAR", "CNY", "MXN"],
    "GBP": ["INR", "USD", "JPY", "ZAR"],
    "USD": ["PHP", "MXN", "BRL", "JPY", "INR", "TRY", "THB", "IDR", "ZAR", "KRW"],
}

START_DATE = date(1999, 1, 4)  # Frankfurter data starts here (ECB reference rates)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "historical_rates.csv")

# Frankfurter can handle ~1 year per request reliably
CHUNK_DAYS = 365

# Be polite — pause between requests
REQUEST_DELAY = 0.3  # seconds


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_corridors() -> None:
    """Raise if any configured corridor uses an unsupported currency."""
    errors: list[str] = []
    for base, targets in CORRIDORS.items():
        if base not in SUPPORTED_CURRENCIES:
            errors.append(f"Base currency '{base}' is not supported by Frankfurter")
        for target in targets:
            if target not in SUPPORTED_CURRENCIES:
                errors.append(f"Target currency '{target}' (in {base} corridors) is not supported by Frankfurter")
            if base == target:
                errors.append(f"Base and target are the same: {base}/{target}")
    if errors:
        raise ValueError("Invalid corridor configuration:\n  " + "\n  ".join(errors))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, retries: int = 3) -> Optional[dict]:
    """Fetch JSON from a URL with retries."""
    for attempt in range(retries):
        try:
            if httpx is not None:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    return resp.json()
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "fibertransfer-fetcher/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode())
        except Exception as exc:
            print(f"  [attempt {attempt + 1}/{retries}] Error fetching {url}: {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
    return None


def _build_timeseries_url(from_currency: str, to_currency: str, start: date, end: date) -> str:
    """
    Build a Frankfurter time-series URL.

    Format: /v1/{start}..{end}?base={from}&symbols={to}
    """
    return (
        f"{BASE_URL}/{start.isoformat()}..{end.isoformat()}"
        f"?base={from_currency}&symbols={to_currency}"
    )


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------

def fetch_corridor(
    from_currency: str,
    to_currency: str,
    start: date,
    end: date,
) -> list[dict]:
    """
    Fetch historical rates for a single corridor in yearly chunks.

    Returns a list of dicts: {"date": str, "from_currency": str, "to_currency": str, "rate": float}
    """
    rows: list[dict] = []
    chunk_start = start

    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), end)
        url = _build_timeseries_url(from_currency, to_currency, chunk_start, chunk_end)
        print(f"  Fetching {from_currency}/{to_currency} "
              f"{chunk_start.isoformat()} → {chunk_end.isoformat()} ...")

        data = _fetch_json(url)
        if data and "rates" in data:
            for rate_date, rate_map in data["rates"].items():
                rate_value = rate_map.get(to_currency)
                if rate_value is not None:
                    rows.append({
                        "date": rate_date,
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "rate": rate_value,
                    })
        else:
            print(f"  ⚠ No data returned for chunk {chunk_start} → {chunk_end}")

        chunk_start = chunk_end + timedelta(days=1)
        time.sleep(REQUEST_DELAY)

    return rows


def main():
    validate_corridors()

    today = date.today()
    all_rows: list[dict] = []

    total_corridors = sum(len(targets) for targets in CORRIDORS.values())
    current = 0

    for from_currency, to_currencies in CORRIDORS.items():
        for to_currency in to_currencies:
            current += 1
            print(f"\n[{current}/{total_corridors}] {from_currency} → {to_currency}")
            rows = fetch_corridor(from_currency, to_currency, START_DATE, today)
            all_rows.extend(rows)
            print(f"  ✓ {len(rows):,} data points")

    if not all_rows:
        print("\n✗ No data fetched. Check your network connection.")
        sys.exit(1)

    # Sort by date, then corridor
    all_rows.sort(key=lambda r: (r["date"], r["from_currency"], r["to_currency"]))

    # Write CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "from_currency", "to_currency", "rate"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✓ Saved {len(all_rows):,} rows to {OUTPUT_FILE}")

    # Print summary
    corridors_found = set()
    date_range = {"min": "9999-99-99", "max": "0000-00-00"}
    for row in all_rows:
        corridors_found.add(f"{row['from_currency']}/{row['to_currency']}")
        if row["date"] < date_range["min"]:
            date_range["min"] = row["date"]
        if row["date"] > date_range["max"]:
            date_range["max"] = row["date"]

    print(f"  Date range: {date_range['min']} → {date_range['max']}")
    print(f"  Corridors:  {', '.join(sorted(corridors_found))}")


if __name__ == "__main__":
    main()