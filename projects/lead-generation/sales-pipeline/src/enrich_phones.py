#!/usr/bin/env python3
"""
Phone Enrichment — Fills in missing phone numbers for pipeline deals via Apollo API.

Queries Apollo /people/match for each deal missing a phone number using:
- contact_name + company (primary)
- contact_email (if available)
- linkedin_url (if available)

Also syncs phone numbers FROM pipeline.db back to the call list so
generate_lead_lists.py has complete data.

Usage:
    python -m src.enrich_phones check     # Preview what would be enriched
    python -m src.enrich_phones enrich    # Actually enrich via Apollo
    python -m src.enrich_phones stats     # Show phone coverage stats
"""

import os
import sys
import re
import sqlite3
import time
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(str(_PROJECT_ROOT / ".env"))

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# Lazy import Apollo client
_apollo = None
def get_apollo():
    global _apollo
    if _apollo is None:
        sys.path.insert(0, str(_PROJECT_ROOT / "projects/lead-generation/src"))
        from src.apollo import ApolloClient
        _apollo = ApolloClient(api_key=APOLLO_API_KEY)
    return _apollo


def normalize_phone(raw: str) -> str:
    """Normalize phone to (XXX) XXX-XXXX format for readability."""
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw  # Return as-is if can't normalize


def get_deals_missing_phone(conn) -> list:
    """Get deals that have no phone number."""
    rows = conn.execute("""
        SELECT id, company, contact_name, contact_email, website, industry
        FROM deals
        WHERE (contact_phone IS NULL OR contact_phone = '')
        AND stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY lead_score DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_phone_stats(conn) -> dict:
    """Get phone coverage statistics."""
    total = conn.execute("SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')").fetchone()[0]
    has_phone = conn.execute("""
        SELECT COUNT(*) FROM deals
        WHERE contact_phone IS NOT NULL AND contact_phone != ''
        AND stage NOT IN ('Closed Won', 'Closed Lost')
    """).fetchone()[0]
    contacted = conn.execute("SELECT COUNT(DISTINCT deal_id) FROM outreach_log WHERE channel = 'Call'").fetchone()[0]
    emailed = conn.execute("SELECT COUNT(DISTINCT deal_id) FROM outreach_log WHERE channel = 'Email'").fetchone()[0]

    return {
        "total_active_deals": total,
        "has_phone": has_phone,
        "missing_phone": total - has_phone,
        "phone_coverage_pct": round(has_phone / max(total, 1) * 100, 1),
        "called": contacted,
        "emailed": emailed,
    }


def enrich_deal_phone(deal: dict, dry_run: bool = True) -> dict:
    """Try to find phone number for a deal via Apollo."""
    apollo = get_apollo()
    company = deal["company"]
    contact = deal.get("contact_name", "")
    email = deal.get("contact_email", "")
    website = deal.get("website", "")

    # Extract domain from website
    domain = ""
    if website:
        domain = website.replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]

    # Strategy 1: Enrich by name + company
    person = None
    if contact and company:
        parts = contact.split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        if first:
            try:
                person = apollo.enrich_person(
                    first_name=first,
                    last_name=last if last != first else None,
                    organization_name=company,
                    domain=domain or None,
                )
            except Exception as e:
                pass

    # Strategy 2: Enrich by email
    if not person and email and "@" in email:
        try:
            person = apollo.enrich_person(email=email)
        except Exception:
            pass

    # Strategy 3: Search company for owner
    if not person and domain:
        try:
            person = apollo.enrich_person(
                organization_name=company,
                domain=domain,
            )
        except Exception:
            pass

    if not person:
        return {"deal_id": deal["id"], "company": company, "phone": None, "source": "not_found"}

    # Extract phone
    phone_numbers = person.get("phone_numbers", [])
    if phone_numbers:
        raw = phone_numbers[0].get("raw_number", "") or phone_numbers[0].get("sanitized_number", "")
        if raw:
            phone = normalize_phone(raw)
            return {"deal_id": deal["id"], "company": company, "phone": phone, "source": "apollo_enrich"}

    # Check organization phone
    org = person.get("organization", {}) or {}
    org_phone = org.get("phone", "")
    if org_phone:
        return {"deal_id": deal["id"], "company": company, "phone": normalize_phone(org_phone), "source": "apollo_org"}

    return {"deal_id": deal["id"], "company": company, "phone": None, "source": "no_phone_in_apollo"}


def run_enrichment(dry_run: bool = True):
    """Enrich all deals missing phone numbers."""
    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not set in .env")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    missing = get_deals_missing_phone(conn)

    print(f"{'DRY RUN' if dry_run else 'ENRICHING'}: {len(missing)} deals missing phone numbers\n")

    found = 0
    not_found = 0

    for i, deal in enumerate(missing):
        result = enrich_deal_phone(deal, dry_run=dry_run)

        if result["phone"]:
            found += 1
            print(f"  [{found}] {result['company']} → {result['phone']} ({result['source']})")

            if not dry_run:
                conn.execute("UPDATE deals SET contact_phone = ? WHERE id = ?",
                           (result["phone"], result["deal_id"]))
                if (found % 10) == 0:
                    conn.commit()
        else:
            not_found += 1
            if dry_run:
                print(f"  [--] {result['company']} → no phone found ({result['source']})")

        # Rate limit: Apollo allows ~5 requests/sec
        time.sleep(0.3)

        # Progress
        if (i + 1) % 20 == 0:
            print(f"\n  Progress: {i+1}/{len(missing)} checked, {found} found, {not_found} not found\n")

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\nResults: {found} phones found, {not_found} not found out of {len(missing)} missing")
    return {"found": found, "not_found": not_found, "total_missing": len(missing)}


def show_stats():
    """Show current phone coverage stats."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    stats = get_phone_stats(conn)

    # Also show stage breakdown with phone coverage
    stages = conn.execute("""
        SELECT stage,
               COUNT(*) as total,
               COUNT(CASE WHEN contact_phone IS NOT NULL AND contact_phone != '' THEN 1 END) as with_phone
        FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY stage
        ORDER BY total DESC
    """).fetchall()

    # Outreach status
    contacted = conn.execute("""
        SELECT d.id, d.company, d.contact_phone, d.stage,
               GROUP_CONCAT(DISTINCT o.channel) as channels,
               COUNT(o.id) as touch_count,
               MAX(o.created_at) as last_touch
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY d.id
        HAVING touch_count > 0
        ORDER BY last_touch DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    print("PIPELINE PHONE COVERAGE")
    print("=" * 50)
    print(f"  Total active deals:  {stats['total_active_deals']}")
    print(f"  With phone:          {stats['has_phone']} ({stats['phone_coverage_pct']}%)")
    print(f"  Missing phone:       {stats['missing_phone']}")
    print(f"  Called (phone):      {stats['called']}")
    print(f"  Emailed:             {stats['emailed']}")
    print()
    print("BY STAGE:")
    for s in stages:
        pct = round(s['with_phone'] / max(s['total'], 1) * 100)
        print(f"  {s['stage']:20s} {s['total']:4d} deals | {s['with_phone']:4d} with phone ({pct}%)")
    print()
    print("RECENTLY CONTACTED:")
    for c in contacted[:10]:
        print(f"  {c['company'][:30]:30s} | {c['channels'] or 'none':15s} | {c['touch_count']} touches | last: {(c['last_touch'] or '')[:10]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        show_stats()
    elif cmd == "check":
        run_enrichment(dry_run=True)
    elif cmd == "enrich":
        run_enrichment(dry_run=False)
    else:
        print("Usage: python -m src.enrich_phones [stats|check|enrich]")
