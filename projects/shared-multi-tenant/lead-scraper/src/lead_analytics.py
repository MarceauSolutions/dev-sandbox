"""
Lead Attribution Analytics and Reporting

Comprehensive analytics on lead sources, conversion rates, multi-touch
attribution, and gap detection across all channels.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.lead_intake import LeadIntakeSystem


class LeadAnalytics:
    """Lead attribution analytics and reporting system"""

    def __init__(self):
        """Initialize analytics system"""
        self.lead_system = LeadIntakeSystem()

    def _calculate_time_to_conversion(self, lead: Dict) -> Optional[float]:
        """Calculate time from first touch to conversion

        Args:
            lead: Lead dict

        Returns:
            Days to conversion, or None if not converted
        """
        if lead.get('status') not in ['converted', 'won']:
            return None

        first_touch = datetime.fromisoformat(lead['timestamp'])
        last_touch = datetime.fromisoformat(lead['last_contact'])

        delta = last_touch - first_touch
        return round(delta.total_seconds() / 86400, 1)  # Convert to days

    def get_source_performance(self) -> Dict:
        """Get performance metrics by source channel

        Returns:
            Dict with metrics per source
        """
        leads = self.lead_system.leads
        by_source = defaultdict(lambda: {
            'total': 0,
            'qualified': 0,
            'converted': 0,
            'won': 0,
            'lost': 0,
            'time_to_conversion': []
        })

        for lead in leads:
            source = lead.get('source_channel', 'unknown')
            status = lead.get('status', 'new')

            by_source[source]['total'] += 1

            if status == 'qualified':
                by_source[source]['qualified'] += 1
            elif status in ['converted', 'won']:
                by_source[source]['converted'] += 1
                if status == 'won':
                    by_source[source]['won'] += 1

                # Track time to conversion
                time_to_conv = self._calculate_time_to_conversion(lead)
                if time_to_conv is not None:
                    by_source[source]['time_to_conversion'].append(time_to_conv)

            elif status == 'lost':
                by_source[source]['lost'] += 1

        # Calculate percentages and averages
        report = {}
        for source, data in by_source.items():
            total = data['total']
            if total > 0:
                report[source] = {
                    'total_leads': total,
                    'qualified_count': data['qualified'],
                    'qualified_pct': round(data['qualified'] / total * 100, 1),
                    'converted_count': data['converted'],
                    'converted_pct': round(data['converted'] / total * 100, 1),
                    'won_count': data['won'],
                    'lost_count': data['lost'],
                    'avg_time_to_conversion': round(
                        sum(data['time_to_conversion']) / len(data['time_to_conversion']), 1
                    ) if data['time_to_conversion'] else None
                }

        return report

    def get_business_comparison(self) -> Dict:
        """Compare lead quality across businesses

        Returns:
            Dict with metrics per business
        """
        leads = self.lead_system.leads
        by_business = defaultdict(lambda: {
            'total': 0,
            'qualified': 0,
            'converted': 0,
            'won': 0
        })

        for lead in leads:
            business = lead.get('business_id', 'unknown')
            status = lead.get('status', 'new')

            by_business[business]['total'] += 1

            if status == 'qualified':
                by_business[business]['qualified'] += 1
            elif status in ['converted', 'won']:
                by_business[business]['converted'] += 1
                if status == 'won':
                    by_business[business]['won'] += 1

        # Calculate percentages
        report = {}
        for business, data in by_business.items():
            total = data['total']
            if total > 0:
                report[business] = {
                    'total_leads': total,
                    'qualified_count': data['qualified'],
                    'qualified_pct': round(data['qualified'] / total * 100, 1),
                    'converted_count': data['converted'],
                    'converted_pct': round(data['converted'] / total * 100, 1),
                    'won_count': data['won']
                }

        return report

    def get_lost_leads(self, days_inactive: int = 14) -> List[Dict]:
        """Detect leads that went cold (no activity in N days)

        Args:
            days_inactive: Number of days of inactivity to consider cold

        Returns:
            List of cold lead dicts
        """
        cutoff_date = datetime.now() - timedelta(days=days_inactive)
        cold_leads = []

        for lead in self.lead_system.leads:
            # Skip already lost/won leads
            if lead.get('status') in ['lost', 'won']:
                continue

            last_contact = datetime.fromisoformat(lead['last_contact'])

            if last_contact < cutoff_date:
                cold_leads.append({
                    'lead_id': lead['lead_id'],
                    'business_id': lead.get('business_id'),
                    'contact_info': lead.get('contact_info'),
                    'source_channel': lead.get('source_channel'),
                    'status': lead.get('status'),
                    'last_contact': lead['last_contact'],
                    'days_inactive': (datetime.now() - last_contact).days
                })

        return cold_leads

    def get_multi_touch_attribution(self) -> Dict:
        """Analyze multi-touch attribution (leads with multiple touchpoints)

        Returns:
            Dict with multi-touch stats
        """
        leads = self.lead_system.leads

        total_multi_touch = 0
        touchpoint_counts = defaultdict(int)
        source_combinations = defaultdict(int)

        for lead in leads:
            touchpoints = lead.get('touchpoint_history', [])
            num_touchpoints = len(touchpoints)

            if num_touchpoints > 1:
                total_multi_touch += 1
                touchpoint_counts[num_touchpoints] += 1

                # Track source combinations
                sources = [tp.get('source_channel') for tp in touchpoints]
                source_combo = ' → '.join(sources)
                source_combinations[source_combo] += 1

        avg_touchpoints = 0
        if len(leads) > 0:
            total_touchpoints = sum(len(l.get('touchpoint_history', [])) for l in leads)
            avg_touchpoints = round(total_touchpoints / len(leads), 1)

        return {
            'total_leads': len(leads),
            'multi_touch_leads': total_multi_touch,
            'multi_touch_pct': round(total_multi_touch / len(leads) * 100, 1) if leads else 0,
            'avg_touchpoints_per_lead': avg_touchpoints,
            'touchpoint_distribution': dict(touchpoint_counts),
            'common_journeys': dict(sorted(
                source_combinations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])  # Top 10 journeys
        }

    def get_funnel_visualization(self) -> Dict:
        """Get conversion funnel data

        Returns:
            Dict with funnel stages
        """
        leads = self.lead_system.leads

        # Count by status
        funnel = {
            'new': 0,
            'contacted': 0,
            'qualified': 0,
            'converted': 0,
            'won': 0,
            'lost': 0
        }

        for lead in leads:
            status = lead.get('status', 'new')
            funnel[status] = funnel.get(status, 0) + 1

        total = len(leads)

        # Calculate conversion rates between stages
        conversion_rates = {}
        if total > 0:
            conversion_rates['new_to_contacted'] = round(
                (funnel['contacted'] + funnel['qualified'] + funnel['converted'] + funnel['won']) / total * 100, 1
            )
            if funnel['contacted'] > 0:
                conversion_rates['contacted_to_qualified'] = round(
                    (funnel['qualified'] + funnel['converted'] + funnel['won']) / funnel['contacted'] * 100, 1
                )
            if funnel['qualified'] > 0:
                conversion_rates['qualified_to_converted'] = round(
                    (funnel['converted'] + funnel['won']) / funnel['qualified'] * 100, 1
                )
            if funnel['converted'] > 0:
                conversion_rates['converted_to_won'] = round(
                    funnel['won'] / funnel['converted'] * 100, 1
                )

        return {
            'total_leads': total,
            'funnel': funnel,
            'conversion_rates': conversion_rates
        }

    def identify_gaps(self) -> List[Dict]:
        """Identify potential gaps in lead management

        Returns:
            List of gap/warning dicts
        """
        gaps = []
        leads = self.lead_system.leads

        # Gap 1: Hot leads not synced to CRM
        hot_unsynced = [
            l for l in leads
            if l.get('priority') in ['critical', 'high']
            and l.get('status') in ['qualified', 'converted']
            and not l.get('crm_synced')
        ]

        if hot_unsynced:
            gaps.append({
                'type': 'hot_leads_not_in_crm',
                'severity': 'critical',
                'count': len(hot_unsynced),
                'message': f"{len(hot_unsynced)} hot leads not synced to CRM",
                'lead_ids': [l['lead_id'] for l in hot_unsynced]
            })

        # Gap 2: Voice AI calls with no follow-up
        voice_no_followup = [
            l for l in leads
            if l.get('source_channel') == 'voice_ai_call'
            and l.get('status') in ['contacted', 'qualified']
            and len(l.get('touchpoint_history', [])) == 1  # No follow-up
            and (datetime.now() - datetime.fromisoformat(l['last_contact'])).days > 2
        ]

        if voice_no_followup:
            gaps.append({
                'type': 'voice_ai_no_followup',
                'severity': 'high',
                'count': len(voice_no_followup),
                'message': f"{len(voice_no_followup)} voice AI calls with no follow-up action",
                'lead_ids': [l['lead_id'] for l in voice_no_followup]
            })

        # Gap 3: Form submissions not contacted within 24h
        form_not_contacted = [
            l for l in leads
            if l.get('source_channel') == 'form_submission'
            and l.get('status') == 'new'
            and (datetime.now() - datetime.fromisoformat(l['timestamp'])).total_seconds() > 86400
        ]

        if form_not_contacted:
            gaps.append({
                'type': 'form_submission_no_contact',
                'severity': 'high',
                'count': len(form_not_contacted),
                'message': f"{len(form_not_contacted)} form submissions not contacted within 24 hours",
                'lead_ids': [l['lead_id'] for l in form_not_contacted]
            })

        return gaps

    def generate_full_report(self) -> Dict:
        """Generate comprehensive analytics report

        Returns:
            Full report dict with all metrics
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'source_performance': self.get_source_performance(),
            'business_comparison': self.get_business_comparison(),
            'multi_touch_attribution': self.get_multi_touch_attribution(),
            'funnel': self.get_funnel_visualization(),
            'lost_leads': len(self.get_lost_leads()),
            'gaps': self.identify_gaps()
        }


