# Live URLs — Canonical Reference

> Source of truth: [`data/live-urls.json`](../data/live-urls.json). Edit that file; this doc mirrors it for humans/Panacea.
> When asked "what's my working link for X," answer from THIS list — do not guess or hand out squatter domains.

_Last verified: 2026-06-14_

## Live & monitored

| Site | URL | Host | Healthy response |
|------|-----|------|------------------|
| Marceau Solutions (brand hub) | https://marceausolutions.com | GitHub Pages | 200 |
| Marceau Air (HVAC site) | https://marceauair.com | GitHub Pages | 200 |
| Marceau Air — appointment intake | https://appointments.marceauair.com/request-service | EC2 form-handler (:8768) | **405** (POST-only endpoint; 405 on GET = healthy) |
| FitAI | https://fitai.marceausolutions.com | EC2 | 200 |
| n8n | https://n8n.marceausolutions.com | EC2 (:5678) | 200 |

## Known dead — do NOT hand these out

- **Flames of Passion** — real domain is `flamesofpassionentertainment.com`, but it has **no DNS A record**: the domain transfer from Squarespace never completed, so it points nowhere and cannot go live until we control the domain and point it at GitHub Pages. `flamesofpassion.com` and `flamesofpassion.org` are **squatter/parking domains we do not own** — never present them as ours.
- **appointments.marceausolutions.com** — **decommissioned 2026-06-15**. Was the HVAC lead-marketplace product squatting on a misleading "appointments" subdomain. nginx route removed, `marketplace.service` disabled. Do not revive at this name.

## Planned (not yet live)

- **leads.marceausolutions.com** — future home of the marketplace product (`projects/lead-generation/marketplace/`), a contractor lead-resale SaaS (separate from Marceau Air's intake). Pre-launch, empty DB. Stand up via [`marketplace/LAUNCH.md`](../projects/lead-generation/marketplace/LAUNCH.md) when onboarding contractors.

## Monitoring

`execution/uptime_monitor.py` runs every 5 min on EC2 (systemd timer `uptime-monitor.timer`), checks every `monitor: true` site in the registry, and Telegrams William **only on state change** (up→down, down→up). Independent of n8n so it survives n8n outages.

- Manual check: `python3 execution/uptime_monitor.py --dry-run`
- Test alert: `python3 execution/uptime_monitor.py --test`
