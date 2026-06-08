"""
HVAC Appointment Marketplace — Flask app.

Pay structure mirrors RoofProspect.ai: prepaid credit wallet -> exclusive
pay-per-appointment. Marceau-Air-first (public signup gated by config flag).

Run:  ./run.sh   (or python app.py)
"""
import functools
from datetime import timezone

from flask import (Flask, request, redirect, url_for, session, flash, abort, jsonify)

import config
import models
import payments
import notifications
from templates import (render, LANDING, LOGIN, REGISTER, DASHBOARD, CREDITS, ADMIN,
                       REQUEST_FORM, THANKYOU)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
models.init_db()


# ---------------- auth helpers ----------------

def current_contractor():
    cid = session.get("contractor_id")
    return models.get_contractor(cid) if cid else None


def login_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if not session.get("contractor_id"):
            return redirect(url_for("login"))
        c = current_contractor()
        if not c or not c["is_active"]:
            session.clear(); flash("Account unavailable.", "err"); return redirect(url_for("login"))
        return f(*a, **k)
    return w


def admin_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*a, **k)
    return w


def _usd_to_cents(v) -> int:
    return int(round(float(v) * 100))


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------- public / contractor ----------------

@app.route("/")
def index():
    if session.get("contractor_id"):
        return redirect(url_for("dashboard"))
    return render(LANDING, promo_cents=config.SIGNUP_PROMO_CENTS,
                  public_signup=config.PUBLIC_SIGNUP)


@app.route("/request-service", methods=["GET", "POST"])
def request_service():
    """Public homeowner intake -> draft appointment with recorded TCPA consent.
    Feeds the lead pipeline AND becomes marketplace inventory once admin qualifies+prices."""
    if request.method == "POST":
        f = request.form
        if not f.get("consent"):
            flash("Please check the consent box to submit.", "err")
            return render(REQUEST_FORM)
        # structured, auditable consent proof
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        ua = request.headers.get("User-Agent", "")[:200]
        consent_src = (f"homeowner web form @ {_now_iso()} | IP {ip} | UA {ua} | "
                       f"checkbox: call/SMS/email authorization")
        try:
            aid = models.create_homeowner_request(
                service_type=f["service_type"], city=f["city"], zip=f["zip"],
                scheduled_time=f.get("scheduled_time"), job_summary=f.get("job_summary"),
                homeowner_name=f["homeowner_name"], address_full=f["address_full"],
                homeowner_phone=f["homeowner_phone"], homeowner_email=f.get("homeowner_email"),
                consent_captured=True, consent_source=consent_src)
        except models.MarketplaceError as e:
            flash(str(e), "err")
            return render(REQUEST_FORM)
        notifications.notify_admin(
            f"🏠 New homeowner request #{aid}: {f['service_type']} — {f['city']} {f['zip']} "
            f"({f['homeowner_name']}, {f['homeowner_phone']})")
        session["thanks"] = {"name": f["homeowner_name"], "phone": f["homeowner_phone"]}
        return redirect(url_for("request_thanks"))
    return render(REQUEST_FORM)


@app.route("/request-service/thanks")
def request_thanks():
    t = session.pop("thanks", {"name": "", "phone": ""})
    return render(THANKYOU, name=t["name"], phone=t["phone"])


@app.route("/health")
def health():
    return jsonify(status="ok", payment_mode=config.PAYMENT_MODE,
                   public_signup=config.PUBLIC_SIGNUP, stripe_live=config.STRIPE_IS_LIVE)


