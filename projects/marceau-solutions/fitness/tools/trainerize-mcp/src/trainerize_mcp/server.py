#!/usr/bin/env python3
"""
ABC Trainerize MCP Server

MCP (Model Context Protocol) server providing 27 tools for ABC Trainerize
personal training platform: client management, workout programs, nutrition
coaching, messaging, scheduling, analytics, and habits.

Registry: io.github.wmarceau/trainerize
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    print(
        "Error: MCP SDK not installed. Install with: pip install mcp",
        file=sys.stderr,
    )
    sys.exit(1)

from .trainerize_api import TrainerizeClient, TrainerizeAPIError

# Server instance
server = Server("trainerize")


# ─────────────────────────────────────────────
# Tool Definitions
# ─────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available Trainerize MCP tools."""
    return [
        # ── Client Management ──────────────────────
        Tool(
            name="list_clients",
            description="""List all clients with optional filters.

Returns a paginated list of clients. Filter by tag, status, or compliance level.
Use for client overviews, finding specific groups, or compliance audits.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Filter by tag (e.g., 'VIP', 'weight-loss', 'beginner')"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"],
                        "description": "Filter by client status"
                    },
                    "compliance_level": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Filter by compliance level"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="get_client",
            description="""Get a client's full profile.

Returns complete client data including name, email, assigned programs,
compliance stats, progress summary, and tags.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="create_client",
            description="""Create a new client.

Registers a new client with their name, email, and optionally phone and tags.
They will receive an invitation to join the Trainerize app.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Client's full name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Client's email address"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Client's phone number (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to assign (e.g., ['VIP', 'weight-loss'])"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Initial notes about the client"
                    }
                },
                "required": ["name", "email"]
            }
        ),
        Tool(
            name="update_client",
            description="""Update an existing client's information.

Modify any combination of name, email, phone, tags, notes, or status.
Only provided fields will be updated.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "Updated name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Updated email"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Updated phone number"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Updated tags (replaces existing)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Updated notes"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive"],
                        "description": "Updated status"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="get_client_progress",
            description="""Get a client's weekly/monthly progress report.

Returns workout compliance percentage, nutrition compliance, body measurements,
and trends over the selected period.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["week", "month", "quarter"],
                        "description": "Report period (default: week)",
                        "default": "week"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="tag_clients",
            description="""Add or remove tags from one or more clients.

Bulk tag operation. Useful for organizing clients into groups
or updating client segments.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of client IDs to update"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to add or remove"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove"],
                        "description": "Whether to add or remove the tags",
                        "default": "add"
                    }
                },
                "required": ["client_ids", "tags"]
            }
        ),

        # ── Training Programs ─────────────────────
        Tool(
            name="list_programs",
            description="""List available training programs.

Returns all training program templates with names, descriptions,
duration, and phase information.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="create_program",
            description="""Create a new training program.

Build a structured training program with phases and workouts.
Each phase can have its own duration and assigned workout templates.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Program name (e.g., '12-Week Strength Builder')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Program description and goals"
                    },
                    "phases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "duration_weeks": {"type": "integer"},
                                "workout_ids": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "description": "Program phases with durations and workouts"
                    },
                    "duration_weeks": {
                        "type": "integer",
                        "description": "Total program duration in weeks"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="assign_program",
            description="""Assign a training program to a client.

Links a program template to a client with an optional start date.
The client will see their assigned workouts in the Trainerize app.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "program_id": {
                        "type": "string",
                        "description": "Unique program identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (YYYY-MM-DD), defaults to today"
                    }
                },
                "required": ["client_id", "program_id"]
            }
        ),
        Tool(
            name="list_workouts",
            description="""List available workout templates.

Returns workout templates with exercises, sets, reps, and other details.
Use to browse your workout library.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="create_workout",
            description="""Create a new workout template.

Build a workout with exercises including sets, reps, rest periods, and notes.
Supports strength, cardio, HIIT, and flexibility workout types.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Workout name (e.g., 'Upper Body Push Day')"
                    },
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Exercise name"},
                                "sets": {"type": "integer", "description": "Number of sets"},
                                "reps": {"type": "integer", "description": "Reps per set"},
                                "rest_seconds": {"type": "integer", "description": "Rest between sets"},
                                "weight": {"type": "string", "description": "Weight (e.g., '135 lbs')"},
                                "notes": {"type": "string", "description": "Exercise notes"}
                            },
                            "required": ["name"]
                        },
                        "description": "List of exercises with parameters"
                    },
                    "description": {
                        "type": "string",
                        "description": "Workout description"
                    },
                    "workout_type": {
                        "type": "string",
                        "enum": ["strength", "cardio", "hiit", "flexibility"],
                        "description": "Type of workout"
                    }
                },
                "required": ["name", "exercises"]
            }
        ),
        Tool(
            name="log_workout",
            description="""Log a completed workout for a client.

Record that a client has completed a workout session with optional
details like duration, actual exercises performed, and notes.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "workout_id": {
                        "type": "string",
                        "description": "Workout template identifier"
                    },
                    "completed_at": {
                        "type": "string",
                        "description": "Completion timestamp in ISO format"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Session duration in minutes"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Session notes"
                    },
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sets_completed": {"type": "integer"},
                                "reps_completed": {"type": "integer"},
                                "weight_used": {"type": "string"}
                            }
                        },
                        "description": "Actual exercises performed"
                    }
                },
                "required": ["client_id", "workout_id"]
            }
        ),
        Tool(
            name="send_wod",
            description="""Send Workout of the Day (WOD) to a group.

Broadcasts a specific workout as the WOD to all members of a group,
with an optional accompanying message.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "Unique group identifier"
                    },
                    "workout_id": {
                        "type": "string",
                        "description": "Workout template ID to send as WOD"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional message to accompany the WOD"
                    }
                },
                "required": ["group_id", "workout_id"]
            }
        ),

        # ── Nutrition ─────────────────────────────
        Tool(
            name="get_nutrition_log",
            description="""Get a client's nutrition log.

Returns meal entries with food items, calories, macros (protein, carbs, fat),
and daily totals for the specified date range.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="create_meal_plan",
            description="""Create a meal plan for a client.

Build a structured meal plan with meals, foods, and macro targets.
Set daily calorie and macronutrient goals.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "Meal plan name (e.g., 'Week 1 - Cutting Phase')"
                    },
                    "meals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Meal name (e.g., 'Breakfast')"},
                                "foods": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "quantity": {"type": "string"},
                                            "calories": {"type": "integer"},
                                            "protein_g": {"type": "number"},
                                            "carbs_g": {"type": "number"},
                                            "fat_g": {"type": "number"}
                                        }
                                    }
                                },
                                "calories": {"type": "integer"}
                            }
                        },
                        "description": "List of meals with foods and nutrition info"
                    },
                    "daily_calories": {
                        "type": "integer",
                        "description": "Target daily calorie intake"
                    },
                    "daily_protein_g": {
                        "type": "integer",
                        "description": "Target daily protein (grams)"
                    },
                    "daily_carbs_g": {
                        "type": "integer",
                        "description": "Target daily carbohydrates (grams)"
                    },
                    "daily_fat_g": {
                        "type": "integer",
                        "description": "Target daily fat (grams)"
                    }
                },
                "required": ["client_id", "name", "meals"]
            }
        ),
        Tool(
            name="get_nutrition_compliance",
            description="""Check a client's nutrition compliance stats.

Returns compliance percentage, streak, calorie adherence, and macro
breakdown for the selected period.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["week", "month"],
                        "description": "Compliance period (default: week)",
                        "default": "week"
                    }
                },
                "required": ["client_id"]
            }
        ),

        # ── Communication ─────────────────────────
        Tool(
            name="send_message",
            description="""Send a message to a client.

Send text, voice, or image messages through the Trainerize in-app
messaging system.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text content"
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["text", "voice", "image"],
                        "description": "Type of message (default: text)",
                        "default": "text"
                    },
                    "attachment_url": {
                        "type": "string",
                        "description": "URL to voice note or image attachment"
                    }
                },
                "required": ["client_id", "text"]
            }
        ),
        Tool(
            name="send_group_message",
            description="""Send a message to a group.

Broadcast a message to all members of a Trainerize group.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "Unique group identifier"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text content"
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["text", "voice", "image"],
                        "description": "Type of message (default: text)",
                        "default": "text"
                    },
                    "attachment_url": {
                        "type": "string",
                        "description": "URL to voice note or image attachment"
                    }
                },
                "required": ["group_id", "text"]
            }
        ),
        Tool(
            name="list_messages",
            description="""Get message history with a client.

Returns paginated message history including text, timestamps,
sender info, and attachment URLs.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Messages per page (default: 50)",
                        "default": 50
                    }
                },
                "required": ["client_id"]
            }
        ),

        # ── Scheduling ────────────────────────────
        Tool(
            name="list_appointments",
            description="""List upcoming appointments and classes.

Returns scheduled sessions, classes, and consultations with date/time,
client info, and type filters.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Filter start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Filter end date (YYYY-MM-DD)"
                    },
                    "client_id": {
                        "type": "string",
                        "description": "Filter by specific client"
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["session", "class", "consultation"],
                        "description": "Filter by appointment type"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (default: 25)",
                        "default": 25
                    }
                }
            }
        ),
        Tool(
            name="create_appointment",
            description="""Schedule a new appointment.

Create a training session, class, or consultation with a client
including date/time, location, and notes.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (e.g., 2024-01-15T09:00:00Z)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format"
                    },
                    "appointment_type": {
                        "type": "string",
                        "enum": ["session", "class", "consultation"],
                        "description": "Appointment type (default: session)",
                        "default": "session"
                    },
                    "title": {
                        "type": "string",
                        "description": "Appointment title"
                    },
                    "location": {
                        "type": "string",
                        "description": "Physical location or meeting link"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Appointment notes"
                    }
                },
                "required": ["client_id", "start_time", "end_time"]
            }
        ),
        Tool(
            name="get_availability",
            description="""Check trainer availability for a given date.

Returns available time slots for the specified date and desired
appointment duration.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check (YYYY-MM-DD)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Desired appointment duration in minutes (default: 60)",
                        "default": 60
                    }
                },
                "required": ["date"]
            }
        ),

        # ── Analytics & Reporting ─────────────────
        Tool(
            name="get_compliance_report",
            description="""Get compliance statistics across all clients.

Returns aggregated workout completion rates, nutrition adherence,
engagement metrics, and identifies at-risk clients.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["week", "month", "quarter"],
                        "description": "Report period (default: week)",
                        "default": "week"
                    }
                }
            }
        ),
        Tool(
            name="get_client_metrics",
            description="""Get client body metrics and measurements.

Returns weight, body fat percentage, and body measurements
(chest, waist, hips, arms, etc.) with trends over time.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "metric_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metric types to include (e.g., ['weight', 'body_fat', 'waist'])"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="get_business_stats",
            description="""Get business overview statistics.

Returns active client count, revenue metrics, client retention rates,
session utilization, and growth trends.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "year"],
                        "description": "Report period (default: month)",
                        "default": "month"
                    }
                }
            }
        ),

        # ── Habits ────────────────────────────────
        Tool(
            name="assign_habit",
            description="""Assign a habit to a client.

Create and assign a trackable habit such as drinking water, stretching,
or meal prep. Supports daily or weekly frequency.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "Habit name (e.g., 'Drink 8 glasses of water')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed habit description"
                    },
                    "frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly"],
                        "description": "How often (default: daily)",
                        "default": "daily"
                    },
                    "target_count": {
                        "type": "integer",
                        "description": "Times per frequency period (default: 1)",
                        "default": 1
                    }
                },
                "required": ["client_id", "name"]
            }
        ),
        Tool(
            name="get_habit_progress",
            description="""Check a client's habit streaks and completion rates.

Returns progress data for all or specific habits including current streak,
longest streak, completion percentage, and recent history.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Unique client identifier"
                    },
                    "habit_id": {
                        "type": "string",
                        "description": "Specific habit ID (returns all if omitted)"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["week", "month"],
                        "description": "Progress period (default: week)",
                        "default": "week"
                    }
                },
                "required": ["client_id"]
            }
        ),
    ]


# ─────────────────────────────────────────────
# Tool Call Handler
# ─────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Route tool calls to the appropriate handler.

    Args:
        name: Tool name to invoke.
        arguments: Tool arguments dictionary.

    Returns:
        List of TextContent with the formatted result.
    """
    # Map tool names to their handler functions
    handlers: Dict[str, Any] = {
        # Client Management
        "list_clients": handle_list_clients,
        "get_client": handle_get_client,
        "create_client": handle_create_client,
        "update_client": handle_update_client,
        "get_client_progress": handle_get_client_progress,
        "tag_clients": handle_tag_clients,
        # Training Programs
        "list_programs": handle_list_programs,
        "create_program": handle_create_program,
        "assign_program": handle_assign_program,
        "list_workouts": handle_list_workouts,
        "create_workout": handle_create_workout,
        "log_workout": handle_log_workout,
        "send_wod": handle_send_wod,
        # Nutrition
        "get_nutrition_log": handle_get_nutrition_log,
        "create_meal_plan": handle_create_meal_plan,
        "get_nutrition_compliance": handle_get_nutrition_compliance,
        # Communication
        "send_message": handle_send_message,
        "send_group_message": handle_send_group_message,
        "list_messages": handle_list_messages,
        # Scheduling
        "list_appointments": handle_list_appointments,
        "create_appointment": handle_create_appointment,
        "get_availability": handle_get_availability,
        # Analytics
        "get_compliance_report": handle_get_compliance_report,
        "get_client_metrics": handle_get_client_metrics,
        "get_business_stats": handle_get_business_stats,
        # Habits
        "assign_habit": handle_assign_habit,
        "get_habit_progress": handle_get_habit_progress,
    }

    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        return await handler(arguments)
    except TrainerizeAPIError as e:
        logger.error("Trainerize API error in %s: %s", name, e)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "status_code": e.status_code,
                "tool": name,
                "hint": "Check your Trainerize API credentials and that the resource exists.",
            }, indent=2),
        )]
    except Exception as e:
        logger.exception("Unexpected error in tool %s", name)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "hint": "Check that TRAINERIZE_CLIENT_ID and TRAINERIZE_CLIENT_SECRET are configured.",
            }, indent=2),
        )]


