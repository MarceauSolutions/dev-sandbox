# Folder Restructure Decision Log

**Purpose**: Document all folder restructuring decisions, rationale, and verification requirements to ensure we don't break critical automation tools.

---

## Restructure History

### Restructure #1: Home Directory Organization (2026-01-21)

**Date**: 2026-01-21
**Commits**: 98370e7, 10b1ab2, 27072d5, b8b82eb

#### Problem Statement
- 90 items scattered at `~/` root level
- Couldn't find Apollo CSV import location
- Production repos mixed with websites, legacy work, and current projects
- No clear categorization

#### Goals
1. Make home directory navigable
2. Categorize by purpose (production, websites, legacy, etc.)
3. Eliminate duplicates
4. Preserve all files (no deletions)

#### Solution: 6-Category Organization
```
~/
├── dev-sandbox/           # Active development (ONE git repo)
├── production/            # Deployed production skills (6 repos)
├── websites/              # Company & client websites (5 repos)
├── active-projects/       # Standalone GitHub projects (3 repos)
├── legacy/                # Pre-Claude work (archived)
└── archived/              # Deprecated projects (archived)
```

#### What Changed
- **MOVED**: 6 `-prod` repos → `~/production/`
- **MOVED**: 5 website repos → `~/websites/`
- **MOVED**: 3 active projects → `~/active-projects/`
- **MOVED**: Legacy Jupyter notebooks → `~/legacy/`
- **MOVED**: Deprecated files → `~/archived/`

#### What Stayed the Same
- ✅ Development in `dev-sandbox/projects/`
- ✅ Testing in `dev-sandbox/`
- ✅ Deployment via `deploy_to_skills.py`
- ✅ All automation tools unchanged
- ✅ All workflows intact

#### Impact on Automation Tools
**ZERO IMPACT** - All automation tools remained in `dev-sandbox/projects/`:
- ✅ Lead scraper: `projects/shared-multi-tenant/lead-scraper/`
- ✅ AI customer service: `projects/shared-multi-tenant/ai-customer-service/`
- ✅ Social media automation: `projects/shared-multi-tenant/social-media-automation/`
- ✅ Personal assistant: `projects/shared-multi-tenant/personal-assistant/`
- ✅ Cold outreach: Uses lead-scraper + Twilio (unchanged)
- ✅ Response tracking: `src/campaign_analytics.py` (unchanged)

#### Verification Required
- [x] Lead scraper still accessible
- [x] Apollo CSV import location documented
- [x] Deploy script updated (now deploys to `~/production/`)
- [x] All git remotes intact
- [x] No nested repos in dev-sandbox

#### Success Criteria
- [x] Can navigate to any company asset in <3 clicks
- [x] No loose files at `~/` root
- [x] All production repos in one category
- [x] Development workflow unchanged

---

### Restructure #2 (PROPOSED): Company-Centric Organization

**Status**: ⚠️ PLANNING PHASE - NOT YET EXECUTED

#### Problem Statement
- Work for each company scattered across 3 locations (projects/, active-projects/, websites/)
- Can't showcase all work for a company in one GitHub repo
- Duplicate repos (fitness-influencer has 3 separate repos)
- No clear portfolio structure
- Nested git repos violating best practices

#### Goals
1. **Showcase**: One GitHub repo per company showing all work
2. **Consolidate**: Merge duplicate repos (fitness-influencer backend+frontend+mcp)
3. **Organize**: Group all company assets together
4. **Maintain**: Keep shared tools accessible
5. **Preserve**: Don't break automation tools

#### Proposed Solution: Company-Centric Structure
```
dev-sandbox/projects/
├── marceau-solutions/           # All Marceau Solutions work
│   ├── website/
│   ├── fitness-influencer/
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── mcp/
│   ├── amazon-seller/
│   └── ...
├── swflorida-hvac/              # All SW Florida HVAC work
│   ├── website/
│   └── hvac-distributors/
├── square-foot-shipping/        # All SquareFoot work
│   ├── website/
│   └── lead-gen/
├── shared/                      # Shared multi-tenant tools
│   ├── lead-scraper/
│   ├── ai-customer-service/
│   ├── social-media-automation/
│   └── personal-assistant/
└── global-utility/              # Global tools (no company)
```

#### CRITICAL: Automation Tools Impact Analysis

**BEFORE proceeding, verify these automation tools will still work:**

##### 1. Lead Scraping Tool
**Current Location**: `projects/shared-multi-tenant/lead-scraper/`
**Proposed Location**: `projects/shared/lead-scraper/`
**Commands Used**:
```bash
cd ~/dev-sandbox/projects/shared-multi-tenant/lead-scraper
python -m src.scraper search --query "gyms Naples FL"
python -m src.apollo_import import --input input/apollo/apollo_export_2026-01-21.csv
```

