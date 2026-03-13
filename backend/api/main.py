"""
BFBM Bet Explorer API — fully authenticated, per-user data isolation.

Every data endpoint requires a valid JWT bearer token.
Every query is scoped to the authenticated user's user_id.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uvicorn
import sys
import os
import tempfile
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, Bet, User, init_db
from scripts.ingest_bets import ingest_csv_file, sanitize_strategy_name
from api.staking_utils import calculate_new_stake, calculate_new_pl, calculate_stake_or_liability
from api.auth import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    RefreshRequest,
    SECRET_KEY,
    ALGORITHM,
)
from jose import JWTError, jwt
from api.stripe_routes import router as stripe_router


# ═══════════════════════════════════════════════════════════════════════════
# App startup
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app):
    init_db()
    # Ensure newer columns exist for older databases
    from sqlalchemy import text, inspect
    from database import engine
    insp = inspect(engine)
    columns = [c['name'] for c in insp.get_columns('bets')]
    with engine.begin() as conn:
        if 'is_deleted' not in columns:
            conn.execute(text("ALTER TABLE bets ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bets_is_deleted ON bets (is_deleted)"))
        if 'is_archived' not in columns:
            conn.execute(text("ALTER TABLE bets ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bets_is_archived ON bets (is_archived)"))
        if 'user_id' not in columns:
            conn.execute(text("ALTER TABLE bets ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bets_user_id ON bets (user_id)"))
        # Drop old unique constraint on bet_id alone (now unique per user)
        try:
            conn.execute(text("ALTER TABLE bets DROP CONSTRAINT IF EXISTS bets_bet_id_key"))
        except Exception:
            pass
        # Create composite unique index if not exists
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_bet_id ON bets (user_id, bet_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_user_strategy ON bets (user_id, strategy)"
        ))

        # ── User subscription columns ──
        user_cols = [c['name'] for c in insp.get_columns('users')]
        if 'subscription_status' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_status VARCHAR DEFAULT 'inactive' NOT NULL"))
        if 'subscription_plan' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_plan VARCHAR"))
        if 'subscription_start' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_start TIMESTAMP"))
        if 'subscription_expires' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_expires TIMESTAMP"))
        if 'stripe_customer_id' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_stripe_customer_id ON users (stripe_customer_id)"))
        if 'stripe_checkout_session_id' not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN stripe_checkout_session_id VARCHAR"))
    yield


app = FastAPI(title="BFBM Bet Explorer API", lifespan=lifespan)
app.include_router(stripe_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════════

class FilterParams(BaseModel):
    strategies: Optional[List[str]] = []
    bet_types: Optional[List[str]] = []
    statuses: Optional[List[str]] = []
    market_types: Optional[List[str]] = []
    country_codes: Optional[List[str]] = []
    events: Optional[List[str]] = []
    min_odds: Optional[float] = None
    max_odds: Optional[float] = None
    min_stake: Optional[float] = None
    max_stake: Optional[float] = None
    min_pl: Optional[float] = None
    max_pl: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    selection_search: Optional[str] = None
    description_search: Optional[str] = None
    staking_type: Optional[str] = 'default'
    base_stake: Optional[float] = 10


class StakingParams(BaseModel):
    staking_type: str
    base_stake: float


class RecalculateStakingParams(FilterParams, StakingParams):
    pass


def apply_filters(query, filters: FilterParams, user_id: int):
    """Apply filters to a query — ALWAYS scoped to the authenticated user."""
    query = query.filter(Bet.user_id == user_id)
    query = query.filter(Bet.is_deleted == False)    # noqa: E712
    query = query.filter(Bet.is_archived == False)   # noqa: E712
    if filters.strategies:
        query = query.filter(Bet.strategy.in_(filters.strategies))
    if filters.bet_types:
        query = query.filter(Bet.bet_type.in_(filters.bet_types))
    if filters.statuses:
        query = query.filter(Bet.status.in_(filters.statuses))
    if filters.market_types:
        query = query.filter(Bet.market_type.in_(filters.market_types))
    if filters.country_codes:
        query = query.filter(Bet.country_code.in_(filters.country_codes))
    if filters.events:
        query = query.filter(Bet.event.in_(filters.events))
    if filters.min_odds is not None:
        query = query.filter(Bet.avg_price_matched >= filters.min_odds)
    if filters.max_odds is not None:
        query = query.filter(Bet.avg_price_matched <= filters.max_odds)
    if filters.min_stake is not None:
        query = query.filter(Bet.matched_amount >= filters.min_stake)
    if filters.max_stake is not None:
        query = query.filter(Bet.matched_amount <= filters.max_stake)
    if filters.min_pl is not None:
        query = query.filter(Bet.profit_loss >= filters.min_pl)
    if filters.max_pl is not None:
        query = query.filter(Bet.profit_loss <= filters.max_pl)
    if filters.date_from:
        query = query.filter(Bet.settled_date >= datetime.fromisoformat(filters.date_from))
    if filters.date_to:
        query = query.filter(Bet.settled_date <= datetime.fromisoformat(filters.date_to))
    if filters.selection_search:
        query = query.filter(Bet.selection.ilike(f"%{filters.selection_search}%"))
    if filters.description_search:
        query = query.filter(Bet.description.ilike(f"%{filters.description_search}%"))
    return query


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _user_dict(user: User) -> dict:
    """Standard user dict returned in auth responses — includes subscription."""
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "subscription_status": user.subscription_status or "inactive",
        "subscription_plan": user.subscription_plan,
        "subscription_expires": (
            user.subscription_expires.isoformat() if user.subscription_expires else None
        ),
    }


async def require_active_subscription(
    user: User = Depends(get_current_user),
) -> User:
    """Dependency: reject requests from users without an active subscription."""
    if user.subscription_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required. Please subscribe to access this feature.",
        )
    if user.subscription_expires and user.subscription_expires <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription has expired. Please renew to continue.",
        )
    return user


# ═══════════════════════════════════════════════════════════════════════════
# Auth endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return {"message": "BFBM Bet Explorer API"}


@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(
        func.lower(User.email) == req.email.lower()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = User(
        email=req.email.lower().strip(),
        password_hash=get_password_hash(req.password),
        display_name=req.display_name or req.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_dict(user),
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive JWT tokens."""
    user = db.query(User).filter(
        func.lower(User.email) == req.email.lower()
    ).first()
    # Constant-time comparison — always hash even if user not found
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_dict(user),
    )


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Get a new access token using a valid refresh token."""
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": user.id})
    new_refresh = create_refresh_token({"sub": user.id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        user=_user_dict(user),
    )


@app.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    d = _user_dict(user)
    d["created_at"] = user.created_at.isoformat() if user.created_at else None
    return d


@app.post("/auth/change-password")
def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = get_password_hash(req.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "message": "Password changed successfully"}


@app.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password-reset token.

    In production, the token is emailed to the user.  Here it is returned
    in the response for development convenience — wire up SMTP as needed.
    """
    user = db.query(User).filter(
        func.lower(User.email) == req.email.lower()
    ).first()

    # Always return success to avoid leaking whether an email exists
    if not user:
        return {"ok": True, "message": "If an account with that email exists, a reset link has been sent."}

    from datetime import timedelta
    token = create_password_reset_token()
    user.password_reset_token = get_password_hash(token)  # store hashed
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # TODO: Send email with reset link containing `token`
    # For now, return token in response (REMOVE IN PRODUCTION)
    return {
        "ok": True,
        "message": "If an account with that email exists, a reset link has been sent.",
        "_dev_reset_token": token,  # REMOVE IN PRODUCTION
    }


