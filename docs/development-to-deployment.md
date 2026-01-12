# Development to Deployment Process

> **Purpose**: Complete guide to the documentation process and repository structure from initial development through skills deployment.

---

## Quick Overview

```
┌─────────────────────────────────────────────────────────────┐
│ DEVELOPMENT (Single Repo)                                   │
│ /Users/williammarceaujr./dev-sandbox/                       │
│   ├── .git/                    ← ONE git repo tracks all    │
│   ├── directives/              ← Capability SOPs            │
│   ├── projects/[name]/         ← NO .git here!              │
│   ├── execution/               ← Shared execution scripts   │
│   └── docs/                    ← Process documentation      │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    deploy_to_skills.py
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION (Separate Repos)                                 │
│ /Users/williammarceaujr./                                   │
│   ├── dev-sandbox/             ← Development repo           │
│   ├── [project]-prod/          ← Deployed skill repo        │
│   │   └── .git/                ← Separate git repo          │
│   └── website-repo/            ← Other standalone repos     │
│       └── .git/                ← Separate git repo          │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

### Development Repository (ONE)

**Location**: `/Users/williammarceaujr./dev-sandbox/`

**Purpose**: Central development environment where ALL projects are developed, tested, and iterated.

**Structure**:
```
dev-sandbox/
├── .git/                          ← Single git repository
├── CLAUDE.md                      ← Core agent instructions
├── directives/                    ← Capability SOPs (what to do)
│   ├── md_to_pdf.md
│   ├── email_analyzer.md
│   └── [capability].md
├── projects/                      ← Active development projects
│   ├── md-to-pdf/                 ← NO .git directory!
│   │   ├── src/                   ← Source code
│   │   ├── workflows/             ← Task procedures
│   │   ├── README.md              ← Project overview
│   │   ├── VERSION                ← Current version
│   │   └── CHANGELOG.md           ← Version history
│   ├── email-analyzer/
│   └── [project-name]/
├── execution/                     ← Shared deterministic scripts
│   ├── email_analyzer.py
│   └── [script].py
├── docs/                          ← Process documentation
│   ├── repository-management.md
│   ├── deployment.md
│   ├── session-history.md
│   └── [guide].md
├── deploy_to_skills.py            ← Deployment orchestrator
└── .tmp/                          ← Temporary work files
```

**Golden Rule**: **NEVER** run `git init` inside `projects/[name]/`. The parent `dev-sandbox` repository tracks everything.

**Git commits**: All development work is committed to the dev-sandbox repository.

### Production Repositories (MANY)

**Location**: `/Users/williammarceaujr./[project-name]-prod/`

**Purpose**: Separate, deployable repositories created by `deploy_to_skills.py`.

**Created by**: Deployment script (automatically)

**Structure** (example: email-analyzer-prod):
```
email-analyzer-prod/
├── .git/                          ← Separate git repository
├── README.md                      ← Project documentation
├── execution/                     ← Copied from dev-sandbox
│   └── email_analyzer.py
├── VERSION                        ← Deployed version
└── CHANGELOG.md                   ← Version history
```

**Relationship to dev-sandbox**: Sibling directories, NOT nested.

```
/Users/williammarceaujr./
├── dev-sandbox/           ← Development (source of truth)
├── email-analyzer-prod/   ← Production deployment
├── interview-prep-prod/   ← Production deployment
└── website-repo/          ← Standalone project
```

---

## Documentation Process

### 1. During Development (in dev-sandbox)

#### A. Create Directive (Capability SOP)

**When**: At project start, defines "what to do"

**Location**: `dev-sandbox/directives/[project-name].md`

**Contents**:
- Capability overview
- Core functionality
- Tool usage patterns
- Edge cases & error handling
- Success criteria
- Testing strategy

**Example**: `directives/md_to_pdf.md`

```markdown
# Directive: Markdown to PDF Converter

## Capability Overview
Convert markdown (.md) files into professional, interactive PDF documents...

## Core Functionality
### 1. Markdown Parsing
- Extract headers (H1-H6) for TOC generation
- Parse markdown with full support for...

## Tool Usage Patterns
### WeasyPrint (Primary PDF Engine)
...

