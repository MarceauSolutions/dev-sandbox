# Digital Tower — Marceau Digital

> Client websites, the company website, and AI-powered web development tools.

## Projects
| Project | Purpose | Status |
|---------|---------|--------|
| `website/` | marceausolutions.com (static HTML, GitHub Pages) | Active |
| `web-dev/` | Client website business (HVAC, BoabFit, Flames) | Active |
| `website-builder/` | AI website generation service (FastAPI) | Development |

## Active Clients (`clients/`)
| Client | Project Dir | Deploy Repo |
|--------|-------------|-------------|
| SW Florida Comfort (HVAC) | `clients/swflorida-hvac/website/` | `MarceauSolutions/swflorida-comfort-hvac` |
| BoabFit | `clients/boabfit/website/` | `MarceauSolutions/boabfit-website` |
| Flames of Passion | `clients/flames-of-passion/website/` | `MarceauSolutions/flames-of-passion-website` |
| Square Foot Shipping | `clients/square-foot-shipping/` | — |

## Revenue
- **Model**: Per-project + optional hosting
- **Billing**: Stripe invoice (custom amount)

## Deploy
```bash
./scripts/deploy_website.sh {marceau|hvac|boabfit|flames}
```

## n8n Workflows (this tower)
- Webdev-Payment-Welcome (`5GXwor2hHuij614l`)
- Webdev-Monthly-Checkin (`N8HIFsZdE5Go7Lky`)
- Webdev-Deploy-Notification (`E0DivEtTGgVZm3v6`)
- Webdev-Cross-Referral (`eoQMjVYQSibMALaZ`)
- Flames-Form-Pipeline (`mrfVYqg5H12Z2l5K`)

## Key Tools
- WebDev Tracker Sheet: `1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q`
- Client onboarding: `digital/web-dev/workflows/client-onboarding.md`
