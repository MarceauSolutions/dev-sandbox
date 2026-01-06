# Directive: Fitness Influencer Operations

## Goal

Automate fitness influencer workflows including email management, calendar reminders, revenue/spend analytics, video editing (jump cuts), and educational content creation with branded graphics.

## Context

Fitness influencers need to manage multiple channels (YouTube, Instagram, TikTok), respond to emails, track business metrics, and create high-quality educational content consistently. This directive establishes workflows to automate repetitive tasks and accelerate content creation.

### Technology Stack

**Video Editing:**
- FFmpeg + MoviePy (open-source, free alternative to CapCut)
- Automated jump cut detection and silence removal
- Text overlays and transitions

**Graphics & Design:**
- Pillow (Python) for educational diagrams and overlays
- Canva API for complex branded designs
- Grok/xAI API for AI-generated images ($0.07/image)

**Business Operations:**
- Gmail API for email monitoring and summarization
- Google Calendar API for reminders
- Google Sheets API for revenue/spend analytics

## Available Capabilities

### Email Management
- Automatic email summarization (daily digest)
- Priority email flagging (sponsorships, collaborations, customer inquiries)
- Draft response generation
- Auto-archive low-priority emails

### Calendar & Reminders
- Content publishing schedule tracking
- Collaboration meeting reminders
- Revenue milestone alerts
- Deadline notifications

### Analytics & Reporting
- Revenue tracking by source (sponsorships, course sales, affiliate)
- Spend analysis by category (equipment, software, ads)
- Month-over-month growth metrics
- Profit margin calculations

### Video Editing
- Automatic jump cut detection (remove silence/pauses)
- Multi-clip concatenation
- Branded intro/outro addition
- Thumbnail generation
- Export in platform-specific formats (YouTube, TikTok, Reels)

### Content Creation
- Educational graphics with branded overlays
- Fitness tip cards (matching Fitness_Tips.jpeg style)
- AI-generated placeholder images
- Consistent branding across all content

## Inputs

### Required Credentials

**Google APIs:**
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `GOOGLE_REFRESH_TOKEN` - OAuth refresh token
- Scopes: gmail.readonly, calendar, sheets

**Canva API:**
- `CANVA_API_KEY` - Canva Connect API key
- `CANVA_CLIENT_ID` - OAuth client ID
- `CANVA_CLIENT_SECRET` - OAuth client secret

**Grok/xAI API:**
- `XAI_API_KEY` - xAI API key for image generation

**Brand Assets:**
- Logo files (PNG with transparency)
- Brand colors (hex codes)
- Font preferences
- Template designs

### Operation-Specific Inputs

**Email Summarization:**
- Date range (e.g., "last 24 hours", "this week")
- Priority keywords (e.g., "sponsorship", "collaboration", "payment")

**Video Editing:**
- Raw video file path
- Silence threshold (decibels, default: -40dB)
- Minimum clip duration (seconds, default: 0.5s)
- Output format (mp4, mov, etc.)

**Content Creation:**
- Topic/title (e.g., "Staying Lean Without Tracking Macros")
- Key points (bullet list)
- Target platform (YouTube, Instagram, TikTok)

**Analytics:**
- Time period (month, quarter, year)
- Metrics to include (revenue, spend, profit, growth)

## Tools

### Core Scripts

- `execution/gmail_monitor.py` - Email monitoring and summarization
- `execution/calendar_reminders.py` - Calendar integration and notifications
- `execution/revenue_analytics.py` - Revenue/spend tracking and analysis
- `execution/video_jumpcut.py` - Automatic jump cut video editing
- `execution/educational_graphics.py` - Generate branded educational content
- `execution/canva_integration.py` - Canva API wrapper for complex designs
- `execution/grok_image_gen.py` - AI image generation via Grok API
- `execution/shotstack_api.py` - Video generation from images (Shotstack API)

## Use Cases

### 1. Daily Email Digest

**Natural Language Request**: "Summarize my emails from the last 24 hours and flag anything urgent"

**Process**:
1. Connect to Gmail API
2. Fetch emails from last 24 hours
3. Categorize by type:
   - Sponsorships/collaborations (HIGH PRIORITY)
   - Customer inquiries
   - Newsletters/promotions
   - Administrative
4. Use Claude to summarize each category
5. Flag urgent items requiring response
6. Generate draft responses for common inquiries

