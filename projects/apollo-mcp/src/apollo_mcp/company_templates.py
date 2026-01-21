"""
Company-specific search templates for automated outreach campaigns.

Each company has predefined search criteria for their target markets.
"""

from typing import Dict, Any, List, Optional
import re


# Company search templates
COMPANY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "southwest_florida_comfort": {
        "name": "Southwest Florida Comfort",
        "industry": ["HVAC", "Heating & Air Conditioning", "Air Conditioning Contractor"],
        "location": "Naples, FL",
        "employee_range": "1,50",
        "titles": ["Owner", "CEO", "President", "Founder", "General Manager"],
        "excluded_titles": ["sales", "outside sales", "representative", "coordinator", "assistant"],
        "keywords": "HVAC, air conditioning, heating",
        "description": "HVAC service businesses in Southwest Florida"
    },
    "marceau_solutions": {
        "name": "Marceau Solutions",
        "industry": ["Restaurants", "Fitness", "Medical", "Professional Services", "Retail"],
        "location": "Southwest Florida",
        "employee_range": "1,50",
        "titles": ["Owner", "CEO", "Founder", "Manager"],
        "excluded_titles": ["sales", "marketing coordinator", "assistant", "intern"],
        "keywords": "small business, local business",
        "description": "Small businesses that could benefit from AI automation"
    },
    "footer_shipping": {
        "name": "Footer Shipping",
        "industry": ["E-commerce", "Retail", "Consumer Goods", "Online Retail"],
        "location": None,  # No location restriction for e-commerce
        "employee_range": "1,30",
        "titles": ["Owner", "Founder", "CEO", "Operations Manager", "E-commerce Manager"],
        "excluded_titles": ["sales", "warehouse", "driver", "picker", "packer"],
        "keywords": "e-commerce, online store, Shopify, Amazon seller",
        "description": "E-commerce businesses that need shipping optimization"
    }
}


# Default exclusions used for all searches
DEFAULT_EXCLUDED_TITLES = [
    "sales",
    "outside sales",
    "representative",
    "business development",
    "assistant",
    "intern",
    "junior",
    "coordinator"
]


def detect_company_from_prompt(prompt: str) -> Optional[str]:
    """
    Detect company context from natural language prompt.

    Args:
        prompt: Natural language prompt (e.g., "Naples HVAC for Southwest Florida Comfort")

    Returns:
        Company key or None if not detected
    """
    prompt_lower = prompt.lower()

    # Check for explicit company mentions
    if "southwest florida comfort" in prompt_lower or "swfl comfort" in prompt_lower:
        return "southwest_florida_comfort"

    if "marceau solutions" in prompt_lower or "marceau" in prompt_lower:
        return "marceau_solutions"

    if "footer shipping" in prompt_lower or "footer" in prompt_lower:
        return "footer_shipping"

    # Check for industry/context clues
    if any(keyword in prompt_lower for keyword in ["hvac", "air conditioning", "heating", "ac repair"]):
        return "southwest_florida_comfort"

    if any(keyword in prompt_lower for keyword in ["e-commerce", "shopify", "amazon seller", "online store"]):
        return "footer_shipping"

    # Default to Marceau Solutions for general small business searches
    if any(keyword in prompt_lower for keyword in ["restaurant", "gym", "fitness", "small business"]):
        return "marceau_solutions"

    return None


def get_company_template(company_key: str) -> Optional[Dict[str, Any]]:
    """
    Get search template for a company.

    Args:
        company_key: Company identifier

    Returns:
        Template dict or None if not found
    """
    return COMPANY_TEMPLATES.get(company_key)


def extract_location_from_prompt(prompt: str) -> Optional[str]:
    """
    Extract location from natural language prompt.

    Args:
        prompt: Natural language prompt

    Returns:
        Location string or None
    """
    # Pattern: "in {location}" or "{location} HVAC" etc.
    location_patterns = [
        r'\bin\s+([A-Z][a-zA-Z\s,]+(?:FL|Florida))',
        r'^([A-Z][a-zA-Z\s,]+(?:FL|Florida))\s+',
        r'([A-Z][a-zA-Z\s,]+(?:FL|Florida))\s+(?:HVAC|gym|restaurant|business)',
    ]

    for pattern in location_patterns:
        match = re.search(pattern, prompt)
        if match:
            return match.group(1).strip()

    return None


def extract_industry_from_prompt(prompt: str) -> Optional[str]:
    """
    Extract industry/keyword from natural language prompt.

    Args:
        prompt: Natural language prompt

    Returns:
        Industry keyword or None
    """
    prompt_lower = prompt.lower()

    # Common industry keywords
    industry_map = {
        "hvac": "HVAC",
        "air conditioning": "HVAC",
        "heating": "HVAC",
        "ac": "HVAC",
        "gym": "Fitness",
        "fitness": "Fitness",
        "restaurant": "Restaurants",
        "medical": "Medical",
        "dental": "Dental",
        "e-commerce": "E-commerce",
        "retail": "Retail"
    }

    for keyword, industry in industry_map.items():
        if keyword in prompt_lower:
            return industry

    return None


def build_search_params_from_template(
    template: Dict[str, Any],
    override_location: Optional[str] = None,
    override_keywords: Optional[str] = None,
    additional_exclusions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build Apollo search parameters from a company template.

    Args:
        template: Company template dict
        override_location: Override template location
        override_keywords: Override template keywords
        additional_exclusions: Additional titles to exclude

    Returns:
        Dict with search parameters ready for Apollo API
    """
    params = {}

    # Location
    location = override_location or template.get("location")
    if location:
        params["organization_locations"] = [location]

    # Employee range
    if template.get("employee_range"):
        params["organization_num_employees_ranges"] = [template["employee_range"]]

    # Keywords
    keywords = override_keywords or template.get("keywords")
    if keywords:
        params["q_keywords"] = keywords

    # Titles (for people search)
    if template.get("titles"):
        params["person_titles"] = template["titles"]

    # Excluded titles (merged with additional)
    excluded = template.get("excluded_titles", []).copy()
    if additional_exclusions:
        excluded.extend(additional_exclusions)

    # Apollo doesn't have a direct "excluded_titles" parameter
    # We'll handle this in the search_refinement module
    params["_excluded_titles"] = list(set(excluded))

    return params


def get_sms_template_name(company_key: str, pain_point: str = "no_website") -> str:
    """
    Get SMS template name for a company and pain point.

    Args:
        company_key: Company identifier
        pain_point: Pain point category

    Returns:
        Template name (e.g., "swfl_comfort_hvac_intro")
    """
    company_prefixes = {
        "southwest_florida_comfort": "swfl_comfort",
        "marceau_solutions": "marceau",
        "footer_shipping": "footer"
    }

    prefix = company_prefixes.get(company_key, company_key)
    return f"{prefix}_{pain_point}_intro"
