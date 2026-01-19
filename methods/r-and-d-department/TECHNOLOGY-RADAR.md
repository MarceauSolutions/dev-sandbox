# Technology Radar

*Last Updated: 2026-01-18*

## Overview

Living document tracking AI tools and technologies across four adoption rings:
- **ADOPT**: Use actively in projects
- **TRIAL**: Testing for specific use case
- **ASSESS**: Evaluating, no active testing yet
- **HOLD**: Not recommended / superseded

---

## Video & Image Generation

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| Sora 2 | ASSESS | OpenAI video gen, high quality but limited access | 2026-01-18 |
| Arcade | ASSESS | Google video AI, fast iteration | 2026-01-18 |
| Creatomate | ADOPT | Video templating API, good for fitness content | 2026-01-15 |
| Shotstack | ADOPT | Video rendering API, batch processing | 2026-01-10 |
| Midjourney | ADOPT | Image generation, high quality | 2026-01-01 |
| DALL-E 3 | ADOPT | Image generation via OpenAI API | 2026-01-01 |
| Runway | TRIAL | Gen-3 video, testing for influencer content | 2026-01-10 |

## Voice & Audio

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| AWS Polly Neural | ADOPT | TTS with SSML, Twilio integration | 2026-01-18 |
| ElevenLabs | TRIAL | Voice cloning, more natural but higher cost | 2026-01-15 |
| OpenAI Whisper | ADOPT | Speech-to-text, excellent accuracy | 2026-01-01 |
| Deepgram | ASSESS | Real-time STT, lower latency than Whisper | 2026-01-18 |

## Conversational AI

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| Claude API | ADOPT | Primary LLM for all projects | 2026-01-01 |
| OpenAI GPT-4 | ADOPT | Secondary LLM, function calling | 2026-01-01 |
| Twilio Voice | ADOPT | Phone call handling, TwiML | 2026-01-18 |
| Vapi | ASSESS | Voice AI platform, simpler than custom Twilio | 2026-01-18 |
| Bland AI | ASSESS | Outbound calling platform | 2026-01-18 |

## Automation & Workflow

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| MCP Protocol | ADOPT | Claude tool integration standard | 2026-01-01 |
| n8n | TRIAL | Self-hosted workflow automation | 2026-01-10 |
| Make.com | HOLD | Superseded by n8n for our needs | 2026-01-05 |
| Zapier | HOLD | Too expensive for volume | 2025-12-01 |

## Data & Research

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| Apollo.io | ADOPT | Lead enrichment, contact data | 2026-01-15 |
| Yelp Fusion API | ADOPT | Business data, reviews | 2026-01-10 |
| Google Places API | ADOPT | Business discovery | 2026-01-10 |
| Clay | ASSESS | Data enrichment platform | 2026-01-18 |
| Clearbit | ASSESS | Company enrichment | 2026-01-18 |

## CRM & Sales

| Tool | Ring | Notes | Last Assessed |
|------|------|-------|---------------|
| ClickUp | ADOPT | CRM for leads, task management | 2026-01-15 |
| HubSpot | HOLD | Too complex for current scale | 2025-11-01 |

---

## Recent Discoveries (Queue for Assessment)

*Tools discovered but not yet formally assessed*

| Tool | Source | Potential Use | Discovered |
|------|--------|---------------|------------|
| | | | |

---

## Assessment Schedule

| Frequency | Action |
|-----------|--------|
| Daily | Check AI news feeds, add discoveries to queue |
| Weekly (Monday) | Review queue, move 2-3 to ASSESS |
| Bi-weekly | Complete assessment for ASSESS items |
| Monthly | Review TRIAL items for ADOPT/HOLD decision |

---

## Ring Movement Criteria

### ASSESS → TRIAL
- Clear use case identified
- API/access available
- Budget approved for testing

### TRIAL → ADOPT
- Tested in real project
- Reliable and documented
- Cost-effective for our scale
- Better than current solution

### Any → HOLD
- Superseded by better tool
- Too expensive
- Reliability issues
- Vendor concerns
