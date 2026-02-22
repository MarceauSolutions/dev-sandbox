# Miko's Lab Knowledge Base

AI Influencer & Content Creation resources from [Miko's Lab](https://t.me/mikoslab) Telegram channel.

## Structure

```
mikos-lab/
├── pdfs/              # Downloaded guides and blueprints
├── posts/             # Scraped channel posts (JSON)
├── assets/            # Images, videos from channel
├── scripts/           # Scraper and sync tools
├── LATEST_POSTS.md    # Summary of recent posts
└── sync_state.json    # Tracks what's been scraped
```

## PDFs (V1 Content)

| Guide | Description |
|-------|-------------|
| AI Influencer Money Printing Blueprint | Monetization strategies |
| THE COMPLETE AI INFLUENCER SYSTEM GUIDE | Full system overview |
| Nano banana pro full guide | NanoBanana Pro tool usage |
| Sora Video Prompt Structure | Prompting for Sora |
| VEO 3.1 VS SORA 2 | Tool comparison |
| Full guide on making AI UGC | UGC that converts |
| HOW TO BUILD AN AI PERSONAL BRAND | Brand building |
| How to Get AI Tools 95% Cheaper | Cost optimization |
| How to Create Realistic AI Voices | Voice generation |
| THE AI CONTENT AGENCY BLUEPRINT | Agency setup |
| How to Get Clients for AI Agency | Client acquisition |
| The Complete AI Influencer Niche Selection | Niche picking |

## Usage

### Run Scraper Manually
```bash
cd /home/clawdbot/dev-sandbox/projects/marceau-solutions/mikos-lab
python3 scripts/scrape_mikoslab.py
```

### Auto-Sync (via cron)
```bash
# Add to crontab for daily sync
0 9 * * * cd /home/clawdbot/dev-sandbox/projects/marceau-solutions/mikos-lab && python3 scripts/scrape_mikoslab.py
```

## Integration with Fitness Influencer

These resources directly apply to:
1. **AI UGC Creation** — Generate realistic fitness content
2. **Tool Selection** — Seedance, Sora, Veo, Kling comparisons
3. **Monetization** — Affiliate, agency, digital products
4. **Content System** — Scripts, voices, video workflows

## Key Concepts

### AI Video Tools (Current Best)
- **Seedance 2** — Realistic human motion
- **Sora** — High quality, expensive
- **Veo 3.1** — Google's offering
- **NanoBanana Pro** — Cost-effective option
- **Kling** — Chinese alternative

### Workflow
1. Generate AI character (consistent face)
2. Create script with hooks
3. Generate video clips (Seedance/Sora/etc)
4. Add realistic voice (ElevenLabs/etc)
5. Edit and add captions
6. Export for platforms

---
*Last synced: See sync_state.json*
