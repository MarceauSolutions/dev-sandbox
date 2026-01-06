---
name: fitness-influencer-operations
description: Automate fitness influencer workflows - video editing (jump cuts), email management, revenue analytics, branded content creation
allowed-tools: ["Bash(python:*)"]
model: opus
trigger-phrases:
  - "edit this video"
  - "remove silence from video"
  - "create fitness graphic"
  - "summarize my emails"
  - "generate revenue report"
  - "create AI fitness image"
  - "make video ad"
---

# Fitness Influencer Operations

## ⚡ Quick Reference (AI: Read This First)

**CAPABILITIES:** Video editing (jump cuts) • Educational graphics • Email digest • Revenue analytics • AI images (Grok) • Video ads (Shotstack)

**WHEN TO USE:** User requests content creation, video editing, email management, or analytics for fitness influencer workflows

**EXECUTION:** Uses deterministic Python scripts in `execution/` directory. Reference directive `directives/fitness_influencer_operations.md` for complete details.

---

## 🎯 Decision Tree

```
User Request → Capability Mapping:

├─ "edit video" / "jump cuts" / "remove silence"
│  └─ USE: execution/video_jumpcut.py
│     INPUT: Video file, silence threshold
│     OUTPUT: Edited video, stats
│
├─ "create graphic" / "fitness tip card" / "educational content"
│  └─ USE: execution/educational_graphics.py
│     INPUT: Title, key points, platform
│     OUTPUT: Branded graphic (1080x1080, 1080x1920, or 1280x720)
│
├─ "email" / "inbox" / "summarize emails"
│  └─ USE: execution/gmail_monitor.py
│     INPUT: Time period (hours back)
│     OUTPUT: Categorized email digest
│
├─ "revenue" / "analytics" / "expenses" / "profit"
│  └─ USE: execution/revenue_analytics.py
│     INPUT: Google Sheet ID, month
│     OUTPUT: Revenue report with trends
│
├─ "generate image" / "AI image" / "fitness photo"
│  └─ USE: execution/grok_image_gen.py
│     INPUT: Prompt, count
│     OUTPUT: Image URLs ($0.07 each)
│
└─ "video ad" / "create ad" / "social video"
   └─ USE: execution/shotstack_api.py + grok_image_gen.py
      PROCESS: Generate 4 images → Create video with Shotstack
      OUTPUT: Video URL (~$0.35 total)
```

---

## 📋 Script Reference

| Script | Purpose | Input | Output | Cost |
|--------|---------|-------|--------|------|
| `video_jumpcut.py` | Remove silence, apply jump cuts | Video file | Edited video | FREE |
| `educational_graphics.py` | Create branded graphics | Title, points | Image (JPG/PNG) | FREE |
| `gmail_monitor.py` | Email categorization | Time period | Email digest | FREE |
| `revenue_analytics.py` | Track income/expenses | Sheet ID | Revenue report | FREE |
| `grok_image_gen.py` | AI image generation | Prompt | Image URLs | $0.07/image |
| `shotstack_api.py` | Video from images | Image URLs | Video URL | $0.06/video |
| `calendar_reminders.py` | Recurring reminders | Title, days, time | Calendar events | FREE |
| `canva_integration.py` | Advanced designs | Template ID | Design URL | FREE |

---

## 🔧 Environment Requirements

Required in `.env`:
```bash
# AI Image Generation
XAI_API_KEY=xxx                    # Grok/xAI for images

# Video Generation
SHOTSTACK_API_KEY=xxx              # Shotstack for video ads
SHOTSTACK_ENV=stage                # or 'v1' for production

# Google APIs (optional)
GOOGLE_CLIENT_ID=xxx               # For Gmail, Calendar, Sheets
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REFRESH_TOKEN=xxx

# Canva API (optional)
CANVA_API_KEY=xxx                  # For advanced designs
```

---

## 🔍 Unknown Use Case Handler

**If user request doesn't match the Decision Tree above:**

### 1. Analyze Request Components
- **Extract:** action verb, target object, desired outcome
- **Example:** "Create workout plan PDF" → `action=create`, `object=PDF`, `outcome=workout plan`

### 2. Check Capability Proximity
Ask yourself:
- Can existing scripts be **combined** to achieve this?
- Is this a **variation** of a known capability?
- Does this require **new development**?

### 3. Response Options

**Option A: Combinable (Best Case)**
```
"I can accomplish this by combining existing tools:
1. Use educational_graphics.py to create workout content
2. Use markdown_to_pdf.py to format as PDF
Would you like me to proceed with this approach?"
```

