import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db, User
from api.auth import get_current_user, require_write_session

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3080")
REFERRAL_CREDIT_GBP = 10
REFERRAL_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

router = APIRouter(prefix="/referrals", tags=["referrals"])


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def generate_referral_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(REFERRAL_ALPHABET) for _ in range(8))
        exists = db.query(User.id).filter(func.upper(User.referral_code) == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Could not generate referral code")


def ensure_referral_code(user: User, db: Session) -> str:
    if not user.referral_code:
        user.referral_code = generate_referral_code(db)
        db.commit()
        db.refresh(user)
    return user.referral_code


def find_referrer_by_code(db: Session, code: str | None) -> User | None:
    clean = (code or "").strip().upper()
    if not clean:
        return None
    return (
        db.query(User)
        .filter(func.upper(User.referral_code) == clean, User.is_active == True)  # noqa: E712
        .first()
    )


def award_referrer_credit(referred_user: User, db: Session) -> None:
    if not referred_user.referred_by_user_id or referred_user.referral_rewarded_at:
        return
    referrer = db.query(User).filter(User.id == referred_user.referred_by_user_id).first()
    if not referrer:
        return
    referrer.referral_credit_balance = (referrer.referral_credit_balance or 0) + 1
    referrer.referral_credits_awarded = (referrer.referral_credits_awarded or 0) + 1
    referred_user.referral_rewarded_at = datetime.now(timezone.utc)


def mark_referral_credit_redeemed(user: User, session_id: str | None) -> None:
    if (
        not session_id
        or user.referral_pending_checkout_session_id != session_id
        or user.referral_last_redeemed_session_id == session_id
    ):
        return
    user.referral_credit_balance = max((user.referral_credit_balance or 0) - 1, 0)
    user.referral_credits_redeemed = (user.referral_credits_redeemed or 0) + 1
    user.referral_last_redeemed_session_id = session_id
    user.referral_pending_checkout_session_id = None


@router.get("/me")
def my_referrals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_write_session(user)
    code = ensure_referral_code(user, db)
    referred_by = None
    if user.referred_by_user_id:
        referrer = db.query(User).filter(User.id == user.referred_by_user_id).first()
        if referrer:
            referred_by = {
                "id": referrer.id,
                "display_name": referrer.display_name,
                "email": referrer.email,
                "referral_code": referrer.referral_code,
            }

    referrals = (
        db.query(User)
        .filter(User.referred_by_user_id == user.id)
        .order_by(User.created_at.desc())
        .all()
    )

    return {
        "referral_code": code,
        "referral_url": f"{FRONTEND_URL}/register?ref={code}",
        "credit_value_gbp": REFERRAL_CREDIT_GBP,
        "credit_balance": user.referral_credit_balance or 0,
        "credits_awarded": user.referral_credits_awarded or 0,
        "credits_redeemed": user.referral_credits_redeemed or 0,
        "referred_by": referred_by,
        "referrals": [
            {
                "id": r.id,
                "display_name": r.display_name,
                "email": r.email,
                "created_at": _dt(r.created_at),
                "subscription_status": r.subscription_status or "inactive",
                "subscription_plan": r.subscription_plan,
                "subscription_expires": _dt(r.subscription_expires),
                "reward_earned": bool(r.referral_rewarded_at),
                "reward_earned_at": _dt(r.referral_rewarded_at),
            }
            for r in referrals
        ],
    }
