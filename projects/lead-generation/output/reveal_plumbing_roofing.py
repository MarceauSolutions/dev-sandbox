#!/usr/bin/env python3
"""
Reveal emails for Plumbing + Roofing Apollo prospects.
Uses reveal_personal_emails=true — spends credits, returns actual emails.
William has 1,872 credits available (628/2500 used).
"""

import json, time, requests, os
from datetime import datetime

API_KEY = "RhRnIKITS2Ye6qSQQO9hUg"
BASE_URL = "https://api.apollo.io/api/v1"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}
OUTPUT = f"/Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/revealed_plumbing_roofing_2026-03-24.json"
MASTER = f"/Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output/master_sendable_2026-03-24.json"

last_req = 0
def rate_limit():
    global last_req
    elapsed = time.time() - last_req
    if elapsed < 1.5:
        time.sleep(1.5 - elapsed)
    last_req = time.time()

def search_segment(keyword, segment_name, page=1):
    rate_limit()
    payload = {
        "person_titles": ["Owner", "President", "Founder", "CEO", "Principal", "General Manager"],
        "person_locations": ["Naples, Florida"],
        "organization_locations": ["Naples, Florida"],
        "q_organization_keyword_tags": [keyword],
        "contact_email_status": ["verified", "guessed"],
        "reveal_personal_emails": True,
        "page": page,
        "per_page": 25
    }
    resp = requests.post(f"{BASE_URL}/mixed_people/search", json=payload, headers=HEADERS, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        people = data.get("people", [])
        print(f"  {segment_name} p{page}: {len(people)} results")
        return people
    else:
        print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
        return []

segments = [
    ("plumbing", "Plumbing"),
    ("roofing", "Roofing"),
]

all_revealed = []
for keyword, name in segments:
    print(f"\n=== {name} ===")
    for page in [1, 2]:
        people = search_segment(keyword, name, page)
        for p in people:
            email = p.get("email", "")
            if not email:
                continue
            org = p.get("organization", {}) or {}
            all_revealed.append({
                "company_name": org.get("name", ""),
                "contact_name": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "title": p.get("title", ""),
                "email": email,
                "phone": p.get("phone_numbers", [{}])[0].get("raw_number", "") if p.get("phone_numbers") else "",
                "website": org.get("website_url", ""),
                "linkedin_url": p.get("linkedin_url", ""),
                "segment": name,
                "source": "apollo_revealed",
                "city": "Naples",
                "state": "FL"
            })
        if len(people) < 25:
            break

# Deduplicate by email
seen = set()
unique = []
for p in all_revealed:
    e = p["email"].lower().strip()
    if e and e not in seen:
        seen.add(e)
        unique.append(p)

print(f"\n=== RESULTS ===")
print(f"Total revealed with email: {len(unique)}")
by_seg = {}
for p in unique:
    by_seg.setdefault(p["segment"], []).append(p)
for seg, items in by_seg.items():
    print(f"  {seg}: {len(items)}")

# Save revealed
with open(OUTPUT, "w") as f:
    json.dump({"generated": str(datetime.now().date()), "total": len(unique), "by_segment": by_seg}, f, indent=2)
print(f"\nSaved revealed contacts: {OUTPUT}")

# Merge into master sendable list
with open(MASTER) as f:
    master = json.load(f)

existing_emails = set()
for seg, items in master.get("by_segment", {}).items():
    for p in items:
        existing_emails.add(p.get("email","").lower())

added = 0
for p in unique:
    e = p["email"].lower()
    if e not in existing_emails:
        seg = p["segment"]
        master["by_segment"].setdefault(seg, []).append(p)
        existing_emails.add(e)
        added += 1

# Recount total
total = sum(len(v) for v in master["by_segment"].values())
master["total"] = total
master["last_updated"] = str(datetime.now().date())

with open(MASTER, "w") as f:
    json.dump(master, f, indent=2)

print(f"Added {added} new contacts to master list")
print(f"Master list total: {total}")
