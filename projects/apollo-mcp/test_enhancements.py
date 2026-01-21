#!/usr/bin/env python3
"""
Test script for Apollo MCP enhancements.

Tests:
1. Company template detection
2. Search parameter building
3. Lead quality scoring
4. Search refinement logic
5. Full pipeline (dry-run without API calls)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apollo_mcp.company_templates import (
    detect_company_from_prompt,
    get_company_template,
    extract_location_from_prompt,
    extract_industry_from_prompt,
    build_search_params_from_template
)

from apollo_mcp.search_refinement import (
    filter_people_by_excluded_titles,
    score_lead_quality,
    validate_search_results,
    select_top_leads_for_enrichment
)


def test_company_detection():
    """Test company context detection from natural language prompts."""
    print("\n=== Testing Company Detection ===")

    test_cases = [
        ("Run cold outreach for Naples HVAC companies for Southwest Florida Comfort", "southwest_florida_comfort"),
        ("Find gyms in Miami for Marceau Solutions", "marceau_solutions"),
        ("Get e-commerce leads for Footer Shipping", "footer_shipping"),
        ("Naples HVAC businesses", "southwest_florida_comfort"),
        ("Find restaurant owners in Fort Myers", "marceau_solutions"),
        ("Shopify store owners", "footer_shipping"),
    ]

    for prompt, expected in test_cases:
        detected = detect_company_from_prompt(prompt)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{prompt}' -> {detected} (expected: {expected})")


def test_location_extraction():
    """Test location extraction from prompts."""
    print("\n=== Testing Location Extraction ===")

    test_cases = [
        ("Naples HVAC companies", "Naples"),
        ("Find gyms in Miami, FL", "Miami, FL"),
        ("Fort Myers restaurants", "Fort Myers"),
        ("Southwest Florida businesses", "Southwest Florida"),
    ]

    for prompt, expected_contains in test_cases:
        location = extract_location_from_prompt(prompt)
        status = "✓" if location and expected_contains in location else "✗"
        print(f"{status} '{prompt}' -> {location}")


def test_industry_extraction():
    """Test industry extraction from prompts."""
    print("\n=== Testing Industry Extraction ===")

    test_cases = [
        ("Naples HVAC companies", "HVAC"),
        ("Find gyms in Miami", "Fitness"),
        ("Restaurant owners", "Restaurants"),
        ("E-commerce businesses", "E-commerce"),
    ]

    for prompt, expected in test_cases:
        industry = extract_industry_from_prompt(prompt)
        status = "✓" if industry == expected else "✗"
        print(f"{status} '{prompt}' -> {industry} (expected: {expected})")


def test_search_params_building():
    """Test building search parameters from template."""
    print("\n=== Testing Search Params Building ===")

    company_key = "southwest_florida_comfort"
    template = get_company_template(company_key)

    if not template:
        print(f"✗ Template not found: {company_key}")
        return

    # Test with default template
    params = build_search_params_from_template(template)
    print(f"✓ Default params: {params.keys()}")

    # Test with location override
    params_with_override = build_search_params_from_template(
        template,
        override_location="Miami, FL",
        override_keywords="air conditioning repair"
    )
    print(f"✓ Override params: location={params_with_override.get('organization_locations')}")
    print(f"  Keywords: {params_with_override.get('q_keywords')}")


def test_lead_filtering():
    """Test filtering people by excluded titles."""
    print("\n=== Testing Lead Filtering ===")

    # Mock people data
    mock_people = [
        {"name": "John Owner", "title": "Owner"},
        {"name": "Jane CEO", "title": "CEO"},
        {"name": "Bob Sales", "title": "Outside Sales Representative"},
        {"name": "Alice Manager", "title": "General Manager"},
        {"name": "Chris Sales", "title": "Sales Director"},
        {"name": "Diana Assistant", "title": "Executive Assistant"},
    ]

    excluded_titles = ["sales", "assistant", "coordinator"]

    filtered = filter_people_by_excluded_titles(mock_people, excluded_titles)

    print(f"Original count: {len(mock_people)}")
    print(f"Filtered count: {len(filtered)}")
    print(f"✓ Remaining leads:")
    for person in filtered:
        print(f"  - {person['name']} ({person['title']})")


def test_lead_scoring():
    """Test lead quality scoring."""
    print("\n=== Testing Lead Quality Scoring ===")

    # Mock leads with varying quality
    mock_leads = [
        {
            "name": "High Quality Lead",
            "title": "Owner",
            "email": "owner@company.com",
            "phone_numbers": [{"raw_number": "555-1234"}],
            "linkedin_url": "https://linkedin.com/in/owner",
            "organization": {"website_url": "https://company.com", "industry": "HVAC"}
        },
        {
            "name": "Medium Quality Lead",
            "title": "Manager",
            "email": "manager@company.com",
            "organization": {"industry": "Restaurants"}
        },
        {
            "name": "Low Quality Lead",
            "title": "Employee",
        }
    ]

    for lead in mock_leads:
        score = score_lead_quality(lead)
        print(f"✓ {lead['name']}: {score:.2f} ({lead.get('title', 'No title')})")


def test_validation_logic():
    """Test search result validation logic."""
    print("\n=== Testing Validation Logic ===")

    # Mock search results
    mock_results = [
        {"name": "Owner 1", "title": "Owner", "email": "a@b.com", "organization": {"website_url": "http://a.com"}},
        {"name": "Owner 2", "title": "CEO", "email": "c@d.com", "organization": {"website_url": "http://c.com"}},
        {"name": "Sales 1", "title": "Sales Representative"},
        {"name": "Sales 2", "title": "Outside Sales"},
        {"name": "Manager 1", "title": "General Manager", "email": "e@f.com"},
    ]

    excluded_titles = ["sales", "representative"]

    validation = validate_search_results(mock_results, excluded_titles, min_quality_score=0.5)

    print(f"Valid: {validation['valid']}")
    print(f"Reason: {validation['reason']}")
    print(f"Metrics:")
    for key, value in validation['metrics'].items():
        print(f"  {key}: {value}")
    print(f"Recommendation: {validation['recommendation']}")


def test_top_lead_selection():
    """Test selecting top leads for enrichment."""
    print("\n=== Testing Top Lead Selection ===")

    # Mock scored leads
    scored_leads = [
        {"person": {"name": f"Lead {i}", "title": "Owner"}, "quality_score": 1.0 - (i * 0.1)}
        for i in range(10)
    ]

    top_leads = select_top_leads_for_enrichment(
        scored_leads,
        top_percent=0.3,  # Top 30%
        min_leads=2,
        max_leads=5
    )

    print(f"Total leads: {len(scored_leads)}")
    print(f"Selected for enrichment: {len(top_leads)}")
    print(f"✓ Top leads:")
    for lead in top_leads:
        print(f"  - {lead['name']}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Apollo MCP Enhancement Tests")
    print("=" * 60)

    try:
        test_company_detection()
        test_location_extraction()
        test_industry_extraction()
        test_search_params_building()
        test_lead_filtering()
        test_lead_scoring()
        test_validation_logic()
        test_top_lead_selection()

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
