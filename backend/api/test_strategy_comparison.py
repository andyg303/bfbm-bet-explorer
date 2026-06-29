import unittest
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Bet, User
from api.strategy_comparison import build_strategy_comparison


class StrategyComparisonTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(
            id=1,
            email="test@example.com",
            password_hash="hash",
            subscription_status="active",
            commission_rate=0,
            commission_rate_aus_nz=0,
        )
        self.db.add(self.user)
        self.db.add_all([
            Bet(
                user_id=1,
                bet_id="early-jan-win",
                strategy="Early",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=10,
                start_time=datetime(2026, 1, 5, 12, 0),
                description="Market A\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                user_id=1,
                bet_id="early-feb-loss",
                strategy="Early",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=3.0,
                profit_loss=-5,
                start_time=datetime(2026, 2, 10, 12, 0),
                description="Market B\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                user_id=1,
                bet_id="kickoff-jan-win",
                strategy="Kickoff",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=4.0,
                profit_loss=20,
                start_time=datetime(2026, 1, 6, 12, 0),
                description="Market C\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                user_id=1,
                bet_id="kickoff-mar-loss",
                strategy="Kickoff",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.5,
                profit_loss=-10,
                start_time=datetime(2026, 3, 1, 12, 0),
                description="Market D\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                user_id=2,
                bet_id="other-user",
                strategy="Early",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=999,
                start_time=datetime(2026, 1, 5, 12, 0),
                is_archived=False,
                is_deleted=False,
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_strategy_comparison_returns_separate_stats_lines_and_months(self):
        filters = SimpleNamespace(
            strategies=["Early", "Kickoff"],
            staking_type="level_stake",
            base_stake=10,
            deduplicate=False,
        )
        bets = self.db.query(Bet).filter(Bet.user_id == self.user.id).all()

        result = build_strategy_comparison(bets, filters.strategies, filters, self.user)

        self.assertEqual([s["strategy"] for s in result["strategies"]], ["Early", "Kickoff"])

        early = result["strategies"][0]
        self.assertEqual(early["stats"]["num_bets"], 2)
        self.assertEqual(early["stats"]["total_pl"], 5)
        self.assertEqual(early["stats"]["avg_odds"], 2.5)
        self.assertEqual(early["stats"]["win_rate"], 50)
        self.assertEqual(
            early["pl_over_time"],
            [
                {"date": "2026-01-05", "daily_pl": 10, "cumulative_pl": 10},
                {"date": "2026-02-10", "daily_pl": -5, "cumulative_pl": 5},
            ],
        )
        self.assertEqual(early["monthly_pl"]["grid"][0]["1"], 10)
        self.assertEqual(early["monthly_pl"]["grid"][0]["2"], -5)

        kickoff = result["strategies"][1]
        self.assertEqual(kickoff["stats"]["total_pl"], 10)
        self.assertEqual(
            kickoff["pl_over_time"],
            [
                {"date": "2026-01-06", "daily_pl": 20, "cumulative_pl": 20},
                {"date": "2026-03-01", "daily_pl": -10, "cumulative_pl": 10},
            ],
        )
        self.assertEqual(kickoff["monthly_pl"]["grid"][0]["1"], 20)
        self.assertEqual(kickoff["monthly_pl"]["grid"][0]["3"], -10)


if __name__ == "__main__":
    unittest.main()
