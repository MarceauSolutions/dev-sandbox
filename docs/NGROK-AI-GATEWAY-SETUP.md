# ngrok AI Gateway Setup Guide

## Overview

This guide covers setting up ngrok AI Gateway for centralized AI API routing with automatic failover, observability, and cost tracking across all Marceau Solutions projects.

---

## Prerequisites

- [ ] ngrok account upgraded to Pay-as-you-go ($20/mo)
- [ ] Anthropic API key
- [ ] OpenAI API key (for failover)
- [ ] Custom domain configured (optional but recommended)

---

## Part 1: ngrok Account Setup

### Step 1: Upgrade Account

1. Go to https://dashboard.ngrok.com/settings/billing
2. Select **Pay-as-you-go** plan ($20/mo + usage)
3. Add payment method

### Step 2: Reserve Custom Domains

1. Go to https://dashboard.ngrok.com/domains
2. Reserve domains for your architecture:

| Domain | Purpose | Hosting | Local Port |
|--------|---------|---------|------------|
| `api.marceausolutions.com` | Voice AI / Twilio webhooks | ngrok | 8000 |
| `marceausolutions.com` | Main business website | GitHub Pages | N/A |
| `www.squarefootshipping.com` | Square Foot client site | ngrok (pending) | 3001 |
| `www.swfloridacomfort.com` | HVAC client site | ngrok | 3002 |

**Note:** The main `marceausolutions.com` website is hosted on GitHub Pages (repository: `/Users/williammarceaujr./marceausolutions.com/`), not through ngrok. Only the `api.` subdomain uses ngrok for backend services.

**To add a custom domain:**
1. Click "New Domain"
2. Enter your domain (e.g., `api.marceausolutions.com`)
3. Add the CNAME record to your DNS (Namecheap):
   - Host: `api`
   - Value: `<your-region>.ngrok.io` (shown in dashboard)
   - TTL: Automatic

---

## Part 2: AI Gateway Setup

### Step 1: Create AI Gateway

1. Go to https://dashboard.ngrok.com/ai-gateways
2. Click **"+ New AI Gateway"**
3. Enter endpoint URL: `ai.marceausolutions.ngrok.dev` (or your custom subdomain)
4. Click **"Create & Configure"**

### Step 2: Add API Keys to ngrok Secrets

1. Go to https://dashboard.ngrok.com/security/secrets
2. Add your API keys:

| Secret Name | Value |
|-------------|-------|
| `anthropic-key` | `sk-ant-api03-...` |
| `openai-key` | `sk-proj-...` |

### Step 3: Configure Providers

In the AI Gateway configuration, set up multi-provider failover:

```yaml
# AI Gateway Traffic Policy
on_http_request:
  - type: ai-gateway
    config:
      only_allow_configured_providers: true

      # Provider configuration with failover order
      providers:
        # Primary: Anthropic Claude
        - id: anthropic
          api_keys:
            - value: ${secrets.get('anthropic-key')}

        # Failover: OpenAI GPT
        - id: openai
          api_keys:
            - value: ${secrets.get('openai-key')}

      # Model selection strategy
      model_selection:
        strategy: ordered  # Try providers in order listed
```

### Step 4: Configure Model Routing (Optional)

For cost optimization, route different query types to appropriate models:

```yaml
on_http_request:
  - type: ai-gateway
    config:
      providers:
        - id: anthropic
          api_keys:
            - value: ${secrets.get('anthropic-key')}
        - id: openai
          api_keys:
            - value: ${secrets.get('openai-key')}

      # Route by model capability
      model_mappings:
        # Fast/cheap for simple queries
        "fast": "claude-3-5-haiku-latest"
        # Balanced for voice AI
        "balanced": "claude-sonnet-4-0"
        # Complex reasoning
        "complex": "claude-opus-4-5"
```

---

## Part 3: Update Voice AI to Use Gateway

### Option A: OpenAI SDK Compatibility (Recommended)

The AI Gateway is OpenAI SDK compatible. Update the voice engine:

```python
# projects/ai-customer-service/src/business_voice_engine.py

from openai import OpenAI

class BusinessVoiceEngine:
    def __init__(self, business_config: dict, system_prompt: str):
        self.config = business_config
        self.system_prompt = system_prompt
        self.settings = get_settings()

        # Use AI Gateway instead of direct Anthropic
        self.client = OpenAI(
            base_url=self.settings.ai_gateway_url,  # https://ai.marceausolutions.ngrok.dev
            api_key=self.settings.ai_gateway_key,   # ngrok API key or passthrough
        )

    async def process_turn(self, state, customer_input):
        # ... existing code ...

        response = self.client.chat.completions.create(
            model="claude-sonnet-4-0",           # Primary model
            models=["gpt-4o"],                   # Failover model
            max_tokens=300,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *messages
            ]
        )

        ai_response = response.choices[0].message.content
        # ... rest of existing code ...
```

### Option B: Keep Anthropic SDK (Passthrough Mode)

If you prefer keeping the Anthropic SDK, use passthrough mode:

```python
# No code changes needed - AI Gateway proxies requests transparently
# Just ensure your Anthropic calls go through the gateway URL

import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url="https://ai.marceausolutions.ngrok.dev/v1"  # Gateway URL
)
```

### Update Config

Add to `projects/ai-customer-service/src/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # AI Gateway
    ai_gateway_url: str = "https://ai.marceausolutions.ngrok.dev"
    ai_gateway_key: str = ""  # If using managed keys

    # Failover config
    ai_primary_model: str = "claude-sonnet-4-0"
    ai_failover_model: str = "gpt-4o"
```

Add to `.env`:

