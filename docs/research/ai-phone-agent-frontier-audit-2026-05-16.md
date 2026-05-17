# AI Phone Agent Frontier Audit — May 2026

**Marceau Solutions | Research Analyst | 2026-05-16**
**Stack audited:** Twilio + ElevenLabs ConvAI (`eleven_flash_v2`, `gemini-2.5-flash`) + Flask on EC2

---

## Executive Summary

The stack is architecturally sound and using credible components. ElevenLabs ConvAI with Twilio native stream integration is a legitimate production approach — not a toy. However, three specific gaps are costing quality and margin:

1. `eleven_flash_v2` has been superseded by `v2.5` and is a free upgrade sitting unclaimed in the dashboard
2. There is exactly one mid-call tool registered (`transfer_to_william`) — zero KB lookup, zero CRM write, zero calendar check — so the agent hallucinates on pricing and coverage questions
3. The Polly.Joanna fallback is a demo-killing voice quality cliff if ElevenLabs has any downtime

The $297–$697 pricing holds against competitors, but only if the product delivers capabilities that $79–$149/month white-label SaaS products do not. That gap does not fully exist yet.

**VERDICT: CONDITIONAL GO** — don't rebuild, don't switch platforms. Fix the three gaps below before signing a second client.

---

## 1. Voice Stack: What SOTA Looks Like in May 2026

| Platform | End-to-End Latency | Interruption Handling | All-In Cost/Min | Best For |
|---|---|---|---|---|
| **ElevenLabs ConvAI (current)** | 450–750ms | Native turn-taking model | $0.08–$0.12 | Voice quality, managed stack |
| Retell AI | 500–700ms | Built-in | $0.07–$0.31 | Fast deploy, local services |
| Vapi | 600–900ms | Custom VAD required | $0.10–$0.20 | Multi-LLM flexibility |
| Bland AI | 700–1000ms | Limited | $0.09–$0.14 | High-volume outbound only |
| OpenAI Realtime API | 300–500ms | Native VAD + cancel event | $0.06–$0.30 | Lowest latency, complex build |
| My AI Front Desk | Unknown | Managed | $79–$149/mo flat | White-label resellers |

**Assessment:** ElevenLabs at 450–750ms is competitive. The native Twilio stream (signed URL) avoids the WebSocket relay penalty that Vapi and Retell add — a real architectural advantage. OpenAI Realtime API has materially lower latency but requires a full custom STT/VAD/interruption build (2–3 weekends minimum). Not worth it for solopreneur capacity.

The `gemini-2.5-flash` LLM wired into the ElevenLabs agent is the correct choice per ElevenLabs' own recommendation for real-time phone agents.

**`eleven_flash_v2` is outdated.** v2.5 has ~75ms model inference (down from ~150ms) and improved prosody. Free upgrade in the ElevenLabs dashboard. Do it before the next demo.

