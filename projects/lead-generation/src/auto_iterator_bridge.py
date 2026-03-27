#!/usr/bin/env python3
"""
auto_iterator_bridge.py — Connects AutoIterator to live outreach systems

WHAT: Bridge between the autonomous optimization engine and the outreach optimizer.
      Handles variant injection, template syncing, and notification dispatch.
WHY:  The AutoIterator proposes variants; this bridge deploys them into the real
      outreach system and notifies William of results via Telegram/SMS.
INPUT: Experiment data from AutoIterator, campaign data from outreach system
OUTPUT: Deployed templates, Telegram notifications, PDF reports
COST: FREE (data routing) + Telegram/SMS notification costs (~$0 / $0.008 per SMS)

QUICK USAGE:
  # Sync winning variants into outreach optimizer
  python execution/auto_iterator_bridge.py sync

  # Send experiment results notification
  python execution/auto_iterator_bridge.py notify --domain sms_outreach

  # Full cycle: check pending experiments, evaluate, sync, notify
  python execution/auto_iterator_bridge.py cycle --domain sms_outreach
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from execution.auto_iterator import AutoIterator, ExperimentStore, STRATEGIES_DIR
from execution.auto_iterator_evaluators import get_evaluator, EVALUATORS

# Lead scraper paths
LEAD_SCRAPER_DIR = ROOT / "projects" / "shared" / "lead-scraper"
OUTREACH_OUTPUT = LEAD_SCRAPER_DIR / "output"
TEMPLATES_DIR = LEAD_SCRAPER_DIR / "templates"
STAGED_TEMPLATES_FILE = OUTREACH_OUTPUT / "auto_iterator_staged_templates.json"


def sync_winning_variants(domain: str = "sms_outreach") -> list[dict]:
    """
    Sync winning AutoIterator variants into the outreach optimizer's template pool.

    When a variant is 'kept', this:
    1. Reads the variant text from experiment store
    2. Creates a template file in lead-scraper/templates/ (if template-based)
    3. Updates the staged templates file so the outreach optimizer picks it up
    4. Returns list of synced variants for notification

    Returns:
        List of dicts with variant info that was synced
    """
    store = ExperimentStore()
    experiments = store.load_domain(domain)

    # Find kept experiments that haven't been synced yet
    kept = [
        e for e in experiments
        if e.result == "kept"
        and not e.variant.metadata.get("synced_to_optimizer", False)
    ]

    if not kept:
        return []

    synced = []
    staged = {}
    if STAGED_TEMPLATES_FILE.exists():
        with open(STAGED_TEMPLATES_FILE) as f:
            staged = json.load(f)

    for exp in kept:
        template_name = exp.variant.metadata.get(
            "deployed_template_name", f"auto_{exp.experiment_id}"
        )

        # Mark as synced
        staged[template_name] = {
            "text": exp.variant.variant_text,
            "hypothesis": exp.variant.hypothesis,
            "experiment_id": exp.experiment_id,
            "baseline_score": exp.baseline_metrics.composite_score,
            "variant_score": exp.variant_metrics.composite_score,
            "improvement_pct": round(
                (exp.variant_metrics.composite_score - exp.baseline_metrics.composite_score)
                / max(exp.baseline_metrics.composite_score, 0.001)
                * 100,
                1,
            ),
            "synced_at": datetime.utcnow().isoformat(),
            "active": True,
        }

        # Mark experiment as synced
        exp.variant.metadata["synced_to_optimizer"] = True
        exp.variant.metadata["synced_at"] = datetime.utcnow().isoformat()
        store.update_experiment(exp)

        synced.append(
            {
                "template_name": template_name,
                "hypothesis": exp.variant.hypothesis,
                "improvement_pct": staged[template_name]["improvement_pct"],
            }
        )

    # Write staged templates
    OUTREACH_OUTPUT.mkdir(parents=True, exist_ok=True)
    with open(STAGED_TEMPLATES_FILE, "w") as f:
        json.dump(staged, f, indent=2)

    return synced


def send_experiment_notification(domain: str, results: list[dict] | None = None) -> bool:
    """
    Send experiment results via Telegram (primary) and SMS (fallback).

    Notification includes:
    - How many experiments were evaluated
    - Which were kept/reverted
    - Cumulative improvement percentage
    - Any experiments pending approval
    """
    store = ExperimentStore()
    stats = store.get_stats(domain)
    learnings = store.get_learnings(domain, limit=3)

    # Build message
    lines = [f"AutoIterator [{domain}]"]
    lines.append(f"Total: {stats['total']} | Kept: {stats['kept']} | Reverted: {stats['reverted']}")

    if stats["proposed"] > 0:
        lines.append(f"Pending approval: {stats['proposed']}")

    if results:
        lines.append("")
        for r in results[:3]:  # Cap at 3 to fit SMS
            lines.append(f"  {r.get('result', '?').upper()}: {r.get('hypothesis', '')[:50]}")

    if learnings:
        lines.append("")
        lines.append("Recent:")
        for l in learnings[:2]:
            emoji = "+" if l["result"] == "kept" else "-"
            lines.append(f"  [{emoji}] {l['hypothesis'][:60]}")

    message = "\n".join(lines)

    # Try Telegram first
    telegram_sent = _send_telegram(message)

    # SMS fallback if Telegram fails
    if not telegram_sent:
        _send_sms(message[:160])

    return True


def _send_telegram(message: str) -> bool:
    """Send notification via Telegram bot."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")

    if not bot_token:
        print("[WARN] No TELEGRAM_BOT_TOKEN — skipping Telegram notification")
        return False

    try:
        import urllib.request

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[WARN] Telegram send failed: {e}")
        return False


