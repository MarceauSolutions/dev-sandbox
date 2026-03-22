"""
Apollo.io API integration for lead enrichment and prospecting.

Apollo.io provides:
- People/company enrichment
- Email finder
- Lead database search
- Contact verification

API Documentation: https://docs.apollo.io/

Environment Variables:
    APOLLO_API_KEY - Your Apollo.io API key

Enhanced Features (2026-01-21):
- Full search filter support (seniority, email status, phone, departments, etc.)
- Search profile templates for reusable configurations
- Organization search with revenue, funding, technology filters
"""

import os
import time
import logging
import requests
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS FOR TYPE SAFETY
# =============================================================================

class Seniority(str, Enum):
    """Apollo seniority levels for person_seniorities filter."""
    OWNER = "owner"
    FOUNDER = "founder"
    C_SUITE = "c_suite"
    PARTNER = "partner"
    VP = "vp"
    HEAD = "head"
    DIRECTOR = "director"
    MANAGER = "manager"
    SENIOR = "senior"
    ENTRY = "entry"
    INTERN = "intern"


class EmailStatus(str, Enum):
    """Apollo email verification status for contact_email_status filter."""
    VERIFIED = "verified"
    GUESSED = "guessed"
    UNAVAILABLE = "unavailable"
    BOUNCED = "bounced"
    PENDING = "pending"


class Department(str, Enum):
    """Apollo department filters."""
    SALES = "sales"
    MARKETING = "marketing"
    ENGINEERING = "engineering"
    FINANCE = "finance"
    HR = "human_resources"
    OPERATIONS = "operations"
    IT = "information_technology"
    LEGAL = "legal"
    CUSTOMER_SERVICE = "customer_service"
    EXECUTIVE = "executive"


class EmployeeRange(str, Enum):
    """Apollo employee count ranges for organization_num_employees_ranges."""
    SOLO = "1,1"
    MICRO = "1,10"
    SMALL = "11,50"
    MEDIUM = "51,200"
    LARGE = "201,500"
    ENTERPRISE = "501,1000"
    MEGA = "1001,5000"
    MASSIVE = "5001,10000"
    HUGE = "10001,"


class RevenueRange(str, Enum):
    """Apollo revenue ranges."""
    UNDER_1M = "0,1000000"
    R_1M_10M = "1000000,10000000"
    R_10M_50M = "10000000,50000000"
    R_50M_100M = "50000000,100000000"
    R_100M_500M = "100000000,500000000"
    R_500M_1B = "500000000,1000000000"
    OVER_1B = "1000000000,"


# =============================================================================
# SEARCH FILTER DATACLASSES
# =============================================================================

