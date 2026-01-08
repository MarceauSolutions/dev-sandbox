# Workflow: Add Images to Slides

## Purpose
Add images from a previous session (or new images) to experience slides in an existing presentation.

## When to Use
- User says "add the images from last night"
- User says "put exp_img files on the slides"
- User has `exp_img_*.jpeg` files in `.tmp/`
- Experience slides are missing images after regeneration

## Prerequisites
- Existing `.pptx` file in `.tmp/`
- Image files (typically `exp_img_1.jpeg` through `exp_img_5.jpeg`)
- Live session started (optional but recommended)

## Steps

### Step 1: Check Available Images
List images in `.tmp/`:
```bash
ls -la .tmp/exp_img_*.jpeg 2>/dev/null || echo "No exp_img files found"
```

**Expected output:**
```
-rw-r--r--  1 user  staff  113551 Jan  7 23:13 .tmp/exp_img_1.jpeg
-rw-r--r--  1 user  staff   70567 Jan  7 23:13 .tmp/exp_img_2.jpeg
-rw-r--r--  1 user  staff  134722 Jan  7 23:13 .tmp/exp_img_3.jpeg
-rw-r--r--  1 user  staff  118625 Jan  7 23:14 .tmp/exp_img_4.jpeg
-rw-r--r--  1 user  staff  170267 Jan  7 23:14 .tmp/exp_img_5.jpeg
```

### Step 2: Identify Target Slides
List slides to find experience slides (typically 14-18):
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action list
```

Look for slides with "Relevant Experience" or experience-related titles.

### Step 3: Add Images to Each Slide
For each image/slide pair:

```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 14 --new-image .tmp/exp_img_1.jpeg --position left --width 4.5

python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 15 --new-image .tmp/exp_img_2.jpeg --position left --width 4.5

python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 16 --new-image .tmp/exp_img_3.jpeg --position left --width 4.5

python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 17 --new-image .tmp/exp_img_4.jpeg --position left --width 4.5

python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
  --slide 18 --new-image .tmp/exp_img_5.jpeg --position left --width 4.5 --open
```

The `--open` flag on the last command opens the file to view results.

### Step 4: Using Live Editor (Alternative)
If live session is active:
```bash
python execution/live_editor.py --add-image --slide 14 --image .tmp/exp_img_1.jpeg --position left --width 4.5
```

This auto-refreshes the open presentation.

## Image Position Options

| Position | Left | Top | Best For |
|----------|------|-----|----------|
| `left` | 0.75" | 1.5" | Two-column layouts |
| `right` | 7.5" | 1.5" | Text on left |
| `center` | 4.0" | 2.0" | Full-width layouts |

## Image Sizing

| Width | Use Case |
|-------|----------|
| 4.5" | Standard two-column |
| 5.0" | Larger image emphasis |
| 6.0" | Half-page image |
| 10.0" | Full-width image |

Height is automatically calculated to preserve aspect ratio.

## Batch Add Script

For convenience, create a one-liner:
```bash
for i in 1 2 3 4 5; do
  python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action add-image \
    --slide $((13 + i)) --new-image ".tmp/exp_img_$i.jpeg" --position left --width 4.5
done
```

Adjust slide numbers as needed.

## Image Mapping

Standard mapping for experience slides:

| Image | Slide | Experience |
|-------|-------|------------|
| exp_img_1.jpeg | 14 | First experience highlight |
| exp_img_2.jpeg | 15 | Second experience highlight |
| exp_img_3.jpeg | 16 | Third experience highlight |
| exp_img_4.jpeg | 17 | Fourth experience highlight |
| exp_img_5.jpeg | 18 | Fifth experience highlight |

## Verification
After adding images, verify:
```bash
python execution/pptx_editor.py --input ".tmp/[FILE].pptx" --action list | grep "🖼"
```

Should show image indicators on target slides:
```
  14. Experience Title [🖼 1]
  15. Experience Title [🖼 1]
  ...
```

## Troubleshooting

### Image Not Found
Check file exists and path is correct:
```bash
ls -la .tmp/exp_img_1.jpeg
```

### Image Added in Wrong Position
Remove and re-add with correct position. Or use reformat workflow to rebuild slide.

### Images from Wrong Session
Image files persist between sessions. Check modification dates:
```bash
ls -la .tmp/exp_img_*.jpeg
```

If dates don't match current session, regenerate images:
```bash
source .env && python execution/interview_research.py \
  --company "[COMPANY]" --role "[ROLE]" --resume "[RESUME]" --generate-images
```

## Scripts Used
- `execution/pptx_editor.py` - Primary tool for adding images
- `execution/live_editor.py` - For live session image additions

## Related Workflows
- [reformat-experience-slides.md](reformat-experience-slides.md) - Reformats slides and preserves images
- [live-editing-session.md](live-editing-session.md) - For interactive image additions
- [generate-presentation.md](generate-presentation.md) - Generates new images with `--generate-images`
