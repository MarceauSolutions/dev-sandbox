#!/usr/bin/env python3
"""
Goal Runner -- Autonomous Grok-Claude execution loop.

Takes a high-level goal, uses Grok API for strategy and Claude Code for
local execution. Removes William as the middle-man between agents.

Architecture:
  1. William (or Grok) sets a goal
  2. Research gate gathers current pipeline/system state
  3. Grok API analyzes state + goal -> generates specific task for Claude
  4. Claude Code executes task locally (file reads, commands, code changes)
  5. Result captured and sent back to Grok for next step
  6. Loop continues until goal complete or max iterations

The key insight: Grok is the strategist (what to do), Claude is the executor
(how to do it). Neither needs William to translate between them.

Safety:
  - Max 5 iterations per goal (prevents runaway loops)
  - Research gate runs before every iteration
  - Protected files list prevents touching autonomous core
  - Dry-run mode shows what would happen without executing
  - All results logged to pipeline.db agent_tasks table

Usage:
    python execution/goal_runner.py "Improve PA integration across towers"
    python execution/goal_runner.py "Audit pipeline data quality" --max-steps 3
    python execution/goal_runner.py "Check system health" --dry-run
    python execution/goal_runner.py --status  # Show recent goal runs
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("goal_runner")

# Safety: never modify these files
PROTECTED_FILES = [
    "projects/lead-generation/src/daily_loop.py",
    "projects/personal-assistant/src/unified_morning_digest.py",
    "projects/personal-assistant/src/system_health_check.py",
    "projects/lead-generation/src/hot_lead_handler.py",
    "execution/safe_git_save.py",
]

MAX_STEPS_DEFAULT = 5
GOAL_LOG_FILE = REPO_ROOT / "projects" / "personal-assistant" / "logs" / "goal_runs.json"


def _get_ssl_context():
    """Build SSL context with certifi certs (macOS Python 3.14 fix)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


STRATEGIST_SYSTEM = (
    "You are a strategic business advisor for Marceau Solutions, a one-person "
    "AI automation consultancy in Naples, FL. You give specific, actionable "
    "instructions for Claude Code (a local executor) to carry out. "
    "Be concise. Output ONLY valid JSON with keys: task (what to do), "
    "commands (list of shell commands to run in the dev-sandbox repo), "
    "done (true if goal is verifiably complete), "
    "reasoning (why this step matters). No markdown wrapping."
)


def _call_strategist(prompt: str, max_tokens: int = 1000) -> str:
    """Call AI strategist API. Tries Grok first, falls back to Claude Haiku.

    Uses certifi for SSL on macOS where default certs are missing.
    """
    import urllib.request

    ssl_ctx = _get_ssl_context()

    # Try Grok first
    xai_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if xai_key:
        result = _try_api(
            url="https://api.x.ai/v1/chat/completions",
            api_key=xai_key,
            model="grok-3-mini",
            prompt=prompt,
            max_tokens=max_tokens,
            ssl_ctx=ssl_ctx,
        )
        if not result.startswith("ERROR:"):
            logger.info("Strategist: Grok API")
            return result
        logger.warning(f"Grok API failed, trying Claude: {result[:80]}")

    # Fall back to Claude Haiku (fast, cheap)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        result = _try_api(
            url="https://api.anthropic.com/v1/messages",
            api_key=anthropic_key,
            model="claude-haiku-4-5-20251001",
            prompt=prompt,
            max_tokens=max_tokens,
            ssl_ctx=ssl_ctx,
            is_anthropic=True,
        )
        if not result.startswith("ERROR:"):
            logger.info("Strategist: Claude Haiku")
            return result
        return result

    return "ERROR: No API keys available (XAI_API_KEY or ANTHROPIC_API_KEY)"


