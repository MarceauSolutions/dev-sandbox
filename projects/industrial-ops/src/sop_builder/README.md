# SOP Builder

Generate Collier County Standard Operating Procedures as markdown + PDF.

## Status
- **Milestone 1**: First SOP deliverable workflow — ✅ ready (run with structured JSON)
- **Milestone 2**: `sop_generator.py` CLI — ✅ done
- **Milestone 3**: Telegram interface via Panacea — pending
- **Milestone 4**: SOP library index + versioning — pending

## Usage

### Mode 1 — Structured JSON input (recommended)
```bash
python3 projects/industrial-ops/src/sop_builder/sop_generator.py \
    --input projects/industrial-ops/src/sop_builder/examples/front_desk_example.json \
    --output-dir projects/industrial-ops/data/output
```

### Mode 2 — Rough notes (uses Claude API to structure)
```bash
python3 projects/industrial-ops/src/sop_builder/sop_generator.py \
    --input my_notes.txt \
    --from-notes \
    --sop-number WW-SOP-002 \
    --title "Lift Station Inspection" \
    --department "Wastewater Operations" \
    --prepared-by "William Marceau, I&E Technician" \
    --output-dir projects/industrial-ops/data/output
```

`--from-notes` requires `ANTHROPIC_API_KEY` in environment.

## Output
- `WW-SOP-001_<slug>.md` — source markdown (editable)
- `WW-SOP-001_<slug>.pdf` — county-styled PDF (deliverable)

## Styling
County-neutral: Arial, navy `#1a2f4f` headers, letter-size, no brand colors.
No Marceau Solutions gold/charcoal. Override via `county_sop.css`.

## Schema (JSON input)
See `examples/front_desk_example.json`. Required fields:
- `sop_number`, `title`, `department`, `version`, `effective_date`
- `prepared_by`, `approved_by`
- `purpose`, `scope`, `procedure`

Optional: `definitions`, `responsibilities`, `exceptions`, `references`, `revision_history`.

## Dependencies
`pip install markdown weasyprint anthropic` (anthropic only needed for `--from-notes` mode).

## Conflict-of-interest note
This tool generates documents for William's internal Collier County work. Output uses
county-neutral styling, not Marceau Solutions branding. See `../../CLAUDE.md`.
