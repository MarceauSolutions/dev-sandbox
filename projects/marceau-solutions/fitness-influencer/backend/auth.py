#!/usr/bin/env python3
"""Client Authentication — Token-based magic link auth for coaching clients."""

from fastapi import HTTPException, Request
from pathlib import Path
from datetime import datetime
import json, secrets, uuid, copy

DATA_DIR = Path(__file__).parent.parent / "data" / "clients"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GAMIFICATION_DIR = Path(__file__).parent.parent / "data" / "gamification"
TENANTS_DIR = Path(__file__).parent.parent / "data" / "tenants"

# Client-specific gamification defaults (fitness-focused, not business-focused)
CLIENT_DEFAULT_PLAYER_STATE = {
    "player": {"level": 1, "xp": 0, "xp_total": 0, "coins": 0, "title": "New Member", "current_streak": 0, "best_streak": 0, "last_active_date": None},
    "levels": [
        {"level": 1, "title": "New Member", "xp_required": 0},
        {"level": 2, "title": "Getting Started", "xp_required": 50},
        {"level": 3, "title": "Building Momentum", "xp_required": 150},
        {"level": 4, "title": "Consistent", "xp_required": 350},
        {"level": 5, "title": "Dedicated", "xp_required": 600},
        {"level": 6, "title": "Warrior", "xp_required": 1000},
        {"level": 7, "title": "Beast Mode", "xp_required": 1500},
        {"level": 8, "title": "Elite", "xp_required": 2500},
        {"level": 9, "title": "Champion", "xp_required": 4000},
        {"level": 10, "title": "Legend", "xp_required": 6000},
    ],
    "daily_quests": [
        {"id": "workout_completed", "name": "Complete today's workout", "xp": 30, "coins": 10, "completed": False},
        {"id": "meal_logged", "name": "Log your meals", "xp": 15, "coins": 5, "completed": False},
        {"id": "check_in", "name": "Daily check-in", "xp": 10, "coins": 3, "completed": False},
    ],
    "power_actions": [
        {"id": "form_check", "name": "Form check submitted", "xp": 25, "coins": 10},
        {"id": "personal_record", "name": "Personal record!", "xp": 100, "coins": 50},
        {"id": "extra_workout", "name": "Extra workout session", "xp": 40, "coins": 15},
    ],
    "achievements": [
        {"id": "first_workout", "name": "First Workout", "description": "Completed your first workout", "xp_bonus": 50, "unlocked": False},
        {"id": "week_warrior", "name": "Week Warrior", "description": "7-day streak", "xp_bonus": 100, "unlocked": False},
        {"id": "form_master", "name": "Form Master", "description": "5 form checks with 80%+ score", "xp_bonus": 150, "unlocked": False},
        {"id": "iron_will", "name": "Iron Will", "description": "30-day streak", "xp_bonus": 500, "unlocked": False},
        {"id": "consistency_king", "name": "Consistency King", "description": "Complete all workouts for 4 weeks", "xp_bonus": 300, "unlocked": False},
        {"id": "month_one", "name": "Month One", "description": "Active for 30 days", "xp_bonus": 200, "unlocked": False},
        {"id": "halfway_there", "name": "Halfway There", "description": "Reached Level 5", "xp_bonus": 200, "unlocked": False},
        {"id": "pr_hunter", "name": "PR Hunter", "description": "Set 5 personal records", "xp_bonus": 250, "unlocked": False},
    ],
    "rewards": [
        {"id": "rest_day", "name": "Guilt-Free Rest Day", "description": "Take a day off", "cost": 50, "icon": "rest"},
        {"id": "cheat_meal", "name": "Cheat Meal Pass", "description": "Enjoy guilt-free", "cost": 100, "icon": "food"},
        {"id": "coaching_call", "name": "Bonus Coaching Call", "description": "15 min extra with coach", "cost": 200, "icon": "call"},
    ],
    "streak_multipliers": [
        {"days": 3, "multiplier": 1.25},
        {"days": 7, "multiplier": 1.5},
        {"days": 14, "multiplier": 2.0},
        {"days": 30, "multiplier": 3.0},
    ],
    "stats": {
        "workouts_completed": 0, "form_checks": 0, "meals_logged": 0,
        "check_ins": 0, "personal_records": 0, "total_workout_minutes": 0,
    },
    "action_log": [],
    "last_quest_reset": None,
}


def _load_index():
    idx_file = DATA_DIR / "index.json"
    if idx_file.exists():
        with open(idx_file, 'r') as f:
            return json.load(f)
    return {"clients": []}


def _save_index(index):
    with open(DATA_DIR / "index.json", 'w') as f:
        json.dump(index, f, indent=2, default=str)


