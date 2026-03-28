#!/usr/bin/env python3
"""
Coaching Client Manager — Client lifecycle for the fitness-coaching tower.

Handles:
  - Client onboarding (payment → welcome → questionnaire → workout delivery)
  - Weekly check-ins (Monday requests → responses → program adjustments)
  - Workout generation and delivery
  - Cancellation flow

Integrations:
  - n8n workflows: Coaching-Payment-Welcome, Coaching-Monday-Checkin, Coaching-Cancellation-Exit
  - branded_pdf_engine.py: Generates workout PDFs
  - pipeline_db.py: Tracks deals and activities

Usage:
    python execution/coaching_client_manager.py onboard --email test@example.com --name "John Doe"
    python execution/coaching_client_manager.py generate-workout --client-id 1
    python execution/coaching_client_manager.py checkin --client-id 1
    python execution/coaching_client_manager.py status
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

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
logger = logging.getLogger("coaching_manager")

# Import dependencies
from pipeline_db import get_db, log_activity, TOWERS
from coaching_schema import create_coaching_tables


# ── N8N Webhook Triggers ─────────────────────────────────────────────────────

N8N_BASE_URL = os.getenv("N8N_WEBHOOK_URL", "https://n8n.marceausolutions.com/webhook")

def trigger_n8n_workflow(workflow_name: str, data: dict) -> dict:
    """Trigger an n8n webhook workflow."""
    webhook_paths = {
        "Coaching-Payment-Welcome": "/coaching-welcome",
        "Coaching-Monday-Checkin": "/coaching-checkin",
        "Coaching-Cancellation-Exit": "/coaching-cancel",
        "Coaching-Workout-Delivery": "/coaching-workout",
    }
    
    path = webhook_paths.get(workflow_name)
    if not path:
        logger.warning(f"Unknown workflow: {workflow_name}")
        return {"error": f"Unknown workflow: {workflow_name}"}
    
    url = f"{N8N_BASE_URL}{path}"
    
    try:
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            logger.info(f"n8n workflow {workflow_name} triggered: {result}")
            return result
    except Exception as e:
        logger.error(f"n8n trigger failed for {workflow_name}: {e}")
        return {"error": str(e)}


def send_telegram(message: str):
    """Send notification to William via Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
    if not bot_token:
        return
    try:
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")


# ── Client Lifecycle ─────────────────────────────────────────────────────────

