# Changelog

All notable changes to the Fitness Influencer AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-07

### Overview
Major release transforming MVP (6/10 production readiness) to battle-tested enterprise platform (9/10) with comprehensive video processing, content optimization, and fitness-specific intelligence.

### Added

#### Phase 1: Infrastructure (Stories 1-4)
- **Background Task Queue**: Redis + RQ for async job processing
  - Job submission, status polling, cancellation
  - Priority queues (high, default, low)
  - Graceful in-memory fallback for development
- **SQLite Database**: SQLAlchemy + Alembic migrations
  - Models: User, Job, Content, ContentExport, Analytics, CaptionStyle
  - PostgreSQL support via DATABASE_URL
- **Structured JSON Logging**: Request tracing with unique IDs
  - Log rotation (10MB, 5 files)
  - Railway-compatible output
- **Rate Limiting & Quotas**: SlowAPI with tier-based limits
  - Free: 5 video/10 caption/20 export per day
  - Pro: 50 video, unlimited captions/exports
  - Enterprise: Unlimited everything

#### Phase 2: Caption System (Stories 5-8)
- **OpenAI Whisper Integration**: Speech-to-text with word-level timestamps
  - Multi-language support (en, es, pt, fr, de, it, ja, ko, zh)
  - Chunked processing for long audio (>25MB)
  - Local Whisper fallback
- **Word-Level Captions**: Karaoke-style highlighting synced to speech
  - ASS subtitle format for precise timing
  - Smart line breaking at punctuation/pauses
- **10 Caption Style Templates**: trending, glow, minimal, bold, clean, neon, subtitle, fitness, professional, dramatic
  - Custom style creation
  - 40+ preset colors
- **Caption Customization API**: Position, font, colors, outline, shadow

#### Phase 3: Video Enhancement (Stories 9-12)
- **Filler Word Detection**: Context-aware detection with 15+ patterns
  - Categories: hesitation, discourse, hedge, tag, repetition
  - Sensitivity presets: aggressive, moderate, conservative
- **Smooth Filler Removal**: 50ms audio crossfade, no pops/clicks
  - FFmpeg filter_complex for seamless concatenation
  - Preview mode for before/after comparison
- **Auto-Reframe Engine**: Aspect ratio conversion (9:16, 1:1, 4:5, 16:9)
  - Center-crop with safe zone margin
  - Motion smoothing with exponential average
- **Face & Body Tracking**: MediaPipe integration
  - Subject priority modes: largest, closest, first, all
  - Configurable smoothing factor (0.1-1.0)

#### Phase 4: Platform Export (Stories 13-16)
- **Multi-Platform Presets**: 9 platforms with optimized encoding
  - TikTok, Instagram (Reels/Feed/Story), YouTube (Shorts/Long), LinkedIn, Twitter, Facebook
  - Duration limit enforcement with warnings
- **Platform-Specific Captions**: Style adaptation per platform
  - Emoji support, animation settings, character limits
- **Hashtag & Description Generator**: 100+ fitness hashtags by category
  - AI-powered description with hooks and CTAs
  - Keyword extraction from transcription
- **Batch Export Workflow**: Parallel export to multiple platforms
  - Webhook notifications on completion

#### Phase 5: Content Repurposing (Stories 17-20)
- **Long-Form Video Analyzer**: Audio energy, motion, scene detection
  - Keyword density analysis
  - Segment scoring (0-100)
  - Processing <2 minutes for 30-minute videos
- **Viral Moment Detection**: Top 10 clips with viral scores
  - Hook strength, emotional markers, transformation detection
  - Context-aware clip boundaries (sentence preservation)
- **Hook Analyzer**: First 3 seconds effectiveness scoring
  - 6-component breakdown (action, curiosity, emotion, audio, visual, text)
  - 3 alternative hook variant generation
  - A/B test tracking framework
- **Retention Curve Predictor**: Audience retention prediction
  - Cliff detection (>10% drops) with cause diagnosis
  - Platform benchmark comparison (TikTok 50%, Instagram 40%, YouTube 45%)

