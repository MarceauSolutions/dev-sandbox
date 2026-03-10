# Marceau Solutions — Tower Index

> Marmon-style tower structure. Each tower has `clients/` (who we serve) and `tools/` (what we use to serve them).

## Tower Layout

| Tower | Purpose | Clients | Tools |
|-------|---------|---------|-------|
| `fitness/` | Coaching, influencer automation, fitness tech | BoabFit, PT Business | FitAI, Trainerize MCP |
| `digital/` | Websites, web dev services | HVAC, Flames, Square Foot | Website Builder, Web Dev Hub |
| `media/` | Social content creation & automation | — | Instagram/YouTube/TikTok creators |
| `labs/` | R&D, new ventures | — | DumbPhone Lock, Amazon Seller, etc. |

## Rules

### Where does a client go?
Pick the tower that matches **what they're paying for**:
- Fitness coaching / influencer automation → `fitness/clients/`
- Website / digital services → `digital/clients/`
- Content / media services → `media/clients/`

### Where does a tool go?
Pick based on **who primarily uses it**:
- Serves fitness clients → `fitness/tools/`
- Serves digital/web clients → `digital/tools/`
- General content creation → `media/tools/`
- Cross-tower (2+ towers) → `execution/` (shared utilities)

### Standard Tower Structure
```
{tower}/
├── clients/          # One dir per client
│   └── {client}/
│       ├── src/      # Client-specific code
│       ├── clients/  # Client's own client roster (if applicable)
│       ├── website/  # Client website (if applicable)
│       └── CLAUDE.md
├── tools/            # Shared within this tower
│   └── {tool}/
│       ├── src/
│       └── CLAUDE.md
└── CLAUDE.md         # Tower overview
```

## Cross-Tower References
- BoabFit website deploys via `./scripts/deploy_website.sh boabfit` (digital deploy script, fitness client)
- Fitness influencer tool in `fitness/tools/` can serve future media clients too — move to `execution/` when that happens
