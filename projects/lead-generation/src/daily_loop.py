#!/usr/bin/env python3
"""
Lead Generation Daily Loop — Autonomous Client Acquisition Orchestrator

Runs the full 8-stage acquisition loop as one coordinated operation.
Designed to execute unattended during William's 7am-3pm work hours.

Stages:
  1. DISCOVER  — Find new prospects (Apollo, Google Places, Sunbiz)
  2. SCORE     — ML scoring, filter to top 20%
  3. ENRICH    — Verify contacts via Apollo
  4. OUTREACH  — Send initial email (Touch 1), email only, max 10/day
  5. MONITOR   — Check Gmail + Twilio for replies
  6. CLASSIFY  — Hot/Warm/Cold/Opt-out classification
  7. FOLLOW-UP — Advance 3-touch sequences for non-responders
  8. REPORT    — Daily analytics digest to Telegram

Schedule (via cron or n8n):
  9:00am  — Full loop (stages 1-4, 7)
  Every 15 min, 9am-5pm — Response check (stages 5-6)
  5:30pm  — Daily digest (stage 8)

Usage:
    python -m src.daily_loop full --dry-run          # Preview full loop
    python -m src.daily_loop full --for-real          # Run full loop
    python -m src.daily_loop check-responses          # Check for replies (stages 5-6)
    python -m src.daily_loop digest                   # Send daily digest (stage 8)
    python -m src.daily_loop status                   # Show pipeline status
"""

import argparse
import json
import logging
import os
import sys
import traceback
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
REPO_ROOT = PROJECT_ROOT.parent.parent

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daily_loop")

# Stage results tracking
STAGE_RESULTS: Dict[str, Dict[str, Any]] = {}

# Self-monitoring
HEALTH_FILE = PROJECT_ROOT / "logs" / "loop_health.json"
CONSECUTIVE_FAILURE_THRESHOLD = 2


# ---------------------------------------------------------------------------
# Self-monitoring
# ---------------------------------------------------------------------------

def _load_health() -> Dict[str, Any]:
    """Load health history from disk."""
    if HEALTH_FILE.exists():
        try:
            with open(HEALTH_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"runs": [], "consecutive_failures": 0, "last_alert_date": None}


def _save_health(health: Dict[str, Any]):
    """Save health history to disk."""
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(health, f, indent=2)


