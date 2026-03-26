#!/usr/bin/env python3
"""
Pitch Briefer — generates customized pitch angles per prospect.

Uses existing deal data (industry, pain points, website, research) to
produce a 30-second pitch script tailored to what THIS business would
find most valuable. Avoids "AI" language — frames everything as
business automation and results.

Usage:
    python -m src.pitch_briefer --deal-id 6
    python -m src.pitch_briefer --company "Dolphin Cooling"
    python -m src.pitch_briefer --next 5       # Next 5 call targets
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")

# --- Pitch angle templates by industry + pain point ---
# Each maps to a specific opening line and value prop
# NO "AI" language — everything framed as business outcomes

PITCH_ANGLES = {
    "no_website": {
        "opener": "I noticed you don't have a website yet — which actually tells me your business is running on reputation and referrals. That's great. But you're invisible to anyone searching Google right now.",
        "hook": "I help businesses like yours get found online and capture leads automatically — without you having to learn anything technical.",
        "services": ["Simple website with booking", "Google Business optimization", "Automated review requests"],
    },
    "missed_calls": {
        "opener": "I was looking at your business and noticed calls after hours go to voicemail. For a {industry} company, that means every missed call is a customer calling your competitor instead.",
        "hook": "I set up a system that answers every call — even at 2 AM — books the appointment, and texts you the details. You wake up with new business on your calendar.",
        "services": ["24/7 call answering", "Automatic appointment booking", "Emergency routing to your cell"],
    },
    "scattered_leads": {
        "opener": "Most {industry} businesses I talk to have the same problem — leads come in from Google, phone calls, their website form, maybe Facebook — and they all land in different places. Some get followed up with, some don't.",
        "hook": "I build one system that catches everything and makes sure every single lead gets a response within 60 seconds. Nothing falls through the cracks.",
        "services": ["Unified lead dashboard", "Instant missed-call text-back", "Automated follow-up sequences"],
    },
    "has_basic_automation": {
        "opener": "I can see you already have some automation set up — {detail}. Smart move. But from what I can tell, those systems aren't talking to each other.",
        "hook": "I connect all your existing tools into one system so your leads flow from first contact to booked appointment without you touching anything.",
        "services": ["System integration", "Automated follow-up", "Pipeline visibility dashboard"],
    },
    "competitor_advantage": {
        "opener": "I've been working with a few {industry} businesses in Naples, and the ones that are growing fastest right now are the ones where every lead gets followed up with instantly — not the ones with the biggest ad budget.",
        "hook": "I can set up the same system for you. Two-week trial, no commitment. If it doesn't work, you owe me nothing.",
        "services": ["Lead capture system", "Automated follow-up", "Review generation"],
    },
    "default": {
        "opener": "Hey, I'm William with Marceau Solutions — I help local businesses make sure no lead falls through the cracks.",
        "hook": "Most businesses have calls, texts, and web inquiries coming in from different places. I connect it all into one system that follows up automatically. Two-week free trial if you want to see it in action.",
        "services": ["Unified lead capture", "Automated follow-up", "After-hours coverage"],
    },
}

# Industry-specific language (avoid jargon, speak their language)
INDUSTRY_CONTEXT = {
    "HVAC / Home Services": {
        "their_world": "service calls, emergency repairs, seasonal demand",
        "their_pain": "missed after-hours emergency calls going to competitors",
        "their_metric": "How many calls do you miss on weekends?",
        "best_angle": "missed_calls",
    },
    "Medical / Dental": {
        "their_world": "patient scheduling, no-shows, insurance verification",
        "their_pain": "patients booking with whoever answers first",
        "their_metric": "How many new patients call and don't book?",
        "best_angle": "scattered_leads",
    },
    "Real Estate": {
        "their_world": "listings, showings, buyer inquiries, time-sensitive leads",
        "their_pain": "leads going cold because follow-up takes too long",
        "their_metric": "How fast do your leads get a response?",
        "best_angle": "scattered_leads",
    },
    "Restaurants / Hospitality": {
        "their_world": "reservations, catering inquiries, reviews",
        "their_pain": "missed catering/event inquiries, review management",
        "their_metric": "How many 5-star reviews did you get this month?",
        "best_angle": "competitor_advantage",
    },
    "Legal": {
        "their_world": "consultations, case intake, client communication",
        "their_pain": "potential clients going to whoever responds first",
        "their_metric": "When someone calls after hours, what happens?",
        "best_angle": "missed_calls",
    },
    "Salon / Spa": {
        "their_world": "appointments, rebooking, product sales, reviews",
        "their_pain": "no-shows, forgetting to rebook, lost review opportunities",
        "their_metric": "What percentage of clients rebook before leaving?",
        "best_angle": "competitor_advantage",
    },
    "Auto / Tire": {
        "their_world": "service appointments, parts inquiries, fleet accounts",
        "their_pain": "phone tag with customers about their car status",
        "their_metric": "How do customers know when their car is ready?",
        "best_angle": "scattered_leads",
    },
}


def get_deal(deal_id: int = None, company: str = None) -> dict:
    """Fetch deal with all context."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if deal_id:
        deal = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    elif company:
        deal = conn.execute(
            "SELECT * FROM deals WHERE company LIKE ? ORDER BY lead_score DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()
    else:
        return None

    if not deal:
        conn.close()
        return None

    result = dict(deal)

    # Get outreach history
    outreach = conn.execute(
        "SELECT channel, message_summary, created_at FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC",
        (result["id"],)
    ).fetchall()
    result["outreach_history"] = [dict(o) for o in outreach]

    conn.close()
    return result


def determine_pitch_angle(deal: dict) -> str:
    """Determine the best pitch angle based on deal data."""

    industry = deal.get("industry", "Other")
    pain_points = deal.get("pain_points", "") or ""
    website = deal.get("website", "") or ""
    notes = deal.get("notes", "") or ""
    research = deal.get("research_verdict", "") or ""
    combined = f"{pain_points} {notes} {research}".lower()

    # Check outreach history notes too
    for o in deal.get("outreach_history", []):
        summary = (o.get("message_summary", "") or "").lower()
        combined += f" {summary}"

    # Check for specific signals
    if "text-back" in combined or "automated" in combined or "crm" in combined or "already has" in combined:
        return "has_basic_automation"

    if not website or website.strip() == "":
        return "no_website"

    if "voicemail" in combined or "after hours" in combined or "missed call" in combined:
        return "missed_calls"

    # Use industry default
    ctx = INDUSTRY_CONTEXT.get(industry, {})
    return ctx.get("best_angle", "scattered_leads")


def generate_pitch_brief(deal: dict) -> dict:
    """Generate a complete pitch brief for a deal."""

    angle_key = determine_pitch_angle(deal)
    angle = PITCH_ANGLES.get(angle_key, PITCH_ANGLES["default"])
    industry = deal.get("industry", "Other")
    industry_ctx = INDUSTRY_CONTEXT.get(industry, {})

    # Determine a clean detail string for the opener
    notes = (deal.get("notes", "") or "").lower()
    if "text-back" in notes:
        detail = "a missed-call text-back system"
    elif "crm" in notes:
        detail = "a CRM for tracking leads"
    elif "automated" in notes:
        detail = "some automated follow-up"
    else:
        detail = "some basic automation"

    # Personalize the opener
    opener = angle["opener"].format(
        industry=industry.split("/")[0].strip().lower() if "/" in industry else industry.lower(),
        detail=detail,
    )

    # Build the brief
    brief = {
        "company": deal.get("company", "Unknown"),
        "contact": deal.get("contact_name", "the owner"),
        "phone": deal.get("contact_phone", ""),
        "industry": industry,
        "lead_score": deal.get("lead_score", 0),
        "angle": angle_key,
        "pitch": {
            "opener": opener,
            "hook": angle["hook"],
            "discovery_question": industry_ctx.get("their_metric", "What happens when you miss a call?"),
            "services_to_mention": angle["services"],
            "close": "I'd love to show you how it works — takes 15 minutes. I can do a quick screen share this week, or if you want, I'll set up a two-week trial so you can see it in action risk-free.",
        },
        "context": {
            "their_world": industry_ctx.get("their_world", "customer inquiries, follow-ups, scheduling"),
            "their_pain": industry_ctx.get("their_pain", "leads falling through the cracks"),
        },
        "outreach_history": deal.get("outreach_history", []),
        "do_not_say": [
            "AI", "artificial intelligence", "machine learning",
            "algorithm", "neural network", "LLM",
            "automation platform", "n8n", "workflow engine",
        ],
        "say_instead": {
            "AI receptionist": "virtual receptionist",
            "AI system": "automated system",
            "AI agent": "smart assistant",
            "machine learning": "learns your preferences",
            "automation": "runs in the background",
            "workflow": "system",
            "pipeline": "dashboard",
        },
    }

    return brief


def format_brief_for_telegram(brief: dict) -> str:
    """Format pitch brief for Telegram delivery."""
    lines = []
    lines.append(f"--- PITCH BRIEF: {brief['company']} ---")
    lines.append(f"Contact: {brief['contact']} | {brief['phone']}")
    lines.append(f"Industry: {brief['industry']} | Score: {brief['lead_score']}")
    lines.append(f"Angle: {brief['angle']}")
    lines.append("")
    lines.append("OPENER:")
    lines.append(f'"{brief["pitch"]["opener"]}"')
    lines.append("")
    lines.append("HOOK:")
    lines.append(f'"{brief["pitch"]["hook"]}"')
    lines.append("")
    lines.append("DISCOVERY Q:")
    lines.append(f'"{brief["pitch"]["discovery_question"]}"')
    lines.append("")
    lines.append("MENTION:")
    for s in brief["pitch"]["services_to_mention"]:
        lines.append(f"  - {s}")
    lines.append("")
    lines.append("CLOSE:")
    lines.append(f'"{brief["pitch"]["close"]}"')
    lines.append("")
    if brief["outreach_history"]:
        lines.append("PRIOR CONTACT:")
        for o in brief["outreach_history"][:3]:
            lines.append(f"  {o['channel']}: {o.get('message_summary', '')[:50]}")
    return "\n".join(lines)


def generate_call_list_with_briefs(limit: int = 10) -> list:
    """Generate today's call list with pitch briefs for each."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Priority 1: Warm leads with follow-ups due
    deals = conn.execute("""
        SELECT * FROM deals
        WHERE next_action_date <= date('now')
        AND next_action_date IS NOT NULL AND next_action_date != ''
        AND stage NOT IN ('Closed Won', 'Closed Lost')
        AND contact_phone IS NOT NULL AND contact_phone != ''
        ORDER BY
            CASE WHEN stage = 'Qualified' THEN 1
                 WHEN stage = 'Meeting Booked' THEN 2
                 WHEN stage = 'Active' THEN 3
                 ELSE 4 END,
            lead_score DESC
    """).fetchall()

    results = []
    seen = set()
    for d in deals:
        if d["id"] not in seen and len(results) < limit:
            deal = dict(d)
            deal["outreach_history"] = [
                dict(o) for o in conn.execute(
                    "SELECT channel, message_summary, created_at FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC LIMIT 3",
                    (d["id"],)
                ).fetchall()
            ]
            deal["priority"] = "FOLLOW-UP DUE"
            results.append(deal)
            seen.add(d["id"])

    # Priority 2: Uncalled high-score leads
    if len(results) < limit:
        remaining = limit - len(results)
        uncalled = conn.execute("""
            SELECT * FROM deals
            WHERE stage IN ('Intake', 'Qualified')
            AND contact_phone IS NOT NULL AND contact_phone != ''
            AND id NOT IN (SELECT DISTINCT deal_id FROM outreach_log WHERE channel = 'Call' AND deal_id IS NOT NULL)
            ORDER BY lead_score DESC
            LIMIT ?
        """, (remaining,)).fetchall()
        for d in uncalled:
            if d["id"] not in seen:
                deal = dict(d)
                deal["outreach_history"] = []
                deal["priority"] = "COLD - FIRST CALL"
                results.append(deal)
                seen.add(d["id"])

    conn.close()

    # Generate pitch brief for each
    briefed = []
    for deal in results:
        brief = generate_pitch_brief(deal)
        brief["priority"] = deal.get("priority", "")
        briefed.append(brief)

    return briefed


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.pitch_briefer --deal-id 6")
        print("  python -m src.pitch_briefer --company 'Dolphin Cooling'")
        print("  python -m src.pitch_briefer --next 5")
        sys.exit(1)

    if sys.argv[1] == "--deal-id":
        deal = get_deal(deal_id=int(sys.argv[2]))
        if deal:
            brief = generate_pitch_brief(deal)
            print(format_brief_for_telegram(brief))
        else:
            print("Deal not found")
    elif sys.argv[1] == "--company":
        deal = get_deal(company=sys.argv[2])
        if deal:
            brief = generate_pitch_brief(deal)
            print(format_brief_for_telegram(brief))
        else:
            print("Company not found")
    elif sys.argv[1] == "--next":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        briefs = generate_call_list_with_briefs(limit)
        for i, brief in enumerate(briefs, 1):
            print(f"\n{'='*50}")
            print(f"#{i} [{brief.get('priority', '')}]")
            print(format_brief_for_telegram(brief))
    else:
        print(f"Unknown option: {sys.argv[1]}")
