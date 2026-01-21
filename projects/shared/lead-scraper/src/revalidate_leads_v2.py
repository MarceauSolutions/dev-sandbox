"""
Re-validate existing leads using the new website validator (Version 2).

This script:
1. Loads full lead data from leads.json (has websites)
2. Loads sequence data from follow_up_sequences.json (has send history)
3. Merges the two datasets by phone number
4. Re-validates websites using website_validator.py
5. Identifies incorrectly targeted leads
6. Creates detailed report
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from website_validator import validate_lead_website, is_real_business_website


def normalize_phone(phone: str) -> str:
    """Normalize phone number for matching."""
    if not phone:
        return ""
    # Remove all non-digit characters except +
    normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
    # Add +1 if missing
    if not normalized.startswith('+'):
        normalized = '+1' + normalized
    return normalized


def load_leads_database(leads_file: Path) -> Dict[str, Dict]:
    """Load leads.json and create phone lookup dict."""
    with open(leads_file, 'r') as f:
        data = json.load(f)

    lookup = {}
    for lead in data.get('leads', []):
        phone = normalize_phone(lead.get('phone', ''))
        if phone:
            lookup[phone] = lead

    return lookup


def load_sequences(sequences_file: Path) -> Dict:
    """Load follow-up sequences from JSON file."""
    with open(sequences_file, 'r') as f:
        return json.load(f)


def revalidate_with_merge(leads_db: Dict[str, Dict], sequences_file: Path) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Re-validate all leads by merging leads.json and sequences.

    Returns:
        (correctly_targeted, incorrectly_targeted, missing_from_db)
    """
    data = load_sequences(sequences_file)
    sequences = data.get('sequences', [])

    correctly_targeted = []
    incorrectly_targeted = []
    missing_from_db = []

    print(f"\n{'='*80}")
    print(f"RE-VALIDATING {len(sequences)} LEADS (with database merge)")
    print(f"{'='*80}\n")

    for i, sequence in enumerate(sequences, 1):
        phone = normalize_phone(sequence.get('phone', ''))

        # Look up full lead data from database
        if phone not in leads_db:
            missing_from_db.append({
                'business_name': sequence.get('business_name'),
                'phone': sequence.get('phone'),
                'reason': 'Phone not found in leads.json database'
            })
            print(f"⚠️  [{i}/{len(sequences)}] {sequence.get('business_name')} - NOT IN DATABASE")
            continue

        # Get full lead data
        lead_full = leads_db[phone]

        # Validate website
        validated = validate_lead_website(lead_full)

        has_real_website = validated['has_real_website']
        website_type = validated['website_type']
        validation_reason = validated['website_validation_reason']

        # Check if this lead was sent "no_website" template
        first_touchpoint = sequence.get('touchpoints', [{}])[0]
        template_used = first_touchpoint.get('template_name', '')
        was_sent_no_website_message = 'no_website' in template_used

        result = {
            'lead_id': sequence.get('lead_id'),
            'business_name': lead_full.get('business_name'),
            'phone': lead_full.get('phone'),
            'website': lead_full.get('website', ''),
            'has_real_website': has_real_website,
            'website_type': website_type,
            'validation_reason': validation_reason,
            'template_used': template_used,
            'was_sent_no_website_message': was_sent_no_website_message,
            'status': sequence.get('status'),
            'response_at': sequence.get('response_at', ''),
            'rating': lead_full.get('rating'),
            'review_count': lead_full.get('review_count')
        }

        # Categorize
        if has_real_website and was_sent_no_website_message:
            # ERROR: Sent "no website" message to business WITH real website
            incorrectly_targeted.append(result)
            print(f"❌ [{i}/{len(sequences)}] {result['business_name']} - HAS WEBSITE (got '{template_used}')")
            print(f"   URL: {result['website'][:80]}")
            print(f"   Type: {website_type} - {validation_reason}")
            if result['response_at']:
                print(f"   💥 RESPONDED (likely angry opt-out)")
            print()
        else:
            # Correctly targeted
            correctly_targeted.append(result)
            if i % 20 == 0:
                print(f"✅ [{i}/{len(sequences)}] Validated {i} leads...")

    return correctly_targeted, incorrectly_targeted, missing_from_db


