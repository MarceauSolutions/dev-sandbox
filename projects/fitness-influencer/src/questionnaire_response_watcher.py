#!/usr/bin/env python3
"""
questionnaire_response_watcher.py — Automated Questionnaire Response Detector & Action Router

WHAT: Polls all open questionnaire sessions for new SMS responses, auto-executes
      actionable items, and routes complex decisions to William via SMS/Telegram.

WHY: Without this, questionnaire responses sit undetected until someone manually
     runs `client_questionnaire.py check`. That's a half-built system. This closes
     the loop so the influencer automation pipeline is fully autonomous.

DESIGN PRINCIPLES:
  - Zero human intervention for detection (runs on schedule via n8n)
  - Auto-execute simple config changes (sender ID, cron time, schedule updates)
  - Route complex/ambiguous answers to William for review
  - Reusable across all fitness influencer clients (not just BoabFit/Julia)
  - Idempotent — safe to run repeatedly without side effects

INPUT: Open questionnaire sessions in .tmp/questionnaires/
OUTPUT: Updated sessions, executed actions, notifications to William

QUICK USAGE:
  # Check all open sessions for new responses
  python execution/questionnaire_response_watcher.py check

  # Dry run — show what would happen without executing
  python execution/questionnaire_response_watcher.py check --dry-run

  # Run once and exit (for n8n/cron scheduling)
  python execution/questionnaire_response_watcher.py poll

SOP COMPLIANCE:
  - SOP 18: Complete the loop — auto-detects replies without manual trigger
  - Service Standards: Uses execution/twilio_sms.py and client_questionnaire.py

DEPENDENCIES: twilio, python-dotenv
API_KEYS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

# Load env from dev-sandbox root
ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
load_dotenv(env_path)

# Import sibling modules
sys.path.insert(0, str(ROOT / "execution"))
from client_questionnaire import ClientQuestionnaire, QUESTIONNAIRES, DATA_DIR
from twilio_sms import TwilioSMS

# Config
WILLIAM_PHONE = "+12393985676"
TELEGRAM_CHAT_ID = "5692454753"


# ============================================================
# ACTION MANIFESTS — Declarative mapping: answer → system action
# ============================================================
# Each questionnaire type defines what to DO with each answer.
# "auto" actions execute without human review.
# "route" actions send to William for decision.
#
# This is the reusable pattern — new influencer clients just
# need a new manifest entry.
# ============================================================

ACTION_MANIFESTS = {
    "boabfit_template_approval": {
        "description": "BoabFit daily SMS template approval from Julia",
        "actions": {
            "sender_name": {
                "type": "route",  # Custom sign-off needs human to update code
                "description": "Update SENDER_ID in daily_checkin_sms.py",
                "route_reason": "Custom sign-off text — needs code update"
            },
            "message_tone": {
                "type": "auto_acknowledge",
                "description": "Tone approval — no action needed if 'yes'",
                "condition_pass": ["yes", "y", "good", "looks good", "perfect", "love it"],
                "on_fail": "route"  # If not approved, route for review
            },
            "send_time": {
                "type": "route",
                "description": "Update n8n cron schedule for daily SMS",
                "route_reason": "Cron schedule change — needs n8n workflow update"
            },
            "start_date": {
                "type": "route",
                "description": "Update workout schedule and start date",
                "route_reason": "Schedule change — needs workout_plan.json update"
            },
            "extra_content": {
                "type": "route",
                "description": "Add requested content to daily messages",
                "route_reason": "Content addition — needs code/data update"
            }
        }
    },

    "client_onboarding": {
        "description": "New client onboarding survey",
        "actions": {
            "business_name": {
                "type": "route",
                "description": "Record business name for project setup",
                "route_reason": "New client setup required"
            },
            "target_audience": {
                "type": "route",
                "description": "Record target audience info",
                "route_reason": "Strategy input — needs human review"
            },
            "goals": {
                "type": "route",
                "description": "Record project goals",
                "route_reason": "Goal setting — needs human review"
            },
            "timeline": {
                "type": "route",
                "description": "Record timeline/deadlines",
                "route_reason": "Timeline planning — needs human review"
            }
        }
    },

    "client_feedback": {
        "description": "Client satisfaction check-in",
        "actions": {
            "satisfaction": {
                "type": "auto_flag",
                "description": "Flag low satisfaction scores",
                "threshold": 7,  # Score below this = flag for review
                "on_low": "route"
            },
            "whats_working": {
                "type": "auto_acknowledge",
                "description": "Log positive feedback",
                "condition_pass": ["*"],  # Any answer is fine
                "on_fail": "route"
            },
            "improvements": {
                "type": "route",
                "description": "Review improvement suggestions",
                "route_reason": "Client wants changes — needs human review"
            },
            "referral": {
                "type": "auto_flag",
                "description": "Flag referral opportunities",
                "keywords": ["yes", "actually", "friend", "know someone", "sister", "colleague"],
                "on_match": "route"
            }
        }
    }
}


class QuestionnaireResponseWatcher:
    """
    Automated watcher that detects questionnaire completions and routes actions.

    Designed to run on a schedule (every 5 min via n8n) to close the loop
    on all open questionnaire sessions.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.questionnaire = ClientQuestionnaire()
        self.sms = TwilioSMS()
        self.results = {
            "checked": 0,
            "new_answers": 0,
            "completed": [],
            "still_waiting": [],
            "actions_executed": [],
            "actions_routed": [],
            "errors": []
        }

    def find_open_sessions(self) -> List[Dict]:
        """Find all questionnaire sessions that aren't complete yet."""
        open_sessions = []
        for session_file in sorted(DATA_DIR.glob("*.json")):
            try:
                with open(session_file) as f:
                    session = json.load(f)
                if session.get("status") != "complete":
                    open_sessions.append(session)
            except (json.JSONDecodeError, IOError) as e:
                self.results["errors"].append(f"Failed to read {session_file.name}: {e}")
        return open_sessions

    def find_recently_completed(self, hours_back: int = 1) -> List[Dict]:
        """Find sessions completed recently that may need action processing."""
        completed = []
        cutoff = datetime.now()
        for session_file in sorted(DATA_DIR.glob("*.json")):
            try:
                with open(session_file) as f:
                    session = json.load(f)
                if session.get("status") == "complete":
                    # Check if actions have been processed
                    if not session.get("actions_processed"):
                        completed.append(session)
            except (json.JSONDecodeError, IOError):
                pass
        return completed

    def check_session(self, session: Dict) -> Dict:
        """
        Check a single session for new responses.

        Returns the updated session with any new answers.
        """
        session_id = session["id"]
        print(f"\n  Checking: {session_id}")
        print(f"    Client: {session['client_name']} ({session['client_phone']})")
        print(f"    Answers: {session['answers_received']}/{session['questions_sent']}")

        if self.dry_run:
            print(f"    [DRY RUN] Would check Twilio for responses")
            return session

        result = self.questionnaire.check_responses(session_id)

        if result.get("success"):
            new = result.get("new_answers", 0)
            updated_session = result["session"]
            if new > 0:
                print(f"    NEW: {new} answer(s) received!")
                self.results["new_answers"] += new
            else:
                print(f"    No new answers yet.")

            if updated_session.get("status") == "complete":
                print(f"    STATUS: COMPLETE — all answers received!")
                self.results["completed"].append(updated_session)
            else:
                self.results["still_waiting"].append(updated_session)

            return updated_session
        else:
            error = result.get("error", "Unknown error")
            print(f"    ERROR: {error}")
            self.results["errors"].append(f"{session_id}: {error}")
            return session

    def process_actions(self, session: Dict) -> List[Dict]:
        """
        Process actions for a completed questionnaire.

        Uses the ACTION_MANIFESTS to determine what to auto-execute
        vs what to route to William.
        """
        questionnaire_key = session.get("questionnaire", "")
        manifest = ACTION_MANIFESTS.get(questionnaire_key)

        if not manifest:
            # No manifest = route everything to William
            return self._route_all_to_william(session)

        actions_taken = []
        route_items = []

        for qid, question_data in session.get("questions", {}).items():
            answer = question_data.get("answer")
            if not answer:
                continue

            action_def = manifest.get("actions", {}).get(qid, {})
            action_type = action_def.get("type", "route")

            action_record = {
                "question_id": qid,
                "answer": answer,
                "action_type": action_type,
                "description": action_def.get("description", ""),
                "executed": False,
                "routed": False,
                "timestamp": datetime.now().isoformat()
            }

            if action_type == "auto_acknowledge":
                # Check if answer matches pass conditions
                pass_conditions = action_def.get("condition_pass", [])
                answer_lower = answer.lower().strip()
                # Strip Q prefix if present (e.g., "Q2: yes" → "yes")
                if ":" in answer_lower:
                    answer_lower = answer_lower.split(":", 1)[1].strip()

                if "*" in pass_conditions or any(c in answer_lower for c in pass_conditions):
                    action_record["executed"] = True
                    action_record["result"] = "Auto-acknowledged — answer approved"
                    print(f"    AUTO: {qid} — acknowledged ('{answer_lower}')")
                else:
                    # Didn't pass — route to William
                    action_record["routed"] = True
                    route_items.append({
                        "qid": qid,
                        "answer": answer,
                        "reason": f"Answer didn't match auto-approve: {answer_lower}"
                    })

            elif action_type == "auto_flag":
                # Flag-based auto action (e.g., satisfaction scores)
                answer_clean = answer.lower().strip()
                if ":" in answer_clean:
                    answer_clean = answer_clean.split(":", 1)[1].strip()

                keywords = action_def.get("keywords", [])
                threshold = action_def.get("threshold")

                if threshold is not None:
                    # Numeric threshold check
                    try:
                        score = int(''.join(c for c in answer_clean if c.isdigit()))
                        if score < threshold:
                            action_record["routed"] = True
                            route_items.append({
                                "qid": qid,
                                "answer": answer,
                                "reason": f"Score {score} below threshold {threshold}"
                            })
                        else:
                            action_record["executed"] = True
                            action_record["result"] = f"Score {score} OK (threshold: {threshold})"
                    except ValueError:
                        action_record["routed"] = True
                        route_items.append({
                            "qid": qid,
                            "answer": answer,
                            "reason": "Could not parse numeric score"
                        })
                elif keywords:
                    if any(kw in answer_clean for kw in keywords):
                        action_record["routed"] = True
                        route_items.append({
                            "qid": qid,
                            "answer": answer,
                            "reason": f"Keyword match — potential opportunity"
                        })
                    else:
                        action_record["executed"] = True
                        action_record["result"] = "No flag keywords found"

            else:
                # "route" type — always send to William
                action_record["routed"] = True
                route_items.append({
                    "qid": qid,
                    "answer": answer,
                    "reason": action_def.get("route_reason", "Requires human review")
                })

            actions_taken.append(action_record)

        # Send routed items to William
        if route_items:
            self._notify_william_actions(session, route_items)

        # Mark session as actions processed
        session_path = DATA_DIR / f"{session['id']}.json"
        session["actions_processed"] = True
        session["actions_processed_at"] = datetime.now().isoformat()
        session["action_records"] = actions_taken
        with open(session_path, 'w') as f:
            json.dump(session, f, indent=2)

        return actions_taken

    def _route_all_to_william(self, session: Dict) -> List[Dict]:
        """Route all answers to William when no manifest exists."""
        route_items = []
        for qid, q in session.get("questions", {}).items():
            if q.get("answer"):
                route_items.append({
                    "qid": qid,
                    "answer": q["answer"],
                    "reason": "No action manifest — manual review needed"
                })

        if route_items:
            self._notify_william_actions(session, route_items)
        return []

    def _notify_william_actions(self, session: Dict, route_items: List[Dict]):
        """Send William a summary of actions that need his review."""
        client = session.get("client_name", "Unknown")
        questionnaire = session.get("questionnaire", "Unknown")

        lines = [
            f"ACTION NEEDED: {questionnaire}",
            f"Client: {client}",
            f"Items needing review: {len(route_items)}",
            ""
        ]

        for item in route_items:
            lines.append(f"• {item['qid']}: {item['answer'][:80]}")
            lines.append(f"  → {item['reason']}")
            lines.append("")

        lines.append("Review in Claude Code session to execute.")

        message = "\n".join(lines)

        if self.dry_run:
            print(f"\n    [DRY RUN] Would send to William:")
            print(f"    {message[:200]}...")
            return

        # Send SMS notification
        self.sms.send_message(to=WILLIAM_PHONE, message=message)
        print(f"    Notified William via SMS ({len(route_items)} items)")

        self.results["actions_routed"].extend(route_items)

    def run(self) -> Dict:
        """
        Main run loop — check all open sessions and process completions.

        Returns summary of what happened.
        """
        print(f"\n{'='*60}")
        print(f"QUESTIONNAIRE RESPONSE WATCHER")
        print(f"{'='*60}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")

        # 1. Check open sessions for new responses
        open_sessions = self.find_open_sessions()
        print(f"\nOpen sessions: {len(open_sessions)}")

        for session in open_sessions:
            self.results["checked"] += 1
            updated = self.check_session(session)

        # 2. Process actions for newly completed sessions
        newly_completed = self.results["completed"]
        if newly_completed:
            print(f"\n--- PROCESSING {len(newly_completed)} COMPLETED SESSION(S) ---")
            for session in newly_completed:
                print(f"\n  Processing actions for: {session['id']}")
                actions = self.process_actions(session)
                self.results["actions_executed"].extend(
                    [a for a in actions if a.get("executed")]
                )

        # 3. Also check for previously completed but unprocessed sessions
        unprocessed = self.find_recently_completed()
        for session in unprocessed:
            if session["id"] not in [s["id"] for s in newly_completed]:
                print(f"\n  Processing unprocessed session: {session['id']}")
                actions = self.process_actions(session)
                self.results["actions_executed"].extend(
                    [a for a in actions if a.get("executed")]
                )

        # 4. Summary
        print(f"\n{'='*60}")
        print(f"WATCHER SUMMARY")
        print(f"{'='*60}")
        print(f"Sessions checked: {self.results['checked']}")
        print(f"New answers found: {self.results['new_answers']}")
        print(f"Completed: {len(self.results['completed'])}")
        print(f"Still waiting: {len(self.results['still_waiting'])}")
        print(f"Actions auto-executed: {len(self.results['actions_executed'])}")
        print(f"Actions routed to William: {len(self.results['actions_routed'])}")
        if self.results["errors"]:
            print(f"Errors: {len(self.results['errors'])}")
            for e in self.results["errors"]:
                print(f"  - {e}")

        return self.results


