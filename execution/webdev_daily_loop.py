#!/usr/bin/env python3
"""
webdev_daily_loop.py - Web Development Tower Daily Operations

Runs daily automated tasks for the web-dev tower:
- Check-in reminders for maintenance clients
- Project status monitoring
- Stalled project alerts
- Summary reporting

SCHEDULE (via cron):
  - 9:00 AM ET (13:00 UTC): Full daily check
  - 5:00 PM ET (21:00 UTC): EOD summary

USAGE:
  python -m execution.webdev_daily_loop full        # Full daily check
  python -m execution.webdev_daily_loop checkins    # Process check-ins only
  python -m execution.webdev_daily_loop stalled     # Check stalled projects
  python -m execution.webdev_daily_loop summary     # Generate summary
"""

import os
import sys
import json
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project paths
sys.path.insert(0, str(Path(__file__).parents[1]))

from execution.webdev_project_manager import WebDevProjectManager

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

DB_PATH = Path("/home/clawdbot/data/pipeline.db")
N8N_BASE = os.getenv("N8N_WEBHOOK_URL", "https://n8n.marceausolutions.com/webhook")

# Telegram notification (via Clawdbot)
TELEGRAM_NOTIFY_URL = os.getenv("TELEGRAM_NOTIFY_URL", "http://127.0.0.1:3000/api/notify")

# Thresholds
STALLED_DAYS = {
    "proposal": 7,      # Proposal not approved after 7 days
    "approved": 3,      # Approved but not started after 3 days
    "research": 5,      # Research phase stalled
    "content": 5,       # Content generation stalled
    "build": 7,         # Build phase stalled
    "review": 14,       # Client review taking too long
    "revision": 10,     # Revisions taking too long
    "deploy": 3,        # Deployment delayed
}


