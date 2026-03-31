#!/usr/bin/env python3
"""
Apollo Prospect Pipeline — 2026-03-23
Searches for Naples FL business prospects, deduplicates against existing CSV,
and attempts email enrichment for prospects missing emails.

Credit-conscious: search is free, enrichment costs 1 credit per person.
"""

import csv
import json
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# --- Config ---
SANDBOX = "/Users/williammarceaujr./dev-sandbox"
EXISTING_CSV = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo.csv"
OUTPUT_JSON = f"{SANDBOX}/projects/shared/lead-scraper/output/apollo_fresh_prospects_2026-03-23.json"
UPDATED_CSV = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo-enriched-2026-03-23.csv"

# Load API key from .env
API_KEY = None
with open(f"{SANDBOX}/.env") as f:
    for line in f:
        if "APOLLO_API_KEY" in line and not line.strip().startswith("#"):
            API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
            break

if not API_KEY:
    print("ERROR: APOLLO_API_KEY not found in .env")
    sys.exit(1)

print(f"Apollo API key loaded ({len(API_KEY)} chars)")

BASE_URL = "https://api.apollo.io/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "x-api-key": API_KEY
}

# --- Rate limiting ---
last_request = 0
def rate_limit():
    global last_request
    elapsed = time.time() - last_request
    if elapsed < 1.2:  # ~50 req/min
        time.sleep(1.2 - elapsed)
    last_request = time.time()

def api_post(endpoint, data):
    rate_limit()
    try:
        resp = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  API error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  Request error: {e}")
        return None

# --- Step 1: Load existing prospects ---
print("\n=== Step 1: Loading existing prospects ===")
existing = []
existing_companies = set()
with open(EXISTING_CSV) as f:
    reader = csv.DictReader(f)
    existing = list(reader)
    for row in existing:
        name = (row.get("company_name", "") or "").strip().lower()
        if name:
            existing_companies.add(name)

print(f"Loaded {len(existing)} existing prospects")
print(f"Unique company names: {len(existing_companies)}")
with_email = sum(1 for r in existing if (r.get("email", "") or "").strip())
print(f"With email: {with_email}, Without: {len(existing) - with_email}")

# --- Step 2: Search for NEW prospects ---
print("\n=== Step 2: Searching for new Naples FL prospects ===")

# Industries to search — these map well to Apollo's search
INDUSTRIES = [
    "HVAC",
    "plumbing",
    "electrical contractor",
    "landscaping",
    "roofing",
    "pest control",
    "dental",
    "medical practice",
    "legal",
    "property management",
    "auto repair",
    "veterinary",
]

TITLES = ["owner", "ceo", "founder", "president", "managing partner", "principal"]

all_new_prospects = []
seen_ids = set()
credits_used = 0
api_calls = 0

for industry in INDUSTRIES:
    print(f"\n  Searching: {industry}...")

    for page in range(1, 4):  # Max 3 pages per industry (300 results)
        data = {
            "person_titles": TITLES,
            "organization_locations": ["Naples, Florida, United States"],
            "organization_num_employees_ranges": ["1,10", "11,50"],
            "q_keywords": industry,
            "page": page,
            "per_page": 100
        }

        result = api_post("/mixed_people/search", data)
        api_calls += 1

        if not result:
            print(f"    Page {page}: API error, skipping")
            break

        people = result.get("people", [])
        pagination = result.get("pagination", {})
        total_entries = pagination.get("total_entries", 0)

        if page == 1:
            print(f"    Total available: {total_entries}")

        if not people:
            break

        for person in people:
            pid = person.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            org = person.get("organization", {}) or {}
            company_name = (org.get("name", "") or "").strip()

            # Check if this company already exists
            if company_name.lower() in existing_companies:
                continue

            prospect = {
                "apollo_id": pid,
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "full_name": person.get("name", ""),
                "title": person.get("title", ""),
                "email": person.get("email", ""),
                "email_status": person.get("email_status", ""),
                "phone": "",
                "linkedin_url": person.get("linkedin_url", ""),
                "company_name": company_name,
                "company_domain": org.get("website_url", ""),
                "industry": org.get("industry", "") or industry,
                "search_industry": industry,
                "employee_count": org.get("estimated_num_employees", ""),
                "city": person.get("city", ""),
                "state": person.get("state", ""),
                "seniority": person.get("seniority", ""),
                "source": "apollo_search",
                "found_date": "2026-03-23"
            }

            # Extract phone if available
            phones = person.get("phone_numbers", [])
            if phones:
                prospect["phone"] = phones[0].get("raw_number", "")

            all_new_prospects.append(prospect)

        print(f"    Page {page}: {len(people)} people, {len(all_new_prospects)} new unique so far")

        # Don't go past available pages
        total_pages = pagination.get("total_pages", 1)
        if page >= total_pages:
            break

print(f"\n  Total new prospects found: {len(all_new_prospects)}")
print(f"  API calls used for search: {api_calls}")
new_with_email = sum(1 for p in all_new_prospects if p.get("email", ""))
print(f"  New prospects with email: {new_with_email}")

