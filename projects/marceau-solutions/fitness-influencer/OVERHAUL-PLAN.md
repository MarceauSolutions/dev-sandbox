# Fitness Influencer AI Assistant - Complete Overhaul Plan

**Version**: 2.0.0
**Created**: 2026-02-07
**Status**: AWAITING APPROVAL
**Estimated Duration**: 4-6 weeks (Ralph autonomous + manual validation)

---

## Executive Summary

This plan transforms the fitness influencer AI assistant from MVP (6/10 production readiness) to a **battle-tested, enterprise-grade platform** (9/10) that anticipates all use cases and outperforms competitors like Descript, CapCut, and Opus Clip.

### Key Improvements
1. **Video Editing**: Add text-based editing, auto-reframe, filler word removal, multi-platform export
2. **Content Repurposing**: Long-form → Shorts pipeline (like Opus Clip)
3. **Engagement Optimization**: Hook detection, retention curve analysis, A/B testing
4. **Production Hardening**: Background processing, error recovery, monitoring
5. **Edge Case Handling**: Bad audio, poor lighting, variable formats

---

## Current State Assessment

### What Works Well (Keep)
| Component | Status | Notes |
|-----------|--------|-------|
| Video Jump Cut Editor | ✅ Production | FFmpeg-based, efficient |
| Grok Image Generation | ✅ Production | $0.07/image, reliable |
| Revenue Analytics | ✅ Production | Google Sheets integration |
| Gmail Monitor | ✅ Production | 24-hour categorization |
| Dual-AI Arbitrator | ✅ Production | Cost-optimized routing |
| MCP Package | ✅ Ready | v1.3.0, PyPI ready |

### Critical Gaps (Fix)
| Gap | Impact | Priority |
|-----|--------|----------|
| No auto-captions | High | P0 |
| No filler word removal | High | P0 |
| No multi-platform export | High | P0 |
| No background processing | High | P0 |
| No long-form → shorts | Medium | P1 |
| No retention analytics | Medium | P1 |
| No database persistence | Medium | P1 |
| No structured logging | Low | P2 |
| No rate limiting | Low | P2 |

---

## Competitive Analysis Summary

### Features We Must Have (Table Stakes)

| Feature | Descript | CapCut | Opus Clip | **Our Target** |
|---------|----------|--------|-----------|----------------|
| Auto-Captions | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| Silence Removal | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **⭐⭐⭐⭐⭐** (already have) |
| Filler Word Removal | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | **⭐⭐⭐⭐⭐** |
| Auto-Reframe (9:16) | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| Multi-Platform Export | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| Long → Shorts | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| Fitness Overlays | ❌ | ⭐⭐⭐ | ❌ | **⭐⭐⭐⭐⭐** (unique advantage) |

### Our Unique Differentiators
1. **Fitness-Specific Intelligence**: Workout timers, rep counters, form annotations
2. **Dual-AI Arbitration**: Unbiased tool selection (Claude vs Grok)
3. **Integrated CRM**: Lead → Content → Conversion pipeline
4. **Cost Optimization**: $100-150/month vs $400-800/month competitors

---

## Architecture Overview

### Current Architecture
```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ Video   │ │ Image   │ │ Email   │ │Analytics│        │
│  │ Jumpcut │ │ Grok    │ │ Monitor │ │ Revenue │        │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘        │
│       └──────────┬┴──────────┬┴───────────┘             │
│                  │  REST API  │                          │
└──────────────────┴────────────┴──────────────────────────┘
                         ↓
              Railway.app Deployment
```

