# Voice AI System Architecture

**Last Updated:** 2026-01-19

This document explains how the Voice AI system works for both SW Florida Comfort HVAC and Square Foot Shipping.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer Calls                           │
│  HVAC: +1 239-766-6129  OR  Shipping: +1 239-880-3365      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                     Twilio Voice API                         │
│  - Receives call                                             │
│  - Identifies which number was called ("To" field)           │
│  - Makes webhook request to server                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                     ngrok Tunnel (Dev)                       │
│  https://abc123.ngrok-free.app                              │
│  → Forwards to localhost:8000                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (src/main.py)                    │
│  - POST /twilio/voice  (incoming calls)                      │
│  - POST /api/form/submit  (website forms)                    │
│  - GET /health  (system status)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│          Twilio Handler (src/twilio_handler.py)              │
│  - Extracts "To" phone number from request                   │
│  - Routes to correct business                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                v                 v
┌──────────────────────┐  ┌──────────────────────┐
│   HVAC Business      │  │  Shipping Business   │
│ swflorida_hvac.py    │  │ squarefoot_shipping.py│
│                      │  │                      │
│ - Greeting           │  │ - Greeting           │
│ - Services list      │  │ - Services list      │
│ - System prompt      │  │ - System prompt      │
│ - Owner: Bill Sr.    │  │ - Owner: William G.  │
│ - Type: HVAC         │  │ - Type: Logistics    │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           └────────┬────────────────┘
                    v
┌─────────────────────────────────────────────────────────────┐
│     Business Voice Engine (src/business_voice_engine.py)     │
│                                                              │
│  1. Play greeting (from business config)                     │
│  2. Start conversation loop:                                 │
│     a. Listen to customer (Deepgram STT)                     │
│     b. Send to Claude (with business context)                │
│     c. Get AI response                                       │
│     d. Speak response (ElevenLabs TTS)                       │
│     e. Repeat until call ends                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Twilio Voice API

**What it does:**
- Receives phone calls to the two numbers
- Captures audio from caller
- Sends webhook to our server: `POST /twilio/voice`
- Includes metadata: `To` number, `From` number, `CallSid`

**Configuration:**
- Managed via: `scripts/configure_twilio.py`
- Console: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

### 2. ngrok Tunnel (Development)

**What it does:**
- Creates a public HTTPS URL (e.g., `https://abc123.ngrok-free.app`)
- Forwards all traffic to `localhost:8000`
- Allows Twilio to reach local server

**Why needed:**
- Twilio webhooks require HTTPS
- Local dev server is HTTP only
- ngrok provides the HTTPS layer

**Limitations:**
- Free tier URL changes on restart
- Must reconfigure Twilio when URL changes
- Not suitable for production (use real server)

**Production alternative:**
- Deploy to DigitalOcean/Heroku/Railway
- Point `api.marceausolutions.com` to server
- Set Twilio webhooks to permanent URL

### 3. FastAPI Server

**Entry point:** `src/main.py`

**Endpoints:**

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | API info |
| `/health` | GET | System health check |
| `/twilio/voice` | POST | Handle incoming calls |
| `/api/form/submit` | POST | Handle website form submissions |

**Middleware:**
- CORS enabled for website forms
- Handles multiple origins (marceausolutions.com, swfloridacomfort.com, etc.)

### 4. Business Router

**File:** `src/twilio_handler.py`

**Logic:**

```python
# Twilio sends: {"To": "+12397666129", "From": "+1234567890", ...}

if request.To == "+12397666129":
    load_business_config("swflorida_hvac")
elif request.To == "+12398803365":
    load_business_config("squarefoot_shipping")
else:
    return "Unknown number"
```

**Why this works:**
- One server handles multiple businesses
- No manual switching needed
- Automatic routing based on called number

### 5. Business Configuration Files

**HVAC:** `businesses/swflorida_hvac.py`

```python
BUSINESS_CONFIG = {
    "name": "SW Florida Comfort HVAC",
    "phone": "+12397666129",
    "owner": "William Marceau Sr.",
    "type": "hvac",
    "greeting": "Thank you for calling SW Florida Comfort HVAC!...",
    "services": [...],
    "service_areas": ["Naples", "Fort Myers", ...],
    "hours": "Office: 8am-5pm Mon-Fri | Emergency: 24/7"
}

SYSTEM_PROMPT = """
You are an AI assistant for SW Florida Comfort HVAC...
[Detailed instructions for handling HVAC calls]
"""
```

**Shipping:** `businesses/squarefoot_shipping.py`

```python
BUSINESS_CONFIG = {
    "name": "Square Foot Shipping & Storage",
    "phone": "+12398803365",
    "owner": "William George",
    "type": "logistics",
    "greeting": "Thank you for calling Square Foot Shipping...",
    "services": [...],
    "hours": "Monday-Friday 8am-6pm, Saturday 9am-1pm"
}

SYSTEM_PROMPT = """
You are an AI assistant for Square Foot Shipping & Storage...
[Detailed instructions for handling shipping calls]
"""
```

