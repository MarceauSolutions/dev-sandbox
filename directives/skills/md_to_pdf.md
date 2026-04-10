# Directive: Markdown to PDF Converter

## Capability Overview

Convert markdown (.md) files into professional, interactive PDF documents with automatic table of contents. Supports single file conversion and batch processing.

## Core Functionality

### 1. Markdown Parsing
- Extract headers (H1-H6) for TOC generation
- Parse markdown with full support for:
  - Headers, paragraphs, lists (ordered/unordered)
  - Code blocks (fenced with syntax highlighting)
  - Tables
  - Blockquotes
  - Images
  - Links
  - Bold, italic, strikethrough

### 2. Table of Contents Generation
- Automatically extract all headers from markdown
- Generate hierarchical TOC structure
- Create clickable internal links (anchor tags)
- Place TOC on first page with page break

### 3. PDF Generation
- Convert HTML to professional PDF
- Apply CSS styling for readability
- Enable interactive navigation (clickable TOC)
- Support custom styling via CSS files

### 4. Batch Processing
- Process multiple markdown files at once
- Use glob patterns (e.g., `docs/*.md`)
- Create output directory structure
- Report success/failure for each file

## Tool Usage Patterns

### WeasyPrint (Primary PDF Engine)
```python
from weasyprint import HTML, CSS

html_obj = HTML(string=html_content)
css_obj = CSS(string=css_content)
html_obj.write_pdf(output_path, stylesheets=[css_obj])
```

**Why**: Best CSS support, interactive hyperlinks, professional output

### markdown2 (Markdown Parser)
```python
import markdown2

html = markdown2.markdown(
    md_content,
    extras=['fenced-code-blocks', 'tables', 'header-ids']
)
```

**Why**: Lightweight, supports all needed markdown features, easy to use

## Command Patterns

### Single File Conversion
```bash
python src/md_to_pdf.py input.md output.pdf
python src/md_to_pdf.py input.md output.pdf --css custom.css
python src/md_to_pdf.py input.md output.pdf --no-toc
```

### Batch Conversion
```bash
python src/md_to_pdf.py "docs/*.md" --output pdfs/
python src/md_to_pdf.py "*.md" --output-dir converted/
```

## Edge Cases & Error Handling

### 1. Missing Dependencies
**Issue**: WeasyPrint or markdown2 not installed

**Solution**:
```python
try:
    import markdown2
    from weasyprint import HTML, CSS
except ImportError as e:
    print(f"Error: Missing package: {e}")
    print("Install: pip install markdown2 weasyprint pygments")
    sys.exit(1)
```

### 2. Images Not Found
**Issue**: Markdown references images that don't exist

**Solutions**:
- Use absolute paths: `![](/full/path/image.png)`
- Use relative paths from markdown location
- Base64 encode images for embedding
- Validate image paths before PDF generation

**Code**:
```python
# Validate image paths
img_pattern = r'!\[.*?\]\((.*?)\)'
for match in re.finditer(img_pattern, md_content):
    img_path = match.group(1)
    if not img_path.startswith('http') and not os.path.exists(img_path):
        print(f"Warning: Image not found: {img_path}")
```

### 3. Duplicate Header Texts
**Issue**: Multiple headers with same text create duplicate anchor IDs

**Solution**: Append numbers to duplicate anchors
```python
def make_unique_anchor(anchor, existing_anchors):
    if anchor not in existing_anchors:
        return anchor

    counter = 1
    while f"{anchor}-{counter}" in existing_anchors:
        counter += 1

    return f"{anchor}-{counter}"
```

