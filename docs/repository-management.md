# Repository Management Guide

## Overview

This document explains how to properly manage git repositories in the dev-sandbox ecosystem to avoid nested repository issues and maintain a clean project structure.

## Repository Structure Philosophy

```
/Users/williammarceaujr./
├── dev-sandbox/                    # Main development workspace (GIT REPO)
│   ├── .git/                       # Git tracking for dev-sandbox
│   ├── projects/                   # Non-git project folders
│   │   ├── interview-prep/
│   │   ├── fitness-influencer/
│   │   ├── amazon-seller/
│   │   └── email-analyzer/         # Projects developed here (NO .git)
│   ├── .claude/skills/             # Local skill definitions (NO .git)
│   ├── execution/                  # Shared executable scripts
│   └── docs/                       # Documentation
│
├── production/                     # Deployed production skills (ORGANIZED CATEGORY)
│   └── email-analyzer-prod/        # Deployed skill repo (SEPARATE)
│       └── .git/                   # Production git tracking
│
└── websites/                       # Company & client websites (ORGANIZED CATEGORY)
    └── website-repo/               # Separate git repo
        └── .git/                   # Its own git tracking
```

## The Golden Rule: No Nested Repositories

**NEVER have a `.git` directory inside another `.git` directory.**

### Why This Matters

1. **Git confusion**: Git doesn't handle nested repos well - changes in nested repos won't be tracked by parent repo
2. **Deployment issues**: Nested repos cause problems when deploying to production
3. **Submodule complexity**: If you need nested repos, use git submodules (advanced, usually unnecessary)
4. **Tool failures**: Many deployment tools and CI/CD pipelines fail with nested repos

### Detecting Nested Repositories

Run this command periodically to check for nested repos:

```bash
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d
```

**Expected output** (only one result):
```
./.git
```

**Problem output** (nested repos found):
```
./.git
./website-repo/.git           # ❌ NESTED - needs to be moved
./projects/some-project/.git  # ❌ NESTED - needs to be moved
```

## Development Workflow

### Phase 1: Develop in dev-sandbox (No Git in Projects)

**Location**: `/Users/williammarceaujr./dev-sandbox/projects/[project-name]/`

**Key principle**: Projects in `dev-sandbox/projects/` should **NOT** have their own `.git` directories.

```bash
# ✅ CORRECT: Develop without initializing git
cd /Users/williammarceaujr./dev-sandbox/projects/email-analyzer
# NO git init here!
# Work on your project files
# Changes tracked by parent dev-sandbox repo

# ✅ Commit changes to dev-sandbox repo
cd /Users/williammarceaujr./dev-sandbox
git add projects/email-analyzer/
git commit -m "feat: Add email analyzer workflows"
git push
```

```bash
# ❌ WRONG: Don't do this inside dev-sandbox
cd /Users/williammarceaujr./dev-sandbox/projects/email-analyzer
git init  # ❌ Creates nested repo!
```

### Phase 2: Deploy to Production (Separate Repo)

**Location**: `/Users/williammarceaujr./production/email-analyzer-prod/` (OUTSIDE dev-sandbox, in production/ category)

