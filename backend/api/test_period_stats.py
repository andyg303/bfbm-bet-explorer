import os
import sys
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Bet, User
from api.main import FilterParams, get_period_stats


class PeriodStatsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(id=1, email="test@example.com", password_hash="hash", subscription_status="active")
        self.other_user = User(id=2, email="other@example.com", password_hash="hash", subscription_status="active")
        self.db.add_all([self.user, self.other_user])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def add_bet(self, bet_id: int, *, start_time: datetime, pl: float,
                strategy: str = "Alpha", user_id: int = 1, commission: float = 0.0):
        bet = Bet(
            id=bet_id,
            user_id=user_id,
            bet_id=f"bet-{user_id}-{bet_id}",
            strategy=strategy,
            start_time=start_time,
            bet_type="BACK",
            status="WON" if pl > 0 else "LOST",
            matched_amount=10.0,
            avg_price_matched=2.0,
            profit_loss=pl,
            commission_paid=commission,
            is_archived=False,
            is_deleted=False,
        )
        self.db.add(bet)
        self.db.commit()
        return bet

    def seed_bets(self):
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # One bet each: today, yesterday, 3d ago, 15d ago, 45d ago
        self.add_bet(1, start_time=now, pl=10.0, commission=0.2)
        self.add_bet(2, start_time=today - timedelta(hours=6), pl=-10.0)
        self.add_bet(3, start_time=today - timedelta(days=3), pl=20.0, commission=0.4)
        self.add_bet(4, start_time=today - timedelta(days=15), pl=-10.0)
        self.add_bet(5, start_time=today - timedelta(days=45), pl=50.0)
        # Another user's bet today — must never leak in
        self.add_bet(6, start_time=now, pl=999.0, user_id=2)

    def test_period_buckets(self):
        self.seed_bets()
        result = get_period_stats(FilterParams(), self.user, self.db)

        self.assertEqual(result["today"]["num_bets"], 1)
        self.assertEqual(result["today"]["net_pl"], 9.8)

        self.assertEqual(result["yesterday"]["num_bets"], 1)
        self.assertEqual(result["yesterday"]["net_pl"], -10.0)

        # last 7 days = today + yesterday + the 3-day-old bet
        self.assertEqual(result["last_7_days"]["num_bets"], 3)
        self.assertEqual(result["last_7_days"]["net_pl"], 19.4)

        # last 30 days adds the 15-day-old bet but not the 45-day-old one
        self.assertEqual(result["last_30_days"]["num_bets"], 4)
        self.assertEqual(result["last_30_days"]["net_pl"], 9.4)

        for key in ("today", "yesterday", "last_7_days", "last_30_days"):
            self.assertEqual(result[key]["num_strategies"], 1)

    def test_empty_periods_return_zeroes(self):
        result = get_period_stats(FilterParams(), self.user, self.db)
        for key in ("today", "yesterday", "last_7_days", "last_30_days"):
            self.assertEqual(result[key]["num_bets"], 0)
            self.assertEqual(result[key]["net_pl"], 0)
            self.assertEqual(result[key]["num_strategies"], 0)

    def test_window_intersects_existing_date_filters(self):
        self.seed_bets()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # User date_from of yesterday narrows last_7_days to today+yesterday
        f = FilterParams(date_from=(today - timedelta(days=1)).isoformat())
        result = get_period_stats(f, self.user, self.db)
        self.assertEqual(result["last_7_days"]["num_bets"], 2)

        # User date_to of 40 days ago excludes everything recent
        f = FilterParams(date_to=(today - timedelta(days=40)).isoformat())
        result = get_period_stats(f, self.user, self.db)
        self.assertEqual(result["today"]["num_bets"], 0)
        self.assertEqual(result["last_30_days"]["num_bets"], 0)

    def test_other_filters_still_apply(self):
        self.seed_bets()
        result = get_period_stats(FilterParams(strategies=["NoSuchStrategy"]), self.user, self.db)
        self.assertEqual(result["today"]["num_bets"], 0)

        result = get_period_stats(FilterParams(strategies=["Alpha"]), self.user, self.db)
        self.assertEqual(result["today"]["num_bets"], 1)


if __name__ == "__main__":
    unittest.main()
