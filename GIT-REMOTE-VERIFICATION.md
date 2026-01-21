# Git Remote Configuration Verification

**Date**: 2026-01-21
**Status**: ⚠️ NEEDS ATTENTION - Most production repos lack GitHub remotes

---

## Current State

### ✅ dev-sandbox (Development Workspace)
```
Repository: ~/dev-sandbox/
Remote: https://github.com/MarceauSolutions/dev-sandbox.git
Status: ✅ CORRECTLY CONFIGURED
```

### ⚠️ production/ (Deployed Skills - 6 repos)

| Repository | Git Remote | Status |
|------------|------------|--------|
| crm-onboarding-prod | ✅ https://github.com/MarceauSolutions/crm-onboarding-prod.git | CONFIGURED |
| email-analyzer-prod | ❌ None | NEEDS SETUP |
| hvac-distributors-prod | ❌ None | NEEDS SETUP |
| interview-prep-prod | ❌ None | NEEDS SETUP |
| lead-scraper-prod | ❌ None | NEEDS SETUP |
| time-blocks-prod | ❌ None | NEEDS SETUP |

**Issue**: 5 of 6 production repos have no GitHub remotes configured

### ✅ websites/ (Company & Client Sites - 5 repos)

| Repository | Git Remote | Status |
|------------|------------|--------|
| marceausolutions.com | ✅ https://github.com/MarceauSolutions/marceausolutions.com.git | CONFIGURED |
| squarefoot-shipping-website | ✅ https://github.com/wmarceau/squarefoot-shipping-website.git | CONFIGURED |
| swflorida-comfort-hvac | ✅ https://github.com/MarceauSolutions/swflorida-comfort-hvac.git | CONFIGURED |
| website-legacy | ✅ https://github.com/MarceauSolutions/marceausolutions.com.git | CONFIGURED |
| website-repo-legacy | ✅ https://github.com/MarceauSolutions/marceausolutions.com.git | CONFIGURED |

**Status**: All website repos correctly configured ✅

### ✅ active-projects/ (Standalone GitHub Projects - 3 repos)

| Repository | Git Remote | Status |
|------------|------------|--------|
| fitness-influencer-backend | ✅ https://github.com/MarceauSolutions/fitness-influencer-backend.git | CONFIGURED |
| fitness-influencer-frontend | ✅ https://github.com/MarceauSolutions/fitness-influencer-frontend.git | CONFIGURED |
| square-foot-shipping | ⚠️ Need to check | CHECK NEEDED |

**Status**: 2 of 3 confirmed, 1 needs verification

---

## Impact Analysis

### What Works Now (No Issues)

**✅ dev-sandbox commits/pushes**:
```bash
cd ~/dev-sandbox
git add .
git commit -m "message"
git push  # ✅ Works - pushes to MarceauSolutions/dev-sandbox
```

**✅ website commits/pushes**:
```bash
cd ~/websites/marceausolutions.com
git add .
git commit -m "message"
git push  # ✅ Works - pushes to MarceauSolutions/marceausolutions.com
```

**✅ active-projects commits/pushes**:
```bash
cd ~/active-projects/fitness-influencer-backend
git add .
git commit -m "message"
git push  # ✅ Works - pushes to MarceauSolutions/fitness-influencer-backend
```

### What Doesn't Work (Needs Fixing)

**❌ production repo pushes (5 of 6)**:
```bash
cd ~/production/email-analyzer-prod
git add .
git commit -m "message"
git push  # ❌ FAILS - No remote configured
```

**Current behavior**: Commits work locally but cannot push to GitHub

---

## Root Cause

**Why production repos lack remotes**:

1. **deploy_to_skills.py behavior**:
   - Creates local git repo in production/
   - Commits changes locally
   - BUT does NOT automatically configure GitHub remote
   - Optional `--repo` flag exists but requires manual specification

2. **Historical deployments**:
   - Most production repos were deployed before GitHub integration was set up
   - Only crm-onboarding-prod has remote (likely deployed with `--repo` flag)

---

## Solution Options

### Option 1: Manual GitHub Remote Setup (Recommended for Existing Repos)

**For each production repo without a remote**:

```bash
# 1. Create GitHub repo (one-time, via GitHub web UI or gh CLI)
gh repo create MarceauSolutions/email-analyzer-prod --public

# 2. Add remote to local repo
cd ~/production/email-analyzer-prod
git remote add origin https://github.com/MarceauSolutions/email-analyzer-prod.git

# 3. Push existing commits
git push -u origin main
```

**Pros**:
- Full control over GitHub repo creation
- Can set repo visibility (public/private)
- Can add description, topics, etc.

**Cons**:
- Manual process for each repo
- Need to create GitHub repos first

### Option 2: Update deploy_to_skills.py Default Behavior

**Modify deployment script to automatically**:
1. Create GitHub repo (using gh CLI)
2. Configure remote
3. Push on deployment

**Pros**:
- Automated for future deployments
- Consistent remote configuration

**Cons**:
- Doesn't fix existing repos
- Requires gh CLI authentication
- May create repos user doesn't want on GitHub

### Option 3: Hybrid Approach (RECOMMENDED)

**For existing repos**: Use Option 1 (manual setup)
**For future repos**: Update deploy_to_skills.py to prompt for GitHub setup

**Benefits**:
- Clean up existing repos now
- Prevent issue for future deployments
- User choice for each deployment

---

## Action Plan

### Immediate Actions (Fix Existing Repos)

**Step 1: Decide which production repos need GitHub remotes**