def onboard_client(
    name: str,
    email: str,
    phone: str = None,
    goal: str = "general fitness",
    experience: str = "intermediate",
    equipment: str = "full gym",
    days_per_week: int = 4,
    monthly_rate: float = 197.0,
    plan_type: str = "monthly",
    stripe_customer_id: str = None,
    stripe_subscription_id: str = None,
    deal_id: int = None,
    dry_run: bool = False
) -> dict:
    """
    Onboard a new coaching client.
    
    Flow:
    1. Create client record in coaching_clients
    2. Trigger n8n welcome workflow (sends welcome email + questionnaire link)
    3. Log activity in pipeline
    4. Send Telegram notification
    """
    conn = get_db()
    create_coaching_tables(conn)
    
    # Check for duplicate
    existing = conn.execute(
        "SELECT id FROM coaching_clients WHERE email = ?", (email,)
    ).fetchone()
    if existing:
        conn.close()
        return {"error": f"Client with email {email} already exists", "client_id": existing["id"]}
    
    if dry_run:
        conn.close()
        logger.info(f"[DRY RUN] Would onboard: {name} <{email}>")
        return {"dry_run": True, "name": name, "email": email}
    
    # Create client record
    start_date = datetime.now().strftime("%Y-%m-%d")
    next_billing = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    cur = conn.execute("""
        INSERT INTO coaching_clients (
            deal_id, name, email, phone, status, plan_type, monthly_rate,
            start_date, next_billing, stripe_customer_id, stripe_subscription_id,
            goal, experience, equipment, days_per_week
        ) VALUES (?, ?, ?, ?, 'onboarding', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        deal_id, name, email, phone, plan_type, monthly_rate,
        start_date, next_billing, stripe_customer_id, stripe_subscription_id,
        goal, experience, equipment, days_per_week
    ))
    client_id = cur.lastrowid
    conn.commit()
    
    # Log activity
    if deal_id:
        log_activity(conn, deal_id, "coaching_onboard", 
                     f"New client: {name}", tower="fitness-coaching")
    
    # Log message
    conn.execute("""
        INSERT INTO coaching_messages (client_id, message_type, channel, subject, n8n_workflow)
        VALUES (?, 'welcome', 'email', 'Welcome to Coaching!', 'Coaching-Payment-Welcome')
    """, (client_id,))
    conn.commit()
    conn.close()
    
    # Trigger n8n welcome workflow
    webhook_data = {
        "client_id": client_id,
        "name": name,
        "email": email,
        "phone": phone,
        "goal": goal,
        "start_date": start_date,
    }
    n8n_result = trigger_n8n_workflow("Coaching-Payment-Welcome", webhook_data)
    
    # Telegram notification
    send_telegram(
        f"💪 *New Coaching Client!*\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Goal: {goal}\n"
        f"Rate: ${monthly_rate}/mo\n\n"
        f"Welcome email sent automatically."
    )
    
    logger.info(f"Client onboarded: {name} (ID: {client_id})")
    return {
        "client_id": client_id,
        "name": name,
        "email": email,
        "status": "onboarding",
        "n8n_result": n8n_result
    }


def activate_client(client_id: int, preferences: dict = None) -> dict:
    """
    Activate a client after questionnaire completion.
    Generates initial workout program.
    """
    conn = get_db()
    create_coaching_tables(conn)
    
    client = conn.execute(
        "SELECT * FROM coaching_clients WHERE id = ?", (client_id,)
    ).fetchone()
    
    if not client:
        conn.close()
        return {"error": f"Client {client_id} not found"}
    
    # Update status and preferences
    prefs_json = json.dumps(preferences) if preferences else None
    conn.execute("""
        UPDATE coaching_clients 
        SET status = 'active', preferences = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (prefs_json, client_id))
    conn.commit()
    
    # Generate initial workout
    workout_result = generate_workout(client_id, conn=conn)
    
    conn.close()
    
    logger.info(f"Client {client_id} activated")
    return {
        "client_id": client_id,
        "status": "active",
        "workout": workout_result
    }


