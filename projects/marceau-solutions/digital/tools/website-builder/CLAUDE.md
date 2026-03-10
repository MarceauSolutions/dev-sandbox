# Website Builder AI — Hub

**Version**: 0.2.0 | **Status**: Active (internal tool) | **Type**: AI Web Service

## What It Does
Automated website generation powered by AI research and social media personality matching. Provide company info and social profiles → get a site that matches the owner's brand personality. Used for Marceau Solutions web dev clients.

## Key Locations
| What | Where |
|------|-------|
| Source | `src/` |
| Output | `output/` (generated sites) |
| Dependencies | `requirements.txt` |

## Key Commands
```bash
# Generate a website
python src/main.py --company "Company Name" --url "https://..." --social "@handle"

# Output lands in output/
```

## Related
- Web dev hub: `projects/marceau-solutions/web-dev/CLAUDE.md`
- Client deploy: `./scripts/deploy_website.sh {client}`
- Live clients: HVAC, BoabFit, Flames of Passion
