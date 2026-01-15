# Fitness Influencer MCP

> Automate fitness content creator workflows via Claude Desktop

**Package:** `fitness-influencer-mcp`
**Version:** 1.0.0
**Registry:** `io.github.wmarceau/fitness-influencer`

## What does this MCP do?

The Fitness Influencer MCP helps fitness content creators automate repetitive tasks like video editing, email management, and revenue tracking through natural language conversations with Claude.

## Installation

```bash
pip install fitness-influencer-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fitness-influencer": {
      "command": "fitness-influencer-mcp",
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

## Available Tools

### create_jump_cuts
Automatically detect and create jump cuts in video files for fast-paced fitness content.

### manage_sponsor_emails
Process and organize sponsor outreach emails, categorize by priority and deal value.

### track_revenue
Track revenue across platforms (YouTube, Instagram, sponsorships).

### generate_branded_content
Create branded content templates for sponsor deliverables.

## Example Prompts

Ask Claude:

> "Create jump cuts for my latest workout video"

> "Show me all pending sponsor emails sorted by deal value"

> "What's my total revenue this month across all platforms?"

> "Generate a branded post template for my Nike sponsorship"

## Use Cases

### Video Editing Automation
- Automatic jump cut detection based on audio gaps
- Silent segment removal
- Clip compilation for social media

### Sponsor Management
- Email categorization and prioritization
- Contract deadline tracking
- Deliverable checklist generation

### Revenue Analytics
- Multi-platform income tracking
- Monthly/quarterly reports
- Revenue forecasting

## FAQ

### What video formats are supported?
MP4, MOV, and AVI are supported for jump cut processing.

### Does this post content automatically?
No, the MCP prepares content but doesn't post automatically. You review and publish manually.

### Can I connect multiple email accounts?
Currently supports one Gmail/Google Workspace account per configuration.

### Is this for YouTube specifically?
It's platform-agnostic and works with any fitness content workflow.

## Links

- **PyPI:** [pypi.org/project/fitness-influencer-mcp](https://pypi.org/project/fitness-influencer-mcp/)
- **Claude Registry:** `io.github.wmarceau/fitness-influencer`
- **Source:** [github.com/wmarceau/fitness-influencer-mcp](https://github.com/wmarceau/fitness-influencer-mcp)

## License

MIT License - Free for personal and commercial use.