**Key principle**: Production/deployed skills get their own git repos in the **production/** directory (sibling to dev-sandbox).

```bash
# ✅ CORRECT: Use deploy script to create separate repo
cd /Users/williammarceaujr./dev-sandbox
python deploy_to_skills.py --project email-analyzer --version 1.1.0

# This creates: /Users/williammarceaujr./production/email-analyzer-prod/
# With its own .git (NOT nested in dev-sandbox)
```

## deploy_to_skills.py Behavior

The deployment script automatically handles repository separation:

### What It Does

1. **Reads** from: `/Users/williammarceaujr./dev-sandbox/projects/[project]/`
2. **Writes** to: `/Users/williammarceaujr./production/[project]-prod/` (SEPARATE location in production/ category)
3. **Creates** a git repo in the production folder (NOT in dev-sandbox)
4. **Copies** only necessary files (workflows, SKILL.md, scripts, etc.)
5. **Commits** and optionally pushes to GitHub

### Directory Mapping

| Development | Production | Git Status |
|-------------|------------|------------|
| `dev-sandbox/email-analyzer/` | `production/email-analyzer-prod/` | Separate repos |
| `dev-sandbox/projects/interview-prep/` | `production/interview-prep-prod/` | Separate repos |
| `dev-sandbox/projects/fitness-influencer/` | `production/fitness-influencer-prod/` | Separate repos |

### Example Deployment

```bash
# Before deployment
/Users/williammarceaujr./
├── dev-sandbox/
│   ├── .git/                              # Only git repo
│   └── email-analyzer/
│       ├── workflows/
│       ├── SKILL.md
│       └── CHANGELOG.md

# After running: python deploy_to_skills.py --project email-analyzer --version 1.1.0
/Users/williammarceaujr./
├── dev-sandbox/
│   ├── .git/                              # Original dev repo
│   └── email-analyzer/
│       └── (files unchanged)
│
└── production/                            # Organized production category
    └── email-analyzer-prod/               # NEW: Separate production repo
        ├── .git/                          # NEW: Its own git tracking
        ├── workflows/                     # Copied from dev-sandbox
        ├── SKILL.md                       # Copied from dev-sandbox
        ├── CHANGELOG.md                   # Copied from dev-sandbox
        └── VERSION                        # Copied from dev-sandbox
```

## Special Cases

### Case 1: Standalone Projects (e.g., website-repo)

**Problem**: You have a project that needs its own git repo but was accidentally created inside dev-sandbox.

**Solution**: Move it outside dev-sandbox.

```bash
# ✅ Move nested repo to organized category
mv /Users/williammarceaujr./dev-sandbox/website-repo /Users/williammarceaujr./websites/website-repo

# Verify no nested repos remain
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d
# Should only show: ./.git
```

**Result**:
```
/Users/williammarceaujr./
├── dev-sandbox/                # Git repo for development
│   └── .git/
├── production/                 # Organized production category
│   └── email-analyzer-prod/    # Separate git repo (deployment target)
│       └── .git/
└── websites/                   # Organized websites category
    └── website-repo/           # Separate git repo
        └── .git/
```

### Case 2: Projects That Need Git During Development

**Rare scenario**: If a project truly needs git during development (e.g., testing git hooks, CI/CD integration).

**Solution**: Develop it as a sibling to dev-sandbox, not inside it.

```bash
# ❌ WRONG
/Users/williammarceaujr./dev-sandbox/special-project/.git

# ✅ CORRECT (in appropriate category)
/Users/williammarceaujr./active-projects/special-project/.git
```

Then use symlinks if you need it visible in dev-sandbox:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects
ln -s ../../active-projects/special-project special-project
# Now appears in dev-sandbox/projects/ but isn't nested
```

### Case 3: Git Submodules (Advanced)

**Only use if absolutely necessary** (rare).

If you must track an external git repo inside dev-sandbox:

```bash
cd /Users/williammarceaujr./dev-sandbox
git submodule add https://github.com/external/library.git projects/library

# This creates proper submodule tracking
# NOT recommended for most projects
```

## Common Mistakes and Fixes

### Mistake 1: Initialized Git in Project Folder

**Problem**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/my-project
git init  # ❌ Oops! Created nested repo
```

**Fix**:
```bash
# Remove the nested git repo
rm -rf /Users/williammarceaujr./dev-sandbox/projects/my-project/.git

# Changes now tracked by parent dev-sandbox repo
cd /Users/williammarceaujr./dev-sandbox
git add projects/my-project/
git commit -m "Add my-project files"
```

### Mistake 2: Cloned Repo Inside dev-sandbox

**Problem**:
```bash
cd /Users/williammarceaujr./dev-sandbox
git clone https://github.com/user/some-repo.git  # ❌ Creates nested repo
```

**Fix**:
```bash
# Move cloned repo outside dev-sandbox
mv /Users/williammarceaujr./dev-sandbox/some-repo /Users/williammarceaujr./some-repo

# Or if you need files in dev-sandbox, copy without .git
cp -r /Users/williammarceaujr./dev-sandbox/some-repo /Users/williammarceaujr./dev-sandbox/projects/some-project
rm -rf /Users/williammarceaujr./dev-sandbox/projects/some-project/.git
```

### Mistake 3: Production Repo Inside dev-sandbox

**Problem**: Deployed the project inside dev-sandbox instead of outside.

**Fix**: Use the deployment script correctly - it automatically creates production repos in the production/ category.

```bash
# ✅ Correct deployment
python deploy_to_skills.py --project email-analyzer --version 1.1.0
# Creates: /Users/williammarceaujr./production/email-analyzer-prod/ (in production/ category)
```

## Verification Checklist

Before committing or deploying, run these checks:

```bash
# 1. Check for nested repos in dev-sandbox
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d
# Expected: Only ./.git

# 2. Check git status is clean
git status
# Should show tracked files, no nested repo warnings

# 3. Verify production repos are in production/ category
ls -la /Users/williammarceaujr./production/
# Should show *-prod directories

# 4. Check deployment targets
python deploy_to_skills.py --list
# Shows where each project deploys (should be in ~/production/)
```

## Best Practices Summary

| Scenario | Correct Approach | Incorrect Approach |
|----------|------------------|-------------------|
| **New project development** | Create in `dev-sandbox/projects/[name]/` without git | Initialize git inside project folder |
| **Existing git repo to work on** | Clone outside dev-sandbox, symlink if needed | Clone inside dev-sandbox |
| **Deploy to production** | Use `deploy_to_skills.py` (creates repo in production/) | Manually create git repo inside dev-sandbox |
| **Multiple related projects** | Keep all in `dev-sandbox/projects/` without git | Create separate git repos for each |
| **Website or standalone app** | Keep in websites/ or active-projects/ category | Put inside dev-sandbox with git |

## Quick Reference Commands

```bash
# Find nested repos (should return only ./.git)
find /Users/williammarceaujr./dev-sandbox -name ".git" -type d

# Move nested repo to appropriate category
mv /Users/williammarceaujr./dev-sandbox/[nested-repo] /Users/williammarceaujr./[category]/[nested-repo]
# Categories: production/, websites/, active-projects/, legacy/, archived/

# Remove .git from project folder (if accidentally initialized)
rm -rf /Users/williammarceaujr./dev-sandbox/projects/[project]/.git

# Deploy project to production/ category
cd /Users/williammarceaujr./dev-sandbox
python deploy_to_skills.py --project [name] --version X.Y.Z
# Creates: ~/production/[name]-prod/

# Commit dev-sandbox changes (includes all project folders)
cd /Users/williammarceaujr./dev-sandbox
git add .
git commit -m "feat: Description"
git push
```

## When to Break These Rules

**Almost never.** The only exception:

- You're using git submodules for external dependencies (advanced, rarely needed)
- You have a specific technical requirement documented with your team

In 99% of cases, follow the structure outlined in this document.

---

**Last updated**: 2026-01-21
**Related docs**: [deployment.md](deployment.md), [versioned-deployment.md](versioned-deployment.md), [HOME-DIRECTORY-REORGANIZATION-COMPLETE.md](../HOME-DIRECTORY-REORGANIZATION-COMPLETE.md)
