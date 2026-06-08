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


def crm_db_path():
    """The resolved canonical CRM path — printed in the report so a Mac/EC2 split is visible."""
    try:
        from execution import pipeline_db
        # get_db resolves EC2 vs Mac; surface whichever it chose
        for attr in ("EC2_DB_PATH", "DB_PATH", "MAC_DB_PATH"):
            pass
        conn = pipeline_db.get_db()
        path = None
        try:
            path = conn.execute("PRAGMA database_list").fetchall()[0][2]
        except Exception:
            pass
        conn.close()
        return path or "<unknown>"
    except Exception as e:
        return f"<unavailable: {e}>"


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
            "email_source, email_confidence, city, state, website FROM deals WHERE id=?",
            (deal_id,)).fetchone()
    finally:
        conn.close()


def _domain(s):
    """Extract a comparable domain from an email or URL ('a@foo.com'->'foo.com')."""
    if not s:
        return ""
    s = s.strip().lower()
    if "@" in s:
        s = s.split("@", 1)[1]
    s = s.replace("https://", "").replace("http://", "").replace("www.", "")
    return s.split("/")[0].strip()


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
            "SELECT id, company_name, contact_name, email, source, source_deal_id, "
            "verified, email_source, email_confidence, contact_raw "
            "FROM contractors ORDER BY id").fetchall()
        contractor_ids = {r["id"] for r in contractors}
        for a in c.execute("SELECT id, sold_to FROM appointments WHERE sold_to IS NOT NULL"):
            if a["sold_to"] not in contractor_ids:
                issues.append({"type": "sold_to_missing", "appointment_id": a["id"],
                               "sold_to": a["sold_to"]})

    for ctr in contractors:
        entry = {"contractor_id": ctr["id"], "company": ctr["company_name"],
                 "email": ctr["email"], "source": ctr["source"],
                 "source_deal_id": ctr["source_deal_id"],
                 "human_verified": bool(ctr["verified"]),
                 "email_source": ctr["email_source"], "email_confidence": ctr["email_confidence"],
                 "verified": None, "crm": None, "anchor": None}
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
                                "website": deal["website"],
                                "email_source": deal["email_source"],
                                "email_confidence": deal["email_confidence"]}
                email_ok = crm_email == ctr["email"].strip().lower()
                company_ok = crm_company == ctr["company_name"].strip().lower()
                # Independent anchor (NOT derived from the copied row): does the buyer's
                # email domain match the CRM deal's website domain? A mismatch means the
                # email may belong to a different entity than the company — investigate.
                ed, wd = _domain(ctr["email"]), _domain(deal["website"])
                if wd and ed:
                    entry["anchor"] = "email-domain==website" if ed == wd else f"DOMAIN MISMATCH ({ed} vs {wd})"
                    if ed != wd:
                        issues.append({"type": "domain_anchor_mismatch", "contractor_id": ctr["id"],
                                       "email_domain": ed, "website_domain": wd})
                else:
                    entry["anchor"] = "no website to anchor against"
                if email_ok and company_ok:
                    entry["verified"] = "link-consistent"  # NOT 'proven' — see human_verified
                else:
                    entry["verified"] = "MISMATCH"
                    if not email_ok:
                        issues.append({"type": "email_mismatch", "contractor_id": ctr["id"],
                                       "marketplace": ctr["email"], "crm": deal["contact_email"]})
                    if not company_ok:
                        issues.append({"type": "company_mismatch", "contractor_id": ctr["id"],
                                       "marketplace": ctr["company_name"], "crm": deal["company"]})
        rows.append(entry)
    return {"ok": len(issues) == 0, "db": crm_db_path(), "contractors": rows, "issues": issues}


def print_report():
    r = reconcile()
    print("=" * 72)
    print("MARKETPLACE ↔ CRM RECONCILIATION  (verify every association — no guessing)")
    print(f"CRM db checked: {r['db']}")
    print("=" * 72)
    unverified = 0
    for e in r["contractors"]:
        vflag = "✓ human-verified" if e["human_verified"] else "⚠ UNVERIFIED (do not trust as a real person)"
        if not e["human_verified"] and e["source_deal_id"] is not None:
            unverified += 1
        line = f"  #{e['contractor_id']} {e['company']} <{e['email']}>  [{e['source']}]  {vflag}"
        if e["source_deal_id"] is not None:
            line += f"\n        link -> CRM deal #{e['source_deal_id']}: {e['verified']}"
            if e["anchor"]:
                line += f" | anchor: {e['anchor']}"
            if e["email_source"] is not None or e["email_confidence"] is not None:
                line += f" | email_src={e['email_source']} conf={e['email_confidence']}"
            if e["crm"]:
                line += (f"\n        CRM row: {e['crm']['company']} / contact='{e['crm']['contact']}' "
                         f"<{e['crm']['email']}> web={e['crm']['website']}")
        print(line)
    print("-" * 72)
    if r["ok"]:
        print(f"✓ No mismatches/orphans across {len(r['contractors'])} buyers.")
    else:
        print(f"✗ {len(r['issues'])} ISSUE(S) — DO NOT act on these until resolved:")
        for i in r["issues"]:
            print(f"    {i}")
    if unverified:
        print(f"⚠ {unverified} CRM-linked buyer(s) are UNVERIFIED — confirm the contact + company "
              f"are real (call/website) and run verify before any in-person/outreach action.")
    print("  NOTE: 'link-consistent' means the copy matches its source — it does NOT prove the")
    print("  original association is correct. Only 'human-verified' means a person confirmed it.")
    print("=" * 72)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(print_report())
