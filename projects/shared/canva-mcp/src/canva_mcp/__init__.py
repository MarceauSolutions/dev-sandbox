"""Canva MCP - Model Context Protocol server for Canva Connect API."""

__version__ = "1.0.0"

from .server import mcp, main
from .auth import CanvaAuth
from .client import CanvaClient, DesignType, ExportFormat, ExportQuality

__all__ = [
    "mcp",
    "main",
    "CanvaAuth",
    "CanvaClient",
    "DesignType",
    "ExportFormat",
    "ExportQuality",
    "__version__",
]
