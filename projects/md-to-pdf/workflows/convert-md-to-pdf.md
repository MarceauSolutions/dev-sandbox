# Workflow: Convert Markdown to Interactive PDF

## Overview

This workflow converts markdown (.md) files into professional PDF documents with an automatic, interactive table of contents. The TOC is generated from markdown headers and includes clickable links for easy navigation.

## Use Cases

- Converting project documentation (README, guides, SOPs) to shareable PDFs
- Creating professional reports from markdown notes
- Generating user manuals with navigation
- Archiving markdown content in PDF format
- Preparing handouts or presentations with proper structure

## Prerequisites

- Markdown file(s) to convert
- Python 3.8+ installed
- Required Python packages (see Installation section)

## Installation

```bash
# Install required packages
pip install markdown2 weasyprint pygments beautifulsoup4

# Alternative: Use reportlab (lighter weight)
pip install markdown2 reportlab pygments
```

**Note**: WeasyPrint provides better CSS support and interactive PDFs. ReportLab is lighter but less feature-rich.

## Workflow Steps

### 1. Prepare Markdown File

**Objective**: Ensure markdown is well-structured for PDF conversion

**Actions**:
- Use proper header hierarchy (`#`, `##`, `###`, etc.)
- Ensure headers are unique for proper TOC linking
- Check that images use relative or absolute paths
- Verify code blocks have language specifiers for syntax highlighting

**Example structure**:
```markdown
# Main Title

## Section 1
Content here...

### Subsection 1.1
More content...

## Section 2
Content here...

### Subsection 2.1
```

**Tools**: Text editor, `Read` tool

---

### 2. Parse Markdown and Extract Headers

**Objective**: Read markdown file and extract all headers for TOC generation

**Actions**:
- Read markdown file content
- Parse headers (lines starting with `#`, `##`, `###`, etc.)
- Extract header level and text
- Generate unique anchor IDs for each header

**Script example** (`src/md_to_pdf.py`):
```python
import re
import markdown2

def extract_headers(md_content):
    """Extract headers from markdown for TOC generation"""
    headers = []

    # Pattern: # Header, ## Header, ### Header, etc.
    header_pattern = r'^(#{1,6})\s+(.+)$'

    for line in md_content.split('\n'):
        match = re.match(header_pattern, line)
        if match:
            level = len(match.group(1))  # Count # symbols
            text = match.group(2).strip()
            anchor_id = text.lower().replace(' ', '-').replace('[', '').replace(']', '')

            headers.append({
                'level': level,
                'text': text,
                'anchor': anchor_id
            })

    return headers
```

**Tools**: Python script, regex parsing

---

### 3. Generate Table of Contents

**Objective**: Create interactive TOC HTML from extracted headers

**Actions**:
- Build hierarchical TOC structure
- Create HTML links to each section
- Style TOC with indentation based on header level
- Add page break after TOC

**Script example**:
```python
def generate_toc(headers):
    """Generate HTML table of contents"""
    toc_html = '<div class="toc">\n<h1>Table of Contents</h1>\n<ul>\n'

    for header in headers:
        indent = '  ' * (header['level'] - 1)
        link = f'<a href="#{header["anchor"]}">{header["text"]}</a>'
        toc_html += f'{indent}<li>{link}</li>\n'

    toc_html += '</ul>\n</div>\n<div style="page-break-after: always;"></div>\n'

    return toc_html
```

**Output**: HTML TOC with clickable links

**Tools**: Python, HTML generation

---

### 4. Convert Markdown to HTML

**Objective**: Transform markdown content into HTML with proper anchor tags

**Actions**:
- Use markdown2 library to convert markdown to HTML
- Add anchor IDs to headers for TOC linking
- Enable extras: tables, code blocks, fenced code
- Process images and embed or link

