#!/usr/bin/env python3
"""
Grok Strategic Layer — Consults Grok (xAI) for strategic direction before Claude executes.

Shared between Panacea (EC2) and Claude Code (Mac).
Every AI request passes through Grok first. No exceptions. No smart routing.

Usage:
    from grok_strategic_layer import consult_grok

    direction = consult_grok("I need to land a client this week")
    # Returns: "Focus on follow-up calls to warm leads..."
"""

import json
import logging
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("grok_strategic_layer")

REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parent.parent.parent.parent))

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-3-latest"
GROK_TIMEOUT = 10


def _get_system_state_summary() -> str:
    """Build a concise system state summary for Grok's context."""
    parts = [f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    goals_file = REPO_ROOT / "projects" / "personal-assistant" / "data" / "goals.json"
    if goals_file.exists():
        try:
            with open(goals_file) as f:
                goals = json.load(f)
            active = [g for g in goals if g.get("status") == "active"]
            for g in active[:3]:
                parts.append(f"Goal: {g.get('description', 'unknown')}")
        except Exception:
            pass

    try:
        import sqlite3
        for db_path in [REPO_ROOT / "data" / "pipeline.db", REPO_ROOT / "execution" / "pipeline.db"]:
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                total = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
                hot = conn.execute("SELECT COUNT(*) FROM deals WHERE stage = 'Hot Response'").fetchone()[0]
                conn.close()
                parts.append(f"Pipeline: {total} deals, {hot} hot leads")
                break
    except Exception:
        pass

    return "\n".join(parts)


def consult_grok(user_message: str, additional_context: str = "") -> Optional[str]:
    """Consult Grok for strategic direction on a user request.

    Returns Grok's direction as a string, or None if unreachable.
    Failure is always logged — never silent.
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        logger.error("XAI_API_KEY not set — Grok consultation FAILED (logged, not silent)")
        return None

    state_summary = _get_system_state_summary()

    system_prompt = (
        "You are Grok, the strategic advisor for Marceau Solutions. "
        "William is a solo entrepreneur building an AI services company in Naples, FL. "
        "He works full-time as an electrical technician at Collier County (7am-3pm weekdays). "
        "Side hustle work happens evenings and weekends. "
        "Your role: provide concise strategic direction for the AI executor (Claude Code). "
        "Focus on what to prioritize, pitfalls to avoid, and how this connects to the bigger picture. "
        "Be direct — 2-3 sentences max."
    )

    context_block = f"System state:\n{state_summary}"
    if additional_context:
        context_block += f"\n\nAdditional context:\n{additional_context}"

    payload = {
        "model": XAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context_block}\n\nWilliam says: {user_message}"},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    try:
        req = urllib.request.Request(
            XAI_API_URL,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=GROK_TIMEOUT)
        result = json.loads(resp.read())
        direction = result["choices"][0]["message"]["content"].strip()
        logger.info(f"Grok consulted — direction: {direction[:100]}...")
        return direction
    except Exception as e:
        logger.error(f"Grok consultation FAILED (logged, not silent): {e}")
        return None


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    try:
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        pass

    if len(sys.argv) < 2:
        print("Usage: python grok_strategic_layer.py 'your message here'")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    result = consult_grok(message)
    if result:
        print(f"\nGrok says:\n{result}")
    else:
        print("\nGrok unreachable — would proceed with Claude Code alone (logged)")
