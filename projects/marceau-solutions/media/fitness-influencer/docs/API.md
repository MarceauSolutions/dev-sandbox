# Fitness Influencer AI v2.0 API Documentation

## Overview

The Fitness Influencer AI API provides comprehensive video processing, content optimization, and fitness-specific intelligence for creators.

**Base URL**: `https://api.your-domain.com` (or `http://localhost:8000` for local development)

**Version**: 2.0.0

## Authentication

All endpoints require authentication via header:

```
X-User-ID: your-user-id
X-User-Tier: free|pro|enterprise
```

## Rate Limits

| Tier | Rate Limit | Video Jobs/Day | Caption Jobs/Day |
|------|------------|----------------|------------------|
| Free | 10/minute | 5 | 10 |
| Pro | 60/minute | 50 | Unlimited |
| Enterprise | 300/minute | Unlimited | Unlimited |

Rate limit headers are included in all responses:
- `X-RateLimit-Tier`: Current tier
- `X-RateLimit-Limit`: Rate limit
- `X-RateLimit-Remaining`: Requests remaining
- `Retry-After`: Seconds until retry (when rate limited)

---

## API Endpoints

### Health & Info

#### GET /
Health check and API info.

**Response:**
```json
{
  "name": "Fitness Influencer Assistant API",
  "status": "active",
  "version": "2.0.0",
  "ai_providers": {
    "anthropic": true,
    "xai": true,
    "shotstack": true
  },
  "endpoints": {...},
  "v2_endpoints": {...}
}
```

---

### Background Jobs

#### POST /api/jobs/submit
Submit a background processing job.

**Request Body:**
```json
{
  "job_type": "video_caption|video_filler_removal|video_reframe|video_export|transcription",
  "params": {
    "video_url": "https://example.com/video.mp4",
    "style": "trending"
  },
  "priority": "high|default|low"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "estimated_time": 120
}
```

#### GET /api/jobs/{job_id}/status
Poll job status.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "processing|completed|failed",
  "progress": 75,
  "estimated_remaining": 30,
  "result": {...}
}
```

---

### Transcription

#### POST /api/transcription
Transcribe video/audio with word-level timestamps.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "language": "en|es|pt|auto",
  "include_word_timestamps": true
}
```

**Response:**
```json
{
  "text": "Full transcription...",
  "language": "en",
  "duration": 120.5,
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95}
  ],
  "segments": [...],
  "cost": 0.72
}
```

---

### Caption System

#### POST /api/video/caption
Add word-level captions to video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "style": "trending|glow|minimal|bold|clean|neon|subtitle|fitness|professional|dramatic",
  "position": "bottom|center|top",
  "word_highlight": true,
  "max_words_per_line": 7,
  "font_size": 48,
  "font_color": "#FFFFFF",
  "outline_color": "#000000",
  "outline_width": 2
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

#### GET /api/captions/styles
List available caption styles.

#### GET /api/captions/styles/{style_name}
Get specific style details.

---

### Filler Word Removal

#### POST /api/video/detect-fillers
Detect filler words in video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "sensitivity": "aggressive|moderate|conservative",
  "confidence_threshold": 0.7
}
```

**Response:**
```json
{
  "fillers": [
    {"word": "um", "start": 1.5, "end": 1.8, "confidence": 0.92, "category": "hesitation"}
  ],
  "statistics": {
    "total_filler_count": 12,
    "filler_percentage": 4.5
  },
  "removal_segments": [...]
}
```

#### POST /api/video/remove-fillers
Remove detected fillers from video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "sensitivity": "moderate",
  "preview_only": false
}
```

---

### Auto-Reframe

#### POST /api/video/reframe
Convert video to different aspect ratio.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "target_aspect_ratio": "9:16|1:1|4:5|16:9",
  "tracking_mode": "face|body|auto|center",
  "smoothing_factor": 0.8,
  "safe_zone_margin": 0.1
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

### Platform Export

#### POST /api/video/export
Export video for multiple platforms.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "platforms": ["tiktok", "instagram_reels", "youtube_shorts"],
  "include_captions": true,
  "generate_descriptions": true,
  "hashtag_count": 15,
  "category": "workout",
  "webhook_url": "https://your-webhook.com/callback"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "platforms": ["tiktok", "instagram_reels", "youtube_shorts"]
}
```

#### GET /api/video/export/platforms
List all supported platforms with specs.

**Response:**
```json
{
  "platforms": [
    {
      "id": "tiktok",
      "name": "TikTok",
      "resolution": [1080, 1920],
      "max_duration": 600,
      "bitrate": "3-4Mbps"
    }
  ]
}
```

---

### Video Analysis

#### POST /api/video/analyze
Analyze long-form video structure.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "analysis_mode": "full|quick",
  "segment_duration": 10
}
```

**Response:**
```json
{
  "duration": 600.0,
  "segments": [
    {
      "start": 0, "end": 10,
      "type": "intro",
      "score": 65,
      "audio_energy": 0.6,
      "motion_intensity": 0.3
    }
  ],
  "audio_peaks": [...],
  "scene_changes": [...]
}
```

#### POST /api/video/viral-moments
Detect viral-worthy clips.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "min_duration": 15,
  "max_duration": 60,
  "count": 10
}
```

**Response:**
```json
{
  "moments": [
    {
      "start": 45.0, "end": 75.0,
      "score": 85,
      "category": "hook",
      "components": {
        "hook_strength": 90,
        "audio_energy": 80,
        "visual_variety": 75
      }
    }
  ]
}
```

---

### Hook Analysis

#### POST /api/video/analyze-hook
Analyze first 3 seconds effectiveness.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "hook_duration": 3.0
}
```

