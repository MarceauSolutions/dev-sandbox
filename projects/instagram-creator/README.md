# Instagram Creator MCP

mcp-name: io.github.wmarceau/instagram-creator

Instagram automation tools for Claude via MCP (Model Context Protocol). Post images, Reels, carousels, Stories, and track analytics.

## Features

- **Post Images**: Single image posts with captions and hashtags
- **Carousels**: Multi-image posts (2-10 images)
- **Reels**: Video posts with cover images
- **Stories**: Image or video Stories
- **Analytics**: Post insights and engagement metrics
- **Comments**: Read and reply to comments
- **Account Stats**: Follower count, post count

## Installation

```bash
pip install instagram-creator-mcp
```

## Setup

### Prerequisites

1. **Facebook Business Account**
2. **Instagram Professional Account** (Business or Creator)
3. **Meta Developer App** with Instagram Graph API

### 1. Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create a new app (Business type)
3. Add **Instagram Graph API** product
4. Add **Facebook Login** product

### 2. Connect Instagram Account

1. In your Meta App, go to **Instagram > Basic Display**
2. Add your Instagram account
3. Generate a **User Access Token**

### 3. Get Long-Lived Token

Short-lived tokens expire in 1 hour. Get a long-lived token (60 days):

```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"
```

### 4. Set Environment Variable

```bash
export INSTAGRAM_ACCESS_TOKEN="your_long_lived_token"
```

## Tools

| Tool | Description |
|------|-------------|
| `post_image` | Post single image to feed |
| `post_carousel` | Post multi-image carousel (2-10) |
| `post_reel` | Post video Reel |
| `post_story` | Post to Stories |
| `get_post_insights` | Get engagement metrics |
| `get_account_stats` | Follower/following count |
| `get_recent_posts` | List recent posts |
| `get_comments` | Get post comments |
| `reply_to_comment` | Reply to a comment |

## Usage Examples

### Post an Image

```json
{
  "tool": "post_image",
  "arguments": {
    "image_url": "https://example.com/image.jpg",
    "caption": "Check out my latest workout routine!",
    "hashtags": ["fitness", "workout", "gym", "motivation"]
  }
}
```

### Post a Reel

```json
{
  "tool": "post_reel",
  "arguments": {
    "video_url": "https://example.com/video.mp4",
    "caption": "Quick tip for better form",
    "hashtags": ["fitness", "reels", "tips"],
    "share_to_feed": true
  }
}
```

### Post a Carousel

```json
{
  "tool": "post_carousel",
  "arguments": {
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg",
      "https://example.com/image3.jpg"
    ],
    "caption": "My transformation journey - swipe to see!",
    "hashtags": ["transformation", "progress", "fitness"]
  }
}
```

## Important Notes

### Media URL Requirements

Instagram Graph API requires media to be hosted at **publicly accessible URLs**. Options:
- Use cloud storage (S3, Google Cloud Storage)
- Use a CDN
- Use a temporary file hosting service

### Rate Limits

- **Content Publishing**: 25 posts per 24-hour period
- **API Calls**: 200 calls per hour per user

### Permissions Required

Your access token needs these permissions:
- `instagram_basic`
- `instagram_content_publish`
- `pages_show_list`
- `pages_read_engagement`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `INSTAGRAM_ACCESS_TOKEN` | Yes | Graph API access token |
| `INSTAGRAM_ACCOUNT_ID` | No | Business Account ID (auto-detected) |

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "instagram-creator": {
      "command": "instagram-creator-mcp",
      "env": {
        "INSTAGRAM_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## License

MIT
