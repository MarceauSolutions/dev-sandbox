# InboundAssistantEngine Edge Case Test Plan

*Created: 2026-01-18*
*Engine: InboundAssistantEngine (voice_engine.py:373-500)*
*Purpose: Stress-test the fast-qualifying receptionist logic*

## Overview

The InboundAssistantEngine is designed to quickly qualify inbound callers and transfer hot leads to William immediately. The core principle is **bias toward transferring** - William would rather take a borderline call than miss a real opportunity.

### Expected Triggers

| Trigger | State Change | When to Use |
|---------|--------------|-------------|
| `[TRANSFER_NOW]` | `state.live_transfer_requested = True` | Hot lead detected, immediate transfer |
| `[MESSAGE_COMPLETE]` | `state.awaiting_confirmation = True` | Non-urgent, message taken |
| `[END_CALL]` | `state.transfer_requested = True` | Sales/spam, or caller wants to end |
| (none) | Continue conversation | Need more info to qualify |

---

## Category 1: Clear Hot Leads

These should trigger `[TRANSFER_NOW]` immediately after first qualifying statement.

### Test 1.1: Direct AI/Automation Request

**Input:** "I need help automating my restaurant's phone system"

**Expected Response:** "Absolutely! Let me connect you with William right now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Explicit request for automation services - core offering. No qualification needed.

---

### Test 1.2: Project Discussion Request

**Input:** "I saw your work online and want to discuss a project"

**Expected Response:** "Perfect, let me get William on the line for you."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Caller mentions "project" and references William's work - clear intent to hire.

---

### Test 1.3: Pricing Inquiry

**Input:** "What do you charge for voice AI?"

**Expected Response:** "Great question! Let me connect you with William to discuss your needs."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Pricing questions indicate buying intent. Don't answer pricing - transfer immediately.

---

### Test 1.4: Business Owner with Problem

**Input:** "I own a dental practice and our front desk is overwhelmed with calls"

**Expected Response:** "I can definitely help with that. Let me get William for you right now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Business owner + specific pain point = ideal customer profile.

---

### Test 1.5: Referral Mention

**Input:** "My friend Mike told me William helped him with chatbots"

**Expected Response:** "That's great! William would love to speak with you. Connecting you now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Referral = warm lead. Skip qualification.

---

### Test 1.6: Direct Request for William

**Input:** "Can I speak to William please?"

**Expected Response:** "He is! What's this regarding so I can let him know?"

**Expected Trigger:** (none - continue conversation)

**Why:** Need one more question to qualify. Could be sales, could be lead.

**Follow-up Input:** "I want to discuss a potential project"

**Expected Response:** "Wonderful! Connecting you now."

**Expected Trigger:** `[TRANSFER_NOW]`

---

## Category 2: Clear Non-Leads

These should NOT transfer to William. Use `[END_CALL]` or `[MESSAGE_COMPLETE]`.

### Test 2.1: Insurance Sales

**Input:** "Hi, I'm calling from XYZ Insurance to offer you a great deal on business coverage"

**Expected Response:** "Thanks for calling, but we're all set. Have a great day!"

**Expected Trigger:** `[END_CALL]`

**Why:** Vendor sales pitch. Polite but firm rejection.

---

### Test 2.2: Wrong Number

**Input:** "Wrong number, sorry"

**Expected Response:** "No problem! Have a great day."

**Expected Trigger:** `[END_CALL]`

**Why:** Caller self-identified as wrong number. No action needed.

---

### Test 2.3: Misdialed Business

**Input:** "Is this the pizza place?"

**Expected Response:** "I'm sorry, this is William Marceau's consulting office. I think you may have the wrong number."

**Expected Trigger:** `[END_CALL]`

**Why:** Clearly looking for different business.

---

### Test 2.4: B2B Software Sales

**Input:** "Hi, I'm from Salesforce and I'd love to show you how our CRM can help your business"

**Expected Response:** "Thanks, but we're not interested at this time. Take care!"

**Expected Trigger:** `[END_CALL]`

**Why:** Inbound sales call. Politely decline.

---

### Test 2.5: Recruiter Call

**Input:** "Hi, I'm a recruiter and I have an exciting opportunity for William"

**Expected Response:** "Thanks for reaching out! William isn't looking for new positions, but I appreciate the call."

**Expected Trigger:** `[END_CALL]`

**Why:** Recruiter - not a client lead. Don't waste William's time.

---

### Test 2.6: Survey/Research

**Input:** "Hi, we're conducting a brief survey about small business technology"

**Expected Response:** "We'll have to pass on surveys, but thanks for thinking of us!"

