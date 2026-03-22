#!/usr/bin/env python3
"""
Naples FL Prospect List Builder — Apollo.io API

Searches Apollo.io for small businesses in Naples, FL across target industries
for AI automation services outreach. Exports to CSV.

Industries: Home Services/HVAC, Medical/Dental, Real Estate, Restaurants/Hospitality, Med Spas/Beauty
Target: 200-500 prospects, employee count 5-50

Usage:
    python scripts/build-naples-prospect-list.py
    python scripts/build-naples-prospect-list.py --max-results 300
    python scripts/build-naples-prospect-list.py --output docs/naples-prospects.csv
"""

import requests
import csv
import time
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"

# Naples FL zip codes
NAPLES_ZIPS = [f"341{i:02d}" for i in range(1, 21)]  # 34101-34120

# Target industries (Apollo industry keywords)
INDUSTRY_SEARCHES = [
    {
        "label": "HVAC / Home Services",
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": ["hvac", "plumbing", "electrical", "roofing", "home services", "air conditioning", "pest control", "landscaping", "pool service"],
    },
    {
        "label": "Medical / Dental",
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": ["dental", "dentist", "medical practice", "physician", "dermatology", "chiropractic", "physical therapy", "veterinary"],
    },
    {
        "label": "Real Estate",
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": ["real estate", "property management", "real estate agent", "mortgage", "title company"],
    },
    {
        "label": "Restaurants / Hospitality",
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": ["restaurant", "catering", "bar", "hospitality", "hotel", "resort", "cafe"],
    },
    {
        "label": "Med Spa / Beauty",
        "organization_industry_tag_ids": [],
        "q_organization_keyword_tags": ["med spa", "medspa", "beauty salon", "hair salon", "spa", "aesthetics", "cosmetic", "wellness center", "nail salon"],
    },
]

# Decision-maker titles to target
TARGET_TITLES = [
    "owner",
    "founder",
    "ceo",
    "president",
    "general manager",
    "managing partner",
    "principal",
    "director of operations",
    "office manager",
    "practice manager",
]


def get_headers():
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }


def check_api_key():
    """Verify the Apollo API key is valid before running searches."""
    # Try a minimal search to test auth
    url = f"{APOLLO_BASE_URL}/mixed_people/api_search"
    payload = {
        # api_key passed via X-Api-Key header (body param deprecated)
        "page": 1,
        "per_page": 1,
        "person_locations": ["Naples, Florida, United States"],
    }
    try:
        resp = requests.post(url, headers=get_headers(), json=payload, timeout=15)
        if resp.status_code == 401:
            print(f"ERROR: Apollo API key is invalid or expired (HTTP 401).")
            print(f"  Key (first 8 chars): {APOLLO_API_KEY[:8]}...")
            print(f"  Response: {resp.text[:300]}")
            print(f"\nTo fix: generate a new key at https://app.apollo.io/#/settings/integrations/api")
            print(f"Then update APOLLO_API_KEY in .env")
            return False
        if resp.status_code == 403:
            print(f"ERROR: Apollo API access forbidden (HTTP 403). Check plan limits.")
            return False
        resp.raise_for_status()
        total = resp.json().get("pagination", {}).get("total_entries", 0)
        print(f"  API key valid. Test query returned {total} total people in Naples FL.\n")
        return True
    except Exception as e:
        print(f"ERROR: Could not verify API key: {e}")
        return False


