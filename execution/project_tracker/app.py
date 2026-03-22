#!/usr/bin/env python3.11
"""
Project Tracker - Web Dashboard
Production deployment at tracker.marceausolutions.com
"""

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv('/home/clawdbot/dev-sandbox/.env')

app = Flask(__name__)
CORS(app)

CONFIG_PATH = Path(__file__).parent / "config.json"
USAGE_LOG_PATH = Path(__file__).parent / "usage_log.json"

# ============== Data Functions ==============

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

# ============== API Fetchers ==============

def get_twilio_usage():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        return {"error": "missing_credentials"}
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Usage/Records/ThisMonth.json"
        response = requests.get(url, auth=(account_sid, auth_token), timeout=10)
        if response.status_code == 200:
            data = response.json()
            sms = next((r for r in data.get("usage_records", []) if r["category"] == "sms"), None)
            return {
                "sms_count": int(sms["count"]) if sms else 0,
                "cost_usd": float(sms["price"]) if sms else 0
            }
    except Exception as e:
        return {"error": str(e)}

def get_elevenlabs_usage():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"error": "missing_credentials"}
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": api_key}, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "characters_used": data.get("character_count", 0),
                "characters_limit": data.get("character_limit", 0),
                "tier": data.get("tier", "unknown")
            }
    except Exception as e:
        return {"error": str(e)}

# ============== Routes ==============

@app.route("/")
def dashboard():
    config = load_config()
    log = load_usage_log()
    
    # Calculate project stats
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    project_stats = {}
    for date_str, projects in log.get("daily_totals", {}).items():
        if date_str >= week_ago:
            for project_id, data in projects.items():
                if project_id not in project_stats:
                    project_stats[project_id] = {"calls": 0, "cost": 0}
                project_stats[project_id]["calls"] += data["calls"]
                project_stats[project_id]["cost"] += data["cost"]
    
    return render_template_string(DASHBOARD_HTML, 
        config=config, 
        project_stats=project_stats,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

@app.route("/api/projects")
def api_projects():
    config = load_config()
    return jsonify(config["projects"])

@app.route("/api/usage")
def api_usage():
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "twilio": get_twilio_usage(),
        "elevenlabs": get_elevenlabs_usage()
    })

@app.route("/api/log", methods=["POST"])
def api_log_call():
    """Log an API call from any project"""
    data = request.json
    project = data.get("project")
    api = data.get("api")
    endpoint = data.get("endpoint", "unknown")
    cost = float(data.get("cost", 0))
    
    if not project or not api:
        return jsonify({"error": "project and api required"}), 400
    
    log = load_usage_log()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "project": project,
        "api": api,
        "endpoint": endpoint,
        "cost": cost
    }
    log["entries"].append(entry)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in log["daily_totals"]:
        log["daily_totals"][today] = {}
    if project not in log["daily_totals"][today]:
        log["daily_totals"][today][project] = {"calls": 0, "cost": 0}
    
    log["daily_totals"][today][project]["calls"] += 1
    log["daily_totals"][today][project]["cost"] += cost
    
    # Keep only last 30 days
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    log["entries"] = [e for e in log["entries"] if e["timestamp"] > cutoff]
    
    save_usage_log(log)
    return jsonify({"status": "logged", "entry": entry})

