#!/usr/bin/env python3
"""
Segment Apollo prospect list by industry and identify outreach readiness.
Reads: projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo.csv
Writes: projects/shared/lead-scraper/output/prospect_segments_2026-03-23.json

TEMPLATE ASSIGNMENT LOGIC (maps segment → best cold_outreach.py template):
  HVAC / Air Conditioning  → hvac_missed_call
  Electrical               → electrical_missed_call
  Roofing                  → roofing_missed_call
  Pool (detected in name)  → pool_missed_call
  Plumbing                 → hvac_missed_call  (same emergency-call hook)
  Pest Control             → service_automation  (scheduled, less emergency)
  Landscaping / Lawn       → service_automation
  General contractor       → contractor_missed_call
  Other home services      → contractor_missed_call
  Dental / Medical         → wellness_automation  (appointment-booking hook)
  All others               → discovery_question   (generic discovery first)

B2B / LOW PHONE-DEPENDENCY AUTO-SKIP:
  Segments that are disqualified via lead_router.py are excluded from TOP 20.
  Fire suppression, drone, IT managed services, commercial-only contractors.
"""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import date

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..'))
CSV_PATH = os.path.join(ROOT, 'projects/marceau-solutions/digital/outputs/naples-ai-prospects-apollo.csv')
OUTPUT_PATH = os.path.join(ROOT, 'projects/shared/lead-scraper/output/prospect_segments_2026-03-23.json')

# Already emailed today — exclude from TOP 20
ALREADY_EMAILED = {
    'jamie@antimidators.com',
    'doug@precisehomepros.com',
    'ron@spsnaples.com',
    'irene@platinumproassist.com',
    'mike@kozakair.com',
    'ltancreti@dolphinacnaples.com',
    'hannah@vogelroof.com',
    'jason@smarthomespecialists.com',
}

# Decision-maker title patterns
DECISION_MAKER_PATTERNS = re.compile(
    r'(owner|founder|ceo|president|principal|managing\s+(director|partner|member)|'
    r'chief\s+executive|partner|proprietor)',
    re.IGNORECASE
)

# Target industries (higher priority for TOP 20)
TARGET_INDUSTRIES = {
    'HVAC / Air Conditioning',
    'Plumbing',
    'Electrical',
    'Roofing',
    'Landscaping / Lawn',
    'Pest Control',
    'Dental / Medical / Healthcare',
    'Legal',
    'Property Management / Real Estate',
    'Smart Home / Technology',
}


