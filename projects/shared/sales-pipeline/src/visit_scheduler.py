#!/usr/bin/env python3.11
"""
In-Person Visit Scheduler - Geographically optimized visit routes

Features:
- Pulls leads with positive signals from call_log, Apollo email data, pipeline
- Optimizes route starting FARTHEST from home base, working back
- Shows WHY each business is on the list
- Integrates with Google Maps for distance calculation

Home base: 2776 Longboat Dr, Naples, FL 34109
"""

import json
import os
import math
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment
load_dotenv("/home/clawdbot/dev-sandbox/.env")

DATA_DIR = "/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data"
CALL_LOG_PATH = os.path.join(DATA_DIR, "call_log.json")
VISIT_LOG_PATH = os.path.join(DATA_DIR, "visit_log.json")
PIPELINE_PATH = os.path.join(DATA_DIR, "pipeline.json")

# Home base coordinates (2776 Longboat Dr, Naples, FL)
HOME_BASE = {
    "address": "2776 Longboat Dr, Naples, FL 34109",
    "lat": 26.2304,
    "lng": -81.8076
}

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


@dataclass
class VisitCandidate:
    """A business that should be visited in person."""
    business_name: str
    address: str
    lat: float
    lng: float
    distance_from_home: float  # miles
    signals: List[str]  # Why they're on the list
    notes: str
    contact_name: str
    phone: str
    priority_score: float  # Higher = more important
    last_contact_date: Optional[str]
    source: str  # call, email, pipeline, manual


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address to lat/lng.
    Uses Google Maps API if available, otherwise returns None.
    """
    if not GOOGLE_MAPS_API_KEY:
        # Fallback: return approximate Naples coordinates with small offset
        # This is a placeholder - in production, always use real geocoding
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        
        if data["status"] == "OK" and data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    return None


def load_call_signals() -> List[Dict[str, Any]]:
    """Load businesses with positive signals from call log."""
    if not os.path.exists(CALL_LOG_PATH):
        return []
    
    with open(CALL_LOG_PATH, 'r') as f:
        data = json.load(f)
    
    # Group by business, keep most recent call
    business_calls = {}
    for call in data.get("calls", []):
        biz = call["business"].lower()
        if biz not in business_calls or call["timestamp"] > business_calls[biz]["timestamp"]:
            business_calls[biz] = call
    
    # Return positive signals
    positive = []
    for call in business_calls.values():
        if call.get("is_positive_signal"):
            positive.append({
                "business": call["business"],
                "signal": f"Call: {call['outcome']}",
                "notes": call.get("notes", ""),
                "contact_name": call.get("contact_name", ""),
                "phone": call.get("phone", ""),
                "date": call.get("date"),
                "source": "call"
            })
    
    return positive


def load_apollo_email_signals() -> List[Dict[str, Any]]:
    """Load businesses with email engagement from Apollo."""
    if not APOLLO_API_KEY:
        return []
    
    signals = []
    
    try:
        # Get recent email activities
        url = "https://api.apollo.io/api/v1/activities/search"
        headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
        payload = {
            "activity_types": ["email_open", "email_click", "email_reply"],
            "per_page": 100,
            "sort_by": "activity_date",
            "sort_ascending": False
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        data = resp.json()
        
        for activity in data.get("activities", []):
            activity_type = activity.get("type", "")
            contact = activity.get("contact", {})
            account = activity.get("account", {})
            
            signal_text = {
                "email_open": "Opened email",
                "email_click": "Clicked email link",
                "email_reply": "Replied to email"
            }.get(activity_type, activity_type)
            
            signals.append({
                "business": account.get("name", contact.get("organization_name", "Unknown")),
                "signal": f"Email: {signal_text}",
                "notes": "",
                "contact_name": contact.get("name", ""),
                "phone": contact.get("phone_number", ""),
                "date": activity.get("activity_date", "")[:10] if activity.get("activity_date") else None,
                "source": "email",
                "address": account.get("street_address", "")
            })
    except Exception as e:
        print(f"Apollo API error: {e}")
    
    return signals


def load_pipeline_prospects() -> List[Dict[str, Any]]:
    """Load prospects from pipeline that should be visited."""
    if not os.path.exists(PIPELINE_PATH):
        return []
    
    with open(PIPELINE_PATH, 'r') as f:
        data = json.load(f)
    
    # Stages that warrant in-person visits
    visit_stages = ["Qualified", "Meeting Booked", "Proposal Sent"]
    
    prospects = []
    for deal in data.get("deals", []):
        if deal.get("stage") in visit_stages:
            prospects.append({
                "business": deal.get("company", "Unknown"),
                "signal": f"Pipeline: {deal.get('stage')}",
                "notes": deal.get("notes", ""),
                "contact_name": deal.get("contact_name", ""),
                "phone": deal.get("phone", ""),
                "date": deal.get("last_activity"),
                "source": "pipeline",
                "address": deal.get("address", "")
            })
    
    return prospects


def calculate_priority_score(signals: List[str], source: str, last_contact_days: int) -> float:
    """Calculate priority score for a visit candidate."""
    score = 0.0
    
    # Signal-based scoring
    signal_scores = {
        "email_reply": 10,
        "meeting_booked": 10,
        "interested": 8,
        "email_click": 7,
        "callback": 6,
        "email_open": 5,
        "spanish_speaker": 5,  # Prepared with translation
        "Proposal Sent": 9,
        "Qualified": 7,
    }
    
    for signal in signals:
        for key, value in signal_scores.items():
            if key.lower() in signal.lower():
                score += value
    
    # Recency bonus (contacted in last 3 days gets bonus)
    if last_contact_days <= 1:
        score += 5
    elif last_contact_days <= 3:
        score += 3
    elif last_contact_days <= 7:
        score += 1
    
    return score


def build_visit_schedule(
    max_visits: int = 10,
    include_sources: List[str] = None
) -> List[VisitCandidate]:
    """
    Build an optimized visit schedule.
    
    Returns list ordered: farthest from home -> closest (so you end near home)
    """
    if include_sources is None:
        include_sources = ["call", "email", "pipeline"]
    
    # Gather all candidates
    all_signals = []
    
    if "call" in include_sources:
        all_signals.extend(load_call_signals())
    
    if "email" in include_sources:
        all_signals.extend(load_apollo_email_signals())
    
    if "pipeline" in include_sources:
        all_signals.extend(load_pipeline_prospects())
    
    # Deduplicate by business name, combining signals
    business_map: Dict[str, Dict] = {}
    
    for sig in all_signals:
        biz_key = sig["business"].lower().strip()
        
        if biz_key not in business_map:
            business_map[biz_key] = {
                "business_name": sig["business"],
                "address": sig.get("address", ""),
                "signals": [],
                "notes": [],
                "contact_name": sig.get("contact_name", ""),
                "phone": sig.get("phone", ""),
                "sources": set(),
                "last_date": sig.get("date")
            }
        
        entry = business_map[biz_key]
        entry["signals"].append(sig["signal"])
        entry["sources"].add(sig["source"])
        
        if sig.get("notes"):
            entry["notes"].append(sig["notes"])
        
        if sig.get("contact_name") and not entry["contact_name"]:
            entry["contact_name"] = sig["contact_name"]
        
        if sig.get("phone") and not entry["phone"]:
            entry["phone"] = sig["phone"]
        
        if sig.get("address") and not entry["address"]:
            entry["address"] = sig["address"]
        
        # Track most recent contact
        if sig.get("date"):
            if not entry["last_date"] or sig["date"] > entry["last_date"]:
                entry["last_date"] = sig["date"]
    
    # Convert to VisitCandidate objects
    candidates = []
    today = datetime.utcnow().date()
    
    for biz_key, data in business_map.items():
        # Calculate days since last contact
        last_contact_days = 999
        if data["last_date"]:
            try:
                last_date = datetime.strptime(data["last_date"][:10], "%Y-%m-%d").date()
                last_contact_days = (today - last_date).days
            except:
                pass
        
        # Calculate priority
        priority = calculate_priority_score(
            data["signals"],
            ",".join(data["sources"]),
            last_contact_days
        )
        
        # Skip low priority
        if priority < 3:
            continue
        
        # Geocode address or use placeholder
        lat, lng = HOME_BASE["lat"], HOME_BASE["lng"]
        distance = 0.0
        
        if data["address"]:
            coords = geocode_address(data["address"])
            if coords:
                lat, lng = coords
                distance = haversine_distance(HOME_BASE["lat"], HOME_BASE["lng"], lat, lng)
            else:
                # Assign random-ish distance for sorting (better than nothing)
                # In production, we'd require valid addresses
                import hashlib
                hash_val = int(hashlib.md5(biz_key.encode()).hexdigest()[:8], 16)
                distance = 1 + (hash_val % 20)  # 1-20 miles
        
        candidates.append(VisitCandidate(
            business_name=data["business_name"],
            address=data["address"] or "Address needed",
            lat=lat,
            lng=lng,
            distance_from_home=distance,
            signals=data["signals"],
            notes="; ".join(data["notes"]) if data["notes"] else "",
            contact_name=data["contact_name"],
            phone=data["phone"],
            priority_score=priority,
            last_contact_date=data["last_date"],
            source=",".join(data["sources"])
        ))
    
    # Sort by priority first, then by distance (farthest first)
    # We want high priority AND farthest first
    candidates.sort(key=lambda x: (-x.priority_score, -x.distance_from_home))
    
    # Take top candidates
    top_candidates = candidates[:max_visits]
    
    # Re-sort by distance: farthest first (so you end at home)
    top_candidates.sort(key=lambda x: -x.distance_from_home)
    
    return top_candidates


def format_visit_schedule(candidates: List[VisitCandidate]) -> str:
    """Format the visit schedule for display."""
    if not candidates:
        return "📋 No visits scheduled. Log some positive calls or wait for email engagement."
    
    lines = [
        f"🚗 **IN-PERSON VISITS** — {datetime.utcnow().strftime('%Y-%m-%d')}",
        f"Route: Farthest → Home (2776 Longboat Dr)",
        f"Total stops: {len(candidates)}",
        ""
    ]
    
    for i, c in enumerate(candidates, 1):
        signal_summary = ", ".join(set(c.signals))
        
        lines.append(f"**{i}. {c.business_name}**")
        lines.append(f"   📍 {c.address}")
        
        if c.phone:
            lines.append(f"   📞 {c.phone}")
        
        if c.contact_name:
            lines.append(f"   👤 {c.contact_name}")
        
        lines.append(f"   🎯 WHY: {signal_summary}")
        
        if c.notes:
            lines.append(f"   📝 Notes: {c.notes}")
        
        lines.append(f"   🚗 ~{c.distance_from_home:.1f} mi from home | Priority: {c.priority_score:.0f}")
        lines.append("")
    
    lines.append("—")
    lines.append("Log visits with: visited [business]: [outcome]")
    
    return "\n".join(lines)


def log_visit(business: str, outcome: str, notes: str = "") -> Dict[str, Any]:
    """Log an in-person visit."""
    if not os.path.exists(VISIT_LOG_PATH):
        data = {"visits": [], "schema_version": "1.0", "created_at": datetime.utcnow().isoformat()}
    else:
        with open(VISIT_LOG_PATH, 'r') as f:
            data = json.load(f)
    
    visit = {
        "id": len(data["visits"]) + 1,
        "business": business.strip(),
        "outcome": outcome.strip(),
        "notes": notes.strip(),
        "timestamp": datetime.utcnow().isoformat(),
        "date": datetime.utcnow().strftime("%Y-%m-%d")
    }
    
    data["visits"].append(visit)
    data["last_updated"] = datetime.utcnow().isoformat()
    
    with open(VISIT_LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    
    return visit


# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python visit_scheduler.py schedule [max_visits]")
        print("  python visit_scheduler.py log 'Business' 'outcome' 'notes'")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "schedule":
        max_visits = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        schedule = build_visit_schedule(max_visits=max_visits)
        print(format_visit_schedule(schedule))
    
    elif cmd == "log" and len(sys.argv) >= 4:
        business = sys.argv[2]
        outcome = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        visit = log_visit(business, outcome, notes)
        print(f"✅ Logged visit: {visit['business']} — {visit['outcome']}")
    
    elif cmd == "test":
        # Test with some sample data
        print("Testing visit scheduler...")
        
        # Add test call
        from call_logger import log_call
        log_call("Test HVAC Company", "interested", "Owner wants demo next week", "John Smith", "239-555-1234")
        log_call("Naples Auto Repair", "spanish_speaker", "Need Spanish materials", "", "239-555-5678")
        
        # Generate schedule
        schedule = build_visit_schedule(max_visits=5)
        print(format_visit_schedule(schedule))
