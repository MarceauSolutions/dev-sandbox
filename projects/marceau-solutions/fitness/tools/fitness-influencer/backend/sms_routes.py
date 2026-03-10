"""
SMS Routes — Hybrid n8n + Python Architecture

Python layer handles:
- Phone number validation (E.164 format)
- TCPA compliance (opt-out checks, time-of-day)
- Template rendering with personalization
- Opt-in/opt-out record persistence

n8n on EC2 handles:
- Actual SMS sending via Twilio node
- Google Sheets logging
- Follow-up sequences with Wait nodes
- Inbound SMS handling (SMS-Response-Handler-v2)

Data flow: Frontend → Python (validate, render) → n8n webhook (send, log)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import json
import re
import os
import httpx

try:
    from backend.sms_templates import TEMPLATES, render_template, list_templates
    from backend.collaborators_routes import (
        _load_collaborators, _save_collaborators, normalize_phone as _collab_normalize
    )
except ImportError:
    from sms_templates import TEMPLATES, render_template, list_templates
    from collaborators_routes import (
        _load_collaborators, _save_collaborators, normalize_phone as _collab_normalize
    )

router = APIRouter(prefix="/api/sms", tags=["sms"])

# n8n webhook URLs on EC2
N8N_BASE_URL = os.getenv("N8N_WEBHOOK_URL", "http://34.193.98.97:5678")
N8N_SEND_WEBHOOK = f"{N8N_BASE_URL}/webhook/fitness/sms/send"
N8N_FOLLOWUP_WEBHOOK = f"{N8N_BASE_URL}/webhook/fitness/sms/enroll-followup"

# Data storage
DATA_DIR = Path(__file__).parent.parent / "data" / "sms"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OPT_INS_FILE = DATA_DIR / "opt_ins.json"
OPT_OUTS_FILE = DATA_DIR / "opt_outs.json"
SMS_HISTORY_FILE = DATA_DIR / "history.json"


# --- Models ---

class SMSSendRequest(BaseModel):
    phone: str
    message: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[dict] = None


class CollaboratorOutreachRequest(BaseModel):
    phone: str
    name: str
    template: str = "collaborator_asset_request_casual"
    enroll_followup: bool = True


class FollowupEnrollRequest(BaseModel):
    phone: str
    name: str
    sequence_type: str = "collaborator"
    day0_message: Optional[str] = None


class SMSOptInRequest(BaseModel):
    phone: str
    firstName: str
    lastName: str
    timestamp: Optional[str] = None


# --- Helpers ---

def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format (+1XXXXXXXXXX)."""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if phone.startswith("+") and len(digits) >= 10:
        return f"+{digits}"
    raise ValueError(f"Invalid phone number: {phone}")


def _load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text())
    return []


def _save_json(path: Path, data: list):
    path.write_text(json.dumps(data, indent=2))


def is_opted_out(phone: str) -> bool:
    """Check if phone number is on the opt-out list."""
    normalized = normalize_phone(phone)
    opt_outs = _load_json(OPT_OUTS_FILE)
    return any(entry["phone"] == normalized for entry in opt_outs)


def record_opt_in(phone: str, first_name: str, last_name: str):
    """Record a new SMS opt-in."""
    normalized = normalize_phone(phone)
    opt_ins = _load_json(OPT_INS_FILE)

    # Check for duplicate
    if any(entry["phone"] == normalized for entry in opt_ins):
        return  # Already opted in

    opt_ins.append({
        "phone": normalized,
        "first_name": first_name,
        "last_name": last_name,
        "opted_in_at": datetime.utcnow().isoformat(),
    })
    _save_json(OPT_INS_FILE, opt_ins)


def record_sms_sent(phone: str, template_id: str, message: str, response: dict):
    """Log an SMS send to local history."""
    history = _load_json(SMS_HISTORY_FILE)
    history.append({
        "phone": phone,
        "template_id": template_id,
        "message": message[:100],
        "response": response,
        "sent_at": datetime.utcnow().isoformat(),
    })
    # Keep last 500 entries
    if len(history) > 500:
        history = history[-500:]
    _save_json(SMS_HISTORY_FILE, history)


