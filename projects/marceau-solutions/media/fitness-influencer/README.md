# Fitness Influencer AI v2.0

AI-powered content creation and automation platform for fitness influencers.

## Features

### Core Capabilities

- **Auto-Captions**: Word-level karaoke-style captions with 10 preset styles
- **Filler Removal**: Context-aware detection and smooth removal of verbal fillers
- **Auto-Reframe**: Intelligent aspect ratio conversion with face/body tracking
- **Multi-Platform Export**: Optimized encoding for 9 platforms (TikTok, Instagram, YouTube, etc.)
- **Viral Clip Detection**: Identify top clips from long-form content
- **Exercise Recognition**: Detect 20+ exercises with rep counting and form analysis
- **Workout Overlays**: HIIT timers, rep counters, interval indicators

### v2.0 Highlights

| Feature | Description |
|---------|-------------|
| Background Jobs | Async processing with Redis + RQ |
| Word-Level Captions | Karaoke highlighting synced to speech |
| 10 Caption Styles | trending, glow, minimal, bold, fitness, etc. |
| Filler Detection | um, uh, like, you know + 10 more patterns |
| Face/Body Tracking | MediaPipe Pose for intelligent reframing |
| 9 Platform Presets | TikTok, IG Reels, YouTube Shorts, LinkedIn, Twitter |
| Viral Scoring | Hook strength, emotional markers, transformation detection |
| Hook Analysis | 6-component breakdown with improvement suggestions |
| Retention Prediction | Audience drop-off prediction with cliff detection |
| Exercise Recognition | 20+ exercises with rep counting and form analysis |
| Workout Timers | HIIT, Tabata, EMOM, AMRAP presets |
| Form Annotations | Arrows, circles, text labels for instruction |

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/fitness-influencer.git
cd fitness-influencer

# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key  # For Whisper transcription

# Optional
XAI_API_KEY=your-xai-key
SHOTSTACK_API_KEY=your-shotstack-key
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./data/fitness.db
```

### API Usage

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Transcribe video
response = client.post("/api/transcription", json={
    "video_url": "https://example.com/workout.mp4",
    "language": "en"
})
transcription = response.json()

# Add captions
response = client.post("/api/video/caption", json={
    "video_url": "https://example.com/workout.mp4",
    "style": "fitness",
    "position": "bottom"
})

# Detect exercise
response = client.post("/api/video/detect-exercise", json={
    "video_url": "https://example.com/squat.mp4",
    "enable_rep_counting": True
})
print(response.json())
# {
#   "detected_exercise": "squat",
#   "confidence": 0.85,
#   "rep_count_estimate": 8,
#   "form_score": 75
# }
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and API info |
| POST | `/api/jobs/submit` | Submit background job |
| GET | `/api/jobs/{id}/status` | Poll job status |
| POST | `/api/transcription` | Transcribe video/audio |
| POST | `/api/video/caption` | Add captions to video |
| POST | `/api/video/detect-fillers` | Detect filler words |
| POST | `/api/video/remove-fillers` | Remove filler words |
| POST | `/api/video/reframe` | Convert aspect ratio |
| POST | `/api/video/export` | Export to platforms |

### Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/video/analyze` | Analyze video structure |
| POST | `/api/video/viral-moments` | Detect viral clips |
| POST | `/api/video/analyze-hook` | Analyze hook effectiveness |
| POST | `/api/video/predict-retention` | Predict retention curve |

