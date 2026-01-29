# Multi-Agent Git Workflow

## Problem
Multiple AI agents (Claude Code, Clawdbot, Ralph) work on dev-sandbox simultaneously, potentially causing conflicts when pushing to main.

## Current Situation
- **Clawdbot & Ralph**: Push directly to main branch
- **Claude Code**: Works in the same repository
- **Risk**: Overwriting each other's changes

## Safe Git Workflow (For Claude Code)

### Before Starting Work

```bash
# 1. Always fetch latest changes
git fetch origin main

# 2. Check if remote has new commits
git log HEAD..origin/main --oneline

# 3. If remote has changes, pull them first
git pull origin main --rebase
```

### Before Committing

```bash
# 1. Check if remote has new commits (Clawdbot/Ralph may have pushed)
git fetch origin main
git log HEAD..origin/main --oneline

# 2. If there are new commits, pull them
git pull origin main --rebase
```

### Before Pushing

```bash
# 1. Create backup branch (in case something goes wrong)
git branch backup-before-push-$(date +%Y%m%d-%H%M%S)

# 2. Fetch and check for conflicts
git fetch origin main
git log HEAD..origin/main --oneline

# 3. If remote has changes, integrate them
git pull origin main --rebase

# 4. Dry run to verify
git push --dry-run origin main

# 5. If dry run succeeds, push for real
git push origin main
```

### If Conflicts Occur

```bash
# 1. Restore from backup
git reset --hard backup-before-push-YYYYMMDD-HHMMSS

# 2. Pull with rebase
git pull origin main --rebase

# 3. Resolve conflicts manually
# Edit conflicted files, then:
git add <conflicted-files>
git rebase --continue

# 4. Push after resolving
git push origin main
```

## Future Improvement: Feature Branches

### Recommended Approach for Large Changes

```bash
# 1. Create feature branch
git checkout -b feature/claude-code-$(date +%Y%m%d)

# 2. Make commits on feature branch
git add .
git commit -m "feat: ..."

# 3. Before merging, update main
git checkout main
git pull origin main

# 4. Rebase feature branch on latest main
git checkout feature/claude-code-$(date +%Y%m%d)
git rebase main

# 5. Merge to main (fast-forward)
git checkout main
git merge --ff-only feature/claude-code-$(date +%Y%m%d)

# 6. Push
git push origin main

# 7. Delete feature branch
git branch -d feature/claude-code-$(date +%Y%m%d)
```

## Agent Coordination

### Option 1: Branch Strategy (Recommended Long-term)
- **Clawdbot**: Works on `clawdbot/` prefix branches
- **Ralph**: Works on `ralph/` prefix branches
- **Claude Code**: Works on `feature/` prefix branches
- **Merge**: All agents create PRs → William reviews → Merge to main

### Option 2: Time-Based Coordination
- **Clawdbot**: Pushes between 00:00-06:00 (overnight)
- **Ralph**: Pushes between 06:00-12:00 (morning)
- **Claude Code**: Pushes between 12:00-23:59 (afternoon/evening)

### Option 3: Lock File (Simple)
- Create `.git-lock` file before starting work
- Check for `.git-lock` before making commits
- Remove `.git-lock` after pushing

## Communication Pattern

**William says**: "Check if Clawdbot or Ralph pushed recently"

**Claude does**:
```bash
git fetch origin main
git log origin/main --oneline -10 --author="clawdbot\|ralph" --since="24 hours ago"
```

## Emergency Recovery

### If Push Overwrote Changes

```bash
# 1. GitHub has reflog, find the lost commit
git reflog origin/main

# 2. Reset to previous state
git reset --hard origin/main@{1}

# 3. Cherry-pick lost commits
git cherry-pick <lost-commit-sha>

# 4. Push with force (only if necessary)
git push --force-with-lease origin main
```

## Best Practices

1. ✅ **Always** fetch before starting work
2. ✅ **Always** create backup branch before pushing
3. ✅ **Always** do a dry-run push first
4. ✅ **Check** git log for Clawdbot/Ralph commits in last 24h
5. ❌ **Never** use `git push --force` without William's approval
6. ✅ **Communicate** with William if conflicts detected

## Status Checking Commands

```bash
# Check who committed recently
git log --oneline -20 --pretty=format:"%h %an %ar: %s"

# Check if we're behind remote
git fetch origin main && git log HEAD..origin/main --oneline

# Check if we're ahead of remote
git log origin/main..HEAD --oneline

# See diverged commits (both behind and ahead)
git log --oneline --left-right HEAD...origin/main
```

## EC2 Conflict Prevention Script

The `/home/clawdbot/scripts/commit-and-push.sh` script implements these safeguards:

```bash
# Key features:
# 1. Fetches before any changes
# 2. Creates backup branch
# 3. Pulls with rebase
# 4. Dry-run push before actual push
# 5. Logs all operations

# Usage on EC2:
/home/clawdbot/scripts/commit-and-push.sh "clawdbot-outputs/" "Auto: description"
```

## Last Updated
2026-01-29
