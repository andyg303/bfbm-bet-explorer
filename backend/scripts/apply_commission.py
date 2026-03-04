"""Apply 2% commission to all winning bets in the database"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Bet

def apply_commission(profit_loss):
    """Apply 2% commission on winning bets"""
    if profit_loss is None:
        return None
    
    # Only apply commission on positive returns (winning bets)
    if profit_loss > 0:
        return profit_loss * 0.98  # Deduct 2% commission
    
    return profit_loss

def main():
    db = SessionLocal()
    
    try:
        # Get all bets with positive profit/loss
        winning_bets = db.query(Bet).filter(Bet.profit_loss > 0).all()
        
        print(f"Found {len(winning_bets)} winning bets to apply commission to")
        
        if len(winning_bets) == 0:
            print("No winning bets found!")
            return
        
        # Calculate total commission
        total_commission = 0
        updated = 0
        
        for bet in winning_bets:
            original_pl = bet.profit_loss
            new_pl = apply_commission(original_pl)
            commission = original_pl - new_pl
            total_commission += commission
            
            bet.profit_loss = new_pl
            updated += 1
            
            if updated % 1000 == 0:
                print(f"  Updated {updated} bets...")
                db.commit()
        
        db.commit()
        
        print(f"\nCommission application complete!")
        print(f"  Updated: {updated} bets")
        print(f"  Total commission deducted: £{total_commission:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
