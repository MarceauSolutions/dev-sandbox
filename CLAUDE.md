# Agent Instructions

> Read this file at the start of every session. It contains core operating methods and pointers to detailed documentation.

## Architecture: DOE (Directive-Orchestration-Execution)

```
Layer 1: DIRECTIVE (directives/*.md)     → What to do
Layer 2: ORCHESTRATION (You/Claude)      → Decision making
Layer 3: EXECUTION (execution/*.py)      → Deterministic scripts
```

**Your role:** Read directives, call execution scripts in order, handle errors, update docs with learnings.

**Why this works:** Push complexity into deterministic code. You focus on decisions, not implementation.

## Documentation Map

| Need | Location |
|------|----------|
| **How we work** | This file (CLAUDE.md) |
| **How to prompt me** | `docs/prompting-guide.md` |
| **Inference guidelines** | `docs/inference-guidelines.md` |
| **Dev-to-deployment process** | `docs/development-to-deployment.md` ⭐ |
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
1. DESIGN in directives/
   └── Create/update [project].md with capability SOPs
   └── Define what the project does

2. DEVELOP in dev-sandbox/projects/[project]/
   └── NO git init inside projects! (see repository-management.md)
   └── Scripts in: [project]/src/
   └── Workflows in: [project]/workflows/
   └── Test with: execution/
   └── Commit to dev-sandbox repo (parent tracks all)

3. ORCHESTRATE (You/Claude)
   └── Read directives
   └── Call execution scripts
   └── Build workflows AS you complete tasks
   └── Update directive with learnings

4. DEPLOY when ready
   └── python deploy_to_skills.py --project [name] --version X.Y.Z
   └── Creates separate repo: /Users/williammarceaujr./[name]-prod/
   └── NOT nested in dev-sandbox (see repository-management.md)
```

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
| "Save this for the client" | Move output to demos/client-[name]/$(date)/ |
| "This is a good example" | Move to samples/ for documentation reference |
| "Clean up test files" | Delete everything in .tmp/ |

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
| **Detailed reference docs** | `docs/` | ✅ dev-sandbox |
| **Capability SOPs** | `directives/` | ✅ dev-sandbox |
| **Task procedures** | `[project]/workflows/` | ✅ dev-sandbox |
| **Session learnings** | `docs/session-history.md` | ✅ dev-sandbox |
| **Deployment config** | `deploy_to_skills.py` | ✅ dev-sandbox |
| **Executable scripts** | `execution/` | ✅ dev-sandbox |
| **Project development** | `projects/[name]/` | ✅ dev-sandbox (NO separate git!) |
| **Client demo outputs** | `projects/[name]/demos/client-[name]/` | ✅ Optional (check sensitivity) |
| **Reference examples** | `projects/[name]/samples/` | ✅ dev-sandbox |
| **Deployed skills** | `/Users/williammarceaujr./[name]-prod/` | ✅ Separate repo |
| **Standalone projects** | `/Users/williammarceaujr./[name]/` | ✅ Separate repo |
| **Temporary/test files** | `.tmp/` | ❌ NOT tracked (ephemeral workspace) |

**Critical**: Never initialize git inside `projects/` - the parent dev-sandbox repo tracks everything. See `docs/repository-management.md`.

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

### SOP 1: New Project Initialization

**When**: Starting a new AI assistant or automation project

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
   - Write scripts in `src/`
   - Test using `execution/` shared scripts
   - Document workflows as you complete tasks
   - Update directive with learnings

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

**When**: Implementing complex features with multiple edge cases

**Steps**:
1. **Create test plan**: `[project]/testing/TEST-PLAN.md`
   - Define test scenarios (3-4 per agent)
   - Assign focus areas to each agent
   - Set isolated workspaces

2. **Create agent prompts**: `[project]/testing/AGENT-PROMPTS.txt`
   - Copy-paste ready prompts for each agent
   - Include workspace isolation instructions
   - Specify expected deliverables

3. **Launch agents** (in parallel):
   - Open separate Claude instances
   - Paste agent-specific prompts
   - Let agents work independently

4. **Consolidate findings**:
   - Wait for all agents to complete
   - Create `[project]/testing/consolidated-results/CONSOLIDATED-FINDINGS.md`
   - Categorize: Critical, Important, Nice-to-Have
   - Prioritize fixes

5. **Implement fixes**:
   - Address critical issues first
   - Update workflows with solutions
   - Deploy new version
   - Update CHANGELOG

**Example**: Email Analyzer v1.1.0 - 4 agents found 6 critical + 6 important issues in 225 minutes

**References**: `email-analyzer/testing/TEST-PLAN.md`

---

### SOP 3: Version Control & Deployment

**When**: Deploying a new version to production

**Steps**:
1. **Develop in dev-sandbox** (version X.Y.Z-dev in VERSION file)
   - Make changes
   - Test thoroughly
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

## Quick Reference: When to Use Which SOP

| Situation | Use SOP |
|-----------|---------|
| Starting a new project | [SOP 1: New Project Initialization](#sop-1-new-project-initialization) |
| Complex feature with edge cases | [SOP 2: Multi-Agent Testing](#sop-2-multi-agent-testing) |
| Ready to deploy to production | [SOP 3: Version Control & Deployment](#sop-3-version-control--deployment) |
| Weekly maintenance / New project added | [SOP 4: Repository Cleanup & Verification](#sop-4-repository-cleanup--verification) |
| End of significant session | [SOP 5: Session Documentation](#sop-5-session-documentation) |
| Just completed a repeatable task | [SOP 6: Workflow Creation](#sop-6-workflow-creation) |
| Deployed too early / No directive | [SOP 7: DOE Architecture Rollback](#sop-7-doe-architecture-rollback) |
| Testing for client / Need to save demo outputs | [SOP 8: Client Demo & Test Output Management](#sop-8-client-demo--test-output-management) |

---

**Principle:** Be pragmatic. Be reliable. Self-anneal.
