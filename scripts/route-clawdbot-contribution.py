#!/usr/bin/env python3
"""
Route Clawdbot contributions to appropriate project folders.

Usage:
    python route-clawdbot-contribution.py route <request-id> <project-path>
    python route-clawdbot-contribution.py approve <request-id> <project-path>
    python route-clawdbot-contribution.py reject <request-id> <project-path>
    python route-clawdbot-contribution.py list [project-path]

Examples:
    python route-clawdbot-contribution.py route req-001 marceau-solutions/swflorida-hvac
    python route-clawdbot-contribution.py approve req-001 marceau-solutions/swflorida-hvac
    python route-clawdbot-contribution.py list
"""

import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

DEV_SANDBOX = Path("/Users/williammarceaujr./dev-sandbox")
INBOX = DEV_SANDBOX / ".tmp" / "clawdbot-inbox"
PROJECTS = DEV_SANDBOX / "projects"


def route_contribution(request_id: str, project_path: str) -> bool:
    """Move Clawdbot contribution from inbox to project's pending folder."""
    source = INBOX / request_id
    dest = PROJECTS / project_path / "clawdbot-contributions" / "PENDING" / request_id

    if not source.exists():
        print(f"Error: Source not found: {source}")
        print(f"Run sync-clawdbot-outputs.sh first to pull from VPS")
        return False

    if dest.exists():
        print(f"Warning: Destination already exists: {dest}")
        response = input("Overwrite? [y/N]: ")
        if response.lower() != 'y':
            return False
        shutil.rmtree(dest)

    # Create destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)

    # Create/update manifest
    manifest_path = dest / "MANIFEST.json"
    manifest = {
        "request_id": request_id,
        "source_channel": "clawdbot",
        "routed_at": datetime.now().isoformat(),
        "project": project_path,
        "status": "pending_review",
        "files": [f.name for f in dest.iterdir() if f.is_file() and f.name != "MANIFEST.json"]
    }

    # Merge with existing manifest if present
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text())
            manifest = {**existing, **manifest}
        except json.JSONDecodeError:
            pass

    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"Routed: {request_id} -> {project_path}/clawdbot-contributions/PENDING/")
    print(f"Files: {', '.join(manifest['files'])}")
    return True


def approve_contribution(request_id: str, project_path: str) -> bool:
    """Move contribution from PENDING to APPROVED."""
    pending = PROJECTS / project_path / "clawdbot-contributions" / "PENDING" / request_id
    approved = PROJECTS / project_path / "clawdbot-contributions" / "APPROVED" / request_id

    if not pending.exists():
        print(f"Error: Not found in PENDING: {pending}")
        return False

    # Update manifest
    manifest_path = pending / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["status"] = "approved"
        manifest["approved_at"] = datetime.now().isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2))

    # Move
    approved.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pending), str(approved))

    print(f"Approved: {request_id}")
    print(f"Location: {approved}")
    return True


def reject_contribution(request_id: str, project_path: str, reason: str = None) -> bool:
    """Move contribution from PENDING to REJECTED."""
    pending = PROJECTS / project_path / "clawdbot-contributions" / "PENDING" / request_id
    rejected = PROJECTS / project_path / "clawdbot-contributions" / "REJECTED" / request_id

    if not pending.exists():
        print(f"Error: Not found in PENDING: {pending}")
        return False

    # Update manifest
    manifest_path = pending / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["status"] = "rejected"
        manifest["rejected_at"] = datetime.now().isoformat()
        if reason:
            manifest["rejection_reason"] = reason
        manifest_path.write_text(json.dumps(manifest, indent=2))

    # Move
    rejected.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pending), str(rejected))

    print(f"Rejected: {request_id}")
    return True


def list_contributions(project_path: str = None):
    """List all Clawdbot contributions."""
    print("\n=== Clawdbot Contributions ===\n")

    # List inbox
    print("📥 INBOX (unrouted):")
    if INBOX.exists():
        for item in sorted(INBOX.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                files = [f.name for f in item.iterdir() if f.is_file()]
                print(f"   {item.name}: {len(files)} files")
    else:
        print("   (empty)")

    print()

    # List project contributions
    if project_path:
        projects_to_check = [PROJECTS / project_path]
    else:
        # Find all projects with clawdbot-contributions
        projects_to_check = list(PROJECTS.glob("*/*/clawdbot-contributions")) + \
                           list(PROJECTS.glob("*/clawdbot-contributions"))

    for contrib_dir in projects_to_check:
        if not contrib_dir.exists():
            contrib_dir = contrib_dir / "clawdbot-contributions"
            if not contrib_dir.exists():
                continue

        project_name = str(contrib_dir.parent).replace(str(PROJECTS) + "/", "")
        print(f"📁 {project_name}:")

        for status in ["PENDING", "APPROVED", "REJECTED"]:
            status_dir = contrib_dir / status
            if status_dir.exists():
                items = list(status_dir.iterdir())
                if items:
                    emoji = {"PENDING": "⏳", "APPROVED": "✅", "REJECTED": "❌"}[status]
                    print(f"   {emoji} {status}:")
                    for item in sorted(items):
                        if item.is_dir():
                            manifest_path = item / "MANIFEST.json"
                            if manifest_path.exists():
                                manifest = json.loads(manifest_path.read_text())
                                files = manifest.get("files", [])
                                print(f"      {item.name}: {len(files)} files")
                            else:
                                print(f"      {item.name}")

        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "route":
        if len(sys.argv) < 4:
            print("Usage: route <request-id> <project-path>")
            sys.exit(1)
        route_contribution(sys.argv[2], sys.argv[3])

    elif command == "approve":
        if len(sys.argv) < 4:
            print("Usage: approve <request-id> <project-path>")
            sys.exit(1)
        approve_contribution(sys.argv[2], sys.argv[3])

    elif command == "reject":
        if len(sys.argv) < 4:
            print("Usage: reject <request-id> <project-path> [reason]")
            sys.exit(1)
        reason = sys.argv[4] if len(sys.argv) > 4 else None
        reject_contribution(sys.argv[2], sys.argv[3], reason)

    elif command == "list":
        project_path = sys.argv[2] if len(sys.argv) > 2 else None
        list_contributions(project_path)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
