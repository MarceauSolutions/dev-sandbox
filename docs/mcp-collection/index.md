# MCP Collection — Master Index

**Last Updated:** 2026-01-28
**Total MCPs:** 11

---

## By Category

### 🏢 Marceau Solutions (Company-Specific)

| MCP | Location | Version | Description |
|-----|----------|---------|-------------|
| **Amazon Seller** | `projects/marceau-solutions/amazon-seller/` | 1.0.0 | FBA fees, inventory optimization, restock recommendations |
| **Fitness Influencer** | `projects/marceau-solutions/fitness-influencer-mcp/` | 1.3.0 | Video editing, AI images, content calendars, comment management |
| **Instagram Creator** | `projects/marceau-solutions/instagram-creator/` | 1.0.0 | Post images, Reels, carousels, Stories, analytics |
| **TikTok Creator** | `projects/marceau-solutions/tiktok-creator/` | 1.0.0 | Post videos, analytics, comment management |
| **YouTube Creator** | `projects/marceau-solutions/youtube-creator/` | 1.0.0 | Upload videos, Shorts, playlists, analytics |

### 🏠 SW Florida HVAC (Company-Specific)

| MCP | Location | Version | Description |
|-----|----------|---------|-------------|
| **HVAC Quotes** | `projects/swflorida-hvac/hvac-mcp/` | 1.0.0 | HVAC equipment RFQ management |

### 🔧 Shared Tools (Multi-Company)

| MCP | Location | Version | Description |
|-----|----------|---------|-------------|
| **Apollo** | `projects/shared/apollo-mcp/` | 1.1.0 | Apollo.io lead enrichment and prospecting |
| **Upwork** | `projects/shared/upwork-mcp/` | 1.0.1 | Job discovery, client analysis, proposal assistance |

### 🌐 Global Utilities (Personal Tools)

| MCP | Location | Version | Description |
|-----|----------|---------|-------------|
| **MD to PDF** | `projects/global-utility/md-to-pdf/` | 1.0.1 | Markdown → professional PDFs with TOC |
| **Twilio** | `projects/global-utility/twilio-mcp/` | 1.0.0 | SMS inbox, sending, lead tracking |
| **Rideshare** | `projects/global-utility/mcp-aggregator/rideshare-mcp/` | 1.0.0 | Uber vs Lyft price comparison |

---

## Quick Reference

```bash
# Run any MCP locally
cd projects/<path-to-mcp>
pip install -e .
python -m <package_name>

# Or via pyproject entry point
pip install -e .
<mcp-name>
```

## Folder Structure Convention

```
projects/
├── marceau-solutions/       # Company 1 MCPs
│   ├── amazon-seller/
│   ├── fitness-influencer-mcp/
│   ├── instagram-creator/
│   ├── tiktok-creator/
│   └── youtube-creator/
├── swflorida-hvac/          # Company 2 MCPs
│   └── hvac-mcp/
├── shared/                  # Multi-company MCPs
│   ├── apollo-mcp/
│   └── upwork-mcp/
└── global-utility/          # Personal utility MCPs
    ├── md-to-pdf/
    ├── twilio-mcp/
    └── mcp-aggregator/
        └── rideshare-mcp/
```

**Rules:**
- Company-specific MCPs go under their company folder
- Tools used by 2+ companies go in `shared/`
- Personal utilities go in `global-utility/`
- Each MCP is a standalone directory with `pyproject.toml`, `src/`, and `server.json`
