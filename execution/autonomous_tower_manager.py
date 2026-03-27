#!/usr/bin/env python3
"""
Autonomous Tower Manager — Detects need for new towers/projects and creates them.

Monitors pipeline.db for signals that indicate a new business vertical or capability
is needed, then proposes creation via SMS to William for approval.

Signals detected:
  1. New industry appearing in deals (not covered by existing towers)
  2. Won deal in a new vertical (coaching client vs AI client vs real estate)
  3. Repeated capability requests that no tower handles

Flow:
  detect_signals() → propose_via_sms() → William replies "yes"/"no"
  → on "yes": tower_factory.create_tower() or create_project()

Called by daily_loop.py after Stage 8 (digest), or standalone.

Usage:
    python execution/autonomous_tower_manager.py check          # Check for signals
    python execution/autonomous_tower_manager.py check --dry-run  # Preview only
    python execution/autonomous_tower_manager.py approve --name "real-estate"  # Manual approve
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tower_manager")

# Industries that map to existing towers
KNOWN_VERTICALS = {
    "ai-systems": ["ai", "automation", "chatbot", "voice ai", "missed call", "text-back"],
    "fitness-influencer": ["gym", "fitness", "pt", "personal training", "coaching", "wellness", "yoga", "crossfit"],
    "lead-generation": ["lead", "outreach", "campaign", "sms", "cold email"],
    "personal-assistant": ["calendar", "email", "scheduling", "digest"],
    "amazon-seller": ["amazon", "fba", "ecommerce", "product listing"],
    "mcp-services": ["mcp", "protocol", "api integration"],
}

PROPOSALS_FILE = REPO_ROOT / "projects" / "lead-generation" / "logs" / "tower_proposals.json"
WILLIAM_PHONE = "+12393985676"


def _get_pipeline_db():
    """Import pipeline_db."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_proposals() -> List[Dict]:
    """Load existing proposals from disk."""
    if PROPOSALS_FILE.exists():
        with open(PROPOSALS_FILE) as f:
            return json.load(f)
    return []


def _save_proposals(proposals: List[Dict]):
    """Save proposals to disk."""
    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROPOSALS_FILE, "w") as f:
        json.dump(proposals, f, indent=2)


def _classify_industry(industry: str) -> Optional[str]:
    """Map an industry string to an existing tower, or None if unmatched."""
    lower = industry.lower().strip()
    for tower_name, keywords in KNOWN_VERTICALS.items():
        if any(kw in lower for kw in keywords):
            return tower_name
    return None


def _clean_name(raw: str) -> str:
    """Convert raw industry string to kebab-case name."""
    import re
    clean = re.sub(r'[^a-z0-9\s-]', '', raw.lower().strip())
    clean = re.sub(r'\s+', '-', clean).strip('-')
    return clean[:30]  # Cap at 30 chars


