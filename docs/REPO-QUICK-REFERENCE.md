# Repository Management - Quick Reference Card

## The Golden Rule

**NEVER have a `.git` directory inside another `.git` directory.**

---

## Quick Check (Run Weekly)

```bash
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d
```

**Expected**: Only `./.git`
**Problem**: Multiple results → See [repository-management.md](repository-management.md)

---

## Correct Structure

```
/Users/williammarceaujr./
├── dev-sandbox/          ← Git repo (development workspace)
├── website-repo/         ← Git repo (standalone project)
├── email-analyzer-prod/  ← Git repo (deployed skill)
└── interview-prep-prod/  ← Git repo (deployed skill)
```

All repos are **siblings** (same level), not nested.

---

## Development Workflow

### ✅ DO THIS

```bash
# 1. Develop in dev-sandbox WITHOUT initializing git
cd /Users/williammarceaujr./dev-sandbox/projects/my-project
# Work on files (NO git init!)

# 2. Commit to dev-sandbox repo
cd /Users/williammarceaujr./dev-sandbox
git add projects/my-project/
git commit -m "feat: Add my-project"
git push

# 3. Deploy when ready (creates separate repo automatically)
python deploy_to_skills.py --project my-project --version 1.0.0
# Creates: /Users/williammarceaujr./my-project-prod/
```

### ❌ DON'T DO THIS

```bash
# ❌ Don't initialize git inside dev-sandbox projects
cd /Users/williammarceaujr./dev-sandbox/projects/my-project
git init  # WRONG! Creates nested repo

# ❌ Don't clone repos inside dev-sandbox
cd /Users/williammarceaujr./dev-sandbox
git clone https://github.com/user/repo.git  # WRONG! Creates nested repo
```

---

## Common Fixes

### Fix 1: Accidentally Initialized Git in Project

```bash
# Remove the nested .git
rm -rf /Users/williammarceaujr./dev-sandbox/projects/my-project/.git

# Changes now tracked by parent repo
cd /Users/williammarceaujr./dev-sandbox
git add projects/my-project/
git commit -m "Add my-project"
```

### Fix 2: Cloned Repo Inside dev-sandbox

```bash
# Move it outside
mv /Users/williammarceaujr./dev-sandbox/cloned-repo /Users/williammarceaujr./cloned-repo

# Verify clean
cd /Users/williammarceaujr./dev-sandbox
find . -name ".git" -type d  # Should only show ./.git
```

---

## Where Things Go

| What | Where | Git? |
|------|-------|------|
| **New project development** | `dev-sandbox/projects/[name]/` | ❌ No |
| **Shared scripts** | `dev-sandbox/execution/` | ❌ No |
| **Directives/SOPs** | `dev-sandbox/directives/` | ❌ No |
| **Local skills** | `dev-sandbox/.claude/skills/` | ❌ No |
| **Deployed production skills** | `/Users/williammarceaujr./[name]-prod/` | ✅ Yes (separate repo) |
| **Standalone projects** | `/Users/williammarceaujr./[name]/` | ✅ Yes (separate repo) |

---

## Deployment Quick Reference

```bash
# Check what can be deployed
python deploy_to_skills.py --list

# Check project status
python deploy_to_skills.py --status email-analyzer

# Deploy to local directory
python deploy_to_skills.py --project email-analyzer --version 1.1.0
# Creates: /Users/williammarceaujr./email-analyzer-prod/

# Deploy to GitHub
python deploy_to_skills.py --project email-analyzer --repo user/repo-name
```

---

## Warning Signs

🚨 **You have a problem if**:

- `find . -name ".git" -type d` shows multiple results
- Git status shows "submodule" warnings
- Deployment script fails with repo errors
- You see `.git` inside `dev-sandbox/projects/`

📚 **Solution**: Read [repository-management.md](repository-management.md)

---

## One-Sentence Summary

**Develop everything in `dev-sandbox/` (one git repo), deploy to separate sibling repos using `deploy_to_skills.py`.**

---

**See also**: [repository-management.md](repository-management.md) (comprehensive guide)
