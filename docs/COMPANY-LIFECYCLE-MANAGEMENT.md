# Company Lifecycle Management

**Purpose**: Manage client relationships through different engagement stages (Active → Retainer → Alumni → Archived)

**Last Updated**: 2026-01-21

---

## Company Status Definitions

### Active
**Definition**: Currently working on active development projects
**Characteristics**:
- Regular development work (weekly or more)
- Multiple projects in progress
- Frequent client communication
- Full automation and monitoring enabled

**Location**: `projects/[company-name]/`

**Examples**:
- Building new features
- Active website updates
- Ongoing automation development

---

### Retainer
**Definition**: Maintenance mode with monthly retainer agreement
**Characteristics**:
- Small updates and tweaks only
- Monthly maintenance fee
- Reduced development hours
- Automation continues but monitored less frequently

**Location**: `projects/[company-name]/` (stays in main projects/)

**README.md Status**: `Status: Retainer`

**Examples**:
- Monthly website content updates
- Quarterly feature additions
- Bug fixes and minor improvements
- Monitoring and uptime maintenance

---

### Alumni
**Definition**: Past client, relationship ended positively, may return
**Characteristics**:
- No active development
- Projects complete and delivered
- Relationship ended on good terms
- Door open for future work

**Location Options**:
1. Keep in `projects/[company-name]/` if likely to return
2. Move to `projects/alumni/[company-name]/` if archived

**README.md Status**: `Status: Alumni`

**Examples**:
- Client moved to in-house team
- Project completed, no ongoing needs
- Client budget constraints (temporary)
- Seasonal business (may return)

---

### Archived
**Definition**: Past client, relationship ended, unlikely to return
**Characteristics**:
- No future work expected
- Relationship ended (any reason)
- Keep for reference/portfolio only
- All automation disabled

**Location**: `projects/archived/[company-name]/`

**README.md Status**: `Status: Archived`

**Examples**:
- Client went out of business
- Relationship ended poorly
- Client chose different vendor
- Client sold/acquired

---

## Folder Structure for Lifecycle

```
projects/
├── [company-1]/                    ← Active (actively developing)
├── [company-2]/                    ← Active
├── [company-3]/                    ← Retainer (stays in main projects/)
│
├── alumni/                         ← Optional: Past clients (good terms)
│   ├── [company-4]/
│   └── [company-5]/
│
└── archived/                       ← Unlikely to return
    ├── [company-6]/
    └── [company-7]/
```

---

## Transitioning Between Stages

### Active → Retainer

**When**: Project development complete, client wants ongoing maintenance

**Steps**:
1. Update README.md status: `Status: Retainer`
2. Document monthly retainer terms
3. Reduce automation monitoring frequency (if applicable)
4. Set up monthly maintenance schedule
5. Update business_id configs if reducing service levels

