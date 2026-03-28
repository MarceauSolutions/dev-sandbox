#!/usr/bin/env python3
"""
Cross-Tower Sync — Lightweight process that runs alongside daily_loop.

Processes:
  1. Pending tower_protocol requests for personal-assistant
  2. Pending tower_protocol requests for fitness-influencer
  3. Pending orchestrator tasks assigned to 'claude'
  4. Goal progress alerts (sends Telegram if off-track)

Designed to run as its own launchd job on a 5-minute cycle,
or be called manually. Does NOT modify daily_loop.py.

Usage:
    python execution/cross_tower_sync.py              # Run once
    python execution/cross_tower_sync.py --dry-run    # Preview only
    python execution/cross_tower_sync.py --status     # Show pending counts
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cross_tower_sync")


def process_tower_requests(dry_run: bool = False) -> dict:
    """Process pending tower_protocol requests for PA and fitness towers."""
    results = {"pa": {"processed": 0}, "fitness": {"processed": 0}}

    # Process personal-assistant requests
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pa_tower_handler",
            REPO_ROOT / "projects" / "personal-assistant" / "src" / "tower_handler.py"
        )
        pa_handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pa_handler)
        results["pa"] = pa_handler.process_pending(dry_run=dry_run)
    except Exception as e:
        logger.error(f"PA tower handler failed: {e}")
        results["pa"]["error"] = str(e)

    # Process fitness-influencer requests
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "fitness_tower_handler",
            REPO_ROOT / "projects" / "fitness-influencer" / "src" / "tower_handler.py"
        )
        fi_handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fi_handler)
        results["fitness"] = fi_handler.process_pending(dry_run=dry_run)
    except Exception as e:
        logger.error(f"Fitness tower handler failed: {e}")
        results["fitness"]["error"] = str(e)

    return results


def check_goal_alerts() -> list:
    """Check if any goals are off-track and return alert messages."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "goal_progress",
            REPO_ROOT / "projects" / "personal-assistant" / "src" / "goal_progress.py"
        )
        gp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gp)
        return gp.check_alerts()
    except Exception as e:
        logger.error(f"Goal alert check failed: {e}")
        return [f"Goal alert check error: {e}"]


def check_deal_attention(dry_run: bool = False) -> str:
    """Proactive deal monitoring — finds deals needing attention.

    Runs every 5 minutes. Sends ONE consolidated Telegram message if anything
    needs William's attention. Designed for hospital-stay/away mode.

    Checks:
    1. Stale proposals (sent >3 days, no follow-up) -> auto-sends follow-up email
    2. Hot leads with no response >24h -> reminder
    3. New email replies from prospects -> notification
    4. Deals stuck in a stage >7 days -> nudge

    Returns: Telegram message string, or empty string if nothing needs attention.
    """
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        alerts = []
        actions_taken = []

        # 1. Stale proposals (>3 days without follow-up call)
        stale_proposals = conn.execute("""
            SELECT d.id, d.company, d.contact_name, d.contact_email, d.updated_at
            FROM deals d
            WHERE d.stage = 'Proposal Sent'
            AND d.updated_at < datetime('now', '-3 days')
            AND d.id NOT IN (
                SELECT deal_id FROM outreach_log
                WHERE created_at > datetime('now', '-3 days')
            )
        """).fetchall()

        for row in stale_proposals:
            d = dict(row)
            if d.get("contact_email") and not dry_run:
                # Auto-send follow-up email
                sent = _send_proposal_followup(d, pdb, conn)
                if sent:
                    actions_taken.append(f"Auto follow-up sent: {d['company']}")
            else:
                alerts.append(f"Proposal stale (>3d): {d['company']} — needs follow-up call")

        # 2. Qualified leads with phone that haven't been contacted in >5 days
        stale_qualified = conn.execute("""
            SELECT d.company, d.contact_phone
            FROM deals d
            WHERE d.stage = 'Qualified'
            AND d.contact_phone IS NOT NULL
            AND d.updated_at < datetime('now', '-5 days')
            LIMIT 3
        """).fetchall()

        if stale_qualified:
            names = [dict(r)["company"] for r in stale_qualified]
            alerts.append(f"Qualified leads going cold ({len(stale_qualified)}): {', '.join(names[:2])}")

        # 3. Trial active with no recent activity
        stale_trials = conn.execute("""
            SELECT d.company FROM deals d
            WHERE d.stage = 'Trial Active'
            AND d.updated_at < datetime('now', '-2 days')
        """).fetchall()

        for row in stale_trials:
            alerts.append(f"Trial needs check-in: {dict(row)['company']}")

        conn.close()

        # Build message
        lines = []
        if actions_taken:
            lines.append("AUTO-ACTIONS TAKEN:")
            for a in actions_taken:
                lines.append(f"  {a}")

        if alerts:
            lines.append("NEEDS YOUR ATTENTION:" if lines else "DEAL ATTENTION:")
            for a in alerts:
                lines.append(f"  {a}")

        if lines:
            # Only send once per hour (check timestamp file)
            alert_file = REPO_ROOT / "projects" / "personal-assistant" / "logs" / ".last_deal_alert"
            now = datetime.now()
            if alert_file.exists():
                try:
                    last = datetime.fromisoformat(alert_file.read_text().strip())
                    if (now - last).total_seconds() < 3600:
                        logger.debug("Deal alert suppressed (sent within last hour)")
                        return ""
                except (ValueError, OSError):
                    pass

            alert_file.parent.mkdir(parents=True, exist_ok=True)
            alert_file.write_text(now.isoformat())

            return "\n".join(lines)

    except Exception as e:
        logger.error(f"Deal attention check failed: {e}")

    return ""


