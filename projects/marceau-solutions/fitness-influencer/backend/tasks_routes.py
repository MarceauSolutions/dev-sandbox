#!/usr/bin/env python3
"""
Task Management Routes for Fitness Influencer AI v2.0

Provides unified task tracking with sections:
- TODAY: Urgent tasks for today
- THIS WEEK: Tasks to complete this week
- CIRCLE BACK: Deferred tasks with trigger conditions
- RECENTLY DONE: Completed tasks (last 7 days)

Multi-tenant support: Each user has isolated task data.

Usage:
    from backend.tasks_routes import router as tasks_router
    app.include_router(tasks_router)
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict, field
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Data directory for task storage
DATA_DIR = Path(__file__).parent.parent / "data" / "tenants"


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"      # P0 - Do immediately
    HIGH = "high"              # P1 - Today
    MEDIUM = "medium"          # P2 - This week
    LOW = "low"                # P3 - When time permits
    DEFERRED = "deferred"      # Circle back later


class TaskSection(str, Enum):
    """Task sections matching TASKS.md structure."""
    TODAY = "today"
    THIS_WEEK = "this_week"
    CIRCLE_BACK = "circle_back"
    RECENTLY_DONE = "recently_done"


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


# ============================================================================
# Pydantic Models
# ============================================================================

class TaskCreate(BaseModel):
    """Model for creating a new task."""
    title: str
    description: Optional[str] = None
    section: TaskSection = TaskSection.TODAY
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[str] = None  # ISO format
    trigger_condition: Optional[str] = None  # For CIRCLE_BACK items
    tags: List[str] = []
    project: Optional[str] = None  # e.g., "fitness-influencer", "x-automation"


class TaskUpdate(BaseModel):
    """Model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    section: Optional[TaskSection] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None
    trigger_condition: Optional[str] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    progress: Optional[int] = None  # 0-100


class Task(BaseModel):
    """Full task model."""
    id: str
    title: str
    description: Optional[str] = None
    section: TaskSection
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[str] = None
    trigger_condition: Optional[str] = None
    tags: List[str] = []
    project: Optional[str] = None
    progress: int = 0
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


# ============================================================================
# Data Storage Functions
# ============================================================================

def get_tenant_path(tenant_id: str) -> Path:
    """Get path to tenant's task data file."""
    tenant_dir = DATA_DIR / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir / "tasks.json"


def load_tasks(tenant_id: str) -> Dict[str, Any]:
    """Load tasks for a tenant."""
    path = get_tenant_path(tenant_id)

    if not path.exists():
        return {
            "tenant_id": tenant_id,
            "tasks": [],
            "stats": {
                "total_created": 0,
                "total_completed": 0,
                "last_updated": None
            }
        }

    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tasks for {tenant_id}: {e}")
        return {
            "tenant_id": tenant_id,
            "tasks": [],
            "stats": {"total_created": 0, "total_completed": 0, "last_updated": None}
        }


def save_tasks(tenant_id: str, data: Dict[str, Any]) -> None:
    """Save tasks for a tenant."""
    path = get_tenant_path(tenant_id)
    data["stats"]["last_updated"] = datetime.utcnow().isoformat()

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving tasks for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save tasks")


def generate_task_id() -> str:
    """Generate a unique task ID."""
    import uuid
    return f"task_{uuid.uuid4().hex[:12]}"


# ============================================================================
# API Routes
# ============================================================================

