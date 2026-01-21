"""Lead Enrichment Pipeline for Personalized Outreach.

Enriches lead data from minimal input (phone/email) to full profile
for personalized outreach campaigns.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BusinessType(Enum):
    """Business type classification."""
    RESTAURANT = "restaurant"
    GYM = "gym"
    FITNESS_STUDIO = "fitness_studio"
    FITNESS_INFLUENCER = "fitness_influencer"
    PERSONAL_TRAINER = "personal_trainer"
    RETAIL = "retail"
    MEDICAL = "medical"
    DENTAL = "dental"
    LAW = "law"
    REAL_ESTATE = "real_estate"
    SALON = "salon"
    SPA = "spa"
    AUTO = "auto"
    HVAC = "hvac"
    PLUMBING = "plumbing"
    OTHER = "other"


class ServiceType(Enum):
    """William's service offerings."""
    AI_CUSTOMER_SERVICE = "ai_customer_service"
    VOICE_AI = "voice_ai"
    FITNESS_CONTENT = "fitness_content_automation"
    BUSINESS_AUTOMATION = "business_automation"


@dataclass
class EnrichedLead:
    """Enriched lead profile for outreach."""
    phone: str
    business_name: Optional[str] = None
    business_type: Optional[BusinessType] = None
    owner_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    social_handles: list = field(default_factory=list)
    pain_points: list = field(default_factory=list)
    recommended_service: Optional[ServiceType] = None
    personalized_greeting: Optional[str] = None
    notes: Optional[str] = None

    def to_outreach_params(self) -> dict:
        """Convert to parameters for outreach_call.py."""
        return {
            "business_name": self.business_name,
            "business_type": self.business_type.value if self.business_type else None,
        }


# Service matching rules
SERVICE_MAP = {
    BusinessType.RESTAURANT: ServiceType.AI_CUSTOMER_SERVICE,
    BusinessType.GYM: ServiceType.FITNESS_CONTENT,
    BusinessType.FITNESS_STUDIO: ServiceType.FITNESS_CONTENT,
    BusinessType.FITNESS_INFLUENCER: ServiceType.FITNESS_CONTENT,
    BusinessType.PERSONAL_TRAINER: ServiceType.FITNESS_CONTENT,
    BusinessType.RETAIL: ServiceType.AI_CUSTOMER_SERVICE,
    BusinessType.MEDICAL: ServiceType.VOICE_AI,
    BusinessType.DENTAL: ServiceType.VOICE_AI,
    BusinessType.LAW: ServiceType.VOICE_AI,
    BusinessType.REAL_ESTATE: ServiceType.VOICE_AI,
    BusinessType.SALON: ServiceType.VOICE_AI,
    BusinessType.SPA: ServiceType.VOICE_AI,
    BusinessType.AUTO: ServiceType.VOICE_AI,
    BusinessType.HVAC: ServiceType.VOICE_AI,
    BusinessType.PLUMBING: ServiceType.VOICE_AI,
    BusinessType.OTHER: ServiceType.BUSINESS_AUTOMATION,
}

# Pain points by business type
PAIN_POINTS = {
    BusinessType.RESTAURANT: [
        "phone volume during rush",
        "missed calls",
        "order accuracy",
        "staff answering phones instead of serving",
    ],
    BusinessType.GYM: [
        "content creation time",
        "member engagement",
        "class scheduling",
        "social media consistency",
    ],
    BusinessType.FITNESS_STUDIO: [
        "content creation time",
        "class booking management",
        "member retention",
    ],
    BusinessType.FITNESS_INFLUENCER: [
        "video editing time",
        "posting consistency",
        "engagement growth",
        "sponsored content turnaround",
    ],
    BusinessType.PERSONAL_TRAINER: [
        "client scheduling",
        "content creation",
        "follow-up with leads",
    ],
    BusinessType.SALON: [
        "appointment booking calls",
        "no-shows",
        "after-hours inquiries",
    ],
}

# Service value propositions
VALUE_PROPS = {
    ServiceType.AI_CUSTOMER_SERVICE: "answer every call and take orders 24/7",
    ServiceType.VOICE_AI: "automate scheduling and never miss a call",
    ServiceType.FITNESS_CONTENT: "automate video editing and posting",
    ServiceType.BUSINESS_AUTOMATION: "streamline your workflows with custom AI",
}


