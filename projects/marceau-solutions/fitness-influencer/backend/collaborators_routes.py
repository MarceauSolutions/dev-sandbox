"""
Collaborator Management Routes

Track fitness influencer collaborators through the AI avatar pipeline:
- Contact info (name, phone, email)
- Pipeline status (lead → contacted → assets collected → avatar created → active)
- Asset tracking (photo, voice clip, consent)
- SMS history integration
- Notes and relationship metadata

Data stored as JSON in data/collaborators/
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import json
import uuid
import re

router = APIRouter(prefix="/api/collaborators", tags=["collaborators"])

# Data storage
DATA_DIR = Path(__file__).parent.parent / "data" / "collaborators"
DATA_DIR.mkdir(parents=True, exist_ok=True)
COLLABORATORS_FILE = DATA_DIR / "collaborators.json"


# --- Pipeline Stages ---

PIPELINE_STAGES = [
    "lead",              # Identified as potential collaborator
    "contacted",         # Initial outreach sent
    "assets_requested",  # Specific asset request sent via SMS
    "photo_received",    # Headshot received
    "voice_received",    # Voice clip received
    "consent_received",  # Written permission received
    "ready",             # All 3 assets collected — ready for avatar
    "avatar_created",    # AI avatar generated
    "active",            # Actively used for content
]


# --- Models ---

class CollaboratorCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: Optional[str] = None  # friend, family, professional, influencer
    notes: Optional[str] = None


class CollaboratorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AssetUpdate(BaseModel):
    asset_type: str  # photo, voice, consent
    file_path: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None


class InboundMediaRequest(BaseModel):
    phone: str
    media_url: str
    media_type: str  # MIME type: image/jpeg, audio/amr, video/mp4, etc.


# --- Helpers ---

def normalize_phone(phone: str) -> str:
    """Normalize phone to E.164 format."""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if phone.startswith("+") and len(digits) >= 10:
        return f"+{digits}"
    raise ValueError(f"Invalid phone number: {phone}")


def _load_collaborators() -> list:
    if COLLABORATORS_FILE.exists():
        return json.loads(COLLABORATORS_FILE.read_text())
    return []


def _save_collaborators(data: list):
    COLLABORATORS_FILE.write_text(json.dumps(data, indent=2))


def _find_collaborator(collaborators: list, collaborator_id: str) -> tuple:
    """Find collaborator by ID. Returns (index, collaborator) or raises 404."""
    for i, c in enumerate(collaborators):
        if c["id"] == collaborator_id:
            return i, c
    raise HTTPException(status_code=404, detail=f"Collaborator {collaborator_id} not found")


def _advance_status(collaborator: dict) -> str:
    """Auto-advance status based on assets received."""
    assets = collaborator.get("assets", {})
    has_photo = bool(assets.get("photo", {}).get("received_at"))
    has_voice = bool(assets.get("voice", {}).get("received_at"))
    has_consent = bool(assets.get("consent", {}).get("received_at"))

    current = collaborator["status"]

    # Don't auto-downgrade from later stages
    current_idx = PIPELINE_STAGES.index(current) if current in PIPELINE_STAGES else 0

    if has_photo and has_voice and has_consent and current_idx < PIPELINE_STAGES.index("ready"):
        return "ready"
    if has_consent and current_idx < PIPELINE_STAGES.index("consent_received"):
        return "consent_received"
    if has_voice and current_idx < PIPELINE_STAGES.index("voice_received"):
        return "voice_received"
    if has_photo and current_idx < PIPELINE_STAGES.index("photo_received"):
        return "photo_received"

    return current


# --- Routes ---

@router.get("")
async def list_collaborators(status: str = None, relationship: str = None):
    """List all collaborators, optionally filtered by status or relationship."""
    collaborators = _load_collaborators()

    if status:
        collaborators = [c for c in collaborators if c["status"] == status]
    if relationship:
        collaborators = [c for c in collaborators if c.get("relationship") == relationship]

    return {
        "collaborators": collaborators,
        "total": len(collaborators),
        "pipeline_stages": PIPELINE_STAGES,
    }


@router.get("/pipeline")
async def pipeline_summary():
    """Get a summary of collaborators at each pipeline stage."""
    collaborators = _load_collaborators()
    summary = {stage: [] for stage in PIPELINE_STAGES}

    for c in collaborators:
        stage = c.get("status", "lead")
        if stage in summary:
            summary[stage].append({
                "id": c["id"],
                "name": f"{c['first_name']} {c.get('last_name', '')}".strip(),
                "phone": c.get("phone"),
            })

    return {
        "pipeline": {stage: {"count": len(items), "collaborators": items}
                      for stage, items in summary.items()},
        "total": len(collaborators),
    }


@router.get("/search/{query}")
async def search_collaborators(query: str):
    """Search collaborators by name, phone, or email."""
    collaborators = _load_collaborators()
    query_lower = query.lower()

    results = []
    for c in collaborators:
        searchable = " ".join(filter(None, [
            c.get("first_name", ""),
            c.get("last_name", ""),
            c.get("phone", ""),
            c.get("email", ""),
            c.get("relationship", ""),
            c.get("notes", ""),
        ])).lower()

        if query_lower in searchable:
            results.append(c)

    return {"results": results, "total": len(results), "query": query}


@router.get("/by-phone/{phone}")
async def get_collaborator_by_phone(phone: str):
    """Look up a collaborator by phone number."""
    try:
        normalized = normalize_phone(phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    collaborators = _load_collaborators()
    for c in collaborators:
        if c.get("phone") == normalized:
            return c

    raise HTTPException(status_code=404, detail=f"No collaborator with phone {normalized}")


@router.post("/process-inbound-media")
async def process_inbound_media(req: InboundMediaRequest):
    """Process inbound media from a collaborator's MMS reply.

    Looks up collaborator by phone, records the asset (photo/voice),
    and auto-advances their pipeline status.
    """
    try:
        normalized = normalize_phone(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    collaborators = _load_collaborators()
    found = None
    for i, c in enumerate(collaborators):
        if c.get("phone") == normalized:
            found = (i, c)
            break

    if not found:
        raise HTTPException(
            status_code=404,
            detail=f"No collaborator with phone {normalized}"
        )

    idx, collaborator = found

    # Classify media type from MIME type
    if req.media_type.startswith("image/"):
        asset_type = "photo"
    elif req.media_type.startswith("audio/"):
        asset_type = "voice"
    elif req.media_type.startswith("video/"):
        asset_type = "voice"  # Treat video as voice clip for pipeline
    else:
        asset_type = "photo"  # Default

    # Record the asset
    collaborator["assets"][asset_type] = {
        "received_at": datetime.utcnow().isoformat(),
        "file_path": None,
        "url": req.media_url,
        "notes": f"Auto-received via MMS ({req.media_type})",
    }

    # Auto-advance pipeline status
    collaborator["status"] = _advance_status(collaborator)
    collaborator["updated_at"] = datetime.utcnow().isoformat()

    collaborators[idx] = collaborator
    _save_collaborators(collaborators)

    name = f"{collaborator['first_name']} {collaborator.get('last_name', '')}".strip()

    return {
        "success": True,
        "collaborator_id": collaborator["id"],
        "name": name,
        "asset_type": asset_type,
        "new_status": collaborator["status"],
        "assets_summary": {
            k: {"received": bool(v.get("received_at"))}
            for k, v in collaborator["assets"].items()
        },
    }


@router.get("/{collaborator_id}")
async def get_collaborator(collaborator_id: str):
    """Get a single collaborator's full record."""
    collaborators = _load_collaborators()
    _, collaborator = _find_collaborator(collaborators, collaborator_id)
    return collaborator


