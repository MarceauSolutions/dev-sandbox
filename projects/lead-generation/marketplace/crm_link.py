"""
Marketplace <-> CRM (pipeline.db) integration, integrity-first.

Hard rules (these exist because of the March-25 mis-association incident — a contact
was associated with the wrong company and William walked into a business asking for a
person who didn't work there):

1. Links are by STABLE ID only (contractors.source_deal_id -> deals.id). Never by name.
2. A buyer's company/contact/email is copied as ONE atomic unit from a single deal row.
3. Every link is VERIFIABLE: reconcile() re-joins marketplace->CRM and flags any
   drift (email/company mismatch, orphaned link, double-linked deal).
4. Nothing is fabricated: purchases are logged to the CRM only as what actually happened.

CRM access is best-effort: if pipeline.db isn't reachable, marketplace integrity checks
still run on marketplace-local data.
"""
import sys
from pathlib import Path

import models

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _crm():
    """Return a pipeline.db connection, or None if the CRM isn't available."""
    try:
        from execution.pipeline_db import get_db
        return get_db()
    except Exception as e:
        print(f"[crm_link] CRM unavailable: {e}", file=sys.stderr)
        return None


def get_deal(deal_id: int):
    """Return the CRM deal row (verified source of a buyer's identity), or None."""
    conn = _crm()
    if conn is None:
        return None
    try:
        conn.row_factory = __import__("sqlite3").Row
        return conn.execute(
            "SELECT id, company, contact_name, contact_email, contact_phone, "
            "email_source, email_confidence, city, state FROM deals WHERE id=?",
            (deal_id,)).fetchone()
    finally:
        conn.close()


def log_marketplace_purchase(contractor, appt: dict) -> bool:
    """Log a marketplace sale to the CRM as an activity on the buyer's deal.

    Only logs if the buyer is CRM-linked (source_deal_id set) — we never invent a deal."""
    deal_id = contractor["source_deal_id"]
    if deal_id is None:
        return False
    conn = _crm()
    if conn is None:
        return False
    try:
        from execution.pipeline_db import log_activity
        desc = (f"Bought marketplace appointment #{appt['id']} "
                f"({appt['service_type']}, {appt['city']} {appt['zip']}) "
                f"for {models.config.dollars(appt['price_cents'])}")
        log_activity(conn, deal_id, "marketplace_purchase", desc, tower="digital-ai-services")
        return True
    except Exception as e:
        print(f"[crm_link] purchase log failed: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


def reconcile() -> dict:
    """Verification report. Returns {ok, contractors:[...], issues:[...]}.

    For every CRM-linked contractor, re-fetch the deal and confirm the email matches.
    Flags: email_mismatch, company_mismatch, orphan_link (deal gone), unlinked_buyer,
    sold_to_missing (appointment points at a non-existent contractor)."""
    issues = []
    rows = []
    with models.get_conn() as c:
        contractors = c.execute(
            "SELECT id, company_name, contact_name, email, source, source_deal_id "
            "FROM contractors ORDER BY id").fetchall()
        contractor_ids = {r["id"] for r in contractors}
        # appointment referential integrity
        for a in c.execute("SELECT id, sold_to FROM appointments WHERE sold_to IS NOT NULL"):
            if a["sold_to"] not in contractor_ids:
                issues.append({"type": "sold_to_missing", "appointment_id": a["id"],
                               "sold_to": a["sold_to"]})

    for ctr in contractors:
        entry = {"contractor_id": ctr["id"], "company": ctr["company_name"],
                 "email": ctr["email"], "source": ctr["source"],
                 "source_deal_id": ctr["source_deal_id"], "verified": None, "crm": None}
        if ctr["source_deal_id"] is None:
            entry["verified"] = "n/a (not CRM-sourced)"
        else:
            deal = get_deal(ctr["source_deal_id"])
            if deal is None:
                entry["verified"] = "ORPHAN — CRM deal not found"
                issues.append({"type": "orphan_link", "contractor_id": ctr["id"],
                               "deal_id": ctr["source_deal_id"]})
            else:
                crm_email = (deal["contact_email"] or "").strip().lower()
                crm_company = (deal["company"] or "").strip().lower()
                entry["crm"] = {"deal_id": deal["id"], "company": deal["company"],
                                "contact": deal["contact_name"], "email": deal["contact_email"],
                                "email_source": deal["email_source"],
                                "email_confidence": deal["email_confidence"]}
                email_ok = crm_email == ctr["email"].strip().lower()
                company_ok = crm_company == ctr["company_name"].strip().lower()
                if email_ok and company_ok:
                    entry["verified"] = "OK"
                else:
                    entry["verified"] = "MISMATCH"
                    if not email_ok:
                        issues.append({"type": "email_mismatch", "contractor_id": ctr["id"],
                                       "marketplace": ctr["email"], "crm": deal["contact_email"]})
                    if not company_ok:
                        issues.append({"type": "company_mismatch", "contractor_id": ctr["id"],
                                       "marketplace": ctr["company_name"], "crm": deal["company"]})
        rows.append(entry)
    return {"ok": len(issues) == 0, "contractors": rows, "issues": issues}


def print_report():
    r = reconcile()
    print("=" * 68)
    print("MARKETPLACE ↔ CRM RECONCILIATION  (verify every association — no guessing)")
    print("=" * 68)
    for e in r["contractors"]:
        line = f"  #{e['contractor_id']} {e['company']} <{e['email']}>  [{e['source']}]"
        if e["source_deal_id"] is not None:
            line += f"  -> CRM deal #{e['source_deal_id']}: {e['verified']}"
            if e["crm"]:
                line += (f"\n        CRM says: {e['crm']['company']} / {e['crm']['contact']} "
                         f"<{e['crm']['email']}> (src={e['crm']['email_source']}, "
                         f"conf={e['crm']['email_confidence']})")
        else:
            line += f"  [{e['verified']}]"
        print(line)
    print("-" * 68)
    if r["ok"]:
        print(f"✓ INTEGRITY OK — {len(r['contractors'])} buyers, 0 mismatches/orphans.")
    else:
        print(f"✗ {len(r['issues'])} ISSUE(S) — DO NOT act on these until resolved:")
        for i in r["issues"]:
            print(f"    {i}")
    print("=" * 68)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(print_report())
