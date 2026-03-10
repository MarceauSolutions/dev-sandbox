# Fitness Tower — Marceau Fitness

> 1:1 coaching, training programs, fitness influencer automation, and fitness technology.

## Structure
```
fitness/
├── clients/
│   ├── boabfit/          # Julia's 6-week challenge (SMS automation, daily check-ins)
│   └── pt-business/      # William's 1:1 PT coaching ($197/mo)
├── tools/
│   ├── fitness-influencer/      # AI fitness content platform (FitAI)
│   ├── fitness-influencer-mcp/  # MCP package for fitness influencer
│   └── trainerize-mcp/         # Trainerize platform integration
└── CLAUDE.md
```

## Clients

| Client | Dir | Status | Revenue |
|--------|-----|--------|---------|
| BoabFit (Julia) | `clients/boabfit/` | Active — daily SMS automation | Per-program |
| PT Business (William) | `clients/pt-business/` | Active — 1:1 coaching | $197/mo Stripe |

## Tools

| Tool | Dir | Purpose |
|------|-----|---------|
| Fitness Influencer (FitAI) | `tools/fitness-influencer/` | AI content platform for fitness clients |
| Fitness Influencer MCP | `tools/fitness-influencer-mcp/` | MCP server wrapper |
| Trainerize MCP | `tools/trainerize-mcp/` | Trainerize platform integration |

## Revenue
- **PT Coaching**: $197/mo Stripe subscription
- **Stripe link**: `https://buy.stripe.com/14A14n29hdqU48wf5wg3601`
- **Calendly**: `calendly.com/wmarceau/free-fitness-strategy-call`

## n8n Workflows (this tower)
- Coaching-Payment-Welcome (`1wS9VvXIt95BrR9V`)
- Coaching-Monday-Checkin (`aBxCj48nGQVLRRnq`)
- Coaching-Cancellation-Exit (`uKjqRexDIheaDJJH`)
- Fitness-SMS-Outreach (`89XxmBQMEej15nak`)
- Fitness-SMS-Followup-Sequence (`VKC5cifm595JNcwG`)
- BoabFit Daily Check-in SMS (`aiYWIAJnzD4qUplH`)
- Questionnaire Response Watcher (`SNVOcExULzj5mMR8`)

## Key Shared Tools (in `execution/`)
- `execution/workout_plan_generator.py`
- `execution/nutrition_guide_generator.py`
- `execution/coaching_analytics.py`
- `execution/client_questionnaire.py`
- `execution/questionnaire_response_watcher.py`
- PT Tracker Sheet: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`

## Live Services
- **FitAI**: `https://fitai.marceausolutions.com/frontend/index.html`
- **Julia voice clone**: ElevenLabs ID `Dfq9xw2lqy9dGc5FIpi5`

## Adding a New Fitness Client
See `docs/sops/sop-34-influencer-automation-pattern.md` for the full onboarding playbook.
