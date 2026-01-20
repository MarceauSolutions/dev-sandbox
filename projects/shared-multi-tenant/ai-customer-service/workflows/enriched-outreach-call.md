# Workflow: Enriched Outreach Call

## Overview

Make personalized AI outreach calls using lead enrichment to match the right service to the right customer.

## Use Cases

- Cold outreach to leads with known business name
- Follow-up calls to leads from Google/Yelp scraping
- Personalized demos of AI services

## Prerequisites

- Server running: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- ngrok tunnel active: `ngrok http 8000 --pooling-enabled`
- Twilio credentials configured in `.env`

## Steps

### 1. Enrich Lead (Optional - for complex campaigns)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service

# Test enrichment
python -c "
from src.lead_enrichment import enrich_lead
lead = enrich_lead('+12393984852', 'Boab Fit', 'fitness')
print(f'Service: {lead.recommended_service}')
print(f'Greeting: {lead.personalized_greeting}')
"
```

### 2. Make Enriched Outreach Call

```bash
# With personalization
python scripts/outreach_call.py PHONE_NUMBER --business "Business Name" --type "business_type"

# Examples:
python scripts/outreach_call.py 2393984852 --business "Boab Fit" --type "fitness"
python scripts/outreach_call.py 2395551234 --business "Mario's Pizza" --type "restaurant"
python scripts/outreach_call.py 2395554321 --business "Naples Salon" --type "salon"
```

### 3. Monitor Call

Watch server logs:
```bash
# In terminal running uvicorn
# Look for: OUTREACH GATHER: CallSid=..., Speech=...
```

Or check ngrok inspector: http://127.0.0.1:4040

### 4. Review Call Transcript

```bash
curl http://localhost:8000/twilio/calls | python -m json.tool
```

## Business Type Options

| Type | Best For |
|------|----------|
| `restaurant` | Pizza shops, cafes, diners |
| `fitness` / `gym` | Gyms, fitness studios |
| `fitness_influencer` | Content creators, trainers |
| `salon` / `spa` | Hair salons, spas |
| `medical` / `dental` | Clinics, dental offices |
| `real_estate` | Realtors, agencies |
| `auto` | Auto shops, mechanics |
| `hvac` / `plumbing` | Service contractors |

## Service Matching

The system automatically matches:
- Restaurants → AI Customer Service
- Fitness → Fitness Content Automation
- Appointment businesses → Voice AI
- Other → Business Automation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Call doesn't connect | Check ngrok is running, server is up |
| "Application error" | Check server logs for exceptions |
| Generic greeting | Verify --business and --type params |
| No speech recognized | Speak clearly after the greeting |

## Success Criteria

- ✅ Call connects and plays personalized greeting
- ✅ AI responds appropriately to interest/disinterest
- ✅ Call ends gracefully with next steps
