# Wastewater Knowledge Base — Full Build Plan

**Tower:** industrial-ops
**Created:** May 10, 2026
**Status:** Planning — Priority 2
**Strategic Context:** Collier County wastewater operations contain decades of tribal knowledge
locked inside DFS vendor specs and the heads of long-tenured staff. Capturing this in a
searchable AI-powered knowledge base creates something irreplaceable — and makes William
the person who built it.

---

## Executive Summary

A searchable library of Collier County wastewater-specific terminology, procedures, and system
knowledge. Accounts for the fact that the county uses a mix of industry-standard terminology,
internally-coined terms, and DFS vendor-specific language that does not exist outside the county.

**Access methods:**
- Telegram: ask Panacea a question, get an answer
- Claude Code (Mac): query during SOP writing to ensure accuracy
- Future: web interface for other county staff (if IT approves)

---

## The Terminology Problem

Collier County wastewater specs contain three types of language:

| Type | Example | Challenge |
|------|---------|-----------|
| Industry-standard | SCADA, PLC, RTU, 4-20mA loop | Easy — documented everywhere |
| County-specific internal | "the south plant," "the rack," "unit 7" | No external documentation — tribal only |
| DFS vendor-specific | DFS system designations, screen names, alarm codes | Documented only in DFS manuals |

Without a knowledge base, new hires spend months learning these distinctions.
With it, William (or any new tech) can look it up in seconds.

---

## Data Architecture

### Entry Schema

```json
{
  "id": "kb-001",
  "term": "lift station 14",
  "term_aliases": ["LS-14", "LS014", "station 14"],
  "term_type": "county_internal",
  "industry_equivalent": "wet well pump station",
  "dfs_designation": "LS-014",
  "definition": "Submersible pump station and wet well located at [address/coordinates]. Controls flow from [upstream zone] to [downstream treatment point]. Equipped with [pump model].",
  "related_terms": ["wet well", "submersible pump", "check valve"],
  "related_sops": ["WW-SOP-002"],
  "source": "DFS Spec Vol 3, Section 4.2 / Field observation",
  "added_by": "William Marceau",
  "added_date": "2026-05-10",
  "last_verified": "2026-05-10",
  "tags": ["pump station", "wet well", "DFS", "lift station", "field equipment"]
}
```

### Term Types

| Type | Description |
|------|-------------|
| `county_internal` | Term coined internally — no industry equivalent |
| `dfs_vendor` | Term from DFS system documentation |
| `industry_standard` | Standard I&E / wastewater terminology |
| `hybrid` | County uses industry term but with local meaning variation |

---

## Data Sources (What William Feeds In)

| Source | Format | Priority |
|--------|--------|----------|
| DFS vendor spec documents | PDF/text → William pastes excerpts | High |
| Field observations | William describes what he sees | High |
| Conversations with senior staff | William logs what he learns verbally | High |
| County internal documents | Any text William has access to | Medium |
| Equipment manuals | Relevant sections | Medium |

**William never commits raw county documents to git.** He types up or paraphrases the knowledge.
`data/collier-county/` is `.gitignore`d for sensitive content.

---

## Ingestion Interface

### Option A — Telegram Quick Entry (for field use)
> "KB add: 'the rack' = county term for the MCC panel in the main control room.
>  DFS calls it CP-001. Contains breakers and PLCs for zones 1–4."

Panacea:
1. Parses the entry
2. Creates structured JSON entry
3. Confirms back to William: "Added KB entry #047: 'the rack' → CP-001"

### Option B — Bulk Entry via Claude Code (Mac)
William pastes a section of spec text → Claude extracts all identifiable terms and definitions
→ Staged list for William to approve/reject/edit → Committed to knowledge base

### Option C — Interview Mode
> "KB interview: tell me about lift station 14"

Panacea asks structured questions:
- "What does the county call it?"
- "What does DFS call it?"
- "Where is it located?"
- "What does it control?"
- "Any quirks or common failure points?"

Generates entry from William's answers.

---

## Query Interface

### Telegram Queries
| Query | Response |
|-------|----------|
| "What is the rack?" | Returns definition + DFS designation + related terms |
| "KB search: pump station" | Returns all entries tagged with pump station |
| "What does LS-014 map to?" | Returns county name + definition |
| "Related SOPs for lift station 14" | Returns linked SOP list |

### During SOP Writing (Claude Code)
When generating an SOP, Claude can query the knowledge base to:
- Auto-populate the Definitions section with accurate county-specific terms
- Verify that terminology used in procedures is consistent with county standard
- Flag terms that appear in the SOP but aren't in the knowledge base yet

---

## File Structure

```
projects/industrial-ops/src/knowledge_base/
├── __init__.py
├── kb_manager.py         # Add, update, delete entries
├── kb_search.py          # Keyword + semantic search
├── kb_ingest.py          # Bulk text → structured entries
├── kb_export.py          # Export as markdown/PDF glossary
└── data/
    └── entries.json      # The knowledge base itself (local)

projects/industrial-ops/data/collier-county/
├── .gitignore            # Ignore sensitive county docs
├── sops/                 # Generated SOP PDFs
└── kb_notes/             # William's raw field notes (not committed)
```

---

## Milestones

### Milestone 1 — Manual Phase (No Code Required)
Start capturing knowledge immediately — no tool needed yet.

- [ ] William starts a running notes file: `data/collier-county/kb_notes/raw_terms.md`
- [ ] Format: one term per section, rough notes are fine
- [ ] Target: 20–30 entries in first month (DFS terms, county names, alarm codes)
- [ ] Panacea can search this flat file via Telegram in the meantime

### Milestone 2 — Structured Data Layer (Week 3–4)
- [ ] Build `kb_manager.py` — CRUD operations on `entries.json`
- [ ] Build `kb_search.py` — keyword search across term, aliases, tags, definition
- [ ] Migrate raw notes into structured JSON entries
- [ ] Telegram command: "KB search [term]" → returns formatted result

### Milestone 3 — Ingestion Tools (Week 5–6)
- [ ] `kb_ingest.py` — paste spec text → Claude extracts terms → staged for approval
- [ ] Interview mode via Telegram
- [ ] Bulk import from DFS spec sections

### Milestone 4 — SOP Integration (Week 7+)
- [ ] SOP Builder queries knowledge base during generation
- [ ] Auto-populates Definitions section with KB entries
- [ ] Flags undefined terms during SOP review

### Milestone 5 — Glossary Export (Week 8+)
- [ ] `kb_export.py` — generates formatted PDF glossary of all entries
- [ ] Organized by term type and tag
- [ ] This document alone is a deliverable worth showing to the department head

---

## Long-Term Value Statement

When this knowledge base reaches 200+ entries it becomes:

1. **An onboarding tool** — new I&E techs get up to speed in days instead of months
2. **A compliance asset** — consistent terminology in SOPs and reports
3. **An institutional memory layer** — knowledge that doesn't retire when senior staff do
4. **William's strongest argument for recognition** — he built something the county cannot replace

No outside AI vendor or consultant could build this without William's domain access and
field experience. That is the moat.

---

## Conflict of Interest Note

The knowledge base contains no proprietary county data in the git repo.
William paraphrases and types up what he learns — the raw spec documents stay off the repo.
The tool itself (the code) is William's intellectual property.
The content (what he types in) is county knowledge he has documented — same as any employee
writing notes. This is standard practice and not a conflict of interest.
