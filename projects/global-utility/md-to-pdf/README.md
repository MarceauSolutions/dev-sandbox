# Markdown to PDF Converter

Convert markdown (.md) files into professional, interactive PDF documents with automatic table of contents.

mcp-name: io.github.wmarceau/md-to-pdf

## Features

- **Automatic Table of Contents** - Generated from markdown headers
- **Interactive Navigation** - Clickable TOC links to sections
- **Professional Styling** - Clean, readable PDF output
- **Code Block Support** - Syntax highlighting preserved
- **Table Support** - Markdown tables convert to PDF tables
- **Image Support** - Embedded images in PDFs
- **Batch Conversion** - Process multiple files at once
- **MCP Integration** - Use as an MCP server for AI assistants

## Use Cases

- Convert documentation to shareable PDFs
- Create professional reports from markdown
- Generate user manuals with navigation
- Archive markdown content in PDF format
- Prepare presentations or handouts
- AI-powered document generation workflows

## Project Structure

```
md-to-pdf/
├── src/
│   ├── md_to_pdf.py          # Core conversion logic
│   └── convert.sh            # Wrapper script (sets library paths)
├── mcp-server/
│   └── md_to_pdf_mcp.py      # MCP server wrapper
├── registry/
│   └── manifest.json         # MCP Registry manifest
├── workflows/
│   └── convert-md-to-pdf.md  # Conversion workflow guide
├── testing/                  # Multi-agent test infrastructure
├── VERSION                   # Current version
├── CHANGELOG.md              # Version history
├── SKILL.md                  # MCP skill documentation
└── README.md                 # This file
```

## Requirements

- Python 3.8+
- markdown2 (markdown parsing)
- weasyprint (PDF generation)
- pygments (code syntax highlighting)
- mcp (MCP server - for MCP mode only)

### macOS Additional Requirements

```bash
brew install pango cairo
```

## Quick Start

### CLI Usage

```bash
# Set library path (macOS)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Convert single file
python src/md_to_pdf.py input.md output.pdf

# Using wrapper script
./src/convert.sh input.md output.pdf

# Batch convert
python src/md_to_pdf.py "docs/*.md" --output-dir pdfs/

# With custom styling
python src/md_to_pdf.py input.md output.pdf --css custom.css

# Without table of contents
python src/md_to_pdf.py input.md output.pdf --no-toc
```

### MCP Server Usage

```bash
# Install MCP SDK
pip install mcp

# Run MCP server
python mcp-server/md_to_pdf_mcp.py
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `convert_markdown_to_pdf` | Convert markdown to PDF with optional TOC |
| `extract_toc` | Extract table of contents structure |
| `get_default_styles` | Get default CSS for customization |

See [SKILL.md](SKILL.md) for detailed MCP tool documentation.

## Version

Current version: 1.0.0

## License

MIT License
