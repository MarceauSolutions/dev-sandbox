#!/usr/bin/env python3
"""
Gamification API Routes

Endpoints for the personal trainer gamification system:
- Player stats (XP, level, coins, streaks)
- Daily quests tracking
- Achievements
- Rewards shop
- Action logging

Data Source: JSON file (can be synced from EC2 or stored locally)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pathlib import Path
import json
import os

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

# Data storage path
DATA_DIR = Path(__file__).parent.parent / "data" / "gamification"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default player state (matches Clawdbot's structure)
DEFAULT_PLAYER_STATE = {
    "player": {
        "level": 1,
        "xp": 0,
        "xp_total": 0,
        "coins": 0,
        "title": "Aspiring Coach",
        "current_streak": 0,
        "best_streak": 0,
        "last_active_date": None
    },
    "levels": [
        {"level": 1, "title": "Aspiring Coach", "xp_required": 0},
        {"level": 2, "title": "Rising Star", "xp_required": 100},
        {"level": 3, "title": "Content Creator", "xp_required": 300},
        {"level": 4, "title": "Community Builder", "xp_required": 600},
        {"level": 5, "title": "Client Magnet", "xp_required": 1000},
        {"level": 6, "title": "Revenue Generator", "xp_required": 1500},
        {"level": 7, "title": "Brand Ambassador", "xp_required": 2500},
        {"level": 8, "title": "Industry Expert", "xp_required": 4000},
        {"level": 9, "title": "Thought Leader", "xp_required": 6000},
        {"level": 10, "title": "Fitness Empire", "xp_required": 10000}
    ],
    "daily_quests": [
        {"id": "post_content", "name": "Post content", "xp": 15, "coins": 5, "completed": False},
        {"id": "respond_comments", "name": "Respond to comments", "xp": 10, "coins": 3, "completed": False},
        {"id": "check_dms", "name": "Check and reply to DMs", "xp": 10, "coins": 3, "completed": False},
        {"id": "engage_posts", "name": "Engage with 5 posts", "xp": 10, "coins": 3, "completed": False},
        {"id": "post_story", "name": "Post a Story", "xp": 15, "coins": 5, "completed": False}
    ],
    "power_actions": [
        {"id": "consultation_booked", "name": "Consultation booked", "xp": 100, "coins": 50},
        {"id": "client_signed", "name": "Client signed", "xp": 500, "coins": 200},
        {"id": "first_payment", "name": "First payment received", "xp": 1000, "coins": 500}
    ],
    "achievements": [
        {"id": "first_post", "name": "First Steps", "description": "Made your first post", "xp_bonus": 50, "unlocked": False},
        {"id": "week_streak", "name": "Week Warrior", "description": "7-day streak", "xp_bonus": 100, "unlocked": False},
        {"id": "month_streak", "name": "Iron Will", "description": "30-day streak", "xp_bonus": 500, "unlocked": False},
        {"id": "first_client", "name": "Client Crusher", "description": "Signed first client", "xp_bonus": 250, "unlocked": False},
        {"id": "5k_goal", "name": "5K Goal", "description": "Reached $5,000 revenue", "xp_bonus": 500, "unlocked": False},
        {"id": "level_5", "name": "Halfway There", "description": "Reached Level 5", "xp_bonus": 200, "unlocked": False},
        {"id": "level_10", "name": "Empire Builder", "description": "Reached Level 10", "xp_bonus": 1000, "unlocked": False}
    ],
    "rewards": [
        {"id": "coffee_break", "name": "Coffee Break", "description": "Take 15 min guilt-free break", "cost": 50},
        {"id": "cheat_meal", "name": "Cheat Meal", "description": "Enjoy a cheat meal", "cost": 100},
        {"id": "game_time", "name": "Game Time", "description": "1 hour of gaming", "cost": 200},
        {"id": "movie_night", "name": "Movie Night", "description": "Watch a movie guilt-free", "cost": 300},
        {"id": "spa_day", "name": "Spa Treatment", "description": "Get a massage/spa treatment", "cost": 500},
        {"id": "day_off", "name": "Day Off", "description": "Take a full day off", "cost": 1000}
    ],
    "streak_multipliers": [
        {"days": 3, "multiplier": 1.25},
        {"days": 7, "multiplier": 1.5},
        {"days": 14, "multiplier": 2.0},
        {"days": 30, "multiplier": 3.0}
    ],
    "stats": {
        "total_posts": 0,
        "total_comments": 0,
        "total_dms": 0,
        "consultations_booked": 0,
        "clients_signed": 0,
        "total_revenue": 0,
        "quests_completed": 0,
        "rewards_purchased": []
    },
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
            return json.load(f)
    # Create default state
    state = DEFAULT_PLAYER_STATE.copy()
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

    for level_info in reversed(levels):
        if player["xp_total"] >= level_info["xp_required"] and player["level"] < level_info["level"]:
            player["level"] = level_info["level"]
            player["title"] = level_info["title"]
            return True
    return False


def reset_daily_quests_if_needed(state: dict):
    """Reset daily quests if it's a new day."""
    today = date.today().isoformat()
    if state.get("last_quest_reset") != today:
        for quest in state["daily_quests"]:
            quest["completed"] = False
        state["last_quest_reset"] = today


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


