<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 23: Cold Outreach Strategy Development

**When**: Developing new cold outreach strategies, testing messaging hypotheses, or optimizing campaign performance

**Purpose**: Systematically create, test, and optimize cold outreach strategies using A/B testing and data-driven iteration

**Agent**: Claude Code (strategy design, A/B analysis). Clawdbot (hypothesis brainstorming). Ralph (bulk template generation).

**The Hormozi Framework** (foundation for all outreach):
1. **Lead with value** - Offer something before asking
2. **Be specific** - Mention their business name, location, pain point
3. **Social proof** - Reference similar businesses helped
4. **Clear CTA** - One simple action to take
5. **Multi-touch** - 5+ touches before giving up (most respond after touch 3-5)

**Steps**:

**Phase 1: Define Target Segment**
```markdown
## Segment Definition
- **Who**: [e.g., Naples gyms without websites]
- **Pain point**: [e.g., losing customers to competitors with online presence]
- **Evidence**: [e.g., 55% of scraped gyms have no website]
- **Offer**: [e.g., free mockup website in 48 hours]
```

**Phase 2: Create Message Hypotheses**

For each segment, develop 2-3 competing message angles:

| Hypothesis | Angle | Example |
|------------|-------|---------|
| A (Control) | Direct pain | "80% of customers search online first" |
| B (Variant) | Social proof | "Just helped 3 Naples businesses" |
| C (Variant) | Scarcity | "Only taking 2 more clients this month" |

**Phase 3: Design A/B Test**
```bash
# Split leads into equal groups
python -m src.campaign_analytics ab-test create \
    --name "pain_vs_social_proof" \
    --control-template no_website_intro \
    --variant-template social_proof_intro \
    --sample-size 100
```

**Phase 4: Execute Campaign** (per SOP 18)
```bash
# Send to control group
python -m src.scraper sms --for-real --limit 50 --template no_website_intro --ab-group control

# Send to variant group
python -m src.scraper sms --for-real --limit 50 --template social_proof_intro --ab-group variant
```

**Phase 5: Analyze Results**
```bash
# After 7+ days and 100+ contacts per variant
python -m src.campaign_analytics ab-test results --name "pain_vs_social_proof"
```

Output shows:
- Response rate per variant
- Statistical significance (85% confidence threshold)
- Recommended winner

**Phase 6: Iterate**
- Winner becomes new control
- Develop new variant hypothesis
- Repeat cycle

**Template Library Structure**:
```
projects/shared/lead-scraper/
├── templates/
│   ├── sms/
│   │   ├── intro/           # Initial outreach templates
│   │   ├── followup/        # Follow-up sequence templates
│   │   └── archived/        # Losing templates (for reference)
│   └── email/
│       ├── intro/
│       └── followup/
```

**New Template Checklist**:
- [ ] Under 160 characters (SMS)
- [ ] Contains personalization ({business_name})
- [ ] Clear CTA
- [ ] "STOP to opt out" included
- [ ] Reviewed by William before sending

**Optimization Cycle**:
```
Define Segment → Create Hypotheses → A/B Test → Analyze → Scale Winner → Repeat
      ↑                                                          │
      └──────────────────────────────────────────────────────────┘
```

**Success Criteria**:
- ✅ Each segment has documented strategy
- ✅ A/B tests reach statistical significance
- ✅ Response rate improves over baseline (target: +20% per quarter)
- ✅ Losing templates archived with learnings

**References**: `projects/shared/lead-scraper/workflows/cold-outreach-strategy-sop.md`, SOP 18 (SMS Campaign Execution), SOP 22 (Campaign Analytics)

