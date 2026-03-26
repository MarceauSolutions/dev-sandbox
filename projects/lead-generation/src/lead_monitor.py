#!/usr/bin/env python3
"""
Lead Monitor - Tracks lead inventory and sends alerts when running low.

Features:
- Monitors Apollo leads remaining vs enrolled
- Monitors Google Places leads remaining
- Sends alerts via SMS/email when below threshold
- Daily digest of outreach capacity
- Tracks burn rate (leads consumed per day)

Usage:
    python -m src.lead_monitor status
    python -m src.lead_monitor check --alert
    python -m src.lead_monitor forecast
"""

import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


@dataclass
class LeadInventory:
    """Current lead inventory status."""
    source: str
    total: int
    with_phone: int
    enrolled: int
    available: int
    opted_out: int
    exhausted: int  # Completed all touches, no response
    daily_burn_rate: float  # Leads consumed per day
    days_remaining: float  # At current burn rate


@dataclass
class AlertConfig:
    """Alert thresholds and settings."""
    low_threshold: int = 100  # Alert when below this
    critical_threshold: int = 50  # Critical alert
    days_warning: int = 7  # Alert if running out in X days
    alert_phone: str = ""  # SMS alert recipient
    alert_email: str = ""  # Email alert recipient


class LeadMonitor:
    """
    Monitors lead inventory across all sources.

    Tracks:
    - Apollo B2B leads
    - Google Places leads
    - Yelp leads
    - Custom imported leads
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.history_file = self.output_dir / "lead_inventory_history.json"

        # Load history for burn rate calculation
        self.history: List[Dict] = []
        self._load_history()

        # Default alert config
        self.alert_config = AlertConfig(
            alert_phone=os.getenv("ALERT_PHONE", ""),
            alert_email=os.getenv("ALERT_EMAIL", os.getenv("SMTP_USERNAME", ""))
        )

    def _load_history(self) -> None:
        """Load inventory history for trend analysis."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)

    def _save_history(self, snapshot: Dict) -> None:
        """Save current snapshot to history."""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "snapshot": snapshot
        })
        # Keep last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        self.history = [
            h for h in self.history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _calculate_burn_rate(self, source: str) -> float:
        """Calculate daily burn rate from history."""
        if len(self.history) < 2:
            return 10.0  # Default assumption

        # Get data points from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent = [
            h for h in self.history
            if datetime.fromisoformat(h["timestamp"]) > week_ago
        ]

        if len(recent) < 2:
            return 10.0

        # Calculate change
        first = recent[0]["snapshot"].get(source, {}).get("available", 0)
        last = recent[-1]["snapshot"].get(source, {}).get("available", 0)
        days = (
            datetime.fromisoformat(recent[-1]["timestamp"]) -
            datetime.fromisoformat(recent[0]["timestamp"])
        ).days or 1

        burn = (first - last) / days
        return max(burn, 0.1)  # Minimum 0.1 to avoid division by zero

    def get_apollo_inventory(self) -> LeadInventory:
        """Get Apollo leads inventory."""
        apollo_file = self.output_dir / "apollo_csv_leads.json"
        enrolled_file = self.output_dir / "apollo_enrolled_leads.json"
        sequences_file = self.output_dir / "follow_up_sequences.json"

        total = 0
        with_phone = 0
        enrolled = 0

        # Count total and with phone
        if apollo_file.exists():
            with open(apollo_file, 'r') as f:
                data = json.load(f)
                people = data.get("people", data) if isinstance(data, dict) else data
                total = len(people)
                with_phone = len([
                    p for p in people
                    if p.get("phone_numbers")
                ])

        # Count enrolled
        if enrolled_file.exists():
            with open(enrolled_file, 'r') as f:
                data = json.load(f)
                enrolled = len(data.get("enrolled_ids", []))

        # Count exhausted (completed sequence, no response)
        exhausted = 0
        if sequences_file.exists():
            with open(sequences_file, 'r') as f:
                data = json.load(f)
                for seq in data.get("sequences", []):
                    if seq.get("status") == "exhausted":
                        exhausted += 1

        available = with_phone - enrolled
        burn_rate = self._calculate_burn_rate("apollo")
        days_remaining = available / burn_rate if burn_rate > 0 else 999

        return LeadInventory(
            source="apollo",
            total=total,
            with_phone=with_phone,
            enrolled=enrolled,
            available=available,
            opted_out=0,  # TODO: Track separately
            exhausted=exhausted,
            daily_burn_rate=burn_rate,
            days_remaining=days_remaining
        )

    def get_google_places_inventory(self) -> LeadInventory:
        """Get Google Places leads inventory."""
        leads_file = self.output_dir / "leads.json"
        sequences_file = self.output_dir / "follow_up_sequences.json"

        total = 0
        with_phone = 0
        enrolled = 0
        exhausted = 0

        # Count from leads file
        if leads_file.exists():
            with open(leads_file, 'r') as f:
                data = json.load(f)
                leads = data.get("leads", [])
                total = len(leads)
                with_phone = len([l for l in leads if l.get("phone")])

        # Count enrolled Google Places leads (source != apollo)
        if sequences_file.exists():
            with open(sequences_file, 'r') as f:
                data = json.load(f)
                for seq in data.get("sequences", []):
                    # Check if it's a Google Places lead (no apollo_b2b pain point)
                    touchpoints = seq.get("touchpoints", [])
                    is_apollo = any("apollo" in tp.get("template_name", "") for tp in touchpoints)
                    if not is_apollo:
                        enrolled += 1
                        if seq.get("status") == "exhausted":
                            exhausted += 1

        available = with_phone - enrolled
        burn_rate = self._calculate_burn_rate("google_places")
        days_remaining = available / burn_rate if burn_rate > 0 else 999

        return LeadInventory(
            source="google_places",
            total=total,
            with_phone=with_phone,
            enrolled=enrolled,
            available=available,
            opted_out=0,
            exhausted=exhausted,
            daily_burn_rate=burn_rate,
            days_remaining=days_remaining
        )

    def get_all_inventory(self) -> Dict[str, LeadInventory]:
        """Get inventory for all lead sources."""
        return {
            "apollo": self.get_apollo_inventory(),
            "google_places": self.get_google_places_inventory()
        }

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check if any alerts need to be triggered."""
        alerts = []
        inventory = self.get_all_inventory()

        for source, inv in inventory.items():
            # Critical threshold
            if inv.available < self.alert_config.critical_threshold:
                alerts.append({
                    "level": "CRITICAL",
                    "source": source,
                    "message": f"Only {inv.available} {source} leads remaining!",
                    "available": inv.available,
                    "days_remaining": inv.days_remaining
                })
            # Low threshold
            elif inv.available < self.alert_config.low_threshold:
                alerts.append({
                    "level": "WARNING",
                    "source": source,
                    "message": f"Low leads: {inv.available} {source} leads remaining",
                    "available": inv.available,
                    "days_remaining": inv.days_remaining
                })
            # Days warning
            elif inv.days_remaining < self.alert_config.days_warning:
                alerts.append({
                    "level": "WARNING",
                    "source": source,
                    "message": f"{source} leads will run out in {inv.days_remaining:.1f} days",
                    "available": inv.available,
                    "days_remaining": inv.days_remaining
                })

        return alerts

    def send_alert_sms(self, message: str) -> bool:
        """Send SMS alert via Twilio."""
        if not self.alert_config.alert_phone:
            return False

        try:
            from twilio.rest import Client

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            from_phone = os.getenv("TWILIO_PHONE_NUMBER")

            if not all([account_sid, auth_token, from_phone]):
                return False

            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_phone,
                to=self.alert_config.alert_phone
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send alert SMS: {e}")
            return False

    def generate_status_report(self) -> str:
        """Generate human-readable status report."""
        inventory = self.get_all_inventory()
        alerts = self.check_alerts()

        lines = [
            "=" * 50,
            f"LEAD INVENTORY STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 50,
            ""
        ]

        # Alerts first
        if alerts:
            lines.append("⚠️  ALERTS:")
            for alert in alerts:
                icon = "🔴" if alert["level"] == "CRITICAL" else "🟡"
                lines.append(f"  {icon} [{alert['level']}] {alert['message']}")
            lines.append("")

        # Inventory by source
        for source, inv in inventory.items():
            lines.extend([
                f"📊 {source.upper()}:",
                f"   Total leads:     {inv.total:,}",
                f"   With phone:      {inv.with_phone:,}",
                f"   Already enrolled: {inv.enrolled:,}",
                f"   Available:       {inv.available:,}",
                f"   Exhausted:       {inv.exhausted:,}",
                f"   Daily burn rate: {inv.daily_burn_rate:.1f}/day",
                f"   Days remaining:  {inv.days_remaining:.1f}",
                ""
            ])

        # Recommendations
        lines.append("📋 RECOMMENDATIONS:")
        total_available = sum(inv.available for inv in inventory.values())
        if total_available < 200:
            lines.append("   → Run new Apollo search to replenish leads")

        apollo = inventory.get("apollo")
        if apollo and apollo.days_remaining < 14:
            lines.append(f"   → Apollo leads will run out in {apollo.days_remaining:.0f} days")
            lines.append("   → Consider increasing Apollo batch size or running new search")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def save_snapshot(self) -> None:
        """Save current inventory snapshot for trend tracking."""
        inventory = self.get_all_inventory()
        snapshot = {
            source: asdict(inv) for source, inv in inventory.items()
        }
        self._save_history(snapshot)


def main():
    """CLI for lead monitoring."""
    parser = argparse.ArgumentParser(description="Lead Inventory Monitor")
    parser.add_argument("command", choices=["status", "check", "forecast", "snapshot"],
                       help="Command to run")
    parser.add_argument("--alert", action="store_true",
                       help="Send alerts if thresholds exceeded")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    monitor = LeadMonitor()

    if args.command == "status":
        if args.json:
            inventory = monitor.get_all_inventory()
            print(json.dumps({k: asdict(v) for k, v in inventory.items()}, indent=2))
        else:
            print(monitor.generate_status_report())

    elif args.command == "check":
        alerts = monitor.check_alerts()

        if not alerts:
            print("✅ All lead inventories healthy")
        else:
            for alert in alerts:
                print(f"[{alert['level']}] {alert['message']}")

            if args.alert:
                # Send SMS alerts for critical issues
                critical = [a for a in alerts if a["level"] == "CRITICAL"]
                if critical:
                    msg = "🚨 LEAD ALERT: " + "; ".join(a["message"] for a in critical)
                    if monitor.send_alert_sms(msg):
                        print(f"\n📱 Alert SMS sent to {monitor.alert_config.alert_phone}")

    elif args.command == "forecast":
        inventory = monitor.get_all_inventory()
        print("\n📈 LEAD FORECAST (at current burn rate):\n")

        for source, inv in inventory.items():
            print(f"{source}:")
            print(f"  Current: {inv.available} available")
            print(f"  Burn rate: {inv.daily_burn_rate:.1f}/day")
            print(f"  Empty in: {inv.days_remaining:.0f} days")

            # Weekly projections
            for weeks in [1, 2, 4]:
                remaining = inv.available - (inv.daily_burn_rate * weeks * 7)
                print(f"  In {weeks} week(s): {max(0, int(remaining))} remaining")
            print()

    elif args.command == "snapshot":
        monitor.save_snapshot()
        print("✅ Inventory snapshot saved to history")


if __name__ == "__main__":
    main()
