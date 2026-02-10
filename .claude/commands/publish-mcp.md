Publish or update an MCP package. Follow these SOPs in sequence:

**First time publishing:**
1. `docs/sops/sop-11-mcp-structure.md` — Create package structure
2. `docs/sops/sop-12-pypi.md` — Publish to PyPI
3. `docs/sops/sop-13-registry.md` — Publish to Claude MCP Registry

**Updating existing MCP:**
1. `docs/sops/sop-14-mcp-update.md` — Version bump + republish

Project to publish: $ARGUMENTS

Key checks:
- All 3 version files must match (pyproject.toml, server.json, __init__.py)
- PyPI upload must succeed before MCP Registry publish
- README must have `mcp-name:` line for ownership verification
