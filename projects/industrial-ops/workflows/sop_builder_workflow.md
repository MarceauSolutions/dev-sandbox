# SOP Builder Workflow

**Tower:** industrial-ops
**Priority:** 1 — Boss has already requested the first deliverable
**First SOP:** Front Desk Agent — outlining daily job duties and procedures

---

## Workflow

```
William provides:
  - Role description (who does this job)
  - Step-by-step process notes (can be rough/conversational)
  - Any county-specific terms or system names

Panacea / Claude Code:
  1. Structures notes into SOP format (Purpose, Scope, Responsibilities, Procedure, References)
  2. Generates Markdown source
  3. Converts to PDF via markdown_to_pdf.py
  4. Returns PDF to William for review before delivery

William:
  - Reviews, requests edits
  - Delivers PDF to boss
  - Documents feedback
```

---

## SOP Template Structure

1. **Header** — SOP Number, Title, Department, Effective Date, Author, Approved By
2. **Purpose** — Why this SOP exists (1–2 sentences)
3. **Scope** — Who this applies to
4. **Definitions** — County-specific terms explained
5. **Responsibilities** — Who does what (role-based)
6. **Procedure** — Numbered step-by-step with sub-steps
7. **References** — Related SOPs, systems, contact list
8. **Revision History** — Table of changes

---

## Styling Note

County SOPs should use neutral professional styling — NOT Marceau Solutions gold/charcoal branding.
Use clean black/white/gray with a simple header. County logo can be added if approved.

---

## First Deliverable Checklist

- [ ] William provides front desk agent process notes
- [ ] Panacea structures into SOP draft
- [ ] PDF generated and reviewed
- [ ] Delivered to boss
- [ ] Reaction documented in `data/collier-county/sop_feedback_log.md`
