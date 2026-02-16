# Comprehensive Company-Centric Restructure Plan

**Date**: 2026-01-21
**Status**: READY FOR APPROVAL
**Complexity**: HIGH (273+ files affected, 9 automation systems, 6 scheduled jobs)
**Estimated Time**: 3-4 days with comprehensive testing
**Risk Level**: MEDIUM-HIGH (mitigated with safeguards)

---

## Why This Wasn't Done Right the First Time

### Honest Assessment

**Restructure #1 (Home Directory Organization)** focused on:
- ✅ Organizing the `~/` root level (90 items → 6 categories)
- ✅ Fixing deployment script paths
- ✅ Moving repos to appropriate categories

**What Restructure #1 MISSED**:
- ❌ Company asset consolidation (still scattered across 3 locations per company)
- ❌ Showcase strategy (no unified company portfolios)
- ❌ Duplicate elimination (fitness-influencer still has 3 repos)
- ❌ Client navigation (still need multiple folders per company)

**Root Cause**: We optimized for **technical cleanliness** (no nested repos, categorized by type) but didn't optimize for **business operations** (company-centric showcase, client presentation).

**Your Feedback Was Correct**: "it also seems like you're kind of losing track of the reason for the choice of restructure"

---

## Complete Business Context Analysis

### How Our Business Operates

**Multi-Business Service Model**:
1. **Marceau Solutions** - Your consulting business
   - Services: Websites + Automation + CRM + AI Tools
   - Clients: Fitness influencers, e-commerce, local businesses
   - Deliverables: Complete digital solutions

2. **SW Florida Comfort HVAC** - Client business
   - Service: Website + Voice AI + Lead Gen + CRM
   - Business model: Local HVAC contractor
   - Deliverables: 24/7 customer service automation

3. **SquareFoot Shipping** - Client business
   - Service: Website + Lead Gen + CRM
   - Business model: Freight shipping broker
   - Deliverables: Lead generation system

**Revenue Model**: Per-company retainer + monthly automation fees

**Sales Process**:
1. Prospect discovers Marceau Solutions
2. Demo shows **all capabilities** (website, automation, CRM, AI)
3. Custom solution built for their business
4. Ongoing optimization and support

**Critical Need**: Portfolio showcase that demonstrates **everything we can do for one company** in a single GitHub repo

---

### What Customers Are Buying

**Not Buying**: Individual tools (lead scraper, voice AI, social media)
**Actually Buying**: **Complete business solutions** that include:

1. **Professional Website** (online presence)
2. **Lead Generation** (customers finding them)
3. **Automation** (SMS campaigns, follow-ups, social media)
4. **CRM Integration** (ClickUp, Google Sheets)
5. **AI Customer Service** (Voice AI for calls)
6. **Response Tracking** (analytics, conversion funnels)

**Current Problem**: To showcase "all work for SW Florida HVAC", prospects must visit:
- `dev-sandbox/projects/swflorida-hvac/` (HVAC distributors project)
- `~/websites/swflorida-comfort-hvac/` (website)
- Plus reference to shared tools (lead-scraper, ai-customer-service)

**Desired State**: Single GitHub repo: `SWFloridaComfortHVAC/complete-solution`
- Contains: website, automation config, CRM setup, Voice AI config
- Shows: Complete digital transformation delivered

---

### Project Types & Setups

**Type 1: App for End Users** (Marceau Solutions products)
- Fitness Influencer Tools (backend, frontend, MCP)
- Instagram/TikTok/YouTube Creators
- Amazon Seller Operations
- Interview Prep

**Setup Process**:
1. Market research (SOP 17)
2. App type decision (SOP 0)
3. Development (SOP 1)
4. Multi-agent testing (SOP 2)
5. Deployment (SOP 3)
6. Publishing (SOPs 11-16 for MCPs)

**Type 2: Website + Automation + CRM** (Client services)
- SW Florida Comfort HVAC
- SquareFoot Shipping
- Marceau Solutions website

