#!/usr/bin/env python3
"""
Central configuration for the Sales Pipeline Orchestrator.

All env vars, database paths, API endpoints, tier thresholds,
ICP definitions, and A/B test parameters live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from dev-sandbox root
_PROJECT_ROOT = Path(__file__).resolve().parents[5]  # dev-sandbox/
load_dotenv(str(_PROJECT_ROOT / ".env"))

# ── Paths ──
DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "pipeline.db")
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TOKEN_PATH = str(_PROJECT_ROOT / "token.json")
CREDENTIALS_PATH = str(_PROJECT_ROOT / "credentials.json")

# ── API Keys ──
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── SMTP / Email ──
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "wmarceau@marceausolutions.com")

# ── Twilio / SMS ──
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+18552399364")

# ── Google Sheets ──
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")

# ── William's Contact ──
WILLIAM_PHONE = "+12393985676"
WILLIAM_EMAIL = "wmarceau@marceausolutions.com"

# ── Tier Thresholds ──
TIER_1_MIN = 80   # Score 80-100 = Tier 1 (hot)
TIER_2_MIN = 50   # Score 50-79  = Tier 2 (warm)
# Below 50 = Tier 3 (cold)

# ── ICP Industries (target verticals) ──
ICP_INDUSTRIES = [
    "HVAC", "Plumbing", "Electrical", "Medical", "Dental",
    "Legal", "Real Estate", "Med Spa", "Roofing", "Chiropractic",
    "Restaurant", "Auto",
]

# Industry scoring weights (higher = better ICP match)
INDUSTRY_SCORES = {
    "HVAC": 25, "HVAC / Home Services": 25,
    "Plumbing": 25,
    "Electrical": 20,
    "Medical": 20, "Medical / Dental": 20,
    "Dental": 20,
    "Legal": 20,
    "Real Estate": 15,
    "Med Spa": 20, "Med Spa / Beauty": 20,
    "Roofing": 20,
    "Chiropractic": 15,
    "Restaurant": 10, "Restaurants / Hospitality": 10,
    "Auto": 15,
    "Salon": 10,
    "Pest Control": 15,
    "Local Business": 5,
    "Other": 0,
    "AI / PropTech": 5,
}

# Location scoring
LOCATION_SCORES = {
    "Naples": 15,
    "Fort Myers": 10,
    "Bonita Springs": 10,
    "Estero": 10,
    "Cape Coral": 8,
    "Marco Island": 8,
    "Lehigh Acres": 5,
}
DEFAULT_FL_SCORE = 5  # Other FL cities

# ── A/B Testing Parameters ──
AB_MIN_TOUCHES_PER_VARIANT = 50   # Minimum sample before evaluating
AB_CONFIDENCE_THRESHOLD = 0.85     # 85% confidence to declare winner
AB_TESTS_FILE = str(DATA_DIR / "ab_tests.json")

# ── Apollo API ──
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
APOLLO_SEARCH_LIMIT = 50  # Max leads per search

# Apollo search parameters for SW Florida ICP
APOLLO_SEARCH_CONFIG = {
    "person_locations": ["Naples, Florida", "Fort Myers, Florida", "Bonita Springs, Florida", "Estero, Florida", "Cape Coral, Florida"],
    "person_titles": ["Owner", "CEO", "President", "General Manager", "Office Manager", "Managing Partner"],
    "organization_num_employees_ranges": ["1,10", "11,50"],
    "q_organization_keyword_tags": ICP_INDUSTRIES,
}

# ── Pipeline Stages ──
STAGES = [
    "Prospect", "Contacted", "Qualified", "Meeting Booked",
    "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost",
]

# Outcome → pipeline action mapping
OUTCOME_MAP = {
    "Interested": {
        "stage": "Qualified",
        "next_action": "Send proposal",
        "days_until_followup": 2,
    },
    "Not Interested": {
        "stage": "Closed Lost",
        "next_action": None,
        "days_until_followup": None,
    },
    "Voicemail": {
        "stage": "Contacted",
        "next_action": "Re-call (left voicemail)",
        "days_until_followup": 3,
    },
    "Callback Requested": {
        "stage": "Qualified",
        "next_action": "Call back as requested",
        "days_until_followup": 1,
    },
    "Meeting Booked": {
        "stage": "Meeting Booked",
        "next_action": "Prepare for meeting",
        "days_until_followup": 0,
    },
    "No Answer": {
        "stage": "Contacted",
        "next_action": "Try again",
        "days_until_followup": 2,
    },
    "Gatekeeper": {
        "stage": "Contacted",
        "next_action": "Try again — get past gatekeeper",
        "days_until_followup": 2,
    },
    "Send Info": {
        "stage": "Contacted",
        "next_action": "Send info email",
        "days_until_followup": 1,
        "auto_send_info": True,
    },
    "Wrong Number": {
        "stage": "Closed Lost",
        "next_action": None,
        "days_until_followup": None,
    },
    "Already Has Solution": {
        "stage": "Closed Lost",
        "next_action": None,
        "days_until_followup": None,
    },
}

# ── Follow-up day defaults ──
DEFAULT_FOLLOWUP_DAYS = {
    "Prospect": 5,
    "Contacted": 3,
    "Qualified": 2,
    "Meeting Booked": 0,
    "Proposal Sent": 3,
    "Negotiation": 2,
}

# ── IMAP (Gmail) ──
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

# ── Daily Schedule Time Blocks ──
DAILY_SCHEDULE_BLOCKS = {
    "call_block": {"start": "09:00", "end": "11:00", "timezone": "America/New_York"},
    "visit_block": {"start": "11:00", "end": "13:00", "timezone": "America/New_York"},
    "email_block": {"start": "13:00", "end": "14:00", "timezone": "America/New_York"},
}
