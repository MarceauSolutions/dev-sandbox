#!/usr/bin/env python3
"""Send approved Tier 1 cold emails — batch 4."""
import json, smtplib, os, time
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
BATCH_FILE = OUTPUT_DIR / "tier1_drafts_batch4_2026-03-23.json"

ANGLE_KEYWORDS = {
    "after_hours_emergency": ["after-hours", "after hours", "10pm", "7pm", "night", "weekend", "voicemail", "off-hours", "dies at"],
    "response_speed_wins_bid": ["first to respond", "calls back first", "whoever responds first", "whoever gets back", "whoever calls back first", "rate shop"],
    "new_patient_acquisition": ["new patient", "new customer", "book with someone else", "long-term patient"],
    "after_hours_urgency": ["after work", "after 5pm", "in pain", "sunday", "won't wait"],
    "elective_consult_recovery": ["research late", "research at night", "9pm", "browsing", "inspiration", "fades", "elective"],
    "real_estate_inquiry": ["zillow", "evening buyer", "evening inquiry", "evening and weekend"],
}

def _derive_angle(pain_point, industry):
    pp_lower = pain_point.lower()
    for angle, kws in ANGLE_KEYWORDS.items():
        if any(kw in pp_lower for kw in kws):
            return angle
    fallbacks = {
        "retail_hardware": "response_speed_wins_bid", "furniture_retail": "elective_consult_recovery",
        "functional_medicine": "new_patient_acquisition", "orthopaedics": "after_hours_urgency",
        "real_estate": "real_estate_inquiry", "mortgage": "response_speed_wins_bid",
        "remodeling": "response_speed_wins_bid", "interior_design": "elective_consult_recovery",
    }
    return fallbacks.get(industry, "general_response_time")

def send_email(to, subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SENDER_EMAIL, to, msg.as_string())

tracking = json.loads(TRACKING_FILE.read_text()) if TRACKING_FILE.exists() else {
    "campaign": "ai-client-sprint-cold-outreach", "date": "2026-03-23",
    "sender": SENDER_EMAIL, "total_sent": 0, "total_failed": 0, "emails": []
}
already_sent = {e["recipient"] for e in tracking["emails"]}
batch = json.loads(BATCH_FILE.read_text())
sent = failed = 0

for email in batch["emails"]:
    if email["to"] in already_sent:
        print(f"SKIP: {email['to']}")
        continue
    try:
        send_email(email["to"], email["subject"], email["body"])
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
            "research_verdict": email.get("verdict", ""),
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
TRACKING_FILE.write_text(json.dumps(tracking, indent=2))
print(f"\n--- Done: {sent} sent, {failed} failed. Total: {tracking['total_sent']} ---")
