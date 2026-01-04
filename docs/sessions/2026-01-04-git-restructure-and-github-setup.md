# Session: 2026-01-04 - Git Restructure & GitHub Repository Setup

**Date**: 2026-01-04
**Focus**: Fixed git repository structure issues, pushed repos to GitHub organization, and established session memory system

## Decisions Made

- **Restructured git repositories**: Moved from single home directory repo to individual project repos
  - Rationale: Home directory tracking caused performance issues and "too many active changes" warnings

- **Use MarceauSolutions organization for production repos**: All production code goes to organization, not personal account
  - Rationale: Better organization structure, easier team collaboration in future

- **Established session memory system**: Created docs/sessions/ for cross-session knowledge persistence
  - Rationale: Prevent re-explaining context each session, similar to how we save workflows as Python scripts

## System Configuration Changes

### Git Repository Restructure

- **Home Directory Git Tracking Removed**
  - Before: `/Users/williammarceaujr./` was a git repository tracking everything
  - After: Moved `.git` to `.git.backup`, each project is now independent
  - Impact: No more "too many active changes" warnings

- **dev-sandbox as Standalone Repo**
  - Created: New git repository at `/Users/williammarceaujr./dev-sandbox`
  - Remote: `https://github.com/MarceauSolutions/dev-sandbox.git`
  - Status: Private repository in MarceauSolutions organization

- **crm-onboarding-prod Pushed to GitHub**
  - Created: Initial commit and pushed to GitHub
  - Remote: `https://github.com/MarceauSolutions/crm-onboarding-prod.git`
  - Status: Private repository in MarceauSolutions organization

### GitHub CLI Setup

- **Installed GitHub CLI (`gh`)**
  - Command: `brew install gh`
  - Purpose: Create and manage repositories from terminal
  - Authentication: Completed via `gh auth login`

## Key Learnings & Discoveries

- **Padlock Icon on GitHub = Private Repository**
  - Context: User saw padlock next to repo name and thought it wasn't showing up
  - Meaning: 🔒 = Private (only you and collaborators can see), 🌐 = Public (anyone can see)
  - Important: Private repos don't appear in public searches, requires login to view

- **GitHub Desktop Categories Based on Remote URL**
  - MarceauSolutions section: Repos with `https://github.com/MarceauSolutions/...`
  - wmarceau section: Repos with `https://github.com/wmarceau/...`
  - Other section: Repos with no remote or unrecognized organization

- **Git Remote URL Determines Repository Owner**
  - Personal account: `https://github.com/USERNAME/repo-name.git`
  - Organization: `https://github.com/ORGANIZATION/repo-name.git`
  - Set with: `git remote set-url origin [URL]`

## Workflows & Scripts Created

### Session Memory System

- **Location**: `docs/sessions/`
- **Template**: [TEMPLATE.md](TEMPLATE.md)
- **Purpose**: Act as persistent memory across sessions, preventing need to re-explain configurations, decisions, and learnings
- **Usage**: Create new session file for each significant work session using template

## Gotchas & Solutions

- **Issue**: Git repository at home directory level causing performance warnings
  - Solution: Move `.git` to `.git.backup`, initialize individual project repos
  - Prevention: Never initialize git at home directory level

- **Issue**: Confusion about where repositories are pushed (personal vs organization)
  - Solution: Always check `git remote -v` to see current remote URL
  - Prevention: Be explicit when creating repos using `gh repo create ORG/name` or `USERNAME/name`

- **Issue**: GitHub CLI error "Unable to add remote 'origin'" when repo already has remote
  - Solution: Create repo without `--remote=origin` flag if remote already exists
  - Command: `gh repo create ORG/name --private` then `git push -u origin main`

## Commands & Shortcuts

```bash
# Check where repository will push to
git remote -v

# Push to personal account (create repo on GitHub first or use gh)
git remote set-url origin https://github.com/wmarceau/repo-name.git
git push -u origin main

# Push to organization account
git remote set-url origin https://github.com/MarceauSolutions/repo-name.git
git push -u origin main

# Create repository on GitHub via CLI (after gh auth login)
gh repo create MarceauSolutions/repo-name --private --description "Description here"

# Check git repository root
git rev-parse --show-toplevel

# Install GitHub CLI
brew install gh

# Authenticate GitHub CLI
gh auth login
```

## File Structure Created

```
dev-sandbox/
├── docs/
│   └── sessions/
│       ├── TEMPLATE.md                                    # Template for future sessions
│       ├── 2026-01-04-git-restructure-and-github-setup.md # This file
│       └── README.md                                      # Index of all sessions (to be created)
```

## Next Steps / Follow-ups

- [ ] If needed: Delete `.git.backup` from home directory after confirming everything works
- [ ] Future sessions: Create new session file using TEMPLATE.md
- [ ] Update session index when adding new session files

## References

- GitHub Repository: [dev-sandbox](https://github.com/MarceauSolutions/dev-sandbox)
- GitHub Repository: [crm-onboarding-prod](https://github.com/MarceauSolutions/crm-onboarding-prod)
- GitHub CLI Docs: [cli.github.com](https://cli.github.com)
