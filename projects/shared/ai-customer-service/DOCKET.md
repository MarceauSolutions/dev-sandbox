# AI Customer Service - Docket

*Deferred features and future work with trigger conditions*

---

## Pending Items

### 1. Stripe Payment Integration
- **Description**: Connect Stripe for payment processing on phone orders
- **Trigger Condition**: First paying restaurant customer OR restaurant MVP deployed
- **Priority**: High
- **Related Files**: `src/models.py` (Order model has payment fields ready)
- **Notes**: Can collect card over phone via Twilio Pay or send payment link via SMS

### 2. POS Integration (Toast, Square)
- **Description**: Connect to restaurant POS systems for order submission
- **Trigger Condition**: Restaurant onboarded with known POS system
- **Priority**: High
- **Related Files**: `src/models.py` (Restaurant has pos_type, pos_config fields)
- **Notes**: Toast and Square both have APIs for order injection

### 3. Call Recording & Analytics
- **Description**: Store call recordings, analyze for quality, track metrics
- **Trigger Condition**: 100+ calls completed OR first production deployment
- **Priority**: Medium
- **Related Files**: Twilio recording settings in `twilio_handler.py`
- **Notes**: Twilio charges extra for recording storage

### 4. SMS Follow-up After Calls
- **Description**: Send SMS with order confirmation, payment link, or callback scheduling
- **Trigger Condition**: First successful order completion
- **Priority**: Medium
- **Related Files**: Could use existing SMS infrastructure from lead-scraper
- **Notes**: Cross-project integration opportunity

### 5. Multi-Language Support
- **Description**: Support Spanish and other languages for voice AI
- **Trigger Condition**: Non-English customer request OR Hispanic market targeting
- **Priority**: Low
- **Related Files**: `voice_engine.py` system prompts, Twilio language settings
- **Notes**: Polly has Spanish neural voices available

### 6. Voicemail Detection & Handling
- **Description**: Detect voicemail, leave message, retry later
- **Trigger Condition**: Outreach campaign with >30% no-answer rate
- **Priority**: Medium
- **Related Files**: `scripts/outreach_call.py`, `twilio_handler.py`
- **Notes**: Twilio has AMD (Answering Machine Detection) feature

### 7. CRM Integration (ClickUp)
- **Description**: Auto-create leads/tasks from outreach calls with outcomes
- **Trigger Condition**: 10+ outreach calls completed
- **Priority**: High
- **Related Files**: Can use existing ClickUp integration from lead-scraper
- **Notes**: Track interested leads, schedule follow-ups

### 8. SSML Voice Styling (Re-attempt)
- **Description**: Add emotional prosody via SSML for more natural voice
- **Trigger Condition**: Plain text voice quality feedback OR competitor analysis
- **Priority**: Low
- **Related Files**: `voice_styles.py` (created but disabled due to parsing issues)
- **Notes**: Need to properly test SSML with Polly neural voices

### 9. Lead Enrichment Pipeline Integration
- **Description**: Auto-research leads before outreach calls
- **Trigger Condition**: Batch outreach campaign >20 leads
- **Priority**: Medium
- **Related Files**: `src/lead_enrichment.py`, Apollo/LinkedIn integration
- **Notes**: Pre-populate person_context from enrichment data

### 10. Call Scheduling System
- **Description**: Schedule outreach calls for optimal times, manage callbacks
- **Trigger Condition**: Callback requested during call OR timezone optimization needed
- **Priority**: Medium
- **Related Files**: Could integrate with Google Calendar
- **Notes**: Respect business hours, timezone awareness

---

## Completed Items

*(Move items here when done)*

---

## How to Use This Docket

1. **Add items** when features are identified but deferred
2. **Check triggers** at start of each session
3. **Promote to active work** when trigger conditions are met
4. **Move to completed** when done

*Last Updated: 2026-01-18*
