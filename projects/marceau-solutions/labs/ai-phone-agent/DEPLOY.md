# AI Phone Agent Deployment

## Overview

This system handles inbound calls to (855) 239-9364 with an AI assistant that:
1. Greets callers and asks qualifying questions
2. Collects lead information (business type, pain points, timeline)
3. Creates a warm lead in the dashboard
4. Sends email notification to William
5. Logs to Google Sheets for tracking

## Components

| Component | Port | URL |
|-----------|------|-----|
| AI Phone Agent | 8795 | ai-phone.marceausolutions.com |
| Warm Leads Dashboard | 8796 | leads.marceausolutions.com |
| n8n Webhook | 5678 | /webhook/ai-phone-lead |

## Prerequisites

1. **ElevenLabs Creator Plan** ($22/mo) - Required for Conversational AI
   - Go to: https://elevenlabs.io/pricing
   - Upgrade to Creator tier
   - Create a Conversational AI agent in the dashboard

2. **Twilio Configuration**
   - Phone number: +18552399364 (already configured)
   - Webhook URL: https://ai-phone.marceausolutions.com/incoming-call

## Deployment Steps

### 1. DNS Records

Add A records in your DNS provider:
```
ai-phone.marceausolutions.com → 34.193.98.97
leads.marceausolutions.com → 34.193.98.97
```

### 2. Install Services

```bash
# AI Phone Agent
sudo cp deploy/ai-phone-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-phone-agent
sudo systemctl start ai-phone-agent

# Warm Leads Dashboard
sudo cp deploy/warm-leads-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable warm-leads-dashboard
sudo systemctl start warm-leads-dashboard
```

### 3. Configure Nginx

```bash
sudo bash -c 'cat deploy/nginx.conf >> /etc/nginx/conf.d/sites.conf'
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificates

```bash
sudo certbot --nginx -d ai-phone.marceausolutions.com
sudo certbot --nginx -d leads.marceausolutions.com
```

### 5. Configure Twilio Webhook

1. Go to: https://console.twilio.com/
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on +18552399364
4. Under "Voice & Fax" → "A Call Comes In":
   - Webhook: `https://ai-phone.marceausolutions.com/incoming-call`
   - Method: POST

### 6. Create n8n Workflow

1. Open n8n: http://localhost:5678
2. Import the workflow from `deploy/n8n-workflow.json`
3. Update the Google Sheets node with your sheet ID
4. Activate the workflow

### 7. (Optional) ElevenLabs Conversational AI

When you upgrade to Creator tier:

1. Go to ElevenLabs dashboard → Conversational AI
2. Create new agent with settings from `config/agent_config.json`
3. Get the Agent ID
4. Add to .env: `ELEVENLABS_AGENT_ID=your_agent_id`
5. Restart the ai-phone-agent service

## Testing

```bash
# Test AI Phone Agent health
curl https://ai-phone.marceausolutions.com/health

# Test Dashboard
curl https://leads.marceausolutions.com/health

# Test lead creation
curl -X POST https://leads.marceausolutions.com/api/leads \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "source": "test", "status": "warm_lead", "collected_data": {"business_type": "HVAC", "pain_points": "Too many calls"}}'

# Call the number
# Have someone call (855) 239-9364 and verify the flow
```

## Fallback Mode

If ElevenLabs Conversational AI is not available (free tier), the system uses:
- Twilio's built-in TTS (Amazon Polly voices)
- Simple speech-to-text gathering
- Same lead collection workflow

This works but is less natural than ElevenLabs.

## Monitoring

- View leads: https://leads.marceausolutions.com
- Service logs: `journalctl -u ai-phone-agent -f`
- Dashboard logs: `journalctl -u warm-leads-dashboard -f`

## Costs

| Service | Cost |
|---------|------|
| Twilio (inbound calls) | ~$0.0085/min |
| ElevenLabs Creator | $22/mo (includes 100 mins of conversation) |
| EC2 (already running) | $0 additional |

Estimated monthly cost for 50 calls averaging 3 min: ~$23-25/mo
