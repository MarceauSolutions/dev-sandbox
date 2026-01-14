# Fitness Influencer AI - Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-01-14

### Added - New MCP Tools for Content Management
- **Comment Auto-Categorizer** (`categorize_comments`)
  - Automatically categorize comments/DMs into: FAQ, SPAM, COLLAB_REQUEST, FAN_MESSAGE, BRAND_INQUIRY, SUPPORT, NEGATIVE
  - Includes suggested actions and priority levels
  - Auto-reply templates for common categories
  - Helps manage high-volume engagement at scale

- **Cross-Platform Content Optimizer** (`optimize_for_platforms`)
  - Optimize content for 9 platforms: TikTok, Instagram (Feed/Reels/Stories), YouTube (Standard/Shorts), Twitter/X, Threads, LinkedIn
  - Platform-specific recommendations: aspect ratios, caption lengths, hashtag counts
  - Optimal posting time suggestions
  - Platform feature recommendations

- **Content Calendar Generator** (`generate_content_calendar`)
  - Generate balanced 30-day content calendars
  - Workload balancing to prevent burnout
  - Content type variety (workout, nutrition, motivation, lifestyle, education)
  - Holiday-aware scheduling
  - Rest day support
  - Effort distribution analysis and recommendations

### New Modules
- `comment_categorizer.py` - Comment categorization engine
- `cross_platform_optimizer.py` - Platform optimization rules
- `content_calendar.py` - Calendar generation with burnout prevention

### Technical
- MCP now exposes 9 tools (up from 6)
- All new tools are FREE (no API costs)

---

## [1.1.0] - 2026-01-13

### Added
- **MCP Server Wrapper** (`mcp-server/fitness_influencer_mcp.py`)
- Six MCP tools:
  - `create_jump_cut_video` - Automatic silence removal
  - `add_video_branding` - Intro/outro insertion
  - `generate_fitness_image` - AI image generation via Grok
  - `generate_workout_plan` - Custom workout plans
  - `get_revenue_report` - Google Sheets analytics
  - `analyze_content_engagement` - Engagement placeholder
- Registry manifest for MCP Registry submission
- SKILL.md documentation

---

## [1.0.0] - 2026-01-08

### Added
- **Dual-AI Architecture**: Claude handles intent understanding and tool routing, Grok/XAI handles image generation and cost optimization
- **Web Chat Interface**: Production-ready chat UI at `/` with real-time API integration
- **Tool Dashboard**: Alternative dashboard view at `/dashboard` with modal-based tool interfaces
- **Cost Confirmation System**: Operations >$0.10 require user confirmation before execution
- **Alternative Suggestions**: Shows cheaper/premium options for paid operations
- **Session Cost Tracking**: Tracks cumulative costs per session with `/api/costs` endpoint

### Core Modules
- `dual_ai_router.py` - Dual-AI decision routing with cost tiers
- `chat_api.py` - FastAPI backend with Claude tool use integration
- `video_jumpcut.py` - FFmpeg-based silence removal
- `educational_graphics.py` - Pillow-based graphic generation
- `grok_image_gen.py` - XAI/Grok image generation
- `video_ads.py` - Shotstack video ad creation
- `gmail_monitor.py` - Email categorization
- `revenue_analytics.py` - Google Sheets analytics
- `workout_plan_generator.py` - Personalized workout plans
- `nutrition_guide_generator.py` - Macro-calculated nutrition guides

### Cost Tiers
- **FREE**: Video editing, graphics, email summary, analytics, workout/nutrition plans
- **LOW** (<$0.10): 1 AI image ($0.07)
- **MEDIUM** ($0.10-$0.30): 2-4 AI images
- **HIGH** (>$0.30): Video ads ($0.34+)

### Deployment
- Railway project: `fitness-influencer-ai`
- Production URL: https://api-production-1edc.up.railway.app
- Health endpoint: `/health`
- Costs endpoint: `/api/costs`

---

## [0.x.x] - Previous Development

Initial development of individual tools:
- Video jump cut automation
- Educational graphics generator
- Grok image generation integration
- Email monitoring
- Revenue analytics
- Calendar reminders
- SMS notifications via Twilio