def _ensure_collaborator(phone: str, name: str, template_id: str, message: str):
    """Auto-create or update collaborator record when outreach SMS is sent."""
    import uuid
    collaborators = _load_collaborators()

    # Find existing by phone
    existing = None
    for i, c in enumerate(collaborators):
        if c.get("phone") == phone:
            existing = (i, c)
            break

    now = datetime.utcnow().isoformat()

    if existing:
        idx, collab = existing
        # Log the SMS and advance status
        collab["sms_history"].append({
            "direction": "outbound",
            "message": message[:200],
            "template_id": template_id,
            "timestamp": now,
        })
        if collab["status"] in ("lead",):
            collab["status"] = "assets_requested"
        collab["updated_at"] = now
        collaborators[idx] = collab
    else:
        # Auto-create new collaborator from outreach
        parts = name.strip().split(" ", 1)
        collab = {
            "id": str(uuid.uuid4())[:8],
            "first_name": parts[0],
            "last_name": parts[1] if len(parts) > 1 else "",
            "phone": phone,
            "email": None,
            "relationship": None,
            "status": "assets_requested",
            "notes": f"Auto-created from SMS outreach ({template_id})",
            "assets": {
                "photo": {"received_at": None, "file_path": None, "url": None, "notes": None},
                "voice": {"received_at": None, "file_path": None, "url": None, "notes": None},
                "consent": {"received_at": None, "file_path": None, "url": None, "notes": None},
            },
            "sms_history": [{
                "direction": "outbound",
                "message": message[:200],
                "template_id": template_id,
                "timestamp": now,
            }],
            "avatar": {
                "created_at": None,
                "image_path": None,
                "voice_id": None,
                "video_paths": [],
            },
            "created_at": now,
            "updated_at": now,
        }
        collaborators.append(collab)

    _save_collaborators(collaborators)
    return collab