@router.get("/")
async def list_tasks(
    tenant_id: str = Query(default="wmarceau", description="Tenant ID"),
    section: Optional[TaskSection] = Query(default=None, description="Filter by section"),
    status: Optional[TaskStatus] = Query(default=None, description="Filter by status"),
    project: Optional[str] = Query(default=None, description="Filter by project"),
    tag: Optional[str] = Query(default=None, description="Filter by tag")
) -> Dict[str, Any]:
    """
    List all tasks with optional filtering.

    Returns tasks organized by section.
    """
    data = load_tasks(tenant_id)
    tasks = data.get("tasks", [])

    # Apply filters
    if section:
        tasks = [t for t in tasks if t.get("section") == section.value]
    if status:
        tasks = [t for t in tasks if t.get("status") == status.value]
    if project:
        tasks = [t for t in tasks if t.get("project") == project]
    if tag:
        tasks = [t for t in tasks if tag in t.get("tags", [])]

    # Organize by section
    organized = {
        "today": [],
        "this_week": [],
        "circle_back": [],
        "recently_done": []
    }

    for task in tasks:
        section_key = task.get("section", "today")
        if section_key in organized:
            organized[section_key].append(task)

    # Sort: today/this_week by priority, circle_back by trigger, done by completed_at
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "deferred": 4}

    for key in ["today", "this_week"]:
        organized[key].sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))

    organized["recently_done"].sort(
        key=lambda x: x.get("completed_at", ""),
        reverse=True
    )

    return {
        "tenant_id": tenant_id,
        "sections": organized,
        "counts": {
            "today": len(organized["today"]),
            "this_week": len(organized["this_week"]),
            "circle_back": len(organized["circle_back"]),
            "recently_done": len(organized["recently_done"])
        },
        "total": len(tasks)
    }


