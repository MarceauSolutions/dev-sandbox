# SOP 12: PyPI Publishing

**When**: Publishing an MCP package to PyPI (AFTER SOP 11 complete)

**Purpose**: Make your MCP installable via `pip install [project]-mcp`

**Agent**: Claude Code (REQUIRED - PyPI credentials on Mac). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ SOP 11 complete (package structure created)
- ✅ PyPI account created at https://pypi.org
- ✅ PyPI API token generated

**One-Time Setup** (first time only):

1. **Create PyPI Account**: https://pypi.org/account/register/
2. **Generate API Token**: https://pypi.org/manage/account/token/
   - Scope: Entire account (for multiple projects) OR per-project
   - Save token securely (starts with `pypi-`)

3. **Install build tools**:
```bash
pip install build twine
```

**Steps**:

**1. Clean Previous Builds**
```bash
cd projects/[project]
rm -rf dist/ build/ *.egg-info
```

**2. Build Package**
```bash
python -m build
```

Expected output:
```
Successfully built [project]_mcp-1.0.0.tar.gz and [project]_mcp-1.0.0-py3-none-any.whl
```

**3. Verify Build Contents**
```bash
# Check wheel contents
unzip -l dist/*.whl

# Should show your package files:
# [project]_mcp/__init__.py
# [project]_mcp/server.py
# [project]_mcp/module.py
```

**4. Upload to PyPI**
```bash
python -m twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN_HERE
```

**5. Verify on PyPI**
- Visit: `https://pypi.org/project/[project]-mcp/`
- Should show your package with version, description, and files

**Version Bumping** (for updates):

If you need to publish an update:
1. Version in `pyproject.toml` MUST be higher than PyPI
2. Version in `server.json` should match
3. Version in `__init__.py` should match
4. PyPI does NOT allow re-uploading same version

```bash
# If 1.0.0 already exists on PyPI, bump to 1.0.1
# Update all three files, then rebuild and upload
```

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `File already exists` | Bump version (can't re-upload same version) |
| `Invalid credentials` | Check token starts with `pypi-` and use `__token__` as username |
| `Package not found in wheel` | Check `[tool.hatch.build.targets.wheel]` path in pyproject.toml |
| `ModuleNotFoundError` | Check package directory name matches pyproject.toml |

**Stored Credentials** (optional):

Create `~/.pypirc` to avoid entering token each time:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

Then upload with just:
```bash
python -m twine upload dist/*
```

**Success Criteria**:
- ✅ Build completes without errors
- ✅ Package visible at `https://pypi.org/project/[project]-mcp/`
- ✅ `pip install [project]-mcp` works in fresh environment

**Next Step**: SOP 13 (MCP Registry Publishing)

**References**:
- PyPI: https://pypi.org
- Twine docs: https://twine.readthedocs.io
