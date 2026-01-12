# Markdown to PDF Converter

Convert markdown (.md) files into professional, interactive PDF documents with automatic table of contents.

## Features

- **Automatic Table of Contents** - Generated from markdown headers
- **Interactive Navigation** - Clickable TOC links to sections
- **Professional Styling** - Clean, readable PDF output
- **Code Block Support** - Syntax highlighting preserved
- **Table Support** - Markdown tables convert to PDF tables
- **Image Support** - Embedded images in PDFs
- **Batch Conversion** - Process multiple files at once

## Use Cases

- Convert documentation to shareable PDFs
- Create professional reports from markdown
- Generate user manuals with navigation
- Archive markdown content in PDF format
- Prepare presentations or handouts

## Project Structure

```
md-to-pdf/
├── src/
│   └── md_to_pdf.py          # Main conversion script
├── workflows/
│   └── convert-md-to-pdf.md  # Conversion workflow guide
├── VERSION                    # Current version
├── CHANGELOG.md              # Version history
└── README.md                 # This file
```

## Requirements

- Python 3.8+
- markdown2 (markdown parsing)
- weasyprint or reportlab (PDF generation)
- pygments (code syntax highlighting)

## Quick Start

```bash
# Convert single file
python src/md_to_pdf.py input.md output.pdf

# Batch convert
python src/md_to_pdf.py docs/*.md --output pdfs/

# With custom styling
python src/md_to_pdf.py input.md output.pdf --style custom.css
```

## Version

Current version: 0.1.0-dev (in development)

## License

MIT License
