#!/usr/bin/env python3
"""Mark a drip email as sent using the client database."""
import json
import sys
sys.path.insert(0, "/home/clawdbot/dev-sandbox/projects/boabfit/src")
from client_db import BoabfitDB

def main():
    if len(sys.argv) < 3:
        print("Usage: drip_mark_sent.py <email> <day>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    day = int(sys.argv[2])
    comm_type = {3: "drip_day3", 7: "drip_day7", 14: "drip_day14"}.get(day, f"drip_day{day}")

    db = BoabfitDB("/home/ec2-user/data/boabfit/clients.db")

    if db.has_received(email, comm_type):
        print(json.dumps({"success": True, "already_sent": True, "email": email, "day": day}))
    else:
        success = db.log_email(email, comm_type, subject=f"Day {day} drip", status="sent")
        print(json.dumps({"success": success, "email": email, "day_marked": day}))

    db.close()

if __name__ == "__main__":
    main()
