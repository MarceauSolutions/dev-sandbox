# AI Customer Service Virtual Employees

## Overview

AI-powered voice ordering system for independent restaurants, handling phone calls to take orders, answer questions, and reduce labor costs by 77-91%.

**Target Market**: Independent restaurants (1-10 locations), starting with pizzerias
**Pricing**: $149-399/month + usage overage
**Decision**: GO (4.15/5 market viability score)

---

## Capabilities

### SOP 1: Handle Inbound Phone Call

**Trigger**: Customer calls restaurant's AI phone number

**Flow**:
1. Twilio receives call → webhook to our server
2. Greet customer with restaurant-specific greeting
3. Transcribe customer speech (Deepgram/Whisper)
4. LLM processes intent → generate response
5. TTS speaks response (ElevenLabs/Cartesia)
6. Continue conversation until order complete or transfer needed
7. Log call, update analytics

**Edge Cases**:
- Customer wants human → Transfer to fallback number
- Unrecognized request → Politely clarify or transfer
- Menu question → Pull from restaurant's menu config
- Special instructions → Capture and include in order
- Multiple items → Handle iteratively with confirmation
- Connection issues → Graceful degradation, callback offer

**Success Metrics**:
- Call completion rate >85%
- Order accuracy >95%
- Average call duration <3 minutes
- Customer satisfaction >4.0/5

---

### SOP 2: Process Order to POS

**Trigger**: Order confirmed by customer on call

**Flow**:
1. Parse order items from conversation
2. Map to restaurant's menu items (SKUs)
3. Calculate totals with tax
4. Submit to POS (Toast/Square API)
5. Confirm order number to customer
6. Send SMS receipt (optional)

**Integrations**:
- Toast POS API
- Square POS API
- Clover (future)
- Custom webhook for others

**Edge Cases**:
- Item not in menu → Suggest alternatives
- POS unavailable → Queue order, notify staff
- Price mismatch → Use POS as source of truth
- Modifiers/customizations → Map to POS modifier codes

---

### SOP 3: Handle Menu Questions

**Trigger**: Customer asks about menu (ingredients, prices, availability)

**Flow**:
1. Identify question type (price, ingredient, availability, recommendation)
2. Query restaurant's menu data
3. Provide accurate, conversational response
4. Upsell if appropriate ("Would you like to add...")

**Data Sources**:
- Menu configuration (uploaded by restaurant)
- Real-time availability (from POS if supported)
- Allergen/dietary info (from menu config)

---

### SOP 4: Transfer to Human

**Trigger**: Customer requests human OR AI can't handle request

**Transfer Triggers**:
- Explicit request: "Let me talk to a person"
- Complaint/upset customer
- Complex modification AI can't parse
- 3+ failed understanding attempts
- Reservation/catering requests (configurable)

**Flow**:
1. Acknowledge transfer request
2. Brief hold message
3. Connect to restaurant's fallback number
4. If no answer → Offer callback, take message
5. Log transfer reason for analytics

---

### SOP 5: Analytics & Reporting

**Metrics Tracked**:
- Calls handled/day
- Completion rate
- Transfer rate (and reasons)
- Average call duration
- Revenue captured
- Peak call times
- Common menu items

**Reports**:
- Daily summary (email to owner)
- Weekly performance digest
- Monthly billing summary
- Custom date range exports

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Customer Service                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Voice Pipeline                      │  │
│  │  Phone → Twilio → STT → LLM → TTS → Twilio → Phone   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│           ┌───────────────┼───────────────┐                │
│           ▼               ▼               ▼                │
│     ┌──────────┐   ┌──────────┐   ┌──────────────┐        │
│     │  Menu    │   │  Order   │   │   Analytics  │        │
│     │  Config  │   │ Processor│   │    Engine    │        │
│     └──────────┘   └────┬─────┘   └──────────────┘        │
│                         │                                  │
│                    ┌────▼────┐                             │
│                    │   POS   │                             │
│                    │  APIs   │                             │
│                    └─────────┘                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   Dashboard (React)                         │
│  • Call history & transcripts                              │
│  • Menu configuration                                       │
│  • Analytics & reports                                      │
│  • Billing & settings                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

### Restaurant
```python
class Restaurant:
    id: str
    name: str
    phone_number: str  # Twilio number
    fallback_number: str  # Human transfer target
    timezone: str
    greeting_script: str
    menu_config: dict  # Structured menu data
    pos_integration: dict  # Toast/Square credentials
    billing: dict  # Stripe customer info
    settings: dict  # Features, hours, etc.
```

### Call
```python
class Call:
    id: str
    restaurant_id: str
    twilio_sid: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    status: str  # completed, transferred, abandoned
    transcript: list[dict]  # [{role, content, timestamp}]
    order_id: str | None
    transfer_reason: str | None
    cost_cents: int  # LLM + voice costs
```

