#!/usr/bin/env python3
"""
auto_iterator_cron.py — EC2 Cron Entry Point for AutoIterator

Runs on EC2 cron to:
1. Overnight (2am): Run instant-eval batch experiments (content_quality, website_cta)
2. Daily (6am): Evaluate any real-data experiments that are ready (sms_outreach)
3. Weekly (Monday 3am): Generate report and sync winning variants

Usage:
    python execution/auto_iterator_cron.py overnight    # 2am daily
    python execution/auto_iterator_cron.py evaluate     # 6am daily  
    python execution/auto_iterator_cron.py weekly       # Monday 3am
    python execution/auto_iterator_cron.py full         # All of the above
    python execution/auto_iterator_cron.py status       # Check current state

Designed for crontab entries on EC2.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "projects" / "lead-generation" / "src"))
sys.path.insert(0, str(REPO_ROOT / "execution"))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

def send_telegram(message: str) -> bool:
    """Send notification to Telegram."""
    import urllib.request
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        print(f"[NO TELEGRAM] {message}")
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message[:4096], "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def run_overnight():
    """Run batch experiments for instant-eval domains (2am daily)."""
    from auto_iterator import AutoIterator
    from auto_iterator_evaluators import get_evaluator
    
    print(f"\n{'='*50}")
    print(f"AutoIterator Overnight Run — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    results = {"kept": 0, "reverted": 0, "errors": 0}
    
    # Instant-eval domains: content_quality, website_cta
    instant_domains = ["content_quality", "website_cta"]
    
    for domain in instant_domains:
        try:
            print(f"\n→ Running {domain} batch (5 iterations)...")
            evaluator = get_evaluator(domain)
            iterator = AutoIterator(evaluator)
            
            # Get current baseline from strategy or default
            baseline = _get_baseline_for_domain(domain)
            
            batch_results = iterator.run_batch(baseline, iterations=5)
            kept = len([r for r in batch_results if r.result == "kept"])
            reverted = len([r for r in batch_results if r.result == "reverted"])
            
            results["kept"] += kept
            results["reverted"] += reverted
            print(f"  ✓ {domain}: {kept} kept, {reverted} reverted")
            
        except Exception as e:
            results["errors"] += 1
            print(f"  ✗ {domain}: {e}")
    
    # Notify if any winners
    if results["kept"] > 0:
        send_telegram(f"🔬 *AutoIterator Overnight*\n\n{results['kept']} winning variants found\n{results['reverted']} reverted\n{results['errors']} errors")
    
    return results


def run_evaluate():
    """Evaluate all pending real-data experiments (6am daily)."""
    from auto_iterator import AutoIterator
    from auto_iterator_evaluators import get_evaluator, EVALUATORS
    
    print(f"\n{'='*50}")
    print(f"AutoIterator Daily Evaluation — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    results = {"evaluated": 0, "kept": 0, "reverted": 0, "collecting": 0}
    
    for domain in EVALUATORS.keys():
        try:
            evaluator = get_evaluator(domain)
            iterator = AutoIterator(evaluator)
            
            eval_results = iterator.evaluate_all_pending()
            for exp in eval_results:
                results["evaluated"] += 1
                if exp.result == "kept":
                    results["kept"] += 1
                elif exp.result == "reverted":
                    results["reverted"] += 1
                elif exp.status == "collecting":
                    results["collecting"] += 1
                    
            if eval_results:
                print(f"  {domain}: evaluated {len(eval_results)}")
                
        except Exception as e:
            print(f"  {domain}: error - {e}")
    
    if results["kept"] > 0:
        send_telegram(f"📊 *AutoIterator Evaluation*\n\n{results['kept']} winners deployed\n{results['reverted']} reverted\n{results['collecting']} still collecting data")
    
    return results


def run_weekly():
    """Weekly report + sync winning variants (Monday 3am)."""
    from auto_iterator import ExperimentStore
    from auto_iterator_evaluators import EVALUATORS
    
    print(f"\n{'='*50}")
    print(f"AutoIterator Weekly Report — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    store = ExperimentStore()
    report_lines = ["🔬 *AutoIterator Weekly Report*\n"]
    
    total_kept = 0
    total_experiments = 0
    
    for domain in EVALUATORS.keys():
        stats = store.get_stats(domain)
        if stats["total"] > 0:
            total_experiments += stats["total"]
            total_kept += stats["kept"]
            report_lines.append(f"*{domain}*: {stats['total']} experiments")
            report_lines.append(f"  ✅ Kept: {stats['kept']} | ❌ Reverted: {stats['reverted']}")
            
            learnings = store.get_learnings(domain, limit=2)
            for l in learnings:
                emoji = "+" if l["result"] == "kept" else "-"
                report_lines.append(f"  [{emoji}] {l['hypothesis'][:50]}...")
            report_lines.append("")
    
    if total_experiments == 0:
        report_lines.append("No experiments run yet. System is ready for optimization.")
    else:
        win_rate = (total_kept / total_experiments * 100) if total_experiments else 0
        report_lines.append(f"*Overall*: {total_kept}/{total_experiments} variants kept ({win_rate:.0f}% win rate)")
    
    report = "\n".join(report_lines)
    print(report)
    send_telegram(report)
    
    return {"total": total_experiments, "kept": total_kept}


def run_status():
    """Show current AutoIterator status."""
    from auto_iterator import ExperimentStore
    from auto_iterator_evaluators import EVALUATORS
    
    store = ExperimentStore()
    
    print(f"\n{'='*50}")
    print(f"AutoIterator Status — {datetime.now().isoformat()}")
    print(f"{'='*50}")
    
    for domain in EVALUATORS.keys():
        stats = store.get_stats(domain)
        print(f"\n{domain}:")
        print(f"  Total: {stats['total']} | Kept: {stats['kept']} | Reverted: {stats['reverted']}")
        print(f"  Active: proposed={stats['proposed']} deployed={stats['deployed']} collecting={stats['collecting']}")


def run_full():
    """Run all AutoIterator tasks."""
    print("Running full AutoIterator cycle...")
    run_overnight()
    run_evaluate()
    

def _get_baseline_for_domain(domain: str) -> str:
    """Get current baseline text for a domain."""
    baselines = {
        "content_quality": """Create a 4-week workout program for a 35-year-old male 
looking to build muscle and lose fat. Include progressive overload principles, 
compound movements, and recovery protocols.""",
        
        "website_cta": "Get a Free Consultation",
        
        "sms_outreach": """Hey {name}! It's William. I help local businesses 
automate their customer follow-ups so they never miss a lead. 
Quick question - how many calls do you miss after hours? 
Reply STOP to opt out.""",
        
        "email_subject": "Quick question about {business_name}",
        
        "nurture_email": """Hi {name},

What's taking up the most time in your business right now?

Most {industry} owners I talk to mention the same 2-3 things. 
Curious if you're dealing with the same challenges.

— William
Marceau Solutions
(239) 398-5676"""
    }
    return baselines.get(domain, "No baseline defined")


def main():
    parser = argparse.ArgumentParser(description="AutoIterator EC2 Cron Runner")
    parser.add_argument("command", choices=["overnight", "evaluate", "weekly", "full", "status"],
                        help="Which task to run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print(f"[DRY RUN] Would run: {args.command}")
        return
    
    if args.command == "overnight":
        run_overnight()
    elif args.command == "evaluate":
        run_evaluate()
    elif args.command == "weekly":
        run_weekly()
    elif args.command == "full":
        run_full()
    elif args.command == "status":
        run_status()


if __name__ == "__main__":
    main()