**Verification Required**:
- [ ] Path update needed in any scripts?
- [ ] Import paths still work (`from projects.shared.lead_scraper import ...`)?
- [ ] Apollo CSV input location documented?
- [ ] Output data separated by business_id?
- [ ] Webhooks still work?

##### 2. Cold Outreach Automation
**Current Location**: `projects/shared-multi-tenant/lead-scraper/src/`
**Files**:
- `sms_outreach.py`
- `follow_up_sequence.py`
- `campaign_analytics.py`
- `twilio_webhook.py`

**Commands Used**:
```bash
python -m src.scraper sms --dry-run --limit 5 --template no_website_intro
python -m src.follow_up_sequence process-due
python -m src.campaign_analytics report
```

**Verification Required**:
- [ ] SMS sending still works after path change?
- [ ] Templates still accessible (`templates/sms/`)?
- [ ] Webhook server still runs?
- [ ] Response tracking still works?
- [ ] Twilio credentials still accessible (`.env`)?

##### 3. Response Tracking
**Current Location**: `projects/shared-multi-tenant/lead-scraper/output/`
**Files**:
- `sms_campaigns.json`
- `campaign_analytics.json`
- `template_performance.json`

**Commands Used**:
```bash
python -m src.campaign_analytics response --phone "+1XXXXXXXXXX" --category hot_lead
python -m src.campaign_analytics funnel
python -m src.campaign_analytics templates
```

**Verification Required**:
- [ ] Output files still written to correct location?
- [ ] Analytics still calculate correctly?
- [ ] Campaign data preserved during move?
- [ ] ClickUp integration still works?

##### 4. AI Customer Service (Voice AI)
**Current Location**: `projects/shared-multi-tenant/ai-customer-service/`
**Proposed Location**: `projects/shared/ai-customer-service/`

**Commands Used**:
```bash
cd projects/shared-multi-tenant/ai-customer-service
python -m src.main
python scripts/start_server.py
```

**Verification Required**:
- [ ] Server still starts?
- [ ] Twilio webhook integration works?
- [ ] Business-specific voice styles load (`src/voice_styles.py`)?
- [ ] Call logs still accessible?

##### 5. Social Media Automation
**Current Location**: `projects/shared-multi-tenant/social-media-automation/`
**Proposed Location**: `projects/shared/social-media-automation/`

**Commands Used**:
```bash
python -m src.business_scheduler schedule-day --date 2026-01-20
python -m src.x_scheduler process
```

**Verification Required**:
- [ ] Business content still loads (`templates/business_content.json`)?
- [ ] X API credentials work?
- [ ] Scheduled posts still execute?
- [ ] Multi-business automation works?

##### 6. Personal Assistant (Morning Digest)
**Current Location**: `projects/shared-multi-tenant/personal-assistant/`
**Proposed Location**: `projects/shared/personal-assistant/`

**Commands Used**:
```bash
python -m src.morning_digest --preview
python -m src.digest_aggregator --hours 24
```

**Verification Required**:
- [ ] Gmail API access works?
- [ ] SMTP email sending works?
- [ ] Calendar integration works?
- [ ] Digest data aggregates correctly?

#### Why This Restructure?

**Primary Drivers**:
1. **Client Showcase Need**: "Show me all work you've done for my company"
   - Current: Scattered across 3+ locations
   - Proposed: Single GitHub repo per company

2. **Duplicate Code Elimination**: fitness-influencer has 3 repos
   - Current: backend/, frontend/, mcp/ all separate
   - Proposed: Unified in marceau-solutions/fitness-influencer/

3. **Portfolio Presentation**: Professional GitHub presence
   - Current: No unified company portfolio
   - Proposed: MarceauSolutions/marceausolutions-complete

4. **Logical Grouping**: Website + projects for same company together
   - Current: Website in `~/websites/`, projects in `~/dev-sandbox/projects/`
   - Proposed: All in `projects/[company]/`

**What We're NOT Changing**:
- ✅ Development workflow (still in dev-sandbox)
- ✅ Deployment process (still use deploy_to_skills.py)
- ✅ Testing procedures (still in dev-sandbox/testing/)
- ✅ Shared utility access (execution/)
- ✅ DOE architecture (directives → orchestration → execution)

---

## Decision Framework for Future Restructures

### When to Restructure

**DO restructure when**:
1. ✅ Can't find critical files (e.g., Apollo CSV import location)
2. ✅ Duplicate repos causing confusion
3. ✅ Client showcase requirement (need to present work)
4. ✅ Clear organizational benefit (navigability, clarity)
5. ✅ Eliminates git anti-patterns (nested repos)

