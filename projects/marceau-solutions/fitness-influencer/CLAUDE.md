# Fitness Influencer AI Platform

## What This Does
AI-powered content creation and automation platform for fitness influencers. FastAPI backend with video processing (captions, reframing, filler removal), exercise recognition, viral clip detection, workout overlays, and multi-platform export. Includes gamification system and content calendar.

## Quick Commands
```bash
# Start the API server
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
alembic upgrade head

# Run battle test suite
python tests/battle_tests.py

# Start background job worker (requires Redis)
rq worker --with-scheduler
```

## Architecture
- **`backend/main.py`** - FastAPI app entry point (v2.0), includes rate limiting, gamification, CORS
- **`backend/caption_generator.py`** + **`caption_styles.py`** - Word-level karaoke captions (10 styles)
- **`backend/filler_detector.py`** + **`filler_remover.py`** - Context-aware filler word removal
- **`backend/auto_reframe.py`** + **`subject_tracker.py`** - Aspect ratio conversion with face/body tracking
- **`backend/exercise_recognition.py`** - 20+ exercise detection with rep counting (MediaPipe)
- **`backend/viral_detector.py`** + **`hook_analyzer.py`** + **`retention_predictor.py`** - Content analysis
- **`backend/platform_exporter.py`** - Optimized export for 9 platforms (TikTok, IG, YouTube, etc.)
- **`backend/workout_overlays.py`** + **`form_annotations.py`** - HIIT timers, form guidance
- **`backend/gamification_routes.py`** - Player progression, XP, streaks, achievements
- **`backend/task_queue.py`** + **`worker.py`** - Async job processing via Redis + RQ
- **`src/`** - Video compositor, text overlays, peptide graphics
- **`frontend/`** - HTML/CSS/JS dashboard with gamification UI
- **`mcp/`** - MCP server wrapper for Claude integration
- **`data/`** - Exercise library, hashtags, gamification state, B-roll, LUTs, music, SFX
- **`content/`** - Weekly content strategy, video scripts, production plans
- **`alembic/`** - Database migration scripts (SQLite default)

## Project-Specific Rules
- FastAPI v2.0 with structured JSON logging and rate limiting (Free/Pro/Enterprise tiers)
- Video processing requires FFmpeg, OpenCV, and MediaPipe installed system-wide
- Background jobs require Redis running (`redis-server`)
- Database is SQLite by default (`data/fitness.db`), configurable via `DATABASE_URL`
- API keys needed: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (Whisper), optionally `XAI_API_KEY`, `SHOTSTACK_API_KEY`
- Multi-tenant support via `data/tenants/` directory
- Content calendar and weekly strategy docs live in `content/`

## Relevant SOPs
- Testing: `docs/testing-strategy.md` (run battle tests before committing)
- Deployment: SOP 3 (Version Control & Deployment)
- MCP Publishing: SOPs 11-14 (if publishing MCP server)
- Video generation: See `execution/multi_provider_video_router.py` for multi-provider routing
