# Restored Functionality (2026-03-30)

Files restored from commit e58ec2e8 (March 26 restructure).

## High Priority — Autonomous Operations

| File | Purpose | Usage |
|------|---------|-------|
| `execution/autonomous_scheduler.py` | Task scheduler with priority, dependencies, retry | Import and run scheduler loop |
| `execution/tower_loops.py` | Tower-specific autonomous task definitions | Defines 15-min to 6-hr task cycles per tower |
| `projects/shared/voice-ai/auto_lead_detector.py` | Extract leads from Voice AI calls | Called by voice_ai_reporter |
| `execution/twilio_handler.py` | Twilio webhook for calls | Flask routes for /voice webhooks |
| `execution/voice_ai_prompts.py` | Lead qualification voice prompts | Prompt templates for call scripts |
| `projects/lead-generation/src/orchestrator.py` | 7-step daily pipeline automation | Run daily: acquire→score→validate→route→outreach→replies→report |
| `projects/lead-generation/src/autonomous_sales_agent.py` | AI lead scoring & follow-up | Autonomous decision-making for pipeline |

## Medium Priority — Sales Tools

| File | Purpose |
|------|---------|
| `execution/pdf_templates/proposal_template.py` | Branded proposal PDF generation |
| `execution/pdf_templates/leave_behind_template.py` | One-pager for in-person outreach |
| `projects/lead-generation/src/morning_call_sheet.py` | Daily call list with scripts |
| `projects/lead-generation/src/pitch_briefer.py` | Customized pitch per prospect |
| `execution/batch_outreach.py` | Parallel AI outreach calls |
| `execution/voice_engine.py` | Core AI conversation handler |

## Integration Status

- [x] Files restored
- [x] Import paths updated
- [x] Syntax validated
- [ ] Runtime integration with daily_loop.py
- [ ] Launchd/cron scheduling
- [ ] Full testing

## Quick Start

```bash
# Run pipeline orchestrator
cd /home/clawdbot/dev-sandbox
python3 projects/lead-generation/src/orchestrator.py --dry-run

# Start autonomous scheduler
python3 execution/autonomous_scheduler.py

# Generate morning call sheet
python3 projects/lead-generation/src/morning_call_sheet.py
```