@router.post("")
async def create_collaborator(req: CollaboratorCreate):
    """Add a new collaborator."""
    collaborators = _load_collaborators()

    # Normalize phone if provided
    phone = None
    if req.phone:
        try:
            phone = normalize_phone(req.phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check for duplicate phone
        if any(c.get("phone") == phone for c in collaborators):
            raise HTTPException(status_code=409, detail=f"Collaborator with phone {phone} already exists")

    collaborator = {
        "id": str(uuid.uuid4())[:8],
        "first_name": req.first_name,
        "last_name": req.last_name or "",
        "phone": phone,
        "email": req.email,
        "relationship": req.relationship,
        "status": "lead",
        "notes": req.notes,
        "assets": {
            "photo": {"received_at": None, "file_path": None, "url": None, "notes": None},
            "voice": {"received_at": None, "file_path": None, "url": None, "notes": None},
            "consent": {"received_at": None, "file_path": None, "url": None, "notes": None},
        },
        "sms_history": [],
        "avatar": {
            "created_at": None,
            "image_path": None,
            "voice_id": None,
            "video_paths": [],
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    collaborators.append(collaborator)
    _save_collaborators(collaborators)

    return {"success": True, "collaborator": collaborator}


@router.put("/{collaborator_id}")
async def update_collaborator(collaborator_id: str, req: CollaboratorUpdate):
    """Update a collaborator's info."""
    collaborators = _load_collaborators()
    idx, collaborator = _find_collaborator(collaborators, collaborator_id)

    if req.first_name is not None:
        collaborator["first_name"] = req.first_name
    if req.last_name is not None:
        collaborator["last_name"] = req.last_name
    if req.phone is not None:
        try:
            collaborator["phone"] = normalize_phone(req.phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if req.email is not None:
        collaborator["email"] = req.email
    if req.relationship is not None:
        collaborator["relationship"] = req.relationship
    if req.notes is not None:
        collaborator["notes"] = req.notes
    if req.status is not None:
        if req.status not in PIPELINE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {PIPELINE_STAGES}")
        collaborator["status"] = req.status

    collaborator["updated_at"] = datetime.utcnow().isoformat()
    collaborators[idx] = collaborator
    _save_collaborators(collaborators)

    return {"success": True, "collaborator": collaborator}


@router.delete("/{collaborator_id}")
async def delete_collaborator(collaborator_id: str):
    """Remove a collaborator."""
    collaborators = _load_collaborators()
    idx, collaborator = _find_collaborator(collaborators, collaborator_id)

    name = f"{collaborator['first_name']} {collaborator.get('last_name', '')}".strip()
    collaborators.pop(idx)
    _save_collaborators(collaborators)

    return {"success": True, "deleted": name}


@router.post("/{collaborator_id}/assets")
async def record_asset(collaborator_id: str, req: AssetUpdate):
    """Record that an asset (photo, voice, consent) was received."""
    if req.asset_type not in ("photo", "voice", "consent"):
        raise HTTPException(status_code=400, detail="asset_type must be: photo, voice, or consent")

    collaborators = _load_collaborators()
    idx, collaborator = _find_collaborator(collaborators, collaborator_id)

    collaborator["assets"][req.asset_type] = {
        "received_at": datetime.utcnow().isoformat(),
        "file_path": req.file_path,
        "url": req.url,
        "notes": req.notes,
    }

    # Auto-advance pipeline status
    collaborator["status"] = _advance_status(collaborator)
    collaborator["updated_at"] = datetime.utcnow().isoformat()

    collaborators[idx] = collaborator
    _save_collaborators(collaborators)

    return {
        "success": True,
        "asset_type": req.asset_type,
        "status": collaborator["status"],
        "assets_summary": {
            k: {"received": bool(v.get("received_at"))}
            for k, v in collaborator["assets"].items()
        },
    }


@router.post("/{collaborator_id}/avatar")
async def record_avatar(collaborator_id: str, image_path: str = None, voice_id: str = None, video_path: str = None):
    """Record avatar creation details."""
    collaborators = _load_collaborators()
    idx, collaborator = _find_collaborator(collaborators, collaborator_id)

    if image_path:
        collaborator["avatar"]["image_path"] = image_path
    if voice_id:
        collaborator["avatar"]["voice_id"] = voice_id
    if video_path:
        if video_path not in collaborator["avatar"]["video_paths"]:
            collaborator["avatar"]["video_paths"].append(video_path)

    if not collaborator["avatar"]["created_at"]:
        collaborator["avatar"]["created_at"] = datetime.utcnow().isoformat()

    collaborator["status"] = "avatar_created"
    collaborator["updated_at"] = datetime.utcnow().isoformat()

    collaborators[idx] = collaborator
    _save_collaborators(collaborators)

    return {"success": True, "avatar": collaborator["avatar"], "status": collaborator["status"]}


@router.post("/{collaborator_id}/sms")
async def log_sms(collaborator_id: str, message: str, direction: str = "outbound", template_id: str = None):
    """Log an SMS interaction with this collaborator."""
    if direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=400, detail="direction must be: inbound or outbound")

    collaborators = _load_collaborators()
    idx, collaborator = _find_collaborator(collaborators, collaborator_id)

    collaborator["sms_history"].append({
        "direction": direction,
        "message": message[:200],
        "template_id": template_id,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Keep last 50 SMS entries per collaborator
    if len(collaborator["sms_history"]) > 50:
        collaborator["sms_history"] = collaborator["sms_history"][-50:]

    # Auto-advance to contacted if first outbound
    if direction == "outbound" and collaborator["status"] == "lead":
        collaborator["status"] = "contacted"

    collaborator["updated_at"] = datetime.utcnow().isoformat()
    collaborators[idx] = collaborator
    _save_collaborators(collaborators)

    return {"success": True, "sms_count": len(collaborator["sms_history"]), "status": collaborator["status"]}


@router.get("/{collaborator_id}/sms")
async def get_sms_history(collaborator_id: str):
    """Get SMS history for a collaborator."""
    collaborators = _load_collaborators()
    _, collaborator = _find_collaborator(collaborators, collaborator_id)

    return {
        "collaborator": f"{collaborator['first_name']} {collaborator.get('last_name', '')}".strip(),
        "phone": collaborator.get("phone"),
        "sms_history": collaborator.get("sms_history", []),
        "total": len(collaborator.get("sms_history", [])),
    }


