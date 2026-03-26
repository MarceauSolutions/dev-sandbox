#!/usr/bin/env python3
"""
Tier 2 batch send — industry-specific templates, free 2-week offer.
Sends up to LIMIT emails from the Tier 2 routed CSV.
"""
import csv, json, smtplib, os, time, sys
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
ROUTED_CSV = Path(__file__).parent.parent.parent.parent / "marceau-solutions/digital/outputs/naples-ai-prospects-routed-2026-03-23.csv"

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 65

# ── Industry classification ───────────────────────────────────────────────────
def classify_industry(company, title):
    s = (company + " " + title).lower()
    if any(k in s for k in ["hvac", " ac ", "a/c", "cooling", "heating", "refriger", "air condition"]):
        return "hvac"
    if any(k in s for k in ["roof", "roofing"]):
        return "roofing"
    if any(k in s for k in ["plumb"]):
        return "plumbing"
    if any(k in s for k in ["electric", "electrical"]):
        return "electrical"
    if any(k in s for k in ["pool service", "pool cleaning", "pool maintenance", "pool care"]):
        return "pool"
    if any(k in s for k in ["dental", "dentist", "orthodon", "oral surgery", "implant center"]):
        return "dental"
    if any(k in s for k in ["real estate", "realty", "realtor", " broker", "properties llc", "properties inc"]):
        return "real_estate"
    if any(k in s for k in ["physical therapy", "physio", "chiropractic", "chiropract",
                              "medical", "health center", "clinic", "wellness center",
                              "animal hospital", "veterinar", "vet clinic"]):
        return "medical"
    if any(k in s for k in ["remodel", "contractor", "construction", "builder", "renovation"]):
        return "construction"
    if any(k in s for k in ["salon", "beauty", "nail", "hair studio", "hair salon", "barber",
                              "aesthetic", "med spa", "medspa", "skin care", "skincare"]):
        return "beauty"
    if any(k in s for k in ["restaurant", "bistro", "grill", "cafe", "catering", "pizz", "eatery"]):
        return "restaurant"
    if any(k in s for k in ["law ", "legal", "attorney", "lawyer"]):
        return "legal"
    return "general"

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = {
    "hvac": {
        "subject_fn": lambda first, company: f"{company} — after-hours AC calls",
        "body_fn": lambda first, company: f"""Hey {first},

When someone's AC dies at 10pm in Naples and they start calling around, they hire whoever responds first. It's not about price — the job goes to whoever calls back within 10 minutes.

I build AI response systems for HVAC companies that handle those calls automatically — responds within 2 minutes, qualifies the issue, texts you the details.

I build and run the whole thing free for 2 weeks so you can see exactly what you're losing to voicemail before deciding if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "after_hours_emergency"
    },
    "roofing": {
        "subject_fn": lambda first, company: f"{company} — storm season call volume",
        "body_fn": lambda first, company: f"""Hey {first},

After a storm rolls through Naples, homeowners call every roofing company they can find. First one to respond and schedule an inspection wins the job — the others get "we already found someone."

I build AI response systems for roofing companies that handle that surge automatically — responds to every call within 2 minutes, qualifies the damage, books the inspection.

I build and run it free for 2 weeks so you can see how many calls it captures before deciding if it's worth paying for.

Worth a quick call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "storm_surge_calls"
    },
    "plumbing": {
        "subject_fn": lambda first, company: f"{company} — emergency call response",
        "body_fn": lambda first, company: f"""Hey {first},

Plumbing emergencies don't wait — a burst pipe or backed-up drain at 9pm needs someone who answers. Homeowners call until someone picks up, then they stop calling.

I build AI response systems for plumbing companies that handle those emergency calls — responds within 2 minutes, qualifies the issue, notifies you immediately.

I build and run the whole thing free for 2 weeks so you can see what you're currently missing before deciding if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "after_hours_emergency"
    },
    "electrical": {
        "subject_fn": lambda first, company: f"{company} — first-response on service calls",
        "body_fn": lambda first, company: f"""Hey {first},

For electrical service calls, the job usually goes to whoever calls back first — not the best price, not the best reviews. Just whoever responds fastest when the customer is standing there with a problem.

I build AI systems for electrical contractors that handle that first response — qualifies the job, notifies you immediately, so you're always first even when you're on-site.

I build and run it free for 2 weeks so you can see what it would have caught before committing to anything.

Worth a quick call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "pool": {
        "subject_fn": lambda first, company: f"{company} — new service inquiry response",
        "body_fn": lambda first, company: f"""Hey {first},

A homeowner looking for pool service calls 3 companies and hires whoever gets back to them with a real answer first. The other two get "we already found someone."

I build AI response systems for pool companies — handles incoming calls and texts, qualifies the job, books the site visit. No more playing phone tag with new customers.

I build and run it free for 2 weeks so you can see the leads it captures before deciding if it's worth paying for.

15 minutes to see if it fits?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "dental": {
        "subject_fn": lambda first, company: f"{company} — new patient calls after hours",
        "body_fn": lambda first, company: f"""Hey {first},

New dental patients call multiple offices before booking. The practice that responds fastest — even after hours — wins the appointment. The others never hear from them again.

I build AI intake systems for dental practices that answer those calls immediately, capture the patient's needs, and schedule the appointment.

I build and run it free for 2 weeks so you can see how many new patient calls it handles before you decide if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "new_patient_acquisition"
    },
    "real_estate": {
        "subject_fn": lambda first, company: f"{company} — evening buyer and seller calls",
        "body_fn": lambda first, company: f"""Hey {first},

Real estate leads don't wait. A buyer calls on a Saturday evening, gets voicemail, and calls the next agent on Zillow before going to bed. They're gone before Monday morning.

I build AI phone systems for real estate businesses that respond to those calls immediately — captures contact details, answers basic questions, and schedules a callback.

I build and run the full system free for 2 weeks so you can see how many inquiries it catches before deciding if it's worth paying for.

Worth a quick call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "real_estate_inquiry"
    },
    "medical": {
        "subject_fn": lambda first, company: f"{company} — new patient call response",
        "body_fn": lambda first, company: f"""Hey {first},

New patients call at lunch and after 5pm — the only times they're free. If they get voicemail, they don't call back. They call the next provider in their network.

I build AI intake systems for medical practices that handle those calls automatically — answers new patient questions and schedules the appointment.

I build and run it free for 2 weeks so you can see how many new patient calls it captures before you decide if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "new_patient_acquisition"
    },
    "construction": {
        "subject_fn": lambda first, company: f"{company} — estimate request response time",
        "body_fn": lambda first, company: f"""Hey {first},

When a homeowner decides they want work done, they call 3 contractors the same day. Whoever gets back to them first with a walkthrough date wins the estimate — and usually the job.

I build AI systems for contractors that handle those first calls — qualifies the project, books the estimate appointment, all within 2 minutes of the call.

I build and run it free for 2 weeks so you can see what you're currently losing to voicemail before deciding if it's worth paying for.

Worth a quick call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "beauty": {
        "subject_fn": lambda first, company: f"{company} — appointment inquiry response",
        "body_fn": lambda first, company: f"""Hey {first},

Clients looking to book a new salon or spa try a few places at once. Whoever confirms an appointment first wins the booking — the others don't hear back.

I build AI intake systems for beauty and wellness businesses that respond to those calls and texts immediately — answers availability questions and books the appointment.

I build and run it free for 2 weeks so you can see how many bookings it captures before you decide if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "restaurant": {
        "subject_fn": lambda first, company: f"{company} — reservation and inquiry calls",
        "body_fn": lambda first, company: f"""Hey {first},

Diners calling for a reservation or large party inquiry during service hours rarely reach anyone. If they can't get through quickly, they call the restaurant next door.

I build AI phone systems for restaurants that handle those calls — takes reservation details, answers menu questions, and confirms bookings automatically.

I build and run it free for 2 weeks so you can see how many calls it handles before deciding if it's worth paying for.

Worth a quick call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "legal": {
        "subject_fn": lambda first, company: f"{company} — new client inquiry calls",
        "body_fn": lambda first, company: f"""Hey {first},

People looking for legal help call multiple firms and go with whoever gets back to them first. They're stressed, they want a response today — not a callback in two days.

I build AI intake systems for law firms that respond to new client inquiries immediately — captures case details, answers initial questions, and schedules the consultation.

I build and run it free for 2 weeks so you can see how many inquiries it captures before you decide if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "response_speed_wins_bid"
    },
    "general": {
        "subject_fn": lambda first, company: f"{company} — missed call follow-up",
        "body_fn": lambda first, company: f"""Hey {first},

Quick question about {company}: when a potential customer calls and can't get through — after hours, busy day, whatever the reason — what's your process for making sure they don't go to a competitor before you get back to them?

I build AI phone/text systems for local businesses in Naples that handle those calls automatically — responds within 2 minutes, captures the lead, notifies you.

I build and run the whole thing free for 2 weeks so you can see what you're currently losing to voicemail before deciding if it's worth paying for.

Worth a 15-minute call?

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com""",
        "angle": "general_response_time"
    },
}

# ── B2B disqualification for Tier 2 ──────────────────────────────────────────
B2B_SIGNALS = [
    "staffing", "recruiting", "wholesale", "distributor", "manufacturer",
    "software", "saas", "enterprise", "b2b", "corporate housing", "drone services",
    "fire suppression", "fire stop", "alarm systems", "security systems",
    "it services", "managed services", "msp", "media production", "photography studio",
    "transaction coordinator", "title company", "mortgage wholesale",
    "hotel", "resort", "hospitality group", "tour operator", "nature tours",
]

def is_b2b(company, title):
    s = (company + " " + title).lower()
    return any(sig in s for sig in B2B_SIGNALS)

# ── Load tracking and CSV ─────────────────────────────────────────────────────
tracking = json.loads(TRACKING_FILE.read_text()) if TRACKING_FILE.exists() else {
    "campaign": "ai-client-sprint-cold-outreach", "date": "2026-03-23",
    "sender": SENDER_EMAIL, "total_sent": 0, "total_failed": 0, "emails": []
}
already_sent = {e["recipient"] for e in tracking["emails"]}

tier2_leads = []
generic_prefixes = ("info@", "office@", "contact@", "admin@", "hello@", "support@")
with open(ROUTED_CSV) as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get("email", "")
        if (row.get("routing_tier") == "2"
                and email
                and email not in already_sent
                and row.get("disqualified", "").lower() != "true"
                and not any(email.lower().startswith(p) for p in generic_prefixes)
                and not is_b2b(row.get("company_name", ""), row.get("title", ""))):
            tier2_leads.append(row)

print(f"Clean Tier 2 leads available: {len(tier2_leads)}")
print(f"Sending up to: {LIMIT}")
print()

# ── Send ──────────────────────────────────────────────────────────────────────
sent = failed = skipped_b2b = 0

for row in tier2_leads[:LIMIT]:
    first = (row.get("first_name") or "there").strip() or "there"
    company = row.get("company_name", "").strip()
    email = row.get("email", "").strip()
    title = row.get("title", "")

    industry = classify_industry(company, title)
    tmpl = TEMPLATES[industry]
    subject = tmpl["subject_fn"](first, company)
    body = tmpl["body_fn"](first, company)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = email
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())

        tracking["emails"].append({
            "recipient": email,
            "first_name": first,
            "company": company,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "tier": 2,
            "industry": industry,
            "pain_point_angle": tmpl["angle"],
            "research_verdict": f"Tier 2 — {industry} batch template",
            "template_id": f"tier2_{industry}",
            "reply_received": False,
            "reply_at": None,
            "pipeline_stage": "Intake"
        })
        already_sent.add(email)
        sent += 1
        print(f"SENT [{industry:18s}] {first} @ {company} <{email}>")
        time.sleep(1.5)

    except Exception as e:
        failed += 1
        print(f"FAILED: {email} — {e}")

tracking["total_sent"] = len(tracking["emails"])
tracking["total_failed"] = tracking.get("total_failed", 0) + failed
TRACKING_FILE.write_text(json.dumps(tracking, indent=2))
print(f"\n{'─'*60}")
print(f"Done: {sent} sent, {failed} failed | Total today: {tracking['total_sent']}")
