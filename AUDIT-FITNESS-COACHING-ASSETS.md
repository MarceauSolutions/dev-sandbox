# Comprehensive Audit: Assets for Fitness Coaching Business

**Date:** 2026-01-31
**Purpose:** Evaluate all existing projects, tools, and workflows for fitness coaching use

---

## Executive Summary

### What You Have (That's Useful)

| Asset | Location | Usefulness | Status |
|-------|----------|------------|--------|
| **Fitness Influencer MCP** | `fitness-influencer-mcp/` | ⭐⭐⭐⭐⭐ | Ready |
| **Trainerize MCP** | `trainerize-mcp/` | ⭐⭐⭐⭐⭐ | Ready |
| **Video Jump-Cut Editor** | `execution/video_jumpcut.py` | ⭐⭐⭐⭐ | Ready |
| **Grok Image Generation** | `execution/grok_image_gen.py` | ⭐⭐⭐⭐⭐ | Ready |
| **Educational Graphics** | `execution/educational_graphics.py` | ⭐⭐⭐⭐ | Ready |
| **Workout Plan Generator** | `execution/workout_plan_generator.py` | ⭐⭐⭐⭐⭐ | Ready |
| **Nutrition Guide Generator** | `execution/nutrition_guide_generator.py` | ⭐⭐⭐⭐ | Ready |
| **Website Builder** | `website-builder/` | ⭐⭐⭐ | Needs customization |
| **Gmail Monitor** | `execution/gmail_monitor.py` | ⭐⭐⭐ | Ready |
| **Calendar Reminders** | `execution/calendar_reminders.py` | ⭐⭐⭐ | Ready |

### What You DON'T Have (That You Need)

| Need | Priority | Effort |
|------|----------|--------|
| Landing page for coaching offer | HIGH | 2-4 hours |
| Calendly or booking system | HIGH | 30 min |
| Client onboarding automation | MEDIUM | 4-6 hours |
| Payment processing | MEDIUM | 1-2 hours |

### What's NOT Useful for Coaching

| Asset | Reason |
|-------|--------|
| Amazon Seller MCP | Different business |
| Apollo MCP | B2B lead gen, not coaching clients |
| SW Florida HVAC content | Different business |
| SquareFoot Shipping content | Different business |
| MCP Aggregator | B2B product, not coaching |

---

## Detailed Asset Breakdown

### 1. Fitness Influencer MCP ⭐⭐⭐⭐⭐

**Location:** `projects/marceau-solutions/fitness-influencer-mcp/`

**What It Does:**
- Video jump-cut editing (removes silence)
- AI fitness image generation ($0.07/image)
- Workout plan generation
- Nutrition guide generation
- Email summarization
- Revenue analytics

**Usefulness for Coaching:**
- **Video editing** → Create content for social media
- **AI images** → Graphics for posts
- **Workout plans** → Auto-generate client programs
- **Nutrition guides** → Deliver nutrition content to clients

**Status:** Production ready. No changes needed.

**How to Use:**
```bash
# Generate workout plan
python src/workout_plan_generator.py --goal muscle_gain --experience intermediate --days 4 --equipment full_gym

# Generate nutrition guide
python src/nutrition_guide_generator.py --goal "fat loss" --calories 2000

# Create jump-cut video
python src/video_jumpcut.py --input raw.mp4 --output edited.mp4

# Generate AI image
python src/grok_image_gen.py --prompt "Fitness athlete doing squats" --count 1
```

---

### 2. Trainerize MCP ⭐⭐⭐⭐⭐

**Location:** `projects/marceau-solutions/trainerize-mcp/`

**What It Does:**
- 27 tools for managing clients
- Create/assign training programs
- Nutrition coaching (meal plans, compliance)
- Messaging clients
- Scheduling appointments
- Analytics and reporting
- Habit tracking

**Usefulness for Coaching:**
- **CRITICAL** — This is your client delivery platform
- Manage all clients in one place
- Assign workouts automatically
- Track compliance and progress
- Message clients in-app

**Status:** Ready to use if you have Trainerize account.

**Requirement:** Need ABC Trainerize account with API access ($19-99/month)

**Decision Point:** 
- If using Trainerize: This MCP is extremely valuable
- If using something else (TrueCoach, etc.): Would need different MCP

---

