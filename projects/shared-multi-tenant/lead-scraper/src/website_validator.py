"""
Website Detection & Validation - FIXED VERSION

Prevents false positives where businesses with websites are incorrectly
flagged as "no_website".

ROOT CAUSE OF JAN 15 DISASTER:
- Scraper confused Yelp/Google Maps URLs with real business websites
- Example: website="https://www.yelp.com/biz/p-fit-north-naples..." marked as "has website"
- Pain point logic incorrectly added "no_website" flag
- Result: 14 angry opt-outs, reputation damage

FIX:
- Check if URL is from aggregator site (Yelp, Google Maps, Facebook, etc.)
- Only count ACTUAL business websites (custom domains)
- Return confidence score for website quality
"""

import re
from urllib.parse import urlparse
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Aggregator/directory sites that are NOT real business websites
AGGREGATOR_DOMAINS = {
    # Review/directory sites
    "yelp.com",
    "yellowpages.com",
    "whitepages.com",
    "superpages.com",
    "manta.com",
    "mapquest.com",
    "hotfrog.com",
    "brownbook.net",
    "bizapedia.com",
    "merchantcircle.com",

    # Google properties
    "google.com",
    "maps.google.com",
    "goo.gl",
    "g.co",
    "google.maps",

    # Social media (profiles, not websites)
    "facebook.com",
    "fb.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "pinterest.com",

    # Booking/scheduling platforms (not owned website)
    "mindbodyonline.com",
    "vagaro.com",
    "booker.com",
    "schedulicity.com",
    "acuityscheduling.com",
    "setmore.com",
    "appointy.com",

    # E-commerce platforms (could be real, but need verification)
    # Removed: shopify.com, square.com, wix.com, squarespace.com
    # (These could be legitimate business sites)
}


def is_real_business_website(url: Optional[str]) -> Tuple[bool, str]:
    """
    Determine if URL is a real business website (not an aggregator).

    Args:
        url: Website URL to check

    Returns:
        (is_real, reason) tuple:
            - is_real: True if legitimate business website
            - reason: Explanation of decision

    Examples:
        >>> is_real_business_website("https://www.yelp.com/biz/p-fit-naples")
        (False, "Aggregator: yelp.com")

        >>> is_real_business_website("https://pfitnaples.com")
        (True, "Custom domain: pfitnaples.com")

        >>> is_real_business_website("")
        (False, "Empty URL")
    """
    if not url or not url.strip():
        return (False, "Empty URL")

    url = url.strip()

    # Parse URL
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Check if it's an aggregator domain
        for aggregator in AGGREGATOR_DOMAINS:
            if domain == aggregator or domain.endswith(f".{aggregator}"):
                return (False, f"Aggregator: {aggregator}")

        # Check for suspicious patterns
        if "facebook.com" in url or "fb.com" in url or "fb.me" in url:
            return (False, "Social media profile (Facebook)")

        if "instagram.com" in url or "instagr.am" in url:
            return (False, "Social media profile (Instagram)")

        if "linkedin.com" in url or "lnkd.in" in url:
            return (False, "Social media profile (LinkedIn)")

        if "yelp.com" in url or "yelp.ca" in url:
            return (False, "Aggregator: Yelp")

        if "google.com/maps" in url or "goo.gl/maps" in url:
            return (False, "Google Maps listing")

        # If we get here, it's likely a real business website
        return (True, f"Custom domain: {domain}")

    except Exception as e:
        logger.warning(f"Error parsing URL '{url}': {e}")
        return (False, f"Invalid URL: {e}")


def assess_website_pain_point(lead_data: dict) -> Tuple[bool, str, int]:
    """
    Determine if lead has "no website" pain point.

    Args:
        lead_data: Dictionary with 'website' key

    Returns:
        (has_pain_point, pain_point_type, severity):
            - has_pain_point: True if business lacks proper website
            - pain_point_type: "no_website", "aggregator_only", or "none"
            - severity: 1-10 (10 = critical, 1 = minor)

    Examples:
        >>> assess_website_pain_point({"website": ""})
        (True, "no_website", 10)

        >>> assess_website_pain_point({"website": "https://yelp.com/biz/..."})
        (True, "aggregator_only", 8)

        >>> assess_website_pain_point({"website": "https://mybusiness.com"})
        (False, "none", 0)
    """
    website = lead_data.get("website", "")

    # No website at all
    if not website or not website.strip():
        return (True, "no_website", 10)

    # Check if it's a real business website
    is_real, reason = is_real_business_website(website)

    if not is_real:
        # Has URL, but it's just an aggregator
        return (True, "aggregator_only", 8)

    # Has a real business website
    return (False, "none", 0)


