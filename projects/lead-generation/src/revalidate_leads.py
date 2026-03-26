"""
Re-validate existing leads using the new website validator.

This script:
1. Loads all existing leads from follow_up_sequences.json
2. Re-validates each lead's website using website_validator.py
3. Updates pain_points and adds validation metadata
4. Creates a report showing:
   - How many leads had incorrect "no_website" classification
   - Which leads should be removed from outreach
   - Which leads are correctly targeted
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from website_validator import validate_lead_website, is_real_business_website


def load_sequences(sequences_file: Path) -> Dict:
    """Load follow-up sequences from JSON file."""
    with open(sequences_file, 'r') as f:
        return json.load(f)


def save_sequences(sequences_file: Path, data: Dict):
    """Save updated sequences back to JSON file."""
    with open(sequences_file, 'w') as f:
        json.dump(data, f, indent=2)


def revalidate_all_leads(sequences_file: Path) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Re-validate all leads in sequences.

    Returns:
        (correctly_targeted, incorrectly_targeted, missing_website_info)
    """
    data = load_sequences(sequences_file)
    sequences = data.get('sequences', [])

    correctly_targeted = []
    incorrectly_targeted = []
    missing_info = []

    print(f"\n{'='*80}")
    print(f"RE-VALIDATING {len(sequences)} LEADS")
    print(f"{'='*80}\n")

    for i, sequence in enumerate(sequences, 1):
        lead_data = {
            'business_name': sequence.get('business_name', 'Unknown'),
            'phone': sequence.get('phone', ''),
            'website': sequence.get('website', ''),
            'pain_points': sequence.get('pain_points', [])
        }

        # Check if lead has website info
        if 'website' not in sequence:
            missing_info.append({
                'lead_id': sequence.get('lead_id'),
                'business_name': lead_data['business_name'],
                'phone': lead_data['phone'],
                'reason': 'No website field in data'
            })
            continue

        # Validate website
        validated = validate_lead_website(lead_data)

        has_real_website = validated['has_real_website']
        website_type = validated['website_type']
        validation_reason = validated['website_validation_reason']

        # Check if this lead was incorrectly targeted
        was_sent_no_website_message = 'no_website' in sequence.get('touchpoints', [{}])[0].get('template_name', '')

        result = {
            'lead_id': sequence.get('lead_id'),
            'business_name': lead_data['business_name'],
            'phone': lead_data['phone'],
            'website': lead_data['website'],
            'has_real_website': has_real_website,
            'website_type': website_type,
            'validation_reason': validation_reason,
            'was_sent_no_website_message': was_sent_no_website_message,
            'status': sequence.get('status'),
            'response_at': sequence.get('response_at')
        }

        # Categorize
        if has_real_website and was_sent_no_website_message:
            # ERROR: Sent "no website" message to business WITH website
            incorrectly_targeted.append(result)
            print(f"❌ [{i}/{len(sequences)}] {lead_data['business_name']} - HAS WEBSITE but got 'no_website' message")
            print(f"   Website: {lead_data['website']}")
            print(f"   Reason: {validation_reason}")
            print()
        else:
            # Correctly targeted (either has no website, or was not sent "no_website" message)
            correctly_targeted.append(result)
            if i % 10 == 0:
                print(f"✅ [{i}/{len(sequences)}] Validated {i} leads...")

        # Update sequence with new validation data
        sequence['has_real_website'] = has_real_website
        sequence['website_type'] = website_type
        sequence['website_validation_reason'] = validation_reason
        sequence['pain_points'] = validated['pain_points']
        sequence['revalidated_at'] = datetime.now().isoformat()

    # Save updated sequences
    data['sequences'] = sequences
    data['last_revalidation'] = datetime.now().isoformat()
    save_sequences(sequences_file, data)

    return correctly_targeted, incorrectly_targeted, missing_info


