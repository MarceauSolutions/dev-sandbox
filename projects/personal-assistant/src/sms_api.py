"""
Personal Assistant Twilio SMS API - Tower-specific SMS operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides SMS send/list via Twilio for personal-assistant tower.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_twilio_client():
    """Get authenticated Twilio client."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        return None, "Twilio credentials not configured"
    try:
        from twilio.rest import Client
        return Client(account_sid, auth_token), None
    except Exception as e:
        return None, str(e)


def send_sms(to: str, body: str, from_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an SMS via Twilio.

    Args:
        to: Recipient phone number
        body: Message body
        from_number: Sender number (falls back to TWILIO_PHONE_NUMBER env var)

    Returns:
        Dict with send status
    """
    if not to:
        return {"success": False, "error": "to is required"}
    if not body:
        return {"success": False, "error": "body is required"}

    from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')
    client, error = _get_twilio_client()
    if not client:
        return {"success": False, "error": error}

    try:
        message = client.messages.create(body=body, from_=from_number, to=to)
        return {
            "success": True,
            "sid": message.sid,
            "to": to,
            "status": message.status
        }
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return {"success": False, "error": str(e)}


def list_sms(limit: int = 20, direction: Optional[str] = None) -> Dict[str, Any]:
    """
    List SMS messages from Twilio.

    Args:
        limit: Maximum number of messages to return
        direction: "inbound", "outbound", or None for all

    Returns:
        Dict with message list
    """
    client, error = _get_twilio_client()
    if not client:
        return {"success": False, "error": error}

    try:
        kwargs = {'limit': limit}
        if direction == 'inbound':
            kwargs['to'] = os.getenv('TWILIO_PHONE_NUMBER')
        elif direction == 'outbound':
            kwargs['from_'] = os.getenv('TWILIO_PHONE_NUMBER')

        messages = client.messages.list(**kwargs)
        sms_list = [{
            'sid': m.sid,
            'from': m.from_,
            'to': m.to,
            'body': m.body,
            'status': m.status,
            'direction': m.direction
        } for m in messages]

        return {
            "success": True,
            "messages": sms_list,
            "count": len(sms_list)
        }
    except Exception as e:
        logger.error(f"Failed to list SMS: {e}")
        return {"success": False, "error": str(e)}


def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for SMS operations."""
    return {
        "name": "personal-assistant-sms",
        "description": "Twilio SMS integration for personal assistant automation",
        "functions": ["send_sms", "list_sms"],
        "protocols": ["direct_import", "mcp_server"]
    }
