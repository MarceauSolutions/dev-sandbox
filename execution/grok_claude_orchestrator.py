#!/usr/bin/env python3
"""
Grok-Claude Orchestrator -- Lightweight 3-agent coordination layer.

Reduces manual copy-paste between agents by providing:
  1. A task queue where Grok (strategist) deposits tasks
  2. Claude Code (executor) picks up tasks and runs them locally
  3. Clawdbot/Ralph (EC2) handles tasks tagged for remote execution
  4. Research gate automatically called before any task execution

Architecture:
  GROK (strategist) -> deposits high-level tasks
  CLAUDE CODE (executor) -> picks up local tasks, runs research gate first
  CLAWDBOT/RALPH (EC2) -> picks up remote tasks via SSH

Task flow:
  1. Grok analyzes situation, creates prioritized task
  2. Task is written to pipeline.db (agent_tasks table)
  3. Claude Code or Clawdbot polls for pending tasks
  4. Research gate runs automatically before execution
  5. Result is logged back to the task

This replaces William manually copy-pasting between Grok chats and Claude Code.

Usage:
    python execution/grok_claude_orchestrator.py add --task "Research HVAC market size" --agent claude
    python execution/grok_claude_orchestrator.py add --task "Deploy daily_loop fix" --agent ralph
    python execution/grok_claude_orchestrator.py pending                    # Show pending tasks
    python execution/grok_claude_orchestrator.py pending --agent claude     # Claude's queue
    python execution/grok_claude_orchestrator.py complete --id 1 --result "Done: 50 HVAC companies in Naples"
    python execution/grok_claude_orchestrator.py status                    # Agent workload summary
"""

import argparse
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")


def _get_db() -> sqlite3.Connection:
    """Get pipeline.db connection and ensure agent_tasks table exists."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pipeline_db", REPO_ROOT / "execution" / "pipeline_db.py"
    )
    pdb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdb)
    conn = pdb.get_db()
    _ensure_table(conn)
    return conn


def _ensure_table(conn: sqlite3.Connection):
    """Create the agent_tasks table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task            TEXT NOT NULL,
            agent           TEXT NOT NULL DEFAULT 'claude'
                            CHECK(agent IN ('claude', 'ralph', 'grok', 'any')),
            priority        TEXT NOT NULL DEFAULT 'medium'
                            CHECK(priority IN ('critical', 'high', 'medium', 'low')),
            category        TEXT DEFAULT 'general',
            context         TEXT DEFAULT '{}',
            status          TEXT DEFAULT 'pending'
                            CHECK(status IN ('pending', 'in_progress', 'completed', 'failed', 'blocked')),
            result          TEXT DEFAULT NULL,
            source          TEXT DEFAULT 'manual',
            research_done   INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            completed_at    TEXT DEFAULT NULL
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

