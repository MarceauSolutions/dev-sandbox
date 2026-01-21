#!/usr/bin/env python3
"""
Apollo.io MCP Server

MCP (Model Context Protocol) server that provides Apollo.io lead enrichment,
prospecting, and company search capabilities.

Registry: io.github.wmarceau/apollo
"""

import asyncio
import json
import sys

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from .apollo import ApolloClient, ApolloConfig
    from .company_templates import (
        detect_company_from_prompt,
        get_company_template,
        extract_location_from_prompt,
        extract_industry_from_prompt,
        build_search_params_from_template,
        DEFAULT_EXCLUDED_TITLES
    )
    from .search_refinement import (
        validate_search_results,
        refine_search_params,
        select_top_leads_for_enrichment
    )
except ImportError as e:
    print(f"Error importing Apollo modules: {e}", file=sys.stderr)
    sys.exit(1)


# Server instance
server = Server("apollo")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        # Search Tools
        Tool(
            name="search_people",
            description="""Search Apollo's database for people matching criteria.

Find contacts based on job title, location, company, and other filters.
Returns contact information including name, title, company, and location.
Use enrich_person to reveal full contact details (costs credits).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_titles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Job titles to search (e.g., ['owner', 'ceo', 'manager'])"
                    },
                    "person_locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Locations (e.g., ['Naples, FL', 'Florida'])"
                    },
                    "organization_locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Company locations"
                    },
                    "organization_num_employees_ranges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Size ranges (e.g., ['1,10', '11,50'])"
                    },
                    "q_keywords": {
                        "type": "string",
                        "description": "Keyword search"
                    },
                    "excluded_titles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exclude people with these title keywords (e.g., ['sales', 'assistant'])"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page, max 100 (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="search_companies",
            description="""Search Apollo's database for companies matching criteria.

Find businesses based on location, industry, size, and technologies.
Returns company information including name, size, industry, and website.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Locations (e.g., ['Naples, FL'])"
                    },
                    "organization_num_employees_ranges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Size ranges (e.g., ['1,50'])"
                    },
                    "organization_not_technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exclude companies using these technologies"
                    },
                    "q_organization_keyword_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Industry tags/keywords"
                    },
                    "q_keywords": {
                        "type": "string",
                        "description": "Keyword search"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page, max 100 (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="search_local_businesses",
            description="""Convenience method to search for local businesses.

Quick search for businesses in a specific location and industry.
Example: 'gyms in Naples, FL with 1-50 employees'""",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location string (e.g., 'Naples, FL')"
                    },
                    "industry_keywords": {
                        "type": "string",
                        "description": "Industry to search (e.g., 'gym', 'restaurant')"
                    },
                    "employee_range": {
                        "type": "string",
                        "description": "Size range (default: '1,50' for small businesses)",
                        "default": "1,50"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 100)",
                        "default": 100
                    }
                },
                "required": ["location"]
            }
        ),

        # Enrichment Tools
        Tool(
            name="enrich_person",
            description="""Enrich a person's data using available identifiers.

COSTS CREDITS: This reveals contact information (email, phone).

At minimum, provide one of:
- email
- first_name + last_name + (organization_name or domain)
- linkedin_url

Returns detailed contact information including email, phone, title, company.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address"
                    },
                    "first_name": {
                        "type": "string",
                        "description": "First name"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name"
                    },
                    "organization_name": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Company domain"
                    },
                    "linkedin_url": {
                        "type": "string",
                        "description": "LinkedIn profile URL"
                    }
                }
            }
        ),
        Tool(
            name="enrich_company",
            description="""Enrich company data using domain or name.

Returns detailed company information including industry, size, revenue,
technologies, and contact information.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Company website domain"
                    },
                    "name": {
                        "type": "string",
                        "description": "Company name"
                    }
                }
            }
        ),

        # Decision Maker Tools
        Tool(
            name="find_decision_makers",
            description="""Find decision makers at a specific company.

Searches for owners, CEOs, presidents, founders, managers, and directors
at the given company domain.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_domain": {
                        "type": "string",
                        "description": "Company website domain (e.g., 'example.com')"
                    },
                    "titles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom job titles to look for (default: owner, ceo, president, founder, manager, director)"
                    }
                },
                "required": ["company_domain"]
            }
        ),
        Tool(
            name="find_email",
            description="""Find a person's email given their name and company domain.

Returns email address if found. Uses enrichment API (costs credits).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "First name"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Company domain"
                    }
                },
                "required": ["first_name", "last_name", "domain"]
            }
        ),

        # End-to-End Pipeline
        Tool(
            name="run_full_outreach_pipeline",
            description="""Execute full end-to-end outreach pipeline from a natural language prompt.

This automates the entire lead generation workflow:
1. Detect company context from prompt
2. Load company-specific search template
3. Execute search with automatic exclusions
4. Validate and refine search results (up to 3 iterations)
5. Score leads by quality
6. Select top 20% for enrichment
7. Enrich selected leads (costs credits)
8. Return enriched leads ready for SMS outreach

Example prompts:
- "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
- "Find gyms in Miami for Marceau Solutions"
- "Get e-commerce leads for Footer Shipping"

This eliminates manual CSV export/import steps and provides end-to-end automation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Natural language prompt describing the search (e.g., 'Naples HVAC for Southwest Florida Comfort')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum initial search results (default: 100)",
                        "default": 100
                    },
                    "enrich_top_n": {
                        "type": "integer",
                        "description": "Number of top leads to enrich (default: 20)",
                        "default": 20
                    },
                    "skip_enrichment": {
                        "type": "boolean",
                        "description": "Skip enrichment step to save credits (default: false)",
                        "default": False
                    }
                },
                "required": ["prompt"]
            }
        ),

        # Account Management
        Tool(
            name="get_credit_balance",
            description="""Check remaining Apollo API credits.

Note: This is a placeholder - Apollo API doesn't provide a direct
credit balance endpoint. Track usage manually or via the web dashboard.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    try:
        if name == "search_people":
            return await handle_search_people(arguments)

        elif name == "search_companies":
            return await handle_search_companies(arguments)

        elif name == "search_local_businesses":
            return await handle_search_local_businesses(arguments)

        elif name == "enrich_person":
            return await handle_enrich_person(arguments)

        elif name == "enrich_company":
            return await handle_enrich_company(arguments)

        elif name == "find_decision_makers":
            return await handle_find_decision_makers(arguments)

        elif name == "find_email":
            return await handle_find_email(arguments)

        elif name == "get_credit_balance":
            return await handle_get_credit_balance(arguments)

        elif name == "run_full_outreach_pipeline":
            return await handle_run_full_outreach_pipeline(arguments)

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "hint": "Check that your APOLLO_API_KEY is configured in environment variables"
            }, indent=2)
        )]


