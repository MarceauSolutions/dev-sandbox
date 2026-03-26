#!/usr/bin/env python3
"""
Campaign Monitoring Dashboard - Real-Time Outreach Health Check

Ensures no leads are missed and all follow-ups happen on schedule.

Key Features:
- Active campaign status by business
- Follow-up queue (overdue, today, upcoming)
- Unread reply alerts
- Response rate metrics
- Daily summary email

Usage:
    # Real-time dashboard (terminal)
    python -m src.campaign_monitor dashboard

    # Check overdue follow-ups
    python -m src.campaign_monitor overdue

    # Daily summary email
    python -m src.campaign_monitor email-summary

    # Export status report
    python -m src.campaign_monitor export --format json

    # Continuous monitoring (runs every 5 minutes)
    python -m src.campaign_monitor watch
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)


# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class CampaignStatus:
    """Status of active campaigns."""
    business_id: str
    business_name: str
    total_leads: int = 0
    active_sequences: int = 0

    # By touch number
    touch_1_sent: int = 0
    touch_2_sent: int = 0
    touch_3_pending: int = 0
    touch_4_pending: int = 0
    touch_5_pending: int = 0

    # Overdue
    overdue_count: int = 0
    overdue_touches: List[Dict[str, Any]] = field(default_factory=list)

    # Replies
    total_replies: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    opt_outs: int = 0

    # Metrics
    response_rate: float = 0.0
    opt_out_rate: float = 0.0

    # Last activity
    last_message_sent: str = ""
    last_reply_received: str = ""


@dataclass
class FollowUpAlert:
    """Alert for overdue or upcoming follow-up."""
    business_name: str
    phone: str
    touch_number: int
    template_name: str
    scheduled_at: str
    days_overdue: int = 0
    priority: str = "normal"  # critical (>3 days), high (1-3 days), normal (today), low (upcoming)


@dataclass
class ReplyAlert:
    """Alert for unprocessed reply."""
    business_name: str
    phone: str
    reply_text: str
    received_at: str
    category: str
    processed: bool
    hours_ago: float


class CampaignMonitor:
    """Monitor and analyze active outreach campaigns."""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "output"
        self.output_dir = output_dir

        # Data files
        self.campaigns_file = output_dir / "sms_campaigns.json"
        self.sequences_file = output_dir / "follow_up_sequences.json"
        self.replies_file = output_dir / "sms_replies.json"
        self.queue_file = output_dir / "outreach_queue.json"

        # Loaded data
        self.campaigns_data = {}
        self.sequences_data = {}
        self.replies_data = {}
        self.queue_data = {}

        # Analysis results
        self.business_statuses: Dict[str, CampaignStatus] = {}
        self.overdue_alerts: List[FollowUpAlert] = []
        self.upcoming_alerts: List[FollowUpAlert] = []
        self.reply_alerts: List[ReplyAlert] = []

    def load_data(self):
        """Load all campaign data files."""
        # Load campaigns
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                self.campaigns_data = json.load(f)

        # Load sequences
        if self.sequences_file.exists():
            with open(self.sequences_file, 'r') as f:
                self.sequences_data = json.load(f)

        # Load replies
        if self.replies_file.exists():
            with open(self.replies_file, 'r') as f:
                self.replies_data = json.load(f)

        # Load queue
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                self.queue_data = json.load(f)

    def analyze(self):
        """Run comprehensive analysis of all campaigns."""
        now = datetime.now()

        # Get all sequences
        sequences = self.sequences_data.get('sequences', [])
        campaigns = self.campaigns_data.get('records', [])
        replies = self.replies_data.get('replies', [])

        # Group by business (infer from business_name patterns)
        business_map = self._map_businesses()

        # Analyze each business
        for business_id, business_name in business_map.items():
            status = CampaignStatus(
                business_id=business_id,
                business_name=business_name
            )

            # Filter sequences for this business
            biz_sequences = [s for s in sequences if self._belongs_to_business(s, business_id)]
            biz_campaigns = [c for c in campaigns if self._belongs_to_business(c, business_id)]
            biz_replies = [r for r in replies if self._belongs_to_business(r, business_id)]

            status.total_leads = len(biz_campaigns)
            status.active_sequences = len([s for s in biz_sequences if s.get('status') == 'in_sequence'])

            # Analyze touchpoints
            touch_counts = defaultdict(int)
            overdue_touches = []

            for seq in biz_sequences:
                if seq.get('status') != 'in_sequence':
                    continue

                touchpoints = seq.get('touchpoints', [])
                for tp in touchpoints:
                    touch_num = tp.get('touch_number', 0)
                    tp_status = tp.get('status', '')

                    if tp_status == 'sent' and tp.get('sent_at') != 'DRY_RUN':
                        touch_counts[f'touch_{touch_num}_sent'] += 1
                    elif tp_status == 'pending':
                        touch_counts[f'touch_{touch_num}_pending'] += 1

                        # Check if overdue
                        scheduled = tp.get('scheduled_at', '')
                        if scheduled:
                            try:
                                sched_dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00').split('+')[0])
                                if sched_dt < now:
                                    days_overdue = (now - sched_dt).days

                                    # Determine priority
                                    if days_overdue > 3:
                                        priority = "critical"
                                    elif days_overdue >= 1:
                                        priority = "high"
                                    else:
                                        priority = "normal"

                                    alert = FollowUpAlert(
                                        business_name=seq.get('business_name', 'Unknown'),
                                        phone=seq.get('phone', ''),
                                        touch_number=touch_num,
                                        template_name=tp.get('template_name', ''),
                                        scheduled_at=scheduled,
                                        days_overdue=days_overdue,
                                        priority=priority
                                    )
                                    overdue_touches.append(alert)
                                    self.overdue_alerts.append(alert)
                                elif sched_dt < now + timedelta(days=1):
                                    # Due within 24 hours
                                    alert = FollowUpAlert(
                                        business_name=seq.get('business_name', 'Unknown'),
                                        phone=seq.get('phone', ''),
                                        touch_number=touch_num,
                                        template_name=tp.get('template_name', ''),
                                        scheduled_at=scheduled,
                                        days_overdue=0,
                                        priority="low"
                                    )
                                    self.upcoming_alerts.append(alert)
                            except:
                                pass

            status.touch_1_sent = touch_counts.get('touch_1_sent', 0)
            status.touch_2_sent = touch_counts.get('touch_2_sent', 0)
            status.touch_3_pending = touch_counts.get('touch_3_pending', 0)
            status.touch_4_pending = touch_counts.get('touch_4_pending', 0)
            status.touch_5_pending = touch_counts.get('touch_5_pending', 0)
            status.overdue_count = len(overdue_touches)
            status.overdue_touches = [asdict(o) for o in overdue_touches]

            # Analyze replies
            status.total_replies = len(biz_replies)
            for reply in biz_replies:
                category = reply.get('category', '')
                if category == 'hot_lead':
                    status.hot_leads += 1
                elif category == 'warm_lead':
                    status.warm_leads += 1
                elif category == 'opt_out':
                    status.opt_outs += 1

                # Check if unprocessed
                if not reply.get('processed', True):
                    received = reply.get('date_sent', '')
                    try:
                        recv_dt = datetime.fromisoformat(received.replace('Z', '+00:00').split('+')[0])
                        hours_ago = (now - recv_dt).total_seconds() / 3600
                    except:
                        hours_ago = 0

                    self.reply_alerts.append(ReplyAlert(
                        business_name=reply.get('business_name', 'Unknown'),
                        phone=reply.get('from_phone', ''),
                        reply_text=reply.get('body', ''),
                        received_at=received,
                        category=category,
                        processed=reply.get('processed', False),
                        hours_ago=hours_ago
                    ))

            # Calculate rates
            if status.total_leads > 0:
                status.response_rate = (status.total_replies / status.total_leads) * 100
                status.opt_out_rate = (status.opt_outs / status.total_leads) * 100

            # Last activity
            if biz_campaigns:
                last_sent = max(c.get('sent_at', '') for c in biz_campaigns)
                status.last_message_sent = last_sent

            if biz_replies:
                last_reply = max(r.get('date_sent', '') for r in biz_replies)
                status.last_reply_received = last_reply

            self.business_statuses[business_id] = status

    def _map_businesses(self) -> Dict[str, str]:
        """Map business IDs to friendly names."""
        # Default businesses (can be expanded)
        return {
            'marceau-solutions': 'Marceau Solutions',
            'sw-fl-comfort': 'Southwest Florida Comfort',
            'footer-shipping': 'Footer Shipping',
            'all': 'All Campaigns (Legacy)'
        }

    def _belongs_to_business(self, record: Dict, business_id: str) -> bool:
        """Check if record belongs to a specific business."""
        # Check explicit business_id field
        if record.get('sending_business_id') == business_id:
            return True

        # Legacy: if no business_id, assume "all"
        if business_id == 'all' and not record.get('sending_business_id'):
            return True

        return False

    def print_dashboard(self):
        """Print real-time dashboard to terminal."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}CAMPAIGN MONITORING DASHBOARD{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Last Updated: {now}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

        # Critical alerts section
        if self.overdue_alerts or self.reply_alerts:
            print(f"{Colors.FAIL}{Colors.BOLD}⚠️  CRITICAL ALERTS{Colors.ENDC}")
            print(f"{Colors.BOLD}{'-'*80}{Colors.ENDC}")

            # Overdue follow-ups
            critical_overdue = [a for a in self.overdue_alerts if a.priority in ['critical', 'high']]
            if critical_overdue:
                print(f"\n{Colors.WARNING}Overdue Follow-Ups: {len(critical_overdue)}{Colors.ENDC}")
                for alert in sorted(critical_overdue, key=lambda x: x.days_overdue, reverse=True)[:10]:
                    priority_color = Colors.FAIL if alert.priority == 'critical' else Colors.WARNING
                    print(f"  {priority_color}• {alert.business_name} (Touch {alert.touch_number}) - {alert.days_overdue} days overdue{Colors.ENDC}")
                    print(f"    Phone: {alert.phone} | Template: {alert.template_name}")

            # Unprocessed replies
            if self.reply_alerts:
                print(f"\n{Colors.WARNING}Unprocessed Replies: {len(self.reply_alerts)}{Colors.ENDC}")
                for alert in sorted(self.reply_alerts, key=lambda x: x.hours_ago, reverse=True)[:5]:
                    category_color = Colors.OKGREEN if alert.category in ['hot_lead', 'warm_lead'] else Colors.OKCYAN
                    print(f"  {category_color}• {alert.business_name} ({alert.category}) - {alert.hours_ago:.1f}h ago{Colors.ENDC}")
                    print(f"    {alert.reply_text[:80]}...")

            print(f"\n{Colors.BOLD}{'-'*80}{Colors.ENDC}\n")

        # Business-by-business status
        print(f"{Colors.HEADER}{Colors.BOLD}CAMPAIGN STATUS BY BUSINESS{Colors.ENDC}")
        print(f"{Colors.BOLD}{'-'*80}{Colors.ENDC}\n")

        for biz_id, status in self.business_statuses.items():
            if status.total_leads == 0:
                continue

            print(f"{Colors.BOLD}{status.business_name}{Colors.ENDC} ({biz_id})")
            print(f"  Total Leads: {status.total_leads} | Active Sequences: {status.active_sequences}")
            print(f"  Touch Progress: T1={status.touch_1_sent} | T2={status.touch_2_sent} | T3={status.touch_3_pending} pending")
            print(f"  {Colors.OKGREEN}Replies: {status.total_replies} ({status.response_rate:.1f}%){Colors.ENDC} | "
                  f"{Colors.WARNING}Opt-outs: {status.opt_outs} ({status.opt_out_rate:.1f}%){Colors.ENDC}")

            if status.hot_leads > 0 or status.warm_leads > 0:
                print(f"  {Colors.OKGREEN}🔥 Hot Leads: {status.hot_leads} | Warm: {status.warm_leads}{Colors.ENDC}")

            if status.overdue_count > 0:
                print(f"  {Colors.FAIL}⚠️  Overdue Follow-Ups: {status.overdue_count}{Colors.ENDC}")

            if status.last_message_sent:
                print(f"  Last Sent: {status.last_message_sent[:19]}")
            if status.last_reply_received:
                print(f"  Last Reply: {status.last_reply_received[:19]}")

            print()

        # Upcoming follow-ups
        if self.upcoming_alerts:
            print(f"\n{Colors.OKCYAN}{Colors.BOLD}📅 UPCOMING (Next 24 Hours): {len(self.upcoming_alerts)}{Colors.ENDC}")
            for alert in sorted(self.upcoming_alerts, key=lambda x: x.scheduled_at)[:10]:
                print(f"  • {alert.business_name} (Touch {alert.touch_number}) - {alert.template_name}")
                print(f"    Scheduled: {alert.scheduled_at[:19]}")

        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    def export_report(self, format='json') -> Dict[str, Any]:
        """Export monitoring report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_businesses': len([b for b in self.business_statuses.values() if b.total_leads > 0]),
                'total_leads': sum(b.total_leads for b in self.business_statuses.values()),
                'active_sequences': sum(b.active_sequences for b in self.business_statuses.values()),
                'total_overdue': len(self.overdue_alerts),
                'critical_overdue': len([a for a in self.overdue_alerts if a.priority == 'critical']),
                'unprocessed_replies': len(self.reply_alerts),
                'upcoming_24h': len(self.upcoming_alerts)
            },
            'businesses': {
                biz_id: asdict(status)
                for biz_id, status in self.business_statuses.items()
                if status.total_leads > 0
            },
            'alerts': {
                'overdue': [asdict(a) for a in sorted(self.overdue_alerts, key=lambda x: x.days_overdue, reverse=True)],
                'upcoming': [asdict(a) for a in sorted(self.upcoming_alerts, key=lambda x: x.scheduled_at)],
                'replies': [asdict(a) for a in sorted(self.reply_alerts, key=lambda x: x.hours_ago, reverse=True)]
            }
        }

        if format == 'json':
            return report
        else:
            # Could add CSV, HTML, etc.
            return report

    def send_email_summary(self):
        """Send daily summary email."""
        # Import SMTP here to avoid dependency if not needed
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        recipient = os.getenv('DIGEST_RECIPIENT', smtp_user)

        if not all([smtp_host, smtp_user, smtp_pass]):
            print("⚠️  SMTP not configured. Skipping email.")
            return

        # Build email content
        subject = f"Campaign Monitor - Daily Summary ({datetime.now().strftime('%Y-%m-%d')})"

        body = f"""
