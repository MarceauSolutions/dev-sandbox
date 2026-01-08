# Workflow: Live Editing Session

## Purpose
Enable real-time interactive editing of a PowerPoint presentation while the user has it open on screen. User can describe changes and watch them happen immediately.

## When to Use
- User says "I have the presentation open..."
- User says "while I'm looking at it, change..."
- User says "let me watch you make edits..."
- User wants to iterate on presentation interactively

## Prerequisites
- Presentation file exists in `.tmp/`
- macOS (for AppleScript refresh functionality)
- PowerPoint or Keynote installed

## Steps

### Step 1: Start Live Session
Initialize the session with the target file:

```bash
python execution/live_editor.py --start ".tmp/[FILE].pptx" --open
```

**Expected output:**
```
✅ Live session started for [FILE].pptx
   📊 Slides: [N]
   📁 File: /path/to/.tmp/[FILE].pptx
   💾 Backup: .tmp/[FILE].backup.pptx
```

The `--open` flag opens the file in the default application.

### Step 2: Verify Session Active
Check session status:

```bash
python execution/live_editor.py --status
```

**Expected output:** File path, slide count, edit count, backup location

### Step 3: List Slides (if needed)
Get overview of presentation structure:

```bash
python execution/live_editor.py --list
```

**Expected output:** Numbered list of slides with titles and image indicators

### Step 4: Make Text Edits
When user requests text changes:

```bash
python execution/live_editor.py --edit-text \
  --slide [N] \
  --find "old text" \
  --replace "new text"
```

**Expected output:**
```
✅ Replaced [N] occurrence(s) on slide [N]
   🔄 PowerPoint refreshed
```

The presentation auto-refreshes after each edit.

### Step 5: Add Images
When user wants to add an image:

```bash
python execution/live_editor.py --add-image \
  --slide [N] \
  --image .tmp/[IMAGE].jpeg \
  --position left \
  --width 5.0
```

**Position options:** `left`, `right`, `center`

### Step 6: Manual Refresh (if needed)
If auto-refresh didn't trigger:

```bash
python execution/live_editor.py --refresh
```

### Step 7: Revert Changes (if needed)
If user wants to undo all changes:

```bash
python execution/live_editor.py --revert
```

This restores the backup created at session start.

### Step 8: End Session
When done editing:

```bash
python execution/live_editor.py --end
```

## Common Edit Patterns

### Pattern: Change Title on Slide
```bash
python execution/live_editor.py --edit-text --slide 1 --find "Old Title" --replace "New Title"
```

### Pattern: Update Company Name Throughout
```bash
# Check which slides have the text first
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action list

# Edit each occurrence
python execution/live_editor.py --edit-text --slide 1 --find "Old Company" --replace "New Company"
python execution/live_editor.py --edit-text --slide 3 --find "Old Company" --replace "New Company"
```

### Pattern: Fix Typo
```bash
python execution/live_editor.py --edit-text --slide [N] --find "teh" --replace "the"
```

### Pattern: Add Image to Experience Slide
```bash
python execution/live_editor.py --add-image --slide 14 --image .tmp/exp_img_1.jpeg --position left --width 5.0
```

## Session State

The live session tracks:
- **file**: Current PPTX file path
- **backup**: Backup file for revert capability
- **slide_count**: Number of slides
- **edit_count**: Number of edits made
- **edits**: History of all edits (type, slide, details, timestamp)

Session file location: `.tmp/live_session.json`

## Verification
- [ ] Presentation opens in PowerPoint/Keynote
- [ ] Edits are visible after each command
- [ ] Status shows correct edit count
- [ ] Backup file exists

## Troubleshooting

### Text Not Found
The find text must match exactly. Use inspect to see actual text:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide [N]
```

### PowerPoint Doesn't Refresh
Try manual refresh:
```bash
python execution/live_editor.py --refresh
```

Or close and reopen the file:
```bash
open ".tmp/[FILE].pptx"
```

### No Active Session Error
Start a session first:
```bash
python execution/live_editor.py --start ".tmp/[FILE].pptx"
```

### Lost Changes
Check if backup exists and revert is possible:
```bash
python execution/live_editor.py --status
```

## Scripts Used
- `execution/live_editor.py` - Main live editing script
- `execution/pptx_editor.py` - For inspection and complex edits

## Related Workflows
- [reformat-experience-slides.md](reformat-experience-slides.md) - For bulk reformatting
- [template-mode.md](template-mode.md) - For starting from existing presentation
