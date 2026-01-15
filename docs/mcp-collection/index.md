# Marceau Solutions MCP Collection

> Production-ready Model Context Protocol (MCP) servers for Claude Desktop

## What are MCPs?

Model Context Protocol (MCP) servers extend Claude's capabilities by providing specialized tools. Install any of these MCPs to add new functionality to Claude Desktop.

---

## Available MCPs

### Document & Content Tools

#### MD to PDF MCP
**Convert Markdown to professional PDFs directly from Claude**

- Convert markdown files to styled PDFs
- Custom themes (modern, classic, minimal)
- Support for code blocks, tables, and images
- Batch conversion support

```bash
pip install md-to-pdf-mcp
```

**Claude Registry:** `io.github.wmarceau/md-to-pdf`
**PyPI:** [md-to-pdf-mcp](https://pypi.org/project/md-to-pdf-mcp/)

---

### Business Operations

#### Amazon Seller MCP
**Manage Amazon Seller Central operations via Claude**

- Inventory management and tracking
- Order processing and status updates
- Product listing optimization
- Sales analytics and reporting

```bash
pip install amazon-seller-mcp
```

**Claude Registry:** `io.github.wmarceau/amazon-seller`
**PyPI:** [amazon-seller-mcp](https://pypi.org/project/amazon-seller-mcp/)

---

#### Fitness Influencer MCP
**Automate fitness content creator workflows**

- Video editing automation (jump cuts)
- Email management for sponsors
- Revenue analytics tracking
- Branded content creation

```bash
pip install fitness-influencer-mcp
```

**Claude Registry:** `io.github.wmarceau/fitness-influencer`
**PyPI:** [fitness-influencer-mcp](https://pypi.org/project/fitness-influencer-mcp/)

---

### Price Comparison & Quotes

#### Rideshare Comparison MCP
**Compare Uber and Lyft prices for any route**

- Real-time price estimates for Uber and Lyft
- Surge pricing detection
- Deep links to book rides
- Multi-city support

```bash
pip install rideshare-comparison-mcp
```

**Claude Registry:** `io.github.wmarceau/rideshare-comparison`
**PyPI:** [rideshare-comparison-mcp](https://pypi.org/project/rideshare-comparison-mcp/)

---

#### HVAC Quotes MCP
**HVAC equipment RFQ management for contractors**

- Submit RFQs to multiple distributors
- Track quote status and responses
- Compare quotes across distributors
- Support for all HVAC equipment types

```bash
pip install hvac-quotes-mcp
```

**Claude Registry:** `io.github.wmarceau/hvac-quotes`
**PyPI:** [hvac-quotes-mcp](https://pypi.org/project/hvac-quotes-mcp/)

---

## Quick Installation

All MCPs follow the same installation pattern:

1. **Install via pip:**
   ```bash
   pip install [mcp-name]
   ```

2. **Add to Claude Desktop config** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "[mcp-name]": {
         "command": "[mcp-name]"
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the new MCP

---

## FAQ

### How do I install an MCP?
Use pip to install, then add the server to your Claude Desktop configuration file. Each MCP's README has specific configuration examples.

### Where is the Claude Desktop config file?
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Can I use multiple MCPs at once?
Yes! Add multiple entries to the `mcpServers` object in your config file.

### Are these MCPs free to use?
Yes, all MCPs in this collection are open source under the MIT license.

### How do I report issues?
Open an issue on the respective GitHub repository or contact support@marceausolutions.com.

---

## About

This collection is maintained by [Marceau Solutions](https://marceausolutions.com), specializing in AI-powered automation and productivity tools.

**Contact:** support@marceausolutions.com
**GitHub:** [github.com/wmarceau](https://github.com/wmarceau)

---

## Resources

- [Claude MCP Documentation](https://docs.anthropic.com/claude/docs/mcp)
- [MCP Registry](https://registry.modelcontextprotocol.io)
- [PyPI - Python Package Index](https://pypi.org)
