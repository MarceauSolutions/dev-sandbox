#!/usr/bin/env python3
"""
BOABFIT Drip Sequence Checker
Reads drip_state.json, finds signups where the next email is due,
and outputs a JSON array of emails to send.

Drip schedule:
  Email 1 (Day 0): immediate after signup — "Welcome to Barbie Body!"
  Email 2 (Day 3): check-in
  Email 3 (Day 7): one week celebration
  Email 4 (Day 14): halfway motivation

State file format:
{
  "signups": {
    "email@example.com": {
      "name": "Jane",
      "phone": "...",
      "signed_up_at": "2026-04-01T12:00:00+00:00",
      "emails_sent": [0, 3]   // day indices sent
    }
  }
}
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta

STATE_FILE = "/home/ec2-user/data/boabfit/drip_state.json"

DRIP_SCHEDULE = [
    {
        "day": 0,
        "subject": "Welcome to Barbie Body! Here's what's next",
        "body": """Hey {name}!

Welcome to the 6-Week Barbie Body program — we're so excited to have you!

Here's what to do RIGHT NOW to get started:

1. Download the BOABFIT app and log in
2. Follow @boabfit on Instagram — Julia posts coaching videos and daily inspiration there
3. Check your email for your program guide
4. Get ready — Day 1 starts NOW!

Julia is doing the workouts right alongside you. You've got a whole community behind you.

Let's get it! 🍑

Julia & the BOABFIT Team
info@boabfit.com"""
    },
    {
        "day": 3,
        "subject": "Day 3 check-in — how are you feeling?",
        "body": """Hey {name}!

You're 3 days in — how's it going?

We hope you're feeling the burn (in a good way)! Julia is right there with you, doing every single workout.

A few things to keep you going:
• Share your progress on Instagram and tag @boabfit — we LOVE seeing it!
• If a workout feels too hard or too easy, remember: scale it to YOU
• Soreness = progress (drink that water!)

You're doing amazing. Keep showing up.

Julia & the BOABFIT Team
info@boabfit.com"""
    },
    {
        "day": 7,
        "subject": "One week down! 💪",
        "body": """Hey {name}!

ONE FULL WEEK. That's HUGE.

Seriously — most people quit before day 7. The fact that you're still here means something.

Tips for staying consistent in week 2:
• Stack your workout onto another habit (morning coffee → workout)
• Take progress photos TODAY — you'll want to compare these at week 6
• Your pre-scheduled workouts are already in the app — just show up!

Julia is so proud of you. Keep going.

Julia & the BOABFIT Team
info@boabfit.com"""
    },
    {
        "day": 14,
        "subject": "Halfway there — don't stop now",
        "body": """Hey {name}!

You've hit the halfway mark of the 6-Week Barbie Body program!

Two weeks of consistency, effort, and showing up even when you didn't feel like it. That's a real transformation — not just physical, but mental.

Here's your week 3 reminder:
• Your progress IS happening, even if you can't see it yet in the mirror
• Track your reps and weights in the app — seeing the numbers go up is addictive
• Julia is posting new coaching videos on Instagram this week — go watch them!

You have everything you need to finish this strong. See you at week 6.

Julia & the BOABFIT Team
info@boabfit.com"""
    }
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"signups": {}}

def main():
    state = load_state()
    now = datetime.now(timezone.utc)
    
    emails_due = []
    
    for email, data in state.get("signups", {}).items():
        signed_up_str = data.get("signed_up_at", "")
        try:
            signed_up = datetime.fromisoformat(signed_up_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        
        emails_sent = set(data.get("emails_sent", []))
        name = data.get("name", "there")
        
        for drip in DRIP_SCHEDULE:
            day = drip["day"]
            if day in emails_sent:
                continue  # Already sent
            
            send_after = signed_up + timedelta(days=day)
            if now >= send_after:
                # Due to send
                body = drip["body"].replace("{name}", name)
                emails_due.append({
                    "email": email,
                    "name": name,
                    "day": day,
                    "subject": drip["subject"],
                    "body": body
                })
                # Only send one email per person per run (lowest day number first)
                break
    
    print(json.dumps(emails_due))

if __name__ == "__main__":
    main()