@dataclass
class PeopleSearchFilters:
    """
    Complete filter options for Apollo People Search API.

    All filters are optional. Only non-None values are sent to the API.

    Example:
        filters = PeopleSearchFilters(
            person_titles=["owner", "ceo", "founder"],
            person_seniorities=[Seniority.OWNER, Seniority.C_SUITE],
            person_locations=["Naples, FL"],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            contact_email_status=[EmailStatus.VERIFIED],
            currently_using_any_of_technology_uids=None,  # Exclude tech filter
        )
    """
    # Person filters
    person_titles: Optional[List[str]] = None
    person_not_titles: Optional[List[str]] = None  # Exclude these titles
    person_seniorities: Optional[List[Seniority]] = None
    person_locations: Optional[List[str]] = None
    person_departments: Optional[List[Department]] = None

    # Contact quality filters
    contact_email_status: Optional[List[EmailStatus]] = None
    has_email: Optional[bool] = None  # Only contacts with email
    has_phone: Optional[bool] = None  # Only contacts with phone (mobile or direct)

    # Organization filters
    organization_locations: Optional[List[str]] = None
    organization_domains: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    organization_num_employees_ranges: Optional[List[EmployeeRange]] = None
    organization_not_locations: Optional[List[str]] = None

    # Industry/keyword filters
    q_keywords: Optional[str] = None
    q_organization_keyword_tags: Optional[List[str]] = None  # Industry tags

    # Technology filters
    currently_using_any_of_technology_uids: Optional[List[str]] = None
    not_using_any_of_technology_uids: Optional[List[str]] = None

    # Revenue/funding filters (organization level)
    revenue_range: Optional[RevenueRange] = None

    # Prospecting filters (for existing contacts)
    prospected_by_current_team: Optional[bool] = None
    revealed_for_current_team: Optional[bool] = None

    # Pagination
    page: int = 1
    per_page: int = 25  # Max 100

    def to_api_params(self) -> Dict[str, Any]:
        """Convert filters to Apollo API parameters."""
        params = {
            "page": self.page,
            "per_page": min(self.per_page, 100)
        }

        # Person filters
        if self.person_titles:
            params["person_titles"] = self.person_titles
        if self.person_not_titles:
            params["person_not_titles"] = self.person_not_titles
        if self.person_seniorities:
            params["person_seniorities"] = [s.value for s in self.person_seniorities]
        if self.person_locations:
            params["person_locations"] = self.person_locations
        if self.person_departments:
            params["person_departments"] = [d.value for d in self.person_departments]

        # Contact quality filters
        if self.contact_email_status:
            params["contact_email_status"] = [e.value for e in self.contact_email_status]

        # Organization filters
        if self.organization_locations:
            params["organization_locations"] = self.organization_locations
        if self.organization_domains:
            params["organization_domains"] = self.organization_domains
        if self.organization_ids:
            params["organization_ids"] = self.organization_ids
        if self.organization_num_employees_ranges:
            params["organization_num_employees_ranges"] = [
                r.value for r in self.organization_num_employees_ranges
            ]
        if self.organization_not_locations:
            params["organization_not_locations"] = self.organization_not_locations

        # Industry/keyword filters
        if self.q_keywords:
            params["q_keywords"] = self.q_keywords
        if self.q_organization_keyword_tags:
            params["q_organization_keyword_tags"] = self.q_organization_keyword_tags

        # Technology filters
        if self.currently_using_any_of_technology_uids:
            params["currently_using_any_of_technology_uids"] = self.currently_using_any_of_technology_uids
        if self.not_using_any_of_technology_uids:
            params["not_using_any_of_technology_uids"] = self.not_using_any_of_technology_uids

        # Revenue filter
        if self.revenue_range:
            params["organization_revenue_ranges"] = [self.revenue_range.value]

        # Prospecting filters
        if self.prospected_by_current_team is not None:
            params["prospected_by_current_team"] = self.prospected_by_current_team
        if self.revealed_for_current_team is not None:
            params["revealed_for_current_team"] = self.revealed_for_current_team

        return params


@dataclass
class OrganizationSearchFilters:
    """
    Complete filter options for Apollo Organization Search API.

    Example:
        filters = OrganizationSearchFilters(
            organization_locations=["Naples, FL", "Fort Myers, FL"],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            q_organization_keyword_tags=["fitness", "gym", "health club"],
            organization_not_technologies=["shopify"],  # Not using Shopify
        )
    """
    # Location filters
    organization_locations: Optional[List[str]] = None
    organization_not_locations: Optional[List[str]] = None

    # Size filters
    organization_num_employees_ranges: Optional[List[EmployeeRange]] = None

    # Revenue filters
    revenue_range: Optional[RevenueRange] = None

    # Industry/keyword filters
    q_keywords: Optional[str] = None
    q_organization_keyword_tags: Optional[List[str]] = None

    # Technology filters
    organization_technologies: Optional[List[str]] = None  # Using these
    organization_not_technologies: Optional[List[str]] = None  # NOT using these

    # Funding filters
    organization_latest_funding_stage_cd: Optional[List[str]] = None  # seed, series_a, etc.

    # Founded year
    organization_founded_year_min: Optional[int] = None
    organization_founded_year_max: Optional[int] = None

    # Pagination
    page: int = 1
    per_page: int = 25  # Max 100

    def to_api_params(self) -> Dict[str, Any]:
        """Convert filters to Apollo API parameters."""
        params = {
            "page": self.page,
            "per_page": min(self.per_page, 100)
        }

        if self.organization_locations:
            params["organization_locations"] = self.organization_locations
        if self.organization_not_locations:
            params["organization_not_locations"] = self.organization_not_locations
        if self.organization_num_employees_ranges:
            params["organization_num_employees_ranges"] = [
                r.value for r in self.organization_num_employees_ranges
            ]
        if self.revenue_range:
            params["organization_revenue_ranges"] = [self.revenue_range.value]
        if self.q_keywords:
            params["q_keywords"] = self.q_keywords
        if self.q_organization_keyword_tags:
            params["q_organization_keyword_tags"] = self.q_organization_keyword_tags
        if self.organization_technologies:
            params["organization_technologies"] = self.organization_technologies
        if self.organization_not_technologies:
            params["organization_not_technologies"] = self.organization_not_technologies
        if self.organization_latest_funding_stage_cd:
            params["organization_latest_funding_stage_cd"] = self.organization_latest_funding_stage_cd
        if self.organization_founded_year_min:
            params["organization_founded_year_min"] = self.organization_founded_year_min
        if self.organization_founded_year_max:
            params["organization_founded_year_max"] = self.organization_founded_year_max

        return params


