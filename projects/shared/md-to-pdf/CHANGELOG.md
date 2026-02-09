# Changelog

All notable changes to the Markdown to PDF Converter project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-13

### Added
- MCP server wrapper (`mcp-server/md_to_pdf_mcp.py`)
- Three MCP tools:
  - `convert_markdown_to_pdf` - Full markdown to PDF conversion
  - `extract_toc` - Table of contents extraction
  - `get_default_styles` - CSS reference for customization
- Registry manifest for MCP Registry submission
- SKILL.md documentation

### Features (from initial development)
- Markdown to PDF conversion with automatic table of contents
- Support for headers, lists, code blocks, tables
- Interactive PDF features (clickable TOC links)
- Custom CSS styling support
- Batch conversion support via CLI
- Professional default styling

## [0.1.0] - 2026-01-12

### Added
- Initial `md_to_pdf.py` converter
- `convert.sh` wrapper for library path handling
- Testing infrastructure with 4-agent test plan
- Multi-agent testing resolved (TESTING-ISSUES-RESOLVED.md)

---

[Unreleased]: https://github.com/williammarceaujr/md-to-pdf/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/williammarceaujr/md-to-pdf/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/williammarceaujr/md-to-pdf/releases/tag/v0.1.0
