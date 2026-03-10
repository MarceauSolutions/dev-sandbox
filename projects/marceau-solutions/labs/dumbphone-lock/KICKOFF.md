# DumbPhone Lock — Kickoff (SOP 0)

## Project Routing (SOP 32)
| Field | Value |
|-------|-------|
| **Type** | Company Project (iOS App) |
| **Location** | `projects/marceau-solutions/dumbphone-lock/` |
| **Deploy To** | App Store (after validation) |
| **Next SOP** | SOP 1 (done), then market validation |
| **Skip SOPs** | SOP 9 (architecture clear), SOP 11-14 (not MCP) |

## App Type Decision
- **Platform**: iOS (SwiftUI)
- **Type**: Native app (not MCP, not web, not CLI)
- **Distribution**: App Store (requires $99 Apple Developer Program)
- **Current state**: Free-signed build on device + waitlist landing page

## Two-Component Architecture
1. **Launcher UI** (free signing): Custom home screen, clock, weather, app grid, focus timer
2. **App Blocker** (paid signing): FamilyControls / ManagedSettings API for real app blocking

## Cost-Benefit Analysis
| Item | Cost | Notes |
|------|------|-------|
| Apple Developer Program | $99/year | Required for FamilyControls + TestFlight + App Store |
| Landing page + n8n | $0 | Already built on existing infra |
| Ad spend (validation) | $100 | 5-day test across Meta, TikTok, Reddit |
| **Total validation cost** | **$100** | Before committing to $99 dev account |

## Revenue Model (if validated)
- Free tier: Basic blocking + manual lock
- Premium ($4.99/mo or $29.99/year): Scheduling, analytics, accountability partners, presets
- Comparable apps: Opal ($79.99/year), One Sec ($4.99/mo), ScreenZen (free)

## Go/No-Go Criteria
- **GO**: 100+ waitlist signups in 48 hours from organic, OR cost-per-lead under $2 from paid
- **NO-GO**: Under 50 signups organic + cost-per-lead over $5 paid
- **PIVOT**: 50-100 signups — rethink positioning, don't invest in dev yet

## Decision: GO (conditional)
Proceed with market validation. Landing page and automation pipeline are live. Decision on $99 Apple Developer account after 48-hour organic test.