**Output**:
```
📧 EMAIL DIGEST - Last 24 Hours

🔴 URGENT (3):
  • Sponsorship inquiry from MuscleTech ($5K offer)
  • Customer refund request (course purchase)
  • YouTube partner program update

📊 BUSINESS (5):
  • Affiliate commission reports
  • Course sales notifications
  • Analytics updates

📬 OTHER (12):
  • Newsletters, promotions, spam

SUGGESTED ACTIONS:
  1. Respond to MuscleTech within 48h
  2. Process refund request
  3. Review YouTube partnership terms
```

### 2. Weekly Revenue Report

**Natural Language Request**: "Show me revenue and expenses for this month compared to last month"

**Process**:
1. Connect to Google Sheets (revenue tracking sheet)
2. Pull current month data
3. Pull previous month data for comparison
4. Calculate:
   - Total revenue by source
   - Total expenses by category
   - Net profit
   - Month-over-month growth %
5. Generate visual report

**Output**:
```
💰 REVENUE REPORT - January 2026

INCOME:
  Sponsorships:    $8,500 (+15% vs Dec)
  Course Sales:    $3,200 (+5% vs Dec)
  Affiliate:       $1,100 (-10% vs Dec)
  ─────────────────────────────
  TOTAL:          $12,800 (+10% vs Dec)

EXPENSES:
  Equipment:       $800
  Software/Tools:  $150
  Ads/Marketing:   $500
  ─────────────────────────────
  TOTAL:          $1,450

NET PROFIT: $11,350 (88.7% margin)

📈 INSIGHTS:
  • Sponsorship growth accelerating
  • Affiliate down due to seasonal trends
  • Profit margin remains strong
```

### 3. Automatic Jump Cut Editing

**Natural Language Request**: "Edit this raw talking-head video - remove silence and add my branded intro/outro"

**Process**:
1. Load video file using FFmpeg
2. Detect silence using audio analysis
   - Threshold: -40dB (configurable)
   - Minimum silence duration: 0.3s
3. Generate cut points
4. Remove silent segments
5. Concatenate remaining clips
6. Add branded intro (5 seconds)
7. Add branded outro (10 seconds)
8. Export in 1080p MP4

**Output**:
- Original: 15:30 minutes
- Edited: 8:45 minutes (43% reduction)
- 47 jump cuts applied
- Total render time: ~2 minutes

### 4. Educational Content Generation

**Natural Language Request**: "Create a fitness tip graphic about 'Staying Lean Without Tracking Macros'"

**Process**:
1. Generate or use provided background image
2. Use Pillow to create graphic:
   - Add title text (styled font)
   - Add 3-5 key points
   - Add Marceau Solutions branding
   - Add logo in bottom corner
   - Apply branded color scheme
3. Export in multiple formats:
   - Instagram Post (1080x1080)
   - Instagram Story (1080x1920)
   - YouTube Thumbnail (1280x720)

**Output**: High-quality branded graphics ready for posting

### 5. Video Series Automation

**Natural Language Request**: "Process this batch of 10 workout videos - add jump cuts, thumbnails, and organize by exercise type"

**Process**:
1. Batch process all videos:
   - Detect silence and apply jump cuts
   - Generate thumbnail from best frame
   - Extract metadata (duration, exercises shown)
2. Organize files:
   - `/strength/` - weightlifting videos
   - `/cardio/` - cardio workout videos
   - `/mobility/` - stretching/mobility videos
3. Create content calendar suggestions
4. Generate YouTube titles and descriptions

**Output**: Organized, edited videos ready for upload

### 6. Calendar Reminder System

**Natural Language Request**: "Remind me to post on Instagram 3x per week and YouTube every Sunday"

**Process**:
1. Create recurring calendar events
2. Send notifications:
   - 1 hour before posting time
   - Include suggested content ideas
   - Track completion
3. Monitor publishing schedule
4. Flag missed deadlines

**Output**: Automated reminders ensure consistent posting

### 7. Video Ad Creation (AI-Generated) ✅ WORKING

**Natural Language Request**: "Create a video ad for @boabfit"

**Process**:
1. Generate AI images with Grok:
   - Prompt: Fitness influencer, workout, motivation, professional
   - Count: 4 images
   - Cost: $0.28
2. Create video with Shotstack:
   - Combine images with transitions (slideLeft)
   - Add headline text overlay
   - Add CTA text overlay
   - Add energetic background music
   - Format: 9:16 vertical for social media
   - Cost: ~$0.06
3. Wait for render (30-60 seconds)
4. Return video URL

