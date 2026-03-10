# Workflow: Evidence Collection

## Overview
Systematically collect, preserve, and catalog evidence for the housing discrimination case. Every piece of evidence must be preserved in its original form, properly named, and cataloged with metadata.

## When to Use
- New evidence discovered (photos, emails, documents)
- Witness statement obtained
- Screenshot captured
- Recording made (where legally permitted)

## Prerequisites
- `data/evidence/` directory exists
- `src/evidence_catalog.py` available

## Steps

### 1. Identify Evidence Type
| Type | Examples |
|------|----------|
| `photo` | Property damage, living conditions, notices posted |
| `document` | Lease, notices, letters, policies, rules |
| `screenshot` | Text messages, social media, online listings |
| `email` | Correspondence with landlord/management |
| `recording` | Phone calls, meetings (FL is two-party consent state!) |
| `witness` | Written or recorded statements from witnesses |
| `financial` | Receipts, bank statements, payment records |
| `official` | Court records, government documents, inspection reports |

### 2. Preserve Original
- **Never modify** the original file
- Copy to `data/evidence/`
- Use naming convention: `YYYY-MM-DD-[type]-[sequential].[ext]`
- Example: `2026-01-15-photo-001.jpg`, `2026-02-01-email-003.pdf`

### 3. Catalog the Evidence
```bash
python src/evidence_catalog.py add \
    --type photo \
    --date 2026-01-15 \
    --desc "Mold damage in bedroom ceiling - reported to landlord 3 times" \
    --source "Personal phone camera" \
    --relevance "Shows habitability issue and landlord neglect" \
    --file "data/evidence/2026-01-15-photo-001.jpg"
```

### 4. Verify Entry
```bash
python src/evidence_catalog.py list
```

### 5. Cross-Reference
- Does this evidence relate to an existing timeline event? If not, add one.
- Does this evidence support or contradict other evidence?
- Who else can corroborate this evidence?

## Florida Recording Law
Florida is a **two-party consent state** (FL Stat. 934.03). You MUST have consent from ALL parties before recording a conversation. Violation is a felony. Exception: recording in public places where there is no reasonable expectation of privacy.

## Chain of Custody
For each piece of evidence, track:
- **Who** collected it
- **When** it was collected
- **Where** it was stored
- **How** it was preserved (original format, copies made)

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Evidence file too large | Compress or store externally, note location in catalog |
| Unsure if something is evidence | When in doubt, preserve it. Better to have it and not need it. |
| Evidence from third party | Note source and obtain written permission if possible |

## Success Criteria
- [ ] Original preserved unmodified
- [ ] File named with date-type-seq convention
- [ ] Cataloged with all metadata fields
- [ ] Cross-referenced with timeline
