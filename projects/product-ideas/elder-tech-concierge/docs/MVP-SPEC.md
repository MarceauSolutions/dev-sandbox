# MVP Specification: Elder Tech Concierge

**Version:** 0.1.0
**Created:** 2026-01-16
**Status:** Planning

---

## Executive Summary

The Elder Tech Concierge MVP delivers a voice-first AI assistant on iPad that enables seniors to stay connected with family, manage appointments, and receive medication reminders - all through natural conversation.

**MVP Goal:** Validate product-market fit with 10 beta customers in Month 2-3.

---

## Phase 1 Features (Weeks 1-8)

### Core Capabilities

#### 1. Voice Interface (P0 - Critical)

**User Story:** As a senior, I want to talk to my assistant naturally so I don't have to type or tap small buttons.

**Acceptance Criteria:**
- [ ] Wake word activation ("Hey Concierge" or tap-to-talk)
- [ ] Voice recognition accuracy >90% for elderly voices
- [ ] Response time <3 seconds
- [ ] Natural voice output (not robotic)
- [ ] Visual confirmation of what was heard
- [ ] Large "Cancel" button always visible

**Technical Implementation:**
- Speech-to-Text: Apple Speech Framework (on-device) + Whisper API (fallback)
- Text-to-Speech: Apple AVSpeechSynthesizer (default) + ElevenLabs (premium)
- Processing: Claude API (claude-3-5-sonnet)

**UI Mockup:**
```
+------------------------------------------+
|                                          |
|     [ Large Microphone Button ]          |
|                                          |
|   "Listening..."                         |
|                                          |
|   +---------------------------------+    |
|   | "What did you hear?"            |    |
|   | "Call my daughter Sarah"        |    |
|   +---------------------------------+    |
|                                          |
|   [ Cancel ]          [ Send ]           |
|                                          |
+------------------------------------------+
```

---

#### 2. Send Text Message (P0 - Critical)

**User Story:** As a senior, I want to text my family members by just saying their name so I can stay in touch without typing.

**Acceptance Criteria:**
- [ ] "Text my daughter" triggers contact selection
- [ ] Voice dictation for message content
- [ ] Read-back message before sending
- [ ] Confirmation: "Your message was sent to Sarah"
- [ ] Contact nicknames supported ("my daughter", "Grandkids", "Dr. Smith")

**Technical Implementation:**
- Backend: `execution/twilio_sms.py` (existing)
- Contact storage: PostgreSQL (name, phone, nickname, relationship)
- Claude: Parse intent and extract contact reference

**Example Flow:**
```
Senior: "Send a text to my daughter"
AI: "What would you like to say to Sarah?"
Senior: "Tell her I'm feeling great today and I love her"
AI: "I'll send this to Sarah: 'I'm feeling great today and I love you.' Should I send it?"
Senior: "Yes"
AI: "Done! Your message was sent to Sarah."
```

---

#### 3. Read Emails (P0 - Critical)

**User Story:** As a senior, I want my assistant to read my important emails out loud so I don't have to squint at small text.

**Acceptance Criteria:**
- [ ] Filter to important emails (not spam/promotions)
- [ ] Summarize sender and subject before reading
- [ ] Option to hear full email or summary
- [ ] "Next email" / "Previous email" navigation
- [ ] "Reply to this email" integration

**Technical Implementation:**
- Backend: `execution/gmail_monitor.py` (existing)
- Claude: Summarize and prioritize emails
- Categories: Family, Health/Medical, Financial, Other

**Example Flow:**
```
Senior: "Do I have any new emails?"
AI: "You have 3 new emails. One from your doctor's office about your appointment,
     one from your grandson Tommy, and one from your bank.
     Would you like me to read the one from Tommy first?"
Senior: "Yes, read Tommy's email"
AI: "Tommy wrote: 'Hi Grandpa! I got an A on my science test!
     Can we have ice cream this weekend? Love, Tommy'"
Senior: "That's wonderful! Reply and say I'm so proud"
AI: "I'll reply: 'I'm so proud of you Tommy! Ice cream this weekend sounds great.'
     Should I send it?"
```

---

#### 4. Set Reminders (P0 - Critical)

