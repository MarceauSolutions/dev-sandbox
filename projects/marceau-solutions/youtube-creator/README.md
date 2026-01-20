# YouTube Creator MCP

mcp-name: io.github.wmarceau/youtube-creator

YouTube automation tools for Claude via MCP (Model Context Protocol). Upload videos, manage Shorts, track analytics, and engage with comments.

## Features

- **Upload Videos**: Upload with title, description, tags, thumbnails
- **YouTube Shorts**: Upload vertical videos with automatic #Shorts tagging
- **Schedule Videos**: Schedule uploads for future publication
- **Analytics**: Get views, likes, watch time, subscriber gains
- **Playlists**: Create playlists and add videos
- **Comments**: Read and reply to comments
- **Channel Stats**: Track subscriber count and total views

## Installation

```bash
pip install youtube-creator-mcp
```

## Setup

### 1. Enable YouTube Data API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable **YouTube Data API v3**
4. Enable **YouTube Analytics API**

### 2. Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Desktop app**
4. Download the JSON file
5. Save as `~/.google/youtube_credentials.json`

### 3. First Run (Authentication)

On first use, you'll be prompted to authenticate via browser. The token is saved for future use.

## Tools

| Tool | Description |
|------|-------------|
| `upload_video` | Upload video with metadata and thumbnail |
| `upload_short` | Upload YouTube Short (vertical, <60s) |
| `update_video_metadata` | Update title/description/tags |
| `get_video_analytics` | Get performance metrics |
| `get_channel_stats` | Subscriber count, total views |
| `schedule_video` | Upload and schedule for later |
| `add_to_playlist` | Add video to playlist |
| `list_playlists` | List channel playlists |
| `create_playlist` | Create new playlist |
| `get_comments` | Get video comments |
| `reply_to_comment` | Reply to a comment |

## Usage Examples

### Upload a Video

```json
{
  "tool": "upload_video",
  "arguments": {
    "video_path": "/path/to/video.mp4",
    "title": "5 Fitness Tips You Need to Know",
    "description": "In this video, I share my top 5 fitness tips...",
    "tags": ["fitness", "workout", "health", "tips"],
    "privacy": "public",
    "category": "howto_style"
  }
}
```

### Upload a Short

```json
{
  "tool": "upload_short",
  "arguments": {
    "video_path": "/path/to/short.mp4",
    "title": "Quick Workout Tip",
    "description": "Save this for your next gym session!",
    "tags": ["fitness", "shorts", "workout"],
    "privacy": "public"
  }
}
```

### Get Analytics

```json
{
  "tool": "get_video_analytics",
  "arguments": {
    "video_id": "dQw4w9WgXcQ"
  }
}
```

## Video Categories

| Category Key | Description |
|--------------|-------------|
| `film_animation` | Film & Animation |
| `music` | Music |
| `pets_animals` | Pets & Animals |
| `sports` | Sports |
| `gaming` | Gaming |
| `people_blogs` | People & Blogs (default) |
| `entertainment` | Entertainment |
| `howto_style` | Howto & Style |
| `education` | Education |
| `science_tech` | Science & Technology |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `YOUTUBE_CREDENTIALS_PATH` | Yes | Path to OAuth client secrets JSON |
| `YOUTUBE_TOKEN_PATH` | No | Token storage path (default: ~/.google/youtube_token.pickle) |

## Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "youtube-creator": {
      "command": "youtube-creator-mcp",
      "env": {
        "YOUTUBE_CREDENTIALS_PATH": "/path/to/credentials.json"
      }
    }
  }
}
```

## License

MIT
