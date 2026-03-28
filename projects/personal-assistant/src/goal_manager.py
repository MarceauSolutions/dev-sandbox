#!/usr/bin/env python3
"""
Goal Manager -- Dynamic goal management with vision protection.

Goals are the compass for all tower operations. This module handles:
  1. CRUD for short/medium/long-term goals
  2. SMS/Telegram quick-set with deadline auto-parsing
  3. Vision protection (long-term Company on a Laptop vision is sacred)
  4. Progress integration (reads from goal_progress.py)
  5. Research-first context injection for all AI decision-making

Usage:
    python -m src.goal_manager show                      # Show all goals with progress
    python -m src.goal_manager set --term short --goal "Land first AI client by April 6"
    python -m src.goal_manager set --term medium --goal "3 paying clients by May 15"
    python -m src.goal_manager quick "goal short: Get 2 clients by April 20"
    python -m src.goal_manager context                   # AI context with research directive
    python -m src.goal_manager progress                  # Live progress from pipeline.db

SMS/Telegram quick-set format:
    "goal short: Land 2 clients by April 15"
    "goal medium: $3000/mo recurring by June"
    "goal long: Full-time Marceau Solutions by 2027"
    "goal progress" -> show live progress
    "goal alerts" -> check off-track warnings
"""

import argparse
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import os as _os
REPO_ROOT = Path(_os.environ["REPO_ROOT"]) if _os.environ.get("REPO_ROOT") else Path(__file__).resolve().parent.parent.parent.parent
GOALS_FILE = REPO_ROOT / "projects" / "personal-assistant" / "data" / "goals.json"
GOAL_HISTORY_FILE = REPO_ROOT / "projects" / "personal-assistant" / "data" / "goal_history.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("goal_manager")

# The long-term vision is protected. Short-term goals can change freely,
# but the long-term "Company on a Laptop" vision requires explicit override.
PROTECTED_VISION = "Replace day job income with Marceau Solutions"


