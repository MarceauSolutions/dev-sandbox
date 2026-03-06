# Miko's Lab Knowledge Base

**Status**: Active scraper | **Type**: Research / knowledge capture

## What It Does
Scrapes and indexes content from Miko's Lab Telegram channel — an AI influencer and content creation resource. Used for reference on AI-powered content strategy, fitness influencer tactics, and automation techniques.

## Key Locations
| What | Where |
|------|-------|
| Scraped posts (JSON) | `posts/` |
| Downloaded PDFs | `pdfs/` |
| Assets (images, video) | `assets/` |
| Scraper scripts | `scripts/` |
| Sync state (last scraped) | `sync_state.json` |
| Recent posts summary | `LATEST_POSTS.md` |
| Key methods extracted | `MIKO_METHODS_SUMMARY.md` |
| Full knowledge base | `KNOWLEDGE_BASE.md` |

## Key Commands
```bash
# Sync latest posts from Telegram channel
python scripts/sync.py

# Check what was last scraped
cat sync_state.json
```

## Related
- Fitness influencer platform: `projects/marceau-solutions/fitness-influencer/`
- Social media automation: `projects/shared/social-media-automation/`
