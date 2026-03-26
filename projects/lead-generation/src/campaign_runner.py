#!/usr/bin/env python3
"""
Autonomous Campaign Runner with Safeguards

This module runs parallel campaigns (SMS outreach + content marketing) with:
1. Token/cost limits to prevent runaway spending
2. Rate limiting to avoid API throttling
3. Checkpoint saving to prevent data loss
4. Human-in-the-loop triggers for critical decisions
5. Automatic pause on errors or anomalies

Usage:
    # Dry run both campaigns (preview only)
    python -m src.campaign_runner --dry-run

    # Run Campaign 1 only (SMS to gyms)
    python -m src.campaign_runner --campaign 1 --for-real

    # Run both campaigns
    python -m src.campaign_runner --for-real

    # Check status
    python -m src.campaign_runner --status
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Safeguard Configuration
# =============================================================================

@dataclass
class SafeguardConfig:
    """Limits and safeguards to prevent runaway operations."""

    # Cost limits
    max_sms_per_day: int = 100          # Hormozi Rule of 100
    max_sms_cost_per_day: float = 1.00  # ~$0.0079 per SMS = 126 max
    max_total_cost_per_day: float = 5.00

    # Rate limits
    sms_delay_seconds: float = 2.0      # Between each SMS
    api_calls_per_minute: int = 30      # General API rate limit

    # Error thresholds
    max_consecutive_errors: int = 5     # Pause after N errors in a row
    max_error_rate_percent: float = 20.0  # Pause if >20% of attempts fail

    # Human-in-the-loop triggers
    require_approval_above_sms: int = 50   # Ask before sending >50 SMS
    require_approval_above_cost: float = 2.00  # Ask before spending >$2

    # Checkpoint frequency
    checkpoint_every_n_operations: int = 10

    # Session limits (prevent infinite loops)
    max_operations_per_session: int = 200
    max_runtime_minutes: int = 30


class CampaignStatus(Enum):
    """Campaign execution status."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class CampaignState:
    """Persistent state for campaign execution."""
    campaign_id: str
    status: str = "not_started"

    # Progress tracking
    total_targets: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0

    # Cost tracking
    total_cost: float = 0.0
    sms_sent_today: int = 0

    # Error tracking
    consecutive_errors: int = 0
    errors: List[str] = None

    # Timestamps
    started_at: str = ""
    last_checkpoint: str = ""
    completed_at: str = ""

    # Human approval
    pending_approval: str = ""
    approval_reason: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


# =============================================================================
# Campaign Runner
# =============================================================================