### 3. Video Jump-Cut Editor ⭐⭐⭐⭐

**Location:** `execution/video_jumpcut.py`

**What It Does:**
- Automatically removes silence from videos
- Makes talking-head content more engaging
- Saves hours of manual editing

**Usefulness for Coaching:**
- Create polished content for X/Instagram
- Edit client testimonial videos
- Educational content for marketing

**Cost:** FREE (uses FFmpeg locally)

---

### 4. Grok Image Generation ⭐⭐⭐⭐⭐

**Location:** `execution/grok_image_gen.py`

**What It Does:**
- Generate AI images via xAI API
- Photorealistic fitness images
- $0.07 per image

**Usefulness for Coaching:**
- Social media graphics
- Content for posts
- Visual variety without photoshoots

**Status:** Ready. API key configured.

---

### 5. Educational Graphics Generator ⭐⭐⭐⭐

**Location:** `execution/educational_graphics.py`

**What It Does:**
- Creates branded fitness tip cards
- Multiple platform sizes (Instagram post, story, YouTube thumbnail)
- Uses Pillow (Python) — FREE

**Usefulness for Coaching:**
- Quick tip graphics for social media
- Educational content that establishes expertise

**Status:** Ready to use.

---

### 6. Workout Plan Generator ⭐⭐⭐⭐⭐

**Location:** `execution/workout_plan_generator.py`

**What It Does:**
- Generate customized workout programs
- Variables: goal, experience level, days/week, equipment
- Outputs structured workout with exercises, sets, reps

**Usefulness for Coaching:**
- Base templates for client programs
- Quick program generation
- Customizable starting point

**Status:** Ready.

---

### 7. Nutrition Guide Generator ⭐⭐⭐⭐

**Location:** `execution/nutrition_guide_generator.py`

**What It Does:**
- Creates nutrition guides based on goals
- Macro breakdowns
- Meal suggestions

**Usefulness for Coaching:**
- Nutrition guidance for clients
- Educational materials
- PDF guides as value-add

**Status:** Ready.

---

### 8. Website Builder ⭐⭐⭐

**Location:** `projects/marceau-solutions/website-builder/`

**What It Does:**
- AI-powered website generation
- Researches company/owner
- Generates copy and design
- Outputs static HTML site

**Usefulness for Coaching:**
- Could generate a coaching landing page
- Would need customization for coaching offer

**Status:** Works, but not optimized for coaching.

**Action Needed:** Generate a coaching-focused landing page or use simpler alternative (Carrd, Linktree, etc.)

---

### 9. Canva MCP ⭐⭐

**Location:** `projects/shared/canva-mcp/`

**Status:** Skeleton only — not fully implemented.

**What It Would Do:**
- Create designs via Canva API
- Upload brand assets
- Export finished designs

**Usefulness:** Would be nice, but not critical. Can use Canva manually.

**Verdict:** DEPRIORITIZE — manual Canva is fine for now.

---

### 10. CapCut MCP ❌

**Status:** NOT POSSIBLE

**Why:** CapCut doesn't provide public API endpoints. No way to programmatically control it.

**Alternative:** 
- Use `video_jumpcut.py` for automated editing (FREE)
- Use CapCut manually for effects/transitions
- Use Creatomate/Shotstack for programmatic video (paid)

---

## What Needs to Be Built/Set Up

### PRIORITY 1: Coaching Landing Page

**Options:**

| Option | Effort | Cost | Recommendation |
|--------|--------|------|----------------|
| Carrd.co | 30 min | $9/year | ✅ Fastest |
| Linktree Pro | 30 min | $5/month | Good for link-in-bio |
| Custom (website-builder) | 2-4 hours | FREE | More control |
| Stan.store | 1 hour | $29/month | Good for digital products |

**What It Needs:**
- Headline: What you do, who you help
- Benefits: What clients get
- Social proof: Any testimonials
- CTA: Book a call (Calendly link)
- Simple contact form

### PRIORITY 2: Booking System (Calendly)

**Setup:**
1. Create free Calendly account
2. Set up 15-min "Free Consultation" slot
3. Connect to Google Calendar
4. Add link to bio and landing page

**Cost:** FREE for basic

### PRIORITY 3: Payment Processing

**Options:**

