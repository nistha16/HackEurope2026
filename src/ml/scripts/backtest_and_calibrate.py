import os
import sys

# Add the parent directory (ml/) to sys.path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from train import EnsembleModel
from predictor import score_today

def run_backtest():
    print("==================================================")
    print(" Global Timing Model - Backtest & Calibration Run ")
    print("==================================================")
    
    # 1. Backtest corridors (Pairs that were likely in your training set)
    training_corridors = [
        ("EUR", "USD"), 
        ("GBP", "EUR"), 
    ]
    
    # 3. Test on unseen corridors (Generalization check - as long as data is in CSV, model handles it)
    unseen_corridors = [
        ("EUR", "MAD"), # Primary demo
        ("GBP", "INR"),
        ("AUD", "CAD") 
    ]
    
    all_corridors = training_corridors + unseen_corridors
    
    print(f"\nEvaluating {len(all_corridors)} corridors...\n")
    for src, tgt in all_corridors:
        try:
            # We call your exact production function
            res = score_today(src, tgt)
            is_unseen = (src, tgt) in unseen_corridors
            tag = "UNSEEN" if is_unseen else "TRAIN "
            
            print(f"[{tag}] {src}->{tgt} | Score: {res['timing_score']:.2f} | Action: {res['recommendation']}")
            print(f"         Reasoning: {res['reasoning']}\n")
        except FileNotFoundError:
            print(f"❌ Skipping {src}->{tgt}: Data not in historical_rates.csv")
        except Exception as e:
            print(f"❌ Error testing {src}->{tgt}: {e}")

if __name__ == "__main__":
    run_backtest()