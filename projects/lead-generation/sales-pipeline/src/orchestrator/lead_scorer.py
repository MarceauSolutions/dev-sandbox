#!/usr/bin/env python3
"""
Lead Scorer — Score and tier all unscored leads in pipeline.db.

Scoring factors (0-100):
  - Industry match to ICP (0-25)
  - Has phone number (+20)
  - Has email (+15)
  - Has website (+10)
  - Employee count sweet spot 2-50 (+10)
  - Location proximity (+5-15)
  - Pain signals in notes/research (+10-20)
  - MEDDIC: decision maker identified (+10)
  - MEDDIC: known pain point (+10)

Tier assignment:
  - T1: 80-100 (hot — call + email + in-person)
  - T2: 50-79  (warm — email + call)
  - T3: <50    (cold — email only)
"""

import re
import sqlite3
from datetime import datetime

from .config import (
    DB_PATH, INDUSTRY_SCORES, LOCATION_SCORES, DEFAULT_FL_SCORE,
    TIER_1_MIN, TIER_2_MIN,
)


# Keywords that indicate pain points or decision-maker context
PAIN_KEYWORDS = [
    "no automation", "missed call", "leads falling", "losing leads",
    "no follow-up", "manual", "slow response", "overwhelmed",
    "fragmented", "scattered", "no crm", "no system",
    "after hours", "no online", "outdated", "struggling",
]

DECISION_MAKER_TITLES = [
    "owner", "ceo", "president", "gm", "general manager",
    "managing partner", "founder", "principal", "director",
]


def score_lead(deal: dict) -> tuple:
    """
    Score a single lead on 0-100 scale.

    Args:
        deal: Dict with deal fields from database

    Returns:
        Tuple of (score, tier, breakdown_dict)
    """
    score = 0
    breakdown = {}

    # 1. Industry match (0-25)
    industry = deal.get("industry") or "Other"
    industry_score = INDUSTRY_SCORES.get(industry, 0)
    score += industry_score
    breakdown["industry"] = industry_score

    # 2. Has phone number (+20)
    phone = deal.get("contact_phone") or ""
    has_phone = bool(phone.strip())
    if has_phone:
        score += 20
    breakdown["has_phone"] = 20 if has_phone else 0

    # 3. Has email (+15)
    email = deal.get("contact_email") or ""
    has_email = bool(email.strip()) and "@" in email
    if has_email:
        score += 15
    breakdown["has_email"] = 15 if has_email else 0

    # 4. Has website (+10)
    website = deal.get("website") or ""
    has_website = bool(website.strip()) and website.strip().lower() not in ("", "none", "n/a")
    if has_website:
        score += 10
    breakdown["has_website"] = 10 if has_website else 0

    # 5. Employee count sweet spot (+10 for 2-50)
    notes = deal.get("notes") or ""
    emp_match = re.search(r"employees?:\s*~?(\d+)", notes.lower())
    emp_score = 0
    if emp_match:
        emp_count = int(emp_match.group(1))
        if 2 <= emp_count <= 50:
            emp_score = 10
        elif 51 <= emp_count <= 100:
            emp_score = 5
    score += emp_score
    breakdown["employee_fit"] = emp_score

    # 6. Location proximity (+5-15)
    city = deal.get("city") or ""
    location_score = LOCATION_SCORES.get(city, 0)
    if not location_score and city:
        state = deal.get("state") or ""
        if state.upper() in ("FL", "FLORIDA"):
            location_score = DEFAULT_FL_SCORE
    score += location_score
    breakdown["location"] = location_score

    # 7. Pain signals in notes/research (+10-20)
    combined_text = f"{notes} {deal.get('pain_points', '') or ''} {deal.get('research_verdict', '') or ''}".lower()
    pain_score = 0
    pain_found = []
    for keyword in PAIN_KEYWORDS:
        if keyword in combined_text:
            pain_found.append(keyword)
    if len(pain_found) >= 3:
        pain_score = 20
    elif len(pain_found) >= 1:
        pain_score = 10
    score += pain_score
    breakdown["pain_signals"] = pain_score

    # 8. MEDDIC: Decision maker identified (+10)
    contact_name = deal.get("contact_name") or ""
    dm_score = 0
    name_lower = contact_name.lower()
    for title in DECISION_MAKER_TITLES:
        if title in name_lower:
            dm_score = 10
            break
    # Also check if contact name is a real person name (not "Unknown" or empty)
    if not dm_score and contact_name and contact_name not in ("Unknown", "the owner", ""):
        # Having a real name is better than nothing
        dm_score = 5
    score += dm_score
    breakdown["decision_maker"] = dm_score

    # Cap at 100
    score = min(score, 100)

    # Tier assignment
    if score >= TIER_1_MIN:
        tier = 1
    elif score >= TIER_2_MIN:
        tier = 2
    else:
        tier = 3

    return score, tier, breakdown


def run_scoring(dry_run: bool = False, rescore_all: bool = False) -> dict:
    """
    Score and tier all unscored leads (or all leads if rescore_all).

    Args:
        dry_run: Preview only, don't update database
        rescore_all: Rescore all leads, not just unscored

    Returns:
        Dict with counts by tier and total scored
    """
    print("\n=== LEAD SCORING ===")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if rescore_all:
        deals = conn.execute("""
            SELECT * FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')
        """).fetchall()
    else:
        # Unscored = lead_score is 0 or NULL, and not already closed
        deals = conn.execute("""
            SELECT * FROM deals
            WHERE (lead_score IS NULL OR lead_score = 0)
            AND stage NOT IN ('Closed Won', 'Closed Lost')
        """).fetchall()

    if not deals:
        print("  No leads to score")
        conn.close()
        return {"total": 0, "t1": 0, "t2": 0, "t3": 0}

    results = {"total": 0, "t1": 0, "t2": 0, "t3": 0}
    updates = []

    for deal in deals:
        d = dict(deal)
        score, tier, breakdown = score_lead(d)

        results["total"] += 1
        if tier == 1:
            results["t1"] += 1
        elif tier == 2:
            results["t2"] += 1
        else:
            results["t3"] += 1

        if dry_run:
            if tier == 1:
                print(f"  [T1] {d['company']}: {score}/100 — {breakdown}")
        else:
            updates.append((score, tier, d["id"]))

    if not dry_run and updates:
        conn.executemany(
            "UPDATE deals SET lead_score = ?, tier = ?, updated_at = datetime('now') WHERE id = ?",
            updates,
        )
        conn.commit()

    conn.close()

    print(f"  Scored {results['total']} leads:")
    print(f"    T1 (hot):  {results['t1']}")
    print(f"    T2 (warm): {results['t2']}")
    print(f"    T3 (cold): {results['t3']}")

    return results


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    rescore = "--rescore-all" in sys.argv
    run_scoring(dry_run=dry, rescore_all=rescore)
