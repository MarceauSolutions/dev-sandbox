# Session History & Learnings

Running log of significant learnings, decisions, and patterns discovered during development sessions.

---

## 2026-01-13: MCP Aggregator Platform Generalization

**Context:** Discovered that MCP Aggregator was developed in parallel with rideshare, baking in 51 rideshare-specific assumptions that blocked non-rideshare services. Executed systematic discovery methodology and parallel agent refactoring.

**Accomplished:**
- Created systematic shortcoming discovery methodology (documented in plan file)
- Analyzed 5 core files: router.py, registry.py, billing.py, schema.sql, rideshare_mcp.py
- Found 51 rideshare-specific assumptions blocking non-rideshare services
- Deployed 4 parallel refactoring agents to fix all shortcomings
- All agents completed successfully with comprehensive changes
- Platform now supports 6 connectivity types, 5 pricing models, 6 scoring profiles
- Updated CHANGELOG.md with v1.1.0-dev documentation
- Verified repository structure (no nested .git repos)
- Committed all changes (48 files, 16,960 insertions)

**Key Learnings:**

1. **Shortcoming Discovery Methodology**
   - Define what current implementation assumes (rideshare characteristics)
   - Define what OTHER services need (HVAC, flights, hotels, etc.)
   - Analyze each file for hardcoded vs configurable values
   - Calculate impact scores for non-rideshare services
   - Prioritize fixes by blocking severity

2. **Platform Core Was Dead Code**
   - `rideshare_mcp.py` bypassed platform core entirely
   - Direct HTTP calls instead of using router.py
   - No health tracking, no billing, no scoring
   - **Fix**: Created `aggregator_mcp.py` that uses platform core

3. **Parallel Agent Deployment**
   - Can deploy 4 agents in parallel using Task tool with subagent_type
   - Each agent gets isolated workspace (agent1/, agent2/, etc.)
   - Agents complete independently, consolidate findings after
   - Much faster than sequential refactoring

4. **Non-Rideshare Service Requirements**
   - Flight search: 3-5s latency (not 100-500ms), $0.10-0.25/call
   - HVAC services: 24-48hr response, email-based, per-RFQ billing
   - Hotels: Commission-based (10-15% of booking value)
   - Payment processors: Webhook-based (inbound events)
   - GraphQL APIs: Query-based (different request structure)

**New Communication Patterns:**
- "Determine shortcomings" → Create discovery methodology, analyze systematically
- "Run parallel agents" → Use Task tool with 4 subagents in single message
- "Platform not working for X" → Check if assumptions from parallel development

**Refactoring Changes:**

**Agent 1 - Platform Core Wiring:**
- Created `mcp-server/aggregator_mcp.py` - New MCP using platform core
- Fixed dead code issue - router.py, registry.py, billing.py now actually used
- Added configurable timeout per-MCP (supports hours for async services)

**Agent 2 - Connectivity Abstraction:**
- Added `ConnectivityType` enum: HTTP, EMAIL, OAUTH, WEBHOOK, GRAPHQL, ASYNC
- Made `endpoint_url` optional (not required for email-based services)
- Added `email_address` and `webhook_path` fields to MCP dataclass
- Validation now connectivity-type-specific

**Agent 3 - Flexible Billing:**
- Added `PricingModel` enum: PER_REQUEST, SUBSCRIPTION, COMMISSION, TIERED, HYBRID
- Added `TierConfig` dataclass for volume-based pricing
- Added fee calculation methods for all pricing models
- Added `subscriptions` and `pricing_tiers` tables to schema

**Agent 4 - Configurable Scoring:**
- Added `ScoringProfile` dataclass with configurable thresholds
- Added 6 scoring profiles: rideshare, travel, food_delivery, async, e_commerce, default
- Latency/cost scoring now uses category-specific thresholds
- Scoring weights configurable per-category

**Results:**
- Flight search (3s latency) now scores 100/100 instead of 30/100
- HVAC services (24hr response) now score fairly
- Email-based services can now register
- Commission-based billing now supported

**Files Created:**
- `projects/mcp-aggregator/mcp-server/aggregator_mcp.py` - New MCP server
- `projects/mcp-aggregator/SHORTCOMING-DISCOVERY-REPORT.md` - Complete analysis
- `projects/mcp-aggregator/agent1-rest-api/` - REST API workspace
- `projects/mcp-aggregator/agent2-accuracy-testing/` - Accuracy testing workspace
- `projects/mcp-aggregator/agent3-platform-core/` - Platform core refactoring

