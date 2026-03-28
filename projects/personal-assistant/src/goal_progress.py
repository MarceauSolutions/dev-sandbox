#!/usr/bin/env python3
"""
Goal Progress Tracker -- Auto-calculates goal progress from pipeline.db.

Connects goals.json to real pipeline outcomes so progress is data-driven,
not just a static JSON file William has to mentally track.

Schema verified against real pipeline.db (2026-03-27):
  deals: id, company, stage, monthly_fee, setup_fee, contact_name, ...
  activities: id, deal_id, activity_type, description, created_at, tower
  outreach_log: id, deal_id, company, channel, created_at, ...
  scheduled_outcomes: id, deal_id, task_type, completed, outcome, resulted_in, ...

Usage:
    python -m src.goal_progress show           # Show progress for all goals
    python -m src.goal_progress digest         # Digest-formatted summary
    python -m src.goal_progress check-alerts   # Check if any goal is off-track
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import os as _os
REPO_ROOT = Path(_os.environ["REPO_ROOT"]) if _os.environ.get("REPO_ROOT") else Path(__file__).resolve().parent.parent.parent.parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("goal_progress")


def _get_pipeline_db():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_goals() -> Dict[str, Any]:
    goals_file = REPO_ROOT / "projects" / "personal-assistant" / "data" / "goals.json"
    if goals_file.exists():
        with open(goals_file) as f:
            return json.load(f)
    return {}


def calculate_goal_progress() -> Dict[str, Any]:
    """Calculate progress for all goals based on real pipeline.db data.

    Every SQL query uses verified column names from PRAGMA table_info.
    """
    goals = _load_goals()
    progress = {}

    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()

        # --- Pipeline metrics (all column names verified) ---
        stage_counts = {}
        for row in conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM deals GROUP BY stage"
        ).fetchall():
            stage_counts[dict(row)["stage"]] = dict(row)["cnt"]

        closed_won = stage_counts.get("Closed Won", 0)

        # Discovery calls: activity_type column (not 'type'), description column (not 'notes')
        discovery_calls = conn.execute(
            "SELECT COUNT(*) FROM activities WHERE activity_type IN ('discovery_call', 'call_logged') "
            "AND (description LIKE '%discovery%' OR description LIKE '%calendly%')"
        ).fetchone()[0]

        # Also count meetings booked
        meetings = conn.execute(
            "SELECT COUNT(*) FROM activities WHERE activity_type = 'meeting_booked'"
        ).fetchone()[0]
        discovery_calls = max(discovery_calls, meetings)

        # Active pipeline (exclude terminal stages)
        active_pipeline = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Lost', 'Closed Won', 'Archived', 'Lost')"
        ).fetchone()[0]

        # Warm+ leads: stages that indicate engagement
        warm_plus = sum(stage_counts.get(s, 0) for s in
                        ["Hot Response", "Warm Response", "Qualified",
                         "Scheduling", "Proposal Sent", "Trial Active"])

        # MRR: monthly_fee column (not 'deal_value')
        mrr = 0.0
        for row in conn.execute(
            "SELECT monthly_fee FROM deals WHERE stage = 'Closed Won' AND monthly_fee IS NOT NULL"
        ).fetchall():
            try:
                mrr += float(dict(row)["monthly_fee"])
            except (ValueError, TypeError):
                pass

        # Trial revenue (active trials)
        trial_mrr = 0.0
        for row in conn.execute(
            "SELECT monthly_fee FROM deals WHERE stage = 'Trial Active' AND monthly_fee IS NOT NULL"
        ).fetchall():
            try:
                trial_mrr += float(dict(row)["monthly_fee"])
            except (ValueError, TypeError):
                pass

        # Outreach volume (last 7 days)
        recent_outreach = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days')"
        ).fetchone()[0]

        # Outcomes tracked
        outcomes_total = conn.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes"
        ).fetchone()[0]
        outcomes_completed = conn.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes WHERE completed = 1"
        ).fetchone()[0]

        conn.close()

        # --- Short-term goal progress ---
        short = goals.get("short_term", {})
        if short:
            deadline = short.get("deadline", "2026-04-06")
            try:
                days_left = max(0, (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days)
            except ValueError:
                days_left = 0

            client_pct = min(100, closed_won * 100)
            call_pct = min(100, discovery_calls * 100)
            pipeline_pct = min(100, int(warm_plus / max(1, 3) * 100))

            overall = int((client_pct + call_pct + pipeline_pct) / 3)

            progress["short_term"] = {
                "goal": short.get("goal", ""),
                "deadline": deadline,
                "days_left": days_left,
                "overall_pct": overall,
                "metrics": {
                    "signed_clients": {"current": closed_won, "target": 1, "pct": client_pct},
                    "discovery_calls": {"current": discovery_calls, "target": 1, "pct": call_pct},
                    "warm_pipeline": {"current": warm_plus, "target": 3, "pct": pipeline_pct},
                },
                "on_track": overall >= 33 or days_left > 7,
                "trend": "up" if recent_outreach > 50 else "flat" if recent_outreach > 10 else "down",
            }

        # --- Medium-term goal progress ---
        medium = goals.get("medium_term", {})
        if medium:
            deadline = medium.get("deadline", "2026-05-15")
            try:
                days_left = max(0, (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days)
            except ValueError:
                days_left = 0

            mrr_pct = min(100, int((mrr + trial_mrr) / max(1, 1500) * 100))
            clients_pct = min(100, int(closed_won / max(1, 3) * 100))

            overall = int((mrr_pct + clients_pct) / 2)

            progress["medium_term"] = {
                "goal": medium.get("goal", ""),
                "deadline": deadline,
                "days_left": days_left,
                "overall_pct": overall,
                "metrics": {
                    "mrr": {"current": mrr + trial_mrr, "target": 1500, "pct": mrr_pct},
                    "paying_clients": {"current": closed_won, "target": 3, "pct": clients_pct},
                },
                "on_track": overall >= 10 or days_left > 30,
                "trend": "up" if closed_won > 0 else "flat",
            }

        # --- Long-term goal progress ---
        long_goal = goals.get("long_term", {})
        if long_goal:
            mrr_pct = min(100, int(mrr / max(1, 5000) * 100))
            clients_pct = min(100, int(closed_won / max(1, 5) * 100))
            auto_pct = min(100, int(outcomes_completed / max(1, 20) * 100))

            overall = int((mrr_pct + clients_pct + auto_pct) / 3)

            progress["long_term"] = {
                "goal": long_goal.get("goal", ""),
                "deadline": long_goal.get("deadline", "2026-12-31"),
                "overall_pct": overall,
                "metrics": {
                    "mrr": {"current": mrr, "target": 5000, "pct": mrr_pct},
                    "active_clients": {"current": closed_won, "target": 5, "pct": clients_pct},
                    "automation_maturity": {"current": outcomes_completed, "target": 20, "pct": auto_pct},
                },
                "on_track": True,  # Long-term, measured differently
            }

        # --- Post-April 6 readiness ---
        post = goals.get("post_april6", {})
        if post:
            auto_pct = min(100, int(recent_outreach / max(1, 10) * 100))
            pipe_pct = min(100, int(active_pipeline / max(1, 10) * 100))
            digest_pct = 100  # Morning digest is active (launchd confirmed)

            progress["post_april6"] = {
                "goal": post.get("goal", ""),
                "overall_pct": min(100, int((digest_pct + auto_pct + pipe_pct) / 3)),
                "metrics": {
                    "morning_digest": {"status": "active", "pct": digest_pct},
                    "auto_outreach_7d": {"current": recent_outreach, "target": 10, "pct": auto_pct},
                    "active_pipeline": {"current": active_pipeline, "target": 10, "pct": pipe_pct},
                },
            }

        # --- Summary ---
        progress["_summary"] = {
            "total_deals": sum(stage_counts.values()),
            "stages": stage_counts,
            "active_pipeline": active_pipeline,
            "closed_won": closed_won,
            "mrr": mrr,
            "trial_mrr": trial_mrr,
            "warm_plus_leads": warm_plus,
            "recent_outreach_7d": recent_outreach,
            "outcomes_tracked": outcomes_completed,
            "calculated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Goal progress calculation failed: {e}")
        progress["_error"] = str(e)

    return progress


def format_for_digest(progress: Dict[str, Any] = None) -> str:
    """Format goal progress for the morning Telegram digest.

    Returns a compact, actionable summary with progress bars.
    """
    if progress is None:
        progress = calculate_goal_progress()

    if "_error" in progress:
        return f"Goal progress error: {progress['_error']}"

    lines = []

    short = progress.get("short_term")
    if short:
        trend_icon = {"up": "^", "flat": "-", "down": "v"}.get(short.get("trend", "flat"), "-")
        on_track = short.get("on_track", True)

        lines.append(f"{'G' if on_track else '!! OFF TRACK'} GOAL: {short['goal']}")
        lines.append(f"  {short['overall_pct']}% done | {short['days_left']}d left | Trend: {trend_icon}")

        for name, m in short.get("metrics", {}).items():
            filled = int(5 * m["pct"] / 100)
            bar = "[" + "#" * filled + "." * (5 - filled) + "]"
            lines.append(f"  {bar} {name}: {m['current']}/{m['target']}")

        if not on_track:
            lines.append("  ACTION: Increase outreach volume or pivot strategy NOW")

    summary = progress.get("_summary", {})
    if summary:
        lines.append(f"  Pipeline: {summary.get('active_pipeline', 0)} active | "
                     f"{summary.get('warm_plus_leads', 0)} warm+ | "
                     f"Outreach 7d: {summary.get('recent_outreach_7d', 0)}")

    return "\n".join(lines)


def check_alerts() -> List[str]:
    """Check if any goal is off-track and return alert messages."""
    progress = calculate_goal_progress()
    alerts = []

    if "_error" in progress:
        alerts.append(f"SYSTEM: Goal progress calculation failed: {progress['_error']}")
        return alerts

    short = progress.get("short_term")
    if short and not short.get("on_track"):
        alerts.append(
            f"SHORT-TERM GOAL OFF TRACK: {short['goal']} "
            f"({short['overall_pct']}% with {short['days_left']}d left). "
            f"Action: increase outreach or pivot approach."
        )

    medium = progress.get("medium_term")
    if medium and not medium.get("on_track"):
        alerts.append(
            f"MEDIUM-TERM GOAL OFF TRACK: {medium['goal']} "
            f"({medium['overall_pct']}% with {medium['days_left']}d left)."
        )

    return alerts


def main():
    parser = argparse.ArgumentParser(description="Goal Progress Tracker")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="Show detailed progress")
    sub.add_parser("digest", help="Show digest-formatted summary")
    sub.add_parser("check-alerts", help="Check for off-track goals")
    args = parser.parse_args()

    if args.command == "show":
        progress = calculate_goal_progress()
        print(json.dumps(progress, indent=2, default=str))
    elif args.command == "digest":
        print(format_for_digest())
    elif args.command == "check-alerts":
        alerts = check_alerts()
        if alerts:
            for a in alerts:
                print(f"!! {a}")
        else:
            print("All goals on track.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