def _import_goal_progress():
    """Import goal_progress.py robustly (works both as package and standalone)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "goal_progress", Path(__file__).parent / "goal_progress.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

DEFAULT_GOALS = {
    "short_term": {
        "goal": "Land first AI client by April 6",
        "deadline": "2026-04-06",
        "metrics": ["1 signed client", "1 discovery call completed", "pipeline producing warm leads"],
        "updated": "2026-03-27",
    },
    "medium_term": {
        "goal": "$5000/mo recurring by July",
        "deadline": "2026-05-15",
        "metrics": ["$1500+ monthly recurring", "referral from first client"],
        "updated": "2026-03-27",
    },
    "long_term": {
        "goal": "Replace day job income with Marceau Solutions AI services",
        "deadline": "2026-12-31",
        "metrics": ["$5000+/mo recurring", "5+ active clients", "system runs autonomously"],
        "updated": "2026-03-27",
        "protected": True,
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
                "the best path -- not just the path William suggests in the moment.",
        "updated": "2026-03-27",
    },
}


def load_goals() -> Dict[str, Any]:
    """Load goals from disk, creating defaults if none exist."""
    if GOALS_FILE.exists():
        with open(GOALS_FILE) as f:
            return json.load(f)
    save_goals(DEFAULT_GOALS)
    return DEFAULT_GOALS


def save_goals(goals: Dict[str, Any]):
    """Save goals to disk."""
    GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOALS_FILE, "w") as f:
        json.dump(goals, f, indent=2)


def _log_goal_change(term: str, old_goal: str, new_goal: str):
    """Log goal changes so we can see how priorities evolved."""
    history = []
    if GOAL_HISTORY_FILE.exists():
        try:
            with open(GOAL_HISTORY_FILE) as f:
                history = json.load(f)
        except (json.JSONDecodeError, ValueError):
            history = []

    history.append({
        "term": term,
        "old": old_goal,
        "new": new_goal,
        "changed_at": datetime.now().isoformat(),
    })

    # Keep last 50 changes
    history = history[-50:]
    GOAL_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOAL_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def _parse_deadline(text: str) -> Optional[str]:
    """Extract a deadline from natural language.

    Handles: "by April 6", "by 2026-04-15", "by June", "by end of May"
    Returns ISO date string or None.
    """
    # ISO format: 2026-04-15
    iso = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if iso:
        return iso.group(1)

    # "by Month Day" or "by Month"
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    pattern = r'by\s+(?:end\s+of\s+)?(\w+)(?:\s+(\d{1,2}))?'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        month_str = match.group(1).lower()
        day_str = match.group(2)

        if month_str in months:
            month = months[month_str]
            day = int(day_str) if day_str else 28  # End of month default
            year = datetime.now().year
            # If the month is in the past, assume next year
            if month < datetime.now().month or (month == datetime.now().month and day < datetime.now().day):
                year += 1
            try:
                return datetime(year, month, min(day, 28)).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def set_goal(term: str, goal: str, deadline: str = "", metrics: str = ""):
    """Set or update a goal with vision protection."""
    goals = load_goals()

    # Vision protection: warn if trying to change protected long-term goal
    if term == "long_term" and goals.get("long_term", {}).get("protected"):
        old_goal = goals.get("long_term", {}).get("goal", "")
        if old_goal and PROTECTED_VISION.lower() not in goal.lower():
            logger.warning(
                f"Long-term vision is protected. Current: '{old_goal}'. "
                f"New goal '{goal}' doesn't reference the core vision. "
                f"Set protected=false in goals.json to override."
            )
            return f"BLOCKED: Long-term vision is protected. Include '{PROTECTED_VISION}' or explicitly remove protection."

    # Log the change
    old_goal = goals.get(term, {}).get("goal", "")
    if old_goal and old_goal != goal:
        _log_goal_change(term, old_goal, goal)

    # Auto-parse deadline from goal text if not provided
    if not deadline:
        parsed = _parse_deadline(goal)
        if parsed:
            deadline = parsed

    goals[term] = {
        "goal": goal,
        "deadline": deadline or goals.get(term, {}).get("deadline", ""),
        "metrics": [m.strip() for m in metrics.split(",")] if metrics else goals.get(term, {}).get("metrics", []),
        "updated": datetime.now().strftime("%Y-%m-%d"),
    }

    # Preserve protection flag on long-term
    if term == "long_term":
        goals[term]["protected"] = True

    save_goals(goals)
    msg = f"Goal {term} updated: {goal}"
    if deadline:
        msg += f" (deadline: {deadline})"
    logger.info(msg)
    return msg


def clear_goal(term: str):
    """Clear a goal (long-term is protected)."""
    goals = load_goals()
    if term == "long_term" and goals.get("long_term", {}).get("protected"):
        return "BLOCKED: Long-term vision is protected. Cannot clear."
    if term in goals:
        _log_goal_change(term, goals[term].get("goal", ""), "(cleared)")
        del goals[term]
        save_goals(goals)
        return f"Goal {term} cleared"
    return f"No {term} goal found"


def show_goals():
    """Display all goals with live progress."""
    goals = load_goals()

    # Get live progress
    try:
        gp = _import_goal_progress()
        progress = gp.calculate_goal_progress()
    except Exception:
        progress = {}

    print("\n" + "=" * 60)
    print("CURRENT GOALS")
    print("=" * 60)

    for term, data in goals.items():
        if term == "research_phase":
            print(f"\nRESEARCH POLICY: {data.get('note', '')[:80]}...")
            continue

        goal = data.get("goal", "Not set")
        deadline = data.get("deadline", "")
        metrics = data.get("metrics", [])
        protected = data.get("protected", False)

        icons = {"short_term": "ST", "medium_term": "MT", "long_term": "LT", "post_april6": "PA6"}
        icon = icons.get(term, "--")
        print(f"\n[{icon}] {term.replace('_', ' ').title()}{'  [PROTECTED]' if protected else ''}:")
        print(f"   {goal}")

        if deadline and deadline != "ongoing":
            try:
                dl = datetime.strptime(deadline, "%Y-%m-%d")
                days = (dl - datetime.now()).days
                status = f"{days}d left" if days > 0 else "OVERDUE" if days < 0 else "TODAY"
                print(f"   Deadline: {deadline} ({status})")
            except ValueError:
                print(f"   Deadline: {deadline}")
        elif deadline == "ongoing":
            print(f"   Deadline: ongoing")

        # Show live progress if available
        prog = progress.get(term, {})
        if prog.get("overall_pct") is not None:
            pct = prog["overall_pct"]
            filled = int(10 * pct / 100)
            bar = "[" + "#" * filled + "." * (10 - filled) + f"] {pct}%"
            print(f"   Progress: {bar}")

        if metrics:
            for m in metrics:
                print(f"   - {m}")


def get_goal_context() -> str:
    """Get goals + research directive formatted for AI context injection.

    This is the single function all orchestrators should call to get
    goal awareness and research-first enforcement in their prompts.
    """
    goals = load_goals()
    lines = ["=== CURRENT GOALS ==="]
    for term, data in goals.items():
        if term == "research_phase":
            continue
        goal = data.get("goal", "")
        deadline = data.get("deadline", "")
        if goal:
            days = ""
            if deadline and deadline != "ongoing":
                try:
                    d = (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days
                    days = f" [{d}d left]" if d > 0 else " [OVERDUE]" if d < 0 else " [TODAY]"
                except ValueError:
                    pass
            lines.append(f"  {term}: {goal}{days}")

    # Append research directive
    lines.append("")
    lines.append(get_research_directive())

    return "\n".join(lines)


def get_research_directive() -> str:
    """Return the research-first execution directive for AI agents.

    This is not a suggestion. It is an architectural gate. Every orchestrator,
    scheduler, and decision-making module MUST include this in its prompt.
    """
    return (
        "=== RESEARCH-FIRST GATE (MANDATORY) ===\n"
        "Before recommending or executing ANY action:\n"
        "  1. READ pipeline.db -- what is the current state? What is working?\n"
        "  2. READ outcome tracking -- which actions actually converted?\n"
        "  3. If William suggests an approach, VALIDATE it against data first\n"
        "  4. Present 2-3 options with tradeoffs, then recommend the best one\n"
        "  5. NEVER execute William's first instinct without data validation\n"
        "  6. NEVER declare 'complete' without running verification commands\n"
        "Violating this gate = trust violation. Data over opinions."
    )


def quick_set(text: str) -> str:
    """Parse a natural language goal update from SMS/Telegram.

    Handles:
        "goal short: Land 2 clients by April 15"
        "goal medium: $3000/mo recurring by June"
        "goal long: Full-time Marceau Solutions by 2027"
        "goal progress" -> returns live progress digest
        "goal alerts" -> returns off-track warnings
        "goal show" -> returns current goals summary

    Returns response string suitable for SMS/Telegram reply.
    """
    lower = text.lower().strip()

    # Read-only commands
    if lower in ("goal progress", "goals progress", "goal status"):
        try:
            gp = _import_goal_progress()
            return gp.format_for_digest() or "No goal progress data available."
        except Exception as e:
            return f"Progress check failed: {e}"

    if lower in ("goal alerts", "goals alerts"):
        try:
            gp = _import_goal_progress()
            alerts = gp.check_alerts()
            return "\n".join(alerts) if alerts else "All goals on track."
        except Exception as e:
            return f"Alert check failed: {e}"

    if lower in ("goal show", "goals", "goal list", "goals show"):
        goals = load_goals()
        lines = []
        for term, data in goals.items():
            if term == "research_phase":
                continue
            goal = data.get("goal", "")
            deadline = data.get("deadline", "")
            if goal:
                dl_str = ""
                if deadline and deadline != "ongoing":
                    try:
                        days = (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days
                        dl_str = f" [{days}d]" if days > 0 else " [OVERDUE]"
                    except ValueError:
                        pass
                lines.append(f"{term}: {goal}{dl_str}")
        return "\n".join(lines) if lines else "No goals set."

    # Set commands
    term_map = {
        "short": "short_term",
        "medium": "medium_term",
        "long": "long_term",
        "post": "post_april6",
    }

    for prefix, term in term_map.items():
        if lower.startswith(f"goal {prefix}:") or lower.startswith(f"goal {prefix} :"):
            goal_text = text.split(":", 1)[1].strip()
            result = set_goal(term, goal_text)
            return result

    return (
        "Goal commands:\n"
        "  goal short: [text] -- set short-term\n"
        "  goal medium: [text] -- set medium-term\n"
        "  goal long: [text] -- set long-term\n"
        "  goal progress -- live progress\n"
        "  goal alerts -- off-track check\n"
        "  goal show -- list all"
    )


def format_for_digest() -> str:
    """Format goals summary for morning digest (with countdown)."""
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
    return f"GOAL: {short}{days_left}"


def main():
    parser = argparse.ArgumentParser(description="Goal Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Show all goals with progress")
    sub.add_parser("context", help="Show goals as AI context with research directive")
    sub.add_parser("progress", help="Show live pipeline progress")

    s = sub.add_parser("set", help="Set a goal")
    s.add_argument("--term", required=True, choices=["short_term", "medium_term", "long_term", "post_april6"])
    s.add_argument("--goal", required=True)
    s.add_argument("--deadline", default="")
    s.add_argument("--metrics", default="", help="Comma-separated metrics")

    c = sub.add_parser("clear", help="Clear a goal")
    c.add_argument("--term", required=True)

    q = sub.add_parser("quick", help="Quick-set via natural language")
    q.add_argument("text", help="e.g. 'goal short: Land 2 clients by April 20'")

    args = parser.parse_args()

    if args.command == "show":
        show_goals()
    elif args.command == "context":
        print(get_goal_context())
    elif args.command == "progress":
        try:
            gp = _import_goal_progress()
            print(gp.format_for_digest())
        except Exception as e:
            print(f"Progress failed: {e}")
    elif args.command == "set":
        print(set_goal(args.term, args.goal, args.deadline, args.metrics))
    elif args.command == "clear":
        print(clear_goal(args.term))
    elif args.command == "quick":
        print(quick_set(args.text))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
