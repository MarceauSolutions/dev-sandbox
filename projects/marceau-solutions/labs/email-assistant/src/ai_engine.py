"""
AI Engine for MailAssist.

Uses Claude API to analyze email threads, generate documentation,
draft intelligent responses, and find relevant emails.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"


def analyze_email_thread(messages: list[dict]) -> dict:
    """
    Analyze an email thread and produce a structured summary.

    Returns: {summary, key_points, action_items, participants, timeline}
    """
    thread_text = _format_thread(messages)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this email thread and provide a structured summary.

EMAIL THREAD:
{thread_text}

Respond in this exact JSON format (no markdown, just raw JSON):
{{
    "summary": "2-3 sentence overview of what this thread is about",
    "key_points": ["point 1", "point 2", ...],
    "action_items": ["action 1", "action 2", ...],
    "participants": [
        {{"name": "Person Name", "email": "email@example.com", "role": "their role in this thread"}}
    ],
    "timeline": [
        {{"date": "date string", "event": "what happened"}}
    ],
    "sentiment": "positive/neutral/negative/escalating",
    "urgency": "low/medium/high/critical"
}}""",
            }
        ],
    )

    import json

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {
            "summary": response.content[0].text,
            "key_points": [],
            "action_items": [],
            "participants": [],
            "timeline": [],
            "sentiment": "unknown",
            "urgency": "unknown",
        }


def generate_thread_document(messages: list[dict], doc_type: str = "summary") -> str:
    """
    Generate a formatted document from an email thread.

    doc_type: 'summary' | 'timeline' | 'evidence' | 'action_plan'
    """
    thread_text = _format_thread(messages)

    prompts = {
        "summary": """Create a professional document summarizing this email thread.
Include: Overview, Key Participants, Timeline of Events, Important Decisions,
Outstanding Action Items, and Recommendations.""",
        "timeline": """Create a detailed chronological timeline document from this email thread.
For each event, include: Date/Time, Who, What happened, Any commitments made.
Format as a clean timeline with headers.""",
        "evidence": """Create an evidence documentation package from this email thread.
This is for dispute/legal purposes. Include:
- Chronological record of all communications
- Key claims and promises made by each party
- Contradictions or inconsistencies
- Financial amounts mentioned
- Deadlines mentioned and whether they were met
Format professionally with exhibit references.""",
        "action_plan": """Create an action plan based on this email thread.
Include: Current Status, What Needs to Happen Next, Who Is Responsible,
Suggested Response Strategy, Deadlines, and Risk Assessment.""",
    }

    prompt = prompts.get(doc_type, prompts["summary"])

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": f"""{prompt}

EMAIL THREAD:
{thread_text}

Format the document with clear headings, bullet points, and professional language.
Use markdown formatting.""",
            }
        ],
    )

    return response.content[0].text


def draft_response(
    messages: list[dict],
    user_intent: str,
    tone: str = "professional",
) -> dict:
    """
    Draft a response to an email thread based on user intent.

    user_intent: What the user wants to accomplish (e.g., "decline their offer",
                 "request more information about the refund process")
    tone: 'professional' | 'friendly' | 'firm' | 'apologetic'

    Returns: {subject, body, reply_to, notes}
    """
    thread_text = _format_thread(messages)
    last_msg = messages[-1] if messages else {}

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"""Draft an email response based on this thread and the user's intent.

EMAIL THREAD:
{thread_text}

USER'S INTENT: {user_intent}
DESIRED TONE: {tone}

Respond in this exact JSON format (no markdown, just raw JSON):
{{
    "subject": "Re: original subject or new subject if needed",
    "body": "The full email body text. Use proper greeting and sign-off. Write naturally.",
    "reply_to_email": "{last_msg.get('from_email', '')}",
    "notes": "Brief explanation of your approach and any suggestions for the user"
}}""",
            }
        ],
    )

    import json

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {
            "subject": f"Re: {last_msg.get('subject', '')}",
            "body": response.content[0].text,
            "reply_to_email": last_msg.get("from_email", ""),
            "notes": "Could not parse structured response — raw draft provided.",
        }


def smart_search_query(user_request: str) -> str:
    """
    Convert a natural language request into a Gmail search query.

    e.g., "find the email from my insurance company about the claim"
    → "from:insurance subject:claim"
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"""Convert this natural language email search request into a Gmail search query.
Use Gmail search operators like: from:, to:, subject:, has:attachment, after:, before:, is:unread, label:, etc.

User's request: "{user_request}"

Respond with ONLY the Gmail search query string, nothing else. Be smart about inferring
what the user means — include multiple relevant terms to find the right emails.""",
            }
        ],
    )

    return response.content[0].text.strip().strip('"').strip("'")


def _format_thread(messages: list[dict]) -> str:
    """Format a list of email messages into readable text for AI processing."""
    parts = []
    for i, msg in enumerate(messages, 1):
        parts.append(
            f"--- Email {i} ---\n"
            f"From: {msg.get('from_name', '')} <{msg.get('from_email', '')}>\n"
            f"To: {msg.get('to', '')}\n"
            f"Date: {msg.get('date', '')}\n"
            f"Subject: {msg.get('subject', '')}\n\n"
            f"{msg.get('body', '(no body)')}\n"
        )
    return "\n".join(parts)