**Option B: Close Match**
```
"I don't have an exact tool for this, but I can do [similar capability].
For example, I can create workout graphics but not full PDF plans yet.
Would that work for your needs?"
```

**Option C: New Capability Needed**
```
"This requires new development. I'll log it as a capability gap.
Based on frequency data, this has been requested [X] times.
I recommend creating a dedicated tool for this workflow."
```

### 4. Learning Protocol

For **every** unhandled request:
1. **Log** to `USE_CASES.json` → `unhandled_requests[]`
2. **Analyze** if it fits existing patterns or needs new capability
3. **Update** frequency counters for capability gaps
4. **Suggest** directive updates for recurring patterns
5. **Document** what was learned in `learning_log[]`

### 5. Auto-Documentation Update

When a new pattern emerges (frequency > 3):
1. Add to `known_use_cases[]` in USE_CASES.json
2. Update Decision Tree with new routing
3. Add Usage Example showing the workflow
4. Document in `learning_log[]` what made this work

**This creates a self-improving system** - the more it's used, the smarter it gets!

---

## 💡 Usage Examples

**Example 1: Edit Video with Jump Cuts**
```
User: "Edit this raw video and remove the silence"

AI Decision:
  ✓ Matches: video editing capability
  ✓ Execute: video_jumpcut.py
  ✓ Default threshold: -40dB

Command:
  python execution/video_jumpcut.py \
    --input uploaded_video.mp4 \
    --output edited_video.mp4 \
    --silence-thresh -40

Output:
  - Edited video with jump cuts
  - Stats: original 15:30 → 8:45 (43% reduction, 47 cuts)
```

**Example 2: Create Fitness Tip Graphic**
```
User: "Create an Instagram post about staying lean without tracking macros"

AI Decision:
  ✓ Matches: educational graphics capability
  ✓ Extract: title + key points from request
  ✓ Execute: educational_graphics.py

Command:
  python execution/educational_graphics.py \
    --title "Staying Lean Without Tracking Macros" \
    --points "Focus on whole foods,Eat protein with every meal,Stay hydrated" \
    --platform instagram_post

Output:
  - 1080x1080 branded graphic with Marceau Solutions branding
```

**Example 3: Generate Video Ad**
```
User: "Create a 15-second video ad for @boabfit"

AI Decision:
  ✓ Matches: video ad creation capability
  ✓ Pipeline: Grok images → Shotstack video
  ✓ Execute: Two-step process

Commands:
  # Step 1: Generate 4 AI images
  python execution/grok_image_gen.py \
    --prompt "Athletic fitness influencer in modern gym" \
    --count 4

  # Step 2: Create video from images
  python execution/shotstack_api.py create-fitness-ad \
    --images "url1,url2,url3,url4" \
    --headline "Transform Your Body" \
    --cta "Follow @boabfit"

Output:
  - 14-second vertical video (9:16)
  - Cost: $0.34 ($0.28 images + $0.06 video)
  - Ready for Instagram/TikTok
```

---

## 📚 Complete Documentation

For comprehensive details, see:
- **Directive:** `directives/fitness_influencer_operations.md` (600+ lines)
- **Tech Evaluation:** `.claude/FITNESS_INFLUENCER_TECH_EVALUATION.md`
- **Deployment Plan:** `.claude/FITNESS_INFLUENCER_DEPLOYMENT_PLAN.md`
- **Knowledge Base:** `.claude/KNOWLEDGE_BASE.md`

---

## 🎉 Recent Successes

**2026-01-06:** First successful video ad created
- 4 Grok-generated images → Shotstack video
- @boabfit promotional ad (14 seconds)
- Total cost: $0.34
- Video URL: https://shotstack-api-stage-output.s3-ap-southeast-2.amazonaws.com/...

**2026-01-05:** Backend deployed to Railway
- Video processing with static file serving
- All execution scripts tested and working
- API endpoints functional

---

## ⚙️ Technical Notes

**Deployment:** Deployed from DOE development environment on 2026-01-05

**Status:** Production-ready with following capabilities:
- ✅ Video editing (FFmpeg + MoviePy)
- ✅ Graphics generation (Pillow)
- ✅ AI images (Grok/xAI API)
- ✅ Video ads (Shotstack API)
- ✅ Email monitoring (Gmail API)
- ✅ Revenue analytics (Google Sheets API)
- ⏳ Calendar reminders (Google Calendar API - setup pending)
- ⏳ Canva integration (API available - implementation pending)

**Intermediate Files:** All temporary files stored in `.tmp/` (not committed)

**Error Handling:** Scripts include comprehensive error handling and logging

**Testing:** All core features tested and verified working