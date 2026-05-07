# Power BI Dashboard Automation — MCP Server Plan

**Created:** May 7, 2026
**Author:** William Marceau / Panacea
**Tower:** mcp-services
**Strategic Direction:** Grok (xAI) — semi-automated approach, agent proposes before executing
**Status:** Planning Phase

---

## Executive Summary

Build an MCP (Model Context Protocol) server that wraps the Power BI REST API, enabling an AI agent (Claude) to accept a natural language dashboard request and take all necessary steps to create a fully functional Power BI dashboard — fetching data, structuring datasets, selecting visualizations, and publishing the result for user approval before going live.

**Feasibility:** ✅ Yes. Power BI exposes a full REST API for programmatic dataset creation, data push, report cloning, and dashboard assembly. The main constraint is that complex visual layouts require PBIX template files — the solution accounts for this with a template library approach.

---

## How It Works (User Flow)

```
User: "Build me a sales dashboard for my HVAC client showing
       revenue by month, top 5 products, and lead conversion rate"

Agent:
  1. Parses request → identifies metrics, dimensions, chart types
  2. Fetches/connects to data source (CSV, SQL, Google Sheets, API)
  3. Creates Power BI dataset with correct schema
  4. Pushes data rows to dataset
  5. Selects best-fit report template from library
  6. Clones template → binds to new dataset
  7. Configures visuals to match requested metrics
  8. Returns preview link → "Here's your dashboard, approve to publish?"
  9. On approval → publishes to workspace, returns embed URL
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| MCP Server | Python `mcp` SDK | Exposes tools to Claude |
| Auth | MSAL (Microsoft Auth Library) | Azure AD OAuth 2.0 for Power BI API |
| Power BI API | Power BI REST API v1.0 | Dataset/report/dashboard management |
| Data Ingestion | pandas, requests, google-api-python-client | Fetch and transform source data |
| Template Engine | PBIX files + Power BI Clone API | Report layout management |
| NL Parser | Claude (via tool call) | Natural language → dashboard spec |
| Config | python-dotenv | Credentials from .env |

---

## Power BI MCP Tools (Exposed to Agent)

### Authentication
- `powerbi_authenticate` — Exchange client credentials for access token (Azure AD)

### Workspace Management
- `list_workspaces` — List all Power BI workspaces user has access to
- `get_workspace` — Get details of a specific workspace

### Dataset Operations
- `create_dataset` — Create a new Push dataset with defined schema
- `push_rows` — Push data rows into an existing dataset table
- `refresh_dataset` — Trigger scheduled/on-demand data refresh
- `list_datasets` — List datasets in a workspace
- `delete_dataset` — Remove a dataset

### Report Operations
- `list_reports` — List available reports and templates
- `clone_report` — Clone a template report into a workspace
- `rebind_report` — Rebind a cloned report to a new dataset
- `get_report_embed_url` — Get embed URL for preview/sharing
- `export_report` — Export report as PDF or PNG

### Dashboard Operations
- `create_dashboard` — Create a new dashboard in a workspace
- `add_tile_from_report` — Pin a report visual to a dashboard
- `list_dashboards` — List dashboards in a workspace

### Intelligence Layer
- `parse_dashboard_request` — NL → structured dashboard spec (metrics, dimensions, chart types, data source)
- `recommend_template` — Match dashboard spec to best template in library
- `validate_dataset_schema` — Verify data matches required schema before push

---

## Azure AD Setup Requirements

1. **App Registration** in Azure Portal (portal.azure.com)
   - Redirect URI: `http://localhost` (for initial auth flow)
   - API permissions required:
     - `Dataset.ReadWrite.All`
     - `Report.ReadWrite.All`
     - `Dashboard.ReadWrite.All`
     - `Workspace.ReadWrite.All`
2. **Service Principal** or delegated user auth
3. **Power BI Embedded capacity** (A-SKU or F-SKU) if embedding in client websites
4. Store in `.env`:
   ```
   POWERBI_CLIENT_ID=
   POWERBI_CLIENT_SECRET=
   POWERBI_TENANT_ID=
   POWERBI_WORKSPACE_ID=
   ```

---

## Template Library Strategy

The Power BI REST API cannot build complex visual layouts from scratch programmatically. Solution: maintain a library of PBIX template files covering common dashboard types.

| Template | Use Case | Visuals Included |
|----------|----------|-----------------|
| `sales-overview.pbix` | Revenue, pipeline, conversion | Line chart, bar chart, KPI cards, map |
| `lead-funnel.pbix` | Lead gen, CRM tracking | Funnel chart, table, donut, timeline |
| `financial-summary.pbix` | P&L, expenses, cash flow | Waterfall, area chart, gauge, table |
| `ops-dashboard.pbix` | Operational KPIs, throughput | Gauge, scatter, heatmap, cards |
| `marketing-analytics.pbix` | Campaign performance, traffic | Bar, line, cards, geographic map |
| `client-report.pbix` | White-label client delivery | Branded layout, logo placeholder |

Agent selects template → clones it → rebinds to new dataset → configures visuals via API where possible, flags manual steps where API is limited.

---

## Milestones

