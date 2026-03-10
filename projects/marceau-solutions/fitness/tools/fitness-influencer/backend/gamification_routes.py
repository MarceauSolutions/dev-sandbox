#!/usr/bin/env python3
"""
Gamification API Routes — Marceau Solutions Business Growth Tracker

Endpoints for the PT coaching business gamification system:
- Player stats (XP, level, coins, streaks)
- Daily quests tracking (Propane tasks, content, outreach)
- Achievements (business milestones)
- Rewards shop (self-rewards for hitting goals)
- Action logging (leads, calls, clients)

Data Source: JSON file (can be synced from EC2 or stored locally)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pathlib import Path
import json
import os
import uuid

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

# Data storage path
DATA_DIR = Path(__file__).parent.parent / "data" / "gamification"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default player state — Marceau Solutions PT Coaching Business
DEFAULT_PLAYER_STATE = {
    "player": {
        "level": 1,
        "xp": 0,
        "xp_total": 0,
        "coins": 0,
        "title": "Getting Started",
        "current_streak": 0,
        "best_streak": 0,
        "last_active_date": None
    },
    "levels": [
        {"level": 1, "title": "Getting Started", "xp_required": 0},
        {"level": 2, "title": "Foundation Builder", "xp_required": 100},
        {"level": 3, "title": "Content Creator", "xp_required": 300},
        {"level": 4, "title": "Niche Expert", "xp_required": 600},
        {"level": 5, "title": "Lead Magnet", "xp_required": 1000},
        {"level": 6, "title": "Conversion Machine", "xp_required": 1500},
        {"level": 7, "title": "Client Crusher", "xp_required": 2500},
        {"level": 8, "title": "Revenue Generator", "xp_required": 4000},
        {"level": 9, "title": "Scaling Pro", "xp_required": 6000},
        {"level": 10, "title": "Fitness Empire", "xp_required": 10000}
    ],
    "daily_quests": [
        {"id": "propane_task", "name": "Complete Propane task", "xp": 20, "coins": 8, "completed": False},
        {"id": "content_created", "name": "Create content piece", "xp": 15, "coins": 5, "completed": False},
        {"id": "community_engage", "name": "Engage with community", "xp": 10, "coins": 3, "completed": False},
        {"id": "outreach", "name": "Outreach/networking", "xp": 15, "coins": 5, "completed": False},
        {"id": "analytics_review", "name": "Review analytics/metrics", "xp": 10, "coins": 3, "completed": False}
    ],
    "power_actions": [
        {"id": "lead_generated", "name": "Lead generated", "xp": 50, "coins": 20},
        {"id": "call_booked", "name": "Strategy call booked", "xp": 100, "coins": 50},
        {"id": "client_signed", "name": "Client signed ($197/mo)", "xp": 500, "coins": 200},
        {"id": "first_payment", "name": "First payment received", "xp": 1000, "coins": 500},
        {"id": "ad_creative", "name": "Ad creative completed", "xp": 75, "coins": 30},
        {"id": "funnel_step", "name": "Funnel step built", "xp": 75, "coins": 30}
    ],
    "achievements": [
        {"id": "first_steps", "name": "First Steps", "description": "Completed first Propane task", "xp_bonus": 50, "unlocked": False},
        {"id": "week_warrior", "name": "Week Warrior", "description": "7-day streak", "xp_bonus": 100, "unlocked": False},
        {"id": "content_machine", "name": "Content Machine", "description": "Created 10 content pieces", "xp_bonus": 150, "unlocked": False},
        {"id": "iron_will", "name": "Iron Will", "description": "30-day streak", "xp_bonus": 500, "unlocked": False},
        {"id": "first_lead", "name": "First Lead", "description": "Generated first lead", "xp_bonus": 200, "unlocked": False},
        {"id": "closer", "name": "Closer", "description": "Signed first client", "xp_bonus": 500, "unlocked": False},
        {"id": "5k_club", "name": "5K Club", "description": "Hit $5K monthly revenue", "xp_bonus": 1000, "unlocked": False},
        {"id": "ad_master", "name": "Ad Master", "description": "Completed 6 ad creatives", "xp_bonus": 200, "unlocked": False},
        {"id": "funnel_builder", "name": "Funnel Builder", "description": "Built complete sales funnel (6 steps)", "xp_bonus": 300, "unlocked": False},
        {"id": "halfway_there", "name": "Halfway There", "description": "Reached Level 5", "xp_bonus": 200, "unlocked": False},
        {"id": "empire_builder", "name": "Empire Builder", "description": "Reached Level 10", "xp_bonus": 1000, "unlocked": False}
    ],
    "rewards": [
        {"id": "coffee_break", "name": "Coffee Break", "description": "Take 30 min off guilt-free", "cost": 50, "icon": "coffee"},
        {"id": "nice_meal", "name": "Nice Meal Out", "description": "Treat yourself to a good restaurant", "cost": 100, "icon": "meal"},
        {"id": "game_session", "name": "Game Session", "description": "2 hours of gaming, no guilt", "cost": 200, "icon": "game"},
        {"id": "new_gear", "name": "New Gear", "description": "Buy something for the gym", "cost": 300, "icon": "gear"},
        {"id": "day_trip", "name": "Day Trip", "description": "Take a full day off to explore", "cost": 500, "icon": "trip"},
        {"id": "major_purchase", "name": "Major Purchase", "description": "That thing you've been eyeing", "cost": 1000, "icon": "gift"}
    ],
    "streak_multipliers": [
        {"days": 3, "multiplier": 1.25},
        {"days": 7, "multiplier": 1.5},
        {"days": 14, "multiplier": 2.0},
        {"days": 30, "multiplier": 3.0}
    ],
    "stats": {
        "total_content": 0,
        "total_outreach": 0,
        "total_leads": 0,
        "calls_booked": 0,
        "total_clients": 0,
        "total_revenue": 0,
        "ad_creatives": 0,
        "funnel_steps": 0,
        "propane_tasks": 0,
        "community_engagements": 0,
        "analytics_reviews": 0,
        "quests_completed": 0,
        "rewards_purchased": []
    },
    "action_log": [],
    "last_quest_reset": None
}


def get_player_file(tenant_id: str = "wmarceau") -> Path:
    """Get the player file path for a tenant."""
    return DATA_DIR / f"{tenant_id}_player.json"


def load_player_state(tenant_id: str = "wmarceau") -> dict:
    """Load player state from file or create default."""
    player_file = get_player_file(tenant_id)
    if player_file.exists():
        with open(player_file, 'r') as f:
            state = json.load(f)
        # Migrate: ensure all new stats fields exist
        default_stats = DEFAULT_PLAYER_STATE["stats"].copy()
        for key, val in default_stats.items():
            if key not in state.get("stats", {}):
                state.setdefault("stats", {})[key] = val
        # Migrate: ensure all new keys exist in state
        for key in DEFAULT_PLAYER_STATE:
            if key not in state:
                state[key] = DEFAULT_PLAYER_STATE[key]
        # Migrate: ensure action_log exists
        if "action_log" not in state:
            state["action_log"] = []
        return state
    # Create default state
    import copy
    state = copy.deepcopy(DEFAULT_PLAYER_STATE)
    save_player_state(state, tenant_id)
    return state


def save_player_state(state: dict, tenant_id: str = "wmarceau"):
    """Save player state to file."""
    player_file = get_player_file(tenant_id)
    with open(player_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def get_streak_multiplier(streak: int, multipliers: list) -> float:
    """Get the XP multiplier based on current streak."""
    current_mult = 1.0
    for m in multipliers:
        if streak >= m["days"]:
            current_mult = m["multiplier"]
    return current_mult


def check_level_up(state: dict) -> bool:
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
    if leveled_up:
        if player["level"] >= 5:
            for a in state["achievements"]:
                if a["id"] == "halfway_there" and not a["unlocked"]:
                    a["unlocked"] = True
                    player["xp"] += a["xp_bonus"]
                    player["xp_total"] += a["xp_bonus"]
        if player["level"] >= 10:
            for a in state["achievements"]:
                if a["id"] == "empire_builder" and not a["unlocked"]:
                    a["unlocked"] = True
                    player["xp"] += a["xp_bonus"]
                    player["xp_total"] += a["xp_bonus"]

    return leveled_up


def reset_daily_quests_if_needed(state: dict):
    """Reset daily quests if it's a new day."""
    today = date.today().isoformat()
    if state.get("last_quest_reset") != today:
        for quest in state["daily_quests"]:
            quest["completed"] = False
        state["last_quest_reset"] = today