**User Story:** As a senior, I want to set reminders by talking so I don't forget important things.

**Acceptance Criteria:**
- [ ] Natural language time parsing ("tomorrow at 2pm", "every morning at 8")
- [ ] Confirmation of reminder details
- [ ] Audio + visual notification when reminder fires
- [ ] Repeat reminders until acknowledged
- [ ] Snooze option ("remind me in 10 minutes")

**Technical Implementation:**
- Backend: `execution/calendar_reminders.py` (existing)
- Local notifications: iOS push notification system
- Persistence: Local storage + cloud sync

**Example Flow:**
```
Senior: "Remind me to take my blood pressure medicine tomorrow at 9am"
AI: "I'll remind you tomorrow, January 17th at 9am, to take your blood pressure medicine.
     Should I make this a daily reminder?"
Senior: "Yes, every day at 9am"
AI: "Done! I'll remind you every day at 9am to take your blood pressure medicine."
```

---

#### 5. Emergency Contact (P0 - Critical)

**User Story:** As a senior, I want a big red emergency button so I can quickly reach help if I need it.

**Acceptance Criteria:**
- [ ] Large, always-visible emergency button (red, minimum 80x80 pt)
- [ ] One tap sends alert to family + optional 911
- [ ] Location shared with family
- [ ] "I'm okay" false alarm cancellation within 30 seconds
- [ ] Confirmation call initiated to primary contact

**Technical Implementation:**
- SMS: Twilio to all emergency contacts simultaneously
- Optional: Integration with existing medical alert services
- Future: Fall detection via device accelerometer

**Emergency Button UI:**
```
+------------------------------------------+
|                                          |
|  +------------------------------------+  |
|  |                                    |  |
|  |        EMERGENCY                   |  |
|  |        Tap for Help                |  |
|  |                                    |  |
|  +------------------------------------+  |
|                                          |
+------------------------------------------+
```

---

#### 6. Quick Action Buttons (P1 - Important)

**User Story:** As a senior, I want big buttons for common tasks so I don't have to remember what to say.

**Acceptance Criteria:**
- [ ] Home screen with 4-6 large buttons
- [ ] Buttons configurable per user
- [ ] Icons + text labels (high contrast)
- [ ] Minimum touch target: 64x64 pt

**Default Quick Actions:**
1. "Call Family" - Speed dial primary contact
2. "Send Text" - Open text message flow
3. "Read Emails" - Check new emails
4. "My Calendar" - Today's events
5. "Weather" - Local weather briefing
6. "Emergency" - Emergency contact button

**Home Screen Layout:**
```
+------------------------------------------+
|  Elder Tech Concierge    [Settings]      |
|------------------------------------------|
|                                          |
|  +----------------+  +----------------+  |
|  |   [Phone]      |  |   [Message]    |  |
|  |   Call         |  |   Send         |  |
|  |   Family       |  |   Text         |  |
|  +----------------+  +----------------+  |
|                                          |
|  +----------------+  +----------------+  |
|  |   [Mail]       |  |   [Calendar]   |  |
|  |   Read         |  |   My           |  |
|  |   Emails       |  |   Calendar     |  |
|  +----------------+  +----------------+  |
|                                          |
|  +----------------+  +----------------+  |
|  |   [Sun]        |  |   [!!!]        |  |
|  |   Weather      |  |   Emergency    |  |
|  |   Today        |  |                |  |
|  +----------------+  +----------------+  |
|                                          |
|  +------------------------------------+  |
|  |         [ Tap to Talk ]            |  |
|  +------------------------------------+  |
|                                          |
+------------------------------------------+
```

---

### Phase 1 User Stories Summary

| ID | User Story | Priority | Complexity | Sprint |
|----|-----------|----------|------------|--------|
| US-01 | Voice interface (speak to assistant) | P0 | High | 1-2 |
| US-02 | Send text message to family | P0 | Low | 2 |
| US-03 | Read and reply to emails | P0 | Medium | 3 |
| US-04 | Set and receive reminders | P0 | Medium | 3-4 |
| US-05 | Emergency contact button | P0 | Low | 2 |
| US-06 | Quick action home screen | P1 | Medium | 4 |
| US-07 | Contact management (with nicknames) | P1 | Low | 2 |
| US-08 | Settings (volume, text size, voice) | P1 | Low | 5 |

