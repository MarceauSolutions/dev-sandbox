# PDF Template Selection

> Summary version lives in `rules/routing/ROUTING.md` tree #5.
> Exact usage commands: `rules/tools/branded-pdf-engine.md`

## All 10 Templates

| Template | CLI Flag | Required Keys | Use For | Example |
|----------|----------|--------------|---------|---------|
| `generic_document` | `--template generic_document` | `title`, `content_markdown` | Any markdown content, guides, SOPs, reports, how-to docs | Session summary, SOP export, analysis report |
| `proposal` | `--template proposal` | `client_name`, `title`, `content_markdown` | Client proposals, service pitches, scope of work | AI services proposal for HVAC company |
| `workout_program` | `--template workout_program` | `client_name`, `program_name`, `weeks`, `exercises` | Training programs, workout plans | 12-week strength program for PT client |
| `nutrition_guide` | `--template nutrition_guide` | `client_name`, `title`, `content_markdown` | Meal plans, nutrition protocols | Cutting diet for Julia |
| `progress_report` | `--template progress_report` | `client_name`, `period`, `metrics`, `content_markdown` | Client check-in reports, metrics reviews | Monthly progress for PT client |
| `agreement` | `--template agreement` | `client_name`, `title`, `content_markdown` | Service agreements, contracts, terms | Coaching agreement |
| `onboarding_packet` | `--template onboarding_packet` | `client_name`, `title`, `content_markdown` | Welcome packets, onboarding materials | New PT client welcome packet |
| `leave_behind` | `--template leave_behind` | `title`, `content_markdown` | Sales one-pagers, marketing leave-behinds | AI services sales sheet |
| `peptide_guide` | `--template peptide_guide` | `title`, `content_markdown` | Peptide protocols, supplement guides | Tesamorelin protocol |
| `challenge_workout` | `--template challenge_workout` | `title`, `content_markdown` | Challenge events, special workouts | 30-day challenge program |

## Example Commands

```bash
# Generic document (most common)
python execution/branded_pdf_engine.py \
  --template generic_document \
  --data '{"title": "AI Services Overview", "content_markdown": "# Overview\n\nContent here..."}' \
  --output output/ai-services-overview.pdf

# Client proposal
python execution/branded_pdf_engine.py \
  --template proposal \
  --data '{"client_name": "HVAC Co", "title": "AI Systems Proposal", "content_markdown": "..."}' \
  --output output/hvac-proposal.pdf

# Workout program
python execution/branded_pdf_engine.py \
  --template workout_program \
  --data '{"client_name": "John D", "program_name": "12-Week Strength", "weeks": 12, "exercises": [...]}' \
  --output output/john-program.pdf
```

## Critical: content_markdown vs content

The most common mistake is using the wrong data key.

- CORRECT: `"content_markdown": "# Header\nBody text..."` — Markdown string, rendered as formatted PDF
- WRONG: `"content": "..."` — Will fail or produce unstyled output
- WRONG: `"sections": [...]` — Wrong key name entirely

Always use `content_markdown` for any template that takes freeform text content.

## After Generation — Always Open

```bash
open output/[filename].pdf
```

Never generate a PDF without opening it. William expects it to appear automatically.