@router.post("/")
async def create_task(
    task: TaskCreate,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Create a new task."""
    data = load_tasks(tenant_id)

    now = datetime.utcnow().isoformat()
    task_id = generate_task_id()

    new_task = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "section": task.section.value,
        "priority": task.priority.value,
        "status": TaskStatus.PENDING.value,
        "due_date": task.due_date,
        "trigger_condition": task.trigger_condition,
        "tags": task.tags,
        "project": task.project,
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "completed_at": None
    }

    data["tasks"].append(new_task)
    data["stats"]["total_created"] = data["stats"].get("total_created", 0) + 1

    save_tasks(tenant_id, data)

    logger.info(f"Created task {task_id}: {task.title}")

    return {
        "success": True,
        "task": new_task,
        "message": f"Task created in {task.section.value}"
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Get a specific task by ID."""
    data = load_tasks(tenant_id)

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return {"task": task}

    raise HTTPException(status_code=404, detail="Task not found")


@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    update: TaskUpdate,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Update a task."""
    data = load_tasks(tenant_id)

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            # Apply updates
            if update.title is not None:
                task["title"] = update.title
            if update.description is not None:
                task["description"] = update.description
            if update.section is not None:
                task["section"] = update.section.value
            if update.priority is not None:
                task["priority"] = update.priority.value
            if update.status is not None:
                task["status"] = update.status.value
                if update.status == TaskStatus.COMPLETE:
                    task["completed_at"] = datetime.utcnow().isoformat()
                    task["progress"] = 100
                    data["stats"]["total_completed"] = data["stats"].get("total_completed", 0) + 1
            if update.due_date is not None:
                task["due_date"] = update.due_date
            if update.trigger_condition is not None:
                task["trigger_condition"] = update.trigger_condition
            if update.tags is not None:
                task["tags"] = update.tags
            if update.project is not None:
                task["project"] = update.project
            if update.progress is not None:
                task["progress"] = min(100, max(0, update.progress))

            task["updated_at"] = datetime.utcnow().isoformat()

            save_tasks(tenant_id, data)

            return {
                "success": True,
                "task": task,
                "message": "Task updated"
            }

    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Mark a task as complete and move to recently_done."""
    data = load_tasks(tenant_id)

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = TaskStatus.COMPLETE.value
            task["section"] = TaskSection.RECENTLY_DONE.value
            task["progress"] = 100
            task["completed_at"] = datetime.utcnow().isoformat()
            task["updated_at"] = datetime.utcnow().isoformat()

            data["stats"]["total_completed"] = data["stats"].get("total_completed", 0) + 1

            save_tasks(tenant_id, data)

            return {
                "success": True,
                "task": task,
                "message": "Task completed! Great work!"
            }

    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/move")
async def move_task(
    task_id: str,
    target_section: TaskSection,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Move a task to a different section."""
    data = load_tasks(tenant_id)

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            old_section = task.get("section")
            task["section"] = target_section.value
            task["updated_at"] = datetime.utcnow().isoformat()

            # If moving to CIRCLE_BACK, set priority to deferred
            if target_section == TaskSection.CIRCLE_BACK:
                task["priority"] = TaskPriority.DEFERRED.value

            save_tasks(tenant_id, data)

            return {
                "success": True,
                "task": task,
                "message": f"Moved from {old_section} to {target_section.value}"
            }

    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Delete a task."""
    data = load_tasks(tenant_id)

    original_count = len(data.get("tasks", []))
    data["tasks"] = [t for t in data.get("tasks", []) if t.get("id") != task_id]

    if len(data["tasks"]) == original_count:
        raise HTTPException(status_code=404, detail="Task not found")

    save_tasks(tenant_id, data)

    return {
        "success": True,
        "message": "Task deleted"
    }


@router.get("/stats/summary")
async def get_stats(
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Get task statistics."""
    data = load_tasks(tenant_id)
    tasks = data.get("tasks", [])

    # Count by section
    section_counts = {section.value: 0 for section in TaskSection}
    for task in tasks:
        section = task.get("section", "today")
        if section in section_counts:
            section_counts[section] += 1

    # Count by status
    status_counts = {status.value: 0 for status in TaskStatus}
    for task in tasks:
        status = task.get("status", "pending")
        if status in status_counts:
            status_counts[status] += 1

    # Count by project
    project_counts = {}
    for task in tasks:
        project = task.get("project") or "unassigned"
        project_counts[project] = project_counts.get(project, 0) + 1

    # Overdue tasks (today section with past due_date)
    now = datetime.utcnow()
    overdue = 0
    for task in tasks:
        if task.get("section") == "today" and task.get("due_date"):
            try:
                due = datetime.fromisoformat(task["due_date"].replace("Z", ""))
                if due < now and task.get("status") != "complete":
                    overdue += 1
            except:
                pass

    return {
        "tenant_id": tenant_id,
        "by_section": section_counts,
        "by_status": status_counts,
        "by_project": project_counts,
        "overdue": overdue,
        "total_created": data.get("stats", {}).get("total_created", 0),
        "total_completed": data.get("stats", {}).get("total_completed", 0),
        "completion_rate": round(
            data.get("stats", {}).get("total_completed", 0) /
            max(1, data.get("stats", {}).get("total_created", 1)) * 100,
            1
        )
    }


@router.post("/cleanup")
async def cleanup_old_tasks(
    days: int = Query(default=7, description="Remove completed tasks older than N days"),
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Remove old completed tasks from recently_done."""
    data = load_tasks(tenant_id)

    cutoff = datetime.utcnow() - timedelta(days=days)
    original_count = len(data.get("tasks", []))

    data["tasks"] = [
        t for t in data.get("tasks", [])
        if not (
            t.get("section") == "recently_done" and
            t.get("completed_at") and
            datetime.fromisoformat(t["completed_at"].replace("Z", "")) < cutoff
        )
    ]

    removed = original_count - len(data["tasks"])

    if removed > 0:
        save_tasks(tenant_id, data)

    return {
        "success": True,
        "removed": removed,
        "message": f"Removed {removed} old completed tasks"
    }


@router.post("/import")
async def import_tasks_from_markdown(
    content: str,
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """
    Import tasks from TASKS.md format.

    Expected format:
    ## TODAY
    - [ ] Task title
    - [x] Completed task

    ## THIS WEEK
    ...
    """
    data = load_tasks(tenant_id)
    imported = 0

    current_section = TaskSection.TODAY
    section_map = {
        "TODAY": TaskSection.TODAY,
        "THIS WEEK": TaskSection.THIS_WEEK,
        "CIRCLE BACK": TaskSection.CIRCLE_BACK,
        "RECENTLY DONE": TaskSection.RECENTLY_DONE
    }

    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Check for section headers
        if line.startswith("## "):
            header = line[3:].upper()
            if header in section_map:
                current_section = section_map[header]
            continue

        # Check for task items
        if line.startswith("- [ ] ") or line.startswith("- [x] "):
            is_complete = line.startswith("- [x] ")
            title = line[6:].strip()

            if not title:
                continue

            now = datetime.utcnow().isoformat()
            task_id = generate_task_id()

            new_task = {
                "id": task_id,
                "title": title,
                "description": None,
                "section": current_section.value,
                "priority": TaskPriority.MEDIUM.value,
                "status": TaskStatus.COMPLETE.value if is_complete else TaskStatus.PENDING.value,
                "due_date": None,
                "trigger_condition": None,
                "tags": [],
                "project": None,
                "progress": 100 if is_complete else 0,
                "created_at": now,
                "updated_at": now,
                "completed_at": now if is_complete else None
            }

            data["tasks"].append(new_task)
            data["stats"]["total_created"] = data["stats"].get("total_created", 0) + 1
            if is_complete:
                data["stats"]["total_completed"] = data["stats"].get("total_completed", 0) + 1
            imported += 1

    if imported > 0:
        save_tasks(tenant_id, data)

    return {
        "success": True,
        "imported": imported,
        "message": f"Imported {imported} tasks"
    }


@router.get("/export/markdown")
async def export_tasks_to_markdown(
    tenant_id: str = Query(default="wmarceau", description="Tenant ID")
) -> Dict[str, Any]:
    """Export tasks to TASKS.md format."""
    data = load_tasks(tenant_id)
    tasks = data.get("tasks", [])

    # Organize by section
    sections = {
        "today": [],
        "this_week": [],
        "circle_back": [],
        "recently_done": []
    }

    for task in tasks:
        section = task.get("section", "today")
        if section in sections:
            sections[section].append(task)

    # Build markdown
    lines = [
        "# TASKS.md",
        "",
        f"_Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
        "",
        "## TODAY",
        ""
    ]

    for task in sections["today"]:
        checkbox = "[x]" if task.get("status") == "complete" else "[ ]"
        priority = f"**[{task.get('priority', 'medium').upper()}]** " if task.get("priority") in ["critical", "high"] else ""
        lines.append(f"- {checkbox} {priority}{task['title']}")

    if not sections["today"]:
        lines.append("_No tasks for today_")

    lines.extend(["", "## THIS WEEK", ""])

    for task in sections["this_week"]:
        checkbox = "[x]" if task.get("status") == "complete" else "[ ]"
        lines.append(f"- {checkbox} {task['title']}")

    if not sections["this_week"]:
        lines.append("_No tasks for this week_")

    lines.extend(["", "## CIRCLE BACK", "", "_Deferred tasks with trigger conditions_", ""])

    for task in sections["circle_back"]:
        trigger = f" (Trigger: {task['trigger_condition']})" if task.get("trigger_condition") else ""
        lines.append(f"- [ ] {task['title']}{trigger}")

    if not sections["circle_back"]:
        lines.append("_No deferred tasks_")

    lines.extend(["", "## RECENTLY DONE", ""])

    for task in sections["recently_done"][:10]:  # Last 10
        completed = task.get("completed_at", "")[:10] if task.get("completed_at") else ""
        lines.append(f"- [x] {task['title']} ({completed})")

    if not sections["recently_done"]:
        lines.append("_No recently completed tasks_")

    lines.append("")

    return {
        "markdown": "\n".join(lines),
        "sections": {k: len(v) for k, v in sections.items()}
    }
