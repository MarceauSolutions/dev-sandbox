# Workflow: Template Mode (Continue from Existing Presentation)

## Purpose
Load an existing PowerPoint presentation and continue editing it, rather than generating a new one from scratch.

## When to Use
- User says "I have a presentation from last night..."
- User says "continue editing my existing PowerPoint..."
- User says "use this file as a starting point..."
- User references a specific `.pptx` file in `.tmp/`
- User provides a `.pptx` file to the `docs/` folder

## Prerequisites
- Existing `.pptx` file in `.tmp/` or `docs/`
- For content edits: original research JSON (optional but helpful)

## Steps

### Step 1: Locate the Template
List available templates:
```bash
python execution/template_manager.py --list
```

**Expected output:**
```
============================================================
Available Templates (N found)
============================================================

  interview_prep_company.pptx
    └─ Company Name | Role | N slides
    └─ Modified: 2026-01-08T...
```

### Step 2: Copy User's File (if from docs/)
If user provided a file in `docs/`:
```bash
cp "interview-prep-pptx/docs/[FILENAME].pptx" ".tmp/[FILENAME].pptx"
```

### Step 3: Load Template Info
Inspect the template structure:
```bash
python execution/template_manager.py --load ".tmp/[FILE].pptx"
```

**Expected output:** Slide structure with titles and image counts

### Step 4: Extract Company/Role
Get metadata from template:
```bash
python execution/template_manager.py --load ".tmp/[FILE].pptx" --extract-info
```

### Step 5: Create Editing Session
```bash
python execution/template_manager.py --load ".tmp/[FILE].pptx" --create-session
```

**Expected output:**
```
✅ Session created!
   Session ID: [timestamp]
   File: [filename]
   Company: [extracted company]
   Role: [extracted role]
```

### Step 6: List Slides
See current slide structure:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action list
```

### Step 7: Start Live Editing
For interactive changes:
```bash
python execution/live_editor.py --start ".tmp/[FILE].pptx" --open
```

### Step 8: Make Edits
Use live editor or pptx_editor for changes:

**Text edit:**
```bash
python execution/live_editor.py --edit-text --slide [N] --find "old" --replace "new"
```

**Add image:**
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide [N] --new-image .tmp/exp_img_1.jpeg --position left --width 5.0
```

## Copy to New File (Non-destructive)

To preserve original while editing:
```bash
python execution/template_manager.py --load ".tmp/[FILE].pptx" --copy-to ".tmp/[FILE]_v2.pptx"
```

Then work with the copy.

## Regenerate with New Theme

If research JSON exists, regenerate with different theme:
```bash
python execution/pptx_generator.py \
  --input ".tmp/interview_research_[company].json" \
  --theme professional
```

## File Formats

| Format | Support | Notes |
|--------|---------|-------|
| `.pptx` | Full | Native format, recommended |
| `.key` | Read-only | Keynote files must be exported to PPTX first |
| `.ppt` | Limited | Old format, may have issues |

**To convert .key to .pptx:**
1. Open in Keynote
2. File → Export To → PowerPoint
3. Save to `.tmp/` folder

## Verification
- [ ] Template loaded successfully
- [ ] Session created
- [ ] Slide list shows expected structure
- [ ] Edits are saved to file

## Troubleshooting

### File Not Found
Check file path and name:
```bash
ls -la .tmp/*.pptx
```

### Keynote File (.key)
Cannot read directly. Export to PPTX from Keynote first.

### Missing Images After Reload
Images may have been removed during editing. Re-add:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide [N] --new-image .tmp/exp_img_1.jpeg --position left
```

## Scripts Used
- `execution/template_manager.py` - Template loading and session creation
- `execution/pptx_editor.py` - Inspection and editing
- `execution/live_editor.py` - Interactive editing session

## Related Workflows
- [live-editing-session.md](live-editing-session.md) - After loading template
- [add-images-to-slides.md](add-images-to-slides.md) - Adding images from previous session
- [reformat-experience-slides.md](reformat-experience-slides.md) - Standardizing slide formats
