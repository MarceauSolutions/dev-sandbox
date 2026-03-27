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

```bash
# From repo root:
./scripts/md-to-branded-pdf.sh docs/LIVE-OPERATION-GUIDE.md "Custom Title"
./scripts/md-to-branded-pdf.sh docs/POST-APRIL-6-ROADMAP.md

# Output: projects/fitness-influencer/outputs/branded-pdfs/<name>_<date>.pdf
```

Uses the `generic_document` template with `content_markdown` data key.
Any tower can call this to generate branded PDFs from markdown content.