**Files Modified:**
- `projects/mcp-aggregator/agent3-platform-core/workspace/router.py` - ScoringProfile
- `projects/mcp-aggregator/agent3-platform-core/workspace/registry.py` - ConnectivityType
- `projects/mcp-aggregator/agent3-platform-core/workspace/billing.py` - PricingModel
- `projects/mcp-aggregator/agent3-platform-core/workspace/schema.sql` - New tables
- `projects/mcp-aggregator/CHANGELOG.md` - v1.1.0-dev documentation

**Next Steps:**
- Integrate refactored platform core back into main mcp-aggregator/src/
- Test with HVAC service registration (next project)
- Deploy aggregator_mcp.py to Claude Desktop
- Create integration tests for all connectivity types

---

## 2026-01-12 (Part 3): Architecture Conflict Resolution - Phase 1 Complete

**Context:** Comprehensive SOP audit revealed 5 major architectural conflicts. Evaluated 3+ solution options for each conflict, chose optimal solutions, and implemented Phase 1 (Documentation Updates).

**Accomplished:**
- Resolved all architectural conflicts with Two-Tier system
- Created comprehensive architecture guide (1000+ lines)
- Updated all core documentation for consistency
- Verified no remaining conflicts across all SOPs

**Key Decisions:**

1. **Code Location**: Hybrid Architecture (Option C)
   - Shared utilities (2+ projects) → `execution/`
   - Project-specific code → `projects/[name]/src/`
   - Extract to `execution/` only when 2+ projects use code

2. **DOE Application**: Two-Tier Architecture (Option C)
   - Tier 1 (Shared): Strict DOE in `execution/`
   - Tier 2 (Projects): Flexible architecture in `projects/[name]/src/`

3. **Skills Deployment**: -prod repos (Option B)
   - Production: `/Users/williammarceaujr./[name]-prod/` (separate repos)
   - Clean git workflow, can push to GitHub

4. **Version Management**: Comprehensive (Option C)
   - VERSION file + CHANGELOG.md + Git tags (three-way sync)

5. **Testing Artifacts**: Separate by Purpose (Option B)
   - `.tmp/` for temporary files
   - `testing/` for multi-agent tests
   - `demos/` for client outputs

**New Documentation:**
- `docs/architecture-guide.md` (1000+ lines) - Complete Two-Tier Architecture reference
  - Decision trees (where to put code, when to extract, how to deploy)
  - Code organization examples
  - Deployment patterns for both tiers
  - Migration guide from old architecture
  - Troubleshooting Q&A

**Files Updated:**
- `CLAUDE.md` - Architecture section replaced with Two-Tier system
  - Documentation Map updated with architecture-guide.md
  - Development Pipeline clarified (execution/ vs projects/src/)
  - "Where to Put Things" table expanded
  - SOP 1 updated with code organization guidance
- `docs/testing-strategy.md` - Integration with Two-Tier Architecture
  - Testing Environment Setup section updated
  - Architecture notes added
- `docs/COMPREHENSIVE-CONFLICT-AUDIT.md` - Status updated (Phase 1 complete)
- `docs/ARCHITECTURE-CONFLICT-RESOLUTION.md` - Status updated (Resolved)
- `docs/SOP-VERIFICATION.md` - Phase 1 implementation status added

**Architecture Resolution:**

**Before** (Conflicting):
```
execution/*.py - Mixed shared and project-specific code
projects/[name]/src/ - Unclear when to use
Confusion about source of truth
```

**After** (Clear):
```
Tier 1: Shared Utilities (Strict DOE)
  execution/*.py - Shared across 2+ projects

Tier 2: Projects (Flexible Architecture)
  projects/[name]/src/*.py - Project-specific code
```

**Decision Rule**: Default to `projects/[name]/src/`, extract to `execution/` when 2+ projects use it.

**Verification:**
- ✅ All documents reference architecture-guide.md
- ✅ Code organization rules clear across all SOPs
- ✅ Testing strategy aligned with Two-Tier Architecture
- ✅ No conflicting guidance remaining

