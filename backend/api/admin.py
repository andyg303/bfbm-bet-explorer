"""
Admin API endpoints — restricted to users with is_admin=True.

Security: the `require_admin` dependency verifies the JWT *and* checks
`is_admin` on every request.  The is_admin flag can only be set directly
in the database — there is no API to promote users.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, case, desc
from datetime import datetime, timezone, timedelta
from typing import Optional
import json

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db, User, Bet, IngestionLog
from api.auth import create_access_token, get_current_user, user_to_auth_dict

router = APIRouter(prefix="/admin", tags=["admin"])
IMPERSONATION_TOKEN_MINUTES = int(os.getenv("ADMIN_IMPERSONATION_EXPIRE_MINUTES", "60"))


class ReferralCreditAdjustRequest(BaseModel):
    credits: int


# ─── Security dependency ─────────────────────────────────────────────────────
async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Reject non-admin users with a generic 403 (don't reveal admin exists)."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


# ─── Dashboard overview stats ─────────────────────────────────────────────────
@router.get("/stats")
def admin_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """High-level platform stats for the admin dashboard."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_subscribers = (
        db.query(func.count(User.id))
        .filter(User.subscription_status == "active")
        .scalar() or 0
    )
    new_users_7d = (
        db.query(func.count(User.id))
        .filter(User.created_at >= week_ago)
        .scalar() or 0
    )
    new_users_30d = (
        db.query(func.count(User.id))
        .filter(User.created_at >= month_ago)
        .scalar() or 0
    )
    total_bets = db.query(func.count(Bet.id)).scalar() or 0
    total_ingestions = db.query(func.count(IngestionLog.id)).scalar() or 0
    failed_ingestions = (
        db.query(func.count(IngestionLog.id))
        .filter(IngestionLog.status == "error")
        .scalar() or 0
    )

    # Subscription breakdown
    sub_breakdown = (
        db.query(User.subscription_status, func.count(User.id))
        .group_by(User.subscription_status)
        .all()
    )

    return {
        "total_users": total_users,
        "active_subscribers": active_subscribers,
        "new_users_7d": new_users_7d,
        "new_users_30d": new_users_30d,
        "total_bets": total_bets,
        "total_ingestions": total_ingestions,
        "failed_ingestions": failed_ingestions,
        "subscription_breakdown": {s: c for s, c in sub_breakdown},
    }


# ─── User list ────────────────────────────────────────────────────────────────
@router.get("/users")
def admin_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
):
    """Paginated user list with bet counts."""
    bet_count_sub = (
        db.query(Bet.user_id, func.count(Bet.id).label("bet_count"))
        .group_by(Bet.user_id)
        .subquery()
    )

    q = (
        db.query(
            User.id,
            User.email,
            User.display_name,
            User.is_admin,
            User.is_active,
            User.subscription_status,
            User.subscription_plan,
            User.subscription_expires,
            User.stripe_customer_id,
            User.created_at,
            User.updated_at,
            User.failed_login_attempts,
            User.locked_until,
            User.referral_code,
            User.referred_by_user_id,
            User.referral_credit_balance,
            User.referral_credits_awarded,
            User.referral_credits_redeemed,
            func.coalesce(bet_count_sub.c.bet_count, 0).label("bet_count"),
        )
        .outerjoin(bet_count_sub, User.id == bet_count_sub.c.user_id)
    )

    if search:
        like = f"%{search}%"
        q = q.filter(
            (User.email.ilike(like)) | (User.display_name.ilike(like))
        )

    # Sorting
    sort_col = {
        "created_at": User.created_at,
        "email": User.email,
        "bet_count": bet_count_sub.c.bet_count,
        "subscription_status": User.subscription_status,
        "referral_credit_balance": User.referral_credit_balance,
    }.get(sort, User.created_at)

    q = q.order_by(desc(sort_col) if order == "desc" else sort_col)

    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()

    users = []
    for r in rows:
        users.append({
            "id": r.id,
            "email": r.email,
            "display_name": r.display_name,
            "is_admin": r.is_admin or False,
            "is_active": r.is_active,
            "subscription_status": r.subscription_status or "inactive",
            "subscription_plan": r.subscription_plan,
            "subscription_expires": r.subscription_expires.isoformat() if r.subscription_expires else None,
            "stripe_customer_id": r.stripe_customer_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "bet_count": r.bet_count,
            "failed_login_attempts": r.failed_login_attempts or 0,
            "locked_until": r.locked_until.isoformat() if r.locked_until else None,
            "referral_code": r.referral_code,
            "referred_by_user_id": r.referred_by_user_id,
            "referral_credit_balance": r.referral_credit_balance or 0,
            "referral_credits_awarded": r.referral_credits_awarded or 0,
            "referral_credits_redeemed": r.referral_credits_redeemed or 0,
        })

    return {"users": users, "total": total, "page": page, "per_page": per_page}