### Milestone 1 — Auth & Scaffold (Week 1)
- [ ] Azure AD app registration
- [ ] MSAL OAuth flow working in Python
- [ ] MCP server scaffold (`mcp-powerbi` in `projects/mcp-services/src/`)
- [ ] `list_workspaces` and `list_datasets` tools working end-to-end
- [ ] `.env` credentials configured and tested

### Milestone 2 — Dataset Pipeline (Week 2)
- [ ] `create_dataset` tool with schema definition
- [ ] `push_rows` tool — CSV/Sheets/API → Power BI push dataset
- [ ] `refresh_dataset` tool
- [ ] Test: push 500 rows of sample sales data, confirm visible in Power BI

### Milestone 3 — Report & Template Engine (Week 3)
- [ ] Build initial template library (3 PBIX templates minimum)
- [ ] `clone_report` tool working
- [ ] `rebind_report` tool — bind cloned template to new dataset
- [ ] `get_report_embed_url` returning accessible preview link
- [ ] Test: clone sales template, bind to pushed dataset, view in browser

### Milestone 4 — Natural Language Layer (Week 4)
- [ ] `parse_dashboard_request` tool — NL → structured JSON spec
  ```json
  {
    "title": "HVAC Revenue Dashboard",
    "metrics": ["revenue", "lead_conversion_rate"],
    "dimensions": ["month", "product"],
    "charts": ["line", "bar", "kpi_card"],
    "data_source": "google_sheets",
    "template": "sales-overview"
  }
  ```
- [ ] `recommend_template` tool — spec → best PBIX match
- [ ] End-to-end test: natural language request → published dashboard

### Milestone 5 — Approval Flow & Delivery (Week 5)
- [ ] Human-in-the-loop approval step before publish
- [ ] `export_report` tool — PDF/PNG snapshot for client delivery
- [ ] Branded PDF wrapper via `branded_pdf_engine.py` (existing shared utility)
- [ ] Telegram delivery: send embed URL or PDF snapshot to William for review
- [ ] Integration with client-delivery tower for handoff

### Milestone 6 — Productization (Week 6+)
- [ ] Web UI or Telegram command interface for non-technical client requests
- [ ] Template library expanded to 8-10 templates
- [ ] Pricing model: one-time setup + monthly maintenance retainer
- [ ] Documentation and SOP for adding new data sources

---

## Known Limitations & Workarounds

| Limitation | Workaround |
|-----------|-----------|
| REST API cannot build arbitrary visual layouts | Template library — clone + rebind approach |
| Push datasets are real-time only, no DirectQuery | Use scheduled push refresh via n8n automation |
| Power BI Free doesn't support embed API | Requires Power BI Pro ($10/user/mo) or Premium |
| Complex DAX measures can't be set via API | Pre-bake common measures into PBIX templates |
| Report visual config via API is limited | Semi-automated: agent sets what it can, flags the rest |

---

## Business Model

**Who buys this:**
- Small-to-mid businesses that need data dashboards but can't afford a BI consultant
- Marketing agencies wanting branded client reporting
- Healthcare/fitness/HVAC/trades businesses with operational data

**Pricing ideas:**
- Dashboard build: $500–$1,500 one-time per dashboard
- Data pipeline setup: $200–$500
- Monthly maintenance + refresh: $99–$199/mo
- White-label for agencies: custom pricing

**Positioning:** "Tell me what you want to see — I'll build the dashboard in 24 hours."

---

## Grok Strategic Direction (May 7, 2026)

> *"Building an MCP for Power BI automation is feasible and aligns with expanding your AI services portfolio. Prioritize identifying specific client pain points in data visualization. Focus on integrating AI to fetch data, suggest layouts, and generate dashboards, but avoid overcomplicating with untested automation — start with semi-automated steps where the agent proposes actions for user approval."*

---

## File Structure (When Built)

```
projects/mcp-services/src/powerbi/
├── __init__.py
├── auth.py              # MSAL OAuth flow
├── client.py            # Power BI REST API wrapper
├── tools/
│   ├── datasets.py      # Dataset CRUD tools
│   ├── reports.py       # Report clone/rebind tools
│   ├── dashboards.py    # Dashboard assembly tools
│   └── nlp.py           # NL → dashboard spec parser
├── templates/
│   ├── sales-overview.pbix
│   ├── lead-funnel.pbix
│   └── financial-summary.pbix
└── server.py            # MCP server entry point

projects/mcp-services/workflows/
└── PowerBI_Dashboard_Automation_Plan.md   ← THIS FILE
```

---

## Next Steps (When Ready to Build)

1. Run `market-check` skill to validate commercial viability before investing build time
2. Register Azure AD app → store credentials in `.env`
3. Start with Milestone 1 scaffold on Mac (Claude Code)
4. Test against a real client data set (ideal: HVAC or med spa client)
5. Deploy MCP server to EC2 alongside existing n8n/Panacea infrastructure

---

*Saved by Panacea on May 7, 2026. Revisit on Mac via Claude Code.*
*File location: `projects/mcp-services/workflows/PowerBI_Dashboard_Automation_Plan.md`*
