"""
Business-specific configuration for multi-tenant form handling.

Each business has its own:
- ClickUp list for leads
- Google Sheets spreadsheet
- Owner notification preferences
- Auto-response templates
- Nurturing sequences
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class BusinessConfig:
    """Configuration for a specific business."""

    # Identification (required)
    business_id: str
    business_name: str
    domain: str  # e.g., "swfloridacomfort.com"

    # Owner info (required)
    owner_name: str
    owner_email: str
    owner_phone: str

    # ClickUp CRM (optional)
    clickup_list_id: str = ""
    clickup_folder_id: str = ""

    # Google Sheets (optional)
    google_sheet_id: str = ""
    sheet_tab_name: str = "Form Submissions"

    # Auto-response config (optional)
    auto_response_enabled: bool = True
    auto_response_sms_template: str = ""
    auto_response_email_template: str = ""
    calendly_link: str = ""

    # Nurturing sequence (optional)
    nurturing_enabled: bool = True
    nurturing_sequence_id: str = ""

    # Branding (optional)
    logo_url: str = ""
    primary_color: str = "#000000"

    # Business relationship (optional)
    is_client_business: bool = False  # True if this is a client's business, False if owned by Marceau Solutions


# Business Registry - All configured businesses
BUSINESS_CONFIGS: Dict[str, BusinessConfig] = {

    # Marceau Solutions (main) - YOUR BUSINESS
    "marceausolutions": BusinessConfig(
        business_id="marceausolutions",
        business_name="Marceau Solutions",
        domain="marceausolutions.com",
        owner_name="William Marceau",
        owner_email="wmarceau@marceausolutions.com",
        owner_phone="+12393985676",
        clickup_list_id="901709132478",  # Main leads list
        google_sheet_id="1AgdGdTLi0E8eZLuNHDvCj2z5wLVhvNVhNBxCkNJz1Mc",
        is_client_business=False,  # This is YOUR business
        auto_response_sms_template="""Hi {name}! Thanks for reaching out to Marceau Solutions.

I received your inquiry and will get back to you within 24 hours.

- William""",
        auto_response_email_template="""Hi {name},

Thank you for contacting Marceau Solutions! I received your inquiry about {interest}.

I'll review your message and get back to you within 24 hours. In the meantime, feel free to:
- Schedule a call directly: {calendly_link}
- Reply to this email with any additional details

Best regards,
William Marceau
Marceau Solutions
""",
        calendly_link="https://calendly.com/wmarceau/30min",
    ),

    # SW Florida Comfort HVAC - FAMILY BUSINESS (William Marceau Sr.)
    "swfloridacomfort": BusinessConfig(
        business_id="swfloridacomfort",
        business_name="SW Florida Comfort HVAC",
        domain="swfloridacomfort.com",
        owner_name="William Marceau Sr.",
        owner_email="wmarceau@marceausolutions.com",  # Notifications go to you for management
        owner_phone="+12397666129",  # Business phone
        clickup_list_id="901709854724",  # HVAC Leads list
        google_sheet_id="",  # TODO: Create Google Sheet for HVAC (needs OAuth)
        is_client_business=True,  # Family business (your father's HVAC company)
        auto_response_sms_template="""Hi {name}! Thanks for contacting SW Florida Comfort HVAC.

We received your request and will call you back shortly to discuss your {service_type} needs.

For emergencies, call us directly at (239) 766-6129.

- SW Florida Comfort Team""",
        auto_response_email_template="""Hi {name},

Thank you for contacting SW Florida Comfort HVAC!

We received your inquiry about {service_type}. One of our technicians will contact you within 2 hours during business hours (8am-6pm).

For immediate assistance or emergencies, please call us at (239) 766-6129.

Best regards,
SW Florida Comfort HVAC
Serving Naples, Fort Myers, and surrounding areas
""",
        calendly_link="",  # HVAC uses phone, not Calendly
    ),

    # Square Foot Shipping & Storage - CLIENT BUSINESS (William George)
    "squarefootshipping": BusinessConfig(
        business_id="squarefootshipping",
        business_name="Square Foot Shipping & Storage",
        domain="squarefootshipping.com",
        owner_name="William George",
        owner_email="wgeorge@squarefootshipping.com",  # Goes to client owner
        owner_phone="+12397666129",  # Using HVAC phone as fallback until we get dedicated number
        clickup_list_id="901709854725",  # Square Foot Leads list
        google_sheet_id="",  # TODO: Create Google Sheet (needs OAuth)
        is_client_business=True,  # This is a CLIENT business
        auto_response_sms_template="""Hi {name}! Thanks for contacting Square Foot Shipping & Storage.

We received your request and will get back to you within 1 business day with a quote.

- Square Foot Team""",
        auto_response_email_template="""Hi {name},

Thank you for contacting Square Foot Shipping & Storage!

We received your inquiry about {service_type}. Our team will review your request and provide a quote within 1 business day.

Best regards,
Square Foot Shipping & Storage
""",
    ),
}


def get_business_config(identifier: str) -> Optional[BusinessConfig]:
    """
    Get business config by ID, domain, or source string.

    Args:
        identifier: Can be business_id, domain, or form source

    Returns:
        BusinessConfig if found, None otherwise
    """
    # Direct lookup by business_id
    if identifier in BUSINESS_CONFIGS:
        return BUSINESS_CONFIGS[identifier]

    # Lookup by domain
    for config in BUSINESS_CONFIGS.values():
        if identifier == config.domain or identifier.endswith(config.domain):
            return config

    # Lookup by form source patterns
    source_mapping = {
        "hvac": "swfloridacomfort",
        "swflorida": "swfloridacomfort",
        "squarefoot": "squarefootshipping",
        "shipping": "squarefootshipping",
        "storage": "squarefootshipping",
        "marceau": "marceausolutions",
        "fitness": "marceausolutions",
        "interview": "marceausolutions",
        "amazon": "marceausolutions",
    }

    identifier_lower = identifier.lower()
    for pattern, business_id in source_mapping.items():
        if pattern in identifier_lower:
            return BUSINESS_CONFIGS.get(business_id)

    # Default to Marceau Solutions
    return BUSINESS_CONFIGS.get("marceausolutions")


def get_all_businesses() -> Dict[str, BusinessConfig]:
    """Get all configured businesses."""
    return BUSINESS_CONFIGS.copy()
