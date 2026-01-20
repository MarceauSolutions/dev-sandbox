# Multi-Company Folder Structure Migration Plan

**Created:** 2026-01-20
**Status:** DESIGN PHASE - NOT YET EXECUTED
**Objective:** Organize dev-sandbox to clearly separate 3 companies while preserving DOE architecture

---

## Current State Analysis

### Companies Operating in dev-sandbox
1. **Marceau Solutions** - AI automation, lead gen, websites, AI voice services
2. **SW Florida HVAC** - HVAC services, local service business
3. **Shipping Logistics** - Logistics/freight services

### Current Problem
- All projects mixed in `projects/` directory
- No clear separation when working on company-specific tasks
- Shared projects (lead-scraper, social-media-automation, ai-customer-service) used by all 3 companies
- Documentation scattered - hard to find company-specific docs vs global docs

### Current Structure
```
dev-sandbox/
├── projects/                    # MIXED - all projects together
│   ├── lead-scraper/            (shared by all 3 - has business_id separation)
│   ├── social-media-automation/ (shared by all 3)
│   ├── ai-customer-service/     (shared by all 3)
│   ├── personal-assistant/      (global)
│   ├── fitness-influencer/      (marceau-only product idea)
│   ├── [25+ other projects]
├── docs/                        # MIXED - all docs together
├── execution/                   # Global utilities (DOE Layer 3)
├── directives/                  # Global directives (DOE Layer 1)
├── methods/                     # Internal frameworks
├── templates/                   # MIXED templates
└── output/                      # MIXED outputs
```

---

## Proposed New Structure

### Key Principles
1. **PRESERVE DOE ARCHITECTURE** - execution/, directives/, methods/ stay unchanged
2. **PRESERVE DEPLOYMENT MODEL** - deploy_to_skills.py still works, deploys to ~/[project]-prod/
3. **ORGANIZE WITHIN dev-sandbox** - NO separate company repos, NO nested .git
4. **CLEAR COMPANY SEPARATION** - Instantly know which folder for each company
5. **SHARED EFFICIENCY** - Multi-tenant projects work seamlessly for all 3

### New Folder Structure

```
dev-sandbox/
├── .git/                        # UNCHANGED - Single root git repo
├── CLAUDE.md                    # UPDATED - Add folder structure guide
├── deploy_to_skills.py          # UPDATED - Paths updated
│
├── projects/                    # REORGANIZED by ownership
│   ├── shared-multi-tenant/     # NEW: Projects used by ALL 3 companies
│   │   ├── lead-scraper/        (has business_id separation in code)
│   │   ├── social-media-automation/
│   │   ├── ai-customer-service/ (voice AI for all 3)
│   │   └── personal-assistant/  (global digest/calendar)
│   │
│   ├── marceau-solutions/       # NEW: Marceau-only projects
│   │   ├── fitness-influencer/  (marceau product idea)
│   │   └── [future marceau projects]
│   │
│   ├── swflorida-hvac/          # NEW: HVAC-only projects
│   │   └── [future hvac projects - placeholder]
│   │
│   └── shipping-logistics/      # NEW: Shipping-only projects
│       └── [future shipping projects - placeholder]
│
├── docs/                        # REORGANIZED - global + company-specific
│   ├── companies/               # NEW: Company-specific docs
│   │   ├── marceau-solutions/
│   │   │   ├── AI-VOICE-SERVICE-ECONOMICS.md
│   │   │   ├── MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md
│   │   │   ├── market-analysis/
│   │   │   └── strategy/
│   │   ├── swflorida-hvac/
│   │   │   ├── 3-PHASE-HVAC-PLAN-JAN-19-2026.md
│   │   │   ├── business-plan/
│   │   │   └── social-media/
│   │   └── shipping-logistics/
│   │       └── [future shipping docs]
│   │
│   └── [ALL GLOBAL DOCS STAY AT ROOT]
│       ├── architecture-guide.md
│       ├── deployment.md
│       ├── testing-strategy.md
│       ├── repository-management.md
│       └── [all SOPs, workflows, global guides]
│
├── output/                      # REORGANIZED by company
│   ├── companies/               # NEW: Company-specific outputs
│   │   ├── marceau-solutions/
│   │   ├── swflorida-hvac/
│   │   └── shipping-logistics/
│   │
│   └── [shared outputs stay at root]
│       ├── form_submissions/    (has business_id in data)
│       └── AI-ASSISTANT-MCP-MARKET-ANALYSIS-2026.md
│
├── templates/                   # REORGANIZED by company
│   ├── companies/               # NEW: Company-specific templates
│   │   ├── marceau-solutions/
│   │   │   ├── sms/
│   │   │   ├── email/
│   │   │   └── forms/
│   │   ├── swflorida-hvac/
│   │   │   ├── sms/
│   │   │   ├── email/
│   │   │   └── forms/
│   │   └── shipping-logistics/
│   │       ├── sms/
│   │       ├── email/
│   │       └── forms/
│   │
│   └── shared/                  # Global templates
│       └── project-kickoff-questionnaire.md
│
├── execution/                   # UNCHANGED - DOE Execution Layer
├── directives/                  # UNCHANGED - DOE Directive Layer
├── methods/                     # UNCHANGED - Internal frameworks
├── ralph/                       # UNCHANGED - PRD execution system
└── scripts/                     # UNCHANGED - Global scripts
```

