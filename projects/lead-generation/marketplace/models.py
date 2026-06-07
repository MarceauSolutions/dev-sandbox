"""
Data layer for the HVAC appointment marketplace. SQLite, money in CENTS.

Design notes:
- Exclusive purchase is ATOMIC: a single immediate-transaction does a conditional
  UPDATE (status='available' -> 'sold') so only the first buyer wins a race, then
  deducts credits and writes a ledger row. If anything fails the whole tx rolls back.
- Every credit movement is recorded in `transactions` (append-only ledger). A
  contractor's balance is a denormalized cache that MUST equal the ledger sum;
  `verify_ledger()` checks this invariant (used by the test suite).
"""
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        yield conn
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name   TEXT NOT NULL,
    contact_name   TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    phone          TEXT,
    password_hash  TEXT NOT NULL,
    balance_cents  INTEGER NOT NULL DEFAULT 0,
    stripe_customer_id TEXT,
    service_area   TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1,
    is_seed        INTEGER NOT NULL DEFAULT 0,   -- Marceau Air / internal first-buyer
    promo_granted  INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Public (masked) fields — visible to all contractors before purchase:
    service_type   TEXT NOT NULL,           -- e.g. "AC Repair", "New System Install"
    city           TEXT NOT NULL,
    zip            TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,            -- ISO; the confirmed appointment window
    job_summary    TEXT NOT NULL,            -- non-identifying qualification notes
    est_job_value_cents INTEGER,            -- estimated ticket size (helps buyer judge)
    price_cents    INTEGER NOT NULL,         -- credit cost to buy this appointment
    -- Private fields — revealed ONLY to the winning buyer:
    homeowner_name TEXT NOT NULL,
    address_full   TEXT NOT NULL,
    homeowner_phone TEXT NOT NULL,
    homeowner_email TEXT,
    private_notes  TEXT,
    -- TCPA / compliance gate:
    consent_captured INTEGER NOT NULL DEFAULT 0,
    consent_source   TEXT,                   -- e.g. "web form 2026-06-07", "inbound call"
    -- Marketplace state:
    status         TEXT NOT NULL DEFAULT 'draft',  -- draft|available|sold|expired|refunded
    sold_to        INTEGER REFERENCES contractors(id),
    sold_at        TEXT,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id  INTEGER NOT NULL REFERENCES contractors(id),
    kind           TEXT NOT NULL,            -- promo|credit_purchase|appointment_purchase|refund|admin_adjust
    amount_cents   INTEGER NOT NULL,         -- +credit in, -credit out
    balance_after  INTEGER NOT NULL,
    appointment_id INTEGER REFERENCES appointments(id),
    stripe_ref     TEXT,
    note           TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_tx_contractor ON transactions(contractor_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_stripe_ref ON transactions(stripe_ref) WHERE stripe_ref IS NOT NULL;
"""


def init_db():
    with get_conn() as c:
        c.executescript(SCHEMA)


# ---------------- Contractors ----------------

class MarketplaceError(Exception):
    """Expected, user-facing failures (insufficient credits, already sold, etc.)."""


def create_contractor(company_name, contact_name, email, password, phone=None,
                      service_area=None, is_seed=False, grant_promo=True) -> int:
    email = email.strip().lower()
    with get_conn() as c:
        existing = c.execute("SELECT id FROM contractors WHERE email=?", (email,)).fetchone()
        if existing:
            raise MarketplaceError("An account with that email already exists.")
        cur = c.execute(
            """INSERT INTO contractors
               (company_name, contact_name, email, phone, password_hash, service_area,
                is_seed, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (company_name.strip(), contact_name.strip(), email, phone,
             generate_password_hash(password), service_area, 1 if is_seed else 0, _now()),
        )
        cid = cur.lastrowid
    if grant_promo and config.SIGNUP_PROMO_CENTS > 0:
        grant_signup_promo(cid)
    return cid


def grant_signup_promo(contractor_id: int) -> bool:
    """Grant the one-time signup promo. Returns True if granted, False if already granted."""
    with get_conn() as c:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute("SELECT balance_cents, promo_granted FROM contractors WHERE id=?",
                        (contractor_id,)).fetchone()
        if row is None:
            c.execute("ROLLBACK"); raise MarketplaceError("Contractor not found.")
        if row["promo_granted"]:
            c.execute("ROLLBACK"); return False
        new_bal = row["balance_cents"] + config.SIGNUP_PROMO_CENTS
        c.execute("UPDATE contractors SET balance_cents=?, promo_granted=1 WHERE id=?",
                  (new_bal, contractor_id))
        _ledger(c, contractor_id, "promo", config.SIGNUP_PROMO_CENTS, new_bal,
                note="Signup promo credits")
        c.execute("COMMIT")
    return True


def authenticate(email: str, password: str) -> Optional[sqlite3.Row]:
    with get_conn() as c:
        row = c.execute("SELECT * FROM contractors WHERE email=? AND is_active=1",
                        (email.strip().lower(),)).fetchone()
    if row and check_password_hash(row["password_hash"], password):
        return row
    return None


def get_contractor(contractor_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as c:
        return c.execute("SELECT * FROM contractors WHERE id=?", (contractor_id,)).fetchone()


def list_contractors():
    with get_conn() as c:
        return c.execute("SELECT * FROM contractors ORDER BY created_at DESC").fetchall()


# ---------------- Credits ----------------

def _ledger(c, contractor_id, kind, amount_cents, balance_after, appointment_id=None,
            stripe_ref=None, note=None):
    c.execute(
        """INSERT INTO transactions
           (contractor_id, kind, amount_cents, balance_after, appointment_id, stripe_ref, note, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (contractor_id, kind, amount_cents, balance_after, appointment_id, stripe_ref, note, _now()),
    )


def add_credits(contractor_id: int, amount_cents: int, kind: str = "admin_adjust",
                stripe_ref: Optional[str] = None, note: Optional[str] = None) -> int:
    """Add (or with negative amount, remove) credits atomically. Returns new balance.

    Idempotent on stripe_ref: if a row with the same stripe_ref exists, it's a no-op
    (protects against duplicate webhook deliveries)."""
    if amount_cents == 0:
        raise MarketplaceError("Credit amount must be non-zero.")
    with get_conn() as c:
        c.execute("BEGIN IMMEDIATE")
        if stripe_ref:
            dup = c.execute("SELECT id FROM transactions WHERE stripe_ref=?", (stripe_ref,)).fetchone()
            if dup:
                bal = c.execute("SELECT balance_cents FROM contractors WHERE id=?",
                                (contractor_id,)).fetchone()
                c.execute("ROLLBACK")
                return bal["balance_cents"] if bal else 0
        row = c.execute("SELECT balance_cents FROM contractors WHERE id=?",
                        (contractor_id,)).fetchone()
        if row is None:
            c.execute("ROLLBACK"); raise MarketplaceError("Contractor not found.")
        new_bal = row["balance_cents"] + amount_cents
        if new_bal < 0:
            c.execute("ROLLBACK"); raise MarketplaceError("Adjustment would make balance negative.")
        c.execute("UPDATE contractors SET balance_cents=? WHERE id=?", (new_bal, contractor_id))
        _ledger(c, contractor_id, kind, amount_cents, new_bal, stripe_ref=stripe_ref, note=note)
        c.execute("COMMIT")
    return new_bal


def get_transactions(contractor_id: int, limit: int = 100):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM transactions WHERE contractor_id=? ORDER BY id DESC LIMIT ?",
            (contractor_id, limit)).fetchall()


# ---------------- Appointments ----------------

def create_appointment(**f) -> int:
    required = ["service_type", "city", "zip", "scheduled_time", "job_summary",
                "price_cents", "homeowner_name", "address_full", "homeowner_phone"]
    for r in required:
        if not f.get(r):
            raise MarketplaceError(f"Missing required field: {r}")
    with get_conn() as c:
        cur = c.execute(
            """INSERT INTO appointments
               (service_type, city, zip, scheduled_time, job_summary, est_job_value_cents,
                price_cents, homeowner_name, address_full, homeowner_phone, homeowner_email,
                private_notes, consent_captured, consent_source, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f["service_type"], f["city"], f["zip"], f["scheduled_time"], f["job_summary"],
             f.get("est_job_value_cents"), int(f["price_cents"]), f["homeowner_name"],
             f["address_full"], f["homeowner_phone"], f.get("homeowner_email"),
             f.get("private_notes"), 1 if f.get("consent_captured") else 0,
             f.get("consent_source"), "draft", _now()),
        )
        return cur.lastrowid


def create_homeowner_request(**f) -> int:
    """Homeowner-submitted service request -> DRAFT appointment with consent metadata.

    No price (admin qualifies + prices before publishing). Consent is REQUIRED here —
    the public form only submits with the TCPA checkbox ticked, and we record the
    structured proof (timestamp, IP, user-agent, exact checkbox text) in consent_source."""
    required = ["service_type", "city", "zip", "homeowner_name", "address_full", "homeowner_phone"]
    for r in required:
        if not f.get(r):
            raise MarketplaceError(f"Please fill in: {r.replace('_', ' ')}.")
    if not f.get("consent_captured"):
        raise MarketplaceError("Consent is required to submit a service request.")
    with get_conn() as c:
        cur = c.execute(
            """INSERT INTO appointments
               (service_type, city, zip, scheduled_time, job_summary, price_cents,
                homeowner_name, address_full, homeowner_phone, homeowner_email,
                private_notes, consent_captured, consent_source, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f["service_type"], f["city"], f["zip"], f.get("scheduled_time") or "TBD — confirm with homeowner",
             f.get("job_summary") or "Homeowner request (admin to qualify)", 0,
             f["homeowner_name"], f["address_full"], f["homeowner_phone"], f.get("homeowner_email"),
             f.get("private_notes"), 1, f.get("consent_source", "homeowner web form"),
             "draft", _now()),
        )
        return cur.lastrowid


def set_price(appointment_id: int, price_cents: int):
    if price_cents <= 0:
        raise MarketplaceError("Price must be greater than zero.")
    with get_conn() as c:
        cur = c.execute("UPDATE appointments SET price_cents=? WHERE id=? AND status IN ('draft','available')",
                        (int(price_cents), appointment_id))
        if cur.rowcount != 1:
            raise MarketplaceError("Could not set price (appointment not found or already sold).")


def publish_appointment(appointment_id: int):
    """Move draft -> available. Gates: consent captured (TCPA) AND price set (>0)."""
    with get_conn() as c:
        c.execute("BEGIN IMMEDIATE")
        a = c.execute("SELECT status, consent_captured, price_cents FROM appointments WHERE id=?",
                      (appointment_id,)).fetchone()
        if a is None:
            c.execute("ROLLBACK"); raise MarketplaceError("Appointment not found.")
        if not a["consent_captured"]:
            c.execute("ROLLBACK")
            raise MarketplaceError("Cannot publish: homeowner consent not captured (TCPA gate).")
        if a["price_cents"] <= 0:
            c.execute("ROLLBACK")
            raise MarketplaceError("Cannot publish: set a credit price first.")
        if a["status"] not in ("draft", "available"):
            c.execute("ROLLBACK"); raise MarketplaceError(f"Cannot publish from status '{a['status']}'.")
        c.execute("UPDATE appointments SET status='available' WHERE id=?", (appointment_id,))
        c.execute("COMMIT")


# Columns safe to show before purchase (no PII / exact address):
PUBLIC_COLS = ["id", "service_type", "city", "zip", "scheduled_time", "job_summary",
               "est_job_value_cents", "price_cents", "status"]


def _public_view(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in PUBLIC_COLS}


def list_available(masked: bool = True):
    with get_conn() as c:
        rows = c.execute("SELECT * FROM appointments WHERE status='available' ORDER BY scheduled_time").fetchall()
    return [_public_view(r) if masked else dict(r) for r in rows]


def get_appointment(appointment_id: int):
    with get_conn() as c:
        return c.execute("SELECT * FROM appointments WHERE id=?", (appointment_id,)).fetchone()


def list_all_appointments():
    with get_conn() as c:
        return c.execute("SELECT * FROM appointments ORDER BY id DESC").fetchall()


def list_purchased_by(contractor_id: int):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM appointments WHERE sold_to=? AND status='sold' ORDER BY sold_at DESC",
            (contractor_id,)).fetchall()


def purchase_appointment(contractor_id: int, appointment_id: int) -> dict:
    """ATOMIC exclusive purchase. Returns the full (revealed) appointment on success.

    Raises MarketplaceError on: not available / already sold (race loser) /
    insufficient credits / appointment not found. All-or-nothing."""
    with get_conn() as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            appt = c.execute("SELECT * FROM appointments WHERE id=?", (appointment_id,)).fetchone()
            if appt is None:
                raise MarketplaceError("Appointment not found.")
            if appt["status"] != "available":
                raise MarketplaceError("This appointment is no longer available.")
            ctr = c.execute("SELECT balance_cents FROM contractors WHERE id=? AND is_active=1",
                            (contractor_id,)).fetchone()
            if ctr is None:
                raise MarketplaceError("Contractor account not found or inactive.")
            price = appt["price_cents"]
            if ctr["balance_cents"] < price:
                raise MarketplaceError(
                    f"Insufficient credits. Need {config.dollars(price)}, "
                    f"have {config.dollars(ctr['balance_cents'])}.")
            # Conditional flip — guarantees only the first concurrent buyer wins.
            cur = c.execute(
                "UPDATE appointments SET status='sold', sold_to=?, sold_at=? "
                "WHERE id=? AND status='available'",
                (contractor_id, _now(), appointment_id))
            if cur.rowcount != 1:
                raise MarketplaceError("This appointment was just purchased by someone else.")
            new_bal = ctr["balance_cents"] - price
            c.execute("UPDATE contractors SET balance_cents=? WHERE id=?", (new_bal, contractor_id))
            _ledger(c, contractor_id, "appointment_purchase", -price, new_bal,
                    appointment_id=appointment_id,
                    note=f"{appt['service_type']} — {appt['city']} {appt['zip']}")
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
        revealed = c.execute("SELECT * FROM appointments WHERE id=?", (appointment_id,)).fetchone()
        return dict(revealed)


def refund_appointment(appointment_id: int, reason: str = "") -> dict:
    """Admin refund: return credits to buyer, mark appointment refunded (pulled from buyer)."""
    with get_conn() as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            appt = c.execute("SELECT * FROM appointments WHERE id=?", (appointment_id,)).fetchone()
            if appt is None:
                raise MarketplaceError("Appointment not found.")
            if appt["status"] != "sold" or appt["sold_to"] is None:
                raise MarketplaceError("Only a sold appointment can be refunded.")
            buyer = appt["sold_to"]; price = appt["price_cents"]
            ctr = c.execute("SELECT balance_cents FROM contractors WHERE id=?", (buyer,)).fetchone()
            new_bal = ctr["balance_cents"] + price
            c.execute("UPDATE contractors SET balance_cents=? WHERE id=?", (new_bal, buyer))
            c.execute("UPDATE appointments SET status='refunded' WHERE id=?", (appointment_id,))
            _ledger(c, buyer, "refund", price, new_bal, appointment_id=appointment_id,
                    note=f"Refund: {reason or 'admin'}")
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
    return {"refunded_to": buyer, "amount_cents": price}


# ---------------- Integrity ----------------

def verify_ledger() -> list:
    """Return list of contractors whose cached balance != ledger sum (should be empty)."""
    bad = []
    with get_conn() as c:
        for ctr in c.execute("SELECT id, balance_cents FROM contractors").fetchall():
            s = c.execute("SELECT COALESCE(SUM(amount_cents),0) AS s FROM transactions WHERE contractor_id=?",
                          (ctr["id"],)).fetchone()["s"]
            if s != ctr["balance_cents"]:
                bad.append({"contractor_id": ctr["id"], "cached": ctr["balance_cents"], "ledger": s})
    return bad