### Target Architecture (v2.0)
```
┌──────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend v2.0                       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    BACKGROUND TASK QUEUE                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ Video   │ │ Caption │ │ Reframe │ │ Shorts  │         │   │
│  │  │ Process │ │ Gen     │ │ Engine  │ │ Extract │         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    CORE VIDEO PIPELINE                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ Silence │ │ Filler  │ │ Auto    │ │ Multi-  │         │   │
│  │  │ Remove  │ │ Words   │ │ Caption │ │ Platform│         │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘         │   │
│  │       └─────────────┴──────────┴───────────┘              │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    FITNESS INTELLIGENCE                    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ Workout │ │ Rep     │ │ Form    │ │ Timer   │         │   │
│  │  │ Detect  │ │ Counter │ │ Annotate│ │ Overlay │         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    CONTENT REPURPOSING                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ Hook    │ │ Viral   │ │ Long→   │ │ Platform│         │   │
│  │  │ Detect  │ │ Score   │ │ Shorts  │ │ Optimize│         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └───────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              PERSISTENCE & MONITORING                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │ SQLite  │ │ Logging │ │ Metrics │ │ Alerts  │         │   │
│  │  │ /Postgres│ │ Struct  │ │ Prom    │ │ Webhook │         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
              Railway.app + Background Workers
```

---

## Feature Specifications

### Phase 1: Video Pipeline Enhancements (P0)

#### 1.1 Auto-Caption Generator
**Competitor Reference**: CapCut's one-click captions with AI styling

**Requirements**:
- Whisper-based transcription (OpenAI or local)
- Word-level timing for karaoke-style animation
- 10+ caption styles (Glow, Trending, Clean, Bold, Minimal)
- Position control (top, center, bottom)
- Font customization (size, color, outline, shadow)
- Export as embedded or SRT/VTT

**Edge Cases Handled**:
| Input | Handling |
|-------|----------|
| Multiple speakers | Speaker diarization with labels |
| Background music | Audio isolation before transcription |
| Accents/dialects | Whisper large-v3 model for accuracy |
| Low audio quality | Pre-processing with noise reduction |
| Non-English | Multi-language support (ES, PT, FR) |

**API Endpoint**:
```
POST /api/video/caption
{
    "video_url": "string",
    "style": "trending|glow|minimal|bold|clean",
    "position": "top|center|bottom",
    "language": "en|es|pt|auto",
    "word_highlight": true,
    "max_words_per_line": 7
}
```

#### 1.2 Filler Word Removal
**Competitor Reference**: Descript's Underlord AI

**Requirements**:
- Detect: "um", "uh", "like", "you know", "so", "basically", "actually"
- Remove with smooth audio crossfade
- Visual jump cut at removal points
- Configurable sensitivity (aggressive, moderate, conservative)
- Preview before/after comparison
- Preserve word-level transcription accuracy

**Edge Cases Handled**:
| Input | Handling |
|-------|----------|
| "So" at sentence start | Context-aware detection (keep meaningful "so") |
| Rapid filler clusters | Smooth removal without stutter |
| Mid-word stumbles | Detect and remove partial words |
| Intentional fillers | User whitelist for creative use |

**API Endpoint**:
```
POST /api/video/remove-fillers
{
    "video_url": "string",
    "sensitivity": "aggressive|moderate|conservative",
    "fillers_to_remove": ["um", "uh", "like", "you know"],
    "preserve_rhythm": true
}
```

#### 1.3 Auto-Reframe Engine
**Competitor Reference**: Opus Clip's subject tracking

**Requirements**:
- Face/body detection with tracking
- Smart cropping to 9:16 (vertical), 1:1 (square), 16:9 (landscape)
- Multiple subject handling (priority-based)
- Motion smoothing (no jerky movements)
- Safe zone awareness (keep subjects in frame)
- Batch processing for multi-clip projects

**Edge Cases Handled**:
| Input | Handling |
|-------|----------|
| Multiple people | Priority tracking with manual override |
| Fast movement | Predictive tracking with smoothing |
| Subject exits frame | Intelligent zoom out or cut |
| Wide shots | Focus on center of action |
| Equipment/props | Include relevant props in frame |

**API Endpoint**:
```
POST /api/video/reframe
{
    "video_url": "string",
    "target_aspect": "9:16|1:1|4:5|16:9",
    "tracking_mode": "face|body|auto",
    "smoothing": 0.8,
    "safe_zone_margin": 0.1
}
```