# ─────────────────────────────────────────────
# Helper: Format response
# ─────────────────────────────────────────────

def _format_response(data: Dict[str, Any], tool_name: str) -> List[TextContent]:
    """Format API response data into TextContent.

    Args:
        data: API response dictionary.
        tool_name: Name of the tool for context.

    Returns:
        List containing one TextContent with formatted JSON.
    """
    response = {
        "success": True,
        "tool": tool_name,
        "data": data,
    }
    return [TextContent(
        type="text",
        text=json.dumps(response, indent=2, default=str),
    )]


# ─────────────────────────────────────────────
# Client Management Handlers
# ─────────────────────────────────────────────

async def handle_list_clients(arguments: dict) -> List[TextContent]:
    """Handle listing clients with optional filters."""
    async with TrainerizeClient() as client:
        result = await client.list_clients(
            tag=arguments.get("tag"),
            status=arguments.get("status"),
            compliance_level=arguments.get("compliance_level"),
            page=arguments.get("page", 1),
            per_page=arguments.get("per_page", 25),
        )
    return _format_response(result, "list_clients")


async def handle_get_client(arguments: dict) -> List[TextContent]:
    """Handle getting a full client profile."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_client(client_id)
    return _format_response(result, "get_client")


async def handle_create_client(arguments: dict) -> List[TextContent]:
    """Handle creating a new client."""
    name = arguments.get("name")
    email = arguments.get("email")
    if not name or not email:
        return [TextContent(type="text", text="Error: name and email are required")]

    async with TrainerizeClient() as client:
        result = await client.create_client(
            name=name,
            email=email,
            phone=arguments.get("phone"),
            tags=arguments.get("tags"),
            notes=arguments.get("notes"),
        )
    return _format_response(result, "create_client")


async def handle_update_client(arguments: dict) -> List[TextContent]:
    """Handle updating a client's information."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.update_client(
            client_id=client_id,
            name=arguments.get("name"),
            email=arguments.get("email"),
            phone=arguments.get("phone"),
            tags=arguments.get("tags"),
            notes=arguments.get("notes"),
            status=arguments.get("status"),
        )
    return _format_response(result, "update_client")


