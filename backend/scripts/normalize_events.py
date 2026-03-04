"""Normalize event names to kebab-case format"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Bet

def normalize_event_name(event_name):
    """Convert event name to kebab-case and standardize names"""
    if not event_name:
        return None
    
    # Convert to lowercase and replace spaces with hyphens
    normalized = event_name.lower().strip()
    normalized = normalized.replace(' ', '-')
    
    # Standardize soccer to football
    if normalized == 'soccer':
        normalized = 'football'
    
    return normalized

def main():
    db = SessionLocal()
    
    try:
        # Get all distinct event names
        events = db.query(Bet.event).distinct().filter(Bet.event.isnot(None)).all()
        event_names = [e[0] for e in events]
        
        print(f"Found {len(event_names)} distinct event names:")
        for event in sorted(event_names):
            print(f"  - {event}")
        
        print("\nNormalizing event names...")
        
        # Create mapping of old to new names
        mappings = {}
        for event in event_names:
            normalized = normalize_event_name(event)
            if normalized != event:
                mappings[event] = normalized
        
        if not mappings:
            print("All event names are already normalized!")
            return
        
        print(f"\nWill update {len(mappings)} event names:")
        for old, new in mappings.items():
            print(f"  '{old}' -> '{new}'")
        
        # Update each event name
        total_updated = 0
        for old_name, new_name in mappings.items():
            count = db.query(Bet).filter(Bet.event == old_name).update(
                {Bet.event: new_name},
                synchronize_session=False
            )
            total_updated += count
            print(f"  Updated {count} bets: '{old_name}' -> '{new_name}'")
        
        db.commit()
        
        print(f"\nNormalization complete! Updated {total_updated} bets.")
        
        # Show final distinct event names
        events_after = db.query(Bet.event).distinct().filter(Bet.event.isnot(None)).all()
        event_names_after = sorted([e[0] for e in events_after])
        
        print(f"\nFinal {len(event_names_after)} distinct event names:")
        for event in event_names_after:
            print(f"  - {event}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
