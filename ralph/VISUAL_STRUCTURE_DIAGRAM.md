# Hybrid Architecture Visual Structure

**Current State** (2026-01-21) - FULLY COMPLIANT ✅

```
dev-sandbox/
├── .git                           ← Single git repo (parent tracks all)
├── CLAUDE.md                      ← Agent instructions
├── .env                           ← All credentials/API keys
├── .gitmodules                    ← Website submodule configs
│
├── directives/                    ← Agent capability SOPs
├── docs/                          ← Architecture & guides
├── execution/                     ← Shared utilities (2+ projects)
├── methods/                       ← Internal frameworks
├── ralph/                         ← Migration & compliance docs
├── scripts/                       ← Automation scripts
├── templates/                     ← Project templates
│
└── projects/
    │
    ├── apollo-mcp/                ← STANDALONE MCP
    │   ├── src/apollo_mcp/        (Not company-specific)
    │   ├── templates/
    │   └── workflows/
    │
    ├── global-utility/            ← WILLIAM'S PERSONAL TOOLS
    │   ├── claude-framework/      (Not for clients)
    │   ├── mcp-aggregator/
    │   ├── md-to-pdf/
    │   ├── naples-weather/
    │   ├── registry/
    │   ├── resume/
    │   ├── time-blocks/
    │   └── twilio-mcp/
    │
    ├── product-ideas/             ← PRE-MARKET VALIDATION
    │   ├── amazon-buyer/          (Not yet launched)
    │   ├── crave-smart/
    │   ├── decide-for-her/
    │   ├── elder-tech-concierge/
    │   └── uber-lyft-comparison/
    │
    ├── shared/                    ← MULTI-TENANT (2+ companies) ⭐
    │   ├── ai-customer-service/   Used by: Marceau Solutions, SWFL HVAC
    │   ├── lead-scraper/          Used by: Marceau Solutions, SWFL HVAC, Square Foot
    │   ├── personal-assistant/    Used by: All companies + William
    │   └── social-media-automation/ Used by: Marceau Solutions, SWFL HVAC
    │
    ├── marceau-solutions/         ← COMPANY 1 (umbrella holding company)
    │   ├── amazon-seller/
    │   ├── fitness-influencer/
    │   ├── instagram-creator/
    │   ├── tiktok-creator/
    │   ├── website/               ✅ Git submodule → marceausolutions.com
    │   ├── website-builder/
    │   └── youtube-creator/
    │
    ├── square-foot-shipping/      ← COMPANY 2 (freight brokerage)
    │   └── lead-gen/
    │       ├── case-study/
    │       ├── lead-gen/
    │       └── quote-automation/
    │
    └── swflorida-hvac/            ← COMPANY 3 (HVAC contractor)
        ├── hvac-distributors/
        └── website/               ✅ Git submodule → swflorida-comfort-hvac
```

---

## Key Principles

### 1. Company-Centric Structure

Each company gets its own top-level folder:
- `marceau-solutions/` - Umbrella company (AI tools for creators)
- `square-foot-shipping/` - Freight brokerage
- `swflorida-hvac/` - HVAC contractor

**Projects go inside company folders**:
```
projects/marceau-solutions/fitness-influencer/
projects/swflorida-hvac/hvac-distributors/
projects/square-foot-shipping/lead-gen/
```

### 2. Shared Multi-Tenant Tools

Tools used by **2 or more companies** live in `projects/shared/`:

| Tool | Used By |
|------|---------|
| `lead-scraper` | All 3 companies |
| `ai-customer-service` | Marceau Solutions, SWFL HVAC |
| `social-media-automation` | Marceau Solutions, SWFL HVAC |
| `personal-assistant` | All companies + William |

**Why separate?**
- Shared codebase = single source of truth
- Updates benefit all companies
- Multi-tenant by design (business configs in `config/`)

### 3. Website Submodules

Each company's website is a **separate git repository** linked as a submodule:

