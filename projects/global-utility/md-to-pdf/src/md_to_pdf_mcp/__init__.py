"""
md-to-pdf-mcp: Convert markdown to professional PDFs via MCP.
"""

__version__ = "1.0.0"

from .converter import (
    DEFAULT_CSS,
    extract_headers,
    generate_toc,
    generate_pdf,
)

__all__ = [
    "DEFAULT_CSS",
    "extract_headers",
    "generate_toc",
    "generate_pdf",
]
