#!/usr/bin/env python3
"""
BOABFIT Drip Checker — uses client_db.py for tracking.
Checks which follow-up emails (Day 3/7/14) are due.
Day 0 (welcome) is handled by the Signup Complete webhook.
"""
import json
import sys
import os
sys.path.insert(0, "/home/clawdbot/dev-sandbox/projects/boabfit/src")
from client_db import BoabfitDB
from datetime import datetime, timezone, timedelta

DRIP_SCHEDULE = [
    {"day": 3, "comm_type": "drip_day3", "subject": "Day 3 check-in \u2014 how are you feeling?",
     "body": "Hey {name}!\n\nYou're 3 days in \u2014 how's it going?\n\nWe hope you're feeling the burn (in a good way)! Julia is right there with you, doing every single workout.\n\nA few things to keep you going:\n\u2022 Share your progress on Instagram and tag @boabfit\n\u2022 If a workout feels too hard or too easy, scale it to YOU\n\u2022 Soreness = progress (drink that water!)\n\nYou're doing amazing. Keep showing up.\n\nJulia & the BOABFIT Team\ninfo@boabfit.com"},
    {"day": 7, "comm_type": "drip_day7", "subject": "One week down!",
     "body": "Hey {name}!\n\nONE FULL WEEK. That's HUGE.\n\nSeriously \u2014 most people quit before day 7. The fact that you're still here means something.\n\nTips for staying consistent in week 2:\n\u2022 Stack your workout onto another habit\n\u2022 Take progress photos TODAY\n\u2022 Your pre-scheduled workouts are already in the app \u2014 just show up!\n\nJulia is so proud of you. Keep going.\n\nJulia & the BOABFIT Team\ninfo@boabfit.com"},
    {"day": 14, "comm_type": "drip_day14", "subject": "Halfway there \u2014 don't stop now",
     "body": "Hey {name}!\n\nYou've hit the halfway mark of the 6-Week Barbie Body program!\n\nTwo weeks of consistency, effort, and showing up. That's a real transformation.\n\nHere's your week 3 reminder:\n\u2022 Your progress IS happening, even if you can't see it yet\n\u2022 Track your reps and weights in the app\n\u2022 Julia is posting new coaching videos on Instagram this week\n\nYou have everything you need to finish this strong.\n\nJulia & the BOABFIT Team\ninfo@boabfit.com"}
]

def main():
    db = BoabfitDB("/home/ec2-user/data/boabfit/clients.db")
    now = datetime.now(timezone.utc)
    emails_due = []

    for client in db.get_all_clients(status="active"):
        enrollments = db.get_enrollments(client["email"])
        if not enrollments:
            continue

        enrollment = enrollments[0]
        try:
            start = datetime.fromisoformat(enrollment["start_date"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            start = datetime.fromisoformat(client["signup_date"].replace("Z", "+00:00"))

        for drip in DRIP_SCHEDULE:
            if db.has_received(client["email"], drip["comm_type"]):
                continue

            send_after = start + timedelta(days=drip["day"])
            if now >= send_after:
                body = drip["body"].replace("{name}", client.get("name", "there"))
                emails_due.append({
                    "email": client["email"],
                    "name": client.get("name", "there"),
                    "day": drip["day"],
                    "comm_type": drip["comm_type"],
                    "subject": drip["subject"],
                    "body": body
                })
                break

    db.close()
    print(json.dumps(emails_due))

if __name__ == "__main__":
    main()
