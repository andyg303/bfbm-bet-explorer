# Stripe Setup Guide — BFBM Bet Explorer

## Overview

Stripe handles payments for the 6-month (£40) and 12-month (£60) subscription plans.  
Everything can be tested locally with **test mode** keys and the **Stripe CLI** — no real money involved.

---

## Step 1 — Get your Test API Keys

1. Go to [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)
2. Make sure **"Test mode"** toggle is ON (top-right of the dashboard)
3. Copy:
   - **Publishable key** → `pk_test_...`
   - **Secret key** → `sk_test_...` (click "Reveal test key")
4. Paste both into your `.env`:
   ```
   STRIPE_SECRET_KEY=<your-secret-key-here>
   STRIPE_PUBLISHABLE_KEY=<your-publishable-key-here>
   ```

---

## Step 2 — Create the Price Objects

Still in Stripe Dashboard (test mode):

1. Go to **Products** → **+ Add product**
2. Create first product:
   - **Name:** `BFBM 6 Month Access`
   - **Pricing:** One-time, **£40.00 GBP**
   - Save → copy the `price_...` ID from the product page
3. Create second product:
   - **Name:** `BFBM 12 Month Access`
   - **Pricing:** One-time, **£60.00 GBP**
   - Save → copy the `price_...` ID
4. Paste into `.env`:
   ```
   STRIPE_PRICE_6MONTH=price_XXXXXXXXXXXXXXXXXXXXXXXX
   STRIPE_PRICE_12MONTH=price_XXXXXXXXXXXXXXXXXXXXXXXX
   ```

---

## Step 3 — Install the Stripe CLI (for local webhook testing)

The Stripe CLI forwards webhook events to your localhost — this is how Stripe "tells"
your backend that a payment succeeded.

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Linux
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee /etc/apt/sources.list.d/stripe.list
sudo apt update && sudo apt install stripe
```

---

## Step 4 — Login to Stripe CLI

```bash
stripe login
```

This opens a browser window — authorise the CLI with your Stripe account.

---

## Step 5 — Forward Webhooks to Localhost

Open a **new terminal** and run:

```bash
stripe listen --forward-to localhost:8000/stripe/webhook
```

This will output a **webhook signing secret** like:
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxxxx
```

Copy that and paste into `.env`:
```
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxx
```

**Keep this terminal running** while you test payments.

---

## Step 6 — Test a Payment

1. Start your backend: `cd backend && uvicorn api.main:app --reload`
2. Start your frontend: `cd frontend && npm run dev`
3. Register a new account
4. You'll be redirected to the Pricing page
5. Click a plan → Stripe Checkout opens
6. Use test card: `4242 4242 4242 4242`, any future expiry, any CVC, any postcode
7. Payment completes → you're redirected back → subscription is activated

### Test Card Numbers

| Card Number          | Description          |
|---------------------|----------------------|
| `4242 4242 4242 4242` | Succeeds             |
| `4000 0000 0000 3220` | Requires 3D Secure   |
| `4000 0000 0000 9995` | Declined              |

---

## Step 7 — Production Setup

When going live:

1. Toggle **off** Test mode in Stripe Dashboard
2. Copy **live** keys into `.env`
3. Create **live** Price objects and update the IDs
4. In Stripe Dashboard → **Developers** → **Webhooks** → **+ Add endpoint**:
   - URL: `https://bfbmbetexplorer.com/api/stripe/webhook`
   - Events: `checkout.session.completed`
   - Copy the signing secret into `STRIPE_WEBHOOK_SECRET`
5. You no longer need the Stripe CLI — Stripe sends webhooks directly to your server

---

## How the Payment Flow Works

```
User clicks "Subscribe"
        ↓
Backend creates Stripe Checkout Session
        ↓
User is redirected to Stripe's hosted payment page
        ↓
User pays with card
        ↓
Stripe sends webhook → POST /stripe/webhook
        ↓
Backend activates subscription (subscription_status = "active")
        ↓
User is redirected back to app → sees dashboard
```

If the webhook is delayed, the app also has a fallback:
the frontend calls `GET /stripe/verify-session/{id}` after redirect,
which checks the payment status directly with Stripe's API.
