# SW Florida Comfort HVAC

Client of Marceau Solutions. HVAC services company in Southwest Florida.

## Projects in This Namespace

| Project | What | Deploy Repo |
|---------|------|-------------|
| `website/` | Client website (static HTML) | `MarceauSolutions/swflorida-comfort-hvac` |
| `hvac-distributors/` | RFQ system for equipment quotes | — |
| `hvac-mcp/` | MCP tools for HVAC operations | PyPI: `hvac-quotes-mcp` |

## Deployment

Website deploys automatically via GitHub Actions when files in `website/` change on main.
Deploy repo: `MarceauSolutions/swflorida-comfort-hvac` (GitHub Pages).

## Shared Tools Used

- `projects/shared/lead-scraper/` — Lead generation
- `projects/shared/ai-customer-service/` — Voice AI for phone quotes
- `projects/shared/social-media-automation/` — Social posting
- `execution/form_handler/` — Form submissions (business_id: `swfloridacomfort`)