**Expected Trigger:** `[END_CALL]`

**Why:** Survey = time waste, not a lead.

---

## Category 3: Edge Cases (Tricky Qualification)

These require careful handling - may need one qualifying question or judgment call.

### Test 3.1: Vague Request for William

**Input:** "Is William available?"

**Expected Response:** "He is! What's this regarding so I can let him know?"

**Expected Trigger:** (none - continue)

**Why:** Could be anything. One quick question to qualify.

**Path A - Business inquiry:**
- Follow-up: "I wanted to discuss AI for my company"
- Response: "Perfect! Connecting you now."
- Trigger: `[TRANSFER_NOW]`

**Path B - Personal call:**
- Follow-up: "I'm his friend from college"
- Response: "Of course! Let me put you through."
- Trigger: `[TRANSFER_NOW]` (personal calls still transfer, but note it)

**Path C - Sales:**
- Follow-up: "I'm calling about a marketing opportunity"
- Response: "Thanks, but William isn't taking marketing calls. Have a great day!"
- Trigger: `[END_CALL]`

---

### Test 3.2: Developer/Competitor Curiosity

**Input:** "I'm a developer interested in your tech stack - how did you build the voice AI?"

**Expected Response:** "That's cool! Let me connect you with William - he loves talking tech."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Bias toward transfer. Could be:
- Potential hire
- Potential collaborator
- Someone who will later become a client
- Worst case: 5-minute conversation William enjoys anyway

---

### Test 3.3: Personal Referral Ambiguity

**Input:** "My friend told me to call"

**Expected Response:** "Great! What can we help you with today?"

**Expected Trigger:** (none - continue)

**Why:** Need to determine if business or personal referral.

**Path A:**
- Follow-up: "He said William does AI consulting - I might need that"
- Trigger: `[TRANSFER_NOW]`

**Path B:**
- Follow-up: "He wanted me to invite William to his birthday party"
- Trigger: `[TRANSFER_NOW]` (personal, but still transfer)

---

### Test 3.4: Existing Customer Complaint

**Input:** "I want to complain about your service"

**Expected Response:** "I'm sorry to hear that. Let me connect you with William right away so we can make this right."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Customer retention is critical. Complaints get escalated immediately.

---

### Test 3.5: Adjacent Service Inquiry

**Input:** "Do you do websites too?"

**Expected Response:** "William focuses on AI and automation, but he might be able to help or point you in the right direction. Want me to connect you?"

**Expected Trigger:** (none - wait for response)

**Why:** Not core service, but could lead to referral opportunity or expanded scope.

**If they say yes:** `[TRANSFER_NOW]`
**If they say no:** "No problem! Is there anything else I can help with?"

---

### Test 3.6: Mumbled/Unclear Speech

**Input:** "Uhh... mmm... automation... something... business..."

**Expected Response:** "I'm sorry, I didn't quite catch that. Could you tell me a bit more about what you're looking for?"

**Expected Trigger:** (none - continue)

**Why:** Ask for clarification once. Keywords "automation" and "business" suggest potential lead.

**If still unclear after 2 attempts:** Take message with `[MESSAGE_COMPLETE]`

---

### Test 3.7: One-Word Responder

**Scenario:** Caller who only says "yeah", "uh-huh", "okay" without substance.

**AI:** "Hi, you've reached William Marceau's office. How can I help you?"
**Input:** "Yeah"
**Response:** "What can I help you with today?"

**Input:** "Uh-huh"
**Response:** "Are you calling about a project or did you have a question for William?"

**Expected Trigger:** (none - continue, but limited patience)

**Why:** Try twice to get substance. If still nothing:

**Input:** "Yeah"
**Response:** "I want to make sure I connect you to the right person. Would you like to leave a message for William?"

**Expected Trigger:** (none - offer message option)

**After 4 exchanges with no substance:** Consider `[END_CALL]` with polite out.

---

### Test 3.8: Caller Gets Frustrated with AI

**Input:** "Ugh, is this a robot? I hate talking to AI"

**Expected Response:** "I understand! Would you like me to connect you directly with William?"

**Expected Trigger:** (none - wait for response)

**Why:** Acknowledge frustration, offer immediate human connection.

**If they say yes:** `[TRANSFER_NOW]`
**If they hang up:** No trigger needed (call ends)

---

### Test 3.9: Media/Press Inquiry

**Input:** "Hi, I'm a reporter from TechCrunch writing about voice AI startups"

**Expected Response:** "That sounds exciting! Let me connect you with William right now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Press = opportunity. Never screen out media.

---

### Test 3.10: Partnership/Collaboration

