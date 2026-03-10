# Fitness Influencer AI Assistant

mcp-name: io.github.wmarceau/fitness-influencer

AI-powered automation suite for fitness content creators. Automates video editing, graphics creation, email management, SMS communication, and revenue analytics.

## Status: Live

**Production URL:** https://fitness-influencer-production.up.railway.app (if deployed)

## Features

| Feature | Script | Cost |
|---------|--------|------|
| Jump-cut video editing | `video_jumpcut.py` | FREE |
| Educational graphics | `educational_graphics.py` | FREE |
| Gmail summarization | `gmail_monitor.py` | FREE |
| Revenue analytics | `revenue_analytics.py` | FREE |
| AI image generation | `grok_image_gen.py` | $0.07/image |
| Calendar reminders | `calendar_reminders.py` | FREE |
| Workout plan generation | `workout_plan_generator.py` | FREE |
| Nutrition guides | `nutrition_guide_generator.py` | FREE |
| Video ads (Shotstack) | `shotstack_api.py` | ~$0.27/video |
| SMS notifications | `twilio_sms.py` | ~$0.01/SMS |

## Directory Structure

```
fitness-influencer/
├── src/                    # Python execution scripts
│   ├── video_jumpcut.py
│   ├── educational_graphics.py
│   ├── gmail_monitor.py
│   ├── revenue_analytics.py
│   ├── grok_image_gen.py
│   ├── calendar_reminders.py
│   ├── nutrition_guide_generator.py
│   ├── workout_plan_generator.py
│   ├── shotstack_api.py
│   ├── video_ads.py
│   ├── creatomate_api.py
│   ├── intelligent_video_router.py
│   ├── fitness_assistant_api.py
│   └── twilio_sms.py
├── frontend/               # Web interface
│   ├── index.html
│   └── terms.html
├── docs/                   # Documentation
└── README.md
```

## Quick Start

### 1. Video Jump-Cut Editing
```bash
python src/video_jumpcut.py --input raw_video.mp4 --output edited.mp4
```

### 2. Create Educational Graphic
```bash
python src/educational_graphics.py --title "5 Morning Habits" --points "Wake early,Hydrate,Stretch,Protein,Plan day" --platform instagram_post
```

### 3. Summarize Emails
```bash
python src/gmail_monitor.py --hours 24
```

### 4. Generate AI Image
```bash
python src/grok_image_gen.py --prompt "Fitness athlete doing deadlift" --count 1
```

## Environment Variables

```env
# Google APIs
GOOGLE_CREDENTIALS_PATH=credentials.json

# AI Services
XAI_API_KEY=your_xai_key_here

# Video Services
SHOTSTACK_API_KEY=your_shotstack_key
CREATOMATE_API_KEY=your_creatomate_key

# Communication
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

## API Endpoints (FastAPI)

When running the API server:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/video/jumpcut` | POST | Process video with jump cuts |
| `/api/graphics/create` | POST | Create educational graphic |
| `/api/email/summary` | GET | Get email summary |
| `/api/image/generate` | POST | Generate AI image |

## Skill Configuration

Located at: `.claude/skills/fitness-influencer-operations/SKILL.md`

Trigger phrases:
- "edit video with jump cuts"
- "create fitness graphic"
- "summarize my emails"
- "generate fitness image"
- "create workout plan"

## Related Documentation

- Main directive: `directives/fitness_influencer_operations.md`
- Skill definition: `.claude/skills/fitness-influencer-operations/SKILL.md`
- Use cases: `.claude/skills/fitness-influencer-operations/USE_CASES.json`
