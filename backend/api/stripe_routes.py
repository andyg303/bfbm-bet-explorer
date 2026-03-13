"""
Stripe payment integration for BFBM Bet Explorer subscriptions.

Handles:
  • Creating Stripe Checkout sessions (6-month / 12-month plans)
  • Webhook processing for automatic subscription activation
  • Subscription status queries
"""

import os
import stripe
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db, User
from api.auth import get_current_user

# ---------------------------------------------------------------------------
# Stripe config
# ---------------------------------------------------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3080")

# Price IDs set up in Stripe Dashboard (or created via API)
PRICE_6MONTH = os.getenv("STRIPE_PRICE_6MONTH", "")
PRICE_12MONTH = os.getenv("STRIPE_PRICE_12MONTH", "")

PLAN_MAP = {
    "6month": {"price_id": PRICE_6MONTH, "months": 6, "label": "6 Month Access"},
    "12month": {"price_id": PRICE_12MONTH, "months": 12, "label": "12 Month Access"},
}

router = APIRouter(prefix="/stripe", tags=["stripe"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateCheckoutRequest(BaseModel):
    plan: str  # "6month" | "12month"


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


# ---------------------------------------------------------------------------
# Create Checkout Session
# ---------------------------------------------------------------------------
@router.post("/create-checkout-session", response_model=CheckoutResponse)
def create_checkout_session(
    req: CreateCheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout Session for the chosen plan."""
    if req.plan not in PLAN_MAP:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose '6month' or '12month'.")

    plan = PLAN_MAP[req.plan]
    if not plan["price_id"]:
        raise HTTPException(
            status_code=500,
            detail="Stripe price ID not configured for this plan. Contact support.",
        )

    # Re-use or create Stripe customer
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.display_name or user.email,
            metadata={"user_id": str(user.id)},
        )
        customer_id = customer.id
        user.stripe_customer_id = customer_id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="payment",  # one-off payment, not recurring
        payment_method_types=["card"],
        line_items=[{
            "price": plan["price_id"],
            "quantity": 1,
        }],
        metadata={
            "user_id": str(user.id),
            "plan": req.plan,
        },
        success_url=f"{FRONTEND_URL}?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}?payment=cancelled",
    )

    user.stripe_checkout_session_id = session.id
    db.commit()

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


# ---------------------------------------------------------------------------
# Webhook — Stripe calls this to confirm payment
# ---------------------------------------------------------------------------
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.
    The main event we care about is `checkout.session.completed`.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _activate_subscription(session, db)

    return {"ok": True}


def _activate_subscription(session: dict, db: Session):
    """Activate subscription after successful payment."""
    metadata = session.get("metadata", {})
    user_id = metadata.get("user_id")
    plan_key = metadata.get("plan")

    if not user_id or not plan_key:
        return  # Can't process without metadata

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return

    plan = PLAN_MAP.get(plan_key)
    if not plan:
        return

    now = datetime.now(timezone.utc)
    # If user already has an active sub that hasn't expired, extend from expiry
    if (
        user.subscription_status == "active"
        and user.subscription_expires
        and user.subscription_expires > now
    ):
        base = user.subscription_expires
    else:
        base = now

    user.subscription_status = "active"
    user.subscription_plan = plan_key
    if not user.subscription_start:
        user.subscription_start = now
    user.subscription_expires = base + relativedelta(months=plan["months"])
    user.stripe_customer_id = session.get("customer", user.stripe_customer_id)
    db.commit()


# ---------------------------------------------------------------------------
# Subscription status (for frontend polling)
# ---------------------------------------------------------------------------
@router.get("/subscription-status")
def subscription_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the user's current subscription info."""
    now = datetime.now(timezone.utc)

    # Auto-expire if past date
    if (
        user.subscription_status == "active"
        and user.subscription_expires
        and user.subscription_expires <= now
    ):
        user.subscription_status = "expired"
        db.commit()

    return {
        "status": user.subscription_status,
        "plan": user.subscription_plan,
        "expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
        "is_active": user.subscription_status == "active",
    }


# ---------------------------------------------------------------------------
# Verify a checkout session (called by frontend after redirect)
# ---------------------------------------------------------------------------
@router.get("/verify-session/{session_id}")
def verify_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify payment was completed and activate if webhook hasn't fired yet."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.payment_status != "paid":
        return {"activated": False, "payment_status": session.payment_status}

    # Check the session belongs to this user
    metadata = session.get("metadata", {})
    if str(metadata.get("user_id")) != str(user.id):
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    # Activate if not already active
    if user.subscription_status != "active":
        _activate_subscription(dict(session), db)

    return {
        "activated": True,
        "status": user.subscription_status,
        "plan": user.subscription_plan,
        "expires": user.subscription_expires.isoformat() if user.subscription_expires else None,
    }