def detect_signals() -> List[Dict[str, Any]]:
    """Scan pipeline.db for signals that a new tower or project is needed.

    Three signal types:
      1. new_vertical: 5+ qualified deals in an industry no tower covers
      2. misrouted: 50+ deals tagged to wrong tower based on industry
      3. capability_gap: High-stage deals with repeated unfulfilled next_action patterns

    Returns list of proposals (max 5 per run to avoid SMS spam).
    """
    signals = []

    try:
        pdb = _get_pipeline_db()
        conn = pdb.get_db()

        # --- Signal 1: New verticals with traction ---
        rows = conn.execute(
            "SELECT industry, COUNT(*) as cnt, "
            "  SUM(CASE WHEN stage IN ('Won','Trial Active') THEN 1 ELSE 0 END) as won "
            "FROM deals "
            "WHERE stage IN ('Qualified','Won','Trial Active','Proposal Sent','Hot Response') "
            "AND industry IS NOT NULL AND industry != '' "
            "GROUP BY industry ORDER BY cnt DESC"
        ).fetchall()

        for row in rows:
            industry = row["industry"]
            count = row["cnt"]
            won = row["won"]
            tower = _classify_industry(industry)

            if tower is None and count >= 5:
                name = _clean_name(industry)
                # More deals or won deals → higher confidence
                confidence = "high" if won >= 1 or count >= 10 else "medium"
                signals.append({
                    "type": "new_vertical",
                    "industry": industry,
                    "deal_count": count,
                    "won_count": won,
                    "confidence": confidence,
                    "suggested_name": name,
                    "suggested_type": "tower" if count >= 15 else "project",
                    "reason": f"{count} qualified+ deals ({won} won) in '{industry}' — no tower covers this",
                })

        # --- Signal 2: Misrouted deals (wrong tower assignment) ---
        misc = conn.execute(
            "SELECT industry, tower, COUNT(*) as cnt FROM deals "
            "WHERE industry IS NOT NULL AND industry != '' "
            "AND stage NOT IN ('Lost', 'Opted Out') "
            "GROUP BY industry, tower HAVING cnt >= 50 "
            "ORDER BY cnt DESC"
        ).fetchall()

        for row in misc:
            industry = row["industry"]
            assigned_tower = row["tower"]
            correct_tower = _classify_industry(industry)

            # Flag if assigned to a tower that doesn't match the industry
            if correct_tower and correct_tower != assigned_tower:
                signals.append({
                    "type": "misrouted",
                    "industry": industry,
                    "deal_count": row["cnt"],
                    "current_tower": assigned_tower,
                    "correct_tower": correct_tower,
                    "confidence": "high",
                    "suggested_name": _clean_name(industry),
                    "suggested_type": "reroute",
                    "reason": f"{row['cnt']} '{industry}' deals in {assigned_tower}, should be in {correct_tower}",
                })
            elif correct_tower is None and row["cnt"] >= 50:
                signals.append({
                    "type": "misrouted",
                    "industry": industry,
                    "deal_count": row["cnt"],
                    "confidence": "medium",
                    "suggested_name": f"{_clean_name(industry)}-services",
                    "suggested_type": "project",
                    "reason": f"{row['cnt']} '{industry}' deals in {assigned_tower} — may need own sub-project",
                })

        # --- Signal 3: Capability gaps (repeated unfulfilled actions) ---
        gaps = conn.execute(
            "SELECT next_action, COUNT(*) as cnt FROM deals "
            "WHERE next_action IS NOT NULL AND next_action != '' "
            "AND stage NOT IN ('Lost', 'Opted Out', 'Won') "
            "GROUP BY next_action HAVING cnt >= 10 "
            "ORDER BY cnt DESC"
        ).fetchall()

        for row in gaps:
            action = row["next_action"]
            # Skip known handled actions
            if action in ("send_calendly", "manual_call", "content_requested",
                          "calendly_sent", "Follow-up email/call"):
                continue
            signals.append({
                "type": "capability_gap",
                "action": action,
                "deal_count": row["cnt"],
                "confidence": "medium",
                "suggested_name": _clean_name(action),
                "suggested_type": "project",
                "reason": f"{row['cnt']} deals stuck at '{action}' — may need automation",
            })

        conn.close()

    except Exception as e:
        logger.warning(f"Signal detection failed: {e}")

    # Cap at 5 proposals per run (avoid SMS spam)
    signals.sort(key=lambda s: (-s.get("deal_count", 0), s.get("confidence", "low")))
    signals = signals[:5]

    # Filter out already-proposed items
    existing = _load_proposals()
    existing_names = {p["suggested_name"] for p in existing}
    signals = [s for s in signals if s["suggested_name"] not in existing_names]

    return signals


