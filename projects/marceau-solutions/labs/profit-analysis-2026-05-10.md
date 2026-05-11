# Marceau Solutions — Project Profit Viability Analysis
**Date:** May 10, 2026 | **Method:** Full GitHub history review + live market research

---

## Verdict (Bottom Line Up Front)

**Productize the AI Phone Agent first. Start this weekend.**
It is fully built, already deployed, 83–85% gross margin, and competitors charge $297–$997/month.
Every other project either needs significant build work or has a lower margin ceiling.

---

## Full Rankings

| Rank | Project | State | Rev @ 3 Clients | Rev @ 10 Clients | Build Left | Margin | Score |
|------|---------|-------|-----------------|------------------|-----------|--------|-------|
| 1 | AI Phone Agent | ✅ Live on EC2 | $1,191/mo + $1,491 setup | $3,970/mo | 1 weekend | 83–85% | ⭐⭐⭐⭐⭐ |
| 2 | Lead Gen DFY Service | ✅ Operational | $5,400/mo | $18,000/mo (team needed) | 2 weekends | 70–80% | ⭐⭐⭐⭐ |
| 3 | n8n Automation Consulting | ✅ 83 workflows | $1,500/mo retainers | $5,000/mo | 0 (sell existing) | 85%+ | ⭐⭐⭐ |
| 4 | Amazon Seller MCP | ✅ Published PyPI | $147/mo | $490/mo | 2–3 weekends | 70% | ⭐⭐ |
| 5 | Product Books (passive) | 🔶 In progress | $300–$500/mo | $1,000–$3,000/mo | Finish writing | 95% | ⭐⭐ |

---

## #1 — AI Phone Agent (GO — THIS WEEKEND)

**What it is:** Twilio + ElevenLabs voice clone handles inbound calls, qualifies callers, warms transfers,
sends Telegram alerts. Already live at ai-phone.marceausolutions.com on EC2.

**Why it wins:**
- Zero new code — 795 lines of production Python, 14 endpoints, systemd deployed
- Demo is the product: call (855) 239-9364, hear it work, prospect is sold
- Competitors: Smith.ai ($255–$1,275/mo), Ruby ($319–$1,079/mo), My AI Front Desk ($65–$150/mo white-label)
- William's pricing: $297–$497/month at $50–$80/month COGS = 83–85% margin
- Target: Naples/Bonita Springs HVAC, plumbers, med spas, electricians, trades businesses

**What to build (1 weekend):**
1. `client_setup.sh` — accepts business name, Twilio number, ElevenLabs agent ID, spins up named instance
2. One-page pitch PDF (use existing `execution/branded_pdf_engine.py`)
3. UptimeRobot monitoring on the endpoint (free)

**Customer acquisition (automated):**
1. Run existing lead gen system targeting Naples HVAC/plumber/med spa (<10 employees)
2. SMS/email sequence: "74% of contractor calls go unanswered. We built the fix."
3. 30-day free trial offer to close the first 3 clients
4. Pipeline follows up automatically — no extra work

**Bundle upsell ($497/mo):** AI Receptionist + n8n automated follow-up workflows.
Competes against a $3,500/month human receptionist. Easy sell.

---

## #2 — Lead Gen Done-For-You ($1,500–$2,500/mo per client)

Fully operational outreach stack. Sell it as a managed service — William runs campaigns on behalf
of local B2B clients. Apollo.io + Twilio SMS + Gmail sequences + pipeline tracking all live.

**Constraint:** 5–8 hours/client/month. At 5 clients = 25–40 hours/month.
Price at $2,000+ to make the time worth it. Secondary priority — start after phone agent has 3 clients.

---

## #3 — n8n Automation Consulting (upsell only)

83 live workflows. Best positioned as an upsell to phone agent clients, not a standalone product.
"AI Receptionist + follow-up automation" at $497/month is a stronger sell than either product alone.

---

## Projects to Shelve

| Project | Reason |
|---------|--------|
| Call Coach | Market dominated by Gong/Chorus/Fireflies. Minimal code exists. |
| Amazon Seller MCP | MCP ecosystem too small in 2026. Revisit 2027. |
| Apollo MCP | Give away free to lead gen clients as retention tool. |
| FitAI / Video Tools | CapCut, Descript, Opus Clip dominate. No differentiation. |
| BoabFit white-label | Trainerize/Glofox too entrenched. Keep as Julia's service only. |
| Power BI MCP | Internal use only (industrial-ops). Too much build work for side income. |
| Grok Code | Ambitious but not monetizable near-term. |

---

## Conflict of Interest Reminder

Industrial-ops tower (SOP Builder, Knowledge Base, Excel/Power BI MCPs) is explicitly internal-use
for Collier County. Do not productize without formal arrangement through county chain of command.
Protects William's primary income and health benefits.

---

## Sources (Market Pricing Verified)

- Smith.ai AI Receptionist: $255–$1,275/month
- Ruby Receptionists: $319–$1,079/month
- My AI Front Desk white-label: $65–$150/month per reseller seat
- Trillet AI Voice (HVAC-focused): pricing confirmed
- B2B Lead Gen Agency (Cleverly, Reply.io): $2,000–$15,000/month market rate
- 74% contractor missed-call rate: NextPhone study of 13,175 calls

*Saved by Panacea, May 10 2026. Full agent report available on request.*
