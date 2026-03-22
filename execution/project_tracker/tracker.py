#!/usr/bin/env python3.11
"""
Project & API Usage Tracker for Marceau Solutions
Tracks API usage, costs, and website metrics per project.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import requests

# Add parent path for shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv('/home/clawdbot/dev-sandbox/.env')

CONFIG_PATH = Path(__file__).parent / "config.json"
USAGE_LOG_PATH = Path(__file__).parent / "usage_log.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_usage_log():
    if USAGE_LOG_PATH.exists():
        with open(USAGE_LOG_PATH) as f:
            return json.load(f)
    return {"entries": [], "daily_totals": {}}


def save_usage_log(log):
    with open(USAGE_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# ============== API Usage Fetchers ==============

def get_anthropic_usage() -> dict:
    """Fetch Anthropic API usage (requires admin API key)"""
    # Anthropic doesn't have a public usage API yet
    # Track locally via request logging instead
    return {"provider": "anthropic", "status": "local_tracking_only"}


def get_twilio_usage() -> dict:
    """Fetch Twilio SMS usage"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        return {"provider": "twilio", "error": "missing_credentials"}
    
    try:
        # Get this month's usage
        today = datetime.now()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Usage/Records/ThisMonth.json"
        response = requests.get(url, auth=(account_sid, auth_token))
        
        if response.status_code == 200:
            data = response.json()
            usage_records = data.get("usage_records", [])
            
            sms_usage = next((r for r in usage_records if r["category"] == "sms"), None)
            
            return {
                "provider": "twilio",
                "period": "this_month",
                "sms_count": int(sms_usage["count"]) if sms_usage else 0,
                "cost_usd": float(sms_usage["price"]) if sms_usage else 0,
                "fetched_at": datetime.now().isoformat()
            }
        else:
            return {"provider": "twilio", "error": f"api_error_{response.status_code}"}
    except Exception as e:
        return {"provider": "twilio", "error": str(e)}


def get_elevenlabs_usage() -> dict:
    """Fetch ElevenLabs character usage"""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        return {"provider": "elevenlabs", "error": "missing_credentials"}
    
    try:
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": api_key}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "provider": "elevenlabs",
                "characters_used": data.get("character_count", 0),
                "characters_limit": data.get("character_limit", 0),
                "characters_remaining": data.get("character_limit", 0) - data.get("character_count", 0),
                "tier": data.get("tier", "unknown"),
                "fetched_at": datetime.now().isoformat()
            }
        else:
            return {"provider": "elevenlabs", "error": f"api_error_{response.status_code}"}
    except Exception as e:
        return {"provider": "elevenlabs", "error": str(e)}


def get_stripe_usage() -> dict:
    """Fetch Stripe transaction summary"""
    api_key = os.getenv("STRIPE_SECRET_KEY")
    
    if not api_key:
        return {"provider": "stripe", "error": "missing_credentials"}
    
    try:
        import stripe
        stripe.api_key = api_key
        
        # Get balance
        balance = stripe.Balance.retrieve()
        
        # Get recent charges
        today = datetime.now()
        month_start = int(today.replace(day=1, hour=0, minute=0, second=0).timestamp())
        charges = stripe.Charge.list(created={"gte": month_start}, limit=100)
        
        total_revenue = sum(c.amount for c in charges.data if c.paid) / 100
        
        return {
            "provider": "stripe",
            "period": "this_month",
            "charges_count": len(charges.data),
            "revenue_usd": total_revenue,
            "balance_available": sum(b.amount for b in balance.available) / 100,
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"provider": "stripe", "error": str(e)}


# ============== Main Functions ==============

def fetch_all_usage() -> dict:
    """Fetch usage from all trackable APIs"""
    return {
        "timestamp": datetime.now().isoformat(),
        "twilio": get_twilio_usage(),
        "elevenlabs": get_elevenlabs_usage(),
        "stripe": get_stripe_usage(),
    }


def log_api_call(project_id: str, api: str, endpoint: str, cost: float = 0):
    """Log an individual API call (for local tracking)"""
    log = load_usage_log()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "project": project_id,
        "api": api,
        "endpoint": endpoint,
        "cost": cost
    }
    
    log["entries"].append(entry)
    
    # Update daily totals
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in log["daily_totals"]:
        log["daily_totals"][today] = {}
    if project_id not in log["daily_totals"][today]:
        log["daily_totals"][today][project_id] = {"calls": 0, "cost": 0}
    
    log["daily_totals"][today][project_id]["calls"] += 1
    log["daily_totals"][today][project_id]["cost"] += cost
    
    # Keep only last 30 days of entries
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    log["entries"] = [e for e in log["entries"] if e["timestamp"] > cutoff]
    
    save_usage_log(log)