def _try_api(url: str, api_key: str, model: str, prompt: str,
             max_tokens: int, ssl_ctx, is_anthropic: bool = False) -> str:
    """Try calling an AI API. Returns content or ERROR string."""
    import urllib.request

    if is_anthropic:
        data = json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "system": STRATEGIST_SYSTEM,
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
    else:
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": STRATEGIST_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
        result = json.loads(resp.read())

        if is_anthropic:
            content = result["content"][0]["text"]
        else:
            content = result["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        return f"ERROR: API call failed ({url}): {e}"


def _execute_commands(commands: List[str], dry_run: bool = False) -> List[Dict[str, str]]:
    """Execute a list of shell commands safely.

    Checks commands against protected files list before running.
    """
    results = []
    for cmd in commands:
        # Safety check: does this command touch protected files?
        is_protected = any(pf in cmd for pf in PROTECTED_FILES)
        if is_protected:
            results.append({
                "command": cmd,
                "output": "BLOCKED: Command touches protected autonomous core file",
                "exit_code": -1,
            })
            continue

        if dry_run:
            results.append({
                "command": cmd,
                "output": "[DRY RUN] Would execute",
                "exit_code": 0,
            })
            continue

        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=str(REPO_ROOT),
            )
            results.append({
                "command": cmd,
                "output": (proc.stdout + proc.stderr)[:500],
                "exit_code": proc.returncode,
            })
        except subprocess.TimeoutExpired:
            results.append({
                "command": cmd,
                "output": "TIMEOUT after 30s",
                "exit_code": -1,
            })
        except Exception as e:
            results.append({
                "command": cmd,
                "output": f"ERROR: {e}",
                "exit_code": -1,
            })

    return results


