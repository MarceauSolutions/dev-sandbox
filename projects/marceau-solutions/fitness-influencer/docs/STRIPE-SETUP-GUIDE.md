# Stripe Setup Guide - Fitness Influencer MCP

**Version**: 1.0
**Date**: 2026-01-16
**Status**: Planning Phase

---

## Executive Summary

This document outlines the Stripe configuration required to support the Fitness Influencer MCP pricing tiers. The current implementation uses **Option B: Local JSON + Manual Stripe** (as decided in `workflows/pricing-implementation-plan.md`), meaning:

1. Stripe handles payment collection via Payment Links
2. Manual process to add subscribers to `~/.fitness_mcp_pro_users.json`
3. `subscription_manager.py` enforces tier-based limits

---

## Pricing Tiers

| Tier | Monthly | Annual (20% off) | Stripe Product Name |
|------|---------|------------------|---------------------|
| **Starter** | $19/month | $182.40/year ($15.20/mo) | `fitness_mcp_starter` |
| **Pro** | $49/month | $470.40/year ($39.20/mo) | `fitness_mcp_pro` |
| **Agency** | $149/month | $1,430.40/year ($119.20/mo) | `fitness_mcp_agency` |

### Annual Pricing Calculation

| Tier | Monthly x 12 | 20% Discount | Annual Price |
|------|--------------|--------------|--------------|
| Starter | $228 | -$45.60 | **$182.40** |
| Pro | $588 | -$117.60 | **$470.40** |
| Agency | $1,788 | -$357.60 | **$1,430.40** |

---

## Stripe Products to Create

### Product 1: Fitness MCP Starter

**Dashboard Location**: Products > Add Product

```
Name: Fitness Influencer MCP - Starter
Description: Enhanced limits for growing fitness creators. 25 video jump-cuts/month, unlimited comments, workout plans, and calendars.

Price 1 (Monthly):
  - Amount: $19.00 USD
  - Billing period: Monthly
  - Price ID naming: price_starter_monthly

Price 2 (Annual):
  - Amount: $182.40 USD
  - Billing period: Yearly
  - Price ID naming: price_starter_annual
```

### Product 2: Fitness MCP Pro

```
Name: Fitness Influencer MCP - Pro
Description: Full access for serious fitness creators. Unlimited video editing, comments, workout plans, calendars, and 20 AI images/month.

Price 1 (Monthly):
  - Amount: $49.00 USD
  - Billing period: Monthly
  - Price ID naming: price_pro_monthly

Price 2 (Annual):
  - Amount: $470.40 USD
  - Billing period: Yearly
  - Price ID naming: price_pro_annual
```

### Product 3: Fitness MCP Agency

```
Name: Fitness Influencer MCP - Agency
Description: Multi-client access for agencies. Everything in Pro plus manage 10+ clients, API access, white-label reports, and 50 AI images/month.

Price 1 (Monthly):
  - Amount: $149.00 USD
  - Billing period: Monthly
  - Price ID naming: price_agency_monthly

Price 2 (Annual):
  - Amount: $1,430.40 USD
  - Billing period: Yearly
  - Price ID naming: price_agency_annual
```

---

## Stripe Payment Links to Create

For each product/price combination, create a Payment Link:

### Payment Links Configuration

| Link Name | Product | Price | After Payment |
|-----------|---------|-------|---------------|
| `fitness-starter-monthly` | Starter | $19/mo | Thank you page |
| `fitness-starter-annual` | Starter | $182.40/yr | Thank you page |
| `fitness-pro-monthly` | Pro | $49/mo | Thank you page |
| `fitness-pro-annual` | Pro | $470.40/yr | Thank you page |
| `fitness-agency-monthly` | Agency | $149/mo | Thank you page |
| `fitness-agency-annual` | Agency | $1,430.40/yr | Thank you page |

**Payment Link Settings**:
- Collect customer email: Required
- Collect billing address: Optional (for invoices)
- Confirmation page: Custom URL or Stripe-hosted
- Allow promotion codes: Optional (for launch discounts)