def check_stat_achievements(state: dict) -> list:
    """Check for stat-based achievements and return list of newly unlocked names."""
    player = state["player"]
    stats = state["stats"]
    unlocked = []

    # First Steps — completed first Propane task
    if stats.get("propane_tasks", 0) >= 1:
        for a in state["achievements"]:
            if a["id"] == "first_steps" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Content Machine — created 10 content pieces
    if stats.get("total_content", 0) >= 10:
        for a in state["achievements"]:
            if a["id"] == "content_machine" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # First Lead — generated first lead
    if stats.get("total_leads", 0) >= 1:
        for a in state["achievements"]:
            if a["id"] == "first_lead" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Closer — signed first client
    if stats.get("total_clients", 0) >= 1:
        for a in state["achievements"]:
            if a["id"] == "closer" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Ad Master — completed 6 ad creatives
    if stats.get("ad_creatives", 0) >= 6:
        for a in state["achievements"]:
            if a["id"] == "ad_master" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    # Funnel Builder — built 6 funnel steps
    if stats.get("funnel_steps", 0) >= 6:
        for a in state["achievements"]:
            if a["id"] == "funnel_builder" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                unlocked.append(a["name"])

    return unlocked


# ============================================================================
# Pydantic Models
# ============================================================================

class PlayerStatsResponse(BaseModel):
    level: int
    title: str
    xp: int
    xp_to_next_level: int
    xp_progress_percent: float
    coins: int
    current_streak: int
    best_streak: int
    streak_multiplier: float
    stats: Optional[Dict[str, Any]] = None


