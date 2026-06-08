"""
Battle-test suite for the HVAC appointment marketplace.

Run: python tests/test_marketplace.py
Exits non-zero on any failure. Uses an isolated temp DB; never touches Stripe.
"""
import os
import sys
import tempfile
import threading
from pathlib import Path

# Isolate DB + force a known config BEFORE importing app modules.
_TMP = tempfile.mkdtemp(prefix="mkt_test_")
os.environ["MARKETPLACE_DB"] = str(Path(_TMP) / "test.db")
os.environ["MARKETPLACE_PUBLIC_SIGNUP"] = "true"
os.environ["MARKETPLACE_PAYMENT_MODE"] = "manual"
os.environ["MARKETPLACE_PROMO_CENTS"] = "30000"
os.environ["MARKETPLACE_PROMO_CODE"] = ""
os.environ["MARKETPLACE_ADMIN_EMAIL"] = "admin@test.com"
os.environ["MARKETPLACE_ADMIN_PASSWORD"] = "adminpass123"
os.environ["MARKETPLACE_SECRET_KEY"] = "test-secret-key-0123456789"
os.environ["MARKETPLACE_NOTIFY"] = "false"
os.environ["MARKETPLACE_ALLOW_INSECURE"] = "true"  # test client uses http; allow non-secure cookies

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config           # noqa: E402
import models           # noqa: E402

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓ {name}")
    else:
        _FAIL += 1
        print(f"  ✗ FAIL: {name}")


def _raises(fn):
    try:
        fn(); return False
    except Exception:
        return True


def expect_error(name, fn):
    try:
        fn()
        check(name + " (should raise)", False)
    except models.MarketplaceError:
        check(name, True)
    except Exception as e:  # wrong exception type
        check(f"{name} (raised {type(e).__name__}, not MarketplaceError)", False)


def appt_payload(price_cents=7500, consent=True):
    return dict(
        service_type="AC Repair", city="Naples", zip="34110",
        scheduled_time="2026-06-10 14:00", job_summary="warm air, ready to schedule",
        price_cents=price_cents, est_job_value_cents=45000,
        homeowner_name="Test Homeowner", address_full="1 Secret St, Naples FL 34110",
        homeowner_phone="(239) 555-0100", homeowner_email="ho@example.com",
        private_notes="gate 1234", consent_captured=consent,
        consent_source="web form" if consent else None)