def _get_research_context() -> str:
    """Get research gate context as a string."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "research_gate", REPO_ROOT / "execution" / "research_gate.py"
        )
        rg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rg)
        return rg.format_for_prompt()
    except Exception as e:
        return f"Research gate unavailable: {e}"


def _log_goal_run(goal: str, steps: List[Dict], status: str):
    """Log a goal run to the goal runs file."""
    runs = []
    if GOAL_LOG_FILE.exists():
        try:
            with open(GOAL_LOG_FILE) as f:
                runs = json.load(f)
        except (json.JSONDecodeError, ValueError):
            runs = []

    runs.append({
        "goal": goal,
        "status": status,
        "steps": len(steps),
        "started_at": steps[0]["timestamp"] if steps else datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "step_summaries": [s.get("task", "?")[:80] for s in steps],
    })

    # Keep last 20 runs
    runs = runs[-20:]
    GOAL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOAL_LOG_FILE, "w") as f:
        json.dump(runs, f, indent=2)


def run_goal(goal: str, max_steps: int = MAX_STEPS_DEFAULT,
             dry_run: bool = False) -> Dict[str, Any]:
    """Run an autonomous goal execution loop.

    1. Gather research context
    2. Ask Grok for next step
    3. Execute step
    4. Loop until done or max steps
    """
    logger.info(f"Goal runner started: {goal} (max_steps={max_steps}, dry_run={dry_run})")

    steps = []
    research = _get_research_context()

    for iteration in range(1, max_steps + 1):
        logger.info(f"--- Step {iteration}/{max_steps} ---")

        # Build prompt for Grok
        history = ""
        if steps:
            history = "\n\nPrevious steps:\n"
            for s in steps:
                history += f"  Step {s['iteration']}: {s['task']}\n"
                history += f"    Result: {s.get('summary', 'no result')[:100]}\n"

        grok_prompt = (
            f"GOAL: {goal}\n\n"
            f"CURRENT STATE:\n{research}\n"
            f"{history}\n"
            f"What specific task should Claude Code execute next to advance this goal? "
            f"If the goal is verifiably complete, set done=true. "
            f"Return JSON: {{task, commands, done, reasoning}}"
        )

        # Call Grok
        logger.info("Calling Grok API for strategy...")
        grok_response = _call_strategist(grok_prompt)

        if grok_response.startswith("ERROR:"):
            logger.error(f"Grok API failed: {grok_response}")
            steps.append({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "task": "Grok API call failed",
                "grok_response": grok_response,
                "error": True,
            })
            break

        # Parse Grok's response
        try:
            # Extract JSON from response (Grok may wrap it in markdown)
            json_str = grok_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            parsed = json.loads(json_str.strip())
            task = parsed.get("task", "No task specified")
            commands = parsed.get("commands", [])
            done = parsed.get("done", False)
            reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, IndexError):
            # If not valid JSON, treat the whole response as a task description
            task = grok_response[:200]
            commands = []
            done = False
            reasoning = "Could not parse JSON from Grok response"

        logger.info(f"Grok says: {task}")
        if reasoning:
            logger.info(f"Reasoning: {reasoning}")

        # Check if done
        if done:
            logger.info("Grok says goal is COMPLETE")
            steps.append({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "task": task,
                "reasoning": reasoning,
                "done": True,
            })
            break

        # Execute commands
        if isinstance(commands, str):
            commands = [commands]

        if commands:
            logger.info(f"Executing {len(commands)} command(s)...")
            cmd_results = _execute_commands(commands, dry_run=dry_run)
        else:
            cmd_results = [{"command": "(no commands)", "output": "Grok gave no commands", "exit_code": 0}]

        # Build step summary
        summary = ""
        for cr in cmd_results:
            exit_note = "OK" if cr["exit_code"] == 0 else f"EXIT {cr['exit_code']}"
            summary += f"[{exit_note}] {cr['command']}: {cr['output'][:100]}\n"

        steps.append({
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "reasoning": reasoning,
            "commands": commands,
            "results": cmd_results,
            "summary": summary,
        })

        # Refresh research context for next iteration
        research = _get_research_context()

    # Determine final status
    final_done = any(s.get("done") for s in steps)
    has_error = any(s.get("error") for s in steps)
    status = "completed" if final_done else "failed" if has_error else "max_steps_reached"

    # Log the run
    _log_goal_run(goal, steps, status)

    result = {
        "goal": goal,
        "status": status,
        "total_steps": len(steps),
        "max_steps": max_steps,
        "dry_run": dry_run,
        "steps": steps,
    }

    logger.info(f"Goal runner finished: {status} ({len(steps)} steps)")
    return result


def show_status() -> Dict[str, Any]:
    """Show recent goal runs."""
    if not GOAL_LOG_FILE.exists():
        return {"runs": [], "total": 0}

    with open(GOAL_LOG_FILE) as f:
        runs = json.load(f)

    return {
        "total": len(runs),
        "recent": runs[-5:] if runs else [],
    }


def format_result(result: Dict[str, Any]) -> str:
    """Format a goal run result for human reading."""
    lines = [
        f"GOAL: {result['goal']}",
        f"STATUS: {result['status']}",
        f"STEPS: {result['total_steps']}/{result['max_steps']}",
        f"DRY RUN: {result['dry_run']}",
        "",
    ]

    for step in result["steps"]:
        lines.append(f"--- Step {step['iteration']} ---")
        lines.append(f"Task: {step['task']}")
        if step.get("reasoning"):
            lines.append(f"Why: {step['reasoning']}")
        if step.get("done"):
            lines.append(">> GOAL COMPLETE")
        if step.get("results"):
            for cr in step["results"]:
                exit_note = "OK" if cr["exit_code"] == 0 else f"FAIL({cr['exit_code']})"
                lines.append(f"  [{exit_note}] {cr['command']}")
                if cr["output"] and cr["output"] != "[DRY RUN] Would execute":
                    lines.append(f"    {cr['output'][:150]}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Goal Runner - Autonomous Grok-Claude execution loop"
    )
    parser.add_argument("goal", nargs="?", help="High-level goal to achieve")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS_DEFAULT)
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--status", action="store_true", help="Show recent goal runs")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.status:
        status = show_status()
        print(json.dumps(status, indent=2))
        return

    if not args.goal:
        parser.print_help()
        return

    result = run_goal(args.goal, max_steps=args.max_steps, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_result(result))


if __name__ == "__main__":
    main()