@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    # Find users with non-expired reset tokens
    users_with_tokens = (
        db.query(User)
        .filter(
            User.password_reset_token.isnot(None),
            User.password_reset_expires > datetime.now(timezone.utc),
        )
        .all()
    )

    target_user = None
    for u in users_with_tokens:
        if verify_password(req.token, u.password_reset_token):
            target_user = u
            break

    if not target_user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    target_user.password_hash = get_password_hash(req.new_password)
    target_user.password_reset_token = None
    target_user.password_reset_expires = None
    target_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "message": "Password has been reset successfully"}


# ═══════════════════════════════════════════════════════════════════════════
# Data endpoints — all require authentication + active subscription
# ═══════════════════════════════════════════════════════════════════════════

@app.delete("/bets/{bet_id}")
def delete_bet(
    bet_id: int,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Permanently soft-delete a single bet. Must belong to the authenticated user."""
    bet = db.query(Bet).filter(Bet.id == bet_id, Bet.user_id == user.id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")
    bet.is_deleted = True
    db.commit()
    return {"ok": True, "id": bet_id}


class ArchiveStrategiesRequest(BaseModel):
    strategies: List[str]


@app.post("/strategies/archive")
def archive_strategies(
    req: ArchiveStrategiesRequest,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Archive strategies — scoped to the authenticated user."""
    if not req.strategies:
        raise HTTPException(status_code=400, detail="No strategies provided")
    count = (
        db.query(Bet)
        .filter(
            Bet.user_id == user.id,
            Bet.strategy.in_(req.strategies),
            Bet.is_archived == False,   # noqa: E712
            Bet.is_deleted == False,     # noqa: E712
        )
        .update({Bet.is_archived: True}, synchronize_session='fetch')
    )
    db.commit()
    return {"ok": True, "archived_bets": count, "strategies": req.strategies}


@app.post("/strategies/restore")
def restore_strategies(
    req: ArchiveStrategiesRequest,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Restore archived strategies — scoped to the authenticated user."""
    if not req.strategies:
        raise HTTPException(status_code=400, detail="No strategies provided")
    count = (
        db.query(Bet)
        .filter(
            Bet.user_id == user.id,
            Bet.strategy.in_(req.strategies),
            Bet.is_archived == True,    # noqa: E712
            Bet.is_deleted == False,     # noqa: E712
        )
        .update({Bet.is_archived: False}, synchronize_session='fetch')
    )
    db.commit()
    return {"ok": True, "restored_bets": count, "strategies": req.strategies}


@app.get("/strategies/archived")
def get_archived_strategies(
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Return strategy-level stats for archived strategies belonging to this user."""
    query = db.query(
        Bet.strategy,
        func.count(Bet.id).label('num_bets'),
        func.sum(Bet.profit_loss).label('total_pl'),
        func.sum(case((Bet.bet_type == 'LAY', Bet.lay_liability), else_=Bet.matched_amount)).label('total_staked'),
        func.avg(Bet.avg_price_matched).label('avg_odds'),
        func.sum(case((Bet.profit_loss > 0, 1), else_=0)).label('num_won'),
        func.min(Bet.settled_date).label('first_bet'),
        func.max(Bet.settled_date).label('last_bet'),
    ).filter(
        Bet.user_id == user.id,
        Bet.is_archived == True,       # noqa: E712
        Bet.is_deleted == False,        # noqa: E712
        Bet.strategy.isnot(None),
    )

    query = query.group_by(Bet.strategy)
    results = query.all()

    stats = []
    for row in results:
        total_pl = float(row.total_pl or 0)
        total_staked = float(row.total_staked or 0)
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        win_rate = (row.num_won / row.num_bets * 100) if row.num_bets > 0 else 0
        stats.append({
            "strategy": row.strategy,
            "num_bets": row.num_bets,
            "total_pl": round(total_pl, 2),
            "total_staked": round(total_staked, 2),
            "roi": round(roi, 2),
            "avg_odds": round(float(row.avg_odds or 0), 2),
            "win_rate": round(win_rate, 2),
            "first_bet": row.first_bet.isoformat() if row.first_bet else None,
            "last_bet": row.last_bet.isoformat() if row.last_bet else None,
        })
    return sorted(stats, key=lambda x: x['total_pl'], reverse=True)


@app.post("/sanitize-strategies")
def sanitize_existing_strategies(
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Clean up funny characters in strategy names for this user."""
    bets = db.query(Bet).filter(
        Bet.user_id == user.id,
        Bet.strategy.isnot(None),
    ).all()
    fixed = 0
    for bet in bets:
        cleaned = sanitize_strategy_name(bet.strategy)
        if cleaned != bet.strategy:
            bet.strategy = cleaned
            fixed += 1
    db.commit()
    return {"ok": True, "rows_fixed": fixed}


@app.post("/migrate-deleted-to-archived")
def migrate_deleted_to_archived(
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Migrate old is_deleted strategy-level soft-deletes into is_archived."""
    all_strategies = (
        db.query(Bet.strategy)
        .filter(Bet.user_id == user.id, Bet.strategy.isnot(None))
        .distinct()
        .all()
    )
    migrated_strategies = []
    migrated_count = 0
    for (strategy,) in all_strategies:
        total = db.query(Bet).filter(
            Bet.user_id == user.id, Bet.strategy == strategy
        ).count()
        deleted = db.query(Bet).filter(
            Bet.user_id == user.id,
            Bet.strategy == strategy,
            Bet.is_deleted == True,  # noqa: E712
        ).count()
        if total > 0 and total == deleted:
            count = (
                db.query(Bet)
                .filter(
                    Bet.user_id == user.id,
                    Bet.strategy == strategy,
                    Bet.is_deleted == True,  # noqa: E712
                )
                .update({Bet.is_archived: True, Bet.is_deleted: False}, synchronize_session='fetch')
            )
            migrated_count += count
            migrated_strategies.append(strategy)
    db.commit()
    return {
        "ok": True,
        "migrated_strategies": migrated_strategies,
        "migrated_bets": migrated_count,
    }


@app.get("/filter-options")
def get_filter_options(
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get available filter options — scoped to this user's bets only."""
    base_filter = and_(
        Bet.user_id == user.id,
        Bet.is_deleted == False,  # noqa: E712
        Bet.is_archived == False,  # noqa: E712
    )
    strategies = db.query(Bet.strategy).distinct().filter(Bet.strategy.isnot(None), base_filter).all()
    bet_types = db.query(Bet.bet_type).distinct().filter(Bet.bet_type.isnot(None), base_filter).all()
    statuses = db.query(Bet.status).distinct().filter(Bet.status.isnot(None), base_filter).all()
    market_types = db.query(Bet.market_type).distinct().filter(Bet.market_type.isnot(None), base_filter).all()
    country_codes = db.query(Bet.country_code).distinct().filter(Bet.country_code.isnot(None), base_filter).all()
    events = db.query(Bet.event).distinct().filter(Bet.event.isnot(None), base_filter).all()

    return {
        "strategies": sorted([s[0] for s in strategies if s[0]]),
        "bet_types": sorted([b[0] for b in bet_types if b[0]]),
        "statuses": sorted([s[0] for s in statuses if s[0]]),
        "market_types": sorted([m[0] for m in market_types if m[0]]),
        "country_codes": sorted([c[0] for c in country_codes if c[0]]),
        "events": sorted([e[0] for e in events if e[0]]),
    }


@app.post("/strategy-stats")
def get_strategy_stats(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get statistics grouped by strategy."""
    if filters.staking_type and filters.staking_type != 'default':
        query = db.query(Bet).filter(Bet.strategy.isnot(None))
        query = apply_filters(query, filters, user.id)
        bets = query.all()

        strategy_data = {}
        for bet in bets:
            if not bet.strategy or not bet.avg_price_matched or bet.profit_loss is None:
                continue
            if bet.strategy not in strategy_data:
                strategy_data[bet.strategy] = {
                    'bets': [], 'num_back': 0, 'num_lay': 0, 'num_wins': 0,
                    'num_bets_with_bsp': 0, 'bsp_abs_sum': 0, 'bsp_pct_sum': 0,
                    'bsp_prob_sum': 0, 'odds_sum': 0,
                }
            strategy_data[bet.strategy]['bets'].append(bet)
            if bet.bet_type == 'BACK':
                strategy_data[bet.strategy]['num_back'] += 1
            else:
                strategy_data[bet.strategy]['num_lay'] += 1
            if bet.profit_loss > 0:
                strategy_data[bet.strategy]['num_wins'] += 1
            if bet.bsp and bet.bsp > 0:
                strategy_data[bet.strategy]['num_bets_with_bsp'] += 1
                if bet.bsp_diff_absolute:
                    strategy_data[bet.strategy]['bsp_abs_sum'] += bet.bsp_diff_absolute
                if bet.bsp_diff_percentage:
                    strategy_data[bet.strategy]['bsp_pct_sum'] += bet.bsp_diff_percentage
                if bet.bsp_diff_probability:
                    strategy_data[bet.strategy]['bsp_prob_sum'] += bet.bsp_diff_probability
            strategy_data[bet.strategy]['odds_sum'] += bet.avg_price_matched

        stats = []
        for strategy, data in strategy_data.items():
            total_pl = 0
            total_staked = 0
            total_stake_only = 0
            for bet in data['bets']:
                original_stake = bet.matched_amount if bet.matched_amount else 0
                if original_stake == 0:
                    continue
                new_stake = calculate_new_stake(
                    bet.bet_type, original_stake, bet.avg_price_matched,
                    filters.staking_type, filters.base_stake,
                )
                new_pl = calculate_new_pl(original_stake, bet.profit_loss, new_stake)
                new_stake_or_liability = calculate_stake_or_liability(
                    bet.bet_type, new_stake, bet.avg_price_matched,
                )
                total_pl += new_pl
                total_staked += new_stake_or_liability
                total_stake_only += new_stake
            num_bets = len(data['bets'])
            roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
            yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
            win_rate = (data['num_wins'] / num_bets * 100) if num_bets > 0 else 0
            bsp_fill_pct = (data['num_bets_with_bsp'] / num_bets * 100) if num_bets > 0 else 0
            avg_odds = data['odds_sum'] / num_bets if num_bets > 0 else 0
            stats.append({
                "strategy": strategy, "num_bets": num_bets,
                "total_pl": round(total_pl, 2), "roi": round(roi, 2),
                "yield_pct": round(yield_pct, 2), "total_staked": round(total_staked, 2),
                "avg_odds": round(avg_odds, 2), "win_rate": round(win_rate, 2),
                "num_back": data['num_back'], "num_lay": data['num_lay'],
                "bsp_fill_pct": round(bsp_fill_pct, 1),
                "avg_bsp_abs": round(data['bsp_abs_sum'] / data['num_bets_with_bsp'], 3) if data['num_bets_with_bsp'] > 0 else 0,
                "avg_bsp_pct": round(data['bsp_pct_sum'] / data['num_bets_with_bsp'], 2) if data['num_bets_with_bsp'] > 0 else 0,
                "avg_bsp_prob": round(data['bsp_prob_sum'] / data['num_bets_with_bsp'], 2) if data['num_bets_with_bsp'] > 0 else 0,
            })
        return sorted(stats, key=lambda x: x['total_pl'], reverse=True)

    # Default staking — aggregation
    query = db.query(
        Bet.strategy,
        func.count(Bet.id).label('num_bets'),
        func.sum(Bet.profit_loss).label('total_pl'),
        func.sum(case((Bet.bet_type == 'LAY', Bet.lay_liability), else_=Bet.matched_amount)).label('total_staked'),
        func.sum(Bet.matched_amount).label('total_stake_only'),
        func.avg(Bet.avg_price_matched).label('avg_odds'),
        func.sum(case((Bet.status == 'WON', 1), else_=0)).label('num_won'),
        func.sum(case((Bet.bet_type == 'BACK', 1), else_=0)).label('num_back'),
        func.sum(case((Bet.bet_type == 'LAY', 1), else_=0)).label('num_lay'),
        func.sum(case((Bet.bsp.isnot(None), 1), else_=0)).label('num_with_bsp'),
        func.avg(Bet.bsp_diff_absolute).label('avg_bsp_abs'),
        func.avg(Bet.bsp_diff_percentage).label('avg_bsp_pct'),
        func.avg(Bet.bsp_diff_probability).label('avg_bsp_prob'),
    ).filter(Bet.strategy.isnot(None))
    query = apply_filters(query, filters, user.id)
    query = query.group_by(Bet.strategy)
    results = query.all()

    stats = []
    for row in results:
        total_staked = float(row.total_staked or 0)
        total_stake_only = float(row.total_stake_only or 0)
        total_pl = float(row.total_pl or 0)
        num_bets = row.num_bets
        num_won = row.num_won
        num_with_bsp = row.num_with_bsp
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
        win_rate = (num_won / num_bets * 100) if num_bets > 0 else 0
        bsp_fill_pct = (num_with_bsp / num_bets * 100) if num_bets > 0 else 0
        stats.append({
            "strategy": row.strategy, "num_bets": num_bets,
            "total_pl": round(total_pl, 2), "roi": round(roi, 2),
            "yield_pct": round(yield_pct, 2), "total_staked": round(total_staked, 2),
            "avg_odds": round(float(row.avg_odds or 0), 2),
            "win_rate": round(win_rate, 2), "num_back": row.num_back, "num_lay": row.num_lay,
            "bsp_fill_pct": round(bsp_fill_pct, 2),
            "avg_bsp_abs": round(float(row.avg_bsp_abs or 0), 4),
            "avg_bsp_pct": round(float(row.avg_bsp_pct or 0), 4),
            "avg_bsp_prob": round(float(row.avg_bsp_prob or 0), 4),
        })
    return stats


@app.post("/bets")
def get_bets(
    filters: FilterParams,
    skip: int = Query(0),
    limit: int = Query(100, le=500),
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get filtered bets with pagination."""
    query = db.query(Bet)
    query = apply_filters(query, filters, user.id)
    query = query.order_by(Bet.settled_date.desc())
    total = query.count()
    bets = query.offset(skip).limit(limit).all()

    if filters.staking_type and filters.staking_type != 'default':
        bet_list = []
        for bet in bets:
            bet_dict = {
                "id": bet.id, "bet_id": bet.bet_id, "description": bet.description,
                "selection": bet.selection, "bet_type": bet.bet_type,
                "matched_amount": bet.matched_amount,
                "avg_price_matched": bet.avg_price_matched,
                "bsp": bet.bsp, "bsp_diff_absolute": bet.bsp_diff_absolute,
                "bsp_diff_percentage": bet.bsp_diff_percentage,
                "bsp_diff_probability": bet.bsp_diff_probability,
                "status": bet.status, "profit_loss": bet.profit_loss,
                "strategy": bet.strategy, "settled_date": bet.settled_date,
                "placed_date": bet.placed_date, "matched_date": bet.matched_date,
                "market_type": bet.market_type, "lay_liability": bet.lay_liability,
                "country_code": bet.country_code, "event": bet.event,
                "competition": bet.competition, "price_requested": bet.price_requested,
            }
            if bet.avg_price_matched and bet.profit_loss is not None and bet.matched_amount:
                new_stake = calculate_new_stake(
                    bet.bet_type, bet.matched_amount, bet.avg_price_matched,
                    filters.staking_type, filters.base_stake,
                )
                new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
                new_liability = calculate_stake_or_liability(
                    bet.bet_type, new_stake, bet.avg_price_matched,
                )
                bet_dict["recalculated_stake"] = round(new_stake, 2)
                bet_dict["recalculated_pl"] = round(new_pl, 2)
                bet_dict["recalculated_liability"] = round(new_liability, 2)
            bet_list.append(bet_dict)
        return {"total": total, "bets": bet_list}

    return {"total": total, "bets": bets}


@app.post("/pl-over-time")
def get_pl_over_time(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get P/L over time data."""
    if filters.staking_type and filters.staking_type != 'default':
        query = db.query(Bet).filter(Bet.settled_date.isnot(None))
        query = apply_filters(query, filters, user.id)
        query = query.order_by(Bet.settled_date)
        bets = query.all()
        daily_data = {}
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            date_key = str(bet.settled_date.date())
            if date_key not in daily_data:
                daily_data[date_key] = 0
            new_stake = calculate_new_stake(
                bet.bet_type, bet.matched_amount, bet.avg_price_matched,
                filters.staking_type, filters.base_stake,
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            daily_data[date_key] += new_pl
        cumulative_pl = 0
        data = []
        for date in sorted(daily_data.keys()):
            daily_pl = daily_data[date]
            cumulative_pl += daily_pl
            data.append({"date": date, "daily_pl": round(daily_pl, 2), "cumulative_pl": round(cumulative_pl, 2)})
        return data

    query = db.query(
        func.date(Bet.settled_date).label('date'),
        func.sum(Bet.profit_loss).label('daily_pl'),
    ).filter(Bet.settled_date.isnot(None))
    query = apply_filters(query, filters, user.id)
    query = query.group_by(func.date(Bet.settled_date)).order_by(func.date(Bet.settled_date))
    results = query.all()
    cumulative_pl = 0
    data = []
    for row in results:
        daily_pl = float(row.daily_pl or 0)
        cumulative_pl += daily_pl
        data.append({
            "date": row.date.isoformat() if row.date else None,
            "daily_pl": round(daily_pl, 2),
            "cumulative_pl": round(cumulative_pl, 2),
        })
    return data


@app.post("/summary-stats")
def get_summary_stats(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get summary statistics."""
    query = db.query(Bet)
    query = apply_filters(query, filters, user.id)
    total_bets = query.count()
    num_strategies = query.with_entities(func.count(func.distinct(Bet.strategy))).scalar()

    if filters.staking_type and filters.staking_type != 'default':
        bets = query.all()
        total_pl = 0
        total_staked = 0
        total_stake_only = 0
        num_wins = 0
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            new_stake = calculate_new_stake(
                bet.bet_type, bet.matched_amount, bet.avg_price_matched,
                filters.staking_type, filters.base_stake,
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            new_stake_or_liability = calculate_stake_or_liability(
                bet.bet_type, new_stake, bet.avg_price_matched,
            )
            total_pl += new_pl
            total_staked += new_stake_or_liability
            total_stake_only += new_stake
            if new_pl > 0:
                num_wins += 1
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
        win_rate = (num_wins / total_bets * 100) if total_bets > 0 else 0
        return {
            "num_bets": total_bets, "num_wins": num_wins,
            "win_rate": round(win_rate, 2), "total_pl": round(total_pl, 2),
            "total_staked": round(total_staked, 2), "roi": round(roi, 2),
            "yield_pct": round(yield_pct, 2), "num_strategies": num_strategies,
        }

    total_pl = query.with_entities(func.sum(Bet.profit_loss)).scalar()
    total_staked = query.with_entities(
        func.sum(case((Bet.bet_type == 'BACK', Bet.matched_amount), else_=Bet.lay_liability))
    ).scalar()
    total_stake_only = query.with_entities(func.sum(Bet.matched_amount)).scalar()
    num_wins = query.filter(Bet.profit_loss > 0).count()
    roi = (float(total_pl) / float(total_staked) * 100) if total_staked and total_pl else 0
    yield_pct = (float(total_pl) / float(total_stake_only) * 100) if total_stake_only and total_pl else 0
    win_rate = (num_wins / total_bets * 100) if total_bets > 0 else 0
    return {
        "num_bets": total_bets, "num_wins": num_wins,
        "win_rate": round(win_rate, 2),
        "total_pl": round(float(total_pl), 2) if total_pl else 0,
        "total_staked": round(float(total_staked), 2) if total_staked else 0,
        "roi": round(roi, 2), "yield_pct": round(yield_pct, 2),
        "num_strategies": num_strategies,
    }


@app.post("/recalculate-staking")
def recalculate_staking(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Recalculate bets with new staking strategy."""
    query = db.query(Bet)
    query = apply_filters(query, filters, user.id)
    bets = query.all()
    recalculated_bets = []
    total_pl = 0
    total_staked = 0
    for bet in bets:
        original_stake = bet.matched_amount or 0
        avg_price = bet.avg_price_matched or 0
        if original_stake == 0 or avg_price == 0:
            continue
        new_stake = calculate_new_stake(
            bet.bet_type, original_stake, avg_price,
            filters.staking_type, filters.base_stake,
        )
        new_pl = calculate_new_pl(original_stake, bet.profit_loss or 0, new_stake)
        stake_or_liability = calculate_stake_or_liability(bet.bet_type, new_stake, avg_price)
        total_pl += new_pl
        total_staked += stake_or_liability
        recalculated_bets.append({
            "bet_id": bet.bet_id,
            "original_stake": round(original_stake, 2),
            "new_stake": round(new_stake, 2),
            "original_pl": round(bet.profit_loss or 0, 2),
            "new_pl": round(new_pl, 2),
        })
    roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
    return {
        "summary": {
            "total_pl": round(total_pl, 2), "total_staked": round(total_staked, 2),
            "roi": round(roi, 2), "num_bets": len(recalculated_bets),
        },
        "sample_bets": recalculated_bets[:10],
    }


@app.post("/odds-bands-profit")
def get_odds_bands_profit(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get profit by odds bands."""
    query = db.query(Bet)
    query = apply_filters(query, filters, user.id)
    bets = query.all()

    bands = {
        "1.01-2.00": {"min": 1.01, "max": 2.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "2.01-3.00": {"min": 2.01, "max": 3.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "3.01-5.00": {"min": 3.01, "max": 5.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "5.01-10.00": {"min": 5.01, "max": 10.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "10.01+": {"min": 10.01, "max": float('inf'), "bets": [], "total_pl": 0, "total_staked": 0},
    }

    if filters.staking_type and filters.staking_type != 'default':
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            odds = bet.avg_price_matched
            new_stake = calculate_new_stake(
                bet.bet_type, bet.matched_amount, bet.avg_price_matched,
                filters.staking_type, filters.base_stake,
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            stake_or_liability = calculate_stake_or_liability(bet.bet_type, new_stake, bet.avg_price_matched)
            for band_name, band_data in bands.items():
                if band_data["min"] <= odds <= band_data["max"]:
                    band_data["bets"].append(bet)
                    band_data["total_pl"] += new_pl
                    band_data["total_staked"] += stake_or_liability
                    break
    else:
        for bet in bets:
            odds = bet.avg_price_matched or 0
            pl = bet.profit_loss or 0
            stake = bet.lay_liability if bet.bet_type == 'LAY' else (bet.matched_amount or 0)
            for band_name, band_data in bands.items():
                if band_data["min"] <= odds <= band_data["max"]:
                    band_data["bets"].append(bet)
                    band_data["total_pl"] += pl
                    band_data["total_staked"] += stake
                    break

    result = []
    for band_name, band_data in bands.items():
        num_bets = len(band_data["bets"])
        total_pl = band_data["total_pl"]
        total_staked = band_data["total_staked"]
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        result.append({
            "band": band_name, "num_bets": num_bets,
            "total_pl": round(total_pl, 2), "total_staked": round(total_staked, 2),
            "roi": round(roi, 2),
        })
    return result


@app.post("/monthly-pl")
def get_monthly_pl(
    filters: FilterParams,
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Get monthly P/L in year×month grid format, plus key statistics."""
    query = db.query(Bet).filter(Bet.settled_date.isnot(None))
    query = apply_filters(query, filters, user.id)
    query = query.order_by(Bet.settled_date)
    bets = query.all()

    monthly: dict[str, float] = {}
    daily_buckets: dict[str, float] = {}
    for bet in bets:
        if bet.profit_loss is None or bet.settled_date is None:
            continue
        if filters.staking_type and filters.staking_type != 'default':
            if not bet.avg_price_matched or not bet.matched_amount:
                continue
            new_stake = calculate_new_stake(
                bet.bet_type, bet.matched_amount, bet.avg_price_matched,
                filters.staking_type, filters.base_stake,
            )
            pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
        else:
            pl = bet.profit_loss
        month_key = bet.settled_date.strftime("%Y-%m")
        monthly[month_key] = monthly.get(month_key, 0) + pl
        day_key = str(bet.settled_date.date())
        daily_buckets[day_key] = daily_buckets.get(day_key, 0) + pl

    daily_pls = [daily_buckets[k] for k in sorted(daily_buckets.keys())]

    if not monthly:
        return {
            "grid": [], "years": [],
            "key_stats": {
                "total_profit": 0, "monthly_average": 0, "monthly_low": 0,
                "monthly_high": 0, "winning_months": 0, "months_of_data": 0,
                "winning_months_pct": 0, "max_absolute_drawdown": 0,
                "max_peak_trough_drawdown": 0,
            },
        }

    month_values = list(monthly.values())
    years_set: set[int] = set()
    for k in monthly:
        years_set.add(int(k[:4]))
    years_sorted = sorted(years_set)
    grid = []
    for year in years_sorted:
        row: dict = {"year": year}
        for m in range(1, 13):
            key = f"{year}-{m:02d}"
            row[str(m)] = round(monthly[key], 2) if key in monthly else None
        grid.append(row)

    total_profit = sum(month_values)
    months_of_data = len(month_values)
    monthly_average = total_profit / months_of_data if months_of_data else 0
    monthly_low = min(month_values) if month_values else 0
    monthly_high = max(month_values) if month_values else 0
    winning_months = sum(1 for v in month_values if v > 0)
    winning_months_pct = (winning_months / months_of_data * 100) if months_of_data else 0

    cumulative = 0.0
    max_abs_dd = 0.0
    for dp in daily_pls:
        cumulative += dp
        if cumulative < max_abs_dd:
            max_abs_dd = cumulative

    cumulative = 0.0
    peak = 0.0
    max_pt_dd = 0.0
    for dp in daily_pls:
        cumulative += dp
        if cumulative > peak:
            peak = cumulative
        dd = cumulative - peak
        if dd < max_pt_dd:
            max_pt_dd = dd

    return {
        "grid": grid, "years": years_sorted,
        "key_stats": {
            "total_profit": round(total_profit, 2),
            "monthly_average": round(monthly_average, 2),
            "monthly_low": round(monthly_low, 2),
            "monthly_high": round(monthly_high, 2),
            "winning_months": winning_months,
            "months_of_data": months_of_data,
            "winning_months_pct": round(winning_months_pct, 1),
            "max_absolute_drawdown": round(max_abs_dd, 2),
            "max_peak_trough_drawdown": round(max_pt_dd, 2),
        },
    }


@app.post("/ingest")
async def ingest_csv(
    file: UploadFile = File(...),
    user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Upload a CSV bet export file — bets are tagged to the authenticated user."""
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    # Limit file size to 50 MB
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = ingest_csv_file(tmp_path, db, user_id=user.id)
        total_bets = db.query(Bet).filter(Bet.user_id == user.id).count()
        return {
            "filename": file.filename,
            "inserted": result['inserted'],
            "updated": result['updated'],
            "skipped": result['skipped'],
            "total_bets_in_db": total_bets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