**Script example**:
```python
def markdown_to_html(md_content, headers):
    """Convert markdown to HTML with anchors"""

    # Add anchor IDs to headers
    for header in headers:
        pattern = f"^({'#' * header['level']})\s+{re.escape(header['text'])}$"
        replacement = f"{{'#' * header['level']}} <a id='{header['anchor']}'></a>{header['text']}"
        md_content = re.sub(pattern, replacement, md_content, flags=re.MULTILINE)

    # Convert markdown to HTML with extras
    html_content = markdown2.markdown(
        md_content,
        extras=[
            'fenced-code-blocks',
            'tables',
            'code-friendly',
            'cuddled-lists',
            'header-ids'
        ]
    )

    return html_content
```

**Tools**: `markdown2` library

---

### 5. Apply CSS Styling

**Objective**: Create professional PDF styling

**Actions**:
- Define page size and margins
- Style headers, paragraphs, code blocks
- Add syntax highlighting for code
- Style TOC (indentation, links, page breaks)
- Set fonts and colors

**CSS template**:
```css
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: 'Arial', 'Helvetica', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 24pt;
    color: #2c3e50;
    page-break-before: always;
    margin-top: 0;
}

h2 {
    font-size: 18pt;
    color: #34495e;
    margin-top: 1.5em;
}

h3 {
    font-size: 14pt;
    color: #7f8c8d;
}

.toc {
    page-break-after: always;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5em 0;
}

.toc a {
    color: #3498db;
    text-decoration: none;
}

code {
    background-color: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

pre {
    background-color: #2d2d2d;
    color: #f8f8f2;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #34495e;
    color: white;
}
```

**Tools**: CSS, WeasyPrint or ReportLab

---

### 6. Generate PDF with WeasyPrint

**Objective**: Convert HTML to interactive PDF

**Actions**:
- Combine TOC HTML + content HTML
- Apply CSS styling
- Generate PDF with WeasyPrint
- Enable hyperlinks for TOC navigation
- Save to output file

**Script example**:
```python
from weasyprint import HTML, CSS
from io import BytesIO

def generate_pdf(md_content, output_path, css_path=None):
    """Generate PDF from markdown content"""

    # Extract headers
    headers = extract_headers(md_content)

    # Generate TOC
    toc_html = generate_toc(headers)

    # Convert markdown to HTML
    content_html = markdown_to_html(md_content, headers)

    # Combine TOC + content
    full_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Document</title>
    </head>
    <body>
        {toc_html}
        {content_html}
    </body>
    </html>
    '''

    # Load CSS
    if css_path:
        with open(css_path, 'r') as f:
            css_content = f.read()
    else:
        css_content = DEFAULT_CSS  # Use default CSS from above

    # Generate PDF
    html_obj = HTML(string=full_html)
    css_obj = CSS(string=css_content)

    html_obj.write_pdf(
        output_path,
        stylesheets=[css_obj],
        presentational_hints=True
    )

    print(f"PDF generated: {output_path}")
```

**Tools**: `weasyprint` library

---

### 7. Batch Conversion (Optional)

**Objective**: Convert multiple markdown files at once

**Actions**:
- Use glob to find all .md files in directory
- Process each file individually
- Generate PDFs with matching names
- Create output directory if needed

**Script example**:
```python
import glob
import os

def batch_convert(input_pattern, output_dir, css_path=None):
    """Convert multiple markdown files to PDF"""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Find all markdown files
    md_files = glob.glob(input_pattern)

    for md_file in md_files:
        # Read markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Generate output filename
        base_name = os.path.basename(md_file).replace('.md', '.pdf')
        output_path = os.path.join(output_dir, base_name)

        # Convert to PDF
        print(f"Converting: {md_file} → {output_path}")
        generate_pdf(md_content, output_path, css_path)

    print(f"\nConverted {len(md_files)} files to {output_dir}/")
```

**Usage**:
```bash
python src/md_to_pdf.py "docs/*.md" --output pdfs/
```

**Tools**: `glob`, `os` modules

---

## Command-Line Interface

