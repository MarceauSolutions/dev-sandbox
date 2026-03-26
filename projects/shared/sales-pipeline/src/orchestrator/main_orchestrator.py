#!/usr/bin/env python3
"""
Sales Pipeline Orchestrator — Single entry point for the daily pipeline run.

Runs all 7 steps in sequence. Logs everything. Handles errors per-step
(one failure doesn't stop others).

Usage:
    python -m src.orchestrator.main_orchestrator              # Full daily run
    python -m src.orchestrator.main_orchestrator --dry-run    # Preview only
    python -m src.orchestrator.main_orchestrator --step score # Run one step
    python -m src.orchestrator.main_orchestrator --step report --dry-run

Available steps:
    acquire    — Pull fresh leads from Apollo
    score      — Score and tier all unscored leads
    validate   — Self-correct pipeline data
    route      — Determine today's tasks for each lead
    outreach   — Send emails (and SMS to opted-in contacts)
    replies    — Check for email responses
    report     — Generate daily Google Sheet call list
    sync       — Pull William's call results from Google Sheet
    ab_eval    — Evaluate A/B test variants
    full       — Run all steps in order (default)
"""

import sys
import sqlite3
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from .config import DB_PATH


def _validate_pipeline(dry_run: bool = False) -> dict:
    """
    Self-validate pipeline before generating reports.

    Fixes:
    - Close dead leads (explicitly said Not Interested)
    - Fix stuck stages (outreach done but still Prospect)
    - Set missing follow-up dates
    """
    print("\n=== PIPELINE VALIDATION ===")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    fixes = {"stuck_fixed": 0, "followups_set": 0, "dead_closed": 0}

    # 1. Fix stuck Prospects with outreach history -> move to Contacted
    stuck = conn.execute("""
        SELECT d.id, d.company FROM deals d
        WHERE d.stage = 'Prospect'
        AND d.id IN (SELECT DISTINCT deal_id FROM outreach_log WHERE deal_id IS NOT NULL)
    """).fetchall()

    for row in stuck:
        if not dry_run:
            conn.execute(
                "UPDATE deals SET stage = 'Contacted', updated_at = datetime('now') WHERE id = ?",
                (row["id"],)
            )
        fixes["stuck_fixed"] += 1
        print(f"  Fixed stuck: {row['company']} (Prospect -> Contacted)")

    # 2. Set missing follow-up dates for active deals
    missing_followup = conn.execute("""
        SELECT id, company, stage FROM deals
        WHERE (next_action_date IS NULL OR next_action_date = '')
        AND stage NOT IN ('Closed Won', 'Closed Lost', 'Prospect')
    """).fetchall()

    from .config import DEFAULT_FOLLOWUP_DAYS
    now = datetime.now()
    for row in missing_followup:
        days = DEFAULT_FOLLOWUP_DAYS.get(row["stage"], 3)
        followup = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        if not dry_run:
            conn.execute(
                "UPDATE deals SET next_action_date = ? WHERE id = ?",
                (followup, row["id"]),
            )
        fixes["followups_set"] += 1

    # 3. Also fix the "Outreach" and "Active" stages that aren't standard
    nonstandard = conn.execute("""
        SELECT id, company, stage FROM deals
        WHERE stage IN ('Outreach', 'Active', 'Intake')
        AND stage NOT IN ('Closed Won', 'Closed Lost')
    """).fetchall()

    for row in nonstandard:
        # Check if they have any outreach logged
        has_outreach = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE deal_id = ?", (row["id"],)
        ).fetchone()[0]

        new_stage = "Contacted" if has_outreach > 0 else "Prospect"
        if not dry_run:
            conn.execute(
                "UPDATE deals SET stage = ?, updated_at = datetime('now') WHERE id = ?",
                (new_stage, row["id"]),
            )
        fixes["stuck_fixed"] += 1

    if not dry_run:
        conn.commit()
    conn.close()

    print(f"  Stuck fixed: {fixes['stuck_fixed']}")
    print(f"  Follow-ups set: {fixes['followups_set']}")
    return fixes


