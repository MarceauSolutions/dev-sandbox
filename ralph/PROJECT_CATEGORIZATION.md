# Project Categorization Analysis

**Created:** 2026-01-20
**Purpose:** Categorize all 27 projects in dev-sandbox by company ownership
**Status:** Story 002 - Categorization Complete

---

## Categorization Framework

### Categories
1. **Shared Multi-Tenant** - Used by all 3 companies with business_id separation
2. **Marceau Solutions** - AI automation, lead gen, websites, content creation products
3. **SW Florida HVAC** - HVAC-specific tools
4. **Shipping Logistics** - Logistics-specific tools
5. **Global Utility** - MCP servers, frameworks, personal tools (no business affiliation)
6. **Product Ideas** - Future revenue products (need to assign to a company)

---

## PROJECT CATEGORIZATION (27 projects)

### SHARED MULTI-TENANT (4 projects)
*Used by ALL 3 companies - business_id separation in code/data*

1. **lead-scraper** → `projects/shared-multi-tenant/lead-scraper/`
   - Lead generation for all 3 businesses
   - Has business_id separation in code
   - Used by: Marceau, HVAC, Shipping

2. **social-media-automation** → `projects/shared-multi-tenant/social-media-automation/`
   - Social posting for all 3 businesses
   - Business separation already exists
   - Used by: Marceau, HVAC, Shipping

3. **ai-customer-service** → `projects/shared-multi-tenant/ai-customer-service/`
   - Voice AI phone ordering for all 3 businesses
   - Restaurant phone ordering system (can be adapted for HVAC quotes, shipping quotes)
   - Used by: Marceau, HVAC, Shipping

4. **personal-assistant** → `projects/shared-multi-tenant/personal-assistant/`
   - William's personal digest/calendar system
   - Global utility - no business affiliation
   - Used by: All (personal productivity)

---

### MARCEAU SOLUTIONS (8 projects)
*AI automation, lead gen, websites, content creation - Marceau's core business offerings*

5. **fitness-influencer** → `projects/marceau-solutions/fitness-influencer/`
   - AI automation suite for fitness creators
   - Marceau product offering (SaaS)
   - MCP published

6. **website-builder** → `projects/marceau-solutions/website-builder/`
   - Automated website generation powered by AI
   - Marceau service offering
   - Part of lead-gen-to-website conversion funnel

7. **instagram-creator** → `projects/marceau-solutions/instagram-creator/`
   - Instagram automation MCP
   - Marceau product offering
   - MCP published

8. **tiktok-creator** → `projects/marceau-solutions/tiktok-creator/`
   - TikTok automation MCP
   - Marceau product offering
   - MCP published

9. **youtube-creator** → `projects/marceau-solutions/youtube-creator/`
   - YouTube automation MCP
   - Marceau product offering
   - MCP published

10. **Automated_SocialMedia_Campaign** → `projects/marceau-solutions/automated-social-media-campaign/`
    - Early social media automation (predecessor to social-media-automation)
    - Marceau offering
    - Consider: Merge with social-media-automation or archive?

11. **interview-prep** → `projects/marceau-solutions/interview-prep/`
    - PowerPoint generator for interview prep
    - Marceau product idea (career services)
    - Could be productized

12. **amazon-seller** → `projects/marceau-solutions/amazon-seller/`
    - Amazon SP-API tools for sellers
    - Marceau product offering (published MCP)
    - Helps e-commerce businesses

---

### SW FLORIDA HVAC (1 project)

13. **hvac-distributors** → `projects/swflorida-hvac/hvac-distributors/`
    - RFQ system for HVAC equipment quotes
    - HVAC-specific tool
    - Used by: HVAC business only

---

### SHIPPING LOGISTICS (0 projects)
*No existing projects - placeholder for future*

**Future projects:**
- Shipping quote comparison
- Freight tracking
- Logistics optimization

---

### GLOBAL UTILITY (9 projects)
*MCP servers, frameworks, personal tools - no specific business affiliation*

14. **md-to-pdf** → `projects/global-utility/md-to-pdf/`
    - Markdown to PDF converter MCP
    - General utility (published MCP)
    - Used across all projects for documentation

