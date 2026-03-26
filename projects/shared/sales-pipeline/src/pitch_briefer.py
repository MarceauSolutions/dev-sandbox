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

# --- STAGE-AWARE SCRIPT SYSTEM ---
# Core positioning: We don't sell standalone AI tools.
# We unify everything you already have into one engine that closes more sales.
#
# Differentiation line (use in every cold call):
# "Most AI companies just sell you another standalone tool.
#  We turn everything you already have into one unified engine."
#
# Rules:
# - Lead with THEIR pain (fragmentation), not our features
# - Question-driven, not monologue
# - One clear CTA per script
# - 60-90 seconds max for cold calls

# The core cold call framework (industry-agnostic)
COLD_CALL_FRAMEWORK = {
    "greeting": "Hi {contact}, this is William with Marceau Solutions. How's your day going so far?",
    "bridge": "I'll keep this to 45 seconds.",
    "pain": "We've been working with {industry} businesses that already use things like automated text-backs and call handling. What we keep hearing is that those leads end up in different places — chat leads go one way, phone leads another, and nothing actually talks to each other. Leads slip through the cracks and follow-ups get delayed.",
    "qualify": "Does that sound familiar at all?",
    "differentiate": "What we do differently is build a single system that integrates everything you already have. It captures every lead no matter where it comes from, routes it to the right person, sends follow-ups at the right time, and manages the whole process through to closing — without jumping between five different tools.",
    "separator": "Most AI companies just sell you another standalone chatbot or voice agent. We turn all your existing systems into one unified engine that actually closes more sales.",
    "discovery": "{discovery_question}",
    "close": "If you're open to it, I'd love to show you a quick 10-15 minute demo tailored to your setup. What does your calendar look like this week?",
}

VOICEMAIL_SCRIPT = "Hi {contact}, this is William with Marceau Solutions. I help businesses eliminate the lead fragmentation that happens when your automation tools don't talk to each other. We built a system that integrates everything you already use into one platform — captures every lead, follows up automatically, and takes it all the way to closing. If you're seeing leads slip through the cracks, give me a call back at (239) 398-5676. Have a great day."

OBJECTION_HANDLERS = {
    "already_have_ai": "Perfect — most of our clients did too. We don't replace what you have. We connect it all into one system so the pieces actually work together instead of competing. Would you be open to seeing how that looks in 10 minutes?",
    "not_interested": "I totally understand. Most people feel the same way until they see how much revenue is falling through the cracks between their existing tools. Would it be okay if I sent you a one-page case study showing the lift our clients get in lead-to-close conversion?",
    "too_busy": "No problem at all. The whole point of our system is to save you time, not add more work. If you ever notice follow-ups getting missed or leads going to the wrong place, I'm only a call away.",
    "send_info": "Absolutely. I'll send that over today. What email should I use? And just so I send you the right stuff — are you more interested in the lead capture side or the follow-up automation side?",
    "how_much": "It depends on what you need connected, but most of our clients are in the $300-500/month range and see ROI within the first month from leads they were already losing. Want me to put together a quick quote based on your setup?",
}

# Industry-specific pain + discovery questions (plugged into the framework)
PITCH_ANGLES = {
    "no_website": {
        "opener": "I noticed you don't have a website — your business runs on reputation. But anyone searching Google right now can't find you.",
        "hook": "I build simple sites that capture leads automatically. No tech needed on your end.",
        "services": ["Website with booking", "Google Business optimization", "Automated review requests"],
    },
    "systems_gap": {
        "opener": COLD_CALL_FRAMEWORK["pain"],
        "hook": COLD_CALL_FRAMEWORK["differentiate"] + " " + COLD_CALL_FRAMEWORK["separator"],
        "services": ["Unified lead pipeline", "Cross-channel automation", "Real-time lead routing"],
    },
    "redundancy": {
        "opener": "Quick question: if your main person who handles leads was out for a week, would every inquiry still get handled the same way?",
        "hook": "I build systems that run whether you're there or not. Your business handles leads the same on your worst day as your best.",
        "services": ["Automated lead intake", "Self-running follow-up", "After-hours coverage"],
    },
    "speed_to_lead": {
        "opener": "The biggest difference I see between {industry} businesses growing and ones stuck is response time. The fast ones are closing way more.",
        "hook": "I build systems that respond to every lead in under 60 seconds. Your competitor is still checking voicemail while your system already booked the appointment.",
        "services": ["Instant lead response", "Automated booking", "Speed-to-lead pipeline"],
    },
    "has_basic_automation": {
        "opener": "I can see you have some automation — {detail}. Smart move. But are those systems talking to each other?",
        "hook": "I connect your existing tools into one system. Leads flow from first contact to booked appointment without you touching anything.",
        "services": ["System integration", "Automated follow-up", "Pipeline visibility"],
    },
    "competitor_advantage": {
        "opener": "I work with {industry} businesses in Naples. The ones growing fastest aren't spending more on ads — they're the ones where every lead gets handled instantly, automatically.",
        "hook": "Two-week trial, no commitment. If it doesn't work, you owe me nothing.",
        "services": ["Full lead automation", "Follow-up sequences", "Review generation"],
    },
    "default": {
        "opener": COLD_CALL_FRAMEWORK["pain"],
        "hook": COLD_CALL_FRAMEWORK["differentiate"] + " " + COLD_CALL_FRAMEWORK["separator"],
        "services": ["Unified lead capture", "Automated follow-up", "Cross-channel integration"],
    },
}