@app.route("/register", methods=["GET", "POST"])
def register():
    if not config.PUBLIC_SIGNUP:
        flash("Signup is invite-only right now. Contact us for access.", "err")
        return redirect(url_for("login"))
    promo_required = bool(config.PROMO_CODE)
    if request.method == "POST":
        f = request.form
        if promo_required and f.get("promo", "").strip() != config.PROMO_CODE:
            flash("Invalid or missing promo code.", "err")
            return render(REGISTER, promo_cents=config.SIGNUP_PROMO_CENTS,
                          promo_required=promo_required, public_signup=config.PUBLIC_SIGNUP)
        try:
            cid = models.create_contractor(
                f["company_name"], f["contact_name"], f["email"], f["password"],
                phone=f.get("phone"), service_area=f.get("service_area"))
        except models.MarketplaceError as e:
            flash(str(e), "err")
            return render(REGISTER, promo_cents=config.SIGNUP_PROMO_CENTS,
                          promo_required=promo_required, public_signup=config.PUBLIC_SIGNUP)
        session["contractor_id"] = cid
        flash(f"Welcome! {config.dollars(config.SIGNUP_PROMO_CENTS)} in free credits added.", "ok")
        notifications.notify_admin(f"🆕 New marketplace signup: {f['company_name']} ({f['email']})")
        return redirect(url_for("dashboard"))
    return render(REGISTER, promo_cents=config.SIGNUP_PROMO_CENTS,
                  promo_required=promo_required, public_signup=config.PUBLIC_SIGNUP)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        c = models.authenticate(request.form["email"], request.form["password"])
        if c:
            session["contractor_id"] = c["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "err")
    return render(LOGIN, show_register=True, public_signup=config.PUBLIC_SIGNUP)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    c = current_contractor()
    return render(DASHBOARD, contractor=c,
                  available=models.list_available(masked=True),
                  purchased=models.list_purchased_by(c["id"]),
                  tx=models.get_transactions(c["id"], limit=12))


@app.route("/appointments/<int:aid>/buy", methods=["POST"])
@login_required
def buy(aid):
    c = current_contractor()
    try:
        appt = models.purchase_appointment(c["id"], aid)
    except models.MarketplaceError as e:
        flash(str(e), "err")
        return redirect(url_for("dashboard"))
    flash(f"You won this appointment! Contact details unlocked below. "
          f"({config.dollars(appt['price_cents'])} spent)", "ok")
    notifications.notify_buyer_won(c, appt)
    try:
        import crm_link
        crm_link.log_marketplace_purchase(c, appt)  # best-effort; tied by source_deal_id
    except Exception:
        pass
    notifications.notify_admin(
        f"💰 {c['company_name']} bought appt #{aid} ({appt['service_type']}, "
        f"{appt['city']}) for {config.dollars(appt['price_cents'])}")
    return redirect(url_for("dashboard"))


@app.route("/credits", methods=["GET", "POST"])
@login_required
def credits():
    c = current_contractor()
    if request.method == "POST" and config.PAYMENT_MODE == "stripe":
        try:
            cents = _usd_to_cents(request.form["amount"])
            sess = payments.create_topup_session(c, cents)
            if sess.get("url"):
                return redirect(sess["url"])
        except (models.MarketplaceError, ValueError) as e:
            flash(str(e), "err")
    return render(CREDITS, contractor=c, mode=config.PAYMENT_MODE,
                  min_cents=config.MIN_TOPUP_CENTS,
                  min_dollars=config.MIN_TOPUP_CENTS // 100,
                  stripe_live=config.STRIPE_IS_LIVE)


@app.route("/credits/success")
@login_required
def credits_success():
    # Credits are granted by the webhook, not here — this is just UX confirmation.
    flash("Payment received. Credits appear once your bank confirms (usually instant).", "ok")
    return redirect(url_for("dashboard"))


@app.route("/credits/cancel")
@login_required
def credits_cancel():
    flash("Payment canceled.", "err")
    return redirect(url_for("credits"))


@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    try:
        res = payments.handle_webhook(request.get_data(), request.headers.get("Stripe-Signature", ""))
    except models.MarketplaceError as e:
        return str(e), 400
    return jsonify(res)


# ---------------- admin ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (request.form.get("email") == config.ADMIN_EMAIL
                and request.form.get("password") == config.ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("Invalid admin credentials.", "err")
    return render(LOGIN, title="Admin log in", is_admin=False, public_signup=config.PUBLIC_SIGNUP)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    return render(ADMIN, is_admin=True,
                  appointments=models.list_all_appointments(),
                  contractors=models.list_contractors(),
                  ledger_bad=models.verify_ledger(),
                  payment_mode=config.PAYMENT_MODE,
                  stripe_live=config.STRIPE_IS_LIVE,
                  public_signup=config.PUBLIC_SIGNUP)


@app.route("/admin/appointments/new", methods=["POST"])
@admin_required
def admin_new_appointment():
    f = request.form
    try:
        aid = models.create_appointment(
            service_type=f["service_type"], city=f["city"], zip=f["zip"],
            scheduled_time=f["scheduled_time"], job_summary=f["job_summary"],
            est_job_value_cents=_usd_to_cents(f["est_job_value"]) if f.get("est_job_value") else None,
            price_cents=_usd_to_cents(f["price"]),
            homeowner_name=f["homeowner_name"], address_full=f["address_full"],
            homeowner_phone=f["homeowner_phone"], homeowner_email=f.get("homeowner_email"),
            private_notes=f.get("private_notes"),
            consent_captured=bool(f.get("consent_captured")),
            consent_source=f.get("consent_source"))
        if f.get("publish"):
            models.publish_appointment(aid)
            flash(f"Appointment #{aid} created and published.", "ok")
        else:
            flash(f"Appointment #{aid} created as draft.", "ok")
    except (models.MarketplaceError, ValueError, KeyError) as e:
        flash(f"Could not create appointment: {e}", "err")
    return redirect(url_for("admin"))


@app.route("/admin/appointments/<int:aid>/price", methods=["POST"])
@admin_required
def admin_set_price(aid):
    try:
        models.set_price(aid, _usd_to_cents(request.form["price"]))
        flash(f"Price set on appointment #{aid}.", "ok")
    except (models.MarketplaceError, ValueError) as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


@app.route("/admin/appointments/<int:aid>/publish", methods=["POST"])
@admin_required
def admin_publish(aid):
    try:
        models.publish_appointment(aid); flash(f"Appointment #{aid} published.", "ok")
    except models.MarketplaceError as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


@app.route("/admin/appointments/<int:aid>/delete", methods=["POST"])
@admin_required
def admin_delete(aid):
    try:
        models.delete_appointment(aid); flash(f"Appointment #{aid} deleted.", "ok")
    except models.MarketplaceError as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


@app.route("/admin/appointments/<int:aid>/refund", methods=["POST"])
@admin_required
def admin_refund(aid):
    try:
        r = models.refund_appointment(aid, reason="admin refund")
        flash(f"Refunded {config.dollars(r['amount_cents'])} to contractor #{r['refunded_to']}.", "ok")
    except models.MarketplaceError as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


@app.route("/admin/contractors/new", methods=["POST"])
@admin_required
def admin_new_contractor():
    f = request.form
    try:
        models.create_contractor(
            f["company_name"], f["contact_name"], f["email"], f["password"],
            phone=f.get("phone"), is_seed=bool(f.get("is_seed")))
        flash(f"Contractor {f['company_name']} created.", "ok")
    except models.MarketplaceError as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


@app.route("/admin/contractors/<int:cid>/credits", methods=["POST"])
@admin_required
def admin_add_credits(cid):
    try:
        cents = _usd_to_cents(request.form["amount"])
        bal = models.add_credits(cid, cents, kind="admin_adjust", note="Manual admin top-up")
        flash(f"Added {config.dollars(cents)}. New balance {config.dollars(bal)}.", "ok")
    except (models.MarketplaceError, ValueError) as e:
        flash(str(e), "err")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    print(f"Marketplace on {config.BASE_URL}  (payment_mode={config.PAYMENT_MODE}, "
          f"public_signup={config.PUBLIC_SIGNUP}, stripe_live={config.STRIPE_IS_LIVE})")
    app.run(host="127.0.0.1", port=config.PORT, debug=False)
