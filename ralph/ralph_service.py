#!/usr/bin/env python3.11
"""
Ralph Service - Autonomous PRD-driven execution agent

Runs as a daemon, checks for pending PRDs/handoffs, executes them autonomously.
Communicates with Clawdbot via agent_bridge_api.

To run: python3.11 ralph_service.py
As service: systemctl start ralph
"""

import json
import os
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration
RALPH_DIR = Path("/home/clawdbot/dev-sandbox/ralph")
HANDOFFS_FILE = RALPH_DIR / "handoffs.json"
PRD_FILE = RALPH_DIR / "prd.json"
AGENT_BRIDGE_URL = "http://localhost:5010"
CHECK_INTERVAL = 60  # seconds between checks

def log(msg: str):
    """Log with timestamp."""
    print(f"[{datetime.now().isoformat()}] {msg}")

def send_message(to_agent: str, message: str) -> bool:
    """Send message via agent bridge."""
    try:
        resp = requests.post(
            f"{AGENT_BRIDGE_URL}/agents/message/send",
            json={
                "from_agent": "ralph",
                "to_agent": to_agent,
                "message": message
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        log(f"Error sending message: {e}")
        return False

def receive_messages() -> list:
    """Check for messages to Ralph."""
    try:
        resp = requests.post(
            f"{AGENT_BRIDGE_URL}/agents/message/receive",
            json={"agent_id": "ralph"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("messages", [])
    except Exception as e:
        log(f"Error receiving messages: {e}")
    return []

def load_handoffs() -> Dict[str, Any]:
    """Load handoffs.json."""
    if not HANDOFFS_FILE.exists():
        return {"pending_for_ralph": [], "pending_for_mac": [], "completed": []}
    with open(HANDOFFS_FILE, 'r') as f:
        return json.load(f)

def save_handoffs(data: Dict[str, Any]):
    """Save handoffs.json."""
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(HANDOFFS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_prd() -> Optional[Dict[str, Any]]:
    """Load current PRD if exists."""
    if not PRD_FILE.exists():
        return None
    with open(PRD_FILE, 'r') as f:
        return json.load(f)

def update_agent_status(status: str):
    """Update Ralph's status in handoffs."""
    handoffs = load_handoffs()
    if "agents" not in handoffs:
        handoffs["agents"] = {}
    handoffs["agents"]["ralph"] = {
        "status": status,
        "last_seen": datetime.utcnow().isoformat()
    }
    save_handoffs(handoffs)

def process_prd(prd: Dict[str, Any]) -> bool:
    """Process a PRD - this would invoke Claude for actual execution."""
    log(f"Processing PRD: {prd.get('name', 'unnamed')}")
    
    # For now, just mark as processed
    # Full implementation would use Claude API or subprocess
    
    send_message("clawdbot", f"Ralph starting PRD: {prd.get('name', 'unnamed')}")
    
    # Placeholder for actual PRD execution
    # This would typically invoke Claude Code or similar
    
    return True

def process_handoff(task: Dict[str, Any]) -> bool:
    """Process a handoff task."""
    task_desc = task.get("task", task.get("description", "Unknown task"))
    log(f"Processing handoff: {task_desc}")
    
    send_message("clawdbot", f"Ralph working on: {task_desc}")
    
    # Placeholder for actual task execution
    
    return True

def main_loop():
    """Main service loop."""
    log("Ralph service starting...")
    update_agent_status("online")
    send_message("clawdbot", "Ralph service started and monitoring for tasks")
    
    while True:
        try:
            # Check for messages
            messages = receive_messages()
            for msg in messages:
                log(f"Received message from {msg.get('from_agent')}: {msg.get('message')}")
            
            # Check for pending handoffs
            handoffs = load_handoffs()
            pending = handoffs.get("pending_for_ec2", []) + handoffs.get("pending_for_ralph", [])
            
            if pending:
                task = pending[0]
                log(f"Found pending task: {task}")
                
                if process_handoff(task):
                    # Move to completed
                    if task in handoffs.get("pending_for_ec2", []):
                        handoffs["pending_for_ec2"].remove(task)
                    if task in handoffs.get("pending_for_ralph", []):
                        handoffs["pending_for_ralph"].remove(task)
                    
                    if "completed" not in handoffs:
                        handoffs["completed"] = []
                    task["completed_at"] = datetime.utcnow().isoformat()
                    handoffs["completed"].append(task)
                    save_handoffs(handoffs)
                    
                    send_message("clawdbot", f"Ralph completed: {task.get('task', 'task')}")
            
            # Check for active PRD
            prd = load_prd()
            if prd and prd.get("status") == "pending":
                process_prd(prd)
            
            # Update status
            update_agent_status("idle")
            
        except Exception as e:
            log(f"Error in main loop: {e}")
            update_agent_status("error")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
