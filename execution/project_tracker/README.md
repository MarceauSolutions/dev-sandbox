# Project & API Usage Tracker

Track API usage and costs per project/website for Marceau Solutions.

## Quick Commands

```bash
# List all registered projects
python3.11 execution/project_tracker/tracker.py --list

# Fetch current API usage from providers
python3.11 execution/project_tracker/tracker.py --fetch

# Generate usage report (last 7 days)
python3.11 execution/project_tracker/tracker.py --report

# Generate report for last 30 days
python3.11 execution/project_tracker/tracker.py --report --days 30

# Log an API call manually
python3.11 execution/project_tracker/tracker.py --log PROJECT_ID API ENDPOINT COST
# Example: python3.11 tracker.py --log fitai-demo anthropic /v1/messages 0.05
```

## How It Works

### 1. Provider-Level Tracking (Automatic)
Fetches usage directly from APIs that support it:
- **Twilio**: SMS count and cost
- **ElevenLabs**: Character usage
- **Stripe**: Revenue and transactions

### 2. Project-Level Tracking (Manual/Instrumented)
Log API calls with project ID to attribute usage:

```python
from execution.project_tracker.tracker import log_api_call

# In your code, after making an API call:
log_api_call("fitai-demo", "anthropic", "/v1/messages", cost=0.05)
```

### 3. n8n Integration
Call the tracker from n8n workflows:
```bash
curl -X POST http://localhost:5002/log-api-call \
  -H "Content-Type: application/json" \
  -d '{"project": "fitai-demo", "api": "anthropic", "endpoint": "/messages", "cost": 0.05}'
```

## Adding a New Project

Edit `config.json`:

```json
{
  "projects": {
    "new-project-id": {
      "name": "My New Project",
      "url": "https://example.com",
      "type": "webapp",
      "apis": ["anthropic", "stripe"],
      "status": "active"
    }
  }
}
```

## Website Analytics

For traffic tracking per website, use:

### Option A: Plausible (Recommended - Privacy-focused)
- Self-host or use cloud: https://plausible.io
- Add to each site: `<script defer data-domain="yoursite.com" src="https://plausible.io/js/script.js"></script>`
- Separate dashboard per site

### Option B: Google Analytics 4
- Create separate GA4 property per site
- Track in Google Analytics dashboard

### Option C: Cloudflare Analytics
- Free with Cloudflare
- Per-domain analytics

## Tracking API Usage Per Website

When a website makes API calls through your backend:

1. **Tag requests with project ID** in your backend
2. **Log each API call** using `log_api_call()`
3. **View aggregated usage** with `--report`

Example backend integration:
```python
# In your Flask/FastAPI route
@app.post("/api/generate")
def generate(request):
    project_id = request.headers.get("X-Project-ID", "unknown")
    
    # Make API call
    response = anthropic_client.messages.create(...)
    
    # Log usage
    log_api_call(project_id, "anthropic", "/messages", cost=calculate_cost(response))
    
    return response
```

## Weekly Report (Automated)

Set up cron job or n8n workflow to run weekly:
```bash
python3.11 execution/project_tracker/tracker.py --report --days 7
```

Send output to Telegram for review.
