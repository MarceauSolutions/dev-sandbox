#!/usr/bin/env python3
"""
Workout Admin Routes — Coach/Admin endpoints for managing clients and workout templates.

NOT auth-protected (matches existing admin pattern in gamification_routes, tasks_routes).
Provides:
- Client CRUD (list, create, detail, update, regenerate token)
- Workout template CRUD (list, create, get)
- Workout assignment (assign a template to a client for a specific week)

Data Sources:
- Client data: data/clients/ via auth module
- Templates: data/workout_templates/{template_id}.json
- Template index: data/workout_templates/index.json
- Assignments: data/clients/{client_id}/workouts.json
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import uuid
import logging

from backend.auth import (
    create_client,
    list_clients,
    load_client_profile,
    regenerate_token,
    DATA_DIR as CLIENTS_DIR,
    GAMIFICATION_DIR,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin — Clients & Workouts"])

# Template storage
TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "workout_templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Pydantic Models
# ============================================================================

class CreateClientRequest(BaseModel):
    """Create a new coaching client."""
    name: str
    email: str
    phone: Optional[str] = None
    goals: Optional[str] = None


class UpdateClientRequest(BaseModel):
    """Update an existing client's profile."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    goals: Optional[str] = None
    program: Optional[str] = None
    coach_notes: Optional[str] = None
    active: Optional[bool] = None


class WorkoutExercise(BaseModel):
    """A single exercise within a workout day."""
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = None  # e.g., "8-12" or "AMRAP"
    weight: Optional[str] = None  # e.g., "135 lbs" or "bodyweight"
    rest_seconds: Optional[int] = 90
    notes: Optional[str] = None
    superset_group: Optional[str] = None  # Group exercises into supersets


class WorkoutDay(BaseModel):
    """A single day within a workout template."""
    day_name: str  # e.g., "Day 1 — Push", "Monday — Upper Body"
    focus: Optional[str] = None  # e.g., "chest/shoulders/triceps"
    warmup: Optional[str] = None
    exercises: List[WorkoutExercise] = []
    cooldown: Optional[str] = None
    duration_estimate_minutes: Optional[int] = None


class CreateTemplateRequest(BaseModel):
    """Create a new workout template."""
    name: str  # e.g., "4-Week Hypertrophy Block A"
    description: Optional[str] = None
    difficulty: Optional[str] = "intermediate"  # beginner, intermediate, advanced
    goal: Optional[str] = None  # e.g., "hypertrophy", "strength", "fat_loss"
    days_per_week: int = 4
    days: List[WorkoutDay] = []
    tags: List[str] = []


class AssignWorkoutRequest(BaseModel):
    """Assign a workout template to a client for a specific week."""
    template_id: str
    week_start: str  # ISO date, e.g., "2026-03-03" (Monday)
    notes: Optional[str] = None  # Coach notes for this specific assignment
    modifications: Optional[Dict[str, Any]] = None  # Per-client tweaks


# ============================================================================
# Template Storage Helpers
# ============================================================================

def _load_template_index() -> dict:
    """Load the workout template index."""
    idx_file = TEMPLATES_DIR / "index.json"
    if idx_file.exists():
        with open(idx_file, 'r') as f:
            return json.load(f)
    return {"templates": []}


def _save_template_index(index: dict):
    """Save the workout template index."""
    with open(TEMPLATES_DIR / "index.json", 'w') as f:
        json.dump(index, f, indent=2, default=str)


def _load_template(template_id: str) -> dict:
    """Load a workout template by ID."""
    tpl_file = TEMPLATES_DIR / f"{template_id}.json"
    if not tpl_file.exists():
        return None
    with open(tpl_file, 'r') as f:
        return json.load(f)


