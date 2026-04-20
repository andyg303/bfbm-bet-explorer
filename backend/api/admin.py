"""
Admin API endpoints — restricted to users with is_admin=True.

Security: the `require_admin` dependency verifies the JWT *and* checks
`is_admin` on every request.  The is_admin flag can only be set directly
in the database — there is no API to promote users.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from datetime import datetime, timezone, timedelta
from typing import Optional
import json

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db, User, Bet, IngestionLog
from api.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


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
        })

    return {"users": users, "total": total, "page": page, "per_page": per_page}


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
