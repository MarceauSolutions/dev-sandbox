# Digital Tower — Marceau Digital

> Client websites, the company website, and AI-powered web development tools.

## Structure
```
digital/
├── clients/
│   ├── swflorida-hvac/       # HVAC client website
│   ├── flames-of-passion/    # Entertainment client website
│   └── square-foot-shipping/ # Shipping client (lead gen)
├── tools/
│   ├── website-builder/      # AI website generation service
│   └── web-dev/              # Web dev workflows, templates, ops
├── website/                  # marceausolutions.com
└── CLAUDE.md
```

## Clients

| Client | Dir | Deploy Repo | Status |
|--------|-----|-------------|--------|
| SW Florida Comfort (HVAC) | `clients/swflorida-hvac/website/` | `MarceauSolutions/swflorida-comfort-hvac` | Live |
| Flames of Passion | `clients/flames-of-passion/website/` | `MarceauSolutions/flames-of-passion-website` | DNS pending |
| Square Foot Shipping | `clients/square-foot-shipping/` | — | Lead gen |

**Note**: BoabFit has moved to the **Fitness Tower** (`fitness/clients/boabfit/`) since it's a fitness influencer client, not a web dev client. Website deploy still works via `./scripts/deploy_website.sh boabfit`.

## Tools

| Tool | Dir | Purpose |
|------|-----|---------|
| Website Builder | `tools/website-builder/` | AI website generation (FastAPI) |
| Web Dev Hub | `tools/web-dev/` | Workflows, ops runbook, templates |

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

## Key Shared Tools (in `execution/`)
- WebDev Tracker Sheet: `1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q`
- Client onboarding: `tools/web-dev/workflows/client-onboarding.md`