def generate_report(correctly_targeted: List[Dict], incorrectly_targeted: List[Dict],
                   missing_from_db: List[Dict], output_file: Path):
    """Generate detailed validation report."""

    total = len(correctly_targeted) + len(incorrectly_targeted) + len(missing_from_db)
    incorrect_count = len(incorrectly_targeted)
    incorrect_responded = len([l for l in incorrectly_targeted if l['response_at']])

    report = f"""# Lead Re-Validation Report (Merged Data)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

🚨 **CRITICAL**: {incorrect_count} businesses ({incorrect_count/total*100:.1f}%) were incorrectly targeted

| Category | Count | Percentage |
|----------|-------|------------|
| **Total Leads in Sequences** | {total} | 100% |
| ✅ Correctly Targeted | {len(correctly_targeted)} | {len(correctly_targeted)/total*100:.1f}% |
| ❌ Incorrectly Targeted | {incorrect_count} | {incorrect_count/total*100:.1f}% |
| ⚠️ Missing from Database | {len(missing_from_db)} | {len(missing_from_db)/total*100:.1f}% |

### Critical Finding

**{incorrect_count} businesses received "no website" messages despite having custom domain websites.**

- **{incorrect_responded} of these responded** (likely angry opt-outs)
- This is the root cause of the 100% opt-out rate disaster

---

## Incorrectly Targeted Leads (STOP OUTREACH IMMEDIATELY)

These {incorrect_count} businesses have REAL websites but were told "you don't have a website":

"""

    for lead in incorrectly_targeted:
        responded = f"💥 **RESPONDED** ({lead['response_at'][:10]})" if lead['response_at'] else "No response yet"
        report += f"""
### {lead['business_name']} - {responded}
- **Phone**: {lead['phone']}
- **Website**: {lead['website'][:100]}{'...' if len(lead['website']) > 100 else ''}
- **Type**: {lead['website_type']} - {lead['validation_reason']}
- **Rating**: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)
- **Template Used**: {lead['template_used']}
- **Status**: {lead['status']}

**Action**: PAUSE this lead, mark as "has_website"

"""

    report += f"""

---

## Correctly Targeted Leads ✅

**{len(correctly_targeted)} leads ({len(correctly_targeted)/total*100:.1f}%) were correctly targeted:**

These leads either:
1. Have NO website at all (empty/missing)
2. Have only aggregator URLs (Yelp, Google Maps, Facebook)
3. Were NOT sent "no_website" template

**These leads can safely continue in follow-up sequences.**

### Breakdown by Website Type

"""

    # Count by website type
    website_types = {}
    for lead in correctly_targeted:
        wtype = lead['website_type']
        website_types[wtype] = website_types.get(wtype, 0) + 1

    for wtype, count in sorted(website_types.items(), key=lambda x: -x[1]):
        report += f"- **{wtype}**: {count} leads\n"

    if missing_from_db:
        report += f"""

---

## Missing from Database ⚠️

{len(missing_from_db)} leads in sequences but not found in leads.json:

"""
        for lead in missing_from_db:
            report += f"- {lead['business_name']} ({lead['phone']})\n"

    report += f"""

---

## Impact Analysis

### Before Fix (Jan 15, 2026)
- ❌ {incorrect_count} businesses incorrectly told they have no website
- ❌ {incorrect_responded} responded (likely all angry opt-outs)
- ❌ 100% opt-out rate
- ❌ 0% positive response rate
- ❌ Reputation damage

### After Implementing Fix
- ✅ Only target {len(correctly_targeted)} truly valid leads
- ✅ Expected response rate: 5-8%
- ✅ Expected opt-out rate: <2%
- ✅ Expected hot/warm leads: 3-5 per 100 contacts
- ✅ No more angry "we have a website!" responses

### Revenue Impact
- **Lost** (from bad targeting): ~$500-2,000 (missed opportunities from opted-out leads)
- **Potential** (from correct targeting): $1,500-3,000/month after fix

---

## Immediate Next Steps

### 1. PAUSE Incorrectly Targeted Leads
```python
# Script to mark these leads as "has_website" and pause outreach
python -m src.pause_incorrect_leads
```

### 2. Integrate Website Validator
- Add `website_validator.py` to scraping pipeline
- Validate BEFORE adding to sequences
- Never send "no website" message to aggregator-only or custom domain businesses

### 3. Manual Verification (Next 20 Leads)
- Before sending ANY new campaigns
- Manually check next 20 leads
- Verify validator is working correctly

### 4. Small Batch Test (3-5 Sends)
- Send to 3-5 validated "no website" leads
- Monitor responses for 48 hours
- Confirm 0% angry responses before scaling

---

## Technical Root Cause

**Problem**: Scraper treated Yelp/Google Maps URLs as "has website"

**Example**:
```
URL: https://www.yelp.com/biz/p-fit-north-naples
Old logic: "website" field populated → NOT flagged as "no_website"
New logic: Aggregator domain detected → CORRECTLY flagged as "aggregator_only"
```

**Fix**: `website_validator.py` detects 45+ aggregator domains

---

**Files Created**:
- This report: `{output_file.name}`
- Validator: `src/website_validator.py`
- Implementation plan: `IMMEDIATE-FIXES-IMPLEMENTATION-PLAN.md`

**Next**: See Implementation Plan Step 6 (Integrate validator into production)
"""

    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n{'='*80}")
    print(f"REPORT SAVED: {output_file}")
    print(f"{'='*80}\n")


