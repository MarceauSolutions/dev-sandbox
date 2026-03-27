#!/usr/bin/env python3
"""
Pipeline Health Analytics — Deal velocity, dynamic scoring, stale detection, conversion metrics.

Endpoints (wired into app.py):
    GET /api/health/report  — Full pipeline health report
    GET /api/health/stale   — Stale deals needing attention
    POST /api/health/rescore — Recalculate lead scores based on engagement

Called by n8n Morning-Call-List-Generator to include health metrics in daily briefing.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")

STAGE_ORDER = ["Intake", "Qualified", "Meeting Booked", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]

# Scoring adjustments based on engagement
ENGAGEMENT_SCORES = {
    "Call": 10,
    "Email": 3,
    "SMS": 5,
    "In-Person": 15,
    "Phone Blitz": 2,
}

OUTCOME_SCORES = {
    "interested": 20,
    "callback": 15,
    "meeting_booked": 25,
    "email_requested": 10,
    "voicemail": 2,
    "no_answer": 0,
    "gatekeeper": 1,
    "not_interested": -10,
    "wrong_number": -20,
    "has_ai_already": -15,
}


def get_pipeline_health(conn) -> Dict[str, Any]:
    """Full pipeline health report."""
    total = conn.execute("SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')").fetchone()[0]

    # Stage distribution
    stages = conn.execute("""
        SELECT stage, COUNT(*) as count FROM deals
        WHERE stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY stage ORDER BY count DESC
    """).fetchall()

    # Conversion funnel
    funnel = {}
    for stage in STAGE_ORDER:
        count = conn.execute("SELECT COUNT(*) FROM deals WHERE stage = ?", (stage,)).fetchone()[0]
        funnel[stage] = count

    # Touch distribution
    touch_dist = conn.execute("""
        SELECT touch_count, COUNT(*) as deals FROM (
            SELECT d.id, COUNT(o.id) as touch_count
            FROM deals d LEFT JOIN outreach_log o ON o.deal_id = d.id
            WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
            GROUP BY d.id
        ) GROUP BY touch_count ORDER BY touch_count
    """).fetchall()

    # Channel effectiveness
    channels = conn.execute("""
        SELECT o.channel,
               COUNT(DISTINCT o.deal_id) as deals_touched,
               COUNT(o.id) as total_touches,
               COUNT(DISTINCT CASE WHEN d.stage IN ('Qualified', 'Meeting Booked', 'Proposal Sent', 'Negotiation') THEN d.id END) as advanced
        FROM outreach_log o
        JOIN deals d ON d.id = o.deal_id
        GROUP BY o.channel
    """).fetchall()

    # Phone coverage
    phone_stats = conn.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN contact_phone IS NOT NULL AND contact_phone != '' THEN 1 END) as with_phone
        FROM deals WHERE stage NOT IN ('Closed Won', 'Closed Lost')
    """).fetchone()

    # Deals needing attention (due today or overdue)
    today = datetime.now().strftime("%Y-%m-%d")
    due_today = conn.execute("""
        SELECT COUNT(*) FROM deals
        WHERE next_action_date <= ? AND next_action_date IS NOT NULL AND next_action_date != ''
        AND stage NOT IN ('Closed Won', 'Closed Lost')
    """, (today,)).fetchone()[0]

    # Untouched deals (in pipeline but never contacted)
    untouched = conn.execute("""
        SELECT COUNT(*) FROM deals d
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
        AND d.id NOT IN (SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL)
    """).fetchone()[0]

    return {
        "total_active": total,
        "funnel": funnel,
        "stages": [{"stage": s["stage"], "count": s["count"]} for s in stages],
        "touch_distribution": [{"touches": t["touch_count"], "deals": t["deals"]} for t in touch_dist],
        "channel_effectiveness": [
            {
                "channel": c["channel"],
                "deals_touched": c["deals_touched"],
                "total_touches": c["total_touches"],
                "advanced": c["advanced"],
                "advance_rate": round(c["advanced"] / max(c["deals_touched"], 1) * 100, 1),
            }
            for c in channels
        ],
        "phone_coverage": {
            "total": phone_stats["total"],
            "with_phone": phone_stats["with_phone"],
            "pct": round(phone_stats["with_phone"] / max(phone_stats["total"], 1) * 100, 1),
        },
        "action_items": {
            "due_today": due_today,
            "untouched": untouched,
        },
    }


