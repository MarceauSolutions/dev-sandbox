#!/usr/bin/env python3
"""
Goal Manager — Set, update, and track short/medium/long-term goals.

The Personal Assistant reads these goals when generating schedules and digests,
ensuring daily actions align with what matters most.

Goals are stored in a simple JSON file, not a database. Easy to read, edit, and
version control.

Usage:
    python -m src.goal_manager show                     # Show all goals
    python -m src.goal_manager set --term short --goal "Land first AI client by April 6"
    python -m src.goal_manager set --term medium --goal "3 paying clients by May 1"
    python -m src.goal_manager set --term long --goal "Replace day job income with AI services"
    python -m src.goal_manager set --term post_april6 --goal "Run business evenings/weekends while at Collier County"
    python -m src.goal_manager clear --term short       # Remove a goal
    python -m src.goal_manager context                  # Show goals formatted for AI context

Goals feed into:
    - daily_scheduler.py (ROI ranking uses goal priorities)
    - unified_morning_digest.py (action items aligned to goals)
    - grok_orchestrator.py (next-action analysis considers goals)
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GOALS_FILE = REPO_ROOT / "projects" / "personal-assistant" / "data" / "goals.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("goal_manager")

DEFAULT_GOALS = {
    "short_term": {
        "goal": "Land first AI client by April 6",
        "deadline": "2026-04-06",
        "metrics": ["1 signed client", "1 discovery call completed", "pipeline producing warm leads"],
        "updated": "2026-03-27",
    },
    "medium_term": {
        "goal": "3 paying AI automation clients by May 15",
        "deadline": "2026-05-15",
        "metrics": ["$1500+ monthly recurring", "referral from first client"],
        "updated": "2026-03-27",
    },
    "long_term": {
        "goal": "Replace day job income with Marceau Solutions AI services",
        "deadline": "2026-12-31",
        "metrics": ["$5000+/mo recurring", "5+ active clients", "system runs autonomously"],
        "updated": "2026-03-27",
    },
    "post_april6": {
        "goal": "Run business evenings and weekends while working at Collier County 7am-3pm",
        "deadline": "ongoing",
        "metrics": ["Morning digest at 6:30am", "System handles outreach during work hours",
                     "Manual work limited to calls, visits, and closing after 3pm"],
        "updated": "2026-03-27",
    },
    "research_phase": {
        "note": "Before acting on a goal, the assistant should research options and tradeoffs "
                "rather than immediately executing based on William's first instinct. "
                "Use data from pipeline.db, outcome tracking, and market signals to recommend "
                "the best path — not just the path William suggests in the moment.",
        "updated": "2026-03-27",
    },
}


def load_goals() -> Dict[str, Any]:
    """Load goals from disk, creating defaults if none exist."""
    if GOALS_FILE.exists():
        with open(GOALS_FILE) as f:
            return json.load(f)
    # Create defaults
    save_goals(DEFAULT_GOALS)
    return DEFAULT_GOALS


def save_goals(goals: Dict[str, Any]):
    """Save goals to disk."""
    GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOALS_FILE, "w") as f:
        json.dump(goals, f, indent=2)


def set_goal(term: str, goal: str, deadline: str = "", metrics: str = ""):
    """Set or update a goal."""
    goals = load_goals()
    goals[term] = {
        "goal": goal,
        "deadline": deadline or goals.get(term, {}).get("deadline", ""),
        "metrics": [m.strip() for m in metrics.split(",")] if metrics else goals.get(term, {}).get("metrics", []),
        "updated": datetime.now().strftime("%Y-%m-%d"),
    }
    save_goals(goals)
    print(f"✓ {term} goal set: {goal}")


def clear_goal(term: str):
    """Clear a goal."""
    goals = load_goals()
    if term in goals:
        del goals[term]
        save_goals(goals)
        print(f"✓ {term} goal cleared")
    else:
        print(f"No {term} goal found")


def show_goals():
    """Display all goals."""
    goals = load_goals()
    print("\n" + "=" * 50)
    print("CURRENT GOALS")
    print("=" * 50)
    for term, data in goals.items():
        if term == "research_phase":
            print(f"\n📚 Research Phase Policy:")
            print(f"   {data.get('note', '')[:100]}")
            continue
        goal = data.get("goal", "Not set")
        deadline = data.get("deadline", "")
        metrics = data.get("metrics", [])
        icons = {"short_term": "🎯", "medium_term": "📈", "long_term": "🏔️", "post_april6": "⏰"}
        icon = icons.get(term, "•")
        print(f"\n{icon} {term.replace('_', ' ').title()}:")
        print(f"   {goal}")
        if deadline:
            print(f"   Deadline: {deadline}")
        if metrics:
            for m in metrics:
                print(f"   ✓ {m}")


def get_goal_context() -> str:
    """Get goals formatted for AI assistant context (used by scheduler and digest)."""
    goals = load_goals()
    lines = ["Current Goals:"]
    for term, data in goals.items():
        if term == "research_phase":
            lines.append(f"  Research Policy: {data.get('note', '')[:150]}")
            continue
        goal = data.get("goal", "")
        deadline = data.get("deadline", "")
        if goal:
            lines.append(f"  {term}: {goal}" + (f" (by {deadline})" if deadline else ""))
    return "\n".join(lines)


def format_for_digest() -> str:
    """Format goals summary for morning digest."""
    goals = load_goals()
    short = goals.get("short_term", {}).get("goal", "")
    if not short:
        return ""
    deadline = goals.get("short_term", {}).get("deadline", "")
    days_left = ""
    if deadline:
        try:
            dl = datetime.strptime(deadline, "%Y-%m-%d")
            days = (dl - datetime.now()).days
            days_left = f" ({days}d left)" if days > 0 else " (OVERDUE)" if days < 0 else " (TODAY)"
        except ValueError:
            pass
    return f"🎯 *GOAL*: {short}{days_left}"


def main():
    parser = argparse.ArgumentParser(description="Goal Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Show all goals")
    sub.add_parser("context", help="Show goals as AI context")

    s = sub.add_parser("set", help="Set a goal")
    s.add_argument("--term", required=True, choices=["short_term", "medium_term", "long_term", "post_april6"])
    s.add_argument("--goal", required=True)
    s.add_argument("--deadline", default="")
    s.add_argument("--metrics", default="", help="Comma-separated metrics")

    c = sub.add_parser("clear", help="Clear a goal")
    c.add_argument("--term", required=True)

    args = parser.parse_args()

    if args.command == "show":
        show_goals()
    elif args.command == "context":
        print(get_goal_context())
    elif args.command == "set":
        set_goal(args.term, args.goal, args.deadline, args.metrics)
    elif args.command == "clear":
        clear_goal(args.term)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
