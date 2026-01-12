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

**Complete documentation**: See `docs/deployment.md`, `docs/repository-management.md`, `docs/versioned-deployment.md`

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

**Prompt interpretation:** See `docs/prompting-guide.md` for complete phrase mappings.

**When unclear:** Ask before deploying or making irreversible changes.

## Operating Principles

1. **Check for existing tools first** - Look in `execution/` and `[project]/workflows/` before creating new
2. **Build workflows as you work** - Document procedures while completing tasks
3. **Self-anneal** - When errors occur: fix → update tool → update directive
4. **Infer intelligently** - See `docs/inference-guidelines.md` for when to extend scope
5. **Living documents** - Some docs evolve throughout sessions, others are stable references:

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
| **Deployed skills** | `/Users/williammarceaujr./[name]-prod/` | ✅ Separate repo |
| **Standalone projects** | `/Users/williammarceaujr./[name]/` | ✅ Separate repo |

**Critical**: Never initialize git inside `projects/` - the parent dev-sandbox repo tracks everything. See `docs/repository-management.md`.

---

**Model:** Use Opus-4.5 for all development work.

**Principle:** Be pragmatic. Be reliable. Self-anneal.
