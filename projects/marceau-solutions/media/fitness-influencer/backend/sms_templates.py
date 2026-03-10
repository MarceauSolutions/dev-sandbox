"""
SMS Templates for Fitness Influencer Platform

Template definitions for collaborator outreach, welcome messages,
and follow-up sequences. Templates use {variable} placeholders
that get rendered by the Python layer before forwarding to n8n.
"""

TEMPLATES = {
    # --- Collaborator Outreach ---
    "collaborator_asset_request": {
        "name": "Collaborator Asset Request",
        "body": (
            "Hey {name}! I'm building an AI fitness content tool and would love "
            "to feature you. I'd need: 1) A clear headshot (front-facing, good "
            "lighting) 2) A 15-30 second voice recording 3) Your OK to use them. "
            "Interested? Just reply here!"
        ),
        "use_case": "Initial outreach to potential collaborators",
        "category": "collaborator",
    },
    "collaborator_asset_request_casual": {
        "name": "Collaborator Asset Request (Casual)",
        "body": (
            "Hey {name}! Working on something cool - an AI fitness avatar thing. "
            "Need a good headshot of you (front-facing, decent lighting), a quick "
            "voice clip (15-30 sec, just talk naturally), and your thumbs up to "
            "use them. Send whenever you can!"
        ),
        "use_case": "Outreach to friends/family collaborators",
        "category": "collaborator",
    },
    "collaborator_followup_day2": {
        "name": "Collaborator Follow-up (Day 2)",
        "body": (
            "Hey {name}, just checking in on the photo and voice clip! No rush, "
            "but wanted to make sure you saw my earlier message. Let me know if "
            "you have any questions!"
        ),
        "use_case": "Day 2-3 follow-up for asset collection",
        "category": "collaborator",
    },
    "collaborator_followup_day5": {
        "name": "Collaborator Follow-up (Day 5)",
        "body": (
            "Hey {name}, still interested in the AI fitness avatar project? "
            "Let me know either way - no pressure!"
        ),
        "use_case": "Final follow-up before closing sequence",
        "category": "collaborator",
    },

    # --- Audience / Subscriber ---
    "welcome": {
        "name": "Welcome SMS",
        "body": (
            "Hi {name}! Welcome to {brand_name} AI Fitness. "
            "We're excited to help you scale your fitness business with "
            "cutting-edge AI tools. Reply STOP to opt-out anytime."
        ),
        "use_case": "Welcome message for new SMS subscribers",
        "category": "audience",
    },
    "content_alert": {
        "name": "New Content Alert",
        "body": (
            "Hey {name}! New content just dropped: {content_title}. "
            "Check it out and let us know what you think! "
            "Reply STOP to opt-out."
        ),
        "use_case": "Notify subscribers of new content",
        "category": "audience",
    },
}

# Default brand name for template rendering
DEFAULT_BRAND_NAME = "Marceau Solutions"


def render_template(template_id: str, variables: dict) -> str:
    """Render an SMS template with the given variables.

    Args:
        template_id: Key from TEMPLATES dict
        variables: Dict of {placeholder: value} pairs

    Returns:
        Rendered message string

    Raises:
        KeyError: If template_id not found
        KeyError: If required variable missing from variables dict
    """
    if template_id not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_id}")

    template = TEMPLATES[template_id]
    body = template["body"]

    # Add default brand name if not provided
    if "brand_name" not in variables:
        variables["brand_name"] = DEFAULT_BRAND_NAME

    return body.format(**variables)


def list_templates(category: str = None) -> list:
    """List available templates, optionally filtered by category.

    Args:
        category: Filter by category (collaborator, audience, etc.)

    Returns:
        List of template info dicts
    """
    result = []
    for tid, tpl in TEMPLATES.items():
        if category and tpl.get("category") != category:
            continue
        result.append({
            "id": tid,
            "name": tpl["name"],
            "use_case": tpl["use_case"],
            "category": tpl.get("category", "general"),
            "preview": tpl["body"][:80] + "..." if len(tpl["body"]) > 80 else tpl["body"],
        })
    return result