**Critical Addition - Deployment Timing**:

User identified missing guidance: "When in the development, testing, and deployment process do we deploy to skills?"

**Added explicit deployment timing**:
- Updated `docs/architecture-guide.md` - Added "When to Deploy to Skills" section
  - 6-step pipeline diagram showing deployment at Step 5
  - Prerequisites checklist before deployment
  - Timeline example (Day 1-10 showing deployment on Day 10)
- Updated `CLAUDE.md` - Development Pipeline step 5 with prerequisites
  - "NEVER deploy before Step 3 (testing) is complete!"
  - Post-deployment verification step added (Step 6)
- Updated `docs/testing-strategy.md` - Complete 6-step pipeline
  - CRITICAL TIMING section
  - Location rules for each step (dev-sandbox vs -prod)
  - Example timeline (Monday-Saturday showing Friday deployment)
  - Common mistake vs correct timing

**Key Rule Established**: Deploy to skills ONLY after ALL testing complete (Manual → Multi-Agent → Pre-Deployment → THEN Deploy)

**Critical Clarification - Post-Deployment Testing**:

User asked: "How does testing only in dev-sandbox (DOE method files) affect deployment since we deploy to Claude skills method files? Is it worth testing again after deployment?"

**Answer: YES - Post-deployment testing is CRITICAL, not optional**

**Why**:
- Dev-sandbox structure (`projects/[name]/src/`) ≠ Production structure (`[name]-prod/execution/`)
- Different directory paths can cause import errors
- Different working directories can break relative paths
- Missing dependencies not caught until production
- Deployment process itself can introduce bugs

**What Was Updated**:
- Changed Scenario 4 from "RECOMMENDED" to "ALWAYS REQUIRED"
- Updated CLAUDE.md Development Pipeline (Step 6 required)
- Updated testing-strategy.md Scenario 4 with comprehensive checklists:
  - Deployment Structure Verification (files, paths, imports)
  - Functional Testing (same tests as pre-deployment)
  - Troubleshooting guide for common issues
- Added "Why Post-Deployment Testing is Critical" section to architecture-guide.md
  - Visual comparison of dev vs prod structure
  - 5 things that can go wrong
  - Real example showing import error

**New Testing Rule**:
```
Step 4: Pre-Deployment Verification - in dev-sandbox (tests CODE)
Step 5: DEPLOY to skills
Step 6: Post-Deployment Verification - in -prod (tests DEPLOYMENT + STRUCTURE)
```

Both steps 4 and 6 are ALWAYS REQUIRED.

**Next Phase**: Phase 2 (Code Audit & Reorganization) - Audit `execution/` folder to separate shared vs project-specific scripts

---

## 2026-01-12 (Part 2): Multi-Agent Testing Failure & Testing Strategy

**Context:** MD-to-PDF multi-agent testing failed due to premature testing (before implementation stable and environment resolved)

**Accomplished:**
- Root caused testing failure
- Created comprehensive testing strategy
- Updated all SOPs with testing prerequisites
- Documented lessons learned

**Key Learning:** **Test too early = agents crash**

Prerequisites for multi-agent testing:
1. ✅ Manual testing complete (Scenario 1)
2. ✅ Core implementation stable
3. ✅ Environment issues resolved (library paths, dependencies)
4. ✅ Basic workflows documented
5. ✅ Basic functionality verified

**New Documentation:**
- `docs/testing-strategy.md` (400+ lines) - Single source of truth for all testing
  - Scenario 1: Manual Testing (ALWAYS required)
  - Scenario 2: Multi-Agent Testing (OPTIONAL, after Scenario 1)
  - Scenario 3: Pre-Deployment Verification (ALWAYS required)
  - Scenario 4: Post-Deployment Verification (RECOMMENDED)
  - Decision trees for when to use each
  - Prerequisites checklists
- `projects/md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md` - Root cause analysis

**Files Updated:**
- `CLAUDE.md` - Added TEST step to Development Pipeline (between DEVELOP and DEPLOY)
  - SOP 2 updated with CRITICAL PREREQUISITES
  - SOP 3 updated with testing prerequisites
  - Quick Reference table updated
- `docs/development-to-deployment.md` - Testing references added
- `docs/SOP-VERIFICATION.md` - Verified all SOPs consistent

