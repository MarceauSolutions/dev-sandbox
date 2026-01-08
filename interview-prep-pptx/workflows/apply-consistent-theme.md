# Workflow: Apply Consistent Theme Across All Slides

## Purpose
Apply a consistent visual theme (navy background, white text, no accent bars) across all slides in a presentation, matching the style of the "professional" experience slides.

## When to Use
- User says "make all slides look like slide X"
- User says "apply consistent theme/style"
- User says "slides have different backgrounds"
- Slides 1-N have different formatting than later slides
- Presentation has mixed themes or inconsistent styling

## Prerequisites
- Existing `.pptx` file in `.tmp/`
- Live editing session started (optional)

## Steps

### Step 1: Identify Inconsistencies
Inspect slides to see differences:

```bash
# Check a slide with old format
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide 3

# Check a slide with target format
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide 19
```

**Look for:**
- Accent bars (thin AUTO_SHAPE at 0.15" height)
- Different background colors
- Text colors that aren't white

### Step 2: Apply Navy Theme
Run the theme application script:

```bash
python execution/apply_navy_theme.py --input ".tmp/[FILE].pptx" --slides "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18"
```

**For all slides:**
```bash
python execution/apply_navy_theme.py --input ".tmp/[FILE].pptx"
```

**Expected output:**
```
============================================================
Applying Navy Theme
============================================================

✅ Processed N of M slides
   Output: .tmp/[FILE].pptx
   Accent bars removed: X

📋 Changes by slide:
   ✓ Slide 1: Navy background, white text
   ✓ Slide 2: Navy background, white text
   ✓ Slide 3: Navy background, white text (removed 1 accent bar)
   ...
```

### Step 3: Refresh/Reopen Presentation
```bash
python execution/live_editor.py --refresh
```

Or reopen:
```bash
open ".tmp/[FILE].pptx"
```

### Step 4: Verify Changes
Inspect a previously inconsistent slide:

```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide 3
```

**Confirm:**
- No thin AUTO_SHAPE (accent bar) present
- Background shape has navy fill
- Text is white

## What the Script Does

The `apply_navy_theme.py` script:

1. **Removes accent bars** - Deletes thin horizontal shapes (< 0.5" height)
2. **Sets navy background** - Changes background color to #1A1A2E (dark navy)
3. **Updates text to white** - Sets all text colors to #FFFFFF

## Theme Specifications

| Element | Value |
|---------|-------|
| Background | Dark Navy #1A1A2E |
| Text Color | White #FFFFFF |
| Accent (if needed) | Orange #FF9900 |
| Accent Bars | Removed |

## Slide Types Handled

| Slide Type | Changes Applied |
|------------|-----------------|
| Title slides | Background + text color |
| Section dividers | Background + text color |
| Content slides | Background + text + remove accent bar |
| Experience slides | Background + text (already formatted) |
| Closing slides | Background + text color |

## Verification Checklist
- [ ] All slides have navy background
- [ ] No visible accent bars
- [ ] All text is readable (white on navy)
- [ ] Images preserved
- [ ] Slide content intact

## Troubleshooting

### Text Not Visible
If text disappears, it may have been navy on navy. Check slide content:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide [N]
```

### Accent Bar Still Visible
Run script again or manually check for shapes:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide [N]
```
Look for AUTO_SHAPE with height < 0.5".

### Need to Revert
Use backup from live session:
```bash
python execution/live_editor.py --revert
```

## Scripts Used
- `execution/apply_navy_theme.py` - Main theme application script
- `execution/pptx_editor.py` - For inspection and verification
- `execution/live_editor.py` - For session management and refresh

## Related Workflows
- [reformat-experience-slides.md](reformat-experience-slides.md) - For experience slides specifically
- [live-editing-session.md](live-editing-session.md) - For interactive editing