async def handle_get_client_progress(arguments: dict) -> List[TextContent]:
    """Handle getting a client's progress report."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_client_progress(
            client_id=client_id,
            period=arguments.get("period", "week"),
        )
    return _format_response(result, "get_client_progress")


async def handle_tag_clients(arguments: dict) -> List[TextContent]:
    """Handle adding/removing tags from clients."""
    client_ids = arguments.get("client_ids")
    tags = arguments.get("tags")
    if not client_ids or not tags:
        return [TextContent(type="text", text="Error: client_ids and tags are required")]

    async with TrainerizeClient() as client:
        result = await client.tag_clients(
            client_ids=client_ids,
            tags=tags,
            action=arguments.get("action", "add"),
        )
    return _format_response(result, "tag_clients")


# ─────────────────────────────────────────────
# Training Program Handlers
# ─────────────────────────────────────────────

async def handle_list_programs(arguments: dict) -> List[TextContent]:
    """Handle listing training programs."""
    async with TrainerizeClient() as client:
        result = await client.list_programs(
            page=arguments.get("page", 1),
            per_page=arguments.get("per_page", 25),
        )
    return _format_response(result, "list_programs")


async def handle_create_program(arguments: dict) -> List[TextContent]:
    """Handle creating a training program."""
    name = arguments.get("name")
    if not name:
        return [TextContent(type="text", text="Error: name is required")]

    async with TrainerizeClient() as client:
        result = await client.create_program(
            name=name,
            description=arguments.get("description"),
            phases=arguments.get("phases"),
            duration_weeks=arguments.get("duration_weeks"),
        )
    return _format_response(result, "create_program")


async def handle_assign_program(arguments: dict) -> List[TextContent]:
    """Handle assigning a program to a client."""
    client_id = arguments.get("client_id")
    program_id = arguments.get("program_id")
    if not client_id or not program_id:
        return [TextContent(type="text", text="Error: client_id and program_id are required")]

    async with TrainerizeClient() as client:
        result = await client.assign_program(
            client_id=client_id,
            program_id=program_id,
            start_date=arguments.get("start_date"),
        )
    return _format_response(result, "assign_program")


async def handle_list_workouts(arguments: dict) -> List[TextContent]:
    """Handle listing workout templates."""
    async with TrainerizeClient() as client:
        result = await client.list_workouts(
            page=arguments.get("page", 1),
            per_page=arguments.get("per_page", 25),
        )
    return _format_response(result, "list_workouts")


async def handle_create_workout(arguments: dict) -> List[TextContent]:
    """Handle creating a workout template."""
    name = arguments.get("name")
    exercises = arguments.get("exercises")
    if not name or not exercises:
        return [TextContent(type="text", text="Error: name and exercises are required")]

    async with TrainerizeClient() as client:
        result = await client.create_workout(
            name=name,
            exercises=exercises,
            description=arguments.get("description"),
            workout_type=arguments.get("workout_type"),
        )
    return _format_response(result, "create_workout")


async def handle_log_workout(arguments: dict) -> List[TextContent]:
    """Handle logging a completed workout."""
    client_id = arguments.get("client_id")
    workout_id = arguments.get("workout_id")
    if not client_id or not workout_id:
        return [TextContent(type="text", text="Error: client_id and workout_id are required")]

    async with TrainerizeClient() as client:
        result = await client.log_workout(
            client_id=client_id,
            workout_id=workout_id,
            completed_at=arguments.get("completed_at"),
            duration_minutes=arguments.get("duration_minutes"),
            notes=arguments.get("notes"),
            exercises=arguments.get("exercises"),
        )
    return _format_response(result, "log_workout")


async def handle_send_wod(arguments: dict) -> List[TextContent]:
    """Handle sending WOD to a group."""
    group_id = arguments.get("group_id")
    workout_id = arguments.get("workout_id")
    if not group_id or not workout_id:
        return [TextContent(type="text", text="Error: group_id and workout_id are required")]

    async with TrainerizeClient() as client:
        result = await client.send_wod(
            group_id=group_id,
            workout_id=workout_id,
            message=arguments.get("message"),
        )
    return _format_response(result, "send_wod")


# ─────────────────────────────────────────────
# Nutrition Handlers
# ─────────────────────────────────────────────

async def handle_get_nutrition_log(arguments: dict) -> List[TextContent]:
    """Handle getting a client's nutrition log."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_nutrition_log(
            client_id=client_id,
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
        )
    return _format_response(result, "get_nutrition_log")


