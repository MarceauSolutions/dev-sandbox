#!/usr/bin/env python3
"""
BOABFIT - Julia Response Monitor
Monitors Julia's SMS responses, classifies them with Grok,
manages question state, and triggers app build approval flow.
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

# Config
STATE_FILE = "/home/ec2-user/dev-sandbox/projects/boabfit/data/julia_questions_state.json"
JULIA_PHONE = "+12393985197"
TWILIO_SMS = "/home/ec2-user/dev-sandbox/execution/twilio_sms.py"
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_URL = "https://api.x.ai/v1/chat/completions"
WILLIAM_CHAT_ID = "5692454753"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
STATE_LOCK = threading.Lock()
RETRY_QUEUE = []

# Load Telegram token from n8n credential or env
def load_telegram_token():
    global TELEGRAM_BOT_TOKEN
    try:
        # Try reading from Clawdbot config
        result = subprocess.run(
            ["grep", "-r", "TELEGRAM_BOT_TOKEN", "/home/ec2-user/.env"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            TELEGRAM_BOT_TOKEN = result.stdout.strip().split("=", 1)[1].strip()
            return
        # Try from clawdbot config
        for path in ["/home/ec2-user/dev-sandbox/projects/personal-assistant/.env",
                     "/home/ec2-user/.env"]:
            if os.path.exists(path):
                with open(path) as f:
                    for line in f:
                        if "TELEGRAM_BOT_TOKEN" in line and "=" in line:
                            TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip()
                            return
    except Exception as e:
        log.warning(f"Could not load Telegram token: {e}")


def load_state():
    with STATE_LOCK:
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            return None


def save_state(state):
    with STATE_LOCK:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.rename(tmp, STATE_FILE)


def send_sms(message):
    """Send SMS to Julia via twilio_sms.py"""
    try:
        result = subprocess.run(
            ["python3", TWILIO_SMS, "--to", JULIA_PHONE, "--message", message],
            capture_output=True, text=True, timeout=30
        )
        log.info(f"SMS sent: {result.stdout[:100]}")
        return True
    except Exception as e:
        log.error(f"SMS send failed: {e}")
        return False


def send_telegram(message):
    """Send message to William's Telegram via Clawdbot"""
    if not TELEGRAM_BOT_TOKEN:
        log.warning("No Telegram token - can't notify William")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": WILLIAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        return resp.ok
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