def classify_business_type(business_name: str, context: str = None) -> BusinessType:
    """Classify business type from name and context."""
    name_lower = business_name.lower()

    # Fitness keywords
    fitness_keywords = ["fit", "gym", "fitness", "workout", "training", "crossfit", "yoga", "pilates"]
    if any(kw in name_lower for kw in fitness_keywords):
        # Check if it's a gym/studio vs influencer/trainer
        if any(x in name_lower for x in ["gym", "studio", "center", "club"]):
            return BusinessType.GYM
        return BusinessType.FITNESS_STUDIO

    # Restaurant keywords
    restaurant_keywords = ["pizza", "grill", "cafe", "restaurant", "bistro", "kitchen", "diner", "bar"]
    if any(kw in name_lower for kw in restaurant_keywords):
        return BusinessType.RESTAURANT

    # Salon/Spa keywords
    salon_keywords = ["salon", "spa", "beauty", "hair", "nails", "barber"]
    if any(kw in name_lower for kw in salon_keywords):
        if "spa" in name_lower:
            return BusinessType.SPA
        return BusinessType.SALON

    # Medical/Dental
    medical_keywords = ["medical", "clinic", "health", "doctor", "physician"]
    if any(kw in name_lower for kw in medical_keywords):
        return BusinessType.MEDICAL

    dental_keywords = ["dental", "dentist", "orthodont"]
    if any(kw in name_lower for kw in dental_keywords):
        return BusinessType.DENTAL

    # Auto
    auto_keywords = ["auto", "car", "motor", "tire", "mechanic"]
    if any(kw in name_lower for kw in auto_keywords):
        return BusinessType.AUTO

    # Use context if provided
    if context:
        context_lower = context.lower()
        if "fitness" in context_lower or "trainer" in context_lower:
            return BusinessType.FITNESS_STUDIO

    return BusinessType.OTHER


def match_service(business_type: BusinessType, signals: dict = None) -> ServiceType:
    """Match business to best service offering."""
    signals = signals or {}

    # Check signals for override
    if signals.get("creates_content") and business_type in [
        BusinessType.GYM, BusinessType.FITNESS_STUDIO,
        BusinessType.FITNESS_INFLUENCER, BusinessType.PERSONAL_TRAINER
    ]:
        return ServiceType.FITNESS_CONTENT

    if signals.get("has_high_phone_volume"):
        return ServiceType.AI_CUSTOMER_SERVICE

    if signals.get("has_appointments"):
        return ServiceType.VOICE_AI

    # Default to type map
    return SERVICE_MAP.get(business_type, ServiceType.BUSINESS_AUTOMATION)


def generate_greeting(lead: EnrichedLead) -> str:
    """Generate personalized greeting for outreach call."""
    service = lead.recommended_service or ServiceType.BUSINESS_AUTOMATION
    value_prop = VALUE_PROPS.get(service, "help streamline your business")

    if lead.business_name and lead.business_type:
        type_friendly = lead.business_type.value.replace("_", " ")
        return (
            f"Hi! This is an AI assistant calling on behalf of William Marceau. "
            f"He noticed {lead.business_name} and wanted to reach out to see if "
            f"you might be interested in any AI services for your {type_friendly} business. "
            f"Things like {value_prop}. Do you have a moment to chat?"
        )
    elif lead.business_name:
        return (
            f"Hi! This is an AI assistant calling on behalf of William Marceau. "
            f"He noticed {lead.business_name} and wanted to reach out to see if "
            f"you might be interested in any AI consulting services. "
            f"Do you have a moment to chat?"
        )
    else:
        return (
            "Hi! This is an AI assistant calling on behalf of William Marceau. "
            "He wanted to reach out and see if you might be interested in any "
            "AI consulting services for your business. Do you have a moment to chat?"
        )


def enrich_lead(
    phone: str,
    business_name: str = None,
    business_type: str = None,
    context: str = None
) -> EnrichedLead:
    """
    Enrich a lead with available data.

    Args:
        phone: Phone number (required)
        business_name: Known business name (optional)
        business_type: Known business type (optional)
        context: Additional context (optional)

    Returns:
        EnrichedLead with matched service and greeting
    """
    lead = EnrichedLead(phone=phone)

    # Set business name if provided
    if business_name:
        lead.business_name = business_name

        # Classify business type if not provided
        if business_type:
            # Try to match to enum
            try:
                lead.business_type = BusinessType(business_type.lower())
            except ValueError:
                lead.business_type = classify_business_type(business_name, context)
        else:
            lead.business_type = classify_business_type(business_name, context)

    # Match service
    if lead.business_type:
        lead.recommended_service = match_service(lead.business_type)
        lead.pain_points = PAIN_POINTS.get(lead.business_type, [])

    # Generate personalized greeting
    lead.personalized_greeting = generate_greeting(lead)

    return lead


if __name__ == "__main__":
    # Test enrichment
    lead = enrich_lead(
        phone="+12393984852",
        business_name="Boab Fit",
        business_type="fitness"
    )

    print(f"Business: {lead.business_name}")
    print(f"Type: {lead.business_type}")
    print(f"Service: {lead.recommended_service}")
    print(f"Pain Points: {lead.pain_points}")
    print(f"\nGreeting:\n{lead.personalized_greeting}")
