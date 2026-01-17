#!/usr/bin/env python3
"""
Twilio MCP Server - SMS Tools for Claude

Provides tools to:
1. Check inbox for SMS replies
2. Send SMS messages
3. Get message history
4. View hot leads and opt-outs

USAGE with Claude Desktop:
  Add to claude_desktop_config.json:
  {
    "mcpServers": {
      "twilio": {
        "command": "python",
        "args": ["-m", "twilio_mcp.server"],
        "env": {
          "TWILIO_ACCOUNT_SID": "your_sid",
          "TWILIO_AUTH_TOKEN": "your_token",
          "TWILIO_PHONE_NUMBER": "+1855XXXXXXX"
        }
      }
    }
  }
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp")
    raise

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    print("ERROR: twilio package not installed. Run: pip install twilio")
    raise


# Initialize MCP server
mcp = Server("twilio-mcp")

# Twilio configuration
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Data paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
LEAD_SCRAPER_OUTPUT = PROJECT_ROOT / "projects" / "lead-scraper" / "output"
CAMPAIGNS_FILE = LEAD_SCRAPER_OUTPUT / "sms_campaigns.json"
REPLIES_FILE = LEAD_SCRAPER_OUTPUT / "sms_replies.json"


def get_twilio_client() -> Client:
    """Get Twilio client, raising error if not configured."""
    if not all([ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUMBER]):
        raise ValueError(
            "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables."
        )
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def load_phone_to_business() -> dict:
    """Load mapping of phone numbers to business names from campaigns."""
    mapping = {}
    if CAMPAIGNS_FILE.exists():
        try:
            with open(CAMPAIGNS_FILE) as f:
                data = json.load(f)
                for record in data.get("records", []):
                    phone = normalize_phone(record.get("phone", ""))
                    business = record.get("business_name", "")
                    if phone and business:
                        mapping[phone] = business
        except Exception:
            pass
    return mapping


def normalize_phone(phone: str) -> str:
    """Normalize phone to E.164 format."""
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    return phone


def categorize_message(body: str) -> str:
    """Categorize a message based on keywords."""
    body_lower = body.lower().strip()

    opt_out = ["stop", "unsubscribe", "remove", "opt out", "cancel"]
    if any(kw in body_lower for kw in opt_out):
        return "opt_out"

    hot = [
        "yes", "interested", "call me", "call back", "website", "how much",
        "price", "cost", "schedule", "available", "sounds good", "sign me up"
    ]
    if any(kw in body_lower for kw in hot):
        return "hot_lead"

    warm = ["maybe", "thinking", "question", "?", "what", "how", "when", "busy"]
    if any(kw in body_lower for kw in warm):
        return "warm_lead"

    return "unknown"


@mcp.list_tools()
async def list_tools():
    """List available Twilio tools."""
    return [
        Tool(
            name="check_sms_inbox",
            description=(
                "Check Twilio inbox for incoming SMS replies from cold outreach campaigns. "
                "Returns new messages categorized as hot_lead, warm_lead, opt_out, or unknown. "
                "Use this to see who responded to SMS outreach."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hours_back": {
                        "type": "integer",
                        "description": "How many hours back to check (default 48)",
                        "default": 48
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="send_sms",
            description=(
                "Send an SMS message to a phone number. "
                "Use for follow-ups with leads or notifications."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "to_phone": {
                        "type": "string",
                        "description": "Phone number to send to (E.164 format: +12395551234)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text to send (max 1600 characters)"
                    }
                },
                "required": ["to_phone", "message"]
            }
        ),
        Tool(
            name="get_sms_reply_summary",
            description=(
                "Get a summary of all SMS replies received. "
                "Shows counts of hot leads, warm leads, and opt-outs."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_hot_leads",
            description=(
                "Get list of hot leads from SMS replies - people who expressed interest. "
                "These are high priority leads that should be followed up with."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_campaign_stats",
            description=(
                "Get statistics about SMS outreach campaigns. "
                "Shows total sent, response rate, and breakdown by status."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="forward_message_to_phone",
            description=(
                "Forward a specific SMS reply to your personal phone number. "
                "Use when you want to be notified of important messages on your real phone."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message_sid": {
                        "type": "string",
                        "description": "The message SID to forward (from check_sms_inbox)"
                    },
                    "forward_to": {
                        "type": "string",
                        "description": "Your personal phone number to forward to"
                    }
                },
                "required": ["message_sid", "forward_to"]
            }
        )
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "check_sms_inbox":
        return await check_sms_inbox(arguments.get("hours_back", 48))

    elif name == "send_sms":
        return await send_sms(
            arguments.get("to_phone"),
            arguments.get("message")
        )

    elif name == "get_sms_reply_summary":
        return await get_sms_reply_summary()

    elif name == "get_hot_leads":
        return await get_hot_leads()

    elif name == "get_campaign_stats":
        return await get_campaign_stats()

    elif name == "forward_message_to_phone":
        return await forward_message_to_phone(
            arguments.get("message_sid"),
            arguments.get("forward_to")
        )

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def check_sms_inbox(hours_back: int = 48):
    """Check for incoming SMS messages."""
    try:
        client = get_twilio_client()
        phone_mapping = load_phone_to_business()

        # Calculate cutoff time
        date_sent_after = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Fetch incoming messages
        messages = client.messages.list(
            to=TWILIO_NUMBER,
            date_sent_after=date_sent_after,
            limit=100
        )

        if not messages:
            return [TextContent(
                type="text",
                text=f"No incoming SMS messages in the last {hours_back} hours."
            )]

        # Process messages
        results = []
        summary = {"hot_lead": 0, "warm_lead": 0, "opt_out": 0, "unknown": 0}

        for msg in messages:
            normalized = normalize_phone(msg.from_)
            business = phone_mapping.get(normalized, "Unknown business")
            category = categorize_message(msg.body)
            summary[category] += 1

            results.append({
                "message_sid": msg.sid,
                "from": msg.from_,
                "business": business,
                "message": msg.body,
                "category": category,
                "time": str(msg.date_sent)
            })

        # Format output
        output = f"## SMS Inbox Check (Last {hours_back} hours)\n\n"
        output += f"**Total Messages:** {len(messages)}\n"
        output += f"- 🔥 Hot Leads: {summary['hot_lead']}\n"
        output += f"- ☀️ Warm Leads: {summary['warm_lead']}\n"
        output += f"- 🚫 Opt-outs: {summary['opt_out']}\n"
        output += f"- 📱 Unknown: {summary['unknown']}\n\n"

        output += "### Messages:\n\n"
        for r in results:
            emoji = {
                "hot_lead": "🔥 HOT LEAD",
                "warm_lead": "☀️ WARM LEAD",
                "opt_out": "🚫 OPT-OUT",
                "unknown": "📱 UNKNOWN"
            }.get(r["category"], "📱")

            output += f"**[{emoji}]** {r['business']}\n"
            output += f"- From: {r['from']}\n"
            output += f"- Message: {r['message'][:100]}{'...' if len(r['message']) > 100 else ''}\n"
            output += f"- Time: {r['time']}\n"
            output += f"- SID: `{r['message_sid']}`\n\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error checking inbox: {str(e)}")]


async def send_sms(to_phone: str, message: str):
    """Send an SMS message."""
    try:
        client = get_twilio_client()

        # Normalize phone
        to_phone = normalize_phone(to_phone)

        # Validate message length
        if len(message) > 1600:
            return [TextContent(
                type="text",
                text=f"Error: Message too long ({len(message)} chars). Max 1600 characters."
            )]

        # Send message
        sms = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=to_phone
        )

        output = f"## SMS Sent Successfully\n\n"
        output += f"- **To:** {to_phone}\n"
        output += f"- **From:** {TWILIO_NUMBER}\n"
        output += f"- **Status:** {sms.status}\n"
        output += f"- **SID:** `{sms.sid}`\n"
        output += f"- **Cost:** ~$0.0079\n\n"
        output += f"**Message:**\n{message}"

        return [TextContent(type="text", text=output)]

    except TwilioRestException as e:
        return [TextContent(type="text", text=f"Twilio Error: {e.msg}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def get_sms_reply_summary():
    """Get summary of SMS replies."""
    try:
        if not REPLIES_FILE.exists():
            return [TextContent(
                type="text",
                text="No replies file found. Run check_sms_inbox first."
            )]

        with open(REPLIES_FILE) as f:
            data = json.load(f)

        summary = data.get("summary", {})
        replies = data.get("replies", [])
        last_updated = data.get("last_updated", "Never")

        output = "## SMS Reply Summary\n\n"
        output += f"**Total Replies:** {summary.get('total', len(replies))}\n"
        output += f"- 🔥 Hot Leads: {summary.get('hot_leads', 0)}\n"
        output += f"- ☀️ Warm Leads: {summary.get('warm_leads', 0)}\n"
        output += f"- 🚫 Opt-outs: {summary.get('opt_outs', 0)}\n"
        output += f"- 📱 Unknown: {summary.get('unknown', 0)}\n\n"
        output += f"**Last Updated:** {last_updated}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def get_hot_leads():
    """Get list of hot leads."""
    try:
        if not REPLIES_FILE.exists():
            return [TextContent(
                type="text",
                text="No replies file found. Run check_sms_inbox first."
            )]

        with open(REPLIES_FILE) as f:
            data = json.load(f)

        replies = data.get("replies", [])
        hot_leads = [r for r in replies if r.get("category") == "hot_lead"]

        if not hot_leads:
            return [TextContent(
                type="text",
                text="No hot leads found yet. Keep sending outreach!"
            )]

        output = "## 🔥 Hot Leads\n\n"
        output += f"**{len(hot_leads)} hot lead(s) found!**\n\n"

        for lead in hot_leads:
            output += f"### {lead.get('business_name', 'Unknown')}\n"
            output += f"- **Phone:** {lead.get('from_phone')}\n"
            output += f"- **Message:** {lead.get('body')}\n"
            output += f"- **Time:** {lead.get('date_sent')}\n\n"

        output += "⚡ **Action Required:** Follow up with these leads ASAP!"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def get_campaign_stats():
    """Get campaign statistics."""
    try:
        if not CAMPAIGNS_FILE.exists():
            return [TextContent(
                type="text",
                text="No campaigns file found."
            )]

        with open(CAMPAIGNS_FILE) as f:
            data = json.load(f)

        records = data.get("records", [])
        sent_today = data.get("sent_today", {})

        # Calculate stats
        total_sent = len(records)
        unique_phones = len(sent_today)

        # Get replies count
        replies_count = 0
        if REPLIES_FILE.exists():
            with open(REPLIES_FILE) as f:
                replies_data = json.load(f)
                replies_count = len(replies_data.get("replies", []))

        response_rate = (replies_count / total_sent * 100) if total_sent > 0 else 0

        output = "## SMS Campaign Statistics\n\n"
        output += f"**Total Messages Sent:** {total_sent}\n"
        output += f"**Unique Phone Numbers:** {unique_phones}\n"
        output += f"**Total Replies:** {replies_count}\n"
        output += f"**Response Rate:** {response_rate:.1f}%\n\n"

        # Recent sends
        if records:
            output += "### Recent Sends:\n"
            for record in records[-5:]:
                output += f"- {record.get('business_name', 'Unknown')}: {record.get('status', 'sent')}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def forward_message_to_phone(message_sid: str, forward_to: str):
    """Forward a message to personal phone."""
    try:
        client = get_twilio_client()

        # Fetch the original message
        original = client.messages(message_sid).fetch()

        # Get business name
        phone_mapping = load_phone_to_business()
        normalized = normalize_phone(original.from_)
        business = phone_mapping.get(normalized, "Unknown business")
        category = categorize_message(original.body)

        emoji = {
            "hot_lead": "🔥 HOT LEAD",
            "warm_lead": "☀️ WARM LEAD",
            "opt_out": "🚫 OPT-OUT",
            "unknown": "📱 SMS"
        }.get(category, "📱")

        # Create forward message
        forward_text = (
            f"{emoji}\n"
            f"From: {original.from_}\n"
            f"Business: {business}\n"
            f"Message: {original.body}\n"
            f"---\n"
            f"Reply to: {original.from_}"
        )

        # Send forward
        forward_to = normalize_phone(forward_to)
        sms = client.messages.create(
            body=forward_text,
            from_=TWILIO_NUMBER,
            to=forward_to
        )

        return [TextContent(
            type="text",
            text=f"✓ Message forwarded to {forward_to}\n\nSID: {sms.sid}"
        )]

    except TwilioRestException as e:
        return [TextContent(type="text", text=f"Twilio Error: {e.msg}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