# --- Step 3: Enrichment for existing prospects missing emails ---
print("\n=== Step 3: Email enrichment for existing prospects ===")
print("NOTE: Person enrichment costs 1 credit per lookup.")
print("Being credit-conscious: only enriching prospects where we have first+last name + company domain")

# Find enrichable existing prospects (have name + website but no email)
enrichable = []
for row in existing:
    if (row.get("email", "") or "").strip():
        continue  # Already has email
    first = (row.get("first_name", "") or "").strip()
    website = (row.get("website", "") or "").strip()
    company = (row.get("company_name", "") or "").strip()
    if first and website and company:
        enrichable.append(row)

print(f"Enrichable prospects (have name + website, no email): {len(enrichable)}")

# Cap enrichment to save credits — do max 50
ENRICH_CAP = 50
enrichable = enrichable[:ENRICH_CAP]
print(f"Enriching up to {len(enrichable)} prospects (capped at {ENRICH_CAP} to save credits)")

enriched_count = 0
enrichment_results = []

for i, row in enumerate(enrichable):
    first = row.get("first_name", "").strip()
    last = row.get("last_name", "").strip()
    website = row.get("website", "").strip()
    company = row.get("company_name", "").strip()

    # Extract domain from website
    domain = website.replace("http://", "").replace("https://", "").split("/")[0]

    print(f"  [{i+1}/{len(enrichable)}] {first} {last} @ {company} ({domain})...", end=" ")

    data = {
        "first_name": first,
        "organization_name": company,
    }
    if last:
        data["last_name"] = last
    if domain:
        data["domain"] = domain

    result = api_post("/people/match", data)
    api_calls += 1
    credits_used += 1

    if result and result.get("person"):
        person = result["person"]
        email = person.get("email", "")
        if email:
            enriched_count += 1
            print(f"FOUND: {email}")
            enrichment_results.append({
                "company_name": company,
                "contact_name": f"{first} {last}".strip(),
                "email": email,
                "email_status": person.get("email_status", ""),
                "apollo_id": row.get("apollo_id", "")
            })
        else:
            print("no email returned")
    else:
        print("no match")

print(f"\n  Enrichment complete: {enriched_count}/{len(enrichable)} emails found")
print(f"  Credits used for enrichment: {credits_used}")

# --- Step 4: Save results ---
print("\n=== Step 4: Saving results ===")

# Save new prospects as JSON
output_data = {
    "generated": "2026-03-23",
    "search_criteria": {
        "location": "Naples, Florida",
        "industries": INDUSTRIES,
        "titles": TITLES,
        "employee_ranges": ["1-10", "11-50"]
    },
    "stats": {
        "existing_prospects": len(existing),
        "existing_with_email": with_email,
        "new_prospects_found": len(all_new_prospects),
        "new_with_email": new_with_email,
        "enrichment_attempted": len(enrichable),
        "emails_enriched": enriched_count,
        "enrichment_credits_used": credits_used,
        "total_api_calls": api_calls
    },
    "new_prospects": all_new_prospects,
    "enrichment_results": enrichment_results
}

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
with open(OUTPUT_JSON, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"New prospects saved to: {OUTPUT_JSON}")

# Save updated CSV with enriched emails merged back
print("Updating CSV with enriched emails...")
enrichment_lookup = {}
for er in enrichment_results:
    key = (er["company_name"].lower(), er["contact_name"].lower())
    enrichment_lookup[key] = er["email"]

updated_count = 0
fieldnames = existing[0].keys() if existing else []
with open(UPDATED_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in existing:
        company = (row.get("company_name", "") or "").strip().lower()
        contact = (row.get("contact_name", "") or "").strip().lower()
        key = (company, contact)
        if key in enrichment_lookup and not (row.get("email", "") or "").strip():
            row["email"] = enrichment_lookup[key]
            updated_count += 1
        writer.writerow(row)

print(f"Updated CSV saved to: {UPDATED_CSV}")
print(f"Emails merged into existing records: {updated_count}")

# --- Summary ---
print("\n" + "=" * 60)
print("APOLLO PIPELINE SUMMARY — 2026-03-23")
print("=" * 60)
print(f"Existing prospects:        {len(existing)}")
print(f"  With email:              {with_email}")
print(f"  Without email:           {len(existing) - with_email}")
print(f"")
print(f"NEW prospects found:       {len(all_new_prospects)}")
print(f"  With email:              {new_with_email}")
print(f"  Without email:           {len(all_new_prospects) - new_with_email}")
print(f"")
print(f"Enrichment results:        {enriched_count}/{len(enrichable)} emails found")
print(f"Enrichment credits used:   {credits_used}")
print(f"Total API calls:           {api_calls}")
print(f"")
print(f"Output files:")
print(f"  New prospects JSON:      {OUTPUT_JSON}")
print(f"  Updated CSV:             {UPDATED_CSV}")
print("=" * 60)

# Industry breakdown of new prospects
if all_new_prospects:
    print("\nNew prospects by search industry:")
    by_ind = {}
    for p in all_new_prospects:
        ind = p.get("search_industry", "other")
        by_ind[ind] = by_ind.get(ind, 0) + 1
    for k, v in sorted(by_ind.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
