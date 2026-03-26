#!/usr/bin/env python3
"""
Verification script for Apollo MCP v1.1.0 enhancements.

Checks:
1. All new modules import successfully
2. All new functions are accessible
3. Templates exist and load correctly
4. Server lists all tools including new ones
5. Version is updated
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_imports():
    """Verify all modules import successfully."""
    print("\n=== Checking Module Imports ===")

    try:
        from apollo_mcp import company_templates
        print("✓ apollo_mcp.company_templates")
    except ImportError as e:
        print(f"✗ apollo_mcp.company_templates: {e}")
        return False

    try:
        from apollo_mcp import search_refinement
        print("✓ apollo_mcp.search_refinement")
    except ImportError as e:
        print(f"✗ apollo_mcp.search_refinement: {e}")
        return False

    try:
        from apollo_mcp import server
        print("✓ apollo_mcp.server")
    except ImportError as e:
        print(f"✗ apollo_mcp.server: {e}")
        return False

    return True


def check_functions():
    """Verify new functions exist."""
    print("\n=== Checking New Functions ===")

    from apollo_mcp import company_templates, search_refinement

    functions = [
        # company_templates.py
        ("detect_company_from_prompt", company_templates),
        ("get_company_template", company_templates),
        ("extract_location_from_prompt", company_templates),
        ("extract_industry_from_prompt", company_templates),
        ("build_search_params_from_template", company_templates),

        # search_refinement.py
        ("filter_people_by_excluded_titles", search_refinement),
        ("score_lead_quality", search_refinement),
        ("validate_search_results", search_refinement),
        ("refine_search_params", search_refinement),
        ("select_top_leads_for_enrichment", search_refinement),
    ]

    all_exist = True
    for func_name, module in functions:
        if hasattr(module, func_name):
            print(f"✓ {func_name}")
        else:
            print(f"✗ {func_name} not found")
            all_exist = False

    return all_exist


def check_templates():
    """Verify template files exist and are valid JSON."""
    print("\n=== Checking Template Files ===")

    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

    if not os.path.exists(templates_dir):
        print(f"✗ Templates directory not found: {templates_dir}")
        return False

    required_templates = [
        'southwest_florida_comfort.json',
        'marceau_solutions.json',
        'footer_shipping.json'
    ]

    all_valid = True
    for template_file in required_templates:
        template_path = os.path.join(templates_dir, template_file)

        if not os.path.exists(template_path):
            print(f"✗ {template_file} not found")
            all_valid = False
            continue

        try:
            with open(template_path, 'r') as f:
                data = json.load(f)

            # Verify required fields
            required_fields = ['company_name', 'company_key', 'search_template']
            missing = [f for f in required_fields if f not in data]

            if missing:
                print(f"✗ {template_file} missing fields: {missing}")
                all_valid = False
            else:
                print(f"✓ {template_file} - {data['company_name']}")

        except json.JSONDecodeError as e:
            print(f"✗ {template_file} invalid JSON: {e}")
            all_valid = False

    return all_valid


def check_company_templates():
    """Verify COMPANY_TEMPLATES dict is populated."""
    print("\n=== Checking COMPANY_TEMPLATES Dict ===")

    from apollo_mcp.company_templates import COMPANY_TEMPLATES

    required_keys = [
        'southwest_florida_comfort',
        'marceau_solutions',
        'footer_shipping'
    ]

    all_present = True
    for key in required_keys:
        if key in COMPANY_TEMPLATES:
            template = COMPANY_TEMPLATES[key]
            print(f"✓ {key}: {template.get('name', 'Unknown')}")
        else:
            print(f"✗ {key} not in COMPANY_TEMPLATES")
            all_present = False

    return all_present


def check_version():
    """Verify VERSION file is updated."""
    print("\n=== Checking Version ===")

    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')

    if not os.path.exists(version_file):
        print("✗ VERSION file not found")
        return False

    with open(version_file, 'r') as f:
        version = f.read().strip()

    if version == "1.1.0":
        print(f"✓ VERSION: {version}")
        return True
    else:
        print(f"✗ VERSION: {version} (expected 1.1.0)")
        return False


def check_documentation():
    """Verify documentation files exist."""
    print("\n=== Checking Documentation ===")

    docs = [
        'README.md',
        'CHANGELOG.md',
        'QUICKSTART.md',
        'workflows/end-to-end-outreach.md',
        'ENHANCEMENT-SUMMARY.md',
        'test_enhancements.py'
    ]

    all_exist = True
    for doc in docs:
        doc_path = os.path.join(os.path.dirname(__file__), doc)
        if os.path.exists(doc_path):
            print(f"✓ {doc}")
        else:
            print(f"✗ {doc} not found")
            all_exist = False

    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Apollo MCP v1.1.0 Verification")
    print("=" * 60)

    checks = [
        ("Module Imports", check_imports),
        ("New Functions", check_functions),
        ("Template Files", check_templates),
        ("Company Templates Dict", check_company_templates),
        ("Version Number", check_version),
        ("Documentation", check_documentation),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "=" * 60)
        print("✓ ALL CHECKS PASSED - Ready for deployment!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ SOME CHECKS FAILED - Review errors above")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
