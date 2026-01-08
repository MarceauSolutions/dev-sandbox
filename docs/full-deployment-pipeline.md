# Full Deployment Pipeline

## Overview

Each project has two deployment targets that are deployed separately:

```
DEV-SANDBOX (Development)
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────────┐               ┌─────────────────────┐
│   SKILL DEPLOYMENT  │               │ FRONTEND DEPLOYMENT │
│   (Claude Code)     │               │     (Railway)       │
├─────────────────────┤               ├─────────────────────┤
│ • .claude/skills/   │               │ • Web UI            │
│ • Chat interaction  │               │ • API endpoints     │
│ • Personal use +    │               │ • Public access     │
│   external users    │               │                     │
└─────────────────────┘               └─────────────────────┘
         │                                         │
         │  Test in chat                           │  Test in browser
         ▼                                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION READY                          │
└─────────────────────────────────────────────────────────────┘
```

## The Three-Phase Pipeline

### Phase 1: Skill Deployment (Chat-First)

New features start as skill capabilities tested via Claude Code chat.

**Steps:**
1. Develop feature in `project/src/`
2. Update SKILL.md with new capabilities
3. Test locally with scripts
4. Deploy to skill: `python deploy_to_skills.py --project <name> --version X.Y.0`
5. Test in Claude Code chat
6. Bump to next dev version: `X.Y+1.0-dev`

**Command:**
```bash
# Deploy skill only
python deploy_to_skills.py --project interview-prep --version 1.2.0
```

### Phase 2: Frontend Integration

Once skill features are validated, integrate them into the web frontend.

**Steps:**
1. Design UI for the new capability
2. Add API endpoints to `src/api.py` (or equivalent)
3. Update frontend HTML/JS to call new endpoints
4. Test locally: `python src/api.py` + open browser
5. Deploy frontend: `railway up` or git push to Railway

**Command:**
```bash
# Test frontend locally
cd interview-prep-pptx && python src/api.py

# Deploy to Railway (after testing)
railway up
# OR
git add -A && git commit -m "feat: Add X to frontend" && git push
```

### Phase 3: Full Production

Both skill and frontend are live and synchronized.

---

## Deployment Commands Reference

### Skill Deployment
```bash
# Check current status
python deploy_to_skills.py --status interview-prep

# Deploy specific version
python deploy_to_skills.py --project interview-prep --version 1.2.0

# Sync scripts to execution/ (without version bump)
python deploy_to_skills.py --sync-execution --project interview-prep

# List all versions
python deploy_to_skills.py --project interview-prep --versions

# Rollback
python deploy_to_skills.py --project interview-prep --rollback 1.1.0
```

### Frontend Deployment
```bash
# Test locally
cd interview-prep-pptx && python src/api.py
# Open http://localhost:8000

# Deploy to Railway (if Railway CLI installed)
cd interview-prep-pptx && railway up

# OR deploy via git push (if Railway connected to repo)
git add -A && git commit -m "feat: Frontend update" && git push
```

### Full Deployment (Both)
```bash
# 1. Deploy skill first
python deploy_to_skills.py --project interview-prep --version 1.2.0

# 2. Test in Claude Code chat
# (manual verification)

# 3. Deploy frontend
cd interview-prep-pptx && railway up

# 4. Bump to next dev version
echo "1.3.0-dev" > interview-prep-pptx/VERSION

# 5. Commit
git add -A && git commit -m "chore: Deploy v1.2.0 (skill + frontend)"
```

---

## Feature Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FEATURE LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DEVELOP                                                              │
│     └── Write code in project/src/                                       │
│     └── Test locally with scripts                                        │
│     └── Update SKILL.md with new capability                              │
│                                                                          │
│  2. DEPLOY SKILL (v1.2.0)                                                │
│     └── python deploy_to_skills.py --project X --version 1.2.0           │
│     └── Test in Claude Code chat                                         │
│     └── Fix issues if needed                                             │
│                                                                          │
│  3. INTEGRATE FRONTEND (if applicable)                                   │
│     └── Add API endpoints for new feature                                │
│     └── Update frontend UI                                               │
│     └── Test locally: python src/api.py                                  │
│                                                                          │
│  4. DEPLOY FRONTEND                                                      │
│     └── railway up OR git push                                           │
│     └── Test in browser                                                  │
│                                                                          │
│  5. FINALIZE                                                             │
│     └── Bump VERSION to 1.3.0-dev                                        │
│     └── Update CHANGELOG.md                                              │
│     └── Commit all changes                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Project-Specific Notes

### Interview Prep

| Target | Location | Deploy Command |
|--------|----------|----------------|
| Skill | `.claude/skills/interview-prep/` | `python deploy_to_skills.py --project interview-prep --version X.Y.Z` |
| Frontend | Railway (interview-prep-pptx) | `cd interview-prep-pptx && railway up` |
| API | `interview-prep-pptx/src/api.py` | Auto-deployed with frontend |

**Current Frontend Capabilities:**
- PowerPoint generation
- Slide editing (add/edit text)
- Download PPTX

**Skill-Only Capabilities (not in frontend yet):**
- Mock interviews
- PDF outputs (cheat sheets, flashcards, etc.)
- Intent routing

