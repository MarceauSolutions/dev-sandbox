# Template Update Checklist

*Last Updated: 2026-01-22*

When updating outreach templates (SMS or email), ensure ALL channels are updated to maintain consistent messaging.

---

## Template Locations

### SMS Templates
| File | Purpose | Business |
|------|---------|----------|
| `projects/shared/lead-scraper/src/sms_outreach.py` | Cold SMS outreach templates | Marceau Solutions |
| `projects/shared/lead-scraper/src/lead_nurture_scheduler.py` | SMS follow-up templates | Marceau Solutions |
| `projects/shared/lead-scraper/templates/sms/optimized/` | JSON template files | Multi-business |

### Email Templates
| File | Purpose | Business |
|------|---------|----------|
| `projects/shared/lead-scraper/src/cold_outreach.py` | Cold email templates | Marceau Solutions |
| `projects/shared/lead-scraper/src/lead_nurture_scheduler.py` | Email nurture sequences | Marceau Solutions |

### Other Outreach Files
| File | Purpose | Notes |
|------|---------|-------|
| `projects/swflorida-hvac/hvac-distributors/src/email_sender.py` | RFQ emails to distributors | B2B quotes, not cold outreach |
| `execution/form_handler/multi_business_handler.py` | Form response templates | Auto-responders |

---

## Update Checklist

When changing outreach messaging/positioning:

### 1. SMS Templates
- [ ] Update `sms_outreach.py` - SMS_TEMPLATES dictionary
- [ ] Update `lead_nurture_scheduler.py` - SMS_TEMPLATES dictionary
- [ ] Check JSON templates in `templates/sms/optimized/` (if used)
- [ ] Deprecate old templates (don't delete - mark as deprecated)

### 2. Email Templates
- [ ] Update `cold_outreach.py` - TEMPLATES dictionary
- [ ] Update `lead_nurture_scheduler.py` - EMAIL_TEMPLATES dictionary
- [ ] Update template selection logic if needed

### 3. Documentation
- [ ] Update `docs/OUTREACH-LESSONS-LEARNED.md` with reasoning
- [ ] Update `projects/marceau-solutions/docs/LEAD-RESPONSE-TEMPLATES.md`
- [ ] Update `projects/marceau-solutions/docs/PRODUCT-CATALOG.md` if positioning changed

### 4. Testing
- [ ] Dry run SMS with new templates: `python -m src.scraper sms --dry-run --limit 5`
- [ ] Dry run email with new templates: `python -m src.cold_outreach generate --limit 5`
- [ ] Verify personalization variables render correctly

---

## Current Positioning (2026-01-22)

**Our Niche:**
1. **Finding problems clients don't know they have**
2. **Building better solutions than what clients originally asked for**

**Key Principles:**
- Lead with discovery questions, NOT product pitches
- Position as "consultant who finds gaps" not "vendor selling X"
- Use "automation" as umbrella term (encompasses all our products)
- One clear CTA per message
- Match template to business type

**Recommended Primary Templates:**
- SMS: `discovery_question`, `consultant_intro`, `gap_finder`
- Email: `discovery_question`, `consultant_intro`, `gap_finder`

---

## Template Deprecation Process

When deprecating a template:

1. **Don't delete** - Keep for backwards compatibility and reference
2. **Mark as deprecated** - Add `"notes": "DEPRECATED - [reason]"`
3. **Document why** - Add to OUTREACH-LESSONS-LEARNED.md
4. **Update selection logic** - Remove from auto-selection
5. **Create replacement** - Make new template with improved approach

---

## Incident Log

| Date | Template | Issue | Fix |
|------|----------|-------|-----|
| 2026-01-22 | `competitor_hook` (SMS) | Confusing - "gym near you got 23 members" made no sense for wellness spa | Deprecated, created discovery-focused templates |

---

## Contact

Questions about outreach templates? Check:
1. `docs/OUTREACH-LESSONS-LEARNED.md` - Past learnings
2. `projects/marceau-solutions/docs/PRODUCT-CATALOG.md` - What we sell
3. `projects/marceau-solutions/docs/LEAD-RESPONSE-TEMPLATES.md` - Response frameworks
