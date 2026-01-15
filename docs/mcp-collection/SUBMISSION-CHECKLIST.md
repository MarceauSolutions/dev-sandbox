# MCP Directory Submission Checklist

Use this checklist when publishing a new MCP or updating existing ones.

## Automatic Channels (No Action Required)

- [x] **Claude MCP Registry** - Published via `mcp-publisher`
- [x] **PyPI** - Published via `twine upload`
- [x] **PulseMCP** - Auto-ingests from MCP Registry weekly

## Manual Submission Required

### Glama.ai
**URL:** https://glama.ai/mcp/servers

**Steps:**
1. [ ] Go to https://glama.ai/mcp/servers
2. [ ] Click "Add Server" button
3. [ ] For each MCP, provide:
   - GitHub repository URL
   - Complete the submission form
4. [ ] Wait for indexing (usually within 24 hours)

**MCPs to Submit:**
- [x] https://github.com/MarceauSolutions/md-to-pdf-mcp ✅
- [x] https://github.com/MarceauSolutions/amazon-seller-mcp ✅
- [x] https://github.com/MarceauSolutions/fitness-influencer-mcp ✅
- [x] https://github.com/MarceauSolutions/rideshare-comparison-mcp ✅
- [x] https://github.com/MarceauSolutions/hvac-quotes-mcp ✅

---

### Awesome MCP Servers (GitHub PR)
**Repository:** https://github.com/punkpeye/awesome-mcp-servers
**PR:** https://github.com/punkpeye/awesome-mcp-servers/pull/1676

**Steps:**
1. [x] Fork the repository ✅
2. [x] Add entries to README.md in appropriate categories ✅
3. [x] Submit pull request ✅ (PR #1676)
4. [ ] Wait for maintainer review

**Proposed Entries:**

#### For "📄 Document Processing" category:
```markdown
- **[md-to-pdf-mcp](https://github.com/MarceauSolutions/md-to-pdf-mcp)** <img src="https://cdn.simpleicons.org/python/3776AB" height="14"/> - Convert Markdown to professional PDFs with custom themes
```

#### For "🛒 E-commerce" category:
```markdown
- **[amazon-seller-mcp](https://github.com/MarceauSolutions/amazon-seller-mcp)** <img src="https://cdn.simpleicons.org/python/3776AB" height="14"/> - Amazon Seller Central operations via SP-API
```

#### For "📱 Social Media" or "🎬 Media" category:
```markdown
- **[fitness-influencer-mcp](https://github.com/MarceauSolutions/fitness-influencer-mcp)** <img src="https://cdn.simpleicons.org/python/3776AB" height="14"/> - Fitness content creator workflow automation
```

#### For "🚗 Transportation" or new "💰 Price Comparison" category:
```markdown
- **[rideshare-comparison-mcp](https://github.com/MarceauSolutions/rideshare-comparison-mcp)** <img src="https://cdn.simpleicons.org/python/3776AB" height="14"/> - Compare Uber and Lyft prices for any route
```

#### For "🏠 Real Estate & Construction" or "📧 Business" category:
```markdown
- **[hvac-quotes-mcp](https://github.com/MarceauSolutions/hvac-quotes-mcp)** <img src="https://cdn.simpleicons.org/python/3776AB" height="14"/> - HVAC equipment RFQ management for contractors
```

---

### MCP.so
**URL:** https://mcp.so
**GitHub:** https://github.com/chatmcp/mcpso

**Steps:**
1. [x] Check submission process ✅ - Submit via GitHub issue
2. [ ] Create issue at https://github.com/chatmcp/mcpso/issues/new
3. [ ] Wait for listing

---

### MCP Market
**URL:** https://mcpmarket.com

**Steps:**
1. [ ] Create account (if required)
2. [ ] Submit each MCP listing
3. [ ] Provide PyPI package names and descriptions

---

## Quick Links

| Directory | Submit URL | Status |
|-----------|------------|--------|
| Claude Registry | via `mcp-publisher` | ✅ Done |
| PyPI | via `twine upload` | ✅ Done |
| PulseMCP | Auto-ingest | ✅ Auto |
| Glama.ai | https://glama.ai/mcp/servers | ⏳ Pending |
| Awesome MCP | PR to GitHub repo | ⏳ Pending |
| MCP.so | TBD | ⏳ Pending |
| MCP Market | TBD | ⏳ Pending |

---

## Post-Submission Verification

After 1 week, verify listings at:
- [ ] https://www.pulsemcp.com/search?q=wmarceau
- [ ] https://glama.ai/mcp/servers (search for wmarceau)
- [ ] https://github.com/punkpeye/awesome-mcp-servers (check if PR merged)

---

## Contact for Issues

- **PulseMCP:** hello@pulsemcp.com
- **Glama:** frank@glama.ai
- **Awesome MCP Servers:** Open GitHub issue

---

## Notes

- PulseMCP processes the official MCP Registry weekly, so new MCPs appear within 7 days
- Glama.ai indexes ~9,000+ servers and updates frequently
- GitHub PR approval time varies by maintainer availability