| Option | Effort | Fees |
|--------|--------|------|
| Stripe (direct) | 1 hour | 2.9% + $0.30 |
| PayPal | 30 min | 2.9% + $0.30 |
| Stripe via Trainerize | Integrated | 2.9% + $0.30 |

**Recommendation:** Use Trainerize's built-in payments if using Trainerize.

### PRIORITY 4: Client Onboarding Automation

**What It Would Do:**
- New client signs up → Auto-send welcome email
- Auto-assign questionnaire
- Auto-create in Trainerize
- Auto-assign initial program

**How to Build:**
- Use Trainerize MCP + Zapier/n8n
- Or manual until you have 5+ clients

**Verdict:** Build after first 3-5 clients. Not needed immediately.

---

## What to IGNORE (Not Relevant for Coaching)

| Asset | Why Ignore |
|-------|------------|
| Amazon Seller MCP | Different business entirely |
| Apollo MCP | B2B lead scraping — coaches get clients via social |
| Lead Scraper tools | B2B focused, not consumer coaching |
| SW Florida HVAC | Different business |
| SquareFoot Shipping | Different business |
| MCP Aggregator | B2B product, complex build |
| Go-Tracker app | Nice project but not revenue-generating |
| Voice AI system | Overkill for personal coaching |

---

## SOPs and Workflows Worth Keeping

### Relevant

| SOP/Workflow | Location | Usefulness |
|--------------|----------|------------|
| Fitness Influencer Operations | `directives/fitness_influencer_operations.md` | Content creation guidance |
| Interview Prep | `interview-prep-pptx/` | For job applications |
| Resume System | `projects/global-utility/resume/` | For job applications |

### Not Relevant

| SOP | Why |
|-----|-----|
| Amazon Seller Operations | Different business |
| HVAC Distributors | Different business |
| Apollo/Lead Scraping | B2B, not coaching |
| MCP Aggregator | B2B product |

---

## Recommended Tech Stack for Coaching

### Minimum Viable Stack (Start Here)

| Component | Tool | Cost |
|-----------|------|------|
| Client delivery | Trainerize | $19-99/month |
| Booking | Calendly Free | $0 |
| Landing page | Carrd.co | $9/year |
| Content creation | Grok + video_jumpcut | ~$5/month |
| Social posting | X scheduler | $0 |
| Payments | Stripe via Trainerize | 2.9% |

**Total monthly cost:** ~$25-100/month

### After 5+ Clients

| Add | Purpose |
|-----|---------|
| Notion/ClickUp | Client notes, tracking |
| Email marketing (ConvertKit) | Nurture leads |
| Client onboarding automation | Save time |

---

## Action Items for Claude Code

### Immediate (This Week)

1. [ ] Set up Calendly (free 15-min consultation)
2. [ ] Create simple landing page (Carrd or custom)
3. [ ] Update X bio with coaching positioning
4. [ ] Queue 2 weeks of coaching content (from templates)
5. [ ] Set up Trainerize account (if not already)

### Soon (Next 2 Weeks)

6. [ ] Connect payment processing
7. [ ] Create 2-3 program templates in Trainerize
8. [ ] Set up basic welcome email sequence
9. [ ] Test Trainerize MCP connection

### Later (After First Clients)

10. [ ] Build client onboarding automation
11. [ ] Create content library in Trainerize
12. [ ] Set up nutrition guides in system

---

## Summary

### Use These Assets

| Asset | For What |
|-------|----------|
| Fitness Influencer MCP | Content creation, program generation |
| Trainerize MCP | Client management and delivery |
| Grok Image Gen | Social media graphics |
| Video Jump-Cut | Video content editing |
| Workout/Nutrition Generators | Client program templates |
| X Scheduler | Automated posting |

### Build These

| Need | Priority |
|------|----------|
| Landing page | HIGH |
| Calendly setup | HIGH |
| Payment processing | MEDIUM |
| Client onboarding automation | LOW (after first clients) |

### Ignore These

- Amazon Seller MCP
- Apollo MCP
- Lead Scraper tools
- HVAC/Shipping content
- MCP Aggregator
- CapCut (no API exists)
- Canva MCP (not built, use Canva manually)

---

**The assets exist. The tools are ready. Now it's about execution: Get clients, deliver results, iterate.**

---

*Generated 2026-01-31*
