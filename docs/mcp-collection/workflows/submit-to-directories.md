# Workflow: Submit MCPs to External Directories

## Overview
Submit published MCP servers to external directories and registries for broader discovery and reach.

## Prerequisites
- MCP already published to PyPI (SOP 12)
- MCP already published to Claude MCP Registry (SOP 13)
- GitHub repository created with source code

## Directory Priority Order

| Priority | Directory | Effort | Reach | Auto-Submit |
|----------|-----------|--------|-------|-------------|
| 1 | Claude MCP Registry | Low | High | SOP 13 |
| 2 | PyPI | Low | Medium | SOP 12 |
| 3 | PulseMCP | None | High | Auto-ingest weekly |
| 4 | Glama.ai | Low | High | Manual |
| 5 | awesome-mcp-servers | Medium | High | PR required |
| 6 | MCP.so | Low | Medium | GitHub issue |
| 7 | MCP Market | Low | Medium | Manual |

---

## Step 1: Create GitHub Repository

**For each MCP, create a public repository:**

```bash
gh repo create [ORG]/[project]-mcp --public --description "[Description] - MCP server for Claude Desktop" --clone=false
```

**Push code:**
```bash
cd /tmp && mkdir -p mcp-push/[project]-mcp
cp -r [source-path]/src/[project]_mcp /tmp/mcp-push/[project]-mcp/
cp [source-path]/pyproject.toml /tmp/mcp-push/[project]-mcp/
cp [source-path]/server.json /tmp/mcp-push/[project]-mcp/
cp [source-path]/README.md /tmp/mcp-push/[project]-mcp/

cd /tmp/mcp-push/[project]-mcp
git init && git add . && git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/[ORG]/[project]-mcp.git
git push -u origin main
```

---

## Step 2: Submit to Glama.ai

**URL:** https://glama.ai/mcp/servers

1. Go to Glama.ai and click "Add Server"
2. Authorize GitHub integration (select repositories only)
3. For each MCP, provide:
   - **Name:** `[project]` (without -mcp suffix)
   - **GitHub URL:** `https://github.com/[ORG]/[project]-mcp`
   - **Description:** 1-2 sentences describing capabilities

**Example descriptions:**
```
md-to-pdf: Convert Markdown files to professional PDFs with customizable themes, headers, footers, and styling.
amazon-seller: Amazon Seller Central operations via SP-API - manage inventory, track orders, analyze sales, and optimize listings.
```

---

## Step 3: Submit PR to awesome-mcp-servers

**Repository:** https://github.com/punkpeye/awesome-mcp-servers

1. **Fork and clone:**
   ```bash
   gh repo fork punkpeye/awesome-mcp-servers --clone=true
   cd awesome-mcp-servers
   git checkout -b add-[org]-mcps
   ```

2. **Find appropriate categories** in README.md:
   - File Systems: Document processing, file conversion
   - Finance & Fintech: E-commerce, payments
   - Social Media: Content creation, influencer tools
   - Travel & Transportation: Rideshare, transportation
   - Workplace & Productivity: Business operations, CRM

3. **Add entries** (alphabetically within category):
   ```markdown
   - [ORG/project-mcp](https://github.com/ORG/project-mcp) 🐍 ☁️ - Description
   ```

   **Icon legend:**
   - 🐍 = Python
   - 📇 = TypeScript
   - ☁️ = Cloud service
   - 🏠 = Local service
   - 🍎 = macOS
   - 🪟 = Windows
   - 🐧 = Linux

4. **Commit and create PR:**
   ```bash
   git add README.md
   git commit -m "Add [ORG] MCP servers"
   git push -u origin add-[org]-mcps
   gh pr create --repo punkpeye/awesome-mcp-servers --title "Add [ORG] MCP servers" --body "..."
   ```

---

## Step 4: Submit to MCP.so

**URL:** https://mcp.so
**GitHub:** https://github.com/chatmcp/mcpso

1. Create issue at: https://github.com/chatmcp/mcpso/issues/new
2. Title: "Add [project]-mcp"
3. Body: Include GitHub URL, PyPI package name, description

---

## Step 5: Submit to MCP Market

**URL:** https://mcpmarket.com

1. Check current submission process on site
2. Create account if required
3. Submit each MCP with PyPI package name

---

## Verification Checklist

After 1 week, verify listings:

- [ ] https://www.pulsemcp.com/search?q=[org]
- [ ] https://glama.ai/mcp/servers (search for [org])
- [ ] https://github.com/punkpeye/awesome-mcp-servers (check if PR merged)
- [ ] https://mcp.so (search for package name)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Glama can't find repo | Ensure repo is public |
| awesome-mcp PR rejected | Check formatting, alphabetical order |
| PulseMCP not showing | Wait 7 days (weekly ingest) |
| GitHub auth expired | Re-run `gh auth login` |

---

## Success Criteria

- ✅ GitHub repos created (public, under org)
- ✅ Glama.ai submissions complete
- ✅ awesome-mcp-servers PR submitted
- ✅ MCP.so issue created
- ✅ Documentation updated with links

---

## Related

- SOP 11: MCP Package Structure
- SOP 12: PyPI Publishing
- SOP 13: MCP Registry Publishing
- SOP 14: MCP Update & Version Bump
