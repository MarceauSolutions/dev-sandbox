# Demo & Sample Output Structure Template

This template shows how to organize client demo outputs and reference samples for your projects.

## Directory Structure

```
projects/[project-name]/
├── demos/
│   ├── client-[name]/           # Client-specific demo outputs
│   │   ├── 2026-01-12/          # Date-stamped test session
│   │   │   ├── output.pdf       # Demo output
│   │   │   ├── screenshot.png   # Visual reference
│   │   │   └── notes.md         # Context about this demo
│   │   ├── 2026-01-13/          # Next session
│   │   └── latest -> 2026-01-13 # Symlink to most recent
│   └── internal/                # Internal testing outputs
└── samples/                     # Reference examples for documentation
    ├── example-basic.pdf
    ├── example-complex.pdf
    └── README.md                # Describes each sample
```

## Quick Start

### 1. Create Demo Directory for a New Client

```bash
PROJECT="interview-prep"
CLIENT="acme"
DATE=$(date +%Y-%m-%d)

mkdir -p projects/$PROJECT/demos/client-$CLIENT/$DATE
```

### 2. Save Test Output from .tmp/

```bash
# After testing in .tmp/ and reviewing output
cp .tmp/output.pdf projects/$PROJECT/demos/client-$CLIENT/$DATE/

# Add context
cat > projects/$PROJECT/demos/client-$CLIENT/$DATE/notes.md <<EOF
# Demo: Acme Corp Interview Prep

## What This Demonstrates
- Custom navy theme matching company branding
- 20 slides including company research, role-specific prep
- AI-generated images for key experience examples

## Client Feedback
- Loved the theme consistency
- Requested adding technical interview section

## Next Steps
- Add technical interview questions
- Include salary negotiation tips
EOF
```

### 3. Create 'latest' Symlink

```bash
cd projects/$PROJECT/demos/client-$CLIENT/
ln -sf $DATE latest
cd -

# Now you can always access latest demo at:
# projects/$PROJECT/demos/client-$CLIENT/latest/
```

### 4. Save Reference Examples

```bash
# For documentation or workflow examples
mkdir -p projects/$PROJECT/samples/
cp .tmp/example-output.pdf projects/$PROJECT/samples/example-complex-table.pdf

# Document what the sample shows
cat > projects/$PROJECT/samples/README.md <<EOF
# Sample Outputs

## example-complex-table.pdf
Demonstrates markdown table rendering with:
- Multi-column layout
- Merged cells
- Syntax highlighting in code blocks

## example-basic.pdf
Simple markdown conversion showing:
- Headers (H1-H6)
- Lists (ordered/unordered)
- Basic formatting
EOF
```

### 5. Clean Up .tmp/

```bash
# After saving what you need
rm -rf .tmp/*
```

## File Naming Conventions

### Demo Outputs
- `output.pdf` - Main deliverable
- `output-v1.pdf`, `output-v2.pdf` - Iterations
- `screenshot-*.png` - Visual references
- `notes.md` - Session context

### Reference Samples
- `example-[descriptor].pdf` - What it demonstrates
- `README.md` - Catalog of samples

## Git Management

### If Demos Contain Sensitive Data

```bash
# Add to .gitignore
echo "projects/*/demos/" >> .gitignore
git add .gitignore
git commit -m "chore: Exclude client demos from version control"
```

### If Demos Are Safe to Commit

```bash
# Commit demo outputs (no sensitive data)
git add projects/$PROJECT/demos/
git commit -m "demo: Add $CLIENT demo outputs for $DATE"
```

## Review Before Client Meeting

```bash
PROJECT="interview-prep"
CLIENT="acme"

# List latest demo files
ls -la projects/$PROJECT/demos/client-$CLIENT/latest/

# Open latest demo
open projects/$PROJECT/demos/client-$CLIENT/latest/output.pdf

# Read context notes
cat projects/$PROJECT/demos/client-$CLIENT/latest/notes.md
```

## Cleanup Old Demos

```bash
# Keep only the 3 most recent sessions
cd projects/$PROJECT/demos/client-$CLIENT/
ls -t | tail -n +4 | grep -v latest | xargs rm -rf
```

## Common Workflows

### Workflow 1: Client Testing Session

```bash
# 1. Test in .tmp/
python projects/interview-prep/src/generate_pptx.py \
  --company "Acme Corp" \
  --output .tmp/acme-demo.pptx

# 2. Review
open .tmp/acme-demo.pptx

# 3. Client approves - save it
DATE=$(date +%Y-%m-%d)
mkdir -p projects/interview-prep/demos/client-acme/$DATE
cp .tmp/acme-demo.pptx projects/interview-prep/demos/client-acme/$DATE/
echo "Acme Corp interview prep - custom navy theme" > \
  projects/interview-prep/demos/client-acme/$DATE/notes.md

# 4. Update latest
cd projects/interview-prep/demos/client-acme/
ln -sf $DATE latest

# 5. Clean up
rm ~/.tmp/acme-demo.pptx
```

### Workflow 2: Creating Documentation Examples

```bash
# 1. Generate example output
python projects/md-to-pdf/src/md_to_pdf.py \
  docs/example-complex.md \
  .tmp/example-output.pdf

# 2. Review
open .tmp/example-output.pdf

# 3. Good example - save to samples
mkdir -p projects/md-to-pdf/samples/
cp .tmp/example-output.pdf projects/md-to-pdf/samples/

# 4. Document what it shows
echo "Complex table rendering example" >> projects/md-to-pdf/samples/README.md

# 5. Clean up
rm .tmp/example-output.pdf
```

### Workflow 3: Pre-Meeting Review

```bash
# Before client call, review all recent demos
PROJECT="interview-prep"
CLIENT="acme"

echo "=== Latest Demo Files ==="
ls -lh projects/$PROJECT/demos/client-$CLIENT/latest/

echo -e "\n=== Demo Context ==="
cat projects/$PROJECT/demos/client-$CLIENT/latest/notes.md

echo -e "\n=== Opening Demo ==="
open projects/$PROJECT/demos/client-$CLIENT/latest/*.pptx
```

## Best Practices

1. **Always add notes.md** - Future you will thank you
2. **Use date-stamped directories** - Easy chronological sorting
3. **Maintain 'latest' symlink** - Quick access without remembering dates
4. **Separate by client** - Keep demos organized
5. **Review before committing** - Check for sensitive data
6. **Regular cleanup** - Archive or delete old sessions (keep latest 2-3)
7. **Clean .tmp/ frequently** - Prevent clutter

## Communication with Claude

When working with Claude Code, use these phrases:

- **"Save this for the client"** → Claude moves output to `demos/client-[name]/$(date)/`
- **"This is a good example"** → Claude moves to `samples/`
- **"Clean up test files"** → Claude deletes everything in `.tmp/`

## References

- See `CLAUDE.md` - SOP 8: Client Demo & Test Output Management
- See `docs/workflow-standard.md` - Documentation best practices
- See `docs/repository-management.md` - Git and .gitignore guidance
