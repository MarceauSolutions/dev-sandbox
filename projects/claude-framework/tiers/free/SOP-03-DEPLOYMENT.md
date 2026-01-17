# SOP 3: Version Control & Deployment

**When**: Ready to deploy or release a new version

## Purpose

Ensure consistent versioning and deployment across all projects. Proper version control prevents confusion, enables rollbacks, and documents project history.

## Prerequisites

- Project initialized (SOP 1 complete)
- Code tested and working
- All changes committed (or ready to commit)

## Version Strategy

Use Semantic Versioning (semver):

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fixes only | Patch (x.y.Z) | 1.0.0 → 1.0.1 |
| New features (backwards compatible) | Minor (x.Y.0) | 1.0.1 → 1.1.0 |
| Breaking changes | Major (X.0.0) | 1.1.0 → 2.0.0 |

### Development Suffix

During development, use `-dev` suffix:
- `1.0.0-dev` → Currently developing
- `1.0.0` → Released version

## Steps

### Step 1: Verify Ready for Release

Before deploying, confirm:
- [ ] All tests pass (if applicable)
- [ ] Code reviewed (if applicable)
- [ ] No pending critical issues
- [ ] Documentation updated

### Step 2: Update VERSION File

```bash
# Check current version
cat VERSION
# Output: 1.0.0-dev

# Update to release version (remove -dev)
echo "1.0.0" > VERSION
```

### Step 3: Update CHANGELOG.md

Add entry for new version:

```markdown
## [1.0.0] - 2026-01-16

### Added
- Feature A: Description
- Feature B: Description

### Changed
- Updated X to do Y

### Fixed
- Bug in Z that caused W
```

**Changelog Categories**:
- `Added` - New features
- `Changed` - Changes to existing features
- `Deprecated` - Features to be removed
- `Removed` - Features removed
- `Fixed` - Bug fixes
- `Security` - Security fixes

### Step 4: Commit Release

```bash
git add VERSION CHANGELOG.md
git commit -m "release: v1.0.0"
git tag -a v1.0.0 -m "Version 1.0.0"
```

### Step 5: Deploy

Run your deployment process:

```bash
# Example: Copy to production directory
cp -r src/* /path/to/production/

# Or: Push to server
git push origin main --tags

# Or: Run deployment script
./deploy.sh
```

### Step 6: Verify Deployment

Confirm deployment succeeded:
- [ ] Application runs in production
- [ ] Key features work as expected
- [ ] No error logs

### Step 7: Bump to Next Dev Version

```bash
# Update to next development version
echo "1.1.0-dev" > VERSION

# Commit
git add VERSION
git commit -m "chore: bump to 1.1.0-dev"
```

## Quick Reference

```bash
# Full release cycle
cat VERSION                    # Check current: 1.0.0-dev
echo "1.0.0" > VERSION         # Set release version
# Update CHANGELOG.md manually
git add VERSION CHANGELOG.md
git commit -m "release: v1.0.0"
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin main --tags
# Deploy to production
echo "1.1.0-dev" > VERSION     # Next dev version
git add VERSION && git commit -m "chore: bump to 1.1.0-dev"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Forgot to update CHANGELOG | Add entry retroactively, amend commit |
| Wrong version number | `git tag -d v1.0.0` then recreate |
| Deploy failed | Roll back, fix issue, re-deploy |
| Missing VERSION file | Create it, set to appropriate version |

## Rollback Procedure

If deployment fails or causes issues:

```bash
# Revert to previous version
git checkout v0.9.0

# Or revert the release commit
git revert HEAD

# Redeploy previous version
./deploy.sh
```

## Success Criteria

- ✅ VERSION file shows release version (no -dev)
- ✅ CHANGELOG.md has complete entry for version
- ✅ Git tag created for version
- ✅ Deployment completed successfully
- ✅ VERSION bumped to next -dev

---

*Part of the Claude Development Framework - Free Tier*
