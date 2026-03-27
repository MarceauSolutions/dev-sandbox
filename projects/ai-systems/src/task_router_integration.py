"""
Task Router Integration — Wire task routing into existing dev-sandbox system.

Provides practical integration points for the task router to work with:
- Existing task_classifier.py for initial task analysis
- Agent communication channels (HANDOFF.md, Mem0)
- Basic routing decisions that can be used immediately

This is the minimal viable integration to get routing working in the rebuild process.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Auto-load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our new task router
from .task_router import task_router, initialize_task_router, route_task_to_agent


def integrate_task_router():
    """Initialize and integrate the task router with existing systems."""
    try:
        # Initialize the router
        initialize_task_router()
        logger.info("Task router integration initialized")

        # Test basic routing
        test_result = route_task_to_agent("Build a simple API endpoint")
        logger.info(f"Test routing result: {test_result}")

        return True
    except Exception as e:
        logger.error(f"Failed to integrate task router: {e}")
        return False


def get_routing_recommendation(task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get a routing recommendation for a task.

    This is the main integration point that existing code can call.
    Returns a simple dict that existing systems can understand.
    """
    try:
        result = route_task_to_agent(task_description, context)

        # Simplify the response for existing systems
        return {
            "recommended_agent": result["assigned_agent"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "estimated_hours": result["predicted_completion"],  # This is actually an ISO string
            "router_used": True
        }
    except Exception as e:
        logger.warning(f"Task router failed, falling back to default: {e}")
        # Fallback to basic logic
        return {
            "recommended_agent": "claude_code",  # Safe default
            "confidence": 0.5,
            "reasoning": "Router unavailable, using safe default",
            "estimated_hours": None,
            "router_used": False
        }


def update_agent_status(agent_id: str, task_completed: bool = None, current_load: float = None):
    """
    Update agent status for routing decisions.

    Call this when agent state changes to keep routing accurate.
    """
    try:
        updates = {}
        if task_completed is not None:
            # This is a simplified version - real implementation would need more context
            pass
        if current_load is not None:
            updates["current_load"] = current_load

        if updates:
            task_router.update_agent_state(agent_id, **updates)
            logger.debug(f"Updated agent {agent_id} status: {updates}")
    except Exception as e:
        logger.warning(f"Failed to update agent status: {e}")


def get_router_status() -> Dict[str, Any]:
    """Get current status of the task router for monitoring."""
    try:
        stats = task_router.get_routing_stats()
        return {
            "router_active": True,
            "agents_registered": len(task_router.agents),
            "routing_history_size": len(task_router.routing_history),
            "stats": stats
        }
    except Exception as e:
        return {
            "router_active": False,
            "error": str(e)
        }


# Integration test functions
def test_integration():
    """Test the integration with existing systems."""
    print("Testing task router integration...")

    # Test 1: Basic routing
    task = "Create a user authentication system"
    result = get_routing_recommendation(task)
    print(f"Task: {task}")
    print(f"Recommended: {result['recommended_agent']} (confidence: {result['confidence']:.2f})")
    print()

    # Test 2: Mac-specific task
    mac_task = "Publish package to PyPI"
    mac_result = get_routing_recommendation(mac_task)
    print(f"Task: {mac_task}")
    print(f"Recommended: {mac_result['recommended_agent']} (confidence: {mac_result['confidence']:.2f})")
    print()

    # Test 3: Status check
    status = get_router_status()
    print(f"Router status: {status}")
    print()

    print("Integration test completed")


if __name__ == "__main__":
    # Initialize integration
    if integrate_task_router():
        print("Task router integration successful")
        test_integration()
    else:
        print("Task router integration failed")