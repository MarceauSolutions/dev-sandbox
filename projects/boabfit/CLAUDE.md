# BoabFit — Julia Marceau

Active client of Marceau Solutions. Women's fitness coaching brand.

**Client:** Julia Marceau | **Phone:** +1 (239) 398-5197 | **Email:** info@boabfit.com
**Domain:** www.boabfit.com (GitHub Pages)

## Projects in This Namespace

| Project | What | Deploy Repo / Location |
|---------|------|------------------------|
| `website/` | Landing pages (homepage, dashboard, 6-week program) | `MarceauSolutions/boabfit-website` (GitHub Pages) |
| `app/` | Mobile app (Expo React Native + Supabase) | Phase 1 in progress |
| `src/` | SMS operations (daily check-ins, drip, relay, abandon tracking) | Live on EC2 via n8n |
| `clients/` | Client roster (18 clients), checkin logs, SMS relay state | Live data |
| `research/` | Market analysis, manufacturer research, Trainerize analysis | Reference |
| `reference/` | Trainerize screen recordings, EC2 sync plan | Reference |

## Deployment

- **Website:** `./scripts/deploy_website.sh boabfit` pushes to `MarceauSolutions/boabfit-website` (GitHub Pages)
- **SMS ops:** 4 n8n workflows on EC2 (signup, drip, abandon x2) execute Python scripts via SSH
- **Lead nurture:** Flask service at `projects/shared/client-lead-systems/boabfit/` (port 5025)

## Lead Management (ISOLATION)

Julia's lead management system is SEPARATE from William's pipeline. Her leads go through:
- Landing page form -> n8n webhook (`/webhook/boabfit-signup`) -> Julia notified at info@boabfit.com
- Abandonment tracking -> n8n follow-up emails
- Drip sequence (Day 0/3/7/14) -> Gmail sends FROM info@boabfit.com

William's leads (Marceau Solutions pipeline) do NOT cross into this system. Julia has her own:
- Lead DB at `projects/shared/client-lead-systems/boabfit/`
- n8n workflows with separate webhook URLs
- Notification routing to Julia's email, NOT William's

## n8n Workflows (EC2)

| Workflow | ID | Trigger |
|----------|----|---------|
| Signup Complete | `qOrsQZ8ENHvk5izE` | Webhook |
| Welcome Drip Sequence | `yPDEvttIB7bhZm6U` | Hourly cron |
| Abandonment Tracker | `3Rp58kNT57VMpzvQ` | Webhook |
| Abandonment Follow-up | `6dv7d5WgvJsMMtdL` | Hourly cron |

## Mobile App (Phase 1)

Tech: Expo React Native + Supabase + Bunny.net (video CDN) + Stripe
Started: 2026-04-02 | Builder: William's brother
Status: Auth scaffold complete, tabs stubbed (Home, Calendar, Library, Profile)
Blocker: Supabase project needs to be created and env vars set

Julia's app requirements (from `reference/trainerize-analysis.md`):
- Press Play workout flow with timer
- Calendar with scheduled workouts
- Exercise video library by muscle group
- Progress tracking + streaks
- Admin: upload workouts, assign programs, view client progress
