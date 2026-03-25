#!/usr/bin/env python3.11
"""
Unified Outreach Tracker - Cross-references ALL touchpoints

Consolidates:
- Apollo emails (sends, opens, clicks, replies)
- Call log (outcomes, notes)
- In-person visits
- Pipeline stages
- SMS (if configured)

Provides:
- /lead/[company] - Full history for a lead
- /leads/hot - Highest engagement leads
- /leads/next-actions - Prioritized action list
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv("/home/clawdbot/dev-sandbox/.env")

DATA_DIR = "/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data"
CALL_LOG_PATH = os.path.join(DATA_DIR, "call_log.json")
VISIT_LOG_PATH = os.path.join(DATA_DIR, "visit_log.json")
PIPELINE_PATH = os.path.join(DATA_DIR, "pipeline.json")

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")


@dataclass
class TouchPoint:
    """A single interaction with a lead."""
    channel: str  # email, call, visit, sms
    action: str   # sent, opened, clicked, replied, called, visited
    outcome: str  # result/status
    date: str     # YYYY-MM-DD
    timestamp: str  # ISO timestamp
    notes: str
    contact_name: str
    is_positive: bool


@dataclass
class LeadProfile:
    """Complete profile of a lead with all touchpoints."""
    company: str
    contact_name: str
    phone: str
    email: str
    address: str
    pipeline_stage: str
    touchpoints: List[TouchPoint]
    engagement_score: float
    last_contact: str
    next_action: str
    next_action_reason: str


def load_json_file(path: str) -> Dict:
    """Load a JSON file safely."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def get_call_touchpoints(company: str) -> List[TouchPoint]:
    """Get call history for a company."""
    data = load_json_file(CALL_LOG_PATH)
    touchpoints = []
    
    company_lower = company.lower()
    
    for call in data.get("calls", []):
        if company_lower in call.get("business", "").lower():
            touchpoints.append(TouchPoint(
                channel="call",
                action="called",
                outcome=call.get("outcome", ""),
                date=call.get("date", ""),
                timestamp=call.get("timestamp", ""),
                notes=call.get("notes", ""),
                contact_name=call.get("contact_name", ""),
                is_positive=call.get("is_positive_signal", False)
            ))
    
    return touchpoints


def get_visit_touchpoints(company: str) -> List[TouchPoint]:
    """Get visit history for a company."""
    data = load_json_file(VISIT_LOG_PATH)
    touchpoints = []
    
    company_lower = company.lower()
    
    for visit in data.get("visits", []):
        if company_lower in visit.get("business", "").lower():
            is_positive = visit.get("outcome", "").lower() in ["interested", "positive", "meeting_booked", "proposal"]
            touchpoints.append(TouchPoint(
                channel="visit",
                action="visited",
                outcome=visit.get("outcome", ""),
                date=visit.get("date", ""),
                timestamp=visit.get("timestamp", ""),
                notes=visit.get("notes", ""),
                contact_name="",
                is_positive=is_positive
            ))
    
    return touchpoints


