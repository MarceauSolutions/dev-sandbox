# X/Twitter Image Generation Pipeline

**Last Updated:** 2026-02-09
**Status:** Production Ready (awaiting API credits)

## Overview

Automated image generation and posting for X/Twitter build-in-public content. The system pre-generates images for qualifying posts and attaches them during scheduled posting.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        X/TWITTER IMAGE GENERATION PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    X-Batch-Image-Generator (Daily 6 AM)                  │    │
│  │                                                                          │    │
│  │   Schedule  →  Get Posts  →  Filter  →  Qualify?  →  Generate  →  Update │    │
│  │   (6 AM)       (Sheets)     (PENDING)   (Category)   (Grok API)   (URL)  │    │
│  │                                           │                              │    │
│  │                              ┌────────────┼────────────┐                 │    │
│  │                              │            │            │                 │    │
│  │                          milestone      tech      behind_scenes          │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                      │
│                                           ▼                                      │
│                            ┌──────────────────────────────┐                      │
│                            │    Google Sheets Queue       │                      │
│                            │    Media_URL column          │                      │
│                            └──────────────────────────────┘                      │
│                                           │                                      │
│                                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │              X-Social-Post-Scheduler-v2 (9am/12pm/3pm/6pm)               │    │
│  │                                                                          │    │
│  │   Schedule  →  Get Next  →  Filter  →  Has Media?                        │    │
│  │   (4x/day)     (Sheets)    (PENDING)       │                             │    │
│  │                                     ┌──────┴──────┐                      │    │
│  │                                     ▼             ▼                      │    │
│  │                              ┌──────────┐  ┌───────────┐                 │    │
│  │                              │ Download │  │ Text Only │                 │    │
│  │                              │ Image    │  │ Post      │                 │    │
│  │                              └────┬─────┘  └─────┬─────┘                 │    │
│  │                                   ▼              │                       │    │
│  │                              ┌──────────┐        │                       │    │
│  │                              │ Upload   │        │                       │    │
│  │                              │ to X     │        │                       │    │
│  │                              └────┬─────┘        │                       │    │
│  │                                   ▼              │                       │    │
│  │                              ┌──────────┐        │                       │    │
│  │                              │ Post w/  │        │                       │    │
│  │                              │ Media    │        │                       │    │
│  │                              └────┬─────┘        │                       │    │
│  │                                   └──────┬───────┘                       │    │
│  │                                          ▼                               │    │
│  │                               ┌─────────────────────┐                    │    │
│  │                               │ Mark Posted + Log   │                    │    │
│  │                               └─────────────────────┘                    │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. X-Batch-Image-Generator

**ID:** `EgLcSeovV58t5OJS`
**Schedule:** Daily at 6 AM
**Purpose:** Pre-generate images for qualifying posts

**Flow:**
1. **Trigger** - Daily 6 AM cron
2. **Get All Posts** - Fetch from Google Sheets X_Post_Queue
3. **Filter: Needs Image** - PENDING status AND empty Media_URL
4. **Qualifies for Image?** - Check category:
   - `bip_milestone` - Achievement/win posts
   - `bip_tech` - Tech stack/automation posts
   - `bip_behind_scenes` - Day-in-life posts
5. **Build Prompt** - Category-specific prompt generation:
   ```javascript
   const prompts = {
     'bip_milestone': `Create a celebratory social media graphic. Theme: "${firstLine}".
       Style: Modern bold typography, dark purple-blue gradient background,
       subtle confetti elements. Professional, inspiring. Square 1080x1080.`,
     'bip_tech': `Create a tech infographic. Theme: "${firstLine}".
       Style: Dark theme with cyan accents, abstract tech elements.
       Professional, developer-friendly. Square 1080x1080.`,
     'bip_behind_scenes': `Create a lifestyle graphic for entrepreneur. Theme: "${firstLine}".
       Style: Warm sunrise gradient, fitness/productivity icons.
       Professional but approachable. Square 1080x1080.`
   };
   ```
6. **Generate Image (Grok)** - Call xAI API ($0.07/image)
7. **Update Media_URL** - Write image URL back to sheet
8. **Rate Limit Wait** - 5 second delay between images

