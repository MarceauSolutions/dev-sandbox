"""
apollo-mcp: Apollo.io lead enrichment and prospecting via MCP.
"""

__version__ = "1.1.1"

from .apollo import ApolloClient, ApolloConfig
from .server import main

__all__ = [
    "ApolloClient",
    "ApolloConfig",
    "main",
    "__version__",
]
