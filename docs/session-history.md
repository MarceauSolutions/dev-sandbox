# Session History & Learnings

Running log of significant learnings, decisions, and patterns discovered during development sessions.

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
