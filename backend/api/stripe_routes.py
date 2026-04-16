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
        mode="subscription",  # works with recurring prices
        payment_method_types=["card"],
        line_items=[{
            "price": plan["price_id"],
            "quantity": 1,
        }],
        metadata={
            "user_id": str(user.id),
            "plan": req.plan,
        },
        subscription_data={
            "metadata": {
                "user_id": str(user.id),
                "plan": req.plan,
            },
        },
        success_url=f"{FRONTEND_URL}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/pricing?payment=cancelled",
    )

    user.stripe_checkout_session_id = session.id
    db.commit()

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


# ---------------------------------------------------------------------------
# Customer Portal — self-service subscription management
# ---------------------------------------------------------------------------
@router.post("/customer-portal")
def create_customer_portal_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Customer Portal session.

    Lets users cancel, change plan, update payment method, and view invoices
    without you having to build any of that UI yourself.
    """
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Please subscribe first.",
        )

    portal_session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{FRONTEND_URL}/account",
    )
    return {"url": portal_session.url}


# ---------------------------------------------------------------------------
# Webhook — Stripe calls this to confirm payment
# ---------------------------------------------------------------------------
# In-memory set of processed event IDs to prevent replay attacks.
# In a multi-process deployment, replace with a DB table or Redis set.
_processed_event_ids: set[str] = set()
_MAX_PROCESSED_EVENTS = 10_000  # cap memory usage


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

    # Idempotency: skip events we've already processed
    event_id = event.get("id")
    if event_id in _processed_event_ids:
        return {"ok": True, "note": "already processed"}
    # Cap memory — evict oldest entries when set grows too large
    if len(_processed_event_ids) >= _MAX_PROCESSED_EVENTS:
        _processed_event_ids.clear()
    _processed_event_ids.add(event_id)

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _activate_subscription(obj, db)

    elif event_type == "customer.subscription.deleted":
        # User cancelled (or Stripe cancelled after failed payments)
        _handle_subscription_cancelled(obj, db)

    elif event_type == "customer.subscription.updated":
        # Plan change, renewal, or status change
        _handle_subscription_updated(obj, db)

    elif event_type == "invoice.payment_failed":
        # Payment failed — mark as past_due so we can warn the user
        _handle_payment_failed(obj, db)

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


def _find_user_by_customer_id(customer_id: str, db: Session) -> User | None:
    """Look up a user by their Stripe customer ID."""
    if not customer_id:
        return None
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()


def _handle_subscription_cancelled(subscription: dict, db: Session):
    """Mark user as cancelled when their Stripe subscription ends."""
    customer_id = subscription.get("customer")
    user = _find_user_by_customer_id(customer_id, db)
    if not user:
        return
    user.subscription_status = "cancelled"
    db.commit()


def _handle_subscription_updated(subscription: dict, db: Session):
    """Sync subscription status when Stripe sends an update.

    Covers plan changes, renewals, and status transitions.
    """
    customer_id = subscription.get("customer")
    user = _find_user_by_customer_id(customer_id, db)
    if not user:
        return

    stripe_status = subscription.get("status")  # active, past_due, canceled, etc.

    if stripe_status == "active":
        user.subscription_status = "active"
        # Update expiry from Stripe's current_period_end
        period_end = subscription.get("current_period_end")
        if period_end:
            user.subscription_expires = datetime.fromtimestamp(period_end, tz=timezone.utc)
    elif stripe_status in ("canceled", "unpaid"):
        user.subscription_status = "cancelled"
    elif stripe_status == "past_due":
        # Keep active for now but could warn the user
        user.subscription_status = "active"

    db.commit()


def _handle_payment_failed(invoice: dict, db: Session):
    """Log payment failure — Stripe retries automatically."""
    customer_id = invoice.get("customer")
    user = _find_user_by_customer_id(customer_id, db)
    if not user:
        return
    # Stripe retries failed payments automatically.
    # After all retries fail, it fires customer.subscription.deleted.
    # For now we just keep the user active and let Stripe handle retries.
    import logging
    logging.getLogger(__name__).warning(
        "Payment failed for user %s (customer %s)", user.id, customer_id
    )


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