class PurchaseRewardRequest(BaseModel):
    reward_id: str
    tenant_id: Optional[str] = "wmarceau"


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

@router.get("/player/stats", response_model=PlayerStatsResponse)
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

    return PlayerStatsResponse(
        level=player["level"],
        title=player["title"],
        xp=player["xp_total"],
        xp_to_next_level=xp_for_next - player["xp_total"],
        xp_progress_percent=min((xp_progress / xp_needed) * 100, 100),
        coins=player["coins"],
        current_streak=player["current_streak"],
        best_streak=player["best_streak"],
        streak_multiplier=get_streak_multiplier(player["current_streak"], state["streak_multipliers"])
    )


@router.get("/quests/daily", response_model=DailyQuestsResponse)
async def get_daily_quests(tenant_id: str = "wmarceau"):
    """Get today's daily quests and their status."""
    state = load_player_state(tenant_id)
    reset_daily_quests_if_needed(state)
    save_player_state(state, tenant_id)

    quests = [QuestStatus(**q) for q in state["daily_quests"]]
    all_complete = all(q.completed for q in quests)

    return DailyQuestsResponse(
        quests=quests,
        all_complete=all_complete,
        bonus_available=all_complete
    )


@router.post("/quests/{quest_id}/complete", response_model=ActionResponse)
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

    # Check for all quests complete bonus
    if all(q["completed"] for q in state["daily_quests"]):
        bonus_xp = int(50 * multiplier)
        player["xp"] += bonus_xp
        player["xp_total"] += bonus_xp
        xp_gained += bonus_xp

    # Check level up
    leveled_up = check_level_up(state)

    save_player_state(state, tenant_id)

    return ActionResponse(
        success=True,
        message=f"Quest completed! +{xp_gained} XP, +{coins_gained} coins",
        xp_gained=xp_gained,
        coins_gained=coins_gained,
        new_level=player["level"] if leveled_up else None,
        new_title=player["title"] if leveled_up else None
    )


@router.post("/player/action", response_model=ActionResponse)
async def log_power_action(request: LogActionRequest):
    """Log a power action (consultation, client signed, etc.)."""
    state = load_player_state(request.tenant_id)

    action = None
    for a in state["power_actions"]:
        if a["id"] == request.action:
            action = a
            break

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    player = state["player"]
    multiplier = get_streak_multiplier(player["current_streak"], state["streak_multipliers"])

    xp_gained = int(action["xp"] * multiplier)
    coins_gained = action["coins"]

    player["xp"] += xp_gained
    player["xp_total"] += xp_gained
    player["coins"] += coins_gained

    # Update stats
    if request.action == "consultation_booked":
        state["stats"]["consultations_booked"] += 1
    elif request.action == "client_signed":
        state["stats"]["clients_signed"] += 1

    # Check for achievements
    achievement_unlocked = None
    if request.action == "client_signed" and state["stats"]["clients_signed"] == 1:
        for a in state["achievements"]:
            if a["id"] == "first_client" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]
                xp_gained += a["xp_bonus"]
                achievement_unlocked = a["name"]

    # Check level up
    leveled_up = check_level_up(state)

    save_player_state(state, request.tenant_id)

    return ActionResponse(
        success=True,
        message=f"{action['name']}! +{xp_gained} XP, +{coins_gained} coins",
        xp_gained=xp_gained,
        coins_gained=coins_gained,
        new_level=player["level"] if leveled_up else None,
        new_title=player["title"] if leveled_up else None,
        achievement_unlocked=achievement_unlocked
    )


@router.get("/achievements", response_model=List[AchievementStatus])
async def get_achievements(tenant_id: str = "wmarceau"):
    """Get all achievements and their status."""
    state = load_player_state(tenant_id)
    return [AchievementStatus(**a) for a in state["achievements"]]


@router.get("/rewards", response_model=List[RewardItem])
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


@router.post("/rewards/purchase", response_model=ActionResponse)
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
            if a["id"] == "week_streak" and not a["unlocked"]:
                a["unlocked"] = True
                player["xp"] += a["xp_bonus"]
                player["xp_total"] += a["xp_bonus"]

    if player["current_streak"] >= 30:
        for a in state["achievements"]:
            if a["id"] == "month_streak" and not a["unlocked"]:
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
