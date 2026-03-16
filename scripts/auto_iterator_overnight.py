#!/usr/bin/env python3
"""
Overnight batch optimization for instant-eval domains.
Runs at 2 AM via launchd. Optimizes content quality, email subjects,
nurture emails, and website CTAs using LLM-as-judge.

Each domain gets a configurable number of iterations.
Results are logged and synced to Mem0 weekly.
"""

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from execution.auto_iterator import AutoIterator
from execution.auto_iterator_evaluators import get_evaluator
from execution.auto_iterator_bridge import send_experiment_notification

# Domains to optimize overnight (instant-eval only)
OVERNIGHT_DOMAINS = {
    "content_quality": {
        "iterations": 20,
        "baseline": "Create a 4-week evidence-based workout plan for a 35-year-old male looking to recomp. Include progressive overload, peptide-informed recovery windows, and macro targets.",
    },
    "email_subject": {
        "iterations": 15,
        "baseline": "Quick question about your business",
    },
    "nurture_email": {
        "iterations": 15,
        "baseline": "Hey {name}, what's taking up the most time in your business right now that you wish you could just hand off to someone? I help local businesses find where they're leaking time and money. — William",
    },
    "website_cta": {
        "iterations": 10,
        "baseline": "Get a Free Consultation",
    },
}


def main():
    print(f"\n{'='*60}")
    print(f"AutoIterator Overnight Batch — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    total_kept = 0
    total_run = 0
    summary = []

    for domain, config in OVERNIGHT_DOMAINS.items():
        print(f"\n--- {domain} ({config['iterations']} iterations) ---")

        try:
            evaluator = get_evaluator(domain)
            iterator = AutoIterator(evaluator)
            results = iterator.run_batch(
                baseline=config["baseline"],
                iterations=config["iterations"],
            )

            kept = [r for r in results if r.result == "kept"]
            total_kept += len(kept)
            total_run += len(results)

            summary.append({
                "domain": domain,
                "run": len(results),
                "kept": len(kept),
            })

            print(f"  {len(kept)}/{len(results)} variants kept")

        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append({"domain": domain, "run": 0, "kept": 0, "error": str(e)})

    # Send summary notification
    print(f"\n{'='*60}")
    print(f"Total: {total_kept}/{total_run} variants kept across {len(OVERNIGHT_DOMAINS)} domains")

    if total_run > 0:
        notification_results = [
            {"result": "kept" if s["kept"] > 0 else "reverted",
             "hypothesis": f"{s['domain']}: {s['kept']}/{s['run']} improvements"}
            for s in summary
        ]
        send_experiment_notification("overnight_batch", notification_results)


if __name__ == "__main__":
    main()