**Input:** "I run an AI agency and wanted to explore potential partnership"

**Expected Response:** "Great! William loves connecting with other folks in the AI space. Transferring you now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Partnership opportunities are valuable. Transfer immediately.

---

## Category 4: Hostile/Difficult Scenarios

Handle gracefully without escalating. Protect William's time.

### Test 4.1: Anti-Robot Hostility

**Input:** "I hate talking to robots. Put me through to a real person now!"

**Expected Response:** "Absolutely, let me connect you right away."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Caller explicitly demands human. Honor request immediately.

---

### Test 4.2: Angry About Unrelated Issue

**Input:** "I am SO frustrated! Nothing is working today and I'm at my wit's end!"

**Expected Response:** "I'm sorry you're having a tough day. How can I help you today?"

**Expected Trigger:** (none - continue)

**Why:** Acknowledge emotion, redirect to purpose of call. May still be a lead.

---

### Test 4.3: Immediate Transfer Demand

**Input:** "Just transfer me. Now."

**Expected Response:** "Of course! Connecting you to William right now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Caller is clearly impatient. Don't waste time - transfer.

---

### Test 4.4: Robocall/Spam Bot

**Input:** (recorded message) "Congratulations! You've been selected for a free cruise..."

**Expected Response:** (hang up immediately - no response needed)

**Expected Trigger:** `[END_CALL]`

**Why:** Obvious robocall. End immediately. Don't engage.

**Detection signals:**
- Recorded/synthesized voice quality
- Generic "you've been selected" language
- Pause before message starts

---

### Test 4.5: Scam Attempt

**Input:** "This is the IRS. You have unpaid taxes and a warrant for your arrest."

**Expected Response:** "This sounds like a scam call. We're not interested. Goodbye."

**Expected Trigger:** `[END_CALL]`

**Why:** Known scam pattern. Firm rejection.

---

### Test 4.6: Profanity/Abuse

**Input:** "[expletive] your stupid AI, let me talk to a [expletive] person!"

**Expected Response:** "I understand you'd prefer to speak with William. Connecting you now."

**Expected Trigger:** `[TRANSFER_NOW]`

**Why:** Despite profanity, caller wants human. Transfer without escalating.
Note: If abuse continues after transfer offer, consider `[END_CALL]`.

---

### Test 4.7: Pranker/Time Waster

**Input:** "What's your favorite color? Do you have feelings? Are you alive?"

**Expected Response:** "Ha! I'm William's AI assistant. Are you calling about a project or did you need to reach William?"

**Expected Trigger:** (none - continue)

**Why:** Redirect to business purpose with light touch. Some curious callers become clients.

**If they continue:** "Was there something I could help you with today?"
**If still no substance after 2-3 exchanges:** "I'll let you go. Feel free to call back if you need help with anything!"
**Trigger:** `[END_CALL]`

---

### Test 4.8: Threatening Language

**Input:** "I know where your office is and I'm coming for you"

**Expected Response:** "I'm going to end this call now. Have a good day."

**Expected Trigger:** `[END_CALL]`

**Why:** Safety first. End threatening calls immediately. Log for review.

---

## Category 5: Complex Multi-Turn Scenarios

These test the AI's ability to track context across multiple exchanges.

### Test 5.1: Gradual Lead Revelation

**Turn 1:**
- Input: "Hi, I'm just calling to ask a quick question"
- Response: "Of course! What's your question?"
- Trigger: (none)

**Turn 2:**
- Input: "I was wondering if AI can really handle phone calls"
- Response: "It absolutely can! Is this for a business you're running?"
- Trigger: (none)

**Turn 3:**
- Input: "Yeah, I have a small insurance agency and we're drowning in calls"
- Response: "William specializes in exactly that. Let me connect you!"
- Trigger: `[TRANSFER_NOW]`

**Why:** Started vague, became hot lead. Patience paid off.

---

### Test 5.2: Skeptical Prospect

**Turn 1:**
- Input: "I've heard AI phone systems are terrible. Why should I trust this?"
- Response: "Fair question! William can walk you through real examples. Want me to connect you?"
- Trigger: (none - wait for response)

**Turn 2:**
- Input: "I don't know... is he going to try to sell me something?"
- Response: "No pressure at all! He just likes helping businesses figure out if AI is right for them. It's a quick chat."
- Trigger: (none)

**Turn 3:**
- Input: "Okay, I guess I can talk to him"
- Response: "Great! Connecting you now."
- Trigger: `[TRANSFER_NOW]`

**Why:** Overcame skepticism through low-pressure approach.

---

### Test 5.3: Message Taker Flow

