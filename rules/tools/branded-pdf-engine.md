# Tool: branded_pdf_engine.py

**File:** `execution/branded_pdf_engine.py`
**When to use:** Any time a document, guide, report, proposal, or readable content needs to be produced. If William or a client will read it, it should be a branded PDF — never a markdown file.

## When NOT to use this tool

- Data output (use CSV or JSON instead)
- Real-time dashboards (use FastAPI web app)
- Quick conversational answers (plain text response)

## All 10 Templates

| Template | Required Keys | Use For |
|----------|--------------|---------|
| `generic_document` | `title`, `content_markdown` | Any guide, SOP, report, analysis, how-to |
| `proposal` | `client_name`, `title`, `content_markdown` | Client proposals, pitches, scopes of work |
| `workout_program` | `client_name`, `program_name`, `content_markdown` | Training plans, workout schedules |
| `nutrition_guide` | `client_name`, `title`, `content_markdown` | Meal plans, nutrition protocols |
| `progress_report` | `client_name`, `period`, `content_markdown` | Client check-ins, metrics reviews |
| `agreement` | `client_name`, `title`, `content_markdown` | Contracts, service agreements |
| `onboarding_packet` | `client_name`, `title`, `content_markdown` | Welcome packets, new client materials |
| `leave_behind` | `title`, `content_markdown` | Sales one-pagers, marketing sheets |
| `peptide_guide` | `title`, `content_markdown` | Peptide protocols, supplement guides |
| `challenge_workout` | `title`, `content_markdown` | Challenge events, special programs |

## Exact Commands

```bash
# List all templates (always run first if unsure)
python execution/branded_pdf_engine.py --list-templates

# Generic document (most common)
python execution/branded_pdf_engine.py \
  --template generic_document \
  --data '{"title": "Document Title", "content_markdown": "# Heading\n\nBody text here."}' \
  --output output/filename.pdf && open output/filename.pdf

# With longer content (use heredoc or temp file for complex markdown)
python execution/branded_pdf_engine.py \
  --template proposal \
  --data-file /tmp/proposal_data.json \
  --output output/proposal.pdf && open output/proposal.pdf
```

## Critical: content_markdown is the key

This is the most common mistake:

```json
// CORRECT
{"title": "My Doc", "content_markdown": "# Header\n\nBody text..."}

// WRONG — will fail or produce unstyled output
{"title": "My Doc", "content": "# Header\n\nBody text..."}

// WRONG — wrong key name entirely
{"title": "My Doc", "sections": ["Header", "Body"]}
```

**Always use `content_markdown`** for the text content field. It accepts full Markdown syntax:
- `# H1`, `## H2` for headings
- `**bold**`, `*italic*`
- `- item` for bullet lists
- `1. item` for numbered lists
- `` `code` `` for inline code

## Using a JSON data file (for large content)

```bash
# Create data file
cat > /tmp/doc_data.json << 'EOF'
{
  "title": "AI Services Overview",
  "content_markdown": "# AI Services\n\n## What We Offer\n\nDetailed content here..."
}
EOF

# Generate PDF
python execution/branded_pdf_engine.py \
  --template generic_document \
  --data-file /tmp/doc_data.json \
  --output output/ai-services.pdf && open output/ai-services.pdf
```

## After Generation — Always Open

```bash
open output/[filename].pdf
```

Never generate a PDF without opening it. William expects it to appear automatically. Always chain with `&&` or run immediately after.

## Common Mistakes to Avoid

1. Using `content` instead of `content_markdown` as the key
2. Not opening the PDF after generation
3. Using a template that requires `client_name` without providing it
4. Writing a custom PDF script instead of using this engine (hook will block it)
5. Committing large PDF output files to git
