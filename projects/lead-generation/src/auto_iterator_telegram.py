#!/usr/bin/env python3
"""
auto_iterator_telegram.py — Telegram Command Handler for AutoIterator

WHAT: Processes Telegram commands to approve/reject/status AutoIterator experiments.
      Designed to be called by Clawdbot or an n8n webhook when William sends commands.
WHY:  William approves experiments from his phone via Telegram — no VS Code needed.
INPUT: Command string from Telegram (e.g., "approve sms_outreach_20260315_abc123")
OUTPUT: Action result + Telegram reply
COST: FREE

COMMANDS:
  approve <experiment_id>   — Approve and deploy a proposed experiment
  reject <experiment_id>    — Reject a proposed experiment
  status [domain]           — Show optimization status
  report                    — Generate and send weekly report
  propose <domain>          — Propose a new variant for a domain
  cycle <domain>            — Run full evaluate→sync→notify cycle

INTEGRATION:
  Called by n8n webhook or Clawdbot command router.
  Can also be run standalone: python execution/auto_iterator_telegram.py "approve abc123"
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from execution.auto_iterator import AutoIterator, ExperimentStore, EXPERIMENTS_DIR
from execution.auto_iterator_evaluators import get_evaluator, EVALUATORS
from execution.auto_iterator_bridge import (
    sync_winning_variants,
    send_experiment_notification,
    run_cycle,
    get_active_baselines,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5692454753")


def send_reply(text: str) -> bool:
    """Send a reply back to William's Telegram."""
    if not BOT_TOKEN:
        print(f"[NO TELEGRAM] {text}")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": CHAT_ID,
            "text": text[:4096],  # Telegram message limit
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[WARN] Telegram reply failed: {e}")
        return False


def handle_command(command_text: str) -> str:
    """
    Parse and execute an AutoIterator command.

    Returns response text to send back.
    """
    parts = command_text.strip().split()
    if not parts:
        return "Usage: approve|reject|status|report|propose|cycle [args]"

    cmd = parts[0].lower().lstrip("/")
    args = parts[1:]

    try:
        if cmd == "approve":
            return _handle_approve(args)
        elif cmd == "reject":
            return _handle_reject(args)
        elif cmd == "status":
            return _handle_status(args)
        elif cmd == "report":
            return _handle_report()
        elif cmd == "propose":
            return _handle_propose(args)
        elif cmd == "cycle":
            return _handle_cycle(args)
        else:
            return (
                "AutoIterator Commands:\n"
                "  approve <id> — Deploy experiment\n"
                "  reject <id> — Skip experiment\n"
                "  status [domain] — Show status\n"
                "  report — Generate PDF report\n"
                "  propose <domain> — New variant\n"
                "  cycle <domain> — Full eval cycle"
            )
    except Exception as e:
        return f"Error: {e}"


def _find_experiment(experiment_id: str):
    """Find an experiment across all domains."""
    store = ExperimentStore()
    for domain in EVALUATORS:
        exp = store.get_experiment(domain, experiment_id)
        if exp:
            return exp, domain
    # Partial match — search by suffix
    for domain in EVALUATORS:
        experiments = store.load_domain(domain)
        for exp in experiments:
            if exp.experiment_id.endswith(experiment_id) or experiment_id in exp.experiment_id:
                return exp, domain
    return None, None


def _handle_approve(args: list) -> str:
    if not args:
        # List pending experiments
        store = ExperimentStore()
        pending = []
        for domain in EVALUATORS:
            for exp in store.get_by_status(domain, "proposed"):
                pending.append(f"  `{exp.experiment_id}`\n  {exp.variant.hypothesis[:80]}")
        if not pending:
            return "No experiments pending approval."
        return "Pending experiments:\n" + "\n\n".join(pending)

    experiment_id = args[0]
    exp, domain = _find_experiment(experiment_id)

    if not exp:
        return f"Experiment `{experiment_id}` not found."
    if exp.status != "proposed":
        return f"Experiment is `{exp.status}`, not proposed."

    evaluator = get_evaluator(domain)
    iterator = AutoIterator(evaluator)

    # Approve
    iterator.approve(exp.experiment_id)

    # Deploy immediately
    try:
        iterator.deploy(exp.experiment_id)
        return (
            f"Approved + deployed: `{exp.experiment_id}`\n"
            f"Domain: {domain}\n"
            f"Hypothesis: {exp.variant.hypothesis[:100]}\n"
            f"Collecting metrics for {evaluator.metrics_window_hours}h..."
        )
    except Exception as e:
        return f"Approved but deploy failed: {e}"


