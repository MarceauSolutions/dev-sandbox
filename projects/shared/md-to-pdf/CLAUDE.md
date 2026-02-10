# Markdown to PDF Converter

## What This Does
Converts markdown files into professional, interactive PDF documents with automatic table of contents, clickable navigation, syntax highlighting, and table support. Published as an MCP server (`io.github.wmarceau/md-to-pdf`) on PyPI and the Claude MCP Registry.

## Quick Commands
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/shared/md-to-pdf

# Set library path (macOS -- required for WeasyPrint)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Convert single file
python src/md_to_pdf.py input.md output.pdf

# Using wrapper script (sets library paths automatically)
./src/convert.sh input.md output.pdf

# Batch convert
python src/md_to_pdf.py "docs/*.md" --output-dir pdfs/

# With custom CSS
python src/md_to_pdf.py input.md output.pdf --css custom.css

# Run MCP server
python mcp-server/md_to_pdf_mcp.py

# Build and publish to PyPI (SOP 14)
rm -rf dist/ build/ && python -m build
python -m twine upload dist/* --username __token__ --password $PYPI_TOKEN
```

## Architecture
- **`src/md_to_pdf.py`** - Core conversion logic (markdown2 + WeasyPrint)
- **`src/convert.sh`** - Shell wrapper that sets `DYLD_LIBRARY_PATH` for macOS
- **`src/md_to_pdf_mcp/`** - MCP package directory (for PyPI: `md-to-pdf-mcp`)
- **`mcp-server/md_to_pdf_mcp.py`** - MCP server wrapper
- **`pyproject.toml`** + **`server.json`** - PyPI and MCP Registry config
- **`testing/`** - Multi-agent test infrastructure (SOP 2 template)
- **`workflows/convert-md-to-pdf.md`** - Conversion workflow guide

## Project-Specific Rules
- macOS requires `brew install pango cairo` and `DYLD_LIBRARY_PATH=/opt/homebrew/lib`
- Always use `convert.sh` wrapper or set library path manually -- WeasyPrint will fail without it
- Dependencies: `markdown2`, `weasyprint`, `pygments` (for syntax highlighting)
- MCP name: `io.github.wmarceau/md-to-pdf`
- README must contain `mcp-name:` line near top for MCP Registry ownership verification
- Version must match across: `pyproject.toml`, `server.json`, `src/md_to_pdf_mcp/__init__.py`
- Testing dir is a reference template for SOP 2 (multi-agent testing)

## Relevant SOPs
- SOP 14: MCP Update & Version Bump (for publishing updates)
- SOPs 11-13: MCP Package Structure, PyPI, Registry (initial publish)
- SOP 2: Multi-Agent Testing (`testing/` is a reference example)
- `workflows/convert-md-to-pdf.md` - Step-by-step conversion guide