**Setup Process**:
1. Client discovery call
2. Website design + build
3. CRM integration (ClickUp)
4. Lead scraper config (business_id)
5. SMS campaign setup
6. Voice AI config (if applicable)
7. Social media automation
8. Response tracking
9. Launch + monitor

**Type 3: Shared Multi-Tenant Tools** (Infrastructure)
- Lead scraper (all companies use)
- AI customer service (all companies use)
- Social media automation (all companies use)
- Personal assistant (William only)

**Setup Process**:
1. Build once with business_id separation
2. Configure per-company in business_config.py
3. Add company templates (SMS, social, voice)
4. Deploy as shared utility

---

## All Aspects Considered for Restructure

### 1. Development Workflows (SOPs 0-24)

**Verified**: All 24 SOPs reviewed for path dependencies
- SOP 0: Project Kickoff ✅ (no path changes)
- SOP 1: New Project Init ✅ (paths documented)
- SOP 2: Multi-Agent Testing ⚠️ (test paths need update)
- SOP 3: Version Control ✅ (deploy script updated)
- SOP 6: Workflow Creation ✅ (workflows move with projects)
- SOP 9: Architecture Exploration ✅ (exploration/ folders move)
- SOP 18: SMS Campaigns ⚠️ (lead-scraper path changes)
- SOP 19: Follow-Up Sequences ⚠️ (lead-scraper path changes)
- SOP 22: Campaign Analytics ⚠️ (lead-scraper path changes)
- SOP 24: Daily Digest ⚠️ (personal-assistant path changes)

**Impact**: 4 SOPs require path updates in CLAUDE.md

---

### 2. Automation Tools (9 Systems)

✅ **All automation tools inventoried** (Explore agent findings):

1. **Lead Scraper** - 45 Python files, Apollo CSV import, Google Places API
2. **SMS Outreach** - Twilio integration, 7-touch sequences, Hormozi framework
3. **Campaign Analytics** - Performance tracking, conversion funnels, A/B testing
4. **Response Tracking** - ClickUp integration, hot/warm/cold categorization
5. **AI Customer Service** - Voice AI for calls, business-specific styles
6. **Social Media Automation** - X posting, multi-business scheduling, content generation
7. **Personal Assistant** - Morning digest, calendar integration, routine scheduler
8. **Form Handler** - Multi-business routing, CRM integration, owner notifications
9. **Deployment System** - deploy_to_skills.py, version control, GitHub push

**Critical**: All 9 systems use business_id separation for multi-tenancy

---

### 3. Scheduled Jobs (6 Automation Schedulers)

✅ **launchd Jobs** (1 active):
- `com.marceausolutions.campaign-launcher.plist`
- Runs 6x/week (Mon-Sat)
- **HARDCODED PATHS** that MUST be updated

✅ **Cron Jobs** (8 shell scripts):
- Billing monitor
- Daily follow-ups
- Outreach scheduling
- Social media posting (4 scripts)
- Business automation runner

**Impact**: All 6 schedulers will FAIL if paths not updated

---

### 4. Business Separation Logic (Multi-Tenancy)

✅ **business_id Architecture** (MUST PRESERVE):

**Files with Multi-Tenant Logic**:
- `execution/form_handler/business_config.py` (3 businesses configured)
- `lead-scraper/src/scraper.py` (business_id parameter)
- `lead-scraper/src/campaign_auto_launcher.py` (per-business campaigns)
- `social-media-automation/src/business_scheduler.py` (per-business posts)
- `ai-customer-service/src/twilio_handler.py` (per-business call routing)

**Data Separation**:
```
output/
├── companies/
│   ├── marceau-solutions/
│   │   ├── leads.json
│   │   ├── campaigns.json
│   │   └── nurture_queue.json
│   ├── swflorida-hvac/
│   │   ├── leads.json
│   │   ├── campaigns.json
│   │   └── nurture_queue.json
│   └── square-foot-shipping/
│       ├── leads.json
│       ├── campaigns.json
│       └── nurture_queue.json
```

**Verification Required**: All 3 businesses' data must remain separated after restructure

