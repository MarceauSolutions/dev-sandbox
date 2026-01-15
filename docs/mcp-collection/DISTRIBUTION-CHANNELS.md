# MCP Distribution Channels

This document tracks all distribution channels for our MCP servers.

## Published MCPs

| MCP | PyPI | Claude Registry | Status |
|-----|------|-----------------|--------|
| md-to-pdf-mcp | v1.0.1 | io.github.wmarceau/md-to-pdf | Live |
| amazon-seller-mcp | v1.0.0 | io.github.wmarceau/amazon-seller | Live |
| fitness-influencer-mcp | v1.0.0 | io.github.wmarceau/fitness-influencer | Live |
| rideshare-comparison-mcp | v1.0.0 | io.github.wmarceau/rideshare-comparison | Live |
| hvac-quotes-mcp | v1.0.0 | io.github.wmarceau/hvac-quotes | Live |

---

## Channel Status

### 1. Claude MCP Registry (Primary)
**Status:** All 5 MCPs published
**URL:** https://registry.modelcontextprotocol.io

This is the official Anthropic registry. Users can discover and install MCPs directly from Claude Desktop.

---

### 2. PyPI (Python Package Index)
**Status:** All 5 MCPs published
**URLs:**
- https://pypi.org/project/md-to-pdf-mcp/
- https://pypi.org/project/amazon-seller-mcp/
- https://pypi.org/project/fitness-influencer-mcp/
- https://pypi.org/project/rideshare-comparison-mcp/
- https://pypi.org/project/hvac-quotes-mcp/

---

### 3. PulseMCP
**Status:** Auto-ingested (weekly from MCP Registry)
**URL:** https://www.pulsemcp.com
**Action Required:** None - PulseMCP automatically ingests from the official MCP Registry weekly.

Check listings at: `https://www.pulsemcp.com/servers/wmarceau-[mcp-name]`

---

### 4. Glama.ai
**Status:** ✅ All 5 MCPs submitted (2026-01-14)
**URL:** https://glama.ai/mcp/servers

All MCPs submitted via GitHub integration with MarceauSolutions organization.
Glama indexes ~9,000+ MCP servers and provides hosting capabilities.

---

### 5. Awesome MCP Servers (GitHub)
**Status:** Pending PR
**Repository:** https://github.com/punkpeye/awesome-mcp-servers
**Action Required:**
1. Fork the repository
2. Add entries for our MCPs in appropriate categories
3. Submit a pull request

**Proposed additions:**

```markdown
### Document Processing
- [md-to-pdf-mcp](https://github.com/MarceauSolutions/md-to-pdf-mcp) - Convert Markdown to professional PDFs

### Business Operations
- [amazon-seller-mcp](https://github.com/MarceauSolutions/amazon-seller-mcp) - Amazon Seller Central operations
- [fitness-influencer-mcp](https://github.com/MarceauSolutions/fitness-influencer-mcp) - Fitness content creator workflows

### Price Comparison
- [rideshare-comparison-mcp](https://github.com/MarceauSolutions/rideshare-comparison-mcp) - Compare Uber and Lyft prices
- [hvac-quotes-mcp](https://github.com/MarceauSolutions/hvac-quotes-mcp) - HVAC equipment RFQ management
```

---

### 6. MCP.so
**Status:** Not submitted
**URL:** https://mcp.so
**Action Required:** Check submission process

---

### 7. MCP Market
**Status:** Not submitted
**URL:** https://mcpmarket.com
**Action Required:** Check submission process

---

## GitHub Repositories

**Status:** ✅ All created under MarceauSolutions organization

| MCP | GitHub Repository |
|-----|-------------------|
| md-to-pdf-mcp | https://github.com/MarceauSolutions/md-to-pdf-mcp |
| amazon-seller-mcp | https://github.com/MarceauSolutions/amazon-seller-mcp |
| fitness-influencer-mcp | https://github.com/MarceauSolutions/fitness-influencer-mcp |
| rideshare-comparison-mcp | https://github.com/MarceauSolutions/rideshare-comparison-mcp |
| hvac-quotes-mcp | https://github.com/MarceauSolutions/hvac-quotes-mcp |

---

## OpenRouter Integration

OpenRouter doesn't have an MCP directory. Instead, users configure MCP servers individually in their OpenRouter setup. Our MCPs work with OpenRouter when users:

1. Install our MCP via pip
2. Configure it in their client (Claude Desktop, Cursor, VS Code)
3. Connect their client to OpenRouter

**No registration required** - OpenRouter routes to models, not tools.

---

## GEO Optimization

Landing pages created for AI search optimization:
- `docs/mcp-collection/index.md` - Main collection page
- `docs/mcp-collection/md-to-pdf.md` - MD to PDF landing page
- `docs/mcp-collection/amazon-seller.md` - Amazon Seller landing page
- `docs/mcp-collection/fitness-influencer.md` - Fitness Influencer landing page
- `docs/mcp-collection/rideshare-comparison.md` - Rideshare landing page
- `docs/mcp-collection/hvac-quotes.md` - HVAC Quotes landing page

Each page includes:
- FAQ section (AI-extractable)
- Clear tool descriptions
- Example prompts
- Installation instructions

---

## Maintenance

### Weekly Tasks
- Check PulseMCP listings (auto-updated)
- Monitor PyPI download stats
- Review any issues/feedback

### On Version Update
1. Update PyPI: `python -m twine upload dist/*`
2. Update MCP Registry: `mcp-publisher publish --server server.json`
3. PulseMCP auto-updates from registry
4. Update landing pages if features changed

---

## Contact

For directory-related issues:
- PulseMCP: hello@pulsemcp.com
- Glama: frank@glama.ai
- Awesome MCP Servers: Submit GitHub issue
