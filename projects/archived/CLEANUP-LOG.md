# Archived Folders Cleanup Log

This directory contains archived folders that were removed from active development for various reasons.

## Archive Log

### 2026-01-20: global-utility/shared/

**Reason:** 100% duplicate of files already present in `/Users/williammarceaujr./dev-sandbox/execution/`

**Original Location:** `/Users/williammarceaujr./dev-sandbox/projects/global-utility/shared/`

**Archived Location:** `/Users/williammarceaujr./dev-sandbox/projects/archived/2026-01-20-global-utility-shared/shared/`

**Files Archived:**
- `ai/grok_image_gen.py` (duplicate of `execution/grok_image_gen.py`)
- `analytics/revenue_analytics.py` (duplicate of `execution/revenue_analytics.py`)
- `communication/twilio_sms.py` (duplicate of `execution/twilio_sms.py`)
- `google/gmail_monitor.py` (duplicate of `execution/gmail_monitor.py`)
- `google/google_auth_setup.py` (duplicate of `execution/google_auth_setup.py`)
- `utils/google_auth_setup.py` (duplicate of `execution/google_auth_setup.py`)
- `utils/grok_image_gen.py` (duplicate of `execution/grok_image_gen.py`)
- `utils/markdown_to_pdf.py` (duplicate of `execution/markdown_to_pdf.py`)
- `README.md`

**Verification Performed:**
- Confirmed files are byte-for-byte identical using `diff` command
- Searched codebase - no Python files import from `global-utility/shared`
- Only documentation files reference the path (analysis reports, Ralph migration scripts)

**Active Equivalents:** All functionality exists in `/Users/williammarceaujr./dev-sandbox/execution/`

**Recovery Instructions:** If needed, files can be restored from:
```bash
/Users/williammarceaujr./dev-sandbox/projects/archived/2026-01-20-global-utility-shared/shared/
```

**Decision:** Moved to archive (not deleted) to allow recovery if unexpected dependencies surface.

---

## Archive Guidelines

When archiving folders:
1. Create date-stamped directory: `YYYY-MM-DD-descriptive-name/`
2. Document reason for archival
3. List original and archived locations
4. Verify no active code references the archived path
5. Commit archive with descriptive message