---

### 5. CRM Integrations (ClickUp, Google Sheets)

✅ **Form Handler → ClickUp Routing**:
- Webhook endpoint: `/submit`
- Business detection from form source
- Auto-create tasks in correct ClickUp list
- Owner SMS notifications

✅ **Google Sheets Lead Tracking**:
- Apollo CSV import → Google Sheets
- Campaign results → Google Sheets
- Per-business spreadsheets

**Impact**: business_id routing MUST be preserved

---

### 6. Client-Facing Components (Webhooks, Websites)

✅ **Public Webhooks** (UNCHANGING URLS):
- Form submissions: `https://[domain]/submit`
- SMS replies: `https://[domain]/webhook/twilio`
- Voice calls: `https://[domain]/voice`

✅ **Websites** (TO BE MOVED):
- marceausolutions.com (from ~/websites/ to projects/marceau-solutions/website/)
- swflorida-comfort-hvac (from ~/websites/ to projects/swflorida-hvac/website/)
- squarefoot-shipping-website (from ~/websites/ to projects/square-foot-shipping/website/)

**Impact**: Webhook handler paths must be verified, website deployments unaffected

---

### 7. Data Persistence (Historical Data)

✅ **Output Data Migration Required**:
- Campaign data: `output/campaigns/*.json` (50+ files)
- SMS tracking: `output/sms_campaigns.json`
- Analytics: `output/campaign_analytics.json`
- Lead records: `output/lead_records.json`
- Nurture queues: `output/companies/*/nurture_queue.json`
- Form submissions: `output/form_submissions/*/`

**Critical**: Historical data MUST be preserved during migration

---

### 8. Template Libraries (SMS, Social, Email)

✅ **SMS Templates** (16 templates):
- Pain point based: no_website, poor_google, low_reviews
- Follow-up sequences: still_looking, social_proof, direct_question
- Optimized variants: hvac_*, shipping_*

✅ **Social Media Templates**:
- Business content strategies
- Post templates per business
- Nick Saraev style guide

**Impact**: Template paths must remain accessible after move

---

### 9. Documentation (66+ Workflow Files)

✅ **Workflow Documentation**:
- Lead scraper: 14 workflow files
- Social media: 8 workflow files
- Personal assistant: 3 workflow files
- AI customer service: 5 workflow files

✅ **SOPs in CLAUDE.md**:
- 24 documented SOPs with code examples
- All reference current paths

**Impact**: All workflow docs and CLAUDE.md need path updates

---

### 10. Testing Infrastructure (SOP 2)

✅ **Multi-Agent Testing**:
- AGENT-PROMPTS.txt (absolute paths)
- TEST-PLAN.md
- Agent workspaces (agent1/, agent2/, etc.)

✅ **Verification Script**:
- verify-automation-tools.sh (38 tests)
- Pre/post-migration validation

**Impact**: Test infrastructure moves with projects, prompts need path updates

---

### 11. Git & Version Control

✅ **No Nested Repos** (verified):
- Single .git at dev-sandbox/.git
- All projects tracked in parent repo

✅ **Git Remotes**:
- 9/15 repos configured
- 6 repos need remote setup

**Impact**: Use `git mv` to preserve history

---

### 12. Import Dependencies (73+ Python Files)

✅ **Cross-Project Imports**:
```python
# Current
from projects.shared_multi_tenant.lead_scraper import LeadScraper

# After
from projects.shared.lead_scraper import LeadScraper
```

**Files Affected**:
- lead-scraper: 45 files
- ai-customer-service: 12 files
- social-media-automation: 8 files
- personal-assistant: 8 files

**Impact**: Automated search/replace required for all imports

---

### 13. Deployment System (deploy_to_skills.py)

✅ **Category Detection Logic**:
```python
categories = [
    "shared",  # ← MUST CHANGE TO "shared"
    "marceau-solutions",
    "swflorida-hvac",
    "square-foot-shipping",
]
```

✅ **Project Configurations**:
- 16 manually configured projects
- Paths hardcoded for special cases