class QuestStatus(BaseModel):
    id: str
    name: str
    xp: int
    coins: int
    completed: bool


class DailyQuestsResponse(BaseModel):
    quests: List[QuestStatus]
    all_complete: bool
    bonus_available: bool


class AchievementStatus(BaseModel):
    id: str
    name: str
    description: str
    xp_bonus: int
    unlocked: bool


class RewardItem(BaseModel):
    id: str
    name: str
    description: str
    cost: int
    can_afford: bool


class LogActionRequest(BaseModel):
    action: str  # quest id or power action id
    tenant_id: Optional[str] = "wmarceau"
    metadata: Optional[Dict[str, Any]] = None


class PurchaseRewardRequest(BaseModel):
    reward_id: str
    tenant_id: Optional[str] = "wmarceau"


class UndoRequest(BaseModel):
    action_id: str
    tenant_id: str = "wmarceau"


class ActionResponse(BaseModel):
    success: bool
    message: str
    xp_gained: int
    coins_gained: int
    new_level: Optional[int] = None
    new_title: Optional[str] = None
    achievement_unlocked: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/player/stats")
async def get_player_stats(tenant_id: str = "wmarceau"):
    """Get current player statistics."""
    state = load_player_state(tenant_id)
    player = state["player"]
    levels = state["levels"]

    # Calculate XP to next level
    current_level = player["level"]
    xp_for_current = levels[current_level - 1]["xp_required"]
    xp_for_next = levels[min(current_level, len(levels) - 1)]["xp_required"]

    xp_progress = player["xp_total"] - xp_for_current
    xp_needed = max(xp_for_next - xp_for_current, 1)

    return {
        "level": player["level"],
        "title": player["title"],
        "xp": player["xp_total"],
        "xp_to_next_level": max(xp_for_next - player["xp_total"], 0),
        "xp_progress_percent": min((xp_progress / xp_needed) * 100, 100),
        "coins": player["coins"],
        "current_streak": player["current_streak"],
        "best_streak": player["best_streak"],
        "streak_multiplier": get_streak_multiplier(player["current_streak"], state["streak_multipliers"]),
        "stats": state.get("stats", {})
    }