## Edge Cases & Error Handling
### 1. Missing Dependencies
**Issue**: WeasyPrint or markdown2 not installed
**Solution**: ...
```

#### B. Create Project Structure

**Location**: `dev-sandbox/projects/[project-name]/`

**Critical**: **DO NOT** run `git init` inside this folder!

**Required files**:

1. **README.md** - Project overview
   - Features
   - Use cases
   - Quick start
   - Requirements

2. **VERSION** - Current version (e.g., `0.1.0-dev`)

3. **CHANGELOG.md** - Version history
   - Based on [Keep a Changelog](https://keepachangelog.com/)
   - Semantic versioning

4. **src/** - Source code
   - Main scripts
   - Implementation files

5. **workflows/** - Task procedures
   - Step-by-step workflows
   - Troubleshooting guides
   - Success criteria

**Example structure**:
```
projects/md-to-pdf/
├── src/
│   └── md_to_pdf.py           ← Implementation
├── workflows/
│   └── convert-md-to-pdf.md   ← Step-by-step procedure
├── README.md                   ← Overview & quick start
├── VERSION                     ← 0.1.0-dev
└── CHANGELOG.md                ← Version history
```

#### C. Create Workflows (Task Procedures)

**When**: AS you complete tasks (SOP 6)

**Location**: `dev-sandbox/projects/[project-name]/workflows/[task].md`

**Purpose**: Document procedures while doing the work

**Contents**:
- Overview & use cases
- Prerequisites
- Step-by-step workflow
- Tools used at each step
- Example commands
- Troubleshooting
- Success criteria

**Example**: `projects/md-to-pdf/workflows/convert-md-to-pdf.md`

```markdown
# Workflow: Convert Markdown to Interactive PDF

## Overview
This workflow converts markdown (.md) files into professional PDF documents...

## Workflow Steps

### 1. Prepare Markdown File
**Objective**: Ensure markdown is well-structured

**Actions**:
- Use proper header hierarchy
- Check image paths
- Verify code blocks

### 2. Parse Markdown and Extract Headers
**Script example**:
...
```

#### D. Update Session History

**When**: Throughout sessions, as learnings occur

**Location**: `dev-sandbox/docs/session-history.md`

**Purpose**: Capture insights, patterns, and decisions

**Format**:
```markdown
## 2026-01-12: Markdown to PDF Converter

**Learnings**:
- WeasyPrint provides better CSS support than ReportLab
- Anchor IDs must match exactly between TOC and headers
- Duplicate headers need numbered anchors

**Decisions**:
- Use markdown2 for parsing (lightweight, sufficient features)
- Default CSS embedded in script for portability
```

#### E. Commit to Dev-Sandbox Repository

**When**: After each significant change

**Where**: Parent `dev-sandbox` repository tracks all changes

**Example**:
```bash
cd /Users/williammarceaujr./dev-sandbox

git add directives/md_to_pdf.md
git add projects/md-to-pdf/
git commit -m "feat: Add Markdown to PDF converter project"
```

**Important**: You're committing to the dev-sandbox repo, NOT a nested repo.

### 2. Before Deployment (Preparation)

#### A. Version the Project

**Update VERSION file**: Change from `X.Y.Z-dev` to `X.Y.Z`

**Example**:
```
Before: 0.1.0-dev
After:  1.0.0
```

#### B. Update CHANGELOG.md

**Document what's being deployed**:

```markdown
## [1.0.0] - 2026-01-12

### Added
- Markdown to PDF conversion with automatic table of contents
- Interactive navigation (clickable TOC links)
- Professional styling with customizable CSS
- Batch conversion support
- Code syntax highlighting
- Table and image support

### Fixed
- (if applicable)

### Changed
- (if applicable)
```

#### C. Test in Dev-Sandbox

**Verify everything works**:
```bash
# Test single conversion
python projects/md-to-pdf/src/md_to_pdf.py README.md test.pdf

# Test batch conversion
python projects/md-to-pdf/src/md_to_pdf.py "docs/*.md" --output pdfs/

# Verify output quality
open test.pdf
```

#### D. Review Documentation

**Checklist**:
- [ ] Directive complete in `directives/`
- [ ] README.md clear and accurate
- [ ] Workflow documented in `workflows/`
- [ ] VERSION updated (remove `-dev`)
- [ ] CHANGELOG.md updated
- [ ] All code committed to dev-sandbox

### 3. Deployment (Creating Production Repo)

#### A. Deploy to Skills

**Command**:
```bash
cd /Users/williammarceaujr./dev-sandbox

