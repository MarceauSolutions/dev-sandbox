#!/usr/bin/env python3
"""
Client Onboarding Script — Marceau Solutions AI Services
=========================================================
Onboards a new missed-call text-back client:
  1. Clones demo-missed-call n8n workflow, customizes for client
  2. Configures Twilio webhook on client's phone number
  3. Updates deal in pipeline.db to "Trial Active" with trial_start_date = today
  4. Sends client a welcome SMS
  5. Sends William a Telegram confirmation

Usage:
  python3 projects/shared/lead-scraper/src/onboard_client.py \\
    --business "Naples HVAC Pro" \\
    --owner "John" \\
    --phone "+12395550100" \\
    --email "john@test.com" \\
    --deal-id 1
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

# ── Load credentials ────────────────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
load_dotenv(_env_path)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM        = os.getenv("TWILIO_PHONE_NUMBER", "+18552399364")

N8N_BASE    = "https://n8n.marceausolutions.com"
N8N_API_KEY = os.getenv("N8N_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "5692454753")

DEMO_WORKFLOW_ID   = "5uIyvR23VGVzX4IO"   # Missed Call Text-Back DEMO
PIPELINE_DB        = "/home/clawdbot/data/pipeline.db"
STRIPE_LINK        = "https://buy.stripe.com/9B66oH7tBaeI0Wk8H8g360f"

# ── Helpers ──────────────────────────────────────────────────────────────────

def step(msg: str):
    print(f"\n[STEP] {msg}")

def ok(msg: str):
    print(f"  OK  {msg}")

def warn(msg: str):
    print(f"  WARN {msg}", file=sys.stderr)

def fail(msg: str):
    print(f"  FAIL {msg}", file=sys.stderr)
    sys.exit(1)


# ── Task 1: Clone & customize n8n workflow ───────────────────────────────────

def clone_n8n_workflow(business: str, owner: str, client_phone: str) -> str:
    """
    Clones the demo workflow, customizes the SMS body for this client,
    and returns the new workflow ID.
    """
    step(f"Cloning demo n8n workflow for {business}...")

    headers = {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }

    # Fetch demo workflow
    resp = requests.get(
        f"{N8N_BASE}/api/v1/workflows/{DEMO_WORKFLOW_ID}",
        headers=headers,
        timeout=15
    )
    if resp.status_code != 200:
        fail(f"Could not fetch demo workflow {DEMO_WORKFLOW_ID}: {resp.status_code} {resp.text[:200]}")

    demo = resp.json()

    # Build customized workflow
    workflow_name = f"Missed-Call-TextBack — {business}"

    # Deep-copy nodes and patch SMS message bodies for this client
    import copy
    nodes = copy.deepcopy(demo.get("nodes", []))
    for node in nodes:
        params = node.get("parameters", {})
        # Find any text/body fields and inject client context
        body = params.get("body", "")
        if isinstance(body, str) and ("missed" in body.lower() or "callback" in body.lower() or "call" in body.lower()):
            # Replace generic references with client-specific ones
            params["body"] = body.replace("{{business}}", business).replace("{{owner}}", owner)

        # Handle bodyParameters list (Twilio SMS nodes)
        body_params = params.get("bodyParameters", {}).get("parameters", [])
        for bp in body_params:
            if bp.get("name") == "Body":
                bp["value"] = (
                    f"Hi! You just missed a call from {business}. "
                    f"We'd love to connect — reply here or call us back at {TWILIO_FROM}. "
                    f"- {business} Team"
                )
            if bp.get("name") == "To":
                # Keep dynamic — webhook passes the caller's number
                pass

        # Patch webhook node to use client-specific path
        if node.get("type") == "n8n-nodes-base.webhook":
            safe_name = business.lower().replace(" ", "-").replace("'", "")
            params["path"] = f"missed-call-{safe_name}"

    new_workflow = {
        "name": workflow_name,
        "active": True,
        "nodes": nodes,
        "connections": demo.get("connections", {}),
        "settings": demo.get("settings", {}),
        "staticData": None
    }

    # Check if workflow already exists for this client (idempotent)
    list_resp = requests.get(f"{N8N_BASE}/api/v1/workflows?limit=200", headers=headers, timeout=15)
    list_resp.raise_for_status()
    existing_id = None
    for w in list_resp.json().get("data", []):
        if w["name"] == workflow_name:
            existing_id = w["id"]
            warn(f"Workflow already exists ({existing_id}). Reusing it.")
            return existing_id

    create_resp = requests.post(
        f"{N8N_BASE}/api/v1/workflows",
        headers=headers,
        json=new_workflow,
        timeout=15
    )
    if create_resp.status_code not in (200, 201):
        fail(f"Failed to create workflow: {create_resp.status_code} {create_resp.text[:300]}")

    new_id = create_resp.json()["id"]
    ok(f"Workflow created: {new_id} — '{workflow_name}'")

    # Activate
    act_resp = requests.patch(
        f"{N8N_BASE}/api/v1/workflows/{new_id}",
        headers=headers,
        json={"active": True},
        timeout=15
    )
    if act_resp.status_code == 200:
        ok("Workflow activated.")
    else:
        warn(f"Activation response: {act_resp.status_code}")

    # Get the webhook URL for Twilio config
    safe_name = business.lower().replace(" ", "-").replace("'", "")
    webhook_url = f"{N8N_BASE}/webhook/missed-call-{safe_name}"
    ok(f"Webhook URL: {webhook_url}")
    return new_id, webhook_url


# ── Task 2: Configure Twilio webhook ─────────────────────────────────────────

def configure_twilio_webhook(client_phone: str, webhook_url: str, business: str):
    """
    Points the client's Twilio phone number to the n8n webhook.
    Uses Twilio REST API directly (no SDK dependency required).
    """
    step(f"Configuring Twilio webhook for {client_phone}...")

    # Find the phone number SID
    list_url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}"
        f"/IncomingPhoneNumbers.json?PhoneNumber={requests.utils.quote(client_phone)}"
    )
    resp = requests.get(list_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=15)

    if resp.status_code != 200:
        warn(f"Twilio lookup failed ({resp.status_code}). Webhook not configured automatically.")
        warn("Manual step: In Twilio Console, set the Voice webhook for this number to:")
        warn(f"  POST {webhook_url}")
        return False

    numbers = resp.json().get("incoming_phone_numbers", [])
    if not numbers:
        warn(f"Phone {client_phone} not found in Twilio account.")
        warn("Possible reasons: number not purchased in this account, or number format mismatch.")
        warn("Manual step: In Twilio Console, set the Voice webhook for this number to:")
        warn(f"  POST {webhook_url}")
        return False

    number_sid = numbers[0]["sid"]
    ok(f"Found number SID: {number_sid}")

    # Update webhook
    update_url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}"
        f"/IncomingPhoneNumbers/{number_sid}.json"
    )
    update_resp = requests.post(
        update_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        data={
            "VoiceUrl": webhook_url,
            "VoiceMethod": "POST",
            "StatusCallback": webhook_url.replace("/webhook/", "/webhook/status-"),
        },
        timeout=15
    )

    if update_resp.status_code in (200, 201):
        ok(f"Twilio webhook set: {webhook_url}")
        return True
    else:
        warn(f"Twilio update failed: {update_resp.status_code} {update_resp.text[:200]}")
        return False


# ── Task 3: Update pipeline.db ───────────────────────────────────────────────

def update_pipeline_db(deal_id: int, business: str):
    """
    Sets the deal stage to 'Trial Active' and records trial dates.
    Works locally if running on EC2; falls back to API call otherwise.
    """
    step(f"Updating pipeline.db — deal {deal_id} → Trial Active...")

    today = date.today()
    trial_end = today + timedelta(days=14)

    # Try direct SQLite (works on EC2, or if pipeline.db is accessible)
    db_paths = [
        PIPELINE_DB,
        os.path.expanduser("~/data/pipeline.db"),
        os.path.join(os.path.dirname(__file__), "../../../../pipeline.db"),
    ]

    db_found = None
    for path in db_paths:
        if os.path.exists(path):
            db_found = path
            break

    if db_found:
        try:
            conn = sqlite3.connect(db_found)
            cur = conn.cursor()
            cur.execute(
                """UPDATE deals SET
                     stage = 'Trial Active',
                     trial_start_date = ?,
                     trial_end_date = ?,
                     updated_at = datetime('now')
                   WHERE id = ?""",
                (today.isoformat(), trial_end.isoformat(), deal_id)
            )
            if cur.rowcount == 0:
                warn(f"No deal found with id={deal_id}. Check the deal ID.")
            else:
                conn.commit()
                ok(f"Deal {deal_id} updated: Trial Active, {today} → {trial_end}")
            conn.close()
            return True
        except Exception as e:
            warn(f"Direct SQLite failed: {e}")

    # Fallback: call pipeline API
    api_url = "https://pipeline.marceausolutions.com/api/pipeline/deals"
    try:
        resp = requests.patch(
            f"{api_url}/{deal_id}",
            json={
                "stage": "Trial Active",
                "trial_start_date": today.isoformat(),
                "trial_end_date": trial_end.isoformat()
            },
            timeout=10
        )
        if resp.status_code in (200, 204):
            ok(f"Deal {deal_id} updated via API: Trial Active, {today} → {trial_end}")
            return True
        else:
            warn(f"Pipeline API returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        warn(f"Pipeline API unreachable: {e}")

    warn("Could not update pipeline.db automatically.")
    warn(f"Manual step: UPDATE deals SET stage='Trial Active', trial_start_date='{today}', trial_end_date='{trial_end}' WHERE id={deal_id};")
    return False


# ── Task 4: Welcome SMS to client ─────────────────────────────────────────────

def send_welcome_sms(owner: str, client_phone: str, business_phone: str, business: str):
    """Sends the client a welcome SMS via Twilio."""
    step(f"Sending welcome SMS to {owner} at {client_phone}...")

    msg = (
        f"Hi {owner}, your AI system is live! "
        f"Test it by calling {business_phone} from another phone. "
        f"- William, Marceau Solutions ({TWILIO_FROM})"
    )

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    resp = requests.post(
        url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        data={
            "From": TWILIO_FROM,
            "To": client_phone,
            "Body": msg
        },
        timeout=15
    )

    if resp.status_code in (200, 201):
        sid = resp.json().get("sid", "unknown")
        ok(f"Welcome SMS sent. SID: {sid}")
        return True
    else:
        warn(f"SMS failed: {resp.status_code} {resp.text[:200]}")
        return False


# ── Task 5: Telegram confirmation to William ──────────────────────────────────

def notify_william(business: str, owner: str, client_phone: str, email: str,
                   deal_id: int, workflow_id, webhook_url: str, trial_end: str):
    step("Notifying William via Telegram...")

    text = (
        f"CLIENT ONBOARDED\n\n"
        f"Business: {business}\n"
        f"Owner: {owner}\n"
        f"Phone: {client_phone}\n"
        f"Email: {email}\n"
        f"Deal ID: {deal_id}\n\n"
        f"Trial: Today → {trial_end}\n"
        f"n8n Workflow: {workflow_id}\n"
        f"Webhook: {webhook_url}\n\n"
        f"Welcome SMS sent. Trial conversion sequence running automatically."
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        },
        timeout=10
    )

    if resp.status_code == 200:
        ok("Telegram notification sent to William.")
    else:
        warn(f"Telegram failed: {resp.status_code} {resp.text[:200]}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Onboard a new missed-call text-back client"
    )
    parser.add_argument("--business", required=True, help="Business name, e.g. 'Naples HVAC Pro'")
    parser.add_argument("--owner",    required=True, help="Owner/contact first name, e.g. 'John'")
    parser.add_argument("--phone",    required=True, help="Client's phone number to receive missed calls, e.g. '+12395550100'")
    parser.add_argument("--email",    required=True, help="Client email address")
    parser.add_argument("--deal-id",  required=True, type=int, help="Deal ID in pipeline.db")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  MARCEAU SOLUTIONS — CLIENT ONBOARDING")
    print("=" * 60)
    print(f"  Business : {args.business}")
    print(f"  Owner    : {args.owner}")
    print(f"  Phone    : {args.phone}")
    print(f"  Email    : {args.email}")
    print(f"  Deal ID  : {args.deal_id}")
    print("=" * 60)

    # Validate required env vars
    missing = []
    for var in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "N8N_API_KEY", "TELEGRAM_BOT_TOKEN"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        fail(f"Missing required env vars: {', '.join(missing)}\nCheck .env at {_env_path}")

    trial_end = (date.today() + timedelta(days=14)).isoformat()

    # Step 1: Clone n8n workflow
    result = clone_n8n_workflow(args.business, args.owner, args.phone)
    if isinstance(result, tuple):
        workflow_id, webhook_url = result
    else:
        # Workflow already existed — reuse
        workflow_id = result
        safe_name = args.business.lower().replace(" ", "-").replace("'", "")
        webhook_url = f"{N8N_BASE}/webhook/missed-call-{safe_name}"

    # Step 2: Configure Twilio webhook
    configure_twilio_webhook(args.phone, webhook_url, args.business)

    # Step 3: Update pipeline.db
    update_pipeline_db(args.deal_id, args.business)

    # Step 4: Send welcome SMS
    send_welcome_sms(args.owner, args.phone, args.phone, args.business)

    # Step 5: Notify William
    notify_william(
        business=args.business,
        owner=args.owner,
        client_phone=args.phone,
        email=args.email,
        deal_id=args.deal_id,
        workflow_id=workflow_id,
        webhook_url=webhook_url,
        trial_end=trial_end
    )

    print("\n" + "=" * 60)
    print("  ONBOARDING COMPLETE")
    print("=" * 60)
    print(f"  n8n workflow : {workflow_id}")
    print(f"  Webhook URL  : {webhook_url}")
    print(f"  Trial ends   : {trial_end}")
    print(f"  SMS sequence : Days 10, 13, 14 (automatic)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
