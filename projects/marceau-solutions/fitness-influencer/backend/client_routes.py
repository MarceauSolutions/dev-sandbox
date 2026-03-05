#!/usr/bin/env python3
"""
Client Portal API Routes — Coaching Client-Facing Endpoints

All endpoints require Bearer token authentication via get_current_client dependency.
Provides:
- Profile & dashboard
- Workout assignments (view, complete)
- Form check submissions & history
- AI coaching chat
- Progress & achievements

Data Source: JSON files per client in data/clients/{client_id}/
Gamification: JSON files in data/gamification/{client_id}_player.json
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import os
import uuid
import copy
import logging

from backend.auth import get_current_client, DATA_DIR as CLIENTS_DIR, GAMIFICATION_DIR
from backend.auth import CLIENT_DEFAULT_PLAYER_STATE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client", tags=["Client Portal"])

# Upload directory for form check videos
UPLOADS_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Client chat message."""
    message: str
    context: Optional[str] = None  # e.g., "workout", "nutrition", "general"


class FormCheckSubmit(BaseModel):
    """Form check submission metadata (video uploaded separately)."""
    exercise_name: str
    notes: Optional[str] = None
    video_filename: Optional[str] = None


class WorkoutCompleteRequest(BaseModel):
    """Mark a workout day as completed."""
    day_index: int = 0  # Which day within the assignment to mark
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# Gamification Helpers (matches gamification_routes.py patterns)
# ============================================================================

def _load_client_gamification(client_id: str) -> dict:
    """Load gamification state for a client."""
    player_file = GAMIFICATION_DIR / f"{client_id}_player.json"
    if player_file.exists():
        with open(player_file, 'r') as f:
            state = json.load(f)
        # Migrate: ensure all default keys exist
        for key in CLIENT_DEFAULT_PLAYER_STATE:
            if key not in state:
                state[key] = copy.deepcopy(CLIENT_DEFAULT_PLAYER_STATE[key])
        # Migrate: ensure all stats keys
        default_stats = CLIENT_DEFAULT_PLAYER_STATE["stats"].copy()
        for key, val in default_stats.items():
            if key not in state.get("stats", {}):
                state.setdefault("stats", {})[key] = val
        if "action_log" not in state:
            state["action_log"] = []
        return state
    # Create default
    state = copy.deepcopy(CLIENT_DEFAULT_PLAYER_STATE)
    _save_client_gamification(client_id, state)
    return state