@router.get("/quests/daily")
async def get_daily_quests(tenant_id: str = "wmarceau"):
    """Get today's daily quests and their status."""
    state = load_player_state(tenant_id)
    reset_daily_quests_if_needed(state)
    save_player_state(state, tenant_id)

    quests = state["daily_quests"]
    all_complete = all(q["completed"] for q in quests)

    return {
        "quests": quests,
        "all_complete": all_complete,
        "bonus_available": all_complete
    }


@router.post("/quests/{quest_id}/complete")
async def complete_quest(quest_id: str, tenant_id: str = "wmarceau"):
    """Mark a daily quest as complete."""
    state = load_player_state(tenant_id)
    reset_daily_quests_if_needed(state)

    quest = None
    for q in state["daily_quests"]:
        if q["id"] == quest_id:
            quest = q
            break

    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    if quest["completed"]:
        return ActionResponse(
            success=False,
            message="Quest already completed today",
            xp_gained=0,
            coins_gained=0
        )

    # Complete the quest
    quest["completed"] = True
    player = state["player"]
    multiplier = get_streak_multiplier(player["current_streak"], state["streak_multipliers"])

    xp_gained = int(quest["xp"] * multiplier)
    coins_gained = quest["coins"]

    player["xp"] += xp_gained
    player["xp_total"] += xp_gained
    player["coins"] += coins_gained
    state["stats"]["quests_completed"] += 1

    # Update stat counters based on quest type
    _update_stat_for_action(state, quest_id)

    # Check for all quests complete bonus
    if all(q["completed"] for q in state["daily_quests"]):
        bonus_xp = int(50 * multiplier)
        player["xp"] += bonus_xp
        player["xp_total"] += bonus_xp
        xp_gained += bonus_xp

    # Generate action_id and append to action_log
    action_id = str(uuid.uuid4())[:8]
    action_log = state.setdefault("action_log", [])
    action_log.append({
        "id": action_id,
        "action": quest_id,
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "timestamp": datetime.now().isoformat(),
        "undone": False
    })
    # Keep only last 50 entries
    if len(action_log) > 50:
        state["action_log"] = action_log[-50:]

    # Check stat-based achievements
    newly_unlocked = check_stat_achievements(state)
    for name in newly_unlocked:
        # XP already added inside check_stat_achievements
        pass

    # Check level up
    leveled_up = check_level_up(state)

    save_player_state(state, tenant_id)

    return {
        "success": True,
        "message": f"Quest completed! +{xp_gained} XP, +{coins_gained} coins",
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "action_id": action_id,
        "new_level": player["level"] if leveled_up else None,
        "new_title": player["title"] if leveled_up else None,
        "achievement_unlocked": newly_unlocked[0] if newly_unlocked else None
    }