```bash
# .gitmodules
[submodule "projects/marceau-solutions/website"]
  path = projects/marceau-solutions/website
  url = https://github.com/MarceauSolutions/marceausolutions.com

[submodule "projects/swflorida-hvac/website"]
  path = projects/swflorida-hvac/website
  url = https://github.com/MarceauSolutions/swflorida-comfort-hvac
```

**Why submodules?**
- Websites deploy independently (Netlify auto-deploys on push)
- Different repos = different deployment pipelines
- Can grant client access to website repo only (not entire dev-sandbox)

### 4. Global Utilities

William's personal tools (not client-facing) in `projects/global-utility/`:
- `claude-framework` - Meta-framework for building AI systems
- `mcp-aggregator` - Cross-MCP orchestration
- `md-to-pdf` - Document conversion
- `resume` - William's resume generator
- `time-blocks` - Time management

### 5. Product Ideas

Pre-market validation projects in `projects/product-ideas/`:
- Not yet launched
- Still in research/MVP phase
- May graduate to company folders or `shared/` later

### 6. Standalone MCPs

Some MCPs aren't company-specific:
- `apollo-mcp` - General-purpose Apollo.io integration
- Could be sold standalone or published to MCP registry

---

## Decision Tree: Where Does a New Project Go?

```
┌─────────────────────────────────────┐
│   New Project: "fitness-app"        │
└─────────────────┬───────────────────┘
                  │
                  ├─ Q1: Is this William's personal tool?
                  │  (Not client-facing, just for William)
                  │  └─ YES → projects/global-utility/fitness-app/
                  │  └─ NO ──┐
                  │          │
                  ├──────────┴─ Q2: Is this a pre-validation product idea?
                  │             (Not yet launched, still researching market)
                  │             └─ YES → projects/product-ideas/fitness-app/
                  │             └─ NO ──┐
                  │                     │
                  ├─────────────────────┴─ Q3: How many companies use it?
                  │                         └─ 1 company → projects/[company-name]/fitness-app/
                  │                         └─ 2+ companies → projects/shared/fitness-app/
                  │                         └─ 0 companies (standalone) → projects/fitness-app-mcp/
                  │
                  └─ Q4: Is this a website?
                     └─ YES → Create separate repo + add as submodule
                        projects/[company]/website/ → separate repo
```

---

## Examples

### Example 1: New Feature for One Company

**Scenario**: SWFL HVAC wants a "Parts Inventory Tracker"

