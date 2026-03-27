# Fitness-Influencer Tower Directive

## Domain
Fitness content creation, video processing, client coaching operations, social media automation, and branded PDF generation.

## Core Capabilities
- **Video Processing**: Jump cuts, captions, reframing, batch export, filler removal
- **Video Analysis**: Hook analysis, retention prediction, viral detection
- **Content Generation**: Educational graphics, social media posts, video ads
- **Social Media Automation**: X posting scheduler, multi-platform distribution, Grok image generation
- **Client Operations**: Onboarding packets, workout program PDFs, Stripe payments
- **Coaching Analytics**: SMS campaign performance, funnel tracking
- **Branded PDF Engine**: Proposals, nutrition guides, progress reports
- **Exercise Recognition**: AI-powered exercise identification
- **Workout Overlays**: Form annotations on video

## Entry Point
- FastAPI app: `src/main.py` (port 8000)
- 14 routers registered (8 backend + 6 extracted route modules)
- 96 total routes

## Integration Points
- **pipeline.db**: Reads deals where `tower = "fitness-coaching"` for coaching clients
- **execution/**: Uses multi_provider_image_router, multi_provider_video_router, branded_pdf_engine (shared)
- **lead-generation**: Receives coaching leads via pipeline.db stage changes
- **social-media/**: Contains social media automation sub-project (X posting, content calendar)

## Current Version
1.0.0-dev