def classify_prospect(company_name: str, industry: str) -> str:
    """Classify a prospect into a segment based on company name and industry field."""
    cn = company_name.lower()
    ind = industry.lower() if industry else ''

    # HVAC / Air Conditioning — check before broader matches
    if any(kw in cn for kw in ['hvac', 'air conditioning', 'a/c', ' ac ', 'cooling', 'heating',
                                'comfort control', 'comfort air', 'climate']):
        # But exclude if clearly plumbing
        if 'plumb' not in cn:
            return 'HVAC / Air Conditioning'

    # Plumbing
    if 'plumb' in cn:
        return 'Plumbing'

    # Electrical
    if any(kw in cn for kw in ['electric', 'electrical', 'power electric']):
        return 'Electrical'

    # Roofing
    if any(kw in cn for kw in ['roof', 'reroofs', 'reroofing']):
        return 'Roofing'

    # Landscaping / Lawn
    if any(kw in cn for kw in ['landscape', 'landscaping', 'lawn', 'tree', 'garden',
                                'irrigation', 'mowing', 'turf']):
        return 'Landscaping / Lawn'

    # Pest Control
    if any(kw in cn for kw in ['pest', 'exterminator', 'termite', 'bug', 'antimidator']):
        return 'Pest Control'

    # Dental / Medical / Healthcare
    if any(kw in cn for kw in ['dental', 'dentist', 'orthodon', 'implant center']):
        return 'Dental / Medical / Healthcare'
    if ind in ('medical / dental',):
        return 'Dental / Medical / Healthcare'
    if any(kw in cn for kw in ['medical', 'health', 'clinic', 'physician', 'doctor',
                                'chiropractic', 'chiropractor', 'dermatology', 'dermatologist',
                                'surgery', 'surgical', 'ortho', 'therapy', 'therapist',
                                'wellness', 'pediatric', 'urgent care', 'hospital',
                                'pharmacy', 'nursing', 'optometry', 'ophthalmol',
                                'cardio', 'oncology', 'neurology', 'anesthesia',
                                'radiology', 'imaging', 'diagnostic', 'rehab',
                                'physical therapy', 'mental health', 'psychiatric',
                                'counseling', 'hospice', 'home health', 'med spa',
                                'medspa', 'aesthetics', 'cosmetic', 'plastic surg',
                                'botox', 'skin care', 'skincare']):
        return 'Dental / Medical / Healthcare'
    if ind in ('med spa / beauty',):
        return 'Dental / Medical / Healthcare'

    # Legal
    if any(kw in cn for kw in ['law ', 'law,', 'legal', 'attorney', 'lawyer',
                                'law office', 'law firm', 'law group', ' pa',
                                'dupont law', 'lawler']):
        # Careful: "lawler" is a realtor name, check
        if 'lawler' in cn and 'law' not in ind:
            pass  # fall through
        else:
            return 'Legal'

    # Property Management / Real Estate
    if any(kw in cn for kw in ['property management', 'real estate', 'realty', 'realtor',
                                'rental', 'home watch', 'homewatch']):
        return 'Property Management / Real Estate'
    if ind == 'real estate':
        return 'Property Management / Real Estate'

    # Smart Home / Technology
    if any(kw in cn for kw in ['smart home', 'technology', 'tech solutions', 'automation',
                                'security system', 'alarm', 'camera install']):
        return 'Smart Home / Technology'

    # Industry-field fallback for anything not caught by company name
    if ind == 'hvac / home services':
        # Generic home services that didn't match specific keywords
        # Try harder with company name
        if any(kw in cn for kw in ['fire', 'water', 'restoration', 'clean',
                                    'maintenance', 'handyman', 'repair', 'remodel',
                                    'construction', 'build', 'contractor', 'pool',
                                    'painting', 'paint', 'floor', 'cabinet',
                                    'window', 'door', 'glass', 'fence',
                                    'garage', 'gutter', 'insulation', 'solar',
                                    'locksmith', 'moving', 'hauling', 'junk',
                                    'pressure wash', 'seal', 'waterproof',
                                    'trapping', 'wildlife', 'animal',
                                    'furniture', 'hardware', 'supply']):
            return 'Other'
        # Remaining home services — likely HVAC-adjacent or general contractor
        return 'Other'

    if ind == 'restaurants / hospitality':
        return 'Other'

    return 'Other'


def is_decision_maker(title: str) -> bool:
    """Check if title indicates a decision maker."""
    if not title:
        return False
    return bool(DECISION_MAKER_PATTERNS.search(title))


# B2B / low phone-dependency signals — these prospects are excluded from TOP 20
# because the AI missed-call offer has no hook for them.
# Sync with execution/lead_router.py CONTEXTUAL_B2B_SIGNALS
B2B_SKIP_KEYWORDS = [
    "fire stop", "fireproofers", "fire suppression", "fire protection",
    "drone", "aerial", "uav",
    "all in one technology", "all-in-one technology",
    "knauf-koenig", "kkgbuild",
    "imperial homes",
    "managed service", "it managed", "it services", "network solutions",
    "technology solutions", "cybersecurity",
    "wholesale", "distributor", "distribution",
    "recruiting", "staffing", "green hunters",
]


def is_b2b_skip(company_name: str) -> bool:
    """Return True if this company should be skipped (B2B / low phone-dependency)."""
    cn = company_name.lower()
    return any(kw in cn for kw in B2B_SKIP_KEYWORDS)


