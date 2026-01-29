#!/usr/bin/env python3
"""
Automation Daemon - Central scheduler for SMS, Email, and Social Media automation.

Runs continuously to process scheduled outreach at the correct times.
Checks system time and triggers SMS, email follow-ups, and social media posts.

Usage:
    python -m src.automation_daemon status
    python -m src.automation_daemon start --dry-run
    python -m src.automation_daemon start --for-real
    python -m src.automation_daemon start --loop --for-real
"""

import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import traceback

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)


def setup_logging(output_dir: Path) -> logging.Logger:
    """Set up logging to both file and console."""
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "automation.log"

    logger = logging.getLogger("automation_daemon")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


@dataclass
class DaemonConfig:
    """Configuration for the automation daemon."""
    output_dir: str = "output"
    social_media_dir: str = "../social-media-automation/output"
    business_hours_start: int = 8
    business_hours_end: int = 20
    skip_weekends: bool = True
    loop_interval_minutes: int = 15
    dry_run: bool = True
    max_sms_per_run: int = 50
    max_emails_per_run: int = 20
    max_posts_per_run: int = 10
    sms_delay_seconds: float = 2.0
    email_delay_seconds: float = 1.0
    post_delay_seconds: float = 5.0


@dataclass
class RunStats:
    """Statistics for a single daemon run."""
    run_started: str = ""
    run_ended: str = ""
    sms_due: int = 0
    sms_sent: int = 0
    sms_errors: List[str] = field(default_factory=list)
    emails_due: int = 0
    emails_sent: int = 0
    email_errors: List[str] = field(default_factory=list)
    posts_due: int = 0
    posts_sent: int = 0
    post_errors: List[str] = field(default_factory=list)
    skipped_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutomationDaemon:
    """
    Central automation daemon that processes SMS, Email, and Social Media.

    Runs on a schedule (default every 15 minutes) and processes any
    outreach that is due to be sent.
    """

    def __init__(self, config: DaemonConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logging(self.output_dir)
        self.state_file = self.output_dir / "daemon_state.json"
        self.state = self._load_state()
        self.social_media_dir = Path(__file__).parent.parent / config.social_media_dir

    def _load_state(self) -> Dict[str, Any]:
        """Load daemon state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_run": None,
            "runs_today": 0,
            "last_run_date": None,
            "total_sms_sent": 0,
            "total_emails_sent": 0,
            "total_posts_sent": 0,
            "errors_24h": []
        }

    def _save_state(self) -> None:
        """Save daemon state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def is_business_hours(self) -> Tuple[bool, str]:
        """Check if current time is within business hours."""
        now = datetime.now()

        if self.config.skip_weekends and now.weekday() >= 5:
            return False, f"Weekend (day {now.weekday()})"

        hour = now.hour
        if hour < self.config.business_hours_start:
            return False, f"Before business hours ({hour}:00 < {self.config.business_hours_start}:00)"
        if hour >= self.config.business_hours_end:
            return False, f"After business hours ({hour}:00 >= {self.config.business_hours_end}:00)"

        return True, "Within business hours"

    def process_sms(self, dry_run: bool = True) -> Dict[str, Any]:
        """Process due SMS touchpoints."""
        stats = {"due": 0, "sent": 0, "errors": []}

        try:
            from .follow_up_sequence import FollowUpSequenceManager
            from .models import LeadCollection

            manager = FollowUpSequenceManager(output_dir=str(self.output_dir))
            collection = LeadCollection(output_dir=str(self.output_dir))
            collection.load_json()

            due_touchpoints = manager.get_due_touchpoints()
            stats["due"] = len(due_touchpoints)

            if stats["due"] == 0:
                self.logger.info("No SMS touchpoints due")
                return stats

            self.logger.info(f"Found {stats['due']} SMS touchpoints due")

            result = manager.process_due_touchpoints(
                leads_collection=collection,
                dry_run=dry_run,
                limit=self.config.max_sms_per_run,
                delay_seconds=self.config.sms_delay_seconds
            )

            stats["sent"] = result.get("sent", 0)
            stats["errors"] = result.get("errors", [])

            self.logger.info(f"SMS: Sent {stats['sent']}/{stats['due']}")

        except ImportError as e:
            self.logger.warning(f"SMS module not available: {e}")
            stats["errors"].append(f"SMS module not available: {e}")
        except Exception as e:
            self.logger.error(f"SMS processing error: {str(e)}")
            self.logger.debug(traceback.format_exc())
            stats["errors"].append(f"SMS processing error: {str(e)}")

        return stats

    def process_emails(self, dry_run: bool = True) -> Dict[str, Any]:
        """Process due email follow-ups."""
        stats = {"due": 0, "sent": 0, "errors": []}

        try:
            from .email_scheduler import EmailScheduler

            scheduler = EmailScheduler(output_dir=str(self.output_dir))
            now = datetime.now()

            # Get emails due today
            due_emails = scheduler.get_due_emails()

            # Filter by scheduled time
            ready_emails = []
            for email in due_emails:
                scheduled_time = email.get("scheduled_time", "08:30")
                try:
                    hour, minute = map(int, scheduled_time.split(":"))
                    scheduled_datetime = datetime.combine(
                        date.today(),
                        datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
                    )
                    if now >= scheduled_datetime:
                        ready_emails.append(email)
                except:
                    ready_emails.append(email)

            stats["due"] = len(ready_emails)

            if stats["due"] == 0:
                self.logger.info("No emails due at this time")
                return stats

            self.logger.info(f"Found {stats['due']} emails ready to send")

            for email in ready_emails[:self.config.max_emails_per_run]:
                try:
                    result = scheduler.send_email(email, dry_run=dry_run)
                    if result["status"] in ["sent", "dry_run"]:
                        stats["sent"] += 1
                    else:
                        stats["errors"].append(f"{email.get('recipient_email')}: {result.get('error', 'Unknown')}")
                    time.sleep(self.config.email_delay_seconds)
                except Exception as e:
                    self.logger.error(f"Email error ({email.get('recipient_email')}): {str(e)}")
                    stats["errors"].append(f"Email error: {str(e)}")

            self.logger.info(f"Email: Sent {stats['sent']}/{stats['due']}")

        except ImportError as e:
            self.logger.warning(f"Email module not available: {e}")
            stats["errors"].append(f"Email module not available: {e}")
        except Exception as e:
            self.logger.error(f"Email processing error: {str(e)}")
            self.logger.debug(traceback.format_exc())
            stats["errors"].append(f"Email processing error: {str(e)}")

        return stats

    def process_social_media(self, dry_run: bool = True) -> Dict[str, Any]:
        """Process due social media posts."""
        stats = {"due": 0, "sent": 0, "errors": []}

        try:
            posts_file = self.social_media_dir / "scheduled_posts.json"
            if not posts_file.exists():
                self.logger.warning(f"Scheduled posts file not found: {posts_file}")
                return stats

            with open(posts_file, 'r') as f:
                posts = json.load(f)

            now = datetime.now()
            due_posts = []

            for post in posts:
                if post.get("status") != "scheduled":
                    continue

                scheduled_str = post.get("scheduled_time", "")
                if not scheduled_str:
                    continue

                try:
                    if "T" in scheduled_str:
                        scheduled = datetime.fromisoformat(scheduled_str.replace("Z", "+00:00"))
                    else:
                        scheduled = datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")

                    if scheduled <= now:
                        due_posts.append(post)
                except Exception as e:
                    self.logger.debug(f"Could not parse scheduled_time '{scheduled_str}': {e}")

            stats["due"] = len(due_posts)

            if stats["due"] == 0:
                self.logger.info("No social media posts due")
                return stats

            self.logger.info(f"Found {stats['due']} social media posts due")

            # Try to import X poster
            try:
                sys.path.insert(0, str(self.social_media_dir.parent / "src"))
                from x_poster import XPoster
                poster = XPoster()

                for post in due_posts[:self.config.max_posts_per_run]:
                    try:
                        if dry_run:
                            self.logger.info(f"[DRY RUN] Would post: {post['text'][:50]}...")
                            stats["sent"] += 1
                        else:
                            result = poster.post(post["text"])
                            if result.get("success"):
                                post["status"] = "posted"
                                post["posted_at"] = datetime.now().isoformat()
                                post["tweet_id"] = result.get("tweet_id", "")
                                stats["sent"] += 1
                            else:
                                stats["errors"].append(f"Post failed: {result.get('error', 'Unknown')}")
                        time.sleep(self.config.post_delay_seconds)
                    except Exception as e:
                        self.logger.error(f"Post error: {str(e)}")
                        stats["errors"].append(f"Post error: {str(e)}")

                # Save updated posts if we actually sent
                if not dry_run:
                    with open(posts_file, 'w') as f:
                        json.dump(posts, f, indent=2)

            except ImportError as e:
                self.logger.warning(f"Could not import social media poster: {e}")
                stats["errors"].append(f"Social media module not available: {e}")

            self.logger.info(f"Social Media: Sent {stats['sent']}/{stats['due']}")

        except Exception as e:
            self.logger.error(f"Social media processing error: {str(e)}")
            self.logger.debug(traceback.format_exc())
            stats["errors"].append(f"Social media processing error: {str(e)}")

        return stats

    def run_once(self, dry_run: bool = True, force: bool = False) -> RunStats:
        """Run one iteration of the daemon."""
        stats = RunStats(run_started=datetime.now().isoformat())

        self.logger.info("=" * 60)
        self.logger.info(f"Automation Daemon Run - {'DRY RUN' if dry_run else 'LIVE'}")
        self.logger.info("=" * 60)

        # Check business hours unless forced
        if not force:
            is_ok, reason = self.is_business_hours()
            if not is_ok:
                self.logger.info(f"Skipping run: {reason}")
                stats.skipped_reason = reason
                stats.run_ended = datetime.now().isoformat()
                return stats

        # Process SMS
        self.logger.info("-" * 40)
        self.logger.info("Processing SMS touchpoints...")
        sms_stats = self.process_sms(dry_run=dry_run)
        stats.sms_due = sms_stats["due"]
        stats.sms_sent = sms_stats["sent"]
        stats.sms_errors = sms_stats["errors"]

        # Process Emails
        self.logger.info("-" * 40)
        self.logger.info("Processing emails...")
        email_stats = self.process_emails(dry_run=dry_run)
        stats.emails_due = email_stats["due"]
        stats.emails_sent = email_stats["sent"]
        stats.email_errors = email_stats["errors"]

        # Process Social Media
        self.logger.info("-" * 40)
        self.logger.info("Processing social media posts...")
        social_stats = self.process_social_media(dry_run=dry_run)
        stats.posts_due = social_stats["due"]
        stats.posts_sent = social_stats["sent"]
        stats.post_errors = social_stats["errors"]

        stats.run_ended = datetime.now().isoformat()

        # Update state
        today_str = date.today().isoformat()
        if self.state.get("last_run_date") != today_str:
            self.state["runs_today"] = 0
            self.state["last_run_date"] = today_str

        self.state["last_run"] = stats.run_started
        self.state["runs_today"] += 1

        if not dry_run:
            self.state["total_sms_sent"] += stats.sms_sent
            self.state["total_emails_sent"] += stats.emails_sent
            self.state["total_posts_sent"] += stats.posts_sent

        # Track errors
        all_errors = stats.sms_errors + stats.email_errors + stats.post_errors
        if all_errors:
            self.state["errors_24h"].extend([
                {"time": datetime.now().isoformat(), "error": e}
                for e in all_errors
            ])
            # Keep only last 24 hours of errors
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            self.state["errors_24h"] = [
                e for e in self.state["errors_24h"]
                if e["time"] > cutoff
            ]

        self._save_state()

        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("Run Summary:")
        self.logger.info(f"  SMS: {stats.sms_sent}/{stats.sms_due} sent")
        self.logger.info(f"  Email: {stats.emails_sent}/{stats.emails_due} sent")
        self.logger.info(f"  Social: {stats.posts_sent}/{stats.posts_due} sent")
        if all_errors:
            self.logger.warning(f"  Errors: {len(all_errors)}")
        self.logger.info("=" * 60)

        return stats

    def run_loop(self, dry_run: bool = True) -> None:
        """Run the daemon continuously."""
        self.logger.info(f"Starting automation daemon loop (interval: {self.config.loop_interval_minutes} min)")

        try:
            while True:
                self.run_once(dry_run=dry_run)
                next_run = datetime.now() + timedelta(minutes=self.config.loop_interval_minutes)
                self.logger.info(f"Next run at: {next_run.strftime('%H:%M:%S')}")
                time.sleep(self.config.loop_interval_minutes * 60)
        except KeyboardInterrupt:
            self.logger.info("Daemon stopped by user")

    def get_status(self) -> Dict[str, Any]:
        """Get current daemon status."""
        return {
            "daemon": {
                "last_run": self.state.get("last_run"),
                "runs_today": self.state.get("runs_today", 0),
                "total_sent": {
                    "sms": self.state.get("total_sms_sent", 0),
                    "emails": self.state.get("total_emails_sent", 0),
                    "posts": self.state.get("total_posts_sent", 0)
                },
                "errors_24h": len(self.state.get("errors_24h", []))
            },
            "pending": {
                "sms": self._get_pending_sms(),
                "emails": self._get_pending_emails(),
                "posts": self._get_pending_posts()
            },
            "business_hours": self.is_business_hours()
        }

    def _get_pending_sms(self) -> Dict[str, Any]:
        """Get pending SMS count."""
        try:
            sequences_file = self.output_dir / "follow_up_sequences.json"
            if not sequences_file.exists():
                return {"error": "No sequences file"}

            with open(sequences_file, 'r') as f:
                data = json.load(f)

            now = datetime.now()
            due_count = 0
            next_scheduled = None
            total_pending = 0

            for seq in data.get("sequences", []):
                for tp in seq.get("touchpoints", []):
                    if tp.get("status") == "pending":
                        total_pending += 1
                        scheduled = tp.get("scheduled_at", "")
                        if scheduled:
                            try:
                                sched_dt = datetime.fromisoformat(scheduled)
                                if sched_dt <= now:
                                    due_count += 1
                                elif next_scheduled is None or scheduled < next_scheduled:
                                    next_scheduled = scheduled
                            except:
                                pass

            return {
                "due_now": due_count,
                "total_pending": total_pending,
                "next_scheduled": next_scheduled
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_pending_emails(self) -> Dict[str, Any]:
        """Get pending email count."""
        try:
            from .email_scheduler import EmailScheduler
            scheduler = EmailScheduler(output_dir=str(self.output_dir))
            due = scheduler.get_due_emails()
            scheduled = [e for e in scheduler.emails if e.get("status") == "scheduled"]

            next_scheduled = None
            for email in scheduled:
                sched_date = email.get("scheduled_date")
                if next_scheduled is None or sched_date < next_scheduled:
                    next_scheduled = sched_date

            return {
                "due_now": len(due),
                "total_scheduled": len(scheduled),
                "next_scheduled": next_scheduled
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_pending_posts(self) -> Dict[str, Any]:
        """Get pending social media posts count."""
        try:
            posts_file = self.social_media_dir / "scheduled_posts.json"
            if not posts_file.exists():
                return {"error": "Scheduled posts file not found"}

            with open(posts_file, 'r') as f:
                posts = json.load(f)

            now = datetime.now()
            scheduled = [p for p in posts if p.get("status") == "scheduled"]
            due_now = 0
            next_scheduled = None

            for post in scheduled:
                scheduled_str = post.get("scheduled_time", "")
                try:
                    if "T" in scheduled_str:
                        scheduled_dt = datetime.fromisoformat(scheduled_str.replace("Z", "+00:00"))
                    else:
                        scheduled_dt = datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")

                    if scheduled_dt <= now:
                        due_now += 1
                    elif next_scheduled is None or scheduled_str < next_scheduled:
                        next_scheduled = scheduled_str
                except:
                    pass

            return {
                "due_now": due_now,
                "total_scheduled": len(scheduled),
                "next_scheduled": next_scheduled
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Automation Daemon")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the daemon")
    start_parser.add_argument("--dry-run", action="store_true", default=True)
    start_parser.add_argument("--for-real", action="store_true")
    start_parser.add_argument("--loop", action="store_true", help="Run continuously")
    start_parser.add_argument("--force", action="store_true", help="Ignore business hours")
    start_parser.add_argument("--interval", type=int, default=15, help="Loop interval in minutes")
    start_parser.add_argument("--output-dir", "-o", default="output")

    # Run-once command
    run_parser = subparsers.add_parser("run-once", help="Run one iteration")
    run_parser.add_argument("--dry-run", action="store_true", default=True)
    run_parser.add_argument("--for-real", action="store_true")
    run_parser.add_argument("--force", action="store_true")
    run_parser.add_argument("--output-dir", "-o", default="output")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show daemon status")
    status_parser.add_argument("--output-dir", "-o", default="output")
    status_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command in ["start", "run-once"]:
        config = DaemonConfig(
            output_dir=args.output_dir,
            loop_interval_minutes=getattr(args, 'interval', 15)
        )
        daemon = AutomationDaemon(config)
        dry_run = not args.for_real

        if args.command == "start" and getattr(args, 'loop', False):
            daemon.run_loop(dry_run=dry_run)
        else:
            stats = daemon.run_once(dry_run=dry_run, force=args.force)
            print("\n" + "=" * 50)
            print("AUTOMATION DAEMON RUN COMPLETE")
            print("=" * 50)
            print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
            print(f"Started: {stats.run_started}")
            print(f"Ended: {stats.run_ended}")
            if stats.skipped_reason:
                print(f"Skipped: {stats.skipped_reason}")
            else:
                print(f"\nSMS:    {stats.sms_sent}/{stats.sms_due} sent")
                print(f"Email:  {stats.emails_sent}/{stats.emails_due} sent")
                print(f"Social: {stats.posts_sent}/{stats.posts_due} sent")

    elif args.command == "status":
        config = DaemonConfig(output_dir=args.output_dir)
        daemon = AutomationDaemon(config)
        status = daemon.get_status()

        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("\n" + "=" * 50)
            print("AUTOMATION DAEMON STATUS")
            print("=" * 50)
            print(f"\nLast Run: {status['daemon']['last_run'] or 'Never'}")
            print(f"Runs Today: {status['daemon']['runs_today']}")
            print(f"Errors (24h): {status['daemon']['errors_24h']}")

            is_ok, reason = status['business_hours']
            print(f"\nBusiness Hours: {'Yes' if is_ok else 'No'} ({reason})")

            print("\n--- Pending Items ---")
            sms = status['pending']['sms']
            if 'error' in sms:
                print(f"SMS: Error - {sms['error']}")
            else:
                print(f"SMS: {sms['due_now']} due now, {sms.get('total_pending', 'N/A')} pending")

            emails = status['pending']['emails']
            if 'error' in emails:
                print(f"Email: Error - {emails['error']}")
            else:
                print(f"Email: {emails['due_now']} due now, {emails['total_scheduled']} scheduled")

            posts = status['pending']['posts']
            if 'error' in posts:
                print(f"Social: Error - {posts['error']}")
            else:
                print(f"Social: {posts['due_now']} due now, {posts['total_scheduled']} scheduled")

            print("\n--- Totals Sent ---")
            totals = status['daemon']['total_sent']
            print(f"SMS: {totals['sms']}, Email: {totals['emails']}, Social: {totals['posts']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
