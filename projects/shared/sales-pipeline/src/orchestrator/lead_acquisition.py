#!/usr/bin/env python3
"""
Lead Acquisition — Pull + import fresh leads from Apollo API.

Searches Apollo for businesses matching the SW Florida ICP,
deduplicates against existing pipeline.db deals, and inserts
new leads as Prospects with scored=False.
"""

import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

from .config import (
    APOLLO_API_KEY, APOLLO_BASE_URL, APOLLO_SEARCH_LIMIT,
    APOLLO_SEARCH_CONFIG, DB_PATH, ICP_INDUSTRIES, DATA_DIR,
)


def _normalize_phone(phone: str) -> str:
    """Strip phone to digits only for dedup comparison."""
    if not phone:
        return ""
    return "".join(c for c in phone if c.isdigit())[-10:]  # Last 10 digits


def _normalize_company(name: str) -> str:
    """Normalize company name for dedup."""
    if not name:
        return ""
    return name.strip().lower().replace(",", "").replace(".", "").replace("llc", "").replace("inc", "").strip()


def search_apollo(industry: str = None, location: str = None, page: int = 1) -> list:
    """
    Search Apollo People API for leads matching ICP.

    Args:
        industry: Specific industry keyword to search (or None for all ICP)
        location: Specific location (or None for all SW Florida)
        page: Page number for pagination

    Returns:
        List of lead dicts with contact + company info
    """
    if not APOLLO_API_KEY:
        print("  [WARN] APOLLO_API_KEY not set — skipping Apollo search")
        return []

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }

    # Build search payload
    payload = {
        "page": page,
        "per_page": min(APOLLO_SEARCH_LIMIT, 100),
        "person_titles": APOLLO_SEARCH_CONFIG["person_titles"],
        "organization_num_employees_ranges": APOLLO_SEARCH_CONFIG["organization_num_employees_ranges"],
    }

    # Location filter
    if location:
        payload["person_locations"] = [location]
    else:
        payload["person_locations"] = APOLLO_SEARCH_CONFIG["person_locations"]

    # Industry filter
    if industry:
        payload["q_organization_keyword_tags"] = [industry]
    else:
        payload["q_organization_keyword_tags"] = APOLLO_SEARCH_CONFIG["q_organization_keyword_tags"]

    try:
        resp = requests.post(
            f"{APOLLO_BASE_URL}/mixed_people/api_search",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        people = data.get("people", [])
        total = data.get("pagination", {}).get("total_entries", 0)
        print(f"  Apollo returned {len(people)} results (total available: {total})")
        return people
    except requests.exceptions.HTTPError as e:
        print(f"  [ERROR] Apollo API HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text[:300]}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Apollo API request failed: {e}")
        return []


def parse_apollo_lead(person: dict) -> dict:
    """Extract structured lead data from Apollo person record."""
    org = person.get("organization", {}) or {}
    phone_numbers = person.get("phone_numbers", []) or []
    primary_phone = ""
    if phone_numbers:
        # Prefer direct dial, then mobile, then any
        for ptype in ["direct_dial", "mobile", "work_hq"]:
            for p in phone_numbers:
                if p.get("type") == ptype and p.get("number"):
                    primary_phone = p["number"]
                    break
            if primary_phone:
                break
        if not primary_phone and phone_numbers[0].get("number"):
            primary_phone = phone_numbers[0]["number"]

    # Determine industry from org keywords
    org_keywords = (org.get("keywords") or [])
    industry = "Other"
    org_industry = (org.get("industry") or "").lower()
    for icp in ICP_INDUSTRIES:
        icp_lower = icp.lower()
        if icp_lower in org_industry:
            industry = icp
            break
        for kw in org_keywords:
            if icp_lower in (kw or "").lower():
                industry = icp
                break
        if industry != "Other":
            break

    # Location
    city = person.get("city", "") or org.get("city", "") or ""
    state = person.get("state", "") or org.get("state", "") or ""

    return {
        "company": org.get("name", "Unknown Company"),
        "contact_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        "contact_email": person.get("email", "") or "",
        "contact_phone": primary_phone,
        "industry": industry,
        "website": org.get("website_url", "") or "",
        "city": city,
        "state": state if state else "FL",
        "lead_source": "Apollo",
        "notes": "",
        "employee_count": org.get("estimated_num_employees", 0) or 0,
    }


def get_existing_companies(conn: sqlite3.Connection) -> set:
    """Get set of normalized company names + phones for dedup."""
    rows = conn.execute("SELECT company, contact_phone FROM deals").fetchall()
    existing = set()
    for row in rows:
        existing.add(_normalize_company(row[0]))
        phone = _normalize_phone(row[1])
        if phone:
            existing.add(phone)
    return existing


def import_leads(leads: list, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    """
    Import parsed leads into pipeline.db, skipping duplicates.

    Args:
        leads: List of lead dicts from parse_apollo_lead
        conn: Database connection
        dry_run: If True, don't actually insert

    Returns:
        Count of new leads added
    """
    existing = get_existing_companies(conn)
    added = 0
    skipped = 0

    for lead in leads:
        # Dedup check: company name OR phone
        norm_company = _normalize_company(lead["company"])
        norm_phone = _normalize_phone(lead.get("contact_phone", ""))

        if norm_company in existing:
            skipped += 1
            continue
        if norm_phone and norm_phone in existing:
            skipped += 1
            continue

        # Skip leads without website (per spec: we want businesses that invest)
        if not lead.get("website"):
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY] Would add: {lead['company']} ({lead['industry']}) - {lead['city']}")
            added += 1
            existing.add(norm_company)
            if norm_phone:
                existing.add(norm_phone)
            continue

        # Insert new deal
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO deals (
                company, contact_name, contact_phone, contact_email,
                industry, website, city, state, lead_source,
                stage, notes, created_at, updated_at, tower
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Prospect', ?, ?, ?, 'digital-ai-services')
        """, (
            lead["company"], lead["contact_name"], lead["contact_phone"],
            lead["contact_email"], lead["industry"], lead["website"],
            lead["city"], lead["state"], lead["lead_source"],
            f"Employees: ~{lead.get('employee_count', 'unknown')}",
            now, now,
        ))
        added += 1
        existing.add(norm_company)
        if norm_phone:
            existing.add(norm_phone)

    if not dry_run:
        conn.commit()

    print(f"  Imported: {added} new leads, skipped {skipped} duplicates")
    return added


def run_acquisition(dry_run: bool = False, industries: list = None, limit: int = None) -> int:
    """
    Run full lead acquisition cycle.

    Searches Apollo for each ICP industry in SW Florida,
    deduplicates, and imports new leads.

    Args:
        dry_run: Preview only, don't insert
        industries: Specific industries to search (or None for all ICP)
        limit: Max total leads to import

    Returns:
        Total new leads added
    """
    print("\n=== LEAD ACQUISITION ===")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure migration has run
    from ..models import _create_tables
    _create_tables(conn)

    target_industries = industries or ICP_INDUSTRIES
    total_added = 0
    all_leads = []

    for industry in target_industries:
        print(f"\n  Searching Apollo: {industry} in SW Florida...")
        people = search_apollo(industry=industry)

        for person in people:
            lead = parse_apollo_lead(person)
            # Override industry with the one we searched for (more accurate)
            if lead["industry"] == "Other":
                lead["industry"] = industry
            all_leads.append(lead)

        if limit and len(all_leads) >= limit:
            all_leads = all_leads[:limit]
            break

    if all_leads:
        total_added = import_leads(all_leads, conn, dry_run=dry_run)
    else:
        print("  No new leads found from Apollo")

    # Save raw search results for reference
    if all_leads and not dry_run:
        log_file = DATA_DIR / f"apollo_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump(all_leads, f, indent=2, default=str)
        print(f"  Raw results saved to: {log_file}")

    conn.close()
    print(f"\n  Total new leads: {total_added}")
    return total_added


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run_acquisition(dry_run=dry)