def validate_lead_website(lead: dict) -> dict:
    """
    Validate and enrich lead data with website analysis.

    Adds new fields:
        - has_real_website: bool
        - website_type: "custom", "aggregator", or "none"
        - website_validation_reason: str

    Updates pain_points list:
        - Adds "no_website" only if truly no website
        - Adds "aggregator_only" if only Yelp/Google Maps
        - Does NOT add if real website exists

    Args:
        lead: Lead dictionary (mutable, will be modified in-place)

    Returns:
        Modified lead dictionary
    """
    website = lead.get("website", "")

    has_pain_point, pain_type, severity = assess_website_pain_point(lead)
    is_real, reason = is_real_business_website(website)

    # Add validation fields
    lead["has_real_website"] = is_real
    lead["website_type"] = "custom" if is_real else ("aggregator" if website else "none")
    lead["website_validation_reason"] = reason

    # Update pain points list
    pain_points = lead.get("pain_points", [])

    # Remove old website-related pain points
    pain_points = [p for p in pain_points if p not in ["no_website", "aggregator_only", "outdated_website"]]

    # Add correct pain point
    if has_pain_point and pain_type != "none":
        pain_points.append(pain_type)

    lead["pain_points"] = pain_points

    logger.info(f"Website validation: {lead.get('business_name')} - {reason}")

    return lead


def batch_validate_leads(leads: list) -> list:
    """
    Validate all leads in a batch.

    Args:
        leads: List of lead dictionaries

    Returns:
        List of validated lead dictionaries
    """
    validated = []
    stats = {"real_websites": 0, "aggregator_only": 0, "no_website": 0}

    for lead in leads:
        validated_lead = validate_lead_website(lead)
        validated.append(validated_lead)

        # Track stats
        if validated_lead.get("has_real_website"):
            stats["real_websites"] += 1
        elif validated_lead.get("website"):
            stats["aggregator_only"] += 1
        else:
            stats["no_website"] += 1

    logger.info(f"Batch validation complete: {stats}")

    return validated


# Compatibility with existing codebase
def has_website(lead: dict) -> bool:
    """
    Check if lead has a REAL business website (not aggregator).

    LEGACY COMPATIBILITY: This function maintains the same signature
    as the old version, but now uses the new validation logic.

    Args:
        lead: Lead dictionary with 'website' key

    Returns:
        True if lead has real business website
    """
    is_real, _ = is_real_business_website(lead.get("website", ""))
    return is_real


if __name__ == "__main__":
    # Test cases
    import json

    test_leads = [
        {
            "business_name": "P-Fit North Naples",
            "website": "https://www.yelp.com/biz/p-fit-north-naples",
            "pain_points": []
        },
        {
            "business_name": "Velocity Indoor Cycling",
            "website": "https://velocitynaples.com",
            "pain_points": []
        },
        {
            "business_name": "CrossFit Naples",
            "website": "",
            "pain_points": []
        },
        {
            "business_name": "Galaxy Gym",
            "website": "https://facebook.com/galaxygym",
            "pain_points": []
        }
    ]

    print("Website Validation Test Results:")
    print("=" * 60)

    for lead in test_leads:
        validated = validate_lead_website(lead.copy())
        print(f"\nBusiness: {validated['business_name']}")
        print(f"  URL: {validated.get('website', 'None')}")
        print(f"  Has Real Website: {validated['has_real_website']}")
        print(f"  Type: {validated['website_type']}")
        print(f"  Reason: {validated['website_validation_reason']}")
        print(f"  Pain Points: {validated['pain_points']}")

        # Should we send "no website" message?
        should_send = "no_website" in validated["pain_points"] or "aggregator_only" in validated["pain_points"]
        print(f"  Send 'no website' message? {should_send}")
