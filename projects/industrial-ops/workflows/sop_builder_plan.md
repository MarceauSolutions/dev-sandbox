# SOP Builder — Full Build Plan

**Tower:** industrial-ops
**Created:** May 10, 2026
**Status:** Priority 1 — Build first
**Strategic Context:** William's boss has already directly requested an SOP for the front desk agent.
This is a zero-cold-outreach deliverable — the demand exists, the tool just needs to be built.

---

## Executive Summary

A system that takes William's rough process notes (conversational, bullet points, or voice-to-text)
and generates a professional, formatted SOP PDF — ready to hand to a boss, put in a binder,
or upload to a county document management system.

**First deliverable:** Front desk agent SOP (boss-requested)
**Time target:** Process notes in → polished PDF out in under 10 minutes

---

## Why This First

- Zero sales required — the ask already came from the boss
- Uses existing tools (`markdown_to_pdf.py` or `branded_pdf_engine.py` from `execution/`)
- No new infrastructure needed for Milestone 1 — Panacea can generate these today
- Establishes William as someone who gets things done beyond his job description
- Creates the template library for all future SOPs (compounding asset)

---

## How It Works

```
Step 1 — William provides process notes (any format):
  - Rough bullet points about how a job is done
  - Conversational description ("first she logs in to X, then she checks Y")
  - Voice memo transcript
  - Existing notes or printouts he types up

Step 2 — Panacea structures the notes:
  - Identifies steps, roles, systems, exceptions
  - Generates a structured Markdown SOP using the county template
  - Presents draft to William for review

Step 3 — William reviews and approves:
  - Quick edits via Telegram or Claude Code on Mac
  - Panacea regenerates if changes needed

Step 4 — PDF generated and delivered:
  - Clean, professional PDF output
  - County-neutral styling (not Marceau Solutions branding)
  - William delivers to boss
```

---

## SOP Template (County-Neutral Style)

Every SOP follows this structure:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COLLIER COUNTY — [DEPARTMENT NAME]
Standard Operating Procedure

SOP Number:  [DEPT]-SOP-[###]
Title:       [Job/Process Title]
Effective:   [Date]
Version:     1.0
Prepared by: [Name / Role]
Approved by: [Supervisor Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PURPOSE
   [1–2 sentences: why this SOP exists]

2. SCOPE
   [Who this applies to, which locations/systems]

3. DEFINITIONS
   [County-specific or system-specific terms explained]

4. RESPONSIBILITIES
   Role A: [what they own]
   Role B: [what they own]

5. PROCEDURE
   5.1 [Phase/Task Name]
       Step 1: ...
       Step 2: ...
   5.2 [Next Phase]
       Step 1: ...

6. EXCEPTIONS & ESCALATION
   [What to do when the normal process breaks down]

7. REFERENCES
   [Related SOPs, system manuals, contact list]

8. REVISION HISTORY
   | Version | Date | Author | Changes |
```

---

## Styling Notes

- **Color scheme:** Black text, dark navy header, white body — county-appropriate, not branded
- **Font:** Arial or Times New Roman (standard government document fonts)
- **Page size:** Letter (8.5" × 11")
- **Footer:** SOP number, version, page number
- **Logo:** Collier County seal in header if approved by boss; plain text header otherwise
- **No Marceau Solutions branding** — this is a county document

---

## First Deliverable: Front Desk Agent SOP

**Scope:** The front desk agent role at William's department
**What William needs to provide:**
- What does the front desk agent do when they arrive in the morning?
- What systems do they log into?
- How do they handle incoming calls / visitors?
- What forms or logs do they fill out?
- What do they do at end of day?
- Who do they escalate to for different situations?

**What Panacea produces:**
- Complete structured SOP PDF, ready to hand to the boss
- No county IT access required — pure document generation

---

## SOP Library (Future State)

After the first SOP lands well, build a library:

| SOP Number | Title | Status |
|-----------|-------|--------|
| WW-SOP-001 | Front Desk Agent Daily Procedures | 🔵 In progress |
| WW-SOP-002 | Lift Station Inspection Procedure | ⬜ Planned |
| WW-SOP-003 | Alarm Response and Escalation | ⬜ Planned |
| WW-SOP-004 | Work Order Logging (Excel) | ⬜ Planned |
| WW-SOP-005 | Equipment Calibration Record | ⬜ Planned |
| WW-SOP-006 | DFS System Startup / Shutdown | ⬜ Planned |

Each SOP added to the library makes the next one faster to produce.
The library itself becomes the case for recognition — William built the department's entire SOP system.

---

## Milestones

### Milestone 1 — First SOP Delivered (This week)
- [ ] William provides front desk agent process notes (can be rough)
- [ ] Panacea generates structured Markdown SOP
- [ ] PDF generated using `markdown_to_pdf.py` with county-neutral styling
- [ ] William reviews and approves
- [ ] Delivered to boss

### Milestone 2 — SOP Builder Tool (Week 2)
- [ ] Build `src/sop_builder/sop_generator.py` — structured script that takes notes → SOP Markdown
- [ ] County SOP PDF template (neutral styling) baked in
- [ ] CLI: `python sop_generator.py --input notes.txt --sop-number WW-001 --title "Front Desk"`
- [ ] Test with 3 different SOPs

### Milestone 3 — Telegram Interface (Week 3)
- [ ] Panacea accepts SOP requests via Telegram
  > "Build SOP for pump inspection procedure — [pastes notes]"
- [ ] Returns PDF link or sends PDF directly to Telegram
- [ ] William can generate SOPs from his phone in the field

### Milestone 4 — SOP Library Index (Week 4+)
- [ ] Auto-generated index page listing all SOPs with version and date
- [ ] SOPs stored in `data/collier-county/sops/`
- [ ] Version tracking — every edit creates a new version, old version archived

---

## Impact Documentation

Track and record for the salary conversation:
- Time to produce each SOP (target: <10 min from notes to PDF)
- Boss's reaction on delivery
- Whether other departments request SOPs after seeing the first one
- Estimated cost of having a technical writer produce the same documents ($75–$150/hr)
