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
| **Project navigation** | `docs/projects.md` |
| **Workflow template** | `docs/workflow-standard.md` |
| **Session learnings** | `docs/session-history.md` |
| **Capability SOPs** | `directives/` |
| **Task procedures** | `[project]/workflows/` |

## Development Pipeline (DOE → Skills)

**Complete documentation**: See `docs/development-to-deployment.md` for full process, or `docs/deployment.md`, `docs/repository-management.md`, `docs/versioned-deployment.md` for specific topics.

```
0. KICKOFF (SOP 0) - BEFORE starting any new project
   └── Complete project-kickoff-questionnaire.md (19 questions)
   └── Decide app type (MCP, CLI, Web, Desktop, Hybrid)
   └── Complete cost-benefit analysis
   └── Decide template vs clean slate
   └── See: docs/app-type-decision-guide.md

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
   └── Creates separate repo: /Users/williammarceaujr./[name]-prod/
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
- **[project]-prod/**: Deployed skills (SEPARATE git repos, siblings to dev-sandbox)
- **Never nest repos**: `find . -name ".git" -type d` should only show `./.git`

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

**Prompt interpretation:** See `docs/prompting-guide.md` for complete phrase mappings.

**When unclear:** Ask before deploying or making irreversible changes.

## Operating Principles

1. **Follow DOE discipline** - Don't deploy frontend until execution layer is solid
   - Layer 1 (Directive) must exist before Layer 3 (Execution)
   - Deploy ONLY when all three layers are complete

2. **Check for existing tools first** - Look in `execution/` and `[project]/workflows/` before creating new

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

7. **Infer intelligently** - See `docs/inference-guidelines.md` for when to extend scope

8. **Living documents** - Some docs evolve throughout sessions, others are stable references:

   **Living (update throughout sessions):**
   - `docs/session-history.md` - Add learnings as they happen
   - `docs/prompting-guide.md` - Add new phrase patterns when discovered
   - `CLAUDE.md` - Update communication patterns table

   **Stable References (update only when system changes):**
   - `docs/inference-guidelines.md` - Framework/ruleset
   - `docs/repository-management.md` - Repository structure rules
   - `docs/REPO-QUICK-REFERENCE.md` - Quick repo checks
   - `docs/versioned-deployment.md` - Version control SOP
   - `docs/deployment.md` - Deployment pipeline architecture
   - `[project]/workflows/` - Task procedures
   - `[project]/USER_PROMPTS.md` - User guidance templates
   - `[project]/CHANGELOG.md` - Version history (update at deploy time)

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
| **Project-specific code** | `projects/[name]/src/` | ✅ dev-sandbox (NO separate git!) |
| **Project development** | `projects/[name]/` | ✅ dev-sandbox (NO separate git!) |
| **Client demo outputs** | `projects/[name]/demos/client-[name]/` | ✅ Optional (check sensitivity) |
| **Reference examples** | `projects/[name]/samples/` | ✅ dev-sandbox |
| **Deployed skills** | `/Users/williammarceaujr./[name]-prod/` | ✅ Separate repo |
| **Standalone projects** | `/Users/williammarceaujr./[name]/` | ✅ Separate repo |
| **Temporary/test files** | `.tmp/` | ❌ NOT tracked (ephemeral workspace) |

**Critical**:
- Never initialize git inside `projects/` - the parent dev-sandbox repo tracks everything
- Code organization: `execution/` for shared (2+ projects), `projects/[name]/src/` for project-specific
- See `docs/repository-management.md` for git structure, `docs/architecture-guide.md` for code organization

**Temporary files policy**: The `.tmp/` directory is for ephemeral work only:
- Testing and experimentation files
- Temporary outputs that don't need long-term storage
- Files that serve a single-use purpose
- **Auto-cleanup**: Delete files after their intended purpose to prevent clutter
- **Not tracked**: `.tmp/` is in `.gitignore` and should never be committed

---

**Model:** Use Opus-4.5 for all development work.

**Principle:** Be pragmatic. Be reliable. Self-anneal.

---

## Standard Operating Procedures (SOPs)

### SOP 0: Project Kickoff & App Type Classification

**When**: BEFORE starting any new project (runs before SOP 1 and SOP 9)

**Purpose**: Ensure proper app type selection, cost analysis, and template decisions are made upfront.

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

**References**: `docs/app-type-decision-guide.md`, `docs/cost-benefit-templates.md`, `templates/project-kickoff-questionnaire.md`

---

### SOP 1: New Project Initialization

**When**: Starting a new AI assistant or automation project (AFTER completing SOP 0)

**Steps**:
1. **Create directive**: `directives/[project-name].md`
   - Define capabilities and SOPs
   - Document edge cases and error handling
   - Include tool usage patterns

2. **Create project folder**: `dev-sandbox/projects/[project-name]/`
   - **DO NOT** run `git init` inside this folder
   - Create structure:
     ```
     projects/[project-name]/
     ├── src/              # Python scripts
     ├── workflows/        # Task procedures (markdown)
     ├── VERSION           # e.g., "1.0.0-dev"
     ├── CHANGELOG.md      # Version history
     ├── SKILL.md          # Skill definition
     └── README.md         # Project documentation
     ```

3. **Develop iteratively**:
   - Write project-specific scripts in `src/`
   - Use shared utilities from `execution/` (if needed)
   - Extract to `execution/` only when 2+ projects use same code
   - Document workflows as you complete tasks
   - Update directive with learnings
   - See: `docs/architecture-guide.md` for code organization decisions

4. **Commit to dev-sandbox**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   git add projects/[project-name]/
   git commit -m "feat: Initial [project-name] structure"
   ```

