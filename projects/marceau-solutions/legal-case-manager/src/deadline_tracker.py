#!/usr/bin/env python3
"""
Deadline Tracker - Track and alert on case-related deadlines.

Usage:
    python src/deadline_tracker.py check          # Show upcoming deadlines
    python src/deadline_tracker.py add             # Add a new deadline
    python src/deadline_tracker.py alert           # Show overdue/urgent items
    python src/deadline_tracker.py complete         # Mark deadline as complete
    python src/deadline_tracker.py list             # List all deadlines
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DEADLINES_FILE = DATA_DIR / "deadlines.json"


def load_deadlines():
    """Load deadlines from JSON file."""
    if DEADLINES_FILE.exists():
        with open(DEADLINES_FILE) as f:
            return json.load(f)
    return {"deadlines": []}


def save_deadlines(data):
    """Save deadlines to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEADLINES_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def add_deadline(args):
    """Add a new deadline."""
    data = load_deadlines()
    deadline = {
        "id": len(data["deadlines"]) + 1,
        "name": args.name,
        "date": args.date,
        "category": getattr(args, "category", "filing"),
        "alert_days": [int(d) for d in args.alert_days.split(",")] if args.alert_days else [30, 14, 7, 3, 1],
        "notes": getattr(args, "notes", ""),
        "status": "active",
        "created": datetime.now().isoformat(),
        "completed_date": None,
    }
    data["deadlines"].append(deadline)
    save_deadlines(data)
    print(f"Added deadline: {args.name} (due {args.date})")


def check_deadlines(args):
    """Show upcoming deadlines with urgency levels."""
    data = load_deadlines()
    today = datetime.now().date()

    active = [d for d in data["deadlines"] if d["status"] == "active"]
    if not active:
        print("No active deadlines.")
        return

    active.sort(key=lambda d: d["date"])

    print(f"\n{'='*60}")
    print(f"  DEADLINE CHECK - {today.isoformat()}")
    print(f"{'='*60}\n")

    for d in active:
        due = datetime.strptime(d["date"], "%Y-%m-%d").date()
        days_left = (due - today).days

        if days_left < 0:
            status = f"OVERDUE by {abs(days_left)} days"
            marker = "[!!!]"
        elif days_left <= 7:
            status = f"{days_left} days left"
            marker = "[!!]"
        elif days_left <= 30:
            status = f"{days_left} days left"
            marker = "[!]"
        else:
            status = f"{days_left} days left"
            marker = "[ ]"

        print(f"  {marker} {d['name']}")
        print(f"       Due: {d['date']} ({status})")
        print(f"       Category: {d['category']}")
        if d.get("notes"):
            print(f"       Notes: {d['notes']}")
        print()


def alert_deadlines(args):
    """Show only overdue and urgent deadlines."""
    data = load_deadlines()
    today = datetime.now().date()

    active = [d for d in data["deadlines"] if d["status"] == "active"]
    urgent = []

    for d in active:
        due = datetime.strptime(d["date"], "%Y-%m-%d").date()
        days_left = (due - today).days
        if days_left <= max(d.get("alert_days", [30])):
            urgent.append((d, days_left))

    if not urgent:
        print("No urgent deadlines.")
        return

    urgent.sort(key=lambda x: x[1])
    print(f"\n{'='*60}")
    print(f"  URGENT DEADLINES")
    print(f"{'='*60}\n")

    for d, days_left in urgent:
        if days_left < 0:
            print(f"  [OVERDUE] {d['name']} - was due {d['date']} ({abs(days_left)} days ago)")
        else:
            print(f"  [URGENT]  {d['name']} - due {d['date']} ({days_left} days left)")


def complete_deadline(args):
    """Mark a deadline as complete."""
    data = load_deadlines()
    for d in data["deadlines"]:
        if d["name"].lower() == args.name.lower():
            d["status"] = "completed"
            d["completed_date"] = datetime.now().isoformat()
            if args.notes:
                d["notes"] = (d.get("notes", "") + f" | Completed: {args.notes}").strip(" | ")
            save_deadlines(data)
            print(f"Completed: {d['name']}")
            return
    print(f"Deadline not found: {args.name}")


def list_deadlines(args):
    """List all deadlines."""
    data = load_deadlines()
    if not data["deadlines"]:
        print("No deadlines recorded.")
        return

    for d in data["deadlines"]:
        status_icon = "completed" if d["status"] == "completed" else "active"
        print(f"  [{status_icon}] {d['name']} - {d['date']} ({d['category']})")


def main():
    parser = argparse.ArgumentParser(description="Legal Case Deadline Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # Add
    add_parser = subparsers.add_parser("add", help="Add a new deadline")
    add_parser.add_argument("--name", required=True, help="Deadline name")
    add_parser.add_argument("--date", required=True, help="Due date (YYYY-MM-DD)")
    add_parser.add_argument("--category", default="filing", help="Category: statute, filing, court, administrative, personal")
    add_parser.add_argument("--alert-days", default="30,14,7,3,1", help="Comma-separated alert thresholds in days")
    add_parser.add_argument("--notes", default="", help="Additional notes")

    # Check
    subparsers.add_parser("check", help="Show upcoming deadlines")

    # Alert
    subparsers.add_parser("alert", help="Show urgent deadlines only")

    # Complete
    complete_parser = subparsers.add_parser("complete", help="Mark deadline as complete")
    complete_parser.add_argument("--name", required=True, help="Deadline name to complete")
    complete_parser.add_argument("--notes", default="", help="Completion notes")

    # List
    subparsers.add_parser("list", help="List all deadlines")

    args = parser.parse_args()

    commands = {
        "add": add_deadline,
        "check": check_deadlines,
        "alert": alert_deadlines,
        "complete": complete_deadline,
        "list": list_deadlines,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
