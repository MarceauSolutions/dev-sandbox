#!/usr/bin/env python3
"""
Send 8 personalized cold outreach emails for AI client sprint.
Plain text only. SMTP via Gmail.
"""

import smtplib
import json
import os
import sys
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path

# Load .env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = 'wmarceau@marceausolutions.com'
SENDER_NAME = 'William Marceau'

EMAILS = [
    {
        "to": "jamie@antimidators.com",
        "company": "Antimidators",
        "first_name": "Jamie",
        "subject": "antimidators.com \u2014 heads up",
        "body": """Hi Jamie,

Your customers clearly love you \u2014 100% recommendation rate on Facebook. But I tried to visit antimidators.com and my browser threw a security warning and wouldn't load the page.

That means every potential customer finding you on Google is hitting that same wall and calling someone else.

I help Naples businesses make sure they never lose a lead \u2014 whether it's a broken site, missed calls, or slow follow-up. Here's what I do: marceausolutions.com/ai-automation.html

Would it be worth a quick chat?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "doug@precisehomepros.com",
        "company": "Precise Home Pros",
        "first_name": "Doug",
        "subject": "precisehomepros.com \u2014 quick heads up",
        "body": """Hi Doug,

I tried to check out precisehomepros.com this morning and got an error page \u2014 it wouldn't load at all.

If customers are hitting the same wall, they're moving on to the next guy on Google. I help Naples businesses make sure no lead slips through \u2014 missed calls, broken sites, follow-up that runs on autopilot.

Here's what I build: marceausolutions.com/ai-automation.html

Worth a quick conversation?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "ron@spsnaples.com",
        "company": "SPS Naples",
        "first_name": "Ron",
        "subject": "spsnaples.com \u2014 thought you should know",
        "body": """Hi Ron,

I tried to visit spsnaples.com and the page just redirected to a blank screen \u2014 which means your potential customers are probably hitting the same wall and calling someone else.

I help Naples service businesses capture every lead automatically \u2014 even when you're on a job. Here's what that looks like: marceausolutions.com/ai-automation.html

Would that be useful to talk about?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "irene@platinumproassist.com",
        "company": "Platinum Pro Assist",
        "first_name": "Irene",
        "subject": "ppahomewatch.com \u2014 contact page issue",
        "body": """Hi Irene,

I was checking out your home watch service and clicked "Contact Us" \u2014 but the page came back as a 404 error. The testimonials page has the same issue.

For seasonal homeowners researching home watch services from up north before they arrive in Naples, that's a dead end. I help businesses make sure no lead falls through the cracks: marceausolutions.com/ai-automation.html

Worth a quick chat?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "mike@kozakair.com",
        "company": "Kozak AC",
        "first_name": "Mike",
        "subject": "Kozak AC \u2014 quick question",
        "body": """Hi Mike,

Running a one-man HVAC operation in Naples \u2014 your BBB accreditation shows you take it seriously. But when you're on a job site, who's picking up the phone?

I build a system that automatically texts back every missed call within 10 seconds \u2014 so the lead stays warm instead of calling the next guy on Google. Free setup, and I'll run it for 2 weeks so you can see the results.

Here's how it works: marceausolutions.com/ai-automation.html

Worth a quick chat?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "ltancreti@dolphinacnaples.com",
        "company": "Dolphin Cooling",
        "first_name": "Lauren",
        "subject": "Dolphin Cooling \u2014 quick thought",
        "body": """Hi Lauren,

736 five-star reviews \u2014 Dolphin is clearly the go-to HVAC company in Naples. I noticed customers can't actually book a time slot online though \u2014 they fill out a form and wait.

With the volume you're doing, I'd bet after-hours leads are falling through. I build systems that capture those automatically \u2014 instant text-back on missed calls, online booking, automated follow-up: marceausolutions.com/ai-automation.html

Would it be worth a quick conversation?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "hannah@vogelroof.com",
        "company": "Vogel Roofing",
        "first_name": "Hannah",
        "subject": "Vogel Roofing \u2014 something on Google",
        "body": """Hi Hannah,

vogelroof.com is one of the sharpest contractor websites in Naples \u2014 seriously well done. But when I Googled "Vogel Roofing Naples reviews," a ComplaintsBoard result about a failed inspection shows up on page one.

With 60 reviews, that one negative result gets outsized visibility. Getting the review count up would push it off the first page. I help businesses automate review collection and lead follow-up \u2014 here's what I do: marceausolutions.com/ai-automation.html

Worth a quick chat?

William Marceau
Marceau Solutions"""
    },
    {
        "to": "jason@smarthomespecialists.com",
        "company": "Smart Home Specialists",
        "first_name": "Jason",
        "subject": "Smart Home Specialists \u2014 quick thought",
        "body": """Hi Jason,

I was looking into smart home installers in Naples and noticed something \u2014 companies like Liaison Technology and Completely Connected are showing up everywhere with project galleries and reviews. You've got 15 years in the game but when someone Googles "smart home installer Naples," they don't see that.

The homeowners building $2M houses in Naples are researching before they call. Right now your competitors are getting those calls. I help businesses close that gap \u2014 reviews, lead capture, automated follow-up: marceausolutions.com/ai-automation.html

Worth a quick chat?

William Marceau
Marceau Solutions"""
    },
]


def send_email(to_addr, subject, body):
    """Send a plain text email via SMTP."""
    msg = MIMEText(body, 'plain')
    msg['Subject'] = subject
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = to_addr

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()


def main():
    print(f"=== Cold Outreach Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # Test SMTP connection first
    print("Testing SMTP connection...")
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.quit()
        print("SMTP connection OK\n")
    except Exception as e:
        print(f"SMTP connection FAILED: {e}")
        sys.exit(1)

    results = []
    success_count = 0
    fail_count = 0

    for i, email in enumerate(EMAILS, 1):
        ts = datetime.now(timezone.utc).isoformat()
        try:
            send_email(email['to'], email['subject'], email['body'])
            status = "sent"
            success_count += 1
            print(f"  [{i}/8] SENT    -> {email['to']} ({email['company']})")
        except Exception as e:
            status = f"failed: {e}"
            fail_count += 1
            print(f"  [{i}/8] FAILED  -> {email['to']} ({email['company']}) - {e}")

        results.append({
            "recipient": email['to'],
            "first_name": email['first_name'],
            "company": email['company'],
            "subject": email['subject'],
            "sent_at": ts,
            "status": status
        })

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"  Sent:   {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total:  {len(EMAILS)}")

    # Save tracking JSON
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'projects', 'shared', 'lead-scraper', 'output',
        'outreach_tracking_2026-03-23.json'
    )
    tracking_data = {
        "campaign": "ai-client-sprint-cold-outreach",
        "date": "2026-03-23",
        "sender": SENDER_EMAIL,
        "total_sent": success_count,
        "total_failed": fail_count,
        "emails": results
    }
    with open(output_path, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    print(f"\nTracking data saved to: {output_path}")


if __name__ == "__main__":
    main()