**Testing Pipeline Established:**
```
Manual Testing → Multi-Agent Testing → Pre-Deployment → Deploy → Post-Deployment
(ALWAYS)         (OPTIONAL)            (ALWAYS)         (Done)   (RECOMMENDED)
```

**Success Example**: email-analyzer (tested after stable implementation)
**Failure Example**: md-to-pdf (tested too early, agents crashed)

---

## 2026-01-12 (Part 1): Documentation Process & MD-to-PDF Project

**Context:** Documenting the complete development-to-deployment pipeline, creating comprehensive reference guides

**Accomplished:**
- Created comprehensive development-to-deployment process guide
- Built Markdown to PDF Converter project following SOP 1
- Enhanced CLAUDE.md with development process references
- Documented repository structure and where files live during each phase

**Key Learnings:**
1. **Documentation process** - Create directive, develop in dev-sandbox, document workflows as you work, deploy when ready
2. **Repository structure** - Development in ONE repo (dev-sandbox), production in separate sibling repos
3. **Document types** - Living (session-history, prompting-guide) vs Stable (SOPs, workflows, directives)
4. **WeasyPrint advantages** - Better CSS support and interactive PDF links than ReportLab
5. **Workflow documentation timing** - Document WHILE completing tasks, not after

**New Documentation:**
- `docs/development-to-deployment.md` - Complete guide from dev through deployment (700+ lines)
  - Repository structure (dev vs prod)
  - Documentation process (5 phases)
  - Common workflows
  - Deployment commands reference
  - Where things live at each stage
  - Quick reference checklists

**New Project: MD-to-PDF Converter**
- `directives/md_to_pdf.md` - Capability SOP with edge cases
- `projects/md-to-pdf/src/md_to_pdf.py` - Full implementation (450+ lines)
- `projects/md-to-pdf/workflows/convert-md-to-pdf.md` - Step-by-step workflow
- `projects/md-to-pdf/README.md` - Project overview
- `projects/md-to-pdf/VERSION` - 0.1.0-dev
- `projects/md-to-pdf/CHANGELOG.md` - Version history

**Files Updated:**
- `CLAUDE.md` - Added development-to-deployment.md to Documentation Map

**Architecture Reinforcement:**
```
Development (ONE repo):
/Users/williammarceaujr./dev-sandbox/
  ├── .git/                    ← Single git repo
  ├── directives/              ← What to do
  ├── projects/[name]/         ← NO .git here!
  └── execution/               ← How to do it

Production (MANY repos):
/Users/williammarceaujr./
  ├── dev-sandbox/             ← Development
  ├── [project]-prod/          ← Deployed skills
  │   └── .git/                ← Separate repos
  └── website-repo/            ← Standalone projects
      └── .git/
```

**Next Steps:**
- Test MD-to-PDF converter with various markdown files
- Deploy v1.0.0 when ready
- Use as reference for future documentation projects

---

## 2026-01-09: DOE Architecture Rollback & Website Builder Social Pipeline

**Context:** Rolling back premature deployments to follow DOE (Directive-Orchestration-Execution) architecture properly. Also completed social media research pipeline for website-builder.

### Part 1: Website Builder Social Research Pipeline

**Accomplished:**
- Built complete social media research → website generation pipeline
- Implemented 5 approaches: Direct API, Web Scraping, Hybrid Search, Manual Input, Multi-Agent
- Selected hybrid approach combining Manual Input + Hybrid Search
- Created personality-driven content generation and styling

**Files Created:**
- `projects/website-builder/src/social_profile_analyzer.py` - Parse social URLs, analyze communication style
- `projects/website-builder/src/web_search.py` - Brave/Tavily web search integration
- `projects/website-builder/src/personality_synthesizer.py` - Brand personality synthesis

**Files Updated:**
- `projects/website-builder/src/research_engine.py` - Added `research_with_social()` method
- `projects/website-builder/src/content_generator.py` - Added `generate_personality_content()`
- `projects/website-builder/src/site_builder.py` - Added `build_personality_site()` with dynamic styling
- `projects/website-builder/src/website_builder_api.py` - Added 4 new endpoints for social workflow
- `projects/website-builder/README.md` - Complete rewrite with architecture diagram
- `projects/website-builder/VERSION` - Updated to 0.2.0

