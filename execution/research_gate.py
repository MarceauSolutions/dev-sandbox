#!/usr/bin/env python3
"""
Research Gate -- Architectural enforcement of research-first execution.

This is NOT a prompt note. It is a callable gate that produces a data snapshot
before any action is taken. Every orchestrator, scheduler, and decision-maker
calls research_gate.gather_context() BEFORE making recommendations.

The gate returns:
  1. Pipeline snapshot (stages, hot leads, recent wins/losses)
  2. Outcome data (what actions actually converted)
  3. Goal progress (are we on/off track)
  4. Outreach stats (what channels are working)

This data replaces William's opinions as the basis for decisions.

Usage (in any orchestrator):
    from execution.research_gate import gather_context, format_for_prompt

    # Before making any recommendation:
    context = gather_context()
    prompt_section = format_for_prompt(context)
    # Include prompt_section in your AI prompt

Usage (CLI):
    python execution/research_gate.py                    # Full context
    python execution/research_gate.py --section pipeline # Just pipeline
    python execution/research_gate.py --section outcomes  # Just outcomes
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research_gate")


def _get_pipeline_db():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gather_context() -> Dict[str, Any]:
    """Gather the full research context from pipeline.db.

    Returns a data snapshot that should inform all decisions.
    Every field uses verified column names from the real schema.
    """
    context = {"gathered_at": datetime.now().isoformat()}

    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()

        # --- Pipeline snapshot ---
        stages = {}
        for row in conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM deals GROUP BY stage ORDER BY cnt DESC"
        ).fetchall():
            stages[dict(row)["stage"]] = dict(row)["cnt"]

        hot_leads = [dict(r) for r in conn.execute(
            "SELECT id, company, contact_name, contact_phone, contact_email, industry, city, stage "
            "FROM deals WHERE stage IN ('Hot Response', 'Qualified', 'Trial Active', 'Proposal Sent') "
            "ORDER BY CASE stage "
            "  WHEN 'Hot Response' THEN 1 "
            "  WHEN 'Trial Active' THEN 2 "
            "  WHEN 'Proposal Sent' THEN 3 "
            "  WHEN 'Qualified' THEN 4 END "
            "LIMIT 10"
        ).fetchall()]

        recent_losses = [dict(r) for r in conn.execute(
            "SELECT company, industry, stage, notes FROM deals "
            "WHERE stage = 'Closed Lost' ORDER BY updated_at DESC LIMIT 5"
        ).fetchall()]

        context["pipeline"] = {
            "stages": stages,
            "total": sum(stages.values()),
            "hot_leads": hot_leads,
            "hot_count": len(hot_leads),
            "recent_losses": recent_losses,
        }

        # --- Outcome data (what actually converted) ---
        outcomes = [dict(r) for r in conn.execute(
            "SELECT deal_id, task_type, company, outcome, resulted_in, scheduled_date "
            "FROM scheduled_outcomes WHERE completed = 1 "
            "ORDER BY created_at DESC LIMIT 20"
        ).fetchall()]

        # What types of activities led to stage changes
        activity_types = {}
        for row in conn.execute(
            "SELECT activity_type, COUNT(*) as cnt FROM activities "
            "GROUP BY activity_type ORDER BY cnt DESC"
        ).fetchall():
            activity_types[dict(row)["activity_type"]] = dict(row)["cnt"]

        context["outcomes"] = {
            "completed_outcomes": outcomes,
            "outcome_count": len(outcomes),
            "activity_types": activity_types,
        }

        # --- Outreach stats (what channels are working) ---
        channel_stats = {}
        for row in conn.execute(
            "SELECT channel, COUNT(*) as sent, "
            "SUM(CASE WHEN response IS NOT NULL AND response != '' THEN 1 ELSE 0 END) as replied "
            "FROM outreach_log GROUP BY channel"
        ).fetchall():
            r = dict(row)
            channel_stats[r["channel"]] = {
                "sent": r["sent"],
                "replied": r["replied"],
                "response_rate": round(r["replied"] / max(1, r["sent"]) * 100, 1),
            }

        recent_7d = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-7 days')"
        ).fetchone()[0]

        context["outreach"] = {
            "by_channel": channel_stats,
            "recent_7d": recent_7d,
        }

        # --- Goal progress ---
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "goal_progress",
                REPO_ROOT / "projects" / "personal-assistant" / "src" / "goal_progress.py"
            )
            gp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gp)
            context["goals"] = gp.calculate_goal_progress()
        except Exception as e:
            context["goals"] = {"_error": str(e)}

        conn.close()

    except Exception as e:
        logger.error(f"Research gate failed: {e}")
        context["_error"] = str(e)

    return context


def format_for_prompt(context: Dict[str, Any] = None) -> str:
    """Format the research context as a prompt section for AI agents.

    Include this in every orchestrator prompt BEFORE the task instruction.
    """
    if context is None:
        context = gather_context()

    lines = ["=== RESEARCH GATE: DATA SNAPSHOT (read before acting) ==="]
    lines.append(f"Gathered: {context.get('gathered_at', 'unknown')}")

    # Pipeline
    pipeline = context.get("pipeline", {})
    stages = pipeline.get("stages", {})
    if stages:
        lines.append(f"\nPIPELINE ({pipeline.get('total', 0)} total):")
        for stage, cnt in stages.items():
            lines.append(f"  {stage}: {cnt}")
        if pipeline.get("hot_leads"):
            lines.append(f"\nHOT LEADS ({pipeline['hot_count']}):")
            for lead in pipeline["hot_leads"][:5]:
                lines.append(f"  - {lead['company']} ({lead.get('industry', '?')}) "
                             f"[{lead['stage']}] {lead.get('city', '')}")

    # Outreach effectiveness
    outreach = context.get("outreach", {})
    channels = outreach.get("by_channel", {})
    if channels:
        lines.append(f"\nOUTREACH EFFECTIVENESS:")
        for ch, stats in channels.items():
            lines.append(f"  {ch}: {stats['sent']} sent, {stats['replied']} replied "
                         f"({stats['response_rate']}% response rate)")
        lines.append(f"  Last 7 days: {outreach.get('recent_7d', 0)} messages")

    # Outcomes
    outcomes = context.get("outcomes", {})
    if outcomes.get("completed_outcomes"):
        lines.append(f"\nOUTCOMES ({outcomes['outcome_count']} tracked):")
        for o in outcomes["completed_outcomes"][:5]:
            lines.append(f"  - {o.get('company', '?')}: {o.get('outcome', '?')} "
                         f"-> {o.get('resulted_in', '?')}")

    # Goal progress
    goals = context.get("goals", {})
    short = goals.get("short_term", {})
    if short:
        lines.append(f"\nGOAL PROGRESS:")
        lines.append(f"  Short-term: {short.get('goal', '?')} "
                     f"[{short.get('overall_pct', 0)}% | {short.get('days_left', '?')}d left]")
        on_track = short.get("on_track", True)
        if not on_track:
            lines.append(f"  !! GOAL IS OFF TRACK - prioritize actions that convert")

    lines.append("")
    lines.append("=== RESEARCH-FIRST RULES ===")
    lines.append("1. Base recommendations on the DATA ABOVE, not opinions")
    lines.append("2. If William suggests X, check if data supports X before executing")
    lines.append("3. Present 2-3 options with tradeoffs")
    lines.append("4. Verify results with real commands before declaring complete")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Research Gate - Data snapshot for decisions")
    parser.add_argument("--section", choices=["pipeline", "outcomes", "outreach", "goals", "all"],
                        default="all", help="Which section to show")
    parser.add_argument("--prompt", action="store_true", help="Output in prompt format")
    args = parser.parse_args()

    context = gather_context()

    if args.prompt:
        print(format_for_prompt(context))
    elif args.section == "all":
        print(json.dumps(context, indent=2, default=str))
    else:
        section = context.get(args.section, {})
        print(json.dumps(section, indent=2, default=str))


if __name__ == "__main__":
    main()
