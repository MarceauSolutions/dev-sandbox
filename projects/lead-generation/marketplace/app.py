"""
HVAC Appointment Marketplace — Flask app.

Pay structure mirrors RoofProspect.ai: prepaid credit wallet -> exclusive
pay-per-appointment. Marceau-Air-first (public signup gated by config flag).

Run:  ./run.sh   (or python app.py)
"""
import functools
import hmac
import secrets as _secrets
import time
from collections import defaultdict

from flask import (Flask, request, redirect, url_for, session, flash, abort, jsonify)
from werkzeug.middleware.proxy_fix import ProxyFix

import config
import models
import payments
import notifications
from templates import (render, LANDING, LOGIN, REGISTER, DASHBOARD, CREDITS, ADMIN,
                       REQUEST_FORM, THANKYOU)

# Boot-time guard: refuse to run in production with default secrets (forgeable admin).
config.validate_security()

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
# Trust exactly one proxy hop (nginx) so client IP for the TCPA consent log is real, not spoofable.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SESSION_COOKIE_SECURE=not config.ALLOW_INSECURE,   # HTTPS-only in prod
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=512 * 1024,                      # cap request body
)
models.init_db()


# ---------- security headers ----------
# The company site (different origin) fetches the public intake form cross-origin.
_CORS_ORIGINS = {"https://marceauair.com", "https://www.marceauair.com"}


@app.after_request
def _security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"            # clickjacking defense on the buy form
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not config.ALLOW_INSECURE:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # CORS only for the public homeowner intake, only for the known company origins.
    if request.path == "/request-service":
        origin = request.headers.get("Origin", "")
        if origin in _CORS_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# ---------- CSRF (lightweight, dependency-free) ----------
def _csrf_token():
    tok = session.get("_csrf")
    if not tok:
        tok = _secrets.token_urlsafe(32)
        session["_csrf"] = tok
    return tok


@app.context_processor
def _inject_csrf():
    return {"csrf_token": _csrf_token()}


# /request-service is a deliberately cross-origin public lead form (posted from the
# company site on a different domain) — CSRF tokens can't cross origins; it's protected
# by the honeypot + required consent instead. The webhook is protected by Stripe signature.
_CSRF_EXEMPT = {"/webhook/stripe", "/request-service"}


@app.before_request
def _csrf_protect():
    if app.config.get("TESTING"):
        return
    if request.method in ("POST", "PUT", "DELETE", "PATCH") and request.path not in _CSRF_EXEMPT:
        sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
        if not sent or not hmac.compare_digest(sent, session.get("_csrf", "")):
            abort(400, "CSRF token missing or invalid")


# ---------- simple per-IP rate limit (login brute-force) ----------
_HITS = defaultdict(list)


def _rate_limited(key, limit=8, window=300):
    now = time.time()
    hits = [t for t in _HITS[key] if now - t < window]
    hits.append(now)
    _HITS[key] = hits
    return len(hits) > limit


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
    cents = int(round(float(v) * 100))
    if cents <= 0:
        raise ValueError("Amount must be positive.")
    if cents > 100_000_00:                         # $100k sanity ceiling (fat-finger guard)
        raise ValueError("Amount exceeds the allowed maximum.")
    return cents


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


@app.route("/request-service", methods=["GET", "POST", "OPTIONS"])
def request_service():
    """Public homeowner intake -> draft appointment with recorded TCPA consent.
    Accepts both a normal form post (redirects to thank-you) and a cross-origin fetch
    from the company site (returns JSON so the site can show inline success/error)."""
    if request.method == "OPTIONS":
        return ("", 204)  # CORS preflight; headers added by after_request
    wants_json = ("application/json" in request.headers.get("Accept", "")
                  or request.headers.get("X-Requested-With") == "fetch")
    if request.method == "POST":
        f = request.form
        def fail(msg, code=400):
            if wants_json:
                return jsonify(ok=False, error=msg), code
            flash(msg, "err"); return render(REQUEST_FORM)
        if not f.get("consent"):
            return fail("Please check the consent box to submit.")
        if f.get("_gotcha"):  # honeypot tripped -> silently accept, drop
            return (jsonify(ok=True) if wants_json else redirect(url_for("request_thanks")))
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        ua = request.headers.get("User-Agent", "")[:200]
        consent_src = (f"homeowner web form @ {_now_iso()} | IP {ip} | UA {ua} | "
                       f"checkbox: call/SMS/email authorization")
        try:
            aid = models.create_homeowner_request(
                service_type=f.get("service_type"), city=f.get("city"), zip=f.get("zip"),
                scheduled_time=f.get("scheduled_time"), job_summary=f.get("job_summary"),
                homeowner_name=f.get("homeowner_name"), address_full=f.get("address_full"),
                homeowner_phone=f.get("homeowner_phone"), homeowner_email=f.get("homeowner_email"),
                consent_captured=True, consent_source=consent_src)
        except models.MarketplaceError as e:
            return fail(str(e))
        notifications.notify_admin(
            f"🏠 New homeowner request #{aid}: {f.get('service_type')} — {f.get('city')} {f.get('zip')} "
            f"({f.get('homeowner_name')}, {f.get('homeowner_phone')})")
        if wants_json:
            return jsonify(ok=True)
        session["thanks"] = {"name": f.get("homeowner_name"), "phone": f.get("homeowner_phone")}
        return redirect(url_for("request_thanks"))
    return render(REQUEST_FORM)


@app.route("/request-service/thanks")
def request_thanks():
    t = session.pop("thanks", {"name": "", "phone": ""})
    return render(THANKYOU, name=t["name"], phone=t["phone"])


@app.route("/health")
def health():
    # Minimal, non-sensitive: real DB touch + ledger invariant. No config disclosure.
    try:
        bad = models.verify_ledger()
        with models.get_conn() as c:
            c.execute("SELECT 1")
        return jsonify(status="ok", db="ok", ledger_ok=(len(bad) == 0))
    except Exception:
        return jsonify(status="degraded", db="error"), 503


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
        if _rate_limited(f"login:{request.remote_addr}"):
            flash("Too many attempts. Wait a few minutes and try again.", "err")
            return render(LOGIN, show_register=True, public_signup=config.PUBLIC_SIGNUP)
        c = models.authenticate(request.form.get("email", ""), request.form.get("password", ""))
        if c:
            session.clear()                       # anti session-fixation
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
    import sqlite3
    try:
        appt = models.purchase_appointment(c["id"], aid)
    except models.MarketplaceError as e:
        flash(str(e), "err")
        return redirect(url_for("dashboard"))
    except sqlite3.OperationalError:
        flash("The system is busy — please try again in a moment.", "err")
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
        if _rate_limited(f"adminlogin:{request.remote_addr}", limit=5):
            flash("Too many attempts. Wait a few minutes.", "err")
            return render(LOGIN, title="Admin log in", is_admin=False, public_signup=config.PUBLIC_SIGNUP)
        email_ok = hmac.compare_digest(request.form.get("email", ""), config.ADMIN_EMAIL)
        pw_ok = hmac.compare_digest(request.form.get("password", ""), config.ADMIN_PASSWORD)
        if email_ok and pw_ok:
            session.clear()                       # anti session-fixation
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


@app.route("/admin/contractors/<int:cid>/verify", methods=["POST"])
@admin_required
def admin_verify_contractor(cid):
    try:
        models.verify_contractor(cid)
        flash(f"Contractor #{cid} marked human-verified.", "ok")
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
