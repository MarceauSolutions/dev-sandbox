# Industrial Ops Tower

**Created:** May 10, 2026
**Owner:** William Marceau
**Status:** Active — Milestone 1 in progress
**Strategic Direction:** Grok (xAI) — internal demonstration only, no direct sales to Collier County

---

## Purpose

AI tools built for William's role as Instrumentation & Electrical Technician at Collier County Government.
These tools are built to demonstrate value, improve departmental efficiency, and support William's case
for salary-based compensation and recognition — NOT for sale through Marceau Solutions.

**Conflict of interest rule:** William cannot sell tools or services to Collier County through his business
while employed there. All tools in this tower are internal-use-only until a formal compensation arrangement
is approved through the appropriate chain of command (supervisor → department head → county administration).

---

## Sub-Projects

| Sub-Project | Status | Location |
|-------------|--------|----------|
| `sop_builder` | **Priority 1 — Boss already asked** | `src/sop_builder/` |
| `knowledge_base` | Priority 2 | `src/knowledge_base/` |
| `excel_mcp` | Priority 3 | `src/excel_mcp/` |
| `powerbi_mcp` | Priority 4 (plan exists) | `src/powerbi_mcp/` |

---

## Sub-Project Details

### 1. SOP Builder (`src/sop_builder/`)
Generate professional SOPs for Collier County departments using the existing `branded_pdf_engine.py`
and `markdown_to_pdf.py` from `execution/`. First deliverable: front desk agent SOP (boss-requested).

**Input:** Interview notes / process descriptions from William
**Output:** Formatted PDF SOP using county-appropriate styling (not Marceau Solutions branding)
**Shared utility:** `execution/markdown_to_pdf.py`, `execution/branded_pdf_engine.py`

### 2. Wastewater Knowledge Base (`src/knowledge_base/`)
A searchable library of Collier County wastewater-specific terminology, specs, and procedures.
Accounts for the fact that Collier County uses a mix of industry-standard and internally-coined
terminology from their DFS vendor specs. Tribal knowledge capture system.

**Input:** William manually feeds spec documents, field notes, DFS vendor manuals
**Output:** Searchable Q&A interface (local first, Telegram query via Panacea)
**Key challenge:** De-conflating Collier-specific terms from industry-standard terms

### 3. Excel MCP (`src/excel_mcp/`)
MCP server wrapping Excel file operations — read, write, transform, summarize spreadsheet data
via natural language. Built for the county's heavy Excel usage before the Power BI migration.

**Reference:** `projects/mcp-services/` for MCP server patterns

### 4. Power BI MCP (`src/powerbi_mcp/`)
Defer to existing plan: `projects/mcp-services/workflows/PowerBI_Dashboard_Automation_Plan.md`
This sub-project links to and extends that plan for county-specific dashboard use cases.

---

## Strategic Notes (Grok, May 10 2026)

> Building tools for internal demonstration is the right move. Selling to the county while employed
> there is a clear conflict of interest and likely violates county ethics policies. The correct path:
> build, document impact, let results speak, then discuss salary recognition through the chain of command.
> County benefits (health, pension) represent significant non-cash compensation — protect that stability.

**The conversation chain when ready:**
1. Supervisor (direct boss) — informal show-and-tell first
2. Department head — formal proposal with documented time savings
3. HR / County Administration — if salary adjustment or title change is on the table

**Document everything:** Time saved per task, error reduction, output quality improvement.
These are the metrics that make the salary conversation possible.

---

## Data Directory

`data/collier-county/` — County-specific reference material William feeds in manually.
This directory is `.gitignore`d if it ever contains sensitive county documents.
Do NOT commit proprietary county specs or internal documents to the repo.

---

## Milestones

### Milestone 1 — SOP Builder (Week 1–2)
- [x] Build SOP template (neutral county styling, navy header, Arial — no Marceau gold/charcoal)
- [x] `sop_generator.py` CLI — structured JSON or rough-notes input modes
- [x] PDF rendering via weasyprint (clean page breaks, no artifacts)
- [x] Test with front desk example — verified clean 3-page PDF
- [ ] Front desk agent SOP — first real deliverable for boss (waiting on William's process notes)
- [ ] Deliver to boss, document reaction and feedback

### Milestone 2 — Knowledge Base Scaffold (Week 3–4)
- [ ] Design data ingestion pipeline (William pastes text → structured entry)
- [ ] Build local search (keyword + semantic) over county spec content
- [ ] Telegram query interface: "What does [term] mean at Collier County?"
- [ ] Seed with 20–30 entries from DFS specs

### Milestone 3 — Excel MCP (Week 5–6)
- [ ] MCP server scaffold in `src/excel_mcp/`
- [ ] Core tools: read_sheet, summarize_sheet, find_in_sheet, write_cell
- [ ] Test against a real county Excel file

### Milestone 4 — Power BI MCP (Week 7+)
- [ ] Follow `projects/mcp-services/workflows/PowerBI_Dashboard_Automation_Plan.md`
- [ ] County-specific templates for wastewater KPIs
