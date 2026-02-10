# SOP 16: OpenRouter Registration

**When**: Registering an MCP on OpenRouter and related directories (PulseMCP, Glama) to expand reach beyond Claude marketplace

**Purpose**: Expand MCP reach to 200+ LLM providers via AI gateway integration, making your tool discoverable to a broader audience

**Agent**: Claude Code (primary, form submissions). Clawdbot (directory research). Ralph: N/A.

**Prerequisites**:
- ✅ MCP published to PyPI (SOP 12 complete)
- ✅ MCP published to Claude MCP Registry (SOP 13 complete)
- ✅ MCP server uses stdio transport (not HTTP)
- ✅ Working documentation/README with clear install instructions
- ✅ GitHub repo public (for some directories)

**Directory Comparison**:

| Directory | Review Time | Audience | Best For |
|-----------|-------------|----------|----------|
| **PulseMCP** | 1-3 days | Developers | Technical MCPs |
| **Glama** | 2-5 days | Enterprise | Production-ready MCPs |
| **MCP Market** | 3-7 days | General | Consumer-friendly MCPs |

**Steps**:

1. **Verify MCP works locally** (required before submission):
   ```bash
   # Test server runs without errors
   python -m [package]_mcp.server

   # Test with Claude Desktop (optional but recommended)
   # Add to ~/.claude.json and verify tools appear
   ```

2. **Prepare submission materials**:
   - **Short description** (under 100 chars): One-line summary
   - **Full description** (300-500 chars): What it does, who it's for
   - **Keywords** (5-10): Related terms for search
   - **Category**: Choose from directory's categories
   - **Installation command**: `pip install [package]-mcp`
   - **Example usage**: 2-3 example tool calls with expected output

3. **Register on PulseMCP** (https://pulsemcp.com):
   ```
   Submit Form Fields:
   - Package Name: [package]-mcp
   - PyPI URL: https://pypi.org/project/[package]-mcp/
   - GitHub URL: https://github.com/[username]/[repo]
   - Description: [your short description]
   - Keywords: [comma-separated keywords]
   ```
   **Expected timeline**: Review in 1-3 business days, email notification

4. **Register on Glama** (https://glama.ai/mcp/servers):
   ```
   Submit Form Fields:
   - Server Name: [Display Name]
   - Source: PyPI or GitHub
   - Identifier: [package]-mcp (or github.com/[username]/[repo])
   - Category: [Select from dropdown]
   - Description: [your full description]
   ```
   **Expected timeline**: Review in 2-5 business days, email notification

5. **Register on MCP Market** (https://mcpmarket.com):
   ```
   Submit Form Fields:
   - Title: [Human-readable name]
   - Package: [package]-mcp
   - Documentation URL: [link to README or docs site]
   - Use Cases: [2-3 example use cases]
   - Screenshots: [optional but recommended]
   ```
   **Expected timeline**: Review in 3-7 business days

6. **Update project documentation**:
   ```markdown
   ## Available On

   - [Claude MCP Registry](https://registry.modelcontextprotocol.io)
   - [PulseMCP](https://pulsemcp.com/[your-listing])
   - [Glama](https://glama.ai/mcp/servers/[your-listing])
   - [MCP Market](https://mcpmarket.com/[your-listing])
   ```

**Maintaining Listings** (after initial registration):

| Event | Action |
|-------|--------|
| New version released | Update version on each directory (if required) |
| Description changed | Submit update request on each platform |
| Deprecated | Mark as archived/deprecated on directories |
| Major feature added | Update keywords and description |

**Troubleshooting**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Submission rejected | Missing PyPI package | Complete SOP 12 first |
| "Not found" error | Package name mismatch | Verify exact PyPI package name |
| No response after 7 days | Stuck in queue | Email directory support |
| Listing shows old version | Cache | Wait 24-48 hours or request refresh |

**Success Criteria**:
- [ ] MCP listed on at least 2 directories
- [ ] Installation instructions verified working
- [ ] Search for MCP name returns your listing
- [ ] README updated with directory links
- [ ] Confirmation emails received from directories

**References**:
- [Using MCP Servers with OpenRouter](https://openrouter.ai/docs/guides/guides/mcp-servers)
- [PulseMCP Directory](https://pulsemcp.com)
- [Glama MCP Servers](https://glama.ai/mcp/servers)
- [MCP Market](https://mcpmarket.com)
