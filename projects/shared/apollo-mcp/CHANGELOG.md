# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-21

### Added
- **End-to-End Outreach Pipeline** (`run_full_outreach_pipeline` tool):
  - Single-prompt workflow for complete lead generation
  - Automatic company context detection (Southwest Florida Comfort, Marceau Solutions, Footer Shipping)
  - Direct Apollo API integration eliminates CSV export/import steps
  - Iterative search refinement (up to 3 iterations)
  - Lead quality scoring system
  - Automatic selection of top 20% for enrichment
- **Company Templates System**:
  - Pre-configured search templates for 3 companies
  - Company-specific SMS template mappings
  - Template JSON files in `/templates/` directory
- **Search Refinement Engine**:
  - `filter_people_by_excluded_titles()` - Remove unwanted titles
  - `score_lead_quality()` - Score leads 0-1.0 based on title, contact info, company data
  - `validate_search_results()` - Validate quality and determine if refinement needed
  - `refine_search_params()` - Automatically adjust search criteria
  - `select_top_leads_for_enrichment()` - Pick best leads to enrich
- **Enhanced Search Tools**:
  - `excluded_titles` parameter added to `search_people` tool
  - Automatic filtering of sales reps, assistants, coordinators
  - Default exclusion list: sales, outside sales, representative, business development, assistant, intern, junior, coordinator
- **Company Detection**:
  - `detect_company_from_prompt()` - Parse natural language for company context
  - `extract_location_from_prompt()` - Extract location overrides
  - `extract_industry_from_prompt()` - Extract industry keywords
  - `build_search_params_from_template()` - Convert templates to Apollo search params

### Changed
- `search_people` now supports filtering by excluded titles
- Search results include `filtered_out` count when exclusions applied
- README updated with full pipeline documentation and company templates

### Technical
- New modules:
  - `src/apollo_mcp/company_templates.py` - Company template management
  - `src/apollo_mcp/search_refinement.py` - Search quality and refinement logic
- Test suite: `test_enhancements.py` with 8 test scenarios
- Templates directory with 3 company JSON configs

## [1.0.0] - 2026-01-21

### Added
- Initial release of Apollo.io MCP server
- Search tools:
  - `search_people` - Search for people by title, location, company
  - `search_companies` - Search for companies by location, industry, size
  - `search_local_businesses` - Convenience method for local business search
- Enrichment tools:
  - `enrich_person` - Reveal contact details (costs credits)
  - `enrich_company` - Get detailed company information
- Decision maker tools:
  - `find_decision_makers` - Find owners, CEOs, managers at companies
  - `find_email` - Find email for a person (costs credits)
- Account management:
  - `get_credit_balance` - Instructions for checking credit balance
- MCP package structure following SOP 11
- Full MCP integration with stdio transport
- Rate limiting (50 requests/minute)
- Comprehensive README with examples