def run_step(step: str, dry_run: bool = False) -> dict:
    """
    Run a single orchestrator step.
    """
    result = {"step": step, "status": "success", "data": {}}

    try:
        if step == "acquire":
            from .lead_acquisition import run_acquisition
            count = run_acquisition(dry_run=dry_run)
            result["data"] = {"new_leads": count}

        elif step == "score":
            from .lead_scorer import run_scoring
            scores = run_scoring(dry_run=dry_run)
            result["data"] = scores

        elif step == "validate":
            fixes = _validate_pipeline(dry_run=dry_run)
            result["data"] = fixes

        elif step == "route":
            from .follow_up_router import run_routing
            tasks = run_routing(dry_run=dry_run)
            result["data"] = {"total_tasks": len(tasks), "tasks": tasks}

        elif step == "outreach":
            from .follow_up_router import run_routing
            from .outreach_executor import run_outreach
            tasks = run_routing(dry_run=True, include_scripts=False)
            outreach_results = run_outreach(tasks, dry_run=dry_run)
            result["data"] = outreach_results

        elif step == "replies":
            from .reply_monitor import check_replies
            replies = check_replies(hours=24, dry_run=dry_run)
            result["data"] = {"total_replies": len(replies), "replies": replies}

        elif step == "report":
            from .follow_up_router import run_routing
            from .daily_report import run_daily_report
            tasks = run_routing(dry_run=False, include_scripts=True)
            sheet_url = run_daily_report(tasks, dry_run=dry_run)
            result["data"] = {"sheet_url": sheet_url, "task_count": len(tasks)}

        elif step == "sync":
            from .sync_outcomes import run_sync
            sync_results = run_sync(dry_run=dry_run)
            result["data"] = sync_results

        elif step == "morning_routine":
            run_morning_routine(dry_run=dry_run)
            result["data"] = {"message": "Morning routine completed"}

        elif step == "ab_eval":
            from .ab_testing_manager import run_ab_evaluation
            ab_results = run_ab_evaluation(dry_run=dry_run)
            result["data"] = ab_results

        else:
            result["status"] = "error"
            result["error"] = f"Unknown step: {step}"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"\n  [ERROR] Step '{step}' failed: {e}")
        traceback.print_exc()

    return result

def run_morning_routine(dry_run: bool = False):
    """Run complete morning routine: create schedule, update goals, prepare command center."""
    print("\n🌅 MORNING ROUTINE")

    # Create daily calendar schedule
    try:
        from ..calendar_integration import create_daily_schedule
        create_daily_schedule()
        print("  ✅ Daily calendar schedule created")
    except Exception as e:
        print(f"  ❌ Calendar creation failed: {e}")

    # Update goal progress
    try:
        from ..accountability_tracker import update_goal_progress
        update_goal_progress()
        print("  ✅ Goal progress updated")
    except Exception as e:
        print(f"  ❌ Goal update failed: {e}")

    # Prepare command center
    try:
        from ..daily_command_center import get_daily_command_center
        data = get_daily_command_center()
        print(f"  ✅ Command center ready: {len(data['calls']['tier_1'])} T1 calls, {len(data['visits'])} visits, {len(data['emails'])} emails")
    except Exception as e:
        print(f"  ❌ Command center failed: {e}")


def run_full_day_workflow(dry_run: bool = False):
    """Run complete daily workflow: Morning → Pipeline → Evening."""
    print("=" * 70)
    print("🌅 FULL DAY WORKFLOW — Complete Daily Sales Cycle")
    print("=" * 70)

    # 1. MORNING ROUTINE
    print("\n🌅 MORNING ROUTINE")
    print("-" * 30)
    try:
        run_morning_routine(dry_run=dry_run)
        print("✅ Morning routine completed")
    except Exception as e:
        print(f"❌ Morning routine failed: {e}")

    # 2. MAIN PIPELINE
    print("\n📊 MAIN PIPELINE")
    print("-" * 30)
    try:
        pipeline_results = run_full_pipeline(dry_run=dry_run)
        print("✅ Pipeline completed")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        pipeline_results = None

    # 3. EVENING ROUTINE
    print("\n🌙 EVENING ROUTINE")
    print("-" * 30)
    try:
        run_evening_routine(dry_run=dry_run)
        print("✅ Evening routine completed")
    except Exception as e:
        print(f"❌ Evening routine failed: {e}")

    print("\n" + "=" * 70)
    print("🎯 FULL DAY WORKFLOW COMPLETE")
    print("Ready for tomorrow's momentum toward April 6 goal!")
    print("=" * 70)

    return {
        "morning_complete": True,
        "pipeline_results": pipeline_results,
        "evening_complete": True,
        "timestamp": datetime.now().isoformat()
    }

