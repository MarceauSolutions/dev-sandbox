# Failure Mode Inventory

> Every critical system's failure mode, detection, and recovery path.
> Updated: 2026-03-17

## Infrastructure Failures

| System | Failure Mode | Detection | Recovery | Auto? |
|--------|-------------|-----------|----------|-------|
| EC2 instance | Instance unreachable | health_check.py SSH timeout (daily 7am) | Alert William via SMS — manual restart needed | Detection: auto. Recovery: manual |
| n8n crash | OOM SIGTERM | systemd auto-restart + Self-Annealing error handler | Automatic restart (symlink fix, session 12) | Full auto |
| n8n workflow failure | Any workflow errors | Self-Annealing catches → Telegram alert | Alert + error logged. Manual fix if needed. | Detection: auto |
| Clawdbot down | Service crash | health_check.py systemd check | systemd auto-restart (RestartSec=10) | Full auto |
| EC2 disk full | >90% usage | health_check.py disk check | Alert William. Run cleanup script. | Detection: auto |

## Revenue-Critical Failures

| System | Failure Mode | Detection | Recovery | Auto? |
|--------|-------------|-----------|----------|-------|
| Stripe webhooks disabled | Stripe disables inactive webhook | health_check.py webhook verification | Alert William. Re-register via Stripe dashboard. | Detection: auto |
| Stripe payment fails | Customer card declines | Stripe-Payment-Failed n8n workflow | Auto-SMS to client + Telegram to William | Full auto |
| SMS delivery fails | Twilio balance <$5 | health_check.py Twilio balance check | Alert William to top up | Detection: auto |
| Gmail OAuth expired | Token refresh fails | n8n workflow errors → Self-Annealing | Alert. Manual re-auth via google_auth_setup.py | Detection: auto |
| Telegram cred stale | Bot token invalidated | health_check.py Telegram test | `--repatch-telegram` flag on health check | Semi-auto |

## Business Operations Failures

| System | Failure Mode | Detection | Recovery | Auto? |
|--------|-------------|-----------|----------|-------|
| Lead capture form down | Webhook URL changes or n8n restart changes path | health_check.py workflow check | Alert. Webhook URLs are persistent in n8n. | Detection: auto |
| Apollo.io API key expired | 401 on API calls | Script error → logged | Alert William to refresh key | Detection: auto |
| Scorecard Sheet access revoked | OAuth permission change | weekly-report.py fails → error logged | Re-run google_auth_setup.py | Detection: auto |
| Morning check-in doesn't fire | n8n schedule missed | William notices no morning Telegram | Check n8n workflow status via dashboard | Manual |
| Content not posted on schedule | Videos not uploaded | Weekly report shows 0 content | Flagged in weekly report as red metric | Auto-detect |

## Monitoring Coverage

| Monitor | Frequency | What It Checks |
|---------|-----------|---------------|
| health_check.py | Daily 7am (launchd) | EC2, n8n (20 workflows), Stripe (6 webhooks), Twilio, AI APIs, domains |
| Self-Annealing | Real-time | All 48 n8n workflow errors |
| AutoIterator overnight | Daily 2am | Experiment status, winning variants |
| Weekly report | Monday 9am | All business KPIs vs targets |
| GitHub-Push-to-Telegram | On push | Code deployment notifications |