**DON'T restructure when**:
1. ❌ Just for aesthetics
2. ❌ Would break automation tools
3. ❌ No clear benefit
4. ❌ Team doesn't understand new structure
5. ❌ Would disrupt active development

### Pre-Restructure Checklist

**MUST complete before any folder restructure**:

- [ ] **Document WHY**: What problem does this solve?
- [ ] **List ALL automation tools**: What runs automatically?
- [ ] **Map dependencies**: What paths do scripts use?
- [ ] **Identify shared assets**: What do multiple companies use?
- [ ] **Plan verification**: How will we test everything still works?
- [ ] **Create rollback plan**: How to undo if it breaks?
- [ ] **Backup everything**: `cp -r dev-sandbox dev-sandbox-backup-$(date +%Y%m%d)`
- [ ] **Test in isolation**: Try changes on one company first
- [ ] **Document new paths**: Update all README files

### Post-Restructure Verification

**MUST verify after any folder restructure**:

- [ ] **No nested repos**: `find . -name ".git" -type d` shows only `./dev-sandbox/.git`
- [ ] **Deploy script works**: `deploy_to_skills.py --list` shows all projects
- [ ] **Automation tools run**: Test each tool with actual commands
- [ ] **Shared assets accessible**: All companies can access shared tools
- [ ] **Git remotes intact**: `verify-git-remotes.sh` passes
- [ ] **Documentation updated**: CLAUDE.md, architecture-guide.md, etc.
- [ ] **Workflows documented**: Updated SOPs with new paths

---

## Critical Automation Tools Inventory

This is the MASTER LIST of automation tools that MUST work after any restructure.

### Lead Generation & Outreach

| Tool | Location | Commands | Critical Files |
|------|----------|----------|----------------|
| Lead Scraper | `projects/shared-multi-tenant/lead-scraper/` | `python -m src.scraper search` | `src/scraper.py`, `src/apollo_import.py` |
| Apollo Import | `lead-scraper/` | `python -m src.apollo_import import` | `input/apollo/`, `src/apollo_import.py` |
| SMS Outreach | `lead-scraper/` | `python -m src.scraper sms` | `src/sms_outreach.py`, `templates/sms/` |
| Follow-up Sequences | `lead-scraper/` | `python -m src.follow_up_sequence process-due` | `src/follow_up_sequence.py` |
| Campaign Analytics | `lead-scraper/` | `python -m src.campaign_analytics report` | `src/campaign_analytics.py`, `output/` |
| Twilio Webhook | `lead-scraper/` | `python -m src.twilio_webhook serve` | `src/twilio_webhook.py` |

### Voice AI & Customer Service

| Tool | Location | Commands | Critical Files |
|------|----------|----------|----------------|
| AI Customer Service | `projects/shared-multi-tenant/ai-customer-service/` | `python -m src.main` | `src/main.py`, `src/voice_engine.py` |
| Voice Styles | `ai-customer-service/` | N/A (imported) | `src/voice_styles.py`, `src/business_voice_engine.py` |
| Twilio Handler | `ai-customer-service/` | `python scripts/start_server.py` | `src/twilio_handler.py` |
| Call Insights | `ai-customer-service/` | N/A (imported) | `src/call_insights.py` |

### Social Media & Content

| Tool | Location | Commands | Critical Files |
|------|----------|----------|----------------|
| Social Media Automation | `projects/shared-multi-tenant/social-media-automation/` | `python -m src.business_scheduler schedule-day` | `src/business_scheduler.py` |
| X Scheduler | `social-media-automation/` | `python -m src.x_scheduler process` | `src/x_scheduler.py` |
| Business Content Gen | `social-media-automation/` | `python -m src.business_content_generator generate` | `src/business_content_generator.py` |
| Content Templates | `social-media-automation/` | N/A (data) | `templates/business_content.json` |

### Personal Assistant

| Tool | Location | Commands | Critical Files |
|------|----------|----------|----------------|
| Morning Digest | `projects/shared-multi-tenant/personal-assistant/` | `python -m src.morning_digest` | `src/morning_digest.py` |
| Digest Aggregator | `personal-assistant/` | `python -m src.digest_aggregator --hours 24` | `src/digest_aggregator.py` |
| Routine Scheduler | `personal-assistant/` | `python -m src.routine_scheduler --create-all` | `src/routine_scheduler.py` |

### Company-Specific Tools

| Tool | Company | Location | Commands |
|------|---------|----------|----------|
| Amazon Seller Ops | Marceau Solutions | `projects/marceau-solutions/amazon-seller/` | `python -m src.seller_operations` |
| HVAC Distributors | SW Florida HVAC | `projects/swflorida-hvac/hvac-distributors/` | `python -m src.rfq_system` |
| Fitness Influencer MCP | Marceau Solutions | `projects/marceau-solutions/fitness-influencer/` | `python -m src.fitness_influencer_mcp` |