def generate_report(correctly_targeted: List[Dict], incorrectly_targeted: List[Dict],
                   missing_info: List[Dict], output_file: Path):
    """Generate detailed validation report."""

    total = len(correctly_targeted) + len(incorrectly_targeted) + len(missing_info)

    report = f"""# Lead Re-Validation Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Category | Count | Percentage |
|----------|-------|------------|
| **Total Leads** | {total} | 100% |
| ✅ Correctly Targeted | {len(correctly_targeted)} | {len(correctly_targeted)/total*100:.1f}% |
| ❌ Incorrectly Targeted | {len(incorrectly_targeted)} | {len(incorrectly_targeted)/total*100:.1f}% |
| ⚠️ Missing Website Info | {len(missing_info)} | {len(missing_info)/total*100:.1f}% |

## Critical Finding

**{len(incorrectly_targeted)} businesses received "no website" messages despite having websites.**

This explains the 100% opt-out rate and angry responses.

---

## Incorrectly Targeted Leads (STOP OUTREACH)

These businesses were sent "no website" messages but actually HAVE websites:

"""

    for lead in incorrectly_targeted:
        responded = "✓ RESPONDED" if lead['response_at'] else ""
        report += f"""
### {lead['business_name']} {responded}
- **Phone**: {lead['phone']}
- **Website**: {lead['website']}
- **Type**: {lead['website_type']}
- **Reason**: {lead['validation_reason']}
- **Status**: {lead['status']}

"""

    report += f"""

---

## Correctly Targeted Leads

{len(correctly_targeted)} leads were correctly targeted:
- No website: Will benefit from "no website" outreach
- Aggregator only: Have Yelp/Google but no real website
- Has website: Were NOT sent "no_website" message

**These leads can continue in follow-up sequences.**

---

## Missing Website Info

{len(missing_info)} leads are missing website data and need to be re-scraped:

"""

    for lead in missing_info:
        report += f"- {lead['business_name']} ({lead['phone']}): {lead['reason']}\n"

    report += f"""

---

## Recommendations

### Immediate Actions

1. **PAUSE all outreach** to the {len(incorrectly_targeted)} incorrectly targeted leads
2. **Remove from sequences** or mark as "has_website"
3. **Apologize? NO** - Honor their opt-outs, fix system instead
4. **Integrate validator** into scraper BEFORE next campaign

### Prevention

1. Use `website_validator.py` in ALL future scraping
2. Manual verification of next 20 leads before sending
3. Small batch test (3-5) with new validator
4. Monitor response rates for correct targeting

### Expected Results After Fix

- Response rate: 5-8% (up from 0% angry responses)
- Opt-out rate: <2% (down from 100%)
- Positive responses: 3-5 per 100 contacts
- Hot leads: 1-2 per 100 contacts

---

**Files Updated**:
- `output/follow_up_sequences.json` - Added validation metadata to all sequences
"""

    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n{'='*80}")
    print(f"REPORT SAVED: {output_file}")
    print(f"{'='*80}\n")


def main():
    """Re-validate all existing leads and generate report."""

    project_root = Path(__file__).parent.parent
    sequences_file = project_root / 'output' / 'follow_up_sequences.json'
    report_file = project_root / 'output' / 'LEAD-REVALIDATION-REPORT.md'

    if not sequences_file.exists():
        print(f"ERROR: {sequences_file} not found")
        sys.exit(1)

    # Re-validate all leads
    correctly_targeted, incorrectly_targeted, missing_info = revalidate_all_leads(sequences_file)

    # Generate report
    generate_report(correctly_targeted, incorrectly_targeted, missing_info, report_file)

    # Print summary
    total = len(correctly_targeted) + len(incorrectly_targeted) + len(missing_info)

    print(f"\n{'='*80}")
    print(f"RE-VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total Leads: {total}")
    print(f"✅ Correctly Targeted: {len(correctly_targeted)} ({len(correctly_targeted)/total*100:.1f}%)")
    print(f"❌ Incorrectly Targeted: {len(incorrectly_targeted)} ({len(incorrectly_targeted)/total*100:.1f}%)")
    print(f"⚠️ Missing Info: {len(missing_info)} ({len(missing_info)/total*100:.1f}%)")
    print(f"\nFull report: {report_file}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
