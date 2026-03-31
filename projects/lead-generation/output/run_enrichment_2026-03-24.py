#!/usr/bin/env python3
"""
Apollo Sequences Activation + Prospect Enrichment
Tasks 1-4 for 2026-03-24 AI client sprint
"""

import json
import time
import requests
import re
from datetime import datetime
from urllib.parse import urlparse

HUNTER_API_KEY = "157c9ef57f69493f1308e6dba1b511f346f51ccc"
APOLLO_API_KEY = "RhRnIKITS2Ye6qSQQO9hUg"

BASE_DIR = "/Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper/output"

SEGMENTS_FILE = f"{BASE_DIR}/prospect_segments_2026-03-23.json"
HUNTER_PREV_FILE = f"{BASE_DIR}/hunter_full_enrichment_2026-03-23.json"
HUNTER_OUTPUT = f"{BASE_DIR}/hunter_enrichment_run2_2026-03-24.json"
APOLLO_OUTPUT = f"{BASE_DIR}/apollo_new_prospects_2026-03-24.json"
MASTER_OUTPUT = f"{BASE_DIR}/master_sendable_2026-03-24.json"
GUIDE_OUTPUT = f"{BASE_DIR}/APOLLO-SEQUENCE-ACTIVATION-GUIDE-2026-03-24.md"


def extract_domain(website):
    """Extract clean domain from website URL."""
    if not website:
        return None
    try:
        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "").strip("/").lower()
        if domain:
            return domain
    except Exception:
        pass
    return None


def load_segments():
    with open(SEGMENTS_FILE, "r") as f:
        return json.load(f)


