#!/usr/bin/env python3
"""
Outcome Learner — Self-improving system that learns from recorded outcomes.

Analyzes what worked and what didn't across industries, channels, and approaches.
Feeds recommendations back into the `next` command and morning digest.

This is the self-annealing component: the system gets smarter with every
outcome William records.

Usage:
    python -m src.outcome_learner insights      # Show what the system has learned
    python -m src.outcome_learner recommend      # Recommend best approach per industry
"""

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import os as _os
REPO_ROOT = Path(_os.environ["REPO_ROOT"]) if _os.environ.get("REPO_ROOT") else Path(__file__).resolve().parent.parent.parent.parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outcome_learner")

# Positive outcomes (led to advancement)
POSITIVE_OUTCOMES = {"conversation", "interested", "meeting_booked", "proposal_sent", "callback", "client_won"}
# Negative outcomes
NEGATIVE_OUTCOMES = {"not_interested", "no_show"}


def _get_pipeline_db():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_insights() -> Dict[str, Any]:
    """Analyze all recorded outcomes and extract actionable insights.

    Returns insights about:
    - Which industries convert best
    - Which channels (call/email/visit) produce best outcomes
    - Which time patterns work
    - Overall conversion funnel
    """
    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()

        # Get all completed outcomes with deal context
        outcomes = conn.execute("""
            SELECT so.outcome, so.resulted_in, so.notes, so.company,
                   d.industry, d.stage, d.city
            FROM scheduled_outcomes so
            LEFT JOIN deals d ON so.deal_id = d.id
            WHERE so.completed = 1
        """).fetchall()

        # Get outreach effectiveness by channel
        channels = conn.execute("""
            SELECT channel,
                   COUNT(*) as sent,
                   SUM(CASE WHEN response IS NOT NULL AND response != '' THEN 1 ELSE 0 END) as replied
            FROM outreach_log
            GROUP BY channel
        """).fetchall()

        conn.close()

        # Analyze outcomes by industry
        industry_outcomes = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
        for row in outcomes:
            d = dict(row)
            industry = (d.get("industry") or "Unknown").strip()
            outcome = d.get("outcome", "")
            industry_outcomes[industry]["total"] += 1
            if outcome in POSITIVE_OUTCOMES:
                industry_outcomes[industry]["positive"] += 1
            elif outcome in NEGATIVE_OUTCOMES:
                industry_outcomes[industry]["negative"] += 1

        # Calculate conversion rates
        industry_rates = {}
        for ind, counts in industry_outcomes.items():
            if counts["total"] > 0:
                industry_rates[ind] = {
                    "positive": counts["positive"],
                    "negative": counts["negative"],
                    "total": counts["total"],
                    "conversion_pct": round(counts["positive"] / counts["total"] * 100, 1),
                }

        # Channel effectiveness
        channel_rates = {}
        for row in channels:
            d = dict(row)
            ch = d["channel"]
            sent = d["sent"]
            replied = d["replied"]
            channel_rates[ch] = {
                "sent": sent,
                "replied": replied,
                "response_rate": round(replied / max(1, sent) * 100, 1),
            }

        # Best approach recommendation
        best_channel = max(channel_rates.items(),
                          key=lambda x: x[1]["response_rate"],
                          default=("Call", {"response_rate": 0}))

        return {
            "total_outcomes": len(outcomes),
            "by_industry": dict(industry_rates),
            "by_channel": channel_rates,
            "best_channel": best_channel[0],
            "best_channel_rate": best_channel[1]["response_rate"],
            "learning_system_ready": len(outcomes) >= 5,
            "outcomes_needed": max(0, 5 - len(outcomes)),
            "insights": _generate_text_insights(industry_rates, channel_rates, len(outcomes)),
        }

    except Exception as e:
        logger.error(f"Outcome learning failed: {e}")
        return {"error": str(e), "total_outcomes": 0}


def _generate_text_insights(industry_rates: dict, channel_rates: dict, total: int) -> List[str]:
    """Generate human-readable insights from the data."""
    insights = []

    if total < 2:
        insights.append(f"Only {total} outcome(s) recorded. Need more data for reliable insights.")
        insights.append("Record outcomes via: result [company]: [outcome]")
        return insights

    # Channel insights
    if channel_rates:
        best = max(channel_rates.items(), key=lambda x: x[1]["response_rate"])
        worst = min(channel_rates.items(), key=lambda x: x[1]["response_rate"])
        if best[1]["response_rate"] > 0:
            insights.append(f"Best channel: {best[0]} ({best[1]['response_rate']}% response rate)")
        if worst[1]["response_rate"] == 0 and worst[1]["sent"] > 10:
            insights.append(f"Stop using: {worst[0]} (0% response rate after {worst[1]['sent']} attempts)")

    # Industry insights
    if industry_rates:
        converting = [(ind, r) for ind, r in industry_rates.items() if r["conversion_pct"] > 50]
        failing = [(ind, r) for ind, r in industry_rates.items() if r["conversion_pct"] == 0 and r["total"] > 1]

        if converting:
            names = [f"{ind} ({r['conversion_pct']}%)" for ind, r in converting]
            insights.append(f"Converting industries: {', '.join(names)}")
        if failing:
            names = [ind for ind, _ in failing]
            insights.append(f"Not converting: {', '.join(names)} — consider different approach or deprioritize")

    return insights


def get_recommendation_for_lead(industry: str) -> str:
    """Get approach recommendation for a specific industry based on historical data."""
    insights = get_insights()

    if insights.get("error") or insights["total_outcomes"] < 2:
        # Not enough data — use channel data instead
        best = insights.get("best_channel", "Call")
        rate = insights.get("best_channel_rate", 0)
        if rate > 50:
            return f"call ({best} at {rate}% response rate)"
        return "call (default — not enough outcome data yet)"

    # Check industry-specific data
    industry_data = insights.get("by_industry", {})
    ind_lower = industry.lower()
    for ind, rates in industry_data.items():
        if ind.lower() in ind_lower or ind_lower in ind.lower():
            if rates["conversion_pct"] > 50:
                return f"call — {ind} converts at {rates['conversion_pct']}%"
            elif rates["conversion_pct"] == 0:
                return f"try different approach — {ind} at 0% conversion"

    # Default to best channel
    return f"call ({insights.get('best_channel', 'Call')} works best at {insights.get('best_channel_rate', 0)}%)"


def format_for_digest() -> str:
    """Format learning insights for the morning digest."""
    insights = get_insights()

    if insights.get("error"):
        return ""

    total = insights["total_outcomes"]
    if total == 0:
        return ""

    lines = []
    if insights["learning_system_ready"]:
        lines.append(f"LEARNING ({total} outcomes):")
    else:
        lines.append(f"LEARNING ({total}/5 outcomes):")

    for insight in insights.get("insights", [])[:3]:
        lines.append(f"  {insight}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Outcome Learner")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("insights", help="Show what the system has learned")
    sub.add_parser("recommend", help="Recommend best approach")
    args = parser.parse_args()

    if args.command == "insights":
        insights = get_insights()
        print(json.dumps(insights, indent=2))
    elif args.command == "recommend":
        insights = get_insights()
        print("LEARNED INSIGHTS:")
        for i in insights.get("insights", []):
            print(f"  {i}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