class WebDevDailyLoop:
    """
    Daily operations for the web-dev tower.
    Monitors projects, sends check-in reminders, and generates reports.
    """

    def __init__(self):
        self.mgr = WebDevProjectManager()
        self.dry_run = False

    def _get_db(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _notify(self, message: str, urgent: bool = False) -> bool:
        """Send notification via Telegram."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would notify: {message}")
            return True
        
        try:
            # Try Clawdbot notify endpoint
            response = requests.post(
                TELEGRAM_NOTIFY_URL,
                json={"message": message, "urgent": urgent},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"Notification failed: {e}")
            return False

    # ── Check-ins ────────────────────────────────────────────────────────────

    def process_checkins(self) -> List[Dict[str, Any]]:
        """
        Process maintenance check-ins for live sites.
        
        Returns list of projects that need check-in action.
        """
        logger.info("Processing maintenance check-ins...")
        
        # Get projects due for check-in (within next 7 days)
        due_projects = self.mgr.get_projects_due_checkin(days_ahead=7)
        
        if not due_projects:
            logger.info("No projects due for check-in")
            return []
        
        actions_needed = []
        today = datetime.now().date()
        
        for project in due_projects:
            next_checkin = project.get('next_checkin')
            if next_checkin:
                checkin_date = datetime.strptime(next_checkin, "%Y-%m-%d").date()
                days_until = (checkin_date - today).days
            else:
                days_until = 0  # No check-in date means overdue
            
            # Determine urgency
            if days_until <= 0:
                urgency = "OVERDUE"
            elif days_until <= 3:
                urgency = "DUE_SOON"
            else:
                urgency = "UPCOMING"
            
            action = {
                "project_id": project['id'],
                "project_name": project['project_name'],
                "company": project.get('company', 'N/A'),
                "contact_email": project.get('contact_email', 'N/A'),
                "next_checkin": next_checkin,
                "days_until": days_until,
                "urgency": urgency,
                "live_url": project.get('live_url')
            }
            actions_needed.append(action)
            
            # Send notification for overdue
            if urgency == "OVERDUE":
                self._notify(
                    f"🌐 OVERDUE Check-in: {project['project_name']}\n"
                    f"Client: {project.get('company', 'N/A')}\n"
                    f"Was due: {next_checkin}",
                    urgent=True
                )
        
        logger.info(f"Found {len(actions_needed)} projects needing check-in attention")
        return actions_needed

    # ── Stalled Projects ─────────────────────────────────────────────────────

    def check_stalled_projects(self) -> List[Dict[str, Any]]:
        """
        Check for projects that have stalled in a stage too long.
        
        Returns list of stalled projects with recommendations.
        """
        logger.info("Checking for stalled projects...")
        
        conn = self._get_db()
        cursor = conn.cursor()
        
        stalled = []
        today = datetime.now()
        
        for stage, max_days in STALLED_DAYS.items():
            cutoff = (today - timedelta(days=max_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                SELECT wp.*, d.company, d.contact_name, d.contact_email
                FROM webdev_projects wp
                LEFT JOIN deals d ON wp.deal_id = d.id
                WHERE wp.status = ?
                AND wp.updated_at < ?
                ORDER BY wp.updated_at ASC
            """, (stage, cutoff))
            
            for row in cursor.fetchall():
                project = dict(row)
                days_stalled = (today - datetime.fromisoformat(project['updated_at'])).days
                
                stalled.append({
                    "project_id": project['id'],
                    "project_name": project['project_name'],
                    "company": project.get('company', 'N/A'),
                    "status": stage,
                    "days_stalled": days_stalled,
                    "threshold_days": max_days,
                    "last_updated": project['updated_at'],
                    "recommendation": self._get_stall_recommendation(stage)
                })
        
        conn.close()
        
        if stalled:
            # Send alert for stalled projects
            stalled_summary = "\n".join([
                f"• {p['project_name']} ({p['status']}): {p['days_stalled']}d"
                for p in stalled[:5]  # Top 5
            ])
            
            self._notify(
                f"⚠️ {len(stalled)} Stalled Web Projects:\n{stalled_summary}",
                urgent=len(stalled) >= 3
            )
        
        logger.info(f"Found {len(stalled)} stalled projects")
        return stalled

    def _get_stall_recommendation(self, stage: str) -> str:
        """Get recommendation for a stalled stage."""
        recommendations = {
            "proposal": "Follow up with client on proposal. Consider scheduling a call.",
            "approved": "Kick off project immediately. Gather requirements.",
            "research": "Complete research phase. Check if more info needed from client.",
            "content": "Generate content or request client input.",
            "build": "Complete site build. Check for blockers.",
            "review": "Follow up with client for feedback. Send reminder.",
            "revision": "Complete revisions or clarify requirements.",
            "deploy": "Deploy immediately or resolve deployment blockers.",
        }
        return recommendations.get(stage, "Review project status and take action.")

    # ── Pipeline Overview ────────────────────────────────────────────────────

    def get_pipeline_overview(self) -> Dict[str, Any]:
        """Get current pipeline overview for all stages."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Projects by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM webdev_projects
            WHERE status != 'archived'
            GROUP BY status
            ORDER BY 
                CASE status
                    WHEN 'proposal' THEN 1
                    WHEN 'approved' THEN 2
                    WHEN 'research' THEN 3
                    WHEN 'content' THEN 4
                    WHEN 'build' THEN 5
                    WHEN 'review' THEN 6
                    WHEN 'revision' THEN 7
                    WHEN 'deploy' THEN 8
                    WHEN 'live' THEN 9
                    WHEN 'maintenance' THEN 10
                    ELSE 99
                END
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Recent activity (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM webdev_projects
            WHERE updated_at >= datetime('now', '-7 days')
        """)
        recent_activity = cursor.fetchone()[0]
        
        # Projects launched this month
        cursor.execute("""
            SELECT COUNT(*) FROM webdev_projects
            WHERE status IN ('live', 'maintenance')
            AND launched_at >= date('now', 'start of month')
        """)
        launched_this_month = cursor.fetchone()[0]
        
        # Revenue this month
        cursor.execute("""
            SELECT 
                SUM(setup_fee) as setup,
                SUM(monthly_fee) as monthly
            FROM webdev_projects
            WHERE status IN ('live', 'maintenance')
            AND launched_at >= date('now', 'start of month')
        """)
        revenue_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "by_status": by_status,
            "total_active": sum(by_status.values()),
            "recent_activity": recent_activity,
            "launched_this_month": launched_this_month,
            "revenue_this_month": {
                "setup": revenue_row['setup'] or 0,
                "monthly": revenue_row['monthly'] or 0
            },
            "timestamp": datetime.now().isoformat()
        }

    # ── Summary Report ───────────────────────────────────────────────────────

    def generate_summary(self, send_notification: bool = True) -> str:
        """
        Generate daily summary report.
        
        Returns formatted summary string.
        """
        logger.info("Generating web-dev tower summary...")
        
        overview = self.get_pipeline_overview()
        checkins = self.mgr.get_projects_due_checkin(days_ahead=7)
        stalled = self.check_stalled_projects()
        stats = self.mgr.get_tower_stats()
        
        # Build summary
        lines = [
            "🌐 **Web-Dev Tower Daily Summary**",
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "**Pipeline Overview:**",
        ]
        
        # Status breakdown
        for status, count in overview['by_status'].items():
            emoji = {
                'proposal': '📋', 'approved': '✅', 'research': '🔍',
                'content': '✏️', 'build': '🔨', 'review': '👀',
                'revision': '🔄', 'deploy': '🚀', 'live': '🟢',
                'maintenance': '🔧'
            }.get(status, '📁')
            lines.append(f"  {emoji} {status.title()}: {count}")
        
        lines.append(f"\n**Activity:**")
        lines.append(f"  • Active projects: {overview['total_active']}")
        lines.append(f"  • Updated this week: {overview['recent_activity']}")
        lines.append(f"  • Launched this month: {overview['launched_this_month']}")
        
        # Revenue
        rev = overview['revenue_this_month']
        if rev['setup'] or rev['monthly']:
            lines.append(f"\n**Revenue This Month:**")
            lines.append(f"  • Setup fees: ${rev['setup']:,.0f}")
            lines.append(f"  • Monthly fees: ${rev['monthly']:,.0f}/mo")
        
        # Check-ins due
        if checkins:
            overdue = [c for c in checkins if c.get('next_checkin') and 
                      datetime.strptime(c['next_checkin'], "%Y-%m-%d").date() <= datetime.now().date()]
            lines.append(f"\n**Maintenance Check-ins:**")
            lines.append(f"  • Due this week: {len(checkins)}")
            lines.append(f"  • Overdue: {len(overdue)}")
        
        # Stalled projects
        if stalled:
            lines.append(f"\n**⚠️ Stalled Projects: {len(stalled)}**")
            for p in stalled[:3]:
                lines.append(f"  • {p['project_name']}: {p['status']} ({p['days_stalled']}d)")
        
        summary = "\n".join(lines)
        
        if send_notification:
            self._notify(summary)
        
        logger.info("Summary generated")
        return summary

    # ── Full Daily Run ───────────────────────────────────────────────────────

    def run_full_daily(self) -> Dict[str, Any]:
        """
        Run full daily operations.
        
        Returns summary of all actions taken.
        """
        logger.info("=" * 60)
        logger.info("WEB-DEV TOWER DAILY LOOP")
        logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run
        }
        
        # 1. Check-ins
        try:
            results['checkins'] = self.process_checkins()
        except Exception as e:
            logger.error(f"Check-ins failed: {e}")
            results['checkins_error'] = str(e)
        
        # 2. Stalled projects
        try:
            results['stalled'] = self.check_stalled_projects()
        except Exception as e:
            logger.error(f"Stalled check failed: {e}")
            results['stalled_error'] = str(e)
        
        # 3. Overview
        try:
            results['overview'] = self.get_pipeline_overview()
        except Exception as e:
            logger.error(f"Overview failed: {e}")
            results['overview_error'] = str(e)
        
        # 4. Send summary
        try:
            self.generate_summary(send_notification=not self.dry_run)
        except Exception as e:
            logger.error(f"Summary failed: {e}")
            results['summary_error'] = str(e)
        
        logger.info("Daily loop complete")
        return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/home/clawdbot/logs/webdev_daily_loop.log', mode='a')
        ]
    )
    
    parser = argparse.ArgumentParser(description="Web-Dev Tower Daily Loop")
    parser.add_argument("command", nargs="?", default="full",
                       choices=["full", "checkins", "stalled", "summary", "overview"],
                       help="Command to run")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without sending notifications")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON")
    
    args = parser.parse_args()
    
    loop = WebDevDailyLoop()
    loop.dry_run = args.dry_run
    
    if args.command == "full":
        result = loop.run_full_daily()
    elif args.command == "checkins":
        result = loop.process_checkins()
    elif args.command == "stalled":
        result = loop.check_stalled_projects()
    elif args.command == "summary":
        result = loop.generate_summary(send_notification=not args.dry_run)
    elif args.command == "overview":
        result = loop.get_pipeline_overview()
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif isinstance(result, str):
        print(result)
    elif isinstance(result, list):
        for item in result:
            print(json.dumps(item, default=str))
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
