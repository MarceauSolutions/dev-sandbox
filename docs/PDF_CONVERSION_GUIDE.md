# Markdown to PDF Conversion Guide

## Quick Start

Convert your markdown documentation to professional PDFs with one command.

### Install Dependencies

```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Install PDF conversion libraries
pip install markdown-pdf markdown pygments
```

### Convert a Single File

```bash
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_SETUP.md \
  --output AMAZON_SETUP.pdf
```

## Common Use Cases

### 1. Convert Session Notes

```bash
# Single session
python execution/markdown_to_pdf.py \
  --input docs/sessions/2026-01-04-git-restructure-and-github-setup.md \
  --output "Session Notes - Git Restructure.pdf" \
  --title "Session Notes: Git Restructure and GitHub Setup"
```

### 2. Batch Convert All Session Notes

```bash
# Create PDFs directory
mkdir -p docs/sessions/pdfs

# Convert all session markdown files
python execution/markdown_to_pdf.py \
  --batch "docs/sessions/*.md" \
  --output-dir docs/sessions/pdfs/
```

### 3. Convert Setup Guides

```bash
# Amazon setup guide
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_SETUP.md \
  --output "Amazon Seller Central Setup Guide.pdf" \
  --author "William Marceau"

# Quick start guide
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_QUICK_START.md \
  --output "Amazon Quick Start.pdf"
```

### 4. Convert README

```bash
python execution/markdown_to_pdf.py \
  --input README.md \
  --output "Dev Sandbox Overview.pdf" \
  --title "Development Sandbox Overview"
```

### 5. Convert Directives

```bash
# Single directive
python execution/markdown_to_pdf.py \
  --input directives/amazon_seller_operations.md \
  --output "Amazon Seller Operations Directive.pdf"

# All directives
python execution/markdown_to_pdf.py \
  --batch "directives/*.md" \
  --output-dir docs/pdfs/directives/
```

### 6. Convert Without Table of Contents

For shorter documents where TOC isn't needed:

```bash
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_QUICK_START.md \
  --output "Quick Start.pdf" \
  --no-toc
```

### 7. Custom CSS Styling

```bash
python execution/markdown_to_pdf.py \
  --input README.md \
  --output README.pdf \
  --css execution/styles/custom_theme.css
```

## Features

### Automatic Styling

The converter automatically applies professional styling:

- **Headers**: H1-H6 with appropriate sizes and colors
- **Body Text**: Serif font, justified, optimal line spacing
- **Code Blocks**: Monospace font with syntax highlighting
- **Tables**: Bordered with alternating row colors
- **Links**: Clickable blue hyperlinks
- **Lists**: Proper indentation and spacing
- **Blockquotes**: Indented with left border

### Table of Contents

Automatically generated from headers (H1-H3) with:
- Clickable links to sections
- Page numbers
- Hierarchical structure

### Metadata

Each PDF includes:
- **Title**: Auto-detected from first H1 or filename
- **Author**: Marceau Solutions (or custom)
- **Creation Date**: Current timestamp
- **Subject**: Source filename

### Syntax Highlighting

Code blocks are automatically highlighted based on language:

````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

Becomes syntax-highlighted Python code in the PDF.

## Command-Line Options

```
usage: markdown_to_pdf.py [-h] (--input INPUT | --batch BATCH)
                          [--output OUTPUT] [--output-dir OUTPUT_DIR]
                          [--title TITLE] [--author AUTHOR] [--css CSS]
                          [--no-toc] [--no-page-numbers]

Convert markdown files to professionally formatted PDFs

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Input markdown file
  --batch BATCH, -b BATCH
                        Batch convert using glob pattern (e.g., "docs/*.md")
  --output OUTPUT, -o OUTPUT
                        Output PDF file (required for single file conversion)
  --output-dir OUTPUT_DIR, -d OUTPUT_DIR
                        Output directory (required for batch conversion)
  --title TITLE, -t TITLE
                        Document title (auto-detected if not provided)
  --author AUTHOR, -a AUTHOR
                        Document author (default: Marceau Solutions)
  --css CSS             Custom CSS file for styling
  --no-toc              Disable table of contents
  --no-page-numbers     Disable page numbers
```

## Default Styling

The converter uses a professional stylesheet ([execution/styles/default_pdf.css](../execution/styles/default_pdf.css)) with:

### Typography
- **Headers**: Arial/Helvetica sans-serif, bold
  - H1: 24pt with blue bottom border
  - H2: 20pt with gray bottom border
  - H3: 16pt
  - H4-H6: 14-11pt
- **Body**: Georgia serif, 11pt, line-height 1.6
- **Code**: Courier New monospace, 9-10pt

