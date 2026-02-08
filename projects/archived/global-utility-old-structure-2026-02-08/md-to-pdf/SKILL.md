# Markdown to PDF MCP

Convert markdown documents to professional PDFs with interactive table of contents.

## Registry Information

- **Namespace**: `io.github.williammarceaujr/md-to-pdf`
- **Category**: Document Processing
- **Connectivity**: Local execution (no API keys required)

## Tools

### `convert_markdown_to_pdf`

Convert markdown content to a professional PDF document.

**Input**:
- `markdown_content` (string, required): The markdown to convert
- `include_toc` (boolean, optional): Include table of contents (default: true)
- `custom_css` (string, optional): Custom CSS for styling
- `filename` (string, optional): Suggested filename (default: document.pdf)

**Output**: JSON with base64-encoded PDF data

```json
{
  "success": true,
  "filename": "document.pdf",
  "size_bytes": 12345,
  "toc_entries": 5,
  "include_toc": true,
  "pdf_base64": "JVBERi0xLjcKCj..."
}
```

### `extract_toc`

Extract table of contents structure from markdown without generating PDF.

**Input**:
- `markdown_content` (string, required): The markdown to analyze

**Output**: JSON with header structure

```json
{
  "total_headers": 5,
  "headers": [
    {"level": 1, "text": "Introduction", "anchor": "introduction"},
    {"level": 2, "text": "Getting Started", "anchor": "getting-started"}
  ]
}
```

### `get_default_styles`

Get the default CSS styles used for PDF generation.

**Input**: None

**Output**: JSON with CSS content for customization reference

## Features

- Automatic table of contents with clickable links
- Professional default styling
- Support for:
  - Tables with alternating row colors
  - Fenced code blocks with syntax highlighting
  - Blockquotes with styled borders
  - Nested lists (ordered and unordered)
  - Images with auto-sizing
  - Horizontal rules
- Customizable CSS
- Page breaks and proper pagination

## Dependencies

- Python 3.8+
- `markdown2`: Markdown parsing
- `weasyprint`: PDF generation
- `pygments`: Syntax highlighting (optional)

## Installation

```bash
pip install markdown2 weasyprint pygments mcp
```

On macOS, WeasyPrint requires Pango and Cairo:
```bash
brew install pango cairo
```

## Running the Server

```bash
# Set library path (macOS)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Run MCP server
python mcp-server/md_to_pdf_mcp.py
```

## Example Usage

```python
# Via MCP client
result = await client.call_tool("convert_markdown_to_pdf", {
    "markdown_content": "# My Document\n\n## Introduction\n\nHello world!",
    "include_toc": True
})

# Decode and save PDF
import base64
pdf_data = base64.b64decode(result["pdf_base64"])
with open("output.pdf", "wb") as f:
    f.write(pdf_data)
```

## Integration

This MCP can be used standalone or through the MCP Aggregator platform:

```python
# Via MCP Aggregator
await aggregator.route({
    "category": "DOCUMENT_PROCESSING",
    "tool": "convert_markdown_to_pdf",
    "params": {...}
})
```