python deploy_to_skills.py --project md-to-pdf --version 1.0.0
```

**What happens**:
1. Creates `/Users/williammarceaujr./md-to-pdf-prod/`
2. Initializes NEW git repository in production folder
3. Copies required files from dev-sandbox
4. Creates README.md for production
5. Commits to production repo
6. Tags with version (v1.0.0)

**Result**: Separate production repository ready for use.

#### B. Optional: Deploy to GitHub

**Command**:
```bash
python deploy_to_skills.py --project md-to-pdf --repo username/md-to-pdf
```

**What happens**:
1. Creates production repo (if not exists)
2. Pushes to GitHub remote
3. Creates GitHub release with tag

#### C. Verify Deployment

**Check production repo**:
```bash
cd /Users/williammarceaujr./md-to-pdf-prod
git log
git tag
```

**Verify structure**:
```
md-to-pdf-prod/
├── .git/              ← NEW separate repository
├── README.md
├── execution/
├── VERSION
└── CHANGELOG.md
```

### 4. After Deployment (Continuation)

#### A. Return to Development

**Update dev-sandbox VERSION**:
```
1.0.0 → 1.1.0-dev
```

**Continue development**:
- All new work happens in `dev-sandbox/projects/md-to-pdf/`
- Commit to dev-sandbox repository
- Production repo remains unchanged until next deployment

#### B. Document Learnings

**Update session-history.md**:
```markdown
## 2026-01-12: Deployed MD-to-PDF v1.0.0

**Deployment notes**:
- First production release
- No issues during deployment
- Successfully tested single and batch conversion