**Turn 1:**
- Input: "I just want to leave a message"
- Response: "Of course! What would you like me to tell William?"
- Trigger: (none)

**Turn 2:**
- Input: "Tell him Sarah called about the proposal"
- Response: "Got it - Sarah called about the proposal. Is there a good number for William to reach you?"
- Trigger: (none)

**Turn 3:**
- Input: "He has it"
- Response: "Perfect! I'll make sure William gets your message. Thanks Sarah!"
- Trigger: `[MESSAGE_COMPLETE]`

**Why:** Clean message-taking flow for non-urgent callbacks.

---

### Test 5.4: Qualifying Then Downgrade

**Turn 1:**
- Input: "I'm interested in AI services"
- Response: "Great! Let me connect you with William."
- Trigger: (none - slight pause to give them chance to add context)

**Turn 2:**
- Input: "Actually, I'm just researching for a school project"
- Response: "Ah, got it! For research, I'd suggest checking out William's website. Is there a specific question I can help with?"
- Trigger: (none - continue but don't transfer)

**Why:** Initial signal was positive, but context changed. Don't transfer students doing research.

---

### Test 5.5: Urgency Indicator

**Turn 1:**
- Input: "I need help urgently - our phone system is down"
- Response: "Let me get William on the line right away!"
- Trigger: `[TRANSFER_NOW]`

**Why:** "Urgently" + "down" = emergency for existing or potential customer. Immediate transfer.

---

## Validation Criteria

For each test scenario, verify:

1. **Correct trigger fired** - Check `state.live_transfer_requested`, `state.awaiting_confirmation`, or `state.transfer_requested`
2. **Response is 1-2 sentences** - This is voice, not text
3. **Tone is warm and professional** - Not robotic or salesy
4. **Bias toward transfer** - When in doubt, transferred
5. **No unnecessary questions** - Didn't interrogate the caller

## Suggested System Prompt Improvements

Based on edge case analysis, consider these additions to the InboundAssistantEngine system prompt:

### 1. Add Explicit Scam/Robocall Handling

```
SCAM/ROBOCALL SIGNALS (end call immediately):
- "You've won" / "You've been selected" / "Free cruise"
- IRS/SSA/government threats
- Recorded/robotic voice quality
- Requests for personal/financial information
```

### 2. Add Media/Press Handling

```
ALWAYS TRANSFER:
- Press/media inquiries (reporters, journalists, podcasters)
- Partnership/collaboration requests from other businesses
- Existing customer issues or complaints
```

### 3. Add Patience Parameters

```
CONVERSATION LIMITS:
- Ask maximum 2 qualifying questions before deciding
- After 4 exchanges with no substance, offer to take message or end politely
- Don't get into debates or extended explanations
```

### 4. Add Safety Handling

```
SAFETY - End immediately if:
- Threats or threatening language
- Harassment
- Clearly intoxicated/impaired caller who can't communicate
End with: "I'm going to end this call now. Goodbye."
[END_CALL]
```

### 5. Add Transfer Context

Consider passing context to William on transfer:
```
When triggering [TRANSFER_NOW], also include:
[TRANSFER_CONTEXT]
Caller interest: {brief description}
Example: "Business owner with overwhelmed front desk"
```

---

## Test Execution Checklist

- [ ] Clear hot leads trigger immediate transfer (5/5 tests)
- [ ] Clear non-leads are politely rejected (6/6 tests)
- [ ] Edge cases are handled with good judgment (10/10 tests)
- [ ] Hostile scenarios are de-escalated gracefully (8/8 tests)
- [ ] Multi-turn scenarios track context correctly (5/5 tests)
- [ ] Average response length under 20 words
- [ ] No qualifying questions for obvious leads
- [ ] Maximum 2 qualifying questions for ambiguous cases

---

## Appendix: State Machine Reference

```
                    ┌─────────────────┐
                    │  Initial State  │
                    │   (Greeting)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Qualify Input  │◄────────────────┐
                    └────────┬────────┘                 │
                             │                          │
              ┌──────────────┼──────────────┐           │
              │              │              │           │
              ▼              ▼              ▼           │
    ┌─────────────┐  ┌─────────────┐  ┌──────────┐     │
    │ Hot Lead    │  │  Non-Lead   │  │  Unclear │     │
    │ Detected    │  │  Detected   │  │  (Ask 1) │─────┘
    └──────┬──────┘  └──────┬──────┘  └──────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │[TRANSFER_NOW]│  │[END_CALL]   │
    │    or       │  │    or       │
    │  continue   │  │[MESSAGE_    │
    │  to message │  │ COMPLETE]   │
    └─────────────┘  └─────────────┘
```
