"""Marceau Solutions - Lead Qualification Voice AI Configuration"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from lead_qualification_voice import LEAD_QUALIFICATION_SYSTEM_PROMPT

BUSINESS_CONFIG = {
    "name": "Marceau Solutions",
    "phone": "+18552399364",  # Main business line
    "owner": "William Marceau",
    "type": "ai_automation",
    "greeting": "Thank you for calling Marceau Solutions! This is our AI assistant.",

    "services": [
        {
            "name": "Voice AI Phone Systems",
            "description": "AI that answers calls 24/7, books appointments, qualifies leads",
            "ideal_for": "Gyms, restaurants, medical offices, service businesses",
            "tower": "digital-ai-services",
            "keywords": ["ai", "phone", "calls", "voice", "answer", "24/7", "appointment", "booking", "missed calls", "text back"]
        },
        {
            "name": "Lead Generation Automation",
            "description": "Automated lead scraping, enrichment, and cold outreach",
            "ideal_for": "B2B companies, agencies, sales teams",
            "tower": "digital-ai-services",
            "keywords": ["leads", "scraping", "outreach", "cold email", "prospecting", "automation", "sales"]
        },
        {
            "name": "Website + Automation Packages",
            "description": "Professional website with integrated booking/CRM automation",
            "ideal_for": "Small businesses without websites or with outdated sites",
            "tower": "digital-web-dev",
            "keywords": ["website", "web", "design", "landing page", "online", "seo", "redesign", "ecommerce"]
        },
        {
            "name": "Social Media Automation",
            "description": "AI-generated content posted automatically to X, Instagram, TikTok",
            "ideal_for": "Fitness influencers, personal brands, small businesses",
            "tower": "fitness-influencer",
            "keywords": ["social media", "content", "instagram", "tiktok", "twitter", "x", "posting", "influencer"]
        }
    ],

    "qualifying_questions": [
        "What's the biggest challenge you're facing right now?",
        "How much time are you spending on [problem] each week?",
        "What happens if you don't solve this?",
        "How soon do you need this solved?",
        "Have you looked into solutions before? What stopped you?"
    ],

    "typical_pain_points": [
        "Missing calls = missing revenue",
        "Spending too much time on repetitive tasks",
        "No website or outdated website",
        "Can't keep up with social media",
        "Lead generation is manual and slow",
        "No system for following up with leads"
    ]
}

# Tower label mapping for human-readable display
TOWER_LABELS = {
    "digital-ai-services": "AI Services (Voice AI / Lead Gen)",
    "digital-web-dev": "Web Development",
    "fitness-coaching": "Fitness Coaching",
    "fitness-influencer": "Influencer / Social Media"
}


def get_services_by_tower(tower_id: str) -> list:
    """Get all services that map to a specific tower."""
    return [s for s in BUSINESS_CONFIG["services"] if s.get("tower") == tower_id]


def get_tower_for_service(service_name: str) -> str:
    """Get the tower ID for a specific service name."""
    for s in BUSINESS_CONFIG["services"]:
        if service_name.lower() in s["name"].lower():
            return s.get("tower", "digital-ai-services")
    return "digital-ai-services"  # Default


def get_all_service_keywords() -> dict:
    """Get a mapping of tower -> all keywords for intent detection."""
    tower_keywords = {}
    for service in BUSINESS_CONFIG["services"]:
        tower = service.get("tower", "digital-ai-services")
        if tower not in tower_keywords:
            tower_keywords[tower] = []
        tower_keywords[tower].extend(service.get("keywords", []))
    return tower_keywords


# Use the lead qualification system prompt
SYSTEM_PROMPT = LEAD_QUALIFICATION_SYSTEM_PROMPT

# Override greeting to be more specific
SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    "Thank you for calling Marceau Solutions!",
    BUSINESS_CONFIG["greeting"]
)
