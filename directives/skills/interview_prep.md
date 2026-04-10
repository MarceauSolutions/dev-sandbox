# Interview Preparation Workflow

## Goal
Research a company and role, then generate a professional PowerPoint presentation to help prepare for and present during an interview. Optionally personalize with resume/CV for tailored talking points.

## Workflows

For detailed step-by-step procedures, see the workflows directory:

| Workflow | File | Use When |
|----------|------|----------|
| Generate Presentation | `workflows/generate-presentation.md` | Creating new presentation from scratch |
| Template Mode | `workflows/template-mode.md` | Continuing from existing PPTX |
| Live Editing | `workflows/live-editing-session.md` | Interactive editing while viewing |
| Reformat Slides | `workflows/reformat-experience-slides.md` | Standardizing slide layouts |
| Add Images | `workflows/add-images-to-slides.md` | Adding images from previous session |

Location: `interview-prep-pptx/workflows/`

## Inputs
- **Company Name** (required): The company to research
- **Role/Position** (required): The specific role being interviewed for
- **Resume/CV** (optional): PDF, DOCX, or TXT file with work experience for personalization
- **Theme** (optional): Presentation style - "modern" (default), "professional", or "minimal"
- **Generate Images** (optional): Create AI visuals for experience highlights ($0.07/image)

## Tools/Scripts

### 1. Research Script
`execution/interview_research.py` - AI-powered company and role research with resume parsing

**What it does:**
- Researches company overview, culture, mission, products
- Analyzes the specific role (responsibilities, skills, success metrics)
- Identifies common interview questions with strategies
- Maps competitive landscape and industry trends
- Creates preparation checklists and talking points
- **NEW:** Parses resume/CV (PDF, DOCX, TXT) for personalized insights
- **NEW:** Extracts relevant experience highlights from resume
- **NEW:** Generates AI images for experience visualization

**Usage:**
```bash
# Basic research (no resume)
python execution/interview_research.py --company "Apple" --role "Senior Product Manager"

# With resume for personalization
python execution/interview_research.py --company "Google" --role "Software Engineer" --resume ~/Documents/resume.pdf

# With resume and AI images for experience highlights
python execution/interview_research.py --company "Meta" --role "Data Scientist" --resume ~/resume.docx --generate-images
```

**Supported Resume Formats:**
- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt, .md)

**Output:** JSON file in `.tmp/interview_research_{company}.json`

### 2. PowerPoint Generator
`execution/pptx_generator.py` - Creates professional presentations from research

**What it does:**
- Generates 10-20 slide professional presentation
- Multiple themes with consistent branding
- Includes: Company overview, culture, role analysis, Q&A prep, talking points, checklist
- **NEW:** Includes personalized experience highlight slides when resume is provided
- **NEW:** Shows visual placeholders for AI-generated images

**Usage:**
```bash
python execution/pptx_generator.py --input .tmp/interview_research_apple.json --theme modern
```

**Output:** PowerPoint file in `.tmp/interview_prep_{company}.pptx`

## Process

### Option A: Basic (No Resume)
```bash
python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}"
python execution/pptx_generator.py --input .tmp/interview_research_{company}.json
open .tmp/interview_prep_{company}.pptx
```

### Option B: Personalized (With Resume)
```bash
python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}" --resume /path/to/resume.pdf
python execution/pptx_generator.py --input .tmp/interview_research_{company}.json
open .tmp/interview_prep_{company}.pptx
```

### Option C: Full Experience (Resume + Images)
```bash
python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}" --resume /path/to/resume.pdf --generate-images
python execution/pptx_generator.py --input .tmp/interview_research_{company}.json
open .tmp/interview_prep_{company}.pptx
```

## One-Liner Examples

**Basic:**
```bash
python execution/interview_research.py --company "Google" --role "Software Engineer" && \
python execution/pptx_generator.py --input .tmp/interview_research_google.json && \
open .tmp/interview_prep_google.pptx
```

**With Resume:**
```bash
python execution/interview_research.py --company "Apple" --role "Product Manager" --resume ~/resume.pdf && \
python execution/pptx_generator.py --input .tmp/interview_research_apple.json --theme professional && \
open .tmp/interview_prep_apple.pptx
```

## Outputs

### Research JSON
```json
{
  "company_overview": { ... },
  "company_culture": { ... },
  "role_analysis": { ... },
  "interview_insights": { ... },
  "competitive_landscape": { ... },
  "preparation_checklist": [ ... ],
  "talking_points": { ... },
  "experience_highlights": [
    {"experience": "Led team of 5...", "relevance": "Demonstrates leadership", "image_url": "..."}
  ],
  "candidate_name": "John Doe"
}
```

### PowerPoint Slides

**Core Slides (Always Included):**
1. **Title Slide** - Company name, role, date
2. **Agenda** - Overview of what's covered
3. **Company Overview** - Industry, mission, products
4. **Recent News** - Latest developments
5. **Company Culture** - Values, work environment
6. **Role Analysis** - Responsibilities, department
7. **Skills & Metrics** - Required skills, success measures
8. **Interview Questions 1** - Common questions with strategies
9. **Interview Questions 2** - More questions
10. **Questions to Ask** - Smart questions for the interviewer
11. **Competitive Landscape** - Competitors, industry trends
12. **Talking Points** - Key messages to communicate

