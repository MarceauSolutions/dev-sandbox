#!/usr/bin/env python3
"""
Timeline Builder - Construct chronological case narrative.

Usage:
    python src/timeline_builder.py add             # Add timeline event
    python src/timeline_builder.py list            # List all events
    python src/timeline_builder.py generate        # Generate timeline document
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TIMELINE_FILE = DATA_DIR / "timeline.json"


def load_timeline():
    """Load timeline from JSON file."""
    if TIMELINE_FILE.exists():
        with open(TIMELINE_FILE) as f:
            return json.load(f)
    return {"events": [], "last_updated": None}


def save_timeline(data):
    """Save timeline to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(TIMELINE_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def add_event(args):
    """Add a timeline event."""
    data = load_timeline()
    event = {
        "id": len(data["events"]) + 1,
        "date": args.date,
        "event": args.event,
        "category": getattr(args, "category", "general"),
        "evidence_ids": [],
        "communication_ids": [],
        "significance": getattr(args, "significance", "normal"),
        "added": datetime.now().isoformat(),
    }
    data["events"].append(event)
    save_timeline(data)
    print(f"Event added: {args.date} - {args.event[:60]}")


def list_events(args):
    """List all timeline events chronologically."""
    data = load_timeline()
    if not data["events"]:
        print("No timeline events recorded.")
        return

    events = sorted(data["events"], key=lambda x: x["date"])
    print(f"\n{'='*70}")
    print(f"  CASE TIMELINE ({len(events)} events)")
    print(f"{'='*70}\n")

    for e in events:
        sig = " ***" if e.get("significance") == "critical" else ""
        print(f"  {e['date']}  {e['event']}{sig}")
        print()


def generate_timeline(args):
    """Generate formatted timeline document."""
    data = load_timeline()
    if not data["events"]:
        print("No timeline events to generate.")
        return

    events = sorted(data["events"], key=lambda x: x["date"])
    fmt = getattr(args, "format", "markdown")
    output_path = getattr(args, "output", None)

    lines = []
    lines.append("# Case Timeline")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    lines.append(f"Total events: {len(events)}\n")
    lines.append("---\n")

    current_month = None
    for e in events:
        month = e["date"][:7]
        if month != current_month:
            current_month = month
            dt = datetime.strptime(month, "%Y-%m")
            lines.append(f"\n## {dt.strftime('%B %Y')}\n")

        sig_marker = " **[CRITICAL]**" if e.get("significance") == "critical" else ""
        lines.append(f"- **{e['date']}**: {e['event']}{sig_marker}")

    lines.append("\n---\n")
    lines.append("*This timeline is a factual chronology of events related to the case.*")

    content = "\n".join(lines)

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            f.write(content)
        print(f"Timeline written to: {output}")
    else:
        print(content)


def main():
    parser = argparse.ArgumentParser(description="Legal Case Timeline Builder")
    subparsers = parser.add_subparsers(dest="command")

    # Add
    add_parser = subparsers.add_parser("add", help="Add timeline event")
    add_parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    add_parser.add_argument("--event", required=True, help="Event description")
    add_parser.add_argument("--category", default="general", help="Category: general, discrimination, filing, communication, legal")
    add_parser.add_argument("--significance", default="normal", help="Significance: normal, important, critical")

    # List
    subparsers.add_parser("list", help="List all events")

    # Generate
    gen_parser = subparsers.add_parser("generate", help="Generate timeline document")
    gen_parser.add_argument("--format", default="markdown", help="Output format: markdown")
    gen_parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args()

    commands = {
        "add": add_event,
        "list": list_events,
        "generate": generate_timeline,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
