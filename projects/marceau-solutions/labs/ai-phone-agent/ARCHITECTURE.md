# AI Phone Agent Architecture

## Overview
Handles inbound calls to (855) 239-9364 via ElevenLabs Conversational AI.

## Components

| Component | Purpose | Location |
|-----------|---------|----------|
| ElevenLabs Agent | Handles live calls | Cloud (agent_9801kmgjg670fb7bdv5z9r96y66d) |
| n8n Workflow | Polls for calls, notifies, routes to CRM | n8n (jPcMv1SNVQj4Z4Ln) |
| app.py | Twilio fallback handler | systemd: ai-phone-agent |
| dashboard.py | Warm leads UI | systemd: warm-leads-dashboard |

## Data Flow

1. **Call comes in** → Twilio routes to ElevenLabs
2. **ElevenLabs handles conversation** → Stores transcript
3. **n8n polls every 2 min** → Fetches new conversations
4. **n8n processes** → Scores lead, sends Telegram alert
5. **If qualified** → Adds to Sales Pipeline

## URLs

- Dashboard: https://leads.marceausolutions.com
- Pipeline: https://pipeline.marceausolutions.com
- Health: https://ai-phone.marceausolutions.com/health

## n8n Workflow Setup

1. Workflow ID: `jPcMv1SNVQj4Z4Ln`
2. Required credential: HTTP Header Auth named `ElevenLabs API`
   - Header Name: `xi-api-key`
   - Header Value: [ELEVENLABS_API_KEY from .env]

## Files

- `src/app.py` — Twilio webhook handler (fallback if ElevenLabs unavailable)
- `src/dashboard.py` — Warm leads web dashboard
- `data/processed_conversations.json` — Deduplication tracker
- `data/calls.json` — Call history
- `data/leads.json` — Lead records
