# Interview Prep PowerPoint Generator

AI-powered interview preparation tool that researches companies, analyzes roles, and generates professional PowerPoint presentations with personalized talking points from your resume.

## Features

- **AI Company Research**: Automatically researches company overview, culture, mission, products, and recent news
- **Role Analysis**: Analyzes job responsibilities, required skills, and success metrics
- **Interview Q&A Prep**: Generates common interview questions with strategic response frameworks
- **Resume Integration**: Parses PDF, DOCX, or TXT resumes to extract relevant experience
- **AI Image Generation**: Creates technical images for experience slides ($0.07/image via Grok/xAI)
- **Interactive Editing**: Modify presentations through natural language commands
- **Multiple Themes**: Modern, Professional, and Minimal presentation styles

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
XAI_API_KEY=your_xai_api_key  # Optional, for AI image generation
```

### 3. Generate a Presentation

**Basic (no resume):**
```bash
python src/interview_research.py --company "Google" --role "Software Engineer"
python src/pptx_generator.py --input .tmp/interview_research_google.json
```

**With resume personalization:**
```bash
python src/interview_research.py --company "Apple" --role "Product Manager" --resume ~/resume.pdf
python src/pptx_generator.py --input .tmp/interview_research_apple.json
```

**Full experience with AI images:**
```bash
python src/interview_research.py --company "Meta" --role "Data Scientist" --resume ~/resume.pdf --generate-images
python src/pptx_generator.py --input .tmp/interview_research_meta.json
```

## Project Structure

```
interview-prep-pptx/
├── src/
│   ├── interview_research.py   # AI-powered company/role research
│   ├── pptx_generator.py       # PowerPoint generation
│   ├── pptx_editor.py          # Interactive slide editing
│   └── grok_image_gen.py       # AI image generation
├── docs/
│   ├── interview_prep.md       # Main workflow documentation
│   └── pptx_interactive_edit.md # Editing workflow documentation
├── examples/
│   └── sample_output.json      # Example research output
├── .tmp/                       # Temporary files (generated)
├── requirements.txt
├── .env.example
└── README.md
```

## Usage Guide

### Research Script

`src/interview_research.py` - AI-powered company and role research

```bash
python src/interview_research.py \
  --company "Brookhaven National Laboratory" \
  --role "Mechanical Design Engineer" \
  --resume ~/Documents/resume.pdf \
  --generate-images \
  --output .tmp/research.json
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `--company` | Yes | Company name to research |
| `--role` | Yes | Position/role being interviewed for |
| `--resume` | No | Path to resume (PDF, DOCX, TXT) |
| `--generate-images` | No | Generate AI images for experience slides |
| `--output` | No | Custom output path for JSON |

### PowerPoint Generator

`src/pptx_generator.py` - Creates presentations from research data

```bash
python src/pptx_generator.py \
  --input .tmp/interview_research_google.json \
  --theme modern \
  --output .tmp/my_presentation.pptx
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `--input` | Yes | Path to research JSON file |
| `--theme` | No | Theme: modern, professional, minimal |
| `--output` | No | Custom output path for PPTX |

### Interactive Editor

`src/pptx_editor.py` - Edit presentations via command line

**List slides:**
```bash
python src/pptx_editor.py --input presentation.pptx --action list
```

**Edit text:**
```bash
python src/pptx_editor.py --input presentation.pptx --action edit-text \
  --slide 3 --find "old text" --replace "new text"
```

**Add slide with your own image (FREE):**
```bash
python src/pptx_editor.py --input presentation.pptx --action add-slide \
  --title "My Experience" \
  --description "Description of the work" \
  --relevance "Why it matters for this role" \
  --new-image ~/Photos/my_project.jpg \
  --after-slide 18 --open
```

**Add slide with AI-generated image ($0.07):**
```bash
python src/pptx_editor.py --input presentation.pptx --action add-slide \
  --title "Technical Project" \
  --description "Designed precision components" \
  --relevance "Demonstrates engineering expertise" \
  --prompt "Technical CAD rendering of precision mechanical assembly" \
  --after-slide 18 --open
```

**Regenerate an image:**
```bash
python src/pptx_editor.py --input presentation.pptx --action regenerate-image \
  --slide 14 --prompt "Detailed aerospace component cutaway diagram"
```

## Presentation Themes

| Theme | Description |
|-------|-------------|
| `modern` | Dark blue with coral accents, contemporary feel |
| `professional` | Navy with orange accents, traditional corporate |
| `minimal` | Dark slate with green accents, clean and simple |

## Output Slides

**Core Slides (Always Included):**
1. Title Slide - Company name, role, date
2. Agenda - Overview of content
3. Company Overview - Industry, mission, products
4. Recent News - Latest developments
5. Company Culture - Values, work environment
6. Role Analysis - Responsibilities, department
7. Skills & Metrics - Required skills, success measures
8. Interview Questions (1/2) - Common questions with strategies
9. Interview Questions (2/2) - More questions
10. Questions to Ask - Smart questions for the interviewer
11. Competitive Landscape - Competitors, industry trends
12. Talking Points - Key messages to communicate

**Personalized Slides (When Resume Provided):**
13. Your Relevant Experience - Section divider
14-18. Experience Highlights - Individual slides for top 5 relevant experiences

**Closing Slides:**
- Preparation Checklist - Action items
- Closing - Motivational ending

## Cost

| Action | Cost |
|--------|------|
| Company/role research | ~$0.02-0.05 (Claude API) |
| Text edits | FREE |
| Title updates | FREE |
| Replace image with local file | FREE |
| Add slide with user's own image | FREE |
| AI image regeneration | $0.07 per image |
| Add slide with AI-generated image | $0.07 per image |

## Supported Resume Formats

- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Plain text (.txt, .md)

## Requirements

- Python 3.8+
- Anthropic API key (for research)
- xAI API key (optional, for image generation)

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Changelog

### v1.0.0 (2026-01-07)
- Initial release
- AI-powered company and role research
- Resume parsing (PDF, DOCX, TXT)
- PowerPoint generation with multiple themes
- AI image generation for experience slides
- Interactive slide editing
- Auto-close existing PowerPoints before opening new ones
