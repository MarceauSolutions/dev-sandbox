# MD to PDF MCP

> Convert Markdown to professional PDFs directly from Claude Desktop

**Package:** `md-to-pdf-mcp`
**Version:** 1.0.1
**Registry:** `io.github.wmarceau/md-to-pdf`

## What does this MCP do?

The MD to PDF MCP adds markdown-to-PDF conversion capabilities to Claude Desktop. Ask Claude to convert your markdown files into professionally styled PDF documents.

## Installation

```bash
pip install md-to-pdf-mcp
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "md-to-pdf": {
      "command": "md-to-pdf-mcp"
    }
  }
}
```

## Available Tools

### convert_md_to_pdf
Convert a markdown file to PDF with optional styling.

**Parameters:**
- `input_path` (required): Path to the markdown file
- `output_path` (optional): Where to save the PDF
- `theme` (optional): Style theme (modern, classic, minimal)

### list_themes
List available PDF themes and their descriptions.

## Example Prompts

Ask Claude:

> "Convert my README.md to a PDF with the modern theme"

> "Turn this markdown document into a professional PDF"

> "Create a PDF from notes.md and save it to ~/Documents/"

## Supported Features

- Headers (H1-H6)
- Bold, italic, strikethrough text
- Code blocks with syntax highlighting
- Tables with borders
- Bullet and numbered lists
- Images (local and remote)
- Blockquotes
- Horizontal rules

## Themes

| Theme | Description |
|-------|-------------|
| modern | Clean, contemporary design with blue accents |
| classic | Traditional document styling |
| minimal | Simple, distraction-free layout |

## FAQ

### What markdown features are supported?
All standard CommonMark features plus GitHub Flavored Markdown extensions like tables and task lists.

### Can I customize the PDF styling?
Choose from built-in themes. Custom CSS support planned for future versions.

### What's the maximum file size?
No hard limit, but very large documents (100+ pages) may take longer to process.

### Does it support images?
Yes, both local file paths and remote URLs are supported.

## Links

- **PyPI:** [pypi.org/project/md-to-pdf-mcp](https://pypi.org/project/md-to-pdf-mcp/)
- **Claude Registry:** `io.github.wmarceau/md-to-pdf`
- **Source:** [github.com/wmarceau/md-to-pdf-mcp](https://github.com/wmarceau/md-to-pdf-mcp)

## License

MIT License - Free for personal and commercial use.
