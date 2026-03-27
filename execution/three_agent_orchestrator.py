#!/usr/bin/env python3
"""
Three-Agent Orchestrator — Formalizes the Grok → Claude → Ralph handoff protocol.

Agents:
  GROK        — Strategic architect. Sets goals, reviews progress, course-corrects.
  CLAUDE CODE — Local executor. File edits, testing, tower work, launchd-scheduled ops.
  RALPH       — EC2 executor. Long-running tasks, PRD execution, background monitoring.

Flow:
  1. Grok sets goal → grok_orchestrator.py analyzes → generates Claude prompt
  2. Claude Code executes locally (code, tests, tower ops)
  3. If heavy/long-running work needed → hand off to Ralph via handoff file + Telegram
  4. Ralph executes on EC2 → reports back via pipeline.db + Telegram
  5. Orchestrator reads result → analyzes progress → generates next prompt or marks done

Handoff mechanism:
  Mac → EC2: Git push + Telegram message with task description
  EC2 → Mac: pipeline.db sync + Telegram result message
  Shared state: pipeline.db (deals, activities, tower_requests)

Usage:
    python execution/three_agent_orchestrator.py route "Build a content scheduler for fitness tower"
    python execution/three_agent_orchestrator.py handoff --to ralph --task "Run 7-day SMS A/B test"
    python execution/three_agent_orchestrator.py status
"""

import argparse
import json
import logging
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HANDOFF_FILE = REPO_ROOT / "HANDOFF.md"
ORCHESTRATOR_LOG = REPO_ROOT / "docs" / "orchestrator_log.json"

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("3agent")


# ---------------------------------------------------------------------------
# Agent capabilities and routing rules
# ---------------------------------------------------------------------------

AGENTS = {
    "claude_code": {
        "name": "Claude Code",
        "platform": "Mac (VS Code / terminal)",
        "strengths": [
            "File editing and code generation",
            "Tower creation and refactoring",
            "Testing and verification",
            "Architecture enforcement",
            "Interactive development",
        ],
        "constraints": [
            "Session-based (not 24/7)",
            "Can't run long background jobs itself",
            "Launchd handles scheduled execution",
        ],
    },
    "ralph": {
        "name": "Ralph / Clawdbot",
        "platform": "EC2 (Telegram + autonomous)",
        "strengths": [
            "Long-running batch operations",
            "PRD-driven autonomous development",
            "Background monitoring (24/7)",
            "SMS/Telegram bot interface",
            "A/B testing and optimization loops",
            "Social media posting automation",
        ],
        "constraints": [
            "PRD-driven (needs structured task definition)",
            "No interactive file editing",
            "Reports via Telegram, not VS Code",
        ],
    },
    "grok": {
        "name": "Grok",
        "platform": "External advisor (conversation)",
        "strengths": [
            "Strategic direction and goal setting",
            "Architecture decisions",
            "Priority evaluation",
            "Course corrections",
        ],
        "constraints": [
            "Cannot execute code",
            "Advisory only — works through Claude Code",
        ],
    },
}

# Routing rules: task type → best agent
ROUTING_RULES = {
    # Claude Code tasks (local, interactive)
    "code_edit": "claude_code",
    "tower_creation": "claude_code",
    "refactor": "claude_code",
    "test": "claude_code",
    "debug": "claude_code",
    "architecture": "claude_code",
    "digest": "claude_code",
    "scheduler": "claude_code",

    # Ralph tasks (EC2, long-running)
    "batch_process": "ralph",
    "ab_test": "ralph",
    "social_media": "ralph",
    "monitoring_24_7": "ralph",
    "prd_execution": "ralph",
    "sms_campaign": "ralph",
    "data_migration": "ralph",

    # Grok tasks (strategic)
    "strategy": "grok",
    "goal_setting": "grok",
    "priority": "grok",
    "review": "grok",
}


def classify_task(description: str) -> str:
    """Classify a task description to determine the best agent."""
    lower = description.lower()

    # Ralph indicators (long-running, batch, EC2)
    ralph_keywords = ["batch", "a/b test", "24/7", "monitor overnight", "run for",
                      "social media post", "sms campaign", "prd", "background",
                      "deploy to ec2", "ec2", "clawdbot", "telegram bot"]
    if any(kw in lower for kw in ralph_keywords):
        return "ralph"

    # Grok indicators (strategic)
    grok_keywords = ["should we", "strategy", "priority", "architecture decision",
                     "evaluate", "which tower", "goal"]
    if any(kw in lower for kw in grok_keywords):
        return "grok"

    # Default: Claude Code (most tasks are local development)
    return "claude_code"


# ---------------------------------------------------------------------------
# Handoff protocol
# ---------------------------------------------------------------------------

