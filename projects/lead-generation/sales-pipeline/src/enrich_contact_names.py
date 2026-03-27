#!/usr/bin/env python3
"""
Batch-enrich missing contact names in pipeline.db.

Step 1: Pattern extraction — "[Name] Chiropractic/Plumbing/Roofing/etc" → "Dr. Name" or "Name"
Step 2: Apollo people search — for companies that don't yield a name via pattern

Run before a call blitz to ensure every deal has a first name ready.

Usage:
    python -m projects.shared.sales-pipeline.src.enrich_contact_names
    python -m projects.shared.sales-pipeline.src.enrich_contact_names --dry-run
    python -m projects.shared.sales-pipeline.src.enrich_contact_names --apollo-only
"""

import sys
import os
import re
import time
import sqlite3
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from dotenv import load_dotenv
load_dotenv('.env')

DB_PATH = 'projects/lead-generation/sales-pipeline/data/pipeline.db'

# Company name suffixes that indicate a named owner practice
# Format: (pattern_regex, title_prefix)
NAMED_PRACTICE_PATTERNS = [
    # Medical / Chiro — always "Dr."
    (r'^(\w+)\s+chiropractic', 'Dr.'),
    (r'^(\w+)\s+chiro\b', 'Dr.'),
    (r'^(\w+)\s+spinal', 'Dr.'),
    (r'^(\w+)\s+family\s+chiro', 'Dr.'),
    (r'^(\w+)\s+family\s+health', 'Dr.'),
    (r'^(\w+)\s+family\s+wellness', 'Dr.'),
    (r'^(\w+)\s+wellness\s+care', 'Dr.'),
    (r'^(\w+)\s+dental', 'Dr.'),
    (r'^(\w+)\s+orthodontics', 'Dr.'),
    (r'^(\w+)\s+medical', 'Dr.'),
    (r'^(\w+)\s+health\s+center', 'Dr.'),
    (r'^(\w+)\s+injury\s+clinic', 'Dr.'),
    # Trades — no title
    (r'^(\w+)\s+plumbing', ''),
    (r'^(\w+)\s+roofing', ''),
    (r'^(\w+)\s+hvac', ''),
    (r'^(\w+)\s+electric', ''),
    (r'^(\w+)\s+construction', ''),
    (r'^(\w+)\s+pest\s+control', ''),
    # Aesthetics / medspa — no title
    (r'^(\w+)\s+medspa', ''),
    (r'^(\w+)\s+med\s+spa', ''),
    (r'^(\w+)\s+aesthetics', ''),
]

# Words that are NOT names (generic business words)
NON_NAME_WORDS = {
    'gulf', 'coast', 'naples', 'florida', 'collier', 'north', 'south', 'east', 'west',
    'premier', 'elite', 'prime', 'advanced', 'best', 'pro', 'professional',
    'american', 'national', 'local', 'community', 'family', 'wellness',
    'health', 'care', 'center', 'clinic', 'group', 'services', 'solutions',
    'emergency', 'urgent', 'express', 'rapid', 'quick', 'all', 'total',
    'complete', 'comprehensive', 'integrated', 'alternative', 'natural',
    'thrive', 'caliber', 'maxliving', 'chiromed', 'chiropractic', 'lifestrength',
    'amazing', 'trinity', 'access', 'parkway', 'vanderbilt', 'moonlight',
    'sunshine', 'suncoast', 'tropical', 'paradise', 'personalized', 'innovative',
    'harmony', 'synergy', 'collective', 'integrated', 'accurate', 'speedy', 'modern',
}


def extract_name_from_company(company: str) -> tuple[str, str]:
    """
    Try to extract owner name from company name pattern.
    Returns (extracted_name, source) or ('', '') if no match.
    """
    company_lower = company.lower().strip()

    for pattern, title in NAMED_PRACTICE_PATTERNS:
        m = re.match(pattern, company_lower, re.IGNORECASE)
        if m:
            candidate = m.group(1).capitalize()
            if candidate.lower() in NON_NAME_WORDS:
                continue
            if len(candidate) < 3:
                continue
            name = f"{title} {candidate}".strip() if title else candidate
            return name, 'pattern'

    return '', ''


def apollo_lookup(company: str, api_key: str) -> tuple[str, str]:
    """
    Search Apollo for the owner of a company in Naples FL.
    Returns (full_name, source) or ('', '') if not found.
    """
    import requests

    headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    payload = {
        'q_keywords': company,
        'person_locations': ['Naples, Florida'],
        'person_titles': ['Owner', 'Founder', 'President', 'CEO', 'Doctor', 'Physician', 'Chiropractor', 'Principal'],
        'per_page': 5,
        'page': 1,
    }

    try:
        resp = requests.post(
            'https://api.apollo.io/api/v1/mixed_people/api_search',
            json=payload, headers=headers, timeout=15
        )
        if resp.status_code == 200:
            people = resp.json().get('people', [])
            if people:
                p = people[0]
                first = p.get('first_name', '')
                last = p.get('last_name', '')
                if first and last:
                    return f"{first} {last}", 'apollo'
    except Exception as e:
        print(f"    Apollo error for '{company}': {e}")

    return '', ''


def run(dry_run=False, apollo_only=False, pattern_only=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, company, contact_name
        FROM deals
        WHERE (contact_name IS NULL OR contact_name = '' OR contact_name = 'Unknown')
        AND stage NOT IN ('Closed Won', 'Closed Lost')
        ORDER BY id
    """)
    missing = cur.fetchall()
    print(f"Deals missing contact name: {len(missing)}")

    api_key = os.getenv('APOLLO_API_KEY', '')
    if not api_key and not pattern_only:
        # Try hardcoded key from existing scripts as fallback
        api_key = 'RhRnIKITS2Ye6qSQQO9hUg'

    updated = []
    skipped = []

    for deal_id, company, current_name in missing:
        name, source = '', ''

        if not apollo_only:
            name, source = extract_name_from_company(company)

        if not name and not pattern_only and api_key:
            time.sleep(1.2)  # rate limit
            name, source = apollo_lookup(company, api_key)

        if name:
            updated.append((deal_id, company, name, source))
            if not dry_run:
                cur.execute(
                    "UPDATE deals SET contact_name = ?, updated_at = datetime('now') WHERE id = ?",
                    (name, deal_id)
                )
        else:
            skipped.append((deal_id, company))

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  Enriched: {len(updated)}")
    print(f"  No match: {len(skipped)}")

    print("\nEnriched:")
    for deal_id, company, name, source in updated:
        print(f"  [{deal_id}] {company:<50} → {name} ({source})")

    if skipped:
        print("\nStill missing (need manual research or Apollo UI):")
        for deal_id, company in skipped:
            print(f"  [{deal_id}] {company}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only — no DB writes')
    parser.add_argument('--apollo-only', action='store_true', help='Skip pattern extraction, only use Apollo')
    parser.add_argument('--pattern-only', action='store_true', help='Skip Apollo, only use pattern extraction')
    args = parser.parse_args()
    run(dry_run=args.dry_run, apollo_only=args.apollo_only, pattern_only=args.pattern_only)