---

## Environment Variables

Add to `.env` (and `.env.example`):

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...  # For future webhook integration

# Payment Links (for landing page)
STRIPE_LINK_STARTER_MONTHLY=https://buy.stripe.com/...
STRIPE_LINK_STARTER_ANNUAL=https://buy.stripe.com/...
STRIPE_LINK_PRO_MONTHLY=https://buy.stripe.com/...
STRIPE_LINK_PRO_ANNUAL=https://buy.stripe.com/...
STRIPE_LINK_AGENCY_MONTHLY=https://buy.stripe.com/...
STRIPE_LINK_AGENCY_ANNUAL=https://buy.stripe.com/...
```

---

## Manual Subscription Process (Phase 1)

Until webhook automation is implemented, follow this process:

### When a Customer Pays

1. **Check Stripe Dashboard**
   - Go to: Stripe Dashboard > Payments
   - Look for new payments with status "Succeeded"

2. **Get Customer Details**
   - Customer email
   - Customer ID (e.g., `cus_xxx123`)
   - Subscription ID (e.g., `sub_xxx123`)
   - Tier purchased (from product name)

3. **Add to Subscriber List**
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
   python -m src.fitness_influencer_mcp.subscription_manager \
     --add "customer@email.com" "pro" "cus_xxx123"
   ```

4. **Verify Subscription**
   ```bash
   python -m src.fitness_influencer_mcp.subscription_manager \
     --check "customer@email.com"
   ```

5. **Send Welcome Email** (manual for now)
   - Confirm subscription tier
   - Provide getting started guide
   - Support contact info

### When a Customer Cancels

1. **Check Stripe Dashboard for Cancellations**
   - Go to: Subscriptions > Filter by "Canceled"

2. **Remove from Subscriber List**
   ```bash
   python -m src.fitness_influencer_mcp.subscription_manager \
     --remove "customer@email.com"
   ```

3. **Send Cancellation Confirmation**
   - Access continues until end of billing period
   - Offer feedback survey

---

## Future: Stripe Webhook Integration (Phase 2)

When ready to automate, implement webhooks for these events:

### Events to Handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Add subscriber |
| `customer.subscription.created` | Add subscriber |
| `customer.subscription.updated` | Update tier (upgrade/downgrade) |
| `customer.subscription.deleted` | Remove subscriber |
| `invoice.payment_failed` | Send reminder, mark at-risk |

### Webhook Endpoint

```python
# Future: src/fitness_influencer_mcp/stripe_webhook.py

from flask import Flask, request
import stripe
from .subscription_manager import SubscriptionManager

app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    manager = SubscriptionManager()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session["customer_email"]
        customer_id = session["customer"]
        # Determine tier from line items
        tier = determine_tier_from_session(session)
        manager.add_subscriber(email, tier, customer_id)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        # Look up email from customer_id
        customer = stripe.Customer.retrieve(customer_id)
        manager.remove_subscriber(customer["email"])

    return "", 200
```

---

## Stripe Dashboard Setup Checklist

### Account Setup
- [ ] Create Stripe account at stripe.com
- [ ] Complete business verification
- [ ] Add bank account for payouts
- [ ] Enable test mode first

### Products Setup
- [ ] Create "Fitness MCP Starter" product
  - [ ] Add $19/month price
  - [ ] Add $182.40/year price
- [ ] Create "Fitness MCP Pro" product
  - [ ] Add $49/month price
  - [ ] Add $470.40/year price
- [ ] Create "Fitness MCP Agency" product
  - [ ] Add $149/month price
  - [ ] Add $1,430.40/year price

### Payment Links Setup
- [ ] Create Starter monthly payment link
- [ ] Create Starter annual payment link
- [ ] Create Pro monthly payment link
- [ ] Create Pro annual payment link
- [ ] Create Agency monthly payment link
- [ ] Create Agency annual payment link