### Order
```python
class Order:
    id: str
    call_id: str
    restaurant_id: str
    items: list[dict]  # [{name, quantity, modifiers, price}]
    subtotal: float
    tax: float
    total: float
    pos_order_id: str | None
    status: str  # pending, submitted, confirmed, failed
```

---

## Configuration

### Environment Variables
```bash
# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=  # Pool or per-restaurant

# LLM
ANTHROPIC_API_KEY=
OPENAI_API_KEY=  # Fallback

# Speech
DEEPGRAM_API_KEY=
ELEVENLABS_API_KEY=

# POS Integrations
TOAST_CLIENT_ID=
TOAST_CLIENT_SECRET=
SQUARE_ACCESS_TOKEN=

# Database
DATABASE_URL=

# Billing
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

### Per-Restaurant Config
```yaml
restaurant:
  name: "Mario's Pizzeria"
  greeting: "Thank you for calling Mario's Pizzeria! How can I help you today?"
  fallback_number: "+1-239-555-0123"
  timezone: "America/New_York"

  hours:
    monday: "11:00-22:00"
    tuesday: "11:00-22:00"
    # ...

  menu_url: "https://..."  # Or inline menu config

  transfer_triggers:
    - "catering"
    - "reservation"
    - "complaint"

  upsell_enabled: true
  sms_receipts: true
```

---

## Error Handling

| Error | Response | Logging |
|-------|----------|---------|
| STT fails | "I'm sorry, I didn't catch that. Could you repeat?" | Log audio quality metrics |
| LLM timeout | Retry once, then transfer | Log latency spike |
| POS unavailable | "Order received, staff will confirm shortly" | Alert restaurant, queue order |
| TTS fails | Use pre-recorded fallback | Log TTS error |
| Complete failure | Transfer to human with apology | Critical alert |

---

## Voice Tuning

### Latency Targets
- STT: <300ms
- LLM: <800ms (streaming)
- TTS: <200ms first byte
- **Total turn latency: <1.5s**

### Voice Quality
- Natural conversational tone
- Restaurant-appropriate energy
- Clear pronunciation of menu items
- Handle interruptions gracefully (barge-in)

### Prompting Guidelines
- Keep responses concise (1-2 sentences)
- Always confirm understanding
- Use customer's order terminology
- Apologize once for misunderstandings, not repeatedly

---

## Billing Model

### Tiers
| Tier | Monthly | Included Minutes | Overage |
|------|---------|------------------|---------|
| Starter | $149 | 500 | $0.20/min |
| Growth | $249 | 1,500 | $0.15/min |
| Pro | $399 | 4,000 | $0.10/min |
| Enterprise | Custom | Unlimited | - |

### Cost Breakdown (per minute)
- Twilio voice: ~$0.02
- STT (Deepgram): ~$0.01
- LLM (Claude): ~$0.02-0.05
- TTS (ElevenLabs): ~$0.01
- **Total COGS: ~$0.06-0.09/min**
- **Gross margin: 70-80%**

---

## Development Phases

### Phase 1: Voice Engine MVP (Weeks 1-4)
- [ ] Twilio voice webhook integration
- [ ] Basic STT → LLM → TTS pipeline
- [ ] Simple order-taking flow
- [ ] Call logging and transcripts
- [ ] Single restaurant test (internal)

### Phase 2: Restaurant Dashboard (Weeks 5-8)
- [ ] FastAPI backend with auth
- [ ] Menu configuration UI
- [ ] Call history and transcripts
- [ ] Basic analytics
- [ ] Stripe billing integration

### Phase 3: POS Integrations (Weeks 9-12)
- [ ] Toast POS integration
- [ ] Square POS integration
- [ ] Order submission flow
- [ ] Real-time availability sync

### Phase 4: Beta Launch (Weeks 13-16)
- [ ] 10 Naples pizzerias onboarded
- [ ] Performance optimization
- [ ] Customer feedback loop
- [ ] Case study development

---

## Success Criteria

### MVP (Phase 1)
- [ ] Complete a phone order end-to-end
- [ ] Latency <2s per turn
- [ ] 80%+ call completion rate

### Beta (Phase 4)
- [ ] 10 restaurants active
- [ ] 85%+ completion rate
- [ ] <5% transfer rate
- [ ] 3 documented ROI case studies

### Scale (Year 1)
- [ ] 100 restaurants
- [ ] $25K MRR
- [ ] <4% monthly churn
- [ ] NPS >40

---

## References

- [Market Analysis](../projects/ai-customer-service/market-analysis/)
- [KICKOFF.md](../projects/ai-customer-service/KICKOFF.md)
- [Twilio Voice Docs](https://www.twilio.com/docs/voice)
- [Deepgram Streaming](https://developers.deepgram.com/docs/streaming)
- [Toast API](https://doc.toasttab.com/)
