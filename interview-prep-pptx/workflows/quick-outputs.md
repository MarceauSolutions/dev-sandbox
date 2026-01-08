# Workflow: Quick Reference Outputs

## Purpose
Generate quick reference materials (cheat sheets, talking points, flashcards, checklists) from existing research data.

## When to Use
- User wants a quick summary before their interview
- User says "give me a cheat sheet"
- User says "create talking points"
- User wants flashcards for practice
- User needs a day-of checklist

## Prerequisites
- Existing research JSON file (run research first if not available)

## Output Types

| Type | Description | Best For |
|------|-------------|----------|
| `cheat-sheet` | One-page quick reference | Quick review before interview |
| `talking-points` | Key messages to communicate | Preparing your narrative |
| `flashcards` | Q&A practice cards | Self-quizzing on questions |
| `checklist` | Day-of preparation list | Interview day preparation |
| `all` | Generate all outputs | Comprehensive preparation |

## Steps

### 1. Check for Research Data
```bash
# List available research files
ls .tmp/interview_research_*.json
```

If no research exists:
```bash
# Run research first
source .env && python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}"
```

### 2. Generate Outputs

**Cheat Sheet:**
```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input .tmp/interview_research_{company_slug}.json \
  --output cheat-sheet
```

**Talking Points:**
```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input .tmp/interview_research_{company_slug}.json \
  --output talking-points
```

**Flashcards:**
```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input .tmp/interview_research_{company_slug}.json \
  --output flashcards
```

**Day-of Checklist:**
```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input .tmp/interview_research_{company_slug}.json \
  --output checklist
```

**All Outputs:**
```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input .tmp/interview_research_{company_slug}.json \
  --output all
```

### 3. Output Files

Files are created in .tmp/ directory:
- `{company}_cheat_sheet.md` - One-page reference
- `{company}_talking_points.md` - Your key messages
- `{company}_flashcards.md` - Q&A practice cards
- `{company}_checklist.md` - Day-of preparation

If pandoc is installed, PDFs are also generated.

### 4. Copy to Downloads (Optional)

```bash
# Copy to Downloads folder
cp .tmp/{company}_cheat_sheet.md ~/Downloads/
cp .tmp/{company}_checklist.md ~/Downloads/
```

Or use the download script:
```bash
python execution/download_pptx.py --input .tmp/{company}_cheat_sheet.md
```

## What Each Output Contains

### Cheat Sheet
- Company at a glance (mission, products, values)
- Role overview (responsibilities, skills)
- Top 5 questions to prepare
- Your key messages
- Questions to ask them
- Quick reminders

### Talking Points
- Why this company
- Why this role
- Your key strengths with examples
- Relevant experience highlights
- How to address potential weaknesses
- Closing statement template

### Flashcards
- 10 common interview questions
- Strategy hint for each question
- Space to write your answers
- Bonus behavioral questions

### Day-of Checklist
- Week before tasks
- Day before tasks
- Morning of tasks
- Virtual interview setup
- Right before reminders
- Questions to ask
- Post-interview follow-up

## User Guidance

After generating outputs:
```
✅ Generated: {company}_cheat_sheet.md

📋 What you can do next:
• "Copy to Downloads folder"
• "Generate talking points too"
• "Create flashcards for practice"
• "Start a mock interview"
```

## Command Reference

```bash
python interview-prep-pptx/src/pdf_outputs.py \
  --input <research_json>     # Required: path to research JSON
  --output <type>             # cheat-sheet, talking-points, flashcards, checklist, all
  --output-dir <dir>          # Optional: output directory (default: .tmp)
```

## Troubleshooting

**"Research file not found":**
- Run research first: `python execution/interview_research.py --company "X" --role "Y"`
- Check file path spelling

**No PDF generated:**
- Install pandoc: `brew install pandoc`
- Markdown files are still usable without pandoc

**Content seems generic:**
- Ensure research JSON has complete data
- Re-run research if needed

## Related Workflows
- [generate-presentation.md](generate-presentation.md) - Full PowerPoint generation
- [mock-interview.md](mock-interview.md) - Practice interviews