**Personalized Slides (When Resume Provided):**
13. **Your Relevant Experience** - Section divider
14-18. **Experience Highlights** - Individual slides for top 5 relevant experiences from resume

**Closing Slides:**
- **Preparation Checklist** - Action items before interview
- **Closing** - Motivational ending

## Themes

| Theme | Description |
|-------|-------------|
| `modern` | Dark blue with coral accents, contemporary feel |
| `professional` | Navy with orange accents, traditional corporate |
| `minimal` | Dark slate with green accents, clean and simple |

## Dependencies
- `anthropic` - For AI research
- `python-pptx` - For PowerPoint generation

Install: `pip install anthropic python-pptx`

## Edge Cases & Learnings

### Common Issues
- **Company not found**: AI will provide best-effort research based on available knowledge
- **Role too specific**: AI generalizes to similar roles in the industry
- **Large companies**: May have multiple divisions - specify if needed (e.g., "Apple - Services")

### Best Practices
- Run research fresh before each interview (news changes)
- Review and customize talking points for your experience
- Practice answering the identified questions out loud
- Research your specific interviewers on LinkedIn

## Cost
- Research: ~$0.02-0.05 per run (Claude API)
- PowerPoint: FREE (local generation)

## Template Mode - Continue From Existing Presentation

When you have an existing PowerPoint from a previous session that you want to continue editing:

### Option D: Load Existing Template

```bash
# Step 1: List available templates in .tmp/
python execution/template_manager.py --list

# Step 2: Load template and see structure
python execution/template_manager.py --load .tmp/interview_prep_company.pptx

# Step 3: Create editing session
python execution/template_manager.py --load .tmp/interview_prep_company.pptx --create-session

# Step 4: Make edits using pptx_editor.py
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action list
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action edit-text --slide 3 --find "old" --replace "new"
```

### Option E: Add Images from Previous Session

If you have AI-generated images from a previous session (exp_img_1.jpeg through exp_img_5.jpeg):

```bash
# Add images to experience slides (14-18)
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 14 --new-image .tmp/exp_img_1.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 15 --new-image .tmp/exp_img_2.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 16 --new-image .tmp/exp_img_3.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 17 --new-image .tmp/exp_img_4.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 18 --new-image .tmp/exp_img_5.jpeg --position left --width 4.5 --open
```

### Option F: Regenerate with Different Theme

Keep the same research but apply a new theme:

```bash
# Uses existing research JSON to regenerate with new theme
python execution/pptx_generator.py --input .tmp/interview_research_company.json --theme professional
```

### Template Manager Commands

| Command | Description |
|---------|-------------|
| `--list` | List all templates in .tmp/ |
| `--load FILE` | Load and inspect a template |
| `--load FILE --extract-info` | Extract company/role from template |
| `--load FILE --create-session` | Create editing session |
| `--load FILE --copy-to NEW` | Copy to new file |

## Live Interactive Editing Mode

For real-time editing while viewing the PowerPoint, use the live editor. This allows you to have the presentation open and watch changes happen as you describe them.

### Starting a Live Session

```bash
# Start session and open the file
python execution/live_editor.py --start .tmp/interview_prep_company.pptx --open

# Or start without opening (if already open)
python execution/live_editor.py --start .tmp/interview_prep_company.pptx
```

### Making Live Edits

```bash
# Edit text on a slide (auto-refreshes PowerPoint)
python execution/live_editor.py --edit-text --slide 3 --find "old text" --replace "new text"

# Add image to a slide
python execution/live_editor.py --add-image --slide 14 --image .tmp/exp_img_1.jpeg --position left

# List all slides
python execution/live_editor.py --list

# Manually refresh PowerPoint to see changes
python execution/live_editor.py --refresh
```

### Session Management

```bash
# Check session status and recent edits
python execution/live_editor.py --status

# Revert all changes to backup
python execution/live_editor.py --revert

# End session
python execution/live_editor.py --end
```

### Live Editor Commands

| Command | Description |
|---------|-------------|
| `--start FILE` | Start live session with a PPTX file |
| `--start FILE --open` | Start and open the file |
| `--list` | List all slides in session |
| `--edit-text --slide N --find "X" --replace "Y"` | Edit text on slide |
| `--add-image --slide N --image PATH` | Add image to slide |
| `--refresh` | Refresh PowerPoint/Keynote to show changes |
| `--status` | Show session status and recent edits |
| `--revert` | Revert to backup from session start |
| `--end` | End the live editing session |

### How It Works

1. A backup is created when you start a session
2. Edits modify the PPTX file directly
3. AppleScript triggers PowerPoint/Keynote to reload (macOS)
4. All edits are logged for undo capability
5. Use `--revert` to restore original state

## Future Enhancements
- [ ] Add interviewer research (LinkedIn integration)
- [ ] Include salary benchmarking data
- [ ] Generate practice question flashcards
- [ ] Add company stock/financial analysis for public companies
