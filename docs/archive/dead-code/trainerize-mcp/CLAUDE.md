# Trainerize MCP

**Version**: See `pyproject.toml` | **Status**: Built | **Type**: MCP Package

## What It Does
MCP server wrapping the ABC Trainerize API (27 tools). Manage PT clients, assign programs and workouts, log sessions, send check-in messages, track nutrition compliance, schedule appointments, and pull business analytics — all from Claude.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Server config | `server.json` |
| Package config | `pyproject.toml` |

## Tool Categories
| Category | Count | What |
|----------|-------|------|
| Client Management | 6 | List, create, update; progress; tags |
| Training Programs | 7 | Programs, workouts, assign, log, WODs |
| Nutrition | 3 | Logs, meal plans, compliance |
| Communication | 3 | Messages to clients/groups, history |
| Scheduling | 3 | Appointments, availability |
| Analytics | 3 | Compliance, body metrics, business stats |
| Habits | 2 | Assign habits, track streaks |

## Prerequisites
- ABC Trainerize account with API access
- OAuth 2.0 credentials from Trainerize Developer Portal
- `TRAINERIZE_CLIENT_ID`, `TRAINERIZE_CLIENT_SECRET` in `.env`

## Related
- PT business hub: `projects/marceau-solutions/pt-business/CLAUDE.md`
- PT coaching ops: `projects/marceau-solutions/pt-business/`