# =============================================================================
# SEARCH PROFILE TEMPLATES
# =============================================================================

class SearchProfiles:
    """
    Pre-built search profile templates for common use cases.

    Usage:
        from src.apollo import SearchProfiles, ApolloClient

        client = ApolloClient()

        # Use a preset profile
        filters = SearchProfiles.small_business_owners("Naples, FL", "gym")
        results = client.search_people_advanced(filters)

        # Or customize a profile
        filters = SearchProfiles.small_business_owners("Naples, FL", "hvac")
        filters.contact_email_status = [EmailStatus.VERIFIED]  # Add verified email filter
        results = client.search_people_advanced(filters)
    """

    @staticmethod
    def small_business_owners(
        location: str,
        industry_keyword: str = None
    ) -> PeopleSearchFilters:
        """
        Find small business owners/decision-makers.

        - Seniorities: owner, founder, c_suite
        - Employee range: 1-50
        - Location: specified
        - Optional: industry keyword
        """
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
            person_locations=[location],
            organization_num_employees_ranges=[EmployeeRange.SOLO, EmployeeRange.MICRO, EmployeeRange.SMALL],
            q_keywords=industry_keyword,
            per_page=100
        )

    @staticmethod
    def verified_contacts_only(
        location: str,
        industry_keyword: str = None
    ) -> PeopleSearchFilters:
        """
        Find contacts with VERIFIED email only.

        Best for cold email campaigns where deliverability matters.
        """
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE, Seniority.MANAGER],
            person_locations=[location],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            contact_email_status=[EmailStatus.VERIFIED],
            q_keywords=industry_keyword,
            per_page=100
        )

    @staticmethod
    def decision_makers_all_sizes(
        location: str,
        titles: List[str] = None
    ) -> PeopleSearchFilters:
        """
        Find decision-makers at companies of all sizes.

        Good for B2B sales prospecting.
        """
        default_titles = ["owner", "ceo", "president", "founder", "partner", "director", "manager"]
        return PeopleSearchFilters(
            person_titles=titles or default_titles,
            person_seniorities=[
                Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE,
                Seniority.VP, Seniority.DIRECTOR, Seniority.MANAGER
            ],
            person_locations=[location],
            per_page=100
        )

    @staticmethod
    def local_service_businesses(
        location: str,
        industry_tags: List[str] = None
    ) -> PeopleSearchFilters:
        """
        Find local service businesses (HVAC, plumbing, contractors, etc.).

        Optimized for:
        - Small teams (1-50 employees)
        - Service industry keywords
        - Decision-makers only
        """
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
            person_locations=[location],
            organization_num_employees_ranges=[EmployeeRange.SOLO, EmployeeRange.MICRO, EmployeeRange.SMALL],
            q_organization_keyword_tags=industry_tags,
            per_page=100
        )

    @staticmethod
    def no_tech_stack(
        location: str,
        exclude_technologies: List[str] = None
    ) -> PeopleSearchFilters:
        """
        Find businesses NOT using specific technologies.

        Example: Find businesses without a website builder (opportunity for web services).
        Common exclude_technologies: ["wordpress", "wix", "squarespace", "shopify"]
        """
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
            person_locations=[location],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            not_using_any_of_technology_uids=exclude_technologies,
            per_page=100
        )

    @staticmethod
    def naples_gyms() -> PeopleSearchFilters:
        """Pre-configured: Naples FL gyms/fitness businesses."""
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE, Seniority.MANAGER],
            person_locations=["Naples, FL", "Naples, Florida"],
            organization_locations=["Naples, FL", "Naples, Florida", "Collier County, FL"],
            organization_num_employees_ranges=[EmployeeRange.SOLO, EmployeeRange.MICRO, EmployeeRange.SMALL],
            q_keywords="gym fitness health club personal training",
            q_organization_keyword_tags=["fitness", "gym", "health club", "personal training"],
            per_page=100
        )

    @staticmethod
    def naples_hvac() -> PeopleSearchFilters:
        """Pre-configured: Naples FL HVAC businesses."""
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE],
            person_locations=["Naples, FL", "Naples, Florida", "Fort Myers, FL"],
            organization_locations=["Naples, FL", "Fort Myers, FL", "Collier County, FL", "Lee County, FL"],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL, EmployeeRange.MEDIUM],
            q_keywords="hvac air conditioning heating cooling",
            q_organization_keyword_tags=["hvac", "air conditioning", "heating", "cooling", "contractor"],
            per_page=100
        )

    @staticmethod
    def naples_restaurants() -> PeopleSearchFilters:
        """Pre-configured: Naples FL restaurants."""
        return PeopleSearchFilters(
            person_seniorities=[Seniority.OWNER, Seniority.FOUNDER, Seniority.C_SUITE, Seniority.MANAGER],
            person_locations=["Naples, FL", "Naples, Florida"],
            organization_locations=["Naples, FL", "Naples, Florida"],
            organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
            q_keywords="restaurant bar cafe dining",
            q_organization_keyword_tags=["restaurant", "food service", "dining", "hospitality"],
            per_page=100
        )


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
    - /mixed_people/api_search: Search for people (API endpoint)
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
            "X-Api-Key": self.config.api_key  # Apollo requires key in header
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

    # ==========================================
    # ADVANCED SEARCH (FULL FILTER SUPPORT)
    # ==========================================

    def search_people_advanced(
        self,
        filters: PeopleSearchFilters
    ) -> Optional[Dict[str, Any]]:
        """
        Search for people using the full set of Apollo filters.

        This is the recommended method for production searches as it
        exposes all filtering capabilities.

        Args:
            filters: PeopleSearchFilters instance with search criteria

        Returns:
            Dict with 'people' list and pagination info

        Example:
            from src.apollo import ApolloClient, PeopleSearchFilters, Seniority, EmailStatus, EmployeeRange

            client = ApolloClient()

            # Custom search with all filters
            filters = PeopleSearchFilters(
                person_seniorities=[Seniority.OWNER, Seniority.FOUNDER],
                person_locations=["Naples, FL"],
                organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
                contact_email_status=[EmailStatus.VERIFIED],
                q_keywords="gym fitness",
                per_page=100
            )
            results = client.search_people_advanced(filters)

            # Or use a preset profile
            from src.apollo import SearchProfiles
            filters = SearchProfiles.naples_gyms()
            results = client.search_people_advanced(filters)
        """
        data = filters.to_api_params()
        logger.info(f"Apollo advanced people search with {len(data)} filters")
        return self._make_request("POST", "/mixed_people/api_search", data)

    def search_organizations_advanced(
        self,
        filters: OrganizationSearchFilters
    ) -> Optional[Dict[str, Any]]:
        """
        Search for organizations using the full set of Apollo filters.

        Args:
            filters: OrganizationSearchFilters instance with search criteria

        Returns:
            Dict with 'organizations' list and pagination info

        Example:
            from src.apollo import ApolloClient, OrganizationSearchFilters, EmployeeRange

            client = ApolloClient()
            filters = OrganizationSearchFilters(
                organization_locations=["Naples, FL"],
                organization_num_employees_ranges=[EmployeeRange.MICRO, EmployeeRange.SMALL],
                q_organization_keyword_tags=["gym", "fitness"],
                organization_not_technologies=["shopify"]  # Not using Shopify
            )
            results = client.search_organizations_advanced(filters)
        """
        data = filters.to_api_params()
        logger.info(f"Apollo advanced organization search with {len(data)} filters")
        return self._make_request("POST", "/mixed_companies/api_search", data)

    def search_with_profile(
        self,
        profile_name: str,
        location: str = None,
        industry_keyword: str = None,
        **overrides
    ) -> Optional[Dict[str, Any]]:
        """
        Search using a named profile from SearchProfiles.

        Args:
            profile_name: One of: small_business_owners, verified_contacts_only,
                         decision_makers_all_sizes, local_service_businesses,
                         no_tech_stack, naples_gyms, naples_hvac, naples_restaurants
            location: Location override (for profiles that accept it)
            industry_keyword: Industry override (for profiles that accept it)
            **overrides: Additional filter overrides

        Returns:
            Search results dict

        Example:
            client = ApolloClient()

            # Use preset Naples gyms profile
            results = client.search_with_profile("naples_gyms")

            # Or use generic profile with location
            results = client.search_with_profile(
                "small_business_owners",
                location="Fort Myers, FL",
                industry_keyword="restaurant"
            )
        """
        profile_map = {
            "small_business_owners": SearchProfiles.small_business_owners,
            "verified_contacts_only": SearchProfiles.verified_contacts_only,
            "decision_makers_all_sizes": SearchProfiles.decision_makers_all_sizes,
            "local_service_businesses": SearchProfiles.local_service_businesses,
            "no_tech_stack": SearchProfiles.no_tech_stack,
            "naples_gyms": SearchProfiles.naples_gyms,
            "naples_hvac": SearchProfiles.naples_hvac,
            "naples_restaurants": SearchProfiles.naples_restaurants,
        }

        if profile_name not in profile_map:
            logger.error(f"Unknown profile: {profile_name}. Available: {list(profile_map.keys())}")
            return None

        # Get the profile function
        profile_func = profile_map[profile_name]

        # Some profiles take location/keyword, some don't
        if profile_name in ["naples_gyms", "naples_hvac", "naples_restaurants"]:
            filters = profile_func()
        elif profile_name == "no_tech_stack":
            filters = profile_func(location or "Naples, FL")
        elif profile_name == "decision_makers_all_sizes":
            filters = profile_func(location or "Naples, FL")
        else:
            filters = profile_func(location or "Naples, FL", industry_keyword)

        # Apply any overrides
        for key, value in overrides.items():
            if hasattr(filters, key):
                setattr(filters, key, value)

        return self.search_people_advanced(filters)

    def search_all_pages(
        self,
        filters: PeopleSearchFilters,
        max_results: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Search and return ALL results across multiple pages.

        Handles pagination automatically up to max_results.

        Args:
            filters: PeopleSearchFilters instance
            max_results: Maximum total results to return (default 500)

        Returns:
            Combined list of all people across pages

        Example:
            filters = SearchProfiles.naples_gyms()
            all_leads = client.search_all_pages(filters, max_results=200)
        """
        all_people = []
        filters.page = 1
        filters.per_page = 100  # Max per request

        while len(all_people) < max_results:
            result = self.search_people_advanced(filters)

            if not result or "people" not in result:
                break

            people = result["people"]
            if not people:
                break

            all_people.extend(people)
            logger.info(f"Retrieved {len(all_people)} people so far (page {filters.page})")

            # Check pagination
            pagination = result.get("pagination", {})
            total_pages = pagination.get("total_pages", 1)

            if filters.page >= total_pages:
                break

            filters.page += 1

        return all_people[:max_results]


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