async def handle_create_meal_plan(arguments: dict) -> List[TextContent]:
    """Handle creating a meal plan."""
    client_id = arguments.get("client_id")
    name = arguments.get("name")
    meals = arguments.get("meals")
    if not client_id or not name or not meals:
        return [TextContent(type="text", text="Error: client_id, name, and meals are required")]

    async with TrainerizeClient() as client:
        result = await client.create_meal_plan(
            client_id=client_id,
            name=name,
            meals=meals,
            daily_calories=arguments.get("daily_calories"),
            daily_protein_g=arguments.get("daily_protein_g"),
            daily_carbs_g=arguments.get("daily_carbs_g"),
            daily_fat_g=arguments.get("daily_fat_g"),
        )
    return _format_response(result, "create_meal_plan")


async def handle_get_nutrition_compliance(arguments: dict) -> List[TextContent]:
    """Handle checking nutrition compliance."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_nutrition_compliance(
            client_id=client_id,
            period=arguments.get("period", "week"),
        )
    return _format_response(result, "get_nutrition_compliance")


# ─────────────────────────────────────────────
# Communication Handlers
# ─────────────────────────────────────────────

async def handle_send_message(arguments: dict) -> List[TextContent]:
    """Handle sending a message to a client."""
    client_id = arguments.get("client_id")
    text = arguments.get("text")
    if not client_id or not text:
        return [TextContent(type="text", text="Error: client_id and text are required")]

    async with TrainerizeClient() as client:
        result = await client.send_message(
            client_id=client_id,
            text=text,
            message_type=arguments.get("message_type", "text"),
            attachment_url=arguments.get("attachment_url"),
        )
    return _format_response(result, "send_message")


async def handle_send_group_message(arguments: dict) -> List[TextContent]:
    """Handle sending a message to a group."""
    group_id = arguments.get("group_id")
    text = arguments.get("text")
    if not group_id or not text:
        return [TextContent(type="text", text="Error: group_id and text are required")]

    async with TrainerizeClient() as client:
        result = await client.send_group_message(
            group_id=group_id,
            text=text,
            message_type=arguments.get("message_type", "text"),
            attachment_url=arguments.get("attachment_url"),
        )
    return _format_response(result, "send_group_message")


async def handle_list_messages(arguments: dict) -> List[TextContent]:
    """Handle listing message history with a client."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.list_messages(
            client_id=client_id,
            page=arguments.get("page", 1),
            per_page=arguments.get("per_page", 50),
        )
    return _format_response(result, "list_messages")


