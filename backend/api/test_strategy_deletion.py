import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Bet, User
from api.strategy_actions import delete_archived_strategy_bets


class StrategyDeletionTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.user = User(id=1, email="test@example.com", password_hash="hash", subscription_status="active")
        self.db.add_all([
            Bet(user_id=1, bet_id="archived-1", strategy="Archived", is_archived=True, is_deleted=False),
            Bet(user_id=1, bet_id="archived-2", strategy="Archived", is_archived=True, is_deleted=False),
            Bet(user_id=1, bet_id="active-1", strategy="Active", is_archived=False, is_deleted=False),
            Bet(user_id=2, bet_id="other-user", strategy="Archived", is_archived=True, is_deleted=False),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_delete_archived_strategies_hard_deletes_only_user_archived_bets(self):
        deleted = delete_archived_strategy_bets(
            self.db,
            self.user.id,
            ["Archived", "Active"],
        )

        self.assertEqual(deleted, 2)
        self.assertEqual(
            [(b.user_id, b.bet_id, b.strategy) for b in self.db.query(Bet).order_by(Bet.bet_id)],
            [(1, "active-1", "Active"), (2, "other-user", "Archived")],
        )


if __name__ == "__main__":
    unittest.main()