def classify_with_grok(message_text, state):
    """Use Grok to classify Julia's message"""
    questions_context = ""
    unanswered = []
    for num, q in state["questions"].items():
        status = "ANSWERED: " + q["answer"] if q["answered"] else "UNANSWERED"
        questions_context += f"Q{num}: {q['question']} [{status}]\n"
        if not q["answered"]:
            unanswered.append(num)

    pending = state.get("pending_clarifications", [])
    pending_context = ""
    if pending:
        pending_context = "\nPENDING CLARIFICATIONS (waiting for Julia to confirm):\n"
        for p in pending:
            pending_context += f"- {p.get('type', '?')}: {p.get('summary', '?')}\n"

    prompt = f"""You are classifying an SMS from Julia Marceau about her BOABFIT fitness app.

QUESTIONS WE ASKED HER:
{questions_context}
{pending_context}
JULIA'S TEXT MESSAGE:
"{message_text}"

Classify this message. Return ONLY valid JSON:
{{
  "type": "question_answer" | "ambiguous" | "actionable_request" | "casual" | "clarification_response",
  "question_numbers": [1],
  "answers": {{"1": "structured clear answer"}},
  "confidence": 0.9,
  "action_summary": "what she wants done (if actionable)",
  "clarification_for": "what pending item this clarifies (if clarification_response)",
  "suggested_response": "casual friendly response from William's perspective",
  "suggested_followup": "clarifying question if ambiguous or actionable (null if not needed)"
}}

RULES:
- "question_answer" ONLY if you're very confident (>0.85) which question(s) this answers clearly
- "ambiguous" if it MIGHT answer a question but isn't clear enough to act on
- "actionable_request" if she's asking for something to be done (website change, feature request, etc.)
- "clarification_response" if this is a follow-up to a pending clarification we asked
- "casual" if it's just conversation
- suggested_response should sound like William texting — casual, friendly, not robotic
- suggested_followup should be a natural clarifying question (null if type is "question_answer" with high confidence or "casual")
- For actionable_request, ALWAYS include a suggested_followup to confirm specifics before acting"""

    try:
        resp = requests.post(XAI_URL, headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "grok-3-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }, timeout=30)

        if resp.status_code != 200:
            log.error(f"Grok API error: {resp.status_code} {resp.text[:200]}")
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        # Extract JSON from response (handle markdown code blocks)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())

    except Exception as e:
        log.error(f"Grok classification failed: {e}")
        return None


def get_unanswered_nudge(state):
    """Generate a natural nudge for unanswered questions"""
    unanswered = []
    for num, q in state["questions"].items():
        if not q["answered"]:
            unanswered.append((num, q["topic"]))

    if not unanswered:
        return ""

    topics = {
        "workout_videos": "the workout videos",
        "pricing_model": "how you want to charge clients",
        "apple_developer": "the Apple Developer Account",
        "multiple_programs": "whether you'll have other programs"
    }

    if len(unanswered) == 1:
        topic = topics.get(unanswered[0][1], unanswered[0][1])
        return f"\n\nAlso whenever you get a chance, still need your thoughts on {topic}!"
    else:
        return f"\n\nAlso still have {len(unanswered)} questions whenever you get a sec!"


def process_message(message_text, sender):
    """Main processing logic for an inbound SMS from Julia"""
    state = load_state()
    if not state:
        log.error("Could not load state file")
        return {"error": "state file missing"}

    # Log raw message
    state["raw_messages"].append({
        "text": message_text,
        "from": sender,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    save_state(state)

    # Forward raw text to William's Telegram immediately
    send_telegram(f"📱 SMS from Julia:\n\n\"{message_text}\"")

    # Classify with Grok
    classification = classify_with_grok(message_text, state)

    if not classification:
        # Grok failed — queue for retry, still notify William
        RETRY_QUEUE.append({"text": message_text, "timestamp": time.time()})
        send_telegram("⚠️ Grok classification failed for Julia's message. Raw text forwarded above. Queued for retry.")
        return {"status": "queued_for_retry"}

    msg_type = classification.get("type", "casual")
    response = classification.get("suggested_response", "")
    followup = classification.get("suggested_followup")
    confidence = classification.get("confidence", 0)

    log.info(f"Classification: type={msg_type}, confidence={confidence}")

    if msg_type == "question_answer" and confidence >= 0.85:
        # High-confidence answer — update state
        for qnum, answer in classification.get("answers", {}).items():
            if qnum in state["questions"]:
                q = state["questions"][qnum]
                q["history"].append({
                    "answer": answer,
                    "raw_text": message_text,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                q["answered"] = True
                q["answer"] = answer

        # Check if all answered
        all_answered = all(q["answered"] for q in state["questions"].values())
        state["all_answered"] = all_answered
        save_state(state)

        # Confirm to Julia
        send_sms(response)

        if all_answered and not state.get("approval_sent"):
            trigger_approval(state)

    elif msg_type == "ambiguous":
        # Need clarification — ask follow-up
        state["pending_clarifications"].append({
            "type": "ambiguous_answer",
            "question_numbers": classification.get("question_numbers", []),
            "raw_text": message_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": followup
        })
        save_state(state)

        sms_text = response
        if followup:
            sms_text = followup
        send_sms(sms_text)

    elif msg_type == "actionable_request":
        # Acknowledge + clarify before acting
        state["pending_clarifications"].append({
            "type": "actionable_request",
            "raw_text": message_text,
            "action_summary": classification.get("action_summary", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confirmed": False,
            "summary": classification.get("action_summary", "")
        })
        save_state(state)

        # Send clarifying response
        sms_text = followup if followup else response
        nudge = get_unanswered_nudge(state)
        send_sms(sms_text + nudge)

        # Notify William about the request
        send_telegram(f"🔧 Julia has an actionable request:\n\"{message_text}\"\n\nAsked her to clarify specifics before acting.")

    elif msg_type == "clarification_response":
        # She's responding to a pending clarification
        pending = state.get("pending_clarifications", [])
        if pending:
            last_pending = pending[-1]
            if last_pending["type"] == "actionable_request":
                # Now we can log the confirmed action
                last_pending["confirmed"] = True
                last_pending["clarification"] = message_text
                state["action_items"].append({
                    "request": last_pending.get("action_summary", ""),
                    "clarification": message_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "pending"
                })
                save_state(state)
                send_sms(response)
                nudge = get_unanswered_nudge(state)
                if nudge:
                    send_sms(nudge.strip())
                send_telegram(f"✅ Julia confirmed actionable request:\nOriginal: \"{last_pending.get('raw_text', '')}\"\nClarification: \"{message_text}\"\n\nLogged as action item.")

            elif last_pending["type"] == "ambiguous_answer":
                # Re-classify with additional context
                combined = last_pending["raw_text"] + " " + message_text
                reclassification = classify_with_grok(combined, state)
                if reclassification and reclassification.get("type") == "question_answer":
                    for qnum, answer in reclassification.get("answers", {}).items():
                        if qnum in state["questions"]:
                            q = state["questions"][qnum]
                            q["history"].append({
                                "answer": answer,
                                "raw_text": combined,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            q["answered"] = True
                            q["answer"] = answer
                    state["all_answered"] = all(q["answered"] for q in state["questions"].values())
                    save_state(state)
                    send_sms(reclassification.get("suggested_response", "Got it, thanks!"))
                    if state["all_answered"] and not state.get("approval_sent"):
                        trigger_approval(state)
                else:
                    save_state(state)
                    send_sms(response)
        else:
            # No pending clarification — treat as casual
            nudge = get_unanswered_nudge(state)
            send_sms(response + nudge)

    else:
        # Casual — respond naturally, nudge unanswered
        nudge = get_unanswered_nudge(state)
        if response:
            send_sms(response + nudge)
        save_state(state)

    return {"status": "processed", "type": msg_type, "confidence": confidence}


def trigger_approval(state):
    """Send structured summary to William for approval"""
    answers = ""
    for num in ["1", "2", "3", "4"]:
        q = state["questions"][num]
        answers += f"\n{num}. {q['topic']}: {q['answer']}"

    action_items = ""
    for item in state.get("action_items", []):
        action_items += f"\n- {item['request']}: {item.get('clarification', '')}"

    msg = f"""🏋️ <b>BOABFIT APP — Julia answered all questions!</b>
{answers}

<b>Action items from conversation:</b>{action_items if action_items else " None"}

Reply <b>APPROVE</b> to start the app build, or <b>REVISE</b> to hold."""

    send_telegram(msg)
    state["approval_sent"] = True
    save_state(state)


# ── Flask Routes ─────────────────────────────

@app.route("/sms", methods=["POST"])
def handle_sms():
    """Receives SMS data from n8n webhook"""
    data = request.json or {}
    message = data.get("message", data.get("Body", data.get("body", "")))
    sender = data.get("from", data.get("From", data.get("sender", "")))

    if not message:
        return jsonify({"error": "no message"}), 400

    # Only process Julia's messages
    if JULIA_PHONE not in sender.replace(" ", "").replace("-", ""):
        return jsonify({"status": "ignored", "reason": "not Julia"}), 200

    result = process_message(message, sender)
    return jsonify(result)


@app.route("/approve", methods=["POST"])
def handle_approval():
    """William approves the app build"""
    state = load_state()
    if not state:
        return jsonify({"error": "no state"}), 500

    state["approved"] = True
    save_state(state)

    # Create handoff for Ralph
    handoff = {
        "project": "BOABFIT App",
        "type": "app_build_kickoff",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answers": {num: q["answer"] for num, q in state["questions"].items()},
        "action_items": state.get("action_items", []),
        "approved_by": "william",
    }

    handoff_path = "/home/ec2-user/data/boabfit/app_build_handoff.json"
    with open(handoff_path, "w") as f:
        json.dump(handoff, f, indent=2)

    send_telegram("✅ APPROVED. App build handoff created. Ralph can pick it up.")
    send_sms("Just got the green light on your app! Starting the build. I'll keep you posted on progress 💪")

    return jsonify({"status": "approved", "handoff": handoff_path})


@app.route("/health", methods=["GET"])
def health():
    state = load_state()
    answered = sum(1 for q in state["questions"].values() if q["answered"]) if state else 0
    return jsonify({
        "status": "ok",
        "service": "julia-response-monitor",
        "questions_answered": f"{answered}/4",
        "all_answered": state.get("all_answered", False) if state else False,
        "approval_sent": state.get("approval_sent", False) if state else False,
        "approved": state.get("approved", False) if state else False
    })


@app.route("/state", methods=["GET"])
def get_state():
    state = load_state()
    return jsonify(state or {"error": "no state"})


@app.route("/mock", methods=["POST"])
def mock_test():
    """Test classification without sending SMS"""
    data = request.json or {}
    message = data.get("message", "")
    state = load_state()
    if not state:
        return jsonify({"error": "no state"}), 500
    classification = classify_with_grok(message, state)
    return jsonify({"classification": classification, "message": message})


# ── Retry Queue Processor ────────────────────

def retry_processor():
    """Process failed Grok classifications every 15 minutes"""
    while True:
        time.sleep(900)
        if RETRY_QUEUE:
            log.info(f"Retrying {len(RETRY_QUEUE)} queued messages")
            to_retry = list(RETRY_QUEUE)
            RETRY_QUEUE.clear()
            for item in to_retry:
                if time.time() - item["timestamp"] > 86400:
                    continue  # skip messages older than 24h
                process_message(item["text"], JULIA_PHONE)


if __name__ == "__main__":
    log.info(f"Telegram token loaded: {'yes' if TELEGRAM_BOT_TOKEN else 'NO'}")
    log.info(f"xAI API key loaded: {'yes' if XAI_API_KEY else 'NO'}")

    # Start retry processor in background
    retry_thread = threading.Thread(target=retry_processor, daemon=True)
    retry_thread.start()

    app.run(host="0.0.0.0", port=5030, debug=False)