def get_recommended_template(segment: str, company_name: str) -> str:
    """
    Return the best cold_outreach.py template key for this segment.

    Priority: company-name-specific signals override segment-level assignment.
    These templates map directly to the AI missed-call offer.
    """
    cn = (company_name or "").lower()

    # Company-name-specific overrides (most specific, highest confidence)
    if any(kw in cn for kw in ["hvac", "air conditioning", "cooling", "heating", "comfort control", "climate"]):
        return "hvac_missed_call"
    if any(kw in cn for kw in ["pool", "spa service"]):
        return "pool_missed_call"
    if any(kw in cn for kw in ["electric", "electrical"]):
        return "electrical_missed_call"
    if any(kw in cn for kw in ["roof", "reroof"]):
        return "roofing_missed_call"
    if any(kw in cn for kw in ["plumb", "drain", "sewer"]):
        return "hvac_missed_call"  # same emergency-call hook applies
    if any(kw in cn for kw in ["repair", "handyman", "paint", "cleaning", "maid",
                                "lawn", "landscape", "irrigation", "moving", "movers"]):
        return "contractor_missed_call"

    # Segment-level fallback
    segment_template_map = {
        "HVAC / Air Conditioning": "hvac_missed_call",
        "Plumbing": "hvac_missed_call",
        "Electrical": "electrical_missed_call",
        "Roofing": "roofing_missed_call",
        "Landscaping / Lawn": "service_automation",
        "Pest Control": "service_automation",
        "Dental / Medical / Healthcare": "wellness_automation",
        "Legal": "discovery_question",
        "Property Management / Real Estate": "discovery_question",
        "Smart Home / Technology": "discovery_question",
        "Other": "contractor_missed_call",
    }
    return segment_template_map.get(segment, "discovery_question")