### 4. Special Characters in Headers
**Issue**: Headers with special chars (?, !, #, etc.) create invalid anchors

**Solution**: Sanitize anchor IDs
```python
anchor_id = text.lower()
anchor_id = re.sub(r'[^\w\s-]', '', anchor_id)  # Remove special chars
anchor_id = re.sub(r'[-\s]+', '-', anchor_id)   # Replace spaces with hyphens
```

### 5. Large Files / Memory Issues
**Issue**: Very large markdown files cause memory errors

**Solutions**:
- Stream HTML generation (don't load entire file in memory)
- Split large documents into chapters
- Process in chunks
- Increase available memory

### 6. Code Syntax Highlighting
**Issue**: Code blocks appear without syntax highlighting

**Solution**:
- Ensure Pygments installed: `pip install pygments`
- Specify language in fenced code blocks
- Include Pygments CSS in styling

```python
# Generate Pygments CSS
from pygments.formatters import HtmlFormatter
pygments_css = HtmlFormatter(style='monokai').get_style_defs('.codehilite')
```

### 7. TOC Links Not Working
**Issue**: Clicking TOC doesn't navigate to section

**Debug**:
```python
# Verify anchor format
print(f"TOC link: <a href='#{anchor}'>{text}</a>")
print(f"Header anchor: <a id='{anchor}'></a>{text}")
# Both anchor values must match exactly
```

## Styling Best Practices

### Default CSS Strategy
- Provide comprehensive default CSS in script
- Support custom CSS override via `--css` flag
- Use standard web fonts (Arial, Courier New)
- Professional color scheme (blues, grays)

### Page Layout
```css
@page {
    size: A4;
    margin: 2cm;
}
```

### TOC Styling
- Clear visual hierarchy (indentation)
- Distinct from main content (page break)
- Clickable links (blue, underlined on hover)

### Code Block Styling
- Dark background for readability
- Monospace font
- Syntax highlighting via Pygments

## Success Criteria

A successful conversion must:
- ✅ Generate valid PDF file
- ✅ Include complete TOC (if requested)
- ✅ All TOC links navigate correctly
- ✅ Preserve markdown formatting
- ✅ Render code blocks with highlighting
- ✅ Display images correctly
- ✅ Tables formatted properly
- ✅ No errors or warnings during generation

## Future Enhancements

### Phase 2
- Custom headers/footers with page numbers
- PDF metadata (title, author, keywords)
- Multiple CSS themes (professional, minimal, dark)
- Configuration file support

### Phase 3
- Bookmarks panel in PDF viewer
- Cross-references between sections
- Footnotes and endnotes
- LaTeX math equation support
- Automatic code block language detection

## Testing Strategy

### Manual Testing
1. Convert sample markdown with:
   - All header levels (H1-H6)
   - Code blocks (Python, JavaScript, Bash)
   - Tables with multiple columns
   - Images (local and remote)
   - Lists (nested, mixed)

2. Verify PDF output:
   - Open in PDF viewer
   - Click TOC links
   - Search text
   - Copy code blocks

### Automated Testing
```python
def test_header_extraction():
    md = "# H1\n## H2\n### H3"
    headers = extract_headers(md)
    assert len(headers) == 3
    assert headers[0]['level'] == 1

def test_toc_generation():
    headers = [{'level': 1, 'text': 'Title', 'anchor': 'title'}]
    toc = generate_toc(headers)
    assert '<a href="#title">Title</a>' in toc
```

## Common User Workflows

### 1. Convert Project Documentation
```bash
# Convert README
python src/md_to_pdf.py README.md README.pdf

# Convert all docs
python src/md_to_pdf.py "docs/*.md" --output pdfs/
```

### 2. Create Professional Report
```bash
# With custom styling
python src/md_to_pdf.py report.md report.pdf --css corporate.css
```

### 3. Archive Notes
```bash
# Batch convert notes folder
python src/md_to_pdf.py "notes/**/*.md" --output-dir archive/
```

## Error Messages

**Clear, actionable error messages**:
```python
# Good
print("Error: markdown2 not installed. Run: pip install markdown2")

# Bad
print("Import error")
```

**Progress feedback**:
```python
print(f"Converting: {md_file} → {pdf_file}")
print(f"✓ Generated: {pdf_file}")
print(f"✗ Failed: {pdf_file} ({error})")
```

## Deployment Considerations

- Ensure dependencies in requirements.txt
- WeasyPrint has system dependencies (Cairo, Pango, GDK-PixBuf)
- Test on target platforms (macOS, Linux, Windows)
- Provide installation instructions for WeasyPrint

## Related Documentation

- Workflow: `projects/md-to-pdf/workflows/convert-md-to-pdf.md`
- README: `projects/md-to-pdf/README.md`
- Script: `projects/md-to-pdf/src/md_to_pdf.py`
