# Marketplace — Launch Runbook

**Canonical product domain: `leads.marceausolutions.com`** (decided 2026-06-15 with Grok).
This is a Marceau Solutions *product* (multi-contractor HVAC lead resale), NOT Marceau Air's
booking page. Keep it strictly separate from `appointments.marceauair.com` (which is Marceau
Air's own contact intake via `execution/form_handler/`).

## Decommission state (current, as of 2026-06-15)
Pre-launch, empty DB (0 contractors / 0 appointments). To kill the misleading
`appointments.marceausolutions.com` naming, the public route and service were idled:
- nginx conf removed (backup: `/etc/nginx/decommissioned/appointments.marceausolutions.com.conf.*` on EC2)
- `marketplace.service` stopped + disabled (was gunicorn on `127.0.0.1:8767`)

## To launch at leads.marceausolutions.com

1. **DNS** (Namecheap → marceausolutions.com → Advanced DNS → Add record):
   `A  |  host: leads  |  value: 34.193.98.97  |  TTL: Automatic`

2. **Re-enable the service** (EC2):
   ```
   sudo systemctl enable --now marketplace.service
   ```

3. **nginx vhost** (EC2) — create `/etc/nginx/conf.d/leads.marceausolutions.com.conf`:
   server_name `leads.marceausolutions.com`; proxy_pass `http://127.0.0.1:8767`; listen 80.
   Then `sudo nginx -t && sudo systemctl reload nginx`.

4. **HTTPS** (EC2): `sudo certbot --nginx -d leads.marceausolutions.com`
   (adds the 443 block + HTTP→HTTPS redirect automatically).

5. **Canonical URL** — set in EC2 `.env`: `MARKETPLACE_BASE_URL=https://leads.marceausolutions.com`,
   then restart the service. (CORS for the homeowner request form stays `marceauair.com` —
   homeowners submit from the HVAC site; contractors log in at leads.marceausolutions.com.)

6. **Add to uptime monitor**: add the URL to `data/live-urls.json` (`monitor: true`).

7. **Go-live gates** (from README phased rollout): start `MARKETPLACE_PUBLIC_SIGNUP=false`,
   `MARKETPLACE_PAYMENT_MODE=manual`; flip to Stripe TEST before live keys.
