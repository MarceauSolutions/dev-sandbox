#!/usr/bin/env python3
"""
Generate prioritized lead lists by tier and outreach type.
Outputs lists ready for phone blitz, email campaigns, or in-person visits.
"""

import sqlite3
from datetime import datetime

DB_PATH = '/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db'


def get_tier_1_phone_leads(limit: int = 20) -> list:
    """Get highest priority leads for phone outreach — NEVER CALLED."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
               d.industry, d.lead_score, d.stage, d.phone_dependency
        FROM deals d
        WHERE d.stage IN ('Intake', 'Contacted')
        AND d.contact_phone IS NOT NULL AND d.contact_phone != ''
        AND d.company NOT IN (SELECT DISTINCT company FROM outreach_log WHERE channel = 'Call')
        ORDER BY d.lead_score DESC, d.phone_dependency DESC
        LIMIT ?
    """, (limit,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_tier_2_phone_leads(limit: int = 20) -> list:
    """Get second priority leads for phone outreach — NEVER CALLED."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
               d.industry, d.lead_score, d.stage
        FROM deals d
        WHERE d.stage IN ('Intake', 'Contacted')
        AND d.contact_phone IS NOT NULL AND d.contact_phone != ''
        AND d.company NOT IN (SELECT DISTINCT company FROM outreach_log WHERE channel = 'Call')
        ORDER BY d.lead_score DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_email_leads(limit: int = 30) -> list:
    """Get leads best suited for email outreach."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_email, d.industry, 
               d.lead_score, d.stage, d.email_template
        FROM deals d
        WHERE d.stage IN ('Intake')
        AND d.outreach_method = 'email'
        AND d.contact_email IS NOT NULL AND d.contact_email != ''
        AND d.contact_email NOT LIKE '%@gmail.com'
        ORDER BY d.lead_score DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_inperson_leads(limit: int = 10) -> list:
    """Get leads best suited for in-person visits."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # In-person leads: high score, local, phone-dependent businesses
    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_phone, d.industry,
               d.lead_score, d.stage, d.city
        FROM deals d
        WHERE d.stage IN ('Contacted', 'Qualified')
        AND d.lead_score >= 80
        AND d.city = 'Naples'
        ORDER BY d.lead_score DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_warm_leads() -> list:
    """Get leads that have been contacted and showed interest."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
               d.stage, d.next_action, d.next_action_date
        FROM deals d
        WHERE d.stage IN ('Qualified', 'Demo Scheduled', 'Proposal Sent')
        ORDER BY d.stage DESC, d.next_action_date ASC
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def format_phone_list(leads: list, tier: str) -> str:
    """Format leads for phone blitz."""
    if not leads:
        return f"No {tier} leads available for phone outreach."
    
    lines = [f"📞 **{tier} PHONE LIST** ({len(leads)} leads)", ""]
    
    for i, lead in enumerate(leads, 1):
        lines.append(f"**{i}. {lead['company']}**")
        if lead.get('contact_phone'):
            lines.append(f"   📞 {lead['contact_phone']}")
        if lead.get('contact_name'):
            lines.append(f"   👤 {lead['contact_name']}")
        if lead.get('industry'):
            lines.append(f"   🏢 {lead['industry']}")
        lines.append(f"   Score: {lead.get('lead_score', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)


def format_warm_leads(leads: list) -> str:
    """Format warm leads for follow-up."""
    if not leads:
        return "No warm leads in pipeline."
    
    lines = ["🔥 **WARM LEADS** (Priority follow-ups)", ""]
    
    for lead in leads:
        lines.append(f"• **{lead['company']}** ({lead['stage']})")
        if lead.get('contact_name'):
            lines.append(f"  Contact: {lead['contact_name']}")
        if lead.get('contact_phone'):
            lines.append(f"  📞 {lead['contact_phone']}")
        if lead.get('next_action'):
            lines.append(f"  Next: {lead['next_action']}")
        lines.append("")
    
    return "\n".join(lines)


def generate_daily_lists() -> dict:
    """Generate all daily lists."""
    return {
        "tier_1_phone": get_tier_1_phone_leads(15),
        "tier_2_phone": get_tier_2_phone_leads(15),
        "email": get_email_leads(20),
        "inperson": get_inperson_leads(5),
        "warm": get_warm_leads(),
        "generated_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_lead_lists.py t1phone    - Tier 1 phone leads")
        print("  python generate_lead_lists.py t2phone    - Tier 2 phone leads")
        print("  python generate_lead_lists.py email      - Email leads")
        print("  python generate_lead_lists.py inperson   - In-person leads")
        print("  python generate_lead_lists.py warm       - Warm leads")
        print("  python generate_lead_lists.py all        - All lists (JSON)")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "t1phone":
        leads = get_tier_1_phone_leads()
        print(format_phone_list(leads, "TIER 1"))
    elif action == "t2phone":
        leads = get_tier_2_phone_leads()
        print(format_phone_list(leads, "TIER 2"))
    elif action == "email":
        leads = get_email_leads()
        print(f"📧 EMAIL LEADS: {len(leads)} available")
        for lead in leads[:10]:
            print(f"  • {lead['company']} - {lead.get('contact_email', 'No email')}")
    elif action == "inperson":
        leads = get_inperson_leads()
        print(f"🚗 IN-PERSON LEADS: {len(leads)} available")
        for lead in leads:
            print(f"  • {lead['company']} ({lead.get('industry', 'Unknown')})")
    elif action == "warm":
        leads = get_warm_leads()
        print(format_warm_leads(leads))
    elif action == "all":
        print(json.dumps(generate_daily_lists(), indent=2, default=str))
    else:
        print(f"Unknown action: {action}")