15. **twilio-mcp** → `projects/global-utility/twilio-mcp/`
    - Twilio SMS MCP server
    - General utility (published MCP)
    - Used by lead-scraper and ai-customer-service

16. **claude-framework** → `projects/global-utility/claude-framework/`
    - Claude Code "operating system"
    - Development framework
    - Meta-project for this workspace

17. **registry** → `projects/global-utility/registry/`
    - MCP Registry (upstream from Anthropic)
    - Publishing tool, not a business project
    - Used for publishing other MCPs

18. **mcp-aggregator** → `projects/global-utility/mcp-aggregator/`
    - Universal MCP aggregation platform
    - Tier 2 aggregation layer
    - General platform (not company-specific)

19. **naples-weather** → `projects/global-utility/naples-weather/`
    - Weather report generator for Naples, FL
    - Personal utility / local info
    - Could be used for social media content

20. **time-blocks** → `projects/global-utility/time-blocks/`
    - Personal productivity calendar tool
    - William's personal tool
    - No business affiliation

21. **resume** → `projects/global-utility/resume/`
    - William's resume project
    - Personal, not business
    - No business affiliation

22. **shared** → `projects/global-utility/shared/`
    - Shared utilities across multiple projects
    - Global utility library
    - Used by all projects

---

### PRODUCT IDEAS (5 projects)
*Future revenue products - need company assignment*

23. **crave-smart** → `projects/product-ideas/crave-smart/`
    - Food craving prediction app (menstrual cycle-based)
    - Product idea (not developed)
    - **Assign to:** Marceau Solutions? (consumer app)

24. **decide-for-her** → `projects/product-ideas/decide-for-her/`
    - Decision-making app for women
    - Product idea (not developed)
    - **Assign to:** Marceau Solutions? (consumer app)

25. **elder-tech-concierge** → `projects/product-ideas/elder-tech-concierge/`
    - White-glove AI setup for seniors
    - Product idea (v0.1.0-dev)
    - **Assign to:** Marceau Solutions? (service offering)

26. **amazon-buyer** → `projects/product-ideas/amazon-buyer/`
    - Amazon buying tools
    - Product idea (not developed)
    - **Assign to:** Marceau Solutions? (e-commerce tools)

27. **uber-lyft-comparison** → `projects/product-ideas/uber-lyft-comparison/`
    - Rideshare price comparison
    - Product idea (SOP 9 exploration phase)
    - **Assign to:** Marceau Solutions? (consumer app)

---

## MIGRATION MAPPING

### Shared Multi-Tenant (4 projects)
```
projects/lead-scraper/              → projects/shared-multi-tenant/lead-scraper/
projects/social-media-automation/   → projects/shared-multi-tenant/social-media-automation/
projects/ai-customer-service/       → projects/shared-multi-tenant/ai-customer-service/
projects/personal-assistant/        → projects/shared-multi-tenant/personal-assistant/
```

### Marceau Solutions (8 projects)
```
projects/fitness-influencer/        → projects/marceau-solutions/fitness-influencer/
projects/website-builder/           → projects/marceau-solutions/website-builder/
projects/instagram-creator/         → projects/marceau-solutions/instagram-creator/
projects/tiktok-creator/            → projects/marceau-solutions/tiktok-creator/
projects/youtube-creator/           → projects/marceau-solutions/youtube-creator/
projects/Automated_SocialMedia_Campaign/ → projects/marceau-solutions/automated-social-media-campaign/
projects/interview-prep/            → projects/marceau-solutions/interview-prep/
projects/amazon-seller/             → projects/marceau-solutions/amazon-seller/
```

### SW Florida HVAC (1 project)
```
projects/hvac-distributors/         → projects/swflorida-hvac/hvac-distributors/
```

### Shipping Logistics (0 projects)
```
[Create placeholder: projects/shipping-logistics/README.md]
```