#### 1.4 Multi-Platform Export Optimizer
**Competitor Reference**: Vizard's platform-aware optimization

**Requirements**:
- Platform presets: TikTok, Instagram Reels, YouTube Shorts, LinkedIn, Twitter
- Automatic bitrate optimization per platform
- Caption style adaptation (casual for TikTok, professional for LinkedIn)
- Hashtag/description generation per platform
- Batch export all platforms at once
- Quality preservation (no double-compression)

**Export Specifications**:
| Platform | Resolution | Bitrate | Frame Rate | Max Duration |
|----------|------------|---------|------------|--------------|
| TikTok | 1080x1920 | 2-4 Mbps | 30fps | 3 min |
| IG Reels | 1080x1920 | 3.5-4.5 Mbps | 30fps | 90s |
| YT Shorts | 1080x1920 | 8-15 Mbps | 30/60fps | 60s |
| LinkedIn | 1080x1920 | 5 Mbps | 30fps | 10 min |
| Twitter | 1280x720 | 5 Mbps | 30fps | 2:20 |

**API Endpoint**:
```
POST /api/video/export
{
    "video_url": "string",
    "platforms": ["tiktok", "instagram", "youtube_shorts"],
    "include_captions": true,
    "generate_descriptions": true,
    "hashtag_count": 5
}
```

### Phase 2: Content Repurposing Engine (P1)

#### 2.1 Long-Form to Shorts Extractor
**Competitor Reference**: Opus Clip's ClipAnything

**Requirements**:
- Analyze 10-60 minute videos
- Identify 5-10 "viral moments" based on:
  - Audio energy peaks
  - Keyword density (pain points, benefits)
  - Visual action intensity
  - Emotional markers (laughter, surprise)
