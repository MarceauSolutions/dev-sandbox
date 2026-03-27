#!/usr/bin/env python3
"""
client_questionnaire.py — Automated SMS Questionnaire System

WHAT: Send multi-question surveys to clients via SMS and collect responses.
WHY: Automate getting client approvals, feedback, and decisions without manual back-and-forth.
INPUT: Client phone, list of questions, questionnaire name
OUTPUT: Collected responses saved to JSON, summary sent to William

SOP COMPLIANCE:
  - SOP 18: TCPA sender ID, opt-out language, quiet hours (via TwilioSMS)
  - SOP 18: Complete the loop — monitors inbox for replies
  - Service Standards: Uses execution/twilio_sms.py shared utility

QUICK USAGE:
  # Send a questionnaire to a client
  python execution/client_questionnaire.py send \\
    --to "+12393985197" \\
    --name "Julia" \\
    --questionnaire boabfit_template_approval

  # Check for responses
  python execution/client_questionnaire.py check --questionnaire boabfit_template_approval

  # List available questionnaires
  python execution/client_questionnaire.py list

  # Create a custom questionnaire interactively
  python execution/client_questionnaire.py create --name "my_survey"

CAPABILITIES:
  - Pre-built questionnaire templates (template approval, onboarding, feedback)
  - Custom questionnaires via JSON
  - Response collection via inbox polling
  - Auto-notification to William when all answers received
  - Multi-client batch surveys

DEPENDENCIES: twilio, python-dotenv
API_KEYS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
"""

import os
import sys
import json
import argparse
import time as time_mod
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load env from dev-sandbox root
ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
load_dotenv(env_path)

# Import shared Twilio utility
from twilio_sms import TwilioSMS

try:
    from twilio.rest import Client
except ImportError:
    print("ERROR: twilio package not installed. pip install twilio")
    sys.exit(1)

# Config
WILLIAM_PHONE = "+12393985676"
DATA_DIR = ROOT / ".tmp" / "questionnaires"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# PRE-BUILT QUESTIONNAIRES
# ============================================================
QUESTIONNAIRES = {
    "boabfit_template_approval": {
        "title": "BOABfit SMS Template Approval",
        "description": "Get Julia's approval on daily check-in message format and content.",
        "intro": (
            "Hey {name}! William here from Marceau Solutions. "
            "I've built your automated daily check-in SMS system for the 6-week program. "
            "I need your input on a few things before we turn it on. "
            "I'll send you a few questions — just reply to each one!"
        ),
        "questions": [
            {
                "id": "sender_name",
                "text": (
                    "Q1: How should the daily texts sign off? Options:\n"
                    "  A) — Julia from BOABFIT\n"
                    "  B) — Julia\n"
                    "  C) — BOABFIT\n"
                    "  D) Something else (just type it!)\n\n"
                    "Reply with A, B, C, or D + your custom sign-off."
                ),
            },
            {
                "id": "message_tone",
                "text": (
                    "Q2: I wrote the daily texts in a super hype girly tone to match your brand. "
                    "Here's a sample:\n\n"
                    "\"BOOTY DAY BABY!! It's lower body BUILD day and we are here to grow "
                    "that peach!! Your legs are gonna be shaking by the end!!\"\n\n"
                    "Is this tone right? Or would you tweak anything? "
                    "Reply YES if good, or tell me how you'd change it."
                ),
            },
            {
                "id": "send_time",
                "text": (
                    "Q3: What time should the daily check-in text go out? "
                    "I have it set for 7:00 AM ET right now.\n\n"
                    "Reply with your preferred time (e.g., '6am', '8am', '7am is good')."
                ),
            },
            {
                "id": "start_date",
                "text": (
                    "Q4: When does the 6-week program officially start? "
                    "I need the date so the system knows Day 1.\n\n"
                    "Reply with the start date (e.g., 'March 15', 'next Monday')."
                ),
            },
            {
                "id": "extra_content",
                "text": (
                    "Q5: Anything else you want in the daily texts? Ideas:\n"
                    "  - Nutrition tips\n"
                    "  - Water/protein reminders\n"
                    "  - Progress photo prompts (weekly)\n"
                    "  - Rest day recovery tips\n\n"
                    "Reply with what you'd like added, or 'looks good' if it's perfect!"
                ),
            },
        ],
        "outro": (
            "That's all the questions! I'll have the system ready to go "
            "based on your answers. Thanks Julia!"
        ),
        "sender_id": "\n\n— William from Marceau Solutions"
    },

    "client_onboarding": {
        "title": "New Client Onboarding Survey",
        "description": "Collect key info from a new client for project setup.",
        "intro": (
            "Hey {name}! William here from Marceau Solutions. "
            "Welcome aboard! I have a few quick questions to get your project rolling. "
            "Just reply to each one as they come in."
        ),
        "questions": [
            {
                "id": "business_name",
                "text": "Q1: What's your business name (exactly as you want it displayed)?",
            },
            {
                "id": "target_audience",
                "text": "Q2: Who is your ideal customer? (age range, interests, location, etc.)",
            },
            {
                "id": "goals",
                "text": "Q3: What are your top 2-3 goals for this project?",
            },
            {
                "id": "timeline",
                "text": "Q4: Any deadlines or dates we need to hit?",
            },
        ],
        "outro": "That's everything! I'll get started and send you updates along the way.",
        "sender_id": "\n\n— William from Marceau Solutions"
    },

    "client_feedback": {
        "title": "Client Satisfaction Check-in",
        "description": "Quick satisfaction survey for existing clients.",
        "intro": (
            "Hey {name}! William here. Quick check-in — I want to make sure "
            "everything's working great for you. Just a few quick questions!"
        ),
        "questions": [
            {
                "id": "satisfaction",
                "text": "Q1: On a scale of 1-10, how happy are you with our work so far?",
            },
            {
                "id": "whats_working",
                "text": "Q2: What's working best for you right now?",
            },
            {
                "id": "improvements",
                "text": "Q3: Anything you wish was different or better?",
            },
            {
                "id": "referral",
                "text": "Q4: Know anyone who could use similar help? No pressure at all!",
            },
        ],
        "outro": "Thanks for the feedback! This really helps me serve you better.",
        "sender_id": "\n\n— William from Marceau Solutions"
    },
}


