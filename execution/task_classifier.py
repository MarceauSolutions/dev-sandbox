"""
Haiku Task Classifier — Auto-route tasks to the right agent.

Replaces manual complexity scoring with an LLM-based classifier using
Claude Haiku (fast, cheap ~$0.001/classification).

Usage:
  from execution.task_classifier import classify_task

  result = classify_task("Build a full CRUD API with auth and tests")
  # Returns: {"agent": "ralph", "complexity": 8, "reason": "Multi-file..."}

  result = classify_task("What's the status of the lead scraper?")
  # Returns: {"agent": "clawdbot", "complexity": 2, "reason": "Quick query..."}
"""

import os
import json
from pathlib import Path
from typing import Optional

# Auto-load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


CLASSIFIER_PROMPT = """You are a task routing classifier for a three-agent development system.

Given a task description, classify it and return JSON with:
- agent: "claude_code" | "clawdbot" | "ralph" | "agent_team"
- complexity: 1-10
- reason: One sentence explaining the routing decision
- estimated_files: Number of files likely touched
- requires_mac: true if needs Mac-specific tools (PyPI, MCP Registry, OAuth, interactive debugging)

Agent capabilities:
- claude_code (Mac, interactive): Best for debugging, deployment, MCP publishing, OAuth, interactive work, medium complexity. Has Mac-only tools.
- clawdbot (EC2, Telegram, 24/7): Best for quick research, simple file edits, status checks, content generation. Complexity 0-4.
- ralph (EC2, autonomous): Best for complex multi-file builds, refactoring, migrations. Complexity 8-10. Takes longer to set up (needs PRD).
- agent_team (Claude Code parallel): Best for medium-complex tasks (5-7) that benefit from parallel sub-agents (e.g., frontend + backend + tests simultaneously).

Routing rules:
- Complexity 0-4 AND no Mac tools needed -> clawdbot
- Complexity 5-7 AND parallelizable sub-tasks -> agent_team
- Complexity 5-7 AND sequential work -> claude_code
- Complexity 8-10 -> ralph
- Requires Mac-specific tools (any complexity) -> claude_code
- Research/questions only -> clawdbot

Return ONLY valid JSON, no markdown."""


def classify_task(
    task: str,
    context: Optional[str] = None,
    model: str = "claude-haiku-4-5-20251001",
) -> dict:
    """
    Classify a task and recommend which agent should handle it.

    Args:
        task: Natural language task description
        context: Optional additional context (current project, recent work)
        model: Model to use (Haiku for speed/cost)

    Returns:
        dict with agent, complexity, reason, estimated_files, requires_mac
    """
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    user_msg = f"Task: {task}"
    if context:
        user_msg += f"\n\nContext: {context}"

    response = client.messages.create(
        model=model,
        max_tokens=200,
        system=CLASSIFIER_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()

    try:
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "agent": "claude_code",
            "complexity": 5,
            "reason": "Classification failed, defaulting to Claude Code",
            "estimated_files": 1,
            "requires_mac": False,
        }

    valid_agents = {"claude_code", "clawdbot", "ralph", "agent_team"}
    if result.get("agent") not in valid_agents:
        result["agent"] = "claude_code"

    return result


def route_task(task: str, context: Optional[str] = None) -> str:
    """Convenience function that returns just the agent name."""
    return classify_task(task, context)["agent"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m execution.task_classifier 'your task description'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    result = classify_task(task)
    print(json.dumps(result, indent=2))
