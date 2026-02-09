# Canva MCP Server

mcp-name: io.github.wmarceau/canva-mcp

MCP (Model Context Protocol) server for the Canva Connect API. Create designs, manage assets, use brand templates with autofill, and export graphics - all through Claude.

## Installation

```bash
pip install canva-mcp
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CANVA_CLIENT_ID` | Yes | Canva Connect API Client ID |
| `CANVA_CLIENT_SECRET` | Yes | Canva Connect API Client Secret |
| `CANVA_TOKEN_FILE` | No | Path to token storage (default: ~/.canva_tokens.json) |

Get your credentials at [developers.canva.com](https://www.canva.com/developers/apps)

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/.claude.json`):

```json
{
  "mcpServers": {
    "canva": {
      "command": "python",
      "args": ["-m", "canva_mcp.server"],
      "env": {
        "CANVA_CLIENT_ID": "your-client-id",
        "CANVA_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

## Tools Provided

### User
- `canva_get_profile` - Get current user's Canva profile information

### Designs
- `canva_list_designs` - List user's designs with optional search
- `canva_get_design` - Get details of a specific design
- `canva_create_design` - Create a new design (presentation, social post, poster, etc.)
- `canva_delete_design` - Delete a design

### Assets
- `canva_upload_asset` - Upload image/video/audio from URL or local file
- `canva_list_assets` - List assets in media library
- `canva_get_asset` - Get asset details
- `canva_delete_asset` - Delete an asset

### Folders
- `canva_list_folders` - List folders
- `canva_create_folder` - Create a new folder
- `canva_delete_folder` - Delete a folder

### Brand Templates
- `canva_list_brand_templates` - List available brand templates
- `canva_get_brand_template` - Get template details
- `canva_get_template_dataset` - Get autofill schema for a template

### Autofill
- `canva_autofill_template` - Generate personalized designs from brand templates

### Export
- `canva_export_design` - Export design to PDF, PNG, JPG, GIF, MP4, or PPTX
- `canva_download_export` - Download exported file to local disk

### Comments
- `canva_list_comments` - List comments on a design
- `canva_add_comment` - Add a comment to a design

### Authentication
- `canva_authenticate` - Re-authenticate with Canva (opens browser)

## Use Cases

### Cold Outreach Personalization
Generate personalized mockup websites or graphics for prospects:
```
1. Create a brand template with placeholder fields
2. Use canva_autofill_template with prospect data
3. Export and send with outreach
```

### Batch Content Creation
Create multiple social posts from a template:
```
1. Get template schema with canva_get_template_dataset
2. Loop through data, calling canva_autofill_template
3. Export each design
```

### Asset Management
Organize and manage your media library:
```
1. Create folders for different projects
2. Upload assets from URLs or local files
3. Use assets in new designs
```

## Design Types

Supported design types for `canva_create_design`:
- `presentation`, `doc`, `whiteboard`
- `instagram_post`, `instagram_story`
- `facebook_post`
- `youtube_thumbnail`
- `poster`, `flyer`, `business_card`, `logo`
- `a4_document`, `us_letter`

## Export Formats

Supported formats for `canva_export_design`:
- `pdf` (default)
- `png`, `jpg`, `gif`
- `mp4` (for animated designs)
- `pptx` (PowerPoint)

Quality options: `regular`, `high`

## Authentication Flow

On first use, the MCP will open a browser window for Canva OAuth authentication. Tokens are saved to `~/.canva_tokens.json` and automatically refreshed.

## Requirements

- Python 3.10+
- Canva Pro or Canva for Teams account (for Connect API access)
- OAuth app created at developers.canva.com

## License

MIT

---

**MCP Documentation**: See [modelcontextprotocol.io](https://modelcontextprotocol.io)
