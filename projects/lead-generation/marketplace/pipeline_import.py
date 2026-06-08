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
import secrets
import sqlite3
import sys
from pathlib import Path

import models
import config

PIPELINE_DB = str(Path(__file__).resolve().parents[1] / "sales-pipeline" / "data" / "pipeline.db")

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


def fetch_deals(industry=None, city=None):
    if not Path(PIPELINE_DB).exists():
        print(f"Pipeline DB not found: {PIPELINE_DB}", file=sys.stderr)
        return []
    c = sqlite3.connect(PIPELINE_DB); c.row_factory = sqlite3.Row
    where = [HVAC_FILTER]
    args = []
    if industry:
        where.append("lower(industry)=lower(?)"); args.append(industry)
    if city:
        where.append("lower(city)=lower(?)"); args.append(city)
    q = (f"SELECT id, company, contact_name, contact_email, contact_phone, city, state, industry "
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
            print(f"  would invite: {d['company']} <{email}> ({d['city']})")
            created += 1; continue
        temp_pw = secrets.token_urlsafe(9)
        try:
            # Atomic copy from ONE verified deal row + hard CRM link (source_deal_id).
            # company/contact/email travel together — never recombined across rows.
            cid = models.create_contractor(
                company_name=d["company"], contact_name=d["contact_name"] or d["company"],
                email=email, password=temp_pw, phone=d["contact_phone"],
                service_area=f"{d['city']}, {d['state']}", is_seed=False, grant_promo=grant_promo,
                source="pipeline_import", source_deal_id=d["id"])
            have.add(email); created += 1
            invites.append({"company": d["company"], "email": email,
                            "temp_password": temp_pw, "contractor_id": cid, "deal_id": d["id"]})
            print(f"  + invited: {d['company']} <{email}>  (deal #{d['id']}, temp pw: {temp_pw})")
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
