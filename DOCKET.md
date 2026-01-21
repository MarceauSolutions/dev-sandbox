# Development Docket

**Purpose**: Track deferred work items with clear trigger conditions
**Status**: Active tracking document

---

## 🔴 High Priority (Work On Next)

### 1. Apollo MCP End-to-End Automation
**Status**: ✅ COMPLETE (v1.1.0)
**Completed**: 2026-01-21
**Trigger**: ✅ MCP server built, pipeline created
**Request**: Full automation from prompt → Apollo search → enrichment → SMS campaign

**Requirements**:
- Single command: "Run cold outreach for Naples HVAC" → entire pipeline executes
- Auto-detect company context (Marceau Solutions vs Southwest Florida Comfort vs Footer Shipping)
- Direct Apollo API calls via MCP (no CSV export/import steps)
- Iterative search refinement with exclusion terms
- Quality validation before enrichment

**Implementation Plan**:
- [ ] Add company-specific search templates
- [ ] Implement excluded terms (e.g., "sales", "outside", "representative")
- [ ] Create iterative search refinement loop
- [ ] Direct MCP → Apollo → MCP workflow (eliminate CSV steps)
- [ ] Company detection from prompt context

**Example Usage**:
```
User: "Run cold outreach for Naples HVAC companies for Southwest Florida Comfort"
Claude:
  1. Detects company = Southwest Florida Comfort
  2. Loads HVAC search template
  3. Executes Apollo search with exclusions
  4. Reviews results, refines if needed
  5. Auto-scores leads
  6. Enriches top 20%
  7. Sends SMS campaign
  8. Reports: "Sent 15 messages, cost 30 credits"
```

---

### 2. Publish Apollo MCP to Distribution Channels
**Status**: Ready (MCP built, needs publishing)
**Trigger**: ✅ Apollo MCP server complete
**Request**: Deploy to PyPI + MCP Registry + OpenRouter

**Steps**:
- [ ] SOP 11: Verify package structure ✅ (already done)
- [ ] SOP 12: Publish to PyPI
- [ ] SOP 13: Publish to MCP Registry
- [ ] SOP 16: Register on OpenRouter directories
- [ ] Update README with installation instructions

**Package Info**:
- Name: `apollo-mcp`
- MCP ID: `io.github.wmarceau/apollo`
- Version: 1.0.0

---

### 3. Google Cloud $100 Charge Investigation
**Status**: ✅ COMPLETE
**Completed**: 2026-01-21
**Trigger**: ✅ User request
**Request**: "Figure out what $100 charge from Google Cloud is"

**Finding**: Likely verification hold, not usage ($10.90 actual usage)

**Investigation Steps**:
- [ ] Check Google Cloud Console billing dashboard
- [ ] Review service usage breakdown (Compute, Storage, APIs)
- [ ] Identify which project caused charge
- [ ] Check for: VM instances running, Cloud Functions, API calls
- [ ] Recommend cost-saving measures
- [ ] Set up billing alerts to prevent future surprises

**Likely Culprits**:
- Compute Engine VMs left running
- Cloud Functions excessive invocations
- BigQuery queries
- Cloud Storage egress fees
- Maps/Places API overages

---

### 4. End-Customer Deployment Strategy
**Status**: ✅ COMPLETE
**Completed**: 2026-01-21
**Trigger**: ✅ User request
**Request**: "Determine best deployment strategies for providing finished products to end customers"

**Recommendation**: Hybrid SaaS ($12/customer at 100 customers, $496K ARR potential)

**Questions to Answer**:
- SaaS vs white-label vs custom deployment?
- Self-hosted vs cloud-hosted?
- Per-customer infrastructure vs multi-tenant?
- Pricing model implications?
- Support/maintenance strategy?

**Options to Evaluate**:
1. **SaaS (Multi-Tenant)**: One platform, all customers share
2. **White Label**: Customer-branded instances
3. **Custom Deployment**: Per-customer infrastructure
4. **Hybrid**: Core SaaS + custom integrations

**Deliverable**: Decision matrix with cost/complexity/scalability analysis

---

## 🟡 Medium Priority (Blocked or Waiting)

### 5. LinkedIn Company Page Posting
**Status**: ⏳ Waiting for API approval
**Trigger**: LinkedIn Community Management API approved
**Blocked By**: LinkedIn approval email (24-48 hours)

**Ready When Approval Arrives**:
- ✅ Second app created (78gy4q6d5k2e3d)
- ✅ OAuth script ready (`linkedin_company_auth.py`)
- ✅ API client ready (`linkedin_company_api.py`)
- ✅ Setup guide created (`LINKEDIN-COMPANY-SETUP.md`)

**Next Steps After Approval**:
1. Add redirect URL to app
2. Get Client Secret
3. Run OAuth flow
4. Get organization ID
5. Test posting
6. Integrate with automation

---

### 6. Facebook Business Page Integration
**Status**: ⏳ Blocked by security verification
**Trigger**: Facebook SMS verification successful OR 24-hour cooldown expires
**Blocked By**: Facebook security system

**What's Needed**:
- App credentials (App ID + Secret)
- OAuth setup for Pages API
- Page posting integration

**Alternative**: Try desktop browser after cooldown period

---

## 🟢 Low Priority (Nice to Have)

### 7. ClickUp Integration Migration
**Status**: Deferred (low priority cleanup)
**Trigger**: When working on ClickUp features OR during next cleanup sprint
**Request**: Move ClickUp from `execution/` to `projects/shared/clickup-crm/`