**Example Implementation:**
```python
# Step 1: Generate images
import requests
import os

api_key = os.getenv('XAI_API_KEY')
response = requests.post(
    'https://api.x.ai/v1/images/generations',
    headers={'Authorization': f'Bearer {api_key}'},
    json={
        'prompt': 'Athletic fitness influencer in modern gym, energetic workout',
        'n': 4,
        'model': 'grok-2-image-1212'
    }
)
image_urls = [img['url'] for img in response.json()['data']]

# Step 2: Create video
from execution.shotstack_api import ShotstackAPI
api = ShotstackAPI()
result = api.create_video_from_images(
    image_urls=image_urls,
    text_overlays=["TRANSFORM YOUR BODY", "", "", "Follow @boabfit"],
    duration_per_image=3.5,
    transition="slideLeft",
    music="energetic",
    resolution="hd"
)
final = api.wait_for_render(result["render_id"])
print(f"Video URL: {final['video_url']}")
```

**Output**:
- MP4 video (HD, 9:16 vertical)
- 14-second duration
- Professional transitions and music
- Total cost: ~$0.35

**First Success (2026-01-06):**
- Created @boabfit video ad
- URL: https://shotstack-api-stage-output.s3-ap-southeast-2.amazonaws.com/26vfkcrs1c/6e66969c-c573-433d-a7ba-2eb29ed6e568.mp4

## Outputs

### Email Summaries
- Categorized email digest
- Priority flagging
- Draft responses
- Action items list

### Analytics Reports
- Revenue breakdown by source
- Expense categorization
- Profit margins
- Growth trends (MoM, YoY)
- Visual charts and graphs

### Edited Videos
- Jump-cut processed videos
- Branded intro/outro
- Platform-optimized formats
- Auto-generated thumbnails

### Educational Content
- Branded graphics (Instagram, YouTube, TikTok)
- Consistent styling matching brand guidelines
- Multiple format exports
- AI-generated supplementary images

### Calendar Alerts
- Content deadline reminders
- Revenue milestone notifications
- Collaboration meeting alerts
- Publishing schedule tracking

## Edge Cases

### API Rate Limits

**Gmail API:**
- 1 billion quota units per day (rarely hit)
- Batch requests where possible

**Google Calendar API:**
- 1 million queries per day
- Cache calendar data locally

**Canva API:**
- Rate limits vary by plan
- Implement exponential backoff

**Grok API:**
- Monitor usage to control costs
- Cache generated images

### Video Processing Failures

**Large File Handling:**
- Videos >2GB may timeout
- Process in chunks or reduce resolution
- Use GPU acceleration if available

**Silence Detection Issues:**
- Adjust threshold if cutting too aggressively
- Set minimum clip duration to avoid choppy cuts
- Manual review for critical content

### Email Categorization Errors

**False Positives:**
- User feedback loop to improve categorization
- Manual override option
- Whitelist/blacklist specific senders

## Cost Optimization

### Video Editing
- FFmpeg + MoviePy: **FREE**
- Savings vs CapCut Pro: $120/year

### Graphics
- Pillow for diagrams: **FREE**
- Grok API for AI images: ~$7/month (100 images)
- Canva API: FREE for basic usage
- Savings vs Canva Pro: $155/year

### Total Savings
- ~$268/year vs paid subscriptions
- Pay-per-use model prevents waste

## Success Criteria

1. Can process daily email digest in <30 seconds
2. Generates accurate revenue reports from Google Sheets
3. Automatically edits raw videos with jump cuts (90%+ accuracy)
4. Creates on-brand educational graphics matching style guide
5. Sends timely calendar reminders for content deadlines
6. Handles batch processing of multiple videos
7. Maintains consistent branding across all content

## References

**APIs & Documentation:**
- [Gmail API](https://developers.google.com/gmail/api)
- [Google Calendar API](https://developers.google.com/calendar)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Canva Developers](https://www.canva.dev/docs/connect/)
- [Grok/xAI API](https://docs.x.ai/docs/guides/image-generations)

**Open-Source Tools:**
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [MoviePy](https://zulko.github.io/moviepy/)
- [Jumpcutter (GitHub)](https://github.com/carykh/jumpcutter)
- [Pillow Documentation](https://pillow.readthedocs.io/)

**Technical Guides:**
- [Automatic Video Editing Guide](https://towardsdatascience.com/automatic-video-editing-using-python-324e5efd7eba/)
- [Python Image Processing](https://realpython.com/image-processing-with-the-python-pillow-library/)

## Next Steps

1. Set up Google OAuth credentials for Gmail, Calendar, Sheets
2. Obtain Canva API credentials
3. Obtain Grok/xAI API key
4. Install dependencies: `pip install moviepy pillow google-auth google-api-python-client`
5. Configure brand assets (logo, colors, fonts)
6. Test with example fitness content
7. Deploy to Skills under `fitness-influencer-assistant` project