### 6. Business Voice Engine

**File:** `src/business_voice_engine.py`

**Conversation Loop:**

```python
1. Play greeting (TwiML <Say>)
2. Start gathering input (<Gather>)
3. Customer speaks
4. Deepgram transcribes audio → text
5. Send text + business context to Claude
6. Claude generates response (aware of business type, services, etc.)
7. ElevenLabs converts response → speech
8. Play speech to customer (<Say>)
9. Repeat steps 3-8 until call ends
```

**AI Context Injection:**

Each Claude request includes:
- **Business name**
- **Services offered**
- **Pricing information**
- **Owner name**
- **Business type** (HVAC vs Logistics)
- **Conversation history** (previous turns)

This ensures Claude responds appropriately for each business.

---

## Data Flow Example

**Scenario: Customer calls HVAC number**

```
1. Customer dials: +1 239-766-6129

2. Twilio receives call, makes webhook request:
   POST https://abc123.ngrok-free.app/twilio/voice
   Body: {
     "To": "+12397666129",
     "From": "+15551234567",
     "CallSid": "CA123..."
   }

3. ngrok forwards to: localhost:8000/twilio/voice

4. FastAPI routes to twilio_handler.py

5. twilio_handler.py detects:
   To = "+12397666129" → Load swflorida_hvac.py config

6. business_voice_engine.py starts conversation:
   - Play greeting: "Thank you for calling SW Florida Comfort HVAC!"
   - Wait for customer to speak

7. Customer says: "My AC is out"

8. Deepgram transcribes: "My AC is out"

9. Send to Claude:
   System: [HVAC system prompt from swflorida_hvac.py]
   User: "My AC is out"

10. Claude responds: "I understand - losing AC in Florida is no joke.
    Let me get a technician heading your way. What's your address?"

11. ElevenLabs converts to speech (Rachel voice)

12. Play audio to customer via Twilio

13. Repeat steps 7-12 until call ends
```

---

## Environment Configuration

**File:** `src/config.py`

**Loads from:** `/Users/williammarceaujr./dev-sandbox/.env`

**Required variables:**

```bash
# Twilio (receives calls, manages phone calls)
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=xxxx...
TWILIO_PHONE_NUMBER=+18552399364  # Outbound caller ID

# Anthropic (Claude AI for responses)
ANTHROPIC_API_KEY=sk-ant-...

# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=xxxx...

# ElevenLabs (Text-to-Speech)
ELEVENLABS_API_KEY=xxxx...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel
```

**How it works:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    twilio_account_sid: str = ""
    anthropic_api_key: str = ""
    # ... etc

    class Config:
        env_file = "/Users/williammarceaujr./dev-sandbox/.env"
```

All components import `get_settings()` to access credentials.

---

## Multi-Business Architecture Benefits

**Why this design?**

1. **Single server, multiple businesses** - No duplicate infrastructure
2. **Shared AI capabilities** - Both benefit from same Claude/Deepgram/ElevenLabs
3. **Business-specific behavior** - Each has its own greeting, services, tone
4. **Easy to add more businesses** - Just create `businesses/new_business.py`
5. **Centralized monitoring** - One place to view all call logs

**Scaling:**

To add a third business (e.g., "Naples Restaurant Delivery"):

1. Get Twilio phone number: +1 239-XXX-XXXX
2. Create: `businesses/naples_delivery.py`
3. Add routing in `twilio_handler.py`:
   ```python
   elif request.To == "+1239XXXXXXX":
       load_business_config("naples_delivery")
   ```
4. Configure Twilio webhook
5. Done!

---

## Production Deployment Roadmap

**Current State:** Development (ngrok tunnel)

**Production Steps:**

1. **Deploy server to cloud:**
   - DigitalOcean Droplet ($4/mo)
   - OR Heroku (free tier available)
   - OR Railway (pay-per-use)

2. **Set up domain:**
   - Point `api.marceausolutions.com` to server IP
   - Add SSL certificate (Let's Encrypt free)

3. **Update Twilio webhooks:**
   - Change from `https://abc123.ngrok-free.app/twilio/voice`
   - To: `https://api.marceausolutions.com/twilio/voice`

4. **Set up monitoring:**
   - Sentry for error tracking
   - Uptime monitoring (Pingdom/UptimeRobot)
   - Call analytics dashboard

5. **Database for call logs:**
   - SQLite → PostgreSQL
   - Store: CallSid, duration, transcripts, outcomes

6. **Backup/failover:**
   - Twilio fallback URL (if main server down)
   - Load balancing (if high call volume)