def main():
    print("\n=== DATA LAYER ===")
    models.init_db()
    check("verify_ledger empty on fresh db", models.verify_ledger() == [])

    # --- contractors + promo ---
    cid = models.create_contractor("Acme HVAC", "Joe", "joe@acme.com", "password123", phone="2395551111")
    c = models.get_contractor(cid)
    check("signup promo granted ($300)", c["balance_cents"] == 30000)
    check("promo_granted flag set", c["promo_granted"] == 1)
    check("ledger ok after promo", models.verify_ledger() == [])
    # promo cannot be granted twice
    granted_again = models.grant_signup_promo(cid)
    check("promo NOT double-granted", granted_again is False
          and models.get_contractor(cid)["balance_cents"] == 30000)

    # duplicate email rejected
    expect_error("duplicate email rejected",
                 lambda: models.create_contractor("Dup", "X", "joe@acme.com", "password123"))

    # auth
    check("auth wrong password fails", models.authenticate("joe@acme.com", "nope") is None)
    check("auth correct password works", models.authenticate("joe@acme.com", "password123") is not None)

    # --- credits ---
    bal = models.add_credits(cid, 5000, kind="credit_purchase", stripe_ref="evt_1", note="topup")
    check("add_credits adds", bal == 35000)
    # idempotent webhook: same stripe_ref does not double-credit
    bal2 = models.add_credits(cid, 5000, kind="credit_purchase", stripe_ref="evt_1")
    check("duplicate stripe_ref is idempotent", bal2 == 35000)
    check("ledger ok after credits", models.verify_ledger() == [])
    expect_error("cannot remove below zero",
                 lambda: models.add_credits(cid, -999999, kind="admin_adjust"))

    # --- appointments + TCPA gate ---
    aid = models.create_appointment(**appt_payload(consent=False))
    check("appointment created as draft", models.get_appointment(aid)["status"] == "draft")
    expect_error("cannot publish without consent (TCPA)",
                 lambda: models.publish_appointment(aid))
    check("draft not in available list", models.list_available() == [])

    aid2 = models.create_appointment(**appt_payload(price_cents=7500, consent=True))
    models.publish_appointment(aid2)
    avail = models.list_available(masked=True)
    check("published appointment is available", len(avail) == 1 and avail[0]["id"] == aid2)
    masked = avail[0]
    check("masked view hides homeowner phone", "homeowner_phone" not in masked)
    check("masked view hides full address", "address_full" not in masked)
    check("masked view hides homeowner name", "homeowner_name" not in masked)
    check("masked view shows city/price", masked["city"] == "Naples" and masked["price_cents"] == 7500)

    # --- purchase: insufficient credits ---
    poor = models.create_contractor("Poor LLC", "P", "poor@x.com", "password123")
    models.add_credits(poor, -30000, kind="admin_adjust")  # drain promo to 0
    expect_error("insufficient credits blocks purchase",
                 lambda: models.purchase_appointment(poor, aid2))
    check("appointment still available after failed buy",
          models.get_appointment(aid2)["status"] == "available")

    # --- purchase: success + reveal ---
    before = models.get_contractor(cid)["balance_cents"]
    revealed = models.purchase_appointment(cid, aid2)
    check("purchase reveals homeowner phone", revealed["homeowner_phone"] == "(239) 555-0100")
    check("purchase reveals full address", "Secret St" in revealed["address_full"])
    check("balance deducted by price", models.get_contractor(cid)["balance_cents"] == before - 7500)
    check("appointment now sold", models.get_appointment(aid2)["status"] == "sold")
    check("sold_to is buyer", models.get_appointment(aid2)["sold_to"] == cid)
    check("appears in buyer's purchased", any(a["id"] == aid2 for a in models.list_purchased_by(cid)))
    check("ledger ok after purchase", models.verify_ledger() == [])

    # buying an already-sold appointment fails
    expect_error("cannot buy already-sold appointment",
                 lambda: models.purchase_appointment(poor, aid2))

    # --- concurrency: only ONE of two simultaneous buyers wins ---
    raceA = models.create_contractor("RaceA", "A", "a@race.com", "password123")
    raceB = models.create_contractor("RaceB", "B", "b@race.com", "password123")
    aid3 = models.create_appointment(**appt_payload(price_cents=5000, consent=True))
    models.publish_appointment(aid3)
    results = {}
    barrier = threading.Barrier(2)

    def attempt(buyer, key):
        barrier.wait()
        try:
            models.purchase_appointment(buyer, aid3)
            results[key] = "won"
        except models.MarketplaceError:
            results[key] = "lost"

    tA = threading.Thread(target=attempt, args=(raceA, "A"))
    tB = threading.Thread(target=attempt, args=(raceB, "B"))
    tA.start(); tB.start(); tA.join(); tB.join()
    wins = list(results.values()).count("won")
    check("exactly one buyer wins the race", wins == 1)
    check("race did not corrupt ledger", models.verify_ledger() == [])
    sold_to = models.get_appointment(aid3)["sold_to"]
    winner_bal = models.get_contractor(sold_to)["balance_cents"]
    loser = raceB if sold_to == raceA else raceA
    check("winner charged 5000", winner_bal == 30000 - 5000)
    check("loser NOT charged", models.get_contractor(loser)["balance_cents"] == 30000)

    # --- refund ---
    r = models.refund_appointment(aid2, reason="test")
    check("refund returns price to buyer", r["amount_cents"] == 7500)
    check("appointment marked refunded", models.get_appointment(aid2)["status"] == "refunded")
    check("buyer balance restored", models.get_contractor(cid)["balance_cents"] == before)
    check("ledger ok after refund", models.verify_ledger() == [])
    expect_error("cannot refund non-sold appointment",
                 lambda: models.refund_appointment(aid2))

    # --- delete (non-sold only) ---
    dtmp = models.create_appointment(**appt_payload(consent=True))
    models.delete_appointment(dtmp)
    check("draft appointment deletes", models.get_appointment(dtmp) is None)
    expect_error("cannot delete a SOLD appointment", lambda: models.delete_appointment(aid3))

    # --- homeowner intake + price gate ---
    print("\n=== HOMEOWNER INTAKE / PRICE GATE ===")
    hreq = models.create_homeowner_request(
        service_type="AC Not Cooling", city="Naples", zip="34110",
        homeowner_name="Jane Doe", address_full="5 Maple St, Naples FL 34110",
        homeowner_phone="2395550199", homeowner_email="jane@example.com",
        consent_captured=True, consent_source="web form @ test | IP 1.2.3.4")
    hr = models.get_appointment(hreq)
    check("homeowner request created as draft", hr["status"] == "draft")
    check("homeowner request consent captured", hr["consent_captured"] == 1)
    check("homeowner request price is 0", hr["price_cents"] == 0)
    expect_error("homeowner request requires consent", lambda: models.create_homeowner_request(
        service_type="x", city="Naples", zip="34110", homeowner_name="N",
        address_full="a", homeowner_phone="1", consent_captured=False))
    expect_error("cannot publish with price 0", lambda: models.publish_appointment(hreq))
    models.set_price(hreq, 6000)
    check("price set on draft", models.get_appointment(hreq)["price_cents"] == 6000)
    models.publish_appointment(hreq)
    check("draft publishes once priced + consented", models.get_appointment(hreq)["status"] == "available")
    expect_error("set_price rejects zero", lambda: models.set_price(hreq, 0))

    # --- CRM linkage integrity (anti mis-association) ---
    print("\n=== CRM LINKAGE INTEGRITY ===")
    # a CRM-sourced buyer carries its deal id atomically
    linked = models.create_contractor("Linked HVAC", "Real Person", "real@linkedhvac.com",
                                       "password123", source="pipeline_import", source_deal_id=4242)
    lc = models.get_contractor(linked)
    check("source_deal_id stored", lc["source_deal_id"] == 4242)
    check("source recorded", lc["source"] == "pipeline_import")
    # the SAME deal cannot be linked to a second contractor (prevents wrong-company reuse)
    expect_error("deal cannot double-link to another contractor",
                 lambda: models.create_contractor("Other Co", "X", "x@other.com",
                         "password123", source="pipeline_import", source_deal_id=4242))
    # origin provenance on appointments
    homeo = models.get_appointment(hreq)
    check("homeowner appt origin = homeowner_form", homeo["origin"] == "homeowner_form")
    admin_appt = models.get_appointment(aid2)
    check("admin appt origin = admin_manual", admin_appt["origin"] == "admin_manual")
    # reconcile runs; non-CRM buyers are 'n/a', no false mismatches
    import crm_link
    rep = crm_link.reconcile()
    check("reconcile returns a report", "contractors" in rep and "issues" in rep)
    seed_entries = [e for e in rep["contractors"] if e["source_deal_id"] is None]
    check("non-CRM buyers marked n/a (not flagged)",
          all("n/a" in (e["verified"] or "") for e in seed_entries))
    check("no sold_to_missing orphans", not any(i["type"] == "sold_to_missing" for i in rep["issues"]))

    # ================= HTTP layer =================
    print("\n=== HTTP LAYER ===")
    import app as flaskapp
    flaskapp.app.config["TESTING"] = True
    client = flaskapp.app.test_client()

    r = client.get("/health")
    check("/health 200 + json", r.status_code == 200 and r.get_json()["status"] == "ok")

    r = client.get("/")
    check("landing renders", r.status_code == 200 and b"appointment" in r.data.lower())

    # register via web (public signup on)
    r = client.post("/register", data=dict(
        company_name="WebCo", contact_name="Web", email="web@co.com",
        phone="2395559999", service_area="Naples", password="password123"),
        follow_redirects=True)
    check("web register -> dashboard", r.status_code == 200 and b"balance" in r.data.lower())
    check("web register granted promo", b"$300.00" in r.data)

    # browse shows masked, NOT phone
    web = models.authenticate("web@co.com", "password123")
    aid4 = models.create_appointment(**appt_payload(price_cents=4000, consent=True))
    models.publish_appointment(aid4)
    r = client.get("/dashboard")
    check("dashboard lists available appt", str(aid4).encode() in r.data or b"AC Repair" in r.data)
    check("dashboard does NOT leak homeowner phone", b"555-0100" not in r.data)

    # buy via web -> reveals contact
    r = client.post(f"/appointments/{aid4}/buy", follow_redirects=True)
    check("web buy succeeds + reveals phone", b"555-0100" in r.data)
    check("web buy sold the appointment", models.get_appointment(aid4)["status"] == "sold")

    # admin gate
    r = client.get("/admin", follow_redirects=False)
    check("admin requires login (redirect)", r.status_code in (301, 302))
    r = client.post("/admin/login", data=dict(email="admin@test.com", password="adminpass123"),
                    follow_redirects=True)
    check("admin login works", r.status_code == 200 and b"Ledger" in r.data)
    r = client.get("/admin")
    check("admin shows ledger OK", b"integrity OK" in r.data)

    # admin creates + publishes appointment via web
    r = client.post("/admin/appointments/new", data=dict(
        service_type="Tune-up", city="Estero", zip="33928", scheduled_time="2026-06-15 09:00",
        price="30", est_job_value="180", job_summary="annual",
        homeowner_name="Adm Test", homeowner_phone="2395550000",
        address_full="9 Admin St", consent_captured="on", consent_source="call", publish="on"),
        follow_redirects=True)
    check("admin created+published appt", b"published" in r.data.lower())

    # homeowner intake via web (public, not gated by contractor signup flag)
    r = client.get("/request-service")
    check("request-service form renders", r.status_code == 200 and b"Request HVAC service" in r.data)
    n_before = len(models.list_all_appointments())
    r = client.post("/request-service", data=dict(
        homeowner_name="Web Homeowner", homeowner_phone="2395550123",
        homeowner_email="wh@example.com", address_full="7 Pine St, Naples FL 34110",
        city="Naples", zip="34110", service_type="AC Not Cooling — Repair",
        job_summary="warm air", scheduled_time="afternoons", consent="on"),
        follow_redirects=True)
    check("homeowner web submit -> thank you", r.status_code == 200 and b"Request received" in r.data)
    check("homeowner submit created a draft appt", len(models.list_all_appointments()) == n_before + 1)
    # consent required: submit without checkbox is rejected
    r = client.post("/request-service", data=dict(
        homeowner_name="No Consent", homeowner_phone="2395550000",
        address_full="9 Oak", city="Naples", zip="34110",
        service_type="Other"), follow_redirects=True)
    check("web submit without consent rejected", b"consent" in r.data.lower())

    # invite-only enforcement: flip flag and ensure register blocked
    config.PUBLIC_SIGNUP = False
    r = client.get("/register", follow_redirects=True)
    check("register blocked when invite-only", b"invite-only" in r.data.lower())
    config.PUBLIC_SIGNUP = True

    # ================= SECURITY + HARDENING =================
    print("\n=== SECURITY / HARDENING ===")
    r = client.get("/")
    check("security headers set (X-Frame-Options, nosniff)",
          r.headers.get("X-Frame-Options") == "DENY"
          and r.headers.get("X-Content-Type-Options") == "nosniff")
    r = client.get("/health")
    hj = r.get_json()
    check("health does NOT leak config", "payment_mode" not in hj and "stripe_live" not in hj)
    check("health reports db+ledger", hj.get("db") == "ok" and hj.get("ledger_ok") is True)

    # CSRF is enforced when not in TESTING mode
    flaskapp.app.config["TESTING"] = False
    try:
        r = client.post("/login", data=dict(email="x@y.com", password="z"))
        check("CSRF blocks tokenless POST (400)", r.status_code == 400)
    finally:
        flaskapp.app.config["TESTING"] = True

    # config refuses insecure defaults (temporarily force defaults + no allow-insecure)
    def _force_insecure():
        sk, pw, ai = config.SECRET_KEY, config.ADMIN_PASSWORD, config.ALLOW_INSECURE
        config.SECRET_KEY = config._DEV_SECRET; config.ADMIN_PASSWORD = config._DEV_ADMIN_PW
        config.ALLOW_INSECURE = False
        try:
            config.validate_security()
        finally:
            config.SECRET_KEY, config.ADMIN_PASSWORD, config.ALLOW_INSECURE = sk, pw, ai
    check("validate_security raises on dev defaults", _raises(_force_insecure))

    # origin anti-fabrication: admin path cannot claim homeowner_form
    fake = models.create_appointment(**dict(appt_payload(consent=True), origin="homeowner_form"))
    check("admin appt cannot fake homeowner_form origin",
          models.get_appointment(fake)["origin"] == "admin_manual")

    # contact-name cleaning (role/parenthetical stripping)
    import pipeline_import
    check("clean strips parenthetical role", pipeline_import._clean_contact_name("Diana (receptionist - friendly)") == "Diana")
    check("clean drops bare role word", pipeline_import._clean_contact_name("Owner (spoke directly)") == "")
    check("clean takes first of slash list", pipeline_import._clean_contact_name("Yolanda / Karrie") == "Yolanda")

    # verification gate + unverified flag in reconcile
    unv = models.create_contractor("Unv HVAC", "Real Person", "p@unvhvac.com", "password123",
                                   source="pipeline_import", source_deal_id=7777, verified=False,
                                   email_confidence="0", contact_raw="Front desk (Sue)")
    rep2 = crm_link.reconcile()
    ue = next(e for e in rep2["contractors"] if e["contractor_id"] == unv)
    check("imported buyer is unverified", ue["human_verified"] is False)
    models.verify_contractor(unv)
    rep3 = crm_link.reconcile()
    ue3 = next(e for e in rep3["contractors"] if e["contractor_id"] == unv)
    check("verify_contractor flips to verified", ue3["human_verified"] is True)

    # amount bounds
    from app import _usd_to_cents
    check("amount rejects non-positive", _raises(lambda: _usd_to_cents(0)))
    check("amount rejects > $100k", _raises(lambda: _usd_to_cents(200000)))
    check("amount accepts normal", _usd_to_cents(75) == 7500)

    # final integrity
    check("FINAL ledger integrity clean", models.verify_ledger() == [])

    print(f"\n=== RESULT: {_PASS} passed, {_FAIL} failed ===")
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
