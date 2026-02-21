#!/usr/bin/env python3
"""
Fetch historical FX rates using yfinance (Yahoo Finance).
No API key required. Highly reliable for historical data.
"""

import pandas as pd
import yfinance as yf
import os
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Majors and target bases for cross-rate generation
TARGET_BASES = ["USD", "EUR", "GBP", "AUD", "SGD", "CAD"]

# A curated list of common/stable currencies available on Yahoo Finance.
# Note: Not every exotic OXR currency is available on Yahoo, 
# but the majors and primary EM corridors are.
CURRENCIES = [
    "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "HKD", "NZD", "SEK", 
    "KRW", "SGD", "NOK", "MXN", "INR", "ZAR", "TRY", "BRL", "TWD", "DKK",
    "PLN", "THB", "IDR", "HUF", "CZK", "ILS", "CLP", "PHP", "AED", "COP",
    "SAR", "MYR", "RON", "MAD", "EGP"
]

START_DATE = "1999-01-01" 
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "historical_rates.csv")

def main():
    print(f"--- Starting Data Fetch via yfinance ---")
    
    # 1. Build Ticker List (All relative to USD for consistency)
    # Yahoo FX format is 'CURRENCY=X' for USD base, or 'USDCUR=X'
    tickers = [f"{curr}USD=X" if curr != "USD" else None for curr in CURRENCIES]
    tickers = [t for t in tickers if t] # Clean list
    
    print(f"Downloading data for {len(tickers)} pairs starting from {START_DATE}...")
    
    # 2. Download from Yahoo Finance
    # We download 'Close' prices which represent the daily rate
    data = yf.download(tickers, start=START_DATE, interval="1d")["Close"]
    
    # Handle the case where a single ticker might return a Series instead of DataFrame
    if isinstance(data, pd.Series):
        data = data.to_frame()

    # 3. Process and Generate Cross Rates
    print("Processing cross-rates...")
    all_rows = []
    
    # Iterate through days
    for timestamp, rates in data.iterrows():
        date_str = timestamp.strftime('%Y-%m-%d')
        
        # We need everything relative to USD = 1.0
        # Yahoo gives us [Currency]USD=X, so Rate = 1 / YahooValue gives us USD/[Currency]
        usd_rates = {"USD": 1.0}
        for ticker, val in rates.items():
            curr = ticker.replace("USD=X", "")
            if pd.notna(val) and val != 0:
                # Yahoo gives: 1 [Curr] = X [USD]. 
                # To get 1 USD = Y [Curr], we do 1/X.
                usd_rates[curr] = 1.0 / val

        # Generate the corridors
        for base in TARGET_BASES:
            if base not in usd_rates: continue
            
            for target in CURRENCIES:
                if base == target or target not in usd_rates: continue
                
                # Math: (USD/Target) / (USD/Base) = Base/Target
                rate = usd_rates[target] / usd_rates[base]
                
                all_rows.append({
                    "date": date_str,
                    "from_currency": base,
                    "to_currency": target,
                    "rate": round(rate, 6)
                })

    # 4. Save to CSV
    df_out = pd.DataFrame(all_rows)
    df_out.sort_values(["date", "from_currency", "to_currency"], inplace=True)
    df_out.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✓ Success! Saved {len(df_out):,} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()