@router.post("/player/action")
async def log_power_action(request: LogActionRequest):
    """Log a power action or quick action (lead gen, call booked, client signed, etc.)."""
    state = load_player_state(request.tenant_id)

    # Handle task_completed with xp_override from metadata
    if request.action == "task_completed" and request.metadata and "xp_override" in request.metadata:
        xp_override = int(request.metadata["xp_override"])
        action = {"id": "task_completed", "name": "Task Completed", "xp": xp_override, "coins": xp_override // 3}
    else:
        # Check power actions first
        action = None
        for a in state["power_actions"]:
            if a["id"] == request.action:
                action = a
                break

        # Also allow logging daily quest actions via this endpoint
        if not action:
            for q in state["daily_quests"]:
                if q["id"] == request.action:
                    action = {"id": q["id"], "name": q["name"], "xp": q["xp"], "coins": q["coins"]}
                    break

        if not action:
            raise HTTPException(status_code=404, detail=f"Action '{request.action}' not found")

    player = state["player"]
    multiplier = get_streak_multiplier(player["current_streak"], state["streak_multipliers"])

    xp_gained = int(action["xp"] * multiplier)
    coins_gained = action["coins"]

    player["xp"] += xp_gained
    player["xp_total"] += xp_gained
    player["coins"] += coins_gained

    # Update stats based on action type
    _update_stat_for_action(state, request.action)

    # Generate action_id and append to action_log
    action_id = str(uuid.uuid4())[:8]
    action_log = state.setdefault("action_log", [])
    action_log.append({
        "id": action_id,
        "action": request.action,
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "timestamp": datetime.now().isoformat(),
        "undone": False
    })
    # Keep only last 50 entries
    if len(action_log) > 50:
        state["action_log"] = action_log[-50:]

    # Check stat-based achievements
    newly_unlocked = check_stat_achievements(state)

    # Check level up
    leveled_up = check_level_up(state)

    save_player_state(state, request.tenant_id)

    return {
        "success": True,
        "message": f"{action['name']}! +{xp_gained} XP, +{coins_gained} coins",
        "xp_gained": xp_gained,
        "coins_gained": coins_gained,
        "action_id": action_id,
        "new_level": player["level"] if leveled_up else None,
        "new_title": player["title"] if leveled_up else None,
        "achievement_unlocked": newly_unlocked[0] if newly_unlocked else None
    }


def _update_stat_for_action(state: dict, action_id: str):
    """Update the appropriate stat counter for a given action."""
    stats = state["stats"]
    stat_map = {
        "propane_task": "propane_tasks",
        "content_created": "total_content",
        "community_engage": "community_engagements",
        "outreach": "total_outreach",
        "analytics_review": "analytics_reviews",
        "lead_generated": "total_leads",
        "call_booked": "calls_booked",
        "client_signed": "total_clients",
        "ad_creative": "ad_creatives",
        "funnel_step": "funnel_steps",
    }
    stat_key = stat_map.get(action_id)
    if stat_key and stat_key in stats:
        stats[stat_key] += 1


def _reverse_stat_for_action(state: dict, action_id: str):
    """Reverse the stat counter for a given action (undo). Floor at 0."""
    stats = state["stats"]
    stat_map = {
        "propane_task": "propane_tasks",
        "content_created": "total_content",
        "community_engage": "community_engagements",
        "outreach": "total_outreach",
        "analytics_review": "analytics_reviews",
        "lead_generated": "total_leads",
        "call_booked": "calls_booked",
        "client_signed": "total_clients",
        "ad_creative": "ad_creatives",
        "funnel_step": "funnel_steps",
    }
    stat_key = stat_map.get(action_id)
    if stat_key and stat_key in stats:
        stats[stat_key] = max(0, stats[stat_key] - 1)


@router.get("/achievements")
async def get_achievements(tenant_id: str = "wmarceau"):
    """Get all achievements and their status."""
    state = load_player_state(tenant_id)
    return [AchievementStatus(**a) for a in state["achievements"]]


@router.get("/rewards")
async def get_rewards(tenant_id: str = "wmarceau"):
    """Get available rewards."""
    state = load_player_state(tenant_id)
    coins = state["player"]["coins"]

    return [
        RewardItem(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            cost=r["cost"],
            can_afford=coins >= r["cost"]
        )
        for r in state["rewards"]
    ]


@router.post("/rewards/purchase")
async def purchase_reward(request: PurchaseRewardRequest):
    """Purchase a reward with coins."""
    state = load_player_state(request.tenant_id)

    reward = None
    for r in state["rewards"]:
        if r["id"] == request.reward_id:
            reward = r
            break

    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    player = state["player"]
    if player["coins"] < reward["cost"]:
        return ActionResponse(
            success=False,
            message=f"Not enough coins. Need {reward['cost']}, have {player['coins']}",
            xp_gained=0,
            coins_gained=0
        )

    # Purchase reward
    player["coins"] -= reward["cost"]
    state["stats"]["rewards_purchased"].append({
        "reward_id": request.reward_id,
        "purchased_at": datetime.now().isoformat()
    })

    save_player_state(state, request.tenant_id)

    return ActionResponse(
        success=True,
        message=f"Purchased {reward['name']}! Enjoy your reward!",
        xp_gained=0,
        coins_gained=-reward["cost"]
    )


@router.get("/stats/summary")
async def get_stats_summary(tenant_id: str = "wmarceau"):
    """Get overall statistics summary."""
    state = load_player_state(tenant_id)
    return {
        "player": state["player"],
        "stats": state["stats"],
        "current_streak_multiplier": get_streak_multiplier(
            state["player"]["current_streak"],
            state["streak_multipliers"]
        )
    }


@router.post("/player/update-streak")
async def update_streak(tenant_id: str = "wmarceau"):
    """Update streak (call daily when user is active)."""
    state = load_player_state(tenant_id)
    player = state["player"]

    today = date.today().isoformat()
    last_active = player.get("last_active_date")

    if last_active == today:
        return {"message": "Already active today", "streak": player["current_streak"]}

    if last_active:
        from datetime import timedelta
        last_date = date.fromisoformat(last_active)
        if (date.today() - last_date).days == 1:
            # Consecutive day - increment streak
            player["current_streak"] += 1
            player["best_streak"] = max(player["best_streak"], player["current_streak"])
        elif (date.today() - last_date).days > 1:
            # Streak broken
            player["current_streak"] = 1
    else:
        # First activity
        player["current_streak"] = 1

    player["last_active_date"] = today

    # Check for streak achievements
    if player["current_streak"] >= 7:
        for a in state["achievements"]:
            if a["id"] == "week_warrior" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]

    if player["current_streak"] >= 30:
        for a in state["achievements"]:
            if a["id"] == "iron_will" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]

    check_level_up(state)
    save_player_state(state, tenant_id)

    return {
        "message": "Streak updated",
        "streak": player["current_streak"],
        "multiplier": get_streak_multiplier(player["current_streak"], state["streak_multipliers"])
    }