**New Endpoints:**
- `POST /api/research/social` - Research with social profiles
- `POST /api/generate/personality` - Personality-driven content
- `POST /api/build/personality` - Personality-styled site
- `POST /api/workflow/social` - Full social workflow

### Part 2: DOE Architecture Rollback

**Problem:** Jumped the gun deploying marketing pages before projects were ready. Violated DOE pattern.

**Rollback Actions:**
1. Updated root `index.html` → "Coming Soon" page with unified inquiry form
2. Updated `contact.html` → Streamlined with consolidated email/SMS opt-in
3. Removed premature pages: `solutions.html`, `about.html`, `setup_form.html`, `nav-styles.css`, `nav-component.js`
4. Updated `website-repo/index.html` → "Coming Soon" with inquiry form
5. Updated `website-repo/contact.html` → Consistent contact form
6. Removed premature website-repo pages: `fitness.html`, `amazon.html`, `medtech.html`, `all-solutions.html`, `services.html`, `about.html`, `assistant.html`, `testimonials.html`, `blog.html`, `signup.html`, `opt-in.html`

**Key Learnings:**
1. **DOE discipline** - Don't deploy frontend until execution layer is solid
2. **Coming Soon pattern** - Show project previews, collect inquiries, auto opt-in for email/SMS
3. **Consolidated opt-in** - Pre-checked email + SMS checkboxes on all forms
4. **Clean rollback** - Remove premature files rather than leaving broken links

**New Communication Patterns:**
- "Roll back" → Remove premature deployments, show Coming Soon
- "Follow DOE" → Check if Directive exists before deploying Execution
- Form submission → Auto opt-in for both email and SMS (pre-checked)

**Architecture Reminder:**
```
DOE Pattern:
Layer 1: DIRECTIVE (directives/*.md)     → What to do
Layer 2: ORCHESTRATION (You/Claude)      → Decision making
Layer 3: EXECUTION (execution/*.py)      → Deterministic scripts
```

Deploy ONLY when all three layers are solid.

---

## 2026-01-08 (Late Night): Fitness Influencer Dual-AI Chat System

**Context:** Building polished web chat interface for Fitness Influencer AI with dual-AI architecture (Claude + Grok)

**Accomplished:**
- Built dual-AI router combining Claude (intent/routing) and Grok (cost optimization/images)
- Implemented cost confirmation guardrails for operations >$0.10
- Created production-ready chat interface with real API integration
- Deployed Fitness Influencer AI to Railway
- Live at: https://api-production-1edc.up.railway.app

**Key Learnings:**
1. **Dual-AI architecture** - Claude handles NLU/routing, Grok handles images + cost suggestions
2. **Cost guardrails** - $0.10 threshold requires user confirmation, show alternatives
3. **Module imports in Railway** - Use `src.module_name` format with try/except for local dev
4. **python-multipart required** - FastAPI file uploads need this dependency
5. **Railway secrets** - Safe for production, but avoid CLI `--set` (logs to shell history)

**New Communication Patterns:**
- "Perfect the Fitness Influencer" → Focus on web chat, not CLI
- Paid operations → Always show cost + alternatives before executing
- "Why show them CLI?" → Client-facing demos should match delivery format

**Cost Tier System:**
- FREE: Video editing, graphics, email, analytics, workout/nutrition plans
- LOW (<$0.10): 1 AI image ($0.07)
- MEDIUM ($0.10-$0.30): 2-4 AI images ($0.14-$0.28)
- HIGH (>$0.30): Video ads ($0.34+)

**Files Created:**
- `projects/fitness-influencer/src/dual_ai_router.py` - Dual-AI decision router
- `projects/fitness-influencer/src/__init__.py` - Module init
- `projects/fitness-influencer/frontend/chat.html` - Chat interface (updated)
- `projects/fitness-influencer/frontend/dashboard.html` - Tool dashboard
- `projects/fitness-influencer/.env.example` - Environment template
- `projects/fitness-influencer/Procfile` - Railway start command
- `projects/fitness-influencer/railway.toml` - Railway config

**Files Updated:**
- `projects/fitness-influencer/src/chat_api.py` - Dual-AI flow, cost tracking
- `projects/fitness-influencer/requirements.txt` - Added python-multipart

