from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Bet
from scripts.bsp_utils import calculate_bsp_metrics

def backfill_bsp_metrics():
    """Backfill BSP metrics for all existing bets"""
    db = SessionLocal()
    
    try:
        print("Starting BSP metrics backfill...")
        
        # Get all bets that have BSP data (recalculate all to fix probability)
        bets = db.query(Bet).filter(
            Bet.avg_price_matched.isnot(None),
            Bet.bsp.isnot(None)
        ).all()
        
        print(f"Found {len(bets)} bets to update")
        
        updated = 0
        for bet in bets:
            absolute_diff, percentage_diff, probability_diff = calculate_bsp_metrics(
                bet.bet_type,
                bet.avg_price_matched,
                bet.bsp
            )
            
            if absolute_diff is not None:
                bet.bsp_diff_absolute = absolute_diff
                bet.bsp_diff_percentage = percentage_diff
                bet.bsp_diff_probability = probability_diff
                updated += 1
                
                if updated % 1000 == 0:
                    db.commit()
                    print(f"  Updated {updated} bets...")
        
        db.commit()
        print(f"\nBackfill complete: {updated} bets updated")
        
    finally:
        db.close()

if __name__ == "__main__":
    backfill_bsp_metrics()