async def handle_search_people(arguments: dict):
    """Search for people."""
    from .search_refinement import filter_people_by_excluded_titles

    client = ApolloClient()

    result = client.search_people(
        person_titles=arguments.get("person_titles"),
        person_locations=arguments.get("person_locations"),
        organization_locations=arguments.get("organization_locations"),
        organization_num_employees_ranges=arguments.get("organization_num_employees_ranges"),
        q_keywords=arguments.get("q_keywords"),
        page=arguments.get("page", 1),
        per_page=arguments.get("per_page", 25)
    )

    if not result:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Search failed",
                "hint": "Check API key and search criteria"
            }, indent=2)
        )]

    people = result.get("people", [])

    # Apply excluded_titles filter if provided
    excluded_titles = arguments.get("excluded_titles")
    if excluded_titles:
        original_count = len(people)
        people = filter_people_by_excluded_titles(people, excluded_titles)
        filtered_count = original_count - len(people)
    else:
        filtered_count = 0

    pagination = result.get("pagination", {})

    response = {
        "success": True,
        "count": len(people),
        "total_entries": pagination.get("total_entries", 0),
        "page": pagination.get("page", 1),
        "total_pages": pagination.get("total_pages", 1),
        "people": people
    }

    if filtered_count > 0:
        response["filtered_out"] = filtered_count
        response["exclusions_applied"] = excluded_titles

    return [TextContent(
        type="text",
        text=json.dumps(response, indent=2, default=str)
    )]


async def handle_search_companies(arguments: dict):
    """Search for companies."""
    client = ApolloClient()

    result = client.search_companies(
        organization_locations=arguments.get("organization_locations"),
        organization_num_employees_ranges=arguments.get("organization_num_employees_ranges"),
        organization_not_technologies=arguments.get("organization_not_technologies"),
        q_organization_keyword_tags=arguments.get("q_organization_keyword_tags"),
        q_keywords=arguments.get("q_keywords"),
        page=arguments.get("page", 1),
        per_page=arguments.get("per_page", 25)
    )

    if not result:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Search failed",
                "hint": "Check API key and search criteria"
            }, indent=2)
        )]

    companies = result.get("organizations", [])
    pagination = result.get("pagination", {})

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "count": len(companies),
            "total_entries": pagination.get("total_entries", 0),
            "page": pagination.get("page", 1),
            "total_pages": pagination.get("total_pages", 1),
            "companies": companies
        }, indent=2, default=str)
    )]


