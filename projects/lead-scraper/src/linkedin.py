"""
LinkedIn integration for lead prospecting.

IMPORTANT: LinkedIn has strict terms of service regarding automated access.
This module provides legitimate integration options:

1. LinkedIn Sales Navigator API (Requires LinkedIn partnership)
2. LinkedIn Marketing API (For ad targeting)
3. Third-party enrichment (Apollo.io, Hunter.io, etc.)

For most use cases, we recommend using Apollo.io or similar services
that have legitimate access to LinkedIn data through their partnerships.

This module provides:
- LinkedIn URL parsing and validation
- Integration with enrichment services for LinkedIn data
- Manual export processing (from Sales Navigator CSV exports)
"""

import re
import csv
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LinkedInProfile:
    """Parsed LinkedIn profile data."""
    linkedin_url: str
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    email: str = ""
    phone: str = ""


class LinkedInParser:
    """
    Parse and validate LinkedIn URLs and profile data.
    """

    LINKEDIN_URL_PATTERNS = [
        r'linkedin\.com/in/([a-zA-Z0-9\-]+)',  # Personal profiles
        r'linkedin\.com/company/([a-zA-Z0-9\-]+)',  # Company pages
        r'linkedin\.com/sales/lead/([a-zA-Z0-9\-]+)',  # Sales Navigator
        r'linkedin\.com/sales/company/([a-zA-Z0-9\-]+)',  # Sales Navigator company
    ]

    @classmethod
    def is_valid_linkedin_url(cls, url: str) -> bool:
        """Check if URL is a valid LinkedIn profile URL."""
        if not url:
            return False
        return any(re.search(pattern, url) for pattern in cls.LINKEDIN_URL_PATTERNS)

    @classmethod
    def extract_profile_id(cls, url: str) -> Optional[str]:
        """Extract the profile ID from a LinkedIn URL."""
        for pattern in cls.LINKEDIN_URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @classmethod
    def get_profile_type(cls, url: str) -> Optional[str]:
        """Determine if URL is for a person or company."""
        if not url:
            return None
        if "/in/" in url or "/lead/" in url:
            return "person"
        if "/company/" in url:
            return "company"
        return None

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """Normalize a LinkedIn URL to standard format."""
        profile_id = cls.extract_profile_id(url)
        if not profile_id:
            return url

        profile_type = cls.get_profile_type(url)
        if profile_type == "person":
            return f"https://www.linkedin.com/in/{profile_id}"
        elif profile_type == "company":
            return f"https://www.linkedin.com/company/{profile_id}"
        return url


class SalesNavigatorExporter:
    """
    Process exports from LinkedIn Sales Navigator.

    Sales Navigator allows you to export lead lists to CSV.
    This class parses those exports into our Lead format.
    """

    # Expected columns in Sales Navigator export
    EXPECTED_COLUMNS = [
        "First Name", "Last Name", "Title", "Company",
        "Company LinkedIn URL", "Location", "Email"
    ]

    @classmethod
    def parse_export(cls, filepath: str) -> List[LinkedInProfile]:
        """
        Parse a Sales Navigator CSV export.

        Args:
            filepath: Path to the CSV file

        Returns:
            List of LinkedInProfile objects
        """
        profiles = []
        path = Path(filepath)

        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return profiles

        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    profile = LinkedInProfile(
                        linkedin_url=row.get("LinkedIn URL", row.get("Person Linkedin Url", "")),
                        first_name=row.get("First Name", ""),
                        last_name=row.get("Last Name", ""),
                        title=row.get("Title", row.get("Job Title", "")),
                        company=row.get("Company", row.get("Company Name", "")),
                        location=row.get("Location", row.get("Geography", "")),
                        email=row.get("Email", ""),
                        phone=row.get("Phone", "")
                    )
                    profiles.append(profile)

            logger.info(f"Parsed {len(profiles)} profiles from {filepath}")

        except Exception as e:
            logger.error(f"Error parsing Sales Navigator export: {e}")

        return profiles

    @classmethod
    def to_lead_format(cls, profile: LinkedInProfile) -> Dict[str, Any]:
        """
        Convert a LinkedIn profile to our Lead format.
        """
        return {
            "business_name": profile.company,
            "address": "",
            "city": cls._extract_city(profile.location),
            "state": cls._extract_state(profile.location),
            "zip_code": "",
            "phone": profile.phone,
            "email": profile.email,
            "website": "",  # Not in LinkedIn export
            "category": "",
            "rating": 0.0,
            "review_count": 0,
            "facebook": "",
            "instagram": "",
            "linkedin": profile.linkedin_url,
            "twitter": "",
            "source": "linkedin_export",
            "pain_points": [],
            "notes": f"Contact: {profile.first_name} {profile.last_name} - {profile.title}"
        }

    @staticmethod
    def _extract_city(location: str) -> str:
        """Extract city from location string."""
        if not location:
            return ""
        parts = location.split(",")
        return parts[0].strip() if parts else ""

    @staticmethod
    def _extract_state(location: str) -> str:
        """Extract state from location string."""
        if not location:
            return ""
        parts = location.split(",")
        if len(parts) >= 2:
            # Handle "City, State" or "City, State, Country"
            state_part = parts[1].strip()
            # Remove country if present
            if len(parts) > 2 or len(state_part) > 2:
                # Might be "FL" or "Florida" or "Florida, United States"
                return state_part.split()[0] if state_part else ""
            return state_part
        return ""


