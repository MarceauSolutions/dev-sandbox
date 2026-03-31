#!/usr/bin/env python3
"""
Coaching Daily Loop — Autonomous operations for the fitness-coaching tower.

Schedule (via cron):
  Monday 8am ET    — Send weekly check-in requests to all active clients
  Wednesday 8am    — Send check-in reminders to non-responders
  Friday 8am       — Generate new programs for clients entering new weeks
  Daily 9pm        — Evening digest to William

Operations:
  1. CHECKIN      — Monday: Request check-ins from all active clients
  2. REMINDER     — Wednesday: Remind clients who haven't responded
  3. PROGRESS     — Friday: Advance program weeks, generate new workouts if needed
  4. DIGEST       — Daily: Send summary to Telegram

Usage:
    python execution/coaching_daily_loop.py checkins    # Monday check-in requests
    python execution/coaching_daily_loop.py reminders   # Wednesday reminders
    python execution/coaching_daily_loop.py progress    # Friday program updates
    python execution/coaching_daily_loop.py digest      # Daily digest
    python execution/coaching_daily_loop.py full        # Run all applicable for today
    python execution/coaching_daily_loop.py --dry-run full
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))
sys.path.insert(0, str(REPO_ROOT / "projects" / "fitness-influencer" / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("coaching_daily_loop")

from pipeline_db import get_db
from coaching_schema import create_coaching_tables, get_coaching_stats
from coaching_client_manager import (
    request_checkin, generate_workout, send_telegram, trigger_n8n_workflow
)


# ── Stage 1: Monday Check-ins ─────────────────────────────────────────────────

def stage_checkins(dry_run: bool = False) -> dict:
    """Send weekly check-in requests to all active clients."""
    logger.info("▶ Stage: CHECKINS (Monday)")
    
    conn = get_db()
    create_coaching_tables(conn)
    
    # Get all active clients
    clients = conn.execute("""
        SELECT id, name, email, program_week
        FROM coaching_clients
        WHERE status = 'active'
    """).fetchall()
    
    # Get this week's Monday
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_of = monday.strftime("%Y-%m-%d")
    
    results = {"requested": 0, "skipped": 0, "errors": 0}
    
    for client in clients:
        # Check if already requested
        existing = conn.execute(
            "SELECT id FROM coaching_checkins WHERE client_id = ? AND week_of = ?",
            (client["id"], week_of)
        ).fetchone()
        
        if existing:
            results["skipped"] += 1
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would request check-in for: {client['name']}")
            results["requested"] += 1
            continue
        
        try:
            result = request_checkin(client["id"], week_of)
            if "error" not in result:
                results["requested"] += 1
            else:
                results["errors"] += 1
                logger.error(f"Check-in request failed for {client['name']}: {result['error']}")
        except Exception as e:
            results["errors"] += 1
            logger.error(f"Check-in request exception for {client['name']}: {e}")
    
    conn.close()
    
    logger.info(f"Check-ins: {results['requested']} requested, {results['skipped']} skipped, {results['errors']} errors")
    return results


# ── Stage 2: Wednesday Reminders ──────────────────────────────────────────────

def stage_reminders(dry_run: bool = False) -> dict:
    """Send reminders to clients who haven't submitted check-ins."""
    logger.info("▶ Stage: REMINDERS (Wednesday)")
    
    conn = get_db()
    create_coaching_tables(conn)
    
    # Get this week's Monday
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_of = monday.strftime("%Y-%m-%d")
    
    # Find pending check-ins
    pending = conn.execute("""
        SELECT ci.id as checkin_id, ci.client_id, cc.name, cc.email, cc.phone
        FROM coaching_checkins ci
        JOIN coaching_clients cc ON ci.client_id = cc.id
        WHERE ci.week_of = ? AND ci.submitted_at IS NULL AND cc.status = 'active'
    """, (week_of,)).fetchall()
    
    results = {"reminders_sent": 0, "errors": 0}
    
    for p in pending:
        if dry_run:
            logger.info(f"[DRY RUN] Would remind: {p['name']}")
            results["reminders_sent"] += 1
            continue
        
        try:
            # Trigger n8n reminder workflow (reuse checkin workflow with reminder flag)
            trigger_n8n_workflow("Coaching-Monday-Checkin", {
                "client_id": p["client_id"],
                "checkin_id": p["checkin_id"],
                "name": p["name"],
                "email": p["email"],
                "week_of": week_of,
                "is_reminder": True
            })
            
            # Log the reminder
            conn.execute("""
                INSERT INTO coaching_messages (client_id, message_type, channel, subject, n8n_workflow)
                VALUES (?, 'checkin_reminder', 'email', 'Reminder: Weekly Check-In', 'Coaching-Monday-Checkin')
            """, (p["client_id"],))
            conn.commit()
            
            results["reminders_sent"] += 1
            logger.info(f"Reminder sent to: {p['name']}")
        except Exception as e:
            results["errors"] += 1
            logger.error(f"Reminder failed for {p['name']}: {e}")
    
    conn.close()
    
    if not pending:
        logger.info("No pending check-ins — all clients responded!")
    else:
        logger.info(f"Reminders: {results['reminders_sent']} sent, {results['errors']} errors")
    
    return results