def propose_via_sms(signal: Dict[str, Any], dry_run: bool = False) -> bool:
    """Save a tower/project proposal for inclusion in the daily digest.

    Proposals are NO LONGER sent as individual SMS (too spammy).
    Instead they are saved to proposals file and surfaced in:
      1. The 5:30pm pipeline digest
      2. The 6:30am morning digest
      3. The `pending` CLI command

    William approves by replying "yes [name]" to any SMS from the system,
    or by running: python execution/autonomous_tower_manager.py approve --name [name]
    """
    name = signal["suggested_name"]
    reason = signal["reason"]
    sig_type = signal["suggested_type"]

    body = (
        f"🏗️ NEW {sig_type.upper()} PROPOSAL\n\n"
        f"Name: {name}\n"
        f"Reason: {reason}\n\n"
        f"Reply:\n"
        f"yes {name} = Create it\n"
        f"no = Skip"
    )

    if dry_run:
        logger.info(f"[DRY RUN] Would propose: {name} ({sig_type})")
        logger.info(f"  Reason: {reason}")
        return True

    # Save proposal (NO individual SMS — batched into daily digest)
    logger.info(f"Proposal saved: {name} ({sig_type})")

    # Save proposal
    proposals = _load_proposals()
    proposals.append({
        **signal,
        "proposed_at": datetime.now().isoformat(),
        "status": "pending",
    })
    _save_proposals(proposals)

    return True


def format_proposals_for_digest() -> str:
    """Format pending proposals as a line for inclusion in Telegram digests.

    Returns empty string if no pending proposals (no noise).
    """
    proposals = _load_proposals()
    pending = [p for p in proposals if p.get("status") == "pending"]
    if not pending:
        return ""

    lines = [f"🏗️ *TOWER PROPOSALS ({len(pending)})*"]
    for p in pending[:3]:
        name = p["suggested_name"]
        reason = p.get("reason", "")[:60]
        lines.append(f"  • {name}: {reason}")
    if len(pending) > 3:
        lines.append(f"  ... +{len(pending) - 3} more")
    lines.append(f"  _Approve: reply 'yes [name]' to any system SMS_")
    return "\n".join(lines)


def handle_approval(name: str) -> Dict[str, Any]:
    """Handle William's approval — create the tower or project.

    Called by twilio_webhook when William replies "yes [name]".
    """
    from tower_factory import create_tower, create_project

    proposals = _load_proposals()
    proposal = None
    for p in proposals:
        if p["suggested_name"] == name and p["status"] == "pending":
            proposal = p
            break

    if not proposal:
        return {"success": False, "error": f"No pending proposal for '{name}'"}

    if proposal["suggested_type"] == "tower":
        result = create_tower(
            name=name,
            domain=f"{proposal.get('industry', name)} operations",
            capabilities=[proposal.get("reason", "")],
        )
    else:
        # Create as sub-project in lead-generation (default home for new verticals)
        result = create_project(
            tower="lead-generation",
            project_name=name,
            description=proposal.get("reason", ""),
        )

    if result.get("success"):
        proposal["status"] = "approved"
        proposal["approved_at"] = datetime.now().isoformat()
        _save_proposals(proposals)
        logger.info(f"Tower/project '{name}' created successfully")
    else:
        proposal["status"] = "failed"
        proposal["error"] = result.get("error", "")
        _save_proposals(proposals)

    return result


def check_and_propose(dry_run: bool = False) -> Dict[str, Any]:
    """Main entry point: detect signals and propose new towers/projects."""
    signals = detect_signals()

    if not signals:
        logger.info("No new tower/project signals detected")
        return {"signals": 0, "proposed": 0}

    proposed = 0
    for signal in signals:
        if propose_via_sms(signal, dry_run=dry_run):
            proposed += 1

    return {"signals": len(signals), "proposed": proposed}


def main():
    parser = argparse.ArgumentParser(description="Autonomous Tower Manager")
    sub = parser.add_subparsers(dest="command")

    chk = sub.add_parser("check", help="Check for new tower/project signals")
    chk.add_argument("--dry-run", action="store_true")

    app = sub.add_parser("approve", help="Manually approve a pending proposal")
    app.add_argument("--name", required=True, help="Proposal name to approve")

    sub.add_parser("pending", help="Show pending proposals")

    args = parser.parse_args()

    if args.command == "check":
        result = check_and_propose(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.command == "approve":
        result = handle_approval(args.name)
        print(json.dumps(result, indent=2))
    elif args.command == "pending":
        proposals = _load_proposals()
        pending = [p for p in proposals if p.get("status") == "pending"]
        if pending:
            for p in pending:
                print(f"  {p['suggested_name']} ({p['suggested_type']}): {p['reason'][:80]}")
        else:
            print("  No pending proposals")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
