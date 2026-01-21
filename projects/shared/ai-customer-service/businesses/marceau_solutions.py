"""Marceau Solutions - Lead Qualification Voice AI Configuration"""

from ..src.lead_qualification_voice import LEAD_QUALIFICATION_SYSTEM_PROMPT

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
            "ideal_for": "Gyms, restaurants, medical offices, service businesses"
        },
        {
            "name": "Lead Generation Automation",
            "description": "Automated lead scraping, enrichment, and cold outreach",
            "ideal_for": "B2B companies, agencies, sales teams"
        },
        {
            "name": "Website + Automation Packages",
            "description": "Professional website with integrated booking/CRM automation",
            "ideal_for": "Small businesses without websites or with outdated sites"
        },
        {
            "name": "Social Media Automation",
            "description": "AI-generated content posted automatically to X, Instagram, TikTok",
            "ideal_for": "Fitness influencers, personal brands, small businesses"
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

# Use the lead qualification system prompt
SYSTEM_PROMPT = LEAD_QUALIFICATION_SYSTEM_PROMPT

# Override greeting to be more specific
SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    "Thank you for calling Marceau Solutions!",
    BUSINESS_CONFIG["greeting"]
)
