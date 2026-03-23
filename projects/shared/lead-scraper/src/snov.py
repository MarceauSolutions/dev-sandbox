"""
Snov.io email enrichment module.

Fallback email discovery tool when Hunter.io returns nothing.
Also has Technology Checker — identifies CMS/tools a site uses
(useful for web dev tower: targeting businesses on Wix/Squarespace ready for custom site).

Waterfall position: Step 3 (after Hunter.io fails or returns low confidence)

API docs: https://snov.io/api
Pricing: $39/mo Starter (1,000 credits), $99/mo Pro (5,000)
1 credit = 1 email found or verified
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

SNOV_API_BASE = "https://api.snov.io/v1"


def _get_access_token() -> Optional[str]:
    """Snov uses OAuth2 client credentials flow."""
    client_id = os.getenv("SNOV_CLIENT_ID", "").strip()
    client_secret = os.getenv("SNOV_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        logger.warning("SNOV_CLIENT_ID or SNOV_CLIENT_SECRET not set — Snov enrichment skipped")
        return None
    try:
        r = requests.post(
            f"{SNOV_API_BASE}/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=8,
        )
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception as e:
        logger.warning(f"Snov.io auth failed: {e}")
        return None


def find_emails_by_domain(domain: str, token: Optional[str] = None) -> list[dict]:
    """
    Get all emails for a domain from Snov.io's database.
    Cost: 1 credit per email returned.
    Returns list of {email, first_name, last_name, position, source}.
    """
    if not token:
        token = _get_access_token()
    if not token:
        return []

    domain = domain.lower().strip().lstrip("www.").split("/")[0]
    try:
        r = requests.post(
            f"{SNOV_API_BASE}/get-domain-emails-with-info",
            data={"access_token": token, "domain": domain, "type": "personal", "limit": 5},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        emails = data.get("emails", [])
        return [
            {
                "email": e.get("email", ""),
                "first_name": e.get("firstName", ""),
                "last_name": e.get("lastName", ""),
                "position": e.get("position", ""),
                "confidence": 70,  # Snov doesn't return confidence, assume moderate
                "source": "snov_domain",
            }
            for e in emails
            if e.get("email")
        ]
    except Exception as e:
        logger.warning(f"Snov domain search failed for {domain}: {e}")
        return []


def find_email_by_name(domain: str, first_name: str, last_name: str,
                       token: Optional[str] = None) -> Optional[dict]:
    """
    Find specific person's email by name + domain.
    Cost: 1 credit if found.
    """
    if not token:
        token = _get_access_token()
    if not token:
        return None

    domain = domain.lower().strip().lstrip("www.").split("/")[0]
    try:
        r = requests.post(
            f"{SNOV_API_BASE}/get-emails-from-names",
            data={
                "access_token": token,
                "domain": domain,
                "firstName": first_name,
                "lastName": last_name,
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        emails = data.get("data", {}).get("emails", [])
        if emails:
            return {
                "email": emails[0],
                "confidence": 65,
                "source": "snov_name_finder",
            }
    except Exception as e:
        logger.warning(f"Snov name finder failed for {domain}: {e}")
    return None


def check_technology(domain: str, token: Optional[str] = None) -> list[str]:
    """
    Returns list of technologies/CMS detected on the domain's website.
    Free with Snov subscription — no credit cost.
    Useful for web dev tower: find businesses on Wix/Squarespace ready to upgrade.

    Returns e.g. ["WordPress", "WooCommerce", "Google Analytics", ...]
    """
    if not token:
        token = _get_access_token()
    if not token:
        return []

    domain = domain.lower().strip().lstrip("www.").split("/")[0]
    try:
        r = requests.post(
            f"{SNOV_API_BASE}/get-domain-technology",
            data={"access_token": token, "domain": domain},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        techs = data.get("data", {}).get("technologies", [])
        return [t.get("name", "") for t in techs if t.get("name")]
    except Exception as e:
        logger.warning(f"Snov tech check failed for {domain}: {e}")
        return []


def enrich_lead(domain: str, first_name: str = "", last_name: str = "") -> Optional[dict]:
    """
    Main Snov.io enrichment entry point (called when Hunter fails).
    Returns best email found or None.
    """
    if not domain:
        return None

    token = _get_access_token()
    if not token:
        return None

    # Try name-based finder first if name available
    if first_name and last_name:
        result = find_email_by_name(domain, first_name, last_name, token)
        if result:
            return result

    # Fall back to domain search
    results = find_emails_by_domain(domain, token)
    if results:
        return results[0]

    return None
