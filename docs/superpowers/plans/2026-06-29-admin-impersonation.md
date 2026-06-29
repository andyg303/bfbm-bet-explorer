# Admin Impersonation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build read-only admin impersonation so admins can debug a user's dashboard exactly as that user sees it.

**Architecture:** The backend mints short-lived impersonation access tokens with `impersonated_by` and `read_only` claims. Existing read endpoints keep using the current user-scoped query architecture, while mutating endpoints use a shared guard that rejects read-only impersonation sessions. The frontend swaps the active auth session into impersonation mode, displays a safety banner, and restores the saved admin session on exit.

**Tech Stack:** FastAPI, SQLAlchemy, python-jose JWTs, Vue 3, Pinia, Axios, TypeScript.

---

### Task 1: Backend token and guard behavior

**Files:**
- Modify: `backend/api/auth.py`
- Modify: `backend/api/admin.py`
- Modify: `backend/api/main.py`
- Test: `backend/api/test_admin_impersonation.py`

- [ ] **Step 1: Write failing tests**

Create `backend/api/test_admin_impersonation.py` with tests that:

```python
import os
import sys
import unittest
from datetime import datetime, timezone

from fastapi import HTTPException
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, User, Bet
from api.auth import ALGORITHM, SECRET_KEY, create_access_token, get_current_user, require_write_session
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
        self.bet = Bet(id=10, user_id=2, bet_id="b1", is_deleted=False, is_archived=False)
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
```

- [ ] **Step 2: Run tests and verify red**

Run: `JWT_SECRET_KEY=test-secret python -m unittest backend.api.test_admin_impersonation -v`

Expected: failure importing `require_write_session` or `impersonate_user`, because the feature is not implemented.

- [ ] **Step 3: Implement minimal backend behavior**

Add token claim parsing in `get_current_user`, a `require_write_session(user)` helper that rejects `user._read_only_session`, and `POST /admin/users/{target_user_id}/impersonate` that returns a short-lived access token and target/admin profile dictionaries.

Add `Depends(require_write_session)` to mutating routes, or call the helper at the top of mutating functions that are difficult to express as dependencies.

- [ ] **Step 4: Run tests and verify green**

Run: `JWT_SECRET_KEY=test-secret python -m unittest backend.api.test_admin_impersonation -v`

Expected: all tests pass.

### Task 2: Frontend session swap and admin entry point

**Files:**
- Modify: `frontend/src/stores/authStore.ts`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/components/AdminDashboard.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Extend auth store**

Add saved-admin-session storage, impersonation metadata, `startImpersonation(...)`, and `stopImpersonation()` actions. Starting impersonation saves the current admin token/profile, persists the returned impersonation token/profile, and marks the session as impersonating.

- [ ] **Step 2: Add API wrapper**

Add `impersonateUser(userId)` to `frontend/src/services/api.ts` that posts to `/admin/users/${userId}/impersonate`.

- [ ] **Step 3: Add admin users-table action**

Add a "View as" action for non-admin active users. On success, start impersonation and navigate to `dashboard`.

- [ ] **Step 4: Add dashboard safety banner**

In `frontend/src/App.vue`, show a persistent banner when `auth.isImpersonating` is true. The banner identifies the target user and includes a "Return to admin" button that restores the admin session and navigates to `admin`.

### Task 3: Frontend read-only controls

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/IngestData.vue`
- Modify: `frontend/src/components/BetTable.vue`
- Modify: `frontend/src/components/ArchivedStrategies.vue`
- Modify: `frontend/src/components/StrategyManager.vue`
- Modify: `frontend/src/components/StakingCalculator.vue`

- [ ] **Step 1: Hide top-level mutating controls**

Hide upload, uploader, account, referral, and password controls while impersonating.

- [ ] **Step 2: Disable dashboard mutating controls**

Use `useAuthStore()` in mutating components and hide or disable delete/archive/restore/merge/sanitize/recalculate-commission controls while impersonating.

### Task 4: Verification

**Files:**
- No source changes unless verification exposes a defect.

- [ ] **Step 1: Backend tests**

Run: `JWT_SECRET_KEY=test-secret python -m unittest backend.api.test_admin_impersonation backend.api.test_strategy_comparison backend.api.test_strategy_deletion -v`

Expected: all tests pass.

- [ ] **Step 2: Frontend type-check and build**

Run: `cd frontend && npm run type-check && npm run build-only`

Expected: both commands exit 0.

- [ ] **Step 3: Inspect git diff**

Run: `git diff --stat && git diff --check`

Expected: only intended files changed and no whitespace errors.