**Single file conversion**:
```bash
python src/md_to_pdf.py input.md output.pdf
```

**With custom CSS**:
```bash
python src/md_to_pdf.py input.md output.pdf --css custom.css
```

**Batch conversion**:
```bash
python src/md_to_pdf.py "docs/*.md" --output pdfs/
```

**With options**:
```bash
python src/md_to_pdf.py input.md output.pdf \
    --css custom.css \
    --no-toc \
    --syntax-theme monokai
```

---

## Troubleshooting

### Images Not Displaying

**Problem**: Images referenced in markdown don't appear in PDF

**Solutions**:
1. Use absolute paths: `![Image](/full/path/to/image.png)`
2. Use base64 encoded images (embedded)
3. Ensure image files exist at specified paths
4. Use `file://` URLs for local images

### TOC Links Not Working

**Problem**: Clicking TOC entries doesn't navigate to sections

**Solutions**:
1. Ensure using WeasyPrint (ReportLab has limited hyperlink support)
2. Verify anchor IDs match header IDs
3. Check HTML output for proper `<a href="#anchor">` and `<a id="anchor">` tags

### Code Blocks Not Highlighted

**Problem**: Code blocks appear as plain text without syntax highlighting

**Solutions**:
1. Install `pygments`: `pip install pygments`
2. Specify language in fenced code blocks:
   ````markdown
   ```python
   def hello():
       print("Hello")
   ```
   ````
3. Include Pygments CSS in styling

### Large Files Timeout

**Problem**: PDF generation hangs or times out for large markdown files

**Solutions**:
1. Split large documents into chapters
2. Reduce image sizes/quality
3. Increase timeout in WeasyPrint configuration
4. Use simpler CSS (avoid complex selectors)

### Fonts Not Rendering

**Problem**: Custom fonts don't appear in PDF

**Solutions**:
1. Install system fonts or embed font files
2. Use `@font-face` in CSS with local font paths
3. Fall back to standard fonts (Arial, Times, Courier)

---

## Output Format

**Single conversion**: Creates `output.pdf` at specified path

**Batch conversion**: Creates directory structure:
```
output_dir/
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

**PDF features**:
- ✅ Interactive table of contents
- ✅ Clickable section links
- ✅ Searchable text
- ✅ Copyable code blocks
- ✅ Embedded images
- ✅ Proper page breaks
- ✅ Professional styling

---

## Success Criteria

A successful conversion includes:

- ✅ PDF file generated without errors
- ✅ Table of contents on first page
- ✅ All headers appear in TOC
- ✅ TOC links navigate to correct sections
- ✅ Markdown formatting preserved (bold, italic, lists)
- ✅ Code blocks have syntax highlighting
- ✅ Tables render correctly
- ✅ Images display properly
- ✅ Page breaks at appropriate locations
- ✅ Professional, readable styling

---

## Example Command Sequence

```bash
# 1. Install dependencies
pip install markdown2 weasyprint pygments

# 2. Convert single file
python src/md_to_pdf.py README.md README.pdf

# 3. Convert with custom styling
python src/md_to_pdf.py docs/guide.md guide.pdf --css styles/professional.css

# 4. Batch convert documentation
python src/md_to_pdf.py "docs/*.md" --output pdfs/

# 5. Verify output
open README.pdf  # macOS
# or
xdg-open README.pdf  # Linux
# or
start README.pdf  # Windows
```

---

## Advanced Features (Future)

- Custom header/footer with page numbers
- Watermarks
- PDF metadata (author, title, keywords)
- Bookmarks panel in PDF viewer
- Cross-references between sections
- Footnotes and endnotes
- Custom page breaks
- Multiple CSS themes (professional, minimal, dark)
- Configuration file support (.pdfrc)

---

**Related Documentation**:
- WeasyPrint: https://weasyprint.readthedocs.io/
- markdown2: https://github.com/trentm/python-markdown2
- Pygments: https://pygments.org/