def generate_workout(
    client_id: int,
    program_name: str = None,
    weeks: int = 4,
    conn = None,
    deliver: bool = True
) -> dict:
    """
    Generate a workout program PDF for a client.
    Uses branded_pdf_engine with workout_program template.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        create_coaching_tables(conn)
        close_conn = True
    
    client = conn.execute(
        "SELECT * FROM coaching_clients WHERE id = ?", (client_id,)
    ).fetchone()
    
    if not client:
        if close_conn:
            conn.close()
        return {"error": f"Client {client_id} not found"}
    
    # Import workout generator and PDF engine
    try:
        from workout_plan_generator import WorkoutPlanGenerator
        from branded_pdf_engine import BrandedPDFEngine
    except ImportError as e:
        if close_conn:
            conn.close()
        return {"error": f"Import failed: {e}"}
    
    # Generate workout data
    generator = WorkoutPlanGenerator()
    
    goal_map = {
        "muscle gain": "muscle_gain",
        "weight loss": "endurance",
        "strength": "strength",
        "general fitness": "muscle_gain",
        "toning": "muscle_gain"
    }
    goal_key = goal_map.get(client["goal"].lower(), "muscle_gain")
    
    try:
        raw_plan = generator.generate_plan(
            goal=goal_key,
            experience=client["experience"] or "intermediate",
            days_per_week=client["days_per_week"] or 4,
            equipment=client["equipment"] or "full_gym"
        )
        
        # Convert generator output to workout_template format
        schedule = []
        for day in raw_plan.get("weekly_schedule", []):
            exercises = []
            for ex in day.get("exercises", []):
                exercises.append({
                    "name": ex.get("exercise", "Exercise"),
                    "sets": ex.get("sets", 3),
                    "reps": ex.get("reps", "8-12"),
                    "rest_seconds": 90,
                    "notes": ex.get("muscle_group", "")
                })
            
            schedule.append({
                "day_number": day.get("day", 1),
                "day_name": f"Day {day.get('day', 1)}",
                "focus": day.get("focus", "Full Body"),
                "warmup": raw_plan.get("notes", {}).get("warm_up", "5-10 min light cardio"),
                "cooldown": raw_plan.get("notes", {}).get("cool_down", "5 min stretching"),
                "exercises": exercises
            })
        
        workout_data = {
            "schedule": schedule,
            "program_notes": raw_plan.get("notes", {})
        }
        
    except Exception as e:
        logger.error(f"Workout generation failed: {e}")
        # Fallback to basic structure
        workout_data = {
            "program_name": f"{client['goal'].title()} Program",
            "schedule": [],
            "program_notes": {"note": "Custom program - contact coach for details"}
        }
    
    # Build PDF data
    if not program_name:
        program_name = f"{client['goal'].title()} Program - Week {client['program_week'] or 1}"
    
    pdf_data = {
        "program_name": program_name,
        "client_name": client["name"],
        "goal": client["goal"],
        "experience_level": client["experience"],
        "equipment": client["equipment"],
        "days_per_week": client["days_per_week"],
        "start_date": datetime.now().strftime("%B %d, %Y"),
        "coach_note": f"This {weeks}-week program is customized for your {client['goal']} goals. "
                      f"Focus on progressive overload and proper form. "
                      f"Reply to your weekly check-in with any questions!",
        "schedule": workout_data.get("schedule", []),
        "program_notes": workout_data.get("program_notes", {})
    }
    
    # Generate PDF
    pdf_engine = BrandedPDFEngine()
    output_dir = REPO_ROOT / "output" / "coaching-pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = client["name"].replace(" ", "_").lower()
    pdf_filename = f"workout_{safe_name}_{timestamp}.pdf"
    pdf_path = str(output_dir / pdf_filename)
    
    try:
        pdf_engine.generate_to_file("workout_program", pdf_data, pdf_path)
        logger.info(f"Generated PDF: {pdf_path}")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        pdf_path = None
    
    # Save workout record
    cur = conn.execute("""
        INSERT INTO coaching_workouts (
            client_id, program_name, program_data, pdf_path, goal, weeks, days_per_week
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id, program_name, json.dumps(pdf_data), pdf_path,
        client["goal"], weeks, client["days_per_week"]
    ))
    workout_id = cur.lastrowid
    
    # Update client's current program
    conn.execute("""
        UPDATE coaching_clients 
        SET current_program_id = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (workout_id, client_id))
    conn.commit()
    
    # Deliver via n8n
    if deliver and pdf_path:
        trigger_n8n_workflow("Coaching-Workout-Delivery", {
            "client_id": client_id,
            "name": client["name"],
            "email": client["email"],
            "pdf_path": pdf_path,
            "program_name": program_name
        })
        
        conn.execute("""
            UPDATE coaching_workouts SET sent_at = datetime('now') WHERE id = ?
        """, (workout_id,))
        conn.commit()
    
    if close_conn:
        conn.close()
    
    return {
        "workout_id": workout_id,
        "pdf_path": pdf_path,
        "program_name": program_name,
        "delivered": deliver and pdf_path is not None
    }


def request_checkin(client_id: int, week_of: str = None) -> dict:
    """
    Send a check-in request to a client.
    Called by coaching_daily_loop on Mondays.
    """
    conn = get_db()
    create_coaching_tables(conn)
    
    client = conn.execute(
        "SELECT * FROM coaching_clients WHERE id = ? AND status = 'active'",
        (client_id,)
    ).fetchone()
    
    if not client:
        conn.close()
        return {"error": f"Active client {client_id} not found"}
    
    if not week_of:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        week_of = monday.strftime("%Y-%m-%d")
    
    # Check if already requested
    existing = conn.execute(
        "SELECT id FROM coaching_checkins WHERE client_id = ? AND week_of = ?",
        (client_id, week_of)
    ).fetchone()
    
    if existing:
        conn.close()
        return {"already_requested": True, "checkin_id": existing["id"]}
    
    # Create check-in record
    cur = conn.execute("""
        INSERT INTO coaching_checkins (client_id, week_of)
        VALUES (?, ?)
    """, (client_id, week_of))
    checkin_id = cur.lastrowid
    
    # Log message
    conn.execute("""
        INSERT INTO coaching_messages (client_id, message_type, channel, subject, n8n_workflow)
        VALUES (?, 'checkin_request', 'email', 'Weekly Check-In', 'Coaching-Monday-Checkin')
    """, (client_id,))
    conn.commit()
    conn.close()
    
    # Trigger n8n
    trigger_n8n_workflow("Coaching-Monday-Checkin", {
        "client_id": client_id,
        "checkin_id": checkin_id,
        "name": client["name"],
        "email": client["email"],
        "week_of": week_of,
        "program_week": client["program_week"]
    })
    
    logger.info(f"Check-in requested for client {client_id}, week {week_of}")
    return {
        "checkin_id": checkin_id,
        "client_id": client_id,
        "week_of": week_of
    }


def process_checkin_response(
    checkin_id: int,
    workouts_completed: int,
    energy_level: int = None,
    soreness_level: int = None,
    weight: float = None,
    notes: str = None
) -> dict:
    """Record a client's check-in response."""
    conn = get_db()
    create_coaching_tables(conn)
    
    conn.execute("""
        UPDATE coaching_checkins 
        SET workouts_completed = ?, energy_level = ?, soreness_level = ?,
            weight = ?, notes = ?, submitted_at = datetime('now')
        WHERE id = ?
    """, (workouts_completed, energy_level, soreness_level, weight, notes, checkin_id))
    
    # Get client info
    checkin = conn.execute(
        "SELECT client_id FROM coaching_checkins WHERE id = ?", (checkin_id,)
    ).fetchone()
    
    if checkin:
        # Update streak
        conn.execute("""
            UPDATE coaching_clients 
            SET last_checkin_date = date('now'),
                checkin_streak = checkin_streak + 1,
                updated_at = datetime('now')
            WHERE id = ?
        """, (checkin["client_id"],))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Check-in {checkin_id} response recorded")
    return {"checkin_id": checkin_id, "status": "submitted"}


def cancel_client(client_id: int, reason: str = None) -> dict:
    """Handle client cancellation."""
    conn = get_db()
    create_coaching_tables(conn)
    
    client = conn.execute(
        "SELECT * FROM coaching_clients WHERE id = ?", (client_id,)
    ).fetchone()
    
    if not client:
        conn.close()
        return {"error": f"Client {client_id} not found"}
    
    conn.execute("""
        UPDATE coaching_clients 
        SET status = 'cancelled', updated_at = datetime('now')
        WHERE id = ?
    """, (client_id,))
    
    conn.execute("""
        INSERT INTO coaching_messages (client_id, message_type, channel, subject, n8n_workflow)
        VALUES (?, 'cancellation', 'email', 'We''re sorry to see you go', 'Coaching-Cancellation-Exit')
    """, (client_id,))
    conn.commit()
    
    # Trigger n8n exit workflow
    trigger_n8n_workflow("Coaching-Cancellation-Exit", {
        "client_id": client_id,
        "name": client["name"],
        "email": client["email"],
        "reason": reason,
        "months_active": _months_between(client["start_date"], datetime.now().strftime("%Y-%m-%d"))
    })
    
    # Notify William
    send_telegram(
        f"⚠️ *Client Cancellation*\n\n"
        f"Name: {client['name']}\n"
        f"Email: {client['email']}\n"
        f"Reason: {reason or 'Not provided'}"
    )
    
    conn.close()
    logger.info(f"Client {client_id} cancelled")
    return {"client_id": client_id, "status": "cancelled"}


def _months_between(start: str, end: str) -> int:
    """Calculate months between two YYYY-MM-DD dates."""
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        return (e.year - s.year) * 12 + (e.month - s.month)
    except:
        return 0


# ── Status / Reporting ───────────────────────────────────────────────────────

def get_coaching_status() -> dict:
    """Get full coaching tower status."""
    conn = get_db()
    create_coaching_tables(conn)
    
    # Active clients
    clients = conn.execute("""
        SELECT id, name, email, status, goal, program_week, last_checkin_date, monthly_rate
        FROM coaching_clients
        ORDER BY status, name
    """).fetchall()
    
    # Stats
    active_count = sum(1 for c in clients if c["status"] == "active")
    mrr = sum(c["monthly_rate"] for c in clients if c["status"] == "active")
    
    # This week's check-ins
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    monday_str = monday.strftime("%Y-%m-%d")
    
    pending_checkins = conn.execute("""
        SELECT ci.id, cc.name, cc.email
        FROM coaching_checkins ci
        JOIN coaching_clients cc ON ci.client_id = cc.id
        WHERE ci.week_of = ? AND ci.submitted_at IS NULL
    """, (monday_str,)).fetchall()
    
    # Recent workouts
    recent_workouts = conn.execute("""
        SELECT cw.program_name, cc.name, cw.created_at, cw.sent_at
        FROM coaching_workouts cw
        JOIN coaching_clients cc ON cw.client_id = cc.id
        ORDER BY cw.created_at DESC
        LIMIT 5
    """).fetchall()
    
    conn.close()
    
    return {
        "clients": [dict(c) for c in clients],
        "active_count": active_count,
        "mrr": mrr,
        "pending_checkins": [dict(c) for c in pending_checkins],
        "recent_workouts": [dict(w) for w in recent_workouts]
    }


def print_status():
    """Print formatted status to console."""
    status = get_coaching_status()
    
    print("\n💪 Fitness Coaching Tower Status")
    print("=" * 50)
    print(f"Active Clients: {status['active_count']}")
    print(f"MRR: ${status['mrr']:,.2f}")
    
    print("\n📋 Clients:")
    for c in status["clients"]:
        emoji = {"active": "✅", "onboarding": "🔄", "paused": "⏸️", "cancelled": "❌"}.get(c["status"], "❓")
        print(f"  {emoji} {c['name']} — {c['goal']} (Week {c['program_week'] or 1})")
    
    if status["pending_checkins"]:
        print(f"\n⏳ Pending Check-ins ({len(status['pending_checkins'])}):")
        for ci in status["pending_checkins"]:
            print(f"  • {ci['name']}")
    
    if status["recent_workouts"]:
        print("\n📄 Recent Workouts:")
        for w in status["recent_workouts"]:
            sent = "✓ sent" if w["sent_at"] else "pending"
            print(f"  • {w['name']}: {w['program_name']} ({sent})")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Coaching Client Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Onboard
    onboard_p = subparsers.add_parser("onboard", help="Onboard new client")
    onboard_p.add_argument("--name", required=True)
    onboard_p.add_argument("--email", required=True)
    onboard_p.add_argument("--phone", default=None)
    onboard_p.add_argument("--goal", default="general fitness")
    onboard_p.add_argument("--experience", default="intermediate")
    onboard_p.add_argument("--equipment", default="full gym")
    onboard_p.add_argument("--days", type=int, default=4)
    onboard_p.add_argument("--rate", type=float, default=197.0)
    onboard_p.add_argument("--dry-run", action="store_true")
    
    # Generate workout
    workout_p = subparsers.add_parser("generate-workout", help="Generate workout PDF")
    workout_p.add_argument("--client-id", type=int, required=True)
    workout_p.add_argument("--name", default=None, help="Custom program name")
    workout_p.add_argument("--weeks", type=int, default=4)
    workout_p.add_argument("--no-deliver", action="store_true")
    
    # Check-in
    checkin_p = subparsers.add_parser("checkin", help="Request check-in")
    checkin_p.add_argument("--client-id", type=int, required=True)
    
    # Cancel
    cancel_p = subparsers.add_parser("cancel", help="Cancel client")
    cancel_p.add_argument("--client-id", type=int, required=True)
    cancel_p.add_argument("--reason", default=None)
    
    # Status
    subparsers.add_parser("status", help="Show coaching status")
    
    args = parser.parse_args()
    
    if args.command == "onboard":
        result = onboard_client(
            name=args.name, email=args.email, phone=args.phone,
            goal=args.goal, experience=args.experience, equipment=args.equipment,
            days_per_week=args.days, monthly_rate=args.rate, dry_run=args.dry_run
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "generate-workout":
        result = generate_workout(
            client_id=args.client_id,
            program_name=args.name,
            weeks=args.weeks,
            deliver=not args.no_deliver
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "checkin":
        result = request_checkin(args.client_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "cancel":
        result = cancel_client(args.client_id, args.reason)
        print(json.dumps(result, indent=2))
    
    elif args.command == "status":
        print_status()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
