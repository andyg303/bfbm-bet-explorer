import pandas as pd
import re
from sqlalchemy.orm import Session
from datetime import datetime
import os
import glob
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db, Bet
from scripts.bsp_utils import calculate_bsp_metrics

def sanitize_currency(value):
    """Remove currency symbols and convert to float"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    value_str = str(value)
    value_str = re.sub(r'[£$€\s,]', '', value_str)
    
    try:
        return float(value_str)
    except ValueError:
        return None

def normalize_event_name(event_name):
    """Convert event name to kebab-case format and standardize names"""
    if pd.isna(event_name) or not event_name:
        return None
    
    # Convert to lowercase and replace spaces with hyphens
    normalized = str(event_name).lower().strip()
    normalized = normalized.replace(' ', '-')
    
    # Standardize soccer to football
    if normalized == 'soccer':
        normalized = 'football'
    
    return normalized

def apply_commission(profit_loss):
    """Apply 2% commission on winning bets"""
    if profit_loss is None:
        return None
    
    # Only apply commission on positive returns (winning bets)
    if profit_loss > 0:
        return profit_loss * 0.98  # Deduct 2% commission
    
    return profit_loss

def calculate_lay_liability(row):
    """Calculate actual liability for lay bets"""
    if row['bet_type'] == 'LAY' and row['matched_amount'] and row['avg_price_matched']:
        return (row['avg_price_matched'] - 1) * row['matched_amount']
    return None

def parse_datetime(value):
    """Parse datetime strings"""
    if pd.isna(value):
        return None
    try:
        dt = pd.to_datetime(value)
        if pd.isna(dt):
            return None
        return dt
    except:
        return None

def ingest_csv_file(filepath: str, db: Session):
    """Ingest a single CSV file into the database"""
    print(f"Processing {filepath}...")
    
    df = pd.read_csv(filepath, encoding='latin-1')
    
    print(f"Found {len(df)} rows")
    
    df['Matched amount'] = df['Matched amount'].apply(sanitize_currency)
    df['Loss rec. amount'] = df['Loss rec. amount'].apply(sanitize_currency)
    df['P/L'] = df['P/L'].apply(sanitize_currency)
    df['Total matched on runner'] = df['Total matched on runner'].apply(sanitize_currency)
    df['Total matched on market'] = df['Total matched on market'].apply(sanitize_currency)
    
    df['Placed date'] = df['Placed date'].apply(parse_datetime)
    df['Matched date'] = df['Matched date'].apply(parse_datetime)
    df['Settled date'] = df['Settled date'].apply(parse_datetime)
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        status = str(row['Status']) if pd.notna(row['Status']) else None
        # Skip bets that are not MATCHED or SETTLED (excludes VOIDED, CANCELLED, etc.)
        if status not in ['MATCHED', 'SETTLED']:
            skipped += 1
            continue
        
        bet_id = str(row['Bet Id'])
        existing = db.query(Bet).filter(Bet.bet_id == bet_id).first()
        
        lay_liability = None
        if row['Bet type'] == 'LAY' and pd.notna(row['Matched amount']) and pd.notna(row['Avg. price matched']):
            lay_liability = (row['Avg. price matched'] - 1) * row['Matched amount']
        
        placed_date = row['Placed date'] if pd.notna(row['Placed date']) else None
        matched_date = row['Matched date'] if pd.notna(row['Matched date']) else None
        settled_date = row['Settled date'] if pd.notna(row['Settled date']) else None
        
        # Calculate BSP metrics
        bet_type = str(row['Bet type']) if pd.notna(row['Bet type']) else None
        avg_price = float(row['Avg. price matched']) if pd.notna(row['Avg. price matched']) else None
        bsp = float(row['BSP']) if pd.notna(row['BSP']) else None
        
        bsp_abs, bsp_pct, bsp_prob = calculate_bsp_metrics(bet_type, avg_price, bsp)
        
        # Apply commission to profit/loss
        raw_pl = row['P/L']
        profit_loss_with_commission = apply_commission(raw_pl)
        
        # Prepare bet data
        bet_data = {
            'bet_id': bet_id,
            'event': normalize_event_name(row['Event']),
            'country_code': str(row['Country code']) if pd.notna(row['Country code']) else None,
            'competition': str(row['Competition']) if pd.notna(row['Competition']) else None,
            'favorite_position': int(row['Favorite position']) if pd.notna(row['Favorite position']) else None,
            'description': str(row['Description']) if pd.notna(row['Description']) else None,
            'selection': str(row['Selection']) if pd.notna(row['Selection']) else None,
            'bet_type': str(row['Bet type']) if pd.notna(row['Bet type']) else None,
            'matched_amount': row['Matched amount'],
            'loss_rec_amount': row['Loss rec. amount'],
            'avg_price_matched': float(row['Avg. price matched']) if pd.notna(row['Avg. price matched']) else None,
            'price_requested': float(row['Price requested']) if pd.notna(row['Price requested']) else None,
            'status': str(row['Status']) if pd.notna(row['Status']) else None,
            'profit_loss': profit_loss_with_commission,
            'strategy': str(row['Strategy']) if pd.notna(row['Strategy']) else None,
            'bsp': float(row['BSP']) if pd.notna(row['BSP']) else None,
            'total_matched_on_runner': row['Total matched on runner'],
            'total_matched_on_market': row['Total matched on market'],
            'short_description': str(row['Short description']) if pd.notna(row['Short description']) else None,
            'tipster': str(row['Tipster']) if pd.notna(row['Tipster']) else None,
            'placed_date': placed_date,
            'matched_date': matched_date,
            'settled_date': settled_date,
            'number_of_selections': int(row['Number of selections']) if pd.notna(row['Number of selections']) else None,
            'market_type': str(row['Market type']) if pd.notna(row['Market type']) else None,
            'lay_liability': lay_liability,
            'bsp_diff_absolute': bsp_abs,
            'bsp_diff_percentage': bsp_pct,
            'bsp_diff_probability': bsp_prob
        }
        
        if existing:
            # Update existing bet
            for key, value in bet_data.items():
                if key != 'bet_id':  # Don't update the primary key
                    setattr(existing, key, value)
            updated += 1
        else:
            # Insert new bet
            bet = Bet(**bet_data)
            db.add(bet)
            inserted += 1
        
        db.commit()
        
        if (inserted + updated) % 100 == 0:
            print(f"  Processed {inserted + updated} rows...")
    
    print(f"Completed: {inserted} inserted, {updated} updated, {skipped} skipped (invalid status)")

def main():
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        csv_files = glob.glob("../*.csv")
        
        if not csv_files:
            print("No CSV files found in parent directory")
            return
        
        print(f"Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            ingest_csv_file(csv_file, db)
        
        total_bets = db.query(Bet).count()
        print(f"\nTotal bets in database: {total_bets}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
