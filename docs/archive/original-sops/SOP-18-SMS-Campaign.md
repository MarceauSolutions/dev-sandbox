<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 18: SMS Campaign Execution

**When**: Running SMS outreach campaigns via Twilio

**Purpose**: Execute compliant SMS campaigns with proper template approval, sending, and tracking

**Agent**: Claude Code (primary, template approval). Clawdbot (execute campaigns after setup). Ralph: N/A.

**Prerequisites**:
- ✅ Twilio account with balance (>$10)
- ✅ Phone number configured (+1 855 239 9364)
- ✅ Templates approved by William
- ✅ Lead list with valid phone numbers
- ✅ Webhook server running for replies

**Steps**:

1. **Verify prerequisites**:
   ```bash
   cd /Users/williammarceaujr./dev-sandbox/projects/shared/lead-scraper
   grep TWILIO .env  # All 3 vars set
   cat output/approved_templates.json | grep template_name
   ```

2. **Dry run first** (always required):
   ```bash
   python -m src.scraper sms --dry-run --limit 5 --template no_website_intro
   ```
   Verify: Messages render correctly, personalization works, under 160 chars

3. **Small batch test** (10 leads):
   ```bash
   python -m src.scraper sms --for-real --limit 10 --pain-point no_website
   ```
   Wait 24 hours, check: Delivery rate, STOP responses, carrier violations

4. **Full campaign** (only after small batch succeeds):
   ```bash
   python -m src.scraper sms --for-real --limit 100 --pain-point no_website
   ```

5. **Monitor**:
   - Twilio Console: https://console.twilio.com/us1/monitor/logs/sms
   - Webhook for replies: `python -m src.twilio_webhook serve --port 5001`

**TCPA Compliance Requirements**:
- B2B exemption for business numbers
- "This is William" in every message
- "Reply STOP to opt out" required
- No messages before 8am or after 9pm local time

**Success Criteria**:
- ✅ Delivery rate >95%
- ✅ Reply rate 2-5%
- ✅ Opt-out rate <2%
- ✅ No carrier violations

**References**: `projects/shared/lead-scraper/workflows/sms-campaign-sop.md`, `projects/shared/lead-scraper/workflows/cold-outreach-sop.md`

