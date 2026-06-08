"""
Wire the existing lead pipeline -> marketplace BUYERS.

The lead pipeline (pipeline.db `deals`) holds B2B businesses William has scraped/
researched. The HVAC companies in there are exactly the buyer base for this
marketplace. This importer pulls HVAC deals and creates marketplace contractor
accounts (invites) with a random temp password, so they can be invited to log in,
get their promo credits, and start buying appointments.

Idempotent: skips deals already imported (matched by email). Dry-run by default.

Usage:
  python pipeline_import.py                 # dry run — show what would import
  python pipeline_import.py --commit        # create the contractor accounts
  python pipeline_import.py --commit --no-promo
  python pipeline_import.py --commit --industry HVAC --city Naples
"""
import argparse
import re
import secrets
import sqlite3
import sys
from pathlib import Path

import models
import config

# CRM access goes through the SAME resolver crm_link/reconcile use — so source_deal_id
# always points into ONE canonical pipeline.db (fixes the Mac/EC2 split-brain that could
# resolve a deal id to a different company).
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _clean_contact_name(raw: str) -> str:
    """Strip observational/role parentheticals ('Diana (receptionist)', 'Owner (spoke directly)').
    Returns '' if nothing verifiable remains (we will NOT present an unverified person)."""
    if not raw:
        return ""
    name = re.sub(r"\([^)]*\)", "", raw)          # drop parentheticals
    name = re.split(r"\s+/\s+", name)[0]           # 'Yolanda / Karrie' -> first only
    name = name.strip(" -—/")
    # role words that aren't a person's name
    if name.lower() in {"owner", "manager", "receptionist", "front desk", "main", "info", "office"}:
        return ""
    return name

# Strong HVAC signal, minus obvious non-HVAC homographs ("hair", "air bar", salons, roofers).
HVAC_FILTER = (
    "( lower(industry) LIKE '%hvac%' "
    "  OR lower(company) LIKE '%hvac%' "
    "  OR lower(company) LIKE '%air conditioning%' "
    "  OR lower(company) LIKE '%cooling%' "
    "  OR lower(company) LIKE '%heating%' "
    "  OR (lower(company) LIKE '% air%' AND lower(company) NOT LIKE '%hair%') ) "
    "AND lower(company) NOT LIKE '%hair%' AND lower(company) NOT LIKE '%salon%' "
    "AND lower(company) NOT LIKE '%spa%' AND lower(company) NOT LIKE '%roof%' "
    "AND lower(company) NOT LIKE '%organic%'")


def _crm_conn():
    """The ONE canonical CRM connection (same resolver as reconcile)."""
    from execution.pipeline_db import get_db
    c = get_db()
    c.row_factory = sqlite3.Row
    return c


def fetch_deals(industry=None, city=None):
    try:
        c = _crm_conn()
    except Exception as e:
        print(f"CRM (pipeline.db) unavailable: {e}", file=sys.stderr)
        return []
    where = [HVAC_FILTER]
    args = []
    if industry:
        where.append("lower(industry)=lower(?)"); args.append(industry)
    if city:
        where.append("lower(city)=lower(?)"); args.append(city)
    q = (f"SELECT id, company, contact_name, contact_email, contact_phone, city, state, "
         f"industry, email_source, email_confidence "
         f"FROM deals WHERE {' AND '.join(where)} AND contact_email IS NOT NULL "
         f"AND contact_email != '' ORDER BY company")
    rows = c.execute(q, args).fetchall()
    c.close()
    return rows


def existing_emails():
    return {c["email"] for c in models.list_contractors()}


def run(commit=False, grant_promo=True, industry=None, city=None):
    models.init_db()
    deals = fetch_deals(industry, city)
    have = existing_emails()
    created, skipped, invites = 0, 0, []
    print(f"Found {len(deals)} HVAC pipeline deals with email "
          f"({'COMMIT' if commit else 'DRY RUN'}).\n")
    for d in deals:
        email = (d["contact_email"] or "").strip().lower()
        if not email or "@" not in email:
            skipped += 1; continue
        if email in have:
            skipped += 1; print(f"  skip (exists): {d['company']} <{email}>"); continue
        if not commit:
            unv = (not d["email_source"]) or str(d["email_confidence"]).lower() in (
                "", "none", "no_email", "0", "personal_owner")
            print(f"  would import: {d['company']} <{email}> ({d['city']}) "
                  f"raw_contact='{d['contact_name'] or ''}'"
                  f"{'  ⚠ UNVERIFIED EMAIL' if unv else ''}")
            created += 1; continue
        temp_pw = secrets.token_urlsafe(12)
        raw_contact = d["contact_name"] or ""
        clean_contact = _clean_contact_name(raw_contact) or d["company"]  # never present an unverified person
        esrc = d["email_source"]
        econf = d["email_confidence"]
        unverified = (not esrc) or str(econf).lower() in ("", "none", "no_email", "0", "personal_owner")
        try:
            # Atomic copy from ONE deal row + hard CRM link (source_deal_id) into the
            # canonical DB. Imported buyers are ALWAYS verified=0 until a human confirms.
            cid = models.create_contractor(
                company_name=d["company"], contact_name=clean_contact,
                email=email, password=temp_pw, phone=d["contact_phone"],
                service_area=f"{d['city']}, {d['state']}", is_seed=False, grant_promo=grant_promo,
                source="pipeline_import", source_deal_id=d["id"], verified=False,
                email_source=esrc, email_confidence=str(econf) if econf is not None else None,
                contact_raw=raw_contact)
            have.add(email); created += 1
            flag = " ⚠ UNVERIFIED EMAIL" if unverified else ""
            invites.append({"company": d["company"], "email": email, "temp_password": temp_pw,
                            "contractor_id": cid, "deal_id": d["id"], "unverified": unverified})
            print(f"  + imported (UNVERIFIED): {d['company']} <{email}>  deal #{d['id']}"
                  f"  raw_contact='{raw_contact}'{flag}")
        except models.MarketplaceError as e:
            skipped += 1; print(f"  skip ({e}): {d['company']}")

    print(f"\n{'Created' if commit else 'Would create'}: {created}  |  Skipped: {skipped}")
    if commit and invites:
        out = Path(__file__).resolve().parent / "import_invites.txt"
        with open(out, "w") as fh:
            fh.write("company\temail\ttemp_password\n")
            for i in invites:
                fh.write(f"{i['company']}\t{i['email']}\t{i['temp_password']}\n")
        print(f"\nInvite credentials written to {out}")
        print("Send each contractor their login + temp password to onboard them.")
    return created


def main():
    ap = argparse.ArgumentParser(description="Import HVAC pipeline deals as marketplace buyers")
    ap.add_argument("--commit", action="store_true", help="actually create accounts (default: dry run)")
    ap.add_argument("--no-promo", action="store_true", help="do not grant signup promo credits")
    ap.add_argument("--industry", help="exact industry filter (e.g. HVAC)")
    ap.add_argument("--city", help="city filter (e.g. Naples)")
    a = ap.parse_args()
    run(commit=a.commit, grant_promo=not a.no_promo, industry=a.industry, city=a.city)


if __name__ == "__main__":
    main()
