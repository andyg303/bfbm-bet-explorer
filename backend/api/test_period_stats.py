import os
import sys
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Bet, User
from api.main import FilterParams, get_period_stats

PERIOD_KEYS = ("yesterday", "last_7_days", "last_30_days", "previous_30_days")


class PeriodStatsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(id=1, email="test@example.com", password_hash="hash", subscription_status="active")
        self.other_user = User(id=2, email="other@example.com", password_hash="hash", subscription_status="active")
        self.db.add_all([self.user, self.other_user])
        self.db.commit()
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

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
        t = self.today
        self.add_bet(1, start_time=t + timedelta(hours=1), pl=999.0)              # today — excluded everywhere
        self.add_bet(2, start_time=t - timedelta(hours=6), pl=-10.0)              # yesterday
        self.add_bet(3, start_time=t - timedelta(days=3), pl=20.0, commission=0.4) # in last 7
        self.add_bet(4, start_time=t - timedelta(days=7) + timedelta(hours=1), pl=5.0)     # oldest day of last 7
        self.add_bet(5, start_time=t - timedelta(days=8), pl=7.0)                          # outside last 7, in last 30
        self.add_bet(6, start_time=t - timedelta(days=30) + timedelta(hours=1), pl=-10.0)  # oldest day of last 30
        self.add_bet(7, start_time=t - timedelta(days=31), pl=100.0)                       # newest day of previous 30
        self.add_bet(8, start_time=t - timedelta(days=60) + timedelta(hours=1), pl=50.0)   # oldest day of previous 30
        self.add_bet(9, start_time=t - timedelta(days=61), pl=1000.0)             # outside everything
        self.add_bet(10, start_time=t - timedelta(hours=3), pl=999.0, user_id=2)  # other user — never leaks

    def test_period_buckets_and_boundaries(self):
        self.seed_bets()
        result = get_period_stats(FilterParams(), self.user, self.db)
        self.assertEqual(set(result.keys()), set(PERIOD_KEYS))

        self.assertEqual(result["yesterday"]["num_bets"], 1)
        self.assertEqual(result["yesterday"]["net_pl"], -10.0)

        # yesterday + 3d + 7d ago; excludes today and 8d ago
        self.assertEqual(result["last_7_days"]["num_bets"], 3)
        self.assertEqual(result["last_7_days"]["net_pl"], 14.6)

        # last 7 + 8d + 30d ago; excludes 31d ago
        self.assertEqual(result["last_30_days"]["num_bets"], 5)
        self.assertEqual(result["last_30_days"]["net_pl"], 11.6)

        # 31d and 60d ago only — no overlap with last 30, excludes 61d
        self.assertEqual(result["previous_30_days"]["num_bets"], 2)
        self.assertEqual(result["previous_30_days"]["net_pl"], 150.0)

    def test_today_is_never_included(self):
        self.add_bet(1, start_time=datetime.now(), pl=10.0)
        result = get_period_stats(FilterParams(), self.user, self.db)
        for key in PERIOD_KEYS:
            self.assertEqual(result[key]["num_bets"], 0, key)

    def test_empty_periods_return_zeroes(self):
        result = get_period_stats(FilterParams(), self.user, self.db)
        for key in PERIOD_KEYS:
            self.assertEqual(result[key]["num_bets"], 0)
            self.assertEqual(result[key]["net_pl"], 0)
            self.assertEqual(result[key]["num_strategies"], 0)

    def test_window_intersects_existing_date_filters(self):
        self.seed_bets()
        t = self.today

        # User date_from of 2 days ago narrows last_7_days to just yesterday
        f = FilterParams(date_from=(t - timedelta(days=2)).isoformat())
        result = get_period_stats(f, self.user, self.db)
        self.assertEqual(result["last_7_days"]["num_bets"], 1)

        # User date_to of 70 days ago excludes everything
        f = FilterParams(date_to=(t - timedelta(days=70)).isoformat())
        result = get_period_stats(f, self.user, self.db)
        for key in PERIOD_KEYS:
            self.assertEqual(result[key]["num_bets"], 0, key)

    def test_other_filters_still_apply(self):
        self.seed_bets()
        result = get_period_stats(FilterParams(strategies=["NoSuchStrategy"]), self.user, self.db)
        self.assertEqual(result["yesterday"]["num_bets"], 0)

        result = get_period_stats(FilterParams(strategies=["Alpha"]), self.user, self.db)
        self.assertEqual(result["yesterday"]["num_bets"], 1)


if __name__ == "__main__":
    unittest.main()
