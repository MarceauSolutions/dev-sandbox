# Workflow: Generate New Presentation

## Purpose
Create a complete interview preparation PowerPoint from scratch, including company research, resume parsing, and slide generation.

## When to Use
- User says "create interview prep for [company] [role]"
- User says "prepare me for an interview at [company]"
- User says "generate presentation for [company]"
- Starting fresh (no existing presentation to edit)

## Prerequisites
- `ANTHROPIC_API_KEY` set in `.env`
- Resume file (optional): PDF, DOCX, or TXT
- Theme preference (optional): modern, professional, or minimal

## Steps

### Step 1: Gather Requirements
Ask user for:
- **Company name** (required)
- **Role/position** (required)
- **Resume path** (optional)
- **Theme** (optional, default: professional)
- **Generate images** (optional, costs $0.07/image)

### Step 2: Run Research Script
```bash
source .env && python execution/interview_research.py \
  --company "[COMPANY]" \
  --role "[ROLE]" \
  --resume "[PATH_TO_RESUME]" \
  --generate-images  # optional
```

**Expected output:**
```
✅ Research complete!
   Company: [COMPANY]
   Role: [ROLE]
   Output: .tmp/interview_research_[company_slug].json
```

**Without resume:**
```bash
source .env && python execution/interview_research.py \
  --company "[COMPANY]" \
  --role "[ROLE]"
```

### Step 3: Generate PowerPoint
```bash
python execution/pptx_generator.py \
  --input .tmp/interview_research_[company_slug].json \
  --theme professional
```

**Expected output:**
```
✅ PowerPoint created!
   Output: .tmp/interview_prep_[company_slug].pptx
   Slides: [N]
```

### Step 4: Open Presentation
```bash
open .tmp/interview_prep_[company_slug].pptx
```

### Step 5: Start Live Session (optional)
If user wants to make edits:
```bash
python execution/live_editor.py --start ".tmp/interview_prep_[company_slug].pptx"
```

## Company Slug Convention

Convert company name to lowercase with underscores:
- "Apple Inc" → `apple_inc`
- "Brookhaven National Laboratory" → `brookhaven_national_laboratory`
- "Google" → `google`

## Theme Options

| Theme | Colors | Description |
|-------|--------|-------------|
| `professional` | Navy (#003366) + Orange (#FF9900) | Recommended for corporate |
| `modern` | Dark blue (#1A1A2E) + Coral (#E94D60) | Contemporary feel |
| `minimal` | Slate (#2C3E50) + Green (#27AE60) | Clean and simple |

## Output Files

After generation:
```
.tmp/
├── interview_research_[company].json    # Research data
├── interview_prep_[company].pptx        # PowerPoint file
└── exp_img_[1-5].jpeg                   # Images (if --generate-images)
```

## Verification
- [ ] Research JSON created in .tmp/
- [ ] PowerPoint file created in .tmp/
- [ ] Presentation opens without errors
- [ ] Slide count matches expected (12-24 slides)
- [ ] Experience slides present if resume provided

## Troubleshooting

### API Key Error
```
Error: ANTHROPIC_API_KEY not set
```
**Solution:** Run `source .env` before the research script

### Resume Parse Error
```
Error: Could not parse resume
```
**Solution:** Check file format (PDF, DOCX, TXT supported). Try converting to TXT.

### Missing Dependencies
```
ModuleNotFoundError: No module named 'anthropic'
```
**Solution:** `pip install anthropic python-pptx PyPDF2 python-docx`

## Scripts Used
- `execution/interview_research.py` - AI research and resume parsing
- `execution/pptx_generator.py` - PowerPoint generation
- `execution/live_editor.py` - For subsequent editing

## Related Workflows
- [live-editing-session.md](live-editing-session.md) - For editing after generation
- [template-mode.md](template-mode.md) - For continuing from existing file
- [reformat-experience-slides.md](reformat-experience-slides.md) - For standardizing slides
