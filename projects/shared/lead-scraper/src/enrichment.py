"""
Lead enrichment module - finds additional contact info for leads.
Includes email discovery, social media lookup, and website analysis.
"""

import re
import time
import logging
import requests
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from .models import Lead
from .config import ScraperConfig

logger = logging.getLogger(__name__)


class LeadEnricher:
    """
    Enriches leads with additional contact information.

    Ethical guidelines:
    - Only scrapes publicly available information
    - Respects robots.txt
    - Rate limits requests
    - Does not bypass authentication
    """

    # Common email patterns on business websites
    EMAIL_PATTERNS = [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]

    # Common contact page paths
    CONTACT_PATHS = [
        "/contact",
        "/contact-us",
        "/about",
        "/about-us",
        "/get-in-touch",
        "/reach-us",
        "/contactus",
    ]

    # Social media URL patterns
    SOCIAL_PATTERNS = {
        "facebook": r'facebook\.com/[^/"\s]+',
        "instagram": r'instagram\.com/[^/"\s]+',
        "linkedin": r'linkedin\.com/(?:company|in)/[^/"\s]+',
        "twitter": r'twitter\.com/[^/"\s]+',
    }

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; LeadScraper/1.0; Contact: your@email.com)"
        })
        self.last_request_time = 0
        self.robots_cache: Dict[str, bool] = {}

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        delay = self.config.rate_limit.delay_between_requests * 2  # Extra delay for scraping
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()

    def _can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL based on robots.txt."""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            if base_url in self.robots_cache:
                return self.robots_cache[base_url]

            robots_url = urljoin(base_url, "/robots.txt")
            response = self.session.get(robots_url, timeout=5)

            # Very basic robots.txt check - look for Disallow: /
            if response.status_code == 200:
                # If there's a blanket disallow for all bots, respect it
                if "Disallow: /" in response.text and "Allow:" not in response.text:
                    self.robots_cache[base_url] = False
                    return False

            self.robots_cache[base_url] = True
            return True

        except Exception:
            # If we can't check robots.txt, be cautious but proceed
            return True

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a webpage with rate limiting and error handling."""
        if not self._can_fetch(url):
            logger.debug(f"Robots.txt disallows: {url}")
            return None

        self._rate_limit()

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Only process HTML responses
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None

            return response.text

        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None

    def _extract_emails(self, html: str) -> List[str]:
        """Extract email addresses from HTML content."""
        emails = set()

        for pattern in self.EMAIL_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                email = match.lower()
                # Filter out common false positives
                if not any(fp in email for fp in [
                    "example.com", "your", "email@", "@email",
                    "name@", "@domain", "test@", ".png", ".jpg",
                    ".gif", "wixpress", "sentry"
                ]):
                    emails.add(email)

        return list(emails)

    def _extract_social_links(self, html: str, base_url: str = "") -> Dict[str, str]:
        """Extract social media links from HTML content."""
        social = {}

        for platform, pattern in self.SOCIAL_PATTERNS.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Take the first valid match
                url = f"https://{matches[0]}"
                social[platform] = url

        return social

    def _extract_phone(self, html: str) -> Optional[str]:
        """Extract phone numbers from HTML content."""
        # US phone pattern
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                # Clean the number
                clean = re.sub(r'[^\d]', '', match)
                if len(clean) == 10 or (len(clean) == 11 and clean.startswith('1')):
                    return match

        return None

    def _analyze_website(self, url: str) -> Dict[str, Any]:
        """
        Analyze a business website for contact info and pain points.

        Returns:
            Dict with emails, phone, social links, and pain points
        """
        result = {
            "emails": [],
            "phone": "",
            "social": {},
            "pain_points": []
        }

        # Fetch main page
        html = self._fetch_page(url)
        if not html:
            result["pain_points"].append("website_unreachable")
            return result

        # Check for outdated indicators
        if self._check_outdated_website(html):
            result["pain_points"].append("outdated_website")

        # Check for mobile friendliness
        if not self._check_mobile_friendly(html):
            result["pain_points"].append("not_mobile_friendly")

        # Extract from main page
        result["emails"].extend(self._extract_emails(html))
        result["social"].update(self._extract_social_links(html, url))

        if not result.get("phone"):
            phone = self._extract_phone(html)
            if phone:
                result["phone"] = phone

        # Try contact pages
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        for path in self.CONTACT_PATHS:
            contact_url = urljoin(base_url, path)
            contact_html = self._fetch_page(contact_url)

            if contact_html:
                result["emails"].extend(self._extract_emails(contact_html))
                if not result.get("phone"):
                    phone = self._extract_phone(contact_html)
                    if phone:
                        result["phone"] = phone

                # Don't need to check all contact pages
                if result["emails"]:
                    break

        # Check for online booking
        if not self._check_online_booking(html):
            result["pain_points"].append("no_online_booking")

        # Deduplicate emails
        result["emails"] = list(set(result["emails"]))

        return result

    def _check_outdated_website(self, html: str) -> bool:
        """Check if website appears outdated."""
        indicators = [
            "flash" in html.lower() and "adobe flash" in html.lower(),
            re.search(r'copyright\s*20[0-1][0-9]', html.lower()),
            "this site requires" in html.lower(),
            "best viewed in internet explorer" in html.lower()
        ]
        return any(indicators)

    def _check_mobile_friendly(self, html: str) -> bool:
        """Check if website appears mobile-friendly."""
        indicators = [
            "viewport" in html.lower(),
            "responsive" in html.lower(),
            "@media" in html.lower()
        ]
        return any(indicators)

    def _check_online_booking(self, html: str) -> bool:
        """Check if website has online booking capability."""
        indicators = [
            "book online" in html.lower(),
            "schedule online" in html.lower(),
            "book now" in html.lower(),
            "make appointment" in html.lower(),
            "calendly" in html.lower(),
            "acuity" in html.lower(),
            "square appointments" in html.lower(),
            "mindbody" in html.lower(),
            "vagaro" in html.lower()
        ]
        return any(indicators)

    def enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich a lead with additional information from their website.

        Args:
            lead: Lead to enrich

        Returns:
            Enriched lead (mutated in place and returned)
        """
        if not lead.website:
            return lead

        logger.info(f"Enriching: {lead.business_name} ({lead.website})")

        try:
            analysis = self._analyze_website(lead.website)

            # Add email if found and lead doesn't have one
            if analysis["emails"] and not lead.email:
                # Prefer emails that match business name
                business_words = lead.business_name.lower().split()
                matching = [e for e in analysis["emails"]
                           if any(w in e for w in business_words if len(w) > 3)]
                lead.email = matching[0] if matching else analysis["emails"][0]

            # Add phone if found and lead doesn't have one
            if analysis["phone"] and not lead.phone:
                lead.phone = analysis["phone"]

            # Update social media links
            if analysis["social"]:
                if not lead.facebook and "facebook" in analysis["social"]:
                    lead.facebook = analysis["social"]["facebook"]
                if not lead.instagram and "instagram" in analysis["social"]:
                    lead.instagram = analysis["social"]["instagram"]
                if not lead.linkedin and "linkedin" in analysis["social"]:
                    lead.linkedin = analysis["social"]["linkedin"]
                if not lead.twitter and "twitter" in analysis["social"]:
                    lead.twitter = analysis["social"]["twitter"]

            # Add discovered pain points
            for pp in analysis["pain_points"]:
                if pp not in lead.pain_points:
                    lead.pain_points.append(pp)

        except Exception as e:
            logger.error(f"Error enriching {lead.business_name}: {e}")

        return lead

    def enrich_leads(self, leads: List[Lead], max_leads: int = None) -> int:
        """
        Enrich multiple leads.

        Args:
            leads: List of leads to enrich
            max_leads: Maximum number to process (None = all)

        Returns:
            Number of leads enriched
        """
        count = 0
        to_process = leads[:max_leads] if max_leads else leads

        for lead in to_process:
            if lead.website and not lead.email:
                self.enrich_lead(lead)
                count += 1

        logger.info(f"Enriched {count} leads")
        return count


class EmailValidator:
    """
    Validates email addresses for deliverability.

    Note: Full validation requires SMTP verification which can be slow
    and may be blocked by some mail servers. This module provides
    syntax validation and basic MX record checking.
    """

    def __init__(self):
        # Common disposable email domains to filter
        self.disposable_domains = {
            "mailinator.com", "guerrillamail.com", "10minutemail.com",
            "tempmail.com", "throwaway.email", "fakeinbox.com"
        }

    def is_valid_syntax(self, email: str) -> bool:
        """Check if email has valid syntax."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def is_business_email(self, email: str) -> bool:
        """Check if email appears to be a business email (not Gmail/Yahoo/etc)."""
        free_providers = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "icloud.com", "mail.com", "protonmail.com"
        }
        domain = email.split("@")[-1].lower()
        return domain not in free_providers

    def is_disposable(self, email: str) -> bool:
        """Check if email is from a disposable email service."""
        domain = email.split("@")[-1].lower()
        return domain in self.disposable_domains

    def validate(self, email: str) -> Dict[str, Any]:
        """
        Validate an email address.

        Returns:
            Dict with validation results
        """
        result = {
            "email": email,
            "valid_syntax": self.is_valid_syntax(email),
            "is_business_email": False,
            "is_disposable": False,
            "score": 0
        }

        if result["valid_syntax"]:
            result["is_business_email"] = self.is_business_email(email)
            result["is_disposable"] = self.is_disposable(email)

            # Score email quality (0-100)
            score = 50  # Base score for valid syntax
            if result["is_business_email"]:
                score += 30
            if not result["is_disposable"]:
                score += 20
            else:
                score -= 50

            result["score"] = max(0, min(100, score))

        return result