def main():
    # Load CSV
    prospects = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prospects.append(row)

    print(f"Loaded {len(prospects)} prospects from CSV\n")

    # Segment
    segments = defaultdict(lambda: {
        'total': 0,
        'with_email': 0,
        'without_email': 0,
        'with_phone': 0,
        'prospects': []
    })

    for p in prospects:
        segment = classify_prospect(p.get('company_name', ''), p.get('industry', ''))
        seg = segments[segment]
        seg['total'] += 1

        has_email = bool(p.get('email', '').strip())
        has_phone = bool(p.get('phone', '').strip())

        if has_email:
            seg['with_email'] += 1
        else:
            seg['without_email'] += 1
        if has_phone:
            seg['with_phone'] += 1

        seg['prospects'].append({
            'company_name': p.get('company_name', ''),
            'contact_name': p.get('contact_name', ''),
            'first_name': p.get('first_name', ''),
            'last_name': p.get('last_name', ''),
            'title': p.get('title', ''),
            'email': p.get('email', ''),
            'phone': p.get('phone', ''),
            'industry': p.get('industry', ''),
            'website': p.get('website', ''),
            'linkedin_url': p.get('linkedin_url', ''),
            'employee_count': p.get('employee_count', ''),
            'segment': segment,
        })

    # Summary
    total_prospects = sum(s['total'] for s in segments.values())
    total_with_email = sum(s['with_email'] for s in segments.values())
    total_without_email = sum(s['without_email'] for s in segments.values())
    total_with_phone = sum(s['with_phone'] for s in segments.values())

    summary = {
        'total_prospects': total_prospects,
        'total_with_email': total_with_email,
        'total_without_email': total_without_email,
        'total_with_phone': total_with_phone,
        'ready_for_outreach': total_with_email,
    }

    # Print table
    print(f"{'Segment':<40} {'Total':>6} {'Email':>6} {'No Email':>9} {'Phone':>6}")
    print('-' * 70)

    # Sort segments: target industries first, then Other
    segment_order = [
        'HVAC / Air Conditioning',
        'Plumbing',
        'Electrical',
        'Roofing',
        'Landscaping / Lawn',
        'Pest Control',
        'Dental / Medical / Healthcare',
        'Legal',
        'Property Management / Real Estate',
        'Smart Home / Technology',
        'Other',
    ]

    for seg_name in segment_order:
        if seg_name in segments:
            s = segments[seg_name]
            print(f"{seg_name:<40} {s['total']:>6} {s['with_email']:>6} {s['without_email']:>9} {s['with_phone']:>6}")

    # Any segments not in our predefined list
    for seg_name in sorted(segments.keys()):
        if seg_name not in segment_order:
            s = segments[seg_name]
            print(f"{seg_name:<40} {s['total']:>6} {s['with_email']:>6} {s['without_email']:>9} {s['with_phone']:>6}")

    print('-' * 70)
    print(f"{'TOTAL':<40} {total_prospects:>6} {total_with_email:>6} {total_without_email:>9} {total_with_phone:>6}")
    print()
    print(f"Ready for cold email outreach: {total_with_email}")
    print(f"Need enrichment (no email):    {total_without_email}")

    # TOP 20 candidates
    print("\n" + "=" * 70)
    print("TOP 20 NEXT-BATCH CANDIDATES")
    print("(Have email, decision makers, target industries, not already emailed,")
    print(" NOT B2B / low phone-dependency)")
    print("=" * 70)

    # Track B2B skips for transparency
    b2b_skipped = []

    candidates = []
    for seg_name in segment_order:
        if seg_name == 'Other':
            continue
        if seg_name not in segments:
            continue
        for p in segments[seg_name]['prospects']:
            email = p.get('email', '').strip()
            if not email:
                continue
            if email.lower() in ALREADY_EMAILED:
                continue
            if not is_decision_maker(p.get('title', '')):
                continue
            # NEW: Skip B2B / low phone-dependency businesses
            if is_b2b_skip(p.get('company_name', '')):
                b2b_skipped.append(p.get('company_name', ''))
                continue
            # Add recommended template
            p['recommended_template'] = get_recommended_template(
                seg_name, p.get('company_name', '')
            )
            candidates.append(p)

    # Sort by segment priority (earlier in segment_order = higher priority)
    seg_priority = {name: i for i, name in enumerate(segment_order)}
    candidates.sort(key=lambda x: seg_priority.get(x['segment'], 99))

    top20 = candidates[:20]

    print(f"\n{'#':<3} {'Company':<32} {'Contact':<13} {'Email':<32} {'Template':<28} {'Segment'}")
    print('-' * 160)
    for i, c in enumerate(top20, 1):
        print(f"{i:<3} {c['company_name'][:31]:<32} {c['contact_name'][:12]:<13} "
              f"{c['email'][:31]:<32} {c.get('recommended_template','')[:27]:<28} {c['segment']}")

    print(f"\nTotal candidates found (before cap): {len(candidates)}")
    if b2b_skipped:
        print(f"\nAUTO-SKIPPED (B2B / low phone-dependency): {len(b2b_skipped)}")
        for name in b2b_skipped:
            print(f"  - {name}")

    # Build output JSON
    output = {
        'generated': str(date.today()),
        'segments': {name: segments[name] for name in segment_order if name in segments},
        'summary': summary,
        'top_20_next_batch': top20,
        'already_emailed_today': sorted(ALREADY_EMAILED),
        'b2b_skipped': b2b_skipped,
        'validation_notes': {
            'b2b_filter': 'Companies matching B2B_SKIP_KEYWORDS are excluded from TOP 20 — they lack phone-dependency for the AI missed-call offer.',
            'template_selection': 'Each candidate has a recommended_template field — use these in cold_outreach.py for industry-specific hooks.',
            'offer_fit': 'Best fits: HVAC, Electrical, Roofing, Pool — emergency/scheduling calls. Worst fits: IT, fire suppression, drones, large GCs.',
        }
    }

    # Write JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nJSON saved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