async def handle_search_local_businesses(arguments: dict):
    """Search local businesses convenience method."""
    client = ApolloClient()

    companies = client.search_local_businesses(
        location=arguments.get("location"),
        industry_keywords=arguments.get("industry_keywords"),
        employee_range=arguments.get("employee_range", "1,50"),
        max_results=arguments.get("max_results", 100)
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "count": len(companies),
            "location": arguments.get("location"),
            "industry": arguments.get("industry_keywords"),
            "companies": companies
        }, indent=2, default=str)
    )]


async def handle_enrich_person(arguments: dict):
    """Enrich person data."""
    client = ApolloClient()

    result = client.enrich_person(
        email=arguments.get("email"),
        first_name=arguments.get("first_name"),
        last_name=arguments.get("last_name"),
        organization_name=arguments.get("organization_name"),
        domain=arguments.get("domain"),
        linkedin_url=arguments.get("linkedin_url")
    )

    if not result:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Enrichment failed",
                "hint": "Provide at least one of: email, (first_name + last_name + domain), or linkedin_url"
            }, indent=2)
        )]

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "person": result,
            "warning": "This operation costs Apollo credits"
        }, indent=2, default=str)
    )]


async def handle_enrich_company(arguments: dict):
    """Enrich company data."""
    client = ApolloClient()

    result = client.enrich_company(
        domain=arguments.get("domain"),
        name=arguments.get("name")
    )

    if not result:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Enrichment failed",
                "hint": "Provide domain or company name"
            }, indent=2)
        )]

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "company": result
        }, indent=2, default=str)
    )]


async def handle_find_decision_makers(arguments: dict):
    """Find decision makers at a company."""
    client = ApolloClient()

    company_domain = arguments.get("company_domain")
    if not company_domain:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "company_domain is required"}, indent=2)
        )]

    people = client.find_decision_makers(
        company_domain=company_domain,
        titles=arguments.get("titles")
    )

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "company_domain": company_domain,
            "count": len(people),
            "decision_makers": people
        }, indent=2, default=str)
    )]


async def handle_find_email(arguments: dict):
    """Find email for a person."""
    client = ApolloClient()

    first_name = arguments.get("first_name")
    last_name = arguments.get("last_name")
    domain = arguments.get("domain")

    if not all([first_name, last_name, domain]):
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "first_name, last_name, and domain are all required"
            }, indent=2)
        )]

    email = client.find_email(
        first_name=first_name,
        last_name=last_name,
        domain=domain
    )

    if not email:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "message": "Email not found",
                "searched_for": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "domain": domain
                }
            }, indent=2)
        )]

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "email": email,
            "warning": "This operation costs Apollo credits"
        }, indent=2)
    )]


async def handle_get_credit_balance(arguments: dict):
    """Get credit balance (placeholder)."""
    return [TextContent(
        type="text",
        text=json.dumps({
            "note": "Apollo API does not provide a direct credit balance endpoint.",
            "suggestion": "Check your credit balance at https://app.apollo.io/settings/credits",
            "tracking": "Track usage by counting enrichment API calls (enrich_person, enrich_company, find_email)"
        }, indent=2)
    )]


