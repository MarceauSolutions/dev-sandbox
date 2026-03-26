#!/usr/bin/env python3
"""
Apollo Prospect Pipeline v2 — 2026-03-23
Fixed: uses /mixed_people/api_search (new endpoint) and reveal_personal_emails for enrichment.
"""

import csv
import json
import os
import sys
import time
import requests
from datetime import datetime

SANDBOX = "/Users/williammarceaujr./dev-sandbox"
EXISTING_CSV = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo.csv"
OUTPUT_JSON = f"{SANDBOX}/projects/shared/lead-scraper/output/apollo_fresh_prospects_2026-03-23.json"
UPDATED_CSV = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo-enriched-2026-03-23.csv"

# Load API key
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

BASE_URL = "https://api.apollo.io"
HEADERS = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "x-api-key": API_KEY
}

last_request = 0
def rate_limit():
    global last_request
    elapsed = time.time() - last_request
    if elapsed < 1.3:
        time.sleep(1.3 - elapsed)
    last_request = time.time()

def api_post(endpoint, data):
    rate_limit()
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.post(url, json=data, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  API {resp.status_code}: {resp.text[:300]}")
            return {"_error": resp.status_code, "_body": resp.text[:500]}
    except Exception as e:
        print(f"  Request error: {e}")
        return None

# ============================
# Step 1: Load existing
# ============================
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

with_email = sum(1 for r in existing if (r.get("email", "") or "").strip())
print(f"Loaded {len(existing)} existing | {with_email} with email | {len(existing)-with_email} without")

# ============================
# Step 2: Search new prospects
# ============================
print("\n=== Step 2: Searching new Naples FL prospects ===")
print("Using POST /v1/mixed_people/api_search (new endpoint)")

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
]

TITLES = ["owner", "ceo", "founder", "president", "managing partner"]

all_new = []
seen_ids = set()
api_calls = 0
search_errors = []