@router.post("/player/undo")
async def undo_action(request: UndoRequest):
    """Undo a recent action within the 5-minute window."""
    state = load_player_state(request.tenant_id)
    action_log = state.get("action_log", [])

    # Find the action by ID
    entry = None
    for item in action_log:
        if item["id"] == request.action_id:
            entry = item
            break

    if not entry:
        raise HTTPException(status_code=404, detail="Action not found")

    if entry.get("undone"):
        raise HTTPException(status_code=400, detail="Already undone")

    # Check 5-minute undo window
    action_time = datetime.fromisoformat(entry["timestamp"])
    elapsed = (datetime.now() - action_time).total_seconds()
    if elapsed > 300:
        raise HTTPException(status_code=400, detail="Undo window expired")

    player = state["player"]
    xp_gained = entry["xp_gained"]
    coins_gained = entry["coins_gained"]

    # Subtract XP and coins (floor at 0)
    player["xp"] = max(0, player["xp"] - xp_gained)
    player["xp_total"] = max(0, player["xp_total"] - xp_gained)
    player["coins"] = max(0, player["coins"] - coins_gained)

    # Reverse the stat increment
    _reverse_stat_for_action(state, entry["action"])

    # Mark as undone
    entry["undone"] = True

    # Check if level should decrease after XP removal
    levels = state["levels"]
    for level_info in reversed(levels):
        if player["xp_total"] >= level_info["xp_required"]:
            if player["level"] != level_info["level"]:
                player["level"] = level_info["level"]
                player["title"] = level_info["title"]
            break

    save_player_state(state, request.tenant_id)

    return {
        "success": True,
        "xp_removed": xp_gained,
        "coins_removed": coins_gained
    }
