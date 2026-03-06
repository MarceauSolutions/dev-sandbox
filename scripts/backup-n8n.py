#!/usr/bin/env python3
"""
backup-n8n.py — Export ALL n8n workflows to a dated JSON snapshot.

Replaces the old backup-n8n-workflows.sh which had hardcoded stale IDs.
Backs up every workflow, not just a curated list.

Usage:
    python scripts/backup-n8n.py            # Export all workflows
    python scripts/backup-n8n.py --list     # Show what would be backed up

Output:
    projects/shared/n8n-workflows/backups/YYYY-MM-DD.json
    
After running: git add projects/shared/n8n-workflows/backups/ && git commit -m "n8n backup YYYY-MM-DD"
"""

import os
import sys
import json
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

EC2_HOST = os.getenv("EC2_HOST", "34.193.98.97")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")


def fetch_workflows():
    req = urllib.request.Request(
        f"http://{EC2_HOST}:5678/api/v1/workflows?limit=200",
        headers={"X-N8N-API-KEY": N8N_API_KEY}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Backup all n8n workflows")
    parser.add_argument("--list", action="store_true", help="List workflows without saving")
    args = parser.parse_args()

    try:
        data = fetch_workflows()
    except Exception as e:
        print(f"✗ Failed to reach n8n API: {e}", file=sys.stderr)
        sys.exit(1)

    workflows = data.get("data", [])
    active = [w for w in workflows if w.get("active")]
    inactive = [w for w in workflows if not w.get("active")]

    if args.list:
        print(f"n8n workflows: {len(workflows)} total ({len(active)} active, {len(inactive)} inactive)")
        for w in sorted(workflows, key=lambda x: (not x.get("active"), x.get("name", ""))):
            status = "✓" if w.get("active") else "○"
            print(f"  {status} [{w['id']}] {w['name']}")
        return

    backup_dir = ROOT / "projects/shared/n8n-workflows/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = backup_dir / f"{date_str}.json"
    backup_file.write_text(json.dumps(data, indent=2))

    print(f"✓ Backed up {len(workflows)} workflows ({len(active)} active) → backups/{date_str}.json")
    print(f"  Commit: git add projects/shared/n8n-workflows/backups/ && git commit -m 'n8n backup {date_str}'")


if __name__ == "__main__":
    main()
