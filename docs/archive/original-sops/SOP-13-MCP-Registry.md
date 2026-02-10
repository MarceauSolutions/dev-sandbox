<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 13: MCP Registry Publishing

**When**: Publishing to Claude's MCP Registry (AFTER SOP 12 complete - package must be on PyPI first)

**Purpose**: Make your MCP discoverable in Claude's marketplace and installable via Claude Desktop

**Agent**: Claude Code (REQUIRED - mcp-publisher uses Mac auth). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ SOP 11 complete (package structure)
- ✅ SOP 12 complete (package live on PyPI)
- ✅ GitHub account (for authentication)
- ✅ `mcp-publisher` CLI installed

**One-Time Setup** (first time only):

1. **Install mcp-publisher**:
```bash
# Requires Go installed
brew install go  # macOS

# Clone and build
git clone https://github.com/modelcontextprotocol/registry.git
cd registry
go build -o bin/mcp-publisher ./cmd/mcp-publisher
```

Or download pre-built binary from releases.

2. **Authenticate with GitHub**:
```bash
./bin/mcp-publisher login github
```

This opens a browser for GitHub device flow authentication:
- Go to: https://github.com/login/device
- Enter the code shown in terminal
- Authorize the application

**Token expires** after ~1 hour. Re-run `login github` if you see `401 Unauthorized` or `token expired`.

**Steps**:

**1. Verify Prerequisites**
```bash
# Check PyPI package exists
pip index versions [project]-mcp
# Should show: [project]-mcp (1.0.0)

# Check server.json exists and is valid
cat projects/[project]/server.json | python -m json.tool

# Check README has mcp-name line
head -5 projects/[project]/README.md
# Should show: mcp-name: io.github.[username]/[project]
```

**2. Publish to MCP Registry**
```bash
cd projects/[project]
/path/to/mcp-publisher publish --server server.json
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.[username]/[project] version 1.0.0
```

**3. Verify Publication**

The MCP should now be discoverable in Claude Desktop and the MCP Registry website.

**Updating an Existing MCP**:

1. Update code in dev-sandbox
2. Bump version in all files:
   - `pyproject.toml`
   - `server.json`
   - `src/[project]_mcp/__init__.py`
3. Rebuild: `python -m build`
4. Upload to PyPI: `twine upload dist/*`
5. Republish to Registry: `mcp-publisher publish --server server.json`

**Troubleshooting**:

| Error | Solution |
|-------|----------|
| `401 Unauthorized` / `token expired` | Re-run `mcp-publisher login github` |
| `server.json not found` | Run from project directory or use absolute path |
| `Package not found on registry` | Ensure PyPI upload completed first (SOP 12) |
| `Ownership validation failed` | Add `mcp-name: io.github.[user]/[project]` to README |
| `registryType "pip" unsupported` | Use `"pypi"` not `"pip"` in server.json |
| `Description too long` | Shorten to under 100 characters |

**server.json Validation**:

Common issues:
```json
{
  "registryType": "pypi",     // NOT "pip"
  "identifier": "[project]-mcp",  // Must match PyPI package name exactly
  "version": "1.0.0"          // Must match PyPI version
}
```

**MCP Registry Namespace**:

Your MCP name format: `io.github.[github-username]/[project-name]`

Examples:
- `io.github.wmarceau/md-to-pdf`
- `io.github.wmarceau/amazon-seller`
- `io.github.wmarceau/fitness-influencer`

**Success Criteria**:
- ✅ `mcp-publisher publish` succeeds
- ✅ MCP appears in Claude Desktop's MCP browser
- ✅ Users can install via the registry

**Complete Publishing Workflow**:

```bash
# From project directory
cd projects/[project]

# 1. Build
rm -rf dist/ && python -m build

# 2. Upload to PyPI
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN

# 3. Publish to MCP Registry
/path/to/mcp-publisher publish --server server.json
```

**References**:
- MCP Registry: https://registry.modelcontextprotocol.io
- mcp-publisher repo: https://github.com/modelcontextprotocol/registry

