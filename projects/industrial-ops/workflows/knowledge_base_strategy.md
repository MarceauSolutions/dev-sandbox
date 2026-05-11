# Wastewater Knowledge Base — Strategy

**Tower:** industrial-ops
**Priority:** 2

---

## The Problem

Collier County Wastewater Management uses a mix of:
- **Industry-standard terminology** (e.g., SCADA, PLC, 4-20mA loop, RTU)
- **Internally-coined terminology** specific to Collier County operations
- **DFS vendor-specific terminology** from proprietary system specs

This creates tribal knowledge — staff who've been there 10+ years know what things mean;
new hires (like William) have to learn an undocumented internal language.

---

## The Solution

A searchable knowledge base that:
1. Stores term definitions, disambiguations, and context
2. Links county-specific terms to industry-standard equivalents where applicable
3. Notes DFS-specific system names and what they correspond to
4. Is queryable via Telegram: "What is [term]?" → Panacea looks it up and responds

---

## Data Ingestion (Manual Phase)

William reads specs and field documents, then feeds entries in one of two formats:

**Quick entry (Telegram):**
> "KB add: 'lift station 14' = county name for the wet well and pump station at [location]. DFS system calls it LS-014."

**Bulk entry (via Claude Code on Mac):**
Paste raw spec text → Claude extracts terms + definitions → staged for William to approve

---

## Entry Structure

```json
{
  "term": "lift station 14",
  "county_name": true,
  "industry_equivalent": "wet well pump station",
  "dfs_designation": "LS-014",
  "definition": "Wet well and submersible pump station at [location]. Controls flow to [downstream point].",
  "source": "DFS Spec Vol 3, Section 4.2",
  "added": "2026-05-10",
  "tags": ["pump station", "wet well", "DFS", "lift station"]
}
```

---

## Query Interface

Via Panacea (Telegram):
- "What is a [term]?"
- "What does [county term] map to in industry standard?"
- "KB search: [keyword]"

Via Claude Code (Mac):
- Direct database queries during SOP writing to ensure accurate terminology

---

## Long-Term Value

Once populated, this knowledge base:
- Accelerates onboarding of new I&E techs
- Enables faster SOP generation (terms auto-populated)
- Creates a institutional memory layer that doesn't leave when people retire
- Is William's strongest argument for salary recognition — he built something irreplaceable