# Industry-specific language (avoid jargon, speak their language)
INDUSTRY_CONTEXT = {
    "HVAC": {
        "their_world": "service calls, emergency repairs, seasonal demand",
        "their_pain": "leads from multiple channels not connected — Google, phone, Angi, website all going to different places",
        "their_metric": "When a lead comes in from Google and another from a phone call — does that all land in one place?",
        "best_angle": "systems_gap",
    },
    "Medical": {
        "their_world": "patient scheduling, no-shows, insurance verification",
        "their_pain": "new patient inquiries coming from phone, website, Google — handled by different people with no unified tracking",
        "their_metric": "If your front desk person is out sick, does every new patient inquiry still get handled?",
        "best_angle": "redundancy",
    },
    "Real Estate": {
        "their_world": "listings, showings, buyer inquiries, time-sensitive leads",
        "their_pain": "leads going cold because follow-up takes too long or falls through cracks between systems",
        "their_metric": "How fast does a new inquiry get a response — and is that consistent even when you're in a showing?",
        "best_angle": "speed_to_lead",
    },
    "Restaurant": {
        "their_world": "reservations, catering inquiries, reviews",
        "their_pain": "catering and event inquiries getting lost between phone, email, and DMs",
        "their_metric": "When a catering inquiry comes in on a busy Friday night, what happens to it?",
        "best_angle": "systems_gap",
    },
    "Legal": {
        "their_world": "consultations, case intake, client communication",
        "their_pain": "potential clients going to whoever responds first — speed to lead is everything",
        "their_metric": "When someone fills out your contact form at 9 PM, how fast do they hear back?",
        "best_angle": "speed_to_lead",
    },
    "Salon": {
        "their_world": "appointments, rebooking, product sales, reviews",
        "their_pain": "no-shows, rebooking gaps, new client inquiries handled inconsistently",
        "their_metric": "When a new client inquires, does the same follow-up happen every time — or does it depend on who's at the desk?",
        "best_angle": "redundancy",
    },
    "Med Spa": {
        "their_world": "consultations, treatment plans, high-value bookings",
        "their_pain": "high-value consultation requests handled inconsistently — some get fast follow-up, some don't",
        "their_metric": "When a $3,000 treatment inquiry comes in, is the follow-up the same whether it's Monday morning or Saturday night?",
        "best_angle": "redundancy",
    },
    "Auto": {
        "their_world": "service appointments, parts inquiries, fleet accounts",
        "their_pain": "customer communication scattered across phone, text, email — no single view",
        "their_metric": "How do your customers know when their car is ready — and how many calls does that take?",
        "best_angle": "systems_gap",
    },
    "Roofing": {
        "their_world": "estimates, storm damage calls, insurance claims, subcontractor coordination",
        "their_pain": "post-storm call surges that overwhelm your team — leads lost because you can't answer fast enough",
        "their_metric": "After the last big storm, how many calls did you miss in the first 48 hours?",
        "best_angle": "speed_to_lead",
    },
    "Plumbing": {
        "their_world": "emergency calls, scheduled maintenance, estimates",
        "their_pain": "emergency calls after hours going to voicemail while competitors answer",
        "their_metric": "When someone has a burst pipe at midnight, what happens when they call you?",
        "best_angle": "redundancy",
    },
    "Chiropractic": {
        "their_world": "patient scheduling, treatment plans, follow-up appointments",
        "their_pain": "new patient calls coming in during adjustments — front desk can't always answer",
        "their_metric": "How many new patient calls come in while you're with a patient — and what happens to those?",
        "best_angle": "redundancy",
    },
    "Electrical": {
        "their_world": "service calls, estimates, permit coordination, emergency work",
        "their_pain": "leads from multiple sources not tracked in one place",
        "their_metric": "When you get a call, a Google inquiry, and a referral in the same day — does all of that land in one system?",
        "best_angle": "systems_gap",
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
        "SELECT channel, message_summary, response, created_at FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC",
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

    if not website or website.strip() == "" or website.strip() == "None":
        # Only use no_website if research explicitly confirmed it
        if "no website" in combined or "doesn't have a site" in combined or "no site" in combined:
            return "no_website"

    # Use industry default or systems_gap (safest general angle)
    ctx = INDUSTRY_CONTEXT.get(industry, {})
    return ctx.get("best_angle", "systems_gap")


def generate_pitch_brief(deal: dict) -> dict:
    """Generate a pitch brief that uses ACTUAL conversation history.

    If we've talked to this person before, the script reflects that.
    Never generate a cold opener for someone we've had a real conversation with.
    """

    outreach_history = deal.get("outreach_history", [])
    industry = deal.get("industry", "Other")
    industry_ctx = INDUSTRY_CONTEXT.get(industry, {})
    next_action = deal.get("next_action", "") or ""

    # Analyze what actually happened with this lead
    has_conversation = False
    last_response = ""
    last_response_detail = ""
    contact_name = deal.get("contact_name", "") or ""
    channels_used = set()

    for o in outreach_history:
        channels_used.add(o.get("channel", ""))
        resp = (o.get("response") or "").strip()
        summary = (o.get("message_summary") or "").strip()
        if resp:
            has_conversation = True
            last_response = resp
            last_response_detail = f"{o.get('channel', '')}: {summary[:40]} -> {resp[:60]}"

    # --- WARM LEAD: We've spoken, they responded ---
    if has_conversation:
        opener, hook, discovery_q, close = _build_warm_script(
            deal, last_response, contact_name, next_action, industry_ctx
        )
        angle_key = "warm_followup"
    else:
        # --- COLD LEAD: Never spoken, use template ---
        angle_key = determine_pitch_angle(deal)
        angle = PITCH_ANGLES.get(angle_key, PITCH_ANGLES["default"])

        notes = (deal.get("notes", "") or "").lower()
        if "text-back" in notes:
            detail = "a missed-call text-back system"
        elif "crm" in notes:
            detail = "a CRM for tracking leads"
        elif "automated" in notes:
            detail = "some automated follow-up"
        else:
            detail = "some basic automation"

        # Format industry name naturally
        ind_name = industry.split("/")[0].strip().lower() if "/" in industry else industry.lower()
        if ind_name in ("other", "none", ""):
            ind_name = "local"
        elif ind_name == "hvac":
            ind_name = "HVAC"
        elif ind_name == "med spa":
            ind_name = "med spa"

        opener = angle["opener"].format(
            industry=ind_name,
            detail=detail,
        )
        hook = angle["hook"]
        discovery_q = industry_ctx.get("their_metric", "When a lead comes in from Google and another from a phone call — does all of that land in one place, or are you checking multiple things?")
        close = "If you're open to it, I'd love to show you a quick 10-15 minute demo tailored to your setup. What does your calendar look like this week?"

    # Determine services based on angle
    if angle_key == "warm_followup":
        services = _services_from_context(deal, last_response, industry_ctx)
    else:
        angle = PITCH_ANGLES.get(angle_key, PITCH_ANGLES["default"])
        services = angle["services"]

    # Build voicemail script (for cold leads only)
    contact_first = contact_name.split("(")[0].strip().split()[0] if contact_name and contact_name not in ("Unknown", "the owner", "") else "there"
    voicemail = VOICEMAIL_SCRIPT.format(contact=contact_first) if not has_conversation else ""

    # Generate full personalized script incorporating differentiation
    full_script = _build_full_personalized_script(deal, opener, hook, discovery_q, close, industry_ctx, has_conversation)

    brief = {
        "company": deal.get("company", "Unknown"),
        "contact": contact_name or "the owner",
        "phone": deal.get("contact_phone", ""),
        "industry": industry,
        "lead_score": deal.get("lead_score", 0),
        "win_probability": deal.get("win_probability", 0),
        "angle": angle_key,
        "is_warm": has_conversation,
        "pitch": {
            "opener": opener,
            "hook": hook,
            "discovery_question": discovery_q,
            "services_to_mention": services,
            "close": close,
            "full_script": full_script,
        },
        "objection_handlers": OBJECTION_HANDLERS,
        "voicemail": voicemail,
        "context": {
            "their_world": industry_ctx.get("their_world", "customer inquiries, follow-ups, scheduling"),
            "their_pain": industry_ctx.get("their_pain", "leads from multiple channels not connected"),
            "last_interaction": last_response_detail if has_conversation else "No prior contact",
            "next_action": next_action,
        },
        "outreach_history": outreach_history,
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


def _build_full_personalized_script(deal, opener, hook, discovery_q, close, industry_ctx, has_conversation):
    """Build a complete, natural script incorporating differentiation and industry pain points."""
    company = deal.get("company", "")
    industry = deal.get("industry", "Other")
    contact_name = deal.get("contact_name", "") or ""

    # Clean contact name for natural conversation
    if contact_name and contact_name not in ("Unknown", "the owner", ""):
        first_name = contact_name.split()[0]
        greeting = f"Hi {first_name}"
    else:
        greeting = "Hi there"

    # Core differentiation to weave in naturally
    differentiation = "I help businesses eliminate the lead fragmentation that happens when conversational AI agents and missed-call follow-up tools don't talk to each other. We built the only AI automation platform that integrates everything you already have into one seamless system that captures every lead, routes it properly, follows up automatically, and manages the entire sales process all the way to closing — without jumping between five different tools."

    # Industry-specific pain points (1-2 per industry)
    industry_pains = {
        "HVAC": ["leads from Google, phone, and Angi going to different people", "emergency calls after hours getting lost"],
        "Medical": ["new patient inquiries scattered across phone, website, and email", "front desk overwhelmed with coordination"],
        "Real Estate": ["buyer inquiries coming in at all hours from multiple sources", "time-sensitive leads going cold"],
        "Restaurant": ["catering and event inquiries getting lost between channels", "busy periods causing missed opportunities"],
        "Legal": ["potential client calls coming in during consultations", "follow-ups getting delayed"],
        "Salon": ["new client inquiries handled inconsistently", "rebooking gaps from manual processes"],
        "Med Spa": ["high-value consultation requests not followed up consistently", "leads slipping through cracks"],
        "Auto": ["service inquiries scattered across phone, text, and email", "customer communication fragmented"],
        "Roofing": ["post-storm call surges overwhelming the team", "insurance claims and estimates getting lost"],
        "Plumbing": ["emergency calls after hours going unanswered", "estimates and scheduling coordination issues"],
        "Chiropractic": ["new patient calls during adjustments going to voicemail", "follow-up appointment coordination"],
        "Electrical": ["service calls and estimates from multiple channels", "coordination between office and field teams"],
    }

    pains = industry_pains.get(industry, ["leads from different channels not connecting", "follow-ups getting missed"])

    # SPIN-style discovery question (Situation/Problem/Implication/Need-payoff)
    spin_question = f"When {pains[0]}, what typically happens to those leads?"

    # Build the full script
    script_parts = []

    # Greeting and opener
    script_parts.append(f"{greeting}, this is William with Marceau Solutions. How's your day going so far?")
    script_parts.append("")
    script_parts.append("GREETING RESPONSE: (Wait for answer, then...)")
    script_parts.append("")
    script_parts.append(f"I'll keep this to 60 seconds. {opener}")
    script_parts.append("")
    script_parts.append("INDUSTRY-SPECIFIC PAIN:")
    script_parts.append(f"For {industry.lower()} businesses like {company}, I see two big pain points:")
    script_parts.append(f"1. {pains[0]}")
    if len(pains) > 1:
        script_parts.append(f"2. {pains[1]}")
    script_parts.append("")
    script_parts.append("DIFFERENTIATION:")
    script_parts.append(differentiation)
    script_parts.append("")
    script_parts.append("DISCOVERY QUESTION:")
    script_parts.append(f"{spin_question}")
    script_parts.append("")
    script_parts.append("CLOSE:")
    script_parts.append(close)

    return "\n".join(script_parts)


def _build_warm_script(deal, last_response, contact_name, next_action, industry_ctx):
    """Build a script for someone we've ALREADY talked to."""
    company = deal.get("company", "")
    resp_lower = last_response.lower()
    # Clean contact name — use first name only for natural conversation
    raw_name = contact_name if contact_name and contact_name not in ("Unknown", "the owner", "") else ""
    if raw_name and "(" in raw_name:
        raw_name = raw_name.split("(")[0].strip()
    # Use first name only
    name_part = raw_name.split()[0] if raw_name else ""

    # Also check the message_summary for context (some details are there, not in response)
    last_summary = ""
    for o in deal.get("outreach_history", []):
        s = (o.get("message_summary") or "").strip()
        if s:
            last_summary = s
            break  # most recent first
    combined_context = resp_lower + " " + last_summary.lower()

    # Tailor based on what happened last — ORDER MATTERS, most specific first
    if any(kw in combined_context for kw in ["co-dev", "partner", "1099", "contract", "redundan"]):
        opener = f"Hey {name_part or 'there'}, it's William — following up on our conversation about working together."
        hook = "I've been thinking about what we discussed. There's a real opportunity here."
        discovery_q = "What does your timeline look like for getting started?"
        close = "Want to map out the details this week?"

    elif "called back" in combined_context or "they called" in combined_context:
        opener = f"Hey {name_part or 'there'}, it's William — thanks for calling back the other day. Appreciated the conversation."
        hook = "Wanted to follow up and see if there's a good next step."
        discovery_q = "Have you had a chance to think about what we talked about?"
        close = "Would a quick proposal or a short demo be more useful?"

    elif "interested" in resp_lower and "not interested" not in resp_lower:
        opener = f"Hey {name_part or 'there'}, it's William — we spoke the other day and you mentioned you'd be open to hearing more."
        hook = "I put together a quick overview of what the system would look like for your business specifically."
        discovery_q = "What's the biggest bottleneck you're dealing with right now?"
        close = "When works best for a 15-minute walkthrough this week?"

    elif "gave email" in resp_lower or "email" in resp_lower:
        opener = f"Hey {name_part or 'there'}, it's William — sent over that info you asked for. Wanted to make sure you got it."
        hook = "Happy to walk through it live if that's easier than reading."
        discovery_q = "Did you get a chance to look at what I sent?"
        close = "Want me to walk you through it in a quick screen share?"

    elif "voicemail" in resp_lower:
        opener = f"Hey {name_part or 'there'}, it's William from Marceau Solutions — left you a voicemail the other day."
        hook = "I'll keep it quick — I help local businesses make sure no inquiry falls through the cracks."
        discovery_q = industry_ctx.get("their_metric", "When leads come in from different places, does that all land in one system?")
        close = "If it sounds relevant, I can show you in 15 minutes. If not, no worries."

    elif "not ready" in resp_lower or "future" in resp_lower:
        opener = f"Hey {name_part or 'there'}, it's William — just checking in. I know the timing wasn't right last time."
        hook = "Not here to push. Just wanted to see if anything's changed on your end."
        discovery_q = "Is this something your team is actively trying to solve this quarter?"
        close = "Want me to check back in a month, or is there a better time?"

    else:
        opener = f"Hey {name_part or 'there'}, it's William from Marceau Solutions — we connected recently."
        hook = "Wanted to follow up and see if there's anything I can help with."
        discovery_q = industry_ctx.get("their_metric", "When leads come in from different channels, does that all land in one system?")
        close = "Would you be open to a quick call this week?"

    # If there's a specific next_action, override the close
    if next_action and next_action not in ("Follow-up call", "Re-email with value-add", "Follow-up email/call", "Follow-up email"):
        close = f"[Per pipeline: {next_action}]"

    return opener, hook, discovery_q, close


def _services_from_context(deal, last_response, industry_ctx):
    """Determine relevant services based on conversation context."""
    resp_lower = last_response.lower()
    notes = (deal.get("notes", "") or "").lower()
    combined = resp_lower + " " + notes

    if "missed call" in combined or "after hours" in combined:
        return ["24/7 call answering", "Missed-call text-back", "After-hours coverage"]
    elif "website" in combined:
        return ["Website with booking", "Google Business optimization", "Online lead capture"]
    elif "leads" in combined or "follow up" in combined:
        return ["Lead capture system", "Automated follow-up", "Pipeline dashboard"]
    elif "review" in combined:
        return ["Automated review requests", "Review management", "Reputation monitoring"]
    else:
        return ["Lead capture", "Automated follow-up", "After-hours coverage"]


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
                    "SELECT channel, message_summary, response, created_at FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC LIMIT 5",
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
            WHERE stage IN ('Intake', 'Contacted', 'Qualified')
            AND contact_phone IS NOT NULL AND contact_phone != ''
            AND id NOT IN (SELECT DISTINCT deal_id FROM outreach_log WHERE channel = 'Call' AND deal_id IS NOT NULL)
            ORDER BY lead_score DESC
            LIMIT ?
        """, (remaining,)).fetchall()
        for d in uncalled:
            if d["id"] not in seen:
                deal = dict(d)
                deal["outreach_history"] = [
                    dict(o) for o in conn.execute(
                        "SELECT channel, message_summary, response, created_at FROM outreach_log WHERE deal_id = ? ORDER BY created_at DESC LIMIT 5",
                        (d["id"],)
                    ).fetchall()
                ]
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