**Deployment:**
- Railway project: fitness-influencer-ai
- Service: api
- Domain: https://api-production-1edc.up.railway.app
- Status: Live and healthy

---

## 2026-01-08 (Night): Interview Prep v1.3.0 Full Deployment

**Context:** Deploying Interview Prep AI Assistant with frontend and website integration

**Accomplished:**
- Deployed Interview Prep v1.3.0 to production
- Frontend deployed to Railway (https://interview-prep-pptx-production.up.railway.app/app)
- Added Interview Prep to website Industries dropdown navigation
- Updated solution card with full AI Assistant capabilities
- Enhanced deployment checklist with security review, pre-deployment verification
- Created MCP server configuration with cost-benefit guidelines
- Documented MCP decision matrix for future deployments

**Key Learnings:**
1. **MCP servers are token-intensive** - Use for external/shared assistants, prefer scripts for personal tools
2. **Full deployment = skill + frontend** - Use `deploy_to_skills.py --full` for one-command deploy
3. **Decision matrix location** - Document in `docs/full-deployment-pipeline.md` for future reference
4. **Industries dropdown** - Edit `nav-component.js` to add new solutions

**Deployment Checklist Additions:**
- Pre-deployment verification (git status, env vars, no hardcoded secrets)
- Security review section (credentials, input validation, API protection)
- Post-deployment monitoring (first hour)
- Documentation section (README, API docs, help text)

**Files Created/Updated:**
- `docs/full-deployment-pipeline.md` - Enhanced deployment checklist
- `.claude/mcp-servers/mcp-config.json` - MCP configuration with cost guidance
- `docs/mcp-integration-opportunities.md` - MCP research and analysis
- `nav-component.js` - Added Interview Prep to Industries dropdown
- `index.html` - Updated solution card to "Interview Prep AI Assistant"
- `.claude/skills/interview-prep/SKILL.md` - Updated to v1.3.0

**Current Status:**
- Production version: 1.3.0
- Development version: 1.4.0-dev
- Frontend: Live at Railway
- Skill: Deployed to `.claude/skills/interview-prep/`

---

## 2026-01-08 (Late Evening): Interview Prep Expansion & Personal AI Assistant

**Context:** Expanding Interview Prep from PowerPoint-only to comprehensive assistant, setting up Personal AI Assistant project

**Accomplished:**
- Expanded Interview Prep scope from "PowerPoint Builder" to full "AI Assistant"
- Built mock interview capability with STAR format evaluation
- Built PDF output generator (cheat sheets, talking points, flashcards, checklists)
- Built intent router for unified conversational interface
- Created Personal AI Assistant project structure
- Updated all documentation to reflect new organization
- Clarified living vs stable documents

**Key Learnings:**
1. **Mock interviews** - Use behavioral/technical/case types, evaluate with STAR format
2. **Intent routing** - Classify user request → route to appropriate workflow
3. **Personal Assistant** - Aggregates all skills, no frontend, Claude Code chat only
4. **Document types** - Living (session-history, prompting-guide, CLAUDE.md) vs Stable (SOPs, workflows)

**New Communication Patterns:**
- "Practice interview with me" → Start mock_interview.py with company/role context
- "Give me a cheat sheet" → Run pdf_outputs.py --output cheat-sheet
- All requests → Route through personal-assistant skill for consistency

**Files Created:**
- `interview-prep-pptx/src/mock_interview.py` - Interactive mock interviews
- `interview-prep-pptx/src/pdf_outputs.py` - Cheat sheets, flashcards, etc.
- `interview-prep-pptx/src/intent_router.py` - Request routing
- `interview-prep-pptx/EXPANDED_SCOPE.md` - Vision for expanded assistant
- `interview-prep-pptx/workflows/mock-interview.md` - Mock interview workflow
- `interview-prep-pptx/workflows/quick-outputs.md` - PDF outputs workflow
- `projects/personal-assistant/README.md` - Personal assistant overview
- `projects/personal-assistant/VERSION` - 1.0.0-dev
- `projects/personal-assistant/CHANGELOG.md` - Version history
- `.claude/skills/personal-assistant/SKILL.md` - Master skill file

**Files Updated:**
- `.claude/skills/interview-prep/SKILL.md` - Expanded capabilities, v1.2.0-dev
- `interview-prep-pptx/VERSION` - Now 1.2.0-dev
- `deploy_to_skills.py` - Added personal-assistant project
- `docs/deployment.md` - Added personal-assistant to architecture
- `CLAUDE.md` - Clarified living vs stable documents

---

## 2026-01-08 (Evening): Versioned Deployment & User Guidance System

**Context:** Building systems for iterative deployment and better user experience

**Accomplished:**
- Created versioned deployment pipeline (like Anthropic ships Claude versions)
- Built user guidance prompts system for interview prep assistant
- Created inference guidelines for intelligent scope extension
- Fixed PowerPoint close-before-open issue
- Updated Brookhaven presentation with consistent theme and enhanced content

**Key Learnings:**
1. **Versioned deployments** - Use VERSION file + CHANGELOG.md per project
2. **Inference guidelines** - Very Low/Low/Medium/High risk determines action
3. **User guidance** - Show next-step prompts after each workflow stage
4. **Theme colors corrected** - #1A1A2E (dark navy), not #003366
5. **Relevance label** - Adobe red #EC1C24 for visual hierarchy

**New Communication Patterns:**
- "Deploy to skills" → Check version, use `deploy_to_skills.py --version X.X.X`
- After any major action → Show user guidance prompts with next options
- Styling changes → Apply to ALL slides (infer consistency)
- Content changes → Only change specified content (don't override user edits)

**Files Created:**
- `docs/versioned-deployment.md` - Complete versioning guide
- `docs/inference-guidelines.md` - When to extend scope vs ask
- `interview-prep-pptx/USER_PROMPTS.md` - User guidance at each stage
- `interview-prep-pptx/VERSION` - Current: 1.1.0-dev
- `interview-prep-pptx/CHANGELOG.md` - Version history
- `execution/download_pptx.py` - Download to ~/Downloads
- `execution/open_pptx.py` - Close previous before opening new
- `execution/enhance_experience_slides.py` - Rich content for slides 14-18

**Scripts Updated:**
- `deploy_to_skills.py` - Added `--status`, `--version` flags
- `live_editor.py` - Added `close_all_presentations()` function
- `apply_navy_theme.py` - Corrected to #1A1A2E

---

## 2026-01-08 (Morning): Interview Prep Workflows & Documentation Reorg

**Context:** Working on Brookhaven National Laboratory presentation, building live editing capabilities

**Accomplished:**
- Created `live_editor.py` for real-time PowerPoint editing
- Created `template_manager.py` for loading existing presentations
- Created `reformat_experience_slides.py` for standardizing slide layouts
- Created `apply_navy_theme.py` for consistent theming
- Built workflow documentation system in `interview-prep-pptx/workflows/`
- Reorganized dev-sandbox documentation structure

**Key Learnings:**
1. **Build workflows as you work** - Document procedures while completing tasks, not after
2. **Experience slide layout:** Title (0.55", 0.3"), Image (0.75", 1.5"), Description (6.55", 1.5"), Relevance (6.55", 4.5")

**New Communication Patterns:**
- "Make slides look like slide X" → Use inspection + reformatting scripts
- "I have the file open" → Start live editing session
- "Don't deploy yet" → Stay in dev-sandbox, iterate locally

**Files Created:**
- `execution/live_editor.py`
- `execution/template_manager.py`
- `execution/reformat_experience_slides.py`
- `execution/apply_navy_theme.py`
- `interview-prep-pptx/workflows/*.md` (6 workflow files)

---

## 2026-01-07: Interview Prep Initial Build

**Context:** Building interview prep PowerPoint generator

**Accomplished:**
- Fixed Railway 500 error (direct module imports vs importlib)
- Combined Steps 1 & 2 into single workflow
- Added slide preview functionality
- Generated first Brookhaven presentation with AI images

**Key Learnings:**
1. Railway needs direct imports, not dynamic importlib
2. Session management helps track iterative edits
3. Grok API costs ~$0.07/image

---

## Adding New Entries

When completing a session with significant learnings:

```markdown
## YYYY-MM-DD: [Brief Title]

**Context:** [What you were working on]

**Accomplished:**
- Item 1
- Item 2

**Key Learnings:**
1. Learning 1
2. Learning 2

**New Communication Patterns:** (if any)
- "User says X" → Do Y

**Files Created:** (if any)
- path/to/file.py
```
