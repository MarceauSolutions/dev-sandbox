#!/usr/bin/env python3
"""
auto_iterator_webhook.py — HTTP Webhook for AutoIterator Commands

WHAT: FastAPI micro-server that receives commands from n8n/Clawdbot webhooks.
WHY:  Enables Telegram → n8n → AutoIterator flow for approvals and commands.
INPUT: POST /webhook/auto-iterator with {"command": "approve abc123"}
OUTPUT: JSON response + Telegram reply
COST: FREE (runs on EC2 alongside agent_bridge_api.py)

ENDPOINTS:
  POST /webhook/auto-iterator  — Execute a command
  GET  /webhook/auto-iterator/status — Health check + quick status
  POST /webhook/auto-iterator/cycle  — Run full cycle for a domain

DEPLOYMENT:
  Runs on EC2 port 5030. Add to n8n as HTTP Request node.
  Or integrate into existing agent_bridge_api.py as a new route group.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

from execution.auto_iterator_telegram import handle_command, send_reply
from execution.auto_iterator import ExperimentStore
from execution.auto_iterator_evaluators import EVALUATORS

app = FastAPI(title="AutoIterator Webhook", version="1.0")


@app.post("/webhook/auto-iterator")
async def execute_command(request: Request):
    """Execute an AutoIterator command from n8n or Clawdbot."""
    body = await request.json()
    command = body.get("command", "")

    if not command:
        return JSONResponse({"error": "Missing 'command' field"}, status_code=400)

    response_text = handle_command(command)

    # Send to Telegram if requested
    if body.get("notify", True):
        send_reply(response_text)

    return {"status": "ok", "response": response_text}


@app.get("/webhook/auto-iterator/status")
async def quick_status():
    """Quick health check and domain status."""
    store = ExperimentStore()
    domains = {}
    for domain in EVALUATORS:
        stats = store.get_stats(domain)
        domains[domain] = stats

    return {
        "status": "healthy",
        "domains": domains,
        "available_commands": ["approve", "reject", "status", "report", "propose", "cycle"],
    }


@app.post("/webhook/auto-iterator/cycle")
async def run_domain_cycle(request: Request):
    """Run a full optimization cycle for a domain."""
    body = await request.json()
    domain = body.get("domain", "sms_outreach")

    response_text = handle_command(f"cycle {domain}")

    if body.get("notify", True):
        send_reply(response_text)

    return {"status": "ok", "domain": domain, "response": response_text}


def main():
    port = int(os.getenv("AUTO_ITERATOR_PORT", "5030"))
    print(f"AutoIterator webhook starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