def _handle_reject(args: list) -> str:
    if not args:
        return "Usage: reject <experiment_id>"

    experiment_id = args[0]
    exp, domain = _find_experiment(experiment_id)

    if not exp:
        return f"Experiment `{experiment_id}` not found."

    store = ExperimentStore()
    exp.status = "evaluated"
    exp.result = "reverted"
    exp.learnings = "Rejected by William via Telegram."
    store.update_experiment(exp)

    return f"Rejected: `{exp.experiment_id}`\nMarked as reverted."


def _handle_status(args: list) -> str:
    store = ExperimentStore()
    domains = args if args else list(EVALUATORS.keys())

    lines = ["AutoIterator Status"]
    for domain in domains:
        stats = store.get_stats(domain)
        if stats["total"] == 0:
            lines.append(f"\n{domain}: No experiments yet")
            continue

        lines.append(f"\n*{domain}*")
        lines.append(f"  Total: {stats['total']} | Kept: {stats['kept']} | Reverted: {stats['reverted']}")

        if stats["proposed"] > 0:
            lines.append(f"  Pending approval: {stats['proposed']}")
        if stats["deployed"] > 0:
            lines.append(f"  Collecting data: {stats['deployed']}")

        learnings = store.get_learnings(domain, limit=2)
        for l in learnings:
            emoji = "+" if l["result"] == "kept" else "-"
            lines.append(f"  [{emoji}] {l['hypothesis'][:60]}")

    return "\n".join(lines)


def _handle_report() -> str:
    try:
        from execution.auto_iterator_report import generate_report
        path = generate_report()
        if path:
            return f"Report generated: {path}\nOpening on Mac..."
        return "No data for report yet."
    except Exception as e:
        return f"Report generation failed: {e}"


def _handle_propose(args: list) -> str:
    if not args:
        return f"Usage: propose <domain>\nAvailable: {', '.join(EVALUATORS.keys())}"

    domain = args[0]
    if domain not in EVALUATORS:
        return f"Unknown domain: {domain}. Available: {', '.join(EVALUATORS.keys())}"

    baselines = get_active_baselines(domain)
    if not baselines:
        return f"No active baselines for {domain}. Need campaign templates first."

    evaluator = get_evaluator(domain)
    iterator = AutoIterator(evaluator)
    exp = iterator.propose(baselines[0])

    # Send approval request
    approval_msg = (
        f"New proposal for *{domain}*:\n\n"
        f"*Hypothesis:* {exp.variant.hypothesis}\n\n"
        f"*Variant:*\n`{exp.variant.variant_text[:300]}`\n\n"
        f"Reply: `approve {exp.experiment_id}` or `reject {exp.experiment_id}`"
    )

    return approval_msg


def _handle_cycle(args: list) -> str:
    if not args:
        return f"Usage: cycle <domain>\nAvailable: {', '.join(EVALUATORS.keys())}"

    domain = args[0]
    if domain not in EVALUATORS:
        return f"Unknown domain: {domain}. Available: {', '.join(EVALUATORS.keys())}"

    result = run_cycle(domain)

    lines = [f"Cycle complete for *{domain}*"]
    lines.append(f"Evaluated: {result['evaluated']} | Synced: {result['synced']}")

    for r in result.get("results", []):
        lines.append(f"  {r['result'].upper()}: {r['hypothesis'][:60]}")

    return "\n".join(lines)


def main():
    """CLI entry point — pass command as argument or read from stdin."""
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = input("Command: ").strip()

    response = handle_command(command)
    print(response)

    # Also send to Telegram
    send_reply(response)


if __name__ == "__main__":
    main()
