# Workflow: Communication Logging

## Overview
Log every interaction with every party involved in the case. Complete communication records strengthen the case and prevent "he said/she said" disputes.

## When to Use
- After ANY interaction with any party (landlord, attorney, agency, witness)
- Before and after phone calls
- When sending or receiving written communications

## Steps

### 1. Log Immediately After Interaction
Don't wait - log while details are fresh:
```bash
python src/communication_logger.py add \
    --date 2026-02-09 \
    --party "Landlord - [Name]" \
    --medium email \
    --summary "Sent demand letter regarding discriminatory treatment. Letter details conditions and requests remedy within 30 days." \
    --next-action "Follow up if no response by 2026-03-11"
```

### 2. Communication Mediums
| Medium | How to Log | Preservation |
|--------|-----------|--------------|
| `email` | Log summary + save original to data/communications/ | Forward/export as PDF |
| `phone` | Log immediately after call with detailed notes | Note: FL is two-party consent |
| `letter` | Log + scan original to data/communications/ | Keep physical original safe |
| `text` | Log + screenshot to data/evidence/ | Screenshot before deletion |
| `in-person` | Log immediately after with detailed notes | Note date, time, location, witnesses |
| `online` | Log + save screenshot/confirmation | Save page as PDF |
| `voicemail` | Log + save recording if possible | Note date/time received |

### 3. What to Capture
For every interaction, note:
- **Date and time** (be specific)
- **Who** (full name and role)
- **Medium** (how the communication happened)
- **Summary** (what was discussed/communicated)
- **Promises made** by any party
- **Threats or intimidation** (flag immediately)
- **Admissions** (anything that acknowledges discrimination)
- **Witnesses present**
- **Next action required**

### 4. Save Written Communications
```bash
# Save email/letter/document to communications folder
cp [original] data/communications/YYYY-MM-DD-[party]-[type].[ext]
# Example: data/communications/2026-02-09-landlord-demand-letter.pdf
```

### 5. Review Communication History
```bash
# All communications
python src/communication_logger.py list

# Filter by party
python src/communication_logger.py list --party "Landlord"

# Recent only
python src/communication_logger.py list --last 10

# Search by keyword
python src/communication_logger.py search --keyword "repair"
```

### 6. Flag Discrimination Evidence
If a communication contains evidence of discrimination:
```bash
python src/communication_logger.py add \
    --date 2026-02-09 \
    --party "Landlord" \
    --medium phone \
    --summary "Landlord stated [discriminatory statement]" \
    --flag discrimination \
    --next-action "Document as evidence, consult attorney"
```

## Best Practices
- Log **before** a phone call (note intent) and **after** (note what happened)
- Prefer written communication (email > phone) for documentation
- Send follow-up emails after phone calls: "Per our conversation today..."
- Keep a separate notebook for real-time notes during calls
- Never delete communications, even unfavorable ones

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Forgot to log immediately | Log as soon as you remember, note "logged from memory on [date]" |
| Communication from unknown party | Log anyway with "Unknown - [description]" and investigate |
| Threatening communication received | Log, flag, and consult attorney immediately |

## Success Criteria
- [ ] Every interaction logged within 24 hours
- [ ] Written communications preserved in data/communications/
- [ ] Discriminatory statements flagged
- [ ] Follow-up actions tracked
