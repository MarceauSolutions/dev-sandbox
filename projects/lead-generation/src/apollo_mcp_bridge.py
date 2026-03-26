#!/usr/bin/env python3
"""
Apollo MCP Bridge - Unified API for Apollo Search

Enables Apollo MCP as a search source in lead-scraper, providing:
- Natural language search interface
- Company template detection
- Lead scoring and filtering
- Contact enrichment
- Compatible output format for SMS workflows

Usage:
    from .apollo_mcp_bridge import ApolloMCPBridge

    bridge = ApolloMCPBridge(api_key=os.getenv("APOLLO_API_KEY"))
    leads = bridge.search(
        query="gyms",
        location="Naples, FL",
        campaign_name="Naples Gyms Campaign",
        company_context="marceau-solutions"
    )
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Lead

logger = logging.getLogger(__name__)


class ApolloMCPBridge:
    """
    Bridge between Apollo MCP and lead-scraper system.

    Provides a unified API for Apollo searches that:
    1. Calls Apollo MCP server (or direct API as fallback)
    2. Converts results to Lead objects
    3. Handles company template detection
    4. Manages credit-efficient enrichment
    """

    def __init__(self, api_key: str):
        """
        Initialize Apollo MCP bridge.

        Args:
            api_key: Apollo.io API key
        """
        self.api_key = api_key
        self._ensure_apollo_mcp_available()

    def _ensure_apollo_mcp_available(self):
        """Ensure Apollo MCP modules are accessible."""
        try:
            # Add apollo-mcp to path
            apollo_mcp_path = Path("/Users/williammarceaujr./dev-sandbox/projects/apollo-mcp/src")
            if apollo_mcp_path.exists() and str(apollo_mcp_path) not in sys.path:
                sys.path.insert(0, str(apollo_mcp_path))

            # Try importing Apollo MCP modules
            from apollo_mcp.apollo import ApolloClient
            logger.info("Apollo MCP modules loaded successfully")
        except ImportError as e:
            logger.warning(f"Apollo MCP not available locally: {e}")
            logger.warning("Install with: pip install apollo-mcp")

    def search(
        self,
        query: str,
        location: str,
        campaign_name: str,
        company_context: str = "marceau-solutions",
        max_results: int = 100,
        enrich_top_n: int = 20,
        min_score: int = 8
    ) -> List[Lead]:
        """
        Search via Apollo MCP and return Lead objects.

        Args:
            query: Industry or business type (e.g., "gyms", "restaurants")
            location: Location string (e.g., "Naples, FL")
            campaign_name: Campaign identifier for tracking
            company_context: Which company template to use
            max_results: Maximum search results to retrieve
            enrich_top_n: How many top leads to enrich with contact data
            min_score: Minimum score for lead selection (default: 8)

        Returns:
            List of Lead objects ready for SMS campaigns

        Example:
            bridge = ApolloMCPBridge(api_key="...")
            leads = bridge.search(
                query="gyms",
                location="Naples, FL",
                campaign_name="Naples Gyms Jan 2026",
                enrich_top_n=10
            )
        """
        logger.info(f"Apollo MCP search: {query} in {location} for {company_context}")

        # Construct natural language prompt
        prompt = f"{query} in {location} for {company_context}"

        # Call Apollo MCP
        result = self._call_apollo_mcp(
            prompt=prompt,
            max_results=max_results,
            enrich_top_n=enrich_top_n,
            min_score=min_score
        )

        if not result or not result.get("success"):
            logger.error("Apollo MCP search failed")
            return []

        # Convert to Lead objects
        leads = self._convert_to_leads(result, campaign_name, location)

        logger.info(f"Apollo MCP returned {len(leads)} enriched leads")

        return leads

    def _call_apollo_mcp(
        self,
        prompt: str,
        max_results: int,
        enrich_top_n: int,
        min_score: int
    ) -> Optional[Dict[str, Any]]:
        """
        Call Apollo MCP server to execute search and enrichment.

        Args:
            prompt: Natural language search prompt
            max_results: Maximum results to retrieve
            enrich_top_n: How many top leads to enrich
            min_score: Minimum score for selection

        Returns:
            Dictionary with search results and enriched leads
        """
        try:
            # Import Apollo MCP modules
            from apollo_mcp.apollo import ApolloClient
            from apollo_mcp.company_templates import (
                detect_company_from_prompt,
                get_company_template,
                build_search_params_from_template
            )
            from apollo_mcp.search_refinement import (
                validate_search_results,
                select_top_leads_for_enrichment
            )

            # Detect company context from prompt
            company_key = detect_company_from_prompt(prompt)
            if not company_key:
                company_key = "marceau_solutions"  # Default

            logger.info(f"Detected company: {company_key}")

            # Get company template and build search params
            template = get_company_template(company_key)
            search_params = build_search_params_from_template(template)

            # Initialize Apollo client
            client = ApolloClient(api_key=self.api_key)

            # Execute search
            logger.info(f"Executing Apollo search with params: {search_params.keys()}")
            result = client.search_people(
                person_titles=search_params.get("person_titles"),
                organization_locations=search_params.get("organization_locations"),
                organization_num_employees_ranges=search_params.get("organization_num_employees_ranges"),
                q_keywords=search_params.get("q_keywords"),
                per_page=min(max_results, 100)
            )

            if not result or "people" not in result:
                logger.error("Apollo search returned no results")
                return None

            people = result["people"]
            logger.info(f"Apollo search returned {len(people)} results")

            # Validate and score results
            excluded_titles = search_params.get("_excluded_titles", [])
            validation = validate_search_results(people, excluded_titles)
            scored_leads = validation["scored_leads"]

            logger.info(f"After filtering: {len(scored_leads)} valid leads")

            # Select top leads for enrichment
            top_leads = select_top_leads_for_enrichment(
                scored_leads,
                top_percent=0.2,  # Top 20%
                min_leads=10,
                max_leads=enrich_top_n,
                min_score=min_score
            )

            logger.info(f"Selected {len(top_leads)} leads for enrichment (min score: {min_score})")

            # Enrich top leads
            enriched = []
            for idx, person in enumerate(top_leads, 1):
                logger.info(f"Enriching {idx}/{len(top_leads)}: {person.get('first_name')} {person.get('last_name')}")

                enriched_data = client.enrich_person(
                    first_name=person.get("first_name"),
                    last_name=person.get("last_name"),
                    organization_name=person.get("organization", {}).get("name"),
                    linkedin_url=person.get("linkedin_url")
                )

                if enriched_data:
                    # Merge score from original data
                    enriched_data["_score"] = person.get("_score", 0)
                    enriched.append(enriched_data)
                else:
                    logger.warning(f"Enrichment failed for {person.get('first_name')} {person.get('last_name')}")

            logger.info(f"Successfully enriched {len(enriched)} leads")

            return {
                "success": True,
                "company": template["name"],
                "leads_searched": len(people),
                "leads_scored": len(scored_leads),
                "leads_enriched": len(enriched),
                "credits_used": len(enriched) * 2,  # Approximate
                "leads": enriched
            }

        except ImportError as e:
            logger.error(f"Apollo MCP not installed: {e}")
            logger.error("Install with: pip install apollo-mcp")
            return None
        except Exception as e:
            logger.error(f"Apollo MCP call failed: {e}", exc_info=True)
            return None

    def _convert_to_leads(
        self,
        apollo_result: Dict[str, Any],
        campaign_name: str,
        location: str
    ) -> List[Lead]:
        """
        Convert Apollo MCP output to Lead objects.

        Args:
            apollo_result: Dictionary from _call_apollo_mcp
            campaign_name: Campaign name for tracking
            location: Location string for city/state parsing

        Returns:
            List of Lead objects
        """
        leads = []

        # Parse location (e.g., "Naples, FL" -> city="Naples", state="FL")
        city, state = self._parse_location(location)

        for apollo_lead in apollo_result.get("leads", []):
            # Extract organization data
            org = apollo_lead.get("organization", {}) or {}

            # Extract phone numbers (Apollo returns list)
            phone_numbers = apollo_lead.get("phone_numbers", [])
            phone = ""
            if phone_numbers and len(phone_numbers) > 0:
                phone = phone_numbers[0].get("raw_number", "")

            # Extract title and score
            title = apollo_lead.get("title", "")
            score = apollo_lead.get("_score", 0)

            # Determine pain points based on available data
            pain_points = self._identify_pain_points(apollo_lead, org)

            # Create Lead object
            lead = Lead(
                source="apollo_mcp",
                business_name=org.get("name", ""),
                owner_name=f"{apollo_lead.get('first_name', '')} {apollo_lead.get('last_name', '')}".strip(),
                phone=phone,
                email=apollo_lead.get("email", ""),
                website=org.get("website_url", ""),
                linkedin=apollo_lead.get("linkedin_url", ""),
                city=apollo_lead.get("city", "") or city,
                state=apollo_lead.get("state", "") or state,
                category=org.get("industry", ""),
                pain_points=pain_points,
                notes=f"Campaign: {campaign_name} | Title: {title} | Score: {score} | Employees: {org.get('estimated_num_employees', 'Unknown')}",
                scraped_at=datetime.now().isoformat()
            )

            leads.append(lead)

        return leads

    def _parse_location(self, location: str) -> tuple[str, str]:
        """
        Parse location string into city and state.

        Args:
            location: Location string (e.g., "Naples, FL")

        Returns:
            Tuple of (city, state)
        """
        if "," in location:
            parts = [p.strip() for p in location.split(",")]
            if len(parts) >= 2:
                return parts[0], parts[1]
        return location, ""

    def _identify_pain_points(
        self,
        apollo_lead: Dict[str, Any],
        org: Dict[str, Any]
    ) -> List[str]:
        """
        Identify potential pain points based on Apollo data.

        Args:
            apollo_lead: Person data from Apollo
            org: Organization data from Apollo

        Returns:
            List of identified pain points
        """
        pain_points = []

        # No website
        if not org.get("website_url"):
            pain_points.append("no_website")

        # Small company (likely resource-constrained)
        employees = org.get("estimated_num_employees", 0)
        if employees and employees < 20:
            pain_points.append("small_team")

        # No LinkedIn (low digital presence)
        if not apollo_lead.get("linkedin_url"):
            pain_points.append("low_online_presence")

        # Growing company (job postings indicator)
        if org.get("current_job_openings", 0) > 0:
            pain_points.append("growing_company")

        return pain_points


def test_apollo_mcp_bridge():
    """Test Apollo MCP bridge with a small search."""
    logging.basicConfig(level=logging.INFO)

    # Load API key from environment
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        print("ERROR: APOLLO_API_KEY not found in .env")
        return

    # Initialize bridge
    bridge = ApolloMCPBridge(api_key=api_key)

    # Test search
    print("\n=== Testing Apollo MCP Bridge ===\n")
    leads = bridge.search(
        query="gyms",
        location="Naples, FL",
        campaign_name="Test Campaign",
        company_context="marceau-solutions",
        max_results=20,
        enrich_top_n=3  # Only enrich 3 for testing (6 credits)
    )

    print(f"\n=== Results ===")
    print(f"Total leads returned: {len(leads)}")

    for idx, lead in enumerate(leads, 1):
        print(f"\nLead {idx}:")
        print(f"  Business: {lead.business_name}")
        print(f"  Owner: {lead.owner_name}")
        print(f"  Phone: {lead.phone}")
        print(f"  Email: {lead.email}")
        print(f"  Website: {lead.website or 'N/A'}")
        print(f"  Pain Points: {', '.join(lead.pain_points) if lead.pain_points else 'None identified'}")
        print(f"  Notes: {lead.notes}")


if __name__ == "__main__":
    test_apollo_mcp_bridge()
