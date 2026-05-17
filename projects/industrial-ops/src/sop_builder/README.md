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

### Mode 4 — From iPhone via Telegram (the real workflow)

The full hands-free path:
1. At work, pull out your phone.
2. Open Google Drive app → Scan (camera icon) → scan paper docs into your SOP folder
   (e.g. `SOP-Front-Desk-Notes`). Each scan saves as a PDF.
3. Open Telegram → `@w_marceaubot` → send a message like:
   > "Make me an SOP from `SOP-Front-Desk-Notes`, number WW-SOP-001, title Front Desk Agent Daily Procedures"
4. Panacea recognizes the request, runs `make_sop.py` with `--deliver`, and sends the PDF
   back to your Telegram chat within ~1-2 minutes.

**One-time setup (literally one command):**
```bash
bash projects/industrial-ops/src/sop_builder/setup_drive_auth.sh
```
This opens a browser, asks you to approve Drive read access for your Google account,
saves the refresh token locally, and SCPs it to EC2 — all in one shot. You only do
this once. After that, everything is hands-free from your phone.

**Battle-tested (2026-05-14):**
- `telegram_send_file.py` send works from both Mac and EC2 ✓
- `sop_generator.py` JSON mode produces clean PDF on Mac and EC2 ✓
- Python 3.9 compat (EC2 runtime) ✓
- Error path (invalid folder) handled gracefully ✓
- Panacea system prompt updated with the new tool invocation ✓
- Drive end-to-end pending: needs you to run `setup_drive_auth.sh` once

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

## Wrapper script: `make_sop.py`

`make_sop.py` is the end-to-end orchestrator that Panacea invokes from Telegram.
It runs `sop_generator.py --gdrive-folder` and optionally delivers the resulting
PDF to William's Telegram chat via `execution/telegram_send_file.py`.

```bash
python3 projects/industrial-ops/src/sop_builder/make_sop.py \
    --gdrive-folder "SOP-Lift-Station-Notes" \
    --sop-number WW-SOP-002 \
    --title "Lift Station Daily Inspection" \
    --department "Wastewater Operations" \
    --prepared-by "William Marceau, I&E Technician" \
    --output-dir projects/industrial-ops/data/output \
    --deliver
```

`--deliver` is the magic flag — it pipes the PDF to Telegram so you get the file
on your phone without touching the EC2 filesystem.

## Dependencies

### Python packages
```
pip install markdown weasyprint anthropic \
    google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
- `anthropic` only needed for `--from-notes` / `--gdrive-folder` modes
- `google-*` only needed for `--gdrive-folder` mode

### System packages (for weasyprint)
WeasyPrint links against native libraries. Without these, you get cryptic GObject errors:

| OS | Command |
|---|---|
| macOS | `brew install pango cairo gdk-pixbuf libffi` |
| Amazon Linux 2023 / RHEL | `sudo dnf install -y pango cairo gdk-pixbuf2 libffi` |
| Debian / Ubuntu | `sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0` |

### Model override
The default Claude model for notes structuring and PDF OCR is `claude-opus-4-7`. To
override: `export SOP_BUILDER_MODEL=claude-sonnet-4-6` (or whatever).

## Conflict-of-interest note
This tool generates documents for William's internal Collier County work. Output uses
county-neutral styling, not Marceau Solutions branding. See `../../CLAUDE.md`.
