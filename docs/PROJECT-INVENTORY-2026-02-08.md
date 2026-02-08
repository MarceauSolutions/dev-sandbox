# Project Inventory & Deployment Assessment

**Date**: 2026-02-08
**Purpose**: Evaluate all projects for deployment per SOP 31 (AI Assistants) and SOP 3 (Skills)

## Deployment Targets

| Target | Location | Purpose |
|--------|----------|---------|
| **AI Assistants** | `~/ai-assistants/[name]/` | Standalone tools for fresh Claude or sale |
| **Skills** | `~/production/[name]-prod/` | Tools for dev-sandbox Claude |
| **Keep in dev-sandbox** | `projects/` | Still in development |
| **Archive** | `~/archived/` | Deprecated or replaced |

---

## Already Deployed

### Production Skills (~/production/)
| Name | Status | Notes |
|------|--------|-------|
| crm-onboarding-prod | ✅ Deployed | CRM setup workflow |
| email-analyzer-prod | ✅ Deployed | Email analysis tool |
| hvac-distributors-prod | ✅ Deployed | Lead scraper for HVAC |
| interview-prep-prod | ✅ Deployed | Interview preparation |
| lead-scraper-prod | ✅ Deployed | General lead scraping |
| time-blocks-prod | ✅ Deployed | Time blocking tool |

### AI Assistants (~/ai-assistants/)
| Name | Status | Notes |
|------|--------|-------|
| upwork-proposal-generator | ✅ Deployed | Generates Upwork proposals |
| website-builder | ✅ Deployed | AI website generation with social research |

---

## Projects to Evaluate

### Shared Projects (projects/shared/)

| Project | Description | Readiness | Recommended Action |
|---------|-------------|-----------|-------------------|
| ai-customer-service | AI support system | ⚠️ Evaluate | Check completion |
| apollo-mcp | Apollo.io MCP | ✅ Ready | **MCP** v1.1.0 - Ready for PyPI/Registry (SOP 12-13) |
| canva-mcp | Canva integration | ❌ Incomplete | Placeholder only - needs implementation |
| lead-scraper | Lead scraping system | ✅ Ready | Already in production |
| n8n-workflows | n8n workflow storage | ✅ Ready | Keep as is (storage) |
| personal-assistant | Daily digest system | ✅ Evaluated | **Skill** (not AI Assistant) - uses personal OAuth, routes to other skills |
| social-media-automation | Social posting | ✅ Evaluated | **Skill** - VERSION added, needs TikTok API completion |
| source-pointer | Source tracking | ⚠️ Evaluate | Check completion |
| ticket-aggregator-mcp | Support tickets | ✅ Ready | **MCP** v1.0.0 - Ready for PyPI/Registry (SOP 12-13) |
| upwork-mcp | Upwork integration | ✅ Ready | **MCP** v1.0.1 - Ready for PyPI/Registry (SOP 12-13) |

### Marceau Solutions Projects (projects/marceau-solutions/)

| Project | Description | Readiness | Recommended Action |
|---------|-------------|-----------|-------------------|
| amazon-seller | Amazon seller tools | ⚠️ Evaluate | Could be AI Assistant |
| fitness-influencer | Fitness AI platform | ⚠️ Evaluate | Complex - needs Ralph |
| fitness-influencer-mcp | MCP version | ⚠️ Evaluate | Check if MCP ready |
| instagram-creator | IG content tools | ✅ Ready | **MCP** v1.0.0 - Ready for PyPI/Registry (SOP 12-13) |
| interview-prep | Interview prep | ✅ Ready | Already in production |
| tiktok-creator | TikTok tools | ✅ Ready | **MCP** v1.0.0 - Ready for PyPI/Registry (SOP 12-13) |
| trainerize-mcp | Trainerize MCP | ⚠️ Evaluate | Check if MCP ready |
| vuori-lead-magnet | Lead magnet | ⚠️ Evaluate | Check completion |
| website | Company website | ✅ Ready | Separate repo |
| website-builder | Website gen | ✅ Deployed | **AI Assistant** at ~/ai-assistants/website-builder/ |
| youtube-creator | YouTube tools | ✅ Ready | **MCP** v1.0.0 - Ready for PyPI/Registry (SOP 12-13) |

### Other Projects (projects/)

| Project | Description | Readiness | Recommended Action |
|---------|-------------|-----------|-------------------|
| Go-Tracker | Go game tracker | ⚠️ Evaluate | Personal project |
| apollo-mcp | Apollo duplicate | ✅ Removed | Moved to archived/ (duplicate of shared/) |
| boabfit-market-analysis | Market research | ⚠️ Evaluate | Check completion |
| boabfit-website | BoabFit site | ⚠️ Evaluate | Check completion |
| global-utility | Global utils | ✅ Archived | Old structure moved to archived/ - contains md-to-pdf, mcp-aggregator, etc. that need migration to shared/ |
| insurance-savings-app | Insurance calc | ⚠️ Evaluate | Check completion |
| portfolio | Portfolio site | ⚠️ Evaluate | Check completion |
| product-ideas | Idea storage | ✅ Keep | Reference only |
| square-foot-shipping | Shipping biz | ⚠️ Evaluate | Check completion |
| swflorida-hvac | HVAC business | ⚠️ Evaluate | Check completion |

---

## External Workspaces

### ~/upwork-projects/
**Purpose**: Client freelance work
**Status**: ✅ Keep as-is
**Notes**: Contains actual client deliverables and timesheets

### ~/website-projects/
**Purpose**: Client website builds
**Status**: ✅ Keep as-is
**Notes**: Template for client website work

### ~/archived/
**Contents**: Old workflow docs, project duplicates
**Status**: ⚠️ Review for deletion

### ~/legacy/
**Contents**: Old data science work (Sep 2025)
**Status**: ✅ Keep for reference

---

## Next Steps

1. **Evaluate each ⚠️ project**:
   - Check for VERSION file
   - Check for working src/
   - Check for documentation
   - Test if it runs

2. **For ready projects**:
   - If standalone tool → Deploy as AI Assistant (SOP 31)
   - If dev-sandbox tool → Deploy as Skill (SOP 3)
   - If MCP → Publish (SOPs 11-14)

3. **For incomplete projects**:
   - Create Ralph PRD
   - Add to development queue

---

## Priority Evaluation Order

### High Priority (frequently used)
1. personal-assistant → AI Assistant candidate
2. website-builder → AI Assistant candidate
3. social-media-automation → Skill candidate
4. amazon-seller → AI Assistant candidate

### Medium Priority (useful but less urgent)
5. apollo-mcp → MCP candidate
6. upwork-mcp → MCP candidate
7. ticket-aggregator-mcp → MCP candidate

### Low Priority (evaluate later)
8. fitness-influencer → Complex, needs Ralph
9. Creator tools (IG, TikTok, YouTube) → Evaluate together
10. Business sites (BoabFit, Square Foot, HVAC)