for industry in INDUSTRIES:
    print(f"\n  Searching: {industry}...")

    for page in range(1, 4):
        data = {
            "person_titles": TITLES,
            "organization_locations": ["Naples, Florida, United States"],
            "organization_num_employees_ranges": ["1,10", "11,50"],
            "q_keywords": industry,
            "page": page,
            "per_page": 100
        }

        result = api_post("/v1/mixed_people/api_search", data)
        api_calls += 1

        if not result or "_error" in (result or {}):
            err_code = (result or {}).get("_error", "unknown")
            err_body = (result or {}).get("_body", "no response")
            if err_code not in [e.get("code") for e in search_errors]:
                search_errors.append({"code": err_code, "body": err_body[:200], "industry": industry})
            print(f"    Page {page}: error {err_code}")
            break

        people = result.get("people", [])
        pagination = result.get("pagination", {})
        total = pagination.get("total_entries", 0)

        if page == 1:
            print(f"    Total available: {total}")

        if not people:
            break

        for person in people:
            pid = person.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            org = person.get("organization", {}) or {}
            cname = (org.get("name", "") or "").strip()

            if cname.lower() in existing_companies:
                continue

            phones = person.get("phone_numbers", [])
            prospect = {
                "apollo_id": pid,
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "full_name": person.get("name", ""),
                "title": person.get("title", ""),
                "email": person.get("email", ""),
                "email_status": person.get("email_status", ""),
                "phone": phones[0].get("raw_number", "") if phones else "",
                "linkedin_url": person.get("linkedin_url", ""),
                "company_name": cname,
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
            all_new.append(prospect)

        print(f"    Page {page}: {len(people)} results, {len(all_new)} new unique total")
        if page >= pagination.get("total_pages", 1):
            break

new_with_email = sum(1 for p in all_new if p.get("email", ""))
print(f"\n  NEW prospects: {len(all_new)} ({new_with_email} with email)")
print(f"  Search API calls: {api_calls}")

if search_errors:
    print(f"\n  SEARCH ERRORS encountered:")
    for e in search_errors:
        print(f"    [{e['code']}] {e['industry']}: {e['body'][:150]}")

# ============================
# Step 3: Enrichment
# ============================
print("\n=== Step 3: Email enrichment for existing prospects ===")
print("Using POST /v1/people/match with reveal_personal_emails=true")

enrichable = []
for row in existing:
    if (row.get("email", "") or "").strip():
        continue
    first = (row.get("first_name", "") or "").strip()
    website = (row.get("website", "") or "").strip()
    company = (row.get("company_name", "") or "").strip()
    if first and website and company:
        enrichable.append(row)

ENRICH_CAP = 25  # Conservative — save credits
enrichable = enrichable[:ENRICH_CAP]
print(f"Enrichable: {len(enrichable)} (capped at {ENRICH_CAP})")

enriched_count = 0
enrichment_results = []
credits_used = 0

for i, row in enumerate(enrichable):
    first = row.get("first_name", "").strip()
    last = row.get("last_name", "").strip()
    website = row.get("website", "").strip()
    company = row.get("company_name", "").strip()
    domain = website.replace("http://", "").replace("https://", "").split("/")[0]

    print(f"  [{i+1}/{len(enrichable)}] {first} {last} @ {domain}...", end=" ", flush=True)

    data = {
        "first_name": first,
        "organization_name": company,
        "domain": domain,
        "reveal_personal_emails": True,
    }
    if last:
        data["last_name"] = last

    result = api_post("/v1/people/match", data)
    api_calls += 1
    credits_used += 1

    if not result or "_error" in (result or {}):
        err = (result or {}).get("_error", "?")
        print(f"error {err}")
        # If we get a 403/402 = out of credits, stop
        if err in [402, 403]:
            print("  STOPPING enrichment — credit/permission issue")
            break
        continue

    person = (result or {}).get("person")
    if person:
        email = person.get("email", "")
        if email:
            enriched_count += 1
            print(f"FOUND: {email}")
            enrichment_results.append({
                "company_name": company,
                "contact_name": f"{first} {last}".strip(),
                "email": email,
                "email_status": person.get("email_status", ""),
            })
        else:
            print("no email")
    else:
        print("no match")

print(f"\n  Enriched: {enriched_count}/{len(enrichable)}")
print(f"  Credits used: {credits_used}")

# ============================
# Step 4: Save
# ============================
print("\n=== Step 4: Saving results ===")

output_data = {
    "generated": "2026-03-23",
    "pipeline_version": "v2",
    "search_criteria": {
        "location": "Naples, Florida",
        "industries": INDUSTRIES,
        "titles": TITLES,
        "employee_ranges": ["1-10", "11-50"]
    },
    "stats": {
        "existing_prospects": len(existing),
        "existing_with_email": with_email,
        "new_prospects_found": len(all_new),
        "new_with_email": new_with_email,
        "enrichment_attempted": len(enrichable),
        "emails_enriched": enriched_count,
        "credits_used": credits_used,
        "total_api_calls": api_calls,
        "search_errors": search_errors
    },
    "new_prospects": all_new,
    "enrichment_results": enrichment_results
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"Saved: {OUTPUT_JSON}")

# Merge enriched emails into updated CSV
enrichment_lookup = {}
for er in enrichment_results:
    key = (er["company_name"].lower(), er["contact_name"].lower())
    enrichment_lookup[key] = er["email"]

updated_count = 0
fieldnames = list(existing[0].keys()) if existing else []
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
print(f"Saved: {UPDATED_CSV} ({updated_count} emails merged)")

# Summary
print("\n" + "=" * 60)
print("APOLLO PIPELINE SUMMARY — 2026-03-23 (v2)")
print("=" * 60)
print(f"Existing:            {len(existing)} ({with_email} with email)")
print(f"New found:           {len(all_new)} ({new_with_email} with email)")
print(f"Enriched:            {enriched_count}/{len(enrichable)}")
print(f"Credits used:        {credits_used}")
print(f"API calls:           {api_calls}")
print(f"Search errors:       {len(search_errors)}")
if search_errors:
    print(f"  First error code:  {search_errors[0]['code']}")
    print(f"  Error detail:      {search_errors[0]['body'][:200]}")
print("=" * 60)

if all_new:
    print("\nNew prospects by industry:")
    by_ind = {}
    for p in all_new:
        ind = p.get("search_industry", "other")
        by_ind[ind] = by_ind.get(ind, 0) + 1
    for k, v in sorted(by_ind.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