def get_apollo_touchpoints(company: str) -> List[TouchPoint]:
    """Get email touchpoints from Apollo for a company."""
    if not APOLLO_API_KEY:
        return []
    
    touchpoints = []
    
    try:
        # Search for account
        url = "https://api.apollo.io/api/v1/accounts/search"
        headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
        payload = {"q_organization_name": company, "per_page": 5}
        
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        accounts = resp.json().get("accounts", [])
        
        if not accounts:
            return []
        
        account_id = accounts[0].get("id")
        
        # Get activities for this account
        url = "https://api.apollo.io/api/v1/activities/search"
        payload = {
            "account_id": account_id,
            "per_page": 50,
            "sort_by": "activity_date",
            "sort_ascending": False
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        activities = resp.json().get("activities", [])
        
        for act in activities:
            act_type = act.get("type", "")
            
            action_map = {
                "email_sent": ("email", "sent", False),
                "email_open": ("email", "opened", True),
                "email_click": ("email", "clicked", True),
                "email_reply": ("email", "replied", True),
                "call": ("call", "logged", False),
            }
            
            if act_type in action_map:
                channel, action, is_positive = action_map[act_type]
                activity_date = act.get("activity_date", "")
                
                touchpoints.append(TouchPoint(
                    channel=channel,
                    action=action,
                    outcome=act_type,
                    date=activity_date[:10] if activity_date else "",
                    timestamp=activity_date,
                    notes="",
                    contact_name=act.get("contact", {}).get("name", ""),
                    is_positive=is_positive
                ))
    
    except Exception as e:
        print(f"Apollo error: {e}")
    
    return touchpoints


def get_pipeline_info(company: str) -> Dict[str, Any]:
    """Get pipeline stage info for a company."""
    data = load_json_file(PIPELINE_PATH)
    
    company_lower = company.lower()
    
    for deal in data.get("deals", []):
        if company_lower in deal.get("company", "").lower():
            return {
                "stage": deal.get("stage", "Unknown"),
                "contact_name": deal.get("contact_name", ""),
                "phone": deal.get("phone", ""),
                "email": deal.get("email", ""),
                "address": deal.get("address", ""),
                "notes": deal.get("notes", "")
            }
    
    return {"stage": "Not in pipeline"}


def calculate_engagement_score(touchpoints: List[TouchPoint]) -> float:
    """Calculate engagement score based on touchpoints."""
    score = 0.0
    
    # Points for each type of engagement
    points = {
        ("email", "replied"): 15,
        ("email", "clicked"): 10,
        ("email", "opened"): 5,
        ("email", "sent"): 1,
        ("call", "called"): 3,
        ("visit", "visited"): 5,
    }
    
    # Positive outcome bonus
    positive_bonus = 10
    
    for tp in touchpoints:
        key = (tp.channel, tp.action)
        score += points.get(key, 1)
        
        if tp.is_positive:
            score += positive_bonus
    
    # Recency bonus
    if touchpoints:
        try:
            latest = max(tp.timestamp for tp in touchpoints if tp.timestamp)
            days_ago = (datetime.utcnow() - datetime.fromisoformat(latest.replace('Z', '+00:00').replace('+00:00', ''))).days
            if days_ago <= 1:
                score *= 1.5
            elif days_ago <= 3:
                score *= 1.3
            elif days_ago <= 7:
                score *= 1.1
        except:
            pass
    
    return round(score, 1)


def determine_next_action(touchpoints: List[TouchPoint], pipeline_stage: str) -> tuple[str, str]:
    """Determine the best next action for a lead."""
    if not touchpoints:
        return "Initial outreach", "No prior contact"
    
    # Sort by timestamp
    sorted_tp = sorted([tp for tp in touchpoints if tp.timestamp], 
                       key=lambda x: x.timestamp, reverse=True)
    
    if not sorted_tp:
        return "Follow up", "No recent activity"
    
    latest = sorted_tp[0]
    
    # Decision tree
    if latest.is_positive:
        if latest.channel == "email" and latest.action == "replied":
            return "Schedule call/meeting", f"Replied to email on {latest.date}"
        elif latest.channel == "call" and latest.outcome in ["interested", "callback"]:
            return "In-person visit", f"Positive call on {latest.date}"
        elif latest.channel == "visit":
            return "Send proposal", f"Visited on {latest.date}"
        else:
            return "Follow up call", f"Positive signal: {latest.outcome}"
    
    # Non-positive recent contact
    if latest.channel == "email":
        if latest.action == "opened":
            return "Call while warm", f"Opened email on {latest.date}"
        elif latest.action == "clicked":
            return "Call immediately", f"Clicked email link on {latest.date}"
        else:
            return "Wait for engagement", f"Email sent {latest.date}"
    
    if latest.channel == "call":
        if latest.outcome == "voicemail":
            return "Try calling again", f"Left voicemail {latest.date}"
        elif latest.outcome == "no_answer":
            return "Call different time", f"No answer {latest.date}"
        elif latest.outcome == "gatekeeper":
            return "Try direct line/email", f"Hit gatekeeper {latest.date}"
        else:
            return "Move to next lead", f"Not interested {latest.date}"
    
    return "Review and decide", f"Last contact: {latest.date}"


def get_lead_profile(company: str) -> LeadProfile:
    """Get complete profile for a lead."""
    # Gather all touchpoints
    touchpoints = []
    touchpoints.extend(get_call_touchpoints(company))
    touchpoints.extend(get_visit_touchpoints(company))
    touchpoints.extend(get_apollo_touchpoints(company))
    
    # Sort by timestamp
    touchpoints.sort(key=lambda x: x.timestamp or "", reverse=True)
    
    # Get pipeline info
    pipeline = get_pipeline_info(company)
    
    # Calculate engagement
    engagement_score = calculate_engagement_score(touchpoints)
    
    # Get last contact
    last_contact = touchpoints[0].date if touchpoints else "Never"
    
    # Determine next action
    next_action, reason = determine_next_action(touchpoints, pipeline.get("stage", ""))
    
    return LeadProfile(
        company=company,
        contact_name=pipeline.get("contact_name", ""),
        phone=pipeline.get("phone", ""),
        email=pipeline.get("email", ""),
        address=pipeline.get("address", ""),
        pipeline_stage=pipeline.get("stage", "Not in pipeline"),
        touchpoints=touchpoints,
        engagement_score=engagement_score,
        last_contact=last_contact,
        next_action=next_action,
        next_action_reason=reason
    )


def format_lead_profile(profile: LeadProfile) -> str:
    """Format lead profile for display."""
    lines = [
        f"📊 **{profile.company}**",
        f"Stage: {profile.pipeline_stage}",
        f"Engagement Score: {profile.engagement_score}",
        f"Last Contact: {profile.last_contact}",
        ""
    ]
    
    if profile.contact_name:
        lines.append(f"👤 {profile.contact_name}")
    if profile.phone:
        lines.append(f"📞 {profile.phone}")
    if profile.email:
        lines.append(f"✉️ {profile.email}")
    
    lines.append("")
    lines.append(f"**➡️ Next Action:** {profile.next_action}")
    lines.append(f"   Reason: {profile.next_action_reason}")
    
    if profile.touchpoints:
        lines.append("")
        lines.append("**📜 History:**")
        for tp in profile.touchpoints[:10]:  # Last 10
            emoji = "🟢" if tp.is_positive else "⚪"
            lines.append(f"  {emoji} {tp.date}: {tp.channel} {tp.action} — {tp.outcome}")
            if tp.notes:
                lines.append(f"      Notes: {tp.notes}")
    
    return "\n".join(lines)


def get_hot_leads(limit: int = 10) -> List[LeadProfile]:
    """Get leads with highest engagement scores."""
    # This would ideally query all leads - for now, use what we have
    all_companies = set()
    
    # Get companies from call log
    call_data = load_json_file(CALL_LOG_PATH)
    for call in call_data.get("calls", []):
        all_companies.add(call.get("business", ""))
    
    # Get companies from visit log
    visit_data = load_json_file(VISIT_LOG_PATH)
    for visit in visit_data.get("visits", []):
        all_companies.add(visit.get("business", ""))
    
    # Get companies from pipeline
    pipeline_data = load_json_file(PIPELINE_PATH)
    for deal in pipeline_data.get("deals", []):
        all_companies.add(deal.get("company", ""))
    
    # Build profiles and sort by engagement
    profiles = []
    for company in all_companies:
        if company:
            profile = get_lead_profile(company)
            if profile.engagement_score > 0:
                profiles.append(profile)
    
    profiles.sort(key=lambda x: x.engagement_score, reverse=True)
    return profiles[:limit]


def get_next_actions(limit: int = 15) -> List[Dict[str, Any]]:
    """Get prioritized list of next actions across all leads."""
    hot_leads = get_hot_leads(limit=50)
    
    actions = []
    for profile in hot_leads:
        if profile.next_action not in ["Move to next lead", "Wait for engagement"]:
            actions.append({
                "company": profile.company,
                "action": profile.next_action,
                "reason": profile.next_action_reason,
                "score": profile.engagement_score,
                "phone": profile.phone,
                "stage": profile.pipeline_stage
            })
    
    # Sort by score
    actions.sort(key=lambda x: x["score"], reverse=True)
    return actions[:limit]


def format_hot_leads(profiles: List[LeadProfile]) -> str:
    """Format hot leads for display."""
    if not profiles:
        return "🔥 No hot leads yet. Start logging calls and sending emails!"
    
    lines = ["🔥 **HOT LEADS** (by engagement)", ""]
    
    for i, p in enumerate(profiles, 1):
        lines.append(f"{i}. **{p.company}** — Score: {p.engagement_score}")
        lines.append(f"   Stage: {p.pipeline_stage} | Last: {p.last_contact}")
        lines.append(f"   ➡️ {p.next_action}")
        if p.phone:
            lines.append(f"   📞 {p.phone}")
        lines.append("")
    
    return "\n".join(lines)


def format_next_actions(actions: List[Dict]) -> str:
    """Format next actions for display."""
    if not actions:
        return "📋 No pending actions. Great job or need more leads!"
    
    lines = ["📋 **NEXT ACTIONS** (prioritized)", ""]
    
    for i, a in enumerate(actions, 1):
        lines.append(f"{i}. **{a['action']}** — {a['company']}")
        lines.append(f"   {a['reason']}")
        if a.get("phone"):
            lines.append(f"   📞 {a['phone']}")
        lines.append("")
    
    return "\n".join(lines)


# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python unified_tracker.py lead 'Company Name'")
        print("  python unified_tracker.py hot [limit]")
        print("  python unified_tracker.py actions [limit]")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "lead" and len(sys.argv) >= 3:
        company = " ".join(sys.argv[2:])
        profile = get_lead_profile(company)
        print(format_lead_profile(profile))
    
    elif cmd == "hot":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        leads = get_hot_leads(limit)
        print(format_hot_leads(leads))
    
    elif cmd == "actions":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        actions = get_next_actions(limit)
        print(format_next_actions(actions))
