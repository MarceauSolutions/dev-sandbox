# Business Tools Optimization Roadmap

*Last Updated: 2026-01-27*
*Status: Prioritized optimization plan*

## Executive Summary

| Tool | LOC | Status | Next Step | Impact |
|------|-----|--------|-----------|--------|
| **Lead Scraper** | 33K | Production | Deploy Phase 1 quick wins | +5-8% response |
| **Apollo MCP** | 1.8K | PyPI Published | MCP Registry (5 min) | Marketplace discovery |
| **Social Media** | 9.4K | Development | Sora 2 + YouTube shorts | 3x engagement |
| **Twilio SMS** | 0.5K | Production | Systemd daemon | Always-on monitoring |
| **Yelp** | Embedded | Integrated | Optional refinement | Marginal gains |

## Immediate Actions (This Week)

### 1. Apollo MCP Registry Publishing (5 min)
**Status**: Blocked on GitHub device auth
**Action**:
```bash
# Authorize GitHub device code (one-time)
# Then run:
cd /Users/williammarceaujr./dev-sandbox/projects/apollo-mcp
/path/to/mcp-publisher publish --server server.json
```
**Result**: Apollo discoverable in Claude marketplace

### 2. Deploy Lead Scraper Phase 1 Quick Wins (3.5 hrs)
**What**:
- Vertical filtering (gyms/salons/restaurants only)
- Offer optimization templates
- Campaign dashboard activation

**Files already created**:
- Vertical filtering in `models.py`
- Templates in `templates/sms/`
- Dashboard in `campaign_dashboard.py`

**Expected Result**: +5-8% response rate improvement

### 3. Activate Sora 2 Video Generation (2-3 hrs)
**What**: Integrate OpenAI Sora 2 for video content
**Prerequisites**: 8 promo codes available in DOCKET
**Result**: 3x engagement boost on video posts

## Week 2 Actions

### 4. YouTube Shorts Automation (1-2 hrs)
- Uploader exists, needs scheduler integration
- Reach: 2B daily YouTube users

### 5. Complete Campaign Dashboard UI (2-3 hrs)
- Dashboard components partially built
- Add real-time metrics display
- Mobile-friendly view

### 6. TikTok Automation Completion (2-3 hrs)
- Implementation doc exists
- Build scheduling engine
- Target: Youth audience (14-24)

## Month 1 Actions

### 7. Unified Cost Monitoring (2 hrs)
- Consolidate: Apollo + Twilio + API costs
- Alert thresholds
- Prevent budget surprises

### 8. Lead Scoring Optimization (3-4 hrs)
- Tune ML model with actual conversion data
- A/B test scoring algorithms
- Better targeting efficiency

## Tool-Specific Details

### Lead Scraper (33K LOC)
**Working Well**:
- Campaign tracking with statistical significance
- Multi-touch attribution
- Apollo integration bridge
- Ralph autonomous agent

**Optimization Queue**:
| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| P1 | Phase 1 Quick Wins | 3.5 hrs | Ready to deploy |
| P1 | Campaign dashboard | 2-3 hrs | Partially built |
| P2 | Webhook optimization | Medium | Needs tuning |
| P3 | Email campaign channel | Medium | Not started |

### Apollo MCP (1.8K LOC)
**Working Well**:
- 10 MCP tools
- Credit-efficient enrichment (80% savings)
- 60-90 sec per 100 leads

**Optimization Queue**:
| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| P0 | MCP Registry publish | 5 min | Blocked on GitHub auth |
| P1 | Zapier integration | 1-2 hrs | Designed |
| P2 | OpenRouter registration | 30 min | Not started |

### Social Media Automation (9.4K LOC)
**Working Well**:
- X/Twitter production ready
- Grok image generation complete
- Content templates

**Deferred Features** (from DOCKET.md):
| Feature | Trigger | Priority |
|---------|---------|----------|
| Sora 2 video | 30+ posts + >2% engagement | P2 |
| Arcads AI | Video proven 3x engagement | P2 |
| X Premium | Rate limit 3x/week | P3 |

### Twilio SMS (0.5K LOC)
**Working Well**:
- Batch sending
- 8 templates
- Webhook support

**Optimization Queue**:
| Priority | Feature | Effort |
|----------|---------|--------|
| P2 | Response categorization | Low |
| P2 | Systemd daemon | 1 hr |
| P3 | A/B test runner | 1-2 hrs |

## Cross-Tool Opportunities

| Opportunity | Tools | Effort | Impact |
|-------------|-------|--------|--------|
| Unified dashboard | All | 3-4 hrs | High visibility |
| Cost monitoring | Apollo + Twilio | 1-2 hrs | Budget control |
| Automated A/B testing | Scraper + Social + SMS | 2-3 hrs | Data-driven |

## Success Metrics

### Week 1
- [ ] Apollo on MCP Registry
- [ ] Phase 1 quick wins deployed
- [ ] Sora 2 activated

### Month 1
- [ ] Campaign dashboard live
- [ ] YouTube + TikTok automated
- [ ] Cost monitoring active
- [ ] +10% overall response rate

### Quarter 1
- [ ] Unified analytics dashboard
- [ ] ML-optimized lead scoring
- [ ] All platforms automated
- [ ] $5K+ revenue from leads

## Related Documents

- [SOP-OPTIMIZATION-WITH-RALPH-CLAWDBOT.md](SOP-OPTIMIZATION-WITH-RALPH-CLAWDBOT.md)
- `projects/social-media-automation/DOCKET.md` - Deferred features
- `projects/shared/lead-scraper/PHASE-1-QUICK-WINS.md` - Ready to deploy
