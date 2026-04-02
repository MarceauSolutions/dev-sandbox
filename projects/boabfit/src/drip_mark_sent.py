#!/usr/bin/env python3
"""
Mark a drip email as sent for a given email address and day.
Usage: python3 drip_mark_sent.py <email> <day>
"""
import json
import sys
import os

STATE_FILE = "/home/ec2-user/data/boabfit/drip_state.json"

def main():
    if len(sys.argv) < 3:
        print("Usage: drip_mark_sent.py <email> <day>")
        sys.exit(1)
    
    email = sys.argv[1].strip().lower()
    day = int(sys.argv[2])
    
    if not os.path.exists(STATE_FILE):
        print(f"State file not found: {STATE_FILE}")
        sys.exit(1)
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    if email in state.get("signups", {}):
        if "emails_sent" not in state["signups"][email]:
            state["signups"][email]["emails_sent"] = []
        if day not in state["signups"][email]["emails_sent"]:
            state["signups"][email]["emails_sent"].append(day)
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(json.dumps({"success": True, "email": email, "day_marked": day}))
    else:
        print(json.dumps({"success": False, "error": f"Email {email} not in state"}))

if __name__ == "__main__":
    main()