def generate_report(days: int = 7) -> str:
    """Generate a usage report for the last N days"""
    config = load_config()
    log = load_usage_log()
    
    # Fetch current API usage
    current_usage = fetch_all_usage()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    report = []
    report.append(f"📊 **API & Project Usage Report**")
    report.append(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    report.append("")
    
    # API Provider Status
    report.append("**API Provider Usage:**")
    
    if "error" not in current_usage.get("twilio", {}):
        twilio = current_usage["twilio"]
        report.append(f"• Twilio: {twilio.get('sms_count', 0)} SMS (${twilio.get('cost_usd', 0):.2f})")
    
    if "error" not in current_usage.get("elevenlabs", {}):
        el = current_usage["elevenlabs"]
        pct = (el.get('characters_used', 0) / el.get('characters_limit', 1)) * 100
        report.append(f"• ElevenLabs: {el.get('characters_used', 0):,}/{el.get('characters_limit', 0):,} chars ({pct:.1f}%)")
    
    if "error" not in current_usage.get("stripe", {}):
        stripe_data = current_usage["stripe"]
        report.append(f"• Stripe: {stripe_data.get('charges_count', 0)} charges, ${stripe_data.get('revenue_usd', 0):.2f} revenue")
    
    report.append("")
    
    # Project breakdown from local logs
    report.append("**Project Activity (Local Logs):**")
    
    project_totals = {}
    for date_str, projects in log.get("daily_totals", {}).items():
        if date_str >= start_date.strftime("%Y-%m-%d"):
            for project_id, data in projects.items():
                if project_id not in project_totals:
                    project_totals[project_id] = {"calls": 0, "cost": 0}
                project_totals[project_id]["calls"] += data["calls"]
                project_totals[project_id]["cost"] += data["cost"]
    
    if project_totals:
        for project_id, data in sorted(project_totals.items(), key=lambda x: x[1]["calls"], reverse=True):
            project_name = config["projects"].get(project_id, {}).get("name", project_id)
            report.append(f"• {project_name}: {data['calls']} calls (${data['cost']:.2f})")
    else:
        report.append("• No local API calls logged yet")
    
    report.append("")
    report.append("_Use `log_api_call(project_id, api, endpoint, cost)` to track API calls per project._")
    
    return "\n".join(report)


def list_projects() -> str:
    """List all registered projects"""
    config = load_config()
    
    lines = ["**Registered Projects:**", ""]
    
    for project_id, info in config["projects"].items():
        status_emoji = "🟢" if info["status"] == "active" or info["status"] == "live" else "🟡" if info["status"] == "demo" else "⚪"
        apis = ", ".join(info.get("apis", [])) or "none"
        lines.append(f"{status_emoji} **{info['name']}** (`{project_id}`)")
        lines.append(f"   Type: {info['type']} | APIs: {apis}")
        if info.get("url"):
            lines.append(f"   URL: {info['url']}")
        lines.append("")
    
    return "\n".join(lines)


# ============== CLI ==============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Project & API Usage Tracker")
    parser.add_argument("--report", action="store_true", help="Generate usage report")
    parser.add_argument("--days", type=int, default=7, help="Days to include in report")
    parser.add_argument("--list", action="store_true", help="List all projects")
    parser.add_argument("--fetch", action="store_true", help="Fetch current API usage")
    parser.add_argument("--log", nargs=4, metavar=("PROJECT", "API", "ENDPOINT", "COST"),
                        help="Log an API call")
    
    args = parser.parse_args()
    
    if args.report:
        print(generate_report(args.days))
    elif args.list:
        print(list_projects())
    elif args.fetch:
        usage = fetch_all_usage()
        print(json.dumps(usage, indent=2))
    elif args.log:
        project, api, endpoint, cost = args.log
        log_api_call(project, api, endpoint, float(cost))
        print(f"Logged: {project} -> {api}:{endpoint} (${cost})")
    else:
        parser.print_help()
