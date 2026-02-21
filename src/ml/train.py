"""To train our predictor on historical data"""

import os, sys

# Add the parent directory to sys.path so we can import custom modules."""
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from predictor import train_and_evaluate

# Assuming fetch_historical.py dumps CSVs into src/ml/data/
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def main():
    target_pairs = ['EUR_CHF', 'EUR_USD', 'GBP_INR']
    csv_path = os.path.join(DATA_DIR, 'historical_rates.csv')
    
    print("Starting ML Pipeline Training...\n")
    
    if not os.path.exists(csv_path):
        print(f"[!] Critical Error: Historical data CSV not found at {csv_path}")
        return
        
    for pair in target_pairs:
        print(f"[*] Training models for {pair}...")
        try:
            metrics = train_and_evaluate(csv_path, pair)
            
            print(f"    Metrics (24h prediction):")
            print(f"    - R²:   {metrics['r2']:.4f}")
            print(f"    - MAE:  {metrics['mae']:.5f}")
            print(f"    - RMSE: {metrics['rmse']:.5f}")
            
            if metrics['r2'] > 0.85:
                print("    -> SUCCESS: R² score exceeds 0.85 acceptance criteria.\n")
            else:
                print("    -> WARNING: R² score is below 0.85. Consider tuning.\n")
        except Exception as e:
            print(f"    -> ERROR processing {pair}: {e}\n")

if __name__ == "__main__":
    main()