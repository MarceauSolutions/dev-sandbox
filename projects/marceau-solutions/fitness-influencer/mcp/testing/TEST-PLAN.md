# Fitness Influencer MCP - Test Plan

**Version**: 1.2.0
**Date**: 2026-01-14

## Current MCP Tools (9 total)

| Tool | Module | Cost | Status |
|------|--------|------|--------|
| `create_jump_cut_video` | video_jumpcut.py | FREE | To Test |
| `add_video_branding` | video_jumpcut.py | FREE | To Test |
| `generate_fitness_image` | grok_image_gen.py | $0.07 | Requires API Key |
| `generate_workout_plan` | workout_plan_generator.py | FREE | To Test |
| `get_revenue_report` | revenue_analytics.py | FREE | Requires Google Creds |
| `analyze_content_engagement` | (placeholder) | FREE | Placeholder Only |
| `categorize_comments` | comment_categorizer.py | FREE | To Test |
| `optimize_for_platforms` | cross_platform_optimizer.py | FREE | To Test |
| `generate_content_calendar` | content_calendar.py | FREE | To Test |

## Not Yet Exposed as MCP Tools

These modules exist in `src/` but aren't in the MCP server:

| Module | Description | Recommendation |
|--------|-------------|----------------|
| `educational_graphics.py` | Pillow-based graphics | Add to MCP |
| `gmail_monitor.py` | Email categorization | Add to MCP |
| `nutrition_guide_generator.py` | Nutrition plans | Add to MCP |
| `calendar_reminders.py` | Calendar integration | Add to MCP |
| `twilio_sms.py` | SMS notifications | Add to MCP |
| `shotstack_api.py` | Video ads ($0.27) | Add to MCP |

---

## Test Scenarios

### Scenario 1: FREE Tools (No API Keys Required)

#### 1.1 Comment Categorizer
```python
from fitness_influencer_mcp.comment_categorizer import CommentCategorizer

categorizer = CommentCategorizer()
test_comments = [
    "What's your diet plan? I want to lose weight",
    "CHECK OUT MY PAGE FOR FREE FOLLOWERS!!!",
    "Hey! We'd love to collab, I have 50k followers",
    "You're my inspiration! Been following for years",
    "We're a fitness brand looking for ambassadors",
    "Your form was off in that video, could hurt someone",
    "SCAM ALERT this guy sells fake supplements"
]
results = categorizer.categorize_batch(test_comments)
```

Expected: Each comment categorized with confidence, action, priority

#### 1.2 Cross-Platform Optimizer
```python
from fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer

optimizer = CrossPlatformOptimizer()
results = optimizer.optimize_for_all_platforms(
    content_type="video",
    original_caption="Just hit a new PR on deadlifts! 405lbs at 175 bodyweight. Here's how I got there...",
    video_duration=90,
    hashtags=["fitness", "gym", "deadlift", "gains"]
)
```

Expected: Platform-specific recommendations for 9 platforms

#### 1.3 Content Calendar Generator
```python
from fitness_influencer_mcp.content_calendar import ContentCalendarGenerator

generator = ContentCalendarGenerator()
calendar = generator.generate_calendar(
    days=7,  # Short test
    posts_per_day=2,
    rest_days=["Sunday"]
)
```

Expected: 7-day calendar with balanced effort, no Sunday posts

#### 1.4 Workout Plan Generator
```python
from fitness_influencer_mcp.workout_plan_generator import generate_workout_plan

plan = generate_workout_plan(
    goal="muscle_gain",
    experience="intermediate",
    days_per_week=4,
    equipment="full_gym"
)
```

Expected: 4-day workout split with exercises, sets, reps

### Scenario 2: Video Tools (Requires FFmpeg)

#### 2.1 Jump Cut Video
```python
# Requires: FFmpeg installed, test video file
from fitness_influencer_mcp.video_jumpcut import create_jump_cut_video

result = create_jump_cut_video(
    input_path="test_video.mp4",
    output_path="test_output.mp4",
    silence_threshold=-40,
    min_silence_duration=0.3
)
```

Expected: Video with silence removed, shorter duration

### Scenario 3: API-Dependent Tools

#### 3.1 AI Image Generation (Requires XAI_API_KEY)
```python
# Cost: $0.07 per image
from fitness_influencer_mcp.grok_image_gen import generate_fitness_image

# Only test if API key is available
import os
if os.getenv("XAI_API_KEY"):
    result = generate_fitness_image(
        prompt="Professional gym with modern equipment, dramatic lighting",
        count=1
    )
```

#### 3.2 Revenue Analytics (Requires Google Credentials)
```python
# Requires: GOOGLE_CREDENTIALS_PATH
from fitness_influencer_mcp.revenue_analytics import get_revenue_report

import os
if os.getenv("GOOGLE_CREDENTIALS_PATH"):
    report = get_revenue_report(
        sheet_id="your-sheet-id",
        month="2026-01"
    )
```

---

## Test Commands

### Quick Import Test
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
from src.fitness_influencer_mcp.workout_plan_generator import generate_workout_plan
print('All imports successful')
"
```

### Full Test Script
```bash
python testing/run_tests.py
```

---

## Gap Analysis

### Missing from MCP (should add in v1.3.0):

1. **Nutrition Guide Generator** - Pairs with workout plans
2. **Educational Graphics** - Create infographics
3. **Gmail Monitor** - Summarize brand emails
4. **Calendar Reminders** - Content scheduling
5. **SMS Notifications** - Alert for urgent items
6. **Video Ads (Shotstack)** - Create video ads

### Placeholder Tools:
- `analyze_content_engagement` - Needs YouTube/IG/TikTok API integration

---

## Success Criteria

- [ ] All FREE tools work without API keys
- [ ] Comment categorizer accurately classifies test comments
- [ ] Platform optimizer returns valid recommendations for all 9 platforms
- [ ] Content calendar respects rest days and balances effort
- [ ] Workout plan generates appropriate exercises for goal/experience
- [ ] Video tools work with FFmpeg installed
- [ ] API tools fail gracefully without credentials