```bash
# AI Gateway
AI_GATEWAY_URL=https://ai.marceausolutions.ngrok.dev
AI_GATEWAY_KEY=  # Optional if using passthrough
```

---

## Part 4: Running Multiple Tunnels

### Create ngrok Configuration File

Create `~/.ngrok/ngrok.yml`:

```yaml
version: "3"
agent:
  authtoken: YOUR_NGROK_AUTHTOKEN

tunnels:
  # Voice AI API
  voice-api:
    proto: http
    addr: 8000
    domain: api.marceausolutions.com

  # Main website
  main-site:
    proto: http
    addr: 3000
    domain: marceausolutions.com

  # Square Foot Shipping
  squarefoot:
    proto: http
    addr: 3001
    domain: squarefootshipping.com

  # SW Florida Comfort HVAC
  hvac:
    proto: http
    addr: 3002
    domain: swfloridacomfort.com
```

### Start All Tunnels

```bash
# Start all tunnels at once
ngrok start --all

# Or start specific tunnels
ngrok start voice-api main-site

# Or start individual tunnel
ngrok start voice-api
```

### Create Startup Script

Create `~/scripts/start-ngrok-tunnels.sh`:

```bash
#!/bin/bash
# Start all ngrok tunnels for Marceau Solutions

echo "Starting ngrok tunnels..."
ngrok start --all --config ~/.ngrok/ngrok.yml

# If you want to run in background:
# nohup ngrok start --all --config ~/.ngrok/ngrok.yml > /tmp/ngrok.log 2>&1 &
```

---

## Part 5: Observability & Cost Tracking

### View AI Gateway Metrics

1. Go to https://dashboard.ngrok.com/ai-gateways
2. Click on your gateway
3. View:
   - Request volume by model
   - Latency percentiles
   - Error rates
   - Failover events

### Track Costs by Business

Add metadata to requests for per-business tracking:

```python
response = self.client.chat.completions.create(
    model="claude-sonnet-4-0",
    messages=messages,
    # Add metadata for tracking
    extra_headers={
        "X-Business-ID": self.config.get("name"),  # "SW Florida Comfort HVAC"
        "X-Call-ID": state.call_id
    }
)
```

### Set Up Alerts

In ngrok dashboard:
1. Go to Settings > Alerts
2. Create alerts for:
   - High error rate (>5%)
   - Failover triggered
   - Latency spike (>2s p95)

---

## Part 6: DNS Configuration (Namecheap)

For custom domains, add these DNS records in Namecheap:

### For api.marceausolutions.com

| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME | api | `tunnel.us.ngrok.com` | Automatic |

### For root domain (marceausolutions.com)

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | ngrok IP (from dashboard) | Automatic |
| CNAME | www | `tunnel.us.ngrok.com` | Automatic |

**Note:** After adding DNS records, verify in ngrok dashboard that the domain shows "Verified".

---

## Quick Reference

### Commands

```bash
# Start all tunnels
ngrok start --all

# Check tunnel status
curl http://localhost:4040/api/tunnels

# View logs
ngrok logs

# Test AI Gateway health
curl https://ai.marceausolutions.ngrok.dev/health
```

### Endpoints After Setup

| Service | URL | Hosting |
|---------|-----|---------|
| Voice AI Webhooks | `https://api.marceausolutions.com/twilio/business-voice` | ngrok → localhost:8000 |
| AI Gateway | `https://ai.marceausolutions.ngrok.dev` | ngrok (future) |
| Main Site | `https://marceausolutions.com` | GitHub Pages |
| Square Foot | `https://www.squarefootshipping.com` | ngrok → localhost:3001 |
| HVAC | `https://www.swfloridacomfort.com` | ngrok → localhost:3002 |

### Twilio Webhook URLs (Update After Setup)

Update in Twilio Console for each phone number:

| Phone | Webhook URL |
|-------|-------------|
| (239) 766-6129 | `https://api.marceausolutions.com/twilio/business-voice` |
| (239) 880-3365 | `https://api.marceausolutions.com/twilio/business-voice` |
| (855) 239-9364 | `https://api.marceausolutions.com/twilio/voice` |

---

## Troubleshooting

### "ERR_NGROK_3200" - Tunnel session limit

**Cause:** Free tier only allows 1 tunnel
**Fix:** Upgrade to Pay-as-you-go for unlimited tunnels

### "Domain not verified"

**Cause:** DNS not propagated or wrong CNAME
**Fix:**
1. Check DNS records in Namecheap
2. Wait 5-30 minutes for propagation
3. Use `dig api.marceausolutions.com` to verify

### AI Gateway returns 502

**Cause:** AI provider error or rate limit
**Fix:**
1. Check ngrok dashboard for error details
2. Verify API keys are correct in secrets
3. Check if failover model is configured

### High latency through gateway

**Cause:** Extra hop through ngrok
**Expected:** ~50-100ms additional latency
**If higher:** Check ngrok status page, try different region

---

## Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| ngrok Pay-as-you-go | $20 base |
| Additional requests (100k+) | ~$0.10 per 10k |
| Custom domains | Included |
| AI Gateway | Included |
| **Estimated Total** | **$20-30/mo** |

AI API costs (Anthropic/OpenAI) are separate and billed directly by those providers.

---

## Migration Checklist

- [ ] Upgrade ngrok account
- [ ] Add API keys to ngrok secrets
- [ ] Create AI Gateway endpoint
- [ ] Configure DNS for custom domains
- [ ] Update `ngrok.yml` with all tunnels
- [ ] Update voice AI code to use gateway (optional)
- [ ] Update Twilio webhook URLs
- [ ] Test all endpoints
- [ ] Set up monitoring alerts

---

*Last Updated: 2026-01-18*
