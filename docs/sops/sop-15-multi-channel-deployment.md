# SOP 15: Multi-Channel Deployment

**When**: Deploying a project to multiple distribution channels simultaneously

**Purpose**: Orchestrate deployment across all configured channels (Local, GitHub, PyPI, MCP Registry, OpenRouter) in a single workflow

**Agent**: Claude Code (REQUIRED for PyPI/MCP channels). Clawdbot (GitHub only). Ralph: N/A.

**Available Channels**:

| Channel | Target Audience | Prerequisites |
|---------|----------------|---------------|
| **Local Workspace** | Internal testing | None (automatic) |
| **GitHub Repo** | Open source / team | GitHub account, repo exists |
| **PyPI Package** | Python developers | pyproject.toml, PyPI token |
| **Claude MCP Registry** | Claude users | server.json, mcp-publisher |
| **OpenRouter** | Multi-LLM users | MCP server with stdio transport |

**Channel Configuration**:

Add `deployment_channels` to project config in `deploy_to_skills.py`:

```python
"project-name": {
    # ... existing config ...
    "deployment_channels": {
        "local": True,           # Always enabled
        "github": "org/repo",    # GitHub repo or False
        "pypi": "package-mcp",   # PyPI package name or False
        "mcp_registry": "io.github.user/project",  # MCP name or False
        "openrouter": True       # Register on OpenRouter directories
    }
}
```

**Commands**:

```bash
# Deploy to all configured channels
python deploy_to_skills.py --project [name] --all-channels --version 1.0.0

# Deploy to specific channels only
python deploy_to_skills.py --project [name] --channels local,github,pypi

# Validate prerequisites without deploying
python deploy_to_skills.py --project [name] --validate-channels

# List configured channels for a project
python deploy_to_skills.py --project [name] --list-channels
```

**Deployment Sequence**:

1. **Validate** - Check all prerequisites for enabled channels
2. **Local Workspace** - Deploy to `~/{project}-prod/`
3. **GitHub** - Push to configured repository
4. **PyPI** - Build and upload package (`twine upload dist/*`)
5. **MCP Registry** - Publish to Claude marketplace (`mcp-publisher publish`)
6. **OpenRouter** - Register on PulseMCP/Glama directories
7. **Verify** - Confirm each deployment succeeded
8. **Report** - Generate deployment summary

**Prerequisites per Channel**:

| Channel | Required Files | Required Tools/Accounts |
|---------|----------------|------------------------|
| Local | VERSION, CHANGELOG | None |
| GitHub | README, LICENSE | `gh` CLI, repo access |
| PyPI | pyproject.toml, src/[pkg]_mcp/ | PyPI token |
| MCP Registry | server.json, mcp-name in README | mcp-publisher, GitHub auth |
| OpenRouter | Working MCP server (stdio) | None (manual registration) |

**Example Multi-Channel Deployment**:

```bash
# Full deployment of rideshare MCP to all channels
python deploy_to_skills.py --project mcp-aggregator-rideshare \
    --all-channels \
    --version 1.0.0

# Output:
# ✓ Local Workspace: ~/mcp-aggregator-rideshare-prod/
# ✓ GitHub: wmarceau/rideshare-comparison-mcp
# ✓ PyPI: rideshare-comparison-mcp v1.0.0
# ✓ MCP Registry: io.github.wmarceau/rideshare-comparison
# ✓ OpenRouter: Listed on PulseMCP, Glama
```

**Post-Deployment**:

1. Update `docs/MCP-CONVERSION-PLAN.md` status
2. Add to curated collection landing page
3. Document in session-history.md

**References**:
- SOP 11-14: Individual channel SOPs
- `docs/deployment.md`: Deployment pipeline documentation