@app.route("/api/report")
def api_report():
    """Generate JSON report"""
    days = int(request.args.get("days", 7))
    log = load_usage_log()
    config = load_config()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    project_totals = {}
    for date_str, projects in log.get("daily_totals", {}).items():
        if date_str >= start_date:
            for project_id, data in projects.items():
                if project_id not in project_totals:
                    project_totals[project_id] = {
                        "name": config["projects"].get(project_id, {}).get("name", project_id),
                        "calls": 0,
                        "cost": 0
                    }
                project_totals[project_id]["calls"] += data["calls"]
                project_totals[project_id]["cost"] += data["cost"]
    
    return jsonify({
        "period_days": days,
        "start_date": start_date,
        "end_date": datetime.now().strftime("%Y-%m-%d"),
        "projects": project_totals,
        "api_usage": {
            "twilio": get_twilio_usage(),
            "elevenlabs": get_elevenlabs_usage()
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ============== Dashboard HTML ==============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Project Tracker | Marceau Solutions</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a; color: #fff;
            padding: 20px; min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-size: 1.8rem; margin-bottom: 10px; }
        .subtitle { color: #888; margin-bottom: 30px; font-size: 0.9rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: #1a1a1a; border-radius: 12px; padding: 20px;
            border: 1px solid #333;
        }
        .card h2 { font-size: 1rem; color: #888; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }
        .stat { font-size: 2rem; font-weight: bold; margin-bottom: 5px; }
        .stat-label { color: #666; font-size: 0.85rem; }
        .project-list { list-style: none; }
        .project-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px 0; border-bottom: 1px solid #222;
        }
        .project-item:last-child { border-bottom: none; }
        .project-name { font-weight: 500; }
        .project-type { color: #666; font-size: 0.8rem; }
        .project-stats { text-align: right; }
        .status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
        .status-live, .status-active { background: #22c55e; }
        .status-demo { background: #eab308; }
        .api-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #222; }
        .api-row:last-child { border-bottom: none; }
        .refresh-btn {
            background: #333; border: none; color: #fff; padding: 10px 20px;
            border-radius: 8px; cursor: pointer; font-size: 0.9rem;
        }
        .refresh-btn:hover { background: #444; }
        .loading { opacity: 0.5; }
        @media (max-width: 600px) {
            .stat { font-size: 1.5rem; }
            h1 { font-size: 1.4rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Project Tracker</h1>
        <p class="subtitle">API usage & metrics per project | Last updated: {{ last_updated }}</p>
        
        <div class="grid">
            <!-- API Usage Card -->
            <div class="card" id="api-usage">
                <h2>API Usage (This Month)</h2>
                <div id="api-stats">
                    <div class="api-row">
                        <span>Twilio SMS</span>
                        <span id="twilio-stat">Loading...</span>
                    </div>
                    <div class="api-row">
                        <span>ElevenLabs</span>
                        <span id="elevenlabs-stat">Loading...</span>
                    </div>
                </div>
                <br>
                <button class="refresh-btn" onclick="refreshUsage()">Refresh</button>
            </div>
            
            <!-- Projects Card -->
            <div class="card">
                <h2>Registered Projects</h2>
                <ul class="project-list">
                    {% for id, project in config.projects.items() %}
                    <li class="project-item">
                        <div>
                            <span class="status status-{{ project.status }}"></span>
                            <span class="project-name">{{ project.name }}</span>
                            <div class="project-type">{{ project.type }} | {{ project.apis | join(', ') or 'no APIs' }}</div>
                        </div>
                        <div class="project-stats">
                            {% if id in project_stats %}
                            <div>{{ project_stats[id].calls }} calls</div>
                            <div style="color: #666;">${{ "%.2f"|format(project_stats[id].cost) }}</div>
                            {% else %}
                            <div style="color: #444;">No activity</div>
                            {% endif %}
                        </div>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #111; border-radius: 12px;">
            <h2 style="font-size: 1rem; color: #888; margin-bottom: 15px;">LOG API CALL</h2>
            <code style="color: #22c55e;">
POST /api/log<br>
{"project": "fitai-demo", "api": "anthropic", "endpoint": "/messages", "cost": 0.05}
            </code>
        </div>
    </div>
    
    <script>
        async function refreshUsage() {
            document.getElementById('api-usage').classList.add('loading');
            try {
                const res = await fetch('/api/usage');
                const data = await res.json();
                
                if (data.twilio && !data.twilio.error) {
                    document.getElementById('twilio-stat').textContent = 
                        `${data.twilio.sms_count} SMS ($${data.twilio.cost_usd.toFixed(2)})`;
                }
                if (data.elevenlabs && !data.elevenlabs.error) {
                    const pct = ((data.elevenlabs.characters_used / data.elevenlabs.characters_limit) * 100).toFixed(1);
                    document.getElementById('elevenlabs-stat').textContent = 
                        `${data.elevenlabs.characters_used.toLocaleString()} / ${data.elevenlabs.characters_limit.toLocaleString()} (${pct}%)`;
                }
            } catch (e) {
                console.error(e);
            }
            document.getElementById('api-usage').classList.remove('loading');
        }
        refreshUsage();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5030, debug=False)
