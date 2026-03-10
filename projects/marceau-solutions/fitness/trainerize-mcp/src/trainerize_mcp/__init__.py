"""
trainerize-mcp: ABC Trainerize personal training tools via MCP.

Provides 27 tools for managing personal training operations:
- Client Management (list, get, create, update, progress, tags)
- Training Programs (list, create, assign, workouts, WOD)
- Nutrition (logs, meal plans, compliance)
- Communication (messages, group messages)
- Scheduling (appointments, availability)
- Analytics (compliance reports, metrics, business stats)
- Habits (assign, progress tracking)
"""

__version__ = "1.0.0"

from .server import server, main
from .trainerize_api import TrainerizeClient, TrainerizeAPIError

__all__ = [
    "server",
    "main",
    "TrainerizeClient",
    "TrainerizeAPIError",
]