# ─────────────────────────────────────────────
# Scheduling Handlers
# ─────────────────────────────────────────────

async def handle_list_appointments(arguments: dict) -> List[TextContent]:
    """Handle listing appointments."""
    async with TrainerizeClient() as client:
        result = await client.list_appointments(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            client_id=arguments.get("client_id"),
            appointment_type=arguments.get("appointment_type"),
            page=arguments.get("page", 1),
            per_page=arguments.get("per_page", 25),
        )
    return _format_response(result, "list_appointments")


async def handle_create_appointment(arguments: dict) -> List[TextContent]:
    """Handle creating an appointment."""
    client_id = arguments.get("client_id")
    start_time = arguments.get("start_time")
    end_time = arguments.get("end_time")
    if not client_id or not start_time or not end_time:
        return [TextContent(type="text", text="Error: client_id, start_time, and end_time are required")]

    async with TrainerizeClient() as client:
        result = await client.create_appointment(
            client_id=client_id,
            start_time=start_time,
            end_time=end_time,
            appointment_type=arguments.get("appointment_type", "session"),
            title=arguments.get("title"),
            location=arguments.get("location"),
            notes=arguments.get("notes"),
        )
    return _format_response(result, "create_appointment")


async def handle_get_availability(arguments: dict) -> List[TextContent]:
    """Handle checking trainer availability."""
    date = arguments.get("date")
    if not date:
        return [TextContent(type="text", text="Error: date is required")]

    async with TrainerizeClient() as client:
        result = await client.get_availability(
            date=date,
            duration_minutes=arguments.get("duration_minutes", 60),
        )
    return _format_response(result, "get_availability")


