# STANDARDIZATION.md — Single Source of Truth

**Last Updated:** 2026-03-30
**Owner:** Clawdbot + William

---

## Principle

> "If you say 'I created X', I know exactly where to find it."

Every output has ONE canonical location. No exceptions.

---

## Canonical Locations

### 📞 CALL SHEETS
**Location:** Google Sheets  
**URL:** https://docs.google.com/spreadsheets/d/1e1uSWhdrnlvYpMqUyFiQGxyfxe93VbPLx86TTyum_RE/edit  
**Format:** Priority, Company, Contact, Phone, Industry, Stage, Tier, Score, Notes  
**Updated by:** Clawdbot (on request or via morning automation)  
**Never:** Generate call sheets as local files, copy-paste in chat, or create new sheets

### 📄 PROPOSALS
**Location:** `projects/lead-generation/sales-pipeline/data/proposals/{company_slug}/`  
**Template:** `execution/pdf_templates/proposal_template.py`  
**Format:** Branded PDF, 49KB target size  
**Standard sections:**
1. Cover page (company name, date, Marceau Solutions branding)
2. Problem statement (their pain points)
3. Solution overview (what we provide)
4. Pricing (setup + monthly, clear numbers)
5. Timeline (implementation schedule)
6. Next steps (how to proceed)

**Quality standard:** Every proposal uses the SAME template. No ad-hoc formats.

### 📊 PIPELINE DATA
**Location:** `projects/shared/sales-pipeline/data/pipeline.db`  
**Access:** PA Service (port 8786), Pipeline API (port 5010)  
**Never:** Create separate databases, JSON files, or spreadsheets for pipeline data

### 📈 REPORTS
**Location:** Telegram (delivered to you)  
**Types:**
- Morning Digest: 6:30am ET
- Evening Digest: 9:00pm ET
- Weekly Report: Monday 9am ET

### 🔗 KEY GOOGLE SHEETS

| Purpose | URL |
|---------|-----|
| **Call Sheet** | https://docs.google.com/spreadsheets/d/1e1uSWhdrnlvYpMqUyFiQGxyfxe93VbPLx86TTyum_RE/edit |
| **Scorecard** | https://docs.google.com/spreadsheets/d/1Y5PwloUBbHM8AeiL032_zWy9jjo9vwhyRZkl7qaKw5o/edit |
| **Lead Tracker** | https://docs.google.com/spreadsheets/d/1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA/edit |
| **Client Tracker** | https://docs.google.com/spreadsheets/d/1gWobdkQsa8XCr7xEOXTFJ3t45e2K54bfxQpYLkCqN7Q/edit |

---

## Output Standards

### When Clawdbot says... You find it at...

| Clawdbot says | Location |
|---------------|----------|
| "Here's your call sheet" | Google Sheet link above |
| "Proposal generated for X" | `proposals/{company}/proposal.pdf` |
| "Pipeline updated" | pipeline.db (query via PA) |
| "Digest sent" | Telegram |
| "Report ready" | Telegram |

### Format Standards

**Call Sheet columns (always in this order):**
```
Priority | Company | Contact | Phone | Industry | Stage | Tier | Score | Notes
```

**Proposal pricing (always formatted as):**
```
Setup Fee: $X,XXX (one-time)
Monthly: $XXX/month
```

**Stage names (only these):**
```
Intake → Contacted → Qualified → Meeting Booked → Proposal Sent → Trial Active → Closed Won / Closed Lost
```

**Tier values (only these):**
```
1 = High priority (phone, personalized)
2 = Batch outreach (email, templated)
0 = Unclassified
```

---

## Anti-Patterns (Never Do These)

❌ Generate call sheets as local HTML/PDF files  
❌ Copy-paste data into Telegram instead of linking to sheet  
❌ Create ad-hoc proposal formats per client  
❌ Store pipeline data in JSON files or markdown  
❌ Send different report formats each time  
❌ Use "T1" vs "1" inconsistently for tiers  

---

## Enforcement

When generating ANY output:
1. Check this document for canonical location
2. Use the standard format
3. Provide the link, not the data
4. If no standard exists, CREATE ONE and update this doc

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2026-03-30 | Initial standardization document | Clawdbot |
| 2026-03-30 | Added call sheet Google Sheet as canonical | Clawdbot |
