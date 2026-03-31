#!/usr/bin/env python3
"""
Autonomous Sales Agent

AI-powered agent that autonomously manages the sales pipeline by:
1. Analyzing lead quality and assigning appropriate actions
2. Optimizing outreach timing and messaging based on A/B tests
3. Automatically progressing deals through stages
4. Learning from successful patterns to improve conversion rates
5. Managing follow-up sequences intelligently

The agent operates in multiple modes:
- REACTIVE: Responds to events (new leads, responses, stage changes)
- PROACTIVE: Initiates actions (follow-ups, re-engagement)
- OPTIMIZATION: Analyzes performance and adjusts strategies
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .models import (
    get_db, update_deal, get_deal, get_all_deals, log_outreach,
    get_outreach_log, get_ab_test_summary, get_deal_ab_assignments
)
from .ab_testing import get_personalized_content, ABTestingEngine


@dataclass
class LeadAnalysis:
    """Analysis result for a lead."""
    deal_id: int
    confidence_score: float  # 0-1
    recommended_action: str
    action_reason: str
    urgency_level: str  # 'high', 'medium', 'low'
    next_action_date: Optional[datetime]
    personalized_content: Optional[Dict[str, Any]] = None


@dataclass
class PipelineDecision:
    """Decision made by the autonomous agent."""
    deal_id: int
    action_type: str  # 'advance_stage', 'schedule_followup', 'send_email', 'schedule_call', etc.
    action_details: Dict[str, Any]
    confidence: float
    reasoning: str
    expected_impact: str


class AutonomousSalesAgent:
    """
    AI-powered autonomous sales agent that learns and optimizes the sales process.

    Features:
    - Lead scoring and prioritization
    - Intelligent follow-up timing
    - A/B test result integration
    - Pattern recognition for successful sequences
    - Automated deal progression
    """

    def __init__(self):
        self.db_conn = None
        self.ab_engine = ABTestingEngine()

    def _get_conn(self):
        """Get database connection."""
        if not self.db_conn:
            self.db_conn = get_db()
        return self.db_conn

    def analyze_lead(self, deal_id: int) -> LeadAnalysis:
        """
        Perform comprehensive analysis of a lead to determine optimal next actions.

        Considers:
        - Lead score and tier
        - Current stage and time in stage
        - Previous outreach history
        - A/B test assignments and performance
        - Industry and company characteristics
        """
        conn = self._get_conn()
        deal = get_deal(conn, deal_id)

        if not deal:
            return LeadAnalysis(
                deal_id=deal_id,
                confidence_score=0.0,
                recommended_action="invalid_deal",
                action_reason="Deal not found",
                urgency_level="low",
                next_action_date=None
            )

        deal_dict = dict(deal)

        # Base analysis
        tier = deal_dict.get("tier", 0)
        stage = deal_dict.get("stage", "Intake")
        lead_score = deal_dict.get("lead_score", 0)
        created_at = datetime.fromisoformat(deal_dict["created_at"])
        days_old = (datetime.now() - created_at).days

        # Get outreach history
        outreach = get_outreach_log(conn, deal_id)
        last_outreach = max(outreach, key=lambda x: x["created_at"]) if outreach else None
        days_since_last_contact = (
            (datetime.now() - datetime.fromisoformat(last_outreach["created_at"])).days
            if last_outreach else days_old
        )

        # Analyze A/B test performance for this lead
        ab_assignments = get_deal_ab_assignments(conn, deal_id)
        personalized_content = None
        if ab_assignments:
            # Get personalized content based on test assignments
            for assignment in ab_assignments:
                content = get_personalized_content(deal_id, assignment["test_type"])
                if content and content.get("variant_name") != "default":
                    personalized_content = content
                    break

        # Decision logic based on stage and characteristics
        confidence_score = 0.0
        recommended_action = "monitor"
        action_reason = "Standard monitoring"
        urgency_level = "low"
        next_action_date = None

        # Intake stage logic
        if stage == "Intake":
            if tier >= 1 and days_since_last_contact >= 1:
                # High-value lead ready for initial outreach
                recommended_action = "send_initial_email"
                action_reason = f"Tier {tier} lead ready for personalized outreach"
                urgency_level = "high" if tier == 1 else "medium"
                confidence_score = 0.85
                next_action_date = datetime.now() + timedelta(hours=2)  # Send within 2 hours

            elif days_old >= 7:
                # Stale lead - needs re-engagement
                recommended_action = "send_nurture_email"
                action_reason = f"Lead inactive for {days_old} days, needs re-engagement"
                urgency_level = "medium"
                confidence_score = 0.7
                next_action_date = datetime.now() + timedelta(days=1)

        # Qualified stage logic
        elif stage == "Qualified":
            if days_since_last_contact >= 3:
                recommended_action = "schedule_followup_call"
                action_reason = "Qualified lead needs meeting scheduling"
                urgency_level = "high"
                confidence_score = 0.9
                next_action_date = datetime.now() + timedelta(hours=4)

        # Meeting Booked stage logic
        elif stage == "Meeting Booked":
            meeting_date = deal_dict.get("next_action_date")
            if meeting_date:
                meeting_dt = datetime.fromisoformat(meeting_date)
                days_until_meeting = (meeting_dt - datetime.now()).days

                if days_until_meeting <= 1:
                    recommended_action = "send_meeting_reminder"
                    action_reason = f"Meeting in {days_until_meeting} days - send reminder"
                    urgency_level = "high"
                    confidence_score = 0.95
                    next_action_date = datetime.now() + timedelta(hours=24)

        # Proposal Sent stage logic
        elif stage == "Proposal Sent":
            if days_since_last_contact >= 5:
                recommended_action = "send_followup_email"
                action_reason = "Proposal sent, needs follow-up"
                urgency_level = "medium"
                confidence_score = 0.8
                next_action_date = datetime.now() + timedelta(days=2)

        # Low-performing leads
        if lead_score < 30 and days_old > 14:
            recommended_action = "deprioritize"
            action_reason = f"Low-score lead ({lead_score}) with no engagement"
            urgency_level = "low"
            confidence_score = 0.6

        return LeadAnalysis(
            deal_id=deal_id,
            confidence_score=confidence_score,
            recommended_action=recommended_action,
            action_reason=action_reason,
            urgency_level=urgency_level,
            next_action_date=next_action_date,
            personalized_content=personalized_content
        )

    def make_pipeline_decisions(self, deal_ids: Optional[List[int]] = None) -> List[PipelineDecision]:
        """
        Analyze multiple deals and generate autonomous decisions.

        Args:
            deal_ids: Specific deals to analyze, or None for all active deals

        Returns:
            List of decisions to execute
        """
        conn = self._get_conn()

        if deal_ids is None:
            # Get all active deals
            deals = get_all_deals(conn)
            deal_ids = [d["id"] for d in deals if d["stage"] not in ["Closed Won", "Closed Lost"]]

        decisions = []

        for deal_id in deal_ids:
            analysis = self.analyze_lead(deal_id)

            if analysis.confidence_score < 0.5:
                continue  # Not confident enough to act

            # Convert analysis to decision
            decision = self._analysis_to_decision(analysis)
            if decision:
                decisions.append(decision)

        conn.close()
        return decisions

    def _analysis_to_decision(self, analysis: LeadAnalysis) -> Optional[PipelineDecision]:
        """Convert lead analysis to executable decision."""

        action_details = {}

        if analysis.recommended_action == "send_initial_email":
            # Get personalized email subject from A/B tests
            email_content = analysis.personalized_content or {}
            subject = email_content.get("content", {}).get("description", "Transform Your Business with AI Automation")

            action_details = {
                "channel": "email",
                "subject": subject,
                "template": "initial_outreach",
                "personalized": bool(analysis.personalized_content)
            }

        elif analysis.recommended_action == "send_nurture_email":
            action_details = {
                "channel": "email",
                "subject": "Following up on your AI automation inquiry",
                "template": "nurture_followup"
            }

        elif analysis.recommended_action == "schedule_followup_call":
            action_details = {
                "channel": "call",
                "purpose": "meeting_scheduling",
                "script_type": "qualification_to_meeting"
            }

        elif analysis.recommended_action == "send_meeting_reminder":
            action_details = {
                "channel": "email",
                "subject": "Reminder: Our meeting tomorrow",
                "template": "meeting_reminder"
            }

        elif analysis.recommended_action == "send_followup_email":
            action_details = {
                "channel": "email",
                "subject": "Following up on our proposal",
                "template": "proposal_followup"
            }

        elif analysis.recommended_action == "deprioritize":
            action_details = {
                "action": "reduce_outreach_frequency",
                "new_tier": 3
            }

        if action_details:
            return PipelineDecision(
                deal_id=analysis.deal_id,
                action_type=analysis.recommended_action,
                action_details=action_details,
                confidence=analysis.confidence_score,
                reasoning=analysis.action_reason,
                expected_impact=f"Expected {analysis.urgency_level} impact on conversion velocity"
            )

        return None

    def execute_decisions(self, decisions: List[PipelineDecision], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute a list of autonomous decisions.

        Args:
            decisions: List of decisions to execute
            dry_run: If True, just log what would be done without executing

        Returns:
            Execution results
        """
        results = {
            "executed": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        conn = self._get_conn()

        for decision in decisions:
            try:
                if dry_run:
                    results["details"].append({
                        "deal_id": decision.deal_id,
                        "action": decision.action_type,
                        "status": "would_execute",
                        "reasoning": decision.reasoning
                    })
                    results["skipped"] += 1
                    continue

                # Execute the decision
                success = self._execute_single_decision(conn, decision)

                if success:
                    results["executed"] += 1
                    results["details"].append({
                        "deal_id": decision.deal_id,
                        "action": decision.action_type,
                        "status": "executed",
                        "reasoning": decision.reasoning
                    })
                else:
                    results["errors"] += 1
                    results["details"].append({
                        "deal_id": decision.deal_id,
                        "action": decision.action_type,
                        "status": "error",
                        "reasoning": "Execution failed"
                    })

            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "deal_id": decision.deal_id,
                    "action": decision.action_type,
                    "status": "error",
                    "reasoning": str(e)
                })

        conn.close()
        return results

    def _execute_single_decision(self, conn, decision: PipelineDecision) -> bool:
        """Execute a single decision."""
        deal = get_deal(conn, decision.deal_id)
        if not deal:
            return False

        action_type = decision.action_type
        details = decision.action_details

        if action_type.startswith("send_") and details.get("channel") == "email":
            # Log email outreach
            log_outreach(
                conn=conn,
                deal_id=decision.deal_id,
                company=dict(deal)["company"],
                contact=dict(deal).get("contact_name") or "",
                channel="Email",
                message=f"Subject: {details.get('subject', 'Automated outreach')}",
                response="",
                follow_up_date=None
            )

            # In a real implementation, this would trigger actual email sending
            # For now, just log the intent
            print(f"Would send email to deal {decision.deal_id}: {details.get('subject')}")

        elif action_type == "schedule_followup_call":
            # Update next action
            update_deal(conn, decision.deal_id,
                       next_action=f"Autonomous: {details.get('purpose', 'follow-up call')}",
                       next_action_date=datetime.now().isoformat())

        elif action_type == "deprioritize":
            # Move to lower tier
            update_deal(conn, decision.deal_id, tier=details.get("new_tier", 3))

        return True

    def optimize_outreach_strategy(self) -> Dict[str, Any]:
        """
        Analyze A/B test results and optimize outreach strategies.

        Returns recommendations for improving conversion rates.
        """
        conn = self._get_conn()
        ab_tests = get_ab_test_summary(conn)
        conn.close()

        recommendations = []

        for test in ab_tests:
            if test.get("total_conversions", 0) > 10:  # Enough data
                conversion_rate = (test.get("total_conversions", 0) /
                                 max(test.get("total_assignments", 1), 1))

                if conversion_rate > 0.15:  # Good performance
                    recommendations.append({
                        "test_type": test["test_type"],
                        "recommendation": "scale_up",
                        "reason": f"High conversion rate ({conversion_rate:.1%}) - expand usage",
                        "impact": "high"
                    })
                elif conversion_rate < 0.05:  # Poor performance
                    recommendations.append({
                        "test_type": test["test_type"],
                        "recommendation": "rethink_approach",
                        "reason": f"Low conversion rate ({conversion_rate:.1%}) - needs optimization",
                        "impact": "medium"
                    })

        return {
            "recommendations": recommendations,
            "tests_analyzed": len(ab_tests),
            "optimization_opportunities": len(recommendations)
        }

    def run_autonomous_cycle(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Complete autonomous cycle: analyze, decide, execute, optimize.

        Args:
            dry_run: If True, don't actually execute actions

        Returns:
            Results of the autonomous cycle
        """
        # 1. Analyze all active deals
        decisions = self.make_pipeline_decisions()

        # 2. Execute decisions
        execution_results = self.execute_decisions(decisions, dry_run=dry_run)

        # 3. Optimize strategies
        optimization_results = self.optimize_outreach_strategy()

        return {
            "decisions_made": len(decisions),
            "execution_results": execution_results,
            "optimization_results": optimization_results,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat()
        }


# ─── Integration Functions ───────────────────────────────────

def run_autonomous_sales_cycle(dry_run: bool = True) -> Dict[str, Any]:
    """
    Run a complete autonomous sales cycle.

    This function can be called by:
    - Scheduled jobs (daily/weekly)
    - API endpoints
    - Manual triggers
    """
    agent = AutonomousSalesAgent()
    return agent.run_autonomous_cycle(dry_run=dry_run)


def analyze_single_lead(deal_id: int) -> Dict[str, Any]:
    """Analyze a single lead and return recommendations."""
    agent = AutonomousSalesAgent()
    analysis = agent.analyze_lead(deal_id)

    return {
        "deal_id": analysis.deal_id,
        "recommended_action": analysis.recommended_action,
        "confidence": analysis.confidence_score,
        "reasoning": analysis.action_reason,
        "urgency": analysis.urgency_level,
        "next_action_date": analysis.next_action_date.isoformat() if analysis.next_action_date else None,
        "personalized_content": analysis.personalized_content
    }


# ─── CLI Interface ───────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Sales Agent")
    parser.add_argument("--analyze-deal", type=int, help="Analyze a specific deal")
    parser.add_argument("--run-cycle", action="store_true", help="Run full autonomous cycle")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute actions, just show what would be done")
    parser.add_argument("--optimize", action="store_true", help="Show optimization recommendations")

    args = parser.parse_args()

    agent = AutonomousSalesAgent()

    if args.analyze_deal:
        result = analyze_single_lead(args.analyze_deal)
        print(json.dumps(result, indent=2, default=str))

    elif args.run_cycle:
        result = agent.run_autonomous_cycle(dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))

    elif args.optimize:
        result = agent.optimize_outreach_strategy()
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()