def search_people(keywords, page=1, per_page=25):
    """
    Search Apollo for people matching criteria in Naples FL.
    Uses the mixed_people/api_search endpoint.
    """
    url = f"{APOLLO_BASE_URL}/mixed_people/api_search"

    payload = {
        # api_key passed via X-Api-Key header (body param deprecated)
        "page": page,
        "per_page": per_page,
        "person_titles": TARGET_TITLES,
        "q_organization_keyword_tags": keywords,
        "person_locations": ["Naples, Florida, United States"],
        "organization_locations": ["Naples, Florida, United States"],
        "organization_num_employees_ranges": ["1,10", "11,20", "21,50"],
        "contact_email_status": ["verified", "guessed", "unavailable"],
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP Error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Request Error: {e}")
        return None


def search_organizations(keywords, page=1, per_page=25):
    """
    Search Apollo for organizations matching criteria in Naples FL.
    Fallback if people search yields limited results.
    """
    url = f"{APOLLO_BASE_URL}/mixed_companies/api_search"

    payload = {
        # api_key passed via X-Api-Key header (body param deprecated)
        "page": page,
        "per_page": per_page,
        "q_organization_keyword_tags": keywords,
        "organization_locations": ["Naples, Florida, United States"],
        "organization_num_employees_ranges": ["1,10", "11,20", "21,50"],
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP Error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Request Error: {e}")
        return None


def extract_person_data(person, industry_label):
    """Extract relevant fields from an Apollo person record."""
    org = person.get("organization", {}) or {}
    return {
        "company_name": org.get("name", ""),
        "contact_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        "first_name": person.get("first_name", ""),
        "last_name": person.get("last_name", ""),
        "title": person.get("title", ""),
        "email": person.get("email", ""),
        "phone": person.get("phone_number", "") or (person.get("phone_numbers", [{}]) or [{}])[0].get("sanitized_number", ""),
        "industry": industry_label,
        "apollo_industry": org.get("industry", ""),
        "employee_count": org.get("estimated_num_employees", ""),
        "website": org.get("website_url", ""),
        "linkedin_url": person.get("linkedin_url", ""),
        "city": person.get("city", ""),
        "state": person.get("state", ""),
        "country": person.get("country", ""),
        "seniority": person.get("seniority", ""),
        "apollo_id": person.get("id", ""),
    }


def extract_org_data(org, industry_label):
    """Extract relevant fields from an Apollo organization record."""
    return {
        "company_name": org.get("name", ""),
        "contact_name": "",
        "first_name": "",
        "last_name": "",
        "title": "",
        "email": "",
        "phone": org.get("phone", ""),
        "industry": industry_label,
        "apollo_industry": org.get("industry", ""),
        "employee_count": org.get("estimated_num_employees", ""),
        "website": org.get("website_url", ""),
        "linkedin_url": org.get("linkedin_url", ""),
        "city": org.get("city", ""),
        "state": org.get("state", ""),
        "country": org.get("country", ""),
        "seniority": "",
        "apollo_id": org.get("id", ""),
    }


def deduplicate(prospects):
    """Remove duplicates by company name + contact name."""
    seen = set()
    unique = []
    for p in prospects:
        key = (p["company_name"].lower().strip(), p["contact_name"].lower().strip())
        if key not in seen and p["company_name"]:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Build Naples FL prospect list from Apollo.io")
    parser.add_argument("--max-results", type=int, default=500, help="Max total prospects (default: 500)")
    parser.add_argument("--output", type=str, default="docs/naples-prospects.csv", help="Output CSV path")
    parser.add_argument("--org-fallback", action="store_true", help="Also search organizations (not just people)")
    args = parser.parse_args()

    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not found in .env")
        sys.exit(1)

    # Resolve output path relative to repo root
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Naples FL Prospect List Builder — Apollo.io")
    print(f"Target: up to {args.max_results} prospects")
    print(f"Output: {output_path}")
    print("=" * 70)

    print("\nVerifying API key...")
    if not check_api_key():
        sys.exit(1)

    all_prospects = []
    total_api_calls = 0

    for industry in INDUSTRY_SEARCHES:
        label = industry["label"]
        keywords = industry["q_organization_keyword_tags"]
        print(f"\n--- Searching: {label} ---")

        # Search in batches of keywords (Apollo handles arrays)
        page = 1
        industry_count = 0
        max_pages = 10  # Safety limit per industry

        while page <= max_pages and len(all_prospects) < args.max_results:
            print(f"  Page {page}...", end=" ", flush=True)

            result = search_people(keywords, page=page, per_page=100)
            total_api_calls += 1

            if not result:
                print("failed, moving on")
                break

            people = result.get("people", [])
            pagination = result.get("pagination", {})
            total_entries = pagination.get("total_entries", 0)

            if page == 1:
                print(f"({total_entries} total matches)")
            else:
                print(f"({len(people)} returned)")

            if not people:
                break

            for person in people:
                prospect = extract_person_data(person, label)
                all_prospects.append(prospect)
                industry_count += 1

            # Check if there are more pages
            total_pages = pagination.get("total_pages", 1)
            if page >= total_pages:
                break

            page += 1

            # Rate limiting: Apollo free tier = ~50 requests/hour
            # Be conservative: 1.5 sec between requests
            time.sleep(1.5)

        print(f"  -> {industry_count} prospects from {label}")

        # If we have enough, stop early
        if len(all_prospects) >= args.max_results:
            print(f"\nReached target of {args.max_results}, stopping search.")
            break

    # Organization search fallback if we're under target
    if args.org_fallback and len(all_prospects) < args.max_results // 2:
        print(f"\n--- Organization Search Fallback (only {len(all_prospects)} people found) ---")
        for industry in INDUSTRY_SEARCHES:
            label = industry["label"]
            keywords = industry["q_organization_keyword_tags"]

            result = search_organizations(keywords, page=1, per_page=100)
            total_api_calls += 1

            if result:
                orgs = result.get("organizations", []) or result.get("accounts", []) or []
                for org_data in orgs:
                    prospect = extract_org_data(org_data, label)
                    all_prospects.append(prospect)
                print(f"  {label}: +{len(orgs)} orgs")

            time.sleep(1.5)

    # Deduplicate
    before_dedup = len(all_prospects)
    all_prospects = deduplicate(all_prospects)
    after_dedup = len(all_prospects)

    print(f"\n{'=' * 70}")
    print(f"Results Summary")
    print(f"{'=' * 70}")
    print(f"  Total API calls: {total_api_calls}")
    print(f"  Raw results: {before_dedup}")
    print(f"  After dedup: {after_dedup}")

    # Stats by industry
    industry_counts = {}
    for p in all_prospects:
        ind = p["industry"]
        industry_counts[ind] = industry_counts.get(ind, 0) + 1

    print(f"\n  By Industry:")
    for ind, count in sorted(industry_counts.items()):
        print(f"    {ind}: {count}")

    # Count with emails
    with_email = sum(1 for p in all_prospects if p["email"])
    with_phone = sum(1 for p in all_prospects if p["phone"])
    print(f"\n  With email: {with_email}")
    print(f"  With phone: {with_phone}")

    # Write CSV
    if all_prospects:
        fieldnames = [
            "company_name", "contact_name", "first_name", "last_name",
            "title", "email", "phone", "industry", "apollo_industry",
            "employee_count", "website", "linkedin_url", "city", "state",
            "country", "seniority", "apollo_id",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_prospects)

        print(f"\n  CSV written to: {output_path}")
        print(f"  Total prospects: {after_dedup}")
    else:
        print("\n  No prospects found. Check API key and search parameters.")

    print(f"\n{'=' * 70}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