def main():
    parser = argparse.ArgumentParser(description="Questionnaire Response Watcher")
    sub = parser.add_subparsers(dest="command", required=True)

    # Check command — interactive, shows full output
    check_parser = sub.add_parser("check", help="Check all open sessions")
    check_parser.add_argument("--dry-run", action="store_true",
                              help="Preview without executing actions")

    # Poll command — for scheduled runs (n8n/cron), minimal output
    poll_parser = sub.add_parser("poll", help="Poll once and exit (for schedulers)")
    poll_parser.add_argument("--dry-run", action="store_true")

    # Status command — show current state
    sub.add_parser("status", help="Show status of all sessions")

    args = parser.parse_args()

    if args.command in ("check", "poll"):
        watcher = QuestionnaireResponseWatcher(dry_run=args.dry_run)
        results = watcher.run()

        # Exit code: 0 if no errors, 1 if errors
        sys.exit(1 if results["errors"] else 0)

    elif args.command == "status":
        print(f"\n{'='*60}")
        print("QUESTIONNAIRE SESSION STATUS")
        print(f"{'='*60}")

        for session_file in sorted(DATA_DIR.glob("*.json")):
            with open(session_file) as f:
                s = json.load(f)
            status_icon = "✅" if s["status"] == "complete" else "⏳"
            actions_icon = "🔧" if s.get("actions_processed") else "❌"
            print(f"\n  {status_icon} {s['id']}")
            print(f"    Client: {s['client_name']} ({s['client_phone']})")
            print(f"    Answers: {s['answers_received']}/{s['questions_sent']}")
            print(f"    Status: {s['status']}")
            print(f"    Actions processed: {actions_icon}")
            if s.get("actions_processed_at"):
                print(f"    Processed at: {s['actions_processed_at']}")


if __name__ == "__main__":
    main()