def create_client(name: str, email: str, phone: str = None, goals: str = None) -> dict:
    """Create a new coaching client. Returns client_id, token, and login_url."""
    client_id = str(uuid.uuid4())[:12]
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow().isoformat()

    # Create client directory
    client_dir = DATA_DIR / client_id
    client_dir.mkdir(parents=True, exist_ok=True)

    # Profile
    profile = {
        "client_id": client_id, "name": name, "email": email,
        "phone": phone, "goals": goals, "start_date": now,
        "program": None, "coach_notes": "", "active": True
    }
    with open(client_dir / "profile.json", 'w') as f:
        json.dump(profile, f, indent=2)

    # Auth
    auth = {"token": token, "created_at": now, "last_login": None}
    with open(client_dir / "auth.json", 'w') as f:
        json.dump(auth, f, indent=2)

    # Empty data files
    for fname, default in [
        ("workouts.json", {"assignments": [], "stats": {"total_assigned": 0, "total_completed": 0}}),
        ("form_checks.json", {"checks": []}),
        ("chat_history.json", {"conversations": []}),
    ]:
        with open(client_dir / fname, 'w') as f:
            json.dump(default, f, indent=2)

    # Initialize gamification profile for this client
    GAMIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    gam_state = copy.deepcopy(CLIENT_DEFAULT_PLAYER_STATE)
    with open(GAMIFICATION_DIR / f"{client_id}_player.json", 'w') as f:
        json.dump(gam_state, f, indent=2, default=str)

    # Initialize tenant tasks
    tenant_dir = TENANTS_DIR / client_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    with open(tenant_dir / "tasks.json", 'w') as f:
        json.dump({"tasks": [], "metadata": {"created": now}}, f, indent=2)

    # Update index
    index = _load_index()
    index["clients"].append({
        "client_id": client_id, "name": name, "email": email,
        "token": token, "created_at": now, "active": True
    })
    _save_index(index)

    login_url = f"/client/#login?token={token}"
    return {"client_id": client_id, "token": token, "login_url": login_url, "profile": profile}


def verify_token(token: str):
    """Verify a client token. Returns client info dict or None."""
    index = _load_index()
    for c in index["clients"]:
        if c.get("token") == token and c.get("active", True):
            # Update last login
            client_dir = DATA_DIR / c["client_id"]
            auth_file = client_dir / "auth.json"
            if auth_file.exists():
                with open(auth_file, 'r') as f:
                    auth = json.load(f)
                auth["last_login"] = datetime.utcnow().isoformat()
                with open(auth_file, 'w') as f:
                    json.dump(auth, f, indent=2)
            return {"client_id": c["client_id"], "name": c["name"], "email": c["email"], "tenant_id": c["client_id"]}
    return None


def regenerate_token(client_id: str) -> str:
    """Generate a new token for a client, invalidating the old one."""
    new_token = secrets.token_urlsafe(32)
    index = _load_index()
    for c in index["clients"]:
        if c["client_id"] == client_id:
            c["token"] = new_token
            break
    _save_index(index)

    auth_file = DATA_DIR / client_id / "auth.json"
    if auth_file.exists():
        with open(auth_file, 'r') as f:
            auth = json.load(f)
        auth["token"] = new_token
        auth["created_at"] = datetime.utcnow().isoformat()
        with open(auth_file, 'w') as f:
            json.dump(auth, f, indent=2)
    return new_token


def load_client_profile(client_id: str) -> dict:
    """Load a client's profile."""
    pf = DATA_DIR / client_id / "profile.json"
    if not pf.exists():
        return None
    with open(pf, 'r') as f:
        return json.load(f)


def list_clients() -> list:
    """List all clients with summary info."""
    index = _load_index()
    results = []
    for c in index["clients"]:
        if not c.get("active", True):
            continue
        # Load gamification stats
        gam_file = GAMIFICATION_DIR / f"{c['client_id']}_player.json"
        level, streak, xp = 1, 0, 0
        if gam_file.exists():
            with open(gam_file, 'r') as f:
                gam = json.load(f)
            p = gam.get("player", {})
            level = p.get("level", 1)
            streak = p.get("current_streak", 0)
            xp = p.get("xp_total", 0)
        # Load workout stats
        wk_file = DATA_DIR / c["client_id"] / "workouts.json"
        workouts_done = 0
        if wk_file.exists():
            with open(wk_file, 'r') as f:
                wk = json.load(f)
            workouts_done = wk.get("stats", {}).get("total_completed", 0)
        # Load auth for last_login
        auth_file = DATA_DIR / c["client_id"] / "auth.json"
        last_login = None
        if auth_file.exists():
            with open(auth_file, 'r') as f:
                auth = json.load(f)
            last_login = auth.get("last_login")
        results.append({
            "client_id": c["client_id"], "name": c["name"], "email": c["email"],
            "level": level, "streak": streak, "xp": xp,
            "workouts_completed": workouts_done, "last_login": last_login, "created_at": c.get("created_at")
        })
    return results


async def get_current_client(request: Request) -> dict:
    """FastAPI dependency — extract and verify Bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")
    token = auth_header[7:]
    client = verify_token(token)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return client
