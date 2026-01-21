# Folder Structure - Quick Reference

## Where to Drop Files

### Apollo CSV Export
```
projects/shared-multi-tenant/lead-scraper/input/apollo/
└── apollo_export_2026-01-21.csv  ← DROP HERE
```

### New SMS Template
```
projects/shared-multi-tenant/lead-scraper/templates/sms/intro/
└── new_template.txt  ← CREATE HERE
```

## Key Locations

| Resource | Path |
|----------|------|
| Lead Database | `projects/shared-multi-tenant/lead-scraper/output/leads.json` |
| Campaign Sequences | `projects/shared-multi-tenant/lead-scraper/output/follow_up_sequences.json` |
| A/B Tests | `projects/shared-multi-tenant/lead-scraper/config/ab_tests.json` |
| Apollo Import | `projects/shared-multi-tenant/lead-scraper/input/apollo/` ← CSV HERE |
| SMS Templates | `projects/shared-multi-tenant/lead-scraper/templates/sms/intro/` |
| All API Keys | `.env` (root) |

## Templates Created (Ralph Deliverables)

✅ MarceauSolutions:
- `templates/sms/intro/marceau_social_proof.txt` (152 chars)
- `templates/sms/intro/marceau_question.txt` (154 chars)
- `templates/sms/intro/marceau_value_prop.txt` (156 chars)

✅ SW Florida Comfort HVAC:
- `templates/sms/intro/hvac_social_proof.txt` (157 chars)
- `templates/sms/intro/hvac_question.txt` (147 chars)
- `templates/sms/intro/hvac_value_prop.txt` (156 chars)

## Duplicates Removed

❌ `projects/lead-scraper/` - Empty, deleted
❌ `projects/social-media-automation/` - Docs moved to shared-multi-tenant, deleted

✅ Single Source of Truth:
- `projects/shared-multi-tenant/lead-scraper/` - ACTIVE
- `projects/shared-multi-tenant/social-media-automation/` - ACTIVE

## Usage: Import Apollo CSV

```bash
# 1. Download from Apollo.io → save to Downloads
# 2. Move to import directory
mv ~/Downloads/apollo_export.csv projects/shared-multi-tenant/lead-scraper/input/apollo/

# 3. Import
cd projects/shared-multi-tenant/lead-scraper
python -m src.apollo_import import --input input/apollo/apollo_export.csv
```