**Next iteration**:
- Add custom headers/footers
- PDF metadata support
```

---

## Common Workflows

### New Project From Scratch

1. **Create directive**: `directives/[name].md`
2. **Create project folder**: `projects/[name]/`
   - DO NOT run `git init`!
3. **Develop iteratively**:
   - Write code in `src/`
   - Document in `workflows/` as you work
4. **Commit to dev-sandbox**: `git add . && git commit`
5. **Deploy when ready**: `python deploy_to_skills.py --project [name] --version X.Y.Z`

### Updating Existing Project

1. **Work in dev-sandbox**: `projects/[name]/`
2. **Version should be**: `X.Y.Z-dev`
3. **Commit changes**: To dev-sandbox repo
4. **Update CHANGELOG**: Document changes
5. **Deploy new version**: `python deploy_to_skills.py --project [name] --version X.Y.Z`

### Creating Workflow Documentation

1. **Start workflow while doing task**: Open `workflows/[task-name].md`
2. **Document each step as you complete it**
3. **Include**:
   - Objective for each step
   - Tools used
   - Example code/commands
   - Troubleshooting
4. **Commit to dev-sandbox**: Along with code changes

### Checking Repository Health

**Quick check**:
```bash
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d
```

**Expected output**:
```
./.git
```

**If you see more**: You have nested repos! Follow [Repository Management Guide](repository-management.md).

---

## Documentation File Types

### Living Documents (Update Throughout Sessions)

**Updated frequently, capture ongoing work**:

- `docs/session-history.md` - Learnings, decisions, insights
- `docs/prompting-guide.md` - New phrase patterns
- `CLAUDE.md` - Communication patterns (as discovered)
- `projects/[name]/CHANGELOG.md` - Version changes

### Stable References (Update When System Changes)

**Updated only when procedures or architecture changes**:

- `docs/deployment.md` - Deployment SOP
- `docs/versioned-deployment.md` - Versioning strategy
- `docs/repository-management.md` - Repository rules
- `docs/inference-guidelines.md` - Decision framework
- `directives/[name].md` - Capability SOPs
- `projects/[name]/workflows/[task].md` - Task procedures

### Project Documentation (Update With Each Version)

**Core project files**:

- `projects/[name]/README.md` - Overview, features, quick start
- `projects/[name]/VERSION` - Current version number
- `projects/[name]/CHANGELOG.md` - Version history

---

## Key Principles

### 1. One Development Repository

**Rule**: All development happens in ONE git repository (`dev-sandbox`)

**Never**:
- Run `git init` inside `projects/[name]/`
- Create `.git` inside dev-sandbox (except at root)
- Nest repositories

**Always**:
- Commit to parent dev-sandbox repo
- Use `git add projects/[name]/` to track changes

### 2. Document As You Work

**Rule**: Create workflows WHILE completing tasks, not after

**Why**: Capture decisions, edge cases, and context in real-time

**Example**: While developing MD-to-PDF converter, simultaneously write `workflows/convert-md-to-pdf.md`

### 3. Separation of Development and Production

**Development**: `dev-sandbox/projects/[name]/` (no separate git)

**Production**: `/Users/williammarceaujr./[name]-prod/` (separate git)

**Never**: Mix development and production in same folder

### 4. Version Everything

**Development versions**: `X.Y.Z-dev` (e.g., `1.1.0-dev`)

**Production versions**: `X.Y.Z` (e.g., `1.0.0`)

**Rule**: Remove `-dev` before deployment, add back after

### 5. Self-Annealing Documentation

**When errors occur**:
1. Fix the issue
2. Update the code/script
3. Update the directive with learnings
4. Update workflow with troubleshooting

**Result**: Documentation gets better with each iteration

---

## Deployment Commands Reference

### List Projects and Versions

```bash
python deploy_to_skills.py --list
```

**Shows**: All projects with dev vs. prod versions

### Check Deployment Status

```bash
python deploy_to_skills.py --status md-to-pdf
```

**Shows**: Version differences, last deployment date

### Deploy to Local Production

```bash
python deploy_to_skills.py --project md-to-pdf --version 1.0.0
```

**Creates**: `/Users/williammarceaujr./md-to-pdf-prod/`

### Deploy to GitHub

```bash
python deploy_to_skills.py --project md-to-pdf --repo username/md-to-pdf
```

**Pushes**: To GitHub with release tag

### Sync Execution Scripts

```bash
python deploy_to_skills.py --sync-execution --project md-to-pdf
```

**Copies**: Latest execution scripts to production

---

## Where Things Live

### Development Phase

| What | Where | Git Tracked By |
|------|-------|----------------|
| Directives | `dev-sandbox/directives/` | dev-sandbox |
| Source code | `dev-sandbox/projects/[name]/src/` | dev-sandbox |
| Workflows | `dev-sandbox/projects/[name]/workflows/` | dev-sandbox |
| Execution scripts | `dev-sandbox/execution/` | dev-sandbox |
| Process docs | `dev-sandbox/docs/` | dev-sandbox |
| Session history | `dev-sandbox/docs/session-history.md` | dev-sandbox |

### Production Phase

| What | Where | Git Tracked By |
|------|-------|----------------|
| Production code | `/Users/williammarceaujr./[name]-prod/` | [name]-prod |
| Execution scripts | `/Users/williammarceaujr./[name]-prod/execution/` | [name]-prod |
| README | `/Users/williammarceaujr./[name]-prod/README.md` | [name]-prod |
| Version | `/Users/williammarceaujr./[name]-prod/VERSION` | [name]-prod |

---

## Troubleshooting

### "I see multiple .git directories"

**Problem**: Nested repositories detected

**Solution**: Follow [Repository Management Guide](repository-management.md#fixing-nested-repositories)

### "Deployment created files in wrong place"

**Problem**: Production repo created inside dev-sandbox

**Solution**:
1. Stop deployment
2. Delete nested production repo
3. Check `deploy_to_skills.py` output paths
4. Re-run deployment

### "Git is tracking too many files"

**Problem**: Possibly tracking production repos as subfolders

**Check**:
```bash
cd dev-sandbox
git status
```

**Solution**: Ensure production repos are siblings, not children of dev-sandbox

### "Lost my development work"

**Problem**: Forgot to commit to dev-sandbox before deployment

**Solution**:
1. Check `git log` in dev-sandbox
2. Recovery: Development work should still exist in `projects/[name]/`
3. Commit: `git add . && git commit -m "Recover dev work"`

---

## Quick Reference Checklist

### Starting New Project
- [ ] Create directive: `directives/[name].md`
- [ ] Create folder: `projects/[name]/` (NO git init!)
- [ ] Add README, VERSION, CHANGELOG
- [ ] Develop in `src/`
- [ ] Document in `workflows/` as you work
- [ ] Commit to dev-sandbox repo

### Deploying Project
- [ ] Test everything works in dev-sandbox
- [ ] Update VERSION (remove `-dev`)
- [ ] Update CHANGELOG with changes
- [ ] Commit all changes to dev-sandbox
- [ ] Run: `deploy_to_skills.py --project [name] --version X.Y.Z`
- [ ] Verify: Check `/Users/williammarceaujr./[name]-prod/`
- [ ] Return to dev: Update VERSION to `X.Y.Z-dev`

### Repository Health Check
- [ ] Run: `find . -name ".git" -type d`
- [ ] Should see: Only `./.git`
- [ ] If more: Fix nested repos immediately

---

## Related Documentation

- [Repository Management Guide](repository-management.md) - Comprehensive repo rules
- [REPO-QUICK-REFERENCE.md](REPO-QUICK-REFERENCE.md) - Single-page lookup
- [Deployment Guide](deployment.md) - Detailed deployment SOP
- [Versioned Deployment](versioned-deployment.md) - Version strategy
- [CLAUDE.md](../CLAUDE.md) - Core operating instructions
- [Session History](session-history.md) - Learning log

---

**Last Updated**: 2026-01-12
**Version**: 1.0.0