### 2. X-Social-Post-Scheduler-v2

**ID:** `CT5em35LljouaCrU`
**Schedule:**
- Weekdays: 9 AM, 12 PM, 3 PM, 6 PM
- Weekends: 10 AM, 4 PM

**Purpose:** Post content to X with or without images

**Flow:**
1. **Trigger** - Schedule trigger
2. **Get Next Post** - Fetch from Google Sheets
3. **Filter Pending** - Status = PENDING
4. **Process One Post** - Take first matching post
5. **Prepare Post Data** - Extract text, category, media_url
6. **Has Media URL?** - Branch based on presence
   - **YES**: Download Image → Upload to Twitter → Post with Media
   - **NO**: Post Text Only
7. **Mark as Posted** - Update Status, Posted_At, Tweet_ID
8. **Log to Analytics** - Optional analytics sheet

## Google Sheets Structure

**Sheet ID:** `1frkdH8tqlNtnLXGAUiPioYQuU8e_g7Gev-C_Rhxb20o`
**Sheet Name:** `X_Post_Queue`

| Column | Description |
|--------|-------------|
| Post_ID | Unique identifier |
| Content | Tweet text |
| Status | PENDING, POSTED, FAILED |
| Category | bip_milestone, bip_tech, bip_behind_scenes, etc |
| Media_URL | Pre-generated image URL (filled by batch generator) |
| Scheduled_Time | (Optional) Specific post time |
| Created_At | Creation timestamp |
| Posted_At | When posted |
| Tweet_ID | X/Twitter post ID |
| Error_Message | If failed |

## Category Definitions

| Category | Description | Gets Image |
|----------|-------------|------------|
| `bip_milestone` | Achievements, wins, progress | ✅ Yes |
| `bip_tech` | Tech stack, automation, tools | ✅ Yes |
| `bip_behind_scenes` | Day-in-life, routines | ✅ Yes |
| `bip_lesson` | Business lessons learned | ❌ No |
| `bip_engagement` | Questions, polls | ❌ No |
| `bip_value` | Tips, advice | ❌ No |

## Cost Analysis

| Provider | Cost/Image | Quality | Speed |
|----------|------------|---------|-------|
| Grok (xAI) | $0.07 | High | ~10s |
| DALL-E 3 | $0.04-0.08 | High | ~10s |
| Replicate SD | $0.003 | Medium | ~15s |
| Ideogram | $0.05 | High (text) | ~10s |

**Estimated Monthly Cost** (30 posts with images):
- 30 × $0.07 = **$2.10/month** (Grok)

## Credentials Required

| Service | Credential ID | Name |
|---------|--------------|------|
| Google Sheets | mywn8S0xjRx9YM9K | Google Sheets account 4 |
| X/Twitter | GE5AiSqCkxMyqg77 | X account |
| xAI (Grok) | P1H6Vz9nbdj2q1KU | XAi_API_key |

## Monitoring

**n8n Dashboard:** http://34.193.98.97:5678

**Check workflow status:**
- X-Batch-Image-Generator: Should run daily, check for failures
- X-Social-Post-Scheduler-v2: Check 4x/day execution

**Common Issues:**
1. **Rate Limit (429)** - xAI spending limit reached → Wait or add credits
2. **Download Failed** - Image URL expired → Regenerate
3. **Upload Failed** - Twitter API issue → Check credentials

## Files

| File | Location |
|------|----------|
| Batch Generator Workflow | `projects/shared/n8n-workflows/x-batch-image-generator.json` |
| Scheduler v2 Workflow | `projects/shared/n8n-workflows/x-scheduler-v2-simple.json` |
| Python Image Generator | `execution/grok_image_gen.py` |
| Multi-Provider Router | `execution/multi_provider_image_router.py` |

## Future Enhancements

1. **Multi-Provider Fallback** - If Grok fails, try DALL-E → Replicate
2. **Image Caching** - Store generated images in S3 for reuse
3. **A/B Testing** - Compare engagement with/without images
4. **Analytics Dashboard** - Track image generation costs and performance
