---
name: fitness-influencer-operations
description: Automate fitness influencer workflows including email management, calendar reminders, revenue/spend analytics, video editing (jump cuts), and educational content creation with branded graphics.
allowed-tools: ["Bash(python:*)"]
---

# Fitness Influencer Operations

## Overview

This skill was deployed from the DOE development environment.

**Source Directive:** `directives/fitness_influencer_operations.md`

Automate fitness influencer workflows including email management, calendar reminders, revenue/spend analytics, video editing (jump cuts), and educational content creation with branded graphics.

## When to use

This skill is automatically triggered based on the description above. Claude will detect when your request matches this skill's capabilities.

## Execution Scripts

This skill uses the following execution scripts:

- `execution/video_jumpcut.py` - Automatic jump cut video editing (COMPLETE ✓)
- `execution/educational_graphics.py` - Branded educational content generator (COMPLETE ✓)
- `execution/gmail_monitor.py` - Email monitoring and summarization (COMPLETE ✓)
- `execution/revenue_analytics.py` - Revenue/spend analytics from Google Sheets (COMPLETE ✓)
- `execution/grok_image_gen.py` - AI image generation via Grok API (COMPLETE ✓)

**Status:**
- ✅ Video editing with jump cuts - Fully implemented
- ✅ Educational graphics generation - Fully implemented
- ✅ Email monitoring and digest - Fully implemented
- ✅ Revenue/expense analytics - Fully implemented
- ✅ Grok AI image generation - Fully implemented
- ⏳ Calendar reminders - Planned (can use Google Calendar API manually)
- ⏳ Canva API integration - Planned (API available, not yet implemented)


## Instructions

For detailed implementation instructions, refer to the source directive:

**Directive:** [fitness_influencer_operations.md](../../directives/fitness_influencer_operations.md)

The directive contains:
- Goal and purpose
- Input requirements
- Step-by-step process
- Output format
- Edge cases and error handling
- API considerations
- Best practices

## Usage

python execution scripts

## Deployment Information

- **Deployed:** 2026-01-05 12:51:55
- **Source:** DOE development environment
- **Status:** Production-ready

## Notes

This skill references the directive in `directives/` for complete documentation.
All execution logic is in deterministic Python scripts in `execution/`.

Intermediate files are stored in `.tmp/` and are not committed to version control.