def main():
    """CLI for lead analytics"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.lead_analytics <command>")
        print("\nCommands:")
        print("  report                  - Full analytics report")
        print("  sources                 - Source performance comparison")
        print("  funnel                  - Conversion funnel visualization")
        print("  gaps                    - Identify gaps in lead management")
        print("  lost                    - Show cold leads (inactive 14+ days)")
        sys.exit(1)

    command = sys.argv[1]
    analytics = LeadAnalytics()

    if command == 'report':
        report = analytics.generate_full_report()

        print("\n=== LEAD ATTRIBUTION ANALYTICS REPORT ===\n")
        print(f"Generated: {report['generated_at']}")

        # Source performance
        print("\n--- SOURCE PERFORMANCE ---")
        for source, metrics in report['source_performance'].items():
            print(f"\n{source.upper()}:")
            print(f"  Total Leads: {metrics['total_leads']}")
            print(f"  Qualified: {metrics['qualified_count']} ({metrics['qualified_pct']}%)")
            print(f"  Converted: {metrics['converted_count']} ({metrics['converted_pct']}%)")
            if metrics['avg_time_to_conversion']:
                print(f"  Avg Time to Conversion: {metrics['avg_time_to_conversion']} days")

        # Business comparison
        print("\n--- BUSINESS COMPARISON ---")
        for business, metrics in report['business_comparison'].items():
            print(f"\n{business}:")
            print(f"  Total: {metrics['total_leads']}")
            print(f"  Qualified: {metrics['qualified_pct']}%")
            print(f"  Converted: {metrics['converted_pct']}%")

        # Gaps
        print("\n--- GAPS & WARNINGS ---")
        if report['gaps']:
            for gap in report['gaps']:
                severity_icon = "🔴" if gap['severity'] == 'critical' else "🟡"
                print(f"{severity_icon} {gap['message']}")
        else:
            print("✅ No gaps detected")

    elif command == 'sources':
        perf = analytics.get_source_performance()

        print("\n=== SOURCE PERFORMANCE COMPARISON ===\n")

        # Sort by conversion rate
        sorted_sources = sorted(
            perf.items(),
            key=lambda x: x[1]['converted_pct'],
            reverse=True
        )

        for source, metrics in sorted_sources:
            print(f"{source}:")
            print(f"  {metrics['total_leads']} leads → {metrics['qualified_pct']}% qualified → {metrics['converted_pct']}% converted")
            if metrics['avg_time_to_conversion']:
                print(f"  Avg conversion time: {metrics['avg_time_to_conversion']} days")
            print()

    elif command == 'funnel':
        funnel = analytics.get_funnel_visualization()

        print("\n=== CONVERSION FUNNEL ===\n")
        print(f"Total Leads: {funnel['total_leads']}")
        print("\nFunnel Stages:")
        for stage, count in funnel['funnel'].items():
            pct = round(count / funnel['total_leads'] * 100, 1) if funnel['total_leads'] > 0 else 0
            print(f"  {stage}: {count} ({pct}%)")

        if funnel['conversion_rates']:
            print("\nConversion Rates:")
            for rate_name, rate_value in funnel['conversion_rates'].items():
                print(f"  {rate_name}: {rate_value}%")

    elif command == 'gaps':
        gaps = analytics.identify_gaps()

        print("\n=== LEAD MANAGEMENT GAPS ===\n")

        if not gaps:
            print("✅ No gaps detected - all leads being properly managed!")
        else:
            for gap in gaps:
                severity_icon = "🔴" if gap['severity'] == 'critical' else "🟡"
                print(f"{severity_icon} {gap['type'].upper()}")
                print(f"   {gap['message']}")
                print(f"   Lead IDs: {', '.join([l[:8] + '...' for l in gap['lead_ids'][:5]])}")
                print()

    elif command == 'lost':
        lost = analytics.get_lost_leads()

        print("\n=== COLD LEADS (14+ DAYS INACTIVE) ===\n")
        print(f"Total: {len(lost)}")

        if lost:
            print("\nLeads:")
            for lead in lost[:10]:  # Show first 10
                print(f"  {lead['lead_id'][:8]}... ({lead['business_id']})")
                print(f"    Source: {lead['source_channel']}")
                print(f"    Status: {lead['status']}")
                print(f"    Days Inactive: {lead['days_inactive']}")
                print()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