def _save_template(template_id: str, data: dict):
    """Save a workout template."""
    with open(TEMPLATES_DIR / f"{template_id}.json", 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _load_client_workouts(client_id: str) -> dict:
    """Load a client's workout assignments."""
    wk_file = CLIENTS_DIR / client_id / "workouts.json"
    if wk_file.exists():
        with open(wk_file, 'r') as f:
            return json.load(f)
    default = {"assignments": [], "stats": {"total_assigned": 0, "total_completed": 0}}
    wk_file.parent.mkdir(parents=True, exist_ok=True)
    with open(wk_file, 'w') as f:
        json.dump(default, f, indent=2)
    return default


def _save_client_workouts(client_id: str, data: dict):
    """Save a client's workout data."""
    wk_file = CLIENTS_DIR / client_id / "workouts.json"
    with open(wk_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ============================================================================
# Client Management Endpoints
# ============================================================================

@router.get("/clients")
async def admin_list_clients():
    """List all coaching clients with summary stats (level, streak, workouts)."""
    clients = list_clients()
    return {
        "clients": clients,
        "total": len(clients),
    }


@router.post("/clients")
async def admin_create_client(body: CreateClientRequest):
    """
    Create a new coaching client. Returns client_id, magic link token, and login URL.
    Also initializes gamification profile and tenant task storage.
    """
    # Check for duplicate email
    existing = list_clients()
    for c in existing:
        if c.get("email", "").lower() == body.email.lower():
            raise HTTPException(status_code=409, detail=f"Client with email {body.email} already exists")

    result = create_client(
        name=body.name,
        email=body.email,
        phone=body.phone,
        goals=body.goals,
    )

    logger.info(f"Created new client: {result['client_id']} ({body.name})")

    return {
        "success": True,
        "client_id": result["client_id"],
        "token": result["token"],
        "login_url": result["login_url"],
        "profile": result["profile"],
        "message": f"Client '{body.name}' created. Share this magic link for login.",
    }


@router.get("/clients/{client_id}")
async def admin_get_client(client_id: str):
    """Get detailed view of a single client — profile, gamification, workout stats."""
    profile = load_client_profile(client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    # Load gamification
    gam_file = GAMIFICATION_DIR / f"{client_id}_player.json"
    gamification = None
    if gam_file.exists():
        with open(gam_file, 'r') as f:
            gamification = json.load(f)

    # Load workout stats
    workouts = _load_client_workouts(client_id)

    # Load auth info
    auth_file = CLIENTS_DIR / client_id / "auth.json"
    auth_info = None
    if auth_file.exists():
        with open(auth_file, 'r') as f:
            auth_info = json.load(f)

    # Load form checks summary
    fc_file = CLIENTS_DIR / client_id / "form_checks.json"
    form_check_count = 0
    if fc_file.exists():
        with open(fc_file, 'r') as f:
            fc_data = json.load(f)
        form_check_count = len(fc_data.get("checks", []))

    return {
        "profile": profile,
        "gamification": {
            "player": gamification.get("player", {}) if gamification else {},
            "stats": gamification.get("stats", {}) if gamification else {},
            "achievements_unlocked": sum(
                1 for a in gamification.get("achievements", []) if a.get("unlocked")
            ) if gamification else 0,
            "achievements_total": len(gamification.get("achievements", [])) if gamification else 0,
        },
        "workouts": {
            "total_assigned": workouts.get("stats", {}).get("total_assigned", 0),
            "total_completed": workouts.get("stats", {}).get("total_completed", 0),
            "assignments_count": len(workouts.get("assignments", [])),
        },
        "form_checks": form_check_count,
        "auth": {
            "last_login": auth_info.get("last_login") if auth_info else None,
            "token_created": auth_info.get("created_at") if auth_info else None,
        },
    }


@router.patch("/clients/{client_id}")
async def admin_update_client(client_id: str, body: UpdateClientRequest):
    """Update a client's profile fields."""
    profile_path = CLIENTS_DIR / client_id / "profile.json"
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Client not found")

    with open(profile_path, 'r') as f:
        profile = json.load(f)

    # Apply updates
    if body.name is not None:
        profile["name"] = body.name
    if body.email is not None:
        profile["email"] = body.email
    if body.phone is not None:
        profile["phone"] = body.phone
    if body.goals is not None:
        profile["goals"] = body.goals
    if body.program is not None:
        profile["program"] = body.program
    if body.coach_notes is not None:
        profile["coach_notes"] = body.coach_notes
    if body.active is not None:
        profile["active"] = body.active

    profile["updated_at"] = datetime.utcnow().isoformat()

    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2, default=str)

    logger.info(f"Updated client profile: {client_id}")

    return {
        "success": True,
        "profile": profile,
        "message": "Client profile updated",
    }


@router.post("/clients/{client_id}/regenerate-token")
async def admin_regenerate_token(client_id: str):
    """Generate a new magic link token for a client, invalidating the old one."""
    profile = load_client_profile(client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    new_token = regenerate_token(client_id)
    login_url = f"/client/#login?token={new_token}"

    logger.info(f"Regenerated token for client: {client_id}")

    return {
        "success": True,
        "client_id": client_id,
        "token": new_token,
        "login_url": login_url,
        "message": "New magic link generated. The old link is no longer valid.",
    }


# ============================================================================
# Workout Assignment Endpoint
# ============================================================================

@router.post("/clients/{client_id}/assign-workout")
async def admin_assign_workout(client_id: str, body: AssignWorkoutRequest):
    """
    Assign a workout template to a client for a specific week.

    1. Load the template
    2. Create an assignment entry with scheduled dates for each day
    3. Save to client's workouts.json
    """
    # Verify client exists
    profile = load_client_profile(client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    # Load the template
    template = _load_template(body.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{body.template_id}' not found")

    # Parse week start date
    try:
        week_start = date.fromisoformat(body.week_start)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid week_start date. Use ISO format: YYYY-MM-DD")

    # Build assignment with scheduled dates for each day
    assignment_id = f"assign_{uuid.uuid4().hex[:10]}"
    template_days = template.get("days", [])

    scheduled_days = []
    for i, tpl_day in enumerate(template_days):
        scheduled_date = (week_start + timedelta(days=i)).isoformat()
        scheduled_days.append({
            "day_index": i,
            "day_name": tpl_day.get("day_name", f"Day {i + 1}"),
            "focus": tpl_day.get("focus"),
            "warmup": tpl_day.get("warmup"),
            "exercises": tpl_day.get("exercises", []),
            "cooldown": tpl_day.get("cooldown"),
            "duration_estimate_minutes": tpl_day.get("duration_estimate_minutes"),
            "scheduled_date": scheduled_date,
            "completed": False,
            "completed_at": None,
            "duration_minutes": None,
            "notes": None,
        })

    assignment = {
        "id": assignment_id,
        "template_id": body.template_id,
        "template_name": template.get("name", "Unnamed Template"),
        "week_start": body.week_start,
        "assigned_at": datetime.utcnow().isoformat(),
        "coach_notes": body.notes,
        "modifications": body.modifications,
        "days": scheduled_days,
    }

    # Save to client workouts
    workouts = _load_client_workouts(client_id)
    workouts["assignments"].append(assignment)
    workouts["stats"]["total_assigned"] = workouts["stats"].get("total_assigned", 0) + len(scheduled_days)
    _save_client_workouts(client_id, workouts)

    logger.info(f"Assigned template '{template.get('name')}' to client {client_id} for week {body.week_start}")

    return {
        "success": True,
        "assignment_id": assignment_id,
        "template_name": template.get("name"),
        "week_start": body.week_start,
        "days_scheduled": len(scheduled_days),
        "assignment": assignment,
        "message": f"Assigned '{template.get('name')}' to {profile.get('name')} for week of {body.week_start}",
    }


# ============================================================================
# Workout Template Endpoints
# ============================================================================

@router.get("/workouts/templates")
async def admin_list_templates():
    """List all workout templates."""
    index = _load_template_index()
    templates = index.get("templates", [])
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.post("/workouts/templates")
async def admin_create_template(body: CreateTemplateRequest):
    """Create a new workout template."""
    template_id = f"tpl_{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat()

    # Serialize the days with exercises
    days_data = []
    for day in body.days:
        exercises_data = []
        for ex in day.exercises:
            exercises_data.append({
                "name": ex.name,
                "sets": ex.sets,
                "reps": ex.reps,
                "weight": ex.weight,
                "rest_seconds": ex.rest_seconds,
                "notes": ex.notes,
                "superset_group": ex.superset_group,
            })
        days_data.append({
            "day_name": day.day_name,
            "focus": day.focus,
            "warmup": day.warmup,
            "exercises": exercises_data,
            "cooldown": day.cooldown,
            "duration_estimate_minutes": day.duration_estimate_minutes,
        })

    template = {
        "id": template_id,
        "name": body.name,
        "description": body.description,
        "difficulty": body.difficulty,
        "goal": body.goal,
        "days_per_week": body.days_per_week,
        "days": days_data,
        "tags": body.tags,
        "created_at": now,
        "updated_at": now,
    }

    # Save the template file
    _save_template(template_id, template)

    # Update the index
    index = _load_template_index()
    index["templates"].append({
        "id": template_id,
        "name": body.name,
        "difficulty": body.difficulty,
        "goal": body.goal,
        "days_per_week": body.days_per_week,
        "tags": body.tags,
        "created_at": now,
    })
    _save_template_index(index)

    logger.info(f"Created workout template: {template_id} ({body.name})")

    return {
        "success": True,
        "template_id": template_id,
        "template": template,
        "message": f"Template '{body.name}' created with {len(days_data)} days",
    }


@router.get("/workouts/templates/{template_id}")
async def admin_get_template(template_id: str):
    """Get a specific workout template with full exercise details."""
    template = _load_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": template}
