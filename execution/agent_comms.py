#!/usr/bin/env python3.11
"""
Agent Communications Bridge
Connects Claude Code (Mac) ↔ Clawdbot (EC2) ↔ Telegram

Usage from Claude Code (Mac):
    # Send message to Clawdbot/William
    curl -X POST http://EC2_IP:5010/agents/message/send \
        -H "Content-Type: application/json" \
        -d '{"from_agent": "claude-code", "to_agent": "clawdbot", "message": "Your message here"}'
    
    # Check for messages from Clawdbot
    curl -X POST http://EC2_IP:5010/agents/message/receive \
        -H "Content-Type: application/json" \
        -d '{"agent_id": "claude-code"}'
    
    # Update shared state
    curl -X POST http://EC2_IP:5010/agents/state/update \
        -H "Content-Type: application/json" \
        -d '{"agent_id": "claude-code", "state": {"working_on": "description", "status": "active"}}'
    
    # Get shared state
    curl -X POST http://EC2_IP:5010/agents/state/get \
        -H "Content-Type: application/json" \
        -d '{"agent_id": "clawdbot"}'

This module provides helper functions for Clawdbot to:
1. Poll for incoming messages from Claude Code
2. Relay messages to Telegram
3. Send messages back to Claude Code
4. Maintain shared state
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

BRIDGE_URL = "http://localhost:5010"

# ============== Message Functions ==============

def send_to_claude_code(message: str, context: Optional[Dict] = None) -> Dict:
    """Send a message from Clawdbot to Claude Code"""
    payload = {
        "from_agent": "clawdbot",
        "to_agent": "claude-code",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if context:
        payload["context"] = context
    
    try:
        resp = requests.post(f"{BRIDGE_URL}/agents/message/send", json=payload, timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_messages_for_clawdbot() -> List[Dict]:
    """Check for messages sent to Clawdbot from other agents"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/agents/message/receive",
            json={"agent_id": "clawdbot"},
            timeout=5
        )
        data = resp.json()
        return data.get("messages", [])
    except Exception as e:
        return []


def get_claude_code_state() -> Dict:
    """Get Claude Code's current state"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/agents/state/get",
            json={"agent_id": "claude-code"},
            timeout=5
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def update_clawdbot_state(state: Dict) -> Dict:
    """Update Clawdbot's state for other agents to see"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/agents/state/update",
            json={"agent_id": "clawdbot", "state": state},
            timeout=5
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ============== Sync Functions ==============

def trigger_git_sync() -> Dict:
    """Trigger a git pull to sync latest changes from GitHub"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/git/pull",
            json={"path": "/home/clawdbot/dev-sandbox"},
            timeout=30
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_sync_status() -> Dict:
    """Get current git sync status"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/git/status",
            json={"path": "/home/clawdbot/dev-sandbox"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ============== Health Check ==============

def get_bridge_health() -> Dict:
    """Get agent bridge API health status"""
    try:
        resp = requests.get(f"{BRIDGE_URL}/health", timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "unreachable"}


# ============== CLI ==============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Communications")
    parser.add_argument("--health", action="store_true", help="Check bridge health")
    parser.add_argument("--messages", action="store_true", help="Get pending messages")
    parser.add_argument("--send", type=str, help="Send message to Claude Code")
    parser.add_argument("--state", action="store_true", help="Get Claude Code state")
    parser.add_argument("--sync", action="store_true", help="Trigger git sync")
    parser.add_argument("--status", action="store_true", help="Get git status")
    
    args = parser.parse_args()
    
    if args.health:
        print(json.dumps(get_bridge_health(), indent=2))
    elif args.messages:
        msgs = get_messages_for_clawdbot()
        if msgs:
            for m in msgs:
                print(f"[{m.get('from_agent', 'unknown')}] {m.get('message', '')}")
        else:
            print("No pending messages")
    elif args.send:
        result = send_to_claude_code(args.send)
        print(json.dumps(result, indent=2))
    elif args.state:
        print(json.dumps(get_claude_code_state(), indent=2))
    elif args.sync:
        print(json.dumps(trigger_git_sync(), indent=2))
    elif args.status:
        print(json.dumps(get_sync_status(), indent=2))
    else:
        parser.print_help()
