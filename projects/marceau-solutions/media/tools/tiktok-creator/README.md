# TikTok Creator MCP

mcp-name: io.github.wmarceau/tiktok-creator

TikTok automation tools for Claude via MCP (Model Context Protocol). Post videos, track analytics, and manage comments.

## Features

- **Post Videos**: Upload from local file or public URL
- **Privacy Control**: Set visibility (self, friends, followers, public)
- **Analytics**: Video views, likes, comments, shares
- **Account Stats**: Follower count, total likes
- **Comments**: Read and reply to comments
- **Interaction Controls**: Enable/disable duets, stitch, comments

## Installation

```bash
pip install tiktok-creator-mcp
```

## Setup

### Prerequisites

1. **TikTok Developer Account**: https://developers.tiktok.com
2. **App with Content Posting API** access

### 1. Create TikTok App

1. Go to [TikTok Developer Portal](https://developers.tiktok.com)
2. Create a new app
3. Request **Content Posting API** access
4. Add redirect URI for OAuth

### 2. OAuth Flow

TikTok uses OAuth 2.0. You'll need to:

1. Direct user to authorization URL
2. Receive authorization code
3. Exchange for access token

```python
# Authorization URL
auth_url = f"https://www.tiktok.com/v2/auth/authorize/?client_key={CLIENT_KEY}&response_type=code&scope=user.info.basic,video.upload,video.list&redirect_uri={REDIRECT_URI}"

# Exchange code for token
token_response = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
)
```

### 3. Set Environment Variables

```bash
export TIKTOK_CLIENT_KEY="your_client_key"
export TIKTOK_CLIENT_SECRET="your_client_secret"
export TIKTOK_ACCESS_TOKEN="your_access_token"
export TIKTOK_REFRESH_TOKEN="your_refresh_token"
```

## Tools

| Tool | Description |
|------|-------------|
| `post_video` | Post video from local file |
| `post_video_from_url` | Post video from public URL |
| `get_video_stats` | Get video performance metrics |
| `get_account_stats` | Follower count, likes, videos |
| `get_video_list` | List your TikTok videos |
| `get_comments` | Get video comments |
| `reply_to_comment` | Reply to a comment |

## Usage Examples

### Post a Video

```json
{
  "tool": "post_video",
  "arguments": {
    "video_path": "/path/to/video.mp4",
    "title": "Quick fitness tip! #fitness #workout",
    "privacy": "PUBLIC_TO_EVERYONE"
  }
}
```

### Post from URL

```json
{
  "tool": "post_video_from_url",
  "arguments": {
    "video_url": "https://example.com/video.mp4",
    "title": "Check out this workout! #gym",
    "privacy": "PUBLIC_TO_EVERYONE",
    "disable_duet": false,
    "disable_stitch": false
  }
}
```

### Get Video Stats

```json
{
  "tool": "get_video_stats",
  "arguments": {
    "video_id": "7123456789012345678"
  }
}
```

## Privacy Levels

| Level | Description |
|-------|-------------|
| `SELF_ONLY` | Only you can see |
| `MUTUAL_FOLLOW_FRIENDS` | Mutual followers only |
| `FOLLOWER_OF_CREATOR` | Your followers only |
| `PUBLIC_TO_EVERYONE` | Everyone can see |

## Video Requirements

- **Format**: MP4, WebM
- **Duration**: 3 seconds - 10 minutes
- **Size**: Max 4GB
- **Aspect Ratio**: 9:16 (vertical) recommended

## Rate Limits

- **Video Posts**: Check TikTok Developer docs for current limits
- **API Calls**: Varies by endpoint

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TIKTOK_CLIENT_KEY` | Yes | App client key |
| `TIKTOK_CLIENT_SECRET` | Yes | App client secret |
| `TIKTOK_ACCESS_TOKEN` | Yes | User access token |
| `TIKTOK_REFRESH_TOKEN` | No | For token renewal |

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "tiktok-creator": {
      "command": "tiktok-creator-mcp",
      "env": {
        "TIKTOK_CLIENT_KEY": "your_key",
        "TIKTOK_CLIENT_SECRET": "your_secret",
        "TIKTOK_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

## License

MIT