**Current State**:
- `execution/clickup_api.py` - Should be in `projects/shared/clickup-crm/src/`
- Used by lead-scraper and other projects
- Works fine in current location

**Migration Steps**:
- [ ] Create `projects/shared/clickup-crm/` structure
- [ ] Move `execution/clickup_api.py` → `projects/shared/clickup-crm/src/clickup_api.py`
- [ ] Update all imports in projects that use it
- [ ] Test all dependent projects
- [ ] Document in `clickup-crm/README.md`

**Blocked By**: Nothing - just low priority since it works fine where it is

---

### 8. Execution Folder Audit & Migration
**Status**: Deferred (large cleanup effort)
**Trigger**: When 3+ projects need same utility OR during major refactor
**Request**: Migrate 60+ files from `execution/` to project-specific locations

**Analysis Complete**: `docs/restructuring/EXECUTION-FOLDER-AUDIT.md`

**Categories Identified**:
- Amazon Seller: 9 files → `projects/marceau-solutions/amazon-seller/src/`
- Interview Prep: 13 files → `projects/marceau-solutions/interview-prep/src/`
- Fitness Influencer: 8 files → `projects/marceau-solutions/fitness-influencer/backend/`
- Shared utilities: Keep in `execution/` (gmail, twilio, etc.)

**Decision**: Migrate incrementally as we work on each project, not all at once

---

### 9. Website Submodule Health Check
**Status**: Routine maintenance
**Trigger**: Weekly OR before deploying website changes
**Request**: Verify website submodules are in sync

**Commands**:
```bash
cd /Users/williammarceaujr./dev-sandbox
git submodule status  # Should show clean commits
git submodule update --remote --merge  # Pull latest from production repos
```

**What to Check**:
- No detached HEAD states
- Submodules point to latest commits
- Production repos (~/) match submodule state
- No uncommitted changes in website folders

---

### 10. Apollo Search Quality Improvements
**Status**: In progress (part of item #1)
**Request**: Iterative search refinement + excluded terms

**Features to Add**:
- Excluded keywords: "sales", "outside", "representative", "intern", "assistant"
- Job title validation (Owner, CEO, President, Founder, Manager only)
- Result quality scoring before enrichment
- Automatic search refinement if results are poor quality

**Example Exclusions**:
```python
excluded_titles = [
    "sales", "outside sales", "sales representative",
    "business development representative",
    "account executive", "inside sales",
    "marketing coordinator", "assistant",
    "intern", "junior"
]
```

---

### 11. Multi-Company Context Detection
**Status**: Planning
**Request**: Auto-detect which company based on prompt

**Companies**:
1. **Marceau Solutions** - AI automation agency
2. **Southwest Florida Comfort** - HVAC services
3. **Footer Shipping** - E-commerce/logistics

**Detection Logic**:
- Keywords: "HVAC", "air conditioning" → Southwest Florida Comfort
- Keywords: "shipping", "e-commerce", "fulfillment" → Footer Shipping
- Keywords: "AI", "automation", "Voice AI" → Marceau Solutions
- Explicit: "for Southwest Florida Comfort" → direct match

**Context Loading**:
Each company has:
- Search templates (industry, keywords, exclusions)
- SMS templates (pain points, value props)
- Follow-up sequences
- Branding (from/reply-to numbers)

---

## 📋 Completed Items

### ✅ Apollo MCP Server Creation
**Completed**: 2026-01-21
**Deliverable**: `/Users/williammarceaujr./dev-sandbox/projects/apollo-mcp/`
- 8 MCP tools for natural language Apollo interaction
- Full package structure (SOP 11)
- Documentation (README, QUICKSTART, TESTING, etc.)

### ✅ Apollo Pipeline Integration
**Completed**: 2026-01-21
**Deliverable**: `/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/lead-scraper/src/apollo_pipeline.py`
- Automated workflow: Search → Score → Filter → Enrich → SMS → Follow-up
- 80-90% credit savings strategy
- CLI interface

### ✅ LinkedIn Personal Posting Setup
**Completed**: 2026-01-21
**Deliverable**: OAuth working, access token saved
- App: Marceau Solutions Automation (7850ny5aexdxs1)
- Scope: `w_member_social`
- Can post to personal profile

### ✅ Apollo.io Cost Optimization Research
**Completed**: 2026-01-21
**Deliverable**: `methods/r-and-d-department/apollo-io-cost-optimization.md`
- Top 3 credit-saving strategies documented
- Export → Qualify → Enrich workflow
- Priority filters guide

---

## 🎯 Next Actions

**Immediate** (Starting now):
1. Enhance Apollo MCP with end-to-end automation
2. Add company context detection
3. Implement excluded terms + iterative search
4. Test full "Run cold outreach for [company]" workflow

**When Ready** (After current work):
1. Publish Apollo MCP to registries
2. Investigate Google Cloud $100 charge
3. Research end-customer deployment strategies

**Waiting On**:
1. LinkedIn API approval → Company page posting
2. Facebook verification → Business page posting

---

**Last Updated**: 2026-01-21 (15:06)
**Active Items**: 11 (added 3 from hybrid architecture session)
**Completed Items**: 4

**Session Notes**: Added items #7-9 from hybrid architecture implementation session - ClickUp migration, execution folder audit, and website submodule maintenance