def _save_client_gamification(client_id: str, state: dict):
    """Save gamification state for a client."""
    GAMIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    player_file = GAMIFICATION_DIR / f"{client_id}_player.json"
    with open(player_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def _get_streak_multiplier(streak: int, multipliers: list) -> float:
    """Get the XP multiplier based on current streak."""
    current_mult = 1.0
    for m in multipliers:
        if streak >= m["days"]:
            current_mult = m["multiplier"]
    return current_mult


def _check_level_up(state: dict) -> bool:
    """Check if player should level up and update accordingly."""
    player = state["player"]
    levels = state["levels"]
    leveled_up = False
    for level_info in reversed(levels):
        if player["xp_total"] >= level_info["xp_required"] and player["level"] < level_info["level"]:
            player["level"] = level_info["level"]
            player["title"] = level_info["title"]
            leveled_up = True
            break
    # Check level-based achievements
    if leveled_up and player["level"] >= 5:
        for a in state["achievements"]:
            if a["id"] == "halfway_there" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
    return leveled_up


def _check_client_achievements(state: dict) -> list:
    """Check for client-specific stat-based achievements. Returns newly unlocked names."""
    player = state["player"]
    stats = state["stats"]
    unlocked = []

    # First Workout
    if stats.get("workouts_completed", 0) >= 1:
        for a in state["achievements"]:
            if a["id"] == "first_workout" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Form Master — 5 form checks with 80%+ score
    if stats.get("form_checks", 0) >= 5:
        for a in state["achievements"]:
            if a["id"] == "form_master" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # PR Hunter — 5 personal records
    if stats.get("personal_records", 0) >= 5:
        for a in state["achievements"]:
            if a["id"] == "pr_hunter" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Streak achievements
    if player.get("current_streak", 0) >= 7:
        for a in state["achievements"]:
            if a["id"] == "week_warrior" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    if player.get("current_streak", 0) >= 30:
        for a in state["achievements"]:
            if a["id"] == "iron_will" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    return unlocked


def _update_streak(state: dict):
    """Update the client's activity streak."""
    player = state["player"]
    today = date.today().isoformat()
    last_active = player.get("last_active_date")

    if last_active == today:
        return  # Already active today

    if last_active:
        last_date = date.fromisoformat(last_active)
        if (date.today() - last_date).days == 1:
            player["current_streak"] += 1
            player["best_streak"] = max(player["best_streak"], player["current_streak"])
        elif (date.today() - last_date).days > 1:
            player["current_streak"] = 1
    else:
        player["current_streak"] = 1

    player["last_active_date"] = today


def _reset_daily_quests_if_needed(state: dict):
    """Reset daily quests if it's a new day."""
    today = date.today().isoformat()
    if state.get("last_quest_reset") != today:
        for quest in state["daily_quests"]:
            quest["completed"] = False
        state["last_quest_reset"] = today


# ============================================================================
# Client data helpers
# ============================================================================

def _load_client_workouts(client_id: str) -> dict:
    """Load a client's workout assignments."""
    wk_file = CLIENTS_DIR / client_id / "workouts.json"
    if wk_file.exists():
        with open(wk_file, 'r') as f:
            return json.load(f)
    default = {"assignments": [], "stats": {"total_assigned": 0, "total_completed": 0}}
    with open(wk_file, 'w') as f:
        json.dump(default, f, indent=2)
    return default


def _save_client_workouts(client_id: str, data: dict):
    """Save a client's workout data."""
    wk_file = CLIENTS_DIR / client_id / "workouts.json"
    with open(wk_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _load_form_checks(client_id: str) -> dict:
    """Load a client's form check history."""
    fc_file = CLIENTS_DIR / client_id / "form_checks.json"
    if fc_file.exists():
        with open(fc_file, 'r') as f:
            return json.load(f)
    default = {"checks": []}
    with open(fc_file, 'w') as f:
        json.dump(default, f, indent=2)
    return default


def _save_form_checks(client_id: str, data: dict):
    """Save form check data."""
    fc_file = CLIENTS_DIR / client_id / "form_checks.json"
    with open(fc_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _load_chat_history(client_id: str) -> dict:
    """Load a client's chat history."""
    ch_file = CLIENTS_DIR / client_id / "chat_history.json"
    if ch_file.exists():
        with open(ch_file, 'r') as f:
            return json.load(f)
    return {"conversations": []}


def _save_chat_history(client_id: str, data: dict):
    """Save chat history."""
    ch_file = CLIENTS_DIR / client_id / "chat_history.json"
    with open(ch_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/me")
async def get_my_profile(client: dict = Depends(get_current_client)):
    """Get the authenticated client's profile."""
    from backend.auth import load_client_profile
    profile = load_client_profile(client["client_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@router.get("/dashboard")
async def get_dashboard(client: dict = Depends(get_current_client)):
    """
    Get client dashboard — aggregates gamification stats, this week's workouts,
    and recent achievements into a single response.
    """
    client_id = client["client_id"]

    # Load gamification state
    gam = _load_client_gamification(client_id)
    _reset_daily_quests_if_needed(gam)
    player = gam["player"]
    levels = gam["levels"]

    # XP progress calculation
    current_level = player["level"]
    xp_for_current = levels[current_level - 1]["xp_required"]
    xp_for_next = levels[min(current_level, len(levels) - 1)]["xp_required"]
    xp_progress = player["xp_total"] - xp_for_current
    xp_needed = max(xp_for_next - xp_for_current, 1)

    streak_mult = _get_streak_multiplier(player["current_streak"], gam["streak_multipliers"])

    # This week's workouts
    workouts = _load_client_workouts(client_id)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    current_week_assignments = []
    for assignment in workouts.get("assignments", []):
        assign_date = assignment.get("week_start")
        if assign_date:
            try:
                ad = date.fromisoformat(assign_date)
                if week_start <= ad <= week_end:
                    current_week_assignments.append(assignment)
            except (ValueError, TypeError):
                pass

    # Count completed workouts this week
    week_completed = 0
    week_total = 0
    for a in current_week_assignments:
        for day in a.get("days", []):
            week_total += 1
            if day.get("completed"):
                week_completed += 1

    # Recent achievements (last 5 unlocked)
    recent_achievements = [
        a for a in gam["achievements"] if a.get("unlocked")
    ][-5:]

    # Daily quests status
    quests = gam["daily_quests"]
    quests_completed = sum(1 for q in quests if q.get("completed"))

    _save_client_gamification(client_id, gam)

    return {
        "player": {
            "level": player["level"],
            "title": player["title"],
            "xp": player["xp_total"],
            "xp_to_next_level": max(xp_for_next - player["xp_total"], 0),
            "xp_progress_percent": min((xp_progress / xp_needed) * 100, 100),
            "coins": player["coins"],
            "current_streak": player["current_streak"],
            "best_streak": player["best_streak"],
            "streak_multiplier": streak_mult,
        },
        "this_week": {
            "assignments": current_week_assignments,
            "completed": week_completed,
            "total": week_total,
            "completion_percent": round((week_completed / max(week_total, 1)) * 100, 1),
        },
        "daily_quests": {
            "quests": quests,
            "completed": quests_completed,
            "total": len(quests),
            "all_complete": quests_completed == len(quests),
        },
        "recent_achievements": recent_achievements,
        "stats": gam.get("stats", {}),
    }


@router.get("/workouts")
async def get_all_workouts(client: dict = Depends(get_current_client)):
    """Get all workout assignments for this client."""
    workouts = _load_client_workouts(client["client_id"])
    return {
        "assignments": workouts.get("assignments", []),
        "stats": workouts.get("stats", {}),
    }


@router.get("/workouts/current-week")
async def get_current_week_workouts(client: dict = Depends(get_current_client)):
    """Get this week's workout assignments."""
    workouts = _load_client_workouts(client["client_id"])
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    current_week = []
    for assignment in workouts.get("assignments", []):
        assign_date = assignment.get("week_start")
        if assign_date:
            try:
                ad = date.fromisoformat(assign_date)
                if week_start <= ad <= week_end:
                    current_week.append(assignment)
            except (ValueError, TypeError):
                pass

    # If no assignments for this week, return the most recent one
    if not current_week and workouts.get("assignments"):
        current_week = [workouts["assignments"][-1]]

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "assignments": current_week,
    }


@router.post("/workouts/{workout_id}/complete")
async def complete_workout(
    workout_id: str,
    body: WorkoutCompleteRequest,
    client: dict = Depends(get_current_client),
):
    """
    Mark a workout day as completed. Awards XP via gamification.

    1. Find the workout assignment by ID
    2. Mark the specific day as completed
    3. Award XP (30 base) with streak multiplier
    4. Update gamification stats
    """
    client_id = client["client_id"]
    workouts = _load_client_workouts(client_id)

    # Find the assignment
    assignment = None
    for a in workouts.get("assignments", []):
        if a.get("id") == workout_id:
            assignment = a
            break

    if not assignment:
        raise HTTPException(status_code=404, detail="Workout assignment not found")

    # Mark the day as completed
    days = assignment.get("days", [])
    if body.day_index < 0 or body.day_index >= len(days):
        raise HTTPException(status_code=400, detail=f"Invalid day_index. Assignment has {len(days)} days.")

    day = days[body.day_index]
    if day.get("completed"):
        return {
            "success": False,
            "message": "This workout day is already marked as completed",
            "xp_earned": 0,
            "coins_earned": 0,
        }

    day["completed"] = True
    day["completed_at"] = datetime.utcnow().isoformat()
    if body.duration_minutes:
        day["duration_minutes"] = body.duration_minutes
    if body.notes:
        day["notes"] = body.notes

    # Update workout stats
    workouts["stats"]["total_completed"] = workouts["stats"].get("total_completed", 0) + 1
    _save_client_workouts(client_id, workouts)

    # --- Gamification: award XP ---
    gam = _load_client_gamification(client_id)
    player = gam["player"]

    # Update streak
    _update_streak(gam)

    multiplier = _get_streak_multiplier(player["current_streak"], gam["streak_multipliers"])
    base_xp = 30
    xp_earned = int(base_xp * multiplier)
    coins_earned = 10

    player["xp"] += xp_earned
    player["xp_total"] += xp_earned
    player["coins"] += coins_earned

    # Update stats
    gam["stats"]["workouts_completed"] = gam["stats"].get("workouts_completed", 0) + 1
    if body.duration_minutes:
        gam["stats"]["total_workout_minutes"] = gam["stats"].get("total_workout_minutes", 0) + body.duration_minutes

    # Mark the workout_completed daily quest as done
    _reset_daily_quests_if_needed(gam)
    for quest in gam["daily_quests"]:
        if quest["id"] == "workout_completed" and not quest["completed"]:
            quest["completed"] = True
            quest_xp = int(quest["xp"] * multiplier)
            player["xp"] += quest_xp
            player["xp_total"] += quest_xp
            player["coins"] += quest["coins"]
            xp_earned += quest_xp
            coins_earned += quest["coins"]
            break

    # Log the action
    action_id = str(uuid.uuid4())[:8]
    action_log = gam.setdefault("action_log", [])
    action_log.append({
        "id": action_id,
        "action": "workout_completed",
        "xp_gained": xp_earned,
        "coins_gained": coins_earned,
        "timestamp": datetime.now().isoformat(),
        "metadata": {"workout_id": workout_id, "day_index": body.day_index},
        "undone": False,
    })
    if len(action_log) > 50:
        gam["action_log"] = action_log[-50:]

    # Check achievements
    newly_unlocked = _check_client_achievements(gam)

    # Check level up
    leveled_up = _check_level_up(gam)

    _save_client_gamification(client_id, gam)

    return {
        "success": True,
        "message": f"Workout completed! +{xp_earned} XP, +{coins_earned} coins",
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "streak": player["current_streak"],
        "streak_multiplier": multiplier,
        "new_level": player["level"] if leveled_up else None,
        "new_title": player["title"] if leveled_up else None,
        "achievement_unlocked": newly_unlocked[0] if newly_unlocked else None,
    }


@router.post("/form-check")
async def submit_form_check(
    exercise_name: str = Form(...),
    notes: Optional[str] = Form(None),
    video: UploadFile = File(...),
    client: dict = Depends(get_current_client),
):
    """
    Submit a form check video for analysis.
    Accepts a video upload, stores it, and runs exercise detection if available.
    """
    client_id = client["client_id"]

    # Save the uploaded video
    file_ext = Path(video.filename).suffix if video.filename else ".mp4"
    video_id = str(uuid.uuid4())[:12]
    video_filename = f"{client_id}_{video_id}{file_ext}"
    video_path = UPLOADS_DIR / video_filename

    try:
        contents = await video.read()
        with open(video_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed to save form check video: {e}")
        raise HTTPException(status_code=500, detail="Failed to save video")

    # Try to run exercise recognition if available
    analysis_result = None
    try:
        from backend.exercise_recognition import ExerciseRecognizer
        recognizer = ExerciseRecognizer()
        analysis_result = await recognizer.analyze_video(str(video_path))
    except ImportError:
        logger.info("Exercise recognition not available (mediapipe not installed)")
    except Exception as e:
        logger.warning(f"Exercise recognition failed: {e}")

    # Build the form check record
    now = datetime.utcnow().isoformat()
    check_record = {
        "id": video_id,
        "exercise_name": exercise_name,
        "notes": notes,
        "video_filename": video_filename,
        "submitted_at": now,
        "status": "analyzed" if analysis_result else "pending_review",
        "analysis": analysis_result,
        "coach_feedback": None,
        "score": None,
    }

    # Save to form checks
    fc_data = _load_form_checks(client_id)
    fc_data["checks"].append(check_record)
    _save_form_checks(client_id, fc_data)

    # Award gamification XP for submitting a form check
    gam = _load_client_gamification(client_id)
    player = gam["player"]
    _update_streak(gam)
    multiplier = _get_streak_multiplier(player["current_streak"], gam["streak_multipliers"])

    # Find form_check power action XP
    form_check_xp = 25
    form_check_coins = 10
    for pa in gam.get("power_actions", []):
        if pa["id"] == "form_check":
            form_check_xp = pa["xp"]
            form_check_coins = pa["coins"]
            break

    xp_earned = int(form_check_xp * multiplier)
    player["xp"] += xp_earned
    player["xp_total"] += xp_earned
    player["coins"] += form_check_coins
    gam["stats"]["form_checks"] = gam["stats"].get("form_checks", 0) + 1

    # Log action
    action_id = str(uuid.uuid4())[:8]
    action_log = gam.setdefault("action_log", [])
    action_log.append({
        "id": action_id,
        "action": "form_check",
        "xp_gained": xp_earned,
        "coins_gained": form_check_coins,
        "timestamp": datetime.now().isoformat(),
        "metadata": {"check_id": video_id, "exercise": exercise_name},
        "undone": False,
    })
    if len(action_log) > 50:
        gam["action_log"] = action_log[-50:]

    newly_unlocked = _check_client_achievements(gam)
    _check_level_up(gam)
    _save_client_gamification(client_id, gam)

    return {
        "success": True,
        "check_id": video_id,
        "status": check_record["status"],
        "analysis": analysis_result,
        "xp_earned": xp_earned,
        "coins_earned": form_check_coins,
        "achievement_unlocked": newly_unlocked[0] if newly_unlocked else None,
        "message": "Form check submitted! Your coach will review it shortly.",
    }


@router.get("/form-check/history")
async def get_form_check_history(client: dict = Depends(get_current_client)):
    """Get all past form check submissions and results."""
    fc_data = _load_form_checks(client["client_id"])
    checks = fc_data.get("checks", [])
    # Return newest first
    checks_sorted = sorted(checks, key=lambda x: x.get("submitted_at", ""), reverse=True)
    return {
        "checks": checks_sorted,
        "total": len(checks_sorted),
    }


@router.post("/chat")
async def client_chat(
    body: ChatMessage,
    client: dict = Depends(get_current_client),
):
    """
    AI coaching chat. Builds a system prompt with client context
    (profile, goals, current program, recent workouts) and uses
    the Anthropic SDK to generate a coaching response.

    Falls back to a simple acknowledgement if the API key is not configured.
    """
    client_id = client["client_id"]

    # Load client context
    from backend.auth import load_client_profile
    profile = load_client_profile(client_id) or {}
    workouts = _load_client_workouts(client_id)
    gam = _load_client_gamification(client_id)

    # Build context string
    client_name = profile.get("name", "Client")
    goals = profile.get("goals", "Not specified")
    program = profile.get("program", "No program assigned")
    level = gam["player"].get("level", 1)
    title = gam["player"].get("title", "New Member")
    streak = gam["player"].get("current_streak", 0)
    recent_workouts = workouts.get("assignments", [])[-3:]  # Last 3 assignments

    workout_summary = ""
    for a in recent_workouts:
        completed_days = sum(1 for d in a.get("days", []) if d.get("completed"))
        total_days = len(a.get("days", []))
        workout_summary += f"  - {a.get('template_name', 'Workout')}: {completed_days}/{total_days} days completed\n"

    system_prompt = f"""You are a supportive, evidence-based fitness coach for Marceau Solutions.
You are chatting with {client_name}.

Client Profile:
- Goals: {goals}
- Current Program: {program}
- Level: {level} ({title})
- Current Streak: {streak} days

Recent Workouts:
{workout_summary if workout_summary else "  No recent workouts yet."}

Guidelines:
- Be encouraging but honest. Celebrate wins, address missed workouts gently.
- Give evidence-based advice. Reference their specific program when relevant.
- Keep responses concise (2-4 paragraphs max for most questions).
- If they ask about peptides, mention that Marceau Solutions specializes in peptide-informed protocols.
- Never diagnose or prescribe. Suggest they consult a healthcare provider for medical questions.
- Context: {body.context or 'general conversation'}"""

    # Try Anthropic SDK
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No ANTHROPIC_API_KEY")

        anthropic_client = anthropic.Anthropic(api_key=api_key)
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": body.message}],
        )
        ai_reply = response.content[0].text
    except Exception as e:
        logger.warning(f"AI chat fallback (Anthropic unavailable): {e}")
        ai_reply = (
            f"Thanks for your message, {client_name}! I've noted your question. "
            f"Your coach will follow up with a detailed response soon. "
            f"In the meantime, keep up your {streak}-day streak!"
        )

    # Save to chat history
    chat_data = _load_chat_history(client_id)
    now = datetime.utcnow().isoformat()
    chat_data["conversations"].append({
        "id": str(uuid.uuid4())[:8],
        "timestamp": now,
        "context": body.context,
        "user_message": body.message,
        "ai_response": ai_reply,
    })
    # Keep last 100 conversations
    if len(chat_data["conversations"]) > 100:
        chat_data["conversations"] = chat_data["conversations"][-100:]
    _save_chat_history(client_id, chat_data)

    return {
        "reply": ai_reply,
        "context": body.context,
        "timestamp": now,
    }


@router.get("/progress")
async def get_progress(client: dict = Depends(get_current_client)):
    """
    Get full progress report — gamification state, achievements, stats,
    streak history, and workout completion data.
    """
    client_id = client["client_id"]

    # Load gamification
    gam = _load_client_gamification(client_id)
    player = gam["player"]
    levels = gam["levels"]

    # XP progress
    current_level = player["level"]
    xp_for_current = levels[current_level - 1]["xp_required"]
    xp_for_next = levels[min(current_level, len(levels) - 1)]["xp_required"]
    xp_progress = player["xp_total"] - xp_for_current
    xp_needed = max(xp_for_next - xp_for_current, 1)

    # Load workouts for completion history
    workouts = _load_client_workouts(client_id)

    # Build workout history summary
    workout_history = []
    for a in workouts.get("assignments", []):
        completed_days = sum(1 for d in a.get("days", []) if d.get("completed"))
        total_days = len(a.get("days", []))
        workout_history.append({
            "id": a.get("id"),
            "template_name": a.get("template_name", "Workout"),
            "week_start": a.get("week_start"),
            "completed": completed_days,
            "total": total_days,
            "completion_percent": round((completed_days / max(total_days, 1)) * 100, 1),
        })

    # Form check summary
    fc_data = _load_form_checks(client_id)
    form_checks = fc_data.get("checks", [])

    return {
        "player": {
            "level": player["level"],
            "title": player["title"],
            "xp": player["xp_total"],
            "xp_to_next_level": max(xp_for_next - player["xp_total"], 0),
            "xp_progress_percent": min((xp_progress / xp_needed) * 100, 100),
            "coins": player["coins"],
            "current_streak": player["current_streak"],
            "best_streak": player["best_streak"],
            "streak_multiplier": _get_streak_multiplier(player["current_streak"], gam["streak_multipliers"]),
        },
        "achievements": gam["achievements"],
        "stats": gam.get("stats", {}),
        "rewards": [
            {**r, "can_afford": player["coins"] >= r["cost"]}
            for r in gam.get("rewards", [])
        ],
        "workout_history": workout_history,
        "form_checks_total": len(form_checks),
        "recent_actions": gam.get("action_log", [])[-10:],
    }
