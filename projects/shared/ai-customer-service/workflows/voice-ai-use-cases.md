# Voice AI Appropriate Use Cases

## The Trust Principle

**AI voice works when it SERVES the caller. It destroys trust when it SELLS to them.**

People don't mind AI when:
- It's helping them get what they want faster
- It's handling routine tasks they don't want to do
- It's clearly identified as AI (no deception)

People hate AI when:
- It's trying to sell them something
- It's wasting their time gathering data
- It's pretending to be human

---

## Use Case Matrix

| Use Case | AI Role | Human Role | Trust Impact |
|----------|---------|------------|--------------|
| **Inbound Receptionist** | Fast-qualify, route to human | Take the actual call | HIGH - caller gets faster service |
| **Restaurant Ordering** | Take orders, handle routine | Handle special requests | HIGH - clear task, no selling |
| **Appointment Confirmation** | "Confirming your 2pm call" | Take the confirmed call | MEDIUM - brief, functional |
| **Cold Outreach** | **DON'T USE** | Human makes initial contact | **DESTROYS TRUST** |
| **Warm Follow-up** | Maybe - depends on context | Human handles relationship | MEDIUM - use carefully |

---

## Implemented Engines

### 1. InboundAssistantEngine (Fast Qualifier)

**Purpose**: Route inbound calls to William FAST

**Flow**:
1. Greeting: "Hi, you've reached William Marceau's office. How can I help you?"
2. Listen for qualification signals
3. Hot lead? → TRANSFER IMMEDIATELY
4. Sales call? → Politely end
5. Message? → Take brief message

**Qualification Signals** (transfer immediately):
- Mentions AI, automation, tech help
- Calling about a project
- Wants to discuss services/pricing
- Sounds like a business owner with a problem
- Specifically asked for William

**Non-Leads** (take message or end):
- Vendors selling something
- Spam/robocalls
- Wrong numbers

**Key principle**: Bias toward transferring. Better to take a borderline call than miss an opportunity.

### 2. WarmFollowUpEngine (Confirmation Only)

**Purpose**: Confirm scheduled calls, then transfer

**Flow**:
1. "Hi {name}, this is William's office confirming your {time} call. Is this still a good time?"
2. If yes → Transfer to William
3. If no → Take reschedule preference

**NOT for**: Cold outreach, lead generation, sales pitches

### 3. ConsultingVoiceEngine (Legacy - Evaluate Before Using)

**Purpose**: Originally for cold outreach

**Current recommendation**: Don't use for cold calling. May have limited use for scheduled demos where the person EXPECTS to talk to an AI.

---

## When to Use Voice AI vs SMS vs Human

| Situation | Best Channel |
|-----------|--------------|
| Initial cold outreach | SMS or Human call |
| Lead responds to SMS | Human call |
| Inbound inquiry | AI receptionist → Human |
| Scheduling confirmation | AI or SMS |
| Active sales conversation | Human ONLY |
| Support/troubleshooting | Human or AI (depends on complexity) |
| Order taking (restaurant) | AI works great |

---

## Implementation Checklist

Before deploying voice AI for a new use case:

- [ ] Does the AI SERVE the caller (not sell to them)?
- [ ] Is the task routine/transactional (not relationship-building)?
- [ ] Will the caller benefit from AI (faster, 24/7, etc)?
- [ ] Is the AI clearly identified as AI?
- [ ] Can the caller easily reach a human if needed?
- [ ] Would YOU want to receive this call from an AI?

If any answer is NO, reconsider using voice AI for that use case.

---

## Commands

**Test inbound receptionist** (call +1-855-239-9364):
The AI will answer, quickly qualify, and transfer hot leads.

**Make confirmation call**:
```bash
python scripts/confirmation_call.py --person "John" --time "2pm today" 2395551234
```

**Check call logs**:
```bash
curl https://midi-bottom-inline-directories.trycloudflare.com/twilio/calls
```