**Impact**: CRITICAL - All deployments fail if not updated

---

### 14. VSCode Workspaces (4 Files)

✅ **Workspace Configurations**:
- dev-sandbox-campaigns.code-workspace
- dev-sandbox-marceau.code-workspace
- dev-sandbox-shared.code-workspace
- dev-sandbox-all-companies.code-workspace

**Impact**: Folder paths in JSON need updates

---

### 15. Professional Polish & Debugging

✅ **Testing Strategy** (docs/testing-strategy.md):
- Scenario 1: Manual Testing (ALWAYS)
- Scenario 2: Multi-Agent Testing (complex features)
- Scenario 3: Pre-Deployment Verification (ALWAYS)
- Scenario 4: Post-Deployment Verification (ALWAYS)

✅ **DOE Architecture** (Directive-Orchestration-Execution):
- Layer 1: Directives (directives/*.md)
- Layer 2: Orchestration (Claude)
- Layer 3: Execution (execution/*.py, projects/*/src/*.py)

**Goal**: Most debugging during development, minimal post-deployment issues

**How Restructure Helps**:
- Clear project boundaries → easier testing
- Company-centric folders → easier verification
- Shared tools isolated → easier regression testing
- No nested repos → cleaner git workflows

---

## Proposed Company-Centric Structure

### Before (Current - SCATTERED)

```
~/
├── dev-sandbox/
│   └── projects/
│       ├── marceau-solutions/           # 9 projects here
│       ├── swflorida-hvac/              # 1 project here
│       ├── square-foot-shipping/        # Empty placeholder
│       └── shared/         # Shared tools
│
├── websites/
│   ├── marceausolutions.com/            # Website separate
│   ├── swflorida-comfort-hvac/          # Website separate
│   └── squarefoot-shipping-website/     # Website separate
│
└── active-projects/
    ├── fitness-influencer-backend/      # Separate backend
    ├── fitness-influencer-frontend/     # Separate frontend
    └── square-foot-shipping/            # Lead gen separate
```

**Problem**: To see all SW Florida HVAC work → visit 2 folders
**Problem**: To see all SquareFoot Shipping work → visit 3 folders
**Problem**: To see all Marceau Solutions work → visit 3 folders

---

### After (Proposed - CONSOLIDATED)

```
~/dev-sandbox/projects/
│
├── marceau-solutions/                   # ALL Marceau Solutions work
│   ├── website/                         # ← MOVED from ~/websites/
│   ├── fitness-influencer/              # ← CONSOLIDATED
│   │   ├── backend/                     # ← MOVED from ~/active-projects/
│   │   ├── frontend/                    # ← MOVED from ~/active-projects/
│   │   └── mcp/                         # ← FROM current location
│   ├── amazon-seller/
│   ├── instagram-creator/
│   ├── tiktok-creator/
│   ├── youtube-creator/
│   ├── interview-prep/
│   └── website-builder/
│
├── swflorida-hvac/                      # ALL SW Florida HVAC work
│   ├── website/                         # ← MOVED from ~/websites/
│   └── hvac-distributors/               # ← FROM current location
│
├── square-foot-shipping/                # ALL SquareFoot Shipping work
│   ├── website/                         # ← MOVED from ~/websites/
│   └── lead-gen/                        # ← MOVED from ~/active-projects/
│
├── shared/                              # ← RENAMED from shared/
│   ├── lead-scraper/                    # All companies use
│   ├── ai-customer-service/             # All companies use
│   ├── social-media-automation/         # All companies use
│   └── personal-assistant/              # William only
│
└── global-utility/                      # NO company affiliation
    ├── md-to-pdf/
    ├── time-blocks/
    ├── email-analyzer/
    └── ... (7 tools)
```

**Benefit**: To see all SW Florida HVAC work → 1 folder (`projects/swflorida-hvac/`)
**Benefit**: To see all SquareFoot Shipping work → 1 folder (`projects/square-foot-shipping/`)
**Benefit**: To see all Marceau Solutions work → 1 folder (`projects/marceau-solutions/`)

---

## GitHub Showcase Strategy

### Goal: Portfolio Repos Per Company

**Create 3 GitHub Repos** (outside dev-sandbox):

1. **MarceauSolutions/marceausolutions-complete**
   - Location: `~/github-showcases/marceausolutions-complete/`
   - Contains: Copy of all projects/marceau-solutions/* assets
   - Purpose: "Here's everything we've built for Marceau Solutions"
   - Audience: Prospective clients, portfolio visitors

2. **SWFloridaComfortHVAC/swflorida-hvac-complete**
   - Location: `~/github-showcases/swflorida-hvac-complete/`
   - Contains: Copy of all projects/swflorida-hvac/* assets
   - Purpose: "Here's your complete digital solution"
   - Audience: Client review, future reference

3. **SquareFootShipping/squarefoot-shipping-complete**
   - Location: `~/github-showcases/squarefoot-shipping-complete/`
   - Contains: Copy of all projects/square-foot-shipping/* assets
   - Purpose: "Here's your complete digital solution"
   - Audience: Client review, future reference

**Setup**:
```bash
# Create showcase directory
mkdir -p ~/github-showcases/

# Copy company assets to showcase repo
cp -r ~/dev-sandbox/projects/swflorida-hvac/ ~/github-showcases/swflorida-hvac-complete/

# Initialize git and push to GitHub
cd ~/github-showcases/swflorida-hvac-complete/
git init
gh repo create SWFloridaComfortHVAC/swflorida-hvac-complete --public
git add .
git commit -m "Initial commit: Complete SW Florida HVAC solution"
git push -u origin main
```

**Update Process**:
- Develop in dev-sandbox as usual
- When ready to update showcase: `rsync -av dev-sandbox/projects/swflorida-hvac/ github-showcases/swflorida-hvac-complete/`
- Commit and push to GitHub

---

## Migration Plan (4-Day Timeline)

### Day 1: Preparation & Backup

**Morning (8 AM - 12 PM)**:
1. ✅ Full backup: `cp -r ~/dev-sandbox ~/dev-sandbox-backup-$(date +%Y%m%d)`
2. ✅ Export current state:
   - `git status > pre-migration-git-status.txt`
   - `crontab -l > pre-migration-crontab.txt`
   - `launchctl list | grep marceau > pre-migration-launchd.txt`
3. ✅ Run pre-migration tests: `bash verify-automation-tools.sh` (ALL MUST PASS)
4. ✅ Inventory data files: `find projects/shared -name "*.json" > pre-migration-data-files.txt`

**Afternoon (1 PM - 5 PM)**:
5. ✅ Create migration script: `scripts/migrate_company_centric.py`
   - Git mv commands for all folders
   - Import path replacements
   - Configuration file updates
   - Dry-run mode for testing
6. ✅ Create rollback script: `scripts/rollback_migration.sh`
7. ✅ Test migration script with `--dry-run` flag
8. ✅ Review dry-run output with William

---

### Day 2: Execute Migration

**Morning (8 AM - 10 AM)**:
1. ✅ STOP all automation:
   ```bash
   # Stop launchd jobs
   launchctl unload ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist

   # Stop cron jobs (backup first)
   crontab -l > crontab-backup.txt
   crontab -r
   ```

2. ✅ Commit all current work:
   ```bash
   cd ~/dev-sandbox
   git add .
   git commit -m "chore: Pre-restructure checkpoint - all automation stopped"
   git push
   ```

**Mid-Morning (10 AM - 12 PM)**:
3. ✅ Execute migration script:
   ```bash
   python scripts/migrate_company_centric.py --execute
   ```

4. ✅ Verify git history preserved:
   ```bash
   git log --follow projects/shared/lead-scraper/
   ```

**Afternoon (1 PM - 5 PM)**:
5. ✅ Update all configuration files:
   - deploy_to_skills.py (category list, project configs)
   - verify-automation-tools.sh (path detection)
   - launchd plist (WorkingDirectory, log paths)
   - Cron scripts (8 files - working directories)

6. ✅ Update documentation:
   - CLAUDE.md (4 SOPs with path changes)
   - All workflow docs (66+ files)
   - VSCode workspaces (4 files)

7. ✅ Commit migration:
   ```bash
   git add .
   git commit -m "feat: Company-centric restructure - all assets grouped by company"
   git push
   ```

---

### Day 3: Verification & Restart Automation

**Morning (8 AM - 12 PM)**:
1. ✅ Run post-migration tests: `bash verify-automation-tools.sh`
   - ALL 38 tests MUST pass
   - If ANY fail → ROLLBACK IMMEDIATELY

2. ✅ Manual verification of each automation:
   - Lead scraper: `cd projects/shared/lead-scraper && python -m src.scraper --help`
   - Apollo import: `python -m src.apollo_import --help`
   - SMS outreach: `python -m src.scraper sms --dry-run --limit 1`
   - Campaign analytics: `python -m src.campaign_analytics report`
   - AI service: `cd projects/shared/ai-customer-service && python -m src.main --help`
   - Social media: `cd projects/shared/social-media-automation && python -m src.business_scheduler --help`
   - Personal assistant: `cd projects/shared/personal-assistant && python -m src.morning_digest --preview`

3. ✅ Verify business_id separation:
   ```bash
   # Test lead scraper with each business
   python -m src.scraper search --business-id marceau-solutions --query "test" --limit 1
   python -m src.scraper search --business-id swflorida-hvac --query "test" --limit 1
   python -m src.scraper search --business-id square-foot-shipping --query "test" --limit 1
   ```

4. ✅ Verify historical data:
   - Check all output/*.json files present
   - Verify company separation in output/companies/
   - Confirm no data loss

**Afternoon (1 PM - 5 PM)**:
5. ✅ Reload launchd job:
   ```bash
   # Verify updated plist has new paths
   cat ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist | grep WorkingDirectory

   # Load job
   launchctl load ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist

   # Verify loaded
   launchctl list | grep campaign-launcher
   ```

6. ✅ Restore cron jobs (with updated paths):
   ```bash
   # Edit crontab-backup.txt with new paths
   # Then install
   crontab crontab-backup.txt

   # Verify
   crontab -l
   ```

7. ✅ Test deployment:
   ```bash
   python deploy_to_skills.py --list
   python deploy_to_skills.py --status lead-scraper
   ```

---

### Day 4: GitHub Showcases & Final Testing

**Morning (8 AM - 12 PM)**:
1. ✅ Create GitHub showcase repos:
   ```bash
   mkdir -p ~/github-showcases/

   # Marceau Solutions
   cp -r ~/dev-sandbox/projects/marceau-solutions/ ~/github-showcases/marceausolutions-complete/
   cd ~/github-showcases/marceausolutions-complete/
   git init
   gh repo create MarceauSolutions/marceausolutions-complete --public
   git add .
   git commit -m "Initial commit: Complete Marceau Solutions portfolio"
   git push -u origin main

   # SW Florida HVAC
   # ... repeat for swflorida-hvac

   # SquareFoot Shipping
   # ... repeat for square-foot-shipping
   ```

2. ✅ Create README files for showcase repos with portfolio summaries

**Afternoon (1 PM - 5 PM)**:
3. ✅ End-to-end testing:
   - Run morning digest
   - Send test SMS campaign
   - Check campaign analytics
   - Test form submission
   - Test webhook responses

4. ✅ Monitor automation for 24 hours:
   - Check launchd logs
   - Check cron job execution
   - Verify no errors

5. ✅ Final verification:
   ```bash
   # No nested repos
   find ~/dev-sandbox -name ".git" -type d
   # Should show only: ./dev-sandbox/.git

   # All tests pass
   bash verify-automation-tools.sh

   # Deploy script works
   python deploy_to_skills.py --list
   ```

---

## Rollback Plan

### If ANY test fails during Day 3:

```bash
# STOP IMMEDIATELY
cd /Users/williammarceaujr.

# Restore from backup
rm -rf dev-sandbox
cp -r dev-sandbox-backup-$(date +%Y%m%d) dev-sandbox

# Reload old automation
launchctl unload ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist
launchctl load ~/Library/LaunchAgents/com.marceausolutions.campaign-launcher.plist
crontab crontab-backup.txt

# Verify restoration
cd dev-sandbox
bash verify-automation-tools.sh

# Document failure
echo "Migration failed at: [step]" >> MIGRATION-FAILURE.md
echo "Error: [error message]" >> MIGRATION-FAILURE.md
echo "Restored from backup successfully" >> MIGRATION-FAILURE.md
```

---

## Success Criteria

### All of These MUST Pass:

- [ ] **No nested git repos**: `find . -name ".git" -type d` shows only `./.git`
- [ ] **All 38 automation tests pass**: `bash verify-automation-tools.sh`
- [ ] **Deploy script works**: `python deploy_to_skills.py --list` shows all projects
- [ ] **Lead scraper accessible**: `python -m src.scraper --help` works
- [ ] **Apollo import works**: `python -m src.apollo_import --help` works
- [ ] **SMS campaigns work**: `python -m src.scraper sms --dry-run --limit 1` works
- [ ] **Campaign analytics work**: `python -m src.campaign_analytics report` works
- [ ] **AI service works**: `python -m src.main --help` works
- [ ] **Social media works**: `python -m src.business_scheduler --help` works
- [ ] **Personal assistant works**: `python -m src.morning_digest --preview` works
- [ ] **All 3 businesses separated**: Verify output/companies/{marceau,swflorida,squarefoot}/ exist
- [ ] **launchd job running**: `launchctl list | grep campaign-launcher`
- [ ] **Cron jobs running**: `crontab -l` shows all jobs
- [ ] **Historical data preserved**: All output/*.json files present
- [ ] **Templates accessible**: All templates/sms/*.txt files load
- [ ] **GitHub showcases created**: 3 repos on GitHub with all company assets
- [ ] **Documentation updated**: CLAUDE.md, workflows, VSCode workspaces all reference new paths
- [ ] **No import errors**: All Python scripts import correctly

---

## What Makes This Different From Restructure #1

### Restructure #1: Technical Organization
- **Goal**: Clean up home directory, fix nested repos
- **Benefit**: Better git hygiene, categorized repos
- **Impact**: Developer experience improved

### Restructure #2 (This One): Business Organization
- **Goal**: Company-centric showcase, client navigation
- **Benefit**: Professional portfolio, easier sales demos
- **Impact**: Business operations improved, client experience improved

**Both Were Needed** - #1 fixed technical debt, #2 optimizes for business value

---

## Approval Required

**William, please confirm**:

1. ✅ **Proceed with migration?** (YES / NO / MODIFY)
   - If YES: Proceed with 4-day plan
   - If NO: Cancel restructure, keep current structure
   - If MODIFY: What changes to approach?

2. ✅ **Timeline acceptable?** (4 days with comprehensive testing)
   - Day 1: Preparation
   - Day 2: Execution
   - Day 3: Verification
   - Day 4: Showcases

3. ✅ **Risk acceptable?** (MEDIUM-HIGH, mitigated with safeguards)
   - 273+ files affected
   - 9 automation systems
   - 6 scheduled jobs
   - Full rollback plan in place

4. ✅ **GitHub showcase repos?**
   - MarceauSolutions/marceausolutions-complete
   - SWFloridaComfortHVAC/swflorida-hvac-complete
   - SquareFootShipping/squarefoot-shipping-complete

---

## Next Steps (After Approval)

1. Create migration scripts (Day 1)
2. Run dry-run and review (Day 1)
3. Execute migration (Day 2)
4. Verify and restart automation (Day 3)
5. Create GitHub showcases (Day 4)

**Estimated Start**: Tomorrow (2026-01-22)
**Estimated Completion**: 2026-01-25

---

**End of Comprehensive Restructure Plan**
