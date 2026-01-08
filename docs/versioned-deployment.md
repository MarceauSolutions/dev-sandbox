# Versioned Deployment Pipeline

## The Problem

When developing AI assistants, you need to:
1. Deploy a working version to production (Claude Skills)
2. Continue developing new features in dev-sandbox
3. Push updates without breaking what's already working
4. Track which version is in production vs development

This is how companies like Anthropic ship Claude 3.5, Claude Opus 4.5, etc. - each version has specific capabilities, and updates are deliberate.

## The Solution: Version-Tagged Deployments

```
DEV-SANDBOX (Development)              PRODUCTION (Claude Skills)
┌────────────────────────┐             ┌────────────────────────┐
│                        │             │                        │
│  interview-prep-pptx/  │  deploy     │  .claude/skills/       │
│  ├── src/              │ ────────>   │  └── interview-prep/   │
│  ├── workflows/        │  v1.0.0     │      ├── SKILL.md      │
│  └── CHANGELOG.md      │             │      └── VERSION       │
│                        │             │                        │
│  [Continue developing] │             │  [Stable in prod]      │
│  v1.1.0-dev            │             │  v1.0.0                │
│                        │             │                        │
└────────────────────────┘             └────────────────────────┘
         │                                       │
         │  When ready                           │
         └───────────────────────────────────────┘
                    deploy v1.1.0
```

## Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fix, small tweak | PATCH | 1.0.0 → 1.0.1 |
| New feature, capability | MINOR | 1.0.0 → 1.1.0 |
| Breaking change, major redesign | MAJOR | 1.0.0 → 2.0.0 |

## Workflow

### Step 1: Tag Current Version Before Changes

Before making changes to a deployed project:

```bash
# Check current version
cat interview-prep-pptx/VERSION

# If no VERSION file, create one
echo "1.0.0" > interview-prep-pptx/VERSION
```

### Step 2: Develop in Dev-Sandbox

Make all changes in dev-sandbox:
- Edit scripts in `project/src/`
- Update workflows in `project/workflows/`
- Test locally

### Step 3: Update CHANGELOG

Document what changed:

```markdown
# CHANGELOG.md

## [1.1.0] - 2026-01-09

### Added
- User guidance prompts at each workflow stage
- Download to ~/Downloads functionality
- Inference guidelines for scope extension

### Changed
- Theme color updated to #1A1A2E (dark navy)
- "Relevance:" label now Adobe red (#EC1C24)

### Fixed
- PowerPoint now closes before reopening updated version
```

### Step 4: Bump Version

```bash
# Update VERSION file
echo "1.1.0" > interview-prep-pptx/VERSION

# Update SKILL.md header (optional but recommended)
# Add: version: 1.1.0
```

### Step 5: Deploy New Version

```bash
python deploy_to_skills.py --project interview-prep --version 1.1.0
```

This will:
1. Create a VERSION file in the deployed skill
2. Tag the git commit with the version
3. Update SKILL.md with version info
4. Push to production

### Step 6: Continue Development

After deploying, immediately bump to next dev version:

```bash
echo "1.2.0-dev" > interview-prep-pptx/VERSION
```

Now you can continue developing without affecting production.

## File Structure Per Project

```
interview-prep-pptx/
├── VERSION              # Current version (e.g., "1.1.0" or "1.2.0-dev")
├── CHANGELOG.md         # History of all versions
├── SKILL.md             # Includes version in header
├── src/
├── workflows/
└── USER_PROMPTS.md
```

## Commands Reference

```bash
# Check what version is deployed
python deploy_to_skills.py --status interview-prep

# Deploy specific version
python deploy_to_skills.py --project interview-prep --version 1.1.0

# Deploy latest (auto-reads VERSION file)
python deploy_to_skills.py --project interview-prep --deploy

# Rollback to previous version
python deploy_to_skills.py --project interview-prep --rollback 1.0.0

# List all versions
python deploy_to_skills.py --project interview-prep --versions
```

## Deployment Checklist

Before deploying a new version:

- [ ] All features tested locally
- [ ] CHANGELOG.md updated with changes
- [ ] VERSION file bumped
- [ ] SKILL.md updated with new capabilities
- [ ] Workflows documented for new features
- [ ] No breaking changes (or MAJOR version bump if so)

## Example: Deploying Interview Prep v1.1.0

```bash
# 1. Ensure everything is tested
python execution/pptx_editor.py --input .tmp/test.pptx --action list

# 2. Update changelog
# Edit interview-prep-pptx/CHANGELOG.md

# 3. Set version
echo "1.1.0" > interview-prep-pptx/VERSION

# 4. Sync scripts to execution/
python deploy_to_skills.py --sync-execution --project interview-prep

# 5. Deploy
python deploy_to_skills.py --project interview-prep --version 1.1.0

# 6. Bump to next dev version
echo "1.2.0-dev" > interview-prep-pptx/VERSION

# 7. Commit
git add -A && git commit -m "chore: Deploy interview-prep v1.1.0, start v1.2.0-dev"
```

## Rollback Procedure

If a deployment has issues:

```bash
# 1. Check previous versions
python deploy_to_skills.py --project interview-prep --versions

# 2. Rollback to stable version
python deploy_to_skills.py --project interview-prep --rollback 1.0.0

# 3. Fix issues in dev-sandbox
# ... make fixes ...

# 4. Deploy fixed version
python deploy_to_skills.py --project interview-prep --version 1.0.1
```

## Production vs Development Tracking

| Location | Purpose | Version |
|----------|---------|---------|
| `interview-prep-pptx/VERSION` | Dev version | 1.2.0-dev |
| `.claude/skills/interview-prep/VERSION` | Production version | 1.1.0 |
| GitHub releases | Version history | All tags |

## Integration with Claude Skills

When deployed, the SKILL.md header includes version:

```yaml
---
name: interview-prep
description: Interview Prep PowerPoint Generator
version: 1.1.0
last_deployed: 2026-01-09
trigger_phrases:
  - interview prep
  - create interview presentation
...
---
```

This allows Claude to know which version is running and what capabilities are available.

## User Communication

When a user asks "what can you do?", the assistant can reference the version:

```
I'm running Interview Prep Assistant v1.1.0.

New in this version:
• User guidance prompts at each stage
• Download to Downloads folder
• Consistent dark navy theme (#1A1A2E)
• Adobe red "Relevance:" labels

What would you like to do?
```
