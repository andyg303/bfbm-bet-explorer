import os
import sys
import unittest
from datetime import datetime, timezone

from fastapi import HTTPException
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, Bet, User
from api.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_current_user,
    require_write_session,
)
from api.admin import impersonate_user
from api.main import delete_bet


class AdminImpersonationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.admin = User(
            id=1,
            email="admin@example.com",
            password_hash="hash",
            is_admin=True,
            is_active=True,
            subscription_status="active",
            created_at=datetime.now(timezone.utc),
        )
        self.user = User(
            id=2,
            email="user@example.com",
            display_name="Debug User",
            password_hash="hash",
            is_admin=False,
            is_active=True,
            subscription_status="active",
            created_at=datetime.now(timezone.utc),
        )
        self.other_admin = User(
            id=3,
            email="other-admin@example.com",
            password_hash="hash",
            is_admin=True,
            is_active=True,
            subscription_status="active",
            created_at=datetime.now(timezone.utc),
        )
        self.bet = Bet(
            id=10,
            user_id=2,
            bet_id="b1",
            is_deleted=False,
            is_archived=False,
        )
        self.db.add_all([self.admin, self.user, self.other_admin, self.bet])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    async def test_impersonation_token_authenticates_as_target_and_marks_session_read_only(self):
        response = impersonate_user(self.user.id, self.admin, self.db)
        payload = jwt.decode(response["access_token"], SECRET_KEY, algorithms=[ALGORITHM])

        current_user = await get_current_user(response["access_token"], self.db)

        self.assertEqual(current_user.id, self.user.id)
        self.assertEqual(payload["sub"], str(self.user.id))
        self.assertEqual(payload["impersonated_by"], self.admin.id)
        self.assertTrue(payload["read_only"])
        self.assertNotIn("refresh_token", response)
        self.assertEqual(response["user"]["email"], self.user.email)
        self.assertEqual(response["impersonator"]["email"], self.admin.email)

    def test_admin_cannot_impersonate_admin_user(self):
        with self.assertRaises(HTTPException) as ctx:
            impersonate_user(self.other_admin.id, self.admin, self.db)

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_read_only_impersonation_token_rejects_mutating_endpoint(self):
        token = create_access_token({
            "sub": str(self.user.id),
            "tv": 0,
            "impersonated_by": self.admin.id,
            "read_only": True,
        })
        current_user = await get_current_user(token, self.db)

        with self.assertRaises(HTTPException) as ctx:
            require_write_session(current_user)

        self.assertEqual(ctx.exception.status_code, 403)

        with self.assertRaises(HTTPException) as delete_ctx:
            delete_bet(self.bet.id, current_user, self.db)

        self.assertEqual(delete_ctx.exception.status_code, 403)
        self.db.refresh(self.bet)
        self.assertFalse(self.bet.is_deleted)


if __name__ == "__main__":
    unittest.main()
