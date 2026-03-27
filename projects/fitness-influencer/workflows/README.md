# Fitness-Influencer Workflows

## Planned Workflows
- **Weekly program generation**: Auto-generate client workout PDFs each Sunday
- **Content calendar**: Schedule social media posts via social-media/ automation
- **Client onboarding**: New client → questionnaire → program → Stripe → welcome email
- **Coaching check-ins**: Monday 9am automated client check-in messages

## Active Automation
- tower_handler.py processes cross-tower coaching content requests
- Social media automation in social-media/ sub-project (X posting)

## Active Workflows

### Markdown to Branded PDF
Converts any `.md` file to a professionally branded PDF using `branded_pdf_engine.py`.
Auto-detects the best template from filename/content keywords.

```bash
# Operation guides, roadmaps, cheat sheets → generic_document
./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md
./scripts/md-to-branded-pdf.sh docs/POST-APRIL-6-ROADMAP.md

# Client proposals → proposal template
./scripts/md-to-branded-pdf.sh drafts/naples-medspa-proposal.md

# Workout programs → workout_program template
./scripts/md-to-branded-pdf.sh clients/julia-week5-program.md

# Nutrition guides → nutrition_guide template
./scripts/md-to-branded-pdf.sh clients/julia-meal-plan.md

# Client onboarding → onboarding_packet template
./scripts/md-to-branded-pdf.sh clients/new-client-welcome.md

# Custom title override
./scripts/md-to-branded-pdf.sh docs/guide.md "My Custom Title"
```

**Template auto-detection**: proposal, workout, nutrition, onboarding, progress, agreement keywords in the filename or first 5 lines.

**Output**: `projects/fitness-influencer/outputs/branded-pdfs/<name>_<date>.pdf`

### Cross-Tower Usage

Any tower can generate branded PDFs by calling the script from the repo root:

```bash
# From lead-generation (e.g., generating a client proposal):
cd ~/dev-sandbox
./make-pdf.sh projects/lead-generation/drafts/naples-medspa-proposal.md

# From personal-assistant (e.g., generating an operation guide):
./make-pdf.sh docs/LIVE-OPERATION-GUIDE.md

# From any tower's Python code (subprocess call):
import subprocess
subprocess.run(["bash", "scripts/md-to-branded-pdf.sh", "path/to/file.md"], cwd=REPO_ROOT)
```

No cross-tower imports needed — the script uses `branded_pdf_engine.py` from execution context.
