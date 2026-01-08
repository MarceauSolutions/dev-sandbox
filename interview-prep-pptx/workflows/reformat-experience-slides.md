# Workflow: Reformat Experience Slides

## Purpose
Standardize experience slides (typically slides 14-18) to match a target slide's layout, colors, and formatting. This ensures visual consistency across all slides that tie resume experience to the role.

## When to Use
- User says "make slides X look like slide Y"
- User says "standardize the experience slides"
- User says "use the same format/theme as slide N"
- Experience slides have inconsistent layouts after generation

## Prerequisites
- Active presentation file in `.tmp/`
- Live editing session started (optional but recommended)
- Research JSON file for experience data (optional, for accurate content)

## Steps

### Step 1: Identify Target Slide Layout
Inspect the target slide to understand its structure:

```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide [TARGET_SLIDE_NUM]
```

**Expected output:** Shape positions, sizes, and content. Note:
- Background color/type
- Title position (e.g., 0.55", 0.3")
- Image position (e.g., 0.75", 1.5")
- Description position (e.g., 6.55", 1.5")
- Relevance section position (e.g., 6.55", 4.5")
- Presence/absence of accent bars

### Step 2: Inspect Source Slides
Check current state of slides to be reformatted:

```bash
for slide in 14 15 16 17 18; do
  echo "=== SLIDE $slide ==="
  python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide $slide 2>&1 | head -25
done
```

**Note differences:** accent bars, title format, text positions, "Why it matters" vs "Relevance:" labels

### Step 3: Run Reformat Script
Execute the reformatting script with research data:

```bash
python execution/reformat_experience_slides.py \
  --input ".tmp/[FILE].pptx" \
  --research ".tmp/interview_research_[company].json" \
  --slides "14,15,16,17,18"
```

**Expected output:**
```
============================================================
Reformatting Experience Slides
============================================================

📝 Slide 14: [Title]
   ✓ Reformatted with navy background and consistent layout
📝 Slide 15: [Title]
   ✓ Reformatted with navy background and consistent layout
...
✅ Saved to: .tmp/[FILE].pptx
```

### Step 4: Refresh Presentation
If user has file open, refresh to show changes:

```bash
python execution/live_editor.py --refresh
```

### Step 5: Verify Changes
Inspect a reformatted slide to confirm:

```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action inspect --slide 14
```

**Expected layout:**
- Shape[0]: TEXT_BOX at (0.55", 0.3") - Title
- Shape[1]: PICTURE at (0.75", 1.5") - Image
- Shape[2]: TEXT_BOX at (6.55", 1.5") - Description
- Shape[3]: TEXT_BOX at (6.55", 4.5") - Relevance section

### Step 6: List All Slides
Confirm slide titles are now descriptive:

```bash
python execution/live_editor.py --list
```

## Target Layout Specification

The "professional" experience slide format:

| Element | Position | Size | Style |
|---------|----------|------|-------|
| Background | Full slide | 13.33" × 7.5" | Navy (#003366) |
| Title | (0.55", 0.3") | 12.23" × 0.54" | 28pt, white, bold |
| Image | (0.75", 1.5") | 5.0" wide | Aspect ratio preserved |
| Description | (6.55", 1.5") | 5.9" × 2.5" | 14pt, white |
| Relevance Header | (6.55", 4.5") | - | 14pt, white, bold |
| Relevance Text | Below header | 5.9" × 2.0" | 12pt, white |

## Verification
- [ ] All target slides have navy background
- [ ] No accent bars present
- [ ] Titles are descriptive (not "Relevant Experience (1)")
- [ ] Images preserved in correct position
- [ ] "Relevance:" header is bold
- [ ] Relevance text is on separate line from header

## Troubleshooting

### Images Not Preserved
The reformat script extracts and re-adds images. If images are missing:
```bash
# Re-add images manually
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 14 --new-image .tmp/exp_img_1.jpeg --position left --width 5.0
```

### Wrong Experience Content
If content doesn't match, check research JSON:
```bash
cat .tmp/interview_research_[company].json | python -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('experience_highlights', []), indent=2))"
```

### Text Formatting Issues
For fine-grained text edits after reformatting:
```bash
python execution/live_editor.py --edit-text --slide 14 --find "old text" --replace "new text"
```

## Scripts Used
- `execution/reformat_experience_slides.py` - Main reformatting script
- `execution/pptx_editor.py` - Inspection and manual edits
- `execution/live_editor.py` - Session management and refresh

## Related Workflows
- [live-editing-session.md](live-editing-session.md) - For interactive editing
- [add-images-to-slides.md](add-images-to-slides.md) - For adding images separately
