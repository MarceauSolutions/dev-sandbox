#!/usr/bin/env python3
"""
Evidence Catalog - Index and manage case evidence with metadata.

Usage:
    python src/evidence_catalog.py add             # Add new evidence
    python src/evidence_catalog.py list            # List all evidence
    python src/evidence_catalog.py search          # Search evidence
    python src/evidence_catalog.py count           # Count by type
"""

import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CATALOG_FILE = DATA_DIR / "evidence_catalog.json"


def load_catalog():
    """Load evidence catalog from JSON file."""
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE) as f:
            return json.load(f)
    return {"evidence": [], "last_updated": None}


def save_catalog(data):
    """Save evidence catalog to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(CATALOG_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def compute_file_hash(file_path):
    """Compute SHA-256 hash for integrity verification."""
    path = Path(file_path)
    if path.exists():
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    return None


def add_evidence(args):
    """Add a new evidence entry."""
    data = load_catalog()

    entry = {
        "id": len(data["evidence"]) + 1,
        "date_collected": datetime.now().isoformat(),
        "date_of_evidence": args.date,
        "type": args.type,
        "description": args.desc,
        "source": getattr(args, "source", ""),
        "relevance": getattr(args, "relevance", ""),
        "file_path": getattr(args, "file", ""),
        "file_hash": compute_file_hash(getattr(args, "file", "")) if getattr(args, "file", "") else None,
        "notes": getattr(args, "notes", ""),
    }

    data["evidence"].append(entry)
    save_catalog(data)
    print(f"Evidence #{entry['id']} added: {args.type} - {args.desc[:60]}")


def list_evidence(args):
    """List all evidence entries."""
    data = load_catalog()
    if not data["evidence"]:
        print("No evidence cataloged.")
        return

    print(f"\n{'='*70}")
    print(f"  EVIDENCE CATALOG ({len(data['evidence'])} items)")
    print(f"{'='*70}\n")

    for e in sorted(data["evidence"], key=lambda x: x["date_of_evidence"]):
        print(f"  #{e['id']:03d} [{e['type']:>10}] {e['date_of_evidence']} - {e['description'][:50]}")
        if e.get("file_path"):
            print(f"       File: {e['file_path']}")
        print()


def search_evidence(args):
    """Search evidence by keyword."""
    data = load_catalog()
    keyword = args.keyword.lower()
    matches = [
        e for e in data["evidence"]
        if keyword in e["description"].lower()
        or keyword in e.get("notes", "").lower()
        or keyword in e.get("relevance", "").lower()
    ]

    if not matches:
        print(f"No evidence matching '{args.keyword}'")
        return

    print(f"\nFound {len(matches)} matches for '{args.keyword}':\n")
    for e in matches:
        print(f"  #{e['id']:03d} [{e['type']}] {e['date_of_evidence']} - {e['description'][:60]}")


def count_evidence(args):
    """Count evidence by type."""
    data = load_catalog()
    if not data["evidence"]:
        print("No evidence cataloged.")
        return

    counts = {}
    for e in data["evidence"]:
        counts[e["type"]] = counts.get(e["type"], 0) + 1

    print(f"\nEvidence Summary ({len(data['evidence'])} total):\n")
    for etype, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {etype:>15}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Legal Case Evidence Catalog")
    subparsers = parser.add_subparsers(dest="command")

    # Add
    add_parser = subparsers.add_parser("add", help="Add new evidence")
    add_parser.add_argument("--type", required=True, help="Evidence type: photo, document, screenshot, email, recording, witness, financial, official")
    add_parser.add_argument("--date", required=True, help="Date of evidence (YYYY-MM-DD)")
    add_parser.add_argument("--desc", required=True, help="Description")
    add_parser.add_argument("--source", default="", help="Source of evidence")
    add_parser.add_argument("--relevance", default="", help="Relevance to case")
    add_parser.add_argument("--file", default="", help="Path to evidence file")
    add_parser.add_argument("--notes", default="", help="Additional notes")

    # List
    subparsers.add_parser("list", help="List all evidence")

    # Search
    search_parser = subparsers.add_parser("search", help="Search evidence")
    search_parser.add_argument("--keyword", required=True, help="Search keyword")

    # Count
    subparsers.add_parser("count", help="Count evidence by type")

    args = parser.parse_args()

    commands = {
        "add": add_evidence,
        "list": list_evidence,
        "search": search_evidence,
        "count": count_evidence,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
