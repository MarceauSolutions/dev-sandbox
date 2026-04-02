#!/usr/bin/env python3
"""
BOABFIT Abandonment Checker
Reads n8n execution history via API, finds people who started the form 
but didn't complete signup within 60+ minutes, and haven't been notified yet.
Outputs: JSON array of {email, name, phone} to follow up with.
"""
import json
import sys
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

N8N_API = "http://localhost:5678/api/v1"
ABANDON_WORKFLOW_ID = "3Rp58kNT57VMpzvQ"
SIGNUP_WORKFLOW_ID = "qOrsQZ8ENHvk5izE"
STATE_FILE = "/home/ec2-user/data/boabfit/abandon_sent.json"
FORM_LINK = "https://www.boabfit.com/signup"
LOOKBACK_HOURS = 24  # Check last 24 hours of abandons

def get_api_key():
    import subprocess
    result = subprocess.run(
        ['sqlite3', '/home/ec2-user/.n8n/database.sqlite', 
         'SELECT apiKey FROM user_api_keys LIMIT 1;'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def n8n_get(path, api_key):
    url = f"{N8N_API}{path}"
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": api_key})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"sent": {}}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def extract_body(execution):
    """Extract body from webhook execution data."""
    try:
        run_data = execution.get("data", {}).get("resultData", {}).get("runData", {})
        webhook_run = run_data.get("Webhook", [{}])[0]
        body = webhook_run.get("data", {}).get("main", [[{}]])[0][0].get("json", {}).get("body", {})
        return body
    except (KeyError, IndexError, TypeError):
        return {}

def main():
    api_key = get_api_key()
    if not api_key:
        print(json.dumps([]))
        return

    state = load_state()
    now = datetime.now(timezone.utc)
    cutoff_old = now - timedelta(hours=LOOKBACK_HOURS)
    cutoff_recent = now - timedelta(minutes=60)

    # Fetch recent abandon executions (last 24h)
    try:
        abandon_execs = n8n_get(
            f"/executions?workflowId={ABANDON_WORKFLOW_ID}&limit=100&status=success&includeData=true",
            api_key
        )["data"]
    except Exception as e:
        sys.stderr.write(f"Failed to fetch abandon execs: {e}\n")
        print(json.dumps([]))
        return

    # Fetch recent signup executions (last 24h)
    try:
        signup_execs = n8n_get(
            f"/executions?workflowId={SIGNUP_WORKFLOW_ID}&limit=100&status=success&includeData=true",
            api_key
        )["data"]
    except Exception as e:
        sys.stderr.write(f"Failed to fetch signup execs: {e}\n")
        print(json.dumps([]))
        return

    # Build set of emails that completed signup
    completed_emails = set()
    for ex in signup_execs:
        body = extract_body(ex)
        email = body.get("email", "").strip().lower()
        if email:
            completed_emails.add(email)

    # Find abandoners who need follow-up
    to_follow_up = []
    for ex in abandon_execs:
        started_at_str = ex.get("startedAt", "")
        try:
            started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        # Must be > 60 min ago (gave them time to finish) and within 24h lookback
        if not (cutoff_old <= started_at <= cutoff_recent):
            continue

        body = extract_body(ex)
        email = body.get("email", "").strip().lower()
        name = body.get("name", "").strip()
        phone = body.get("phone", "").strip()

        if not email:
            continue

        # Skip if already signed up
        if email in completed_emails:
            continue

        # Skip if we already sent a follow-up
        if email in state["sent"]:
            continue

        to_follow_up.append({
            "email": email,
            "name": name if name else "there",
            "phone": phone,
            "abandoned_at": started_at_str,
            "form_link": FORM_LINK
        })

    # Mark them as sent (will be confirmed after email send)
    # We write the state now so a race condition doesn't double-send
    for person in to_follow_up:
        state["sent"][person["email"]] = {
            "notified_at": now.isoformat(),
            "abandoned_at": person["abandoned_at"]
        }
    
    if to_follow_up:
        save_state(state)

    print(json.dumps(to_follow_up))

if __name__ == "__main__":
    main()
