# Project Inventory & Deployment Assessment

**Date**: 2026-02-08
**Last Updated**: 2026-02-08 (Post-Deployment Sweep)
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
| apollo-mcp | Apollo.io MCP | ✅ Ready (v1.1.1) | **MCP** - Ready for PyPI/Registry (SOP 12-13) |
| canva-mcp | Canva integration | ✅ **COMPLETE** | **MCP** v1.0.0 - 21 tools, ready for PyPI/Registry |
| lead-scraper | Lead scraping system | ✅ Ready | Already in production |
| mcp-aggregator | MCP marketplace | ✅ Migrated | Migrated from global-utility |
| md-to-pdf | Markdown to PDF | ✅ Ready (v1.0.1) | **MCP** - Ready for PyPI/Registry |
| n8n-workflows | n8n workflow storage | ✅ Ready | Keep as is (storage) |
| personal-assistant | Daily digest system | ✅ Evaluated | **Skill** (not AI Assistant) - uses personal OAuth |
| resume | Resume template | ✅ Migrated | Migrated from ~/global-utility |
| social-media-automation | Social posting | ✅ **UPDATED** | **Skill** - TikTok API modules NOW IMPLEMENTED |
| source-pointer | Source tracking | ⚠️ Evaluate | Check completion |
| ticket-aggregator-mcp | Support tickets | ✅ Ready (v1.0.0) | **MCP** - Ready for PyPI/Registry |
| twilio-mcp | Twilio SMS | ✅ Migrated | Migrated from global-utility |
| upwork-mcp | Upwork integration | ✅ Ready (v1.0.1) | **MCP** - Ready for PyPI/Registry |

### Marceau Solutions Projects (projects/marceau-solutions/)

| Project | Description | Readiness | Recommended Action |
|---------|-------------|-----------|-------------------|
| amazon-seller | Amazon seller tools | ✅ Ready (v1.0.0) | **MCP** - Ready for PyPI/Registry |
| fitness-influencer | Fitness AI platform | ⚠️ Evaluate | Complex - needs Ralph |
| fitness-influencer-mcp | MCP version | ❌ Incomplete | Missing pyproject.toml, server.json |
| instagram-creator | IG content tools | ✅ Ready (v1.0.0) | **MCP** - VERSION file created |
| interview-prep | Interview prep | ✅ Ready | Already in production |
| tiktok-creator | TikTok tools | ✅ Ready (v1.0.0) | **MCP** - VERSION file created |
| trainerize-mcp | Trainerize MCP | ✅ Ready | Has pyproject.toml, server.json |
| vuori-lead-magnet | Lead magnet | ⚠️ Evaluate | Marketing video project |
| website | Company website | ✅ Ready | Separate repo |
| website-builder | Website gen | ✅ Deployed | **AI Assistant** at ~/ai-assistants/ |
| youtube-creator | YouTube tools | ✅ Ready (v1.0.0) | **MCP** - VERSION file created |

### Other Projects (projects/)

| Project | Description | Readiness | Recommended Action |
|---------|-------------|-----------|-------------------|
| product-ideas/go-tracker | Go game tracker | ⚠️ Personal | iOS app - keep |
| boabfit/ | BoabFit client (website + research) | ✅ Static | Consolidated client namespace |
| product-ideas/insurance-savings-app | Insurance calc | ✅ Has PRD | Full src/, PRD.md exists, needs testing |
| marceau-solutions/portfolio | Portfolio demos | ⚠️ Evaluate | Check completion |
| product-ideas/ | Idea storage | ✅ Keep | Reference only |
| square-foot-shipping/ | Shipping client | ⚠️ Minimal | Just README and lead-gen folder |
| swflorida-hvac/ | HVAC client (website + tools) | ✅ Active | Website + hvac-mcp + distributors |
| flames-of-passion/ | Candle brand client (website) | ✅ Static | Promoted from client-sites/ |

---

## Completed During Deployment Sweep (2026-02-08)

### Phase 1: Cleanup & Organization
- ✅ Deleted `~/active-projects/` (empty)
- ✅ Deleted `~/n8n-workflows-temp/` (empty)
- ✅ Migrated `~/global-utility/resume` → `projects/shared/resume/`
- ✅ Migrated `mcp-aggregator` → `projects/shared/mcp-aggregator/`
- ✅ Migrated `md-to-pdf` → `projects/shared/md-to-pdf/`
- ✅ Migrated `twilio-mcp` → `projects/shared/twilio-mcp/`

### Phase 2: MCP Finalization
- ✅ Created `projects/shared/canva-mcp/server.json`
- ✅ Updated `projects/shared/canva-mcp/README.md` (was placeholder, now complete)

### Phase 3: MCP Version Fixes
- ✅ Fixed `md-to-pdf/VERSION` and `__init__.py` (1.0.0 → 1.0.1)
- ✅ Fixed `apollo-mcp/VERSION` and `__init__.py` (1.1.0 → 1.1.1)
- ✅ Created `youtube-creator/VERSION` (1.0.0)
- ✅ Created `instagram-creator/VERSION` (1.0.0)
- ✅ Created `tiktok-creator/VERSION` (1.0.0)

### Phase 4: TikTok Implementation
- ✅ Created `src/tiktok_auth.py` - OAuth 2.0 authentication
- ✅ Created `src/tiktok_api.py` - Video upload and publish API
- ✅ Created `src/tiktok_scheduler.py` - Queue management and scheduling
- ✅ Updated `src/__init__.py` - Exports TikTok modules (v1.1.0-dev)

---

## MCPs Ready for Publishing

| MCP | Version | PyPI Package | Status |
|-----|---------|--------------|--------|
| amazon-seller | 1.0.0 | amazon-seller-mcp | ✅ Ready |
| apollo-mcp | 1.1.1 | apollo-mcp | ✅ Ready |
| canva-mcp | 1.0.0 | canva-mcp | ✅ Ready (21 tools) |
| instagram-creator | 1.0.0 | instagram-creator-mcp | ✅ Ready |
| md-to-pdf | 1.0.1 | md-to-pdf-mcp | ✅ Ready |
| ticket-aggregator | 1.0.0 | ticket-aggregator-mcp | ✅ Ready |
| tiktok-creator | 1.0.0 | tiktok-creator-mcp | ✅ Ready |
| upwork-mcp | 1.0.1 | upwork-mcp | ✅ Ready |
| youtube-creator | 1.0.0 | youtube-creator-mcp | ✅ Ready |

**To publish**: See `ralph/prd-mcp-publishing-all.json` (15 stories)

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
**Status**: ✅ Reviewed - contains backup of old global-utility structure

### ~/legacy/
**Contents**: Old data science work (Sep 2025)
**Status**: ✅ Keep for reference

---

## Next Steps

1. **Publish MCPs to PyPI/Registry**:
   - Execute `ralph/prd-mcp-publishing-all.json` (15 stories)
   - Or manually run SOP 12-13 for each MCP

2. **Test insurance-savings-app**:
   - Has full codebase and PRD.md
   - Needs manual testing before deployment

3. **Evaluate remaining ⚠️ projects**:
   - Check for VERSION file
   - Check for working src/
   - Test if it runs

---

## Summary

**Total Projects**: 30+
**MCPs Ready**: 9
**Deployed Skills**: 6
**AI Assistants**: 2
**Pending Evaluation**: 8