# ─────────────────────────────────────────────
# Analytics Handlers
# ─────────────────────────────────────────────

async def handle_get_compliance_report(arguments: dict) -> List[TextContent]:
    """Handle getting compliance report across all clients."""
    async with TrainerizeClient() as client:
        result = await client.get_compliance_report(
            period=arguments.get("period", "week"),
        )
    return _format_response(result, "get_compliance_report")


async def handle_get_client_metrics(arguments: dict) -> List[TextContent]:
    """Handle getting client body metrics."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_client_metrics(
            client_id=client_id,
            metric_types=arguments.get("metric_types"),
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
        )
    return _format_response(result, "get_client_metrics")


async def handle_get_business_stats(arguments: dict) -> List[TextContent]:
    """Handle getting business overview statistics."""
    async with TrainerizeClient() as client:
        result = await client.get_business_stats(
            period=arguments.get("period", "month"),
        )
    return _format_response(result, "get_business_stats")


# ─────────────────────────────────────────────
# Habits Handlers
# ─────────────────────────────────────────────

async def handle_assign_habit(arguments: dict) -> List[TextContent]:
    """Handle assigning a habit to a client."""
    client_id = arguments.get("client_id")
    name = arguments.get("name")
    if not client_id or not name:
        return [TextContent(type="text", text="Error: client_id and name are required")]

    async with TrainerizeClient() as client:
        result = await client.assign_habit(
            client_id=client_id,
            name=name,
            description=arguments.get("description"),
            frequency=arguments.get("frequency", "daily"),
            target_count=arguments.get("target_count", 1),
        )
    return _format_response(result, "assign_habit")


async def handle_get_habit_progress(arguments: dict) -> List[TextContent]:
    """Handle checking habit progress."""
    client_id = arguments.get("client_id")
    if not client_id:
        return [TextContent(type="text", text="Error: client_id is required")]

    async with TrainerizeClient() as client:
        result = await client.get_habit_progress(
            client_id=client_id,
            habit_id=arguments.get("habit_id"),
            period=arguments.get("period", "week"),
        )
    return _format_response(result, "get_habit_progress")


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

async def run_server() -> None:
    """Run the Trainerize MCP server."""
    logger.info("Starting ABC Trainerize MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Main entry point for the Trainerize MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