- Score each clip for viral potential (1-100)
- Auto-generate hooks for first 3 seconds
- Maintain context (don't cut mid-sentence)

**Viral Scoring Algorithm**:
```
viral_score = (
    hook_strength * 0.30 +
    retention_curve * 0.25 +
    audio_energy * 0.15 +
    visual_variety * 0.15 +
    cta_clarity * 0.15
)
```

**API Endpoint**:
```
POST /api/video/extract-shorts
{
    "video_url": "string",
    "target_duration": [15, 30, 60],
    "max_clips": 10,
    "min_viral_score": 70,
    "include_hooks": true,
    "fitness_focus": true
}
```

#### 2.2 Hook Detection & Optimization
**Competitor Reference**: Industry research on 3-second hooks

**Requirements**:
- Analyze first 3 seconds for hook effectiveness
- Score based on: action, curiosity, emotion, audio
- Suggest improvements (reorder, add text, change music)
- A/B test hook variants
- Track retention correlation

**Hook Types**:
| Type | Description | Fitness Example |
|------|-------------|-----------------|
| Action | Immediate impressive movement | Heavy deadlift, explosive jump |
| Curiosity | Question or unexpected visual | "Watch what happens when..." |
| Transformation | Before/after tease | Split-screen physique change |
| Pain Point | Relatable problem | "Still not seeing results?" |
| Social Proof | Authority/results | "How my clients lost 20lbs" |

**API Endpoint**:
```
POST /api/video/analyze-hook
{
    "video_url": "string",
    "current_hook_duration": 3.0,
    "suggest_improvements": true,
    "generate_variants": 3
}
```

#### 2.3 Retention Curve Analyzer
**Requirements**:
- Predict retention curve before publishing
- Identify "cliff" moments where viewers drop off
- Suggest edits to improve retention
- Compare against platform benchmarks
- Track actual vs predicted after publishing

**Retention Benchmarks**:
| Platform | Good | Great | Viral |
|----------|------|-------|-------|
| TikTok | 50% | 70% | 85%+ |
| IG Reels | 40% | 55% | 70%+ |
| YT Shorts | 45% | 60% | 75%+ |

**API Endpoint**:
```
POST /api/video/predict-retention
{
    "video_url": "string",
    "platform": "tiktok|instagram|youtube",
    "return_improvement_suggestions": true
}
```

### Phase 3: Fitness-Specific Intelligence (P1)

#### 3.1 Workout Timer Overlays
**Requirements**:
- HIIT countdown timers (work/rest intervals)
- Rep counters (auto-increment or manual)
- Round indicators
- Exercise name labels
- Progress bars
- Customizable colors/positioning

**Overlay Presets**:
| Preset | Elements | Best For |
|--------|----------|----------|
| HIIT | Timer + Work/Rest indicator | Cardio circuits |
| Strength | Rep counter + Set indicator | Weight training |
| Yoga | Hold timer + Pose name | Flow sequences |
| Running | Distance + Pace + Time | Cardio tracking |

**API Endpoint**:
```
POST /api/video/add-workout-overlay
{
    "video_url": "string",
    "overlay_type": "hiit|strength|yoga|running",
    "intervals": [
        {"label": "Squats", "duration": 45, "type": "work"},
        {"label": "Rest", "duration": 15, "type": "rest"}
    ],
    "position": "top_right",
    "style": "minimal|bold|neon"
}
```

#### 3.2 Form Annotation System
**Requirements**:
- Draw arrows pointing to form cues
- Circle areas of focus
- Add text labels for muscle groups
- Slow-motion replay with annotations
- Split-screen correct vs incorrect form
- Voiceover sync for cues

**Annotation Types**:
| Type | Use Case | Visual |
|------|----------|--------|
| Arrow | Point to form element | Animated arrow |
| Circle | Highlight muscle group | Pulsing circle |
| Line | Show movement path | Traced line |
| Text | Exercise/muscle name | Floating label |
| Split | Compare form | Side-by-side |

**API Endpoint**:
```
POST /api/video/add-form-annotations
{
    "video_url": "string",
    "annotations": [
        {"type": "arrow", "from": [100, 200], "to": [150, 180], "label": "Keep back straight"},
        {"type": "circle", "center": [300, 400], "radius": 50, "label": "Glutes engaged"}
    ],
    "slow_motion_segments": [{"start": 2.0, "end": 4.0, "speed": 0.5}]
}
```

#### 3.3 Exercise Recognition
**Requirements**:
- Identify exercise type from video
- Suggest rep count (if detectable)
- Recommend complementary exercises
- Tag for content categorization
- Auto-generate video descriptions

**Supported Exercises** (Phase 1):
- Squats (back, front, goblet)
- Deadlifts (conventional, sumo, Romanian)
- Bench press (flat, incline, decline)
- Pull-ups/Chin-ups
- Rows (bent over, cable, dumbbell)
- Lunges (forward, reverse, walking)
- Planks (standard, side, variations)
- Push-ups (standard, diamond, wide)

**API Endpoint**:
```
POST /api/video/detect-exercise
{
    "video_url": "string",
    "return_recommendations": true,
    "generate_description": true
}
```

### Phase 4: Production Hardening (P0)

#### 4.1 Background Task Queue
**Requirements**:
- Async processing for all video operations
- Job status polling (queued, processing, complete, failed)
- Progress percentage updates
- Webhook notifications on completion
- Priority queue (paid users first)
- Retry with exponential backoff

**Implementation**: Redis + RQ (or Celery)

**API Endpoints**:
```
POST /api/jobs/submit
→ {"job_id": "abc123", "status": "queued", "estimated_time": 120}

GET /api/jobs/{job_id}/status
→ {"status": "processing", "progress": 45, "estimated_remaining": 60}

POST /api/jobs/{job_id}/cancel
→ {"status": "cancelled"}
```

#### 4.2 Database Persistence
**Requirements**:
- SQLite for Railway (single instance)
- PostgreSQL option for scaling
- Store: jobs, users, content, analytics
- Automatic migrations
- Backup/restore capability

**Schema**:
```sql
-- Jobs table
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,  -- caption, reframe, export, etc.
    status TEXT,  -- queued, processing, complete, failed
    input_url TEXT,
    output_url TEXT,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Content table
CREATE TABLE content (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    original_url TEXT,
    processed_urls JSON,  -- {tiktok: url, instagram: url, ...}
    metadata JSON,
    viral_score INTEGER,
    created_at TIMESTAMP
);

-- Analytics table
CREATE TABLE analytics (
    id TEXT PRIMARY KEY,
    content_id TEXT,
    platform TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    retention_curve JSON,
    recorded_at TIMESTAMP
);
```

#### 4.3 Structured Logging & Monitoring
**Requirements**:
- JSON-formatted logs
- Request/response tracing
- Error categorization
- Performance metrics
- Webhook alerts for errors

**Log Format**:
```json
{
    "timestamp": "2026-02-07T10:30:00Z",
    "level": "INFO",
    "request_id": "abc123",
    "endpoint": "/api/video/caption",
    "user_id": "user_456",
    "duration_ms": 2500,
    "status": "success",
    "metadata": {"video_duration": 60, "caption_style": "trending"}
}
```

#### 4.4 Rate Limiting & Quotas
**Requirements**:
- Per-user rate limits
- Tier-based quotas (free, pro, enterprise)
- Graceful degradation when limits hit
- Clear error messages with retry-after

**Tier Limits**:
| Tier | Video Processing | Captions | Exports/Day |
|------|------------------|----------|-------------|
| Free | 5/day | 10/day | 20 |
| Pro | 50/day | Unlimited | Unlimited |
| Enterprise | Unlimited | Unlimited | Unlimited |

#### 4.5 Error Recovery System
**Requirements**:
- Automatic retry for transient failures
- Dead letter queue for manual review
- Partial result preservation
- User notification on failure
- Rollback capability

**Retry Policy**:
```python
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2,
    "retryable_errors": [
        "ECONNREFUSED",
        "ETIMEDOUT",
        "rate_limit",
        "temporary_failure"
    ]
}
```

---

## Edge Case Handling Matrix

### Video Input Quality

| Issue | Detection | Handling |
|-------|-----------|----------|
| **Low resolution** (<720p) | Check dimensions | Warn user, proceed with AI upscaling option |
| **Bad audio** | SNR analysis | Apply noise reduction, warn if too degraded |
| **Variable frame rate** | FFprobe analysis | Normalize to constant frame rate |
| **Corrupt file** | FFprobe validation | Clear error message, suggest re-upload |
| **Wrong aspect ratio** | Metadata check | Auto-detect and suggest reframe |
| **No audio track** | Stream analysis | Proceed without captions, suggest music |
| **Interlaced video** | FFprobe | Deinterlace before processing |
| **HDR content** | Color space check | Tone map to SDR for social platforms |

### Audio Quality

| Issue | Detection | Handling |
|-------|-----------|----------|
| **Background noise** | SNR < 15dB | Apply spectral subtraction |
| **Echo/reverb** | Reverb detection | Apply dereverb filter |
| **Clipping** | Peak analysis | Apply limiter, warn about quality |
| **Multiple speakers** | Diarization | Label speakers, offer separation |
| **Music overlay** | Source separation | Isolate voice for captions |
| **Low volume** | LUFS analysis | Normalize to -14 LUFS |
| **Mono audio** | Channel check | Upmix to stereo if needed |

### Content Edge Cases

| Issue | Detection | Handling |
|-------|-----------|----------|
| **No faces detected** | Face detection | Use body tracking, center-frame fallback |
| **Too many subjects** | Object counting | Priority-based tracking, user selection |
| **Fast movement** | Motion analysis | Increase tracking smoothing |
| **Green screen** | Chroma detection | Offer background replacement |
| **Text-heavy frames** | OCR detection | Avoid cutting mid-text |
| **Watermarks** | Pattern detection | Warn user, offer removal option |
| **Copyright audio** | Audio fingerprint | Warn, suggest royalty-free alternatives |

---

## Battle Testing Plan

### Test Categories

#### 1. Input Variety Testing
- [ ] 4K source video (2160p)
- [ ] 720p source video
- [ ] 480p source video (edge case)
- [ ] Variable frame rate (GoPro footage)
- [ ] iPhone ProRes video
- [ ] Android compressed video
- [ ] Screen recording with cursor
- [ ] Zoom meeting recording
- [ ] Multiple aspect ratios (16:9, 4:3, 1:1, 9:16)
- [ ] Videos with no audio
- [ ] Audio-only with static image
- [ ] HDR video
- [ ] 60fps+ video

#### 2. Audio Quality Testing
- [ ] Professional lavalier mic
- [ ] Phone microphone (variable quality)
- [ ] Gym ambient noise
- [ ] Outdoor wind noise
- [ ] Echo-heavy room
- [ ] Multiple overlapping speakers
- [ ] Music playing in background
- [ ] Whispered speech
- [ ] Shouting/loud speech
- [ ] Non-native English speakers
- [ ] Spanish/Portuguese content

#### 3. Content Type Testing
- [ ] Talking head (single person)
- [ ] Workout demonstration (full body)
- [ ] Form breakdown (close-up)
- [ ] Multi-person training session
- [ ] Gym B-roll (no faces)
- [ ] Before/after transformation
- [ ] Nutrition/meal prep
- [ ] Tutorial with screen share
- [ ] Podcast interview style
- [ ] Vlog style (moving camera)

#### 4. Duration Testing
- [ ] 15-second short
- [ ] 60-second reel
- [ ] 3-minute tutorial
- [ ] 10-minute workout
- [ ] 30-minute full session
- [ ] 60-minute podcast

#### 5. Stress Testing
- [ ] 10 concurrent jobs
- [ ] 50 concurrent jobs
- [ ] 100 concurrent jobs (load limit)
- [ ] Large file (2GB+)
- [ ] Multiple sequential jobs
- [ ] Job cancellation mid-process
- [ ] Server restart during processing
- [ ] Database connection failure
- [ ] Third-party API timeout (Whisper, FFmpeg)

#### 6. Platform Compliance Testing
- [ ] TikTok upload and playback
- [ ] Instagram Reels upload and playback
- [ ] YouTube Shorts upload and playback
- [ ] LinkedIn video upload
- [ ] Twitter video upload
- [ ] Caption rendering on each platform
- [ ] Hashtag acceptance per platform
- [ ] File size limits per platform

---

## Ralph PRD Structure

This overhaul will be executed via Ralph with the following story breakdown:

### PRD: Fitness Influencer AI v2.0

```json
{
  "metadata": {
    "prd_name": "Fitness Influencer AI v2.0 Overhaul",
    "objective": "Transform MVP to battle-tested enterprise platform",
    "total_stories": 24,
    "autonomous_mode": false,
    "checkpoint_stories": [4, 8, 12, 16, 20, 24],
    "branchName": "feature/v2-overhaul",
    "created": "2026-02-07",
    "estimated_duration": "4-6 weeks"
  }
}
```

### Story Breakdown

#### Phase 1: Infrastructure (Stories 1-4)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 001 | Set up background task queue (Redis + RQ) | No |
| 002 | Add SQLite database with migrations | No |
| 003 | Implement structured logging | No |
| 004 | Add rate limiting and quotas | **CHECKPOINT** |

#### Phase 2: Caption System (Stories 5-8)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 005 | Integrate Whisper transcription | No |
| 006 | Build word-level caption generator | No |
| 007 | Create 10 caption style templates | No |
| 008 | Add caption position/font customization | **CHECKPOINT** |

#### Phase 3: Video Enhancement (Stories 9-12)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 009 | Build filler word detection | No |
| 010 | Implement smooth audio removal | No |
| 011 | Create auto-reframe engine | No |
| 012 | Add face/body tracking | **CHECKPOINT** |

#### Phase 4: Platform Export (Stories 13-16)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 013 | Build multi-platform export presets | No |
| 014 | Add platform-specific caption styling | No |
| 015 | Implement hashtag/description generator | No |
| 016 | Create batch export workflow | **CHECKPOINT** |

#### Phase 5: Content Repurposing (Stories 17-20)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 017 | Build long-form analyzer | No |
| 018 | Implement viral moment detection | No |
| 019 | Create hook analyzer and optimizer | No |
| 020 | Add retention curve predictor | **CHECKPOINT** |

#### Phase 6: Fitness Intelligence (Stories 21-24)
| Story | Title | Checkpoint |
|-------|-------|------------|
| 021 | Build workout timer overlay system | No |
| 022 | Create form annotation tools | No |
| 023 | Implement exercise recognition | No |
| 024 | Final integration and battle testing | **CHECKPOINT** |

---

## Cost Projections

### Development Cost (One-Time)
| Item | Hours | Rate | Cost |
|------|-------|------|------|
| Ralph development (24 stories) | 60 | $0 (internal) | $0 |
| Third-party API testing | - | - | ~$50 |
| Battle testing | 20 | $0 (internal) | $0 |
| **Total** | 80 | - | **~$50** |

### Operational Cost (Monthly)
| Service | Current | v2.0 | Notes |
|---------|---------|------|-------|
| Railway hosting | $5-10 | $20-30 | Background workers |
| Redis (Railway add-on) | $0 | $5-10 | Task queue |
| Whisper API (OpenAI) | $0 | $20-40 | Transcription |
| Grok images | $28 | $28 | Unchanged |
| Grok videos | $30 | $30 | Unchanged |
| Shotstack | $20 | $20 | Unchanged |
| **Total** | ~$83 | **~$133-168** | +$50-85/month |

### ROI Projection
- **Time saved per video**: 30-60 minutes
- **Videos per week**: 10-15
- **Time saved per week**: 5-15 hours
- **Value at $50/hour**: $250-750/week
- **Monthly value**: $1,000-3,000
- **ROI**: 600-2,200%

---

## Success Metrics

### Technical Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Processing time (1-min video) | 2-5 min | <1 min | Job duration logs |
| Caption accuracy | N/A | >95% WER | Whisper benchmark |
| Auto-reframe accuracy | N/A | >90% face in frame | Manual sampling |
| Platform export success | N/A | >99% | Upload success rate |
| System uptime | ~95% | >99.5% | Railway monitoring |
| Error rate | ~10% | <2% | Structured logs |

### Business Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Videos processed/week | 5-10 | 30-50 | Database count |
| Time saved/video | 0 | 30-60 min | User survey |
| Platform posts/week | 5-10 | 20-30 | Scheduler logs |
| Content viral rate | Unknown | 10% hit 10K+ views | Analytics tracking |
| User satisfaction | N/A | >4.5/5 | Feedback form |

---

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Infrastructure | Background queue, database, logging, rate limiting |
| 2 | Caption System | Whisper integration, caption generator, styles |
| 3 | Video Enhancement | Filler removal, auto-reframe, tracking |
| 4 | Platform Export | Multi-platform presets, batch export |
| 5 | Content Repurposing | Long→shorts, hook detection, retention |
| 6 | Fitness Intelligence + Testing | Timers, annotations, battle testing |

---

## Approval Required

Before proceeding, please confirm:

1. [ ] **Scope**: Is this scope appropriate? Any features to add/remove?
2. [ ] **Priority**: Is the phase ordering correct?
3. [ ] **Timeline**: Is 4-6 weeks acceptable?
4. [ ] **Budget**: Is ~$50 dev + ~$50-85/month additional OK?
5. [ ] **Ralph Mode**: Manual mode (story-by-story) or autonomous with checkpoints?

---

## Next Steps

Upon approval:
1. Create `ralph/prd.json` with full story definitions
2. Initialize feature branch `feature/v2-overhaul`
3. Begin Story 001 (background task queue)
4. Checkpoint reviews at stories 4, 8, 12, 16, 20, 24

**Ready to proceed?**