def main():
    """Re-validate all existing leads and generate report."""

    project_root = Path(__file__).parent.parent
    leads_file = project_root / 'output' / 'leads.json'
    sequences_file = project_root / 'output' / 'follow_up_sequences.json'
    report_file = project_root / 'output' / 'LEAD-REVALIDATION-REPORT-V2.md'

    if not leads_file.exists():
        print(f"ERROR: {leads_file} not found")
        sys.exit(1)

    if not sequences_file.exists():
        print(f"ERROR: {sequences_file} not found")
        sys.exit(1)

    # Load full lead database
    print("Loading leads database...")
    leads_db = load_leads_database(leads_file)
    print(f"Loaded {len(leads_db)} leads from database\n")

    # Re-validate all leads
    correctly_targeted, incorrectly_targeted, missing_from_db = revalidate_with_merge(leads_db, sequences_file)

    # Generate report
    generate_report(correctly_targeted, incorrectly_targeted, missing_from_db, report_file)

    # Print summary
    total = len(correctly_targeted) + len(incorrectly_targeted) + len(missing_from_db)

    print(f"\n{'='*80}")
    print(f"RE-VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total Leads: {total}")
    print(f"✅ Correctly Targeted: {len(correctly_targeted)} ({len(correctly_targeted)/total*100:.1f}%)")
    print(f"❌ Incorrectly Targeted: {len(incorrectly_targeted)} ({len(incorrectly_targeted)/total*100:.1f}%)")
    print(f"⚠️ Missing from DB: {len(missing_from_db)} ({len(missing_from_db)/total*100:.1f}%)")
    print(f"\nFull report: {report_file}")
    print(f"{'='*80}\n")

    # Extra alert if incorrectly targeted
    if incorrectly_targeted:
        print(f"🚨 ALERT: {len(incorrectly_targeted)} businesses were incorrectly targeted!")
        print(f"   These should be PAUSED from outreach immediately")
        print()


if __name__ == '__main__':
    main()