### Global Utility (9 projects)
```
projects/md-to-pdf/                 → projects/global-utility/md-to-pdf/
projects/twilio-mcp/                → projects/global-utility/twilio-mcp/
projects/claude-framework/          → projects/global-utility/claude-framework/
projects/registry/                  → projects/global-utility/registry/
projects/mcp-aggregator/            → projects/global-utility/mcp-aggregator/
projects/naples-weather/            → projects/global-utility/naples-weather/
projects/time-blocks/               → projects/global-utility/time-blocks/
projects/resume/                    → projects/global-utility/resume/
projects/shared/                    → projects/global-utility/shared/
```

### Product Ideas (5 projects)
```
projects/crave-smart/               → projects/product-ideas/crave-smart/
projects/decide-for-her/            → projects/product-ideas/decide-for-her/
projects/elder-tech-concierge/      → projects/product-ideas/elder-tech-concierge/
projects/amazon-buyer/              → projects/product-ideas/amazon-buyer/
projects/uber-lyft-comparison/      → projects/product-ideas/uber-lyft-comparison/
```

---

## DOCUMENTATION CATEGORIZATION

### Marceau Solutions Docs (move to `docs/companies/marceau-solutions/`)

**Strategy & Business**
- `AI-VOICE-SERVICE-ECONOMICS.md`
- `MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md`
- `COLD-OUTREACH-STRATEGY-JAN-19-2026.md`
- `CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md`
- `BUSINESS-MODEL-OPTIONS-ANALYSIS.md`
- `MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md`
- `EXECUTION-PLAN-WEEK-JAN-19-2026.md`

**Operations & Tracking**
- `API-USAGE-COST-CHECKER.md`
- `APOLLO-IO-MAXIMIZATION-PLAN.md`
- `COST-BUDGET-TRACKING-JAN-19-2026.md`
- `LEAD-TRACKING-FOLLOWUP-SYSTEM.md`
- `ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md`
- `ACTION-ITEMS-JAN-20-2026.md`
- `EXECUTION-SUMMARY-JAN-19-2026.md`
- `GROK-IMAGE-COLD-OUTREACH-JAN-19-2026.md`

**Market Analysis**
- `output/AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md`
- `output/ai-automation-agency-market-research-2026.md`
- `projects/fitness-influencer/market-analysis/FITNESS_INFLUENCER_MARKET_ANALYSIS_JAN2026.md`
- `projects/personal-assistant/output/ai-customer-service-market-opportunity-jan-2026.md`
- `projects/personal-assistant/output/ai-job-market-report-jan-2026.md`

### SW Florida HVAC Docs (move to `docs/companies/swflorida-hvac/`)

**Business Plan**
- `3-PHASE-HVAC-PLAN-JAN-19-2026.md`

**Future:**
- HVAC pricing models
- Service area maps
- Social media content calendar
- Lead conversion tracking

### Shipping Logistics Docs (move to `docs/companies/shipping-logistics/`)

**Future:**
- Shipping business plan
- Route optimization docs
- Quote comparison workflows

### Global Docs (STAY AT ROOT `docs/`)

**Architecture & Framework**
- `ARCHITECTURE-CONFLICT-RESOLUTION.md`
- `COMPREHENSIVE-CONFLICT-AUDIT.md`
- `EXECUTION-FOLDER-AUDIT.md`
- `DEPLOYMENT_GUIDE.md`
- All `architecture-*.md`
- All `deployment-*.md`
- All `testing-*.md`
- All SOPs and workflow guides

**Amazon Setup** (Global utility)
- `AMAZON_QUICK_START.md`
- `AMAZON_QUICK_START.pdf`
- `AMAZON_SETUP.md`
- `AMAZON_SETUP.pdf`

**Development Guides**
- `BUSINESS-SETUP-STATUS.md`
- `COST-TRACKING.md`
- `MULTI-BUSINESS-FORM-SYSTEM.md`
- `NGROK-AI-GATEWAY-SETUP.md`
- `X-ACCOUNT-SETUP-GUIDE.md`
- `mobile-app-development-guide.md`
- `multi-tier-agent-architecture.md`

---

## TEMPLATES CATEGORIZATION

### Marceau Solutions Templates

**SMS Templates** (move to `templates/companies/marceau-solutions/sms/`)
- Lead scraper SMS templates
- Cold outreach templates
- Follow-up sequences