@router.post("/users/{target_user_id}/impersonate")
def impersonate_user(
    target_user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a short-lived read-only access token for viewing a user's dashboard."""
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_admin:
        raise HTTPException(status_code=400, detail="Cannot impersonate an admin user")
    if not target.is_active:
        raise HTTPException(status_code=400, detail="Cannot impersonate an inactive user")

    token_version = target.token_version if hasattr(target, "token_version") else 0
    access_token = create_access_token(
        {
            "sub": str(target.id),
            "tv": token_version or 0,
            "impersonated_by": admin.id,
            "read_only": True,
        },
        expires_delta=timedelta(minutes=IMPERSONATION_TOKEN_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": IMPERSONATION_TOKEN_MINUTES,
        "read_only": True,
        "user": user_to_auth_dict(target),
        "impersonator": user_to_auth_dict(admin),
    }


# ─── Ingestion log / error log ────────────────────────────────────────────────
@router.get("/ingestion-logs")
def admin_ingestion_logs(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: Optional[int] = Query(None),
):
    """Paginated ingestion log — filter by status or user."""
    q = (
        db.query(IngestionLog, User.email, User.display_name)
        .join(User, IngestionLog.user_id == User.id)
    )

    if status_filter:
        q = q.filter(IngestionLog.status == status_filter)
    if user_id:
        q = q.filter(IngestionLog.user_id == user_id)

    q = q.order_by(desc(IngestionLog.created_at))
    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()

    logs = []
    for log, email, display_name in rows:
        warnings = []
        if log.warnings:
            try:
                warnings = json.loads(log.warnings)
            except (json.JSONDecodeError, TypeError):
                warnings = [log.warnings]
        logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": email,
            "user_display_name": display_name,
            "filename": log.filename,
            "status": log.status,
            "rows_total": log.rows_total,
            "rows_inserted": log.rows_inserted,
            "rows_updated": log.rows_updated,
            "rows_skipped": log.rows_skipped,
            "error_message": log.error_message,
            "warnings": warnings,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {"logs": logs, "total": total, "page": page, "per_page": per_page}


# ─── Toggle user active status ───────────────────────────────────────────────
@router.post("/users/{target_user_id}/toggle-active")
def toggle_user_active(
    target_user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Enable/disable a user account."""
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot disable your own account")
    target.is_active = not target.is_active
    # Invalidate their tokens if disabling
    if not target.is_active:
        target.token_version = (target.token_version or 0) + 1
    db.commit()
    return {"id": target.id, "is_active": target.is_active}


# ─── Unlock locked account ───────────────────────────────────────────────────
@router.post("/users/{target_user_id}/unlock")
def unlock_user(
    target_user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset failed login attempts and unlock a user account."""
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.failed_login_attempts = 0
    target.locked_until = None
    db.commit()
    return {"id": target.id, "locked_until": None, "failed_login_attempts": 0}


# ─── Referrals ───────────────────────────────────────────────────────────────
@router.get("/referrals")
def admin_referrals(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Referral attribution and credit overview."""
    Referrer = aliased(User)
    Referred = aliased(User)
    referral_count = func.count(Referred.id).label("referral_count")
    qualified_count = func.coalesce(
        func.sum(case((Referred.referral_rewarded_at.isnot(None), 1), else_=0)),
        0,
    ).label("qualified_referral_count")

    total_referral_signups = (
        db.query(func.count(User.id))
        .filter(User.referred_by_user_id.isnot(None))
        .scalar() or 0
    )
    qualified_referrals = (
        db.query(func.count(User.id))
        .filter(User.referral_rewarded_at.isnot(None))
        .scalar() or 0
    )

    top_rows = (
        db.query(
            Referrer.id,
            Referrer.email,
            Referrer.display_name,
            Referrer.referral_code,
            Referrer.referral_credit_balance,
            Referrer.referral_credits_awarded,
            Referrer.referral_credits_redeemed,
            referral_count,
            qualified_count,
            func.max(Referred.created_at).label("latest_referral_at"),
        )
        .outerjoin(Referred, Referred.referred_by_user_id == Referrer.id)
        .filter(
            (Referred.id.isnot(None))
            | (func.coalesce(Referrer.referral_credit_balance, 0) > 0)
            | (func.coalesce(Referrer.referral_credits_awarded, 0) > 0)
        )
        .group_by(
            Referrer.id,
            Referrer.email,
            Referrer.display_name,
            Referrer.referral_code,
            Referrer.referral_credit_balance,
            Referrer.referral_credits_awarded,
            Referrer.referral_credits_redeemed,
        )
        .order_by(desc(qualified_count), desc(referral_count))
        .limit(50)
        .all()
    )

    referral_rows = (
        db.query(Referred, Referrer)
        .join(Referrer, Referred.referred_by_user_id == Referrer.id)
        .order_by(desc(Referred.created_at))
        .limit(200)
        .all()
    )

    return {
        "stats": {
            "total_referral_signups": total_referral_signups,
            "qualified_referrals": qualified_referrals,
            "pending_referrals": max(total_referral_signups - qualified_referrals, 0),
            "total_credit_balance": db.query(func.coalesce(func.sum(User.referral_credit_balance), 0)).scalar() or 0,
            "total_credits_awarded": db.query(func.coalesce(func.sum(User.referral_credits_awarded), 0)).scalar() or 0,
            "total_credits_redeemed": db.query(func.coalesce(func.sum(User.referral_credits_redeemed), 0)).scalar() or 0,
        },
        "top_referrers": [
            {
                "id": r.id,
                "email": r.email,
                "display_name": r.display_name,
                "referral_code": r.referral_code,
                "referral_credit_balance": r.referral_credit_balance or 0,
                "referral_credits_awarded": r.referral_credits_awarded or 0,
                "referral_credits_redeemed": r.referral_credits_redeemed or 0,
                "referral_count": r.referral_count or 0,
                "qualified_referral_count": r.qualified_referral_count or 0,
                "latest_referral_at": r.latest_referral_at.isoformat() if r.latest_referral_at else None,
            }
            for r in top_rows
        ],
        "referrals": [
            {
                "referred_user_id": referred.id,
                "referred_email": referred.email,
                "referred_display_name": referred.display_name,
                "referred_created_at": referred.created_at.isoformat() if referred.created_at else None,
                "referred_subscription_status": referred.subscription_status or "inactive",
                "referral_rewarded_at": referred.referral_rewarded_at.isoformat() if referred.referral_rewarded_at else None,
                "referrer_id": referrer.id,
                "referrer_email": referrer.email,
                "referrer_display_name": referrer.display_name,
                "referrer_code": referrer.referral_code,
            }
            for referred, referrer in referral_rows
        ],
    }


@router.post("/users/{target_user_id}/referral-credits")
def adjust_referral_credits(
    target_user_id: int,
    req: ReferralCreditAdjustRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Manually add or remove referral credits from a user."""
    if req.credits == 0 or abs(req.credits) > 100:
        raise HTTPException(status_code=400, detail="Credit adjustment must be between -100 and 100")
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    new_balance = (target.referral_credit_balance or 0) + req.credits
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Credit balance cannot go below zero")
    target.referral_credit_balance = new_balance
    if req.credits > 0:
        target.referral_credits_awarded = (target.referral_credits_awarded or 0) + req.credits
    db.commit()
    return {
        "id": target.id,
        "referral_credit_balance": target.referral_credit_balance or 0,
        "referral_credits_awarded": target.referral_credits_awarded or 0,
        "referral_credits_redeemed": target.referral_credits_redeemed or 0,
    }
