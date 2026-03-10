# Client Onboarding Workflow

**Trigger**: Stripe $197/mo payment received
**SLA**: Client experiences coaching within 60 seconds of payment
**Based on**: SOP 6 (Workflow Creation), Client Acquisition System Guide v2

---

## Automated (n8n — Coaching-Payment-Welcome)

These happen instantly, no action needed from you:

1. Portal account created at `fitai.marceausolutions.com/client/`
2. Starter workout template (Beginner Full Body) pre-assigned
3. Welcome SMS sent with portal magic link
4. Welcome email sent with portal CTA + Calendly kickoff + intake form
5. Client added to Client Roster Google Sheet
6. Payment logged in Billing tab
7. Admin notification SMS to your phone

## Manual (You Do These)

| Step | When | How | Done? |
|------|------|-----|-------|
| Verify n8n fired | Within 1 hour | Check n8n executions for Coaching-Payment-Welcome | [ ] |
| Verify Sheet entry | Within 1 hour | Client Roster tab — name, email, portal link present | [ ] |
| Check kickoff booking | Within 24 hours | Calendly — did they book? | [ ] |
| Send kickoff reminder | If no booking in 24h | `python execution/twilio_sms.py --template coaching_kickoff_reminder --to <phone>` | [ ] |
| Review intake form | After they submit | Google Form responses — read their goals, injuries, history | [ ] |
| Do kickoff call | Calendly scheduled | 30 min Zoom — learn about them, set expectations | [ ] |
| Customize program | Within 48h of kickoff | Replace starter template with personalized program in portal | [ ] |
| Create Drive folder | After kickoff | `python scripts/create-coaching-drive-folders.py` | [ ] |
| Upload legal docs | After folder created | Waiver, working-together, cancellation policy to their Resources folder | [ ] |
| Send "you're all set" SMS | After program uploaded | Confirm their custom program is live in the portal | [ ] |

## Success Criteria

- Client has portal access within 60 seconds of payment
- Kickoff call booked within 48 hours
- Custom program delivered within 48 hours of kickoff call
- Client completes first workout within 7 days of payment

## If Something Breaks

| Problem | Fix |
|---------|-----|
| n8n didn't fire | Check workflow is active, check Stripe webhook events |
| No SMS sent | Check Twilio balance, check credential in n8n |
| Portal account not created | Check fitai API is running: `curl https://fitai.marceausolutions.com/docs` |
| Client can't access portal | Generate new magic link manually, send via SMS |
| Kickoff not booked after 48h | Call them directly — this is a relationship, not a SaaS |
