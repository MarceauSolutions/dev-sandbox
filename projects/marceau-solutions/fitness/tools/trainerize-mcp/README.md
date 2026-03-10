# ABC Trainerize MCP Server

MCP (Model Context Protocol) server for the **ABC Trainerize** personal training platform. Provides 27 tools for managing clients, training programs, nutrition coaching, messaging, scheduling, analytics, and habits.

## Overview

ABC Trainerize is the #1 personal training software used by 400K+ trainers worldwide. This MCP server wraps the Trainerize API to give AI assistants (like Claude) full access to your training business operations.

### Capabilities

| Category | Tools | Description |
|----------|-------|-------------|
| **Client Management** | 6 | List, create, update clients; track progress; manage tags |
| **Training Programs** | 7 | Create programs & workouts, assign to clients, log sessions, send WODs |
| **Nutrition** | 3 | View nutrition logs, create meal plans, check compliance |
| **Communication** | 3 | Send messages to clients and groups, view message history |
| **Scheduling** | 3 | Manage appointments, check availability |
| **Analytics** | 3 | Compliance reports, body metrics, business stats |
| **Habits** | 2 | Assign habits, track streaks and progress |

## Setup

### Prerequisites

- Python 3.9+
- ABC Trainerize account with API access
- OAuth 2.0 credentials (client ID and secret)

### Installation

```bash
pip install trainerize-mcp
```

Or install from source:

