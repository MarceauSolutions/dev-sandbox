# Power BI MCP — Collier County Build Plan

**Tower:** industrial-ops
**Created:** May 10, 2026
**Status:** Planning
**Priority:** 4
**Reference:** Full MCP architecture plan at `projects/mcp-services/workflows/PowerBI_Dashboard_Automation_Plan.md`
**Strategic Context:** Collier County is migrating from Excel to Power BI for departmental reporting.
William can position himself as the person who accelerates and owns that migration.

---

## Executive Summary

Extend the existing Power BI MCP plan (already documented in `mcp-services`) with county-specific
dashboard templates for wastewater operations. The MCP allows an AI agent to build Power BI
dashboards from natural language requests — William describes what he needs, the agent builds it.

**Example use case:**
> William: "Build me a dashboard showing pump failure rates by lift station for the last 90 days"
> Agent: fetches data → creates dataset → clones template → publishes dashboard → returns link

---

## County-Specific Context

Collier County's Power BI migration means:
- Departments that relied on static Excel reports need dynamic dashboards
- There is no dedicated BI team at the department level — William can fill that gap
- Dashboards that take a BI consultant days to build can take William minutes with this tool
- County leadership can see live operational data instead of waiting for weekly Excel exports

---

## County-Specific Dashboard Templates

In addition to the general templates in the `mcp-services` plan, build these wastewater-specific templates:

| Template | Use Case | Key Visuals |
|----------|----------|------------|
| `wastewater-ops.pbix` | Daily operational KPIs | Pump status, flow rates, alarm counts, uptime |
| `maintenance-tracker.pbix` | Work order status and history | Open/closed by category, avg resolution time |
| `lift-station-health.pbix` | Per-station performance | Station map, failure rate, last inspection date |
| `compliance-report.pbix` | Regulatory reporting | Permit limits vs actuals, exceedance events |
| `equipment-lifecycle.pbix` | Asset management | Age, replacement schedule, maintenance cost |

---

## Data Sources Available at Collier County

| Source | Type | Connection Method |
|--------|------|-----------------|
| Excel work order logs | .xlsx files | Excel connector in Power BI |
| SCADA historian | SQL or CSV export | Direct query or scheduled export |
| DFS system exports | CSV/Excel | File import |
| County SharePoint | SharePoint lists | Power BI SharePoint connector |
| Manual field logs | Excel/paper → digitized | Via Excel MCP ingestion layer |

---

## Integration with Excel MCP

The Excel MCP (Priority 3) feeds this tool:
1. Excel MCP reads and cleans raw county data
2. Power BI MCP takes the cleaned data → pushes to Power BI dataset
3. Dashboard auto-updates when new Excel data is loaded

This creates an automated pipeline:
```
Field data (Excel) → Excel MCP (clean + structure) → Power BI MCP (push + refresh) → Live Dashboard
```

---

## Build Approach

Follow the 6-milestone plan in `projects/mcp-services/workflows/PowerBI_Dashboard_Automation_Plan.md`.
County-specific additions:

1. **Azure AD setup** — Use county's Microsoft 365 tenant if IT approves, or William's personal
   Azure account for demo purposes first
2. **County workspace** — Request a Power BI workspace in the county's Power BI tenant, or demo
   in William's personal Pro workspace
3. **Template library** — Build the 5 county-specific templates above in addition to the general ones
4. **Data privacy** — All test data must be anonymized or synthetic; no real PII in demo datasets

---

## Conversation Chain for Deployment

Before using this on county data or county Power BI accounts:
1. Demo to boss using synthetic/anonymized data → show him the output
2. Boss takes it to IT → get approval for county tenant access
3. IT approves → move to county Power BI workspace
4. Department head sees it → salary conversation becomes possible

William can build and demo the entire system on his personal Azure + Power BI Pro account
($10/month) before the county is involved at all.

---

## Milestones

### Milestone 1 — Foundation (After Excel MCP is working)
- [ ] Azure AD app registration (personal account for demo)
- [ ] Power BI Pro trial or $10/mo subscription for demo workspace
- [ ] Adapt `mcp-services` Power BI MCP scaffold to `industrial-ops` context
- [ ] `list_workspaces` and `list_datasets` working

### Milestone 2 — County Templates
- [ ] Build `wastewater-ops.pbix` template (first priority)
- [ ] Build `maintenance-tracker.pbix` template
- [ ] Clone + rebind flow working end-to-end

### Milestone 3 — Data Pipeline
- [ ] Excel MCP → Power BI MCP pipeline working
- [ ] Push 30 days of synthetic work order data → live dashboard
- [ ] `get_report_embed_url` returning shareable link

### Milestone 4 — Demo to Boss
- [ ] Fully functional wastewater ops dashboard on synthetic data
- [ ] Recorded walkthrough or live demo
- [ ] Document time it took to build vs. traditional method
- [ ] Present to boss — "this took me 4 minutes, a BI consultant would charge $2,000"

---

## Conflict of Interest Note

Demo on personal Azure account using synthetic data first — no county systems involved
until IT explicitly approves. This keeps William completely clean on ethics while still
building something demonstrably real and impressive.
