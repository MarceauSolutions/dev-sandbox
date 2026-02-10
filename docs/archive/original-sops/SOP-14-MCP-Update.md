<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 14: MCP Update & Version Bump

**When**: Updating an MCP that's already published to PyPI and the Claude MCP Registry

**Purpose**: Push code changes to an existing MCP while maintaining version consistency across all systems

**Agent**: Claude Code (REQUIRED - publishing credentials). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ MCP already published (SOPs 11-13 completed previously)
- ✅ Code changes made and tested in dev-sandbox
- ✅ PyPI credentials available

**Version Bump Rules**:

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fixes only | Patch (x.y.Z) | 1.0.0 → 1.0.1 |
| New features (backwards compatible) | Minor (x.Y.0) | 1.0.1 → 1.1.0 |
| Breaking changes | Major (X.0.0) | 1.1.0 → 2.0.0 |

**Files That Must Be Updated** (all 3 must match):

1. `pyproject.toml` - Line: `version = "X.Y.Z"`
2. `server.json` - Line: `"version": "X.Y.Z"`
3. `src/[project]_mcp/__init__.py` - Line: `__version__ = "X.Y.Z"`

**Steps**:

**1. Make Code Changes**
```bash
# Edit files in the package directory
cd projects/[project]/src/[project]_mcp/
# Make your changes to server.py, modules, etc.
```

**2. Test Changes Locally**
```bash
# Test the MCP server works
cd projects/[project]
python -m src.[project]_mcp.server
# Or run your test suite
```

**3. Determine New Version**

Check current published version:
```bash
pip index versions [project]-mcp
# Shows: [project]-mcp (1.0.0)
```

Decide bump type based on changes:
- Bug fix → 1.0.0 → 1.0.1
- New feature → 1.0.0 → 1.1.0
- Breaking change → 1.0.0 → 2.0.0

**4. Update Version in All 3 Files**

```bash
# Update pyproject.toml
sed -i '' 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml

# Update server.json
sed -i '' 's/"version": "1.0.0"/"version": "1.0.1"/' server.json

# Update __init__.py
sed -i '' 's/__version__ = "1.0.0"/__version__ = "1.0.1"/' src/[project]_mcp/__init__.py
```

Or edit manually - just ensure all 3 match exactly.

**5. Update CHANGELOG.md**

```markdown
## [1.0.1] - 2026-01-14

### Fixed
- Description of bug fix

### Changed
- Description of changes

### Added
- Description of new features
```

**6. Clean and Rebuild**

```bash
cd projects/[project]
rm -rf dist/ build/ *.egg-info
python -m build
```

Verify build:
```
Successfully built [project]_mcp-1.0.1.tar.gz and [project]_mcp-1.0.1-py3-none-any.whl
```

**7. Upload to PyPI**

```bash
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN
```

Or if using `~/.pypirc`:
```bash
python -m twine upload dist/*
```

**8. Republish to MCP Registry**

```bash
# Re-authenticate if needed (token expires after ~1 hour)
/path/to/mcp-publisher login github

# Publish updated version
cd projects/[project]
/path/to/mcp-publisher publish --server server.json
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.[username]/[project] version 1.0.1
```

**9. Commit Changes to dev-sandbox**

```bash
cd /Users/williammarceaujr./dev-sandbox
git add projects/[project]/
git commit -m "feat([project]): Bump to v1.0.1 - [description of changes]"
git push
```

**10. Verify Update**

```bash
# Check PyPI shows new version
pip index versions [project]-mcp
# Should show: [project]-mcp (1.0.1, 1.0.0)

# Test installation
pip install --upgrade [project]-mcp
python -c "from [project]_mcp import __version__; print(__version__)"
# Should print: 1.0.1
```

**Quick Update Workflow** (copy-paste ready):

```bash
# Set variables
PROJECT="md-to-pdf"
OLD_VERSION="1.0.1"
NEW_VERSION="1.0.2"
PYPI_TOKEN="pypi-YOUR_TOKEN"

# Update versions
cd /Users/williammarceaujr./dev-sandbox/projects/$PROJECT
sed -i '' "s/version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i '' "s/\"version\": \"$OLD_VERSION\"/\"version\": \"$NEW_VERSION\"/" server.json
sed -i '' "s/__version__ = \"$OLD_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/${PROJECT//-/_}_mcp/__init__.py

# Build and publish
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN

# Update MCP Registry
/Users/williammarceaujr./dev-sandbox/projects/registry/bin/mcp-publisher publish --server server.json
```

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `File already exists` on PyPI | Version not bumped - check all 3 files |
| `Version mismatch` on Registry | server.json version must match PyPI exactly |
| `401 Unauthorized` | Re-run `mcp-publisher login github` |
| Build includes old version | Delete `dist/`, `build/`, `*.egg-info` before rebuild |

**Version Mismatch Detection**:

```bash
# Check all versions match
echo "pyproject.toml: $(grep 'version = ' pyproject.toml)"
echo "server.json: $(grep '"version"' server.json)"
echo "__init__.py: $(grep '__version__' src/*_mcp/__init__.py)"
```

All three should show the same version number.

**Success Criteria**:
- ✅ All 3 version files updated and matching
- ✅ CHANGELOG.md updated
- ✅ PyPI shows new version
- ✅ MCP Registry shows new version
- ✅ `pip install --upgrade` pulls new version
- ✅ Changes committed to dev-sandbox

**References**:
- SOP 12: PyPI Publishing (initial publish)
- SOP 13: MCP Registry Publishing (initial publish)
- Semantic Versioning: https://semver.org

