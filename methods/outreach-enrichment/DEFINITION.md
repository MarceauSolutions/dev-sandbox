# Outreach Enrichment Method

*Created: 2026-01-18*
*Version: 1.0*

## Problem Statement

Cold outreach (calls, SMS, emails) performs better when personalized to the recipient's:
- Business name and type
- Specific pain points
- Relevant service offerings
- Optimal timing

Currently, outreach is either generic or requires manual research per lead. We need a systematic method to enrich lead data and personalize outreach automatically.

## Scope

This method covers:
1. **Lead Enrichment** - Gathering data about a lead before outreach
2. **Service Matching** - Selecting the right service offer based on lead profile
3. **Personalization** - Customizing messaging with lead-specific details
4. **Timing Optimization** - Determining the best time to reach out

## Users

- **William (human)**: Reviews enriched leads, approves outreach campaigns
- **Claude (AI)**: Executes enrichment, generates personalized scripts
- **Voice AI**: Delivers personalized outreach calls
- **SMS System**: Sends personalized text campaigns

## Success Criteria

- 2x improvement in response rate vs generic outreach
- 90%+ leads enriched with business name + type
- <5 minutes per lead for enrichment (automated)
- Service-lead match accuracy >80%

## Inputs

1. **Lead Data** (minimum):
   - Phone number OR email
   - Location (optional but helpful)

2. **Service Catalog**:
   - AI Customer Service (restaurants, retail)
   - AI Voice Agents (any business with phone volume)
   - Fitness Content Automation (gyms, trainers, influencers)
   - Business Automation (any business)

## Outputs

1. **Enriched Lead Profile**:
   ```json
   {
     "phone": "+12393984852",
     "business_name": "Boab Fit",
     "business_type": "fitness",
     "owner_name": "Sarah",
     "social_presence": ["instagram"],
     "pain_points": ["content_creation", "booking"],
     "recommended_service": "fitness_content_automation",
     "personalized_greeting": "...",
     "best_contact_time": "10am-2pm weekdays"
   }
   ```

2. **Personalized Script** for voice/SMS/email

## Method Overview

```
Lead Input → Enrichment → Service Matching → Script Generation → Outreach
     ↓            ↓              ↓                  ↓
  Phone/Email  Google/Social  Pain Point Map    Template + Data
```

## Next Steps

1. Create enrichment pipeline (sources: Google, social, business directories)
2. Build service-to-business-type mapping matrix
3. Create script templates with variable slots
4. Integrate with outreach_call.py and SMS system