### Fitness Influencer

| Target | Location | Deploy Command |
|--------|----------|----------------|
| Skill | `.claude/skills/fitness-influencer-operations/` | `python deploy_to_skills.py --project fitness-influencer --version X.Y.Z` |
| Frontend | `projects/fitness-influencer/frontend/` | TBD |

### Amazon Seller

| Target | Location | Deploy Command |
|--------|----------|----------------|
| Skill | `.claude/skills/amazon-seller-operations/` | `python deploy_to_skills.py --project amazon-seller --version X.Y.Z` |
| Frontend | TBD | TBD |

### Personal Assistant

| Target | Location | Deploy Command |
|--------|----------|----------------|
| Skill | `.claude/skills/personal-assistant/` | Local only - no external deploy |
| Frontend | **None** | N/A (Claude Code chat only) |

---

## Quick Reference: "Deploy Everything"

When you say "deploy interview-prep" or "deploy this project", here's the full sequence:

```bash
# 1. Update CHANGELOG
# (Edit interview-prep-pptx/CHANGELOG.md with changes)

# 2. Set version
echo "1.2.0" > interview-prep-pptx/VERSION

# 3. Deploy skill
python deploy_to_skills.py --project interview-prep --version 1.2.0

# 4. Test in chat (manual)

# 5. Deploy frontend (if changes)
cd interview-prep-pptx && railway up

# 6. Test in browser (manual)

# 7. Bump to next dev
echo "1.3.0-dev" > interview-prep-pptx/VERSION

# 8. Commit
git add -A && git commit -m "$(cat <<'EOF'
chore: Deploy interview-prep v1.2.0

- Skill deployed to .claude/skills/
- Frontend deployed to Railway

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## MCP Server Decision Matrix

**MCP servers are token-intensive.** Before enabling MCP in a deployment, evaluate:

| Deployment Type | Use MCP? | Reason |
|-----------------|----------|--------|
| **External/shared AI assistants** | YES | Standardization benefits outweigh token costs |
| **Personal/internal tools** | EVALUATE | Custom scripts may be more cost-effective |
| **Rate-limited APIs** | YES | Automatic rate limiting is valuable (e.g., amazon-sp-api) |
| **High-frequency operations** | NO | Direct scripts are more token-efficient |
| **Web search** | NO | Claude's built-in search is sufficient |
| **Filesystem operations** | NO | Native Claude tools are more efficient |

### MCP Recommendations by Project

| Project | MCP Servers to Enable | Reason |
|---------|----------------------|--------|
| Interview Prep (deployed) | google-sheets, google-drive | User data storage for shared product |
| Interview Prep (personal) | NONE | Use Python scripts |
| Amazon Seller | amazon-sp-api | Rate limiting critical |
| Personal Assistant | amazon-sp-api only | Scripts for everything else |
| Fitness Influencer (deployed) | google-sheets | User data tracking |

**Config location:** `.claude/mcp-servers/mcp-config.json`

**Rule of thumb:**
- Building for yourself → use Python scripts in `execution/`
- Deploying for others → consider MCP for standardization

---

## Deployment Checklist

Before any deployment:

### Pre-Deployment Verification
- [ ] All changes committed to feature branch (no uncommitted work)
- [ ] `.env` variables verified (no missing keys for new features)
- [ ] No hardcoded secrets or API keys in code
- [ ] Dependencies up to date (`requirements.txt`, `package.json`)

### Skill Deployment
- [ ] All scripts tested locally with real inputs
- [ ] Error handling tested (bad inputs, API failures)
- [ ] SKILL.md updated with new capabilities
- [ ] VERSION file set to release version (not -dev)
- [ ] CHANGELOG.md updated with user-facing changes
- [ ] **MCP decision made** (see matrix above)
- [ ] Execution scripts synced to `execution/` directory
- [ ] Workflow files updated if flow changed

### Frontend Deployment
- [ ] API endpoints tested locally (`python src/api.py`)
- [ ] All new endpoints have error handling
- [ ] Frontend UI tested in browser (all user flows)
- [ ] No console errors (check browser dev tools)
- [ ] Mobile responsive (if applicable)
- [ ] Loading states work correctly
- [ ] Error messages display properly to users

### Security Review
- [ ] No credentials in code (use environment variables)
- [ ] User inputs sanitized/validated
- [ ] API endpoints protected (if authentication required)
- [ ] File uploads validated (if applicable)

### Post-Deployment
- [ ] Test skill in Claude Code chat (run each capability)
- [ ] Test frontend in browser (complete a full workflow)
- [ ] VERSION bumped to next -dev
- [ ] Changes committed to git with deployment tag
- [ ] Rollback tested or rollback plan documented
- [ ] Monitor for errors in first hour

### Documentation
- [ ] README updated if setup steps changed
- [ ] API documentation current (if public endpoints)
- [ ] User-facing help text accurate

---

## Rollback Procedures

### Skill Rollback
```bash
python deploy_to_skills.py --project interview-prep --rollback 1.1.0
```

### Frontend Rollback
```bash
# Railway keeps deployment history
railway rollback

# OR revert git commit and redeploy
git revert HEAD
git push
```