Sources: [TokenMix latency benchmark](https://tokenmix.ai/blog/voice-ai-api-realtime-vs-gemini-live-vs-elevenlabs-2026) | [Ringlyn per-minute pricing 2026](https://www.ringlyn.com/blog/ai-voice-agent-pricing-per-minute-2026/) | [OpenAI Realtime interruption](https://openai.com/index/delivering-low-latency-voice-ai-at-scale/) | [ElevenLabs ConvAI docs](https://elevenlabs.io/docs/conversational-ai/customization/llm)

---

## 2. Agentic Loop: What Top Systems Do

Top-tier phone agents in May 2026 use **structured multi-turn with tool dispatch** — not ReAct, not plan-and-execute. The LLM receives a tool manifest at session start. Mid-conversation it calls tools like `check_calendar_availability`, `lookup_kb_answer`, `create_crm_lead`. Results return as JSON; voice resumes within 200–400ms.

The current agent has exactly **one registered tool**: `transfer_to_william`. The `/elevenlabs-tool/transfer` endpoint is correctly implemented — right pattern, wrong scope.

What leading service-business deployments expose (all achievable with ElevenLabs server-side tools + existing n8n):

1. **`lookup_kb`** — returns FAQ JSON (pricing, coverage, services) — prevents hallucination
2. **`capture_lead`** — fires after Q2 to write partial lead to CRM mid-call — prevents data loss on hangups
3. **`check_calendar`** — Cal.com or Calendly API — agent offers specific appointment slots
4. **`send_confirmation_sms`** — Twilio SMS post-qualification
5. **`transfer_to_william`** — already implemented

ElevenLabs ConvAI supports all of these natively. An n8n workflow template for voice-based booking with ElevenLabs + Cal.com already exists in the n8n template library.

Sources: [ElevenLabs tool calling](https://elevenlabs.io/docs/conversational-ai/customization/tools/client-tools) | [ElevenLabs + Cal.com n8n template](https://n8n.io/workflows/5670-voice-based-appointment-booking-system-with-elevenlabs-ai-and-calcom/) | [Agentic AI design patterns 2026](https://www.innovatrixinfotech.com/blog/agentic-ai-design-patterns-react-reflection-tool-use)

---

## 3. Competitor Pricing — HVAC / Med Spa / Local Services ICP

| Competitor | Model | Price | ICP Match |
|---|---|---|---|
| Smith.ai AI Receptionist | Human + AI hybrid | $255–$1,275/mo | Yes, hybrid |
| Ruby Receptionists | Human-first | $319–$1,079/mo | Yes, expensive |
| My AI Front Desk | White-label SaaS | $79–$149/mo | **Direct low-end threat** |
| Dialzara | Managed AI | $99–$500/mo | Yes |
| Trillet AI (HVAC) | Vertical SaaS | Undisclosed | Yes — vertical competitor |
| Retell AI (developer) | Usage-based | $0.07–$0.31/min | No portal for end clients |

**William's $297–$697/mo pricing is correctly positioned above commodity.** The real threat is My AI Front Desk resellers charging $197–$250/mo to the same Naples HVAC ICP. The defense: William's agent is per-client customized (persona, qualifying questions, transfer numbers), includes SMS follow-up automation (n8n), and will have KB + calendar tools that flat-rate SaaS products omit. **That differentiation must be real and demonstrable in the demo — currently it is not fully real.**

Sources: [My AI Front Desk pricing](https://www.myaifrontdesk.com/pricing) | [AI receptionist pricing 2026](https://ai-receptionist.com/pricing-comparison/) | [Retell AI pricing](https://www.retellai.com/pricing)

---

## 4. Specific Gaps in the Current Stack

**Gap 1 — Fallback path destroys the demo.** If ElevenLabs returns non-200 on the signed URL call, code falls back to `voice='Polly.Joanna'` with basic `<Gather>` and a "I didn't hear a message. Goodbye!" dead-end. A prospect calling during any ElevenLabs incident gets a 2005-era IVR. The demo is the entire sales motion; a broken demo ends the deal. **Fix:** swap Polly fallback for pre-recorded MP3 + `<Record>` voicemail. 30 min.

**Gap 2 — Agent hallucinates on specifics, no KB.** `agent_config.json` encodes qualifying questions but agent has no `lookup_kb` tool. Callers asking "do you cover Fort Myers?" or "what does the $297 plan include?" get either "I don't know" or hallucinations. **Fix:** n8n webhook returning FAQ JSON, registered as ElevenLabs server-side tool. 3–4 hours.

**Gap 3 — No mid-call lead capture — partial calls lose data.** `webhook_url` fires post-call. If caller hangs up after Q2, no lead record. **Fix:** register `capture_lead` tool that fires to n8n after Q2 answers. 2 hours.

**Gap 4 — Per-client isolation is unbuilt.** One agent ID, one voice. GTM plan promises custom persona per client. The `client_setup.sh` script called out as Week 1 deliverable does not exist. Taking a second client means manual ElevenLabs agent creation + Flask config editing every time. **Fix:** Python script wrapping ElevenLabs agent create API + Twilio subaccount create. 4–6 hours. **This blocks all growth beyond 1 client.**

**Gap 5 — `eleven_flash_v2` not upgraded to v2.5.** Free upgrade in dashboard. Do it today.

---

## 5. Top 3 Highest-ROI Upgrades (4–8 hour budget)

**Upgrade 1 — KB tool + anti-hallucination system (3–4 hours) — HIGHEST ROI**
Register a `lookup_kb` server-side tool in ElevenLabs agent config. One n8n webhook returning JSON keyed by topic (pricing, coverage, services, process, FAQ). The agent calls it automatically when callers ask specifics. The difference between a demo that closes and one that creates doubt. n8n infrastructure already live.

**Upgrade 2 — Client isolation script (4–6 hours) — BLOCKS GROWTH**
Build `client_setup.py` using ElevenLabs REST API + Twilio subaccounts API. Input: client JSON config. Output: live client instance in 5 minutes. Without this, the business cannot scale past 1 client.

**Upgrade 3 — Replace Polly fallback + mid-call lead capture (2 hours) — RISK MITIGATION**
Two changes in `app.py` and ElevenLabs config. Replace Polly TTS fallback with pre-recorded voicemail + `<Record>`. Register `capture_lead` tool to fire to n8n after Q2. Protects against the two most common failure modes.

---

## Red Flags

- **COGS may be understated at volume.** At 200 min/month per client (realistic for busy HVAC), ElevenLabs alone at $0.08/min = $16/month. Twilio adds $5–$10. COGS is $30–$40/month per client at moderate volume — margin holds. At 400+ min/month, add a "telecom cost pass-through above 300 minutes" clause.
- **ElevenLabs pricing stability risk.** Two pricing structure changes in 18 months. Whether current per-minute rates are contractually locked is UNVERIFIED.
- **Confidence level: MEDIUM.** Latency figures are from third-party benchmarks, not William's actual call logs. Pull median latency from ElevenLabs agent call history before making specific latency claims to prospects.
