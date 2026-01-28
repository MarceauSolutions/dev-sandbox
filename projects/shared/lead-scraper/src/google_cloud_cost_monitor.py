#!/usr/bin/env python3
"""
Google Cloud Cost Monitor - Automated Billing Alert System

This script:
1. Polls Google Cloud Billing API daily for current spend
2. Compares spend against budget thresholds
3. Sends SMS alerts via Twilio when thresholds exceeded
4. Logs cost trends to JSON for historical analysis
5. Listens to Pub/Sub for real-time budget alerts

Usage:
    # Check current billing status (one-time)
    python -m src.google_cloud_cost_monitor

    # Run with custom alert threshold
    python -m src.google_cloud_cost_monitor --alert-threshold 25

    # Listen for Pub/Sub alerts (background mode)
    python -m src.google_cloud_cost_monitor --pubsub-listen

    # Run once and exit (for cron)
    python -m src.google_cloud_cost_monitor --once

    # Test SMS alert without checking billing
    python -m src.google_cloud_cost_monitor --test-sms

Setup:
    1. Enable Cloud Billing API:
       https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com

    2. Create service account with "Billing Account Viewer" role:
       https://console.cloud.google.com/iam-admin/serviceaccounts

    3. Download JSON key and set environment variable:
       export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

    4. Set up Pub/Sub topic for budget alerts (optional):
       https://console.cloud.google.com/cloudpubsub

Environment Variables (in .env):
    GOOGLE_PROJECT_ID=fitness-influencer-assistant
    GOOGLE_BILLING_ACCOUNT_ID=your-billing-account-id (optional)
    TWILIO_ACCOUNT_SID=ACfbc4026cbc748718b1aefce581716cea
    TWILIO_AUTH_TOKEN=227fc6e26dea5a2f81834920ed60f669
    TWILIO_PHONE_NUMBER=+18552399364
    NOTIFICATION_PHONE=+12393985676

Cron Setup (daily at 9 AM):
    0 9 * * * cd /path/to/lead-scraper && python -m src.google_cloud_cost_monitor --once >> /tmp/billing-monitor.log 2>&1
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Alert thresholds (in dollars)
THRESHOLDS = {
    'LOW': 10.0,      # 10% of $100 budget - email only
    'MEDIUM': 25.0,   # 25% of budget - email + SMS
    'HIGH': 50.0,     # 50% of budget - urgent SMS
    'CRITICAL': 100.0 # 100% of budget - disable APIs (optional)
}

# Budget
MONTHLY_BUDGET = 100.0  # $100/month


@dataclass
class BillingSnapshot:
    """Represents a billing status snapshot."""
    timestamp: str
    project_id: str
    current_spend: float
    budget: float
    percentage_used: float
    days_into_month: int
    projected_monthly_spend: float
    alert_level: str
    services_breakdown: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Twilio SMS Alert System
# =============================================================================

class SMSAlertManager:
    """Send SMS alerts via Twilio when billing thresholds exceeded."""

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.to_number = os.getenv('NOTIFICATION_PHONE')

        # Validate credentials
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            logger.warning("Twilio credentials not configured - SMS alerts disabled")
            self.enabled = False
        else:
            self.enabled = True

    def send_alert(self, message: str) -> bool:
        """Send SMS alert."""
        if not self.enabled:
            logger.warning(f"SMS alert would have been sent: {message}")
            return False

        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)
            sms = client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )

            logger.info(f"✅ SMS alert sent to {self.to_number} (SID: {sms.sid})")
            return True

        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def format_alert(self, snapshot: BillingSnapshot) -> str:
        """Format SMS alert message based on severity."""

        if snapshot.alert_level == 'CRITICAL':
            return (
                f"🔴 CRITICAL: Google Cloud budget exhausted!\n"
                f"💰 Spend: ${snapshot.current_spend:.2f} / ${snapshot.budget:.2f}\n"
                f"📊 {snapshot.percentage_used:.0f}% of monthly budget\n"
                f"⚠️ Consider disabling APIs to prevent overage"
            )

        elif snapshot.alert_level == 'HIGH':
            return (
                f"🚨 URGENT: Google Cloud costs at 50% budget\n"
                f"💰 Spend: ${snapshot.current_spend:.2f} / ${snapshot.budget:.2f}\n"
                f"📅 Day {snapshot.days_into_month} of month\n"
                f"📈 Projected: ${snapshot.projected_monthly_spend:.2f}"
            )

        elif snapshot.alert_level == 'MEDIUM':
            return (
                f"⚠️ WARNING: Google Cloud costs at 25% budget\n"
                f"💰 Spend: ${snapshot.current_spend:.2f} / ${snapshot.budget:.2f}\n"
                f"📅 Day {snapshot.days_into_month} of month"
            )

        else:  # LOW
            return (
                f"ℹ️ Google Cloud costs: ${snapshot.current_spend:.2f}\n"
                f"📊 {snapshot.percentage_used:.0f}% of ${snapshot.budget:.2f} budget"
            )


# =============================================================================
# Google Cloud Billing API Client
# =============================================================================

class BillingAPIClient:
    """Interface to Google Cloud Billing API."""

    def __init__(self, project_id: str, billing_account_id: Optional[str] = None):
        self.project_id = project_id
        self.billing_account_id = billing_account_id

        # Initialize client (lazy load)
        self._client = None

    def _get_client(self):
        """Lazy-load billing client."""
        if self._client is None:
            try:
                from google.cloud import billing_v1
                self._client = billing_v1.CloudBillingClient()
            except ImportError:
                logger.error("google-cloud-billing not installed. Run: pip install google-cloud-billing")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize billing client: {e}")
                return None

        return self._client

    def get_current_spend(self) -> Optional[float]:
        """
        Get current month-to-date spend for project.

        Note: This requires Cloud Billing API enabled and proper credentials.
        Falls back to estimate-based approach if API unavailable.
        """
        client = self._get_client()

        if not client:
            logger.warning("Billing API unavailable - using estimate-based approach")
            return None

        try:
            # Get billing info for project
            # Note: This is a simplified example - actual implementation would use
            # BigQuery billing export or Cloud Billing Catalog API for precise costs

            # For now, we'll use the estimate-based approach from check_google_api_costs.py
            # In production, you'd query BigQuery billing export table

            logger.warning("Using estimate-based billing (API integration TODO)")
            return None

        except Exception as e:
            logger.error(f"Failed to query billing API: {e}")
            return None

    def get_billing_account_id(self) -> Optional[str]:
        """Get billing account ID for project."""
        if self.billing_account_id:
            return self.billing_account_id

        client = self._get_client()
        if not client:
            return None

        try:
            project_name = f"projects/{self.project_id}"
            billing_info = client.get_project_billing_info(name=project_name)
            return billing_info.billing_account_name.split('/')[-1]

        except Exception as e:
            logger.error(f"Failed to get billing account: {e}")
            return None


# =============================================================================
# Estimate-Based Cost Tracker (Fallback)
# =============================================================================

class EstimateBasedCostTracker:
    """
    Estimate costs based on API usage (from leads scraped).
    Fallback when Cloud Billing API unavailable.
    """

    def __init__(self, leads_file: str = "output/leads.json"):
        self.leads_file = Path(__file__).parent.parent / leads_file

        # Cost constants (per 1,000 requests)
        self.NEARBY_SEARCH_COST = 32.00
        self.PLACE_DETAILS_COST = 25.00  # $17 basic + $3 contact + $5 atmosphere

    def get_api_usage(self) -> Dict[str, int]:
        """Count API calls from scraped leads."""
        if not self.leads_file.exists():
            logger.warning(f"Leads file not found: {self.leads_file}")
            return {
                'google_places_leads': 0,
                'nearby_search_calls': 0,
                'place_details_calls': 0,
                'total_calls': 0
            }

        try:
            with open(self.leads_file, 'r') as f:
                data = json.load(f)

            leads = data.get('leads', [])
            google_leads = [
                lead for lead in leads
                if lead.get('source', '').startswith('google_places')
            ]

            # Estimate API calls
            nearby_calls = len(google_leads) // 20 + 1  # ~20 results per search
            details_calls = len(google_leads)  # 1 per lead

            return {
                'google_places_leads': len(google_leads),
                'nearby_search_calls': nearby_calls,
                'place_details_calls': details_calls,
                'total_calls': nearby_calls + details_calls
            }

        except Exception as e:
            logger.error(f"Failed to read leads file: {e}")
            return {'google_places_leads': 0, 'nearby_search_calls': 0, 'place_details_calls': 0, 'total_calls': 0}

    def estimate_costs(self, api_usage: Dict[str, int]) -> Dict[str, float]:
        """Calculate estimated costs from API usage."""

        nearby_cost = (api_usage['nearby_search_calls'] / 1000) * self.NEARBY_SEARCH_COST
        details_cost = (api_usage['place_details_calls'] / 1000) * self.PLACE_DETAILS_COST
        total_cost = nearby_cost + details_cost

        return {
            'nearby_search': round(nearby_cost, 2),
            'place_details': round(details_cost, 2),
            'total': round(total_cost, 2),
            'google_maps': round(total_cost, 2),  # All costs are Maps Platform
            'other_services': 0.0
        }


# =============================================================================
# Billing Snapshot & Logging
# =============================================================================

class BillingSnapshotLogger:
    """Log billing snapshots for historical tracking."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.output_dir.mkdir(exist_ok=True)

        self.log_file = self.output_dir / "google_cloud_billing_log.json"
        self.snapshots: List[BillingSnapshot] = []
        self._load_log()

    def _load_log(self):
        """Load existing log."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.snapshots = [BillingSnapshot(**s) for s in data.get('snapshots', [])]
            except Exception as e:
                logger.error(f"Failed to load billing log: {e}")
                self.snapshots = []

    def _save_log(self):
        """Save log to file."""
        try:
            # Keep only last 90 days
            cutoff = datetime.now() - timedelta(days=90)
            self.snapshots = [
                s for s in self.snapshots
                if datetime.fromisoformat(s.timestamp) > cutoff
            ]

            data = {
                'snapshots': [s.to_dict() for s in self.snapshots],
                'last_updated': datetime.now().isoformat(),
                'summary': self._generate_summary()
            }

            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save billing log: {e}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not self.snapshots:
            return {}

        recent = self.snapshots[-30:] if len(self.snapshots) > 30 else self.snapshots

        return {
            'total_snapshots': len(self.snapshots),
            'current_spend': self.snapshots[-1].current_spend if self.snapshots else 0,
            'average_daily_spend': sum(s.current_spend for s in recent) / len(recent) if recent else 0,
            'highest_alert_level': max((s.alert_level for s in recent), default='NONE'),
            'days_tracked': len(self.snapshots)
        }

    def add_snapshot(self, snapshot: BillingSnapshot):
        """Add new snapshot to log."""
        self.snapshots.append(snapshot)
        self._save_log()

    def get_trend(self, days: int = 7) -> List[BillingSnapshot]:
        """Get billing trend for last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            s for s in self.snapshots
            if datetime.fromisoformat(s.timestamp) > cutoff
        ]