async def handle_run_full_outreach_pipeline(arguments: dict):
    """Execute full end-to-end outreach pipeline."""
    import logging
    logger = logging.getLogger(__name__)

    prompt = arguments.get("prompt", "")
    max_results = arguments.get("max_results", 100)
    enrich_top_n = arguments.get("enrich_top_n", 20)
    skip_enrichment = arguments.get("skip_enrichment", False)

    pipeline_log = []

    # Step 1: Detect company context
    company_key = detect_company_from_prompt(prompt)
    if not company_key:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Could not detect company context from prompt",
                "hint": "Include company name (Southwest Florida Comfort, Marceau Solutions, Footer Shipping) or clear industry keywords",
                "prompt": prompt
            }, indent=2)
        )]

    template = get_company_template(company_key)
    pipeline_log.append(f"✓ Detected company: {template['name']}")

    # Step 2: Extract location/industry overrides from prompt
    location_override = extract_location_from_prompt(prompt)
    industry_override = extract_industry_from_prompt(prompt)

    if location_override:
        pipeline_log.append(f"✓ Using location: {location_override}")
    if industry_override:
        pipeline_log.append(f"✓ Using industry: {industry_override}")

    # Step 3: Build search parameters
    search_params = build_search_params_from_template(
        template,
        override_location=location_override,
        override_keywords=industry_override
    )

    excluded_titles = search_params.pop("_excluded_titles", DEFAULT_EXCLUDED_TITLES)
    pipeline_log.append(f"✓ Excluding titles: {', '.join(excluded_titles[:5])}...")

    # Step 4: Iterative search with refinement
    client = ApolloClient()
    iteration = 0
    max_iterations = 3
    all_people = []

    while iteration < max_iterations:
        iteration += 1
        pipeline_log.append(f"\n--- Search Iteration {iteration} ---")

        # Execute search
        result = client.search_people(
            person_titles=search_params.get("person_titles"),
            organization_locations=search_params.get("organization_locations"),
            organization_num_employees_ranges=search_params.get("organization_num_employees_ranges"),
            q_keywords=search_params.get("q_keywords"),
            per_page=100
        )

        if not result or "people" not in result:
            pipeline_log.append("✗ Search failed")
            break

        people = result.get("people", [])
        pipeline_log.append(f"✓ Found {len(people)} results")

        # Step 5: Validate results
        validation = validate_search_results(people, excluded_titles, min_quality_score=0.5)

        pipeline_log.append(f"✓ After filtering: {validation['metrics']['after_filtering']} leads")
        pipeline_log.append(f"✓ High quality: {validation['metrics']['high_quality']} leads")
        pipeline_log.append(f"  Exclusion rate: {validation['metrics']['exclusion_rate']:.0%}")
        pipeline_log.append(f"  Quality rate: {validation['metrics']['quality_rate']:.0%}")

        if validation["valid"]:
            all_people = validation["scored_leads"]
            pipeline_log.append(f"✓ {validation['reason']}")
            break
        else:
            pipeline_log.append(f"⚠ {validation['reason']}")
            pipeline_log.append(f"  Recommendation: {validation['recommendation']}")

            # Refine search params
            refined_params = refine_search_params(search_params, validation, iteration)
            if refined_params:
                search_params = refined_params
                pipeline_log.append(f"✓ Refining search with new parameters")
            else:
                # Max iterations reached, use what we have
                all_people = validation["scored_leads"]
                pipeline_log.append(f"⚠ Max iterations reached, using current results")
                break

    if not all_people:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "No leads found after search refinement",
                "pipeline_log": pipeline_log,
                "recommendation": "Try different search criteria or location"
            }, indent=2)
        )]

    # Step 6: Select top leads for enrichment
    top_leads = select_top_leads_for_enrichment(
        all_people,
        top_percent=0.2,
        min_leads=10,
        max_leads=enrich_top_n
    )

    pipeline_log.append(f"\n--- Lead Selection ---")
    pipeline_log.append(f"✓ Selected top {len(top_leads)} leads for enrichment")

    # Step 7: Enrich leads (optional)
    enriched_leads = []
    if not skip_enrichment:
        pipeline_log.append(f"\n--- Enrichment (costs {len(top_leads)} credits) ---")

        for i, person in enumerate(top_leads, 1):
            enriched = client.enrich_person(
                first_name=person.get("first_name"),
                last_name=person.get("last_name"),
                organization_name=person.get("organization", {}).get("name") if person.get("organization") else None,
                linkedin_url=person.get("linkedin_url")
            )

            if enriched:
                enriched_leads.append(enriched)
                pipeline_log.append(f"  {i}/{len(top_leads)}: {enriched.get('name')} - {enriched.get('email') or 'no email'}")
            else:
                pipeline_log.append(f"  {i}/{len(top_leads)}: Enrichment failed")

        pipeline_log.append(f"✓ Enriched {len(enriched_leads)} leads")
    else:
        # Return non-enriched leads
        enriched_leads = top_leads
        pipeline_log.append("⚠ Skipping enrichment (skip_enrichment=true)")

    # Step 8: Return results
    pipeline_log.append(f"\n--- Pipeline Complete ---")
    pipeline_log.append(f"✓ Total leads ready: {len(enriched_leads)}")

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "company": template["name"],
            "company_key": company_key,
            "search_iterations": iteration,
            "total_leads_found": len(all_people),
            "leads_selected": len(top_leads),
            "leads_enriched": len(enriched_leads),
            "credits_used": len(enriched_leads) if not skip_enrichment else 0,
            "pipeline_log": pipeline_log,
            "leads": enriched_leads,
            "next_steps": [
                f"Review {len(enriched_leads)} enriched leads",
                "Export to SMS campaign tool",
                f"Use template: {template['name']} outreach messages"
            ]
        }, indent=2, default=str)
    )]


def main():
    """Run the MCP server."""
    asyncio.run(run_server())


async def run_server():
    """Async server runner."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    main()
