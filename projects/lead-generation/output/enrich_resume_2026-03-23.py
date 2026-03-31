#!/usr/bin/env python3
"""
Resume Apollo enrichment — 2026-03-23
Uses apollo_id for direct people/match lookups (no credit cost unless reveal=true)
"""
import csv, json, os, sys, time, requests
from datetime import datetime

SANDBOX = "/Users/williammarceaujr./dev-sandbox"
INPUT_CSV  = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo.csv"
OUTPUT_CSV = f"{SANDBOX}/projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo-enriched-2026-03-23.csv"
LOG_FILE   = f"{SANDBOX}/projects/shared/lead-scraper/output/enrich_resume_log_2026-03-23.json"

REVEAL = "--reveal" in sys.argv  # pass --reveal to use email credits

# Load key
API_KEY = None
with open(f"{SANDBOX}/.env") as f:
    for line in f:
        if "APOLLO_API_KEY" in line and not line.strip().startswith("#"):
            API_KEY = line.strip().split("=",1)[1].strip().strip('"').strip("'")
            break

if not API_KEY:
    print("ERROR: APOLLO_API_KEY not found"); sys.exit(1)

HEADERS = {"Content-Type":"application/json","x-api-key":API_KEY}
BASE = "https://api.apollo.io"

last_req = 0
def rate_limit():
    global last_req
    wait = 1.3 - (time.time() - last_req)
    if wait > 0: time.sleep(wait)
    last_req = time.time()

def match_person(row):
    rate_limit()
    payload = {
        "id": row.get("apollo_id","").strip(),
        "reveal_personal_emails": REVEAL
    }
    try:
        r = requests.post(f"{BASE}/api/v1/people/match", json=payload, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            print("  RATE LIMITED — sleeping 60s")
            time.sleep(60)
            r = requests.post(f"{BASE}/api/v1/people/match", json=payload, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json().get("person", {})
        else:
            print(f"  {r.status_code}: {r.text[:200]}")
            return {}
    except Exception as e:
        print(f"  Error: {e}")
        return {}

# Load all rows
with open(INPUT_CSV) as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    all_rows = list(reader)

needs_enrichment = [(i, r) for i, r in enumerate(all_rows) if not (r.get("email","") or "").strip()]
print(f"Loaded {len(all_rows)} total | {len(needs_enrichment)} need enrichment")
print(f"Reveal mode: {'ON (using credits)' if REVEAL else 'OFF (free)'}")
print()

found = 0
attempted = 0
log = []

for idx, (row_i, row) in enumerate(needs_enrichment):
    name = f"{row.get('first_name','')} {row.get('last_name','')}".strip()
    company = row.get("company_name","")
    print(f"[{idx+1}/{len(needs_enrichment)}] {name} @ {company}", end=" ... ")

    person = match_person(row)
    attempted += 1

    email = (person.get("email") or "").strip()

    # Update row with any new data
    if email:
        all_rows[row_i]["email"] = email
        found += 1
        print(f"EMAIL: {email}")
    else:
        # Still grab any other data we can
        if person.get("phone_numbers"):
            phones = person.get("phone_numbers", [])
            if phones:
                all_rows[row_i]["phone"] = phones[0].get("sanitized_number","")
        if person.get("linkedin_url") and not (row.get("linkedin_url","") or "").strip():
            all_rows[row_i]["linkedin_url"] = person.get("linkedin_url","")
        print("no email")

    log.append({
        "name": name,
        "company": company,
        "apollo_id": row.get("apollo_id",""),
        "email_found": email,
        "status": person.get("email_status","")
    })

    # Save every 25 rows
    if (idx + 1) % 25 == 0:
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n--- Checkpoint: saved {idx+1} processed, {found} emails found so far ---\n")

# Final save
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_rows)

with open(LOG_FILE, "w") as f:
    json.dump({"run_at": datetime.now().isoformat(), "reveal": REVEAL, "attempted": attempted, "found": found, "details": log}, f, indent=2)

print(f"\n=== DONE ===")
print(f"Attempted: {attempted} | Emails found: {found} ({found/max(attempted,1)*100:.1f}%)")
print(f"CSV saved: {OUTPUT_CSV}")
print(f"Log saved: {LOG_FILE}")
