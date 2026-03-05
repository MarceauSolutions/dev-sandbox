# Client Offboarding Workflow

**Trigger**: Client cancels Stripe subscription
**SLA**: Offboarding complete within 2 hours of cancellation
**Based on**: SOP 6, SOP 19 (Multi-Touch Follow-Up)

---

## Automated (n8n — Coaching-Cancellation-Exit)

These happen instantly:

1. Feedback SMS sent (immediate) — asks why they're leaving
2. Admin notification SMS to your phone
3. Day 7: Re-engagement SMS
4. Day 30: Final re-engagement SMS

## Manual (You Do These)

| Step | When | How | Done? |
|------|------|-----|-------|
| Update Client Roster | Within 2 hours | Set status to "Cancelled", add cancel date | [ ] |
| Read their feedback SMS reply | Within 24 hours | Check Twilio inbox or inbound webhook | [ ] |
| Send exit email | Within 24 hours | Thank you + progress summary + door's always open | [ ] |
| Note cancel reason | Within 24 hours | Add to Client Roster "Cancel Reason" column | [ ] |
| Keep Drive access | Permanent | Do NOT remove their folder — they keep it forever | [ ] |
| Portal access | 30 days | Keep active for 30 days post-cancel as goodwill gesture | [ ] |

## Re-Engagement Timeline

| Day | Channel | Message | Goal |
|-----|---------|---------|------|
| 0 | SMS (auto) | "Sorry to see you go. Quick question — what could I have done better?" | Get feedback |
| 7 | SMS (auto) | "Miss having you in the program. Door's always open — no hard feelings." | Soft re-engage |
| 30 | SMS (auto) | "It's been a month. If you ever want to pick back up, your program is still here." | Final attempt |
| 60 | Email (manual) | Share a win/testimonial from another client. Social proof. | Long-term re-engage |

## Cancel Reason Categories

Track these to identify patterns:

| Reason | Action |
|--------|--------|
| Too expensive | Consider offering 1-month discount on return |
| Not seeing results | Review their adherence — were they doing the work? |
| Life circumstances | Offer pause instead of cancel (30 days free) |
| Found another coach | Note who/what they switched to — competitive intel |
| Not responsive/engaged | Improve your check-in frequency for future clients |
| No reason given | The Day 0 feedback SMS should catch this |

## Success Criteria

- Feedback collected from 80%+ of cancellations
- Cancel reasons logged in Client Roster
- Re-engagement messages sent on schedule
- 10%+ of cancelled clients return within 90 days
