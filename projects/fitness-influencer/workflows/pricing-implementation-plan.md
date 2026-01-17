# Pricing Implementation Plan - Fitness Influencer MCP

*Research completed: 2026-01-16 by Agent C*

## Executive Summary

**Recommended Approach:** Option B - Local JSON + Manual Stripe Setup
- **Complexity:** Low (20-30 hours)
- **Timeline:** 1-2 weeks
- **Rationale:** Minimal backend overhead, enforcement in MCP tool handlers, easy migration path

## Pricing Tiers (from GO-NO-GO Decision)

| Tier | Price | Target User |
|------|-------|-------------|
| **STARTER** | $19/month | Free tier users who need more |
| **PRO** | $49/month | Active creators (10K-100K followers) |
| **AGENCY** | $149/month | Agencies managing 10+ creators |

Annual billing: 20% discount ($152/$392/$1,192 per year)

## Feature Limits by Tier

| Feature | Free | Starter | Pro | Agency |
|---------|------|---------|-----|--------|
| Video jump-cuts | 5/mo | 25/mo | Unlimited | Unlimited |
| Comment categorization | 10/day | Unlimited | Unlimited | Unlimited |
| Workout plans | 3/mo | Unlimited | Unlimited | Unlimited |
| Content calendars | 1/week | Unlimited | Unlimited | Unlimited |
| AI images | 2/mo | 10/mo | 20/mo | 50/mo |
| Cross-platform optimizer | Unlimited | Unlimited | Unlimited | Unlimited |
| Multi-client management | - | - | - | 10 clients |
| API access | - | - | - | Yes |
| White-label | - | - | - | Yes |

## Implementation Architecture

```
User pays via Stripe Payment Link
        ↓
You manually add email to ~/.fitness_mcp_pro_users.json
        ↓
MCP tool checks pro_users.json on each call
        ↓
Enforce limits or allow unlimited based on tier
```

## Files to Create

1. `src/fitness_influencer_mcp/subscription_manager.py` (~150-200 lines)
2. `src/fitness_influencer_mcp/usage_tracker.py` (~150-200 lines)
3. `landing-page/pricing.html` (~400-500 lines)
4. `PRICING-SETUP.md` - Manual payment processing runbook

## Files to Modify

1. `server.py` - Add limit checking to tool handlers (+300-400 lines)
2. `landing-page/index.html` - Add pricing section
3. `CHANGELOG.md` - v1.4.0 entry
4. `README.md` - Add pricing info

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
- Create `subscription_manager.py`
- Create `usage_tracker.py`
- Update `cogs_tracker.py` for per-user tracking

### Phase 2: Tool Integration (Days 3-5)
- Modify `server.py` tool handlers
- Add new tools: `get_user_tier`, `get_usage_summary`, `check_feature_access`
- Test limit enforcement

### Phase 3: Stripe & Pricing Page (Days 6-7)
- Create Stripe products and payment links
- Update landing page with pricing cards
- Create payment processing runbook

### Phase 4: Testing (Days 8-10)
- Test all limit scenarios
- Test edge cases (missing email, concurrent calls, resets)
- Update documentation

### Phase 5: Deploy (Days 11-14)
- Version bump to 1.4.0
- Push to PyPI and MCP Registry
- Announce pricing changes

## Effort Estimate

| Phase | Hours |
|-------|-------|
| Foundation | 9 |
| Tool Integration | 18 |
| Stripe & Pricing | 10 |
| Testing | 8 |
| Deploy | 4 |
| **TOTAL** | **~49 hours** |

## Key Implementation Pattern

```python
# In each tool handler:
async def handle_generate_fitness_image(arguments: dict):
    user_email = os.getenv("MCP_USER_EMAIL", "anonymous")

    subscription = SubscriptionManager()
    tier = subscription.get_tier(user_email)

    if tier == "free":
        tracker = UsageTracker()
        can_proceed, msg = tracker.check_limit(user_email, "ai_image")
        if not can_proceed:
            return [TextContent(
                type="text",
                text=msg + "\n\nUpgrade to Pro: https://marceausolutions.com/fitness-pro"
            )]

    # ... existing implementation ...
    tracker.increment_usage(user_email, "ai_image")
    return result
```

## Why Option B Over Full Stripe Integration

| Factor | Option B (Recommended) | Full Stripe (Option A) |
|--------|------------------------|------------------------|
| Timeline | 1-2 weeks | 3-4 weeks |
| Complexity | Low | High |
| Backend needed | None | AWS/GCP required |
| Scaling ceiling | ~30 users | 10K+ users |
| MVP validation | Perfect | Overkill |
| Upgrade path | Easy → Option A | N/A |

## Next Steps

1. Confirm Option B approach
2. Set up Stripe products + payment links
3. Implement Phase 1-2 (subscription_manager.py + server.py changes)
4. Create pricing page
5. Test and deploy v1.4.0

---

*Full research report available at: /tmp/claude/-Users-williammarceaujr--dev-sandbox/tasks/afa6fb6.output*
