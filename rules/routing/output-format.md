# Output Format Rules

> Summary version lives in `rules/routing/ROUTING.md` tree #2.

## Decision Table

| I am producing... | Format | Tool / Location |
|-------------------|--------|----------------|
| Guide, SOP, report, proposal, document | Branded PDF | `execution/branded_pdf_engine.py` |
| Leads, contacts, enriched data | CSV | `projects/[name]/output/[name]-YYYY-MM-DD.csv` |
| Pipeline/API results | JSON | `projects/[name]/output/` or pipeline.db |
| Real-time data display | Web app | FastAPI, not a static file |
| Quick answer to William now | Plain text | Conversation response |
| Internal note / agent-readable | Markdown | `docs/` or project CLAUDE.md |
| Content William reads | Branded PDF | Never raw markdown for William |

## Branded PDF — Quick Reference

```bash
# List all templates
python execution/branded_pdf_engine.py --list-templates

# Generate with content (ALWAYS use content_markdown, not content or sections)
python execution/branded_pdf_engine.py \
  --template generic_document \
  --data '{"title": "My Title", "content_markdown": "# Header\nBody text here"}' \
  --output output/my-doc.pdf

# Open immediately after generating
open output/my-doc.pdf
```

Full template list and required keys: `rules/tools/branded-pdf-engine.md`

## CSV Output — Naming Convention

```
projects/[tower]/[project]/output/[description]-YYYY-MM-DD.csv
```

Example: `projects/marceau-solutions/digital/outputs/naples-ai-prospects-2026-03-23.csv`

Never commit large data CSVs to git (add to .gitignore if needed).

## What Markdown Files Are For

Markdown is appropriate ONLY for:
- SOPs and procedures that Claude reads (in `docs/sops/`)
- Project CLAUDE.md context files (for agents)
- Architecture decisions and internal notes (for developers/agents)
- Code comments and inline documentation

Markdown is NOT appropriate for:
- Any content William reads directly
- Any deliverable shown to a client
- Any report or analysis result
- Any guide or instructions for a user

**Rule**: If William would open it — it should be a PDF or web page.