def create_handoff(to_agent: str, task: str, context: Dict = None) -> Dict[str, Any]:
    """Create a handoff to another agent.

    For Ralph: writes to HANDOFF.md and sends Telegram notification.
    For Grok: writes analysis to orchestrator log for review.
    For Claude: generates prompt (use grok_orchestrator.py).
    """
    context = context or {}
    timestamp = datetime.now().isoformat()

    handoff = {
        "to": to_agent,
        "task": task,
        "context": context,
        "created_at": timestamp,
        "status": "pending",
    }

    if to_agent == "ralph":
        # Write to HANDOFF.md for Ralph to pick up
        _write_handoff_file(task, context)
        # Notify via Telegram
        _send_telegram(f"📋 *HANDOFF TO RALPH*\n\nTask: {task}\n\nPick up from HANDOFF.md in dev-sandbox.")
        logger.info(f"Handoff to Ralph: {task}")

    elif to_agent == "grok":
        logger.info(f"Needs Grok decision: {task}")
        print(f"\n⚠️  This task needs Grok's strategic input:")
        print(f"  Task: {task}")
        print(f"  Present this to Grok for a decision.")

    elif to_agent == "claude_code":
        # Generate a Claude prompt using the orchestrator
        from grok_orchestrator import analyze_goal
        analysis = analyze_goal(task)
        print(f"\n→ Claude Code prompt: \"{analysis['claude_prompt']}\"")

    # Log
    _log_handoff(handoff)
    return handoff


def _write_handoff_file(task: str, context: Dict):
    """Write/update HANDOFF.md for inter-agent handoff."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""
## Pending Handoff — {timestamp}

**Task**: {task}

**Context**:
```json
{json.dumps(context, indent=2)}
```

**Status**: Pending — Ralph to pick up

---
"""
    # Append to HANDOFF.md
    existing = HANDOFF_FILE.read_text() if HANDOFF_FILE.exists() else "# Agent Handoffs\n\n"
    with open(HANDOFF_FILE, "w") as f:
        f.write(existing + entry)


def _send_telegram(message: str) -> bool:
    """Send Telegram notification."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        return False
    try:
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def _log_handoff(handoff: Dict):
    """Log handoff to orchestrator log."""
    log = []
    if ORCHESTRATOR_LOG.exists():
        with open(ORCHESTRATOR_LOG) as f:
            log = json.load(f)
    log.append(handoff)
    # Keep last 50 entries
    log = log[-50:]
    ORCHESTRATOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ORCHESTRATOR_LOG, "w") as f:
        json.dump(log, f, indent=2)


# ---------------------------------------------------------------------------
# Status and routing
# ---------------------------------------------------------------------------

def route_task(description: str) -> None:
    """Analyze a task and route to the best agent."""
    agent = classify_task(description)
    agent_info = AGENTS[agent]

    print(f"\n{'='*60}")
    print(f"TASK ROUTING")
    print(f"{'='*60}")
    print(f"\nTask: {description}")
    print(f"Best agent: {agent_info['name']} ({agent_info['platform']})")
    print(f"\nWhy: {', '.join(agent_info['strengths'][:3])}")

    if agent == "ralph":
        print(f"\n→ This is a Ralph task (long-running / EC2).")
        print(f"  To hand off: python execution/three_agent_orchestrator.py handoff --to ralph --task \"{description}\"")
    elif agent == "grok":
        print(f"\n→ This needs Grok's strategic input.")
        print(f"  Present the task to Grok for a decision.")
    else:
        print(f"\n→ This is a Claude Code task (local development).")
        print(f"  Execute directly in VS Code / terminal.")


def show_status() -> None:
    """Show current orchestration status."""
    print(f"\n{'='*60}")
    print(f"3-AGENT ORCHESTRATOR STATUS")
    print(f"{'='*60}")

    for agent_id, info in AGENTS.items():
        print(f"\n{info['name']} ({info['platform']}):")
        print(f"  Strengths: {', '.join(info['strengths'][:3])}")

    # Pending handoffs
    if HANDOFF_FILE.exists():
        content = HANDOFF_FILE.read_text()
        pending = content.count("Status**: Pending")
        print(f"\nPending handoffs: {pending}")

    # Recent log
    if ORCHESTRATOR_LOG.exists():
        with open(ORCHESTRATOR_LOG) as f:
            log = json.load(f)
        if log:
            last = log[-1]
            print(f"Last handoff: {last.get('to', '?')} — {last.get('task', '?')[:60]}")


def main():
    parser = argparse.ArgumentParser(description="Three-Agent Orchestrator")
    sub = parser.add_subparsers(dest="command")

    r = sub.add_parser("route", help="Route a task to the best agent")
    r.add_argument("description", help="Task description")

    h = sub.add_parser("handoff", help="Create a handoff to another agent")
    h.add_argument("--to", required=True, choices=["ralph", "grok", "claude_code"])
    h.add_argument("--task", required=True, help="Task description")

    sub.add_parser("status", help="Show orchestration status")

    args = parser.parse_args()

    if args.command == "route":
        route_task(args.description)
    elif args.command == "handoff":
        create_handoff(args.to, args.task)
    elif args.command == "status":
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
