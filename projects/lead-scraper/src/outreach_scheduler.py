#!/usr/bin/env python3
"""
Outreach Scheduler - Automated daily email/SMS campaigns

Similar to social media automation, this schedules and sends outreach campaigns
at optimal times throughout the day.

Usage:
    python -m src.outreach_scheduler daily-run --business marceau-solutions
    python -m src.outreach_scheduler process --max 10
    python -m src.outreach_scheduler status
"""

import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = PROJECT_ROOT / "output"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OutreachConfig:
    """Configuration for automated outreach."""
    business_id: str
    business_name: str
    emails_per_day: int
    sms_per_day: int
    optimal_times: List[int]  # Hours of day (EST)
    optimal_days: List[int]  # Days of week (0=Mon, 6=Sun)
    target_categories: List[str]
    pain_points: List[str]
    enrich_first: bool = True


BUSINESS_CONFIGS = {
    "marceau-solutions": OutreachConfig(
        business_id="marceau-solutions",
        business_name="Marceau Solutions (AI Automation)",
        emails_per_day=20,  # Rule of 100 spread across week
        sms_per_day=10,
        optimal_times=[10, 11, 12, 13, 14],  # 10 AM - 2 PM EST (peak decision-maker availability)
        optimal_days=[1, 2, 3],  # Tue, Wed, Thu only (avoid Mon morning, Fri afternoon, weekends)
        target_categories=["gym", "restaurant", "medical"],
        pain_points=["no_website", "low_reviews", "no_google_listing"],
        enrich_first=True
    ),
    "swflorida-hvac": OutreachConfig(
        business_id="swflorida-hvac",
        business_name="SW Florida Comfort HVAC",
        emails_per_day=15,
        sms_per_day=10,
        optimal_times=[10, 11, 12, 13, 14],  # 10 AM - 2 PM EST (consistent timing)
        optimal_days=[1, 2, 3],  # Tue, Wed, Thu only
        target_categories=["restaurant", "gym", "retail"],
        pain_points=["no_website", "low_reviews"],
        enrich_first=True
    )
}


