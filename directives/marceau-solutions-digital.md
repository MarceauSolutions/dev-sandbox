# Directive: Marceau Solutions — Digital Tower

## Tower: digital
## Path: projects/marceau-solutions/digital/
## Owner: William Marceau

---

## Purpose
The Digital Tower is Marceau Solutions' AI services business unit. It serves local Naples FL
businesses (HVAC, med spas, dentists, roofing, etc.) with custom AI-powered systems, automation
platforms, and marketplace builds.

## Capabilities
- Client proposals (branded PDF, tiered pricing)
- Platform builds: lead marketplaces, contractor dashboards, bidding systems
- AI automation (lead scoring, CRM automation, voice receptionist)
- Onboarding packets and signed agreements
- Stripe billing setup and management
- Client delivery documentation

## Brand Standards (Non-Negotiable)
- Colors: Dark `#333333` + Gold `#C9963C` — NEVER green `#22c55e`
- Tagline: "Embrace the Pain & Defy the Odds"
- Email: wmarceau@marceausolutions.com
- Phone: (239) 398-5676
- Website: marceausolutions.com
- Calendly: calendly.com/wmarceau/ai-services-discovery

## Client Data Isolation
Each client lives in: `projects/marceau-solutions/digital/clients/[client-name]/`
Never cross-reference one client's data with another.

## Proposal Output Path
`projects/marceau-solutions/digital/proposals/`

## DOE Layer Mapping
- Layer 1 (Directive): This file
- Layer 2 (Orchestration): Claude Code / agent
- Layer 3 (Execution): execution/branded_pdf_engine.py, execution/stripe_payments.py, SMTP

## Delivery Protocol
- PDFs → email wmarceau@marceausolutions.com
- Payment links → SMS to (239) 398-5676
- Always confirm: "Sent [doc] via email and [link] via SMS"
