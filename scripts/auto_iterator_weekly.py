#!/usr/bin/env python3
"""
Weekly AutoIterator report + cross-domain learning.
Runs Monday 8 AM via launchd.

1. Generate weekly PDF report (auto-opens)
2. Run cross-domain pattern analysis
3. Sync insights to Mem0
4. Update strategy documents
5. Send Telegram summary
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from execution.auto_iterator_report import generate_report
from execution.auto_iterator_learner import CrossDomainLearner
from execution.auto_iterator_bridge import send_experiment_notification


def main():
    print("=== Weekly AutoIterator Report ===\n")

    # 1. Generate PDF report
    print("[1/4] Generating weekly PDF report...")
    pdf_path = generate_report()
    if pdf_path:
        print(f"  Report: {pdf_path}")
        subprocess.run(["open", pdf_path])
    else:
        print("  No data for report.")

    # 2. Cross-domain analysis
    print("[2/4] Running cross-domain pattern analysis...")
    learner = CrossDomainLearner()
    result = learner.run_full_analysis()

    patterns = result.get("patterns_found", 0)
    stored = result.get("mem0_stored", 0)
    updated = result.get("strategies_updated", [])

    print(f"  Patterns: {patterns}, Mem0: {stored}, Strategies: {len(updated)}")

    # 3. Send Telegram summary
    print("[3/4] Sending Telegram summary...")
    summary_lines = [
        "Weekly AutoIterator Report",
        f"Patterns found: {patterns}",
        f"Mem0 insights: {stored}",
        f"Strategies updated: {len(updated)}",
    ]

    # Add top patterns
    analysis = result.get("analysis", {})
    for p in analysis.get("patterns", [])[:3]:
        summary_lines.append(f"  [{p.get('confidence', '?')}] {p['pattern'][:80]}")

    send_experiment_notification("weekly_report", [
        {"result": "kept", "hypothesis": line}
        for line in summary_lines[1:4]
    ])

    print("[4/4] Done.\n")


if __name__ == "__main__":
    main()