class ClientQuestionnaire:
    """SMS-based questionnaire system for automated client communication."""

    def __init__(self):
        self.sms = TwilioSMS()
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )

    def send_questionnaire(
        self,
        to: str,
        name: str,
        questionnaire_key: str,
        custom_questionnaire: dict = None,
        delay_between: int = 3,
        dry_run: bool = False
    ) -> dict:
        """
        Send a questionnaire to a client via SMS.

        Args:
            to: Phone number (E.164)
            name: Client's first name
            questionnaire_key: Key from QUESTIONNAIRES or "custom"
            custom_questionnaire: Custom questionnaire dict (if key is "custom")
            delay_between: Seconds between questions
            dry_run: Preview without sending

        Returns:
            Dict with session info for tracking responses
        """
        # Load questionnaire
        if custom_questionnaire:
            q = custom_questionnaire
        elif questionnaire_key in QUESTIONNAIRES:
            q = QUESTIONNAIRES[questionnaire_key]
        else:
            return {"success": False, "error": f"Unknown questionnaire: {questionnaire_key}"}

        sender_id = q.get("sender_id", "\n\n— William from Marceau Solutions")

        # Create tracking session
        session = {
            "id": f"{questionnaire_key}_{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "questionnaire": questionnaire_key,
            "client_name": name,
            "client_phone": to,
            "sent_at": datetime.now().isoformat(),
            "questions_sent": len(q["questions"]),
            "questions": {qn["id"]: {"text": qn["text"], "answer": None} for qn in q["questions"]},
            "status": "sent",
            "answers_received": 0
        }

        print(f"\n{'='*60}")
        print(f"QUESTIONNAIRE: {q['title']}")
        print(f"{'='*60}")
        print(f"To: {name} ({to})")
        print(f"Questions: {len(q['questions'])}")

        if dry_run:
            print(f"\n--- DRY RUN ---\n")
            intro = q["intro"].format(name=name) + sender_id
            print(f"INTRO:\n{intro}\n")
            for qn in q["questions"]:
                print(f"  {qn['text']}{sender_id}\n")
            outro = q["outro"] + sender_id
            print(f"OUTRO:\n{outro}")
            return {"success": True, "dry_run": True, "session": session}

        # Send intro
        intro_msg = q["intro"].format(name=name) + sender_id
        result = self.sms.send_message(to=to, message=intro_msg)
        if not result.get("success"):
            return {"success": False, "error": f"Failed to send intro: {result.get('error')}"}

        time_mod.sleep(delay_between)

        # Send each question
        for i, qn in enumerate(q["questions"], 1):
            msg = qn["text"] + sender_id
            print(f"\n  Sending Q{i}/{len(q['questions'])}...")
            result = self.sms.send_message(to=to, message=msg)
            if not result.get("success"):
                print(f"  Failed Q{i}: {result.get('error')}")
                session["status"] = f"partial_send_failed_at_q{i}"
                break
            if i < len(q["questions"]):
                time_mod.sleep(delay_between)

        # Save session
        session_path = DATA_DIR / f"{session['id']}.json"
        with open(session_path, 'w') as f:
            json.dump(session, f, indent=2)

        print(f"\n  Session saved: {session_path}")
        print(f"  Run 'check' command to collect responses.")

        # Notify William
        william_msg = (
            f"Questionnaire '{q['title']}' sent to {name} ({to}). "
            f"{len(q['questions'])} questions. "
            f"Check responses: python execution/client_questionnaire.py check "
            f"--session {session['id']}"
        )
        self.sms.send_message(to=WILLIAM_PHONE, message=william_msg)

        return {"success": True, "session": session, "session_path": str(session_path)}

    def check_responses(self, session_id: str) -> dict:
        """
        Check for responses to a questionnaire by polling Twilio inbox.

        Args:
            session_id: Session ID from send_questionnaire

        Returns:
            Updated session with any new answers
        """
        session_path = DATA_DIR / f"{session_id}.json"
        if not session_path.exists():
            return {"success": False, "error": f"Session not found: {session_id}"}

        with open(session_path) as f:
            session = json.load(f)

        client_phone = session["client_phone"]
        sent_time = datetime.fromisoformat(session["sent_at"])

        # Fetch inbound messages from this client since the questionnaire was sent
        messages = self.twilio_client.messages.list(
            from_=client_phone,
            to=os.getenv('TWILIO_PHONE_NUMBER'),
            date_sent_after=sent_time.replace(tzinfo=timezone.utc) if sent_time.tzinfo is None
                else sent_time,
            limit=50
        )

        # Filter to only messages AFTER the questionnaire was sent
        replies = []
        for msg in messages:
            body = msg.body.strip()
            # Skip opt-out keywords
            if body.upper() in ['STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT']:
                continue
            replies.append({
                "body": body,
                "timestamp": msg.date_sent.isoformat() if msg.date_sent else None,
                "sid": msg.sid
            })

        # Sort oldest first
        replies.reverse()

        # Map replies to questions (in order)
        unanswered = [qid for qid, q in session["questions"].items() if q["answer"] is None]
        new_answers = 0

        for reply in replies:
            if not unanswered:
                break
            qid = unanswered.pop(0)
            if session["questions"][qid]["answer"] is None:
                session["questions"][qid]["answer"] = reply["body"]
                session["questions"][qid]["answered_at"] = reply["timestamp"]
                session["questions"][qid]["message_sid"] = reply["sid"]
                new_answers += 1
                session["answers_received"] += 1

        # Check if complete
        all_answered = all(q["answer"] is not None for q in session["questions"].values())
        if all_answered:
            session["status"] = "complete"

        # Save updated session
        with open(session_path, 'w') as f:
            json.dump(session, f, indent=2)

        # Print results
        print(f"\n{'='*60}")
        print(f"QUESTIONNAIRE RESPONSES: {session['questionnaire']}")
        print(f"{'='*60}")
        print(f"Client: {session['client_name']} ({session['client_phone']})")
        print(f"Sent: {session['sent_at']}")
        print(f"Status: {session['status']}")
        print(f"Answers: {session['answers_received']}/{session['questions_sent']}")
        print()

        for qid, q in session["questions"].items():
            status = "ANSWERED" if q["answer"] else "WAITING"
            print(f"  [{status}] {qid}:")
            print(f"    Q: {q['text'][:80]}...")
            if q["answer"]:
                print(f"    A: {q['answer']}")
            print()

        # If complete, notify William with summary
        if all_answered and new_answers > 0:
            summary_lines = [
                f"All answers received for '{session['questionnaire']}' from {session['client_name']}!",
                ""
            ]
            for qid, q in session["questions"].items():
                summary_lines.append(f"{qid}: {q['answer']}")
            summary = "\n".join(summary_lines)
            self.sms.send_message(to=WILLIAM_PHONE, message=summary)
            print("  William notified with full summary.")

            # Send outro to client
            q_template = QUESTIONNAIRES.get(session["questionnaire"])
            if q_template and "outro" in q_template:
                outro = q_template["outro"] + q_template.get("sender_id", "")
                self.sms.send_message(to=client_phone, message=outro)

        return {"success": True, "session": session, "new_answers": new_answers}

    def list_sessions(self) -> list:
        """List all questionnaire sessions."""
        sessions = []
        for f in sorted(DATA_DIR.glob("*.json")):
            with open(f) as fh:
                s = json.load(fh)
                sessions.append({
                    "id": s["id"],
                    "questionnaire": s["questionnaire"],
                    "client": s["client_name"],
                    "status": s["status"],
                    "answers": f"{s['answers_received']}/{s['questions_sent']}",
                    "sent_at": s["sent_at"]
                })
        return sessions


