#!/usr/bin/env python3
"""
Export master_sendable JSON → Apollo-ready CSV.

Filters:
  - Must have first_name (required for {{first_name}} subject lines)
  - Must have email
  - Deduplicates by email

Usage:
    python -m projects.shared.lead-scraper.src.export_apollo_csv
    python -m projects.shared.lead-scraper.src.export_apollo_csv --input path/to/master.json
    python -m projects.shared.lead-scraper.src.export_apollo_csv --segment HVAC
"""

import json
import csv
import argparse
from datetime import date
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / 'output'
FIELDS = ['first_name', 'last_name', 'email', 'title', 'company_name',
          'website', 'phone', 'city', 'state', 'linkedin_url']


def export(input_path: str = None, segment_filter: str = None):
    if not input_path:
        # Default to latest master_sendable
        candidates = sorted(OUTPUT_DIR.glob('master_sendable_*.json'), reverse=True)
        if not candidates:
            print("No master_sendable file found in output/")
            return
        input_path = candidates[0]

    with open(input_path) as f:
        data = json.load(f)

    all_contacts = []
    for seg, items in data.get('by_segment', {}).items():
        for p in items:
            p['segment'] = seg
            all_contacts.append(p)

    total_raw = len(all_contacts)

    # Filter: must have email
    all_contacts = [p for p in all_contacts if p.get('email', '').strip()]

    # Filter: must have first_name
    no_first_name = [p for p in all_contacts if not p.get('first_name', '').strip()]
    all_contacts = [p for p in all_contacts if p.get('first_name', '').strip()]

    # Optional segment filter
    if segment_filter:
        all_contacts = [p for p in all_contacts
                        if segment_filter.lower() in p.get('segment', '').lower()]

    # Deduplicate by email
    seen = set()
    unique = []
    for p in all_contacts:
        e = p['email'].lower().strip()
        if e not in seen:
            seen.add(e)
            unique.append(p)

    # Write CSV
    suffix = f"_{segment_filter.lower().replace(' ', '_')}" if segment_filter else ''
    out_path = OUTPUT_DIR / f"apollo_import_{date.today()}{suffix}.csv"

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader()
        for c in unique:
            w.writerow({
                'first_name': c.get('first_name', ''),
                'last_name':  c.get('last_name', ''),
                'email':      c.get('email', ''),
                'title':      c.get('title', ''),
                'company_name': c.get('company_name', ''),
                'website':    c.get('website', ''),
                'phone':      c.get('phone', ''),
                'city':       c.get('city', 'Naples'),
                'state':      c.get('state', 'FL'),
                'linkedin_url': c.get('linkedin_url', ''),
            })

    print(f"Input:            {Path(input_path).name}")
    print(f"Raw contacts:     {total_raw}")
    print(f"Missing email:    {total_raw - (len(all_contacts) + len(no_first_name))}")
    print(f"Missing first_name (excluded): {len(no_first_name)}")
    if no_first_name:
        for p in no_first_name:
            print(f"  - {p.get('company_name', '?')} ({p.get('email', '?')})")
    print(f"Exported:         {len(unique)}")
    print(f"Output:           {out_path}")
    return out_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='Path to master_sendable JSON')
    parser.add_argument('--segment', help='Filter to specific segment (e.g. HVAC)')
    args = parser.parse_args()
    export(args.input, args.segment)