class OutreachScheduler:
    """Schedules and manages automated outreach campaigns."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load queue
        self.queue_file = self.output_dir / "outreach_queue.json"
        self.queue = self._load_queue()

        # Load history
        self.history_file = self.output_dir / "outreach_history.json"
        self.history = self._load_history()

    def _load_queue(self) -> List[Dict]:
        """Load outreach queue."""
        if self.queue_file.exists():
            with open(self.queue_file) as f:
                data = json.load(f)
                return data.get("queue", [])
        return []

    def _save_queue(self):
        """Save outreach queue."""
        with open(self.queue_file, 'w') as f:
            json.dump({
                "updated_at": datetime.now().isoformat(),
                "queue": self.queue
            }, f, indent=2)

    def _load_history(self) -> Dict:
        """Load outreach history."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return {"campaigns": [], "stats": {}}

    def _save_history(self):
        """Save outreach history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def schedule_daily_outreach(self, business_id: str, date: datetime = None):
        """
        Schedule outreach for a business for the day.

        This is similar to social media daily-run - it prepares the day's campaigns.
        """
        if date is None:
            date = datetime.now()

        config = BUSINESS_CONFIGS.get(business_id)
        if not config:
            logger.error(f"Unknown business: {business_id}")
            return

        # Only schedule for optimal days (Tue-Thu by default)
        day_of_week = date.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        if day_of_week not in config.optimal_days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            logger.info(f"Skipping {day_names[day_of_week]} {date.date()} - only schedule on Tue/Wed/Thu")
            return

        logger.info(f"Scheduling outreach for {config.business_name} on {date.date()}")

        # Distribute emails across optimal times
        emails_per_slot = config.emails_per_day // len(config.optimal_times)

        for i, hour in enumerate(config.optimal_times):
            scheduled_time = datetime.combine(date.date(), time(hour=hour))

            # Create outreach batch
            self.queue.append({
                "id": f"{business_id}_{date.strftime('%Y%m%d')}_{hour}",
                "business_id": business_id,
                "type": "email",
                "count": emails_per_slot + (1 if i == 0 and config.emails_per_day % len(config.optimal_times) else 0),
                "scheduled_time": scheduled_time.isoformat(),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "filters": {
                    "categories": config.target_categories,
                    "pain_points": config.pain_points,
                    "enrich": config.enrich_first
                }
            })

        # Add SMS batches (if configured)
        if config.sms_per_day > 0:
            sms_per_slot = config.sms_per_day // 2  # Morning + afternoon
            for i, hour in enumerate([10, 13]):  # 10 AM and 1 PM for SMS (within optimal window)
                scheduled_time = datetime.combine(date.date(), time(hour=hour))

                self.queue.append({
                    "id": f"{business_id}_sms_{date.strftime('%Y%m%d')}_{hour}",
                    "business_id": business_id,
                    "type": "sms",
                    "count": sms_per_slot,
                    "scheduled_time": scheduled_time.isoformat(),
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "filters": {
                        "categories": config.target_categories,
                        "pain_points": ["no_website"]  # SMS only for no-website
                    }
                })

        self._save_queue()
        logger.info(f"Scheduled {len([q for q in self.queue if q['business_id'] == business_id and q['status'] == 'pending'])} batches for {business_id}")

    def process_queue(self, max_batches: int = None):
        """
        Process pending outreach batches.

        This is called by cron job at each optimal time.
        """
        now = datetime.now()
        processed = 0

        # Validate current day is optimal (Tue-Thu)
        day_of_week = now.weekday()
        # Most configs use [1, 2, 3] for Tue-Thu
        if day_of_week not in [1, 2, 3]:
            logger.info(f"Skipping queue processing - today is not an optimal day (only Tue-Thu)")
            return 0

        # Find batches ready to send
        ready_batches = [
            b for b in self.queue
            if b['status'] == 'pending'
            and datetime.fromisoformat(b['scheduled_time']) <= now
        ]

        if max_batches:
            ready_batches = ready_batches[:max_batches]

        logger.info(f"Processing {len(ready_batches)} outreach batches")

        for batch in ready_batches:
            try:
                self._execute_batch(batch)
                batch['status'] = 'sent'
                batch['sent_at'] = now.isoformat()
                processed += 1
            except Exception as e:
                logger.error(f"Failed to execute batch {batch['id']}: {e}")
                batch['status'] = 'failed'
                batch['error'] = str(e)

        self._save_queue()
        logger.info(f"Processed {processed} batches")

        return processed

    def _execute_batch(self, batch: Dict):
        """Execute a single outreach batch."""
        from .models import LeadCollection
        from .scraper import LeadScraperCLI

        logger.info(f"Executing batch {batch['id']} ({batch['type']})")

        # Load leads
        scraper = LeadScraperCLI(output_dir=str(self.output_dir))

        # PHASE 1 OPTIMIZATION: Filter to high-response verticals FIRST
        leads = scraper.leads.filter_high_response_verticals()
        logger.info(f"Filtered to {len(leads)} high-response vertical leads (gyms, salons, restaurants)")

        # Apply filters
        filters = batch.get('filters', {})
        categories = filters.get('categories', [])
        pain_points = filters.get('pain_points', [])

        # Filter by category (if specified)
        if categories:
            leads = [l for l in leads if any(cat.lower() in l.category.lower() for cat in categories)]

        # Filter by pain point
        if pain_points:
            leads = [l for l in leads if any(pp in l.pain_points for pp in pain_points)]

        # Execute based on type
        if batch['type'] == 'email':
            self._send_email_batch(batch, leads)
        elif batch['type'] == 'sms':
            self._send_sms_batch(batch, leads)

    def _send_email_batch(self, batch: Dict, leads: List):
        """Send email outreach batch."""
        from .cold_outreach import ColdOutreachManager

        count = batch.get('count', 10)
        business_id = batch['business_id']

        # Filter to only leads with websites (for enrichment) or existing emails
        leads = [l for l in leads if l.website or l.email]

        if not leads:
            logger.warning(f"No leads with emails/websites for batch {batch['id']}")
            return

        manager = ColdOutreachManager(output_dir=str(self.output_dir))

        # Enrich first if needed
        enrich = batch.get('filters', {}).get('enrich', False)

        stats = manager.run_campaign(
            leads=leads[:count],
            template_name=None,  # Auto-select based on pain point
            enrich=enrich,
            dry_run=False,  # REAL sending
            daily_limit=count
        )

        # Record stats
        self.history['campaigns'].append({
            "batch_id": batch['id'],
            "business_id": business_id,
            "type": "email",
            "sent_at": datetime.now().isoformat(),
            "stats": stats
        })
        self._save_history()

        logger.info(f"Email batch sent: {stats.get('emails_sent', 0)} emails")

    def _send_sms_batch(self, batch: Dict, leads: List):
        """Send SMS outreach batch."""
        from .sms_outreach import SMSOutreachManager

        count = batch.get('count', 10)
        business_id = batch['business_id']

        # Filter to only leads with phone numbers
        leads = [l for l in leads if l.phone]

        if not leads:
            logger.warning(f"No leads with phones for batch {batch['id']}")
            return

        manager = SMSOutreachManager(output_dir=str(self.output_dir))

        stats = manager.run_campaign(
            leads=leads[:count],
            template_name=None,
            dry_run=False,  # REAL sending
            daily_limit=count
        )

        # Record stats
        self.history['campaigns'].append({
            "batch_id": batch['id'],
            "business_id": business_id,
            "type": "sms",
            "sent_at": datetime.now().isoformat(),
            "stats": stats
        })
        self._save_history()

        logger.info(f"SMS batch sent: {stats.get('messages_sent', 0)} messages")

    def get_status(self) -> Dict:
        """Get scheduler status."""
        now = datetime.now()

        pending = [b for b in self.queue if b['status'] == 'pending']
        sent_today = [
            b for b in self.queue
            if b.get('sent_at') and datetime.fromisoformat(b['sent_at']).date() == now.date()
        ]

        return {
            "total_queued": len(self.queue),
            "pending": len(pending),
            "sent_today": len(sent_today),
            "next_batch": pending[0] if pending else None,
            "businesses": list(BUSINESS_CONFIGS.keys())
        }


def main():
    parser = argparse.ArgumentParser(description="Automated Outreach Scheduler")
    parser.add_argument("command", choices=["daily-run", "process", "status", "schedule-week"])
    parser.add_argument("--business", "-b", help="Business ID (marceau-solutions, swflorida-hvac)")
    parser.add_argument("--max", type=int, help="Max batches to process")
    parser.add_argument("--output-dir", default="output", help="Output directory")

    args = parser.parse_args()

    scheduler = OutreachScheduler(output_dir=args.output_dir)

    if args.command == "daily-run":
        # Schedule today's outreach for specified business
        if not args.business:
            print("Error: --business required for daily-run")
            return 1

        scheduler.schedule_daily_outreach(args.business)

        # Also process any ready batches
        scheduler.process_queue()

        print(f"✅ Daily outreach scheduled for {args.business}")

    elif args.command == "process":
        # Process pending batches
        processed = scheduler.process_queue(max_batches=args.max)
        print(f"✅ Processed {processed} batches")

    elif args.command == "status":
        # Show status
        status = scheduler.get_status()
        print("\n=== Outreach Scheduler Status ===")
        print(f"Total queued: {status['total_queued']}")
        print(f"Pending: {status['pending']}")
        print(f"Sent today: {status['sent_today']}")

        if status['next_batch']:
            nb = status['next_batch']
            print(f"\nNext batch:")
            print(f"  Business: {nb['business_id']}")
            print(f"  Type: {nb['type']}")
            print(f"  Count: {nb['count']}")
            print(f"  Scheduled: {nb['scheduled_time']}")

    elif args.command == "schedule-week":
        # Schedule full week for business (only optimal days will be scheduled)
        if not args.business:
            print("Error: --business required for schedule-week")
            return 1

        scheduled_days = 0
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            # schedule_daily_outreach will skip non-optimal days automatically
            scheduler.schedule_daily_outreach(args.business, date=date)

            # Count if this day was actually scheduled (Tue-Thu)
            if date.weekday() in [1, 2, 3]:
                scheduled_days += 1

        print(f"✅ Week scheduled for {args.business} ({scheduled_days} optimal days)")

    return 0


if __name__ == "__main__":
    exit(main())
