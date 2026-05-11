# Excel MCP — Build Plan

**Tower:** industrial-ops
**Created:** May 10, 2026
**Status:** Planning
**Priority:** 3 (after SOP Builder and Knowledge Base)
**Strategic Context:** Collier County uses Excel heavily for tracking, reporting, and data management
before their planned migration to Power BI. This MCP allows an AI agent to read, analyze,
and write to Excel files via natural language.

---

## Executive Summary

An MCP server that wraps Excel file operations, allowing Claude (or Panacea via Telegram) to
answer questions about spreadsheet data, find values, summarize sheets, and make edits —
all without William manually opening the file.

**Example use case:**
> William: "What's the last recorded reading for lift station 7 in the maintenance log?"
> Panacea: reads the Excel file → returns the answer in seconds

---

## How It Works

```
User (William via Telegram or Claude Code):
  "Summarize last month's work orders from the tracker"

Agent:
  1. Calls read_sheet() → loads the Excel file
  2. Calls filter_rows() → filters by date range
  3. Calls summarize_sheet() → groups by category/status
  4. Returns plain-language summary with key numbers
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| MCP Server | Python `mcp` SDK | Exposes tools to Claude |
| Excel Engine | `openpyxl` + `pandas` | Read/write .xlsx files |
| File Access | Local file path or shared drive path | Access county Excel files |
| NL Layer | Claude (via tool call) | Natural language → sheet operations |
| Config | `python-dotenv` | Credentials and file paths |

---

## MCP Tools (Exposed to Agent)

### File Operations
- `list_sheets` — List all sheets in a workbook
- `read_sheet` — Load a sheet into memory as a dataframe
- `get_headers` — Return column names from a sheet
- `get_row_count` — Return row count of a sheet

### Data Operations
- `filter_rows` — Filter rows by column value, date range, or keyword
- `find_value` — Search for a specific value across all columns
- `summarize_sheet` — Group and aggregate data (counts, sums, averages)
- `get_column` — Return all values from a specific column
- `get_cell` — Return value of a specific cell (e.g., B14)

### Write Operations
- `write_cell` — Write a value to a specific cell
- `append_row` — Add a new row of data to a sheet
- `update_row` — Update an existing row by row index or lookup key

### Report Generation
- `sheet_to_markdown` — Convert a filtered sheet to a markdown table
- `sheet_to_pdf` — Export a sheet or summary as a formatted PDF (via `branded_pdf_engine.py`)

---

## File Structure (When Built)

```
projects/industrial-ops/src/excel_mcp/
├── __init__.py
├── server.py          # MCP server entry point
├── tools/
│   ├── file_ops.py    # list_sheets, read_sheet, get_headers
│   ├── data_ops.py    # filter_rows, find_value, summarize_sheet
│   ├── write_ops.py   # write_cell, append_row, update_row
│   └── reports.py     # sheet_to_markdown, sheet_to_pdf
└── utils/
    ├── loader.py      # openpyxl/pandas file loading
    └── schema.py      # Column type detection and validation
```

---

## Use Cases at Collier County

| Use Case | Tool Chain | Frequency |
|----------|-----------|-----------|
| "What work orders are still open?" | read_sheet → filter_rows (status=open) | Daily |
| "Summarize this month's pump failures" | read_sheet → filter_rows (date) → summarize_sheet | Weekly |
| "Log today's calibration reading for meter 12" | read_sheet → append_row | As needed |
| "Find all entries for lift station 14" | read_sheet → find_value → sheet_to_markdown | As needed |
| "Generate a PDF report of last month's work orders" | read_sheet → filter_rows → sheet_to_pdf | Monthly |

---

## Milestones

### Milestone 1 — Scaffold & Read (Week 1)
- [ ] MCP server scaffold in `src/excel_mcp/server.py`
- [ ] `list_sheets`, `read_sheet`, `get_headers` working
- [ ] Test against a real county Excel file (anonymized copy)
- [ ] `find_value` and `filter_rows` working end-to-end

### Milestone 2 — Summarization & Reports (Week 2)
- [ ] `summarize_sheet` with groupby and aggregate support
- [ ] `sheet_to_markdown` for Telegram-readable output
- [ ] `sheet_to_pdf` via existing `branded_pdf_engine.py`

### Milestone 3 — Write Operations (Week 3)
- [ ] `write_cell`, `append_row`, `update_row`
- [ ] Approval gate before any write (agent proposes → William confirms → executes)
- [ ] Test: log a maintenance entry via Telegram

### Milestone 4 — Telegram Integration (Week 4)
- [ ] Panacea can query Excel files from Telegram
- [ ] File path config stored in `.env` per spreadsheet alias
  ```
  EXCEL_WORK_ORDERS=/path/to/work_orders.xlsx
  EXCEL_MAINTENANCE_LOG=/path/to/maintenance_log.xlsx
  ```
- [ ] Show to boss as demo

---

## Known Constraints

| Constraint | Workaround |
|-----------|-----------|
| County files may be on a shared network drive | Configure file path per environment — local copy or mapped drive |
| .xls (legacy) format may be in use | Add `xlrd` for legacy support alongside `openpyxl` |
| Large files (10k+ rows) slow to load | Load on-demand with row limit; cache recent reads |
| Write operations are irreversible | Always create a timestamped backup before any write |

---

## Conflict of Interest Note

This tool is built for internal demonstration only. William uses it in his own workflow
to show efficiency gains. No billing or invoicing to the county — value is demonstrated
through output quality, which supports the salary conversation.
