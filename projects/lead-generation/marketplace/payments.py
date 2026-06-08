"""
Credit top-up payments. Two modes (config.PAYMENT_MODE):

- 'manual': no Stripe calls at all. Admin adds credits directly. Safe for testing
            and for the Marceau-Air-first phase (you control the only buyer).
- 'stripe': real Stripe Checkout Session for prepaid credit top-ups. Credits are
            granted ONLY by the verified webhook (checkout.session.completed), never
            on the optimistic redirect — so a closed browser tab can't mint credits.

NOTE: config.STRIPE_IS_LIVE is surfaced to the UI so a live key is never used by
accident during testing.
"""
import config
import models

_stripe = None


def _client():
    global _stripe
    if _stripe is None:
        import stripe
        stripe.api_key = config.STRIPE_SECRET_KEY
        _stripe = stripe
    return _stripe


def create_topup_session(contractor, amount_cents: int) -> dict:
    """Return {'mode','url'|'error'}. In manual mode returns a sentinel the UI handles."""
    if amount_cents < config.MIN_TOPUP_CENTS:
        raise models.MarketplaceError(
            f"Minimum top-up is {config.dollars(config.MIN_TOPUP_CENTS)}.")
    if config.PAYMENT_MODE != "stripe":
        return {"mode": "manual"}
    if not config.STRIPE_SECRET_KEY:
        raise models.MarketplaceError("Stripe not configured (no secret key).")
    stripe = _client()
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=contractor["email"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"{config.BRAND['name']} — account credits"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        metadata={"contractor_id": str(contractor["id"]), "credit_cents": str(amount_cents)},
        success_url=f"{config.BASE_URL}/credits/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{config.BASE_URL}/credits/cancel",
    )
    return {"mode": "stripe", "url": session.url, "session_id": session.id}


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify + process Stripe webhook. Grants credits on completed checkout.

    Idempotent via models.add_credits(stripe_ref=...). Returns a small status dict."""
    if config.PAYMENT_MODE != "stripe":
        return {"ok": False, "reason": "not in stripe mode"}
    stripe = _client()
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise models.MarketplaceError(f"Webhook signature verification failed: {e}")
    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        if s.get("payment_status") != "paid":
            return {"ok": True, "ignored": "not paid"}
        # Credit the AUTHORITATIVE amount Stripe actually captured, never client metadata.
        cents = s.get("amount_total")
        try:
            cid = int((s.get("metadata") or {}).get("contractor_id"))
        except (TypeError, ValueError):
            # Malformed/missing metadata: ACK with 200 so Stripe stops retrying; log for review.
            print(f"[payments] webhook {s.get('id')} missing contractor_id metadata", file=__import__('sys').stderr)
            return {"ok": True, "ignored": "no contractor_id"}
        if not cents or cents <= 0:
            return {"ok": True, "ignored": "no amount_total"}
        bal = models.add_credits(cid, int(cents), kind="credit_purchase",
                                 stripe_ref=s["id"], note="Stripe credit top-up")
        return {"ok": True, "contractor_id": cid, "credited": int(cents), "balance": bal}
    return {"ok": True, "ignored": event["type"]}
