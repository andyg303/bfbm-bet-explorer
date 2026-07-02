import os
import sys
import unittest
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Bet, User
from api.main import (
    DeleteMergeDuplicateBetsRequest,
    MergeStrategiesRequest,
    delete_merge_duplicate_bets,
    merge_strategies,
)


class StrategyMergeTest(unittest.TestCase):
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

    def add_bet(
        self,
        bet_id: int,
        *,
        user_id: int = 1,
        strategy: str = "Source",
        selection: str = "Runner",
        description: str = "Market One\\Runner",
        market_id: str | None = "market-1",
        market_name: str | None = "Market One",
        event: str | None = "Event One",
        placed_date: datetime | None = None,
        matched_date: datetime | None = None,
        settled_date: datetime | None = None,
        start_time: datetime | None = None,
        avg_price_matched: float | None = 2.0,
        price_requested: float | None = 2.1,
        is_archived: bool = False,
        is_deleted: bool = False,
    ):
        bet = Bet(
            id=bet_id,
            user_id=user_id,
            bet_id=f"bet-{user_id}-{bet_id}",
            strategy=strategy,
            selection=selection,
            description=description,
            market_id=market_id,
            market_name=market_name,
            event=event,
            placed_date=placed_date,
            matched_date=matched_date,
            settled_date=settled_date,
            start_time=start_time,
            avg_price_matched=avg_price_matched,
            price_requested=price_requested,
            is_archived=is_archived,
            is_deleted=is_deleted,
        )
        self.db.add(bet)
        self.db.commit()
        return bet

    def remaining_ids(self):
        return [row.id for row in self.db.query(Bet).order_by(Bet.id).all()]

    def test_merge_returns_duplicate_groups_without_deleting_anything(self):
        self.add_bet(
            10,
            strategy="Target",
            placed_date=datetime(2026, 1, 1, 12, 0),
        )
        self.add_bet(
            11,
            strategy="Source",
            placed_date=datetime(2026, 1, 1, 12, 1),
            avg_price_matched=3.0,
        )
        self.add_bet(
            12,
            strategy="Source",
            selection="Other Runner",
            description="Market Two\\Other Runner",
            market_id="market-2",
            market_name="Market Two",
            placed_date=datetime(2026, 1, 1, 12, 2),
        )

        result = merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        self.assertEqual(result["merged_bets"], 2)
        self.assertEqual(self.remaining_ids(), [10, 11, 12])
        self.assertEqual(
            [row.strategy for row in self.db.query(Bet).order_by(Bet.id).all()],
            ["Target", "Target", "Target"],
        )

        groups = result["duplicate_groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["bet_name"], "Runner")
        self.assertEqual(groups[0]["market"], "Market One")
        self.assertEqual(groups[0]["suggested_keep_bet_id"], 10)
        self.assertEqual(groups[0]["suggested_delete_bet_ids"], [11])
        self.assertEqual(
            [(bet["id"], bet["original_strategy"], bet["avg_price_matched"]) for bet in groups[0]["bets"]],
            [(10, "Target", 2.0), (11, "Source", 3.0)],
        )

    def test_merge_duplicate_groups_use_timestamp_fallback_and_lowest_id_for_suggestions(self):
        self.add_bet(
            30,
            strategy="Target",
            placed_date=None,
            matched_date=datetime(2026, 1, 1, 12, 1),
        )
        self.add_bet(
            31,
            strategy="Source",
            placed_date=None,
            matched_date=datetime(2026, 1, 1, 12, 0),
        )
        self.add_bet(
            32,
            strategy="Source",
            placed_date=None,
            matched_date=datetime(2026, 1, 1, 12, 0),
        )

        result = merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        group = result["duplicate_groups"][0]
        self.assertEqual(group["suggested_keep_bet_id"], 31)
        self.assertEqual(group["suggested_delete_bet_ids"], [32, 30])
        self.assertEqual(self.remaining_ids(), [30, 31, 32])

    def test_merge_duplicate_groups_ignore_other_users_archived_and_deleted_bets(self):
        self.add_bet(40, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 3))
        self.add_bet(41, user_id=2, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 0))
        self.add_bet(42, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 1), is_archived=True)
        self.add_bet(43, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 2), is_deleted=True)

        result = merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        self.assertEqual(result["merged_bets"], 0)
        self.assertEqual(result["duplicate_groups"], [])
        self.assertEqual(self.remaining_ids(), [40, 41, 42, 43])

    def test_delete_merge_duplicate_bets_hard_deletes_only_confirmed_duplicate_rows(self):
        self.add_bet(50, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 0))
        self.add_bet(51, strategy="Source", placed_date=datetime(2026, 1, 1, 12, 1))
        self.add_bet(52, strategy="Source", placed_date=datetime(2026, 1, 1, 12, 2))
        merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        result = delete_merge_duplicate_bets(
            DeleteMergeDuplicateBetsRequest(target_strategy="Target", bet_ids=[51]),
            self.user,
            self.db,
        )

        self.assertEqual(result["deleted_duplicates"], 1)
        self.assertEqual(self.remaining_ids(), [50, 52])

    def test_delete_merge_duplicate_bets_rejects_deleting_every_bet_in_a_group(self):
        self.add_bet(60, strategy="Target", placed_date=datetime(2026, 1, 1, 12, 0))
        self.add_bet(61, strategy="Source", placed_date=datetime(2026, 1, 1, 12, 1))
        merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        with self.assertRaises(HTTPException) as ctx:
            delete_merge_duplicate_bets(
                DeleteMergeDuplicateBetsRequest(target_strategy="Target", bet_ids=[60, 61]),
                self.user,
                self.db,
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(self.remaining_ids(), [60, 61])


if __name__ == "__main__":
    unittest.main()
