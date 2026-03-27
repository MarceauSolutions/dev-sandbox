#!/usr/bin/env python3
"""
auto_iterator_report.py — Weekly Optimization Report Generator

WHAT: Generates a branded PDF report of AutoIterator experiment results
WHY:  William reviews optimization progress weekly without opening VS Code
INPUT: Experiment data from all domains
OUTPUT: Branded PDF report, auto-opened
COST: FREE

QUICK USAGE:
  python execution/auto_iterator_report.py
  python execution/auto_iterator_report.py --domain sms_outreach
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from execution.auto_iterator import ExperimentStore, EXPERIMENTS_DIR
from execution.auto_iterator_evaluators import EVALUATORS
from execution.branded_pdf_engine import BrandedPDFEngine

REPORTS_DIR = ROOT / "data" / "auto_iterator" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def build_domain_report(domain: str) -> dict:
    """Build report data for a single domain."""
    store = ExperimentStore()
    stats = store.get_stats(domain)
    learnings = store.get_learnings(domain, limit=5)
    experiments = store.load_domain(domain)

    # Calculate cumulative improvement
    kept = [e for e in experiments if e.result == "kept"]
    improvement = 0
    if kept:
        first_baseline = kept[0].baseline_metrics.composite_score
        last_variant = kept[-1].variant_metrics.composite_score
        if first_baseline > 0:
            improvement = round((last_variant - first_baseline) / first_baseline * 100, 1)

    # Find best variant
    best_variant = None
    if kept:
        best = max(kept, key=lambda e: e.variant_metrics.composite_score)
        best_variant = {
            "text": best.variant.variant_text,
            "score": best.variant_metrics.composite_score,
            "hypothesis": best.variant.hypothesis,
        }

    # Active experiments
    active = [
        {
            "id": e.experiment_id,
            "status": e.status,
            "hypothesis": e.variant.hypothesis,
            "deployed_at": e.deployed_at,
        }
        for e in experiments
        if e.status in ("proposed", "approved", "deployed", "collecting")
    ]

    return {
        "name": domain,
        "stats": stats,
        "improvement_pct": improvement,
        "best_variant": best_variant,
        "recent_learnings": learnings,
        "active_experiments": active,
    }


def generate_report(domains: list[str] | None = None) -> str:
    """
    Generate the weekly optimization report PDF.

    Returns path to generated PDF.
    """
    if not domains:
        # Auto-detect domains from experiment files
        domains = [
            f.stem.replace("_experiments", "")
            for f in EXPERIMENTS_DIR.glob("*_experiments.json")
        ]
        # Also include registered domains that may not have experiments yet
        for d in EVALUATORS:
            if d not in domains:
                domains.append(d)

    if not domains:
        print("No domains found. Run some experiments first.")
        return ""

    # Build report data
    today = datetime.now()
    week_ago = today - timedelta(days=7)

    data = {
        "title": "AutoIterator Weekly Optimization Report",
        "period": f"{week_ago.strftime('%B %d')} - {today.strftime('%B %d, %Y')}",
        "domains": [build_domain_report(d) for d in domains],
    }

    # Generate PDF
    engine = BrandedPDFEngine()
    output_path = REPORTS_DIR / f"optimization_report_{today.strftime('%Y%m%d')}.pdf"
    engine.generate_to_file("optimization_report", data, str(output_path))

    return str(output_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoIterator Weekly Report")
    parser.add_argument("--domain", "-d", nargs="*", help="Specific domains (default: all)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the PDF")
    args = parser.parse_args()

    path = generate_report(args.domain)

    if path:
        print(f"Report generated: {path}")
        if not args.no_open:
            subprocess.run(["open", path])
    else:
        print("No report generated.")


if __name__ == "__main__":
    main()
