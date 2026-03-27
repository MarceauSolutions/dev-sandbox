#!/usr/bin/env python3
"""
Fitness-Influencer Tower Handler — Processes cross-tower requests via tower_protocol.

Polls tower_requests table for pending requests addressed to fitness-influencer,
then executes them (e.g., generate coaching content for a won deal).

Called by: launchd (future), or manually, or imported by daily_loop.

Usage:
    python -m src.tower_handler process          # Process pending requests
    python -m src.tower_handler process --dry-run # Preview only
    python -m src.tower_handler pending           # Show pending requests
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness_handler")


def process_pending(dry_run: bool = False) -> Dict[str, Any]:
    """Process all pending tower_requests for fitness-influencer."""
    from tower_protocol import check_pending, claim_request, complete_action, fail_action

    pending = check_pending("fitness-influencer")
    if not pending:
        logger.info("No pending requests for fitness-influencer")
        return {"processed": 0}

    processed = 0
    for req in pending:
        action = req["action"]
        payload = json.loads(req["payload"]) if isinstance(req["payload"], str) else req["payload"]
        req_id = req["id"]

        logger.info(f"Processing request #{req_id}: {action}")

        if dry_run:
            logger.info(f"  [DRY RUN] Would process: {action} with {payload}")
            processed += 1
            continue

        claim_request(req_id)

        if action == "generate_coaching_content":
            result = _generate_coaching_content(payload)
        else:
            result = {"error": f"Unknown action: {action}"}

        if "error" in result:
            fail_action(req_id, result["error"])
        else:
            complete_action(req_id, result)
            processed += 1

    return {"processed": processed, "total_pending": len(pending)}


def _generate_coaching_content(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate coaching onboarding content for a won deal."""
    deal_id = payload.get("deal_id")
    client_name = payload.get("client_name", "Client")

    try:
        # Call build_client_program.py as subprocess (respects its own imports)
        project_root = Path(__file__).parent.parent
        cmd = [
            sys.executable, "-m", "src.build_client_program",
            "--client", client_name,
            "--goal", "general fitness",
            "--days", "4",
            "--experience", "intermediate",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            logger.info(f"Coaching content generated for {client_name}")
            return {
                "deal_id": deal_id,
                "client_name": client_name,
                "status": "generated",
                "output": result.stdout[:500],
            }
        else:
            return {"error": f"build_client_program failed: {result.stderr[:200]}"}

    except subprocess.TimeoutExpired:
        return {"error": "Content generation timed out (60s)"}
    except Exception as e:
        return {"error": str(e)}


def show_pending():
    """Show pending requests for fitness-influencer."""
    from tower_protocol import check_pending
    pending = check_pending("fitness-influencer")
    if not pending:
        print("No pending requests.")
        return
    print(f"\nPending requests ({len(pending)}):")
    for r in pending:
        payload = json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]
        print(f"  #{r['id']}: {r['action']} from {r['from_tower']} — {payload}")


def main():
    parser = argparse.ArgumentParser(description="Fitness-Influencer Tower Handler")
    sub = parser.add_subparsers(dest="command")
    proc = sub.add_parser("process", help="Process pending requests")
    proc.add_argument("--dry-run", action="store_true")
    sub.add_parser("pending", help="Show pending requests")
    args = parser.parse_args()

    if args.command == "process":
        result = process_pending(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.command == "pending":
        show_pending()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
