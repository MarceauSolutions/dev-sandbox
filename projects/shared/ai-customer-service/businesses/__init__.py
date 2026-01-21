"""Business configurations for Voice AI"""

from .squarefoot_shipping import BUSINESS_CONFIG as SQUAREFOOT_CONFIG, SYSTEM_PROMPT as SQUAREFOOT_PROMPT
from .swflorida_hvac import BUSINESS_CONFIG as HVAC_CONFIG, SYSTEM_PROMPT as HVAC_PROMPT

# Map phone numbers to business configs
BUSINESS_REGISTRY = {
    "+12398803365": {
        "config": SQUAREFOOT_CONFIG,
        "prompt": SQUAREFOOT_PROMPT
    },
    "+12397666129": {
        "config": HVAC_CONFIG,
        "prompt": HVAC_PROMPT
    }
}

def get_business_by_phone(phone_number: str):
    """Get business configuration by the phone number that was called."""
    # Normalize phone number
    clean_number = ''.join(filter(str.isdigit, phone_number))
    if not clean_number.startswith('1'):
        clean_number = '1' + clean_number
    clean_number = '+' + clean_number

    return BUSINESS_REGISTRY.get(clean_number)

def list_businesses():
    """List all configured businesses."""
    return [
        {
            "name": config["config"]["name"],
            "phone": config["config"]["phone"],
            "type": config["config"]["type"]
        }
        for config in BUSINESS_REGISTRY.values()
    ]
