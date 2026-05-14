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

### Mode 3 — Google Drive folder (scan with phone, generate from anywhere)

**One-time setup:**
1. Open the Google Drive app on your phone.
2. Create a folder for SOP source material (e.g. `SOP-Front-Desk-Notes`).
3. Use the Drive Scanner (camera icon → Scan) to scan paper notes, training docs,
   or process sketches. Save them to that folder. You can also drop typed notes
   (`.txt`, `.md`), Google Docs, or photos in the same folder.
4. The first time you run with `--gdrive-folder`, a browser tab opens asking for
   read-only Drive access. Approve. The token is saved to `token_drive_readonly.json`
   and reused forever after.

**Then anytime:**
```bash
python3 projects/industrial-ops/src/sop_builder/sop_generator.py \
    --gdrive-folder "SOP-Front-Desk-Notes" \
    --sop-number WW-SOP-001 \
    --title "Front Desk Agent Daily Procedures" \
    --department "Wastewater Operations" \
    --output-dir projects/industrial-ops/data/output \
    --save-notes /tmp/combined_notes.txt
```

What happens under the hood:
1. Drive API lists every file in that folder.
2. PDFs and images are sent to Claude vision for verbatim transcription
   (Drive Scanner output is scanned PDFs — Claude OCRs them).
3. Google Docs are exported as plain text.
4. All text is concatenated with `=== Source: filename ===` headers.
5. The combined text feeds the same `--from-notes` Claude structuring pass.
6. Markdown + PDF are written to `--output-dir`.

**Requirements:** `ANTHROPIC_API_KEY` in env (for OCR + structuring), `credentials.json`
in repo root (Google OAuth client — already present from existing Gmail/Sheets setup).

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
```
pip install markdown weasyprint anthropic \
    google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
- `anthropic` only needed for `--from-notes` / `--gdrive-folder` modes
- `google-*` only needed for `--gdrive-folder` mode

## Conflict-of-interest note
This tool generates documents for William's internal Collier County work. Output uses
county-neutral styling, not Marceau Solutions branding. See `../../CLAUDE.md`.
