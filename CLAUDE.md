# Agent Instructions

> Read this file at the start of every session. It contains core operating methods and pointers to detailed documentation.

## Architecture: Two-Tier System

### Tier 1: Shared Utilities (Strict DOE)

**For code used by multiple projects:**

```
Layer 1: DIRECTIVE (directives/shared_utilities.md)
Layer 2: ORCHESTRATION (Claude)
Layer 3: EXECUTION (execution/*.py) ← Shared across multiple projects
```

### Tier 2: Projects (Flexible Architecture)

**For project-specific code:**

```
Layer 1: DIRECTIVE (directives/[project].md)
Layer 2: ORCHESTRATION (Claude or standalone)
Layer 3: IMPLEMENTATION (projects/[project]/src/*.py) ← Project-specific
```

### Decision Rules: Where to Put Code

**Put code in `execution/` when:**
- Used by 2+ projects
- Stable, shared API
- General-purpose utility

**Put code in `projects/[name]/src/` when:**
- Used by 1 project only
- Project-specific logic
- Frequently changing during development

**Your role:** Read directives, orchestrate execution (shared utilities) or implementation (project code), handle errors, update docs with learnings.

**Why this works:** Shared utilities follow strict DOE for stability. Projects have flexibility for rapid iteration.

**See:** [docs/architecture-guide.md](docs/architecture-guide.md) for comprehensive architecture explanation and decision trees.

## Documentation Map

| Need | Location |
|------|----------|
| **How we work** | This file (CLAUDE.md) |
| **Architecture & code organization** | `docs/architecture-guide.md` ⭐ |
| **App type decision** | `docs/app-type-decision-guide.md` ⭐ |
| **Mobile app development** | `docs/mobile-app-development-guide.md` ⭐ |
| **Cost-benefit analysis** | `docs/cost-benefit-templates.md` |
| **Project kickoff questionnaire** | `templates/project-kickoff-questionnaire.md` |
| **How to prompt me** | `docs/prompting-guide.md` |
| **Inference guidelines** | `docs/inference-guidelines.md` |
| **Dev-to-deployment process** | `docs/development-to-deployment.md` ⭐ |
| **Testing strategy** | `docs/testing-strategy.md` ⭐ |
| **Deployment pipeline** | `docs/deployment.md` |
| **Repository management** | `docs/repository-management.md` ⭐ |
| **Repository quick ref** | `docs/REPO-QUICK-REFERENCE.md` |
| **Versioned deployment** | `docs/versioned-deployment.md` |
| **Cloud function model** | `docs/cloud-function-deployment-analysis.md` ⭐ |
| **Optimization thresholds** | `docs/optimization-threshold-policy.md` ⭐ |
| **Project navigation** | `docs/projects.md` |
| **Workflow template** | `docs/workflow-standard.md` |
| **Session learnings** | `docs/session-history.md` |
| **Autonomous agent triggers** | `docs/autonomous-agent-decision-tree.md` ⭐ |
| **Deferred features/reminders** | `projects/social-media-automation/DOCKET.md` ⭐ |
| **Documentation decision framework** | `docs/SOP-25-DOCUMENTATION-DECISION-FRAMEWORK.md` ⭐ |
| **User statement validation (MANDATORY)** | `docs/SOP-26-USER-STATEMENT-VALIDATION-PROTOCOL.md` ⭐ |
| **Clawdbot usage (when/how)** | `docs/SOP-27-CLAWDBOT-USAGE.md` ⭐ |
| **Ralph usage (when/how)** | `docs/SOP-28-RALPH-USAGE.md` ⭐ |
| **Three-agent collaboration (NEW)** | `docs/SOP-29-THREE-AGENT-COLLABORATION.md` ⭐ |
| **Clawdbot capabilities** | `docs/CLAWDBOT-CAPABILITIES.md` |
| **Clawdbot ops manual** | `docs/CLAWDBOT-OPS-MANUAL.md` |
| **Clawdbot test plan** | `docs/CLAWDBOT-TEST-PLAN.md` |
| **Clawdbot implementation** | `docs/CLAWDBOT-IMPLEMENTATION-SUMMARY.md` |
| **Troubleshooting methodology** | `docs/TROUBLESHOOTING-METHODOLOGY.md` ⭐ |
| **AI routing optimization** | `docs/AI-ROUTING-OPTIMIZATION.md` ⭐ |
| **Ralph capabilities** | `docs/RALPH-CAPABILITIES.md` |
| **n8n transition plan** | `docs/N8N-TRANSITION-PLAN.md` ⭐ |
| **n8n workflow management (SOP 30)** | See SOP 30 below ⭐ |
| **n8n Agent Orchestrator** | `docs/AGENT-ORCHESTRATOR-GUIDE.md` ⭐ |
| **EC2 n8n setup** | `docs/EC2-N8N-SETUP.md` |
| **Folder structure decisions** | `docs/FOLDER-STRUCTURE-GUIDE.md` ⭐ |
| **Hybrid architecture quick ref** | `docs/HYBRID-ARCHITECTURE-QUICK-REF.md` |
| **MCP conversion plan** | `docs/MCP-CONVERSION-PLAN.md` |
| **Credentials & API keys** | `.env` (root of dev-sandbox) ⭐ |
| **Capability SOPs** | `directives/` |
| **Task procedures** | `[project]/workflows/` |
| **Incident reports** | `docs/incidents/` |
| **Archived documentation** | `docs/archive/` |

## Development Pipeline (DOE → Skills)

**Complete documentation**: See `docs/development-to-deployment.md` for full process, or `docs/deployment.md`, `docs/repository-management.md`, `docs/versioned-deployment.md` for specific topics.

```
-1. RESEARCH (SOP 17/9) - BEFORE committing resources
   └── For NEW product ideas: SOP 17 Market Viability (4 agents)
   └── For OPTIMIZATION decisions: SOP 9 Multi-Agent Exploration (3-4 agents)
   └── Output: GO/NO-GO decision or optimal approach selection
   └── Skip if: Internal tool, <2 days effort, or clear requirements

0. KICKOFF (SOP 0) - BEFORE starting any new project
   └── Prerequisites: ✅ SOP 17 = GO (if applicable)
   └── Complete project-kickoff-questionnaire.md (19 questions)
   └── Decide app type (MCP, CLI, Web, Desktop, Hybrid, Mobile, PWA)
   └── If Mobile considered: Run Mobile App Viability Scorecard (≥24 to proceed)
   └── Complete cost-benefit analysis
   └── Decide template vs clean slate
   └── See: docs/app-type-decision-guide.md, docs/mobile-app-development-guide.md

1. DESIGN in directives/
   └── Create/update [project].md with capability SOPs
   └── Define what the project does

2. DEVELOP in dev-sandbox
   └── NO git init inside projects! (see repository-management.md)
   └── Project-specific code: projects/[project]/src/
   └── Shared utilities (2+ projects): execution/
   └── Workflows in: [project]/workflows/
   └── See: docs/architecture-guide.md for where to put code
   └── Commit to dev-sandbox repo (parent tracks all)

3. TEST in dev-sandbox (BEFORE deployment!)
   └── Manual testing (ALWAYS required)
   └── Multi-agent testing (OPTIONAL for complex projects)
   └── Pre-deployment verification
   └── See: docs/testing-strategy.md for complete pipeline

4. ORCHESTRATE (You/Claude)
   └── Read directives
   └── Call execution scripts
   └── Build workflows AS you complete tasks
   └── Update directive with learnings

5. DEPLOY when ALL testing complete (Step 3 finished)
   └── Prerequisites: ✅ Manual testing, ✅ Multi-agent (if complex), ✅ Pre-deployment verification
   └── python deploy_to_skills.py --project [name] --version X.Y.Z
   └── Creates separate repo: ~/production/[name]-prod/
   └── NOT nested in dev-sandbox (see repository-management.md)
   └── NEVER deploy before Step 3 (testing) is complete!

6. POST-DEPLOYMENT VERIFICATION (ALWAYS REQUIRED)
   └── Test in production repo to verify deployment succeeded
   └── Verify scripts run identically in -prod structure
   └── Test imports and dependencies in production environment
   └── See: docs/testing-strategy.md Scenario 4

7. MCP REGISTRY PUBLISHING (OPTIONAL - for MCP projects)
   └── Prerequisites: ✅ Steps 1-6 complete, ✅ PyPI account, ✅ GitHub account
   └── SOP 11: Create MCP package structure (pyproject.toml, server.json)
   └── SOP 12: Publish to PyPI (pip install [project]-mcp)
   └── SOP 13: Publish to MCP Registry (Claude marketplace)
   └── See: SOPs 11-13 for detailed steps
```

**CRITICAL**:
- Deployment happens AFTER dev-sandbox testing (Step 5), not during development (Step 2)
- Post-deployment verification (Step 6) is REQUIRED to catch deployment/structure issues
- Production structure is different from dev-sandbox (execution/ vs projects/src/)

