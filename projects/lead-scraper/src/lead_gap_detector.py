"""
Lead Gap Detection and Alert System

Automated system to detect leads falling through cracks and alert William
via SMS/email. Prevents lost opportunities from missed follow-ups.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.lead_intake import LeadIntakeSystem
from src.lead_analytics import LeadAnalytics


class LeadGapDetector:
    """Automated lead gap detection and alerting"""

    def __init__(self):
        """Initialize gap detector"""
        self.lead_system = LeadIntakeSystem()
        self.analytics = LeadAnalytics()

        # Alert configuration
        self.alert_email = os.getenv('DIGEST_RECIPIENT', 'william@example.com')
        self.alert_sms = os.getenv('TWILIO_PHONE_NUMBER', '+18552399364')

        # Track detected gaps
        project_root = Path(__file__).parent.parent
        self.gaps_file = project_root / 'output' / 'detected_gaps.json'
        self.gaps_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_gaps()

    def _load_gaps(self):
        """Load previously detected gaps"""
        if self.gaps_file.exists():
            with open(self.gaps_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.gaps_history = data
                else:
                    self.gaps_history = []
        else:
            self.gaps_history = []

    def _save_gaps(self):
        """Save detected gaps"""
        with open(self.gaps_file, 'w') as f:
            json.dump(self.gaps_history, f, indent=2, default=str)

    def scan_for_gaps(self) -> List[Dict]:
        """Scan lead_intake.json for all gap types

        Returns:
            List of detected gaps
        """
        all_gaps = []

        # Gap 1: No follow-up within 24 hours
        gaps = self._detect_no_followup_24h()
        all_gaps.extend(gaps)

        # Gap 2: Hot lead not in CRM after 48 hours
        gaps = self._detect_hot_lead_not_in_crm()
        all_gaps.extend(gaps)

        # Gap 3: Callback requested but not scheduled
        gaps = self._detect_callback_not_scheduled()
        all_gaps.extend(gaps)

        # Gap 4: Form submission with no contact attempt
        gaps = self._detect_form_no_contact()
        all_gaps.extend(gaps)

        # Gap 5: Cold leads (30+ days no activity, never converted)
        gaps = self._detect_archive_candidates()
        all_gaps.extend(gaps)

        # Save scan results
        scan_record = {
            'timestamp': datetime.now().isoformat(),
            'gaps_found': len(all_gaps),
            'gaps': all_gaps
        }
        self.gaps_history.append(scan_record)
        self._save_gaps()

        return all_gaps

    def _detect_no_followup_24h(self) -> List[Dict]:
        """Detect leads with no follow-up within 24 hours

        Returns:
            List of gap dicts
        """
        cutoff = datetime.now() - timedelta(hours=24)
        gaps = []

        for lead in self.lead_system.leads:
            # Skip if already converted/lost
            if lead.get('status') in ['converted', 'won', 'lost']:
                continue

            # Check if only 1 touchpoint (no follow-up)
            touchpoints = lead.get('touchpoint_history', [])
            if len(touchpoints) == 1:
                first_touch = datetime.fromisoformat(touchpoints[0]['timestamp'])
                if first_touch < cutoff:
                    gaps.append({
                        'type': 'no_followup_24h',
                        'severity': 'high',
                        'lead_id': lead['lead_id'],
                        'business_id': lead.get('business_id'),
                        'contact_info': lead.get('contact_info'),
                        'source_channel': lead.get('source_channel'),
                        'hours_since_first_touch': round((datetime.now() - first_touch).total_seconds() / 3600, 1),
                        'message': f"No follow-up for {round((datetime.now() - first_touch).total_seconds() / 3600, 1)} hours"
                    })

        return gaps

    def _detect_hot_lead_not_in_crm(self) -> List[Dict]:
        """Detect hot leads not synced to CRM after 48 hours

        Returns:
            List of gap dicts
        """
        cutoff = datetime.now() - timedelta(hours=48)
        gaps = []

        for lead in self.lead_system.leads:
            # Must be high priority and qualified/converted
            if lead.get('priority') not in ['critical', 'high']:
                continue
            if lead.get('status') not in ['qualified', 'converted']:
                continue

            # Not synced to CRM
            if lead.get('crm_synced'):
                continue

            # Check if 48+ hours old
            created = datetime.fromisoformat(lead['timestamp'])
            if created < cutoff:
                gaps.append({
                    'type': 'hot_lead_not_in_crm',
                    'severity': 'critical',
                    'lead_id': lead['lead_id'],
                    'business_id': lead.get('business_id'),
                    'contact_info': lead.get('contact_info'),
                    'priority': lead.get('priority'),
                    'status': lead.get('status'),
                    'hours_old': round((datetime.now() - created).total_seconds() / 3600, 1),
                    'message': f"Hot lead ({lead.get('priority')}) not in CRM - {round((datetime.now() - created).total_seconds() / 3600, 1)} hours old"
                })

        return gaps

    def _detect_callback_not_scheduled(self) -> List[Dict]:
        """Detect voice AI callback requests not scheduled within 3 days

        Returns:
            List of gap dicts
        """
        cutoff = datetime.now() - timedelta(days=3)
        gaps = []

        for lead in self.lead_system.leads:
            # Must be voice AI call
            if lead.get('source_channel') != 'voice_ai_call':
                continue

            # Check if callback was requested
            source_detail = lead.get('source_detail', {})
            if source_detail.get('outcome') != 'callback_requested':
                continue

            # Still in qualified status (not converted yet)
            if lead.get('status') != 'qualified':
                continue

            # Check if 3+ days old
            created = datetime.fromisoformat(lead['timestamp'])
            if created < cutoff:
                gaps.append({
                    'type': 'callback_not_scheduled',
                    'severity': 'high',
                    'lead_id': lead['lead_id'],
                    'business_id': lead.get('business_id'),
                    'contact_info': lead.get('contact_info'),
                    'call_sid': source_detail.get('call_sid'),
                    'days_old': (datetime.now() - created).days,
                    'message': f"Callback requested {(datetime.now() - created).days} days ago - not scheduled"
                })

        return gaps

    def _detect_form_no_contact(self) -> List[Dict]:
        """Detect form submissions with no contact attempt

        Returns:
            List of gap dicts
        """
        gaps = []

        for lead in self.lead_system.leads:
            # Must be form submission
            if lead.get('source_channel') != 'form_submission':
                continue

            # Still in 'new' status (never contacted)
            if lead.get('status') != 'new':
                continue

            # Only 1 touchpoint (the form submission itself)
            touchpoints = lead.get('touchpoint_history', [])
            if len(touchpoints) > 1:
                continue

            gaps.append({
                'type': 'form_submit_no_contact',
                'severity': 'high',
                'lead_id': lead['lead_id'],
                'business_id': lead.get('business_id'),
                'contact_info': lead.get('contact_info'),
                'message': f"Form submission never contacted"
            })

        return gaps

    def _detect_archive_candidates(self) -> List[Dict]:
        """Detect leads that should be archived (30+ days old, never converted)

        Returns:
            List of gap dicts
        """
        cutoff = datetime.now() - timedelta(days=30)
        gaps = []

        for lead in self.lead_system.leads:
            # Skip if already won/lost
            if lead.get('status') in ['won', 'lost']:
                continue

            # Check if old and never progressed
            last_contact = datetime.fromisoformat(lead['last_contact'])
            if last_contact < cutoff and lead.get('status') in ['new', 'contacted']:
                gaps.append({
                    'type': 'archive_candidate',
                    'severity': 'low',
                    'lead_id': lead['lead_id'],
                    'business_id': lead.get('business_id'),
                    'contact_info': lead.get('contact_info'),
                    'days_inactive': (datetime.now() - last_contact).days,
                    'message': f"Inactive for {(datetime.now() - last_contact).days} days - recommend archiving"
                })

        return gaps

    def send_alert(self, gaps: List[Dict], method: str = 'email'):
        """Send alert about detected gaps

        Args:
            gaps: List of gap dicts
            method: Alert method ('email', 'sms', or 'both')
        """
        if not gaps:
            return

        # Filter for critical/high severity only
        critical_gaps = [g for g in gaps if g.get('severity') in ['critical', 'high']]

        if not critical_gaps:
            return

        # Build alert message
        message = "LEAD GAP ALERT\n\n"
        message += f"Found {len(critical_gaps)} critical/high priority gaps:\n\n"

        for gap in critical_gaps[:5]:  # Limit to 5 in alert
            message += f"• {gap['type']}: {gap['message']}\n"
            if 'contact_info' in gap:
                phone = gap['contact_info'].get('phone', 'N/A')
                message += f"  Contact: {phone}\n"

        if method in ['email', 'both']:
            self._send_email_alert(message, critical_gaps)

        if method in ['sms', 'both']:
            self._send_sms_alert(message, critical_gaps)

    def _send_email_alert(self, message: str, gaps: List[Dict]):
        """Send email alert

        Args:
            message: Alert message
            gaps: Gap dicts
        """
        # Would integrate with SMTP here
        print(f"\n📧 EMAIL ALERT to {self.alert_email}:")
        print(message)

    def _send_sms_alert(self, message: str, gaps: List[Dict]):
        """Send SMS alert via Twilio

        Args:
            message: Alert message
            gaps: Gap dicts
        """
        # Would integrate with Twilio here
        print(f"\n📱 SMS ALERT to {self.alert_sms}:")
        # Truncate for SMS (160 chars)
        sms_message = message[:160]
        print(sms_message)

    def auto_remediate(self, gaps: List[Dict], dry_run: bool = True):
        """Auto-remediate certain gap types

        Args:
            gaps: List of gap dicts
            dry_run: If True, don't actually remediate (just report)
        """
        remediation_actions = []

        for gap in gaps:
            gap_type = gap['type']

            if gap_type == 'hot_lead_not_in_crm':
                # Auto-sync to CRM with HIGH priority
                action = f"Add to CRM: {gap['lead_id'][:8]}... (HIGH priority)"
                remediation_actions.append(action)

                if not dry_run:
                    # Would trigger CRM sync here
                    pass

            elif gap_type == 'callback_not_scheduled':
                # Add to CRM with note to schedule callback
                action = f"Add to CRM: {gap['lead_id'][:8]}... (SCHEDULE CALLBACK)"
                remediation_actions.append(action)

                if not dry_run:
                    # Would trigger CRM sync with callback note
                    pass

        if remediation_actions:
            mode = "WOULD" if dry_run else "DID"
            print(f"\n🔧 AUTO-REMEDIATION ({mode}):")
            for action in remediation_actions:
                print(f"  • {action}")

    def get_weekly_report(self) -> Dict:
        """Generate weekly gap detection report

        Returns:
            Report dict
        """
        # Get scans from last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        recent_scans = [
            scan for scan in self.gaps_history
            if datetime.fromisoformat(scan['timestamp']) > cutoff
        ]

        total_gaps = sum(scan['gaps_found'] for scan in recent_scans)

        # Count gaps prevented (gaps that were resolved)
        # This would track gaps that appeared then disappeared
        prevented = 0  # Placeholder

        return {
            'week_start': (datetime.now() - timedelta(days=7)).isoformat(),
            'week_end': datetime.now().isoformat(),
            'total_scans': len(recent_scans),
            'total_gaps_found': total_gaps,
            'gaps_prevented': prevented,
            'avg_gaps_per_scan': round(total_gaps / len(recent_scans), 1) if recent_scans else 0
        }


def main():
    """CLI for gap detector"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.lead_gap_detector <command>")
        print("\nCommands:")
        print("  scan                    - Scan for gaps")
        print("  alert                   - Scan and send alerts")
        print("  weekly-report           - Weekly gap detection summary")
        sys.exit(1)

    command = sys.argv[1]
    detector = LeadGapDetector()

    if command == 'scan':
        gaps = detector.scan_for_gaps()

        print("\n=== LEAD GAP DETECTION SCAN ===\n")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Total Gaps Found: {len(gaps)}")

        if gaps:
            # Group by severity
            by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
            for gap in gaps:
                severity = gap.get('severity', 'medium')
                by_severity[severity].append(gap)

            for severity in ['critical', 'high', 'medium', 'low']:
                if by_severity[severity]:
                    print(f"\n{severity.upper()} ({len(by_severity[severity])}):")
                    for gap in by_severity[severity]:
                        print(f"  • {gap['type']}: {gap['message']}")

        else:
            print("\n✅ No gaps detected!")

    elif command == 'alert':
        gaps = detector.scan_for_gaps()

        print(f"\nScanned and found {len(gaps)} gaps")

        # Send alerts
        detector.send_alert(gaps, method='both')

        # Auto-remediate
        detector.auto_remediate(gaps, dry_run=True)

    elif command == 'weekly-report':
        report = detector.get_weekly_report()

        print("\n=== WEEKLY GAP DETECTION REPORT ===\n")
        print(f"Period: {report['week_start'][:10]} to {report['week_end'][:10]}")
        print(f"Total Scans: {report['total_scans']}")
        print(f"Total Gaps Found: {report['total_gaps_found']}")
        print(f"Gaps Prevented: {report['gaps_prevented']}")
        print(f"Avg per Scan: {report['avg_gaps_per_scan']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