def _send_proposal_followup(deal: dict, pdb, conn) -> bool:
    """Auto-send a follow-up email for a stale proposal."""
    import importlib.util

    contact = deal.get("contact_name") or ""
    first_name = contact.split()[0] if contact else ""
    greeting = f"Hi {first_name}" if first_name else "Hi"

    subject = f"Following up — {deal['company']} proposal"
    body = (
        f"{greeting},\n\n"
        f"I wanted to follow up on the proposal I sent over for {deal['company']}. "
        f"I know things get busy, so I wanted to make sure it didn't slip through "
        f"the cracks.\n\n"
        f"Quick reminder of the highlights:\n"
        f"- Custom AI system for your business\n"
        f"- $497/month, no long-term commitment\n"
        f"- 30-day money-back guarantee\n"
        f"- Live in 7 days\n\n"
        f"Would a 15-minute call this week work to walk through it together?\n"
        f"https://calendly.com/wmarceau/ai-services-discovery\n\n"
        f"William Marceau\n"
        f"Marceau Solutions\n"
        f"wmarceau@marceausolutions.com"
    )

    try:
        spec = importlib.util.spec_from_file_location(
            "gmail_api", REPO_ROOT / "projects" / "personal-assistant" / "src" / "gmail_api.py"
        )
        gm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gm)
        result = gm.send_email(to=deal["contact_email"], subject=subject, body=body)

        if result.get("success"):
            pdb.log_activity(conn, deal["id"], "outreach",
                             f"Auto follow-up email sent to {deal['contact_email']}")
            logger.info(f"Auto follow-up sent: {deal['company']} -> {deal['contact_email']}")
            return True
    except Exception as e:
        logger.error(f"Auto follow-up failed for {deal['company']}: {e}")

    return False


def get_status() -> dict:
    """Get pending counts across all systems."""
    status = {}

    try:
        from tower_protocol import check_pending
        status["pa_pending"] = len(check_pending("personal-assistant"))
        status["fitness_pending"] = len(check_pending("fitness-influencer"))
    except Exception as e:
        status["protocol_error"] = str(e)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "orchestrator", REPO_ROOT / "execution" / "grok_claude_orchestrator.py"
        )
        orch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orch)
        tasks = orch.get_pending(agent="claude")
        status["claude_tasks_pending"] = len(tasks)
        if tasks:
            status["next_task"] = tasks[0].get("task", "?")[:60]
    except Exception as e:
        status["orchestrator_error"] = str(e)

    try:
        alerts = check_goal_alerts()
        status["goal_alerts"] = len(alerts)
        if alerts:
            status["alert_detail"] = alerts[0][:80]
    except Exception:
        pass

    return status


