# Directive: Convert Markdown to PDF

## Goal

Convert markdown documentation files to professionally formatted PDF documents with appropriate styling for headers, body text, code blocks, tables, and images.

## Context

The dev-sandbox workspace contains extensive markdown documentation:
- Session notes in `docs/sessions/`
- Setup guides (e.g., `docs/AMAZON_SETUP.md`)
- Directives in `directives/`
- README files

These need to be converted to PDF for:
- Sharing with team members or clients
- Archival purposes
- Offline reading
- Professional documentation deliverables

## Required Features

### Styling
- **Headers (H1-H6)**: Different font sizes, bold, with spacing
- **Body Text**: Professional font, appropriate line spacing
- **Code Blocks**: Monospace font, syntax highlighting, background color
- **Inline Code**: Monospace with light background
- **Tables**: Proper borders, alternating row colors
- **Lists**: Bullets and numbered lists with proper indentation
- **Links**: Clickable hyperlinks in blue
- **Images**: Embedded with proper sizing
- **Blockquotes**: Indented with left border

### Document Features
- **Table of Contents**: Auto-generated from headers
- **Page Numbers**: Footer with page numbers
- **Metadata**: Title, author, date
- **Headers/Footers**: Document title in header
- **Page Breaks**: Respect markdown page break indicators

## Inputs

### Required
- `markdown_file` - Path to markdown file to convert
- `output_pdf` - Path for output PDF file

### Optional
- `title` - Document title (defaults to filename or H1 header)
- `author` - Author name (default: "Marceau Solutions")
- `css_file` - Path to custom CSS file for styling
- `toc` - Include table of contents (default: True)
- `page_numbers` - Include page numbers (default: True)
- `syntax_highlighting` - Enable code syntax highlighting (default: True)

## Tools

### Primary Script
- `execution/markdown_to_pdf.py` - Main conversion script

### Libraries Used
- `markdown-pdf` - Markdown to PDF conversion with styling
- `markdown` - Markdown parsing and extensions
- `pymupdf` (fitz) - PDF manipulation
- `pygments` - Syntax highlighting for code blocks

## Process

### 1. Parse Markdown
- Read markdown file
- Parse front matter (if present) for metadata
- Extract first H1 for document title if not provided
- Identify all headers for TOC generation

### 2. Apply Styling
- Load custom CSS or use default professional styling
- Configure fonts (headers: bold sans-serif, body: serif, code: monospace)
- Set page layout (A4, margins, orientation)
- Apply syntax highlighting to code blocks

### 3. Generate PDF
- Convert markdown to HTML with extensions
- Apply CSS styling
- Generate table of contents (if enabled)
- Add page numbers and headers/footers
- Embed images and format tables
- Create clickable hyperlinks

### 4. Post-Processing
- Add metadata (title, author, creation date)
- Optimize file size
- Verify all content rendered correctly

## Default Styling

### Typography
```css
/* Headers */
h1: 24pt, bold, color: #2c3e50, margin-top: 20pt
h2: 20pt, bold, color: #34495e, margin-top: 16pt
h3: 16pt, bold, color: #34495e, margin-top: 12pt
h4-h6: 14pt, bold, color: #555555

/* Body */
body: 11pt, Georgia or serif, line-height: 1.6, color: #333333

/* Code */
code: 10pt, Courier New or monospace, background: #f4f4f4
pre: 9pt, Courier New, background: #f8f8f8, border: 1px solid #ddd
```

### Layout
- **Page Size**: A4 (210mm x 297mm)
- **Margins**: Top: 25mm, Bottom: 25mm, Left: 20mm, Right: 20mm
- **Line Spacing**: 1.6 for body text
- **Paragraph Spacing**: 8pt after paragraphs

