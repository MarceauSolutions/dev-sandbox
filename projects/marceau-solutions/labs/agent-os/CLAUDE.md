# AgentOS — Claude Code Operating System

> **Status**: Scoping
> **Tower**: Labs
> **Product Type**: Digital download (template package)
> **Price Tiers**: $497 / $1,497 / $2,997

## What Is It

A battle-tested, self-configuring operating system for Claude Code that transforms it from a chatbot into an autonomous business partner. Buyer downloads the package, drops it into their repo, opens Claude Code — and the AI configures itself by interviewing the user about their business, stack, and workflows.

## The Core Insight

The product is **self-installing**. The CLAUDE.md template includes onboarding instructions that tell Claude Code: "When you detect this is a fresh install, walk the user through setup." The AI fills in every blank — business name, contacts, deploy targets, API keys, communication preferences. Zero manual configuration.

## What Ships In The Package

### Tier 1: "The Framework" — $497
```
agent-os/
├── CLAUDE.md                    # Master agent config (templatized)
├── .claude/
│   ├── commands/                # 8 slash commands (/deploy, /test, etc.)
│   ├── hooks/                   # 10 guard hooks (cost, stack, tool-reuse)
│   └── settings.local.json      # Permission defaults
├── memory/
│   ├── MEMORY.md                # Memory index template
│   └── templates/               # Memory file templates by type
├── docs/
│   ├── setup-guide.md           # "Drop in and go" instructions
│   └── execution-discipline.md  # The E1-E12 rules with origin stories
└── README.md                    # Sales page / quick start
```

### Tier 2: "The Full System" — $1,497
Everything in Tier 1, plus:
```
├── docs/
│   └── sops/                    # All 37 SOPs (genericized)
│       ├── INDEX.md
│       ├── sop-01-*.md through sop-37-*.md
│       ├── deployment.md
│       ├── testing-strategy.md
│       ├── architecture-guide.md
│       └── service-standards.md
├── execution/                   # Shared utility scripts
│   ├── branded_pdf_engine.py    # PDF generation
│   ├── send_email.py            # SMTP email
│   ├── sms_sender.py            # Twilio SMS
│   └── ... (genericized subset)
├── scripts/
│   ├── health_check.py          # System health monitor
│   ├── inventory.py             # Tool search
│   ├── daily_standup.sh         # Morning briefing
│   └── ... (launch scripts)
├── three-agent/
│   ├── architecture.md          # Mac + EC2 agent design
│   ├── clawdbot-setup.md        # Telegram bot setup guide
│   ├── ec2-sync.md              # Git-based sync protocol
│   ├── handoff-template.md      # HANDOFF.md template
│   └── n8n/
│       ├── patterns.md          # Workflow patterns + gotchas
│       └── starter-workflows/   # Importable workflow JSONs
└── session-management/
    ├── session-history.md       # Template
    ├── system-state.md          # Template
    └── architecture-decisions.md # Cross-agent conventions template
```

### Tier 3: "Done-With-You" — $2,997-$4,997
Everything in Tier 2, plus:
- 3x 60-min consulting calls (Calendly scheduling)
- Custom CLAUDE.md written for their specific business
- EC2 + Clawdbot deployment assistance
- 30 days async support (email/Telegram)
- Custom SOP writing for their top 5 workflows

## Self-Configuration Flow

When a buyer drops AgentOS into their repo and opens Claude Code, the CLAUDE.md detects it's a fresh install (no `.agent-os-configured` marker file) and triggers the onboarding sequence:

### Phase 1: Identity (30 seconds)
- "What's your name?"
- "What's your business/project?"
- "What's your role?" (solo dev, agency owner, founder, etc.)
- "What's your tech stack?"

### Phase 2: Infrastructure (2 minutes)
- "Do you have a server/VPS?" → configures single-agent or multi-agent
- "Do you use n8n/automation tools?" → enables/disables automation SOPs
- "What communication channels?" → SMS, email, Telegram, Slack
- "Where do you deploy?" → GitHub Pages, Vercel, AWS, etc.

### Phase 3: Preferences (1 minute)
- "How should I communicate?" → terse vs detailed, emoji preference
- "What should I never do without asking?" → custom safety rules
- "Any tools/services you want me to avoid?"

### Phase 4: Write Config
- AI fills in CLAUDE.md with all answers
- Creates personalized MEMORY.md
- Creates `.agent-os-configured` marker
- Runs first health check
- "You're set up. Here's what I can do for you now."

Total onboarding: ~5 minutes, zero manual file editing.

## Target Buyers

1. **Solo developers** tired of Claude Code forgetting context between sessions ($497)
2. **Agency owners** who want AI-augmented operations across their business ($1,497)
3. **Technical founders** who want a "second brain" dev setup without 3 months of trial-and-error ($1,497)
4. **Non-technical business owners** who need hand-holding to set it up ($2,997)

## Distribution

- **Platform**: Gumroad or LemonSqueezy (digital download)
- **Format**: ZIP file containing the full directory structure
- **Updates**: Buyers get version updates (major releases, new SOPs)
- **Support**: Discord community (free), async consulting (Tier 3 only)

## Competitive Landscape

| Competitor | Price | What They Sell | Our Edge |
|-----------|-------|---------------|----------|
| Cursor Rules templates | Free-$50 | Single config files | We sell a complete operating system |
| AI prompt courses | $200-$2K | Education, not tooling | Ours is plug-and-play, not "learn then build" |
| SaaS boilerplates | $249-$399 | Code templates | We change how the AI *thinks*, not just code |
| DevOps starter kits | $50-$500 | Infrastructure templates | We include the AI agent layer on top |
| Agency ops frameworks | $500-$2K | Process docs | Ours is machine-readable + self-configuring |

**Key differentiator**: Nobody else sells a self-configuring AI agent operating system. The closest thing is scattered `.cursorrules` files on GitHub. We're selling months of battle-tested iteration in a drop-in package.

## Revenue Projections (Conservative)

| Scenario | Monthly Sales | Revenue/Month |
|----------|--------------|---------------|
| Low (5 Tier 1, 2 Tier 2) | 7 units | $5,479 |
| Medium (10 Tier 1, 5 Tier 2, 1 Tier 3) | 16 units | $15,467 |
| High (20 Tier 1, 10 Tier 2, 3 Tier 3) | 33 units | $33,910 |

## Marketing Angles

1. **"Your AI forgot everything again?"** — Pain point: Claude Code has no persistent memory or discipline
2. **"3 months of iteration, 5 minutes to install"** — Value prop: skip the learning curve
3. **"The operating system Claude Code should have shipped with"** — Positioning: essential upgrade
4. **Video demo**: Show before/after of Claude Code with and without AgentOS — the difference is dramatic
5. **Twitter/X thread**: "I spent 3 months turning Claude Code into an autonomous business partner. Here's what I learned." → funnel to product page

## Build Checklist

- [ ] Genericize CLAUDE.md (strip personal info, create template variables)
- [ ] Genericize all 37 SOPs
- [ ] Genericize execution scripts (remove business-specific logic)
- [ ] Build self-configuration onboarding flow
- [ ] Create setup guide with screenshots
- [ ] Record demo video (before/after)
- [ ] Set up Gumroad/LemonSqueezy storefront
- [ ] Write sales page copy
- [ ] Build landing page (can use our website-builder)
- [ ] Create Discord community
- [ ] Launch Twitter thread + Product Hunt
- [ ] Package Tier 1 ZIP
- [ ] Package Tier 2 ZIP
- [ ] Define Tier 3 consulting workflow

## Generated Files
- `CLAUDE.md` — this file (product spec + project config)