**Automation Changes**:
- Keep automation running (if they're paying for it)
- Reduce monitoring alerts (less critical)
- Monthly check-ins instead of weekly

**Files to Update**:
```bash
# Update README.md
vim projects/[company-name]/README.md
# Change: Status: Active → Status: Retainer
# Add: Monthly Retainer: $X/month

# Update CLAUDE.md if needed (list of active companies)
vim CLAUDE.md

# Git commit
git add projects/[company-name]/README.md
git commit -m "status: Move [Company] to retainer status

Monthly retainer: $X for [scope of work]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Active/Retainer → Alumni

**When**: Relationship ended positively, door open for future work

**Steps**:
1. **Option A: Keep in projects/** (if likely to return soon)
   - Update README.md status: `Status: Alumni`
   - Keep all code in place
   - Disable automation (unless they're still paying)

2. **Option B: Move to projects/alumni/** (if archived but positive)
   - Create alumni folder if doesn't exist
   - Move entire company folder
   - Update README.md status: `Status: Alumni`
   - Disable automation

**Commands** (Option B):
```bash
# Create alumni folder if needed
mkdir -p projects/alumni

# Move company folder
git mv projects/[company-name] projects/alumni/[company-name]

# Update README.md status
cd projects/alumni/[company-name]
vim README.md
# Change: Status: Active/Retainer → Status: Alumni
# Add: Relationship Ended: YYYY-MM-DD
# Add: Reason: [Brief explanation]

# Stop automation (if using shared tools)
# Remove from shared tool configs or disable business_id

# Git commit
cd /Users/williammarceaujr./dev-sandbox
git add -A
git commit -m "status: Move [Company] to alumni status

Relationship ended: [Date]
Reason: [Brief reason]
Projects delivered: [List main deliverables]

Door open for future work.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Automation Changes**:
- Stop all automation (lead scraping, social media, etc.)
- Disable business_id in shared tools
- Remove from monitoring dashboards

---

### Active/Retainer/Alumni → Archived

**When**: Relationship ended, unlikely to work together again

**Steps**:
1. Create archived folder if doesn't exist
2. Move entire company folder to archived
3. Update README.md status: `Status: Archived`
4. Stop ALL automation
5. Document archive reason
6. Create archive summary

**Commands**:
```bash
# Create archived folder if needed
mkdir -p projects/archived

# Move company folder
git mv projects/[company-name] projects/archived/[company-name]
# OR if coming from alumni
git mv projects/alumni/[company-name] projects/archived/[company-name]

# Update README.md status
cd projects/archived/[company-name]
vim README.md
# Change: Status: [Previous] → Status: Archived
# Add: Archived Date: YYYY-MM-DD
# Add: Archive Reason: [Explanation]

# Create archive summary
cat > ARCHIVE-SUMMARY.md <<'EOF'
# Archive Summary: [Company Name]

**Archived**: YYYY-MM-DD
**Reason**: [Why archived]

## Projects Delivered
- [Project 1]: [Description]
- [Project 2]: [Description]

## Total Revenue
$[amount]

## Lessons Learned
- [Lesson 1]
- [Lesson 2]

## Portfolio Use
- [ ] Can use in portfolio (with permission)
- [ ] Can use as case study (anonymized)
- [ ] Private/NDA - do not share
EOF

# Stop automation
# Remove business_id from all shared tools
# Remove from .env if they had dedicated API keys

# Git commit
cd /Users/williammarceaujr./dev-sandbox
git add -A
git commit -m "archive: Move [Company] to archived status

Archived: [Date]
Reason: [Brief reason]
Total revenue: $[amount]
Projects delivered: [count]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Automation Changes**:
- Stop ALL automation (no exceptions)
- Remove business_id from shared tools
- Remove from monitoring
- Remove dedicated API keys from .env

---

## Checklist Templates

### Moving to Retainer Checklist

```markdown
- [ ] Update README.md status to "Retainer"
- [ ] Document monthly retainer amount and scope
- [ ] Set up recurring invoice (if applicable)
- [ ] Reduce monitoring frequency
- [ ] Schedule monthly check-in meetings
- [ ] Update CLAUDE.md if needed
- [ ] Git commit status change
```

### Moving to Alumni Checklist

```markdown
- [ ] Update README.md status to "Alumni"
- [ ] Document end date and reason (positive)
- [ ] Create project completion summary
- [ ] Stop automation (unless they're paying)
- [ ] Remove from shared tool configs
- [ ] Archive temporary files
- [ ] Ensure all code committed
- [ ] Move to projects/alumni/ (if desired)
- [ ] Send thank you / stay in touch message
- [ ] Add to "past clients" portfolio (if permitted)
- [ ] Git commit status change
```

### Moving to Archived Checklist

```markdown
- [ ] Update README.md status to "Archived"
- [ ] Document archive date and reason
- [ ] Create ARCHIVE-SUMMARY.md
- [ ] Stop ALL automation
- [ ] Remove business_id from all shared tools
- [ ] Remove dedicated API keys from .env
- [ ] Remove from monitoring dashboards
- [ ] Archive login credentials
- [ ] Move to projects/archived/
- [ ] Extract lessons learned
- [ ] Git commit archive
```

---

## Status Indicators in README.md

Every company README.md should have a status line at the top:

```markdown
**Status**: Active | Retainer | Alumni | Archived
```

**With details**:
```markdown
**Status**: Retainer
**Retainer Terms**: $500/month for 5 hours maintenance
**Contract Start**: 2025-06-01
**Contract Renewal**: 2026-06-01
```

```markdown
**Status**: Alumni
**Relationship Ended**: 2025-12-15
**Reason**: Project completed successfully, client went in-house
**Future Work**: Door open, positive relationship
```

```markdown
**Status**: Archived
**Archived Date**: 2025-09-20
**Reason**: Client went out of business
**Total Revenue**: $15,000
**Projects Delivered**: 3
```

---

## Quick Reference Commands

### Check all company statuses
```bash
grep -h "^\*\*Status\*\*:" projects/*/README.md projects/alumni/*/README.md projects/archived/*/README.md
```

### List active companies
```bash
grep -l "Status: Active" projects/*/README.md | xargs -n1 dirname | xargs -n1 basename
```

### List retainer companies
```bash
grep -l "Status: Retainer" projects/*/README.md | xargs -n1 dirname | xargs -n1 basename
```

### List alumni companies
```bash
grep -l "Status: Alumni" projects/*/README.md projects/alumni/*/README.md | xargs -n1 dirname | xargs -n1 basename
```

### List archived companies
```bash
ls projects/archived/
```

---

## Automation Management by Status

### Active
- Full automation enabled
- Real-time monitoring
- All shared tools configured
- Weekly/daily check-ins

### Retainer
- Automation continues (if in scope)
- Reduced monitoring frequency
- Monthly check-ins
- On-demand updates

### Alumni
- **No automation** (unless specifically contracted)
- Remove from shared tool configs
- No monitoring
- Ad-hoc contact only

### Archived
- **Zero automation**
- Remove from ALL configs
- No monitoring
- No contact

---

## Revenue Tracking by Status

**Active**:
- Track project-based revenue
- Invoice per milestone or monthly

**Retainer**:
- Track monthly recurring revenue (MRR)
- Automatic monthly invoicing

**Alumni**:
- Track total historical revenue
- No ongoing revenue

**Archived**:
- Track total historical revenue
- Document for tax/accounting purposes

---

## Communication Patterns

| Status | Frequency | Type | Purpose |
|--------|-----------|------|---------|
| Active | Weekly+ | Meetings, Slack, Email | Project updates, questions |
| Retainer | Monthly | Email, Calls | Maintenance check-ins |
| Alumni | Quarterly | Email | Stay in touch, check for new needs |
| Archived | Never | None | No communication unless they reach out |

---

## Portfolio & Case Study Use

### Active
- Generally NO (work in progress, confidential)
- Ask permission if needed for marketing

### Retainer
- ASK PERMISSION (they're still a client)
- May use as case study with approval

### Alumni
- ASK PERMISSION (positive relationship)
- Good candidates for testimonials

### Archived
- Review NDA terms before sharing anything
- Anonymize if using as case study
- Default: Do not share without permission

---

## See Also

- `docs/FOLDER-STRUCTURE-GUIDE.md` - How to create new company folders
- `CLAUDE.md` - Operating principles
- `.demo-structure-template/company-readme-template.md` - README template
- `scripts/move-company-to-alumni.sh` - Helper script (if created)
- `scripts/move-company-to-archived.sh` - Helper script (if created)