def run_evening_routine(dry_run: bool = False):
    """Run evening routine: reflection, streak update, tomorrow prep."""
    print("📝 Reviewing today's performance...")

    # Update streaks and momentum
    try:
        from ..accountability_tracker import auto_log_from_pipeline, check_missed_activities
        auto_log_from_pipeline()
        check_missed_activities()
        print("  ✅ Accountability and streaks updated")
    except Exception as e:
        print(f"  ❌ Accountability update failed: {e}")

    # Generate tomorrow's preview
    try:
        from ..daily_command_center import get_daily_command_center
        tomorrow_data = get_daily_command_center()
        tomorrow_calls = len(tomorrow_data['calls']['tier_1']) + len(tomorrow_data['calls']['tier_2'])
        tomorrow_visits = len(tomorrow_data['visits'])
        tomorrow_emails = len(tomorrow_data['emails'])
        print(f"  📋 Tomorrow preview: {tomorrow_calls} calls, {tomorrow_visits} visits, {tomorrow_emails} emails")
    except Exception as e:
        print(f"  ❌ Tomorrow preview failed: {e}")

    # Send evening recap if configured
    try:
        from ..accountability_tracker import send_telegram_message
        streak_data = tomorrow_data.get('accountability', {}).get('streaks', {})
        recap = f"""🌙 Evening Recap - {datetime.now().strftime('%m/%d')}

🔥 Streak: {streak_data.get('current_streak', 0)} days
📊 Momentum: {streak_data.get('momentum_level', 'Low')}

📋 Tomorrow: {tomorrow_calls} calls, {tomorrow_visits} visits, {tomorrow_emails} emails

Keep the momentum going! 💪"""
        send_telegram_message(recap)
        print("  ✅ Evening recap sent")
    except Exception as e:
        print(f"  ❌ Evening recap failed: {e}")

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sales Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  acquire      Pull fresh leads from Apollo
  score        Score and tier all unscored leads
  validate     Self-correct pipeline data
  route        Determine today's tasks for each lead
  outreach     Send emails + SMS (opted-in only)
  replies      Check for email responses
  report       Generate daily Google Sheet call list
  sync         Pull call results from Google Sheet
  ab_eval      Evaluate A/B test variants
  full         Run all steps (default)
  full-day     Complete daily workflow (morning → pipeline → evening)

Examples:
  python -m src.orchestrator.main_orchestrator              # Full daily run
  python -m src.orchestrator.main_orchestrator --dry-run    # Preview only
  python -m src.orchestrator.main_orchestrator --step score # Score leads only
  python -m src.orchestrator.main_orchestrator --step sync  # Sync call outcomes
  python -m src.orchestrator.main_orchestrator --full-day   # Complete daily workflow
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't make changes")
    parser.add_argument("--step", type=str, default="full",
                       help="Run a specific step (or 'full' for all)")
    parser.add_argument("--full-day", action="store_true",
                       help="Run complete daily workflow (morning → pipeline → evening)")
    parser.add_argument("--tab", type=str, default=None,
                       help="Specific Google Sheet tab name (for sync step)")

    args = parser.parse_args()

    if args.full_day:
        results = run_full_day_workflow(dry_run=args.dry_run)
    elif args.step == "full":
        results = run_full_pipeline(dry_run=args.dry_run)
    elif args.step == "sync" and args.tab:
        from .sync_outcomes import run_sync
        results = run_sync(dry_run=args.dry_run, tab_name=args.tab)
    else:
        results = run_step(args.step, dry_run=args.dry_run)

    # Exit with error code if any step failed
    if isinstance(results, dict):
        if results.get("status") == "error":
            sys.exit(1)
        if results.get("_summary", {}).get("steps_failed", 0) > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
