#!/usr/bin/env python3
"""
SMS Outreach Scheduler - Automated sending at optimal times.

Features:
- TCPA/Florida compliance (8AM-8PM recipient timezone)
- Optimal time windows (Tue-Fri, 9AM-11AM peak)
- Daily batch scheduling with rate limiting
- A/B testing support for timing
- Cron-compatible execution

Usage:
    # Check what would be sent (dry run)
    python -m src.sms_scheduler preview

    # Execute scheduled sends
    python -m src.sms_scheduler run

    # Schedule for specific time window
    python -m src.sms_scheduler run --window morning

    # Run via cron (add to crontab)
    # 0 9 * * 2-5 cd /path/to/lead-scraper && python -m src.sms_scheduler run --window morning
"""

import os
import json
import logging
from datetime import datetime, time, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import random

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from .sms_outreach import SMSOutreachManager, SMS_TEMPLATES
from .models import Lead, LeadCollection
from .opt_out_manager import OptOutManager

logger = logging.getLogger(__name__)


class DayOfWeek(Enum):
    """Days of week with priority scores."""
    MONDAY = (0, 1)      # Lowest priority - people are overwhelmed
    TUESDAY = (1, 4)     # Good - mid-week focus
    WEDNESDAY = (2, 3)   # Decent - mid-week
    THURSDAY = (3, 5)    # Best - decision-making day
    FRIDAY = (4, 5)      # Best - end-of-week decisions
    SATURDAY = (5, 1)    # Low - not B2B optimal
    SUNDAY = (6, 1)      # Low - not B2B optimal

    @property
    def weekday(self) -> int:
        return self.value[0]

    @property
    def priority(self) -> int:
        return self.value[1]


@dataclass
class TimeWindow:
    """Defines a sending time window."""
    name: str
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    priority: int  # 1-5, higher is better
    description: str

    def contains(self, dt: datetime) -> bool:
        """Check if datetime falls within this window."""
        start = time(self.start_hour, self.start_minute)
        end = time(self.end_hour, self.end_minute)
        current = dt.time()
        return start <= current <= end

    def get_random_time_in_window(self, date: datetime) -> datetime:
        """Get a random time within this window on the given date."""
        start_minutes = self.start_hour * 60 + self.start_minute
        end_minutes = self.end_hour * 60 + self.end_minute
        random_minutes = random.randint(start_minutes, end_minutes)
        return date.replace(
            hour=random_minutes // 60,
            minute=random_minutes % 60,
            second=0,
            microsecond=0
        )


# Optimal time windows for B2B SMS outreach (EST)
TIME_WINDOWS = {
    "morning_peak": TimeWindow(
        name="morning_peak",
        start_hour=9, start_minute=0,
        end_hour=11, end_minute=0,
        priority=5,
        description="Peak decision-making window (9-11 AM)"
    ),
    "late_morning": TimeWindow(
        name="late_morning",
        start_hour=11, start_minute=0,
        end_hour=12, end_minute=0,
        priority=4,
        description="Pre-lunch engagement (11 AM-12 PM)"
    ),
    "afternoon": TimeWindow(
        name="afternoon",
        start_hour=14, start_minute=0,
        end_hour=16, end_minute=0,
        priority=3,
        description="Afternoon re-engagement (2-4 PM)"
    ),
    "evening": TimeWindow(
        name="evening",
        start_hour=17, start_minute=0,
        end_hour=19, end_minute=0,
        priority=2,
        description="End-of-day catch-up (5-7 PM)"
    ),
}

# TCPA/Florida compliance window
COMPLIANCE_WINDOW = TimeWindow(
    name="compliance",
    start_hour=8, start_minute=0,
    end_hour=20, end_minute=0,  # 8 PM
    priority=0,
    description="Florida Mini-TCPA compliant window (8 AM - 8 PM)"
)


@dataclass
class ScheduleConfig:
    """Configuration for the SMS scheduler."""
    # Daily limits
    daily_limit: int = 25

    # Preferred days (0=Monday, 4=Friday)
    preferred_days: List[int] = None

    # Preferred time windows
    preferred_windows: List[str] = None

    # Delay between messages (seconds)
    delay_between_messages: float = 2.0

    # Template to use (or auto-select)
    template: Optional[str] = None

    # Whether to randomize send times within window
    randomize_timing: bool = True

    # A/B test settings
    ab_test_enabled: bool = False
    ab_test_windows: List[str] = None

    def __post_init__(self):
        if self.preferred_days is None:
            # Tuesday through Friday (1-4)
            self.preferred_days = [1, 2, 3, 4]
        if self.preferred_windows is None:
            self.preferred_windows = ["morning_peak", "late_morning"]
        if self.ab_test_windows is None:
            self.ab_test_windows = ["morning_peak", "afternoon"]


