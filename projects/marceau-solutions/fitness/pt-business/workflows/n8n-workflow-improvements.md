# n8n Workflow Improvements — COMPLETED

**Based on**: SOP 19 (Multi-Touch Follow-Up), SOP 22 (Campaign Analytics), SOP 30 (n8n Workflow Management)
**Date**: March 4, 2026
**Status**: ALL 5 TASKS COMPLETE

---

## 1. Extend Non-Converter Follow-Up to Day 60 — DONE

**Workflow**: Non-Converter-Followup (ID: `Y2jfeIlTRDlbCHeS`)
**What changed**: Extended from 3 messages (Day 10, 14, 30) to 7 messages (Day 10, 14, 21, 30, 45, 60) + lead removal logic + sequence completion marker.

| Day | Channel | Message | Status |
|-----|---------|---------|--------|
| 10 | SMS | Soft check-in, Calendly link | Existed |
| 14 | SMS | Founding member rate, Stripe link | Existed |
| 21 | Email | Value tip based on quiz data (protein target) | **ADDED** |
| 30 | Email | Breakup positioning: "No hard feelings" | **UPDATED** (was value, now breakup) |
| 45 | SMS | Social proof: "A client just hit their milestone" | **ADDED** |
| 60 | Email | Re-engagement: testimonial + Stripe link + Calendly | **ADDED** |

**Also added**:
- Lead removal logic (Code node) — skips if status is `converted`, `opted_out`, or `undeliverable`
- Marks lead as `sequence_complete` in Leads sheet after Day 60
- All emails use dark+gold brand colors (fixed green #22c55e → gold #C9963C)

---

## 2. Inbound SMS Response Tracking — DONE

**Workflow**: SMS-Response-Handler-v2 (ID: `G14Mb6lpeFZVYGwa`)
**Webhook URL**: `https://n8n.marceausolutions.com/webhook/sms-response`

**Upgraded from** basic webhook+Telegram **to** full STOP handling + logging:

```
Twilio Webhook → Extract SMS Data → Respond to Twilio (empty TwiML)
                                  → Is STOP Request?
                                    → YES: Mark Lead Opted Out (Sheets) → Send Unsubscribe Confirmation (Twilio) → Notify Opt-Out (Telegram)
                                    → NO: Log to Responses Tab (Sheets) → Process Inbound → Notify William (Telegram)
```

**Google Sheets tabs created**:
- **Responses** tab: Date, From, Message, Lead Name, Category, Responded
- Headers auto-populated

**Twilio webhook config needed** (one-time manual step):
- Go to Twilio console → Phone Numbers → +1 (855) 239-9364
- Messaging → "A MESSAGE COMES IN" → Webhook
- URL: `https://n8n.marceausolutions.com/webhook/sms-response`
- Method: POST

---

## 3. Campaign Analytics Automation — DONE

**Workflow**: Weekly-Campaign-Analytics (ID: `M62QBpROE48mEgDC`)
**Schedule**: Every Monday at 7:00 AM ET

**Flow**:
1. Pulls Twilio message logs for past 7 days via HTTP API
2. Code node calculates: sent, delivered, failed, replies, opt-outs, rates, cost
3. Writes summary row to "Campaign Analytics" tab in Leads sheet
4. Sends William an SMS summary to +1 (239) 398-5676
5. Sends Telegram summary to chat 5692454753

**Google Sheets tab created**:
- **Campaign Analytics** tab: Week, Sent, Delivered, Delivery Rate, Replies, Reply Rate, Opt-Outs, Opt-Out Rate, Cost

**Targets monitored**: Delivery rate >95%, Reply rate 2-5%, Opt-out rate <2%

---

## 4. n8n Health Monitoring — DONE

**Workflow**: n8n-Health-Check (ID: `QhDtNagsZFUrKFsG`)
**Schedule**: Every day at 6:00 AM ET

**Flow**:
1. HTTP request to `http://localhost:5678/healthz`
2. Code node checks 13 critical workflows are active via internal API
3. IF all OK → Telegram log (silent confirmation)
4. IF any issue → SMS alert to William + Telegram alert

**Critical workflows monitored** (13):
- Coaching-Monday-Checkin, Coaching-Payment-Welcome, Coaching-Cancellation-Exit
- Fitness-SMS-Outreach, Fitness-SMS-Followup-Sequence
- Lead-Magnet-Capture, Nurture-Sequence-7Day, Non-Converter-Followup
- SMS-Response-Handler-v2, Challenge-Signup-7Day, Challenge-Day7-Upsell
- Premium-Waitlist-Capture, Digital-Product-Delivery

---

## 5. Automated n8n Workflow Backup — DONE

**Workflow**: Monthly-Workflow-Backup (ID: `2QaQbhIUlL7ctfq4`)
**Schedule**: 1st of each month at 3:00 AM ET

**Flow**:
1. Lists all workflows via n8n internal API
2. Exports each non-archived workflow to JSON
3. Saves to `/home/clawdbot/dev-sandbox/projects/shared/n8n-workflows/backups/{date}/`
4. Git add + commit + push
5. Telegram notification with export summary

**Also available**: `scripts/backup-n8n-workflows.sh` for manual backups (17 workflows registered).

---

## Complete Workflow ID Registry

| ID | Name | Active | Created |
|----|------|--------|---------|
| `aBxCj48nGQVLRRnq` | Coaching-Monday-Checkin | YES | Feb 11 |
| `1wS9VvXIt95BrR9V` | Coaching-Payment-Welcome | YES | Feb 11 |
| `uKjqRexDIheaDJJH` | Coaching-Cancellation-Exit | YES | Feb 11 |
| `89XxmBQMEej15nak` | Fitness-SMS-Outreach | YES | Feb 10 |
| `VKC5cifm595JNcwG` | Fitness-SMS-Followup-Sequence | YES | Feb 10 |
| `hgInaJCLffLFBX1G` | Lead-Magnet-Capture | YES | Mar 1 |
| `szuYee7gtQkzRn3L` | Nurture-Sequence-7Day | YES | Mar 1 |
| `Y2jfeIlTRDlbCHeS` | Non-Converter-Followup | YES | Mar 1 |
| `G14Mb6lpeFZVYGwa` | SMS-Response-Handler-v2 | YES | Jan 31 |
| `WTZDxLDQuSkIkcqf` | Challenge-Signup-7Day | YES | Mar 1 |
| `Xza1DB4f4PIHw2lZ` | Challenge-Day7-Upsell | YES | Mar 2 |
| `j306crRxCmWW3dMo` | Premium-Waitlist-Capture | YES | Mar 2 |
| `kk7ZjWtjmZgylVzi` | Digital-Product-Delivery | YES | Mar 2 |
| `BsoplLFe1brLCBof` | GitHub Push Notifications | YES | Feb 16 |
| `QhDtNagsZFUrKFsG` | n8n-Health-Check | YES | Mar 4 |
| `M62QBpROE48mEgDC` | Weekly-Campaign-Analytics | YES | Mar 4 |
| `2QaQbhIUlL7ctfq4` | Monthly-Workflow-Backup | YES | Mar 4 |

---

*All workflows deployed and active on EC2. Access via https://n8n.marceausolutions.com*
