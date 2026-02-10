#!/usr/bin/env python3
"""
Communication Logger - Log all interactions with case parties.

Usage:
    python src/communication_logger.py add          # Log a communication
    python src/communication_logger.py list         # List communications
    python src/communication_logger.py search       # Search communications
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
COMMS_FILE = DATA_DIR / "communications.json"


def load_communications():
    """Load communications from JSON file."""
    if COMMS_FILE.exists():
        with open(COMMS_FILE) as f:
            return json.load(f)
    return {"communications": [], "last_updated": None}


def save_communications(data):
    """Save communications to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(COMMS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def add_communication(args):
    """Add a communication entry."""
    data = load_communications()
    entry = {
        "id": len(data["communications"]) + 1,
        "date": args.date,
        "party": args.party,
        "medium": args.medium,
        "summary": args.summary,
        "direction": getattr(args, "direction", "outgoing"),
        "next_action": getattr(args, "next_action", ""),
        "flag": getattr(args, "flag", "none"),
        "file_path": getattr(args, "file", ""),
        "logged": datetime.now().isoformat(),
    }
    data["communications"].append(entry)
    save_communications(data)
    print(f"Communication #{entry['id']} logged: {args.date} - {args.party} ({args.medium})")


def list_communications(args):
    """List communications, optionally filtered."""
    data = load_communications()
    comms = data["communications"]

    if not comms:
        print("No communications logged.")
        return

    party_filter = getattr(args, "party", None)
    last_n = getattr(args, "last", None)

    if party_filter:
        comms = [c for c in comms if party_filter.lower() in c["party"].lower()]

    comms = sorted(comms, key=lambda x: x["date"], reverse=True)

    if last_n:
        comms = comms[:int(last_n)]

    print(f"\n{'='*70}")
    print(f"  COMMUNICATION LOG ({len(comms)} entries)")
    print(f"{'='*70}\n")

    for c in comms:
        flag_marker = f" [{c['flag'].upper()}]" if c.get("flag", "none") != "none" else ""
        print(f"  #{c['id']:03d} {c['date']} | {c['party']:20s} | {c['medium']:10s}{flag_marker}")
        print(f"       {c['summary'][:65]}")
        if c.get("next_action"):
            print(f"       Next: {c['next_action']}")
        print()


def search_communications(args):
    """Search communications by keyword."""
    data = load_communications()
    keyword = args.keyword.lower()
    matches = [
        c for c in data["communications"]
        if keyword in c["summary"].lower()
        or keyword in c["party"].lower()
        or keyword in c.get("next_action", "").lower()
    ]

    if not matches:
        print(f"No communications matching '{args.keyword}'")
        return

    print(f"\nFound {len(matches)} matches for '{args.keyword}':\n")
    for c in matches:
        print(f"  #{c['id']:03d} {c['date']} | {c['party']} | {c['summary'][:50]}")


def main():
    parser = argparse.ArgumentParser(description="Legal Case Communication Logger")
    subparsers = parser.add_subparsers(dest="command")

    # Add
    add_parser = subparsers.add_parser("add", help="Log a communication")
    add_parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    add_parser.add_argument("--party", required=True, help="Other party name/role")
    add_parser.add_argument("--medium", required=True, help="Medium: email, phone, letter, in-person, text, online, voicemail")
    add_parser.add_argument("--summary", required=True, help="Summary of communication")
    add_parser.add_argument("--direction", default="outgoing", help="Direction: outgoing, incoming")
    add_parser.add_argument("--next-action", default="", help="Next action required")
    add_parser.add_argument("--flag", default="none", help="Flag: none, discrimination, retaliation, threat, admission")
    add_parser.add_argument("--file", default="", help="Path to saved communication file")

    # List
    list_parser = subparsers.add_parser("list", help="List communications")
    list_parser.add_argument("--party", default=None, help="Filter by party name")
    list_parser.add_argument("--last", default=None, help="Show only last N entries")

    # Search
    search_parser = subparsers.add_parser("search", help="Search communications")
    search_parser.add_argument("--keyword", required=True, help="Search keyword")

    args = parser.parse_args()

    commands = {
        "add": add_communication,
        "list": list_communications,
        "search": search_communications,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