**Response:**
```json
{
  "overall_score": 75,
  "grade": "C",
  "components": {
    "action": 80,
    "curiosity": 60,
    "emotion": 70,
    "audio_impact": 85,
    "visual_variety": 75,
    "text_hook": 65
  },
  "improvements": [
    {
      "type": "ADD_TEXT_OVERLAY",
      "priority": 1,
      "description": "Add text hook in first 0.5 seconds"
    }
  ],
  "variants": [...]
}
```

---

### Retention Prediction

#### POST /api/video/predict-retention
Predict audience retention curve.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "target_platform": "tiktok|instagram|youtube_shorts|youtube"
}
```

**Response:**
```json
{
  "predicted_retention": 45.0,
  "grade": "B",
  "retention_curve": [
    {"timestamp": 0, "retention": 100},
    {"timestamp": 3, "retention": 85},
    {"timestamp": 10, "retention": 60}
  ],
  "cliffs": [
    {
      "timestamp": 15.0,
      "drop_percentage": 15,
      "cause": "slow_intro",
      "suggestions": [...]
    }
  ],
  "platform_comparison": {
    "tiktok": {"benchmark": 50, "status": "below", "delta": -5}
  }
}
```

---

### Workout Overlays

#### POST /api/video/add-workout-overlay
Add timer overlay to video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "timer_type": "countdown|countup|interval|rep_counter",
  "preset": "hiit|tabata|emom|amrap|strength|yoga",
  "position": "top_right|top_left|bottom_right|bottom_left|center",
  "style": "minimal|bold|neon|digital",
  "work_duration": 45,
  "rest_duration": 15,
  "rounds": 8
}
```

**Response:**
```json
{
  "success": true,
  "output_path": "/path/to/video_with_timer.mp4"
}
```

#### GET /api/video/add-workout-overlay/presets
List workout presets.

---

### Form Annotations

#### POST /api/video/add-form-annotations
Add form annotations to video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "annotations": [
    {
      "type": "arrow",
      "start": [100, 200],
      "end": [300, 400],
      "color": "#FF0000",
      "start_time": 0,
      "end_time": 5
    },
    {
      "type": "circle",
      "center": [500, 300],
      "radius": 50,
      "pulsing": true
    },
    {
      "type": "text",
      "position": [100, 100],
      "text": "Keep back straight",
      "background": "#000000"
    }
  ],
  "slow_motion_segments": [
    {"start_time": 2, "end_time": 4, "speed": 0.5}
  ]
}
```

---

### Exercise Recognition

#### POST /api/video/detect-exercise
Detect exercise type from video.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "min_confidence": 0.7,
  "enable_rep_counting": true,
  "enable_form_analysis": true
}
```

**Response:**
```json
{
  "success": true,
  "detected_exercise": "squat",
  "exercise_name": "Squat",
  "confidence": 0.85,
  "category": "legs",
  "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
  "rep_count_estimate": 8,
  "avg_rep_duration": 2.5,
  "description": "Performing Squat for 8 reps targeting the quadriceps, glutes, hamstrings.",
  "recommendations": [
    "Focus on even weight distribution between sides",
    "Key cue: Keep chest up and core engaged"
  ],
  "complementary_exercises": ["deadlift", "lunge", "leg_press"],
  "form_score": 75,
  "form_observations": [
    "Minor knee asymmetry detected (8.5°)",
    "Good squat depth achieved"
  ]
}
```

#### GET /api/video/detect-exercise/exercises
List all 20+ supported exercises.

#### GET /api/video/detect-exercise/categories
List exercise categories.

---

### Content Metadata

#### POST /api/content/metadata
Generate hashtags and description.

**Request Body:**
```json
{
  "transcription_text": "Today we're doing squats...",
  "platform": "instagram",
  "category": "workout",
  "hashtag_count": 20
}
```

**Response:**
```json
{
  "hashtags": ["workout", "fitness", "gym", "legday", ...],
  "hashtag_string": "#workout #fitness #gym ...",
  "description": "🔥 Try this workout!...",
  "keywords": ["squat", "legs", "form"]
}
```

---

### Quota Management

#### GET /api/quota/status
Get current quota usage.

**Response:**
```json
{
  "tier": "free",
  "quotas": {
    "video": {"used": 2, "limit": 5, "remaining": 3},
    "caption": {"used": 5, "limit": 10, "remaining": 5},
    "export": {"used": 8, "limit": 20, "remaining": 12}
  },
  "reset_at": "2026-02-08T00:00:00Z"
}
```

#### GET /api/quota/tiers
Get available tiers and limits.

---

## Error Handling

All errors return JSON with consistent format:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Webhooks

For long-running jobs, provide a `webhook_url` to receive completion notifications:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "result": {...}
}
```

---

## SDK Examples

### Python

```python
import httpx

client = httpx.Client(
    base_url="https://api.your-domain.com",
    headers={"X-User-ID": "user123", "X-User-Tier": "pro"}
)

# Transcribe video
response = client.post("/api/transcription", json={
    "video_url": "https://example.com/video.mp4",
    "language": "en"
})
transcription = response.json()

# Add captions
response = client.post("/api/video/caption", json={
    "video_url": "https://example.com/video.mp4",
    "style": "trending",
    "position": "bottom"
})
job = response.json()

# Poll status
while True:
    status = client.get(f"/api/jobs/{job['job_id']}/status").json()
    if status["status"] == "completed":
        break
    time.sleep(5)
```

### cURL

```bash
# Detect exercise
curl -X POST "https://api.your-domain.com/api/video/detect-exercise" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user123" \
  -d '{
    "video_url": "https://example.com/workout.mp4",
    "enable_rep_counting": true
  }'
```

---

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.
