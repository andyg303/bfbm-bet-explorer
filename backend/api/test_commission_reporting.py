import unittest
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Bet, User
from api.commission import apply_commission_for_user
from api.main import (
    get_all_strategies,
    get_archived_strategies,
    get_monthly_pl,
    get_odds_bands_profit,
    get_pl_over_time,
    get_profit_curve_by_odds,
    get_strategy_stats,
    get_summary_stats,
)
from api.strategy_comparison import build_strategy_comparison


def filters(**overrides):
    values = {
        "strategies": [],
        "bet_types": [],
        "statuses": [],
        "market_types": [],
        "country_codes": [],
        "events": [],
        "min_odds": None,
        "max_odds": None,
        "min_stake": None,
        "max_stake": None,
        "min_pl": None,
        "max_pl": None,
        "date_from": None,
        "date_to": None,
        "selection_search": None,
        "description_search": None,
        "staking_type": "default",
        "base_stake": 10,
        "deduplicate": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class CommissionReportingTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.user = User(
            id=1,
            email="test@example.com",
            password_hash="hash",
            subscription_status="active",
            commission_rate=2,
            commission_rate_aus_nz=5,
        )
        self.db.add(self.user)
        self.db.add_all([
            Bet(
                id=1,
                user_id=1,
                bet_id="gross-win",
                strategy="Gross Strategy",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=10,
                commission_paid=0.2,
                start_time=datetime(2026, 6, 1, 12, 0),
                placed_date=datetime(2026, 6, 1, 11, 0),
                description="Market One\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                id=2,
                user_id=1,
                bet_id="loss",
                strategy="Gross Strategy",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=-10,
                commission_paid=0,
                start_time=datetime(2026, 6, 1, 13, 0),
                placed_date=datetime(2026, 6, 1, 11, 30),
                description="Market Two\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                id=3,
                user_id=1,
                bet_id="other-win",
                strategy="Other Strategy",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=1.5,
                profit_loss=5,
                commission_paid=0.1,
                start_time=datetime(2026, 6, 2, 12, 0),
                placed_date=datetime(2026, 6, 2, 11, 0),
                description="Market Three\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                id=4,
                user_id=1,
                bet_id="archived-win",
                strategy="Archived Strategy",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=10,
                commission_paid=0.2,
                start_time=datetime(2026, 6, 3, 12, 0),
                placed_date=datetime(2026, 6, 3, 11, 0),
                description="Market Four\\Runner",
                is_archived=True,
                is_deleted=False,
            ),
            Bet(
                id=5,
                user_id=2,
                bet_id="other-user",
                strategy="Gross Strategy",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=999,
                commission_paid=99,
                start_time=datetime(2026, 6, 1, 12, 0),
                is_archived=False,
                is_deleted=False,
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_commission_recalculation_keeps_gross_pl_and_sets_commission_separately(self):
        self.db.query(Bet).delete()
        self.db.add(Bet(
            id=10,
            user_id=1,
            bet_id="single-win",
            strategy="Single",
            bet_type="BACK",
            matched_amount=10,
            avg_price_matched=2.0,
            profit_loss=10,
            commission_paid=0,
            start_time=datetime(2026, 6, 4, 12, 0),
            placed_date=datetime(2026, 6, 4, 11, 0),
            description="Market Five\\Runner",
            is_archived=False,
            is_deleted=False,
        ))
        self.db.commit()

        apply_commission_for_user(self.db, self.user)

        bet = self.db.query(Bet).filter(Bet.bet_id == "single-win").one()
        self.assertEqual(bet.profit_loss, 10)
        self.assertEqual(bet.commission_paid, 0.2)

        apply_commission_for_user(self.db, self.user)
        self.db.refresh(bet)
        self.assertEqual(bet.profit_loss, 10)
        self.assertEqual(bet.commission_paid, 0.2)

    def test_commission_recalculation_restores_legacy_net_pl_rows_without_inflating_gross_rows(self):
        self.db.query(Bet).delete()
        self.db.add_all([
            Bet(
                id=11,
                user_id=1,
                bet_id="already-gross",
                strategy="Already Gross",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=10,
                commission_paid=0.2,
                start_time=datetime(2026, 6, 4, 12, 0),
                placed_date=datetime(2026, 6, 4, 11, 0),
                description="Market Six\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
            Bet(
                id=12,
                user_id=1,
                bet_id="legacy-net",
                strategy="Legacy Net",
                bet_type="BACK",
                matched_amount=10,
                avg_price_matched=2.0,
                profit_loss=9.8,
                commission_paid=0.2,
                start_time=datetime(2026, 6, 5, 12, 0),
                placed_date=datetime(2026, 6, 5, 11, 0),
                description="Market Seven\\Runner",
                is_archived=False,
                is_deleted=False,
            ),
        ])
        self.db.commit()

        apply_commission_for_user(self.db, self.user)

        already_gross = self.db.query(Bet).filter(Bet.bet_id == "already-gross").one()
        legacy_net = self.db.query(Bet).filter(Bet.bet_id == "legacy-net").one()
        self.assertEqual(already_gross.profit_loss, 10)
        self.assertEqual(already_gross.commission_paid, 0.2)
        self.assertEqual(legacy_net.profit_loss, 10)
        self.assertEqual(legacy_net.commission_paid, 0.2)

    def test_dashboard_reports_use_net_pl_after_commission(self):
        f = filters()

        strategy_stats = {row["strategy"]: row for row in get_strategy_stats(f, self.user, self.db)}
        self.assertEqual(strategy_stats["Gross Strategy"]["total_pl"], -0.2)
        self.assertEqual(strategy_stats["Other Strategy"]["total_pl"], 4.9)

        summary = get_summary_stats(f, self.user, self.db)
        self.assertEqual(summary["total_pl"], 4.7)
        self.assertEqual(summary["roi"], 15.67)

        pl_over_time = get_pl_over_time(f, self.user, self.db)
        self.assertEqual(pl_over_time, [
            {"date": "2026-06-01", "daily_pl": -0.2, "cumulative_pl": -0.2},
            {"date": "2026-06-02", "daily_pl": 4.9, "cumulative_pl": 4.7},
        ])

        odds_bands = get_odds_bands_profit(f, self.user, self.db)
        self.assertEqual(odds_bands[0]["total_pl"], 4.7)

        odds_curve = get_profit_curve_by_odds(f, self.user, self.db)
        self.assertEqual(odds_curve[-1]["cum_pl"], 4.7)

        monthly = get_monthly_pl(filters(deduplicate=True), self.user, self.db)
        self.assertEqual(monthly["key_stats"]["total_profit"], 4.7)
        self.assertEqual(monthly["grid"][0]["6"], 4.7)

    def test_restaked_reports_recalculate_commission_from_gross_pl(self):
        summary = get_summary_stats(
            filters(staking_type="level_stake", base_stake=10),
            self.user,
            self.db,
        )

        self.assertEqual(summary["total_pl"], 4.7)

    def test_strategy_manager_archive_and_comparison_stats_use_net_pl(self):
        archived = {row["strategy"]: row for row in get_archived_strategies(self.user, self.db)}
        self.assertEqual(archived["Archived Strategy"]["total_pl"], 9.8)

        all_strategies = {row["strategy"]: row for row in get_all_strategies(self.user, self.db)}
        self.assertEqual(all_strategies["Gross Strategy"]["total_pl"], -0.2)
        self.assertEqual(all_strategies["Other Strategy"]["total_pl"], 4.9)
        self.assertEqual(all_strategies["Archived Strategy"]["total_pl"], 9.8)

        comparison_filters = filters(strategies=["Gross Strategy", "Other Strategy"])
        bets = self.db.query(Bet).filter(Bet.user_id == self.user.id).all()
        comparison = build_strategy_comparison(
            bets,
            comparison_filters.strategies,
            comparison_filters,
            self.user,
        )
        by_strategy = {row["strategy"]: row for row in comparison["strategies"]}
        self.assertEqual(by_strategy["Gross Strategy"]["stats"]["total_pl"], -0.2)
        self.assertEqual(by_strategy["Other Strategy"]["stats"]["total_pl"], 4.9)


if __name__ == "__main__":
    unittest.main()
