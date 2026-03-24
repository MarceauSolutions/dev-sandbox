#!/usr/bin/env python3
"""
Marceau Hub — One URL, all your tools.
Always-running master launcher at http://127.0.0.1:8760
"""

import os
import signal
import socket
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template

APP_DIR = Path(__file__).parent
DEV_SANDBOX = APP_DIR.parents[3]  # /Users/.../dev-sandbox
SCRIPTS_DIR = DEV_SANDBOX / "scripts"

app = Flask(__name__, template_folder=str(APP_DIR / "templates"))

# ---------------------------------------------------------------------------
# App Registry — all web apps with their ports and launch scripts
# ---------------------------------------------------------------------------

APPS = [
    # ── Hub (self) ──────────────────────────────────────────────────────────
    {
        "id": "hub",
        "name": "Marceau Hub",
        "description": "This page — your master launcher",
        "port": 8760,
        "script": None,
        "category": "system",
        "icon": "&#127968;",
    },

    # ── Production (EC2 — always live) ──────────────────────────────────────
    {
        "id": "pipeline-prod",
        "name": "Sales Pipeline",
        "description": "Full CRM — call day, email day, kanban, outreach log, proposals. Your primary sales workspace.",
        "port": None,
        "external_url": "https://pipeline.marceausolutions.com",
        "script": None,
        "category": "production",
        "icon": "&#128200;",
    },
    {
        "id": "calls-prod",
        "name": "Call Scoring & Coach",
        "description": "Log calls, score outcomes, track close rate. Identifies which sales skills to sharpen based on your real call data.",
        "port": None,
        "external_url": "https://calls.marceausolutions.com",
        "script": None,
        "category": "production",
        "icon": "&#127908;",
    },
    {
        "id": "signing-prod",
        "name": "Client Signing",
        "description": "Send contracts, collect e-signatures, onboard new AI clients.",
        "port": None,
        "external_url": "https://sign.marceausolutions.com",
        "script": None,
        "category": "production",
        "icon": "&#9999;",
    },
    {
        "id": "fitai-prod",
        "name": "FitAI Platform",
        "description": "Julia's fitness influencer platform — client dashboard, programs, analytics.",
        "port": None,
        "external_url": "https://fitai.marceausolutions.com",
        "script": None,
        "category": "production",
        "icon": "&#128170;",
    },

    # ── Local Sales Tools ───────────────────────────────────────────────────
    {
        "id": "sales-practice",
        "name": "Sales Practice",
        "description": "AI mock call roleplay — practice your pitch against realistic prospect personas. Identify weak spots before live calls.",
        "port": 8796,
        "script": "sales-coach.sh",
        "category": "business",
        "icon": "&#127919;",
    },
    {
        "id": "outreach-analytics",
        "name": "Outreach Analytics",
        "description": "Email campaign performance — open rates, reply tracking, A/B results.",
        "port": 8794,
        "script": "outreach-analytics.sh",
        "category": "business",
        "icon": "&#128139;",
    },

    # ── Operations ──────────────────────────────────────────────────────────
    {
        "id": "accountability",
        "name": "Accountability Engine",
        "description": "90-day goal tracking, daily check-ins, health-aware coaching.",
        "port": 8780,
        "script": "accountability.sh",
        "category": "productivity",
        "icon": "&#9989;",
    },
    {
        "id": "api-key-manager",
        "name": "KeyVault",
        "description": "API key manager — view, rotate, and sync credentials across all agents.",
        "port": 8793,
        "script": "api-key-manager.sh",
        "category": "system",
        "icon": "&#128273;",
    },
    {
        "id": "email-assistant",
        "name": "Email Assistant",
        "description": "AI-powered Gmail search, smart drafts, and document generation.",
        "port": 8791,
        "script": "email-assistant.sh",
        "category": "productivity",
        "icon": "&#9993;&#65039;",
    },

    # ── Health ──────────────────────────────────────────────────────────────
    {
        "id": "dystonia-digest",
        "name": "Dystonia Digest",
        "description": "Daily health digest — treatment tracking, research summaries, symptom trends.",
        "port": 8792,
        "script": "dystonia-digest.sh",
        "category": "health",
        "icon": "&#128138;",
    },

    # ── Labs / Build ────────────────────────────────────────────────────────
    {
        "id": "mikos-lab",
        "name": "Miko's Lab",
        "description": "AI avatar workshop — projects, methods, prompts, knowledge base.",
        "port": 8766,
        "script": "mikos-lab.sh",
        "category": "build",
        "icon": "&#129302;",
    },
    {
        "id": "claim-back",
        "name": "ClaimBack",
        "description": "AI medical billing dispute platform — dispute letters, appeal tracking.",
        "port": 8790,
        "script": "claim-back.sh",
        "category": "build",
        "icon": "&#9878;&#65039;",
    },
    {
        "id": "launchpad",
        "name": "LaunchPad",
        "description": "Product launch platform — 5-phase market validation pipeline.",
        "port": 8765,
        "script": "launchpad.sh",
        "category": "build",
        "icon": "&#128640;",
    },
    {
        "id": "agent-os",
        "name": "AgentOS",
        "description": "Self-configuring Claude Code operating system — product landing page.",
        "port": 8795,
        "script": "agent-os-landing.sh",
        "category": "build",
        "icon": "&#129504;",
    },
]


def is_port_open(port: int) -> bool:
    """Check if a port is listening (app is running)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/apps")
def api_apps():
    """Return all apps with live status."""
    result = []
    for a in APPS:
        info = dict(a)
        if a.get("external_url"):
            info["running"] = True  # External/production apps are always live
            info["external"] = True
            info["url"] = a["external_url"]
        else:
            info["running"] = is_port_open(a["port"]) if a["port"] else False
            info["external"] = False
            info["url"] = f"http://127.0.0.1:{a['port']}" if a["port"] else None
        result.append(info)
    return jsonify(result)


@app.route("/api/launch/<app_id>", methods=["POST"])
def api_launch(app_id):
    """Launch an app by starting its script in background."""
    target = None
    for a in APPS:
        if a["id"] == app_id:
            target = a
            break

    if not target:
        return jsonify({"error": "Unknown app"}), 404

    if not target.get("script"):
        return jsonify({"error": "No launch script"}), 400

    # Already running?
    if is_port_open(target["port"]):
        return jsonify({"success": True, "already_running": True, "url": f"http://127.0.0.1:{target['port']}"})

    script_path = SCRIPTS_DIR / target["script"]
    if not script_path.exists():
        return jsonify({"error": f"Script not found: {target['script']}"}), 404

    try:
        # Launch in background, detached from this process
        subprocess.Popen(
            ["bash", str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(DEV_SANDBOX),
        )
        return jsonify({"success": True, "url": f"http://127.0.0.1:{target['port']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop/<app_id>", methods=["POST"])
def api_stop(app_id):
    """Stop an app by killing its port."""
    target = None
    for a in APPS:
        if a["id"] == app_id:
            target = a
            break

    if not target or target["id"] == "hub":
        return jsonify({"error": "Cannot stop this app"}), 400

    port = target["port"]
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True,
        )
        pids = result.stdout.strip().split("\n")
        for pid in pids:
            if pid.strip():
                os.kill(int(pid.strip()), signal.SIGTERM)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("HUB_PORT", 8760))
    print(f"\n  Marceau Hub — http://127.0.0.1:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)
