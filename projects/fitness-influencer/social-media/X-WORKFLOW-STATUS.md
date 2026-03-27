# X Social Post Scheduler - Workflow Status

**Last Updated**: 2026-02-09
**Status**: Active and Working

## Workflow Details

| Property | Value |
|----------|-------|
| **Workflow ID** | `yBcHFdspRnc4gVUB` |
| **Name** | X-Social-Post-Scheduler |
| **Status** | Active |
| **Location** | EC2 n8n at http://34.193.98.97:5678 |

## Schedule

| Day | Times (EST) |
|-----|-------------|
| Monday-Friday | 9:00 AM, 12:00 PM, 3:00 PM, 6:00 PM |
| Saturday-Sunday | 10:00 AM, 4:00 PM |

## Queue Location

**Google Sheets Document**: `1frkdH8tqlNtnLXGAUiPioYQuU8e_g7Gev-C_Rhxb20o`

| Sheet | Purpose |
|-------|---------|
| `X_Post_Queue` | Content queue (add posts here) |
| `X_Post_Analytics` | Performance tracking |

## Queue Schema

| Column | Type | Description |
|--------|------|-------------|
| Post_ID | string | Unique identifier (e.g., bip_001) |
| Content | string | Tweet content (max 280 chars) |
| Status | string | PENDING or POSTED |
| Category | string | Content category (bip_revenue, bip_tech, etc.) |
| Posted_At | datetime | When it was posted (auto-filled) |
| Tweet_ID | string | Twitter ID (auto-filled) |

## How to Add Posts

### Option 1: Manual (Google Sheets)
1. Open the Google Sheet: https://docs.google.com/spreadsheets/d/1frkdH8tqlNtnLXGAUiPioYQuU8e_g7Gev-C_Rhxb20o
2. Go to `X_Post_Queue` sheet
3. Add new rows with Status = "PENDING"

### Option 2: Batch Import
1. Use CSV files from `projects/shared/social-media-automation/content-queue/`
2. Copy-paste into Google Sheets

## Content Queue Files

| File | Description |
|------|-------------|
| `content-queue/x-posts-week-1.csv` | 10 build-in-public posts for Week 1 |

## Build-in-Public Content Categories

| Category Code | Description |
|---------------|-------------|
| bip_revenue | Revenue and financial updates |
| bip_milestone | Wins and milestone celebrations |
| bip_lesson | Failures and lessons learned |
| bip_tech | Tech stack and automation updates |
| bip_behind_scenes | Day-in-the-life content |
| bip_engagement | Questions and community building |

## Content Templates

Full templates available at:
- `projects/shared/social-media-automation/templates/build-in-public-content.json`

## Monitoring

### Check Workflow Status
```bash
# Via n8n MCP
mcp__n8n__get_workflow_summary --workflow_id yBcHFdspRnc4gVUB
```

### Check Queue Status
1. Open Google Sheet
2. Filter by Status = "PENDING" to see queued posts
3. Filter by Status = "POSTED" to see completed posts

## Workflow Architecture

```
Schedule Trigger (cron)
    ↓
Get Next Post from Queue (Google Sheets read)
    ↓
Filter Pending Posts (Status = PENDING)
    ↓
Prepare Post Data (extract Content, Post_ID)
    ↓
Post to X (Twitter API)
    ↓
├── Mark as Posted (update Status = POSTED)
└── Log to Analytics (append to X_Post_Analytics)
```

## Credentials

| Service | Credential ID | Name |
|---------|---------------|------|
| Google Sheets | mywn8S0xjRx9YM9K | Google Sheets account 4 |
| X/Twitter | GE5AiSqCkxMyqg77 | X account |
