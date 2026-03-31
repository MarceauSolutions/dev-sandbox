#!/usr/bin/env python3
"""
State Summary Blueprint - Grok Read-Only Endpoint

Provides /state/summary for external agents to query system state.
Read-only, no sensitive data exposed.
"""

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify

# Timezone utilities for Eastern time display (William is in Naples, FL)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "execution"))
    from timezone_utils import now_eastern, format_eastern, EASTERN_TZ
except ImportError:
    # Fallback
    EASTERN_TZ = None
    def now_eastern():
        return datetime.now()
    def format_eastern(dt=None, fmt="%Y-%m-%d %I:%M %p ET"):
        return (dt or datetime.now()).strftime(fmt)

state_summary_bp = Blueprint('state_summary', __name__)

# Data source paths
PIPELINE_DB = Path('/home/clawdbot/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db')
LEARNED_PREFS = Path('/home/clawdbot/dev-sandbox/projects/personal-assistant/data/learned_preferences.json')
GOALS_FILE = Path('/home/clawdbot/dev-sandbox/projects/personal-assistant/data/goals.json')
LOOP_HEALTH = Path('/home/clawdbot/dev-sandbox/projects/lead-generation/logs/loop_health.json')


def get_pipeline_stats() -> dict:
    """Get pipeline statistics from SQLite database."""
    result = {
        "total_deals": 0,
        "by_stage": {},
        "conversion_rate": 0.0
    }
    
    if not PIPELINE_DB.exists():
        return result
    
    try:
        conn = sqlite3.connect(str(PIPELINE_DB))
        cursor = conn.cursor()
        
        # Total deals
        cursor.execute("SELECT COUNT(*) FROM deals")
        result["total_deals"] = cursor.fetchone()[0]
        
        # By stage
        cursor.execute("SELECT stage, COUNT(*) FROM deals GROUP BY stage")
        result["by_stage"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Conversion rate (Qualified + Closed Won / Total * 100)
        qualified = result["by_stage"].get("Qualified", 0)
        closed_won = result["by_stage"].get("Closed Won", 0)
        if result["total_deals"] > 0:
            result["conversion_rate"] = round(
                (qualified + closed_won) / result["total_deals"] * 100, 1
            )
        
        conn.close()
    except Exception:
        pass
    
    return result


def get_learning_insights() -> dict:
    """Get learned preferences insights."""
    result = {
        "total_outcomes": 0,
        "best_channel": "Unknown",
        "best_channel_rate": 0.0,
        "insights": []
    }
    
    if not LEARNED_PREFS.exists():
        return result
    
    try:
        data = json.loads(LEARNED_PREFS.read_text())
        result["total_outcomes"] = data.get("total_outcomes", 0)
        result["best_channel"] = data.get("best_channel", "Unknown")
        result["best_channel_rate"] = data.get("best_channel_rate", 0.0)
        result["insights"] = data.get("insights", [])[:5]  # Limit to 5
    except Exception:
        pass
    
    return result


def get_goals_progress() -> dict:
    """Get goals and progress information."""
    result = {
        "short_term": "Not set",
        "deadline": None,
        "days_remaining": None,
        "progress": "Unknown"
    }
    
    if not GOALS_FILE.exists():
        return result
    
    try:
        data = json.loads(GOALS_FILE.read_text())
        st = data.get("short_term", {})
        result["short_term"] = st.get("goal", "Not set")
        result["deadline"] = st.get("deadline")
        
        if result["deadline"]:
            deadline_dt = datetime.strptime(result["deadline"], "%Y-%m-%d")
            now = datetime.now()
            result["days_remaining"] = (deadline_dt - now).days
        
        # Calculate progress from pipeline
        if PIPELINE_DB.exists():
            conn = sqlite3.connect(str(PIPELINE_DB))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deals WHERE stage = 'Closed Won'")
            wins = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM deals WHERE stage = 'Qualified'")
            qualified = cursor.fetchone()[0]
            conn.close()
            result["progress"] = f"{wins} wins, {qualified} qualified"
    except Exception:
        pass
    
    return result


def get_system_health() -> dict:
    """Get system health information."""
    result = {
        "pa_service": "unknown",
        "daily_loop": "unknown",
        "cron_jobs": 0
    }
    
    # Check PA service
    try:
        status = subprocess.run(
            ["systemctl", "is-active", "personal-assistant"],
            capture_output=True, text=True, timeout=5
        )
        result["pa_service"] = status.stdout.strip() or "not-found"
    except Exception:
        result["pa_service"] = "check-failed"
    
    # Loop health
    if LOOP_HEALTH.exists():
        try:
            data = json.loads(LOOP_HEALTH.read_text())
            runs = data.get("runs", [])
            if runs:
                last = runs[-1]
                result["daily_loop"] = f"last_run: {last.get('date')} {last.get('time')}, stages: {last.get('stages_passed')}/{last.get('stages_total')}"
        except Exception:
            pass
    
    # Cron jobs count
    try:
        cron = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=5
        )
        lines = [l for l in cron.stdout.split('\n') if l.strip() and not l.startswith('#')]
        result["cron_jobs"] = len(lines)
    except Exception:
        pass
    
    return result


def get_agent_status() -> dict:
    """Get multi-agent status."""
    # These are known agents in the system
    return {
        "claude_code": "active",
        "panacea": "active", 
        "ralph": "dormant",
        "grok": "external"
    }


@state_summary_bp.route('/state/summary', methods=['GET'])
def state_summary():
    """
    GET /state/summary
    
    Returns aggregated system state for external agents (Grok).
    Read-only, no sensitive data.
    
    Note: timestamps include both UTC (for API consumers) and Eastern 
    (for human readability — William is in Naples, FL).
    """
    return jsonify({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_eastern": format_eastern(),
        "timezone_note": "System runs on UTC. William is in Naples, FL (Eastern Time).",
        "pipeline": get_pipeline_stats(),
        "learning": get_learning_insights(),
        "goals": get_goals_progress(),
        "health": get_system_health(),
        "agents": get_agent_status()
    })
