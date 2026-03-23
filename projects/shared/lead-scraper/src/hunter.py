"""
Hunter.io email enrichment module.

Primary email discovery tool for Marceau Solutions lead pipeline.
Domain-based approach — works for any business with a website.
Native n8n node available for workflow integration.

Waterfall position: Step 2 (after contact page crawl, before Snov.io fallback)

API docs: https://hunter.io/api-documentation
Pricing: $49/mo Starter (500 searches), $104/mo Growth (5,000)
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

HUNTER_API_BASE = "https://api.hunter.io/v2"


def _get_key() -> Optional[str]:
    key = os.getenv("HUNTER_API_KEY", "").strip()
    if not key:
        logger.warning("HUNTER_API_KEY not set — Hunter enrichment skipped")
    return key or None


def domain_search(domain: str, limit: int = 5) -> list[dict]:
    """
    Find all email addresses associated with a domain.
    Returns list of {email, confidence, type, first_name, last_name, position}.
    Confidence 0-100. Use >= 50 as minimum threshold to protect sender reputation.

    Cost: 1 credit per domain search.
    """
    key = _get_key()
    if not key:
        return []

    domain = domain.lower().strip().lstrip("www.").split("/")[0]
    try:
        r = requests.get(
            f"{HUNTER_API_BASE}/domain-search",
            params={"domain": domain, "api_key": key, "limit": limit},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        emails = data.get("emails", [])
        results = []
        for e in emails:
            results.append({
                "email": e.get("value", ""),
                "confidence": e.get("confidence", 0),
                "type": e.get("type", "generic"),  # "personal" or "generic"
                "first_name": e.get("first_name", ""),
                "last_name": e.get("last_name", ""),
                "position": e.get("position", ""),
                "source": "hunter_domain",
            })
        # Sort: personal emails first, then by confidence descending
        results.sort(key=lambda x: (0 if x["type"] == "personal" else 1, -x["confidence"]))
        return results
    except requests.RequestException as e:
        logger.warning(f"Hunter domain search failed for {domain}: {e}")
        return []


def find_email(domain: str, first_name: str = "", last_name: str = "") -> Optional[dict]:
    """
    Find a specific person's email using domain + name.
    More targeted than domain_search — uses Hunter's Email Finder endpoint.
    Cost: 1 credit per call (only charged if email is found).

    Returns: {email, confidence, type, source} or None
    """
    key = _get_key()
    if not key:
        return None

    domain = domain.lower().strip().lstrip("www.").split("/")[0]
    params = {"domain": domain, "api_key": key}
    if first_name:
        params["first_name"] = first_name
    if last_name:
        params["last_name"] = last_name

    try:
        r = requests.get(
            f"{HUNTER_API_BASE}/email-finder",
            params=params,
            timeout=8,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        email = data.get("email")
        if not email:
            return None
        return {
            "email": email,
            "confidence": data.get("score", 0),
            "type": "personal" if first_name and last_name else "generic",
            "source": "hunter_finder",
        }
    except requests.RequestException as e:
        logger.warning(f"Hunter email finder failed for {domain}: {e}")
        return None


def enrich_lead(domain: str, first_name: str = "", last_name: str = "",
                min_confidence: int = 50) -> Optional[dict]:
    """
    Main enrichment entry point. Tries email finder first (more targeted),
    falls back to domain search and picks best result.

    Returns best email match or None if nothing above min_confidence.
    """
    if not domain:
        return None

    # Try targeted finder if we have a name
    if first_name or last_name:
        result = find_email(domain, first_name, last_name)
        if result and result["confidence"] >= min_confidence:
            return result

    # Fall back to domain search
    results = domain_search(domain)
    for r in results:
        if r["confidence"] >= min_confidence:
            return r

    return None


def check_credits() -> dict:
    """Check remaining Hunter API credits."""
    key = _get_key()
    if not key:
        return {"available": 0, "used": 0}
    try:
        r = requests.get(f"{HUNTER_API_BASE}/account", params={"api_key": key}, timeout=5)
        r.raise_for_status()
        data = r.json().get("data", {})
        requests_left = data.get("requests", {})
        return {
            "available": requests_left.get("available", 0),
            "used": requests_left.get("used", 0),
            "plan": data.get("plan_name", "unknown"),
        }
    except Exception:
        return {"available": 0, "used": 0}