---

## Path Migration Rules

### Rule 1: Shared Tools Stay Accessible

**Before**:
```python
from projects.shared_multi_tenant.lead_scraper import LeadScraper
```

**After** (if renamed to `shared/`):
```python
from projects.shared.lead_scraper import LeadScraper
```

**Action Required**: Update all import statements in scripts that reference shared tools.

### Rule 2: Preserve business_id Separation

All shared tools MUST maintain `business_id` parameter for multi-tenant operation:

```python
# CORRECT - maintains separation
lead_scraper.search(business_id="marceau-solutions", query="...")
ai_service.handle_call(business_id="swflorida-hvac", ...)
social_media.post(business_id="square-foot-shipping", ...)

# WRONG - breaks multi-tenant
lead_scraper.search(query="...")  # Which company?
```

### Rule 3: Environment Variables Unchanging

`.env` location NEVER changes: `/Users/williammarceaujr./dev-sandbox/.env`

All automation tools MUST continue reading from this single `.env` file.

### Rule 4: Output Data Separation

Shared tools MUST separate output data by company:

```
projects/shared/lead-scraper/output/
├── companies/
│   ├── marceau-solutions/
│   │   └── leads.json
│   ├── swflorida-hvac/
│   │   └── leads.json
│   └── square-foot-shipping/
│       └── leads.json
└── campaign_analytics.json  # Global analytics
```

---

## Verification Test Suite

### Pre-Migration Tests (RUN BEFORE RESTRUCTURE)

```bash
# 1. Lead Scraper
cd ~/dev-sandbox/projects/shared-multi-tenant/lead-scraper
python -m src.scraper search --query "test" --limit 1
echo "✅ Lead scraper works" || echo "❌ STOP - Lead scraper broken"

# 2. Apollo Import
python -m src.apollo_import --help
echo "✅ Apollo import accessible" || echo "❌ STOP - Apollo import broken"

# 3. SMS Outreach
python -m src.scraper sms --dry-run --limit 1
echo "✅ SMS outreach works" || echo "❌ STOP - SMS broken"

# 4. Campaign Analytics
python -m src.campaign_analytics report
echo "✅ Analytics works" || echo "❌ STOP - Analytics broken"

# 5. AI Customer Service
cd ~/dev-sandbox/projects/shared-multi-tenant/ai-customer-service
python -m src.main --help
echo "✅ AI service accessible" || echo "❌ STOP - AI service broken"

# 6. Social Media
cd ~/dev-sandbox/projects/shared-multi-tenant/social-media-automation
python -m src.business_scheduler --help
echo "✅ Social media works" || echo "❌ STOP - Social media broken"

# 7. Personal Assistant
cd ~/dev-sandbox/projects/shared-multi-tenant/personal-assistant
python -m src.morning_digest --preview
echo "✅ Morning digest works" || echo "❌ STOP - Digest broken"
```

### Post-Migration Tests (RUN AFTER RESTRUCTURE)

**Same commands as above, but from new paths:**

```bash
# After moving to projects/shared/
cd ~/dev-sandbox/projects/shared/lead-scraper
python -m src.scraper search --query "test" --limit 1
# ... etc
```

**ALL tests must pass** before considering migration complete.

---

## Emergency Rollback Procedure

If ANY automation tool breaks after restructure:

```bash
# STOP IMMEDIATELY
cd /Users/williammarceaujr.

# Restore from backup
rm -rf dev-sandbox
cp -r dev-sandbox-backup-$(date +%Y%m%d) dev-sandbox

# Verify tools work
cd dev-sandbox
bash verify-automation-tools.sh

# Document what broke
echo "Broke: [tool name] - [error message]" >> RESTRUCTURE-FAILURES.md
```

**DO NOT proceed with restructure until issue is understood and mitigated.**

---

## Summary: Why We Restructure

### Legitimate Reasons
1. **Can't find critical files** (e.g., Apollo CSV location unclear)
2. **Client showcase requirement** (need professional portfolio)
3. **Eliminate confusion** (duplicate repos, scattered assets)
4. **Fix git anti-patterns** (nested repos)
5. **Improve navigability** (clear categorization)

### Invalid Reasons
1. ❌ "Looks cleaner" (aesthetics alone)
2. ❌ "I prefer it this way" (personal preference)
3. ❌ "Other projects do it" (cargo culting)
4. ❌ "Might be useful someday" (speculative)

### Golden Rule
**Only restructure if the benefit (time saved, clarity gained, showcase enabled) outweighs the risk (breaking tools, migration time, learning curve).**

---

**Last Updated**: 2026-01-21
**Next Review**: Before any proposed restructure
**Owner**: William + Claude