5. **Deploy when ready**:
   ```bash
   python deploy_to_skills.py --project [project-name] --version 1.0.0
   ```

**References**: `docs/deployment.md`, `docs/repository-management.md`

---

### SOP 2: Multi-Agent Testing

**When**: After manual testing complete AND implementing complex features with multiple edge cases

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

### SOP 3: Version Control & Deployment

**When**: Deploying a new version to production (AFTER testing complete)

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
   - Creates `/Users/williammarceaujr./[name]-prod/` with separate git repo
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

**References**: `docs/versioned-deployment.md`

---

### SOP 4: Repository Cleanup & Verification

**When**: Weekly maintenance, or when adding new projects

**Steps**:
1. **Check for nested repos**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox
   find . -name ".git" -type d
   # Expected: Only ./.git
   ```

2. **If nested repos found**:
   - Move to parent: `mv dev-sandbox/[nested-repo] /Users/williammarceaujr./[nested-repo]`
   - Verify: Re-run find command
   - Commit change: `git add -A && git commit -m "fix: Move nested repo to parent"`

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

**References**: `docs/repository-management.md`, `docs/REPO-QUICK-REFERENCE.md`

---

### SOP 5: Session Documentation

**When**: At end of each significant session or when major learnings occur

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

**References**: `docs/session-history.md`, `docs/prompting-guide.md`

---

### SOP 6: Workflow Creation

**When**: Completing a repeatable task for the first time

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

**References**: `docs/workflow-standard.md`

---

### SOP 7: DOE Architecture Rollback

**When**: Premature deployment detected (deployed execution without directive)

**Steps**:
1. **Identify premature deployments**:
   - Frontend deployed without backend
   - Execution scripts without directive
   - Features advertised but not implemented

2. **Create "Coming Soon" page**:
   - Replace premature content with inquiry form
   - Collect email/SMS opt-ins (pre-checked)
   - Show project preview/description
   - Link to contact form

3. **Remove premature files**:
   ```bash
   git rm [premature-file.html]
   git commit -m "rollback: Remove premature [feature] deployment"
   ```

4. **Build directive first**:
   - Create `directives/[project].md`
   - Define capabilities, SOPs, edge cases
   - Document tool usage patterns

5. **Then build execution**:
   - Create scripts in `[project]/src/`
   - Test thoroughly
   - Update directive with learnings

6. **Finally deploy frontend** (when ready):
   - All layers complete (Directive, Orchestration, Execution)
   - Replace "Coming Soon" with real content

**References**: `docs/session-history.md` (2026-01-09 entry)

---

### SOP 8: Client Demo & Test Output Management

**When**: Testing workflows for clients or need to preserve test outputs for review/demonstration

**Purpose**: Systematically save valuable test outputs while maintaining workspace cleanliness

**Directory Structure**:
```
projects/[project-name]/
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

**References**: See `docs/workflow-standard.md` for documentation examples, `docs/repository-management.md` for .gitignore best practices

---

### SOP 9: Multi-Agent Architecture Exploration

**When**: Before starting implementation of a new project with multiple possible approaches

**Purpose**: Research and evaluate 3-4 different implementation strategies in parallel to choose the optimal approach BEFORE writing code

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

**References**:
- See `docs/testing-strategy.md` for distinction between exploration (SOP 9) and testing (SOP 2)
- See `email-analyzer/testing/` as template for multi-agent setup (similar structure)

---

### SOP 10: Multi-Agent Parallel Development

**When**: Building a complex system with 3+ independent components that can be developed simultaneously

**Purpose**: Accelerate development by having multiple agents BUILD different components in parallel, then consolidate outputs into a unified codebase

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
- `projects/md-to-pdf/` - Working example
- `projects/amazon-seller/` - Working example
- `projects/fitness-influencer/` - Working example

---

### SOP 12: PyPI Publishing

**When**: Publishing an MCP package to PyPI (AFTER SOP 11 complete)

**Purpose**: Make your MCP installable via `pip install [project]-mcp`

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

## Quick Reference: When to Use Which SOP

| Situation | Use SOP | ⚠️ Prerequisites |
|-----------|---------|-----------------|
| **FIRST** for any new project | [SOP 0: Project Kickoff & App Type Classification](#sop-0-project-kickoff--app-type-classification) | None (START HERE) |
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

**Critical Notes**:
- **Project Kickoff (SOP 0)**: ALWAYS start here for new projects - decide app type, cost-benefit, template vs clean slate
- **Architecture Exploration (SOP 9)**: Use BEFORE coding to research which approach is best
- **Parallel Development (SOP 10)**: Use DURING coding to build components simultaneously
- **Testing**: ALWAYS see `docs/testing-strategy.md` for complete pipeline (Manual → Multi-Agent → Pre-Deployment)
- **Multi-Agent Testing**: ALWAYS check `email-analyzer/testing/` first as reference template
- **Deployment**: Can ONLY happen after all testing scenarios complete
- **MCP Publishing (SOPs 11-13)**: OPTIONAL step after deployment - publishes to Claude's marketplace

---

**Principle:** Be pragmatic. Be reliable. Self-anneal.