def add_task(task: str, agent: str = "claude", priority: str = "medium",
             category: str = "general", context: Dict = None,
             source: str = "manual") -> int:
    """Add a task to the queue.

    Args:
        task: Human-readable task description
        agent: Who should execute (claude, ralph, grok, any)
        priority: critical > high > medium > low
        category: Task category (outreach, engineering, research, admin, deployment)
        context: Additional context dict
        source: Who created (manual, grok, daily_loop, research_gate)

    Returns: task ID
    """
    conn = _get_db()
    cursor = conn.execute(
        "INSERT INTO agent_tasks (task, agent, priority, category, context, source) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (task, agent, priority, category, json.dumps(context or {}), source)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"Task #{task_id} added: [{agent}/{priority}] {task}")
    return task_id


def get_pending(agent: str = None) -> List[Dict[str, Any]]:
    """Get pending tasks, optionally filtered by agent.

    Returns tasks ordered by priority (critical first) then creation time.
    """
    conn = _get_db()
    if agent:
        rows = conn.execute(
            "SELECT * FROM agent_tasks WHERE status = 'pending' "
            "AND (agent = ? OR agent = 'any') "
            "ORDER BY CASE priority "
            "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
            "  WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, "
            "created_at ASC",
            (agent,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM agent_tasks WHERE status = 'pending' "
            "ORDER BY CASE priority "
            "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
            "  WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, "
            "created_at ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def claim_task(task_id: int, agent: str) -> bool:
    """Mark a task as in_progress (claimed by an agent)."""
    conn = _get_db()
    conn.execute(
        "UPDATE agent_tasks SET status = 'in_progress', agent = ?, "
        "updated_at = datetime('now') WHERE id = ? AND status = 'pending'",
        (agent, task_id)
    )
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def complete_task(task_id: int, result: str) -> bool:
    """Mark a task as completed with result."""
    conn = _get_db()
    conn.execute(
        "UPDATE agent_tasks SET status = 'completed', result = ?, "
        "completed_at = datetime('now'), updated_at = datetime('now') "
        "WHERE id = ?",
        (result, task_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Task #{task_id} completed")
    return True


def fail_task(task_id: int, error: str) -> bool:
    """Mark a task as failed."""
    conn = _get_db()
    conn.execute(
        "UPDATE agent_tasks SET status = 'failed', result = ?, "
        "updated_at = datetime('now') WHERE id = ?",
        (json.dumps({"error": error}), task_id)
    )
    conn.commit()
    conn.close()
    logger.warning(f"Task #{task_id} failed: {error}")
    return True


def mark_research_done(task_id: int) -> bool:
    """Mark that research gate was called before executing this task."""
    conn = _get_db()
    conn.execute(
        "UPDATE agent_tasks SET research_done = 1, updated_at = datetime('now') "
        "WHERE id = ?", (task_id,)
    )
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Status and reporting
# ---------------------------------------------------------------------------

def get_status() -> Dict[str, Any]:
    """Get overall agent workload status."""
    conn = _get_db()

    status = {}

    # Tasks by agent and status
    for row in conn.execute(
        "SELECT agent, status, COUNT(*) as cnt FROM agent_tasks "
        "GROUP BY agent, status"
    ).fetchall():
        r = dict(row)
        agent = r["agent"]
        if agent not in status:
            status[agent] = {}
        status[agent][r["status"]] = r["cnt"]

    # Recent completions
    recent = [dict(r) for r in conn.execute(
        "SELECT id, task, agent, result, completed_at FROM agent_tasks "
        "WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 5"
    ).fetchall()]

    # Research gate compliance
    total_completed = conn.execute(
        "SELECT COUNT(*) FROM agent_tasks WHERE status = 'completed'"
    ).fetchone()[0]
    research_compliant = conn.execute(
        "SELECT COUNT(*) FROM agent_tasks WHERE status = 'completed' AND research_done = 1"
    ).fetchone()[0]

    conn.close()

    return {
        "by_agent": status,
        "recent_completions": recent,
        "research_compliance": {
            "total_completed": total_completed,
            "research_done": research_compliant,
            "compliance_pct": round(research_compliant / max(1, total_completed) * 100, 1),
        },
    }


def format_pending_for_telegram(agent: str = None) -> str:
    """Format pending tasks for Telegram display."""
    tasks = get_pending(agent)
    if not tasks:
        return "No pending tasks." + (f" ({agent} queue)" if agent else "")

    lines = [f"Pending tasks ({len(tasks)}):"]
    for t in tasks[:10]:
        pri_icon = {"critical": "!!", "high": "!", "medium": "-", "low": "."}.get(t["priority"], "-")
        lines.append(f"  {pri_icon} #{t['id']} [{t['agent']}] {t['task'][:60]}")

    if len(tasks) > 10:
        lines.append(f"  ... and {len(tasks) - 10} more")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Integration: run research gate before task execution
# ---------------------------------------------------------------------------

def execute_with_research(task_id: int) -> Dict[str, Any]:
    """Run research gate and return context for a task.

    Call this before executing any task to enforce research-first.
    Returns the research context and marks the task as research_done.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "research_gate", REPO_ROOT / "execution" / "research_gate.py"
    )
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)

    context = rg.gather_context()
    mark_research_done(task_id)
    claim_task(task_id, "claude")

    return {
        "task_id": task_id,
        "research_context": context,
        "prompt_section": rg.format_for_prompt(context),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Grok-Claude Orchestrator")
    sub = parser.add_subparsers(dest="command")

    # Add task
    add_p = sub.add_parser("add", help="Add a task")
    add_p.add_argument("--task", required=True, help="Task description")
    add_p.add_argument("--agent", default="claude", choices=["claude", "ralph", "grok", "any"])
    add_p.add_argument("--priority", default="medium", choices=["critical", "high", "medium", "low"])
    add_p.add_argument("--category", default="general")

    # View pending
    pend = sub.add_parser("pending", help="Show pending tasks")
    pend.add_argument("--agent", default=None)

    # Complete task
    comp = sub.add_parser("complete", help="Complete a task")
    comp.add_argument("--id", type=int, required=True)
    comp.add_argument("--result", required=True)

    # Fail task
    fail = sub.add_parser("fail", help="Fail a task")
    fail.add_argument("--id", type=int, required=True)
    fail.add_argument("--error", required=True)

    # Status
    sub.add_parser("status", help="Agent workload status")

    args = parser.parse_args()

    if args.command == "add":
        task_id = add_task(args.task, args.agent, args.priority, args.category)
        print(f"Task #{task_id} created")
    elif args.command == "pending":
        print(format_pending_for_telegram(args.agent))
    elif args.command == "complete":
        complete_task(args.id, args.result)
        print(f"Task #{args.id} completed")
    elif args.command == "fail":
        fail_task(args.id, args.error)
        print(f"Task #{args.id} failed")
    elif args.command == "status":
        print(json.dumps(get_status(), indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
