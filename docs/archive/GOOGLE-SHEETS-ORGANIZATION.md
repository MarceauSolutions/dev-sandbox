# Google Sheets Organization Plan

**Created**: 2026-02-07
**Status**: ACTION REQUIRED

## Current State Audit

### Existing Spreadsheets

| Spreadsheet | ID | Purpose | Status |
|-------------|-----|---------|--------|
| **Lead Captures** | `1AgdGdTLi0E8eZBUZ3yHVCCdVSlXOuxFhOZ7BSXmNbZM` | Lead capture from scraping | ✅ Working |
| **Form Submissions** | `1iXAvYMJBqAH-VBWBiy4mXpGXP6wxLWy23U2HaHUtmk4` | Website form submissions | ✅ Working |
| **Agent Orchestrator** | `1egMBLln5cIGgwn1zeG9begxpv5VxvyY1IoIIiI1ix64` | Agent sessions & SMS responses | ✅ Working |

### Workflows Using Google Sheets

| Workflow | Current Sheet ID | Expected Tabs | Status |
|----------|------------------|---------------|--------|
| X-Social-Post-Scheduler | `1AgdGdTLi0E8eZBUZ3yHVCCdVSlXOuxFhOZ7BSXmNbZM` (WRONG) | X_Post_Queue, X_Post_Analytics | ❌ MISCONFIGURED |
| Grok B-Roll Generator | `YOUR_GOOGLE_SHEET_ID_HERE` (PLACEHOLDER) | B_Roll_Prompts, B_Roll_Generated | ❌ NOT CONFIGURED |
| Form-Submission-Pipeline | `1iXAvYMJBqAH-VBWBiy4mXpGXP6wxLWy23U2HaHUtmk4` | Form_Submissions | ✅ Working |
| Universal-Agent-Orchestrator | `1egMBLln5cIGgwn1zeG9begxpv5VxvyY1IoIIiI1ix64` | Agent_Sessions | ✅ Working |
| SMS-Response-Handler | `1egMBLln5cIGgwn1zeG9begxpv5VxvyY1IoIIiI1ix64` | SMS_Responses | ✅ Working |

---

## Required Action: Create Social Media Automation Spreadsheet

### Step 1: Create New Google Sheet

**Name**: `Marceau Solutions - Social Media Automation`

**Location**: Google Drive → Marceau Solutions folder

### Step 2: Create Required Tabs

#### Tab 1: `X_Post_Queue`
| Column | Type | Description |
|--------|------|-------------|
| A: Post_ID | Text | Unique identifier (auto-generated) |
| B: Content | Text | Post content (max 280 chars) |
| C: Media_URL | URL | Optional image/video URL |
| D: Scheduled_Time | DateTime | When to post (ISO 8601) |
| E: Status | Text | PENDING, POSTED, FAILED, SKIPPED |
| F: Category | Text | fitness, motivation, tips, promo |
| G: Created_At | DateTime | When row was created |
| H: Posted_At | DateTime | When actually posted |
| I: Tweet_ID | Text | X/Twitter post ID after posting |
| J: Error_Message | Text | If failed, why |

**Sample Data Row**:
```
Post_ID: X001
Content: "Just finished a killer leg day! 🦵💪 Remember: consistency beats intensity every time. #FitnessMotivation"
Media_URL: https://example.com/image.jpg
Scheduled_Time: 2026-02-07T09:00:00-05:00
Status: PENDING
Category: motivation
Created_At: 2026-02-06T15:00:00-05:00
```

#### Tab 2: `X_Post_Analytics`
| Column | Type | Description |
|--------|------|-------------|
| A: Tweet_ID | Text | X/Twitter post ID |
| B: Post_ID | Text | Reference to X_Post_Queue |
| C: Content | Text | Copy of post content |
| D: Posted_At | DateTime | When posted |
| E: Impressions | Number | View count |
| F: Engagements | Number | Total engagements |
| G: Likes | Number | Like count |
| H: Retweets | Number | Retweet count |
| I: Replies | Number | Reply count |
| J: Profile_Clicks | Number | Profile click count |
| K: Link_Clicks | Number | Link click count |
| L: Updated_At | DateTime | Last metrics update |

#### Tab 3: `B_Roll_Prompts`
| Column | Type | Description |
|--------|------|-------------|
| A: Prompt_ID | Text | Unique identifier |
| B: Prompt | Text | Image generation prompt |
| C: Category | Text | workout, motivation, food, lifestyle |
| D: Status | Text | PENDING, GENERATING, COMPLETED, FAILED |
| E: Image_URL | URL | Generated image URL |
| F: Created_At | DateTime | When added |
| G: Generated_At | DateTime | When image was generated |
| H: Cost | Number | Generation cost in USD |
| I: Provider | Text | grok, dalle, ideogram, replicate |

#### Tab 4: `B_Roll_Generated`
| Column | Type | Description |
|--------|------|-------------|
| A: Image_ID | Text | Unique identifier |
| B: Prompt_ID | Text | Reference to B_Roll_Prompts |
| C: Prompt | Text | The prompt used |
| D: Image_URL | URL | Generated image URL |
| E: Provider | Text | Which AI generated it |
| F: Cost | Number | Cost in USD |
| G: Quality_Score | Number | 1-5 rating |
| H: Used_In | Text | Where image was used |
| I: Created_At | DateTime | Generation timestamp |

---

## Step 3: Update Workflow Configurations

After creating the spreadsheet, get the new ID from the URL:
`https://docs.google.com/spreadsheets/d/{NEW_SPREADSHEET_ID}/edit`

### Workflows to Update

1. **X-Social-Post-Scheduler** (ID: `yBcHFdspRnc4gVUB`)
   - Replace all instances of `1AgdGdTLi0E8eZBUZ3yHVCCdVSlXOuxFhOZ7BSXmNbZM`
   - With new Social Media Automation spreadsheet ID

2. **Grok B-Roll Generator** (ID: from EC2)
   - Replace all instances of `YOUR_GOOGLE_SHEET_ID_HERE`
   - With new Social Media Automation spreadsheet ID

---

## Environment Variable Updates

Add to `.env`:
```bash
# Social Media Automation
SOCIAL_MEDIA_SPREADSHEET_ID=<NEW_SPREADSHEET_ID>
```

---

## Google Drive Organization

Recommended folder structure:
```
Marceau Solutions/
├── Lead Captures (existing)
├── Form Submissions (existing)
├── Agent Orchestrator (existing)
└── Social Media Automation (NEW)
    - X_Post_Queue tab
    - X_Post_Analytics tab
    - B_Roll_Prompts tab
    - B_Roll_Generated tab
```

---

## Verification Checklist

After creating the spreadsheet:

- [ ] Spreadsheet created with correct name
- [ ] All 4 tabs created with correct column headers
- [ ] Spreadsheet ID copied from URL
- [ ] X-Social-Post-Scheduler workflow updated
- [ ] Grok B-Roll Generator workflow updated
- [ ] .env file updated with SOCIAL_MEDIA_SPREADSHEET_ID
- [ ] Test X-Social-Post-Scheduler reads from correct sheet
- [ ] Test B-Roll Generator reads/writes correctly

---

## Quick Commands

Once you have the new spreadsheet ID, run:

```bash
# Update the workflow on EC2 n8n
# Use Claude Code to call the n8n MCP tools with the new ID
```

Or manually in n8n UI:
1. Open X-Social-Post-Scheduler workflow
2. Click each Google Sheets node
3. Change Document ID to new spreadsheet
4. Save and activate