### Fitness Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/video/detect-exercise` | Detect exercise type |
| POST | `/api/video/add-workout-overlay` | Add timer overlay |
| POST | `/api/video/add-form-annotations` | Add form annotations |
| POST | `/api/video/add-slow-motion` | Add slow motion |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/captions/styles` | List caption styles |
| GET | `/api/video/export/platforms` | List platform specs |
| GET | `/api/video/detect-exercise/exercises` | List supported exercises |
| GET | `/api/quota/status` | Get quota usage |

## Supported Exercises

The exercise recognition system supports 20+ exercises:

| Category | Exercises |
|----------|-----------|
| Legs | Squat, Lunge, Leg Press |
| Back | Deadlift, Bent Over Row, Pull-Up, Lat Pulldown, Romanian Deadlift |
| Chest | Bench Press, Push-Up, Dips |
| Shoulders | Overhead Press, Lateral Raise, Face Pull |
| Arms | Bicep Curl, Tricep Extension |
| Core | Plank, Mountain Climber |
| Glutes | Hip Thrust |
| Full Body | Burpee |

## Supported Platforms

Export-optimized settings for 9 platforms:

| Platform | Resolution | Max Duration | Bitrate |
|----------|------------|--------------|---------|
| TikTok | 1080x1920 | 10 min | 3-4 Mbps |
| Instagram Reels | 1080x1920 | 90s | 4-4.5 Mbps |
| Instagram Feed | 1080x1350 | 60s | 3.5-4 Mbps |
| YouTube Shorts | 1080x1920 | 60s | 10-15 Mbps |
| YouTube Long | 1920x1080 | 12 hours | 12-20 Mbps |
| LinkedIn | 1080x1920 | 10 min | 5 Mbps |
| Twitter | 1280x720 | 2m 20s | 5 Mbps |

## Caption Styles

10 preset styles optimized for different content:

| Style | Best For | Features |
|-------|----------|----------|
| trending | TikTok, IG | Pop animation, bold text |
| glow | Night content | Glowing effect |
| minimal | Professional | Clean, simple |
| bold | High energy | Large, bouncy |
| clean | Tutorials | Typewriter animation |
| neon | Party/club | Neon glow effect |
| subtitle | YouTube | Traditional subtitles |
| fitness | Workouts | Athletic style |
| professional | LinkedIn | Formal appearance |
| dramatic | Reveals | Dramatic pop |

## Rate Limits

| Tier | Rate Limit | Video Jobs/Day | Caption Jobs/Day |
|------|------------|----------------|------------------|
| Free | 10/min | 5 | 10 |
| Pro | 60/min | 50 | Unlimited |
| Enterprise | 300/min | Unlimited | Unlimited |

## Architecture

```
fitness-influencer/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── task_queue.py           # Background job queue
│   ├── worker.py               # RQ worker processes
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # Database models
│   ├── transcription.py        # Whisper integration
│   ├── caption_generator.py    # Caption system
│   ├── caption_styles.py       # Style templates
│   ├── filler_detector.py      # Filler detection
│   ├── filler_remover.py       # Filler removal
│   ├── auto_reframe.py         # Aspect ratio conversion
│   ├── subject_tracker.py      # Face/body tracking
│   ├── platform_exporter.py    # Multi-platform export
│   ├── video_analyzer.py       # Long-form analysis
│   ├── viral_detector.py       # Viral clip detection
│   ├── hook_analyzer.py        # Hook effectiveness
│   ├── retention_predictor.py  # Retention prediction
│   ├── workout_overlays.py     # Timer overlays
│   ├── form_annotations.py     # Form annotations
│   └── exercise_recognition.py # Exercise detection
├── data/
│   ├── fitness.db              # SQLite database
│   ├── fitness_hashtags.json   # Hashtag library
│   └── exercise_library.json   # Exercise definitions
├── tests/
│   └── battle_tests.py         # 50+ test cases
├── docs/
│   └── API.md                  # API documentation
├── alembic/                    # Database migrations
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## Development

### Running Tests

```bash
# Run battle test suite
python tests/battle_tests.py

# Run specific category
python tests/battle_tests.py --category api_endpoints

# Output as JSON
python tests/battle_tests.py --json
```

### Starting Worker

```bash
# Start background job worker
rq worker --with-scheduler
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Dependencies

### Core
- FastAPI 0.104.1
- SQLAlchemy 2.0+
- Alembic 1.13+
- Redis 5.0+ & RQ 1.15+
- httpx 0.25+

### Video Processing
- FFmpeg (system)
- OpenCV 4.8+
- MediaPipe 0.10+
- MoviePy 1.0.3

### AI
- OpenAI API (Whisper)
- Anthropic API (Claude)
- xAI API (Grok)

## License

Proprietary - Marceau Solutions LLC

## Support

For issues and feature requests, contact: support@marceausolutions.com