def get_stale_deals(conn, days_threshold: int = 5) -> List[Dict]:
    """Get deals that haven't been touched in X days."""
    cutoff = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d")

    rows = conn.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
               d.stage, d.lead_score, d.next_action,
               MAX(o.created_at) as last_touch,
               COUNT(o.id) as touch_count,
               CAST(julianday('now') - julianday(MAX(o.created_at)) AS INTEGER) as days_stale
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
        GROUP BY d.id
        HAVING (last_touch IS NULL OR last_touch < ?)
        ORDER BY d.lead_score DESC, days_stale DESC
    """, (cutoff,)).fetchall()

    return [dict(r) for r in rows]


def rescore_leads(conn, dry_run: bool = True) -> Dict[str, Any]:
    """Recalculate lead scores based on engagement history."""
    deals = conn.execute("""
        SELECT d.id, d.company, d.lead_score as old_score, d.stage
        FROM deals d
        WHERE d.stage NOT IN ('Closed Won', 'Closed Lost')
    """).fetchall()

    updated = 0
    rescored = []

    for deal in deals:
        deal_id = deal["id"]
        base_score = deal["old_score"] or 50

        # Get all outreach for this deal
        outreach = conn.execute("""
            SELECT channel, response, created_at FROM outreach_log
            WHERE deal_id = ? ORDER BY created_at
        """, (deal_id,)).fetchall()

        engagement_bonus = 0
        for o in outreach:
            channel = o["channel"] or ""
            response = o["response"] or ""

            # Channel bonus
            engagement_bonus += ENGAGEMENT_SCORES.get(channel, 1)

            # Outcome bonus
            for outcome, score in OUTCOME_SCORES.items():
                if outcome in response.lower():
                    engagement_bonus += score
                    break

        # Stage bonus
        stage_bonus = {
            "Intake": 0,
            "Qualified": 15,
            "Meeting Booked": 25,
            "Proposal Sent": 30,
            "Negotiation": 35,
        }.get(deal["stage"], 0)

        # Recency penalty — if no outreach in 14+ days, lose points
        if outreach:
            last_touch = outreach[-1]["created_at"]
            try:
                days_since = (datetime.now() - datetime.strptime(last_touch[:19], "%Y-%m-%d %H:%M:%S")).days
                if days_since > 14:
                    engagement_bonus -= 10
                elif days_since > 7:
                    engagement_bonus -= 5
            except:
                pass

        new_score = min(max(base_score + engagement_bonus + stage_bonus, 0), 100)

        if new_score != deal["old_score"]:
            rescored.append({
                "deal_id": deal_id,
                "company": deal["company"],
                "old_score": deal["old_score"],
                "new_score": new_score,
                "engagement_bonus": engagement_bonus,
                "stage_bonus": stage_bonus,
            })
            if not dry_run:
                conn.execute("UPDATE deals SET lead_score = ? WHERE id = ?", (new_score, deal_id))
                updated += 1

    if not dry_run:
        conn.commit()

    return {
        "total_deals": len(deals),
        "rescored": len(rescored),
        "updated": updated,
        "dry_run": dry_run,
        "changes": rescored[:20],  # Top 20 changes
    }


def format_health_report(health: Dict, stale: List) -> str:
    """Format health report for Telegram/display."""
    lines = [
        f"📊 PIPELINE HEALTH — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Active deals: {health['total_active']}",
        f"Phone coverage: {health['phone_coverage']['pct']}%",
        f"Due today: {health['action_items']['due_today']}",
        f"Untouched: {health['action_items']['untouched']}",
        "",
        "FUNNEL:",
    ]

    for stage in STAGE_ORDER:
        count = health["funnel"].get(stage, 0)
        if count > 0:
            bar = "█" * min(count // 5, 20)
            lines.append(f"  {stage:18s} {count:4d} {bar}")

    lines.append("")
    lines.append("CHANNEL EFFECTIVENESS:")
    for ch in health["channel_effectiveness"]:
        lines.append(f"  {ch['channel']:15s} {ch['deals_touched']:4d} deals → {ch['advance_rate']}% advanced")

    if stale:
        lines.append("")
        lines.append(f"⚠️ STALE ({len(stale)} deals need attention):")
        for s in stale[:5]:
            days = f"{s['days_stale']}d ago" if s['days_stale'] else "never"
            lines.append(f"  • {s['company'][:30]} | Score: {s['lead_score']} | Last: {days}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"

    if cmd == "report":
        health = get_pipeline_health(conn)
        stale = get_stale_deals(conn)
        print(format_health_report(health, stale))
    elif cmd == "stale":
        stale = get_stale_deals(conn)
        print(f"Stale deals: {len(stale)}")
        for s in stale[:20]:
            print(f"  {s['company'][:35]:35s} | Score: {s['lead_score']:3d} | {s['touch_count']} touches | {s['days_stale'] or 'never'}d")
    elif cmd == "rescore":
        dry = "--for-real" not in sys.argv
        result = rescore_leads(conn, dry_run=dry)
        print(f"{'DRY RUN' if dry else 'UPDATED'}: {result['rescored']} deals rescored")
        for c in result["changes"][:10]:
            print(f"  {c['company'][:30]:30s} {c['old_score']:3d} → {c['new_score']:3d} (eng: {c['engagement_bonus']:+d}, stage: {c['stage_bonus']:+d})")

    conn.close()