# ── Stage 3: Friday Progress ──────────────────────────────────────────────────

def stage_progress(dry_run: bool = False) -> dict:
    """
    Advance program weeks and generate new workouts for clients who need them.
    
    Logic:
    - Clients who submitted check-ins advance to next week
    - Every 4 weeks, generate a fresh program
    - Clients who missed check-ins get flagged
    """
    logger.info("▶ Stage: PROGRESS (Friday)")
    
    conn = get_db()
    create_coaching_tables(conn)
    
    # Get this week's Monday
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_of = monday.strftime("%Y-%m-%d")
    
    results = {
        "advanced": 0,
        "new_programs": 0,
        "missed": 0,
        "errors": 0
    }
    
    # Get all active clients
    clients = conn.execute("""
        SELECT cc.id, cc.name, cc.email, cc.program_week, cc.missed_checkins,
               ci.submitted_at as checkin_submitted
        FROM coaching_clients cc
        LEFT JOIN coaching_checkins ci ON cc.id = ci.client_id AND ci.week_of = ?
        WHERE cc.status = 'active'
    """, (week_of,)).fetchall()
    
    for client in clients:
        client_id = client["id"]
        current_week = client["program_week"] or 1
        
        if client["checkin_submitted"]:
            # Client submitted — advance week
            new_week = current_week + 1
            
            if dry_run:
                logger.info(f"[DRY RUN] Would advance {client['name']} to week {new_week}")
                results["advanced"] += 1
                
                if new_week > 4 and (new_week - 1) % 4 == 0:
                    results["new_programs"] += 1
                continue
            
            conn.execute("""
                UPDATE coaching_clients 
                SET program_week = ?, missed_checkins = 0, updated_at = datetime('now')
                WHERE id = ?
            """, (new_week, client_id))
            conn.commit()
            results["advanced"] += 1
            
            # Generate new program every 4 weeks
            if new_week > 4 and (new_week - 1) % 4 == 0:
                try:
                    generate_workout(client_id, weeks=4)
                    results["new_programs"] += 1
                    logger.info(f"New program generated for {client['name']}")
                except Exception as e:
                    results["errors"] += 1
                    logger.error(f"Program generation failed for {client['name']}: {e}")
        else:
            # Client missed check-in
            missed_count = (client["missed_checkins"] or 0) + 1
            
            if dry_run:
                logger.info(f"[DRY RUN] Would flag missed check-in for {client['name']} (#{missed_count})")
                results["missed"] += 1
                continue
            
            conn.execute("""
                UPDATE coaching_clients 
                SET missed_checkins = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (missed_count, client_id))
            conn.commit()
            results["missed"] += 1
            
            # Alert on 2+ consecutive misses
            if missed_count >= 2:
                send_telegram(
                    f"⚠️ *Client Attention Needed*\n\n"
                    f"{client['name']} has missed {missed_count} consecutive check-ins.\n"
                    f"Consider reaching out personally."
                )
    
    conn.close()
    
    logger.info(f"Progress: {results['advanced']} advanced, {results['new_programs']} new programs, "
                f"{results['missed']} missed, {results['errors']} errors")
    return results


# ── Stage 4: Daily Digest ─────────────────────────────────────────────────────

def stage_digest(dry_run: bool = False) -> dict:
    """Send daily coaching digest to Telegram."""
    logger.info("▶ Stage: DIGEST")
    
    conn = get_db()
    create_coaching_tables(conn)
    stats = get_coaching_stats(conn)
    
    # Get this week's Monday
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_of = monday.strftime("%Y-%m-%d")
    
    # Pending check-ins
    pending = conn.execute("""
        SELECT cc.name
        FROM coaching_checkins ci
        JOIN coaching_clients cc ON ci.client_id = cc.id
        WHERE ci.week_of = ? AND ci.submitted_at IS NULL AND cc.status = 'active'
    """, (week_of,)).fetchall()
    
    # Recent activity
    recent_messages = conn.execute("""
        SELECT message_type, COUNT(*) as cnt
        FROM coaching_messages
        WHERE sent_at > datetime('now', '-24 hours')
        GROUP BY message_type
    """).fetchall()
    
    conn.close()
    
    # Build message
    day_name = today.strftime("%A")
    lines = [f"💪 *Coaching Digest — {day_name}*\n"]
    
    # Client stats
    by_status = stats.get("clients_by_status", {})
    active = by_status.get("active", 0)
    onboarding = by_status.get("onboarding", 0)
    
    lines.append(f"📊 *Clients:* {active} active, {onboarding} onboarding")
    lines.append(f"💰 *MRR:* ${stats.get('mrr', 0):,.0f}")
    
    # This week's check-ins
    received = stats.get("checkins_received", 0)
    due = stats.get("checkins_due", 0)
    lines.append(f"\n📋 *This Week:* {received}/{due} check-ins received")
    
    if pending:
        names = ", ".join(p["name"] for p in pending[:5])
        if len(pending) > 5:
            names += f" (+{len(pending) - 5} more)"
        lines.append(f"⏳ *Pending:* {names}")
    
    # Recent activity
    if recent_messages:
        activity = ", ".join(f"{r['cnt']} {r['message_type']}" for r in recent_messages)
        lines.append(f"\n📧 *Last 24h:* {activity}")
    
    # Day-specific reminders
    if day_name == "Monday":
        lines.append("\n✅ Check-in requests should have been sent")
    elif day_name == "Wednesday":
        if pending:
            lines.append("\n⚡ Send reminders to non-responders")
    elif day_name == "Friday":
        lines.append("\n📈 Advancing programs for responsive clients")
    
    message = "\n".join(lines)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would send digest:\n{message}")
        return {"dry_run": True, "message": message}
    
    send_telegram(message)
    logger.info("Digest sent")
    return {"sent": True}


# ── Full Loop ─────────────────────────────────────────────────────────────────

def run_full_loop(dry_run: bool = False):
    """Run all applicable stages for today."""
    today = date.today()
    day_name = today.strftime("%A")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"COACHING DAILY LOOP — {day_name} — {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info(f"{'='*60}\n")
    
    results = {}
    
    # Monday: Check-ins
    if day_name == "Monday":
        results["checkins"] = stage_checkins(dry_run)
    
    # Wednesday: Reminders
    elif day_name == "Wednesday":
        results["reminders"] = stage_reminders(dry_run)
    
    # Friday: Progress
    elif day_name == "Friday":
        results["progress"] = stage_progress(dry_run)
    
    # Daily: Digest (always run, even on off-days for visibility)
    results["digest"] = stage_digest(dry_run)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"COACHING LOOP COMPLETE")
    logger.info(f"{'='*60}\n")
    
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Coaching Daily Loop")
    parser.add_argument("command", nargs="?", default="full",
                        choices=["checkins", "reminders", "progress", "digest", "full"],
                        help="Which stage to run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without actions")
    args = parser.parse_args()
    
    if args.command == "checkins":
        result = stage_checkins(args.dry_run)
    elif args.command == "reminders":
        result = stage_reminders(args.dry_run)
    elif args.command == "progress":
        result = stage_progress(args.dry_run)
    elif args.command == "digest":
        result = stage_digest(args.dry_run)
    else:
        result = run_full_loop(args.dry_run)
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
