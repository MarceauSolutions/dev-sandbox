#!/usr/bin/env python3
"""
Lead Qualification Script for Square Foot Shipping

Scores leads based on fit criteria:
- Estimated shipping volume (30% weight)
- Business type fit (30% weight)
- Contact information quality (20% weight)
- Location (US-based = 20% weight)

Outputs scored and categorized leads (HOT/WARM/COLD)

Example usage:
    python qualify_leads.py --input scraped-leads.json --output qualified-leads.json
    python qualify_leads.py --show-hot
    python qualify_leads.py --min-score 7
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any


class LeadQualifier:
    """Scores and qualifies leads based on business fit criteria"""

    # Scoring weights
    WEIGHT_VOLUME = 0.30
    WEIGHT_TYPE = 0.30
    WEIGHT_CONTACT = 0.20
    WEIGHT_LOCATION = 0.20

    # Score thresholds
    HOT_THRESHOLD = 8.0
    WARM_THRESHOLD = 5.0

    def __init__(self):
        self.stats = {
            'total': 0,
            'hot': 0,
            'warm': 0,
            'cold': 0
        }

    def score_volume(self, lead: Dict[str, Any]) -> float:
        """
        Score based on estimated shipping volume

        Scoring logic:
        - 100-1000/month = 10 pts
        - 50-100/month = 7 pts
        - 10-50/month = 5 pts
        - <10/month = 3 pts
        - Unknown = 5 pts (neutral)
        """
        volume = lead.get('estimated_volume_monthly', 0)

        # Handle string values (e.g., "100-1000")
        if isinstance(volume, str):
            volume = self._parse_volume_range(volume)

        if volume >= 100:
            return 10.0
        elif volume >= 50:
            return 7.0
        elif volume >= 10:
            return 5.0
        elif volume > 0:
            return 3.0
        else:
            # Unknown volume - neutral score
            return 5.0

    def score_business_type(self, lead: Dict[str, Any]) -> float:
        """
        Score based on business type fit

        Scoring logic:
        - E-commerce/Physical goods = 10 pts
        - Manufacturing/Distribution = 10 pts
        - Retail with online presence = 8 pts
        - B2B services with shipping = 7 pts
        - Digital/Software = 3 pts
        - Unknown = 5 pts (neutral)
        """
        business_type = lead.get('business_type', '').lower()
        industry = lead.get('industry', '').lower()
        description = lead.get('description', '').lower()

        # Combine all text fields for better matching
        combined = f"{business_type} {industry} {description}"

        # High-fit indicators
        high_fit_keywords = [
            'ecommerce', 'e-commerce', 'physical goods', 'manufacturing',
            'distribution', 'wholesale', 'warehouse', 'fulfillment',
            'product', 'inventory', 'shipment', 'freight'
        ]

        # Medium-fit indicators
        medium_fit_keywords = [
            'retail', 'store', 'marketplace', 'b2b', 'supplies',
            'equipment', 'materials', 'goods'
        ]

        # Low-fit indicators
        low_fit_keywords = [
            'software', 'digital', 'saas', 'consulting', 'marketing',
            'agency', 'virtual', 'online service'
        ]

        if any(keyword in combined for keyword in high_fit_keywords):
            return 10.0
        elif any(keyword in combined for keyword in medium_fit_keywords):
            return 7.5
        elif any(keyword in combined for keyword in low_fit_keywords):
            return 3.0
        else:
            return 5.0

    def score_contact_quality(self, lead: Dict[str, Any]) -> float:
        """
        Score based on contact information completeness

        Scoring logic:
        - Email + Phone + Name = 10 pts
        - Email + Phone = 9 pts
        - Email + Name = 7 pts
        - Email only = 5 pts
        - Phone only = 3 pts
        - No contact = 0 pts
        """
        score = 0.0

        has_email = bool(lead.get('email'))
        has_phone = bool(lead.get('phone'))
        has_name = bool(lead.get('contact_name') or lead.get('owner_name'))

        if has_email and has_phone and has_name:
            score = 10.0
        elif has_email and has_phone:
            score = 9.0
        elif has_email and has_name:
            score = 7.0
        elif has_email:
            score = 5.0
        elif has_phone:
            score = 3.0

        # Bonus for verified/valid looking email
        email = lead.get('email', '')
        if email and '@' in email and '.' in email:
            score = min(10.0, score + 0.5)

        return score

    def score_location(self, lead: Dict[str, Any]) -> float:
        """
        Score based on location (US-based preference)

        Scoring logic:
        - US-based = 10 pts
        - Canada/Mexico = 7 pts
        - International = 5 pts
        - Unknown = 5 pts (neutral)
        """
        country = lead.get('country', '').upper()
        state = lead.get('state', '').upper()
        address = lead.get('address', '').lower()

        # Check for US indicators
        us_indicators = ['US', 'USA', 'UNITED STATES', 'U.S.']
        if country in us_indicators or state or any(ind.lower() in address for ind in us_indicators):
            return 10.0

        # Check for North America
        na_indicators = ['CA', 'CANADA', 'MX', 'MEXICO']
        if country in na_indicators or any(ind.lower() in address for ind in na_indicators):
            return 7.0

        # International or unknown
        if country and country not in us_indicators:
            return 5.0

        return 5.0  # Unknown location

    def score_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall lead score (0-10) based on weighted criteria

        Returns enriched lead dict with:
        - score: Overall score (0-10)
        - category: HOT/WARM/COLD
        - score_breakdown: Individual component scores
        """
        # Calculate component scores
        volume_score = self.score_volume(lead)
        type_score = self.score_business_type(lead)
        contact_score = self.score_contact_quality(lead)
        location_score = self.score_location(lead)

        # Calculate weighted total
        total_score = (
            volume_score * self.WEIGHT_VOLUME +
            type_score * self.WEIGHT_TYPE +
            contact_score * self.WEIGHT_CONTACT +
            location_score * self.WEIGHT_LOCATION
        )

        # Categorize lead
        if total_score >= self.HOT_THRESHOLD:
            category = "HOT"
            self.stats['hot'] += 1
        elif total_score >= self.WARM_THRESHOLD:
            category = "WARM"
            self.stats['warm'] += 1
        else:
            category = "COLD"
            self.stats['cold'] += 1

        self.stats['total'] += 1

        # Enrich lead with scoring data
        scored_lead = lead.copy()
        scored_lead['score'] = round(total_score, 2)
        scored_lead['category'] = category
        scored_lead['score_breakdown'] = {
            'volume': round(volume_score, 2),
            'business_type': round(type_score, 2),
            'contact_quality': round(contact_score, 2),
            'location': round(location_score, 2)
        }

        return scored_lead

    def qualify_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and sort all leads"""
        scored_leads = [self.score_lead(lead) for lead in leads]

        # Sort by score descending (highest first)
        scored_leads.sort(key=lambda x: x['score'], reverse=True)

        return scored_leads

    def _parse_volume_range(self, volume_str: str) -> int:
        """Parse volume range string like '100-1000' to midpoint"""
        try:
            if '-' in volume_str:
                parts = volume_str.split('-')
                low = int(parts[0].strip())
                high = int(parts[1].strip())
                return (low + high) // 2
            else:
                return int(volume_str)
        except (ValueError, IndexError):
            return 0

    def print_stats(self):
        """Print qualification statistics"""
        print("\n" + "="*60)
        print("LEAD QUALIFICATION SUMMARY")
        print("="*60)
        print(f"Total Leads Scored: {self.stats['total']}")
        print(f"  HOT  (8-10): {self.stats['hot']} ({self._percent(self.stats['hot'])}%)")
        print(f"  WARM (5-7):  {self.stats['warm']} ({self._percent(self.stats['warm'])}%)")
        print(f"  COLD (1-4):  {self.stats['cold']} ({self._percent(self.stats['cold'])}%)")
        print("="*60 + "\n")

    def _percent(self, count: int) -> str:
        """Calculate percentage of total"""
        if self.stats['total'] == 0:
            return "0"
        return f"{(count / self.stats['total'] * 100):.1f}"


def load_leads(input_file: Path) -> List[Dict[str, Any]]:
    """Load leads from JSON file"""
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            leads = data
        elif isinstance(data, dict) and 'leads' in data:
            leads = data['leads']
        else:
            leads = [data]

        print(f"Loaded {len(leads)} leads from {input_file}")
        return leads

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {input_file}: {e}")
        sys.exit(1)


def save_leads(leads: List[Dict[str, Any]], output_file: Path):
    """Save qualified leads to JSON file"""
    output_data = {
        'qualified_leads': leads,
        'total_count': len(leads),
        'hot_count': sum(1 for lead in leads if lead['category'] == 'HOT'),
        'warm_count': sum(1 for lead in leads if lead['category'] == 'WARM'),
        'cold_count': sum(1 for lead in leads if lead['category'] == 'COLD')
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved {len(leads)} qualified leads to {output_file}")


def display_leads(leads: List[Dict[str, Any]], category: str = None, min_score: float = None):
    """Display leads in formatted table"""

    # Filter leads
    filtered = leads
    if category:
        filtered = [lead for lead in filtered if lead['category'] == category.upper()]
    if min_score is not None:
        filtered = [lead for lead in filtered if lead['score'] >= min_score]

    if not filtered:
        print(f"No leads found matching criteria (category={category}, min_score={min_score})")
        return

    print(f"\n{'='*100}")
    print(f"QUALIFIED LEADS ({len(filtered)} shown)")
    print(f"{'='*100}")
    print(f"{'Category':<10} {'Score':<8} {'Business Name':<30} {'Contact':<30}")
    print(f"{'-'*100}")

    for lead in filtered:
        business_name = lead.get('business_name', lead.get('name', 'Unknown'))[:28]
        contact = lead.get('email', lead.get('phone', 'No contact'))[:28]

        print(f"{lead['category']:<10} {lead['score']:<8.2f} {business_name:<30} {contact:<30}")

    print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Qualify and score leads for Square Foot Shipping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score leads and save output
  python qualify_leads.py --input scraped-leads.json --output qualified-leads.json

  # Show only HOT leads
  python qualify_leads.py --input scraped-leads.json --show-hot

  # Show leads with score >= 7
  python qualify_leads.py --input scraped-leads.json --min-score 7

  # Show WARM leads only
  python qualify_leads.py --input scraped-leads.json --category WARM
        """
    )

    parser.add_argument(
        '--input',
        type=Path,
        default=Path('scraped-leads.json'),
        help='Input JSON file with scraped leads (default: scraped-leads.json)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        help='Output JSON file for qualified leads (default: qualified-leads.json)'
    )

    parser.add_argument(
        '--show-hot',
        action='store_true',
        help='Display only HOT leads (score 8-10)'
    )

    parser.add_argument(
        '--show-warm',
        action='store_true',
        help='Display only WARM leads (score 5-7)'
    )

    parser.add_argument(
        '--show-cold',
        action='store_true',
        help='Display only COLD leads (score 1-4)'
    )

    parser.add_argument(
        '--category',
        choices=['HOT', 'WARM', 'COLD'],
        help='Filter by category'
    )

    parser.add_argument(
        '--min-score',
        type=float,
        help='Show only leads with score >= threshold'
    )

    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Display all scored leads'
    )

    args = parser.parse_args()

    # Load leads
    leads = load_leads(args.input)

    if not leads:
        print("No leads to qualify")
        return

    # Qualify leads
    qualifier = LeadQualifier()
    qualified_leads = qualifier.qualify_leads(leads)

    # Print stats
    qualifier.print_stats()

    # Save output if specified
    if args.output:
        save_leads(qualified_leads, args.output)
    elif not any([args.show_hot, args.show_warm, args.show_cold, args.show_all, args.category, args.min_score]):
        # Default output file if no display options specified
        default_output = Path('qualified-leads.json')
        save_leads(qualified_leads, default_output)

    # Display leads based on flags
    if args.show_hot:
        display_leads(qualified_leads, category='HOT')
    elif args.show_warm:
        display_leads(qualified_leads, category='WARM')
    elif args.show_cold:
        display_leads(qualified_leads, category='COLD')
    elif args.category:
        display_leads(qualified_leads, category=args.category)
    elif args.min_score is not None:
        display_leads(qualified_leads, min_score=args.min_score)
    elif args.show_all:
        display_leads(qualified_leads)


if __name__ == '__main__':
    main()
