# SOP 03 — Deployment

> Checklist for deploying code to production.

## Pre-Deploy Verification
- [ ] All tests pass
- [ ] No uncommitted changes: `git status`
- [ ] Code reviewed (self-review at minimum)
- [ ] Configuration/secrets are in .env, not hardcoded
- [ ] CLAUDE.md updated with any new files or changes

## Deploy Steps
1. Commit all changes with descriptive message
2. Push to remote: `git push origin main`
3. Deploy to target platform (platform-specific steps)
4. Verify deployment succeeded

## Post-Deploy Verification
- [ ] Application starts without errors
- [ ] Core functionality works (manual smoke test)
- [ ] Logs show no errors
- [ ] User can access the deployment
- [ ] Health check passes: `python scripts/health_check.py`

## Rollback
If deployment fails, see SOP 07 (Rollback).