---

## Testing & Debugging

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**

```json
{
  "status": "healthy",
  "services": {
    "voice_ai": {
      "twilio_configured": true,
      "anthropic_configured": true,
      "deepgram_configured": true
    },
    "forms": {
      "enabled": true,
      "endpoint": "/api/form/submit"
    }
  }
}
```

### Test 2: Business Config Loading

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/ai-customer-service

python -c "
from businesses.swflorida_hvac import BUSINESS_CONFIG
print(BUSINESS_CONFIG['name'])
print(BUSINESS_CONFIG['phone'])
"
```

**Expected:**

```
SW Florida Comfort HVAC
+12397666129
```

### Test 3: Make a Real Call

1. Start server: `python scripts/start_server.py`
2. Configure Twilio: `python scripts/configure_twilio.py --ngrok-url <URL>`
3. Call from phone: +1 239-766-6129
4. Speak to AI: "My AC is broken"
5. Check logs: `tail -f /tmp/server.log`

### Test 4: View Call Logs

```bash
python scripts/check_call_logs.py
```

Shows recent calls with: Duration, From, To, Status

---

## Cost Breakdown

**Per-minute costs:**

| Service | Cost | Example (5 min call) |
|---------|------|----------------------|
| Twilio Voice | $0.0085/min | $0.04 |
| Deepgram STT | $0.0043/min | $0.02 |
| Anthropic Claude | ~$0.01/call | $0.01 |
| ElevenLabs TTS | ~$0.05/call | $0.05 |
| **Total** | **~$0.12/call** | **$0.12** |

**Monthly estimates (100 calls/mo, 5 min avg):**
- **Total call cost:** ~$12/month
- **Server (ngrok paid or DigitalOcean):** $4-12/month
- **Total monthly:** ~$16-24/month

**Compare to:**
- Virtual receptionist: $400-800/month
- In-house receptionist: $2,500+/month

**ROI:** 95%+ cost savings

---

## Security Considerations

**Current safeguards:**

1. **Webhook validation** - Twilio requests include signature we verify
2. **CORS restrictions** - Only allowed origins can submit forms
3. **Environment variables** - Credentials not hardcoded
4. **HTTPS only** - ngrok/production both use SSL

**Production additions needed:**

1. **Rate limiting** - Prevent abuse (X calls per minute)
2. **Authentication** - API keys for admin endpoints
3. **Audit logging** - Track all calls, transcripts, outcomes
4. **PII handling** - Encrypt customer data at rest
5. **Compliance** - TCPA (call recording consent), GDPR if applicable

---

## Maintenance

**Daily:**
- Check call logs for errors
- Monitor Twilio balance

**Weekly:**
- Review call transcripts for AI improvements
- Check ngrok tunnel still active (dev mode)

**Monthly:**
- Review costs (Twilio + AI services)
- Update business configs if services/pricing changes
- Test both phone numbers

**Quarterly:**
- Evaluate AI performance (% of calls requiring human)
- Consider moving to production if volume high

---

## Troubleshooting Guide

### Issue: Calls go straight to voicemail

**Cause:** Twilio webhook not configured or server down

**Fix:**
1. Check server: `curl http://localhost:8000/health`
2. Check ngrok: `curl http://localhost:4040/api/tunnels`
3. Reconfigure Twilio: `python scripts/configure_twilio.py --ngrok-url <URL>`

### Issue: AI doesn't respond / call drops

**Cause:** Missing API keys or service down

**Fix:**
1. Check health endpoint: `curl http://localhost:8000/health`
2. Verify all services show `true`
3. Check logs: `tail -f /tmp/server.log`
4. Test individual services:
   - Deepgram: https://console.deepgram.com/
   - Anthropic: https://console.anthropic.com/
   - ElevenLabs: https://elevenlabs.io/app/speech-synthesis

### Issue: Wrong business greeting plays

**Cause:** Routing logic error

**Fix:**
1. Check logs: `tail -f /tmp/server.log`
2. Verify "To" number matches business config:
   - HVAC: +12397666129
   - Shipping: +12398803365
3. Review `src/twilio_handler.py` routing logic

### Issue: Server won't start (port in use)

**Fix:**

```bash
lsof -ti:8000 | xargs kill -9
python scripts/start_server.py
```

---

## Next Steps

1. ✅ **Start server:** See `SERVER-STARTUP.md`
2. ✅ **Test calls:** Call both numbers
3. ✅ **Monitor performance:** Check logs after 10-20 calls
4. ⏳ **Production deployment:** When ready, deploy to cloud
5. ⏳ **Analytics dashboard:** Build call analytics UI
6. ⏳ **CRM integration:** Connect to ClickUp for lead tracking

---

**Last Updated:** 2026-01-19
**Status:** ✅ Operational (dev mode)
