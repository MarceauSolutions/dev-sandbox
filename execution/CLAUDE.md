# Execution: Shared Utilities Directory

## What This Does
Contains shared utility scripts used by 2 or more projects. This is the cross-project code layer in the DOE architecture. If a script is only used by one project, it belongs in `projects/[name]/src/` instead.

## When to Add Code Here
```
Is this script used by 2+ projects?
  YES -> Put it in execution/
  NO  -> Put it in projects/[name]/src/
  UNSURE -> Start in projects/[name]/src/, promote here when a second project needs it
```

## Key Script Categories

### Communication & Notifications
- **`gmail_monitor.py`** + **`gmail_api_monitor.py`** - Gmail inbox monitoring and alerts
- **`twilio_sms.py`** - SMS sending via Twilio (used by fitness, amazon, personal-assistant)
- **`twilio_inbox_monitor.py`** - Inbound SMS monitoring
- **`send_onboarding_email.py`** - Email onboarding sequences
- **`email_response_monitor.py`** - Track email responses

### AI Content Generation
- **`grok_image_gen.py`** - Image generation via xAI/Grok Aurora
- **`grok_video_gen.py`** - Video generation via xAI/Grok
- **`multi_provider_image_router.py`** - Multi-provider image routing (Grok, DALL-E, Replicate, Ideogram)
- **`multi_provider_video_router.py`** - Multi-provider video routing (MoviePy, Hailuo, Creatomate, Veo 3)
- **`intelligent_video_router.py`** - Smart video provider selection
- **`moviepy_video_generator.py`** - Local video generation (free tier)
- **`shotstack_api.py`** + **`creatomate_api.py`** - Cloud video APIs
- **`educational_graphics.py`** - Infographic generation
- **`canva_integration.py`** - Canva API wrapper

### Amazon / E-commerce
- **`amazon_sp_api.py`** + **`amazon_fee_calculator.py`** + **`amazon_inventory_optimizer.py`** - SP-API tools
- **`amazon_oauth_server.py`** + **`refresh_amazon_token.py`** - Auth flow

### CRM & Lead Management
- **`clickup_api.py`** + **`clickup_oauth.py`** - ClickUp CRM integration
- **`add_lead.py`** + **`lead_manager.py`** - Lead intake and management
- **`intent_router.py`** - Route inbound requests by intent

### Presentation & Documents
- **`pptx_generator.py`** + **`pptx_editor.py`** - PowerPoint generation/editing
- **`markdown_to_pdf.py`** + **`pdf_outputs.py`** - PDF generation
- **`apply_navy_theme.py`** + **`standardize_experience_slides.py`** - Slide theming

### Infrastructure
- **`agent_bridge_api.py`** - n8n Agent Orchestrator Python Bridge (runs on EC2 localhost:5010)
- **`deploy_to_skills.py`** - Deployment script for all projects
- **`secrets_manager.py`** + **`security_scanner.py`** + **`mcp_security.py`** - Security utilities
- **`revenue_analytics.py`** - Cross-project revenue tracking
- **`session_manager.py`** - Claude session state management

### Fitness-Specific (shared across fitness projects)
- **`fitness_assistant_api.py`** - Fitness API wrapper
- **`workout_plan_generator.py`** + **`nutrition_guide_generator.py`** - Content generators
- **`video_jumpcut.py`** + **`video_ads.py`** + **`video_analytics_dashboard.py`** - Video tools

## Project-Specific Rules
- Never put single-project scripts here -- they belong in `projects/[name]/src/`
- When promoting a script: move file, update imports in all consuming projects, test
- Multi-provider routers track per-provider costs and rate limits with 30-day history
- `agent_bridge_api.py` is the Python Bridge for n8n on EC2 (v5.1-Ultra, 200+ endpoints)
- All scripts read credentials from root `.env` via `python-dotenv`

## Relevant SOPs
- Root `CLAUDE.md` architecture section (Tier 1 vs Tier 2 code placement)
- `docs/architecture-guide.md` - Full decision tree for code placement
- SOP 30: n8n Workflow Management (for `agent_bridge_api.py`)
- `README.md` in this directory - Detailed promotion/demotion guide