---

## Project Categorization

### Shared Multi-Tenant Projects (ALL 3 companies use)
- **lead-scraper** - Lead generation for all 3 businesses (business_id separation)
- **social-media-automation** - Social posting for all 3 (business separation exists)
- **ai-customer-service** - Voice AI for all 3 businesses
- **personal-assistant** - Global digest/calendar (William's personal)

### Company-Specific Projects

#### Marceau Solutions
- **fitness-influencer** - Product idea for fitness creators (marceau offering)
- Future: **website-builder**, **decide-for-her**, **crave-smart**

#### SW Florida HVAC
- No existing projects yet (all current work uses shared multi-tenant tools)
- Future: HVAC-specific booking, quoting, scheduling tools

#### Shipping Logistics
- No existing projects yet
- Future: Shipping-specific quote tools, tracking, logistics

### Uncategorized/General Projects (need review)
- **amazon-seller**, **amazon-buyer** - Which company?
- **claude-framework** - Global utility?
- **elder-tech-concierge** - Product idea for which company?
- **hvac-distributors** - Related to HVAC business?
- **instagram-creator**, **tiktok-creator**, **youtube-creator** - Shared?
- **mcp-aggregator** - Global utility
- **md-to-pdf** - Global utility
- **naples-weather** - Global utility
- **registry** - MCP registry (global)
- **resume** - Personal
- **time-blocks** - Personal
- **twilio-mcp** - Global utility
- **uber-lyft-comparison** - Product idea?
- **website-builder** - Marceau offering?

---

## Documentation Categorization

### Marceau Solutions Docs (move to `docs/companies/marceau-solutions/`)
- `AI-VOICE-SERVICE-ECONOMICS.md`
- `MARCEAU-SOLUTIONS-COMPLETE-SERVICE-OFFERING.md`
- `COLD-OUTREACH-STRATEGY-JAN-19-2026.md`
- `CUSTOMER-ACQUISITION-STRATEGY-JAN-19-2026.md`
- `API-USAGE-COST-CHECKER.md`
- `APOLLO-IO-MAXIMIZATION-PLAN.md`
- `BUSINESS-MODEL-OPTIONS-ANALYSIS.md`
- `COST-BUDGET-TRACKING-JAN-19-2026.md`
- `EXECUTION-PLAN-WEEK-JAN-19-2026.md`
- `LEAD-TRACKING-FOLLOWUP-SYSTEM.md`
- `MAKE-MONEY-FIRST-STRATEGY-JAN-19-2026.md`
- Market analysis from `projects/fitness-influencer/market-analysis/`
- Market analysis from `projects/personal-assistant/output/ai-*.md`

### SW Florida HVAC Docs (move to `docs/companies/swflorida-hvac/`)
- `3-PHASE-HVAC-PLAN-JAN-19-2026.md`
- `ACTUAL-COSTS-AND-LEADS-STATUS-JAN-19-2026.md` (if HVAC-specific)
- Future: HVAC business plan, pricing, social media ready content

### Shipping Logistics Docs (move to `docs/companies/shipping-logistics/`)
- None yet - placeholder for future

### Global Docs (STAY AT ROOT `docs/`)
- `ARCHITECTURE-CONFLICT-RESOLUTION.md`
- `COMPREHENSIVE-CONFLICT-AUDIT.md`
- `EXECUTION-FOLDER-AUDIT.md`
- `DEPLOYMENT_GUIDE.md`
- All architecture guides
- All SOPs and workflows
- All testing strategy docs
- All deployment guides

---

## Migration Strategy

### Phase 1: Create New Structure (Story 003)
1. Create company directories
2. Create README.md for each company
3. NO file moves yet - just structure

### Phase 2: Categorize & Map (Story 002)
1. Audit all projects - determine ownership
2. Create file mapping (old path → new path)
3. Identify cross-company dependencies

### Phase 3: Execute Migration (Story 003-004)
1. Run migration script with `--dry-run` first
2. Review dry-run output
3. **CHECKPOINT: Get approval before executing**
4. Execute migration with `git mv` (preserves history)
5. Single atomic commit

### Phase 4: Update References (Story 005)
1. Update all Python imports
2. Update deploy_to_skills.py paths
3. Update CLAUDE.md documentation
4. Test all projects still work

---

## Git Safety

### Rules
1. **Single .git repo** - NO nested .git directories
2. **Use git mv** - Preserve file history
3. **Atomic commit** - All moves in single commit
4. **Test before commit** - Verify nothing breaks
5. **Rollback script** - Create before executing

### Verification Commands
```bash
# Check for nested repos (should only show ./.git)
find . -name ".git" -type d

# Check git status
git status

# Verify no broken imports
python -m pytest  # if tests exist
```

---

## Import Strategy

### Old Imports (BEFORE migration)
```python
from projects.lead_scraper.src import scraper
from projects.social_media_automation.src import scheduler
```

### New Imports (AFTER migration)
```python
# Shared multi-tenant projects
from projects.shared_multi_tenant.lead_scraper.src import scraper
from projects.shared_multi_tenant.social_media_automation.src import scheduler

# Company-specific projects
from projects.marceau_solutions.fitness_influencer.src import analyzer

# Global utilities (UNCHANGED)
from execution.form_handler import FormHandler
```

### Migration Script Handles
- Automatically update all imports
- Preserve functionality
- Test each import path

---

## Deployment Model (UNCHANGED)

### Current Model (PRESERVED)
```bash
# Deploy from shared multi-tenant
python deploy_to_skills.py --project lead-scraper --version 1.2.0
# Creates: ~/lead-scraper-prod/

# Deploy from company-specific
python deploy_to_skills.py --project fitness-influencer --version 1.0.0
# Creates: ~/fitness-influencer-prod/
```

### What Changes
- Internal paths in deploy_to_skills.py config
- Example: `projects/lead-scraper/` → `projects/shared-multi-tenant/lead-scraper/`

### What Stays Same
- Deployment destinations (~/[project]-prod/)
- Deployment workflow
- Version control
- All external integrations

---

## Success Criteria

### Clarity
- Developer instantly knows which folder for each company
- Company-specific work isolated in dedicated folders
- Shared projects clearly marked as multi-tenant

### Isolation
- Marceau work doesn't pollute HVAC folders
- HVAC work doesn't pollute Shipping folders
- Each company has dedicated: projects/, docs/, output/, templates/

### Shared Efficiency
- Multi-tenant projects (lead-scraper, social, voice AI) work for all 3
- No duplication of shared code
- Business_id separation maintained in data

### Git Safety
- Single .git repo
- No nested repos
- Clean history preserved
- All tests pass

### Backward Compatibility
- All existing commands work (with updated paths)
- deploy_to_skills.py works
- All integrations work
- No broken imports

---

## Rollback Plan

### If Migration Fails
1. Run `rollback_migration.py` (created in Story 003)
2. Restores all files to original locations
3. Restores all imports to original paths
4. Single `git revert` command

### Rollback Testing
- Test rollback script on a branch first
- Verify full restoration
- Keep backup before executing

---

## Next Steps

1. **Story 002**: Audit all projects and categorize
2. **Story 003**: Create migration script (CHECKPOINT before execute)
3. **Story 004**: Migrate docs/templates/output
4. **Story 005**: Update imports and test

---

## Questions to Resolve

1. **Project ownership** - Determine which company owns:
   - amazon-seller, amazon-buyer
   - elder-tech-concierge
   - hvac-distributors
   - website-builder
   - creator tools (instagram, tiktok, youtube)
   - uber-lyft-comparison

2. **Template organization** - Which SMS/email templates belong to which company?

3. **Output organization** - Which output files are company-specific vs shared?

4. **Cross-company dependencies** - Any projects that reference each other?

---

**Status:** DESIGN COMPLETE - Ready for Story 002 (Categorization)