def run_sync(dry_run: bool = False):
    """Run the full cross-tower sync cycle."""
    logger.info(f"Cross-tower sync starting (dry_run={dry_run})")

    # 1. Process tower requests
    tower_results = process_tower_requests(dry_run=dry_run)
    pa_count = tower_results["pa"].get("processed", 0)
    fi_count = tower_results["fitness"].get("processed", 0)
    if pa_count or fi_count:
        logger.info(f"Tower requests: PA={pa_count}, Fitness={fi_count}")

    # 2. Check goal alerts
    alerts = check_goal_alerts()
    if alerts:
        logger.warning(f"Goal alerts ({len(alerts)}): {alerts[0][:80]}")
        # Send to Telegram if we have bot credentials
        _send_telegram_alert("\n".join(alerts))

    # 3. Proactive deal monitoring (hospital-stay mode)
    deal_alerts = check_deal_attention(dry_run=dry_run)
    if deal_alerts:
        _send_telegram_alert(deal_alerts)

    # 4. Sync pipeline.db to EC2 (if changed)
    try:
        sync_script = REPO_ROOT / "scripts" / "sync_pipeline_to_ec2.sh"
        if sync_script.exists():
            import subprocess
            result = subprocess.run(
                ["bash", str(sync_script)],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                logger.info(f"Pipeline sync: {result.stdout.strip()}")
    except Exception as e:
        logger.debug(f"Pipeline sync skipped: {e}")

    # 5. Daily decision email (once per day, for hospital-stay mode)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "daily_decision_email",
            REPO_ROOT / "projects" / "personal-assistant" / "src" / "daily_decision_email.py"
        )
        dde = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dde)
        if dde.should_send_today() and not dry_run:
            now_hour = datetime.now().hour
            if 6 <= now_hour <= 8:  # Send between 6-8am
                result = dde.send_decision_email()
                if result.get("sent"):
                    logger.info(f"Decision email sent: {result['decisions_count']} decisions")
    except Exception as e:
        logger.debug(f"Decision email skipped: {e}")

    # 6. End-of-day summary to Telegram (once per day at 5pm)
    now = datetime.now()
    if 17 <= now.hour <= 18 and not dry_run:
        eod_file = REPO_ROOT / "projects" / "personal-assistant" / "logs" / ".last_eod_summary"
        should_send = True
        if eod_file.exists():
            try:
                last = eod_file.read_text().strip()[:10]
                should_send = last != now.strftime("%Y-%m-%d")
            except (ValueError, OSError):
                pass
        if should_send:
            eod_msg = _generate_eod_summary()
            if eod_msg:
                _send_telegram_alert(eod_msg)
                eod_file.parent.mkdir(parents=True, exist_ok=True)
                eod_file.write_text(now.isoformat())
                logger.info("End-of-day summary sent to Telegram")

    # 7. Summary
    status = get_status()
    logger.info(f"Sync complete: {json.dumps(status)}")
    return status


def _generate_eod_summary() -> str:
    """Generate end-of-day summary: what happened today + what needs attention tomorrow."""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        lines = [f"END OF DAY — {datetime.now().strftime('%A %B %d')}"]

        # Today's outreach
        outreach_today = conn.execute(
            "SELECT COUNT(*) FROM outreach_log WHERE created_at > datetime('now', '-12 hours')"
        ).fetchone()[0]

        # Stage changes today
        stage_changes = conn.execute(
            "SELECT COUNT(*) FROM activities WHERE activity_type = 'stage_changed' "
            "AND created_at > datetime('now', '-12 hours')"
        ).fetchone()[0]

        # Outcomes recorded today
        outcomes_today = conn.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes "
            "WHERE completed = 1 AND created_at > datetime('now', '-12 hours')"
        ).fetchone()[0]

        lines.append(f"Outreach sent: {outreach_today}")
        lines.append(f"Stage changes: {stage_changes}")
        lines.append(f"Outcomes recorded: {outcomes_today}")

        # Pipeline snapshot
        stages = dict(conn.execute(
            "SELECT stage, COUNT(*) FROM deals "
            "WHERE stage IN ('Qualified','Proposal Sent','Trial Active','Closed Won') "
            "GROUP BY stage"
        ).fetchall())
        if stages:
            parts = [f"{cnt} {s}" for s, cnt in stages.items()]
            lines.append(f"Pipeline: {', '.join(parts)}")

        # Tomorrow's priorities
        hot = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE stage IN ('Trial Active','Proposal Sent')"
        ).fetchone()[0]
        qualified = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE stage = 'Qualified' AND contact_phone IS NOT NULL"
        ).fetchone()[0]

        conn.close()

        if hot > 0:
            lines.append(f"\nTOMORROW: {hot} deal(s) close to cash — follow up first")
        if qualified > 0:
            lines.append(f"Then call {qualified} qualified leads (use 'next' for prep)")

        # Goal progress
        try:
            gp_spec = importlib.util.spec_from_file_location(
                "goal_progress",
                REPO_ROOT / "projects" / "personal-assistant" / "src" / "goal_progress.py"
            )
            gp = importlib.util.module_from_spec(gp_spec)
            gp_spec.loader.exec_module(gp)
            progress = gp.calculate_goal_progress()
            short = progress.get("short_term", {})
            if short:
                lines.append(f"Goal: {short.get('overall_pct', 0)}% | {short.get('days_left', '?')}d left")
        except Exception:
            pass

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"EOD summary failed: {e}")
        return ""


def _send_telegram_alert(message: str):
    """Send an alert to William via Telegram (if credentials available)."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        logger.debug("No TELEGRAM_BOT_TOKEN, skipping alert")
        return

    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram alert sent")
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Cross-Tower Sync")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    parser.add_argument("--status", action="store_true", help="Show pending counts only")
    args = parser.parse_args()

    if args.status:
        status = get_status()
        print(json.dumps(status, indent=2))
    else:
        result = run_sync(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