# =============================================================================
# Pub/Sub Listener (Real-Time Alerts)
# =============================================================================

class PubSubBillingListener:
    """Listen for budget alerts from Google Cloud Pub/Sub."""

    def __init__(self, project_id: str, subscription_id: str = "billing-alerts-handler"):
        self.project_id = project_id
        self.subscription_id = subscription_id
        self._subscriber = None

    def _get_subscriber(self):
        """Lazy-load Pub/Sub subscriber."""
        if self._subscriber is None:
            try:
                from google.cloud import pubsub_v1
                self._subscriber = pubsub_v1.SubscriberClient()
            except ImportError:
                logger.error("google-cloud-pubsub not installed. Run: pip install google-cloud-pubsub")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub client: {e}")
                return None

        return self._subscriber

    def listen(self, callback):
        """
        Listen for budget alert messages.

        Args:
            callback: Function to call when message received. Signature: callback(message_data: dict)
        """
        subscriber = self._get_subscriber()
        if not subscriber:
            logger.error("Pub/Sub unavailable")
            return

        subscription_path = subscriber.subscription_path(self.project_id, self.subscription_id)

        def message_callback(message):
            """Handle incoming Pub/Sub message."""
            try:
                data = json.loads(message.data.decode('utf-8'))
                logger.info(f"Received budget alert: {data}")

                # Call user callback
                callback(data)

                # Acknowledge message
                message.ack()

            except Exception as e:
                logger.error(f"Failed to process Pub/Sub message: {e}")
                message.nack()

        logger.info(f"Listening for budget alerts on: {subscription_path}")

        # Start listening (blocking)
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=message_callback)

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Pub/Sub listener stopped")