def main():
    parser = argparse.ArgumentParser(description="Client SMS Questionnaire System")
    sub = parser.add_subparsers(dest="command", required=True)

    # Send command
    send_parser = sub.add_parser("send", help="Send a questionnaire")
    send_parser.add_argument("--to", required=True, help="Client phone number")
    send_parser.add_argument("--name", required=True, help="Client first name")
    send_parser.add_argument("--questionnaire", required=True,
                             help="Questionnaire key or 'custom'")
    send_parser.add_argument("--custom-file", help="Path to custom questionnaire JSON")
    send_parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    send_parser.add_argument("--delay", type=int, default=3,
                             help="Seconds between questions (default: 3)")

    # Check command
    check_parser = sub.add_parser("check", help="Check for responses")
    check_parser.add_argument("--session", required=True, help="Session ID")

    # List commands
    sub.add_parser("list", help="List available questionnaires")
    sub.add_parser("sessions", help="List all sent questionnaires")

    # Create command
    create_parser = sub.add_parser("create", help="Create a custom questionnaire")
    create_parser.add_argument("--name", required=True, help="Questionnaire name/key")
    create_parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    if args.command == "list":
        print(f"\n{'='*60}")
        print("AVAILABLE QUESTIONNAIRES")
        print(f"{'='*60}")
        for key, q in QUESTIONNAIRES.items():
            print(f"\n  {key}")
            print(f"    {q['title']}")
            print(f"    {q['description']}")
            print(f"    Questions: {len(q['questions'])}")
        return

    if args.command == "sessions":
        cq = ClientQuestionnaire()
        sessions = cq.list_sessions()
        print(f"\n{'='*60}")
        print("QUESTIONNAIRE SESSIONS")
        print(f"{'='*60}")
        if not sessions:
            print("  No sessions yet.")
        for s in sessions:
            print(f"\n  {s['id']}")
            print(f"    Client: {s['client']}")
            print(f"    Status: {s['status']} ({s['answers']})")
            print(f"    Sent: {s['sent_at']}")
        return

    if args.command == "create":
        # Interactive questionnaire creation
        print(f"\nCreating questionnaire: {args.name}")
        print("Enter questions (empty line to finish):\n")
        questions = []
        i = 1
        while True:
            q_text = input(f"  Q{i}: ").strip()
            if not q_text:
                break
            q_id = input(f"  ID for Q{i} (e.g., 'sender_name'): ").strip()
            if not q_id:
                q_id = f"q{i}"
            questions.append({"id": q_id, "text": q_text})
            i += 1

        if not questions:
            print("No questions entered. Aborting.")
            return

        intro = input("\nIntro message (use {name} for client name): ").strip()
        outro = input("Outro message: ").strip()

        questionnaire = {
            "title": args.name.replace("_", " ").title(),
            "description": f"Custom questionnaire: {args.name}",
            "intro": intro or "Hey {name}! I have a few questions for you.",
            "questions": questions,
            "outro": outro or "Thanks for your answers!",
            "sender_id": "\n\n— William from Marceau Solutions"
        }

        output_path = args.output or str(DATA_DIR / f"custom_{args.name}.json")
        with open(output_path, 'w') as f:
            json.dump(questionnaire, f, indent=2)
        print(f"\nSaved: {output_path}")
        print(f"Use: python execution/client_questionnaire.py send "
              f"--questionnaire custom --custom-file {output_path} --to ... --name ...")
        return

    if args.command == "send":
        cq = ClientQuestionnaire()
        custom_q = None
        if args.questionnaire == "custom" and args.custom_file:
            with open(args.custom_file) as f:
                custom_q = json.load(f)

        result = cq.send_questionnaire(
            to=args.to,
            name=args.name,
            questionnaire_key=args.questionnaire,
            custom_questionnaire=custom_q,
            delay_between=args.delay,
            dry_run=args.dry_run
        )

        if result.get("success"):
            if not args.dry_run:
                print(f"\nSession ID: {result['session']['id']}")
                print(f"Check responses: python execution/client_questionnaire.py check "
                      f"--session {result['session']['id']}")
        else:
            print(f"\nFailed: {result.get('error')}")
            sys.exit(1)
        return

    if args.command == "check":
        cq = ClientQuestionnaire()
        result = cq.check_responses(args.session)
        if not result.get("success"):
            print(f"\nFailed: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
