import os
import sys
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Bet, StrategyFavorite, StrategyGroup, StrategyGroupMember, User
from api.main import (
    CreateStrategyGroupRequest,
    MergeStrategiesRequest,
    StarStrategyRequest,
    StrategyGroupMembersRequest,
    add_strategy_group_members,
    create_strategy_group,
    delete_strategy_group,
    get_strategy_meta,
    merge_strategies,
    remove_strategy_group_members,
    star_strategy,
)


class StrategyGroupsTest(unittest.TestCase):
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

    def add_bet(self, bet_id: int, *, user_id: int = 1, strategy: str = "Alpha"):
        bet = Bet(
            id=bet_id,
            user_id=user_id,
            bet_id=f"bet-{user_id}-{bet_id}",
            strategy=strategy,
            is_archived=False,
            is_deleted=False,
        )
        self.db.add(bet)
        self.db.commit()
        return bet

    # ── Stars ────────────────────────────────────────────────────────────

    def test_star_strategy_is_idempotent_and_user_scoped(self):
        result = star_strategy(
            StarStrategyRequest(strategy="Alpha", starred=True), self.user, self.db
        )
        self.assertTrue(result["starred"])

        # Starring again must not duplicate the row
        star_strategy(StarStrategyRequest(strategy="Alpha", starred=True), self.user, self.db)
        meta = get_strategy_meta(self.user, self.db)
        self.assertEqual(meta["starred"], ["Alpha"])

        # Other user's stars stay separate
        self.assertEqual(get_strategy_meta(self.other_user, self.db)["starred"], [])

        star_strategy(StarStrategyRequest(strategy="Alpha", starred=False), self.user, self.db)
        self.assertEqual(get_strategy_meta(self.user, self.db)["starred"], [])

    def test_star_strategy_rejects_blank_name(self):
        with self.assertRaises(HTTPException) as ctx:
            star_strategy(StarStrategyRequest(strategy="   ", starred=True), self.user, self.db)
        self.assertEqual(ctx.exception.status_code, 400)

    # ── Groups ───────────────────────────────────────────────────────────

    def test_create_group_add_members_and_read_meta(self):
        group = create_strategy_group(
            CreateStrategyGroupRequest(name="Horse Racing"), self.user, self.db
        )
        self.assertEqual(group["name"], "Horse Racing")
        self.assertEqual(group["strategies"], [])

        group = add_strategy_group_members(
            group["id"],
            StrategyGroupMembersRequest(strategies=["Alpha", "Beta", "Alpha", "  "]),
            self.user,
            self.db,
        )
        self.assertEqual(group["strategies"], ["Alpha", "Beta"])

        # Re-adding an existing member is a no-op
        group = add_strategy_group_members(
            group["id"], StrategyGroupMembersRequest(strategies=["Alpha"]), self.user, self.db
        )
        self.assertEqual(group["strategies"], ["Alpha", "Beta"])

        meta = get_strategy_meta(self.user, self.db)
        self.assertEqual(len(meta["groups"]), 1)
        self.assertEqual(meta["groups"][0]["strategies"], ["Alpha", "Beta"])
        self.assertEqual(get_strategy_meta(self.other_user, self.db)["groups"], [])

    def test_create_group_rejects_duplicate_name_case_insensitive(self):
        create_strategy_group(CreateStrategyGroupRequest(name="My Group"), self.user, self.db)
        with self.assertRaises(HTTPException) as ctx:
            create_strategy_group(CreateStrategyGroupRequest(name="my group"), self.user, self.db)
        self.assertEqual(ctx.exception.status_code, 409)

        # The same name is fine for another user
        other = create_strategy_group(
            CreateStrategyGroupRequest(name="My Group"), self.other_user, self.db
        )
        self.assertEqual(other["name"], "My Group")

    def test_remove_members_and_delete_group(self):
        group = create_strategy_group(CreateStrategyGroupRequest(name="G"), self.user, self.db)
        group = add_strategy_group_members(
            group["id"],
            StrategyGroupMembersRequest(strategies=["Alpha", "Beta", "Gamma"]),
            self.user,
            self.db,
        )

        group = remove_strategy_group_members(
            group["id"], StrategyGroupMembersRequest(strategies=["Beta"]), self.user, self.db
        )
        self.assertEqual(group["strategies"], ["Alpha", "Gamma"])

        delete_strategy_group(group["id"], self.user, self.db)
        self.assertEqual(get_strategy_meta(self.user, self.db)["groups"], [])
        self.assertEqual(self.db.query(StrategyGroupMember).count(), 0)

    def test_group_endpoints_reject_other_users_groups(self):
        group = create_strategy_group(CreateStrategyGroupRequest(name="G"), self.user, self.db)
        with self.assertRaises(HTTPException) as ctx:
            add_strategy_group_members(
                group["id"], StrategyGroupMembersRequest(strategies=["Alpha"]),
                self.other_user, self.db,
            )
        self.assertEqual(ctx.exception.status_code, 404)
        with self.assertRaises(HTTPException) as ctx:
            delete_strategy_group(group["id"], self.other_user, self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    # ── Merge keeps stars/groups pointed at the surviving name ───────────

    def test_merge_renames_star_and_group_memberships(self):
        self.add_bet(10, strategy="Target")
        self.add_bet(11, strategy="Source")

        star_strategy(StarStrategyRequest(strategy="Source", starred=True), self.user, self.db)
        group = create_strategy_group(CreateStrategyGroupRequest(name="G"), self.user, self.db)
        add_strategy_group_members(
            group["id"], StrategyGroupMembersRequest(strategies=["Source", "Other"]),
            self.user, self.db,
        )

        merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        meta = get_strategy_meta(self.user, self.db)
        self.assertEqual(meta["starred"], ["Target"])
        self.assertEqual(sorted(meta["groups"][0]["strategies"]), ["Other", "Target"])

    def test_merge_dedupes_memberships_when_target_already_present(self):
        star_strategy(StarStrategyRequest(strategy="Source", starred=True), self.user, self.db)
        star_strategy(StarStrategyRequest(strategy="Target", starred=True), self.user, self.db)
        group = create_strategy_group(CreateStrategyGroupRequest(name="G"), self.user, self.db)
        add_strategy_group_members(
            group["id"], StrategyGroupMembersRequest(strategies=["Source", "Target"]),
            self.user, self.db,
        )

        merge_strategies(
            MergeStrategiesRequest(source_strategies=["Source"], target_strategy="Target"),
            self.user,
            self.db,
        )

        meta = get_strategy_meta(self.user, self.db)
        self.assertEqual(meta["starred"], ["Target"])
        self.assertEqual(meta["groups"][0]["strategies"], ["Target"])
        self.assertEqual(self.db.query(StrategyFavorite).count(), 1)


if __name__ == "__main__":
    unittest.main()