def record_run_health(stage_results: Dict[str, Dict[str, Any]]):
    """Record this run's health and alert on consecutive failures.

    Tracks success/failure per stage. If the loop has critical failures
    (discover_score or follow_up) on 2+ consecutive days, sends a
    Telegram alert so William knows the system is degraded.
    """
    health = _load_health()
    today = datetime.now().strftime("%Y-%m-%d")

    successes = sum(1 for r in stage_results.values() if r.get("success"))
    total = len(stage_results)
    critical_ok = all(
        stage_results.get(s, {}).get("success", False)
        for s in ["discover_score", "follow_up"]
    )

    run_record = {
        "date": today,
        "time": datetime.now().strftime("%H:%M"),
        "stages_passed": successes,
        "stages_total": total,
        "critical_ok": critical_ok,
        "failures": {
            name: details.get("error", "")[:100]
            for name, details in stage_results.items()
            if not details.get("success")
        },
    }

    # Keep last 14 days of history
    health["runs"] = [r for r in health["runs"] if r.get("date", "") >= (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")]
    health["runs"].append(run_record)

    if critical_ok:
        health["consecutive_failures"] = 0
    else:
        health["consecutive_failures"] = health.get("consecutive_failures", 0) + 1

    _save_health(health)

    # Alert if consecutive failures hit threshold
    if health["consecutive_failures"] >= CONSECUTIVE_FAILURE_THRESHOLD:
        if health.get("last_alert_date") != today:
            failed_stages = ", ".join(run_record["failures"].keys())
            errors = "\n".join(f"  • {k}: {v}" for k, v in run_record["failures"].items())
            alert = (
                f"⚠️ *DAILY LOOP DEGRADED*\n\n"
                f"Failed {health['consecutive_failures']} days in a row.\n"
                f"Failing stages: {failed_stages}\n\n"
                f"Errors:\n{errors}\n\n"
                f"Check logs: `projects/lead-generation/logs/`\n"
                f"Manual run: `python -m src.daily_loop full --dry-run`"
            )
            send_telegram(alert)
            health["last_alert_date"] = today
            _save_health(health)
            logger.warning(f"ALERT SENT: {health['consecutive_failures']} consecutive failures")

    logger.info(f"Health: {successes}/{total} passed, consecutive failures: {health['consecutive_failures']}")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _get_ssl_context():
    """Get SSL context with proper CA bundle (fixes launchd SSL errors)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def send_telegram(message: str) -> bool:
    """Send message to William via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        logger.warning("No TELEGRAM_BOT_TOKEN — skipping Telegram")
        return False
    try:
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        urllib.request.urlopen(req, timeout=10, context=_get_ssl_context())
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_hot_lead_sms(deal: dict, reply_text: str) -> bool:
    """Send HOT lead alert SMS to William's phone with reply-to-action."""
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        to_number = "+12393985676"  # William's personal phone

        if not all([account_sid, auth_token, from_number]):
            logger.warning("Twilio credentials not configured — skipping SMS alert")
            return False

        company = deal.get("company", "Unknown")
        contact = deal.get("contact_name", "")
        industry = deal.get("industry", "")
        score = deal.get("score", "")
        city = deal.get("city", "Naples")

        body = (
            f"🔥 HOT LEAD\n\n"
            f"{company}"
            f"{' — ' + contact if contact else ''}\n"
            f'"{reply_text[:120]}"\n\n'
            f"Score: {score} | {industry} | {city}\n\n"
            f"Reply:\n"
            f"1 = Send Calendly link\n"
            f"2 = I'll call them now\n"
            f"3 = Pass"
        )

        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=body, from_=from_number, to=to_number)
        logger.info(f"HOT lead SMS sent: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"HOT lead SMS failed: {e}")
        return False


def get_pipeline_db():
    """Import pipeline_db from execution/ (shared utility)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _extract_count(text: str, *keywords) -> int:
    """Extract a numeric count near any of the given keywords in stdout text."""
    import re
    lower = text.lower()
    for kw in keywords:
        # Look for patterns like "discovered: 15" or "15 leads found"
        for pattern in [rf'{kw}\D*(\d+)', rf'(\d+)\D*{kw}']:
            m = re.search(pattern, lower)
            if m:
                return int(m.group(1))
    return 0


def log_stage(stage_name: str, success: bool, details: Dict[str, Any]):
    """Record stage result for the daily digest."""
    STAGE_RESULTS[stage_name] = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        **details,
    }
    status = "✓" if success else "✗"
    logger.info(f"Stage {stage_name}: {status} — {details}")


# ---------------------------------------------------------------------------
# Stage implementations
# ---------------------------------------------------------------------------

def _run_module(module_name: str, args: List[str], timeout: int = 300) -> Dict[str, Any]:
    """Run a lead-gen src module as a subprocess, respecting relative imports."""
    import subprocess
    cmd = [sys.executable, "-m", f"src.{module_name}"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stage_discover_and_score(dry_run: bool = True) -> Dict[str, Any]:
    """Stages 1-3: Discover, score, enrich, and outreach via campaign_auto_launcher."""
    try:
        args = ["--business", "marceau-solutions"]
        if dry_run:
            args.append("--dry-run")
        else:
            args.append("--for-real")

        result = _run_module("campaign_auto_launcher", args, timeout=180)

        if result["success"]:
            # Parse counts from stdout
            stdout = result.get("stdout", "")
            discovered = _extract_count(stdout, "discovered", "leads found")
            outreached = _extract_count(stdout, "outreached", "sent", "emails")
            log_stage("discover_score", True, {
                "discovered": discovered,
                "outreached": outreached,
            })
        else:
            stderr = result.get("stderr", "")[:500]
            logger.error(f"campaign_auto_launcher failed:\n{stderr}")
            log_stage("discover_score", False, {"error": stderr[:200]})

        return result

    except Exception as e:
        logger.error(f"Stage discover_score failed: {e}\n{traceback.format_exc()}")
        log_stage("discover_score", False, {"error": str(e)})
        return {"error": str(e)}


def stage_follow_up(dry_run: bool = True) -> Dict[str, Any]:
    """Stage 7: Advance follow-up sequences for non-responders."""
    try:
        args = ["process"]
        if dry_run:
            args.append("--dry-run")
        else:
            args.append("--for-real")

        result = _run_module("follow_up_sequence", args, timeout=120)

        if result["success"]:
            stdout = result.get("stdout", "")
            sent = _extract_count(stdout, "sent", "delivered", "processed")
            skipped = _extract_count(stdout, "skipped", "already")
            log_stage("follow_up", True, {"sent": sent, "skipped": skipped})
        else:
            stderr = result.get("stderr", "")[:500]
            logger.error(f"follow_up_sequence failed:\n{stderr}")
            log_stage("follow_up", False, {"error": stderr[:200]})

        return result

    except Exception as e:
        logger.error(f"Stage follow_up failed: {e}\n{traceback.format_exc()}")
        log_stage("follow_up", False, {"error": str(e)})
        return {"error": str(e)}


def stage_email_sequences(dry_run: bool = True) -> Dict[str, Any]:
    """Stage 7b: Process email sequences via Gmail API.
    
    - Auto-enrolls qualified leads from pipeline
    - Sends due emails
    - Checks for replies and stops sequences
    """
    try:
        sys.path.insert(0, str(REPO_ROOT.parent.parent / "execution"))
        from email_sequence_engine import (
            enroll_from_pipeline, process_due_emails, check_replies, get_status
        )
        
        results = {
            "enrolled": 0,
            "sent": 0,
            "replies": 0,
            "errors": 0
        }
        
        # Step 1: Auto-enroll new leads
        enrolled = enroll_from_pipeline(max_enrollments=20, dry_run=dry_run)
        results["enrolled"] = len(enrolled)
        
        # Step 2: Process due emails
        if not dry_run:
            stats = process_due_emails(dry_run=False)
            results["sent"] = stats.get("sent", 0)
            results["errors"] = stats.get("errors", 0)
        else:
            stats = process_due_emails(dry_run=True)
            results["sent"] = stats.get("sent", 0)
        
        # Step 3: Check for replies
        if not dry_run:
            reply_count = check_replies()
            results["replies"] = reply_count
        
        logger.info(f"Email sequences: enrolled={results['enrolled']}, sent={results['sent']}, replies={results['replies']}")
        log_stage("email_sequences", True, results)
        
        return {"success": True, **results}
        
    except Exception as e:
        logger.error(f"Email sequences stage failed: {e}")
        log_stage("email_sequences", False, {"error": str(e)})
        return {"success": False, "error": str(e)}


def stage_check_responses() -> Dict[str, Any]:
    """Stages 5-6: Monitor for replies and classify them."""
    hot_leads = []
    warm_leads = []
    opt_outs = []

    # Check Twilio inbox
    try:
        from twilio_inbox_monitor import TwilioInboxMonitor
        monitor = TwilioInboxMonitor()
        inbox_result = monitor.check_inbox()
        new_replies = inbox_result.get("new_replies", [])
        logger.info(f"Twilio inbox: {len(new_replies)} new replies")
    except Exception as e:
        logger.warning(f"Twilio inbox check failed: {e}")
        new_replies = []

    # Check Gmail for email replies
    try:
        gmail_replies = _check_gmail_replies()
        logger.info(f"Gmail: {len(gmail_replies)} new replies")
        new_replies.extend(gmail_replies)
    except Exception as e:
        logger.warning(f"Gmail reply check failed: {e}")

    # Sync with response tracker
    try:
        from response_tracker import ResponseTracker
        tracker = ResponseTracker()
        sync_result = tracker.sync_replies_to_templates()
        logger.info(f"Response tracker sync: {sync_result}")
    except Exception as e:
        logger.warning(f"Response tracker sync failed: {e}")

    # Classify each reply
    pdb = get_pipeline_db()
    conn = pdb.get_db()

    for reply in new_replies:
        classification = classify_response(reply.get("body", ""))
        phone = reply.get("from", "")
        body = reply.get("body", "")

        # Find the deal associated with this reply
        deal = _find_deal_by_contact(conn, phone)

        if classification == "hot":
            hot_leads.append({"deal": deal, "reply": body, "phone": phone})
            if deal:
                pdb.log_activity(conn, deal["id"], "hot_response", body[:200])
                pdb.update_deal(conn, deal["id"], stage="Hot Response",
                                next_action="schedule_call")
            # INSTANT alert to William
            send_hot_lead_sms(deal or {"company": phone}, body)
            send_telegram(f"🔥 *HOT LEAD*: {deal.get('company', phone) if deal else phone}\n\"{body[:150]}\"")

        elif classification == "warm":
            warm_leads.append({"deal": deal, "reply": body})
            if deal:
                pdb.log_activity(conn, deal["id"], "warm_response", body[:200])
                pdb.update_deal(conn, deal["id"], stage="Warm Response")

        elif classification == "opt_out":
            opt_outs.append({"phone": phone, "body": body})
            if deal:
                pdb.update_deal(conn, deal["id"], stage="Opted Out")
                pdb.log_activity(conn, deal["id"], "opt_out", body[:200])
            # Add to global opt-out registry
            try:
                from opt_out_manager import OptOutManager
                om = OptOutManager()
                om.add_opt_out(phone, reason="replied_stop", channel="sms")
            except Exception:
                pass

        # Cold = no action needed, just log
        elif classification == "cold" and deal:
            pdb.log_activity(conn, deal["id"], "cold_response", body[:200])

    conn.close()

    log_stage("check_responses", True, {
        "total_replies": len(new_replies),
        "hot": len(hot_leads),
        "warm": len(warm_leads),
        "opt_outs": len(opt_outs),
    })

    return {
        "hot": hot_leads,
        "warm": warm_leads,
        "opt_outs": opt_outs,
        "total": len(new_replies),
    }


def stage_digest() -> Dict[str, Any]:
    """Stage 8: Send daily analytics digest to Telegram."""
    try:
        pdb = get_pipeline_db()
        conn = pdb.get_db()

        # Today's activities
        today = datetime.now().strftime("%Y-%m-%d")
        activities = conn.execute(
            "SELECT activity_type, COUNT(*) as cnt FROM activities "
            "WHERE date(created_at) = ? GROUP BY activity_type",
            (today,)
        ).fetchall()
        activity_summary = {r["activity_type"]: r["cnt"] for r in activities}

        # Pipeline stages
        stages = conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM deals "
            "WHERE stage NOT IN ('Lost', 'Opted Out') "
            "GROUP BY stage ORDER BY cnt DESC"
        ).fetchall()
        pipeline = {r["stage"]: r["cnt"] for r in stages}

        # Hot leads needing attention
        hot = conn.execute(
            "SELECT company, contact_name FROM deals "
            "WHERE stage = 'Hot Response' AND next_action IS NOT NULL"
        ).fetchall()

        # Tomorrow's scheduled follow-ups
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        followups = conn.execute(
            "SELECT COUNT(*) as cnt FROM outreach_log "
            "WHERE follow_up_date = ?", (tomorrow,)
        ).fetchone()

        conn.close()

        # Format digest
        lines = [f"📊 *PIPELINE DIGEST — {today}*\n"]

        # Stage results from today's loop
        if STAGE_RESULTS:
            ds = STAGE_RESULTS.get("discover_score", {})
            fu = STAGE_RESULTS.get("follow_up", {})
            cr = STAGE_RESULTS.get("check_responses", {})
            lines.append("*Today's Loop:*")
            if ds.get("success"):
                lines.append(f"  Discovered: {ds.get('discovered', 0)} | "
                             f"Outreached: {ds.get('outreached', 0)}")
            if fu.get("success"):
                lines.append(f"  Follow-ups sent: {fu.get('sent', 0)}")
            if cr.get("success"):
                lines.append(f"  Replies: {cr.get('total_replies', 0)} "
                             f"(🔥{cr.get('hot', 0)} warm:{cr.get('warm', 0)} "
                             f"optout:{cr.get('opt_outs', 0)})")
            lines.append("")

        # Hot leads
        if hot:
            lines.append(f"🔥 *Hot Leads ({len(hot)}):*")
            for h in hot:
                lines.append(f"  • {h['company']}"
                             f"{' — ' + h['contact_name'] if h['contact_name'] else ''}")
            lines.append("")

        # Pipeline
        if pipeline:
            pipeline_str = " → ".join(f"{cnt} {stage}" for stage, cnt in pipeline.items())
            lines.append(f"📈 Pipeline: {pipeline_str}")

        # Tomorrow
        if followups and followups["cnt"] > 0:
            lines.append(f"\n📅 Tomorrow: {followups['cnt']} auto follow-ups scheduled")

        message = "\n".join(lines)
        send_telegram(message)
        log_stage("digest", True, {"message_length": len(message)})
        return {"sent": True}

    except Exception as e:
        logger.error(f"Digest failed: {e}\n{traceback.format_exc()}")
        log_stage("digest", False, {"error": str(e)})
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------

HOT_SIGNALS = [
    "interested", "let's talk", "lets talk", "tell me more", "sounds good",
    "i'd like to", "id like to", "set up a time", "when are you free",
    "can we chat", "call me", "send me info", "how much", "pricing",
    "what do you charge", "yes please", "absolutely", "i'm in", "im in",
    "let's do it", "love to hear more", "schedule",
]

OPT_OUT_SIGNALS = [
    "stop", "unsubscribe", "remove me", "opt out", "optout", "don't text",
    "dont text", "don't contact", "dont contact", "take me off", "no more",
    "leave me alone", "not interested stop", "remove my number",
]

COLD_SIGNALS = [
    "no thanks", "not interested", "no thank you", "pass", "not right now",
    "we're good", "were good", "already have", "don't need", "dont need",
]


def classify_response(text: str) -> str:
    """Classify a response as hot, warm, cold, or opt_out."""
    lower = text.lower().strip()

    # Opt-out takes priority (compliance)
    for signal in OPT_OUT_SIGNALS:
        if signal in lower:
            return "opt_out"

    # Hot signals
    for signal in HOT_SIGNALS:
        if signal in lower:
            return "hot"

    # Cold signals
    for signal in COLD_SIGNALS:
        if signal in lower:
            return "cold"

    # Default: warm (replied but unclear intent)
    return "warm"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_gmail_replies() -> List[Dict]:
    """Check Gmail for replies to outreach emails. Returns list of reply dicts.

    Self-contained — uses Google API directly via shared token.json.
    Does NOT import from personal-assistant tower (tower independence).
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = REPO_ROOT / "token.json"
        if not token_path.exists():
            return []

        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(
            userId="me", q="is:unread in:inbox newer_than:1d", maxResults=20
        ).execute()

        messages = results.get("messages", [])
        replies = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata"
            ).execute()
            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            subj = headers.get("Subject", "").lower()
            if any(kw in subj for kw in ["re:", "automation", "follow-up", "ai services"]):
                replies.append({
                    "from": headers.get("From", ""),
                    "body": msg_data.get("snippet", ""),
                    "channel": "email",
                    "date": headers.get("Date", ""),
                })
        return replies
    except Exception as e:
        logger.warning(f"Gmail reply check failed: {e}")
        return []


def _find_deal_by_contact(conn, phone_or_email: str) -> Optional[dict]:
    """Find a deal in pipeline by phone or email."""
    if not phone_or_email:
        return None
    clean = phone_or_email.strip().replace(" ", "")
    row = conn.execute(
        "SELECT * FROM deals WHERE contact_phone LIKE ? OR contact_email LIKE ? "
        "ORDER BY updated_at DESC LIMIT 1",
        (f"%{clean[-10:]}%", f"%{phone_or_email}%")
    ).fetchone()
    return dict(row) if row else None


def _process_cross_tower_handoffs():
    """Check for deals that need cross-tower action.

    - Won coaching deals → request fitness-influencer content generation
    - Scheduling deals → request personal-assistant Calendly email
    """
    try:
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        from tower_protocol import request_coaching_content, request_calendly_email

        pdb = get_pipeline_db()
        conn = pdb.get_db()

        # Coaching leads that reached "Won" — need onboarding content
        won_coaching = conn.execute(
            "SELECT id, company, contact_name FROM deals "
            "WHERE tower = 'fitness-coaching' AND stage = 'Won' "
            "AND next_action IS NULL"
        ).fetchall()
        for deal in won_coaching:
            request_coaching_content(deal["id"], deal.get("contact_name", deal["company"]))
            pdb.update_deal(conn, deal["id"], next_action="content_requested")
            logger.info(f"Coaching content requested for: {deal['company']}")

        # Scheduling deals — need Calendly email
        scheduling = conn.execute(
            "SELECT id, company, contact_email FROM deals "
            "WHERE next_action = 'send_calendly' AND contact_email IS NOT NULL"
        ).fetchall()
        for deal in scheduling:
            request_calendly_email(deal["id"], deal["contact_email"], deal["company"])
            pdb.update_deal(conn, deal["id"], next_action="calendly_sent")
            logger.info(f"Calendly email requested for: {deal['company']}")

        conn.close()

        total = len(won_coaching) + len(scheduling)
        if total:
            logger.info(f"Cross-tower: {len(won_coaching)} coaching + {len(scheduling)} scheduling handoffs")
        else:
            logger.info("Cross-tower: no handoffs needed")

    except Exception as e:
        logger.warning(f"Cross-tower handoff check failed: {e}")


def show_status():
    """Show current pipeline status."""
    pdb = get_pipeline_db()
    conn = pdb.get_db()

    stages = conn.execute(
        "SELECT stage, COUNT(*) as cnt FROM deals GROUP BY stage ORDER BY cnt DESC"
    ).fetchall()

    recent = conn.execute(
        "SELECT company, stage, updated_at FROM deals ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()

    conn.close()

    print("\n📊 Pipeline Status\n")
    print("Stage Distribution:")
    for r in stages:
        print(f"  {r['cnt']:>4}  {r['stage']}")
    print(f"\nRecent Deals:")
    for r in recent:
        print(f"  {r['updated_at'][:10]}  {r['stage']:<20}  {r['company']}")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_full_loop(dry_run: bool = True):
    """Run the complete 8-stage acquisition loop."""
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info(f"\n{'='*60}")
    logger.info(f"DAILY LOOP — {mode} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"{'='*60}\n")

    # Stage 0: Standardization check (non-blocking)
    logger.info("▶ Stage 0: CLAUDE.md compliance check")
    try:
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        from standardization_enforcer import run_all_checks, send_alert
        enforcer_result = run_all_checks()
        if enforcer_result["compliant"]:
            log_stage("compliance", True, {"violations": 0})
        else:
            log_stage("compliance", True, {"violations": enforcer_result["violation_count"]})
            logger.warning(f"CLAUDE.md violations: {enforcer_result['violation_count']}")
            send_alert(enforcer_result)
    except Exception as e:
        logger.warning(f"Compliance check skipped: {e}")

    # Stage 1-3: Discover, score, enrich, outreach (Touch 1)
    logger.info("\n▶ Stages 1-4: Discover → Score → Enrich → Outreach")
    stage_discover_and_score(dry_run=dry_run)

    # Stage 5-6: Check responses
    logger.info("\n▶ Stages 5-6: Check responses → Classify")
    stage_check_responses()

    # Stage 7: Follow-up sequences
    logger.info("\n▶ Stage 7: Follow-up sequences")
    stage_follow_up(dry_run=dry_run)

    # Stage 7b: Email sequences (Gmail API)
    logger.info("\n▶ Stage 7b: Email sequences")
    stage_email_sequences(dry_run=dry_run)

    # Stage 8a: Cross-tower handoffs (coaching leads → fitness-influencer)
    logger.info("\n▶ Stage 8a: Cross-tower handoffs")
    try:
        _process_cross_tower_handoffs()
    except Exception as e:
        logger.warning(f"Cross-tower handoffs skipped: {e}")

    # Stage 8: Daily digest
    logger.info("\n▶ Stage 8: Daily digest")
    stage_digest()

    # Stage 9: Autonomous tower/project detection (non-critical, best-effort)
    logger.info("\n▶ Stage 9: Tower/project signal detection")
    try:
        sys.path.insert(0, str(REPO_ROOT / "execution"))
        from autonomous_tower_manager import check_and_propose
        result = check_and_propose(dry_run=dry_run)
        log_stage("tower_signals", True, result)
    except Exception as e:
        logger.warning(f"Tower signal detection skipped: {e}")
        log_stage("tower_signals", True, {"skipped": str(e)})

    # Summary + self-monitoring
    successes = sum(1 for r in STAGE_RESULTS.values() if r.get("success"))
    total = len(STAGE_RESULTS)
    logger.info(f"\n{'='*60}")
    logger.info(f"DAILY LOOP COMPLETE: {successes}/{total} stages succeeded")
    logger.info(f"{'='*60}\n")

    record_run_health(STAGE_RESULTS)

    # Auto-save after successful run (safe — only tracked files, no secrets)
    if not dry_run and successes == total:
        try:
            sys.path.insert(0, str(REPO_ROOT / "execution"))
            from safe_git_save import safe_save
            save_result = safe_save(
                message=f"auto: daily loop {successes}/{total} — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
            if save_result.get("saved"):
                logger.info(f"Auto-save: {save_result.get('files', 0)} files committed")
        except Exception as e:
            logger.warning(f"Auto-save skipped: {e}")


def record_visit_outcome(deal_id: int, outcome: str, notes: str = ""):
    """Record the outcome of a scheduled visit or call.

    Usage from phone/terminal:
        python -m src.daily_loop record --deal 42 --outcome meeting_booked --notes "Call back Thursday"

    Outcomes: no_show, conversation, meeting_booked, proposal_sent, client_won, callback, not_interested
    """
    pdb = get_pipeline_db()
    conn = pdb.get_db()

    deal = conn.execute("SELECT company FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not deal:
        print(f"Deal #{deal_id} not found")
        conn.close()
        return

    pdb.log_scheduled_task(conn, deal_id, "manual_visit", deal["company"])
    # Get the ID of what we just logged
    last_id = conn.execute("SELECT MAX(id) FROM scheduled_outcomes").fetchone()[0]
    pdb.record_outcome(conn, last_id, completed=True, outcome=outcome,
                       resulted_in=outcome, notes=notes)
    conn.close()

    print(f"✓ Recorded: Deal #{deal_id} ({deal['company']}) → {outcome}")
    if notes:
        print(f"  Notes: {notes}")


def main():
    parser = argparse.ArgumentParser(description="Lead Generation Daily Loop")
    parser.add_argument("command", choices=["full", "check-responses", "digest", "status", "record"],
                        help="Which operation to run")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Preview without sending (default for full loop)")
    parser.add_argument("--for-real", action="store_true", default=False,
                        help="Actually send outreach")
    parser.add_argument("--deal", type=int, help="Deal ID (for record command)")
    parser.add_argument("--outcome", help="Outcome: no_show, conversation, meeting_booked, proposal_sent, client_won, callback, not_interested")
    parser.add_argument("--notes", default="", help="Notes about the outcome")

    args = parser.parse_args()
    dry_run = not args.for_real

    if args.command == "full":
        run_full_loop(dry_run=dry_run)
    elif args.command == "check-responses":
        stage_check_responses()
    elif args.command == "digest":
        stage_digest()
    elif args.command == "status":
        show_status()
    elif args.command == "record":
        if not args.deal or not args.outcome:
            print("Usage: python -m src.daily_loop record --deal 42 --outcome meeting_booked")
            return
        record_visit_outcome(args.deal, args.outcome, args.notes)


if __name__ == "__main__":
    main()