---

## Phase 2 Features (Weeks 9-12)

### Enhanced Capabilities

#### 7. Calendar Integration (P1)

**User Story:** As a senior, I want my assistant to tell me about upcoming appointments so I don't miss them.

**Features:**
- View today's/week's events
- Add events via voice
- Smart reminders (travel time, prep time)
- Sync with family calendar

---

#### 8. Semi-Automated Appointment Booking (P1)

**User Story:** As a senior, I want help scheduling doctor appointments without navigating confusing phone trees.

**Phase 2 Implementation (MVP):**
- AI drafts appointment request email to doctor's office
- User confirms before sending
- AI monitors for response
- Creates calendar event when confirmed

**Future (Phase 3+):**
- Direct integration with Calendly/Acuity-based practices
- FHIR integration with Epic MyChart

---

#### 9. Family Notifications (P1)

**User Story:** As a family member, I want to receive alerts about my parent so I know they're safe.

**Notification Types:**
- Daily "all is well" check (senior confirms they're okay)
- Missed medication reminder (not acknowledged)
- Emergency alert
- Weekly activity summary

**Family Dashboard (web):**
- View parent's calendar
- See recent activity
- Add reminders remotely
- Receive push notifications

---

#### 10. Medication Reminders (P2)

**User Story:** As a senior, I want reminders to take my medications so I stay healthy.

**Features:**
- Multiple medication schedules
- Photo confirmation option
- Refill reminders
- Missed dose alerts to family

---

## Phase 3 Features (Weeks 13-14+)

### Advanced Capabilities (Post-MVP)

| Feature | Description | Complexity |
|---------|-------------|------------|
| Weather briefing | Daily weather + clothing suggestions | Low |
| News summary | Customized news digest read aloud | Low |
| Video calling | Initiate FaceTime/Zoom to family | Medium |
| Shopping list | Voice-managed shared grocery list | Low |
| Smart home | Control lights, thermostat via voice | Medium |
| Healthcare booking | Direct integration with providers | High |
| Fall detection | Device accelerometer monitoring | High |
| Activity insights | Pattern analysis for family | High |

---

## Technical Architecture

### System Diagram

```
+------------------+          +------------------+          +------------------+
|                  |  HTTPS   |                  |  HTTPS   |                  |
|   iPad App       |<-------->|   Backend API    |<-------->|   Claude API     |
|   (SwiftUI)      |          |   (FastAPI)      |          |   (Anthropic)    |
|                  |          |                  |          |                  |
+------------------+          +--------+---------+          +------------------+
       |                               |
       | On-device                     | API calls
       v                               v
+------------------+          +------------------+          +------------------+
|  Apple Speech    |          |   PostgreSQL     |          |   Twilio         |
|  Framework       |          |   (Supabase)     |          |   SMS            |
+------------------+          +------------------+          +------------------+
                                       |
                                       v
                              +------------------+          +------------------+
                              |   Gmail API      |          |   Google         |
                              |   (Read/Send)    |          |   Calendar       |
                              +------------------+          +------------------+
```

### API Endpoints (Backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Send user message to Claude |
| `/api/v1/contacts` | GET/POST | Manage user contacts |
| `/api/v1/reminders` | GET/POST/DELETE | Manage reminders |
| `/api/v1/emails` | GET | Fetch and summarize emails |
| `/api/v1/emails/{id}/reply` | POST | Reply to email |
| `/api/v1/sms/send` | POST | Send SMS via Twilio |
| `/api/v1/calendar/events` | GET/POST | Calendar management |
| `/api/v1/emergency` | POST | Trigger emergency alert |
| `/api/v1/family/notifications` | POST | Send family notification |

### Data Models

**User**
```python
class User:
    id: UUID
    name: str
    phone: str
    email: str
    timezone: str
    created_at: datetime
    settings: dict  # volume, text_size, voice_preference
```

**Contact**
```python
class Contact:
    id: UUID
    user_id: UUID
    name: str
    phone: str
    email: str
    relationship: str  # daughter, son, doctor, friend
    nicknames: list[str]  # ["my daughter", "Sarah", "sweetie"]
    is_emergency: bool
    priority: int  # 1 = primary, 2 = secondary
```

**Reminder**
```python
class Reminder:
    id: UUID
    user_id: UUID
    title: str
    description: str
    scheduled_at: datetime
    repeat: str  # none, daily, weekly, monthly
    acknowledged: bool
    created_at: datetime
```

---

## Accessibility Requirements

### Visual

| Requirement | Standard | Our Target |
|-------------|----------|------------|
| Minimum text size | 16pt | 24pt+ |
| Touch target | 44x44 pt | 64x64 pt |
| Contrast ratio | 4.5:1 | 7:1+ |
| Color blindness | Consider | Full support |

### Auditory

- All text readable aloud
- Adjustable speech rate (slow/normal/fast)
- Volume boost option
- Visual confirmation of all audio

### Cognitive

- Maximum 3 steps per task
- Always-visible "Home" button
- Clear "Cancel" option on every screen
- No timeouts that lose work
- Consistent navigation patterns

---

## Testing Plan

### Beta Testing (10 Users)

**Selection Criteria:**
- Age 68-78 (sweet spot for adoption)
- Has smartphone but underuses it
- Family member willing to assist with setup
- In local metro area

**Testing Protocol:**
1. **Week 1:** In-home setup, basic training
2. **Week 2:** Daily check-ins, collect feedback
3. **Week 3:** Reduced support, monitor usage patterns
4. **Week 4:** Exit interview, NPS survey

**Success Metrics:**
- Setup time < 3 hours
- 80% of users active daily
- NPS > 50
- 3+ organic referrals
- Support < 2 hours/user/month

---

## Cost Estimates

### Development (One-Time)

| Component | Hours | Notes |
|-----------|-------|-------|
| iOS App (SwiftUI) | 80-100 | Voice interface, UI |
| Backend API (FastAPI) | 40-60 | Endpoints, integrations |
| Integration Layer | 20-30 | Twilio, Gmail, Calendar |
| Testing & QA | 20-40 | Accessibility audit |
| **Total** | **160-230** | 8-12 weeks |

### Operational (Monthly per User)

| Service | Cost |
|---------|------|
| Claude API | $5-15 |
| Twilio SMS | $0.50-2 |
| Hosting | $2-5 |
| Push notifications | $0-1 |
| **Total** | **$8-23** |

### Pricing vs Cost

| Tier | Price | Cost | Margin |
|------|-------|------|--------|
| Essential ($49/mo) | $49 | $12 | 75% |
| Premium ($99/mo) | $99 | $18 | 82% |

---

## Launch Checklist

### Pre-Beta (Week 7)
- [ ] Core voice interface working
- [ ] SMS sending functional
- [ ] Email reading functional
- [ ] Reminder system functional
- [ ] Emergency button functional
- [ ] Home screen with quick actions
- [ ] Basic settings (volume, text size)

### Beta Launch (Week 8)
- [ ] 10 beta users identified
- [ ] Setup documentation complete
- [ ] Support procedures defined
- [ ] Feedback collection system ready
- [ ] Family notification system working

### Full Launch (Week 14)
- [ ] 10 beta users validated
- [ ] NPS > 50
- [ ] 5+ testimonials collected
- [ ] Pricing confirmed
- [ ] Marketing materials ready
- [ ] Referral program defined

---

## Appendix: Competitor Feature Matrix

| Feature | Elder Tech | GrandPad | Geek Squad | ElliQ |
|---------|------------|----------|------------|-------|
| Voice-first interface | Yes | No | No | Yes |
| Claude AI backend | Yes | No | No | Proprietary |
| In-home setup | Yes | Mail | Store visit | Mail |
| Ongoing support | Yes | Yes | Subscription | Yes |
| Family dashboard | Yes | Yes | No | Yes |
| Custom automations | Yes | No | No | Limited |
| SMS integration | Yes | Yes | No | No |
| Email management | Yes | Yes | No | No |
| Price (monthly) | $49-99 | $79 | $200/yr | $39 |

---

*Specification created: 2026-01-16*
*Last updated: 2026-01-16*
*Status: Ready for development*
