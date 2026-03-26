#!/usr/bin/env python3
"""
Follow-Up Router — Decide what action each lead gets today.

Queries deals where:
  1. next_action_date <= today (follow-ups due)
  2. New prospects that need first touch
  3. Stuck leads needing re-engagement

Routes by tier:
  T1: Call task + email + flag for in-person if Naples
  T2: Email task + call task
  T3: Email only

Generates personalized scripts via pitch_briefer.
"""

import sqlite3
from datetime import datetime, timedelta

from .config import DB_PATH, DEFAULT_FOLLOWUP_DAYS


def get_followups_due(conn: sqlite3.Connection) -> list:
    """Get deals with next_action_date <= today."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT o.id) AS outreach_count,
               MAX(o.created_at) AS last_outreach_date,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END) AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.next_action_date IS NOT NULL
          AND d.next_action_date != ''
          AND d.next_action_date <= ?
          AND d.stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY d.id
        ORDER BY
            CASE WHEN d.tier = 1 THEN 0 WHEN d.tier = 2 THEN 1 ELSE 2 END,
            d.next_action_date ASC
    """, (today,)).fetchall()
    return [dict(r) for r in rows]


def get_new_prospects(conn: sqlite3.Connection) -> list:
    """Get new prospects that haven't been touched yet."""
    rows = conn.execute("""
        SELECT d.*,
               0 AS outreach_count,
               NULL AS last_outreach_date,
               NULL AS last_called,
               NULL AS last_emailed
        FROM deals d
        WHERE d.stage = 'Prospect'
          AND d.id NOT IN (
              SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL
          )
          AND d.lead_score > 0
        ORDER BY d.lead_score DESC, d.tier ASC
        LIMIT 50
    """).fetchall()
    return [dict(r) for r in rows]


def route_lead(deal: dict) -> dict:
    """
    Determine today's actions for a lead based on tier.

    Args:
        deal: Dict with deal fields

    Returns:
        Task dict with actions to take
    """
    tier = deal.get("tier") or 3
    city = (deal.get("city") or "").lower()
    has_phone = bool(deal.get("contact_phone"))
    has_email = bool(deal.get("contact_email")) and "@" in (deal.get("contact_email") or "")
    is_naples = "naples" in city
    stage = deal.get("stage") or "Prospect"
    next_action = deal.get("next_action") or ""

    task = {
        "deal_id": deal["id"],
        "company": deal.get("company", "Unknown"),
        "contact": deal.get("contact_name", ""),
        "phone": deal.get("contact_phone", ""),
        "email": deal.get("contact_email", ""),
        "industry": deal.get("industry", "Other"),
        "tier": tier,
        "stage": stage,
        "score": deal.get("lead_score", 0),
        "actions": [],
        "priority": "normal",
        "next_action": next_action,
        "is_followup": bool(deal.get("next_action_date")),
    }

    if tier == 1:
        # T1: Full-court press
        task["priority"] = "high"
        if has_phone:
            task["actions"].append("call")
        if has_email:
            task["actions"].append("email")
        if is_naples and has_phone:
            task["actions"].append("in_person_flag")
    elif tier == 2:
        # T2: Email + call
        task["priority"] = "medium"
        if has_email:
            task["actions"].append("email")
        if has_phone:
            task["actions"].append("call")
    else:
        # T3: Email only
        task["priority"] = "low"
        if has_email:
            task["actions"].append("email")

    # If no contact methods, flag for manual research
    if not task["actions"]:
        task["actions"].append("needs_contact_info")

    return task


def generate_task_scripts(task: dict, conn: sqlite3.Connection) -> dict:
    """
    Attach pitch scripts to a task using pitch_briefer.

    Args:
        task: Task dict from route_lead
        conn: Database connection

    Returns:
        Task dict enriched with pitch scripts
    """
    try:
        from ..pitch_briefer import get_deal as pb_get_deal, generate_pitch_brief
        deal = pb_get_deal(deal_id=task["deal_id"])
        if deal:
            brief = generate_pitch_brief(deal)
            task["pitch"] = brief.get("pitch", {})
            task["objection_handlers"] = brief.get("objection_handlers", {})
            task["voicemail"] = brief.get("voicemail", "")
            task["do_not_say"] = brief.get("do_not_say", [])
            task["say_instead"] = brief.get("say_instead", {})
        else:
            task["pitch"] = {}
    except Exception as e:
        task["pitch"] = {}
        task["pitch_error"] = str(e)

    return task


def run_routing(dry_run: bool = False, include_scripts: bool = True) -> list:
    """
    Run follow-up routing for today.

    Args:
        dry_run: Preview only
        include_scripts: Generate pitch scripts (slower but needed for call sheet)

    Returns:
        List of task dicts for today
    """
    print("\n=== FOLLOW-UP ROUTING ===")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get follow-ups due
    followups = get_followups_due(conn)
    print(f"  Follow-ups due today: {len(followups)}")

    # Get new prospects needing first touch
    new_prospects = get_new_prospects(conn)
    print(f"  New prospects to touch: {len(new_prospects)}")

    all_tasks = []

    # Route follow-ups (higher priority)
    for deal in followups:
        task = route_lead(deal)
        task["task_type"] = "followup"
        if include_scripts:
            task = generate_task_scripts(task, conn)
        all_tasks.append(task)

    # Route new prospects
    for deal in new_prospects:
        task = route_lead(deal)
        task["task_type"] = "first_touch"
        if include_scripts:
            task = generate_task_scripts(task, conn)
        all_tasks.append(task)

    # Summary
    calls = [t for t in all_tasks if "call" in t["actions"]]
    emails = [t for t in all_tasks if "email" in t["actions"]]
    in_person = [t for t in all_tasks if "in_person_flag" in t["actions"]]

    print(f"\n  Today's tasks:")
    print(f"    Total:     {len(all_tasks)}")
    print(f"    Calls:     {len(calls)}")
    print(f"    Emails:    {len(emails)}")
    print(f"    In-person: {len(in_person)}")
    print(f"    T1: {sum(1 for t in all_tasks if t['tier'] == 1)}")
    print(f"    T2: {sum(1 for t in all_tasks if t['tier'] == 2)}")
    print(f"    T3: {sum(1 for t in all_tasks if t['tier'] == 3)}")

    if dry_run:
        for t in all_tasks[:10]:
            print(f"  [{t['priority'].upper()}] {t['company']} (T{t['tier']}) — {', '.join(t['actions'])}")

    conn.close()
    return all_tasks


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run_routing(dry_run=dry)
