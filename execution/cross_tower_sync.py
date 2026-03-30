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
    """Process pending tower_protocol requests for all towers.
    
    NEW: Requests are processed in ROI priority order (high priority first).
    """
    results = {
        "pa": {"processed": 0}, 
        "fitness": {"processed": 0},
        "triggers_fired": 0,
        "conversions_logged": 0,
        "priority_order": True,
    }

    # Step 1: Check for deal stage changes and fire triggers
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tower_triggers", REPO_ROOT / "execution" / "tower_triggers.py"
        )
        triggers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(triggers)
        
        if not dry_run:
            trigger_results = triggers.check_stage_triggers(since_minutes=15)
            total_triggered = sum(len(v) for v in trigger_results.values())
            results["triggers_fired"] = total_triggered
            if total_triggered:
                logger.info(f"Stage triggers fired: {total_triggered} requests")
    except Exception as e:
        logger.error(f"Trigger check failed: {e}")
        results["trigger_error"] = str(e)

    # Step 2: Process personal-assistant requests (priority order)
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

    # Step 3: Process fitness-influencer requests (priority order)
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

    # Step 4: Log conversions for recently completed requests
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tower_analytics", REPO_ROOT / "execution" / "tower_analytics.py"
        )
        analytics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analytics)
        
        # Get recently completed requests
        from tower_protocol import _get_db
        conn = _get_db()
        completed = conn.execute("""
            SELECT id FROM tower_requests 
            WHERE status IN ('completed', 'failed')
            AND updated_at > datetime('now', '-20 minutes')
        """).fetchall()
        conn.close()
        
        conversion_count = 0
        for row in completed:
            req_id = row[0]
            conv_id = analytics.auto_log_completed_request(req_id)
            if conv_id:
                conversion_count += 1
        
        results["conversions_logged"] = conversion_count
        
        # Periodically update conversion probabilities (every ~6 hours)
        analytics.update_conversion_probabilities()
        
    except Exception as e:
        logger.error(f"Analytics logging failed: {e}")
        results["analytics_error"] = str(e)

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

        # 1. Stale proposals — follow-up timing adapts based on learning
        # Default: 3 days. With 5+ outcomes: 2 days (more aggressive).
        try:
            _ol_spec = importlib.util.spec_from_file_location(
                "outcome_learner", REPO_ROOT / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
            )
            _ol = importlib.util.module_from_spec(_ol_spec)
            _ol_spec.loader.exec_module(_ol)
            follow_up_days = _ol.load_preferences().get("follow_up_days", 3)
        except Exception:
            follow_up_days = 3

        stale_proposals = conn.execute(f"""
            SELECT d.id, d.company, d.contact_name, d.contact_email, d.updated_at
            FROM deals d
            WHERE d.stage = 'Proposal Sent'
            AND d.updated_at < datetime('now', '-{follow_up_days} days')
            AND d.id NOT IN (
                SELECT deal_id FROM outreach_log
                WHERE created_at > datetime('now', '-{follow_up_days} days')
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

        # 4. AWAY-MODE: Auto-prepare new hot/warm responses
        # When a lead responds positively, don't just alert — prepare everything
        # so William only needs to make ONE call.
        new_responses = conn.execute("""
            SELECT d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
                   d.industry, d.city, d.stage, d.notes
            FROM deals d
            WHERE d.stage IN ('Hot Response', 'Warm Response', 'Qualified')
            AND d.updated_at > datetime('now', '-1 hour')
            AND d.id NOT IN (
                SELECT deal_id FROM activities
                WHERE description LIKE '%Away-mode auto-prep%'
                AND created_at > datetime('now', '-6 hours')
            )
            LIMIT 3
        """).fetchall()

        for row in new_responses:
            d = dict(row)
            company = d["company"]
            prep_actions = []

            # Auto-generate proposal if email exists and no proposal yet
            if d.get("contact_email") and not dry_run:
                has_proposal = conn.execute(
                    "SELECT COUNT(*) FROM activities WHERE deal_id = ? AND description LIKE '%Proposal%'",
                    (d["id"],)
                ).fetchone()[0]
                if not has_proposal:
                    if _auto_generate_proposal(d):
                        pdb.log_activity(conn, d["id"], "outreach",
                                         f"Proposal auto-generated for {company}")
                        prep_actions.append("proposal generated")

            # Build call prep context
            phone = d.get("contact_phone") or "no phone"
            name = d.get("contact_name") or "?"
            industry = d.get("industry") or "?"
            notes = (d.get("notes") or "")[:120]

            # Log the away-mode prep
            if not dry_run:
                pdb.log_activity(conn, d["id"], "outreach",
                                 f"Away-mode auto-prep: {', '.join(prep_actions) if prep_actions else 'call brief ready'}")

            # Build notification with full context
            notif_lines = [
                f"NEW: {company} [{d['stage']}]",
                f"  Call {name} at {phone}",
                f"  Industry: {industry} | {d.get('city', 'Naples')}",
            ]
            if notes:
                notif_lines.append(f"  Context: {notes}")
            if prep_actions:
                notif_lines.append(f"  Auto: {', '.join(prep_actions)}")
            if d.get("contact_email"):
                notif_lines.append(f"  Ready: 'send proposal {company}'")
            notif_lines.append(f"  After call: 'result {company}: [outcome]'")

            actions_taken.append("\n".join(notif_lines))

        # 5. Auto-generate proposals for qualified leads with email but no proposal yet
        # This is the key hospital-stay automation: system creates proposals without William
        new_qualified = conn.execute("""
            SELECT d.id, d.company, d.contact_name, d.contact_email, d.industry
            FROM deals d
            WHERE d.stage = 'Qualified'
            AND d.contact_email IS NOT NULL AND d.contact_email != ''
            AND d.id NOT IN (
                SELECT deal_id FROM activities
                WHERE activity_type = 'outreach'
                AND description LIKE '%Proposal%'
            )
            LIMIT 2
        """).fetchall()

        for row in new_qualified:
            d = dict(row)
            if not dry_run:
                generated = _auto_generate_proposal(d)
                if generated:
                    pdb.log_activity(conn, d["id"], "outreach",
                                     f"Proposal auto-generated for {d['company']}")
                    actions_taken.append(f"Proposal auto-generated: {d['company']}")
            else:
                actions_taken.append(f"[DRY] Would auto-generate proposal: {d['company']}")

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
    """Get pending counts across all systems including priority queue status."""
    status = {}

    try:
        from tower_protocol import check_pending, get_high_priority_requests
        
        # Pending by tower
        pa_pending = check_pending("personal-assistant")
        fitness_pending = check_pending("fitness-influencer")
        
        status["pa_pending"] = len(pa_pending)
        status["fitness_pending"] = len(fitness_pending)
        
        # High priority requests
        high_priority = get_high_priority_requests(min_priority=0.7)
        status["high_priority_pending"] = len(high_priority)
        
        # Show top priority request
        if pa_pending:
            top = pa_pending[0]
            status["pa_top_priority"] = f"{top.get('action', '?')} (p={top.get('priority_score', 0.5):.2f})"
        if fitness_pending:
            top = fitness_pending[0]
            status["fitness_top_priority"] = f"{top.get('action', '?')} (p={top.get('priority_score', 0.5):.2f})"
            
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

    # Analytics summary
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tower_analytics", REPO_ROOT / "execution" / "tower_analytics.py"
        )
        analytics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analytics)
        
        dash = analytics.get_tower_dashboard()
        overall = dash.get("overall", {})
        status["cross_tower_revenue"] = overall.get("total_revenue", 0)
        status["cross_tower_clients_won"] = overall.get("clients_won", 0)
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


def _auto_generate_proposal(deal: dict) -> bool:
    """Auto-generate a branded proposal PDF for a qualified lead.

    Called by check_deal_attention when a qualified lead has an email
    but no proposal has been generated yet. The proposal is saved locally
    and William is notified — it is NOT auto-sent to the client (that
    requires William's approval for quality control).
    """
    import importlib.util
    import sys
    from datetime import datetime

    try:
        # Generate the proposal using the same engine as handle_proposal
        sys.path.insert(0, str(REPO_ROOT / "projects" / "fitness-influencer" / "src"))
        import pdf_templates.proposal_template  # registers the template
        from branded_pdf_engine import BrandedPDFEngine

        industry = (deal.get("industry") or "business").lower()
        pain_map = {
            "hvac": ("Missing after-hours emergency calls.",
                     "AI Phone Agent + Automated Follow-Up System"),
            "med spa": ("No-shows and missed booking follow-ups.",
                        "AI Booking Assistant + Smart Follow-Up Engine"),
            "plumb": ("Emergency calls going to voicemail after hours.",
                      "AI Emergency Call Handler + Lead Capture System"),
            "chiro": ("New patient follow-ups falling through the cracks.",
                      "AI Patient Engagement System"),
        }

        pain = "Manual follow-ups and missed opportunities."
        solution = "AI Automation System"
        for key, (p, s) in pain_map.items():
            if key in industry:
                pain, solution = p, s
                break

        proposal_data = {
            "client_name": deal.get("contact_name") or "",
            "business_name": deal["company"],
            "industry": deal.get("industry") or "Local Business",
            "problem_statement": pain,
            "solution": solution,
            "solution_details": [
                "24/7 automated response to inquiries",
                "Smart follow-up sequences via SMS and email",
                "Lead qualification and appointment booking",
                "Monthly analytics and ROI dashboard",
            ],
            "timeline": "7 days to full deployment",
            "investment": {"setup": "$0 setup", "monthly": "$497/mo"},
            "guarantee": "30-day money-back guarantee.",
            "next_steps": "Book a demo: calendly.com/wmarceau/ai-services-discovery",
        }

        engine = BrandedPDFEngine()
        output_dir = REPO_ROOT / "projects" / "personal-assistant" / "logs" / "proposals"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = deal["company"].replace(" ", "_").replace("/", "-").replace("&", "_")[:30]
        filename = f"proposal_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = output_dir / filename

        engine.generate_to_file("proposal", proposal_data, str(output_path))
        logger.info(f"Auto-proposal generated: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
        return True

    except Exception as e:
        logger.error(f"Auto-proposal failed for {deal.get('company', '?')}: {e}")
        return False


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
    """Queue alert for digest instead of sending immediately."""
    try:
        from execution.notification_policy import queue_for_digest
        queue_for_digest(
            "tower_sync",
            "Cross-Tower Sync Update",
            message[:500],
            metadata={"source": "cross_tower_sync"}
        )
        logger.info("Alert queued for digest")
    except Exception as e:
        logger.error(f"Failed to queue alert: {e}")


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