```bash
git clone https://github.com/MarceauSolutions/dev-sandbox.git
cd dev-sandbox/projects/trainerize-mcp
pip install -e .
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRAINERIZE_CLIENT_ID` | ✅ | OAuth 2.0 Client ID |
| `TRAINERIZE_CLIENT_SECRET` | ✅ | OAuth 2.0 Client Secret |
| `TRAINERIZE_API_URL` | ❌ | API base URL (default: `https://api.trainerize.com`) |

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trainerize": {
      "command": "trainerize-mcp",
      "env": {
        "TRAINERIZE_CLIENT_ID": "your-client-id",
        "TRAINERIZE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Or using `uvx`:

```json
{
  "mcpServers": {
    "trainerize": {
      "command": "uvx",
      "args": ["trainerize-mcp"],
      "env": {
        "TRAINERIZE_CLIENT_ID": "your-client-id",
        "TRAINERIZE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

## Tools Reference

### Client Management

#### `list_clients`
List all clients with optional filters.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag` | string | No | Filter by tag (e.g., "VIP") |
| `status` | string | No | Filter: "active", "inactive", "pending" |
| `compliance_level` | string | No | Filter: "high", "medium", "low" |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Results per page (default: 25) |

#### `get_client`
Get a client's full profile including programs, compliance, and progress.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |

#### `create_client`
Create a new client and send them an invitation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Client's full name |
| `email` | string | Yes | Client's email address |
| `phone` | string | No | Phone number |
| `tags` | string[] | No | Tags to assign |
| `notes` | string | No | Initial notes |

#### `update_client`
Update any client fields (only provided fields are changed).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |
| `name` | string | No | Updated name |
| `email` | string | No | Updated email |
| `phone` | string | No | Updated phone |
| `tags` | string[] | No | Updated tags (replaces existing) |
| `notes` | string | No | Updated notes |
| `status` | string | No | "active" or "inactive" |

#### `get_client_progress`
Get workout compliance, nutrition compliance, and measurements.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |
| `period` | string | No | "week", "month", or "quarter" (default: "week") |

#### `tag_clients`
Bulk add/remove tags from multiple clients.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_ids` | string[] | Yes | List of client IDs |
| `tags` | string[] | Yes | Tags to add or remove |
| `action` | string | No | "add" or "remove" (default: "add") |

---

### Training Programs

#### `list_programs`
List all training program templates.

#### `create_program`
Create a training program with phases and workouts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Program name |
| `description` | string | No | Description and goals |
| `phases` | object[] | No | Phases with durations and workout IDs |
| `duration_weeks` | integer | No | Total duration |

#### `assign_program`
Assign a program to a client.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `program_id` | string | Yes | Program ID |
| `start_date` | string | No | Start date (YYYY-MM-DD) |

#### `list_workouts`
List workout templates in your library.

#### `create_workout`
Create a workout with exercises, sets, reps, and rest periods.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Workout name |
| `exercises` | object[] | Yes | Exercises with sets, reps, rest |
| `description` | string | No | Workout description |
| `workout_type` | string | No | "strength", "cardio", "hiit", "flexibility" |

#### `log_workout`
Record a completed workout session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `workout_id` | string | Yes | Workout template ID |
| `completed_at` | string | No | Completion timestamp (ISO) |
| `duration_minutes` | integer | No | Duration in minutes |
| `notes` | string | No | Session notes |
| `exercises` | object[] | No | Actual exercises performed |

#### `send_wod`
Send Workout of the Day to a group.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | string | Yes | Group ID |
| `workout_id` | string | Yes | Workout to send |
| `message` | string | No | Accompanying message |

---

### Nutrition

#### `get_nutrition_log`
Get a client's meal entries with macros and calories.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

#### `create_meal_plan`
Build a structured meal plan with macro targets.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `name` | string | Yes | Plan name |
| `meals` | object[] | Yes | Meals with foods and nutrition info |
| `daily_calories` | integer | No | Daily calorie target |
| `daily_protein_g` | integer | No | Daily protein target (g) |
| `daily_carbs_g` | integer | No | Daily carbs target (g) |
| `daily_fat_g` | integer | No | Daily fat target (g) |

#### `get_nutrition_compliance`
Check nutrition adherence stats.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `period` | string | No | "week" or "month" |

---

### Communication

#### `send_message`
Send a text, voice, or image message to a client.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `text` | string | Yes | Message content |
| `message_type` | string | No | "text", "voice", or "image" |
| `attachment_url` | string | No | URL for voice/image attachment |

#### `send_group_message`
Broadcast a message to a group.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | string | Yes | Group ID |
| `text` | string | Yes | Message content |
| `message_type` | string | No | "text", "voice", or "image" |
| `attachment_url` | string | No | Attachment URL |

#### `list_messages`
Get message history with a client.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `page` | integer | No | Page number |
| `per_page` | integer | No | Messages per page |

---

### Scheduling

#### `list_appointments`
List upcoming sessions, classes, and consultations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date filter |
| `end_date` | string | No | End date filter |
| `client_id` | string | No | Filter by client |
| `appointment_type` | string | No | "session", "class", "consultation" |

#### `create_appointment`
Schedule a new appointment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `start_time` | string | Yes | Start time (ISO format) |
| `end_time` | string | Yes | End time (ISO format) |
| `appointment_type` | string | No | Type (default: "session") |
| `title` | string | No | Title |
| `location` | string | No | Location or meeting link |
| `notes` | string | No | Notes |

#### `get_availability`
Check available time slots for a date.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date (YYYY-MM-DD) |
| `duration_minutes` | integer | No | Slot duration (default: 60) |

---

### Analytics & Reporting

#### `get_compliance_report`
Aggregated compliance stats across all clients.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | "week", "month", or "quarter" |

#### `get_client_metrics`
Body measurements and trends (weight, body fat, etc.).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `metric_types` | string[] | No | Types to include |
| `start_date` | string | No | Start date |
| `end_date` | string | No | End date |

#### `get_business_stats`
Business overview: active clients, revenue, retention.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | "week", "month", "quarter", "year" |

---

### Habits

#### `assign_habit`
Assign a trackable habit to a client.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `name` | string | Yes | Habit name |
| `description` | string | No | Detailed description |
| `frequency` | string | No | "daily" or "weekly" |
| `target_count` | integer | No | Times per period (default: 1) |

#### `get_habit_progress`
Check habit streaks and completion rates.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Client ID |
| `habit_id` | string | No | Specific habit (all if omitted) |
| `period` | string | No | "week" or "month" |

## API Notes

This MCP server communicates with the ABC Trainerize API using OAuth 2.0 (client credentials flow). The API endpoints follow REST conventions inferred from Trainerize's Zapier integration and standard fitness platform patterns.

### Authentication Flow

1. Client credentials are exchanged for an access token
2. Tokens are automatically refreshed when expired
3. All requests include Bearer token authentication
4. Rate limiting: 60 requests per minute (sliding window)

### Error Handling

All tools return structured error responses with:
- `error`: Human-readable error message
- `status_code`: HTTP status code (if applicable)
- `tool`: Tool name that generated the error
- `hint`: Suggestion for resolving the issue

## License

MIT — See [LICENSE](LICENSE) for details.

## Author

**William Marceau Jr.** — [Marceau Solutions](https://marceausolutions.com)
