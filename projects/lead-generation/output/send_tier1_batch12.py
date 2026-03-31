#!/usr/bin/env python3
"""Send approved Tier 1 cold emails — batch 1 and batch 2."""
import json
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SENDER_NAME = os.getenv("SENDER_NAME", "William Marceau")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

OUTPUT_DIR = Path(__file__).parent
TRACKING_FILE = OUTPUT_DIR / "outreach_tracking_2026-03-23.json"

batch_files = [
    OUTPUT_DIR / "tier1_drafts_batch1_2026-03-23.json",
    OUTPUT_DIR / "tier1_drafts_batch2_2026-03-23.json",
]

ANGLE_KEYWORDS = {
    "after_hours_emergency": ["after-hours", "after hours", "10pm", "7pm", "night", "weekend", "emergency", "voicemail", "off-hours"],
    "missed_calls_during_procedures": ["during procedure", "during a procedure", "in a procedure", "tied up", "physically unavailable"],
    "storm_surge_calls": ["storm", "after a storm", "hurricane", "surge"],
    "response_speed_wins_bid": ["response time", "first to respond", "calls back first", "calls around", "whoever responds first", "whoever picks up"],
    "new_patient_acquisition": ["new patient", "new customer inquiry", "first to respond", "book with someone else"],
    "after_hours_urgency": ["after 5pm", "after hours", "after-hours", "urgent", "won't wait"],
    "direct_pay_intake": ["direct-pay", "direct pay", "cash-pay", "cash pay", "out of pocket"],
    "implant_consult_followup": ["implant", "consult", "consult follow"],
}


def _derive_angle(pain_point: str, industry: str) -> str:
    """Map a pain_point string to a canonical angle key for the scorecard."""
    pp_lower = pain_point.lower()
    for angle, keywords in ANGLE_KEYWORDS.items():
        if any(kw in pp_lower for kw in keywords):
            return angle
    # Industry-level fallbacks
    fallbacks = {
        "hvac": "after_hours_emergency",
        "roofing": "storm_surge_calls",
        "electrical": "after_hours_emergency",
        "dental": "missed_calls_during_procedures",
        "physical_therapy": "direct_pay_intake",
        "pool_service": "response_speed_wins_bid",
        "veterinary": "after_hours_urgency",
        "home_services": "after_hours_emergency",
        "plumbing": "after_hours_emergency",
    }
    return fallbacks.get(industry, "general_response_time")


def send_email(to, first_name, company, subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SENDER_EMAIL, to, msg.as_string())

def load_tracking():
    if TRACKING_FILE.exists():
        return json.loads(TRACKING_FILE.read_text())
    return {"campaign": "ai-client-sprint-cold-outreach", "date": "2026-03-23",
            "sender": SENDER_EMAIL, "total_sent": 0, "total_failed": 0, "emails": []}

def save_tracking(data):
    TRACKING_FILE.write_text(json.dumps(data, indent=2))

tracking = load_tracking()
already_sent = {e["recipient"] for e in tracking["emails"]}

sent = 0
failed = 0

for batch_file in batch_files:
    batch = json.loads(batch_file.read_text())
    for email in batch["emails"]:
        if email["to"] in already_sent:
            print(f"SKIP (already sent): {email['to']}")
            continue
        try:
            send_email(email["to"], email["first_name"], email["company"],
                       email["subject"], email["body"])
            tracking["emails"].append({
                "recipient": email["to"],
                "first_name": email["first_name"],
                "company": email["company"],
                "subject": email["subject"],
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent",
                "tier": email.get("tier", 1),
                "industry": email.get("industry", ""),
                "pain_point_angle": _derive_angle(email.get("pain_point", ""), email.get("industry", "")),
                "research_verdict": email.get("verdict", email.get("hook", "")),
                "template_id": email.get("id", ""),
                "reply_received": False,
                "reply_at": None,
                "pipeline_stage": "Intake"
            })
            already_sent.add(email["to"])
            sent += 1
            print(f"SENT: {email['first_name']} @ {email['company']} <{email['to']}>")
            time.sleep(2)
        except Exception as e:
            failed += 1
            print(f"FAILED: {email['to']} — {e}")

tracking["total_sent"] = len(tracking["emails"])
tracking["total_failed"] = tracking.get("total_failed", 0) + failed
save_tracking(tracking)

print(f"\n--- Done: {sent} sent, {failed} failed. Total tracked: {tracking['total_sent']} ---")