async def forward_to_n8n(webhook_url: str, payload: dict) -> dict:
    """Forward a request to n8n webhook on EC2."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
        return resp.json()


# --- Routes ---

@router.post("/send")
async def send_sms(req: SMSSendRequest):
    """Send a single SMS via n8n.

    Either provide a direct `message` or a `template` + `variables`.
    Validates phone, checks opt-out, renders template, then forwards to n8n.
    """
    try:
        phone = normalize_phone(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if is_opted_out(phone):
        raise HTTPException(status_code=403, detail="Phone number has opted out of SMS")

    # Render message from template or use direct message
    if req.template:
        try:
            message = render_template(req.template, req.variables or {})
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Template error: {e}")
    elif req.message:
        message = req.message
    else:
        raise HTTPException(status_code=400, detail="Provide either 'message' or 'template'")

    # Forward to n8n
    try:
        result = await forward_to_n8n(N8N_SEND_WEBHOOK, {
            "phone": phone,
            "message": message,
            "template_id": req.template or "direct",
            "collaborator_name": (req.variables or {}).get("name", ""),
        })
        record_sms_sent(phone, req.template or "direct", message, result)
        return {"success": True, "n8n_response": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"n8n forwarding failed: {e}")


@router.post("/collaborator-outreach")
async def collaborator_outreach(req: CollaboratorOutreachRequest):
    """Send a collaborator asset request SMS and optionally enroll in follow-up sequence.

    This is the primary endpoint for requesting photos/voice from collaborators.
    """
    try:
        phone = normalize_phone(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if is_opted_out(phone):
        raise HTTPException(status_code=403, detail="Phone number has opted out of SMS")

    # Render the outreach message
    try:
        message = render_template(req.template, {"name": req.name})
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Template error: {e}")

    # Send via n8n
    try:
        send_result = await forward_to_n8n(N8N_SEND_WEBHOOK, {
            "phone": phone,
            "message": message,
            "template_id": req.template,
            "collaborator_name": req.name,
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"n8n send failed: {e}")

    record_sms_sent(phone, req.template, message, send_result)

    # Auto-create/update collaborator record
    collaborator = _ensure_collaborator(phone, req.name, req.template, message)

    # Enroll in follow-up sequence if requested
    followup_result = None
    if req.enroll_followup:
        day2_msg = render_template("collaborator_followup_day2", {"name": req.name})
        day5_msg = render_template("collaborator_followup_day5", {"name": req.name})
        try:
            followup_result = await forward_to_n8n(N8N_FOLLOWUP_WEBHOOK, {
                "phone": phone,
                "name": req.name,
                "sequence_type": "collaborator",
                "day0_message": message,
                "day2_message": day2_msg,
                "day5_message": day5_msg,
            })
        except Exception as e:
            # Non-fatal: outreach sent but follow-up enrollment failed
            followup_result = {"error": str(e)}

    return {
        "success": True,
        "phone": phone,
        "message_sent": message[:80] + "...",
        "send_result": send_result,
        "followup_enrolled": followup_result,
        "collaborator_id": collaborator["id"],
    }


@router.post("/enroll-followup")
async def enroll_followup(req: FollowupEnrollRequest):
    """Enroll a phone number in a follow-up sequence via n8n."""
    try:
        phone = normalize_phone(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if is_opted_out(phone):
        raise HTTPException(status_code=403, detail="Phone number has opted out of SMS")

    # Build follow-up messages from templates
    day0 = req.day0_message or render_template(
        "collaborator_asset_request_casual", {"name": req.name}
    )
    day2 = render_template("collaborator_followup_day2", {"name": req.name})
    day5 = render_template("collaborator_followup_day5", {"name": req.name})

    try:
        result = await forward_to_n8n(N8N_FOLLOWUP_WEBHOOK, {
            "phone": phone,
            "name": req.name,
            "sequence_type": req.sequence_type,
            "day0_message": day0,
            "day2_message": day2,
            "day5_message": day5,
        })
        return {"success": True, "enrolled": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"n8n enrollment failed: {e}")


@router.get("/templates")
async def get_templates(category: str = None):
    """List available SMS templates."""
    return {"templates": list_templates(category)}


@router.get("/history")
async def get_history(limit: int = 50):
    """Get recent SMS send history."""
    history = _load_json(SMS_HISTORY_FILE)
    return {"history": history[-limit:], "total": len(history)}


@router.post("/optin")
async def sms_optin(opt_in: SMSOptInRequest):
    """Handle SMS opt-in. Records consent and sends welcome SMS via n8n."""
    try:
        phone = normalize_phone(opt_in.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Record opt-in
    record_opt_in(phone, opt_in.firstName, opt_in.lastName)

    # Send welcome SMS via n8n
    try:
        message = render_template("welcome", {"name": opt_in.firstName})
        result = await forward_to_n8n(N8N_SEND_WEBHOOK, {
            "phone": phone,
            "message": message,
            "template_id": "welcome",
            "collaborator_name": opt_in.firstName,
        })
        record_sms_sent(phone, "welcome", message, result)
        return {
            "success": True,
            "message": "Welcome SMS sent",
            "n8n_response": result,
            "data": {
                "phone": phone,
                "firstName": opt_in.firstName,
                "lastName": opt_in.lastName,
            },
        }
    except Exception as e:
        # Opt-in was recorded even if SMS fails
        return {
            "success": True,
            "message": "Opt-in recorded but SMS send failed",
            "error": str(e),
            "data": {
                "phone": phone,
                "firstName": opt_in.firstName,
                "lastName": opt_in.lastName,
            },
        }


@router.post("/optout")
async def sms_optout(phone: str):
    """Record an SMS opt-out."""
    try:
        normalized = normalize_phone(phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    opt_outs = _load_json(OPT_OUTS_FILE)
    if not any(entry["phone"] == normalized for entry in opt_outs):
        opt_outs.append({
            "phone": normalized,
            "opted_out_at": datetime.utcnow().isoformat(),
        })
        _save_json(OPT_OUTS_FILE, opt_outs)

    return {"success": True, "phone": normalized, "status": "opted_out"}