#### Phase 6: Fitness Intelligence (Stories 21-23)
- **Workout Timer Overlays**: HIIT, Tabata, EMOM, AMRAP presets
  - Timer types: countdown, countup, interval, rep_counter
  - 4 visual styles: minimal, bold, neon, digital
  - 5 position options
- **Form Annotation Tools**: 5 annotation types
  - Arrow, circle, line, text, highlight_box
  - Slow-motion segments (0.25x-0.75x)
  - 20+ preset colors
- **Exercise Recognition**: 20+ exercises detected via pose estimation
  - MediaPipe Pose integration
  - Rep counting with joint angle oscillation
  - Form analysis with asymmetry detection
  - Auto-generated descriptions for captions
  - Complementary exercise suggestions

#### Phase 6: Integration & Testing (Story 24)
- **Battle Test Suite**: 50+ test cases across 8 categories
  - Input variety, audio quality, content types
  - Duration extremes, stress tests, edge cases
  - API endpoints, integration tests
- **API Documentation**: Complete OpenAPI documentation
- **Performance Benchmarks**: Documented processing times

### New API Endpoints (v2.0)

| Category | Endpoints |
|----------|-----------|
| Jobs | `/api/jobs/submit`, `/api/jobs/{id}/status`, `/api/jobs/{id}/cancel` |
| Transcription | `/api/transcription` |
| Captions | `/api/video/caption`, `/api/captions/styles`, `/api/captions/fonts` |
| Fillers | `/api/video/detect-fillers`, `/api/video/remove-fillers` |
| Reframe | `/api/video/reframe` |
| Export | `/api/video/export`, `/api/video/export/batch`, `/api/video/export/platforms` |
| Analysis | `/api/video/analyze`, `/api/video/viral-moments` |
| Hook | `/api/video/analyze-hook` |
| Retention | `/api/video/predict-retention` |
| Overlays | `/api/video/add-workout-overlay` |
| Annotations | `/api/video/add-form-annotations`, `/api/video/add-slow-motion` |
| Exercise | `/api/video/detect-exercise` |
| Metadata | `/api/content/metadata` |
| Quota | `/api/quota/status`, `/api/quota/tiers` |

### Technical Improvements

- **Async/await throughout** for non-blocking I/O
- **FFmpeg filter_complex** for complex video operations
- **MediaPipe integration** for pose estimation and tracking
- **Graceful degradation** when optional dependencies unavailable
- **Comprehensive error handling** with structured responses
- **Request tracing** with unique IDs for debugging

### Performance

| Operation | v1.0 | v2.0 | Improvement |
|-----------|------|------|-------------|
| 30-min video analysis | N/A | <2 min | New feature |
| Caption generation | 3-5 min | 1-2 min | 2-3x faster |
| Multi-platform export | Sequential | Parallel | 3-5x faster |
| Filler detection | N/A | <30s | New feature |

### Dependencies Added

- `rq>=1.15.0` - Background job queue
- `redis>=5.0.0` - Job persistence
- `sqlalchemy>=2.0.0` - Database ORM
- `alembic>=1.13.0` - Database migrations
- `slowapi>=0.1.9` - Rate limiting
- `httpx>=0.25.0` - Async HTTP client
- `opencv-python>=4.8.0` - Video processing
- `mediapipe>=0.10.0` - Pose estimation
- `numpy>=1.24.0` - Numerical operations

### Known Limitations

- MediaPipe requires installation for exercise recognition (graceful fallback available)
- Local Whisper fallback requires separate installation
- Redis required for production rate limiting (in-memory fallback for development)

### Migration Guide

1. Install new dependencies: `pip install -r requirements.txt`
2. Run database migrations: `alembic upgrade head`
3. Set up Redis for production (optional for development)
4. Update environment variables (see `.env.example`)

---

## [1.0.0] - 2025-12-01

### Added
- Initial MVP release
- Video jump cut (silence removal)
- AI chat integration (Anthropic + xAI)
- Image generation (Grok)
- Email digest system
- Revenue analytics
- Basic video processing

### Known Issues
- Synchronous video processing (blocking)
- No persistent job storage
- Limited caption styles
- No multi-platform export

---

## [0.1.0] - 2025-10-15

### Added
- Project initialization
- Basic FastAPI structure
- Development environment setup