### Colors
- **Headers**: Dark blue-gray (#2c3e50, #34495e)
- **Body Text**: Dark gray (#333333)
- **Links**: Blue (#0066cc)
- **Code Background**: Light gray (#f4f4f4, #f8f8f8)
- **Table Headers**: Blue (#3498db)

### Layout
- **Page Size**: A4 (210mm × 297mm)
- **Margins**: 25mm top/bottom, 20mm left/right
- **Line Spacing**: 1.6 for body text
- **Paragraph Spacing**: 8pt after paragraphs

## Custom CSS

You can create custom stylesheets for different document types:

### Example: Create a custom theme

```css
/* execution/styles/custom_theme.css */

/* Dark theme */
body {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

h1, h2, h3 {
    color: #4fc3f7;
}

code {
    background-color: #2d2d2d;
    color: #ce9178;
}

/* Your custom styles here */
```

Use it:
```bash
python execution/markdown_to_pdf.py \
  --input file.md \
  --output file.pdf \
  --css execution/styles/custom_theme.css
```

## Natural Language Integration

Once set up, you can use natural language commands:

**You:** "Convert all my session notes to PDFs"

**AI:** *Runs batch conversion*
```bash
python execution/markdown_to_pdf.py \
  --batch "docs/sessions/*.md" \
  --output-dir docs/sessions/pdfs/
```

**You:** "Create a PDF of the Amazon setup guide for my team"

**AI:** *Converts with professional metadata*
```bash
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_SETUP.md \
  --output "Amazon Seller Central Setup Guide - Marceau Solutions.pdf" \
  --title "Amazon Seller Central Setup Guide" \
  --author "William Marceau"
```

## Tips & Best Practices

### 1. Use Descriptive Titles
```bash
# Good
--title "Amazon Seller Central Setup Guide"

# Less clear
--title "setup"
```

### 2. Organize Output PDFs
```bash
# Create dedicated PDF directories
mkdir -p docs/pdfs/guides
mkdir -p docs/pdfs/sessions
mkdir -p docs/pdfs/directives
```

### 3. Batch Convert by Type
```bash
# All guides
python execution/markdown_to_pdf.py \
  --batch "docs/*.md" \
  --output-dir docs/pdfs/guides/

# All directives
python execution/markdown_to_pdf.py \
  --batch "directives/*.md" \
  --output-dir docs/pdfs/directives/
```

### 4. Include TOC for Long Documents
- ✅ Include TOC: Setup guides, session notes, long directives
- ❌ Skip TOC: Quick reference, short documents (<5 sections)

### 5. Consistent Author Attribution
```bash
# Set author for professional documents
--author "Marceau Solutions"
--author "William Marceau"
```

## Troubleshooting

### Import Error
**Error**: `ImportError: No module named 'markdown_pdf'`

**Solution**:
```bash
pip install markdown-pdf markdown pygments
```

### CSS Not Found
**Warning**: Default CSS not found, using fallback

**Solution**: Ensure `execution/styles/default_pdf.css` exists or provide custom CSS with `--css`

### Unicode Characters
**Issue**: Special characters or emojis not rendering

**Solution**: The default fonts support most Unicode. For extended support, modify CSS to use fonts like "DejaVu Sans"

### Large Files
**Issue**: Very long documents (100+ pages) take time to process

**Solution**: Normal behavior. Add `-v` flag if you implement verbose mode for progress tracking.

### Image Links Broken
**Issue**: External images don't appear in PDF

**Solution**: Ensure images are local or accessible at conversion time. External URLs should be reachable.

## File Organization

### Recommended Structure
```
dev-sandbox/
├── docs/
│   ├── pdfs/                    # All PDFs organized here
│   │   ├── guides/              # Setup guides, how-tos
│   │   ├── sessions/            # Session note PDFs
│   │   └── directives/          # Directive PDFs
│   ├── sessions/                # Original session markdown
│   ├── AMAZON_SETUP.md
│   └── AMAZON_QUICK_START.md
├── directives/                  # Original directives
└── execution/
    ├── markdown_to_pdf.py       # Converter script
    └── styles/
        └── default_pdf.css      # Default styling
```

### .gitignore
Add PDF output directories to `.gitignore` if PDFs are regenerated:
```
# PDFs (regenerated from markdown)
docs/pdfs/
*.pdf
```

## Advanced Usage

### Scripting Batch Conversions

Create a convenience script for common conversions:

```bash
#!/bin/bash
# convert_all_docs.sh

echo "Converting all documentation to PDF..."

# Session notes
python execution/markdown_to_pdf.py \
  --batch "docs/sessions/*.md" \
  --output-dir docs/pdfs/sessions/ \
  --author "Marceau Solutions"

# Guides
for file in docs/*.md; do
    filename=$(basename "$file" .md)
    python execution/markdown_to_pdf.py \
        --input "$file" \
        --output "docs/pdfs/guides/${filename}.pdf" \
        --author "Marceau Solutions"
done

# Directives
python execution/markdown_to_pdf.py \
  --batch "directives/*.md" \
  --output-dir docs/pdfs/directives/ \
  --author "Marceau Solutions"

echo "✓ All documentation converted to PDF"
```

Make it executable:
```bash
chmod +x convert_all_docs.sh
./convert_all_docs.sh
```

## Next Steps

1. Install dependencies: `pip install markdown-pdf markdown pygments`
2. Test with a simple file: `python execution/markdown_to_pdf.py --input README.md --output test.pdf`
3. Convert your documentation as needed
4. Customize CSS for your branding (optional)
5. Set up batch conversion scripts for regular use

## Related Files

- **Converter Script**: [execution/markdown_to_pdf.py](../execution/markdown_to_pdf.py)
- **Default CSS**: [execution/styles/default_pdf.css](../execution/styles/default_pdf.css)
- **Directive**: [directives/convert_markdown_to_pdf.md](../directives/convert_markdown_to_pdf.md)

---

**Created**: 2026-01-04
**Last Updated**: 2026-01-04
