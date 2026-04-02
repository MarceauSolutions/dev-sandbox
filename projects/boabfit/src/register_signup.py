#!/usr/bin/env python3
"""
Register a new signup in the drip state file.
Usage: python3 register_signup.py <email> <name> [<phone>]
Called by the BOABFIT - Signup Complete n8n workflow via Execute Command node.
"""
import json
import sys
import os
from datetime import datetime, timezone

STATE_FILE = "/home/ec2-user/data/boabfit/drip_state.json"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "email required"}))
        sys.exit(1)
    
    email = sys.argv[1].strip().lower()
    name = sys.argv[2].strip() if len(sys.argv) > 2 and sys.argv[2] else "there"
    phone = sys.argv[3].strip() if len(sys.argv) > 3 and sys.argv[3] else ""
    
    # Initialize state if not exists
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    else:
        state = {"signups": {}}
    
    if "signups" not in state:
        state["signups"] = {}
    
    # Register signup (or refresh if re-signing)
    now = datetime.now(timezone.utc).isoformat()
    
    if email not in state["signups"]:
        state["signups"][email] = {
            "name": name,
            "phone": phone,
            "signed_up_at": now,
            "emails_sent": []
        }
        result = {"success": True, "action": "registered", "email": email}
    else:
        # Already registered — don't reset their drip position
        result = {"success": True, "action": "already_registered", "email": email}
    
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