def load_hunter_prev():
    try:
        with open(HUNTER_PREV_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


# ─────────────────────────────────────────────────────────
# TASK 1: Hunter.io enrichment on missing-email prospects
# ─────────────────────────────────────────────────────────

def task1_hunter_enrichment(segments_data):
    print("\n=== TASK 1: Hunter.io Enrichment ===")

    # Collect already-enriched emails to skip
    prev_enriched_domains = set()
    prev_data = load_hunter_prev()
    for r in prev_data:
        d = extract_domain(r.get("website", ""))
        if d:
            prev_enriched_domains.add(d)

    # Also skip domains that already have email in segments
    already_have_email = set()
    for seg_name, seg_data in segments_data["segments"].items():
        for p in seg_data["prospects"]:
            if p.get("email") and p.get("website"):
                d = extract_domain(p["website"])
                if d:
                    already_have_email.add(d)

    results = []
    processed_domains = set()

    for seg_name, seg_data in segments_data["segments"].items():
        for p in seg_data["prospects"]:
            if p.get("email"):
                continue  # Already has email
            if not p.get("website"):
                continue  # No website to search

            domain = extract_domain(p["website"])
            if not domain:
                continue
            if domain in prev_enriched_domains:
                print(f"  SKIP (prev enriched): {domain}")
                continue
            if domain in processed_domains:
                continue

            processed_domains.add(domain)

            print(f"  Searching Hunter for: {domain} ({p.get('first_name', '')} @ {p.get('company_name', '')})")

            try:
                url = f"https://api.hunter.io/v2/domain-search"
                params = {
                    "domain": domain,
                    "api_key": HUNTER_API_KEY,
                    "limit": 5
                }
                resp = requests.get(url, params=params, timeout=10)

                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    emails = data.get("emails", [])

                    if emails:
                        # Try to find a name match first
                        first_name = p.get("first_name", "").lower().strip()
                        best = None

                        if first_name:
                            for e in emails:
                                efirst = (e.get("first_name") or "").lower().strip()
                                if efirst == first_name and e.get("confidence", 0) >= 50:
                                    if best is None or e.get("confidence", 0) > best.get("confidence", 0):
                                        best = e

                        # Fallback: highest confidence
                        if not best:
                            for e in sorted(emails, key=lambda x: x.get("confidence", 0), reverse=True):
                                if e.get("value") and e.get("confidence", 0) >= 50:
                                    best = e
                                    break

                        if best and best.get("value"):
                            result = {
                                "company": p.get("company_name", ""),
                                "segment": seg_name,
                                "domain": domain,
                                "first_name": p.get("first_name", ""),
                                "last_name": p.get("last_name", ""),
                                "title": p.get("title", ""),
                                "email": best.get("value", ""),
                                "confidence": best.get("confidence", 0),
                                "source": "hunter_domain",
                                "website": p.get("website", ""),
                                "linkedin_url": p.get("linkedin_url", "")
                            }
                            results.append(result)
                            print(f"    FOUND: {result['email']} (confidence: {result['confidence']})")
                        else:
                            print(f"    No qualifying email found (emails present but low confidence or empty)")
                    else:
                        print(f"    No emails found for domain")
                elif resp.status_code == 429:
                    print(f"    RATE LIMITED - waiting 5s...")
                    time.sleep(5)
                elif resp.status_code == 401:
                    print(f"    AUTH ERROR - check Hunter API key")
                    break
                else:
                    print(f"    HTTP {resp.status_code}: {resp.text[:100]}")

            except Exception as e:
                print(f"    ERROR: {e}")

            time.sleep(1.1)  # Rate limit: 1 req/sec

    with open(HUNTER_OUTPUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nTask 1 complete: {len(results)} new emails found via Hunter")
    print(f"Saved to: {HUNTER_OUTPUT}")
    return results


# ─────────────────────────────────────────────────────────
# TASK 2: Apollo API - fetch new prospects for thin segments
# ─────────────────────────────────────────────────────────

APOLLO_SEGMENT_QUERIES = [
    {
        "segment": "Plumbing",
        "keywords": ["plumbing", "plumber"],
        "target": 25
    },
    {
        "segment": "Roofing",
        "keywords": ["roofing", "roofer"],
        "target": 25
    },
    {
        "segment": "Landscaping / Lawn",
        "keywords": ["landscaping", "lawn care", "lawn service"],
        "target": 20
    },
    {
        "segment": "Legal",
        "keywords": ["law firm", "attorney", "legal"],
        "target": 20
    },
    {
        "segment": "Pest Control",
        "keywords": ["pest control", "exterminator"],
        "target": 15
    }
]


def task2_apollo_prospects():
    print("\n=== TASK 2: Apollo New Prospect Search ===")

    all_results = {}
    headers = {
        "x-api-key": APOLLO_API_KEY,
        "Content-Type": "application/json"
    }

    for seg_config in APOLLO_SEGMENT_QUERIES:
        seg_name = seg_config["segment"]
        keywords = seg_config["keywords"]
        target = seg_config["target"]

        print(f"\n  Searching Apollo for: {seg_name} (target: {target} prospects)")

        seg_prospects = []

        for page in range(1, 3):  # Try up to 2 pages
            if len(seg_prospects) >= target:
                break

            # Use first keyword for primary search
            keyword = keywords[0]

            payload = {
                "person_titles": ["Owner", "President", "Founder", "CEO", "Principal", "Managing Partner"],
                "person_locations": ["Naples, Florida"],
                "organization_locations": ["Naples, Florida"],
                "q_organization_keyword_tags": [keyword],
                "contact_email_status": ["verified", "guessed", "likely to engage"],
                "page": page,
                "per_page": 25
            }

            try:
                # Note: /api/v1/mixed_people/api_search is the current endpoint (search only, no credits)
                # Emails come back obfuscated in search; actual reveal requires credit spend
                # Per task instructions: do NOT spend credits. We collect metadata only.
                resp = requests.post(
                    "https://api.apollo.io/api/v1/mixed_people/api_search",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                if resp.status_code == 200:
                    data = resp.json()
                    people = data.get("people", [])
                    total_found = data.get("total_entries", 0)
                    print(f"    Page {page}: {len(people)} prospects returned (total available: {total_found})")

                    for person in people:
                        org = person.get("organization", {}) or {}
                        # Apollo search returns obfuscated emails in free search
                        # email field may be present if already in our contacts, else empty
                        email = person.get("email", "")
                        # last_name may be obfuscated (e.g. "Sm***h") — flag it
                        last_name_raw = person.get("last_name", "") or person.get("last_name_obfuscated", "")
                        is_obfuscated = "***" in (last_name_raw or "")

                        prospect = {
                            "company_name": org.get("name", person.get("organization_name", "")),
                            "contact_name": f"{person.get('first_name', '')} {last_name_raw}".strip(),
                            "first_name": person.get("first_name", ""),
                            "last_name": last_name_raw,
                            "title": person.get("title", ""),
                            "email": email,
                            "has_email_flag": person.get("has_email", False),
                            "email_obfuscated": is_obfuscated,
                            "apollo_id": person.get("id", ""),
                            "phone": "",
                            "website": org.get("website_url", ""),
                            "linkedin_url": person.get("linkedin_url", ""),
                            "employee_count": str(org.get("num_employees", "")),
                            "segment": seg_name,
                            "source": "apollo_search",
                            "city": person.get("city", ""),
                            "state": person.get("state", ""),
                            "note": "Email requires Apollo reveal credit - flagged for manual review" if (person.get("has_email") and not email) else ""
                        }
                        seg_prospects.append(prospect)

                    if len(people) < 25:
                        break  # No more pages

                elif resp.status_code == 422:
                    print(f"    Validation error: {resp.text[:200]}")
                    break
                elif resp.status_code == 429:
                    print(f"    Rate limited - waiting 10s...")
                    time.sleep(10)
                elif resp.status_code == 401:
                    print(f"    Auth error - check Apollo API key")
                    break
                else:
                    print(f"    HTTP {resp.status_code}: {resp.text[:200]}")
                    break

            except Exception as e:
                print(f"    ERROR: {e}")
                break

            time.sleep(1.5)  # Rate limit between pages

        all_results[seg_name] = seg_prospects
        print(f"  {seg_name}: {len(seg_prospects)} prospects found ({len([p for p in seg_prospects if p.get('email')])} with email)")

        time.sleep(1.5)  # Rate limit between segments

    # Save raw Apollo results
    with open(APOLLO_OUTPUT, "w") as f:
        json.dump(all_results, f, indent=2)

    total = sum(len(v) for v in all_results.values())
    total_with_email = sum(len([p for p in v if p.get("email")]) for v in all_results.values())
    print(f"\nTask 2 complete: {total} total prospects ({total_with_email} with email)")
    print(f"Saved to: {APOLLO_OUTPUT}")
    return all_results


# ─────────────────────────────────────────────────────────
# TASK 3: Build master sendable list
# ─────────────────────────────────────────────────────────

def normalize_email(email):
    return email.lower().strip() if email else ""


def task3_master_sendable(segments_data, hunter_run2, apollo_new):
    print("\n=== TASK 3: Building Master Sendable List ===")

    seen_emails = set()
    by_segment = {}

    def add_prospect(p, source_override=None):
        email = normalize_email(p.get("email", ""))
        if not email:
            return False
        if email in seen_emails:
            return False
        seen_emails.add(email)

        seg = p.get("segment", "Other")
        if seg not in by_segment:
            by_segment[seg] = []

        by_segment[seg].append({
            "company_name": p.get("company_name", p.get("company", "")),
            "contact_name": p.get("contact_name", f"{p.get('first_name','')} {p.get('last_name','')}".strip()),
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "title": p.get("title", ""),
            "email": email,
            "segment": seg,
            "website": p.get("website", ""),
            "linkedin_url": p.get("linkedin_url", ""),
            "source": source_override or p.get("source", "apollo")
        })
        return True

    # 1. Existing prospects WITH email from segments file
    count_segments = 0
    for seg_name, seg_data in segments_data["segments"].items():
        for p in seg_data["prospects"]:
            if p.get("email"):
                p_copy = dict(p)
                p_copy["source"] = "apollo"
                if add_prospect(p_copy):
                    count_segments += 1
    print(f"  From segments file (existing with email): {count_segments}")

    # 2. Previous Hunter enrichment (12 records from hunter_full_enrichment_2026-03-23.json)
    prev_hunter = load_hunter_prev()
    count_prev_hunter = 0
    for r in prev_hunter:
        if add_prospect(r, source_override="hunter"):
            count_prev_hunter += 1
    print(f"  From previous Hunter enrichment: {count_prev_hunter}")

    # 3. New Hunter enrichment (Task 1)
    count_new_hunter = 0
    for r in hunter_run2:
        if add_prospect(r, source_override="hunter"):
            count_new_hunter += 1
    print(f"  From new Hunter enrichment (Task 1): {count_new_hunter}")

    # 4. New Apollo prospects from Task 2 with emails
    count_new_apollo = 0
    for seg_name, prospects in apollo_new.items():
        for p in prospects:
            if p.get("email"):
                if add_prospect(p, source_override="apollo_search"):
                    count_new_apollo += 1
    print(f"  From new Apollo search (Task 2): {count_new_apollo}")

    total = sum(len(v) for v in by_segment.values())

    master = {
        "generated": "2026-03-24",
        "total": total,
        "sources": {
            "segments_with_email": count_segments,
            "hunter_prev": count_prev_hunter,
            "hunter_run2": count_new_hunter,
            "apollo_search": count_new_apollo
        },
        "by_segment": by_segment
    }

    with open(MASTER_OUTPUT, "w") as f:
        json.dump(master, f, indent=2)

    print(f"\nTask 3 complete: {total} total sendable prospects (deduplicated by email)")
    print(f"Saved to: {MASTER_OUTPUT}")
    print("\nBreakdown by segment:")
    for seg, prospects in sorted(by_segment.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {seg}: {len(prospects)}")
    return master


# ─────────────────────────────────────────────────────────
# TASK 4: Apollo UI Activation Guide
# ─────────────────────────────────────────────────────────

def task4_activation_guide(master_data):
    print("\n=== TASK 4: Generating Apollo Sequence Activation Guide ===")

    by_segment = master_data.get("by_segment", {})
    total = master_data.get("total", 0)

    # Map our segments to Apollo sequence names
    sequence_mapping = {
        "General AI Services": None,  # Will be built from all segments
        "HVAC / Air Conditioning": by_segment.get("HVAC / Air Conditioning", []),
        "Plumbing": by_segment.get("Plumbing", []),
        "Dental / Medical / Healthcare": by_segment.get("Dental / Medical / Healthcare", []),
        "Roofing": by_segment.get("Roofing", []),
    }

    # Count by each target sequence
    hvac_count = len(sequence_mapping["HVAC / Air Conditioning"])
    plumbing_count = len(sequence_mapping["Plumbing"])
    medspa_count = len(sequence_mapping["Dental / Medical / Healthcare"])
    roofing_count = len(sequence_mapping["Roofing"])

    # Other segments for General sequence
    other_segs = [s for s in by_segment.keys() if s not in [
        "HVAC / Air Conditioning", "Plumbing", "Dental / Medical / Healthcare", "Roofing"
    ]]
    general_count = sum(len(by_segment[s]) for s in other_segs)

    segment_table_rows = []
    for seg, prospects in sorted(by_segment.items(), key=lambda x: len(x[1]), reverse=True):
        segment_table_rows.append(f"| {seg} | {len(prospects)} |")

    segment_table = "\n".join(segment_table_rows)

    guide_content = f"""# Apollo.io Sequence Activation Guide
**Date:** March 24, 2026
**Sprint:** 14-Day AI Client Sprint (Mar 23 – Apr 5)
**Goal:** Activate 5 email sequences covering {total} sendable prospects in Naples FL

---

## Master Prospect Count by Segment

| Segment | Prospects with Email |
|---------|---------------------|
{segment_table}
| **TOTAL** | **{total}** |

---

## Step 1: Log In and Navigate to Sequences

1. Go to [https://app.apollo.io](https://app.apollo.io)
2. Log in with your Marceau Solutions credentials
3. In the left sidebar, click **Engage** → **Sequences**
4. You'll land on the Sequences dashboard

---

## Step 2: Create 5 Sequences

You need to create (or activate if already existing) these 5 sequences:

| Sequence Name | Target Segment | Prospect Count |
|---------------|----------------|----------------|
| General AI Services | All other segments combined | {general_count} |
| HVAC AI Automation | HVAC / Air Conditioning | {hvac_count} |
| Plumbing AI Automation | Plumbing | {plumbing_count} |
| Med Spa & Healthcare AI | Dental / Medical / Healthcare | {medspa_count} |
| Roofing AI Automation | Roofing | {roofing_count} |

**For each sequence:**
1. Click **+ New Sequence** (top right)
2. Name it as shown above
3. Set **Type:** Active
4. Set **Timezone:** Eastern Time (US & Canada)

---

## Step 3: Set Up the 3-Step Email Cadence

For **each** sequence, add 3 email steps:

### Step 1 — Day 0 (Immediate Send)
- Click **+ Add Step** → **Email**
- **Delay:** 0 days (send immediately on enrollment)
- **Subject:** `Quick question about [Company Name]'s lead follow-up`
- **Body:** Use the segment-specific template (see below)

### Step 2 — Day 3
- Click **+ Add Step** → **Email**
- **Delay:** 3 days after Step 1
- **Subject:** `Following up — AI automation for [Company Name]`
- **Body:** Value prop email — focus on time saved, missed calls automated

### Step 3 — Day 7
- Click **+ Add Step** → **Email**
- **Delay:** 7 days after Step 2
- **Subject:** `Last note — free 2-week trial for [Company Name]`
- **Body:** Final CTA with free onboarding offer, link to Calendly

**For each step:**
- Click the step → **Edit**
- Set **From:** William Marceau `<wmarceau@marceausolutions.com>`
- Enable **Personalization:** First name, company name variables `{{first_name}}`, `{{company_name}}`

---

## Step 4: Add Prospects to Each Sequence

The master sendable list is saved at:
```
projects/shared/lead-scraper/output/master_sendable_2026-03-24.json
```

**Method A — Apollo UI (manual, for small batches):**
1. Go to **Search** → **People** in Apollo
2. Filter by segment using company keywords
3. Select contacts → **Add to Sequence** → choose the correct sequence

**Method B — CSV Import (faster, recommended):**
1. From the master list JSON, export each segment to CSV
2. In Apollo: **Sequences** → select sequence → **Add People** → **Import CSV**
3. Map columns: `first_name`, `last_name`, `email`, `company_name`, `title`

**Segment routing:**
- HVAC / Air Conditioning → **HVAC AI Automation** sequence ({hvac_count} contacts)
- Plumbing → **Plumbing AI Automation** sequence ({plumbing_count} contacts)
- Dental / Medical / Healthcare → **Med Spa & Healthcare AI** sequence ({medspa_count} contacts)
- Roofing → **Roofing AI Automation** sequence ({roofing_count} contacts)
- All other segments → **General AI Services** sequence ({general_count} contacts)

---

## Step 5: Connect SendGrid for Email Delivery

1. In Apollo, go to **Settings** (gear icon, bottom left)
2. Click **Integrations** → **Email**
3. Under **Email Provider**, select **SendGrid**
4. Paste your SendGrid API key (find in `.env` as `SENDGRID_API_KEY`)
5. Click **Verify**
6. Under **Sending Domain**, add `marceausolutions.com`
7. Apollo will show you DNS records to add — add them in your domain registrar (usually Cloudflare)
8. Click **Verify Domain** after DNS propagates (can take up to 24hrs)

**From address to use:** `wmarceau@marceausolutions.com`

---

## Step 6: Configure Sending Limits

1. Go to **Settings** → **Email Settings** (or inside each sequence settings)
2. Set the following:
   - **Max emails per day:** 50 (start conservative, increase after 2 weeks if deliverability is good)
   - **Sending window:** 9:00 AM – 5:00 PM EST only
   - **Days to send:** Monday – Friday only
   - **Minimum time between emails:** 2 minutes (prevents spam-like behavior)

---

## Step 7: Activate Sequences

1. Go back to **Engage** → **Sequences**
2. For each sequence: click the sequence name → **Settings** → toggle **Active** to ON
3. Verify the sequence shows a green "Active" badge

---

## Step 8: Monitor Daily

Check Apollo Engage dashboard each morning (or Clawdbot can pull stats):
- **Opens** (target: >40%)
- **Replies** (target: >5%)
- **Bounces** (keep below 2%)

If bounce rate creeps above 2%, pause sending and review the email list.

---

## Quick Reference — Prospect Counts by Sequence

| Apollo Sequence | Segment Source | Ready Contacts |
|-----------------|----------------|----------------|
| General AI Services | Multiple segments | {general_count} |
| HVAC AI Automation | HVAC / Air Conditioning | {hvac_count} |
| Plumbing AI Automation | Plumbing | {plumbing_count} |
| Med Spa & Healthcare AI | Dental / Medical / Healthcare | {medspa_count} |
| Roofing AI Automation | Roofing | {roofing_count} |
| **TOTAL READY TO SEND** | | **{total}** |

---

## Important Notes

- **No cold SMS** — TCPA rules. Email only for first contact.
- **Apollo credits** — Do NOT use Apollo reveal/enrich credits. We already have emails from Hunter + Apollo search.
- **Calendly link for bookings:** `https://calendly.com/wmarceau/ai-services-discovery`
- **Free trial offer:** "Free 2-week AI onboarding" as referenced on the marceausolutions.com AI services page
- **Opt-outs:** Apollo handles unsubscribes automatically. Honor all opt-outs immediately.

---

*Generated by Claude Code on 2026-03-24 for William Marceau's AI client sprint.*
"""

    with open(GUIDE_OUTPUT, "w") as f:
        f.write(guide_content)

    print(f"Task 4 complete: Activation guide written to {GUIDE_OUTPUT}")
    return GUIDE_OUTPUT


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("APOLLO SPRINT: ENRICHMENT + MASTER LIST BUILD")
    print(f"Date: 2026-03-24")
    print("=" * 60)

    # Load base data
    segments_data = load_segments()
    print(f"\nLoaded segments: {list(segments_data['segments'].keys())}")

    # Task 1: Hunter enrichment
    hunter_run2 = task1_hunter_enrichment(segments_data)

    # Task 2: Apollo new prospects
    apollo_new = task2_apollo_prospects()

    # Task 3: Master sendable list
    master = task3_master_sendable(segments_data, hunter_run2, apollo_new)

    # Task 4: Activation guide
    task4_activation_guide(master)

    print("\n" + "=" * 60)
    print("ALL TASKS COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Task 1 - Hunter emails found: {len(hunter_run2)}")

    total_apollo = sum(len(v) for v in apollo_new.values())
    total_apollo_email = sum(len([p for p in v if p.get('email')]) for v in apollo_new.values())
    print(f"  Task 2 - Apollo prospects found: {total_apollo} ({total_apollo_email} with email)")
    print(f"  Task 3 - Master sendable list total: {master['total']}")
    print(f"  Task 4 - Guide: {GUIDE_OUTPUT}")

    print(f"\nMaster list by segment:")
    for seg, prospects in sorted(master['by_segment'].items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {seg}: {len(prospects)}")


if __name__ == "__main__":
    main()