@dataclass
class ScheduledSend:
    """A scheduled SMS send."""
    lead_id: str
    business_name: str
    phone: str
    template: str
    scheduled_time: str
    window_name: str
    status: str = "scheduled"
    sent_at: Optional[str] = None
    message_sid: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SMSScheduler:
    """
    Automated SMS scheduler with optimal timing.

    Respects:
    - TCPA quiet hours (8 AM - 8 PM Florida)
    - Optimal B2B engagement windows
    - Daily rate limits
    - Opt-out compliance
    """

    def __init__(self, output_dir: str = "output", config: Optional[ScheduleConfig] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = config or ScheduleConfig()
        self.sms_manager = SMSOutreachManager(output_dir=output_dir)
        self.opt_out_manager = OptOutManager(output_dir=output_dir)

        # Load/create schedule file
        self.schedule_file = self.output_dir / "sms_schedule.json"
        self.schedule: List[ScheduledSend] = []
        self._load_schedule()

    def _load_schedule(self) -> None:
        """Load existing schedule from file."""
        if self.schedule_file.exists():
            with open(self.schedule_file, 'r') as f:
                data = json.load(f)
                self.schedule = [ScheduledSend(**s) for s in data.get("scheduled", [])]

    def _save_schedule(self) -> None:
        """Save schedule to file."""
        data = {
            "scheduled": [s.to_dict() for s in self.schedule],
            "config": asdict(self.config),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.schedule_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_optimal_day(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """Check if today is an optimal day for sending."""
        dt = dt or datetime.now()
        weekday = dt.weekday()
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]

        if weekday in self.config.preferred_days:
            return True, f"{day_name} is an optimal sending day"
        else:
            return False, f"{day_name} is not optimal (prefer Tue-Fri)"

    def is_compliant_time(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """Check if current time is within TCPA compliance window."""
        dt = dt or datetime.now()

        if COMPLIANCE_WINDOW.contains(dt):
            return True, f"Within Florida compliance window (8 AM - 8 PM)"
        else:
            return False, f"Outside compliance window - cannot send before 8 AM or after 8 PM"

    def get_current_window(self, dt: Optional[datetime] = None) -> Optional[TimeWindow]:
        """Get the current time window, if any."""
        dt = dt or datetime.now()

        for window in TIME_WINDOWS.values():
            if window.contains(dt):
                return window
        return None

    def get_best_window_for_today(self) -> Optional[TimeWindow]:
        """Get the best available window for today."""
        now = datetime.now()
        current_time = now.time()

        # Find windows that haven't passed yet
        available = []
        for name in self.config.preferred_windows:
            window = TIME_WINDOWS.get(name)
            if window and time(window.end_hour, window.end_minute) > current_time:
                available.append(window)

        # Sort by priority (highest first)
        available.sort(key=lambda w: w.priority, reverse=True)

        return available[0] if available else None

    def get_eligible_leads(self, limit: int = None) -> List[Lead]:
        """Get leads eligible for outreach."""
        limit = limit or self.config.daily_limit

        # Load all leads
        collection = LeadCollection(output_dir=str(self.output_dir))
        collection.load_json()

        leads = list(collection.leads.values())

        # Filter to leads with phones
        leads = [l for l in leads if l.phone]

        # Filter out already contacted
        leads = [l for l in leads if l.id not in self.sms_manager.campaigns]

        # Filter out opted-out
        leads = [l for l in leads if not self.opt_out_manager.is_opted_out(phone=l.phone)]

        # Filter to leads with no_website pain point (our target)
        leads = [l for l in leads if "no_website" in l.pain_points]

        # Return up to limit
        return leads[:limit]

    def preview_schedule(self, window_name: Optional[str] = None) -> Dict[str, Any]:
        """Preview what would be sent without actually sending."""
        now = datetime.now()

        # Check day
        is_good_day, day_reason = self.is_optimal_day(now)

        # Check compliance
        is_compliant, compliance_reason = self.is_compliant_time(now)

        # Get window
        if window_name:
            window = TIME_WINDOWS.get(window_name)
        else:
            window = self.get_current_window(now) or self.get_best_window_for_today()

        # Get eligible leads
        eligible = self.get_eligible_leads()

        preview = {
            "timestamp": now.isoformat(),
            "day_check": {
                "is_optimal": is_good_day,
                "reason": day_reason
            },
            "compliance_check": {
                "is_compliant": is_compliant,
                "reason": compliance_reason
            },
            "window": {
                "name": window.name if window else None,
                "description": window.description if window else "No window available",
                "priority": window.priority if window else 0
            },
            "eligible_leads": len(eligible),
            "daily_limit": self.config.daily_limit,
            "would_send": min(len(eligible), self.config.daily_limit),
            "sample_leads": [
                {"business": l.business_name, "phone": l.phone[:7] + "****"}
                for l in eligible[:5]
            ],
            "can_send": is_compliant and len(eligible) > 0,
            "warnings": []
        }

        if not is_good_day:
            preview["warnings"].append(f"⚠️ {day_reason}")
        if not is_compliant:
            preview["warnings"].append(f"❌ {compliance_reason}")
        if len(eligible) == 0:
            preview["warnings"].append("❌ No eligible leads to send")

        return preview

    def run_scheduled_sends(
        self,
        window_name: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Execute scheduled SMS sends.

        Args:
            window_name: Specific window to use (or auto-detect)
            dry_run: Preview without sending
            force: Send even on non-optimal days

        Returns:
            Results dict with statistics
        """
        now = datetime.now()
        results = {
            "timestamp": now.isoformat(),
            "dry_run": dry_run,
            "window": None,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "messages": []
        }

        # Check day
        is_good_day, day_reason = self.is_optimal_day(now)
        if not is_good_day and not force:
            results["error"] = f"Not an optimal day: {day_reason}. Use --force to override."
            return results

        # Check compliance window
        is_compliant, compliance_reason = self.is_compliant_time(now)
        if not is_compliant:
            results["error"] = f"Outside compliance window: {compliance_reason}"
            return results

        # Get window
        if window_name:
            window = TIME_WINDOWS.get(window_name)
            if not window:
                results["error"] = f"Unknown window: {window_name}"
                return results
        else:
            window = self.get_current_window(now)
            if not window:
                # Check if any preferred window is still available today
                window = self.get_best_window_for_today()
                if not window:
                    results["error"] = "No sending window available. Try again tomorrow morning."
                    return results

        results["window"] = window.name

        # Get eligible leads
        leads = self.get_eligible_leads()

        if not leads:
            results["error"] = "No eligible leads to contact"
            return results

        logger.info(f"Running SMS campaign: {len(leads)} leads, window={window.name}, dry_run={dry_run}")

        # Run campaign through SMS manager
        template = self.config.template or "no_website_intro"

        campaign_results = self.sms_manager.run_campaign(
            leads=leads,
            template_name=template,
            dry_run=dry_run,
            daily_limit=self.config.daily_limit,
            delay_seconds=self.config.delay_between_messages
        )

        results["sent"] = campaign_results.get("messages_sent", 0)
        results["failed"] = len(campaign_results.get("errors", []))
        results["skipped"] = (
            campaign_results.get("skipped_no_phone", 0) +
            campaign_results.get("skipped_already_contacted", 0) +
            campaign_results.get("skipped_opted_out", 0)
        )
        results["details"] = campaign_results

        # Log results
        logger.info(f"Campaign complete: {results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        now = datetime.now()

        # Get campaign stats
        campaign_stats = self.sms_manager.get_campaign_stats()

        # Get eligible leads count
        eligible = self.get_eligible_leads()

        # Calculate daily/weekly projections
        daily_rate = self.config.daily_limit
        eligible_count = len(eligible)
        days_to_complete = eligible_count // daily_rate if daily_rate > 0 else 0

        return {
            "timestamp": now.isoformat(),
            "campaign_stats": campaign_stats,
            "eligible_leads": eligible_count,
            "daily_limit": daily_rate,
            "days_to_complete_all": days_to_complete,
            "optimal_days_this_week": sum(1 for d in range(7) if (now + timedelta(days=d)).weekday() in self.config.preferred_days),
            "current_window": self.get_current_window(now).name if self.get_current_window(now) else None,
            "is_sending_time": self.is_compliant_time(now)[0] and self.is_optimal_day(now)[0]
        }


def main():
    """CLI entry point for SMS scheduler."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="SMS Outreach Scheduler")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview scheduled sends")
    preview_parser.add_argument("--window", "-w", choices=list(TIME_WINDOWS.keys()), help="Specific window")
    preview_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute scheduled sends")
    run_parser.add_argument("--window", "-w", choices=list(TIME_WINDOWS.keys()), help="Specific window")
    run_parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    run_parser.add_argument("--force", action="store_true", help="Send even on non-optimal days")
    run_parser.add_argument("--limit", "-l", type=int, default=25, help="Daily limit")
    run_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show scheduler statistics")
    stats_parser.add_argument("--output-dir", "-o", default="output", help="Output directory")

    # Windows command
    windows_parser = subparsers.add_parser("windows", help="List available time windows")

    # Cron command (for generating crontab entries)
    cron_parser = subparsers.add_parser("cron", help="Generate crontab entries")
    cron_parser.add_argument("--path", "-p", default=".", help="Path to lead-scraper directory")

    args = parser.parse_args()

    if args.command == "windows":
        print("\n=== Available Time Windows (EST) ===\n")
        for name, window in TIME_WINDOWS.items():
            start = f"{window.start_hour:02d}:{window.start_minute:02d}"
            end = f"{window.end_hour:02d}:{window.end_minute:02d}"
            print(f"📅 {name}")
            print(f"   Time: {start} - {end}")
            print(f"   Priority: {'⭐' * window.priority}")
            print(f"   {window.description}")
            print()

        print("=== TCPA Compliance Window ===")
        print(f"   Legal sending hours: 8:00 AM - 8:00 PM (recipient timezone)")
        print(f"   Florida Mini-TCPA requires stricter 8 PM cutoff")
        print()
        return 0

    if args.command == "cron":
        path = args.path
        print("\n=== Recommended Crontab Entries ===\n")
        print("# SMS Outreach Scheduler - Optimal Times (Tue-Fri)")
        print("# Add to crontab with: crontab -e")
        print()
        print(f"# Morning peak window (9 AM EST, Tue-Fri)")
        print(f"0 9 * * 2-5 cd {path} && python -m src.sms_scheduler run --window morning_peak >> /tmp/sms_scheduler.log 2>&1")
        print()
        print(f"# Late morning window (11 AM EST, Tue-Fri) - optional second batch")
        print(f"# 0 11 * * 2-5 cd {path} && python -m src.sms_scheduler run --window late_morning >> /tmp/sms_scheduler.log 2>&1")
        print()
        print(f"# Afternoon window (2 PM EST, Thu-Fri only)")
        print(f"# 0 14 * * 4-5 cd {path} && python -m src.sms_scheduler run --window afternoon >> /tmp/sms_scheduler.log 2>&1")
        print()
        return 0

    output_dir = getattr(args, "output_dir", "output")
    config = ScheduleConfig()

    if hasattr(args, "limit") and args.limit:
        config.daily_limit = args.limit

    scheduler = SMSScheduler(output_dir=output_dir, config=config)

    if args.command == "preview":
        preview = scheduler.preview_schedule(window_name=args.window)

        print("\n=== SMS Schedule Preview ===\n")
        print(f"📅 Day Check: {'✅' if preview['day_check']['is_optimal'] else '⚠️'} {preview['day_check']['reason']}")
        print(f"⏰ Compliance: {'✅' if preview['compliance_check']['is_compliant'] else '❌'} {preview['compliance_check']['reason']}")

        if preview['window']['name']:
            print(f"🎯 Window: {preview['window']['name']} - {preview['window']['description']}")

        print(f"\n📊 Eligible Leads: {preview['eligible_leads']}")
        print(f"📤 Would Send: {preview['would_send']} (daily limit: {preview['daily_limit']})")

        if preview['sample_leads']:
            print("\n📋 Sample Leads:")
            for lead in preview['sample_leads']:
                print(f"   • {lead['business']} - {lead['phone']}")

        if preview['warnings']:
            print("\n⚠️ Warnings:")
            for warning in preview['warnings']:
                print(f"   {warning}")

        print(f"\n{'✅ Ready to send!' if preview['can_send'] else '❌ Cannot send at this time'}")
        return 0

    if args.command == "run":
        results = scheduler.run_scheduled_sends(
            window_name=args.window,
            dry_run=args.dry_run,
            force=args.force
        )

        print("\n=== SMS Campaign Results ===\n")

        if results.get("error"):
            print(f"❌ Error: {results['error']}")
            return 1

        print(f"⏰ Timestamp: {results['timestamp']}")
        print(f"🎯 Window: {results['window']}")
        print(f"{'🔍 DRY RUN' if results['dry_run'] else '📤 LIVE SEND'}")
        print()
        print(f"✅ Sent: {results['sent']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⏭️ Skipped: {results['skipped']}")

        return 0

    if args.command == "stats":
        stats = scheduler.get_stats()

        print("\n=== SMS Scheduler Statistics ===\n")
        print(f"📊 Campaign Stats:")
        print(f"   Total Messages: {stats['campaign_stats']['total_messages']}")
        for status, count in stats['campaign_stats'].get('by_status', {}).items():
            print(f"   {status}: {count}")

        print(f"\n📋 Eligible Leads: {stats['eligible_leads']}")
        print(f"📤 Daily Limit: {stats['daily_limit']}")
        print(f"📅 Days to Complete: {stats['days_to_complete_all']}")
        print(f"🗓️ Optimal Days This Week: {stats['optimal_days_this_week']}")

        if stats['current_window']:
            print(f"\n⏰ Current Window: {stats['current_window']}")

        print(f"\n{'✅ Good time to send!' if stats['is_sending_time'] else '⏳ Wait for optimal time'}")

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
