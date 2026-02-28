# Service Standards

> Canonical reference for which service to use for each capability. Every new script MUST use these services. No exceptions without updating this document first.

**Last updated:** 2026-02-21
**API keys:** All in `.env` (root of dev-sandbox)

## Media Generation

| Capability | Service | API Key | Cost | Notes |
|-----------|---------|---------|------|-------|
| **Images (budget)** | Replicate — Stable Diffusion XL | `REPLICATE_API_TOKEN` | $0.003/img | Bulk generation, backgrounds |
| **Images (standard)** | Grok Aurora (xAI) | `XAI_API_KEY` | $0.07/img | Default for most use cases |
| **Video (free)** | MoviePy (local) | None | $0 | Always try first, 70-85% success |
| **Video (paid)** | Grok Imagine (xAI) | `XAI_API_KEY` | $0.07/sec ($0.35 min) | Default paid video |
| **Video (premium)** | Veo 3 via Kie.ai | `KIE_API_KEY` | $0.40-$2.00/8s | Premium quality only |
| **Video (character-consistent)** | Kling 3.0 Omni (Replicate) | `REPLICATE_API_TOKEN` | ~$0.50/5s (pro) | Up to 7 reference images for character lock |
| **Video (template)** | Creatomate | `CREATOMATE_API_KEY` | $0.05/video | Template-based overlays, different paradigm |
| **Voice/TTS** | ElevenLabs | `ELEVENLABS_API_KEY` | $22/mo flat (Creator) | Only TTS provider. Voice cloning included |
| **Talking Head** | OmniHuman 1.5 (Replicate) | `REPLICATE_API_TOKEN` | $2.80/20s | ByteDance model, best quality |
| **Graphics (free)** | Pillow/PIL | None | $0 | Branded overlays, educational graphics |
| **Lip Sync** | LatentSync (Replicate) | `REPLICATE_API_TOKEN` | ~$0.09/run | ByteDance, 106K+ runs, best value |

### Retired Services (DO NOT USE)

| Service | Reason | Replacement |
|---------|--------|-------------|
| DALL-E 3 (OpenAI) | Quota exceeded, marginal quality gain over Grok | Grok Aurora |
| Ideogram | Underused, same quality tier as Grok, extra API key | Grok Aurora |
| MiniMax TTS (fal.ai) | fal.ai exhausted, ElevenLabs is superior | ElevenLabs |
| Resemble AI | Test-only, never production | ElevenLabs |
| SadTalker (Replicate) | Low quality | OmniHuman 1.5 |
| Hailuo video (fal.ai) | fal.ai exhausted. Available on Replicate at $0.10/vid if needed | Grok Imagine or Replicate Hailuo |
| OpenAI TTS | Quota exceeded | ElevenLabs |

## Serverless GPU Platforms

| Platform | Status | What We Use It For |
|----------|--------|-------------------|
| **Replicate** | PRIMARY | Images (SD), Talking Head (OmniHuman), Lip Sync (LatentSync), Kling 3.0 Omni (character video), Veo 3 (premium video) |
| **Kie.ai** | EXCEPTION | Veo 3 only (not available elsewhere) |
| ~~fal.ai~~ | RETIRED | Balance exhausted. All models available on Replicate |

**Rule:** If a model exists on Replicate, use Replicate. Only use another platform if the model is unavailable on Replicate.

## Communication & Messaging

| Capability | Service | API Key | Notes |
|-----------|---------|---------|-------|
| **SMS** | Twilio | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | +1 855 239 9364 |
| **Email (send)** | Gmail SMTP | `SMTP_USERNAME` + `SMTP_PASSWORD` | App password, not regular |
| **Email (monitor)** | Gmail API | OAuth (`credentials.json`) | Inbox monitoring |

## File Storage & Collaboration

| Capability | Service | Auth | Notes |
|-----------|---------|------|-------|
| **File sharing** | Google Drive | OAuth (`token_sheets.json`) | Script: `execution/google_drive_share.py` |
| **Spreadsheets** | Google Sheets | OAuth (same token) | Client tracking, analytics |
| **Calendar** | Google Calendar | OAuth (`token.json`) | Scheduling, availability |
| **Client bookings** | Calendly | Webhook | External scheduling |

## Business Operations

| Capability | Service | API Key | Notes |
|-----------|---------|---------|-------|
| **Payments** | Stripe | `STRIPE_SECRET_KEY` | Subscriptions, invoices, webhooks |
| **Lead enrichment** | Apollo.io | `APOLLO_API_KEY` | Contact search, email finder |
| **CRM** | ClickUp | `CLICKUP_API_TOKEN` | Sales pipeline, task management |
| **E-commerce** | Amazon SP-API | OAuth (LWA) | Inventory, pricing, orders |

## Infrastructure

| Capability | Service | Location | Notes |
|-----------|---------|----------|-------|
| **Workflow automation** | n8n | EC2 (34.193.98.97:5678) | 73 endpoints, agent orchestrator |
| **Python bridge** | Flask API | EC2 localhost:5010 | n8n ↔ filesystem bridge |
| **AI models** | Anthropic | API | Claude Sonnet 4.5 for agent tasks |

## API Key Count

**Active keys needed: 11**
1. `REPLICATE_API_TOKEN` — Images, Talking Head, Lip Sync
2. `XAI_API_KEY` — Images (Grok Aurora), Video (Grok Imagine)
3. `KIE_API_KEY` — Video (Veo 3 only)
4. `CREATOMATE_API_KEY` — Template video
5. `ELEVENLABS_API_KEY` — Voice/TTS
6. `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` — SMS
7. `STRIPE_SECRET_KEY` — Payments
8. `APOLLO_API_KEY` — Leads
9. `CLICKUP_API_TOKEN` — CRM
10. Google OAuth (`credentials.json`) — Drive, Sheets, Calendar, Gmail
11. Amazon LWA — SP-API

**Retired keys (can remove from .env when ready):**
- `FAL_API_KEY`
- `IDEOGRAM_API_KEY`
- `OPENAI_API_KEY` (if only used for DALL-E/TTS — check if needed for anything else)
- `RESEMBLE_API_KEY`

## Routers

The two canonical routers that all code should use:

| Router | File | Handles |
|--------|------|---------|
| **Image Router** | `execution/multi_provider_image_router.py` | All image generation |
| **Video Router** | `execution/multi_provider_video_router.py` | All video generation |

**Rule:** Never call a provider API directly. Always go through the router. This ensures cost tracking, rate limiting, and fallback behavior.

## Code Deduplication

| Shared Utility | Canonical Location | Import As |
|---------------|-------------------|-----------|
| Grok image gen | `execution/grok_image_gen.py` | `from execution.grok_image_gen import GrokImageGenerator` |
| Image router | `execution/multi_provider_image_router.py` | `from execution.multi_provider_image_router import MultiProviderImageRouter` |
| Video router | `execution/multi_provider_video_router.py` | `from execution.multi_provider_video_router import MultiProviderVideoRouter` |
| Educational graphics | `execution/educational_graphics.py` | `from execution.educational_graphics import ...` |
| Google Drive | `execution/google_drive_share.py` | `from execution.google_drive_share import upload_and_share` |

**Rule:** If a utility exists in `execution/`, import from there. Never copy the file into your project.
