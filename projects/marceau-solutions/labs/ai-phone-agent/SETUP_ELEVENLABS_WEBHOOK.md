# ElevenLabs Webhook Configuration

## The Problem
ElevenLabs handles calls directly via native Twilio integration, but **call data isn't being sent back** to your systems. This means:
- No notification when calls complete
- No transcript capture
- No lead qualification
- No CRM routing

## The Solution
Configure ElevenLabs to send a webhook after each call completes.

## Steps

### 1. Log into ElevenLabs
Go to: https://elevenlabs.io/app/conversational-ai

### 2. Select Your Agent
Agent ID: `agent_9801kmgjg670fb7bdv5z9r96y66d`
(Marceau Solutions AI Services Assistant)

### 3. Configure Webhook
In the agent settings, find **Webhooks** or **Post-call actions**:

**Webhook URL:**
```
https://ai-phone.marceausolutions.com/webhook/elevenlabs
```

**Method:** POST

**Events to send:**
- ✅ Conversation completed
- ✅ Include transcript
- ✅ Include recording URL (if available)
- ✅ Include caller phone number

### 4. Alternative: Use the ElevenLabs API
If the dashboard doesn't support webhooks, we can poll the API for recent conversations:

```python
import requests

response = requests.get(
    'https://api.elevenlabs.io/v1/convai/conversations',
    headers={'xi-api-key': 'YOUR_API_KEY'},
    params={'agent_id': 'agent_9801kmgjg670fb7bdv5z9r96y66d'}
)
```

## Testing

After configuration, test the webhook:

```bash
# Simulate a call
curl -X POST https://ai-phone.marceausolutions.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{
    "caller": "+12395551234",
    "duration": 120,
    "transcript": [
      {"role": "user", "message": "Hi, I run a plumbing company and need help with after-hours calls"}
    ]
  }'
```

You should receive a Telegram notification within seconds.

## What Happens After Setup

1. **Call comes in** → ElevenLabs handles conversation
2. **Call ends** → ElevenLabs sends webhook to our server
3. **Server processes** → 
   - Parses transcript for qualification data
   - Scores lead (hot/warm/cold)
   - Sends rich Telegram notification
   - Adds to Google Sheets CRM
   - Creates deal in Sales Pipeline (if qualified)
4. **William gets notified** → Full context, priority, next steps

## Webhook Payload Expected

```json
{
  "conversation_id": "conv_xxxxx",
  "call_sid": "CA...",
  "caller": "+12395551234",
  "duration": 180,
  "status": "completed",
  "transcript": [
    {"role": "assistant", "message": "Hi, thanks for calling..."},
    {"role": "user", "message": "Hi, I run a plumbing company..."}
  ],
  "recording_url": "https://..."
}
```

## Fallback: Twilio Status Callback

Also configure Twilio to send status callbacks as a fallback:

1. Go to Twilio Console → Phone Numbers → +18552399364
2. Under "Voice & Fax", add Status Callback URL:
   ```
   https://ai-phone.marceausolutions.com/webhook/twilio-status
   ```
3. This catches calls that ElevenLabs doesn't report

## Support

If ElevenLabs doesn't support webhooks in the dashboard, reach out to their support or we can implement API polling as a workaround.