**Decision**:
- Q1: Personal tool? NO (it's for SWFL HVAC)
- Q2: Pre-validation? NO (client requested it)
- Q3: How many companies? 1 (only SWFL HVAC)
- **Location**: `projects/swflorida-hvac/parts-inventory/`

### Example 2: Feature Used by Multiple Companies

**Scenario**: Both Marceau Solutions and SWFL HVAC want "Email Campaign Analytics"

**Decision**:
- Q1: Personal tool? NO
- Q2: Pre-validation? NO
- Q3: How many companies? 2 (Marceau + SWFL)
- **Location**: `projects/shared/email-campaign-analytics/`

**Multi-tenant config**:
```python
# projects/shared/email-campaign-analytics/config/
marceau_solutions.json
swflorida_hvac.json
```

### Example 3: William's Internal Research

**Scenario**: William wants to build "AI Research Paper Summarizer" for personal use

**Decision**:
- Q1: Personal tool? YES (just for William)
- **Location**: `projects/global-utility/research-summarizer/`

### Example 4: New Company Website

**Scenario**: New company "Crave Smart" needs a website

**Steps**:
1. Create separate GitHub repo: `github.com/MarceauSolutions/crave-smart-website`
2. Deploy to Netlify (auto-deploy on push)
3. Add as submodule:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   git submodule add https://github.com/MarceauSolutions/crave-smart-website projects/crave-smart/website
   ```
4. Edit `.gitmodules` to add entry

### Example 5: Standalone MCP for Publishing

**Scenario**: Build "Stripe MCP" to sell on Claude marketplace

**Decision**:
- Q1: Personal tool? NO
- Q2: Pre-validation? Maybe (if not yet launched)
- Q3: How many companies? 0 (it's a product to sell)
- **Location**: `projects/stripe-mcp/` (standalone)

**Publishing**:
- SOP 11-14: Package → PyPI → MCP Registry
- Separate production repo: `/Users/williammarceaujr./stripe-mcp-prod/`

---

## Visual Comparison: Before vs After

### ❌ Before (Flat Structure)

```
projects/
├── fitness-influencer/        ← Who owns this?
├── lead-scraper/              ← Used by who?
├── amazon-seller/             ← Marceau project?
├── hvac-distributors/         ← SWFL project?
├── ai-customer-service/       ← Shared?
└── social-media-automation/   ← Shared?
```

**Problems**:
- Hard to tell who owns what
- Shared tools mixed with single-company projects
- No clear ownership
- Difficult to filter by company

### ✅ After (Hybrid Architecture)

```
projects/
├── marceau-solutions/
│   ├── fitness-influencer/    ← Clear: Marceau owns this
│   └── amazon-seller/         ← Clear: Marceau owns this
├── swflorida-hvac/
│   └── hvac-distributors/     ← Clear: SWFL owns this
├── shared/
│   ├── lead-scraper/          ← Clear: Used by all companies
│   └── ai-customer-service/   ← Clear: Shared multi-tenant
└── global-utility/
    └── resume/                ← Clear: William's personal tool
```

**Benefits**:
- Instant clarity on ownership
- Easy to filter: `ls projects/marceau-solutions/` shows all Marceau projects
- Shared tools explicitly labeled
- Personal vs client tools separated
- Product ideas isolated

---

## Git Workflow

### Single Parent Repo

```bash
# Only ONE .git directory
find . -name ".git" -type d
# Output: ./.git

# All projects tracked in single repo
cd /Users/williammarceaujr./dev-sandbox
git status
# Shows changes in ALL projects
```

### Submodules (Websites Only)

```bash
# Websites are separate repos
cd projects/marceau-solutions/website
git status  # This is a SEPARATE repo

# Update website
cd projects/marceau-solutions/website
git pull origin main
cd ../..
git add projects/marceau-solutions/website
git commit -m "Update website submodule"
```

### Deployment (Separate Repos)

```bash
# Deploy creates SEPARATE production repos
python deploy_to_skills.py --project lead-scraper --version 1.0.0

# Creates:
/Users/williammarceaujr./lead-scraper-prod/  ← Separate repo (sibling to dev-sandbox)

# NOT nested:
# ❌ /Users/williammarceaujr./dev-sandbox/lead-scraper-prod/  (WRONG)
# ✅ /Users/williammarceaujr./lead-scraper-prod/  (CORRECT)
```

---

## Compliance Checklist

| Item | Status |
|------|--------|
| ✅ Company folders exist | 3 companies (marceau-solutions, square-foot-shipping, swflorida-hvac) |
| ✅ Shared folder named correctly | `projects/shared/` (not `shared-multi-tenant/`) |
| ✅ Website submodules configured | 2 submodules (marceau, swfl) |
| ✅ Global utilities separated | `projects/global-utility/` |
| ✅ Product ideas separated | `projects/product-ideas/` |
| ✅ Standalone MCPs isolated | `projects/apollo-mcp/` |
| ✅ No nested repos | Only `./.git` at root |
| ✅ All docs reference correct paths | 62 files updated |
| ✅ All scripts reference correct paths | 3 files updated |
| ✅ All cron jobs reference correct paths | 10+ cron jobs updated |

---

## Migration Complete ✅

**Date**: 2026-01-21
**Status**: Fully compliant with hybrid architecture
**Files Updated**: 62 documentation files
**Scripts Updated**: 3 automation scripts
**Cron Jobs Updated**: 10+ scheduled tasks
**Remaining Issues**: 0

**See**: `ralph/FINAL_COMPLIANCE_REPORT.md` for detailed audit results
