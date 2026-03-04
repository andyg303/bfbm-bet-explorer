import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Bet

db = SessionLocal()

# Check if BSP columns exist and have data
bet_with_bsp = db.query(Bet).filter(Bet.bsp_diff_absolute.isnot(None)).first()

if bet_with_bsp:
    print(f"Found bet with BSP metrics:")
    print(f"  Bet ID: {bet_with_bsp.bet_id}")
    print(f"  Bet Type: {bet_with_bsp.bet_type}")
    print(f"  Avg Price: {bet_with_bsp.avg_price_matched}")
    print(f"  BSP: {bet_with_bsp.bsp}")
    print(f"  BSP Diff Absolute: {bet_with_bsp.bsp_diff_absolute}")
    print(f"  BSP Diff Percentage: {bet_with_bsp.bsp_diff_percentage}")
    print(f"  BSP Diff Probability: {bet_with_bsp.bsp_diff_probability}")
else:
    print("No bets with BSP metrics found")

# Count total bets with BSP metrics
count = db.query(Bet).filter(Bet.bsp_diff_absolute.isnot(None)).count()
print(f"\nTotal bets with BSP metrics: {count}")

# Count total bets
total = db.query(Bet).count()
print(f"Total bets in database: {total}")

db.close()
