# Legal Case Manager - Housing Discrimination

> Case management system for navigating a housing discrimination claim. This file contains all SOPs, commands, and references needed to work on the case.

## Overview

This project provides tools and workflows for:
- **Evidence cataloging** with metadata and chain of custody
- **Deadline tracking** for HUD, FCHR, and court filing windows
- **Timeline construction** for chronological case narrative
- **Document generation** from templates (complaints, demand letters)
- **Communication logging** for all party interactions

## Quick Commands

```bash
# Working directory
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/legal-case-manager

# Evidence
python src/evidence_catalog.py add --type photo --date 2026-01-15 --desc "Description"
python src/evidence_catalog.py list
python src/evidence_catalog.py search --keyword "damage"

# Deadlines
python src/deadline_tracker.py check          # Show upcoming deadlines
python src/deadline_tracker.py add --name "HUD Filing" --date 2027-01-15 --alert-days 30,14,7,3,1
python src/deadline_tracker.py alert          # Show overdue/urgent items

# Timeline
python src/timeline_builder.py add --date 2026-01-15 --event "Description of event"
python src/timeline_builder.py generate --format markdown
python src/timeline_builder.py generate --format pdf

# Documents
python src/document_generator.py generate --template hud-complaint --output data/filings/
python src/document_generator.py generate --template demand-letter --output data/filings/
python src/document_generator.py list-templates

# Communication Log
python src/communication_logger.py add --date 2026-02-09 --party "Landlord" --medium email --summary "Sent demand letter"
python src/communication_logger.py list
python src/communication_logger.py list --party "HUD"
```

## Communication Patterns

| You Say | Claude Does |
|---------|-------------|
| "Log evidence" / "Add evidence" | Run evidence_catalog.py add with details |
| "Check deadlines" / "What's due?" | Run deadline_tracker.py check |
| "Add deadline" | Run deadline_tracker.py add |
| "Build timeline" / "Generate timeline" | Run timeline_builder.py generate |
| "Draft HUD complaint" | Run document_generator.py with hud-complaint template |
| "Draft demand letter" | Run document_generator.py with demand-letter template |
| "Log communication" / "I spoke with..." | Run communication_logger.py add |
| "Show all communications with [party]" | Run communication_logger.py list --party |
| "Case summary" / "Where do we stand?" | Run timeline + deadlines + evidence count summary |
| "What should I do next?" | Check deadlines, review pending actions, suggest next steps |

## Case-Specific SOPs

### SOP L1: Evidence Collection

**When**: Any time new evidence is discovered or created

**Workflow**: See `workflows/evidence-collection.md` for full procedure

**Quick Steps**:
1. Identify evidence type: photo, document, screenshot, recording, email, text, witness statement
2. Preserve original (never modify source files)
3. Copy to `data/evidence/` with naming: `YYYY-MM-DD-[type]-[seq].[ext]`
4. Catalog: `python src/evidence_catalog.py add --type [type] --date [date] --desc "[description]"`
5. Verify entry: `python src/evidence_catalog.py list`

**Metadata captured**: Date, type, source, description, relevance to claim, file path, hash (integrity)

---

### SOP L2: Deadline Management

**When**: New filing window opens, court date set, or response deadline established

**Workflow**: See `workflows/deadline-management.md` for full procedure

**Critical Deadlines** (housing discrimination):

| Filing | Deadline | Statute |
|--------|----------|---------|
| **HUD Complaint** | 1 year from discriminatory act | 42 USC 3610(a)(1)(A)(i) |
| **FCHR Complaint** | 365 days from discriminatory act | FL Stat. 760.34(1) |
| **Federal Lawsuit** | 2 years from discriminatory act | 42 USC 3613(a)(1)(A) |
| **State Court Lawsuit** | 2 years (general FL statute) | FL Stat. 95.11 |

**Alert Thresholds**: 90 days, 30 days, 14 days, 7 days, 3 days, 1 day

**Quick Steps**:
1. Add deadline: `python src/deadline_tracker.py add --name "[Name]" --date [YYYY-MM-DD] --alert-days 90,30,14,7,3,1`
2. Daily check: `python src/deadline_tracker.py check`
3. Review alerts: `python src/deadline_tracker.py alert`

---

### SOP L3: Filing Procedure

**When**: Ready to file a complaint, motion, or response

**Workflow**: See `workflows/filing-procedure.md` for full procedure

**Filing Options** (can pursue multiple simultaneously):