# =============================================================================
# Main Monitor Class
# =============================================================================

class GoogleCloudCostMonitor:
    """Main cost monitoring orchestrator."""

    def __init__(self, project_id: str, budget: float = MONTHLY_BUDGET):
        self.project_id = project_id
        self.budget = budget

        # Initialize components
        self.billing_api = BillingAPIClient(project_id)
        self.estimator = EstimateBasedCostTracker()
        self.sms_manager = SMSAlertManager()
        self.logger = BillingSnapshotLogger()
        self.pubsub_listener = PubSubBillingListener(project_id)

    def get_current_snapshot(self) -> BillingSnapshot:
        """Get current billing snapshot."""

        # Try to get actual spend from Billing API
        current_spend = self.billing_api.get_current_spend()

        # Fallback to estimate-based approach
        if current_spend is None:
            logger.info("Using estimate-based cost tracking")
            api_usage = self.estimator.get_api_usage()
            costs = self.estimator.estimate_costs(api_usage)
            current_spend = costs['total']
            services_breakdown = {
                'google_maps': costs['google_maps'],
                'other_services': costs['other_services']
            }
        else:
            services_breakdown = {}

        # Calculate metrics
        percentage_used = (current_spend / self.budget) * 100
        days_into_month = datetime.now().day
        days_in_month = 30  # Simplified
        projected_monthly_spend = (current_spend / days_into_month) * days_in_month

        # Determine alert level
        if current_spend >= THRESHOLDS['CRITICAL']:
            alert_level = 'CRITICAL'
        elif current_spend >= THRESHOLDS['HIGH']:
            alert_level = 'HIGH'
        elif current_spend >= THRESHOLDS['MEDIUM']:
            alert_level = 'MEDIUM'
        elif current_spend >= THRESHOLDS['LOW']:
            alert_level = 'LOW'
        else:
            alert_level = 'NONE'

        snapshot = BillingSnapshot(
            timestamp=datetime.now().isoformat(),
            project_id=self.project_id,
            current_spend=current_spend,
            budget=self.budget,
            percentage_used=percentage_used,
            days_into_month=days_into_month,
            projected_monthly_spend=projected_monthly_spend,
            alert_level=alert_level,
            services_breakdown=services_breakdown
        )

        return snapshot

    def check_and_alert(self, send_sms: bool = True) -> BillingSnapshot:
        """
        Check billing status and send alerts if thresholds exceeded.

        Args:
            send_sms: Whether to send SMS alerts (default: True)

        Returns:
            BillingSnapshot
        """
        snapshot = self.get_current_snapshot()

        # Log snapshot
        self.logger.add_snapshot(snapshot)

        # Print report
        self.print_report(snapshot)

        # Send SMS if alert level warrants it
        if send_sms and snapshot.alert_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
            message = self.sms_manager.format_alert(snapshot)
            self.sms_manager.send_alert(message)

        return snapshot

    def print_report(self, snapshot: BillingSnapshot):
        """Print human-readable billing report."""

        print("\n" + "=" * 70)
        print("💰 GOOGLE CLOUD BILLING MONITOR")
        print("=" * 70)
        print(f"Project: {snapshot.project_id}")
        print(f"Timestamp: {datetime.fromisoformat(snapshot.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        print(f"\n📊 CURRENT STATUS:")
        print(f"  Current spend: ${snapshot.current_spend:.2f}")
        print(f"  Monthly budget: ${snapshot.budget:.2f}")
        print(f"  Percentage used: {snapshot.percentage_used:.1f}%")
        print(f"  Days into month: {snapshot.days_into_month}")
        print(f"  Projected monthly: ${snapshot.projected_monthly_spend:.2f}")

        if snapshot.services_breakdown:
            print(f"\n🗂️  SERVICES BREAKDOWN:")
            for service, cost in snapshot.services_breakdown.items():
                print(f"  {service}: ${cost:.2f}")

        print(f"\n🚨 ALERT LEVEL: {snapshot.alert_level}")

        if snapshot.alert_level == 'CRITICAL':
            print("  🔴 CRITICAL - Budget exhausted! Consider disabling APIs.")
        elif snapshot.alert_level == 'HIGH':
            print("  🚨 HIGH - 50% of budget used. Review and optimize.")
        elif snapshot.alert_level == 'MEDIUM':
            print("  ⚠️  MEDIUM - 25% of budget used. Monitor closely.")
        elif snapshot.alert_level == 'LOW':
            print("  ℹ️  LOW - 10% of budget used. Normal usage.")
        else:
            print("  ✅ NONE - Under 10% of budget. All good!")

        print("\n" + "=" * 70 + "\n")

    def listen_pubsub(self):
        """Listen for real-time budget alerts from Pub/Sub."""

        def handle_alert(message_data: dict):
            """Handle Pub/Sub budget alert message."""
            budget_name = message_data.get('budgetDisplayName', 'Unknown')
            cost_amount = message_data.get('costAmount', 0)
            budget_amount = message_data.get('budgetAmount', 0)
            threshold = message_data.get('alertThresholdExceeded', 0)

            logger.info(f"Budget alert received: {budget_name}")
            logger.info(f"  Cost: ${cost_amount:.2f} / ${budget_amount:.2f}")
            logger.info(f"  Threshold: {threshold * 100:.0f}%")

            # Send SMS alert
            alert_msg = (
                f"🚨 Budget Alert: {budget_name}\n"
                f"💰 ${cost_amount:.2f} / ${budget_amount:.2f}\n"
                f"📊 {threshold * 100:.0f}% threshold exceeded"
            )
            self.sms_manager.send_alert(alert_msg)

        logger.info("Starting Pub/Sub listener for budget alerts...")
        self.pubsub_listener.listen(handle_alert)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Google Cloud Cost Monitor - Automated billing alerts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current billing status (one-time)
  python -m src.google_cloud_cost_monitor

  # Run with custom budget
  python -m src.google_cloud_cost_monitor --budget 50

  # Listen for Pub/Sub alerts (background)
  python -m src.google_cloud_cost_monitor --pubsub-listen

  # Run once and exit (for cron)
  python -m src.google_cloud_cost_monitor --once

  # Test SMS without checking billing
  python -m src.google_cloud_cost_monitor --test-sms
        """
    )

    parser.add_argument('--project-id', type=str, default=os.getenv('GOOGLE_PROJECT_ID'),
                       help='Google Cloud project ID (default: from GOOGLE_PROJECT_ID env var)')
    parser.add_argument('--budget', type=float, default=MONTHLY_BUDGET,
                       help=f'Monthly budget in dollars (default: ${MONTHLY_BUDGET})')
    parser.add_argument('--pubsub-listen', action='store_true',
                       help='Listen for Pub/Sub budget alerts (blocking)')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (for cron jobs)')
    parser.add_argument('--test-sms', action='store_true',
                       help='Test SMS alert without checking billing')
    parser.add_argument('--no-sms', action='store_true',
                       help='Disable SMS alerts (only print report)')

    args = parser.parse_args()

    # Validate project ID
    if not args.project_id:
        logger.error("Project ID not set. Use --project-id or set GOOGLE_PROJECT_ID env var")
        return 1

    # Initialize monitor
    monitor = GoogleCloudCostMonitor(args.project_id, args.budget)

    # Test SMS
    if args.test_sms:
        test_snapshot = BillingSnapshot(
            timestamp=datetime.now().isoformat(),
            project_id=args.project_id,
            current_spend=55.0,
            budget=args.budget,
            percentage_used=55.0,
            days_into_month=15,
            projected_monthly_spend=110.0,
            alert_level='HIGH',
            services_breakdown={'google_maps': 55.0}
        )
        message = monitor.sms_manager.format_alert(test_snapshot)
        print(f"\nTest SMS message:\n{message}\n")
        monitor.sms_manager.send_alert(message)
        return 0

    # Pub/Sub listener mode
    if args.pubsub_listen:
        try:
            monitor.listen_pubsub()
        except KeyboardInterrupt:
            logger.info("Pub/Sub listener stopped by user")
        return 0

    # Standard check mode
    send_sms = not args.no_sms
    snapshot = monitor.check_and_alert(send_sms=send_sms)

    # Exit code based on alert level
    if snapshot.alert_level == 'CRITICAL':
        return 2  # Critical
    elif snapshot.alert_level == 'HIGH':
        return 1  # Warning
    else:
        return 0  # OK


if __name__ == '__main__':
    import sys
    sys.exit(main())