Campaign Monitoring Daily Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
OVERVIEW
{'='*60}

Total Leads: {sum(b.total_leads for b in self.business_statuses.values())}
Active Sequences: {sum(b.active_sequences for b in self.business_statuses.values())}
Overdue Follow-Ups: {len(self.overdue_alerts)}
Unprocessed Replies: {len(self.reply_alerts)}
Upcoming (24h): {len(self.upcoming_alerts)}

"""

        # Add critical alerts
        critical = [a for a in self.overdue_alerts if a.priority in ['critical', 'high']]
        if critical:
            body += f"\n{'='*60}\n⚠️  CRITICAL ALERTS ({len(critical)})\n{'='*60}\n\n"
            for alert in sorted(critical, key=lambda x: x.days_overdue, reverse=True)[:10]:
                body += f"• {alert.business_name} (Touch {alert.touch_number}) - {alert.days_overdue} days overdue\n"
                body += f"  Template: {alert.template_name}\n\n"

        # Add business breakdown
        body += f"\n{'='*60}\nBUSINESS BREAKDOWN\n{'='*60}\n\n"
        for biz_id, status in self.business_statuses.items():
            if status.total_leads == 0:
                continue

            body += f"{status.business_name}\n"
            body += f"  Leads: {status.total_leads} | Active: {status.active_sequences}\n"
            body += f"  Response Rate: {status.response_rate:.1f}% | Opt-out: {status.opt_out_rate:.1f}%\n"
            body += f"  Hot: {status.hot_leads} | Warm: {status.warm_leads} | Opt-outs: {status.opt_outs}\n"
            if status.overdue_count > 0:
                body += f"  ⚠️  Overdue: {status.overdue_count}\n"
            body += "\n"

        # Send email
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"✅ Daily summary email sent to {recipient}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")


def main():
    parser = argparse.ArgumentParser(description='Campaign Monitoring Dashboard')
    parser.add_argument('command', choices=['dashboard', 'overdue', 'email-summary', 'export', 'watch'],
                       help='Command to run')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Export format')
    parser.add_argument('--output', type=str, help='Output file for export')
    parser.add_argument('--interval', type=int, default=300,
                       help='Watch interval in seconds (default: 300 = 5 minutes)')

    args = parser.parse_args()

    monitor = CampaignMonitor()
    monitor.load_data()
    monitor.analyze()

    if args.command == 'dashboard':
        monitor.print_dashboard()

    elif args.command == 'overdue':
        print(f"\n{Colors.FAIL}{Colors.BOLD}OVERDUE FOLLOW-UPS{Colors.ENDC}\n")
        if not monitor.overdue_alerts:
            print(f"{Colors.OKGREEN}✅ No overdue follow-ups!{Colors.ENDC}\n")
        else:
            for alert in sorted(monitor.overdue_alerts, key=lambda x: x.days_overdue, reverse=True):
                priority_color = Colors.FAIL if alert.priority == 'critical' else Colors.WARNING
                print(f"{priority_color}• {alert.business_name} (Touch {alert.touch_number}){Colors.ENDC}")
                print(f"  Phone: {alert.phone}")
                print(f"  Template: {alert.template_name}")
                print(f"  Days Overdue: {alert.days_overdue}")
                print(f"  Scheduled: {alert.scheduled_at}")
                print()

    elif args.command == 'email-summary':
        monitor.send_email_summary()

    elif args.command == 'export':
        report = monitor.export_report(format=args.format)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"✅ Report exported to {output_path}")
        else:
            print(json.dumps(report, indent=2))

    elif args.command == 'watch':
        print(f"👀 Starting continuous monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                monitor = CampaignMonitor()
                monitor.load_data()
                monitor.analyze()
                monitor.print_dashboard()

                print(f"\n💤 Sleeping {args.interval}s... (Ctrl+C to stop)")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")


if __name__ == '__main__':
    main()
