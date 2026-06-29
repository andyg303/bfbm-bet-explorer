"""Recalculate stored commission_paid for all users."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, User
from api.commission import apply_commission_for_user


def main():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        total_processed = 0
        for user in users:
            processed = apply_commission_for_user(db, user)
            total_processed += processed
            print(f"User {user.id}: recalculated commission for {processed} bets")

        print("\nCommission recalculation complete")
        print(f"  Users: {len(users)}")
        print(f"  Bets processed: {total_processed}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
