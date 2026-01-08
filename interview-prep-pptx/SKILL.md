---
name: interview-prep
description: Generate interview preparation PowerPoint presentations with AI-powered company research, resume parsing, and technical images
trigger_phrases:
  - interview prep
  - create interview presentation
  - prepare for interview
  - research company for interview
  - make interview slides
  - interview powerpoint
  - job interview preparation
model: opus
allowed_tools:
  - Bash(python:*)
  - Bash(python3:*)
  - Read
  - Write
  - Edit
---

# Interview Prep PowerPoint Generator

AI-powered tool that researches companies, analyzes roles, and generates professional PowerPoint presentations for interview preparation.

## Capabilities

1. **Research Company & Role** - AI-powered research on company culture, mission, products, and role requirements
2. **Parse Resume** - Extract relevant experience from PDF, DOCX, or TXT resumes
3. **Generate PowerPoint** - Create professional presentations with multiple themes
4. **Add AI Images** - Generate technical images for experience slides ($0.07/image)
5. **Interactive Editing** - Modify slides through natural language commands

## Decision Tree

```
User Request → Check Intent
│
├─ "Research [company] for [role]" → Run interview_research.py
│   └─ With resume? → Add --resume flag
│   └─ Want images? → Add --generate-images flag
│
├─ "Create/Generate presentation" → Run pptx_generator.py
│   └─ Check for research JSON in .tmp/
│
├─ "Edit slide..." → Run pptx_editor.py
│   └─ Text edit → --action edit-text
│   └─ Image change → --action regenerate-image or replace-image
│   └─ Add slide → --action add-slide
│
├─ "Show/List slides" → Run pptx_editor.py --action list
│
└─ "Add [experience] slide with my image" → Run pptx_editor.py --action add-slide --new-image
```

## Usage Examples

### Full Workflow
```bash
# Research with resume and images
python execution/interview_research.py \
  --company "Google" \
  --role "Software Engineer" \
  --resume ~/resume.pdf \
  --generate-images

# Generate presentation
python execution/pptx_generator.py \
  --input .tmp/interview_research_google.json \
  --theme modern
```

### Interactive Editing
```bash
# List slides
python execution/pptx_editor.py --input .tmp/interview_prep_google.pptx --action list

# Add slide with user's image (FREE)
python execution/pptx_editor.py --input .tmp/interview_prep_google.pptx \
  --action add-slide \
  --title "My Project" \
  --description "Description here" \
  --relevance "Why it matters" \
  --new-image ~/photo.jpg \
  --after-slide 18 --open

# Add slide with AI image ($0.07)
python execution/pptx_editor.py --input .tmp/interview_prep_google.pptx \
  --action add-slide \
  --title "Technical Experience" \
  --description "Engineering work" \
  --relevance "Demonstrates skills" \
  --prompt "Technical CAD rendering" \
  --after-slide 18 --open
```

## Required Environment Variables

```bash
ANTHROPIC_API_KEY=...  # Required for research
XAI_API_KEY=...        # Optional for AI images
```

## Cost

| Action | Cost |
|--------|------|
| Research (Claude API) | ~$0.02-0.05 |
| Text/title edits | FREE |
| Add slide with own image | FREE |
| AI image generation | $0.07/image |

## Output Location

- Research JSON: `.tmp/interview_research_{company}.json`
- PowerPoint: `.tmp/interview_prep_{company}.pptx`