### Testing
- [ ] Test each payment link in test mode
- [ ] Verify email collection works
- [ ] Test subscription management CLI

### Go Live
- [ ] Switch to live mode
- [ ] Update payment links in landing page
- [ ] Document payment link URLs in `.env`

---

## Integration Points

### Existing Files That Reference Stripe

| File | Purpose |
|------|---------|
| `src/fitness_influencer_mcp/subscription_manager.py` | Stores Stripe customer IDs |
| `workflows/pricing-implementation-plan.md` | Implementation roadmap |
| `MONETIZATION.md` | Business strategy |
| `NEXT-STEPS.md` | Phase planning |

### Files to Update After Stripe Setup

| File | Update |
|------|--------|
| `.env.example` | Add STRIPE_* variables |
| `landing-page/index.html` | Add payment link buttons |
| `README.md` | Add pricing section |

---

## Pricing Display Recommendations

### Landing Page Pricing Cards

```html
<!-- Starter -->
<div class="pricing-card">
  <h3>Starter</h3>
  <div class="price">$19<span>/month</span></div>
  <div class="annual">or $182.40/year (save 20%)</div>
  <ul>
    <li>25 video jump-cuts/month</li>
    <li>Unlimited comment categorization</li>
    <li>Unlimited workout plans</li>
    <li>Unlimited content calendars</li>
    <li>10 AI images/month</li>
  </ul>
  <a href="[STRIPE_LINK_STARTER_MONTHLY]" class="btn">Get Started</a>
</div>

<!-- Pro (Most Popular) -->
<div class="pricing-card featured">
  <span class="badge">Most Popular</span>
  <h3>Pro</h3>
  <div class="price">$49<span>/month</span></div>
  <div class="annual">or $470.40/year (save 20%)</div>
  <ul>
    <li>Unlimited video jump-cuts</li>
    <li>Unlimited comment categorization</li>
    <li>Unlimited workout plans</li>
    <li>Unlimited content calendars</li>
    <li>20 AI images/month</li>
    <li>Priority support</li>
  </ul>
  <a href="[STRIPE_LINK_PRO_MONTHLY]" class="btn primary">Get Started</a>
</div>

<!-- Agency -->
<div class="pricing-card">
  <h3>Agency</h3>
  <div class="price">$149<span>/month</span></div>
  <div class="annual">or $1,430.40/year (save 20%)</div>
  <ul>
    <li>Everything in Pro</li>
    <li>Manage 10+ clients</li>
    <li>API access</li>
    <li>White-label reports</li>
    <li>50 AI images/month</li>
    <li>Priority support</li>
  </ul>
  <a href="[STRIPE_LINK_AGENCY_MONTHLY]" class="btn">Contact Sales</a>
</div>
```

---

## Revenue Projections with New Pricing

| Scenario | Starter | Pro | Agency | Monthly | Annual |
|----------|---------|-----|--------|---------|--------|
| Conservative | 5 x $19 | 3 x $49 | 1 x $149 | $391 | $4,692 |
| Expected | 15 x $19 | 10 x $49 | 3 x $149 | $1,222 | $14,664 |
| Optimistic | 50 x $19 | 30 x $49 | 10 x $149 | $3,910 | $46,920 |

---

## Next Steps

1. **Immediate**: Create Stripe account and products (test mode)
2. **This Week**: Create payment links and test flow
3. **Next Week**: Update landing page with payment links
4. **Month 2**: Implement webhook automation (if volume warrants)

---

## References

- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Payment Links: https://stripe.com/docs/payment-links
- Stripe Webhooks: https://stripe.com/docs/webhooks
- `subscription_manager.py`: `/Users/williammarceaujr./dev-sandbox/projects/fitness-influencer/src/fitness_influencer_mcp/subscription_manager.py`
- `pricing-implementation-plan.md`: `/Users/williammarceaujr./dev-sandbox/projects/fitness-influencer/workflows/pricing-implementation-plan.md`