class AutonomousCampaignRunner:
    """
    Runs campaigns autonomously with built-in safeguards.

    Safeguards:
    - Cost limits per day
    - Rate limiting between operations
    - Automatic pause on errors
    - Checkpoint saving for recovery
    - Human approval for large operations
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = SafeguardConfig()
        self.state_file = self.output_dir / "campaign_state.json"
        self.states: Dict[str, CampaignState] = {}

        # Session tracking
        self.session_start = datetime.now()
        self.operations_this_session = 0

        # Load existing state
        self._load_state()

    def _load_state(self) -> None:
        """Load campaign state from file."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                for campaign_id, state_dict in data.get("campaigns", {}).items():
                    self.states[campaign_id] = CampaignState(**state_dict)

    def _save_state(self) -> None:
        """Save campaign state to file (checkpoint)."""
        data = {
            "campaigns": {k: asdict(v) for k, v in self.states.items()},
            "last_saved": datetime.now().isoformat(),
            "config": asdict(self.config)
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Checkpoint saved to {self.state_file}")

    def _check_safeguards(self, campaign_id: str) -> tuple[bool, str]:
        """
        Check all safeguards before proceeding.

        Returns:
            (can_proceed, reason_if_not)
        """
        state = self.states.get(campaign_id)
        if not state:
            return True, ""

        # Check session limits
        runtime = (datetime.now() - self.session_start).total_seconds() / 60
        if runtime > self.config.max_runtime_minutes:
            return False, f"Session runtime exceeded ({runtime:.1f} > {self.config.max_runtime_minutes} minutes)"

        if self.operations_this_session >= self.config.max_operations_per_session:
            return False, f"Max operations reached ({self.operations_this_session})"

        # Check cost limits
        if state.total_cost >= self.config.max_total_cost_per_day:
            return False, f"Daily cost limit reached (${state.total_cost:.2f})"

        if state.sms_sent_today >= self.config.max_sms_per_day:
            return False, f"Daily SMS limit reached ({state.sms_sent_today})"

        # Check error rate
        if state.consecutive_errors >= self.config.max_consecutive_errors:
            return False, f"Too many consecutive errors ({state.consecutive_errors})"

        total_attempts = state.successful + state.failed
        if total_attempts > 10:
            error_rate = (state.failed / total_attempts) * 100
            if error_rate > self.config.max_error_rate_percent:
                return False, f"Error rate too high ({error_rate:.1f}%)"

        # Check pending approval
        if state.pending_approval:
            return False, f"Awaiting human approval: {state.approval_reason}"

        return True, ""

    def _request_approval(self, campaign_id: str, reason: str) -> None:
        """Request human approval before proceeding."""
        state = self.states[campaign_id]
        state.status = CampaignStatus.AWAITING_APPROVAL.value
        state.pending_approval = "required"
        state.approval_reason = reason
        self._save_state()
        logger.warning(f"HUMAN APPROVAL REQUIRED: {reason}")

    def approve(self, campaign_id: str) -> None:
        """Human approves pending operation."""
        if campaign_id in self.states:
            state = self.states[campaign_id]
            state.pending_approval = ""
            state.approval_reason = ""
            state.status = CampaignStatus.RUNNING.value
            self._save_state()
            logger.info(f"Campaign {campaign_id} approved")

    # =========================================================================
    # Campaign 1: SMS to Gyms
    # =========================================================================

    def run_campaign_1_sms(self, dry_run: bool = True, limit: int = 100) -> Dict[str, Any]:
        """
        Campaign 1: Send SMS to gym owners without websites.

        Safeguards applied:
        - Rate limiting between SMS
        - Cost tracking
        - Checkpoint every 10 SMS
        - Auto-pause on errors
        """
        campaign_id = "campaign_1_website_sms"

        # Initialize or resume state
        if campaign_id not in self.states:
            self.states[campaign_id] = CampaignState(campaign_id=campaign_id)

        state = self.states[campaign_id]
        state.status = CampaignStatus.RUNNING.value

        # Check if approval needed for large campaign
        if not dry_run and limit > self.config.require_approval_above_sms:
            if not state.pending_approval == "approved":
                self._request_approval(
                    campaign_id,
                    f"Sending {limit} SMS messages (>${limit * 0.0079:.2f} estimated)"
                )
                return {"status": "awaiting_approval", "reason": state.approval_reason}

        # Check safeguards
        can_proceed, reason = self._check_safeguards(campaign_id)
        if not can_proceed:
            state.status = CampaignStatus.PAUSED.value
            self._save_state()
            return {"status": "paused", "reason": reason}

        # Import SMS manager
        from .sms_outreach import SMSOutreachManager, SMS_TEMPLATES
        from .models import LeadCollection

        # Load leads
        leads_collection = LeadCollection(str(self.output_dir))
        leads_collection.load_json()

        # Filter leads with no_website pain point and phone
        leads = [
            l for l in leads_collection.leads.values()
            if l.phone and "no_website" in l.pain_points
        ]

        state.total_targets = min(len(leads), limit)

        # Calculate how many more we can send
        remaining = limit - state.processed
        if remaining <= 0:
            state.status = CampaignStatus.COMPLETED.value
            self._save_state()
            return {"status": "completed", "state": asdict(state)}

        logger.info(f"Campaign 1: {state.processed}/{state.total_targets} processed, {remaining} remaining")

        # Initialize SMS manager
        sms_manager = SMSOutreachManager(output_dir=str(self.output_dir))

        # Process leads with safeguards
        for i, lead in enumerate(leads[state.processed:state.processed + remaining]):
            # Check safeguards before each operation
            can_proceed, reason = self._check_safeguards(campaign_id)
            if not can_proceed:
                state.status = CampaignStatus.PAUSED.value
                self._save_state()
                logger.warning(f"Campaign paused: {reason}")
                break

            try:
                # Select template
                template_name = "no_website_intro"
                template = SMS_TEMPLATES[template_name]

                # Personalize message
                message = template["body"].replace("$business_name", lead.business_name)

                if dry_run:
                    logger.info(f"[DRY RUN] Would send to {lead.phone}: {message[:50]}...")
                    state.successful += 1
                else:
                    # Send SMS
                    result = sms_manager.send_sms(lead.phone, message)
                    if result.get("success"):
                        state.successful += 1
                        state.sms_sent_today += 1
                        state.total_cost += 0.0079  # Approximate cost per SMS
                        state.consecutive_errors = 0
                    else:
                        state.failed += 1
                        state.consecutive_errors += 1
                        state.errors.append(f"{lead.business_name}: {result.get('error', 'Unknown')}")

                state.processed += 1
                self.operations_this_session += 1

                # Checkpoint every N operations
                if state.processed % self.config.checkpoint_every_n_operations == 0:
                    state.last_checkpoint = datetime.now().isoformat()
                    self._save_state()

                # Rate limiting
                time.sleep(self.config.sms_delay_seconds)

            except Exception as e:
                state.failed += 1
                state.consecutive_errors += 1
                state.errors.append(f"{lead.business_name}: {str(e)}")
                logger.error(f"Error processing {lead.business_name}: {e}")

        # Final checkpoint
        if state.processed >= state.total_targets:
            state.status = CampaignStatus.COMPLETED.value
            state.completed_at = datetime.now().isoformat()

        self._save_state()

        return {
            "status": state.status,
            "processed": state.processed,
            "successful": state.successful,
            "failed": state.failed,
            "cost": state.total_cost,
            "dry_run": dry_run
        }

    # =========================================================================
    # Campaign 2: Fitness Influencer Landing Page
    # =========================================================================

    def run_campaign_2_landing_page(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Campaign 2: Deploy Fitness Influencer landing page.

        This is a one-time setup operation:
        1. Check if Formspree form exists
        2. Update landing page with form ID
        3. Provide deployment instructions
        """
        campaign_id = "campaign_2_fitness_landing"

        if campaign_id not in self.states:
            self.states[campaign_id] = CampaignState(campaign_id=campaign_id)

        state = self.states[campaign_id]
        state.status = CampaignStatus.RUNNING.value

        # Check landing page exists
        landing_page = Path(__file__).parent.parent.parent / "fitness-influencer" / "landing-page" / "index.html"

        if not landing_page.exists():
            state.status = CampaignStatus.ERROR.value
            state.errors.append("Landing page not found")
            self._save_state()
            return {"status": "error", "reason": "Landing page not found"}

        # Check if Formspree ID is configured
        formspree_id = os.getenv("FORMSPREE_FORM_ID", "")

        result = {
            "landing_page_exists": True,
            "landing_page_path": str(landing_page),
            "formspree_configured": bool(formspree_id),
            "deployment_options": [
                "GitHub Pages (free) - git push to gh-pages branch",
                "Netlify (free) - drag and drop or CLI deploy",
                "Vercel (free) - vercel deploy command"
            ]
        }

        if not formspree_id:
            result["action_required"] = "Set FORMSPREE_FORM_ID in .env (get from formspree.io)"
            state.status = CampaignStatus.AWAITING_APPROVAL.value
            state.pending_approval = "formspree_setup"
            state.approval_reason = "Need Formspree form ID to capture emails"
        else:
            result["formspree_id"] = formspree_id
            state.status = CampaignStatus.COMPLETED.value
            state.successful = 1

        self._save_state()
        return result

    # =========================================================================
    # Status & Control
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get status of all campaigns."""
        return {
            "campaigns": {k: asdict(v) for k, v in self.states.items()},
            "session_runtime_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "operations_this_session": self.operations_this_session,
            "safeguards": asdict(self.config)
        }

    def pause_campaign(self, campaign_id: str) -> None:
        """Manually pause a campaign."""
        if campaign_id in self.states:
            self.states[campaign_id].status = CampaignStatus.PAUSED.value
            self._save_state()

    def resume_campaign(self, campaign_id: str) -> None:
        """Resume a paused campaign."""
        if campaign_id in self.states:
            state = self.states[campaign_id]
            if state.status == CampaignStatus.PAUSED.value:
                state.status = CampaignStatus.RUNNING.value
                state.consecutive_errors = 0  # Reset error counter
                self._save_state()

    def reset_campaign(self, campaign_id: str) -> None:
        """Reset a campaign (use with caution)."""
        if campaign_id in self.states:
            del self.states[campaign_id]
            self._save_state()
            logger.info(f"Campaign {campaign_id} reset")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Campaign Runner")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    parser.add_argument("--for-real", action="store_true", help="Actually execute campaigns")
    parser.add_argument("--campaign", type=int, choices=[1, 2], help="Run specific campaign only")
    parser.add_argument("--limit", type=int, default=100, help="SMS limit for campaign 1")
    parser.add_argument("--status", action="store_true", help="Show campaign status")
    parser.add_argument("--approve", type=str, help="Approve pending campaign")
    parser.add_argument("--pause", type=str, help="Pause campaign")
    parser.add_argument("--resume", type=str, help="Resume campaign")
    parser.add_argument("--reset", type=str, help="Reset campaign (caution!)")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")

    args = parser.parse_args()

    runner = AutonomousCampaignRunner(output_dir=args.output_dir)

    if args.status:
        status = runner.get_status()
        print(json.dumps(status, indent=2))
        return 0

    if args.approve:
        runner.approve(args.approve)
        print(f"Approved: {args.approve}")
        return 0

    if args.pause:
        runner.pause_campaign(args.pause)
        print(f"Paused: {args.pause}")
        return 0

    if args.resume:
        runner.resume_campaign(args.resume)
        print(f"Resumed: {args.resume}")
        return 0

    if args.reset:
        runner.reset_campaign(args.reset)
        print(f"Reset: {args.reset}")
        return 0

    dry_run = not args.for_real

    print(f"\n{'='*60}")
    print(f"AUTONOMOUS CAMPAIGN RUNNER")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print(f"{'='*60}\n")

    # Run campaigns
    if args.campaign == 1 or args.campaign is None:
        print("\n--- Campaign 1: SMS to Gym Owners ---")
        result = runner.run_campaign_1_sms(dry_run=dry_run, limit=args.limit)
        print(json.dumps(result, indent=2))

    if args.campaign == 2 or args.campaign is None:
        print("\n--- Campaign 2: Fitness Landing Page ---")
        result = runner.run_campaign_2_landing_page(dry_run=dry_run)
        print(json.dumps(result, indent=2))

    print("\n--- Final Status ---")
    print(json.dumps(runner.get_status(), indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
