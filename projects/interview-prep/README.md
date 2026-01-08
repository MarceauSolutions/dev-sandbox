# Interview Prep PowerPoint AI Assistant

AI-powered interview preparation tool that researches companies and roles, then generates professional PowerPoint presentations with personalized talking points.

## Status: Live

**Production URL:** https://interview-prep-pptx-production.up.railway.app/app

## Features

| Feature | Script | Cost |
|---------|--------|------|
| Company/role research | `interview_research.py` | ~$0.03/research |
| PowerPoint generation | `pptx_generator.py` | FREE |
| Text editing | `pptx_editor.py` | FREE |
| Image replacement (local) | `pptx_editor.py` | FREE |
| AI image generation | `grok_image_gen.py` | $0.07/image |
| Add slide (user image) | `pptx_editor.py` | FREE |
| Add slide (AI image) | `pptx_editor.py` | $0.07/image |

## Directory Structure

```
interview-prep/
├── src/                    # Python execution scripts
│   ├── interview_research.py
│   ├── pptx_generator.py
│   ├── pptx_editor.py
│   ├── grok_image_gen.py
│   └── interview_prep_api.py
├── frontend/               # Web interface
│   └── index.html
├── docs/                   # Documentation
├── Procfile                # Railway deployment
├── railway.json            # Railway config
└── README.md
```

## Quick Start

### 1. Research a Company
```bash
source .env && ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" python src/interview_research.py \
  --company "Google" --role "Software Engineer"
```

### 2. Generate PowerPoint
```bash
python src/pptx_generator.py --input .tmp/interview_research_google.json --theme modern
```

### 3. With Resume (Personalized)
```bash
source .env && ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" python src/interview_research.py \
  --company "Apple" --role "Product Manager" --resume ~/resume.pdf
```

### 4. Add Custom Slide
```bash
# With your own image (FREE)
python src/pptx_editor.py --input .tmp/interview_prep_google.pptx --action add-slide \
  --title "My Experience" --description "Description" --relevance "Why it matters" \
  --new-image ~/my_photo.jpg --after-slide 18 --open

# With AI image ($0.07)
python src/pptx_editor.py --input .tmp/interview_prep_google.pptx --action add-slide \
  --title "My Experience" --description "Description" --relevance "Why it matters" \
  --prompt "Technical CAD rendering" --after-slide 18 --open
```

## Presentation Themes

| Theme | Description |
|-------|-------------|
| `modern` | Dark blue with coral accents (default) |
| `professional` | Navy with orange accents |
| `minimal` | Dark slate with green accents |

## Slide Structure

**Core Slides (Always):**
1. Title Slide
2. Agenda
3. Company Overview
4. Recent News
5. Company Culture
6. Role Analysis
7. Skills & Metrics
8-9. Interview Questions
10. Questions to Ask
11. Competitive Landscape
12. Talking Points

**With Resume:**
13. Experience Section Header
14-18. Personalized Experience Slides

**Closing:**
19. Preparation Checklist
20. You're Ready!

## Environment Variables

```env
ANTHROPIC_API_KEY=your_anthropic_key
XAI_API_KEY=your_xai_key  # For AI image generation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/app` | GET | Web interface |
| `/api/research` | POST | Research company/role |
| `/api/research/upload` | POST | Research with resume |
| `/api/generate` | POST | Generate PowerPoint |
| `/api/slides` | GET | List slides |
| `/api/edit/text` | POST | Edit slide text |
| `/api/edit/add-slide` | POST | Add new slide |
| `/api/download/{file}` | GET | Download .pptx |

## Skill Configuration

Located at: `.claude/skills/interview-prep/SKILL.md`

Trigger phrases:
- "prepare for interview at [company]"
- "research [company] for interview"
- "create interview prep slides"
- "generate interview presentation"

## Output Format

Generated `.pptx` files are compatible with:
- Microsoft PowerPoint (Windows & Mac)
- Google Slides (import)
- LibreOffice Impress
- Office 365

## Related Documentation

- Main directive: `directives/interview_prep.md`
- Interactive editing: `directives/pptx_interactive_edit.md`
- Skill definition: `.claude/skills/interview-prep/SKILL.md`
- Use cases: `.claude/skills/interview-prep/USE_CASES.json`
