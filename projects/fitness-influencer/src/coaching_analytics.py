#!/usr/bin/env python3
"""
coaching_analytics.py - PT Business Campaign Analytics

WHAT: Track SMS campaign performance, funnel conversion, and lead status
WHY: Can't optimize what you can't measure (SOP 22)
INPUT: Twilio message logs, Google Sheets lead data
OUTPUT: Campaign metrics report

QUICK USAGE:
  python execution/coaching_analytics.py --report weekly
  python execution/coaching_analytics.py --report funnel
  python execution/coaching_analytics.py --health-check

DEPENDENCIES: twilio, google-auth, google-api-python-client
API_KEYS: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, COACHING_TRACKER_SPREADSHEET_ID
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class CoachingAnalytics:
    """Track PT business metrics: SMS performance, funnel conversion, lead status."""

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.leads_sheet_id = os.getenv(
            'LEADS_SPREADSHEET_ID',
            '13bEJ2eEdgRN3vM-wAOv1CrEp-7AtlKnAQTCnutP535E'
        )
        self.client_sheet_id = os.getenv(
            'COACHING_TRACKER_SPREADSHEET_ID',
            '1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA'
        )

    def sms_weekly_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Pull SMS metrics from Twilio for the last N days.

        Returns delivery rate, reply rate, opt-out rate.
        """
        try:
            from twilio.rest import Client
        except ImportError:
            return {"error": "twilio package not installed"}

        if not all([self.account_sid, self.auth_token, self.from_number]):
            return {"error": "Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"}

        client = Client(self.account_sid, self.auth_token)
        since = datetime.utcnow() - timedelta(days=days)

        # Get outbound messages
        outbound = client.messages.list(
            from_=self.from_number,
            date_sent_after=since,
            limit=500
        )

        # Get inbound messages (replies)
        inbound = client.messages.list(
            to=self.from_number,
            date_sent_after=since,
            limit=500
        )

        # Categorize outbound
        sent = len(outbound)
        delivered = sum(1 for m in outbound if m.status == 'delivered')
        failed = sum(1 for m in outbound if m.status in ('failed', 'undelivered'))
        total_cost = sum(float(m.price or 0) for m in outbound)

        # Categorize inbound
        replies = len(inbound)
        opt_outs = sum(
            1 for m in inbound
            if m.body and m.body.strip().upper() in ('STOP', 'UNSUBSCRIBE', 'CANCEL', 'QUIT')
        )

        report = {
            "period": f"Last {days} days",
            "period_start": since.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "outbound": {
                "sent": sent,
                "delivered": delivered,
                "failed": failed,
                "delivery_rate": f"{(delivered/sent*100):.1f}%" if sent > 0 else "N/A",
                "total_cost": f"${abs(total_cost):.2f}"
            },
            "inbound": {
                "total_replies": replies,
                "opt_outs": opt_outs,
                "reply_rate": f"{(replies/sent*100):.1f}%" if sent > 0 else "N/A",
                "opt_out_rate": f"{(opt_outs/sent*100):.1f}%" if sent > 0 else "N/A"
            },
            "targets": {
                "delivery_rate": ">95%",
                "reply_rate": "2-5%",
                "opt_out_rate": "<2%"
            }
        }

        return report

    def funnel_report(self) -> Dict[str, Any]:
        """
        Read Leads sheet and calculate funnel metrics.

        Tracks: Total leads → Day 7 reached → Converted → Active clients
        """
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
        except ImportError:
            return {"error": "google-api-python-client not installed"}

        # Try to load Google credentials
        token_path = Path.home() / ".config" / "google" / "token.json"
        if not token_path.exists():
            # Try alternate location
            token_path = Path(__file__).parent.parent / ".google_token.json"

        if not token_path.exists():
            return {"error": f"Google token not found at {token_path}"}

        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build('sheets', 'v4', credentials=creds)

        # Read Leads sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=self.leads_sheet_id,
            range="Leads!A:T"
        ).execute()

        rows = result.get('values', [])
        if len(rows) < 2:
            return {"total_leads": 0, "message": "No leads yet"}

        headers = rows[0]
        leads = rows[1:]

        # Find status column
        status_col = None
        source_col = None
        for i, h in enumerate(headers):
            if 'status' in h.lower() or 'nurture' in h.lower():
                status_col = i
            if 'source' in h.lower():
                source_col = i

        total = len(leads)
        quiz_leads = sum(1 for r in leads if len(r) > (source_col or 0) and 'quiz' in r[source_col or 0].lower()) if source_col is not None else 0
        challenge_leads = sum(1 for r in leads if len(r) > (source_col or 0) and 'challenge' in r[source_col or 0].lower()) if source_col is not None else 0

        # Count by status
        status_counts = {}
        if status_col is not None:
            for r in leads:
                if len(r) > status_col:
                    status = r[status_col]
                    status_counts[status] = status_counts.get(status, 0) + 1

        day7_reached = sum(
            v for k, v in status_counts.items()
            if 'day7' in k.lower()
        )

        # Read Client Roster for conversion count
        try:
            client_result = service.spreadsheets().values().get(
                spreadsheetId=self.client_sheet_id,
                range="Client Roster!A:F"
            ).execute()
            client_rows = client_result.get('values', [])
            active_clients = max(0, len(client_rows) - 1)  # minus header
        except Exception:
            active_clients = 0

        funnel = {
            "total_leads": total,
            "by_source": {
                "quiz": quiz_leads,
                "challenge": challenge_leads,
                "other": total - quiz_leads - challenge_leads
            },
            "by_status": status_counts,
            "funnel_stages": {
                "captured": total,
                "day7_reached": day7_reached,
                "converted": active_clients,
                "conversion_rate": f"{(active_clients/total*100):.1f}%" if total > 0 else "N/A"
            }
        }

        return funnel

    def n8n_health_check(self) -> Dict[str, Any]:
        """Check n8n is running and all workflows are active."""
        import subprocess

        results = {"timestamp": datetime.utcnow().isoformat(), "checks": []}

        # Check n8n health endpoint
        try:
            r = subprocess.run(
                ["ssh", "-i", os.path.expanduser("~/.ssh/marceau-ec2-key.pem"),
                 "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no",
                 "ec2-user@34.193.98.97",
                 "curl -s -o /dev/null -w '%{http_code}' http://localhost:5678/healthz"],
                capture_output=True, text=True, timeout=30
            )
            status_code = r.stdout.strip().replace("'", "")
            healthy = status_code == "200"
            results["checks"].append({
                "name": "n8n health endpoint",
                "status": "OK" if healthy else "FAILED",
                "http_code": status_code
            })
        except Exception as e:
            results["checks"].append({
                "name": "n8n health endpoint",
                "status": "FAILED",
                "error": str(e)
            })

        # Check SSL cert expiry
        try:
            r = subprocess.run(
                ["ssh", "-i", os.path.expanduser("~/.ssh/marceau-ec2-key.pem"),
                 "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no",
                 "ec2-user@34.193.98.97",
                 "sudo certbot certificates 2>/dev/null | grep 'Expiry Date' | head -1"],
                capture_output=True, text=True, timeout=30
            )
            cert_info = r.stdout.strip()
            results["checks"].append({
                "name": "SSL certificate",
                "status": "OK" if cert_info else "UNKNOWN",
                "details": cert_info or "Could not check"
            })
        except Exception as e:
            results["checks"].append({
                "name": "SSL certificate",
                "status": "UNKNOWN",
                "error": str(e)
            })

        # Check Twilio balance
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            balance = client.api.v2010.account.balance.fetch()
            bal_amount = float(balance.balance)
            results["checks"].append({
                "name": "Twilio balance",
                "status": "OK" if bal_amount > 10 else "LOW",
                "balance": f"${bal_amount:.2f}",
                "currency": balance.currency
            })
        except Exception as e:
            results["checks"].append({
                "name": "Twilio balance",
                "status": "UNKNOWN",
                "error": str(e)
            })

        # Overall status
        all_ok = all(c["status"] == "OK" for c in results["checks"])
        results["overall"] = "ALL OK" if all_ok else "ISSUES DETECTED"

        return results

    def template_performance(self) -> Dict[str, Any]:
        """
        Analyze SMS template performance from local log file.

        Reads .tmp/logs/sms_log.jsonl and groups send counts by template.
        SOP 22 requirement: track response rates per template.
        """
        log_file = Path(".tmp/logs/sms_log.jsonl")
        if not log_file.exists():
            return {"error": "No SMS log found at .tmp/logs/sms_log.jsonl. Send some messages first."}

        template_stats: Dict[str, Dict[str, int]] = {}

        try:
            with open(log_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    template_name = entry.get("template", "custom_message")
                    if template_name not in template_stats:
                        template_stats[template_name] = {"sent": 0}
                    template_stats[template_name]["sent"] += 1
        except Exception as e:
            return {"error": f"Failed to parse SMS log: {e}"}

        # Sort by send count
        sorted_templates = dict(
            sorted(template_stats.items(), key=lambda x: x[1]["sent"], reverse=True)
        )

        return {
            "total_templates_used": len(sorted_templates),
            "templates": sorted_templates,
            "note": "Reply-rate attribution requires matching inbound replies to templates (via twilio_inbox_monitor)"
        }

    def print_report(self, data: Dict[str, Any], title: str):
        """Pretty-print a report."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2))
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="PT Business Analytics")
    parser.add_argument('--report', choices=['weekly', 'funnel', 'templates', 'all'],
                        help='Report type to generate')
    parser.add_argument('--health-check', action='store_true',
                        help='Run infrastructure health check')
    parser.add_argument('--days', type=int, default=7,
                        help='Lookback period in days (default: 7)')

    args = parser.parse_args()
    analytics = CoachingAnalytics()

    if args.health_check:
        result = analytics.n8n_health_check()
        analytics.print_report(result, "Infrastructure Health Check")
        sys.exit(0 if result["overall"] == "ALL OK" else 1)

    if not args.report:
        print("Error: --report or --health-check required")
        parser.print_help()
        sys.exit(1)

    if args.report in ('weekly', 'all'):
        result = analytics.sms_weekly_report(days=args.days)
        analytics.print_report(result, f"SMS Campaign Report (Last {args.days} Days)")

    if args.report in ('funnel', 'all'):
        result = analytics.funnel_report()
        analytics.print_report(result, "Funnel Conversion Report")

    if args.report in ('templates', 'all'):
        result = analytics.template_performance()
        analytics.print_report(result, "Template Performance Report")


if __name__ == "__main__":
    main()
