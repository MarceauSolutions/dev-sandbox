# Fitness Influencer Operations MCP

Comprehensive toolkit for fitness content creators: video editing, AI image generation, analytics, and content planning.

## Registry Information

- **Namespace**: `io.github.williammarceaujr/fitness-influencer`
- **Category**: Content Creation
- **Connectivity**: Hybrid (local + API)

## Tools

### Video Operations

#### `create_jump_cut_video`
Automatically remove silence from videos using FFmpeg.

**Input**:
- `input_video_path` (string, required): Path to input video
- `output_video_path` (string, optional): Output path
- `silence_threshold` (number, default: -40): Silence threshold in dB
- `min_silence_duration` (number, default: 0.3): Min silence to cut
- `generate_thumbnail` (boolean, default: false): Generate thumbnail

**Output**:
```json
{
  "success": true,
  "output_path": "/path/to/edited.mp4",
  "thumbnail_path": "/path/to/thumbnail.jpg"
}
```

**Cost**: FREE (local FFmpeg)

#### `add_video_branding`
Add intro and outro to videos.

**Input**:
- `video_path` (string, required): Main video
- `intro_path` (string, optional): Intro video
- `outro_path` (string, optional): Outro video
- `output_path` (string, required): Output path

**Cost**: FREE

### AI Content Generation

#### `generate_fitness_image`
Generate AI images using Grok/xAI Aurora model.

**Input**:
- `prompt` (string, required): Image description
- `count` (integer, default: 1): Number of images (1-10)
- `output_path` (string, optional): Save path

**Output**:
```json
{
  "success": true,
  "images": ["url1", "url2"],
  "cost": "$0.14"
}
```

**Cost**: $0.07 per image

### Content Planning

#### `generate_workout_plan`
Create customized workout plans.

**Input**:
- `goal` (string, required): muscle_gain, strength, endurance
- `experience` (string, required): beginner, intermediate, advanced
- `days_per_week` (integer, required): 3-6
- `equipment` (string, required): full_gym, home_gym, minimal

**Output**: Complete workout plan with exercises, sets, reps

**Cost**: FREE

### Analytics

#### `get_revenue_report`
Generate revenue analytics from Google Sheets.

**Input**:
- `sheet_id` (string, required): Google Sheets ID
- `month` (string, optional): YYYY-MM format

**Output**:
```json
{
  "success": true,
  "report": {
    "totals": {
      "revenue": 5000,
      "expenses": 1200,
      "profit": 3800,
      "margin": 76.0
    },
    "growth": {
      "revenue": 15.2,
      "expenses": -5.1
    }
  }
}
```

**Requires**: Google Sheets API credentials

#### `analyze_content_engagement`
Analyze content performance (placeholder for social media API integration).

## Features

### Video Editing
- Automatic silence detection and removal
- Jump cut creation for engaging content
- Branded intro/outro insertion
- Thumbnail generation from best frame
- Support for MP4, MOV, AVI formats

### AI Image Generation
- Photorealistic fitness images
- Batch generation (up to 10 images)
- Automatic cost tracking
- Direct download option

### Workout Planning
- Customized training splits
- Exercise selection by equipment
- Sets/reps based on experience
- Export to markdown and JSON

### Revenue Analytics
- Revenue by source tracking
- Expense categorization
- Month-over-month growth
- Profit margin analysis

## Dependencies

```bash
# Video editing
pip install moviepy pillow

# AI image generation
pip install requests python-dotenv

# Analytics
pip install google-auth google-auth-oauthlib google-api-python-client

# MCP server
pip install mcp
```

### System Requirements

```bash
# FFmpeg for video processing
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Ubuntu
```

## Configuration

Create `.env` file:

```env
# Grok/xAI for image generation
XAI_API_KEY=your_xai_api_key

# Google APIs (for analytics)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## Running the Server

```bash
python mcp-server/fitness_influencer_mcp.py
```

## Example Usage

```python
# Via MCP client

# Create jump cut video
result = await client.call_tool("create_jump_cut_video", {
    "input_video_path": "/raw/workout.mp4",
    "silence_threshold": -35,
    "generate_thumbnail": True
})

# Generate fitness image
images = await client.call_tool("generate_fitness_image", {
    "prompt": "Fitness influencer doing deadlifts in modern gym, dramatic lighting",
    "count": 3
})

# Create workout plan
plan = await client.call_tool("generate_workout_plan", {
    "goal": "muscle_gain",
    "experience": "intermediate",
    "days_per_week": 4,
    "equipment": "full_gym"
})

# Get revenue report
report = await client.call_tool("get_revenue_report", {
    "sheet_id": "1abc...",
    "month": "2026-01"
})
```

## Revenue Model

- **Market**: Fitness content creators, influencers
- **Moat**: Multi-capability orchestration (video + AI + analytics)
- **Value**: Time savings (hours per video), professional quality

## Cost Summary

| Tool | Cost |
|------|------|
| Video jump cuts | FREE |
| Video branding | FREE |
| Workout plans | FREE |
| AI images | $0.07/image |
| Revenue analytics | FREE (with Google API) |
