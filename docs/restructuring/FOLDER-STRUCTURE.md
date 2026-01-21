# Dev-Sandbox Folder Structure

**Last Updated**: 2026-01-21
**Status**: ✅ Reorganized - duplicates removed

---

## Core Principle

**All shared/multi-tenant tools live under `projects/shared-multi-tenant/`**

Individual company-specific projects live under their respective folders (e.g., `projects/marceau-solutions/`, `projects/swflorida-hvac/`).

---

## Directory Map

```
/Users/williammarceaujr./dev-sandbox/
│
├── projects/
│   │
│   ├── shared-multi-tenant/          ← MULTI-COMPANY TOOLS (used by 2+ businesses)
│   │   ├── lead-scraper/             ← Lead generation & cold outreach
│   │   │   ├── input/
│   │   │   │   └── apollo/           ← 📍 DROP APOLLO CSV FILES HERE
│   │   │   ├── src/                  ← Python scripts
│   │   │   ├── config/               ← A/B tests, sequences, Ralph rules
│   │   │   ├── output/               ← Leads, campaigns, analytics
│   │   │   ├── templates/            ← SMS & email templates
│   │   │   │   ├── sms/
│   │   │   │   │   ├── intro/        ← Initial outreach templates
│   │   │   │   │   └── followup/     ← Follow-up templates
│   │   │   │   └── email/
│   │   │   └── ralph/                ← Ralph PRDs
│   │   │
│   │   ├── ai-customer-service/      ← Voice AI phone systems
│   │   │   └── businesses/           ← Per-business Voice AI configs
│   │   │       ├── marceau_solutions.py
│   │   │       └── swflorida_hvac.py
│   │   │
│   │   ├── personal-assistant/       ← Morning digest, calendar, email
│   │   │   ├── src/
│   │   │   │   ├── digest_aggregator.py
│   │   │   │   ├── morning_digest.py
│   │   │   │   └── routine_scheduler.py
│   │   │   └── output/digests/
│   │   │
│   │   └── social-media-automation/  ← X, LinkedIn, TikTok, YouTube
│   │       ├── src/
│   │       ├── config/
│   │       ├── output/
│   │       └── templates/
│   │
│   ├── marceau-solutions/            ← MARCEAU SOLUTIONS COMPANY PROJECTS
│   │   ├── amazon-seller/            ← Amazon FBA operations
│   │   ├── fitness-influencer/       ← Fitness influencer AI tools
│   │   ├── instagram-creator/        ← Instagram automation
│   │   ├── marceausolutions.com/     ← Company website
│   │   ├── tiktok-creator/           ← TikTok automation
│   │   ├── website-builder/          ← Custom website builder
│   │   └── youtube-creator/          ← YouTube automation
│   │
│   ├── swflorida-hvac/               ← SW FLORIDA COMFORT HVAC PROJECTS
│   │   └── hvac-distributors/        ← HVAC equipment RFQ system
│   │
│   ├── global-utility/               ← UNIVERSAL TOOLS (not business-specific)
│   │   ├── apollo-mcp/               ← Apollo.io MCP integration
│   │   ├── mcp-aggregator/           ← MCP routing/billing platform
│   │   ├── md-to-pdf/                ← Markdown to PDF converter
│   │   ├── naples-weather/           ← Naples weather reports
│   │   └── twilio-mcp/               ← Twilio MCP integration
│   │
│   ├── product-ideas/                ← FUTURE PRODUCT IDEAS
│   │   ├── amazon-buyer/
│   │   ├── crave-smart/
│   │   ├── decide-for-her/
│   │   ├── elder-tech-concierge/
│   │   └── uber-lyft-comparison/
│   │
│   └── archived/                     ← OLD/DEPRECATED PROJECTS
│
├── docs/                             ← DOCUMENTATION
│   ├── companies/                    ← Company-specific docs
│   │   ├── marceau-solutions/
│   │   └── swflorida-hvac/
│   └── *.md                          ← Architecture, guides, SOPs
│
├── templates/                        ← REUSABLE TEMPLATES
│   └── companies/
│       ├── marceau-solutions/
│       └── swflorida-hvac/
│
├── output/                           ← CONSOLIDATED OUTPUTS
│   └── companies/
│       ├── marceau-solutions/
│       └── swflorida-hvac/
│
├── execution/                        ← SHARED EXECUTION SCRIPTS (DOE Layer 3)
│
└── .env                              ← ALL API KEYS & CREDENTIALS