Not all production repos may need to be on GitHub. Review each:

| Repo | Push to GitHub? | Reasoning |
|------|----------------|-----------|
| crm-onboarding-prod | ✅ Already done | N/A |
| email-analyzer-prod | ? | Decision needed |
| hvac-distributors-prod | ? | Decision needed |
| interview-prep-prod | ? | Decision needed |
| lead-scraper-prod | ? | Decision needed |
| time-blocks-prod | ? | Decision needed |

**Question for William**: Which production repos should be backed up to GitHub?

**Step 2: Create GitHub repos for selected repos**

Using GitHub CLI:
```bash
# For each repo you want on GitHub:
gh repo create MarceauSolutions/email-analyzer-prod --public --description "Email analyzer skill - production deployment"
```

Or via GitHub web UI:
1. Go to https://github.com/new
2. Create repo: MarceauSolutions/[repo-name]
3. Do NOT initialize with README (we have local commits)

**Step 3: Configure remotes**

```bash
# For each production repo:
cd ~/production/email-analyzer-prod
git remote add origin https://github.com/MarceauSolutions/email-analyzer-prod.git
git branch -M main  # Ensure branch is named 'main'
git push -u origin main
```

**Step 4: Verify square-foot-shipping**

```bash
cd ~/active-projects/square-foot-shipping
git remote -v
# If no remote, add it:
# git remote add origin https://github.com/MarceauSolutions/square-foot-shipping.git
# git push -u origin main
```

### Long-term Solution (Prevent Future Issues)

**Update deploy_to_skills.py** to include GitHub remote setup:

```python
def deploy_to_local_workspace(project_name: str, version: str = None, setup_github: bool = False):
    # ... existing code ...

    # NEW: Optional GitHub setup
    if setup_github:
        repo_name = f"{project_name}-prod"
        org = "MarceauSolutions"

        # Create GitHub repo using gh CLI
        subprocess.run([
            "gh", "repo", "create", f"{org}/{repo_name}",
            "--public",
            "--description", f"{config['skill_name']} - production deployment"
        ])

        # Add remote
        subprocess.run(["git", "remote", "add", "origin",
                       f"https://github.com/{org}/{repo_name}.git"],
                      cwd=workspace_path)

        # Push
        subprocess.run(["git", "push", "-u", "origin", "main"],
                      cwd=workspace_path)
```

**Usage**:
```bash
# Deploy with GitHub setup
python deploy_to_skills.py --project email-analyzer --version 1.1.0 --setup-github

# Deploy without GitHub (local only)
python deploy_to_skills.py --project email-analyzer --version 1.1.0
```

---

## Verification Commands

**Check all production repo remotes**:
```bash
for repo in ~/production/*-prod; do
  echo -e "\n📁 $(basename $repo):"
  cd "$repo" && git remote -v || echo "  No git repo"
done
```

**Check all website repo remotes**:
```bash
for repo in ~/websites/*; do
  echo -e "\n📁 $(basename $repo):"
  cd "$repo" && git remote -v || echo "  No git repo"
done
```

**Check all active-project repo remotes**:
```bash
for repo in ~/active-projects/*; do
  echo -e "\n📁 $(basename $repo):"
  cd "$repo" && git remote -v || echo "  No git repo"
done
```

**Test push to dev-sandbox**:
```bash
cd ~/dev-sandbox
git push --dry-run
# Should show: To https://github.com/MarceauSolutions/dev-sandbox.git
```

---

## Quick Setup Script (After GitHub Repos Created)

Save as `setup-production-remotes.sh`:

```bash
#!/bin/bash

# Setup GitHub remotes for production repos
# Run AFTER creating GitHub repos manually

REPOS=(
  "email-analyzer-prod"
  "hvac-distributors-prod"
  "interview-prep-prod"
  "lead-scraper-prod"
  "time-blocks-prod"
)

ORG="MarceauSolutions"

for repo in "${REPOS[@]}"; do
  echo "Setting up remote for $repo..."

  cd ~/production/$repo

  # Check if remote already exists
  if git remote | grep -q "origin"; then
    echo "  ✅ Remote already configured"
  else
    # Add remote
    git remote add origin "https://github.com/$ORG/$repo.git"

    # Ensure on main branch
    git branch -M main

    # Push
    git push -u origin main

    echo "  ✅ Remote configured and pushed"
  fi
done

echo -e "\n✅ All production remotes configured!"
```

**Usage**:
```bash
chmod +x setup-production-remotes.sh
./setup-production-remotes.sh
```

---

## Summary

**Current Status**:
- ✅ 1 category fully configured (dev-sandbox)
- ✅ 1 category fully configured (websites - 5/5 repos)
- ✅ 1 category mostly configured (active-projects - 2/3 repos)
- ⚠️ 1 category needs attention (production - 1/6 repos)

**Impact**:
- Development workflow: ✅ Works (dev-sandbox pushes fine)
- Website deployments: ✅ Works (all have remotes)
- Production deployments: ⚠️ Local only (cannot push to GitHub)

**Next Steps**:
1. **Decide**: Which production repos need GitHub remotes?
2. **Create**: GitHub repos for selected production deployments
3. **Configure**: Add remotes and push existing commits
4. **Update**: deploy_to_skills.py to prevent future issues (optional)

---

**References**:
- [deploy_to_skills.py](deploy_to_skills.py) - Deployment script
- [repository-management.md](docs/repository-management.md) - Git structure guide
- [GitHub CLI docs](https://cli.github.com/manual/gh_repo_create) - Creating repos

**Last updated**: 2026-01-21