**Repository structure**:
- **dev-sandbox/**: Development workspace (ONE git repo)
- **production/[project]-prod/**: Deployed skills (SEPARATE git repos)
- **websites/[site]/**: Company & client websites (SEPARATE git repos)
- **active-projects/[project]/**: Standalone GitHub projects (SEPARATE git repos)
- **Never nest repos**: Within dev-sandbox, `find . -name ".git" -type d` should only show `./.git`

### Key Commands

**Repository management**:
```bash
# Check for nested repos (run weekly)
cd /Users/williammarceaujr./dev-sandbox && find . -name ".git" -type d
# Should only show: ./.git

# Commit dev-sandbox changes (includes all projects)
cd /Users/williammarceaujr./dev-sandbox
git add .
git commit -m "feat: Description"
git push
```

**Deployment**:
```bash
python deploy_to_skills.py --list                    # List projects + versions
python deploy_to_skills.py --status [name]           # Check dev vs prod version
python deploy_to_skills.py --sync-execution --project [name]  # Sync to execution/
python deploy_to_skills.py --project [name] --version 1.1.0   # Deploy with version
python deploy_to_skills.py --project [name] --repo [org/repo]  # Deploy to GitHub
```

## Three-Agent Development Integration (SOP-29)

**Purpose**: All development—regardless of project type—follows the three-agent collaboration model. This section maps agents to development phases.

**Reference**: `docs/SOP-29-THREE-AGENT-COLLABORATION.md` for complete routing logic.

### Agent Capabilities Summary

| Agent | Platform | Availability | Complexity Range | Best For |
|-------|----------|--------------|------------------|----------|
| **Claude Code** | Mac terminal | When user present | Any (Mac-specific) | Interactive debugging, PyPI/MCP publishing, live editing |
| **Clawdbot** | EC2 24/7 | Always (Telegram) | 0-6 | Quick tasks, research, simple builds, mobile access |
| **Ralph** | EC2 24/7 | Via PRD trigger | 7-10 | Complex multi-story builds, autonomous overnight work |

### Development Pipeline → Agent Mapping

```
-1. RESEARCH (SOP 17/9)
    └── Claude Code: Interactive exploration when present
    └── Clawdbot: 24/7 research, web search, competitor analysis
    └── Ralph: Complex 4-agent market viability (SOP 17)

0. KICKOFF (SOP 0)
    └── Claude Code: Interactive questionnaire completion
    └── Clawdbot: Quick kickoff for simple projects (complexity 0-4)
    └── Ralph: N/A (kickoff requires human decisions)

1. DESIGN in directives/
    └── Claude Code: Interactive directive creation
    └── Clawdbot: Simple directive templates
    └── Ralph: Complex system architecture docs (PRD-driven)

2. DEVELOP in dev-sandbox
    └── Claude Code: Interactive development, debugging, Mac-specific
    └── Clawdbot: Builds complexity 0-6 autonomously
    └── Ralph: Builds complexity 7-10 via PRD (multi-story)

3. TEST in dev-sandbox
    └── Claude Code: Interactive test runs, debugging failures
    └── Clawdbot: Run Scenario 1 (manual testing) for simple projects
    └── Ralph: Generate test suites, run SOP 2 (multi-agent testing)

4. ORCHESTRATE
    └── Claude Code: Primary orchestrator when present
    └── Clawdbot: Orchestrate simple workflows, trigger Ralph
    └── Ralph: Self-orchestrating for PRD execution

5. DEPLOY
    └── Claude Code: REQUIRED for PyPI/MCP Registry (Mac keychain)
    └── Clawdbot: Git commits, GitHub pushes (non-PyPI)
    └── Ralph: Prepare for deployment, hand off to Claude Code

6. POST-DEPLOYMENT VERIFICATION
    └── Claude Code: Interactive verification, debugging
    └── Clawdbot: Automated smoke tests
    └── Ralph: N/A (verification is interactive)

7. MCP REGISTRY PUBLISHING
    └── Claude Code: REQUIRED (mcp-publisher uses Mac auth)
    └── Clawdbot: N/A (Mac-specific tools)
    └── Ralph: N/A (Mac-specific tools)
```

### SOP → Agent Mapping Matrix

| SOP | Name | Claude Code | Clawdbot | Ralph |
|-----|------|-------------|----------|-------|
| **SOP 0** | Project Kickoff | ✅ Primary | ⚠️ Simple only | ❌ |
| **SOP 1** | New Project Init | ✅ Primary | ✅ Complexity 0-6 | ✅ Complexity 7-10 |
| **SOP 2** | Multi-Agent Testing | ✅ Orchestrate | ❌ | ✅ Generate tests |
| **SOP 3** | Version Control & Deploy | ✅ Primary | ✅ Git only | ❌ |
| **SOP 9** | Architecture Exploration | ✅ Interactive | ✅ Research | ✅ Complex analysis |
| **SOP 10** | Parallel Development | ✅ Orchestrate | ✅ Components 0-6 | ✅ Components 7-10 |
| **SOP 11** | MCP Package Structure | ✅ REQUIRED | ❌ | ❌ |
| **SOP 12** | PyPI Publishing | ✅ REQUIRED | ❌ | ❌ |
| **SOP 13** | MCP Registry Publish | ✅ REQUIRED | ❌ | ❌ |
| **SOP 14** | MCP Update/Version Bump | ✅ REQUIRED | ❌ | ❌ |
| **SOP 17** | Market Viability | ✅ Orchestrate | ✅ Research agents | ✅ 4-agent execution |
| **SOP 18** | SMS Campaign | ✅ Primary | ✅ Execute (Phase 4+) | ❌ |
| **SOP 30** | n8n Workflow Mgmt | ✅ Primary | ✅ Basic workflows | ✅ Complex automation |

### Complexity Scoring Quick Reference

| Score | Examples | Agent |
|-------|----------|-------|
| **0-3** | Typo fix, research, status check, simple question | Clawdbot |
| **4-6** | 3-4 file build, Flask API, calculator, SMS script | Clawdbot |
| **7-8** | 8+ stories, multi-component, test suite | Ralph |
| **9-10** | Full app with database, API, tests, docs | Ralph |
| **Any (Mac)** | PyPI, MCP Registry, Xcode, iOS | Claude Code |

### Handoff Patterns

**Clawdbot → Ralph** (complexity escalation):
```
User: "Build analytics dashboard"
Clawdbot: Scores as 8 → Creates PRD → Triggers Ralph → Monitors progress
Ralph: Executes 8 stories → Notifies Clawdbot on completion
Clawdbot: Verifies → Reports to user
```

**Ralph → Claude Code** (deployment handoff):
```
Ralph: Completes complex build → Commits to git → Creates "ready to deploy" note
Clawdbot: Notifies user "Ready for PyPI publishing"
User (on Mac): "Deploy to PyPI"
Claude Code: SOP 12 → SOP 13 → Published
```

**Claude Code → Clawdbot** (mobility handoff):
```
User (Mac): "I'm heading out, continue this"
Claude Code: Summarizes state → User tells Clawdbot to continue
Clawdbot: Picks up work → Commits progress
User (mobile): Monitors via Telegram
```

### Testing Strategy Integration

| Testing Scenario | Primary Agent | Supporting Agent |
|------------------|---------------|------------------|
| **Scenario 1**: Manual Testing | Claude Code (interactive) | Clawdbot (simple scripts) |
| **Scenario 2**: Multi-Agent Edge Cases | Ralph (test generation) | Claude Code (orchestrate) |
| **Scenario 3**: Pre-Deployment | Claude Code (verification) | Clawdbot (smoke tests) |
| **Scenario 4**: Post-Deployment | Claude Code (interactive) | Clawdbot (automated checks) |

### Operating Principle #9a Integration

When Operating Principle #9a (Pre-commit testing gate) triggers:
- **Claude Code**: Runs imports, verifies functionality interactively
- **Clawdbot**: Can run basic import tests: `python -c "from module import X"`
- **Ralph**: Should auto-include testing phase in every PRD with implementation

**Auto-add testing phase rule**: Any PRD or plan with "implement" must include corresponding "test" phase.

### Unified Agent Decision Flowchart

**Three decisions to make for every task:**

```
STEP 1: SELECT PRIMARY AGENT
─────────────────────────────
Is task Mac-specific? (PyPI, MCP, Xcode, iOS)
├─ YES → Claude Code (REQUIRED)
└─ NO ↓

Is user present at Mac?
├─ YES → Prefer Claude Code (interactive)
└─ NO ↓

Score task complexity (0-10):
├─ 0-6 → Clawdbot
└─ 7-10 → Ralph (via PRD)


STEP 2: SPAWN SUBAGENTS? (Task tool)
────────────────────────────────────
Does task involve:
├─ Multiple valid approaches to research? → YES: Spawn 3-4 Explore agents (SOP 9)
├─ New product/idea validation? → YES: Spawn 4 market viability agents (SOP 17)
├─ Complex feature with 5+ edge cases? → YES: Spawn 4 testing agents (SOP 2)
├─ 4+ independent components to build? → YES: Spawn parallel dev agents (SOP 10)
├─ Open-ended codebase research? → YES: Spawn Explore agent(s)
└─ None of above → NO subagents needed


STEP 3: AGENT COMBINATIONS
──────────────────────────
Primary: Claude Code
├─ Can spawn: Explore, Plan, general-purpose subagents
├─ Can trigger: Clawdbot (via Telegram), Ralph (via PRD)
└─ Receives from: Ralph (deployment handoff)

Primary: Clawdbot
├─ Can spawn: Limited (no Task tool currently)
├─ Can trigger: Ralph (via PRD webhook)
└─ Receives from: Claude Code (mobility handoff), Ralph (completion)

Primary: Ralph
├─ Can spawn: N/A (self-contained PRD execution)
├─ Can trigger: N/A (autonomous)
└─ Hands off to: Claude Code (for Mac-specific), Clawdbot (for notification)
```

### Subagent Types (Task Tool)

| Subagent Type | When to Use | Spawned By |
|---------------|-------------|------------|
| **Explore** | Codebase research, file discovery | Claude Code |
| **Plan** | Architecture planning, implementation design | Claude Code |
| **general-purpose** | Multi-step research, keyword search | Claude Code |
| **Bash** | Git operations, command execution | Claude Code |

### Decision Matrix: Full Combinations

| Scenario | Primary | Subagents? | Example |
|----------|---------|------------|---------|
| Quick question | Clawdbot | No | "What's the weather?" |
| Simple build (3 files) | Clawdbot | No | "Build Flask API" |
| Complex build (8+ stories) | Ralph | No (self-contained) | "Build analytics dashboard" |
| Mac deployment | Claude Code | No | "Deploy to PyPI" |
| Research + decide approach | Claude Code | Yes (3-4 Explore) | "How should we implement X?" |
| New product validation | Claude Code | Yes (4 market agents) | "Should we build X?" |
| Edge case testing | Claude Code + Ralph | Yes (4 test agents) | "Test thoroughly" |
| Large parallel build | Claude Code | Yes (3-4 dev agents) | "Build these 5 components" |
| Codebase exploration | Claude Code | Yes (Explore) | "Find all auth-related code" |
| Mobile + overnight work | Clawdbot → Ralph | No | "Build X while I sleep" |

### When NOT to Spawn Subagents

- Simple single-file edits (overkill)
- Quick lookups (faster directly)
- User doing step-by-step (respect their pace)
- Unclear requirements (clarify first)
- Complexity 0-3 tasks (Clawdbot handles alone)

## Communication Patterns (William ↔ Claude)

| William Says | Claude Does |
|--------------|-------------|
| "Make slides look like slide X" | Inspect target → run reformat script |
| "Make it consistent" / "Same style" | Apply theme to ALL slides |
| "I have the file open" | Start live editing session |
| "Download it" / "Save final version" | Copy to ~/Downloads |
| "Continue from last night" | Template mode workflow |
| "Deploy to skills" / "Ship it" | Use deploy_to_skills.py with version |
| "Don't deploy yet" | Stay in dev-sandbox, iterate locally |
| "Save session progress" | Update docs/session-history.md |
| "Document this" / "Create workflow" | Create/update workflow or SOP |
| "Roll back" | Remove premature deployments, show Coming Soon |
| "Follow DOE" | Check if Directive exists before deploying |
| "Perfect the [project]" | Focus on production-ready polish |
| "Run multi-agent testing" | Launch specialized testing agents |
| "Run parallel agents" | Deploy multiple agents simultaneously via Task tool |
| "Determine shortcomings" | Create discovery methodology, analyze systematically |
| "Save this for the client" | Move output to demos/client-[name]/$(date)/ |
| "This is a good example" | Move to samples/ for documentation reference |
| "Clean up test files" | Delete everything in .tmp/ |
| "Publish to registry" / "Put on Claude marketplace" | Run SOPs 11-13 (MCP → PyPI → Registry) |
| "Make this an MCP" | Run SOP 11 (create package structure) |
| "Update the MCP" / "Push new version" | Run SOP 14 (version bump → PyPI → Registry) |
| "Run SMS campaign" / "Send outreach" | Run SOP 18 (template approval → dry run → send) |
| "Start follow-up sequence" | Run SOP 19 (create campaign → process due) |
| "Create a method for [X]" | Run SOP 20 (Internal Method Development) |
| "How should we classify [X]" | Run SOP 20 (Internal Method Development) |
| "Should this be an SOP?" | Run SOP 21 (score using decision tree) |
| "Log this as a product opportunity" | Add entry to methods/product-opportunities/OPPORTUNITY-LOG.md |
| "This could be a product" | Ask for details, add to OPPORTUNITY-LOG.md |
| "Weekly product review" | Open OPPORTUNITY-LOG.md, review pending items |
| "Show campaign analytics" / "How's the campaign doing?" | Run `python -m src.campaign_analytics report` (SOP 22) |
| "Which template performs best?" | Run `python -m src.campaign_analytics templates` (SOP 22) |
| "Record response from [phone]" | Run `python -m src.campaign_analytics response --phone X --category Y` |
| "Show conversion funnel" | Run `python -m src.campaign_analytics funnel` (SOP 22) |
| "Create A/B test" / "Test this message" | Run SOP 23 (create hypothesis → design test → execute) |
| "New outreach strategy for [segment]" | Run SOP 23 (define segment → create hypotheses → test) |
| "Should we build X?" / "Is X worth it?" | **AUTO**: Launch SOP 17 (4 market viability agents) |
| "I have an idea for..." / "What about selling..." | **AUTO**: Launch SOP 17 (4 market viability agents) |
| "How should we implement X?" | **AUTO**: Launch SOP 9 (3-4 architecture agents) |
| "Multiple ways to do this..." | **AUTO**: Launch SOP 9 (3-4 architecture agents) |
| Complex feature completed | **AUTO**: Launch SOP 2 (4 testing agents) after manual pass |
| "Check the docket" / "What's deferred?" | Review DOCKET.md, report items with met triggers |
| "Create a new company" / "Add company [Name]" | Run `./scripts/create-company-folder.sh "Company Name"` |
| "Add [project] to [company]" / "Create [tool] for [company]" | Run `./scripts/add-company-project.sh company-name "project-name" type` |
| "Add a website for [company]" | Follow hybrid architecture website submodule setup (see FOLDER-STRUCTURE-GUIDE.md) |
| "Add a shared tool" / "Multi-tenant [tool]" | Create in `projects/shared/[tool-name]/` (used by 2+ companies) |
| "Document this setup" / "Save this config" | Use SOP-25 decision tree → Create setup guide |
| "Don't forget this" / "Save this decision" | Create decision record with rationale |
| "This should be in the SOPs" | Evaluate using SOP-25 → Create SOP if warranted |
| "We should document [X]" | Determine doc type (Setup Guide/SOP/Decision Record/Workflow) |
| "Start Ralph for [project]" / "Use Ralph" | Read prd.json, run ALL stories autonomously, stop at checkpoints |
| "Start Ralph in manual mode" | Implement ONE story, wait for "continue ralph" |
| "Continue Ralph" / "Next Ralph iteration" | Resume after checkpoint OR next story (manual mode) |
| "Ralph status" | Show X/Y complete, next story, checkpoints ahead |
| "Integrate Ralph correctly" | Set up Ralph structure for autonomous development loops |
| "Quick question..." | Route to Clawdbot (if mobile) or answer directly |
| "Build X while I sleep" | Route to Ralph via Clawdbot PRD creation |
| "Help me debug..." | Route to Claude Code (interactive session needed) |
| "Research X" | Route to Clawdbot (24/7 web search capability) |
| "Tell Clawdbot to..." / "Ask Clawdbot..." | Delegate to Clawdbot via Telegram |
| "Ralph: Build..." | Direct Ralph trigger with PRD |
| "Route this to..." | Follow AI routing optimization doc |
| "Check my ideas" / "What's in my idea queue?" | Run `python -m src.ideas_queue list` → Show pending ideas from Telegram |
| "Mark idea X done" / "Complete idea X" | Run `python -m src.ideas_queue complete X` |
| "New Upwork client: [name]" | Create `~/upwork-projects/clients/[name]/` with README + TIMESHEET |
| "Log [X] hours on [client]" | Update `~/upwork-projects/clients/[client]/TIMESHEET.md` |
| "Package [client] for delivery" | Prepare clean handoff in client folder |
| "Switch to Upwork workspace" | Work in `~/upwork-projects/` (separate from dev-sandbox) |
| "New website client: [name]" | Run `~/website-projects/scripts/new-client.sh "[name]"` |
| "Use [template] for [client]" | Copy template to `~/website-projects/clients/[client]/site/` |
| "Switch to website workspace" | Work in `~/website-projects/` (separate from dev-sandbox) |
| *(SSH/EC2 commands)* | **Claude announces:** "I'm about to SSH into EC2—you'll see a fingerprint prompt." |

**Prompt interpretation:** See `docs/prompting-guide.md` for complete phrase mappings.

**When unclear:** Ask before deploying or making irreversible changes.

## Operating Principles

1. **Follow DOE discipline** - Don't deploy frontend until execution layer is solid
   - Layer 1 (Directive) must exist before Layer 3 (Execution)
   - Deploy ONLY when all three layers are complete

2. **Check for existing tools first** - BEFORE creating anything new:
   - Search `projects/` for similar capabilities
   - Check `execution/` for shared utilities (gmail_monitor.py, twilio_sms.py, etc.)
   - Check `[project]/workflows/` for documented procedures
   - Run: `ls projects/` to see all available projects
   - Run: `grep -r "keyword" projects/` to find relevant functionality
   - **Goal: Reuse existing work, don't reinvent the wheel**

   **Quick Reference - Common Tools:**
   - **Email/Gmail:** `execution/gmail_monitor.py` OR `projects/shared/personal-assistant/src/digest_aggregator.py`
   - **SMS:** `execution/twilio_sms.py`
   - **Lead Management:** `projects/shared/lead-scraper/`
   - **Social Media:** `projects/social-media-automation/`
   - **Video Generation:** Shotstack (documented), Creatomate (researched)
   - **Image Generation:** Grok/XAI API (execution/grok_image_gen.py if created)
   - **Apollo.io:** `projects/shared/lead-scraper/` (has Apollo integration)

3. **Build workflows as you work** - Document procedures while completing tasks
   - Create workflows in `[project]/workflows/` as tasks are completed
   - Update directives with learnings after each task

4. **Self-anneal** - When errors occur: fix → update tool → update directive
   - Fix the immediate issue
   - Update the execution script if needed
   - Document the learning in the directive

5. **Repository hygiene** - Never nest git repositories
   - Weekly check: `find . -name ".git" -type d` should only show `./.git`
   - Develop in `dev-sandbox/projects/` WITHOUT git init
   - Deploy creates separate sibling repos automatically

6. **Multi-agent testing** - Use specialized agents for comprehensive testing
   - Launch when implementing complex features
   - Each agent focuses on specific edge cases
   - Consolidate findings before implementing fixes

7. **Parallel agent execution** - Use Task tool with multiple agents when possible
   - If tasks are independent (no dependencies), launch in parallel
   - Send a single message with multiple Task tool calls
   - Example: Research + implementation can run in parallel
   - Example: Multiple file searches can run in parallel
   - **Always prefer parallel over sequential for independent work**

8. **Infer intelligently** - See `docs/inference-guidelines.md` for when to extend scope

9. **Autonomous agent execution** - Launch agents WITHOUT explicit user request when:
   - New product/idea mentioned → Auto-launch SOP 17 (4 market viability agents)
   - Multiple implementation approaches → Auto-launch SOP 9 (architecture exploration)
   - Complex feature done + manual test passed → Auto-launch SOP 2 (multi-agent testing)
   - 4+ independent components to build → Auto-launch SOP 10 (parallel development)
   - Open-ended codebase questions → Auto-launch Explore agents
   - **New code written → BLOCK commit until testing complete** (see #9a below)
   - See: `docs/autonomous-agent-decision-tree.md` for full decision matrix

9a. **Pre-commit testing gate** - BEFORE committing new code implementations:
   - **ALWAYS** run at minimum Scenario 1 (Manual Testing) from testing-strategy.md
   - **NEVER** commit new `.py` files without verifying they at least run
   - **CHECK** if plan includes implementation phases → testing phases MUST follow
   - When creating plans with code implementation, automatically add testing phases
   - If about to commit and new code hasn't been tested: STOP and ask user
   - See: `docs/testing-strategy.md` for complete testing pipeline
   - Incident that created this rule: `docs/incidents/2026-02-08-untested-code-committed.md`

10. **Track deferred work** - Use DOCKET.md for items with future trigger conditions
   - Add items with clear trigger conditions (metrics, dates, dependencies)
   - Check docket when relevant metrics change
   - Move completed items to "Completed" section
   - See: `projects/social-media-automation/DOCKET.md`

11. **Living documents & self-annealing** - This system improves itself through use:

   **Core Principle**: Workflows, SOPs, and project structures emerge FROM doing work, not upfront planning.
   - Build workflows WHILE completing tasks (not before)
   - Create SOPs when patterns repeat 2+ times (not theoretically)
   - Document learnings immediately (not at end of project)
   - Create project structures on the fly as needs become clear
   - The 17+ SOPs in this file all came from real work, then got documented
   - **If you're doing something new, do it first, then document what worked**

   **Self-Annealing Triggers** (update CLAUDE.md when):
   - New communication pattern emerges → add to Communication Patterns table
   - New autonomous agent trigger identified → add to Operating Principles #9
   - Repeated manual action should be automated → create workflow or SOP
   - Error occurs that could be prevented → document fix in relevant SOP
   - User asks for something 2+ times the same way → codify as pattern
   - New project type encountered → create project-specific workflows on the fly
   - New tool/integration discovered → add to relevant project's workflows/

   **Living (update throughout sessions):**
   - `CLAUDE.md` - Communication patterns, operating principles, autonomous triggers
   - `docs/session-history.md` - Add learnings as they happen
   - `docs/prompting-guide.md` - Add new phrase patterns when discovered
   - `docs/autonomous-agent-decision-tree.md` - New agent launch conditions
   - `projects/social-media-automation/DOCKET.md` - Deferred work with triggers

   **Stable References (update only when system changes):**
   - `docs/inference-guidelines.md` - Framework/ruleset
   - `docs/repository-management.md` - Repository structure rules
   - `docs/REPO-QUICK-REFERENCE.md` - Quick repo checks
   - `docs/versioned-deployment.md` - Version control SOP
   - `docs/deployment.md` - Deployment pipeline architecture
   - `[project]/workflows/` - Task procedures
   - `[project]/USER_PROMPTS.md` - User guidance templates
   - `[project]/CHANGELOG.md` - Version history (update at deploy time)

12. **Document Large Efforts Immediately** - Use SOP-25 decision tree to prevent repeating work
   - One-time setups (Stripe, OAuth, DNS, webhooks) → Create setup guide DURING work
   - Strategic decisions (pricing, positioning, niche choice) → Create decision record with rationale
   - Repeatable processes (campaign execution, testing) → Create SOP or workflow
   - Architecture choices (tech stack, integrations) → Create Architecture Decision Record
   - **Rule: If it took >30 minutes, document it BEFORE moving on**
   - **Document DURING work, not AFTER** - you'll forget critical details
   - See: `docs/SOP-25-DOCUMENTATION-DECISION-FRAMEWORK.md` for decision tree

13. **Research before retrying (Rule of Three)** - If same approach fails 3 times, STOP and research
   - Get exact error message and understand what it means
   - Check official docs → GitHub issues → web search (in that order)
   - Understand root cause before designing solution
   - Know environment constraints (headless server, permissions, etc.)
   - See: `docs/TROUBLESHOOTING-METHODOLOGY.md` for full methodology

## Inference Quick Reference

| Risk | Example | Action |
|------|---------|--------|
| Very Low | Theme consistency on remaining slides | Just do it |
| Low | Extend pattern to similar elements | Do it, mention in summary |
| Medium | Changes that could override user edits | Ask first |
| High | Structural changes (delete, reorder) | Always ask |

**Key question:** Would NOT doing this create obvious inconsistency? → If yes, just do it.

## Session Start Checklist

1. ✅ Read this file (automatic)
2. Check context - which project are we working on?
3. Check `docs/session-history.md` if continuing previous work
4. Check `[project]/workflows/` for existing procedures

## Where to Put Things

| What | Where | Git? |
|------|-------|------|
| **Core methods & patterns** | `CLAUDE.md` (this file) | ✅ dev-sandbox |
| **Architecture decisions** | `docs/architecture-guide.md` | ✅ dev-sandbox |
| **Detailed reference docs** | `docs/` | ✅ dev-sandbox |
| **Capability SOPs** | `directives/` | ✅ dev-sandbox |
| **Task procedures** | `[project]/workflows/` | ✅ dev-sandbox |
| **Session learnings** | `docs/session-history.md` | ✅ dev-sandbox |
| **Deployment config** | `deploy_to_skills.py` | ✅ dev-sandbox |
| **Shared utilities (2+ projects)** | `execution/` | ✅ dev-sandbox |
| **Multi-tenant projects (2+ companies)** | `projects/shared/[name]/` | ✅ dev-sandbox |
| **Company-specific code** | `projects/[company]/[project]/src/` | ✅ dev-sandbox (NO separate git!) |
| **Company websites (production)** | `projects/[company]/website/` | ✅ Git submodule (separate repo) |
| **Project development** | `projects/[company]/[project]/` | ✅ dev-sandbox (NO separate git!) |
| **Client demo outputs** | `projects/[company]/demos/client-[name]/` | ✅ Optional (check sensitivity) |
| **Reference examples** | `projects/[company]/samples/` | ✅ dev-sandbox |
| **Deployed skills** | `/Users/williammarceaujr./[name]-prod/` | ✅ Separate repo |
| **Temporary/test files** | `.tmp/` | ❌ NOT tracked (ephemeral workspace) |

**Critical - Hybrid Architecture**:
- Company-centric: All company assets in `projects/[company]/`
- Websites: Git submodules (production repos for hosting)
- Projects: Regular folders (tracked in dev-sandbox)
- Shared tools: `projects/shared/` for multi-tenant (2+ companies)
- See `docs/FOLDER-STRUCTURE-GUIDE.md` for decision tree
- See `docs/HYBRID-ARCHITECTURE-QUICK-REF.md` for workflows

**Temporary files policy**: The `.tmp/` directory is for ephemeral work only:
- Testing and experimentation files
- Temporary outputs that don't need long-term storage
- Files that serve a single-use purpose
- **Auto-cleanup**: Delete files after their intended purpose to prevent clutter
- **Not tracked**: `.tmp/` is in `.gitignore` and should never be committed

## Home Directory Organization (Hybrid Architecture)

**Hybrid approach**: Company-centric folders in dev-sandbox + separate repos for deployed assets

| Directory | Purpose | Examples | Git Repos? |
|-----------|---------|----------|------------|
| **dev-sandbox/** | Active development workspace | `projects/marceau-solutions/`, `projects/shared/` | ✅ ONE repo (parent tracks all except websites) |
| **dev-sandbox/projects/[company]/website/** | Website submodules (WITHIN dev-sandbox) | marceausolutions.com, swflorida-comfort-hvac | ✅ Git submodules → separate production repos |
| **~/production/[name]-prod/** | Deployed Skills (for dev-sandbox Claude) | `lead-scraper-prod/`, `interview-prep-prod/` | ✅ Separate repos (SOP 3) |
| **~/ai-assistants/[name]/** | Deployed AI Assistants (standalone/sellable) | `upwork-proposal-generator/`, `website-builder/` | ✅ Separate repos each (SOP 31) |
| **~/upwork-projects/** | Client freelance work (SEPARATE workspace) | `clients/client-a/`, `clients/client-b/` | ✅ Per-client repos (isolated from personal work) |
| **~/website-projects/** | Client website builds (SEPARATE workspace) | `clients/acme-corp/`, `clients/local-gym/` | ✅ Per-client repos (clean handoffs) |
| **~/marceausolutions.com/** | Website production repos (OUTSIDE dev-sandbox) | Cloned for direct editing | ✅ Same repos as submodules |

**Deployment Targets**:
| What | Deploy To | SOP | Fresh Claude? |
|------|-----------|-----|---------------|
| Skills (used by dev-sandbox Claude) | `~/production/[name]-prod/` | SOP 3 | ❌ No |
| AI Assistants (standalone/sellable) | `~/ai-assistants/[name]/` | SOP 31 | ✅ Yes |
| MCP Packages | PyPI + MCP Registry | SOPs 11-14 | ✅ Yes |

**Navigation Tips**:
```bash
# Jump to active development (personal projects)
cd ~/dev-sandbox

# Jump to AI assistants (standalone tools)
cd ~/ai-assistants

# Jump to Upwork client work (separate workspace)
cd ~/upwork-projects

# Jump to website client builds (separate workspace)
cd ~/website-projects

# Check deployed skills (for dev-sandbox Claude)
ls ~/production

# Work on company website
cd ~/websites/marceausolutions.com
```

**Maintenance**:
- **Weekly**: Verify `dev-sandbox/` has no nested repos (SOP 4)
- **Monthly**: Review `archived/` for items that can be deleted
- **As needed**: Deploy AI assistants with SOP 31, Skills with SOP 3

**Reorganization**: Last updated 2026-02-08 (added ~/ai-assistants/ for standalone AI tools per SOP 31)

## Credentials & API Keys

**All credentials are stored in `/Users/williammarceaujr./dev-sandbox/.env`**

This is the single source of truth for all API keys, tokens, and secrets across all projects.

| Category | Environment Variables | Notes |
|----------|----------------------|-------|
| **Google OAuth** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID` | For Gmail, Calendar, Sheets, Drive APIs |
| **Google Sheets** | `GOOGLE_SHEETS_SPREADSHEET_ID` | Form submissions storage |
| **Gmail/SMTP** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Email sending |
| **Amazon SP-API** | `AMAZON_REFRESH_TOKEN`, `AMAZON_LWA_APP_ID`, `AMAZON_LWA_CLIENT_SECRET`, `AMAZON_AWS_*` | Seller Central access |
| **Twilio SMS** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | SMS campaigns (+1 855 239 9364) |
| **ClickUp CRM** | `CLICKUP_API_TOKEN`, `CLICKUP_WORKSPACE_ID`, `CLICKUP_LIST_ID` | Lead management |
| **Lead Scraping** | `GOOGLE_PLACES_API_KEY`, `YELP_API_KEY`, `APOLLO_API_KEY` | Business discovery |
| **Video/Image AI** | `SHOTSTACK_API_KEY`, `XAI_API_KEY`, `CREATOMATE_API_KEY` | Content generation |
| **Social Media** | `X_API_KEY`, `X_ACCESS_TOKEN`, `YOUTUBE_*`, `TIKTOK_*` | Platform integrations |
| **PyPI Publishing** | `PYPI_TOKEN` | MCP package publishing |
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude API access |

**Google OAuth Setup** (for Gmail/Calendar/Sheets):

Scripts that need Google API access require a `credentials.json` file generated from the `.env` variables:

```bash
# Generate credentials.json from .env (one-time setup)
cd /Users/williammarceaujr./dev-sandbox
python -c "
import os, json
from dotenv import load_dotenv
load_dotenv()
creds = {
    'installed': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'project_id': os.getenv('GOOGLE_PROJECT_ID'),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'redirect_uris': ['http://localhost']
    }
}
with open('credentials.json', 'w') as f:
    json.dump(creds, f, indent=2)
print('Created credentials.json')
"

# Then run the script once to generate token.json (browser auth flow)
cd projects/shared/personal-assistant
python -m src.digest_aggregator --hours 1
```

**Important**:
- `.env` is in `.gitignore` - never commit credentials
- `credentials.json` and `token.json` are also gitignored
- When setting up a new machine, copy `.env` from secure backup
- Each project reads from the root `.env` via `python-dotenv`

---

**Model:** Use Opus-4.5 for all development work.

**Principle:** Be pragmatic. Be reliable. Self-anneal.

---

## Standard Operating Procedures (SOPs)

### SOP 0: Project Kickoff & App Type Classification

**When**: BEFORE starting any new project (runs before SOP 1 and SOP 9)

**Purpose**: Ensure proper app type selection, cost analysis, and template decisions are made upfront.

**Agent**: Claude Code (primary, interactive). Clawdbot for complexity 0-4 projects only. Ralph: N/A.

**Steps**:
1. **Complete kickoff questionnaire**: Copy `templates/project-kickoff-questionnaire.md` to project folder
   - Answer all 19 questions
   - Part 1: Business/Purpose (Q1-5)
   - Part 2: Technical Requirements (Q6-10)
   - Part 3: App Type Decision (Q11-13)
   - Part 4: Resource Assessment (Q14-16)
   - Part 5: Template Decision (Q17-19)

2. **Determine MCP Aggregator alignment**:
   - Use `docs/app-type-decision-guide.md` decision tree
   - If YES → Select MCP connectivity type (HTTP, EMAIL, OAUTH, WEBHOOK, GRAPHQL, ASYNC)
   - If NO → Select standalone app type (CLI, Skill, Web API, Full-Stack, Desktop, Hybrid)

3. **Complete cost-benefit analysis**:
   - Use templates from `docs/cost-benefit-templates.md`
   - Calculate development cost
   - Calculate monthly operational cost
   - Project revenue/value
   - Determine break-even timeline

4. **Decide template vs clean slate**:
   - Low innovation → Use full template
   - Medium innovation → Adapt template
   - High innovation → Clean slate

5. **Document decision**:
   - Record in `KICKOFF.md` in project folder
   - Include rationale for app type choice
   - Include cost-benefit summary
   - Get approval before proceeding

**Decision Output**:
- App Type selected
- Connectivity type (if MCP)
- Template decision
- Go/No-Go decision
- Next step (SOP 1 or SOP 9)

**Success Criteria**:
- [ ] Kickoff questionnaire completed (19 questions answered)
- [ ] App type selected with rationale documented
- [ ] Cost-benefit analysis shows positive ROI or strategic value
- [ ] KICKOFF.md created in project folder
- [ ] Go/No-Go decision made and documented

**References**: `docs/app-type-decision-guide.md`, `docs/cost-benefit-templates.md`, `templates/project-kickoff-questionnaire.md`

---

### SOP 1: New Project Initialization

**When**: Starting a new AI assistant or automation project (AFTER completing SOP 0)

**Purpose**: Create standardized project structure with proper folder placement, version control, and documentation scaffolding.

**Agent**: Claude Code (primary). Clawdbot for complexity 0-6. Ralph for complexity 7-10 via PRD.

**Prerequisites**:
- ✅ SOP 0 complete (KICKOFF.md exists with Go decision)
- ✅ App type determined (MCP, CLI, Web, etc.)
- ✅ Company/shared placement decided

**Steps**:
1. **Determine location** using folder structure decision tree:
   - **Company-specific** → `projects/[company-name]/[project-name]/`
   - **Multi-tenant (2+ companies)** → `projects/shared/[project-name]/`
   - See: `docs/FOLDER-STRUCTURE-GUIDE.md` for decision tree

2. **Use automated scripts**:
   ```bash
   # For company-specific project
   ./scripts/add-company-project.sh company-name "project-name" [type]

   # For shared/multi-tenant project
   ./scripts/add-company-project.sh shared "project-name" [type]
   ```

   **Project types** (3rd argument):
   - `tool` (default) - Automation tool or internal utility
   - `product` - Customer-facing product/service
   - `service` - Backend service or API
   - `workflow` - Documented procedure or process
   - `mcp` - Model Context Protocol server (for PyPI/MCP Registry publishing)

3. **Create directive (if needed)**: `directives/[project-name].md`
   - Define capabilities and SOPs
   - Document edge cases and error handling
   - Include tool usage patterns

4. **Create project structure**:
   - **DO NOT** run `git init` inside folder
   - Structure (same for company-specific or shared):
     ```
     projects/[location]/[project-name]/
     ├── src/              # Python scripts
     ├── workflows/        # Task procedures (markdown)
     ├── VERSION           # e.g., "1.0.0-dev"
     ├── CHANGELOG.md      # Version history
     ├── SKILL.md          # Skill definition (if deploying)
     └── README.md         # Project documentation
     ```

5. **Develop iteratively**:
   - Write code in `src/`
   - Use shared utilities from `execution/` (if needed)
   - Extract to `execution/` only when 3+ projects use same code
   - Document workflows as you complete tasks
   - Update directive with learnings

6. **Commit to dev-sandbox**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   git add projects/[location]/[project-name]/
   git commit -m "feat([company]): Initial [project-name] structure"
   git push origin main
   ```

7. **Deploy when ready**:
   ```bash
   python deploy_to_skills.py --project [project-name] --version 1.0.0
   ```

**Success Criteria**:
- [ ] Project folder created in correct location (company-specific or shared)
- [ ] Standard structure present: src/, workflows/, VERSION, CHANGELOG.md, README.md
- [ ] No nested git repository (`find . -name ".git"` shows only parent)
- [ ] Initial commit pushed to dev-sandbox
- [ ] Directive created (if project has SOPs)

**References**:
- `docs/FOLDER-STRUCTURE-GUIDE.md` - Where to put new code
- `docs/HYBRID-ARCHITECTURE-QUICK-REF.md` - Quick reference
- `scripts/add-company-project.sh` - Automated project creation
- `docs/deployment.md` - Deployment pipeline

---

### SOP 2: Multi-Agent Testing

**When**: After manual testing complete AND implementing complex features with multiple edge cases

**Agent**: Claude Code (orchestrate agents). Ralph (generate test suites). Clawdbot: N/A.

**Complete Testing Guide**: See `docs/testing-strategy.md` for full pipeline

**This SOP is Scenario 2** in the testing pipeline:
```
Manual Testing → Multi-Agent Testing → Pre-Deployment → Deploy
(Scenario 1)     (Scenario 2 - YOU)    (Scenario 3)
```

**CRITICAL PREREQUISITES** (verify ALL before creating test plan):
1. ✅ **Manual testing complete** - Scenario 1 from testing-strategy.md passed
2. ✅ **Core implementation stable** - All main scripts working in `src/`
3. ✅ **Basic functionality verified** - Tool works for simple happy-path cases
4. ✅ **Environment dependencies resolved** - All libraries installed and accessible
5. ✅ **Workflows documented** - At least 1-2 workflows tested manually

**DO NOT start multi-agent testing if**:
- Manual testing (Scenario 1) hasn't been completed
- Implementation is incomplete
- Scripts haven't been manually tested first
- Environment issues exist (library paths, dependencies, etc.)
- You haven't tested it yourself first

**Steps**:
1. **Reference working example first**: `email-analyzer/testing/`
   - Use as template for directory structure
   - Copy AGENT-PROMPTS.txt format
   - Use **absolute paths** in prompts (not relative)
   - Include clear "HOW TO RUN" sections with exact commands

2. **Create test infrastructure**:
   - `[project]/testing/TEST-PLAN.md` - Define test scenarios (3-4 per agent)
   - `[project]/testing/AGENT-PROMPTS.txt` - Copy-paste ready prompts
   - `[project]/testing/agent1/` through `agent4/` - Empty workspace directories
   - `[project]/testing/consolidated-results/` - Results folder
   - `[project]/testing/START-HERE.md` - Quick launch guide

3. **Set up workspace structure**:
   ```
   projects/[project]/testing/
   ├── TEST-PLAN.md
   ├── AGENT-PROMPTS.txt
   ├── START-HERE.md
   ├── agent1/              ← Absolute paths in prompts
   ├── agent2/
   ├── agent3/
   ├── agent4/
   └── consolidated-results/
   ```

4. **Write agent prompts with**:
   - **Absolute paths**: `/Users/williammarceaujr./dev-sandbox/projects/[project]/testing/agent1/`
   - **Exact commands**: Full paths to wrapper scripts or executables
   - **Clear examples**: Show exact command with expected output
   - **Workspace isolation**: "CRITICAL: I will ONLY work in my workspace"

5. **Launch agents** (in parallel):
   - Open separate Claude instances
   - Paste agent-specific prompts
   - Let agents work independently

6. **Consolidate findings**:
   - Wait for all agents to complete
   - Create `[project]/testing/consolidated-results/CONSOLIDATED-FINDINGS.md`
   - Categorize: Critical, Important, Nice-to-Have
   - Prioritize fixes

7. **Implement fixes**:
   - Address critical issues first
   - Update workflows with solutions
   - Deploy new version
   - Update CHANGELOG

**Troubleshooting Template**: If agents fail, create `TESTING-ISSUES-RESOLVED.md`:
- Document root causes
- List all fixes applied
- Verify with test runs
- Reference: `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`

**Successful Example**: `email-analyzer/testing/` - 4 agents found 6 critical + 6 important issues in 225 minutes

**Failed Example (lessons learned)**: `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`
- Used relative paths → agents confused about workspace
- Missing library path wrapper → agents crashed on conversion
- Fixed with absolute paths + wrapper script

**References**: `email-analyzer/testing/TEST-PLAN.md`, `md-to-pdf/testing/TESTING-ISSUES-RESOLVED.md`

---

### SOP 3: Version Control & Deployment (Skills)

**When**: Deploying a Skill to production for dev-sandbox Claude usage (AFTER testing complete)

**Agent**: Claude Code (primary, REQUIRED for PyPI/MCP). Clawdbot (git operations only). Ralph: N/A.

**This SOP is for Skills** (used by dev-sandbox Claude). For standalone AI Assistants (fresh Claude or sellable), see **SOP 31**.

| Deployment Type | Target | SOP | Used By |
|-----------------|--------|-----|---------|
| **Skills** | `~/production/[name]-prod/` | SOP 3 (this) | Dev-sandbox Claude |
| **AI Assistants** | `~/ai-assistants/[name]/` | SOP 31 | Fresh Claude / Buyers |
| **Both** | Both locations | SOP 3 + SOP 31 | Both |

**CRITICAL PREREQUISITES** (verify BEFORE deploying):
1. ✅ **Manual testing complete** - Scenario 1 from testing-strategy.md
2. ✅ **Multi-agent testing complete** (if applicable) - Scenario 2
3. ✅ **Pre-deployment verification passed** - Scenario 3 from testing-strategy.md
4. ✅ **All critical issues resolved**
5. ✅ **Documentation updated**

**Complete Testing Guide**: See `docs/testing-strategy.md`

**Steps**:
1. **Develop and test in dev-sandbox** (version X.Y.Z-dev in VERSION file)
   - Make changes
   - Test thoroughly (see testing-strategy.md)
   - Fix all critical issues
   - Update workflows

2. **Update version files**:
   - `VERSION`: Change from `X.Y.Z-dev` to `X.Y.Z`
   - `CHANGELOG.md`: Document all changes under `## [X.Y.Z] - YYYY-MM-DD`
   - Include: Added, Changed, Fixed, Deprecated sections

3. **Deploy with version**:
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```
   - Creates `~/production/[name]-prod/` with separate git repo
   - Copies necessary files
   - Commits and tags version

4. **Bump to next dev version**:
   - `VERSION`: Update to `X.Y+1.0-dev` (or `X+1.0.0-dev` for major)
   - Commit to dev-sandbox

5. **Verify deployment**:
   ```bash
   python deploy_to_skills.py --status [name]
   # Should show: dev-sandbox (X.Y+1.0-dev) vs prod (X.Y.Z)
   ```

**Version strategy**:
- **Major (X.0.0)**: Breaking changes, major features
- **Minor (x.Y.0)**: New features, backwards compatible
- **Patch (x.y.Z)**: Bug fixes only

**Success Criteria**:
- [ ] Production folder created at `~/production/[name]-prod/`
- [ ] VERSION file updated (no -dev suffix)
- [ ] CHANGELOG.md has entry for this version
- [ ] `deploy_to_skills.py --status` shows matching versions
- [ ] Dev-sandbox bumped to next -dev version
- [ ] Post-deployment verification passed (Scenario 4)

**References**: `docs/versioned-deployment.md`

---

### SOP 4: Repository Cleanup & Verification

**When**: Weekly maintenance, or when adding new projects

**Purpose**: Maintain clean repository structure with no nested git repos, ensuring all production code is properly organized.

**Agent**: Any agent (Claude Code for complex fixes, Clawdbot for checks, Ralph: N/A).

**Steps**:
1. **Check for nested repos**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   find . -name ".git" -type d
   # Expected: Only ./.git
   ```

2. **If nested repos found**:
   - Move to appropriate category: `mv dev-sandbox/[nested-repo] ~/[category]/[nested-repo]`
   - Categories: production/, websites/, active-projects/, legacy/, archived/
   - Verify: Re-run find command
   - Commit change: `git add -A && git commit -m "fix: Move nested repo to [category]"`

3. **Verify git status**:
   ```bash
   git status
   # Should show clean working tree or expected changes
   # Should NOT show submodule warnings
   ```

4. **Check deployment targets**:
   ```bash
   python deploy_to_skills.py --list
   # Verify all prod repos are outside dev-sandbox
   ```

**If issues persist**: See `docs/repository-management.md` Section: "Common Mistakes and Fixes"

**Success Criteria**:
- [ ] `find . -name ".git" -type d` shows only `./.git`
- [ ] `git status` shows no submodule warnings
- [ ] All production repos outside dev-sandbox verified

**References**: `docs/repository-management.md`, `docs/REPO-QUICK-REFERENCE.md`

---

### SOP 5: Session Documentation

**When**: At end of each significant session or when major learnings occur

**Purpose**: Capture session learnings, patterns, and progress to enable continuity across sessions and self-annealing system improvement.

**Agent**: All agents document their own work. Claude Code updates CLAUDE.md. Clawdbot/Ralph update session-history.md.

**Intermittent Save Points**:

Save progress mid-session when:
- Completing a major milestone (e.g., all repos created, PR submitted)
- Before starting a risky operation (destructive commands, major refactors)
- At natural breakpoints in multi-step tasks
- Every 30-60 minutes of intensive work
- After discovering something that took effort to figure out

**Quick Save Actions:**
1. Update relevant checklist/tracking doc (mark items complete)
2. Commit changes to dev-sandbox if files were modified
3. Note critical learnings in session-history.md (brief bullet points)

**Full Save** (end of session): Follow Steps 1-4 below.

**Steps**:
1. **Update session-history.md**:
   ```markdown
   ## YYYY-MM-DD: [Session Title]

   **Context:** [What you were working on]

   **Accomplished:**
   - [Key achievement 1]
   - [Key achievement 2]

   **Key Learnings:**
   1. [Learning with explanation]
   2. [Pattern discovered]

   **New Communication Patterns:**
   - "[User phrase]" → [What Claude does]

   **Files Created/Updated:**
   - `path/to/file.ext` - [What changed]
   ```

2. **Update prompting-guide.md** (if new phrases discovered):
   - Add to appropriate category
   - Include context and expected action

3. **Update CLAUDE.md Communication Patterns** (if recurring pattern):
   - Add row to table
   - Keep concise (3-5 words in each column)

4. **Commit documentation**:
   ```bash
   git add docs/session-history.md docs/prompting-guide.md CLAUDE.md
   git commit -m "docs: Session learnings from YYYY-MM-DD"
   ```

**Success Criteria**:
- [ ] session-history.md updated with accomplishments and learnings
- [ ] New communication patterns added to CLAUDE.md (if discovered)
- [ ] Documentation committed to git
- [ ] Future sessions can continue without re-learning

**References**: `docs/session-history.md`, `docs/prompting-guide.md`

---

### SOP 6: Workflow Creation

**When**: Completing a repeatable task for the first time

**Purpose**: Document repeatable processes as workflows to prevent re-learning and enable consistent execution across sessions and agents.

**Agent**: Any agent. Claude Code for complex workflows. Clawdbot for simple 3-5 step workflows. Ralph: N/A.

**Decision Matrix** - Score each factor 0-3:

| Factor | 0 | 1 | 2 | 3 |
|--------|---|---|---|---|
| **Recurrence** | One-time | Unlikely | Probable | Frequent |
| **Consistency** | Doesn't matter | Nice to have | Important | Critical |
| **Complexity** | Trivial (<3 steps) | Simple | Moderate | Complex (10+ steps) |
| **Onboarding** | Only I'll do this | Might help others | Would help | Essential for handoff |

**Total Score:**
- **0-3**: Skip workflow, note in session-history.md if notable
- **4-6**: Consider workflow, or create after second occurrence
- **7-9**: Create workflow during this session
- **10-12**: Create workflow immediately

**Quick Test**: If you'd feel frustrated repeating the same research/trial-and-error next time, create the workflow now.

**Parallel Workflow Creation** (Optional for complex tasks):
Launch a second Claude instance to document steps as you work:
1. Main instance: Execute the task
2. Workflow instance: Document steps in real-time
3. Benefit: Captures edge cases and troubleshooting without interrupting work

**Steps**:
1. **While working**, note the steps you're taking

2. **After completion**, create workflow file:
   - Location: `[project]/workflows/[workflow-name].md`
   - Structure:
     ```markdown
     # Workflow: [Name]

     ## Overview
     [What this workflow does]

     ## Use Cases
     - [Use case 1]
     - [Use case 2]

     ## Prerequisites
     - [What must exist before starting]

     ## Steps

     ### 1. [Step Name]
     **Objective**: [What this step achieves]
     **Actions**: [What to do]
     **Tools**: [Which tools to use]

     ## Troubleshooting
     [Common issues and solutions]

     ## Success Criteria
     - ✅ [Criterion 1]
     - ✅ [Criterion 2]
     ```

3. **Test the workflow**:
   - Have another agent (or yourself fresh) follow it
   - Note any ambiguities
   - Refine steps

4. **Reference in directive**:
   - Add to `directives/[project].md`
   - Link to workflow for detailed steps

**Example**: `email-analyzer/workflows/analyze-email-from-html.md`

**Success Criteria**:
- [ ] Workflow file created in `[project]/workflows/`
- [ ] Contains: Overview, Use Cases, Prerequisites, Steps, Troubleshooting, Success Criteria
- [ ] Another agent can follow workflow without additional context
- [ ] Referenced in project directive (if applicable)

**References**: `docs/workflow-standard.md`

---

### SOP 7: DOE Architecture Rollback

**When**: Premature deployment detected (deployed before all DOE layers complete)

**Purpose**: Safely roll back deployments that violated DOE discipline (Directive → Orchestration → Execution order), preventing broken features from reaching users while capturing learnings.

**Agent**: Claude Code (primary for code rollback and git operations). Clawdbot can identify violations. Ralph: N/A.

**Prerequisites**:
- ✅ Premature deployment identified (feature deployed without directive)
- ✅ Git access to affected repository
- ✅ Understanding of which DOE layer is missing

**DOE Violation Patterns**:

| Violation | Example | Impact |
|-----------|---------|--------|
| **No Directive** | Scripts deployed without SOPs | Users don't know how to use feature |
| **No Orchestration** | Standalone scripts, no integration | Feature works in isolation only |
| **No Execution** | Frontend with no backend | Broken UI, failed API calls |
| **Skip Testing** | Deployed without Scenario 1-3 | Bugs reach production |

**Steps**:

1. **Identify the violation**:
   ```bash
   # Check what's deployed
   ls ~/production/[project]-prod/

   # Check if directive exists
   ls directives/[project].md

   # Check if tested
   grep -r "testing" projects/[project]/
   ```

2. **Assess rollback scope**:
   - **Minor**: Missing docs only → Add docs, no code rollback
   - **Moderate**: Missing tests → Add tests, keep code
   - **Major**: Missing execution → Roll back frontend/UI
   - **Critical**: Broken production → Immediate rollback + incident doc

3. **Execute rollback** (for Major/Critical):
   ```bash
   # Option A: Remove specific files
   cd ~/production/[project]-prod
   git rm [premature-file]
   git commit -m "rollback: Remove premature [feature] - missing [layer]"
   git push

   # Option B: Revert to last good version
   git revert HEAD
   git push
   ```

4. **Create placeholder** (if user-facing):
   - Replace removed feature with "Coming Soon" page
   - Add email capture form for notifications
   - Link to existing working features

5. **Document the violation**:
   ```bash
   # Create incident doc
   cat > docs/incidents/$(date +%Y-%m-%d)-[feature]-rollback.md << 'EOF'
   # Incident: [Feature] Premature Deployment

   **Date**: $(date +%Y-%m-%d)
   **Severity**: [Minor/Moderate/Major/Critical]
   **DOE Violation**: [Missing layer]

   ## What Happened
   [Description]

   ## Impact
   [User impact]

   ## Resolution
   [Rollback steps taken]

   ## Prevention
   [What we'll do differently]
   EOF
   ```

6. **Complete the missing layer**:
   - If missing Directive → Create `directives/[project].md`
   - If missing Orchestration → Integrate with Claude/n8n
   - If missing Execution → Build and test `src/` scripts
   - If missing Testing → Complete Scenarios 1-3

7. **Re-deploy properly** (after all layers complete):
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't identify what's premature | Unclear deployment history | Check `git log`, CHANGELOG.md |
| Rollback breaks other features | Tight coupling | Isolate change, test dependencies |
| Users already using feature | Deployed too long ago | Gradual deprecation instead |

**Success Criteria**:
- [ ] Premature deployment removed from production
- [ ] Incident documented in `docs/incidents/`
- [ ] Missing DOE layer identified and planned
- [ ] No broken features visible to users
- [ ] Lesson added to session-history.md

**References**: `docs/architecture-guide.md`, `docs/testing-strategy.md`

---

### SOP 8: Client Demo & Test Output Management

**When**: Testing workflows for clients or need to preserve test outputs for review/demonstration

**Purpose**: Systematically save valuable test outputs while maintaining workspace cleanliness

**Agent**: Claude Code (primary for file management). Clawdbot can copy/move files. Ralph: N/A.

**Directory Structure**:

For **company-specific** projects:
```
projects/[company-name]/[project-name]/
├── demos/
│   ├── client-[name]/           # Client-specific demo outputs
│   │   ├── YYYY-MM-DD/          # Date-stamped test sessions
│   │   │   ├── output.pdf
│   │   │   ├── screenshot.png
│   │   │   └── notes.md         # Context about this demo
│   │   └── latest/              # Symlink to most recent
│   └── internal/                # Internal testing outputs
└── samples/                     # Reference examples for documentation
```

For **shared/multi-tenant** projects:
```
projects/shared/[project-name]/
├── demos/
│   ├── client-[name]/           # Client-specific demo outputs
│   │   ├── YYYY-MM-DD/          # Date-stamped test sessions
│   │   │   ├── output.pdf
│   │   │   ├── screenshot.png
│   │   │   └── notes.md         # Context about this demo
│   │   └── latest/              # Symlink to most recent
│   └── internal/                # Internal testing outputs
└── samples/                     # Reference examples for documentation
```

**Steps**:

1. **During Testing (in .tmp/)**:
   - Run workflow tests in `.tmp/` as normal
   - Outputs are created temporarily
   - Review outputs immediately

2. **Identify Keeper Outputs**:
   Ask yourself:
   - Does this demonstrate client capability?
   - Would I show this to a client?
   - Is this a reference example for docs?
   - Does this show an edge case or important result?

   **If YES** → Save to appropriate location
   **If NO** → Delete from `.tmp/`

3. **Save Demo Outputs**:
   ```bash
   # Create client demo directory (if doesn't exist)
   mkdir -p projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)

   # Copy valuable outputs from .tmp/
   cp .tmp/output.pdf projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)/

   # Add context notes
   echo "Demo showing [feature] - client requested [capability]" > \
     projects/[project]/demos/client-[name]/$(date +%Y-%m-%d)/notes.md

   # Update 'latest' symlink
   cd projects/[project]/demos/client-[name]/
   ln -sf $(date +%Y-%m-%d) latest
   ```

4. **Save Reference Examples**:
   ```bash
   # For documentation examples or edge cases
   mkdir -p projects/[project]/samples/
   cp .tmp/example.pdf projects/[project]/samples/example-complex-table.pdf
   ```

5. **Clean Up .tmp/**:
   ```bash
   # After saving what you need, clean temporary files
   rm .tmp/output.pdf .tmp/test-*.pdf

   # Or clean entire .tmp/ directory
   rm -rf .tmp/*
   ```

6. **Review Before Client Meeting**:
   ```bash
   # Check latest demo outputs
   ls -la projects/[project]/demos/client-[name]/latest/

   # Open for review
   open projects/[project]/demos/client-[name]/latest/output.pdf
   ```

7. **Commit Demo Outputs** (optional, based on sensitivity):
   ```bash
   # Commit if outputs don't contain sensitive data
   git add projects/[project]/demos/
   git commit -m "demo: Add [client-name] demo outputs for [date]"

   # OR add to .gitignore if sensitive
   echo "projects/[project]/demos/" >> .gitignore
   ```

**Best Practices**:

- **Date-stamp sessions**: Use `YYYY-MM-DD` format for chronological sorting
- **Add context notes**: Brief `notes.md` explaining what the output demonstrates
- **Use 'latest' symlink**: Easy access to most recent demo without remembering dates
- **Client folders**: Separate outputs by client for easy organization
- **Sensitive data**: Add `demos/` to `.gitignore` if outputs contain client data
- **Regular cleanup**: Archive or delete old demo sessions (keep latest 2-3)

**File Naming Conventions**:
```
demos/client-acme/2026-01-12/
├── notes.md                    # "Demonstrates PowerPoint generation with custom theme"
├── output-v1.pdf               # First iteration
├── output-v2-revised.pdf       # After feedback
└── screenshot-theme.png        # Visual reference
```

**Communication Pattern**:
- "Save this for the client" → Move to `demos/client-[name]/$(date)/`
- "This is a good example" → Move to `samples/`
- "Clean up test files" → Delete everything in `.tmp/`

**Example Workflow**:
```bash
# 1. Test in .tmp/
python projects/interview-prep/src/generate_pptx.py --company "Acme Corp" --output .tmp/acme-demo.pptx

# 2. Review output
open .tmp/acme-demo.pptx

# 3. Client likes it! Save for demo
mkdir -p projects/interview-prep/demos/client-acme/2026-01-12
cp .tmp/acme-demo.pptx projects/interview-prep/demos/client-acme/2026-01-12/
echo "Acme Corp interview prep demo - custom navy theme" > \
  projects/interview-prep/demos/client-acme/2026-01-12/notes.md

# 4. Update latest symlink
cd projects/interview-prep/demos/client-acme/
ln -sf 2026-01-12 latest

# 5. Clean .tmp/
rm .tmp/acme-demo.pptx

# 6. Before client meeting
open projects/interview-prep/demos/client-acme/latest/acme-demo.pptx
```

**Success Criteria**:
- [ ] Valuable outputs saved to `demos/` or `samples/`
- [ ] Each demo has `notes.md` with context
- [ ] `latest` symlink updated for easy access
- [ ] `.tmp/` cleaned after session
- [ ] Sensitive outputs added to `.gitignore` (if applicable)

**References**: See `docs/workflow-standard.md` for documentation examples, `docs/repository-management.md` for .gitignore best practices

---

### SOP 9: Multi-Agent Architecture Exploration

**When**: Before starting implementation of a new project with multiple possible approaches

**Purpose**: Research and evaluate 3-4 different implementation strategies in parallel to choose the optimal approach BEFORE writing code

**Agent**: Claude Code (orchestrate, interactive). Clawdbot (research agents). Ralph (complex 4-agent analysis).

**Key Distinction**:
- **SOP 9 (Exploration)**: BEFORE implementation - "Which approach should we use?"
- **SOP 2 (Testing)**: AFTER implementation - "Does our implementation handle edge cases?"

**Directory Structure**:
```
projects/[project-name]/
├── exploration/                    # PRE-implementation research
│   ├── EXPLORATION-PLAN.md         # Research questions for each agent
│   ├── AGENT-PROMPTS.txt           # Copy-paste prompts for 4 agents
│   ├── agent1-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent2-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent3-[approach-name]/
│   │   └── FINDINGS.md
│   ├── agent4-[approach-name]/
│   │   └── FINDINGS.md
│   └── consolidated-results/
│       ├── COMPARISON-MATRIX.md    # Side-by-side comparison
│       └── RECOMMENDATION.md        # Chosen approach + rationale
│
├── directives/                     # Created AFTER choosing approach
└── src/                            # Implementation starts AFTER exploration
```

**Steps**:

**1. Identify Multiple Approaches**

Define 3-4 possible ways to build the project:

Example (Uber/Lyft Price Comparison):
- Approach 1: Official APIs
- Approach 2: Web Scraping
- Approach 3: Third-Party Aggregator APIs
- Approach 4: Mobile App Integration

**2. Define Evaluation Criteria** (`exploration/EXPLORATION-PLAN.md`):

```markdown
## Evaluation Criteria
- **Feasibility**: Can this actually be built?
- **Legal**: Does this violate Terms of Service or laws?
- **Cost**: What are the ongoing API/service costs?
- **Reliability**: How often will this break?
- **Maintenance**: How much ongoing work is required?
- **User Experience**: How fast/accurate are the results?
- **Scalability**: Can this handle growth?

## Scoring System
- 5 stars: Excellent
- 4 stars: Good
- 3 stars: Acceptable
- 2 stars: Poor
- 1 star: Unusable
```

**3. Create Agent Prompts** (`exploration/AGENT-PROMPTS.txt`):

```
==================================================
AGENT 1: [APPROACH NAME] RESEARCH
==================================================

I'm Agent 1 in a multi-agent EXPLORATION effort for [Project Name].

MY WORKSPACE: /Users/williammarceaujr./dev-sandbox/projects/[project]/exploration/agent1-[approach]/

MY MISSION: Research [Approach 1 Name]

RESEARCH QUESTIONS:
1. [Specific question about feasibility]
2. [Specific question about cost]
3. [Specific question about legal compliance]
4. [Specific question about reliability]
5. [Specific question about maintenance]

DELIVERABLE: Create FINDINGS.md with:
- **Summary** (feasible? yes/no)
- **Technical Details** (how it works)
- **Costs** (setup, ongoing, per-use)
- **Pros** (3-5 advantages)
- **Cons** (3-5 disadvantages)
- **Risks** (legal, technical, business)
- **Code Example** (if feasible - proof of concept)
- **RECOMMENDATION** (1-5 stars with rationale)

Use web search, documentation review, technical analysis, and proof-of-concept code.

DO NOT implement the full solution - only research and create small proof-of-concept if helpful.
```

Create similar prompts for Agents 2, 3, 4 (different approaches).

**4. Launch 4 Agents in Parallel**:
- Open 4 separate Claude instances (browser tabs or windows)
- Copy-paste each agent prompt into a separate instance
- Let agents research independently (1-2 hours each)
- Agents should use web search, read documentation, write proof-of-concept code

**5. Consolidate Findings** (`exploration/consolidated-results/COMPARISON-MATRIX.md`):

```markdown
# Approach Comparison Matrix

| Criterion | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|-----------|------------|------------|------------|------------|
| **Feasibility** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Legal** | ✅ Allowed | ❌ Violation | ✅ Allowed | ⚠️ Gray area |
| **Cost** | $0.10/call | Free | $50/mo | Free |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Maintenance** | ⭐⭐⭐⭐⭐ Low | ⭐⭐ High | ⭐⭐⭐⭐ Low | ⭐⭐⭐ Med |
| **Speed** | <1s | 3-5s | <2s | 2-3s |
| **UX** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **TOTAL SCORE** | 23/25 | 9/25 | 20/25 | 15/25 |

## Key Findings

**Approach 1** (Highest Score):
- Pros: [List from agent findings]
- Cons: [List from agent findings]
- Risk: [Main risk identified]

**Approach 2** (Lowest Score):
- Fatal Flaw: [Why this won't work]

[etc...]
```

**6. Make Recommendation** (`exploration/consolidated-results/RECOMMENDATION.md`):

```markdown
# Recommended Approach: [Chosen Approach]

## Decision
Use **[Approach Name]** for the following reasons:

**Pros**:
- ✅ [Key advantage 1]
- ✅ [Key advantage 2]
- ✅ [Key advantage 3]

**Cons**:
- ❌ [Known limitation 1]
- ❌ [Known limitation 2]

**Cost Analysis**:
- [Detailed cost breakdown]
- [ROI or sustainability plan]

**Risk Mitigation**:
- [How we'll handle main risk 1]
- [How we'll handle main risk 2]

**Alternative Considered**: [Second best approach]
- Why not chosen: [Specific reason]
- When we'd reconsider: [Conditions that would change decision]

## Next Steps
1. [First implementation task]
2. [Second implementation task]
3. Create directive: `directives/[project].md`
4. Implement using SOP 1

## Architecture Decision
**Tier 2 (Project-Specific)**:
- `projects/[name]/src/[main-script].py`
- `projects/[name]/src/[helper].py`

**Shared Utilities** (if needed):
- `execution/[utility].py` (if other projects use it)
```

**7. Proceed to Implementation** (SOP 1):
- Now implement the CHOSEN approach
- Create directive based on recommendation
- Build with confidence (research already done)
- Skip approaches that were ruled out

**When to Use**:

✅ **Use SOP 9 when**:
- Multiple valid approaches exist (3+ ways to solve it)
- Significant cost, legal, or technical unknowns
- High stakes (don't want to rebuild from scratch)
- New technology domain (unfamiliar territory)
- Examples: API vs Scraping vs Third-party, SQL vs NoSQL, Cloud provider selection

❌ **Skip SOP 9 when**:
- Obvious approach (only one way to do it)
- Low stakes (quick experiment, easy to pivot)
- Familiar domain (you know the best approach already)
- Simple project with clear requirements

**Benefits**:

1. **Avoid Costly Mistakes**: Don't spend 2 weeks implementing wrong approach
2. **Evidence-Based Decisions**: Compare approaches with data, not guessing
3. **Uncover Hidden Issues Early**: Discover ToS violations, API limits, costs BEFORE coding
4. **Parallel Research = Faster**: 4 agents in parallel (1-2 hours) vs sequential (4-8 hours)
5. **Documentation for Future**: Explains WHY you chose this approach for future reference

**Integration with Development Pipeline**:

```
0. KICKOFF (SOP 0) - ALWAYS FIRST
   └── Complete questionnaire (19 questions)
   └── App type decision, cost-benefit analysis
   └── Template vs clean slate decision

0.5 EXPLORE (SOP 9) - IF multiple approaches possible
   └── Multi-agent architecture exploration
   └── Choose best approach

1. DESIGN (Directive)
   └── Based on chosen approach

2. DEVELOP (SOP 1)
   └── Implement chosen approach

3. TEST (SOP 2)
   └── Test implementation for edge cases

4. DEPLOY (SOP 3)

5. VERIFY (Scenario 4)
```

**Example Timeline**:
```
Day 1-2: Architecture Exploration (SOP 9) - 4 agents research in parallel
Day 3: Consolidate findings, choose approach
Day 4: Create directive based on chosen approach
Day 5-9: Implement (SOP 1)
Day 10-12: Multi-Agent Testing (SOP 2) - Test implementation
Day 13-14: Deploy (SOP 3)
```

**Compared to Without SOP 9**:
```
Day 1: Pick approach (guess)
Day 2-7: Implement wrong approach
Day 8: Discover it violates ToS / too expensive / doesn't work
Day 9: Start over with different approach
Day 10-15: Implement correct approach
Day 16-18: Testing
Day 19-20: Deploy

Net savings with SOP 9: 5-7 days
```

**Success Criteria**:
- [ ] 3-4 approaches researched by parallel agents
- [ ] `exploration/COMPARISON-MATRIX.md` created with scores
- [ ] `exploration/RECOMMENDATION.md` documents chosen approach with rationale
- [ ] Chosen approach has clear implementation path
- [ ] Alternatives documented for future reference

**References**:
- See `docs/testing-strategy.md` for distinction between exploration (SOP 9) and testing (SOP 2)
- See `email-analyzer/testing/` as template for multi-agent setup (similar structure)

---

### SOP 10: Multi-Agent Parallel Development

**When**: Building a complex system with 3+ independent components that can be developed simultaneously

**Purpose**: Accelerate development by having multiple agents BUILD different components in parallel, then consolidate outputs into a unified codebase

**Agent**: Claude Code (orchestrate consolidation). Clawdbot (build components 0-6). Ralph (build components 7-10).

**Key Distinction from Other Multi-Agent SOPs**:
- **SOP 2 (Testing)**: Agents find bugs in EXISTING code (after implementation)
- **SOP 9 (Exploration)**: Agents research different APPROACHES (before implementation)
- **SOP 10 (Development)**: Agents BUILD different COMPONENTS simultaneously (during implementation)

**When to Use**:

✅ **Use SOP 10 when**:
- Large refactoring with 3+ independent files
- System has clear component boundaries
- Components don't have circular dependencies
- Each agent can work in isolation without conflicting edits
- Time savings justify the consolidation overhead

❌ **Skip SOP 10 when**:
- Components are tightly coupled (agents would edit same files)
- Less than 3 components
- Single file changes
- Unclear how to divide work

**Directory Structure**:
```
projects/[project]/
├── agent1-[component-name]/
│   ├── workspace/          ← Agent 1 builds code here
│   └── output/
│       ├── FINDINGS.md     ← What agent discovered
│       └── COMPLETION-SUMMARY.md
├── agent2-[component-name]/
│   ├── workspace/
│   └── output/
├── agent3-[component-name]/
│   ├── workspace/
│   └── output/
├── agent4-[component-name]/
│   ├── workspace/
│   └── output/
├── consolidated/           ← Final consolidated findings
└── src/                    ← Final integrated code lives here
```

**Steps**:

**Phase 1: Component Decomposition**

1. **Identify independent components** that can be built in parallel:
   - Each component should have clear boundaries
   - Minimal dependencies between components
   - Each agent can work without knowing what others are doing

   Example (MCP Aggregator):
   - Agent 1: REST API Server (`server.py`, `auth.py`, `models.py`)
   - Agent 2: Accuracy Testing (`test scripts`, `data generators`)
   - Agent 3: Platform Core (`router.py`, `registry.py`, `billing.py`, `schema.sql`)
   - Agent 4: MCP Server (`aggregator_mcp.py`, Claude Desktop integration)

2. **Define integration points** - how components will connect:
   - What imports/interfaces each component exposes
   - What other components depend on
   - Shared data structures or schemas

**Phase 2: Agent Prompt Creation**

Create `AGENT-PROMPTS.txt` with clear prompts for each agent:

```markdown
==================================================
AGENT 1: [COMPONENT NAME]
==================================================

I'm Agent 1 in a PARALLEL DEVELOPMENT effort for [Project Name].

MY WORKSPACE: /absolute/path/to/agent1-[component]/workspace/
MY OUTPUT: /absolute/path/to/agent1-[component]/output/

MY MISSION: Build [Component Name]

COMPONENTS TO BUILD:
1. [File 1] - [Description]
2. [File 2] - [Description]
3. [File 3] - [Description]

INTERFACE CONTRACT:
- I will expose: [class/function names with signatures]
- I will expect from other agents: [dependencies - may not exist yet]
- Shared schema: [if applicable]

DELIVERABLES:
1. All code files in workspace/
2. output/FINDINGS.md - Technical decisions made
3. output/COMPLETION-SUMMARY.md - What was built, what human needs to do

CRITICAL: Work independently. Do not assume other agents exist.
Build to the interface contract. Test your component in isolation.
```

**Phase 3: Launch and Monitor**

1. **Launch all agents** simultaneously:
   - Open 4 separate Claude instances
   - Copy-paste each agent's prompt
   - Let agents work independently

2. **Do not interrupt** - let agents complete autonomously

3. **Collect completion summaries** from each agent's `output/` folder

**Phase 4: Consolidation (CRITICAL)**

This is where outputs are merged into a working system:

1. **Create consolidation plan**:
   ```markdown
   # Consolidation Plan

   ## Agent Outputs to Integrate
   - Agent 1: workspace/server.py → src/api/server.py
   - Agent 2: workspace/test_*.py → testing/
   - Agent 3: workspace/*.py → src/core/
   - Agent 4: workspace/aggregator_mcp.py → mcp-server/

   ## Integration Order
   1. Foundation: Agent 3 (core) first - everything depends on it
   2. API Layer: Agent 1 (uses core)
   3. MCP Server: Agent 4 (uses core)
   4. Testing: Agent 2 (tests everything)

   ## Import Updates Required
   - Agent 4's code imports from agent3/workspace → change to src.core
   - Agent 1's code may need core imports
   ```

2. **Copy files to final locations**:
   ```bash
   # Foundation first
   cp agent3-platform-core/workspace/*.py src/core/

   # Then dependent layers
   cp agent1-rest-api/workspace/*.py src/api/
   cp mcp-server/*.py mcp-server/
   ```

3. **Update imports** in all files:
   - Change `from agent3...` to `from src.core...`
   - Fix relative imports
   - Create `__init__.py` files for modules

4. **Create module `__init__.py`** that exposes all classes:
   ```python
   from .router import Router, RoutingRequest
   from .registry import Registry, MCP, MCPCategory
   from .billing import BillingSystem, PricingModel
   ```

5. **Test integration**:
   ```bash
   python -c "from src.core import Router, Registry, BillingSystem"
   ```

6. **Document in CHANGELOG.md**:
   ```markdown
   ## [X.Y.Z-dev] - YYYY-MM-DD

   ### Added - Multi-Agent Development

   **Agent 1**: [What they built]
   **Agent 2**: [What they built]
   **Agent 3**: [What they built]
   **Agent 4**: [What they built]

   ### Integration Notes
   - Agent outputs consolidated into src/
   - Imports updated from agentN-workspace to src.module
   ```

**Phase 5: Verification**

1. **Run all tests** (if any exist)
2. **Verify imports work** from multiple entry points
3. **Test end-to-end flow** that uses all components
4. **Commit integrated result**

**Example: MCP Aggregator (2026-01-13)**

**Problem**: Platform had 51 rideshare-specific assumptions blocking non-rideshare services

**Agent Assignments**:
| Agent | Component | Output |
|-------|-----------|--------|
| Agent 1 | REST API | `server.py`, `auth.py`, `models.py`, `config.py` |
| Agent 2 | Accuracy Testing | Test scripts, data generators |
| Agent 3 | Platform Core | `router.py`, `registry.py`, `billing.py`, `schema.sql` (+ enums, scoring profiles) |
| Agent 4 | MCP Server | `aggregator_mcp.py` |

**Consolidation**:
1. Copied Agent 3 outputs to `src/core/`
2. Copied Agent 1 outputs to `src/api/`
3. Updated `aggregator_mcp.py` imports from `agent3-workspace` to `src.core`
4. Created `__init__.py` exposing all classes
5. Verified imports: `from src.core import Router, Registry, BillingSystem`

**Result**: 4 agents completed in ~2 hours what would take 8+ hours sequentially

**Common Consolidation Mistakes**:

| Mistake | Fix |
|---------|-----|
| Left agent workspace imports | Search-replace `agent[N]-workspace` → `src.module` |
| Missing `__init__.py` | Create module inits exposing key classes |
| Circular dependencies | Order consolidation by dependency graph |
| Duplicate implementations | Compare, choose best, delete other |
| Conflicting schemas | Merge manually, choosing superset |

**Success Criteria**:

- ✅ All agent code consolidated into `src/`
- ✅ No imports reference `agent[N]-workspace`
- ✅ All modules have `__init__.py`
- ✅ Integration test passes
- ✅ CHANGELOG documents all agent contributions

**References**:
- `projects/mcp-aggregator/` - Working example of SOP 10
- `projects/mcp-aggregator/CHANGELOG.md` - How to document agent contributions

---

### SOP 11: MCP Package Structure

**When**: Converting a project to MCP (Model Context Protocol) format for distribution via PyPI and the Claude MCP Registry

**Purpose**: Create a properly structured Python package that can be installed via `pip` and registered on Claude's MCP marketplace

**Agent**: Claude Code (REQUIRED - Mac keychain for publishing). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ Project has working `src/` code with MCP server implementation
- ✅ Project has been tested (SOP 2/3 complete)
- ✅ README.md exists with project description

**Directory Structure** (before → after):
```
projects/[project]/
├── src/
│   ├── server.py              # Original MCP server
│   └── module.py              # Supporting modules
├── README.md
├── VERSION
└── CHANGELOG.md

↓ After SOP 11 ↓

projects/[project]/
├── src/
│   ├── [project]_mcp/         # NEW: Package directory
│   │   ├── __init__.py        # Package init with version
│   │   ├── server.py          # MCP server (imports fixed)
│   │   └── module.py          # Supporting modules (copied)
│   └── (original files)
├── pyproject.toml             # NEW: Build configuration
├── server.json                # NEW: MCP Registry manifest
├── README.md                  # UPDATED: Add mcp-name line
├── VERSION
└── CHANGELOG.md
```

**Steps**:

**1. Create Package Directory**
```bash
mkdir -p projects/[project]/src/[project]_mcp/
```

**2. Create `__init__.py`**
```python
# projects/[project]/src/[project]_mcp/__init__.py
__version__ = "1.0.0"

from .server import mcp  # or main entry point
```

**3. Copy and Fix Server Code**
```bash
# Copy server and modules to package directory
cp projects/[project]/src/server.py projects/[project]/src/[project]_mcp/
cp projects/[project]/src/module.py projects/[project]/src/[project]_mcp/
```

Then fix imports in `server.py`:
```python
# BEFORE (absolute imports)
from module import SomeClass

# AFTER (relative imports for package)
from .module import SomeClass
```

Also remove any `sys.path` manipulation:
```python
# DELETE these lines if present
import sys
sys.path.insert(0, str(Path(__file__).parent))
```

**4. Create `pyproject.toml`**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "[project]-mcp"
version = "1.0.0"
description = "Short description under 100 characters"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
keywords = ["mcp", "claude", "ai", "[domain-keywords]"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "mcp>=1.0.0",
    # Add other dependencies from requirements.txt
]

[project.urls]
Homepage = "https://github.com/[username]/[repo]"
Repository = "https://github.com/[username]/[repo]"

[project.scripts]
[project]-mcp = "[project]_mcp.server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/[project]_mcp"]
```

**5. Create `server.json`** (MCP Registry manifest)
```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.[username]/[project]",
  "description": "Short description under 100 characters",
  "repository": {
    "url": "https://github.com/[username]/[repo]",
    "source": "github",
    "subfolder": "projects/[project]"
  },
  "version": "1.0.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "[project]-mcp",
      "version": "1.0.0",
      "transport": {
        "type": "stdio"
      },
      "runtime": "python",
      "environmentVariables": [
        {
          "name": "API_KEY",
          "description": "Description of required API key"
        }
      ]
    }
  ]
}
```

**6. Update README.md** (add ownership verification line)
```markdown
# Project Name

mcp-name: io.github.[username]/[project]

Rest of README...
```

**Important**: The `mcp-name:` line MUST be near the top of README for MCP Registry ownership verification.

**7. Verify Package Structure**
```bash
# Check all files exist
ls -la projects/[project]/src/[project]_mcp/
# Should show: __init__.py, server.py, and modules

# Test imports work
cd projects/[project]
python -c "from src.[project]_mcp import mcp"
```

**Naming Conventions**:
| Item | Format | Example |
|------|--------|---------|
| PyPI package name | `[project]-mcp` | `fitness-influencer-mcp` |
| Package directory | `[project]_mcp` | `fitness_influencer_mcp` |
| MCP Registry name | `io.github.[user]/[project]` | `io.github.wmarceau/fitness-influencer` |

**Common Mistakes**:
| Mistake | Fix |
|---------|-----|
| Using hyphens in package dir | Use underscores: `fitness_influencer_mcp` not `fitness-influencer-mcp` |
| Absolute imports in package | Change to relative: `from .module import X` |
| sys.path manipulation | Remove it - package imports handle this |
| Description > 100 chars | Shorten it for MCP Registry |
| Missing `mcp-name:` in README | Add it near top for ownership verification |

**Success Criteria**:
- ✅ Package directory created with `__init__.py`
- ✅ All imports use relative syntax (`.module`)
- ✅ `pyproject.toml` has correct package path
- ✅ `server.json` has valid schema
- ✅ README has `mcp-name:` line
- ✅ `python -c "from src.[project]_mcp import ..."` works

**Next Step**: SOP 12 (PyPI Publishing)

**References**:
- `projects/shared/md-to-pdf/` - Working example
- `projects/marceau-solutions/amazon-seller/` - Working example
- `projects/marceau-solutions/fitness-influencer-mcp/` - Working example

---

### SOP 12: PyPI Publishing

**When**: Publishing an MCP package to PyPI (AFTER SOP 11 complete)

**Purpose**: Make your MCP installable via `pip install [project]-mcp`

**Agent**: Claude Code (REQUIRED - PyPI credentials on Mac). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ SOP 11 complete (package structure created)
- ✅ PyPI account created at https://pypi.org
- ✅ PyPI API token generated

**One-Time Setup** (first time only):

1. **Create PyPI Account**: https://pypi.org/account/register/
2. **Generate API Token**: https://pypi.org/manage/account/token/
   - Scope: Entire account (for multiple projects) OR per-project
   - Save token securely (starts with `pypi-`)

3. **Install build tools**:
```bash
pip install build twine
```

**Steps**:

**1. Clean Previous Builds**
```bash
cd projects/[project]
rm -rf dist/ build/ *.egg-info
```

**2. Build Package**
```bash
python -m build
```

Expected output:
```
Successfully built [project]_mcp-1.0.0.tar.gz and [project]_mcp-1.0.0-py3-none-any.whl
```

**3. Verify Build Contents**
```bash
# Check wheel contents
unzip -l dist/*.whl

# Should show your package files:
# [project]_mcp/__init__.py
# [project]_mcp/server.py
# [project]_mcp/module.py
```

**4. Upload to PyPI**
```bash
python -m twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN_HERE
```

**5. Verify on PyPI**
- Visit: `https://pypi.org/project/[project]-mcp/`
- Should show your package with version, description, and files

**Version Bumping** (for updates):

If you need to publish an update:
1. Version in `pyproject.toml` MUST be higher than PyPI
2. Version in `server.json` should match
3. Version in `__init__.py` should match
4. PyPI does NOT allow re-uploading same version

```bash
# If 1.0.0 already exists on PyPI, bump to 1.0.1
# Update all three files, then rebuild and upload
```

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `File already exists` | Bump version (can't re-upload same version) |
| `Invalid credentials` | Check token starts with `pypi-` and use `__token__` as username |
| `Package not found in wheel` | Check `[tool.hatch.build.targets.wheel]` path in pyproject.toml |
| `ModuleNotFoundError` | Check package directory name matches pyproject.toml |

**Stored Credentials** (optional):

Create `~/.pypirc` to avoid entering token each time:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

Then upload with just:
```bash
python -m twine upload dist/*
```

**Success Criteria**:
- ✅ Build completes without errors
- ✅ Package visible at `https://pypi.org/project/[project]-mcp/`
- ✅ `pip install [project]-mcp` works in fresh environment

**Next Step**: SOP 13 (MCP Registry Publishing)

**References**:
- PyPI: https://pypi.org
- Twine docs: https://twine.readthedocs.io

---

### SOP 13: MCP Registry Publishing

**When**: Publishing to Claude's MCP Registry (AFTER SOP 12 complete - package must be on PyPI first)

**Purpose**: Make your MCP discoverable in Claude's marketplace and installable via Claude Desktop

**Agent**: Claude Code (REQUIRED - mcp-publisher uses Mac auth). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ SOP 11 complete (package structure)
- ✅ SOP 12 complete (package live on PyPI)
- ✅ GitHub account (for authentication)
- ✅ `mcp-publisher` CLI installed

**One-Time Setup** (first time only):

1. **Install mcp-publisher**:
```bash
# Requires Go installed
brew install go  # macOS

# Clone and build
git clone https://github.com/modelcontextprotocol/registry.git
cd registry
go build -o bin/mcp-publisher ./cmd/mcp-publisher
```

Or download pre-built binary from releases.

2. **Authenticate with GitHub**:
```bash
./bin/mcp-publisher login github
```

This opens a browser for GitHub device flow authentication:
- Go to: https://github.com/login/device
- Enter the code shown in terminal
- Authorize the application

**Token expires** after ~1 hour. Re-run `login github` if you see `401 Unauthorized` or `token expired`.

**Steps**:

**1. Verify Prerequisites**
```bash
# Check PyPI package exists
pip index versions [project]-mcp
# Should show: [project]-mcp (1.0.0)

# Check server.json exists and is valid
cat projects/[project]/server.json | python -m json.tool

# Check README has mcp-name line
head -5 projects/[project]/README.md
# Should show: mcp-name: io.github.[username]/[project]
```

**2. Publish to MCP Registry**
```bash
cd projects/[project]
/path/to/mcp-publisher publish --server server.json
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.[username]/[project] version 1.0.0
```

**3. Verify Publication**

The MCP should now be discoverable in Claude Desktop and the MCP Registry website.

**Updating an Existing MCP**:

1. Update code in dev-sandbox
2. Bump version in all files:
   - `pyproject.toml`
   - `server.json`
   - `src/[project]_mcp/__init__.py`
3. Rebuild: `python -m build`
4. Upload to PyPI: `twine upload dist/*`
5. Republish to Registry: `mcp-publisher publish --server server.json`

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `401 Unauthorized` / `token expired` | Re-run `mcp-publisher login github` |
| `server.json not found` | Run from project directory or use absolute path |
| `Package not found on registry` | Ensure PyPI upload completed first (SOP 12) |
| `Ownership validation failed` | Add `mcp-name: io.github.[user]/[project]` to README |
| `registryType "pip" unsupported` | Use `"pypi"` not `"pip"` in server.json |
| `Description too long` | Shorten to under 100 characters |

**server.json Validation**:

Common issues:
```json
{
  "registryType": "pypi",     // NOT "pip"
  "identifier": "[project]-mcp",  // Must match PyPI package name exactly
  "version": "1.0.0"          // Must match PyPI version
}
```

**MCP Registry Namespace**:

Your MCP name format: `io.github.[github-username]/[project-name]`

Examples:
- `io.github.wmarceau/md-to-pdf`
- `io.github.wmarceau/amazon-seller`
- `io.github.wmarceau/fitness-influencer`

**Success Criteria**:
- ✅ `mcp-publisher publish` succeeds
- ✅ MCP appears in Claude Desktop's MCP browser
- ✅ Users can install via the registry

**Complete Publishing Workflow**:

```bash
# From project directory
cd projects/[project]

# 1. Build
rm -rf dist/ && python -m build

# 2. Upload to PyPI
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN

# 3. Publish to MCP Registry
/path/to/mcp-publisher publish --server server.json
```

**References**:
- MCP Registry: https://registry.modelcontextprotocol.io
- mcp-publisher repo: https://github.com/modelcontextprotocol/registry

---

### SOP 14: MCP Update & Version Bump

**When**: Updating an MCP that's already published to PyPI and the Claude MCP Registry

**Purpose**: Push code changes to an existing MCP while maintaining version consistency across all systems

**Agent**: Claude Code (REQUIRED - publishing credentials). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ MCP already published (SOPs 11-13 completed previously)
- ✅ Code changes made and tested in dev-sandbox
- ✅ PyPI credentials available

**Version Bump Rules**:

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fixes only | Patch (x.y.Z) | 1.0.0 → 1.0.1 |
| New features (backwards compatible) | Minor (x.Y.0) | 1.0.1 → 1.1.0 |
| Breaking changes | Major (X.0.0) | 1.1.0 → 2.0.0 |

**Files That Must Be Updated** (all 3 must match):

1. `pyproject.toml` - Line: `version = "X.Y.Z"`
2. `server.json` - Line: `"version": "X.Y.Z"`
3. `src/[project]_mcp/__init__.py` - Line: `__version__ = "X.Y.Z"`

**Steps**:

**1. Make Code Changes**
```bash
# Edit files in the package directory
cd projects/[project]/src/[project]_mcp/
# Make your changes to server.py, modules, etc.
```

**2. Test Changes Locally**
```bash
# Test the MCP server works
cd projects/[project]
python -m src.[project]_mcp.server
# Or run your test suite
```

**3. Determine New Version**

Check current published version:
```bash
pip index versions [project]-mcp
# Shows: [project]-mcp (1.0.0)
```

Decide bump type based on changes:
- Bug fix → 1.0.0 → 1.0.1
- New feature → 1.0.0 → 1.1.0
- Breaking change → 1.0.0 → 2.0.0

**4. Update Version in All 3 Files**

```bash
# Update pyproject.toml
sed -i '' 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml

# Update server.json
sed -i '' 's/"version": "1.0.0"/"version": "1.0.1"/' server.json

# Update __init__.py
sed -i '' 's/__version__ = "1.0.0"/__version__ = "1.0.1"/' src/[project]_mcp/__init__.py
```

Or edit manually - just ensure all 3 match exactly.

**5. Update CHANGELOG.md**

```markdown
## [1.0.1] - 2026-01-14

### Fixed
- Description of bug fix

### Changed
- Description of changes

### Added
- Description of new features
```

**6. Clean and Rebuild**

```bash
cd projects/[project]
rm -rf dist/ build/ *.egg-info
python -m build
```

Verify build:
```
Successfully built [project]_mcp-1.0.1.tar.gz and [project]_mcp-1.0.1-py3-none-any.whl
```

**7. Upload to PyPI**

```bash
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN
```

Or if using `~/.pypirc`:
```bash
python -m twine upload dist/*
```

**8. Republish to MCP Registry**

```bash
# Re-authenticate if needed (token expires after ~1 hour)
/path/to/mcp-publisher login github

# Publish updated version
cd projects/[project]
/path/to/mcp-publisher publish --server server.json
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.[username]/[project] version 1.0.1
```

**9. Commit Changes to dev-sandbox**

```bash
cd /Users/williammarceaujr./dev-sandbox
git add projects/[project]/
git commit -m "feat([project]): Bump to v1.0.1 - [description of changes]"
git push
```

**10. Verify Update**

```bash
# Check PyPI shows new version
pip index versions [project]-mcp
# Should show: [project]-mcp (1.0.1, 1.0.0)

# Test installation
pip install --upgrade [project]-mcp
python -c "from [project]_mcp import __version__; print(__version__)"
# Should print: 1.0.1
```

**Quick Update Workflow** (copy-paste ready):

```bash
# Set variables
PROJECT="md-to-pdf"
OLD_VERSION="1.0.1"
NEW_VERSION="1.0.2"
PYPI_TOKEN="pypi-YOUR_TOKEN"

# Update versions
cd /Users/williammarceaujr./dev-sandbox/projects/$PROJECT
sed -i '' "s/version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i '' "s/\"version\": \"$OLD_VERSION\"/\"version\": \"$NEW_VERSION\"/" server.json
sed -i '' "s/__version__ = \"$OLD_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/${PROJECT//-/_}_mcp/__init__.py

# Build and publish
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN

# Update MCP Registry
/Users/williammarceaujr./dev-sandbox/projects/registry/bin/mcp-publisher publish --server server.json
```

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `File already exists` on PyPI | Version not bumped - check all 3 files |
| `Version mismatch` on Registry | server.json version must match PyPI exactly |
| `401 Unauthorized` | Re-run `mcp-publisher login github` |
| Build includes old version | Delete `dist/`, `build/`, `*.egg-info` before rebuild |

**Version Mismatch Detection**:

```bash
# Check all versions match
echo "pyproject.toml: $(grep 'version = ' pyproject.toml)"
echo "server.json: $(grep '"version"' server.json)"
echo "__init__.py: $(grep '__version__' src/*_mcp/__init__.py)"
```

All three should show the same version number.

**Success Criteria**:
- ✅ All 3 version files updated and matching
- ✅ CHANGELOG.md updated
- ✅ PyPI shows new version
- ✅ MCP Registry shows new version
- ✅ `pip install --upgrade` pulls new version
- ✅ Changes committed to dev-sandbox

**References**:
- SOP 12: PyPI Publishing (initial publish)
- SOP 13: MCP Registry Publishing (initial publish)
- Semantic Versioning: https://semver.org

---

### SOP 15: Multi-Channel Deployment

**When**: Deploying a project to multiple distribution channels simultaneously

**Purpose**: Orchestrate deployment across all configured channels (Local, GitHub, PyPI, MCP Registry, OpenRouter) in a single workflow

**Agent**: Claude Code (REQUIRED for PyPI/MCP channels). Clawdbot (GitHub only). Ralph: N/A.

**Available Channels**:

| Channel | Target Audience | Prerequisites |
|---------|----------------|---------------|
| **Local Workspace** | Internal testing | None (automatic) |
| **GitHub Repo** | Open source / team | GitHub account, repo exists |
| **PyPI Package** | Python developers | pyproject.toml, PyPI token |
| **Claude MCP Registry** | Claude users | server.json, mcp-publisher |
| **OpenRouter** | Multi-LLM users | MCP server with stdio transport |

**Channel Configuration**:

Add `deployment_channels` to project config in `deploy_to_skills.py`:

```python
"project-name": {
    # ... existing config ...
    "deployment_channels": {
        "local": True,           # Always enabled
        "github": "org/repo",    # GitHub repo or False
        "pypi": "package-mcp",   # PyPI package name or False
        "mcp_registry": "io.github.user/project",  # MCP name or False
        "openrouter": True       # Register on OpenRouter directories
    }
}
```

**Commands**:

```bash
# Deploy to all configured channels
python deploy_to_skills.py --project [name] --all-channels --version 1.0.0

# Deploy to specific channels only
python deploy_to_skills.py --project [name] --channels local,github,pypi

# Validate prerequisites without deploying
python deploy_to_skills.py --project [name] --validate-channels

# List configured channels for a project
python deploy_to_skills.py --project [name] --list-channels
```

**Deployment Sequence**:

1. **Validate** - Check all prerequisites for enabled channels
2. **Local Workspace** - Deploy to `~/{project}-prod/`
3. **GitHub** - Push to configured repository
4. **PyPI** - Build and upload package (`twine upload dist/*`)
5. **MCP Registry** - Publish to Claude marketplace (`mcp-publisher publish`)
6. **OpenRouter** - Register on PulseMCP/Glama directories
7. **Verify** - Confirm each deployment succeeded
8. **Report** - Generate deployment summary

**Prerequisites per Channel**:

| Channel | Required Files | Required Tools/Accounts |
|---------|----------------|------------------------|
| Local | VERSION, CHANGELOG | None |
| GitHub | README, LICENSE | `gh` CLI, repo access |
| PyPI | pyproject.toml, src/[pkg]_mcp/ | PyPI token |
| MCP Registry | server.json, mcp-name in README | mcp-publisher, GitHub auth |
| OpenRouter | Working MCP server (stdio) | None (manual registration) |

**Example Multi-Channel Deployment**:

```bash
# Full deployment of rideshare MCP to all channels
python deploy_to_skills.py --project mcp-aggregator-rideshare \
    --all-channels \
    --version 1.0.0

# Output:
# ✓ Local Workspace: ~/mcp-aggregator-rideshare-prod/
# ✓ GitHub: wmarceau/rideshare-comparison-mcp
# ✓ PyPI: rideshare-comparison-mcp v1.0.0
# ✓ MCP Registry: io.github.wmarceau/rideshare-comparison
# ✓ OpenRouter: Listed on PulseMCP, Glama
```

**Post-Deployment**:

1. Update `docs/MCP-CONVERSION-PLAN.md` status
2. Add to curated collection landing page
3. Document in session-history.md

**References**:
- SOP 11-14: Individual channel SOPs
- `docs/deployment.md`: Deployment pipeline documentation

---

### SOP 16: OpenRouter Registration

**When**: Registering an MCP on OpenRouter and related directories (PulseMCP, Glama) to expand reach beyond Claude marketplace

**Purpose**: Expand MCP reach to 200+ LLM providers via AI gateway integration, making your tool discoverable to a broader audience

**Agent**: Claude Code (primary, form submissions). Clawdbot (directory research). Ralph: N/A.

**Prerequisites**:
- ✅ MCP published to PyPI (SOP 12 complete)
- ✅ MCP published to Claude MCP Registry (SOP 13 complete)
- ✅ MCP server uses stdio transport (not HTTP)
- ✅ Working documentation/README with clear install instructions
- ✅ GitHub repo public (for some directories)

**Directory Comparison**:

| Directory | Review Time | Audience | Best For |
|-----------|-------------|----------|----------|
| **PulseMCP** | 1-3 days | Developers | Technical MCPs |
| **Glama** | 2-5 days | Enterprise | Production-ready MCPs |
| **MCP Market** | 3-7 days | General | Consumer-friendly MCPs |

**Steps**:

1. **Verify MCP works locally** (required before submission):
   ```bash
   # Test server runs without errors
   python -m [package]_mcp.server

   # Test with Claude Desktop (optional but recommended)
   # Add to ~/.claude.json and verify tools appear
   ```

2. **Prepare submission materials**:
   - **Short description** (under 100 chars): One-line summary
   - **Full description** (300-500 chars): What it does, who it's for
   - **Keywords** (5-10): Related terms for search
   - **Category**: Choose from directory's categories
   - **Installation command**: `pip install [package]-mcp`
   - **Example usage**: 2-3 example tool calls with expected output

3. **Register on PulseMCP** (https://pulsemcp.com):
   ```
   Submit Form Fields:
   - Package Name: [package]-mcp
   - PyPI URL: https://pypi.org/project/[package]-mcp/
   - GitHub URL: https://github.com/[username]/[repo]
   - Description: [your short description]
   - Keywords: [comma-separated keywords]
   ```
   **Expected timeline**: Review in 1-3 business days, email notification

4. **Register on Glama** (https://glama.ai/mcp/servers):
   ```
   Submit Form Fields:
   - Server Name: [Display Name]
   - Source: PyPI or GitHub
   - Identifier: [package]-mcp (or github.com/[username]/[repo])
   - Category: [Select from dropdown]
   - Description: [your full description]
   ```
   **Expected timeline**: Review in 2-5 business days, email notification

5. **Register on MCP Market** (https://mcpmarket.com):
   ```
   Submit Form Fields:
   - Title: [Human-readable name]
   - Package: [package]-mcp
   - Documentation URL: [link to README or docs site]
   - Use Cases: [2-3 example use cases]
   - Screenshots: [optional but recommended]
   ```
   **Expected timeline**: Review in 3-7 business days

6. **Update project documentation**:
   ```markdown
   ## Available On

   - [Claude MCP Registry](https://registry.modelcontextprotocol.io)
   - [PulseMCP](https://pulsemcp.com/[your-listing])
   - [Glama](https://glama.ai/mcp/servers/[your-listing])
   - [MCP Market](https://mcpmarket.com/[your-listing])
   ```

**Maintaining Listings** (after initial registration):

| Event | Action |
|-------|--------|
| New version released | Update version on each directory (if required) |
| Description changed | Submit update request on each platform |
| Deprecated | Mark as archived/deprecated on directories |
| Major feature added | Update keywords and description |

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Submission rejected | Missing PyPI package | Complete SOP 12 first |
| "Not found" error | Package name mismatch | Verify exact PyPI package name |
| No response after 7 days | Stuck in queue | Email directory support |
| Listing shows old version | Cache | Wait 24-48 hours or request refresh |

**Success Criteria**:
- [ ] MCP listed on at least 2 directories
- [ ] Installation instructions verified working
- [ ] Search for MCP name returns your listing
- [ ] README updated with directory links
- [ ] Confirmation emails received from directories

**References**:
- [Using MCP Servers with OpenRouter](https://openrouter.ai/docs/guides/guides/mcp-servers)
- [PulseMCP Directory](https://pulsemcp.com)
- [Glama MCP Servers](https://glama.ai/mcp/servers)
- [MCP Market](https://mcpmarket.com)

---

### SOP 17: Market Viability Analysis (Multi-Agent)

**When**: BEFORE investing significant development time in a new product/project idea

**Purpose**: Quickly assess market viability using parallel research agents to determine if an idea is worth pursuing, saving weeks of wasted development time on unviable products.

**Agent**: Claude Code (orchestrate 4 agents). Clawdbot (research agents). Ralph (4-agent execution via PRD).

**Key Principle**: Fail fast, fail cheap. Better to spend 2 hours researching than 2 weeks building something nobody wants.

**Prerequisites**:
- Product/service idea defined (can be vague)
- Target customer hypothesis (who would use this?)

**Directory Structure**:
```
projects/[project-name]/
├── market-analysis/
│   ├── ANALYSIS-PLAN.md           # Research questions for each agent
│   ├── AGENT-PROMPTS.txt          # Copy-paste prompts for 4 agents
│   ├── agent1-market-size/
│   │   └── FINDINGS.md
│   ├── agent2-competition/
│   │   └── FINDINGS.md
│   ├── agent3-customer-research/
│   │   └── FINDINGS.md
│   ├── agent4-monetization/
│   │   └── FINDINGS.md
│   └── consolidated/
│       ├── VIABILITY-SCORECARD.md
│       └── GO-NO-GO-DECISION.md
```

**The 4 Research Agents**:

| Agent | Focus | Key Questions |
|-------|-------|---------------|
| **Agent 1: Market Size** | TAM/SAM/SOM | How big is the market? Growing or shrinking? |
| **Agent 2: Competition** | Competitive landscape | Who else solves this? How do they monetize? |
| **Agent 3: Customer** | Buyer persona & pain | Would they pay? How much? Where do they hang out? |
| **Agent 4: Monetization** | Revenue model | B2B vs B2C? Subscription? One-time? Unit economics? |

**Steps**:

**Phase 1: Define the Research Questions**

Create `market-analysis/ANALYSIS-PLAN.md`:

```markdown
# Market Viability Analysis: [Product Name]

## Product Hypothesis
**What it is**: [1-2 sentence description]
**Who it's for**: [Target customer]
**Problem it solves**: [Pain point]
**How we'd make money**: [Initial monetization idea]

## Agent 1: Market Size Questions
1. What is the TAM (Total Addressable Market)?
2. What is the SAM (Serviceable Addressable Market)?
3. What is the realistic SOM (Serviceable Obtainable Market)?
4. Is the market growing, stable, or shrinking?
5. What are the key market trends?

## Agent 2: Competition Questions
1. Who are the direct competitors (same solution)?
2. Who are indirect competitors (different solution, same problem)?
3. What do competitors charge? What's their revenue model?
4. What's their market share / funding / size?
5. What's their main weakness we could exploit?
6. Is there a gap in the market?

## Agent 3: Customer Research Questions
1. Who exactly is the target customer (be specific)?
2. How painful is this problem (1-10)?
3. How do they currently solve it (workarounds)?
4. How much do they currently pay for alternatives?
5. Where do they congregate online (forums, social)?
6. What triggers them to search for a solution?

## Agent 4: Monetization Questions
1. What pricing model makes sense (subscription, usage, one-time)?
2. What price point would the market bear?
3. What are realistic customer acquisition costs?
4. What's the expected LTV (lifetime value)?
5. What's the break-even timeline?
6. Are there adjacent revenue opportunities (upsells)?
```

**Phase 2: Create Agent Prompts**

Create `market-analysis/AGENT-PROMPTS.txt`:

```
==================================================
AGENT 1: MARKET SIZE RESEARCH
==================================================

I'm Agent 1 in a MARKET VIABILITY analysis for [Product Name].

MY WORKSPACE: /absolute/path/to/market-analysis/agent1-market-size/
MY OUTPUT: Create FINDINGS.md

PRODUCT HYPOTHESIS:
[Paste product description here]

MY MISSION: Determine market size (TAM/SAM/SOM) and trends

RESEARCH QUESTIONS:
1. What is the TAM (Total Addressable Market)?
2. What is the SAM (Serviceable Addressable Market)?
3. What is the realistic SOM (Serviceable Obtainable Market)?
4. Is the market growing, stable, or shrinking? What's the CAGR?
5. What are key market trends affecting this space?

DELIVERABLE FORMAT (FINDINGS.md):
- **TAM**: $X billion [source]
- **SAM**: $X million [source]
- **SOM**: $X million (realistic year 1-3) [methodology]
- **Growth Rate**: X% CAGR [source]
- **Key Trends**: Bullet list with sources
- **Market Viability Score**: 1-5 stars with rationale

Use web search extensively. Cite all sources. Be skeptical of inflated market claims.
```

(Create similar prompts for Agents 2, 3, 4 with their specific questions)

**Phase 3: Launch Agents in Parallel**

1. Open 4 separate Claude instances
2. Copy-paste each agent's prompt
3. Let agents research independently (30-60 minutes each)
4. Agents should use web search, industry reports, competitor analysis

**Phase 4: Consolidate into Viability Scorecard**

After all agents complete, create `consolidated/VIABILITY-SCORECARD.md`:

```markdown
# Market Viability Scorecard: [Product Name]

## Summary Scores

| Factor | Score (1-5) | Weight | Weighted |
|--------|-------------|--------|----------|
| **Market Size** | ⭐⭐⭐⭐ | 25% | 1.0 |
| **Competition** | ⭐⭐⭐ | 25% | 0.75 |
| **Customer Pain** | ⭐⭐⭐⭐⭐ | 30% | 1.5 |
| **Monetization** | ⭐⭐⭐ | 20% | 0.6 |
| **TOTAL** | | 100% | **3.85/5** |

## Scoring Guide
- ⭐⭐⭐⭐⭐ (5): Exceptional - strong signal to proceed
- ⭐⭐⭐⭐ (4): Good - worth pursuing
- ⭐⭐⭐ (3): Acceptable - proceed with caution
- ⭐⭐ (2): Weak - significant concerns
- ⭐ (1): Poor - likely not viable

## Key Findings

### Market Size (Agent 1)
- TAM: $X
- SAM: $X
- SOM: $X (year 1-3 realistic)
- Growth: X% CAGR
- **Verdict**: [Summary]

### Competition (Agent 2)
- Direct competitors: [List]
- Indirect competitors: [List]
- Market gap: [Opportunity]
- **Verdict**: [Summary]

### Customer Pain (Agent 3)
- Target persona: [Description]
- Pain level: X/10
- Current solutions: [How they solve it now]
- Willingness to pay: [Evidence]
- **Verdict**: [Summary]

### Monetization (Agent 4)
- Recommended model: [Subscription/Usage/etc]
- Price point: $X
- CAC estimate: $X
- LTV estimate: $X
- Break-even: X months
- **Verdict**: [Summary]

## Red Flags
- [List any serious concerns discovered]

## Opportunities
- [List any positive surprises or blue ocean opportunities]
```

**Phase 5: Make Go/No-Go Decision**

Create `consolidated/GO-NO-GO-DECISION.md`:

```markdown
# Go/No-Go Decision: [Product Name]

## Overall Score: X.XX/5

## Decision: [GO / NO-GO / PIVOT]

## Rationale
[2-3 paragraphs explaining the decision]

## If GO:
- Recommended MVP scope: [What to build first]
- Target customer segment: [Who to focus on]
- Pricing strategy: [How to price]
- Go-to-market: [Where to find customers]

## If NO-GO:
- Primary dealbreaker: [What killed it]
- Could this pivot work?: [Alternative ideas]

## If PIVOT:
- Original idea: [What we started with]
- Pivoted idea: [What might work instead]
- Why pivot is more viable: [Rationale]

## Next Steps
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]
```

**Scoring Thresholds**:

| Score | Decision | Action |
|-------|----------|--------|
| **4.0-5.0** | GO | Proceed to SOP 0 (Project Kickoff) |
| **3.0-3.9** | CONDITIONAL GO | Address red flags first, then proceed |
| **2.0-2.9** | PIVOT | Research alternative approaches |
| **1.0-1.9** | NO-GO | Archive idea, move on |

**Time Investment**:
- Phase 1-2: 30 minutes (setup)
- Phase 3: 1-2 hours (parallel agent research)
- Phase 4-5: 30 minutes (consolidation)
- **Total: 2-3 hours** vs weeks of building the wrong thing

**When to Use vs Skip**:

✅ **Use SOP 17 when**:
- New product idea with uncertain market
- Entering unfamiliar market segment
- Significant development investment required (>1 week)
- B2C product (harder to validate than B2B)
- No existing customers or waitlist

❌ **Skip SOP 17 when**:
- Building for yourself (dog-fooding)
- Existing customers already requesting it
- Simple feature addition to existing product
- Internal tool (no revenue model needed)
- Quick experiment (<2 days to build)

**Integration with Development Pipeline**:

```
-1. MARKET ANALYSIS (SOP 17) - BEFORE committing to build
    └── 4-agent parallel research
    └── Viability scorecard
    └── Go/No-Go decision
    └── If NO-GO: Stop here, save weeks of work

0. KICKOFF (SOP 0) - Only if SOP 17 = GO
   └── Complete questionnaire
   └── App type decision

1. DESIGN → 2. DEVELOP → 3. TEST → 4. DEPLOY
```

**Example: Fitness Influencer AI Viability**

```
Agent 1 (Market Size):
- TAM: $21.4B creator economy
- SAM: $2.1B fitness influencer tools
- SOM: $50-100K (year 1 realistic for solopreneur)
- Growth: 15% CAGR
- Score: ⭐⭐⭐⭐ (4/5)

Agent 2 (Competition):
- Direct: Later, Buffer (social scheduling)
- Indirect: Canva, CapCut (manual tools)
- Gap: All-in-one for fitness niche
- Score: ⭐⭐⭐ (3/5) - crowded but fragmented

Agent 3 (Customer):
- Persona: 10K-100K follower fitness creators
- Pain: 8/10 (time-consuming editing)
- Current: Piecing together 5+ tools
- WTP: $20-50/month
- Score: ⭐⭐⭐⭐⭐ (5/5) - strong pain

Agent 4 (Monetization):
- Model: Freemium + Pro subscription
- Price: $29/month Pro tier
- CAC: $10-30 (content marketing)
- LTV: $200+ (6+ month retention)
- Score: ⭐⭐⭐⭐ (4/5)

TOTAL: 4.0/5 = GO
```

**References**:
- SOP 0: Project Kickoff (runs after GO decision)
- SOP 9: Architecture Exploration (technical approach)
- `docs/cost-benefit-templates.md` (financial projections)

---

### SOP 18: SMS Campaign Execution

**When**: Running SMS outreach campaigns via Twilio

**Purpose**: Execute compliant SMS campaigns with proper template approval, sending, and tracking

**Agent**: Claude Code (primary, template approval). Clawdbot (execute campaigns after setup). Ralph: N/A.

**Prerequisites**:
- ✅ Twilio account with balance (>$10)
- ✅ Phone number configured (+1 855 239 9364)
- ✅ Templates approved by William
- ✅ Lead list with valid phone numbers
- ✅ Webhook server running for replies

**Steps**:

1. **Verify prerequisites**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
   grep TWILIO .env  # All 3 vars set
   cat output/approved_templates.json | grep template_name
   ```

2. **Dry run first** (always required):
   ```bash
   python -m src.scraper sms --dry-run --limit 5 --template no_website_intro
   ```
   Verify: Messages render correctly, personalization works, under 160 chars

3. **Small batch test** (10 leads):
   ```bash
   python -m src.scraper sms --for-real --limit 10 --pain-point no_website
   ```
   Wait 24 hours, check: Delivery rate, STOP responses, carrier violations

4. **Full campaign** (only after small batch succeeds):
   ```bash
   python -m src.scraper sms --for-real --limit 100 --pain-point no_website
   ```

5. **Monitor**:
   - Twilio Console: https://console.twilio.com/us1/monitor/logs/sms
   - Webhook for replies: `python -m src.twilio_webhook serve --port 5001`

**TCPA Compliance Requirements**:
- B2B exemption for business numbers
- "This is William" in every message
- "Reply STOP to opt out" required
- No messages before 8am or after 9pm local time

**Success Criteria**:
- ✅ Delivery rate >95%
- ✅ Reply rate 2-5%
- ✅ Opt-out rate <2%
- ✅ No carrier violations

**References**: `projects/shared/lead-scraper/workflows/sms-campaign-sop.md`, `projects/shared/lead-scraper/workflows/cold-outreach-sop.md`

---

### SOP 19: Multi-Touch Follow-Up Sequence

**When**: Managing automated follow-up sequences for non-responding leads

**Purpose**: Execute the 7-touch, 60-day follow-up sequence based on Hormozi's "Still Looking" framework

**Agent**: Claude Code (setup). Clawdbot (daily processing). Ralph: N/A. Note: Consider n8n workflow replacement.

**Prerequisites**:
- ✅ SOP 18 campaign created (initial outreach complete)
- ✅ Lead list loaded with valid phone numbers
- ✅ Follow-up templates approved
- ✅ Twilio balance sufficient for sequence duration

**Sequence Architecture**:
```
Day 0:  Initial outreach (intro message)
Day 2:  Follow-up #1 (still_looking)
Day 5:  Follow-up #2 (social_proof)
Day 10: Follow-up #3 (direct_question)
Day 15: Follow-up #4 (availability)
Day 30: Follow-up #5 (breakup)
Day 60: Follow-up #6 (re_engage)
```

**Steps**:

1. **Create campaign with sequence**:
   ```bash
   python -m src.follow_up_sequence create \
       --name "Naples Gyms No Website" \
       --pain-point no_website \
       --limit 100
   ```

2. **Send initial outreach (Day 0)**:
   ```bash
   python -m src.follow_up_sequence send --campaign {campaign_id} --day 0
   ```

3. **Process due follow-ups** (run daily via cron or manually):
   ```bash
   python -m src.follow_up_sequence process-due
   ```

4. **Handle responses**:
   ```bash
   # Mark lead as responded
   python -m src.follow_up_sequence mark-responded \
       --campaign {campaign_id} \
       --phone "+1XXXXXXXXXX" \
       --outcome positive  # positive, negative, callback_scheduled, not_interested
   ```

5. **View campaign status**:
   ```bash
   python -m src.follow_up_sequence status --campaign {campaign_id}
   python -m src.follow_up_sequence report --format daily
   ```

**Exit Conditions** (lead removed from sequence):
- Lead replies (any response)
- Lead opts out (STOP)
- Delivery fails 2x consecutive
- Callback scheduled
- Day 60 completed

**Success Criteria**:
- ✅ Overall reply rate >5%
- ✅ Opt-out rate <3%
- ✅ Delivery rate >95%
- ✅ >80% reach Day 60

**References**: `projects/shared/lead-scraper/workflows/multi-touch-followup-sop.md`

---

### SOP 20: Internal Method Development

**When**: Creating internal operational frameworks, classification systems, or procedural methods

**Purpose**: Develop internal methods (estimation frameworks, qualification criteria, onboarding processes) with the same rigor as projects, but with appropriate differences

**Agent**: Claude Code (primary). Clawdbot (research phases). Ralph (complex method via PRD).

**Prerequisites**:
- ✅ Problem clearly defined (not vague)
- ✅ Used by 2+ people or applied 2+ times
- ✅ Existing ad-hoc approach to formalize

**Key Distinction from Projects**:
- **Projects** → External products/services → Deploy to PyPI/GitHub
- **Internal Methods** → Operational tools → Integrate into CLAUDE.md/SOPs

**Directory Structure**:
```
methods/[method-name]/
├── DEFINITION.md           # Problem statement, scope, success criteria
├── exploration/            # SOP 9 multi-agent research
│   ├── EXPLORATION-PLAN.md
│   ├── agent1-[focus]/
│   ├── agent2-[focus]/
│   ├── agent3-[focus]/
│   ├── agent4-[focus]/
│   └── consolidated/
├── [METHOD-OUTPUT].md      # The actual framework/matrix
├── templates/              # Supporting templates
└── VALIDATION-LOG.md       # Test cases and refinements
```

**Steps**:

1. **DEFINE** - Create `methods/[name]/DEFINITION.md`:
   - What problem does this method solve?
   - Who uses it (William, Claude, both)?
   - What does success look like?
   - What are the inputs and outputs?

2. **EXPLORE** (SOP 9) - Multi-agent research:
   - Launch 3-4 agents to research different aspects
   - Consolidate findings into recommendation

3. **DESIGN** - Create the method:
   - Classification matrix / decision tree
   - Templates / checklists
   - Automation scripts (if applicable)

4. **DOCUMENT** - Make it usable:
   - Create SOP in `workflows/`
   - Add to CLAUDE.md communication patterns
   - Update KNOWLEDGE_BASE.md

5. **VALIDATE** - Test on real scenarios:
   - Apply to 3-5 past or hypothetical cases
   - Document in `VALIDATION-LOG.md`
   - Refine based on results

6. **INTEGRATE** - No deployment, just integration:
   - Reference in relevant SOPs
   - Add communication patterns to CLAUDE.md

**Versioning**: Date-based (2026-01-15) not semantic (1.0.0)

**Examples of Internal Methods**:
- Project scoping & estimation
- Lead qualification criteria
- Client onboarding process
- Pricing strategy framework
- Quality assurance checklists
- SOP creation method (meta-method)

**Success Criteria**:
- [ ] DEFINITION.md exists with problem statement and success definition
- [ ] Method validated on 3-5 real or hypothetical cases
- [ ] VALIDATION-LOG.md documents test results
- [ ] Integrated into CLAUDE.md or relevant SOPs
- [ ] Another agent can apply method without additional context

**References**: SOP 9 (Multi-Agent Exploration), SOP 6 (Workflow Creation)

---

### SOP 21: SOP Creation Method (Meta-Method)

**When**: A recurring process is identified that needs documentation

**Purpose**: Systematically decide when and how to create new SOPs on-the-fly

**Agent**: Any agent. Claude Code for complex SOPs. Clawdbot for simple SOPs. Ralph: N/A.

**Trigger Conditions**:
- Task repeated 2+ times
- Complex multi-step process completed
- New integration/tool set up
- Process others (or future Claude sessions) will need to replicate

**Decision Tree**:
```
Is this task repeatable?
├── NO → Skip SOP, note in session-history.md if notable
└── YES → Score using SOP 6 matrix (Recurrence, Consistency, Complexity, Onboarding)
          ├── Score 0-3 → Skip or create after 2nd occurrence
          ├── Score 4-6 → Create lightweight SOP
          └── Score 7-12 → Create full SOP immediately
```

**Lightweight SOP Template** (scores 4-6):
```markdown
# SOP: [Name]

*Created: YYYY-MM-DD*

## Purpose
[One sentence: what this SOP does]

## When to Use
[Trigger conditions]

## Steps
1. [Step]
2. [Step]
3. [Step]

## Commands
\`\`\`bash
[key commands]
\`\`\`

## Verification
- [ ] [How to know it worked]
```

**Full SOP Template** (scores 7-12):
```markdown
# SOP: [Name]

*Last Updated: YYYY-MM-DD*
*Version: 1.0.0*

## Overview
[What this SOP covers]

## Prerequisites
| Requirement | Check | Expected |
|-------------|-------|----------|
| ... | ... | ... |

## Steps
### Step 1: [Name]
**Objective**: ...
**Actions**: ...
**Verification**: ✅ You should see...

[Repeat for each step]

## Troubleshooting
| Issue | Cause | Solution |
|-------|-------|----------|

## Rollback Procedures
[How to undo/recover]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Commands Reference
\`\`\`bash
[All commands used]
\`\`\`
```

**Integration**:
- Add new SOP to CLAUDE.md Quick Reference table
- Add communication pattern if relevant
- Reference in SOP 6 (Workflow Creation)

**Location for meta-method documentation**: `methods/sop-creation/`

**Success Criteria**:
- [ ] Task scored using SOP 6 matrix (Recurrence, Consistency, Complexity, Onboarding)
- [ ] Appropriate template used (Lightweight 4-6, Full 7-12)
- [ ] SOP added to CLAUDE.md Quick Reference table
- [ ] Communication pattern added (if applicable)

**References**: SOP 6 (Workflow Creation), SOP 20 (Internal Method Development)

---

### SOP 22: Campaign Analytics & Tracking

**When**: Tracking campaign performance, response rates, and optimizing outreach strategies

**Purpose**: Measure campaign effectiveness, identify winning templates, and track conversion funnels to continuously improve cold outreach ROI

**Agent**: Claude Code (primary, complex analysis). Clawdbot (quick status checks). Ralph: N/A.

**Prerequisites**:
- ✅ Campaign data exists in `output/sms_campaigns.json`
- ✅ At least one campaign completed (SOP 18)
- ✅ Lead scraper project dependencies installed

**Key Metrics Tracked**:
- Response rates by template
- Conversion funnel (Contacted → Responded → Qualified → Converted)
- Multi-touch attribution (which follow-up drives responses)
- A/B test performance with statistical significance

**Directory Structure**:
```
projects/shared/lead-scraper/
├── output/
│   ├── sms_campaigns.json       # Raw campaign data
│   ├── campaign_analytics.json  # Aggregated metrics
│   └── template_performance.json
├── src/
│   └── campaign_analytics.py    # Analytics engine
```

**Steps**:

1. **Record a response** when lead replies:
   ```bash
   python -m src.campaign_analytics response \
       --phone "+1XXXXXXXXXX" \
       --text "Yes, I'm interested" \
       --category hot_lead
   ```

   Categories: `hot_lead`, `warm_lead`, `cold_lead`, `not_interested`, `wrong_number`, `callback_requested`

2. **Update campaign metrics** after batch completes:
   ```bash
   python -m src.campaign_analytics update --campaign-id "wave_1_no_website_jan15"
   ```

3. **View performance report**:
   ```bash
   python -m src.campaign_analytics report
   ```

4. **Compare template performance**:
   ```bash
   python -m src.campaign_analytics templates
   ```

5. **View conversion funnel**:
   ```bash
   python -m src.campaign_analytics funnel
   ```

**Conversion Funnel Stages**:
```
CONTACTED (100%) → RESPONDED (5-10%) → QUALIFIED (50% of responded) → CONVERTED (20% of qualified)
```

**Statistical Significance for A/B Tests**:
- Minimum 100 contacts per variant
- 85% confidence threshold for declaring winner
- Run tests for minimum 7 days

**ClickUp Integration Strategy**:
- ClickUp = **Qualified leads only** (hot/warm)
- Don't create tasks for every cold contact
- Auto-create task when lead categorized as `hot_lead` or `callback_requested`

**Success Criteria**:
- ✅ Response rates tracked per template
- ✅ Funnel conversion rates calculated
- ✅ A/B tests reach statistical significance
- ✅ Winning templates identified

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| No campaigns found | Missing sms_campaigns.json | Run SOP 18 first to create campaign |
| Stats not updating | Cache stale | Run `campaign_analytics update` |
| Template comparison empty | No A/B data | Ensure templates tagged in campaign creation |
| Funnel shows 0% | No responses recorded | Check webhook receiving SMS replies |

**References**: `projects/shared/lead-scraper/src/campaign_analytics.py`, SOP 18 (SMS Campaign Execution)

---

### SOP 23: Cold Outreach Strategy Development

**When**: Developing new cold outreach strategies, testing messaging hypotheses, or optimizing campaign performance

**Purpose**: Systematically create, test, and optimize cold outreach strategies using A/B testing and data-driven iteration

**Agent**: Claude Code (strategy design, A/B analysis). Clawdbot (hypothesis brainstorming). Ralph (bulk template generation).

**The Hormozi Framework** (foundation for all outreach):
1. **Lead with value** - Offer something before asking
2. **Be specific** - Mention their business name, location, pain point
3. **Social proof** - Reference similar businesses helped
4. **Clear CTA** - One simple action to take
5. **Multi-touch** - 5+ touches before giving up (most respond after touch 3-5)

**Steps**:

**Phase 1: Define Target Segment**
```markdown
## Segment Definition
- **Who**: [e.g., Naples gyms without websites]
- **Pain point**: [e.g., losing customers to competitors with online presence]
- **Evidence**: [e.g., 55% of scraped gyms have no website]
- **Offer**: [e.g., free mockup website in 48 hours]
```

**Phase 2: Create Message Hypotheses**

For each segment, develop 2-3 competing message angles:

| Hypothesis | Angle | Example |
|------------|-------|---------|
| A (Control) | Direct pain | "80% of customers search online first" |
| B (Variant) | Social proof | "Just helped 3 Naples businesses" |
| C (Variant) | Scarcity | "Only taking 2 more clients this month" |

**Phase 3: Design A/B Test**
```bash
# Split leads into equal groups
python -m src.campaign_analytics ab-test create \
    --name "pain_vs_social_proof" \
    --control-template no_website_intro \
    --variant-template social_proof_intro \
    --sample-size 100
```

**Phase 4: Execute Campaign** (per SOP 18)
```bash
# Send to control group
python -m src.scraper sms --for-real --limit 50 --template no_website_intro --ab-group control

# Send to variant group
python -m src.scraper sms --for-real --limit 50 --template social_proof_intro --ab-group variant
```

**Phase 5: Analyze Results**
```bash
# After 7+ days and 100+ contacts per variant
python -m src.campaign_analytics ab-test results --name "pain_vs_social_proof"
```

Output shows:
- Response rate per variant
- Statistical significance (85% confidence threshold)
- Recommended winner

**Phase 6: Iterate**
- Winner becomes new control
- Develop new variant hypothesis
- Repeat cycle

**Template Library Structure**:
```
projects/shared/lead-scraper/
├── templates/
│   ├── sms/
│   │   ├── intro/           # Initial outreach templates
│   │   ├── followup/        # Follow-up sequence templates
│   │   └── archived/        # Losing templates (for reference)
│   └── email/
│       ├── intro/
│       └── followup/
```

**New Template Checklist**:
- [ ] Under 160 characters (SMS)
- [ ] Contains personalization ({business_name})
- [ ] Clear CTA
- [ ] "STOP to opt out" included
- [ ] Reviewed by William before sending

**Optimization Cycle**:
```
Define Segment → Create Hypotheses → A/B Test → Analyze → Scale Winner → Repeat
      ↑                                                          │
      └──────────────────────────────────────────────────────────┘
```

**Success Criteria**:
- ✅ Each segment has documented strategy
- ✅ A/B tests reach statistical significance
- ✅ Response rate improves over baseline (target: +20% per quarter)
- ✅ Losing templates archived with learnings

**References**: `projects/shared/lead-scraper/workflows/cold-outreach-strategy-sop.md`, SOP 18 (SMS Campaign Execution), SOP 22 (Campaign Analytics)

---

### SOP 24: Daily/Weekly Digest System

**When**: Reviewing business operations or setting up automated digest delivery

**Purpose**: Aggregate data from multiple sources (Gmail, SMS, Forms, Calendar, Campaigns) into unified morning digest with prioritized action items

**Agent**: Claude Code (setup, debugging). Clawdbot ("Run morning digest" command). Ralph: N/A.

**Key Files**:
```
projects/shared/personal-assistant/
├── src/
│   ├── digest_aggregator.py    # Combines all data sources
│   ├── morning_digest.py       # Generates + sends digest via SMTP
│   └── routine_scheduler.py    # Creates calendar reminders
├── workflows/
│   ├── daily-routine-sop.md    # Morning checklist (8-10:30 AM)
│   └── weekly-routine-sop.md   # Weekly/monthly tasks
└── output/digests/             # Historical digests (JSON)
```

**Commands**:

```bash
# Preview morning digest (no email sent)
cd /Users/williammarceaujr./dev-sandbox/projects/shared/personal-assistant
python -m src.morning_digest --preview

# Send digest email
python -m src.morning_digest

# Check digest data only
python -m src.digest_aggregator --hours 24

# Create calendar reminders (one-time setup)
python -m src.routine_scheduler --create-all
```

**Data Sources Aggregated**:

| Source | Data Retrieved |
|--------|----------------|
| Gmail API | Emails categorized (urgent, sponsorship, business, customer) |
| SMS Campaigns | Hot leads, callbacks, questions, opt-outs |
| Form Submissions | New inquiries with source tracking |
| Google Calendar | Today's events + upcoming week |
| Campaign Analytics | Response rates, funnel metrics |

**Digest Schedule**:

| Frequency | Tasks | Time |
|-----------|-------|------|
| Daily | Morning digest review, SMS replies, Form submissions | 8:00-10:30 AM |
| Weekly (Mon) | Campaign performance, ClickUp pipeline, Week preview | 9:00-10:30 AM |
| Bi-weekly | Revenue analytics, API costs, Inventory check | 10:30-11:30 AM |
| Monthly | Revenue report, ROI analysis, Churn, Storage fees | 1st of month |

**Setup Requirements**:

1. **Environment variables** (in `.env`):
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   DIGEST_RECIPIENT=your-email@gmail.com
   ```

2. **Google OAuth** (first time):
   - Place `credentials.json` in project root
   - Run once to generate `token.json`

**Communication Patterns**:
- "Run morning digest" → `python -m src.morning_digest --preview`
- "Send the digest" → `python -m src.morning_digest`
- "Set up calendar reminders" → `python -m src.routine_scheduler --create-all`

**Success Criteria**:
- ✅ Morning digest delivers at 8 AM with all summaries
- ✅ Action items prioritized (hot leads first)
- ✅ Calendar reminders created for all routine tasks
- ✅ Historical digests saved in `output/digests/`

**References**: `projects/shared/personal-assistant/workflows/daily-routine-sop.md`, `projects/shared/personal-assistant/workflows/weekly-routine-sop.md`

---

### SOP 26: User Statement Validation Protocol

**MANDATORY** - See: `docs/SOP-26-USER-STATEMENT-VALIDATION-PROTOCOL.md`

**Core Rule**: NEVER contradict user statements about prior work. Trust and proceed.

**Incident Report**: `docs/incidents/2026-01-27-user-statement-contradiction.md`

---

### SOP 30: n8n Workflow Management

**When**: Creating, managing, or transitioning automations to n8n

**Purpose**: Use n8n for visual workflow automation, webhooks, and scheduled tasks instead of Python scripts where appropriate.

**Agent**: Claude Code (all n8n MCP operations). Clawdbot (status checks only). Ralph (complex automation via PRD).

**Prerequisites**:
- ✅ EC2 n8n running at http://34.193.98.97:5678
- ✅ n8n MCP configured in `~/.claude.json`
- ✅ Python Bridge API running on EC2 (localhost:5010)

**⚠️ CRITICAL: EC2 INSTANCE ONLY**

| Instance | URL | Usage |
|----------|-----|-------|
| **EC2 (PRODUCTION)** | http://34.193.98.97:5678 | ✅ ALL development, testing, production |
| Local | http://localhost:5678 | ❌ DEPRECATED - do not use |

- **Never start or use the local n8n instance**
- **All workflow creation/editing happens on EC2**
- **Claude Code MCP is configured to connect to EC2** (`~/.claude.json`)
- **Weekly backup (optional)**: Export workflows from EC2 to `projects/shared/n8n-workflows/`

**When to Use n8n vs Python**:

| Use n8n | Use Python |
|---------|------------|
| Webhook handlers | Complex ML/AI logic |
| Scheduled tasks with visual debugging | Statistical analysis |
| Multi-service integrations | Lead scoring algorithms |
| Follow-up sequences (Wait nodes) | Video/image generation |
| Form → CRM → Email pipelines | Custom API clients |

**Active n8n Workflows** (on EC2):

| Workflow | ID | Webhook Path |
|----------|-----|--------------|
| SMS-Response-Handler-v2 | G14Mb6lpeFZVYGwa | `/webhook/sms-response` |
| Form-Submission-Pipeline | MmXDtZMsY9nR5Wrx | `/webhook/form-submit` |
| Daily-Operations-Digest | Hz05R5SeJGb4VNCl | *Scheduled 8 AM* |
| Follow-Up-Sequence-Engine | w8PYKJyeozM3qJQW | `/webhook/enroll-followup` |
| Hot-Lead-to-ClickUp | SzVXrbi1y433799Y | `/webhook/hot-lead-clickup` |
| Grok-Imagine-B-Roll-Generator | sYvUyTooDcHQQuKN | *Manual trigger* |

**Commands**:
```bash
# Check EC2 n8n status
curl http://34.193.98.97:5678/healthz

# List workflows via MCP
# Use mcp__n8n__list_workflows_minimal tool

# Export workflow to local backup
# Use mcp__n8n__export_workflow_to_file tool
```

**Python Scripts Replaced by n8n**:
- `twilio_webhook.py` → SMS-Response-Handler-v2
- `form_webhook.py` → Form-Submission-Pipeline
- `morning_digest.py` → Daily-Operations-Digest
- `follow_up_sequence.py` → Follow-Up-Sequence-Engine

**Communication Patterns**:
- "Check n8n status" → `curl http://34.193.98.97:5678/healthz`
- "Create n8n workflow for X" → Use n8n MCP tools (connects to EC2)
- "Migrate X to n8n" → Follow transition plan in `docs/N8N-TRANSITION-PLAN.md`
- "Backup n8n workflows" → Export to `projects/shared/n8n-workflows/`

**Success Criteria**:
- [ ] Workflow created/updated on EC2 n8n
- [ ] Workflow activated and responding to triggers
- [ ] Webhook URL documented in table above
- [ ] Backup exported to `projects/shared/n8n-workflows/`

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't connect to n8n | EC2 not running | SSH and check `docker ps` or PM2 status |
| MCP tool fails | n8n credential expired | Re-authenticate in n8n MCP settings |
| Webhook not firing | Workflow inactive | Activate workflow in n8n UI |
| Python Bridge error | Port 5010 not listening | SSH and restart `agent_bridge_api.py` |
| Workflow execution fails | Node error | Check n8n execution log, fix node config |

**References**: `docs/N8N-TRANSITION-PLAN.md`, `docs/EC2-N8N-SETUP.md`

---

### SOP 31: AI Assistant Deployment

**When**: Deploying a standalone AI assistant that fresh Claude instances (or buyers) can use without dev-sandbox context

**Purpose**: Deploy AI assistants as self-contained products with Python scripts that can be:
1. Used by fresh Claude Code instances in isolation
2. Packaged and sold to customers
3. Optionally registered as Skills for dev-sandbox Claude

**Key Distinction from SOP 3:**
- **SOP 3 (Skills)**: Deploys to `~/production/[name]-prod/` for dev-sandbox Claude use
- **SOP 31 (AI Assistants)**: Deploys to `~/ai-assistants/[name]/` for standalone/sellable use
- **Both**: A project can be deployed BOTH as a Skill AND an AI Assistant

**Deployment Location:**
```
~/ai-assistants/                         # Container folder (NOT a git repo)
├── upwork-proposal-generator/           # ✅ Separate git repo
├── website-builder/                     # ✅ Separate git repo
├── md-to-pdf/                           # ✅ Separate git repo
└── [future-assistants]/                 # Each is its own repo
```

**Standard AI Assistant Structure:**
```
~/ai-assistants/[name]/
├── CLAUDE.md           # Instructions for LLM usage (self-contained)
├── README.md           # Human documentation, GitHub readme
├── requirements.txt    # Python dependencies
├── VERSION             # Version tracking
├── CHANGELOG.md        # Version history
│
├── src/                # THE PRODUCT (Python scripts - what you sell)
│   ├── __init__.py
│   ├── main.py         # Primary entry point
│   └── utils.py        # Supporting utilities
│
├── templates/          # Data templates and user configuration
│   └── profile.json    # User-specific data (name, skills, etc.)
│
├── output/             # Generated outputs (gitignored)
│
└── workflows/          # Step-by-step procedures (optional)
```

**What Gets Sold (if selling):**
- `src/` - Python scripts (the product)
- `templates/` - Configuration templates
- `README.md` - Usage documentation
- `requirements.txt` - Dependencies

**What's For LLM Usage (not sold):**
- `CLAUDE.md` - Instructions for Claude to orchestrate the .py files

**CLAUDE.md Template for AI Assistants:**
```markdown
# [Assistant Name]

## What This Does
[One paragraph - problem it solves]

## Quick Start
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Commands
- `python src/main.py --option "value"` - [Description]
- `python src/main.py --help` - Show all options

## User Configuration
Edit `templates/profile.json` to customize:
- [Config option 1]
- [Config option 2]

## Examples
[2-3 concrete usage examples with expected output]
```

**Steps:**

1. **Develop in dev-sandbox** (as normal):
   ```bash
   dev-sandbox/projects/[company]/[project]/
   ```

2. **Test thoroughly** (SOP 2/testing-strategy.md)

3. **Create assistant structure**:
   ```bash
   mkdir -p ~/ai-assistants/[name]/{src,templates,output,workflows}
   cd ~/ai-assistants/[name]
   git init
   ```

4. **Copy product files**:
   ```bash
   cp -r dev-sandbox/projects/[company]/[name]/src/* ~/ai-assistants/[name]/src/
   cp dev-sandbox/projects/[company]/[name]/requirements.txt ~/ai-assistants/[name]/
   ```

5. **Create self-contained CLAUDE.md** (fresh Claude needs ONLY this file)

6. **Create profile template**:
   ```bash
   # templates/profile.json - user-editable configuration
   ```

7. **Add .gitignore**:
   ```
   output/
   __pycache__/
   *.pyc
   .env
   ```

8. **Commit and push**:
   ```bash
   git add .
   git commit -m "Initial AI assistant deployment"
   git remote add origin git@github.com:[user]/[name].git
   git push -u origin main
   ```

9. **(Optional) Also deploy as Skill** for dev-sandbox usage:
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```

**Distribution Options:**

| Target Buyer | Distribution Method | Complexity |
|--------------|---------------------|------------|
| Developers | GitHub repo + `pip install -r requirements.txt` | Low |
| Claude users | MCP package (SOPs 11-14) | Medium |
| Non-technical | Streamlit/Gradio web app | Medium |
| General public | Desktop app (Electron/PyInstaller) | High |

**Verification** (fresh Claude test):
1. Open new Claude Code instance
2. Open ONLY `~/ai-assistants/[name]/`
3. Claude should be able to use the assistant with ONLY the CLAUDE.md
4. No reference to dev-sandbox should be needed

**Communication Patterns**:
- "Deploy as AI assistant" → SOP 31 to `~/ai-assistants/[name]/`
- "Deploy as skill" → SOP 3 to `~/production/[name]-prod/`
- "Deploy as both" → Run SOP 31 then SOP 3
- "Package for sale" → Zip `src/`, `templates/`, `README.md`, `requirements.txt`

**References**: SOP 3 (Skills), SOPs 11-14 (MCP packaging)

---

## Quick Reference: When to Use Which SOP

| Situation | Use SOP | ⚠️ Prerequisites |
|-----------|---------|-----------------|
| **NEW IDEA** - uncertain market viability | [SOP 17: Market Viability Analysis](#sop-17-market-viability-analysis-multi-agent) | Product hypothesis, target customer |
| **FIRST** for any new project | [SOP 0: Project Kickoff & App Type Classification](#sop-0-project-kickoff--app-type-classification) | ⚠️ SOP 17 = GO (if applicable) |
| Starting a new project | [SOP 1: New Project Initialization](#sop-1-new-project-initialization) | **⚠️ Complete SOP 0 first** |
| Just wrote code / Need to test | `docs/testing-strategy.md` ⭐ | **Start with Scenario 1 (Manual Testing)** |
| Complex feature with edge cases | [SOP 2: Multi-Agent Testing](#sop-2-multi-agent-testing) | **⚠️ Manual testing complete (Scenario 1), environment working** |
| Ready to deploy to production | [SOP 3: Version Control & Deployment](#sop-3-version-control--deployment) | **⚠️ All testing scenarios complete** |
| Weekly maintenance / New project added | [SOP 4: Repository Cleanup & Verification](#sop-4-repository-cleanup--verification) | None |
| End of significant session | [SOP 5: Session Documentation](#sop-5-session-documentation) | None |
| Just completed a repeatable task | [SOP 6: Workflow Creation](#sop-6-workflow-creation) | Task tested |
| Deployed too early / No directive | [SOP 7: DOE Architecture Rollback](#sop-7-doe-architecture-rollback) | None |
| Testing for client / Need to save demo outputs | [SOP 8: Client Demo & Test Output Management](#sop-8-client-demo--test-output-management) | None |
| New project with multiple possible approaches | [SOP 9: Multi-Agent Architecture Exploration](#sop-9-multi-agent-architecture-exploration) | **⚠️ Complete SOP 0 first** (use BEFORE implementation) |
| Large system with 3+ independent components | [SOP 10: Multi-Agent Parallel Development](#sop-10-multi-agent-parallel-development) | Clear component boundaries |
| Converting project to MCP format | [SOP 11: MCP Package Structure](#sop-11-mcp-package-structure) | **⚠️ Project tested and working** |
| Publishing MCP to PyPI | [SOP 12: PyPI Publishing](#sop-12-pypi-publishing) | **⚠️ SOP 11 complete, PyPI account** |
| Publishing to Claude MCP Registry | [SOP 13: MCP Registry Publishing](#sop-13-mcp-registry-publishing) | **⚠️ SOP 12 complete (on PyPI first)** |
| Updating an existing MCP | [SOP 14: MCP Update & Version Bump](#sop-14-mcp-update--version-bump) | **⚠️ MCP already published, changes tested** |
| Deploy to multiple channels at once | [SOP 15: Multi-Channel Deployment](#sop-15-multi-channel-deployment) | **⚠️ Channels configured in deploy_to_skills.py** |
| Register MCP on OpenRouter directories | [SOP 16: OpenRouter Registration](#sop-16-openrouter-registration) | **⚠️ SOP 12 complete (PyPI first)** |
| Submit to external directories | See `docs/mcp-collection/workflows/submit-to-directories.md` | **⚠️ GitHub repos created, SOP 12-13 complete** |
| Running SMS campaign | [SOP 18: SMS Campaign Execution](#sop-18-sms-campaign-execution) | **⚠️ Templates approved, Twilio configured** |
| Managing follow-up sequences | [SOP 19: Multi-Touch Follow-Up Sequence](#sop-19-multi-touch-follow-up-sequence) | **⚠️ Campaign created, leads loaded** |
| Creating internal frameworks/methods | [SOP 20: Internal Method Development](#sop-20-internal-method-development) | None |
| Deciding when to create an SOP | [SOP 21: SOP Creation Method](#sop-21-sop-creation-method-meta-method) | Repeatable task identified |
| Tracking campaign performance | [SOP 22: Campaign Analytics & Tracking](#sop-22-campaign-analytics--tracking) | **⚠️ Campaign data exists in sms_campaigns.json** |
| Developing new outreach strategies | [SOP 23: Cold Outreach Strategy Development](#sop-23-cold-outreach-strategy-development) | Target segment defined |
| Daily/weekly routine check | [SOP 24: Daily/Weekly Digest System](#sop-24-dailyweekly-digest-system) | **⚠️ SMTP configured, Google OAuth optional** |
| Documenting large effort (>30 min) | [SOP 25: Documentation Decision Framework](docs/SOP-25-DOCUMENTATION-DECISION-FRAMEWORK.md) | Task completed, >30 minutes invested |
| User states something was previously done | [SOP 26: User Statement Validation Protocol](#sop-26-user-statement-validation-protocol) | **⚠️ MANDATORY - Never contradict user** |
| Quick task while mobile / away from computer | [SOP 27: Clawdbot Usage](docs/SOP-27-CLAWDBOT-USAGE.md) | Clawdbot VPS running |
| Complex multi-story development task | [SOP 28: Ralph Usage](docs/SOP-28-RALPH-USAGE.md) | PRD structure, clear requirements |
| Deciding which agent to use | [SOP 29: Three-Agent Collaboration](docs/SOP-29-THREE-AGENT-COLLABORATION.md) | See routing decision tree |
| Visual workflow automation / webhooks | [SOP 30: n8n Workflow Management](#sop-30-n8n-workflow-management) | EC2 n8n at http://34.193.98.97:5678 ⚠️ **EC2 ONLY** |
| Deploying standalone AI assistant | [SOP 31: AI Assistant Deployment](#sop-31-ai-assistant-deployment) | **Tested, self-contained CLAUDE.md written** |
| Selling/packaging an AI tool | [SOP 31: AI Assistant Deployment](#sop-31-ai-assistant-deployment) | **Product files ready (src/, templates/)** |

**Critical Notes**:
- **Market Viability (SOP 17)**: For NEW product ideas - 2-hour research saves weeks of building the wrong thing
- **Project Kickoff (SOP 0)**: ALWAYS start here for new projects - decide app type, cost-benefit, template vs clean slate
- **Architecture Exploration (SOP 9)**: Use BEFORE coding to research which approach is best
- **Parallel Development (SOP 10)**: Use DURING coding to build components simultaneously
- **Testing**: ALWAYS see `docs/testing-strategy.md` for complete pipeline (Manual → Multi-Agent → Pre-Deployment)
- **Multi-Agent Testing**: ALWAYS check `email-analyzer/testing/` first as reference template
- **Deployment Types**: Skills (SOP 3) → `~/production/`, AI Assistants (SOP 31) → `~/ai-assistants/`
- **AI Assistants (SOP 31)**: Self-contained tools for fresh Claude or sale - CLAUDE.md must work in isolation
- **MCP Publishing (SOPs 11-14)**: Publishes to Claude's marketplace
- **Multi-Channel (SOPs 15-16)**: Expands reach beyond Claude to OpenRouter + directories
- **Tool Selection (SOPs 27-28)**: Use Clawdbot for mobile/quick tasks, Ralph for complex multi-story development

---

**Principle:** Be pragmatic. Be reliable. Self-anneal.
