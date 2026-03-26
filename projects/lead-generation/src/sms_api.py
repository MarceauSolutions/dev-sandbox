"""
Lead Generation SMS API - Tower-specific SMS operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides SMS functionality for lead-generation tower only.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio client singleton
_twilio_client = None

def get_twilio_client():
    """Get or create Twilio client for lead-generation tower."""
    global _twilio_client
    if _twilio_client is not None:
        return _twilio_client

    try:
        from twilio.rest import Client

        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')

        if not account_sid or not auth_token:
            logger.error("Twilio credentials not configured")
            return None

        _twilio_client = Client(account_sid, auth_token)
        logger.info("Twilio client initialized for lead-generation tower")
        return _twilio_client

    except ImportError:
        logger.error("Twilio package not installed")
        return None
    except Exception as e:
        logger.error(f"Twilio client initialization failed: {e}")
        return None


def send_sms(to: str, body: str, from_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an SMS via Twilio.

    Args:
        to: Recipient phone number
        body: SMS message body
        from_number: Sender phone number (optional, uses env default)

    Returns:
        Dict with send status
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not available"}

    if not to:
        return {"success": False, "error": "Recipient phone number required"}

    if not body:
        return {"success": False, "error": "Message body required"}

    try:
        from_number = from_number or os.getenv('TWILIO_PHONE_NUMBER')
        if not from_number:
            return {"success": False, "error": "Sender phone number not configured"}

        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to
        )

        return {
            "success": True,
            "sid": message.sid,
            "to": to,
            "from": from_number,
            "status": message.status,
            "body_length": len(body)
        }

    except Exception as e:
        logger.error(f"Failed to send SMS to {to}: {e}")
        return {"success": False, "error": str(e)}


def list_sms_messages(limit: int = 20, direction: Optional[str] = None) -> Dict[str, Any]:
    """
    List SMS messages from Twilio.

    Args:
        limit: Maximum number of messages to return
        direction: Filter by direction ('inbound' or 'outbound')

    Returns:
        Dict with messages list
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not available"}

    try:
        kwargs = {'limit': min(limit, 50)}  # Twilio limit

        if direction == 'inbound':
            kwargs['to'] = os.getenv('TWILIO_PHONE_NUMBER')
        elif direction == 'outbound':
            kwargs['from_'] = os.getenv('TWILIO_PHONE_NUMBER')

        messages = client.messages.list(**kwargs)

        sms_list = []
        for msg in messages:
            sms_list.append({
                "sid": msg.sid,
                "from": msg.from_,
                "to": msg.to,
                "body": msg.body,
                "status": msg.status,
                "direction": msg.direction,
                "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                "date_created": msg.date_created.isoformat() if msg.date_created else None
            })

        return {
            "success": True,
            "messages": sms_list,
            "count": len(sms_list),
            "direction_filter": direction
        }

    except Exception as e:
        logger.error(f"Failed to list SMS messages: {e}")
        return {"success": False, "error": str(e)}


def get_sms_status(sid: str) -> Dict[str, Any]:
    """
    Get the status of a specific SMS message.

    Args:
        sid: Twilio message SID

    Returns:
        Dict with message status
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not available"}

    if not sid:
        return {"success": False, "error": "Message SID required"}

    try:
        message = client.messages(sid).fetch()

        return {
            "success": True,
            "sid": message.sid,
            "status": message.status,
            "to": message.to,
            "from": message.from_,
            "body": message.body,
            "direction": message.direction,
            "date_sent": message.date_sent.isoformat() if message.date_sent else None,
            "date_created": message.date_created.isoformat() if message.date_created else None,
            "error_code": message.error_code,
            "error_message": message.error_message
        }

    except Exception as e:
        logger.error(f"Failed to get SMS status for {sid}: {e}")
        return {"success": False, "error": str(e)}


def send_bulk_sms(recipients: List[str], body: str, from_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Send SMS to multiple recipients.

    Args:
        recipients: List of phone numbers
        body: SMS message body
        from_number: Sender phone number (optional)

    Returns:
        Dict with bulk send results
    """
    if not recipients:
        return {"success": False, "error": "No recipients provided"}

    if len(recipients) > 100:
        return {"success": False, "error": "Maximum 100 recipients allowed"}

    results = []
    success_count = 0
    error_count = 0

    for phone in recipients:
        result = send_sms(phone, body, from_number)
        results.append({
            "recipient": phone,
            "success": result.get("success", False),
            "sid": result.get("sid"),
            "error": result.get("error")
        })

        if result.get("success"):
            success_count += 1
        else:
            error_count += 1

    return {
        "success": True,
        "total_recipients": len(recipients),
        "successful_sends": success_count,
        "failed_sends": error_count,
        "results": results
    }


def get_sms_usage(days: int = 30) -> Dict[str, Any]:
    """
    Get SMS usage statistics.

    Args:
        days: Number of days to look back

    Returns:
        Dict with usage statistics
    """
    client = get_twilio_client()
    if not client:
        return {"success": False, "error": "Twilio client not available"}

    try:
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        # Get usage records
        usage_records = client.usage.records.list(
            start_date=start_date.date(),
            end_date=datetime.now().date()
        )

        total_sms = 0
        total_cost = 0.0

        for record in usage_records:
            if hasattr(record, 'count'):
                total_sms += record.count
            if hasattr(record, 'price'):
                total_cost += float(record.price or 0)

        # Get current balance
        balance = None
        try:
            account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
            balance = float(account.balance or 0)
        except:
            pass

        return {
            "success": True,
            "period_days": days,
            "total_sms": total_sms,
            "total_cost": round(total_cost, 4),
            "account_balance": balance,
            "average_daily": round(total_sms / days, 1) if days > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get SMS usage: {e}")
        return {"success": False, "error": str(e)}


# Tower interface functions for CLAUDE.md compliance
def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for SMS operations."""
    return {
        "name": "lead-generation-sms",
        "description": "SMS integration for lead generation campaigns",
        "functions": [
            "send_sms",
            "list_sms_messages",
            "get_sms_status",
            "send_bulk_sms",
            "get_sms_usage"
        ],
        "protocols": ["direct_import", "mcp_server"]
    }


def get_mcp_server_config() -> Dict[str, Any]:
    """Return MCP server configuration for tower integration."""
    return {
        "name": "lead-generation-sms",
        "version": "1.0.0",
        "capabilities": get_tower_capabilities(),
        "endpoints": {
            "send": "/sms/send",
            "list": "/sms/list",
            "status": "/sms/status",
            "bulk": "/sms/bulk",
            "usage": "/sms/usage"
        }
    }


if __name__ == "__main__":
    # Test the SMS API extraction
    print("Testing lead-generation SMS API extraction...")

    # Test client initialization
    client = get_twilio_client()
    if client:
        print("✓ Twilio client initialized")
    else:
        print("✗ Twilio client failed - check credentials")

    # Test capabilities
    caps = get_tower_capabilities()
    print(f"✓ Tower capabilities: {caps['name']}")

    print("SMS API extraction test completed")