**Option A: HUD Administrative Complaint**
1. Complete HUD Form 903 or draft written complaint
2. Generate from template: `python src/document_generator.py generate --template hud-complaint`
3. File online at hud.gov, by mail, or by phone (1-800-669-9777)
4. HUD investigates within 100 days
5. If cause found → conciliation or ALJ hearing
6. Log filing: `python src/communication_logger.py add --party "HUD" --medium online --summary "Filed complaint"`
7. Add response deadline: `python src/deadline_tracker.py add --name "HUD 100-day investigation" --date [date+100]`

**Option B: Florida Commission on Human Relations (FCHR)**
1. File with FCHR (can be dual-filed with HUD)
2. FCHR has 180 days to investigate
3. If no determination → right to sue letter
4. File online at fchr.myflorida.com

**Option C: Federal Court (Fair Housing Act)**
1. Can file directly without exhausting admin remedies
2. 2-year statute of limitations
3. Entitled to actual damages, punitive damages, attorney fees, injunctive relief
4. Generate demand letter first: `python src/document_generator.py generate --template demand-letter`

**Option D: State Court (Florida Fair Housing Act)**
1. FL Stat. Chapter 760
2. Same protections as federal + age and marital status
3. Can pursue state remedies simultaneously with federal

---

### SOP L4: Communication Logging

**When**: ANY interaction with any party (landlord, property management, attorney, HUD, FCHR, court, witnesses)

**Workflow**: See `workflows/communication-log.md` for full procedure

**Quick Steps**:
1. Log immediately after interaction (don't wait)
2. `python src/communication_logger.py add --date [YYYY-MM-DD] --party "[Name]" --medium [email|phone|letter|in-person|text] --summary "[What was discussed]"`
3. If written (email/letter/text): save copy to `data/communications/`
4. Note any promises made, threats received, or admissions
5. Flag if interaction contains evidence of discrimination

**Parties to Track**: Landlord, Property Manager, HOA, Attorney (yours), Attorney (theirs), HUD, FCHR, Court, Witnesses, Others

---

### SOP L5: Timeline & Case Summary

**When**: Preparing case narrative for attorney review, HUD submission, or court filing

**Workflow**: See `workflows/timeline-construction.md` for full procedure

**Quick Steps**:
1. Ensure all events are logged: `python src/timeline_builder.py list`
2. Generate narrative: `python src/timeline_builder.py generate --format markdown`
3. Review for gaps - are there missing dates or events?
4. Cross-reference with evidence: `python src/evidence_catalog.py list`
5. Cross-reference with communications: `python src/communication_logger.py list`
6. Export final version: `python src/timeline_builder.py generate --format markdown --output data/filings/case-timeline.md`

**Case Summary Command** (runs all three):
```bash
echo "=== DEADLINES ===" && python src/deadline_tracker.py check && \
echo "=== EVIDENCE COUNT ===" && python src/evidence_catalog.py count && \
echo "=== RECENT COMMUNICATIONS ===" && python src/communication_logger.py list --last 10
```

---

## Key Legal References

### Federal Law
- **Fair Housing Act (FHA)**: 42 USC 3601-3619
- **Protected Classes**: Race, color, national origin, religion, sex (including gender identity and sexual orientation), familial status, disability
- **Prohibited Acts**: Refusal to rent/sell, discrimination in terms/conditions, intimidation, retaliation
- **Remedies**: Actual damages, punitive damages, attorney fees, injunctive relief
- **Statute of Limitations**: 1 year (HUD complaint), 2 years (federal lawsuit)

### Florida Law
- **Florida Fair Housing Act**: FL Stat. Chapter 760
- **Additional Protected Classes**: Age, marital status (beyond federal protections)
- **FCHR**: Florida Commission on Human Relations (state enforcement agency)
- **Statute of Limitations**: 365 days (FCHR complaint), 2 years (state lawsuit)

### Key Case Law (Research as Needed)
- *Texas Dept. of Housing v. Inclusive Communities Project* (2015) - Disparate impact liability
- *Trafficante v. Metropolitan Life Insurance Co.* (1972) - Standing to sue
- *City of Miami v. Bank of America* (2017) - Proximate cause standard

### Enforcement Agencies
- **HUD**: U.S. Department of Housing and Urban Development - 1-800-669-9777 - hud.gov
- **FCHR**: Florida Commission on Human Relations - 850-488-7082 - fchr.myflorida.com
- **DOJ**: Department of Justice Civil Rights Division (pattern/practice cases)

## Data Security

- **All case data** is in `data/` which is **gitignored**
- **Never commit** evidence, communications, filings, or PII to version control
- **Templates** in `templates/` contain NO case-specific information (safe to commit)
- **Source code** in `src/` contains NO case-specific information (safe to commit)
- **Backup sensitive data** to encrypted external storage separately

## Operating Principle

Be thorough. Be organized. Document everything. Miss nothing.