**Email Templates** (move to `templates/companies/marceau-solutions/email/`)
- Cold email templates
- Nurture sequences
- Service offering emails

**Form Templates** (move to `templates/companies/marceau-solutions/forms/`)
- Lead intake forms
- Service request forms
- Contact forms

### SW Florida HVAC Templates

**SMS Templates** (move to `templates/companies/swflorida-hvac/sms/`)
- HVAC service reminders
- Quote follow-ups
- Seasonal maintenance offers

**Email Templates** (move to `templates/companies/swflorida-hvac/email/`)
- Service confirmation emails
- Estimate emails
- Newsletter templates

### Shipping Logistics Templates

**SMS Templates** (move to `templates/companies/shipping-logistics/sms/`)
- Quote request templates
- Shipment tracking notifications

**Email Templates** (move to `templates/companies/shipping-logistics/email/`)
- Quote confirmation
- Shipment updates

### Shared Templates (STAY AT `templates/shared/`)
- `project-kickoff-questionnaire.md`
- Generic form templates
- Global email signatures

---

## OUTPUT FILES CATEGORIZATION

### Current State
```
output/
├── AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md  → Marceau
├── ai-automation-agency-market-research-2026.md → Marceau
└── form_submissions/                          → Multi-tenant (has business_id)
```

### New Structure
```
output/
├── companies/
│   ├── marceau-solutions/
│   │   ├── market-analysis/
│   │   │   ├── AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md
│   │   │   └── ai-automation-agency-market-research-2026.md
│   │   └── campaigns/
│   ├── swflorida-hvac/
│   │   └── campaigns/
│   └── shipping-logistics/
│       └── campaigns/
└── shared/
    └── form_submissions/  (has business_id separation in data)
```

---

## DEPENDENCIES & CROSS-REFERENCES

### Projects with Dependencies
1. **lead-scraper** → Uses `execution/form_handler.py`, `execution/clickup_sync.py`
2. **social-media-automation** → Uses `execution/` utilities
3. **ai-customer-service** → Uses Twilio MCP, form_handler
4. **fitness-influencer** → Uses video processing from `execution/`
5. **website-builder** → Uses lead-scraper data

### Shared Execution Layer (UNCHANGED)
- `execution/form_handler.py` - Used by all form-based projects
- `execution/clickup_sync.py` - CRM integration for all 3 companies
- `execution/google_sheets_handler.py` - Data storage for all
- All shared utilities stay in `execution/` (no changes)

---

## QUESTIONS FOR WILLIAM

### Product Ideas - Which Company?
1. **crave-smart** - Marceau Solutions? (consumer app product)
2. **decide-for-her** - Marceau Solutions? (consumer app product)
3. **elder-tech-concierge** - Marceau Solutions? (service offering)
4. **amazon-buyer** - Marceau Solutions? (e-commerce tools)
5. **uber-lyft-comparison** - Marceau Solutions? (consumer app)

**Recommendation:** All 5 → Marceau Solutions (all are product ideas for Marceau's portfolio)

### Archive Candidates
1. **Automated_SocialMedia_Campaign** - Superseded by social-media-automation?
   - Action: Archive or merge into social-media-automation

---

## SUMMARY STATS

| Category | Count | Destination |
|----------|-------|-------------|
| **Shared Multi-Tenant** | 4 | `projects/shared-multi-tenant/` |
| **Marceau Solutions** | 8 | `projects/marceau-solutions/` |
| **SW Florida HVAC** | 1 | `projects/swflorida-hvac/` |
| **Shipping Logistics** | 0 | `projects/shipping-logistics/` (placeholder) |
| **Global Utility** | 9 | `projects/global-utility/` |
| **Product Ideas** | 5 | `projects/product-ideas/` → Marceau? |
| **TOTAL** | **27** | |

---

## NEXT STEPS

1. Review product ideas assignment → Confirm all go to Marceau
2. Decide on Automated_SocialMedia_Campaign → Archive or merge?
3. Create migration script (Story 003)
4. **CHECKPOINT:** Review before executing file moves

---

**Status:** CATEGORIZATION COMPLETE - Ready for Story 003 (Migration Script)
