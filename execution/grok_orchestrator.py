#!/usr/bin/env python3
"""
Grok Orchestrator — Translates high-level strategic goals into Claude Code tasks.

Grok (strategic architect) sets direction. This script:
  1. Takes a high-level goal (e.g., "land first client by April 6")
  2. Reads current system state (pipeline, tower status, digest, health)
  3. Identifies the highest-leverage next action
  4. Generates a precise, actionable prompt for Claude Code
  5. Logs the goal → action → result chain for Grok's review

This is NOT autonomous execution — it generates prompts that William or Grok
reviews before giving to Claude Code. It's a thinking tool, not an agent.

Usage:
    python execution/grok_orchestrator.py goal "Land first client by April 6"
    python execution/grok_orchestrator.py status
    python execution/grok_orchestrator.py history
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grok_orchestrator")

GOALS_FILE = REPO_ROOT / "docs" / "grok_goals.json"


def _load_goals() -> List[Dict]:
    if GOALS_FILE.exists():
        with open(GOALS_FILE) as f:
            return json.load(f)
    return []


def _save_goals(goals: List[Dict]):
    GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOALS_FILE, "w") as f:
        json.dump(goals, f, indent=2)


def get_system_state() -> Dict[str, Any]:
    """Read current system state for goal analysis."""
    state = {"timestamp": datetime.now().isoformat()}

    # Pipeline
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()
        stages = conn.execute(
            "SELECT stage, COUNT(*) as cnt FROM deals GROUP BY stage ORDER BY cnt DESC"
        ).fetchall()
        state["pipeline"] = {r["stage"]: r["cnt"] for r in stages}
        state["total_deals"] = sum(r["cnt"] for r in stages)
        hot = conn.execute("SELECT COUNT(*) FROM deals WHERE stage = 'Hot Response'").fetchone()[0]
        state["hot_leads"] = hot
        conn.close()
    except Exception as e:
        state["pipeline_error"] = str(e)

    # Health
    try:
        spec2 = importlib.util.spec_from_file_location(
            "health", REPO_ROOT / "projects" / "personal-assistant" / "src" / "system_health_check.py"
        )
        hc = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(hc)
        state["health"] = hc.run_all_checks()
    except Exception:
        state["health"] = {"healthy": "unknown"}

    # Towers
    state["towers"] = {}
    for tower in ["ai-systems", "amazon-seller", "fitness-influencer",
                   "lead-generation", "mcp-services", "personal-assistant"]:
        ver_path = REPO_ROOT / "projects" / tower / "VERSION"
        state["towers"][tower] = ver_path.read_text().strip() if ver_path.exists() else "missing"

    # Loop health
    health_file = REPO_ROOT / "projects" / "lead-generation" / "logs" / "loop_health.json"
    if health_file.exists():
        with open(health_file) as f:
            lh = json.load(f)
        state["loop_consecutive_failures"] = lh.get("consecutive_failures", 0)
        runs = lh.get("runs", [])
        state["last_loop_run"] = runs[-1] if runs else None

    return state


def analyze_goal(goal: str) -> Dict[str, Any]:
    """Analyze a high-level goal against current system state.

    Returns the highest-leverage next action and a Claude Code prompt.
    """
    state = get_system_state()
    now = datetime.now()
    april_6 = datetime(2026, 4, 6)
    days_left = (april_6 - now).days

    analysis = {
        "goal": goal,
        "analyzed_at": now.isoformat(),
        "days_to_april_6": days_left,
        "system_state_summary": {},
        "blockers": [],
        "next_action": "",
        "claude_prompt": "",
        "priority": "high",
    }

    # Assess pipeline health
    total = state.get("total_deals", 0)
    hot = state.get("hot_leads", 0)
    pipeline = state.get("pipeline", {})
    qualified = pipeline.get("Qualified", 0)

    analysis["system_state_summary"] = {
        "total_deals": total,
        "hot_leads": hot,
        "qualified": qualified,
        "system_healthy": state.get("health", {}).get("healthy", False),
        "loop_failures": state.get("loop_consecutive_failures", 0),
        "days_left": days_left,
    }

    # Identify blockers
    if state.get("loop_consecutive_failures", 0) >= 2:
        analysis["blockers"].append("Daily loop has failed 2+ times — fix before anything else")
    if not state.get("health", {}).get("healthy", True):
        analysis["blockers"].append("System health check failing — diagnose with system_health_check.py")

    # Determine highest-leverage action based on goal
    goal_lower = goal.lower()

    if "client" in goal_lower or "land" in goal_lower or "close" in goal_lower:
        if hot > 0:
            analysis["next_action"] = f"CALL HOT LEADS NOW — {hot} hot lead(s) waiting. This is the closest path to cash."
            analysis["claude_prompt"] = (
                "Show me the HOT leads from pipeline.db with their contact details, "
                "company info, and the message they sent. I need to call them today."
            )
            analysis["priority"] = "critical"
        elif qualified > 0:
            analysis["next_action"] = f"VISIT QUALIFIED LEADS — {qualified} qualified leads. Walk-ins convert 5-10x vs email."
            analysis["claude_prompt"] = (
                "List the top 5 qualified leads from pipeline.db sorted by industry, "
                "with addresses if available. I want to plan walk-in visits today."
            )
            analysis["priority"] = "high"
        elif total > 0:
            analysis["next_action"] = f"RUN LIVE LOOP — {total} deals in pipeline but no hot leads yet. Run --for-real to generate outreach."
            analysis["claude_prompt"] = (
                "Run the daily loop with --for-real to send outreach to the top-scored leads. "
                "Then show me the pipeline status and what was sent."
            )
        else:
            analysis["next_action"] = "BUILD PIPELINE — No deals yet. Need to discover and score leads first."
            analysis["claude_prompt"] = (
                "Run the campaign auto-launcher to discover leads for marceau-solutions. "
                "Score them and prepare the first outreach batch."
            )

    elif "schedule" in goal_lower or "day" in goal_lower or "plan" in goal_lower:
        analysis["next_action"] = "GENERATE TODAY'S PLAN — Run the daily scheduler for ROI-prioritized time blocks."
        analysis["claude_prompt"] = (
            "Run the daily scheduler preview and show me the proposed time blocks. "
            "Then run the morning digest preview so I can see the full day plan."
        )

    elif "personal assistant" in goal_lower or "run my life" in goal_lower or "roi" in goal_lower or "delegation" in goal_lower:
        # Check if the PA system is already complete
        has_scheduler = (REPO_ROOT / "projects" / "personal-assistant" / "src" / "daily_scheduler.py").exists()
        has_digest = (REPO_ROOT / "projects" / "personal-assistant" / "src" / "unified_morning_digest.py").exists()
        has_handlers = (REPO_ROOT / "projects" / "personal-assistant" / "src" / "clawdbot_handlers.py").exists()
        if has_scheduler and has_digest:
            analysis["next_action"] = (
                "SYSTEM ALREADY COMPLETE — PA has: daily_scheduler (ROI blocks + calendar write), "
                "morning digest (health + schedule + pipeline), clawdbot handlers (conversational). "
                "Run it live and iterate based on real outcome data."
            )
            analysis["claude_prompt"] = (
                "The Personal Assistant is already built. Run: "
                "python -m src.daily_scheduler preview && python -m src.unified_morning_digest --preview "
                "to verify, then run the daily loop --for-real to generate leads."
            )
            analysis["priority"] = "low"
        else:
            analysis["next_action"] = "BUILD PA SCHEDULER — daily_scheduler.py and morning digest need creation."
            analysis["claude_prompt"] = "Build the daily_scheduler.py with ROI time blocking for the personal-assistant tower."

    elif "tower" in goal_lower or "architecture" in goal_lower or "compliance" in goal_lower:
        analysis["next_action"] = "CHECK COMPLIANCE — Run the standardization enforcer to verify tower health."
        analysis["claude_prompt"] = (
            "Run the standardization enforcer and show results. "
            "Then check if any towers need structural work."
        )

    elif "deploy" in goal_lower or "ec2" in goal_lower or "ralph" in goal_lower:
        analysis["next_action"] = "HAND OFF TO RALPH — This needs EC2 deployment."
        analysis["claude_prompt"] = (
            "Create a handoff to Ralph via: "
            f"python3 execution/three_agent_orchestrator.py handoff --to ralph --task \"{goal}\""
        )
        analysis["priority"] = "medium"

    elif "content" in goal_lower or "social" in goal_lower or "post" in goal_lower:
        analysis["next_action"] = "ROUTE TO FITNESS-INFLUENCER — Content tasks belong in that tower."
        analysis["claude_prompt"] = (
            "Check fitness-influencer tower status and wire content generation. "
            "Social media automation is in fitness-influencer/social-media/."
        )

    else:
        analysis["next_action"] = "ASSESS — Analyzing system state for best action."
        analysis["claude_prompt"] = (
            f"The goal is: '{goal}'. Show me the current system state: "
            "pipeline status, health check, tower versions, and the morning digest preview. "
            "Then recommend the single highest-leverage action."
        )

    return analysis


def process_goal(goal: str) -> None:
    """Analyze a goal and display the recommended action + Claude prompt."""
    analysis = analyze_goal(goal)

    print(f"\n{'='*60}")
    print(f"GROK ORCHESTRATOR — Goal Analysis")
    print(f"{'='*60}")
    print(f"\nGoal: {goal}")
    print(f"Days to April 6: {analysis['days_to_april_6']}")
    print(f"Priority: {analysis['priority'].upper()}")

    state = analysis["system_state_summary"]
    print(f"\nSystem State:")
    print(f"  Pipeline: {state['total_deals']} deals, {state['hot_leads']} hot, {state['qualified']} qualified")
    print(f"  Health: {'✓' if state['system_healthy'] else '✗'}")
    print(f"  Loop failures: {state['loop_failures']}")

    if analysis["blockers"]:
        print(f"\n⚠️  Blockers:")
        for b in analysis["blockers"]:
            print(f"  • {b}")

    print(f"\n→ NEXT ACTION: {analysis['next_action']}")
    print(f"\n→ CLAUDE PROMPT:")
    print(f"  \"{analysis['claude_prompt']}\"")

    # Save to history
    goals = _load_goals()
    goals.append(analysis)
    _save_goals(goals)
    print(f"\n(Saved to {GOALS_FILE})")


def show_status():
    """Show current system state summary."""
    state = get_system_state()
    print(f"\n{'='*60}")
    print(f"SYSTEM STATE — {state['timestamp'][:16]}")
    print(f"{'='*60}")
    print(f"\nPipeline: {state.get('total_deals', '?')} deals, {state.get('hot_leads', '?')} hot")
    print(f"Health: {state.get('health', {}).get('healthy', '?')}")
    print(f"Loop failures: {state.get('loop_consecutive_failures', '?')}")
    print(f"\nTowers:")
    for tower, ver in state.get("towers", {}).items():
        print(f"  {tower}: v{ver}")


def show_history():
    """Show goal analysis history."""
    goals = _load_goals()
    if not goals:
        print("No goal history yet.")
        return
    print(f"\nGoal History ({len(goals)} entries):")
    for g in goals[-5:]:
        print(f"  [{g['analyzed_at'][:10]}] {g['goal']}")
        print(f"    → {g['next_action'][:80]}")


def main():
    parser = argparse.ArgumentParser(description="Grok Orchestrator")
    sub = parser.add_subparsers(dest="command")

    g = sub.add_parser("goal", help="Analyze a goal and get next action")
    g.add_argument("text", help="The goal (e.g., 'Land first client by April 6')")

    sub.add_parser("status", help="Show current system state")
    sub.add_parser("history", help="Show goal analysis history")

    args = parser.parse_args()

    if args.command == "goal":
        process_goal(args.text)
    elif args.command == "status":
        show_status()
    elif args.command == "history":
        show_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