### Colors
- **Headers**: Dark blue-gray (#2c3e50, #34495e)
- **Body Text**: Dark gray (#333333)
- **Links**: Blue (#0066cc)
- **Code Background**: Light gray (#f4f4f4)
- **Table Borders**: Medium gray (#cccccc)
- **Alternating Rows**: Light blue-gray (#f9f9f9)

## Use Cases

### 1. Convert Single File

**Natural Language**: "Convert docs/AMAZON_SETUP.md to PDF"

**Command**:
```bash
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_SETUP.md \
  --output docs/AMAZON_SETUP.pdf
```

### 2. Convert with Custom Title

**Natural Language**: "Convert the session notes to PDF with custom title"

**Command**:
```bash
python execution/markdown_to_pdf.py \
  --input docs/sessions/2026-01-04-git-restructure-and-github-setup.md \
  --output Session_Notes_2026-01-04.pdf \
  --title "Session Notes: Git Restructure" \
  --author "William Marceau"
```

### 3. Batch Convert All Session Notes

**Natural Language**: "Convert all session markdown files to PDFs"

**Command**:
```bash
python execution/markdown_to_pdf.py \
  --batch docs/sessions/*.md \
  --output-dir docs/sessions/pdfs/
```

### 4. Convert with Custom CSS

**Natural Language**: "Convert README with custom styling"

**Command**:
```bash
python execution/markdown_to_pdf.py \
  --input README.md \
  --output README.pdf \
  --css execution/styles/custom_theme.css
```

### 5. Convert Without TOC

**Natural Language**: "Convert quick start guide without table of contents"

**Command**:
```bash
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_QUICK_START.md \
  --output AMAZON_QUICK_START.pdf \
  --no-toc
```

## Edge Cases

### Large Files
- **Issue**: Very long markdown files (100+ pages)
- **Solution**: Add progress indicator, optimize memory usage, chunk processing

### Images
- **Issue**: External image URLs may not be accessible
- **Solution**: Download and embed images, handle broken links gracefully

### Code Blocks
- **Issue**: Very long code lines overflow page width
- **Solution**: Enable word wrap or horizontal scrolling, reduce font size for code

### Tables
- **Issue**: Wide tables exceed page width
- **Solution**: Auto-scale tables to fit page, rotate page to landscape if needed

### Special Characters
- **Issue**: Unicode or emoji characters may not render
- **Solution**: Use fonts with broad Unicode support (e.g., DejaVu Sans)

### Links
- **Issue**: Internal markdown links (e.g., `[link](#section)`)
- **Solution**: Convert to PDF internal links/bookmarks

### Front Matter
- **Issue**: YAML front matter at top of markdown file
- **Solution**: Parse and extract metadata, don't render in PDF body

## Output Structure

### PDF Metadata
```
Title: [Extracted from H1 or --title parameter]
Author: [From --author or default "Marceau Solutions"]
Subject: [Auto-generated from filename]
Creator: Marceau Solutions PDF Generator
CreationDate: [Current timestamp]
```

### Document Structure
```
1. Cover Page (optional)
   - Document title
   - Author
   - Date
   - Logo (if provided)

2. Table of Contents (if enabled)
   - Clickable links to sections
   - Page numbers

3. Main Content
   - Headers (H1-H6)
   - Body text
   - Code blocks with syntax highlighting
   - Tables
   - Images
   - Lists
   - Blockquotes

4. Footer
   - Page numbers (e.g., "Page 1 of 10")
   - Document title (optional)
```

## Success Criteria

1. Converts markdown to PDF with professional formatting
2. Preserves all markdown formatting (headers, lists, code, tables)
3. Generates table of contents from headers
4. Applies syntax highlighting to code blocks
5. Handles images and links correctly
6. Adds page numbers and metadata
7. Supports batch conversion of multiple files
8. Produces PDFs suitable for professional distribution

## File Organization

### Input Files
- Markdown files from anywhere in workspace
- Common locations: `docs/`, `directives/`, root directory

### Output Files
- PDF files generated in `.tmp/pdfs/` by default
- Or user-specified output directory
- Naming convention: `{original_name}.pdf`

### Styling Assets
- Default CSS: `execution/styles/default_pdf.css`
- Custom CSS: User-provided
- Fonts: System fonts or embedded custom fonts

## Examples

### Example 1: Session Notes
```bash
# Convert session notes with TOC
python execution/markdown_to_pdf.py \
  --input docs/sessions/2026-01-04-amazon-sp-api-wrapper.md \
  --output "Session Notes - Amazon SP-API.pdf" \
  --title "Development Session: Amazon SP-API Wrapper" \
  --toc
```

**Result**: Professional PDF with:
- Cover page with title and date
- Table of contents with all sections
- Syntax-highlighted code blocks
- Properly formatted commands
- Clickable reference links

### Example 2: Setup Guide
```bash
# Convert setup guide for client delivery
python execution/markdown_to_pdf.py \
  --input docs/AMAZON_SETUP.md \
  --output "Amazon Seller Central Setup Guide.pdf" \
  --author "Marceau Solutions" \
  --toc
```

**Result**: Client-ready documentation with:
- Professional styling
- Step-by-step instructions clearly formatted
- Code blocks with syntax highlighting
- Embedded images (if any)
- Page numbers

### Example 3: Batch Convert
```bash
# Convert all session notes to PDFs
python execution/markdown_to_pdf.py \
  --batch "docs/sessions/*.md" \
  --output-dir "docs/sessions/pdfs/" \
  --author "Marceau Solutions"
```

**Result**: All session markdown files converted to PDFs in dedicated folder

## References

- [markdown-pdf Library](https://pypi.org/project/markdown-pdf/)
- [fpdf2 with Markdown](https://py-pdf.github.io/fpdf2/CombineWithMarkdown.html)
- [Python Markdown Extensions](https://python-markdown.github.io/extensions/)
- [Pygments Syntax Highlighting](https://pygments.org/)

## Next Steps

1. Install required dependencies
2. Create default CSS stylesheet
3. Build main conversion script
4. Test with various markdown files
5. Add batch processing capability
6. Create convenience wrapper for common conversions
7. Document in session notes
