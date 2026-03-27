# Post-April 6 Roadmap — Personal Assistant Evolution

**Written**: March 26, 2026
**Revisit**: April 13, 2026 (after 1 week of live operation)

## Current State (ships tonight)

The system runs autonomously during 7-3 work hours:
- 6:30am digest with ROI-prioritized daily plan
- 9am acquisition loop (discover → score → outreach → follow-up)
- 15-min response polling with HOT lead SMS alerts
- 5:30pm pipeline digest
- Calendar blocking on "yes schedule" approval
- 10-check compliance enforcement on every run
- 3-agent routing (Claude local, Ralph EC2, Grok strategic)

## Week 1 (March 27 — April 5): Validate

**Goal**: Land first client. Everything else is secondary.

**DO**:
- Run the live loop daily
- Read the morning digest
- Visit qualified leads in person
- Reply "1" to HOT lead SMS
- Reply "yes schedule" to proposed blocks
- Run `./scripts/save.sh` after each session

**DO NOT**:
- Add features
- Refactor code
- Build learning systems
- Optimize before you have data

## Week 2-3 (April 6-19): Operate Under Job Constraints

**Schedule changes automatically** — the scheduler detects post-April-6 and switches to:
- Pre-work block: 6:15-6:45 (prep)
- Lunch block: 12:00-12:45 (calls + follow-ups)
- Post-work block: 15:15-17:15 (visits + deep work)
- Evening admin: 20:15-21:00

**Track manually in a notebook**:
- Which proposed visits actually happened
- Which calls led to meetings
- Which meetings led to proposals
- Which proposals closed

This manual tracking is the "learning data" the system will eventually need.

## Month 2 (May): First Improvements Based on Real Data

**Only after you have 20+ data points** (proposed tasks → outcomes):

1. **Outcome tracking table** in pipeline.db:
   - scheduled_task → completed? → resulted_in_meeting? → resulted_in_client?
   - Simple columns, manual entry initially

2. **ROI recalibration**:
   - If walk-ins convert at 0% but calls convert at 15% → swap priority
   - If certain industries respond better → weight those leads higher
   - This is a one-time manual adjustment, not ML

3. **Approval reduction**:
   - After 2 weeks of consistently good schedules, stop replying "yes schedule"
   - Just follow the digest suggestions directly
   - Keep approval for new tower creation and proposals (always)

## Month 3+ (June): Adaptive Features

**Only build these if the manual data justifies them**:

1. **Auto-outcome tracking**: Link calendar events to pipeline.db deal stage changes
2. **Industry-weighted scoring**: Auto-adjust lead scoring based on conversion history
3. **Ralph-driven A/B testing**: Test different outreach angles per industry on EC2
4. **Content auto-scheduling**: Wire fitness-influencer social media to launchd

## Architecture Principles (Permanent)

- **Human approval on**: pricing, proposals, contracts, new tower creation, reputation-impacting actions
- **Never auto-approve**: calendar events in first month, financial commitments, client communications
- **Data before code**: Don't build learning systems until you have 20+ outcome data points
- **One change at a time**: Each improvement gets 1 week of observation before the next
- **Grok reviews before major changes**: Use grok_orchestrator.py to analyze before implementing

## How to Iterate (Using the 3-Agent System)

```bash
# Grok gives a goal after reviewing data
python3 execution/grok_orchestrator.py goal "Improve call conversion rate"
# → Analyzes pipeline → Suggests next action → Generates Claude prompt

# Claude implements the change
# (Grok reviews the proposed change before executing)

# If it's a long-running test → hand off to Ralph
python3 execution/three_agent_orchestrator.py handoff --to ralph --task "A/B test call scripts"

# Save after each iteration
./scripts/save.sh "improvement: adjusted call ROI based on week 2 data"
```

## Success Metrics

| Metric | Week 1 Target | Month 1 Target | Month 3 Target |
|--------|--------------|----------------|----------------|
| Outreach emails/day | 10 | 10 | 15-20 |
| Hot leads/week | 1+ | 3-5 | 5-10 |
| Discovery calls/week | 1 | 2-3 | 3-5 |
| Clients signed | 1 | 2-3 | 5+ |
| System uptime | 95% | 99% | 99% |
| Manual intervention/day | 5-10 min | 3-5 min | 1-2 min |