def _send_sms(message: str) -> bool:
    """Send notification via Twilio SMS."""
    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER", "+18552399364")
        to_number = os.getenv("WILLIAM_PHONE", "+12393985676")

        if not account_sid or not auth_token:
            print("[WARN] No Twilio credentials — skipping SMS notification")
            return False

        client = Client(account_sid, auth_token)
        client.messages.create(body=message, from_=from_number, to=to_number)
        return True
    except Exception as e:
        print(f"[WARN] SMS send failed: {e}")
        return False


def send_approval_request(experiment_id: str, domain: str) -> bool:
    """
    Send a Telegram message requesting approval for a proposed experiment.
    William can reply via Clawdbot to approve/reject.
    """
    store = ExperimentStore()
    exp = store.get_experiment(domain, experiment_id)
    if not exp:
        return False

    message = (
        f"New AutoIterator proposal [{domain}]\n\n"
        f"Hypothesis: {exp.variant.hypothesis}\n\n"
        f"Variant:\n{exp.variant.variant_text[:300]}\n\n"
        f"Reply 'approve {experiment_id}' to deploy or 'reject {experiment_id}' to skip."
    )

    return _send_telegram(message)


def run_cycle(domain: str) -> dict:
    """
    Run a full optimization cycle:
    1. Check for experiments pending evaluation
    2. Evaluate any that are ready
    3. Sync winning variants to optimizer
    4. Send notification with results
    """
    evaluator = get_evaluator(domain)
    iterator = AutoIterator(evaluator)

    # Evaluate pending
    evaluated = iterator.evaluate_all_pending()
    eval_results = [
        {"experiment_id": e.experiment_id, "result": e.result, "hypothesis": e.variant.hypothesis}
        for e in evaluated
    ]

    # Sync winners
    synced = sync_winning_variants(domain)

    # Notify
    if evaluated or synced:
        send_experiment_notification(domain, eval_results)

    return {
        "domain": domain,
        "evaluated": len(evaluated),
        "synced": len(synced),
        "results": eval_results,
        "report": iterator.status_report(),
    }


def get_active_baselines(domain: str = "sms_outreach") -> list[str]:
    """
    Get the current best-performing template texts to use as baselines for proposals.
    Pulls from the outreach optimizer's real performance data.
    """
    # Read existing campaign JSON files for real template texts
    baselines = []
    campaigns_dir = OUTREACH_OUTPUT / "campaigns"

    if campaigns_dir.exists():
        for f in campaigns_dir.glob("*.json"):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                templates = data.get("templates", {})
                for name, tpl in templates.items():
                    body = tpl.get("body", "")
                    if body:
                        baselines.append(body)
            except (json.JSONDecodeError, KeyError):
                continue

    # Also check staged templates for any prior winning variants
    if STAGED_TEMPLATES_FILE.exists():
        try:
            with open(STAGED_TEMPLATES_FILE) as f:
                staged = json.load(f)
            for name, tpl in staged.items():
                if tpl.get("active") and tpl.get("text"):
                    baselines.append(tpl["text"])
        except (json.JSONDecodeError, KeyError):
            pass

    return baselines


# ── CLI ──


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoIterator Bridge — Outreach Integration")
    subparsers = parser.add_subparsers(dest="command")

    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync winning variants to outreach optimizer")
    sync_parser.add_argument("--domain", "-d", default="sms_outreach")

    # Notify
    notify_parser = subparsers.add_parser("notify", help="Send experiment results notification")
    notify_parser.add_argument("--domain", "-d", default="sms_outreach")

    # Cycle
    cycle_parser = subparsers.add_parser("cycle", help="Full cycle: evaluate → sync → notify")
    cycle_parser.add_argument("--domain", "-d", default="sms_outreach")

    # Propose
    propose_parser = subparsers.add_parser("propose", help="Propose a new variant from best baseline")
    propose_parser.add_argument("--domain", "-d", default="sms_outreach")

    args = parser.parse_args()

    if args.command == "sync":
        synced = sync_winning_variants(args.domain)
        if synced:
            print(f"Synced {len(synced)} winning variants:")
            for s in synced:
                print(f"  {s['template_name']}: +{s['improvement_pct']}% ({s['hypothesis'][:60]})")
        else:
            print("No new variants to sync.")

    elif args.command == "notify":
        send_experiment_notification(args.domain)
        print("Notification sent.")

    elif args.command == "cycle":
        result = run_cycle(args.domain)
        print(f"Cycle complete: evaluated={result['evaluated']}, synced={result['synced']}")
        if result["results"]:
            for r in result["results"]:
                print(f"  {r['result'].upper()}: {r['hypothesis'][:60]}")

    elif args.command == "propose":
        baselines = get_active_baselines(args.domain)
        if not baselines:
            print("No active baselines found. Add templates to the outreach system first.")
            return

        # Use the first baseline (best performing) for proposal
        baseline = baselines[0]
        evaluator = get_evaluator(args.domain)
        iterator = AutoIterator(evaluator)
        exp = iterator.propose(baseline)

        print(f"Proposed: {exp.experiment_id}")
        print(f"Hypothesis: {exp.variant.hypothesis}")
        print(f"Variant: {exp.variant.variant_text[:200]}...")

        if exp.approval_required:
            send_approval_request(exp.experiment_id, args.domain)
            print("Approval request sent via Telegram.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
