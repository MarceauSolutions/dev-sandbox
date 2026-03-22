"""
Apollo.io API integration for lead enrichment and prospecting.

Apollo.io provides:
- People/company enrichment
- Email finder
- Lead database search
- Contact verification

API Documentation: https://apolloio.github.io/apollo-api-docs/

Environment Variables:
    APOLLO_API_KEY - Your Apollo.io API key
"""

import os
import time
import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ApolloConfig:
    """Apollo.io API configuration."""
    api_key: str = ""
    base_url: str = "https://api.apollo.io/v1"
    requests_per_minute: int = 50  # Apollo rate limit

    @classmethod
    def from_env(cls) -> "ApolloConfig":
        return cls(
            api_key=os.getenv("APOLLO_API_KEY", "")
        )


class ApolloClient:
    """
    Apollo.io API client for lead enrichment and prospecting.

    Key endpoints:
    - /people/match: Enrich person data
    - /organizations/enrich: Enrich company data
    - /mixed_people/api_search: Search for people
    - /mixed_companies/api_search: Search for companies
    """

    def __init__(self, config: Optional[ApolloConfig] = None):
        self.config = config or ApolloConfig.from_env()
        self.session = requests.Session()
        self.last_request_time = 0

        if not self.config.api_key:
            logger.warning("No Apollo API key found. Set APOLLO_API_KEY environment variable.")

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        min_interval = 60.0 / self.config.requests_per_minute
        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Make an API request to Apollo."""
        if not self.config.api_key:
            logger.error("Apollo API key not configured")
            return None

        self._rate_limit()

        url = f"{self.config.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.config.api_key  # Auth via header, not body
        }

        # Initialize data/params if None
        if method.upper() == "POST" and data is None:
            data = {}
        if method.upper() == "GET" and params is None:
            params = {}

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if method.upper() == "POST" else None,
                params=params if method.upper() == "GET" else None,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error: {e}")
            return None

    # ==========================================
    # ENRICHMENT ENDPOINTS
    # ==========================================

    def enrich_person(
        self,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        organization_name: str = None,
        domain: str = None,
        linkedin_url: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich a person's data using available identifiers.

        At minimum, provide one of:
        - email
        - first_name + last_name + (organization_name or domain)
        - linkedin_url

        Returns:
            Person data including email, phone, title, company info
        """
        data = {}

        if email:
            data["email"] = email
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if organization_name:
            data["organization_name"] = organization_name
        if domain:
            data["domain"] = domain
        if linkedin_url:
            data["linkedin_url"] = linkedin_url

        if not data:
            logger.error("At least one identifier required for person enrichment")
            return None

        result = self._make_request("POST", "/people/match", data)

        if result and "person" in result:
            return result["person"]
        return None

    def enrich_company(
        self,
        domain: str = None,
        name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich company data using domain or name.

        Returns:
            Company data including industry, size, revenue, technologies
        """
        data = {}

        if domain:
            data["domain"] = domain
        if name:
            data["name"] = name

        if not data:
            logger.error("Domain or name required for company enrichment")
            return None

        result = self._make_request("POST", "/organizations/enrich", data)

        if result and "organization" in result:
            return result["organization"]
        return None

    # ==========================================
    # SEARCH ENDPOINTS
    # ==========================================

    def search_people(
        self,
        person_titles: List[str] = None,
        person_locations: List[str] = None,
        organization_domains: List[str] = None,
        organization_locations: List[str] = None,
        organization_num_employees_ranges: List[str] = None,
        q_keywords: str = None,
        page: int = 1,
        per_page: int = 25
    ) -> Optional[Dict[str, Any]]:
        """
        Search Apollo's database for people matching criteria.

        Args:
            person_titles: Job titles to search (e.g., ["owner", "ceo", "manager"])
            person_locations: Locations (e.g., ["Naples, FL", "Florida"])
            organization_domains: Company domains to filter
            organization_locations: Company locations
            organization_num_employees_ranges: Size ranges (e.g., ["1,10", "11,50"])
            q_keywords: Keyword search
            page: Page number (1-indexed)
            per_page: Results per page (max 100)

        Returns:
            Dict with 'people' list and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100)
        }

        if person_titles:
            data["person_titles"] = person_titles
        if person_locations:
            data["person_locations"] = person_locations
        if organization_domains:
            data["organization_domains"] = organization_domains
        if organization_locations:
            data["organization_locations"] = organization_locations
        if organization_num_employees_ranges:
            data["organization_num_employees_ranges"] = organization_num_employees_ranges
        if q_keywords:
            data["q_keywords"] = q_keywords

        return self._make_request("POST", "/mixed_people/api_search", data)

    def search_companies(
        self,
        organization_locations: List[str] = None,
        organization_num_employees_ranges: List[str] = None,
        organization_not_technologies: List[str] = None,
        q_organization_keyword_tags: List[str] = None,
        q_keywords: str = None,
        page: int = 1,
        per_page: int = 25
    ) -> Optional[Dict[str, Any]]:
        """
        Search Apollo's database for companies matching criteria.

        Args:
            organization_locations: Locations (e.g., ["Naples, FL"])
            organization_num_employees_ranges: Size ranges
            organization_not_technologies: Exclude companies using these techs
            q_organization_keyword_tags: Industry tags
            q_keywords: Keyword search
            page: Page number
            per_page: Results per page

        Returns:
            Dict with 'organizations' list and pagination info
        """
        data = {
            "page": page,
            "per_page": min(per_page, 100)
        }

        if organization_locations:
            data["organization_locations"] = organization_locations
        if organization_num_employees_ranges:
            data["organization_num_employees_ranges"] = organization_num_employees_ranges
        if organization_not_technologies:
            data["organization_not_technologies"] = organization_not_technologies
        if q_organization_keyword_tags:
            data["q_organization_keyword_tags"] = q_organization_keyword_tags
        if q_keywords:
            data["q_keywords"] = q_keywords

        return self._make_request("POST", "/mixed_companies/api_search", data)

    # ==========================================
    # EMAIL FINDING
    # ==========================================

    def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Optional[str]:
        """
        Find a person's email given their name and company domain.

        Returns:
            Email address if found, None otherwise
        """
        result = self.enrich_person(
            first_name=first_name,
            last_name=last_name,
            domain=domain
        )

        if result and result.get("email"):
            return result["email"]
        return None

    # ==========================================
    # CONVENIENCE METHODS FOR LEAD SCRAPING
    # ==========================================

    def find_decision_makers(
        self,
        company_domain: str,
        titles: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find decision makers at a company.

        Args:
            company_domain: Company website domain
            titles: Job titles to look for (default: owner, CEO, president, founder, manager)

        Returns:
            List of people with contact info
        """
        if titles is None:
            titles = ["owner", "ceo", "president", "founder", "manager", "director"]

        result = self.search_people(
            organization_domains=[company_domain],
            person_titles=titles,
            per_page=10
        )

        if result and "people" in result:
            return result["people"]
        return []

    def search_local_businesses(
        self,
        location: str,
        industry_keywords: str = None,
        employee_range: str = "1,50",
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for local businesses in a specific location.

        Args:
            location: Location string (e.g., "Naples, FL")
            industry_keywords: Industry to search (e.g., "gym", "restaurant")
            employee_range: Size range (e.g., "1,50" for small businesses)
            max_results: Maximum results to return

        Returns:
            List of companies with contact info
        """
        all_companies = []
        page = 1
        per_page = 100

        while len(all_companies) < max_results:
            result = self.search_companies(
                organization_locations=[location],
                organization_num_employees_ranges=[employee_range],
                q_keywords=industry_keywords,
                page=page,
                per_page=per_page
            )

            if not result or "organizations" not in result:
                break

            companies = result["organizations"]
            if not companies:
                break

            all_companies.extend(companies)

            # Check if there are more pages
            pagination = result.get("pagination", {})
            if page >= pagination.get("total_pages", 1):
                break

            page += 1

        return all_companies[:max_results]


def apollo_to_lead(apollo_person: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Apollo person data to our Lead format.

    Args:
        apollo_person: Person data from Apollo API

    Returns:
        Dict matching our Lead model fields
    """
    org = apollo_person.get("organization", {}) or {}

    return {
        "business_name": org.get("name", ""),
        "address": "",  # Apollo doesn't provide full address
        "city": apollo_person.get("city", ""),
        "state": apollo_person.get("state", ""),
        "zip_code": "",
        "phone": apollo_person.get("phone_numbers", [{}])[0].get("raw_number", "") if apollo_person.get("phone_numbers") else "",
        "email": apollo_person.get("email", ""),
        "website": org.get("website_url", ""),
        "category": org.get("industry", ""),
        "rating": 0.0,
        "review_count": 0,
        "facebook": "",
        "instagram": "",
        "linkedin": apollo_person.get("linkedin_url", ""),
        "twitter": apollo_person.get("twitter_url", ""),
        "source": "apollo",
        "pain_points": [],
        "notes": f"Contact: {apollo_person.get('first_name', '')} {apollo_person.get('last_name', '')} - {apollo_person.get('title', '')}"
    }


def apollo_company_to_lead(apollo_company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Apollo company data to our Lead format.

    Args:
        apollo_company: Company data from Apollo API

    Returns:
        Dict matching our Lead model fields
    """
    return {
        "business_name": apollo_company.get("name", ""),
        "address": apollo_company.get("street_address", ""),
        "city": apollo_company.get("city", ""),
        "state": apollo_company.get("state", ""),
        "zip_code": apollo_company.get("postal_code", ""),
        "phone": apollo_company.get("phone", ""),
        "email": "",  # Company search doesn't return emails directly
        "website": apollo_company.get("website_url", ""),
        "category": apollo_company.get("industry", ""),
        "rating": 0.0,
        "review_count": 0,
        "facebook": apollo_company.get("facebook_url", ""),
        "instagram": "",
        "linkedin": apollo_company.get("linkedin_url", ""),
        "twitter": apollo_company.get("twitter_url", ""),
        "source": "apollo",
        "pain_points": [],
        "notes": f"Employees: {apollo_company.get('estimated_num_employees', 'Unknown')}"
    }
