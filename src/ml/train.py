"""To train our predictor on historical data"""

import os
from predictor import train_and_evaluate

# Assuming fetch_historical.py dumps CSVs into src/ml/data/
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def main():
    target_pairs = ['EUR_CHF', 'EUR_USD', 'GBP_INR']
    
    print("Starting ML Pipeline Training...\n")
    
    for pair in target_pairs:
        csv_path = os.path.join(DATA_DIR, f"{pair}.csv")
        
        if not os.path.exists(csv_path):
            print(f"[!] Skipping {pair}: Historical data CSV not found at {csv_path}")
            continue
            
        print(f"[*] Training models for {pair}...")
        metrics = train_and_evaluate(csv_path, pair)
        
        print(f"    Metrics (24h prediction):")
        print(f"    - R²:   {metrics['r2']:.4f}")
        print(f"    - MAE:  {metrics['mae']:.5f}")
        print(f"    - RMSE: {metrics['rmse']:.5f}")
        
        if metrics['r2'] > 0.85:
            print("    -> SUCCESS: R² score exceeds 0.85 acceptance criteria.\n")
        else:
            print("    -> WARNING: R² score is below 0.85. Consider tuning.\n")

if __name__ == "__main__":
    main()