class LinkedInSearchBuilder:
    """
    Build LinkedIn Sales Navigator search URLs.

    Useful for generating search URLs that users can manually execute
    in Sales Navigator to find leads matching specific criteria.
    """

    BASE_URL = "https://www.linkedin.com/sales/search/people"

    @classmethod
    def build_search_url(
        cls,
        keywords: str = None,
        title: str = None,
        company: str = None,
        location: str = None,
        industry: str = None,
        company_size: str = None
    ) -> str:
        """
        Build a Sales Navigator search URL.

        Note: This URL format may change. Sales Navigator searches
        are complex and often require manual navigation.

        Args:
            keywords: General search keywords
            title: Job title filter
            company: Company name filter
            location: Geographic filter
            industry: Industry filter
            company_size: Company size range

        Returns:
            Sales Navigator search URL
        """
        # Sales Navigator uses complex URL encoding
        # This provides a starting point for manual searches
        params = []

        if keywords:
            params.append(f"keywords={keywords}")
        if title:
            params.append(f"titleIncluded={title}")
        if location:
            params.append(f"geoIncluded={location}")

        if params:
            return f"{cls.BASE_URL}?{'&'.join(params)}"
        return cls.BASE_URL

    @classmethod
    def generate_search_instructions(
        cls,
        target_titles: List[str],
        target_locations: List[str],
        target_industries: List[str] = None,
        company_size: str = "1-50"
    ) -> str:
        """
        Generate instructions for manual Sales Navigator search.

        Returns:
            Markdown-formatted instructions
        """
        instructions = """
## LinkedIn Sales Navigator Search Instructions

### Step 1: Open Sales Navigator
Go to: https://www.linkedin.com/sales/search/people

### Step 2: Apply Filters

**Job Titles (any of):**
"""
        for title in target_titles:
            instructions += f"- {title}\n"

        instructions += "\n**Locations (any of):**\n"
        for location in target_locations:
            instructions += f"- {location}\n"

        if target_industries:
            instructions += "\n**Industries (any of):**\n"
            for industry in target_industries:
                instructions += f"- {industry}\n"

        instructions += f"""
**Company Size:** {company_size} employees

### Step 3: Export Results
1. Select the leads you want
2. Click "Save to list" or use the export feature
3. Export to CSV
4. Import into lead scraper using:
   ```
   python scraper.py import-linkedin --file exported_leads.csv
   ```
"""
        return instructions


# Recommended approach: Use Apollo.io for LinkedIn enrichment
def enrich_linkedin_url_via_apollo(
    linkedin_url: str,
    apollo_client: Any  # ApolloClient instance
) -> Optional[Dict[str, Any]]:
    """
    Enrich a LinkedIn URL using Apollo.io.

    This is the recommended approach for getting contact info
    from LinkedIn profiles without violating ToS.

    Args:
        linkedin_url: LinkedIn profile URL
        apollo_client: Initialized ApolloClient instance

    Returns:
        Enriched person data from Apollo
    """
    if not LinkedInParser.is_valid_linkedin_url(linkedin_url):
        logger.error(f"Invalid LinkedIn URL: {linkedin_url}")
        return None

    return apollo_client.enrich_person(linkedin_url=linkedin_url)
