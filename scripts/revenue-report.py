#!/usr/bin/env python3
"""
Weekly Revenue Dashboard

Generates a summary of revenue, payments, and business metrics.
Can be run manually or via cron for weekly reports.

USAGE:
    python scripts/revenue-report.py                # Weekly summary
    python scripts/revenue-report.py --period 7     # Last 7 days
    python scripts/revenue-report.py --period 30    # Last 30 days
    python scripts/revenue-report.py --email        # Send via email

CRON SETUP (for weekly reports):
    0 9 * * 1 cd /home/clawdbot/dev-sandbox && python scripts/revenue-report.py --email

Created: 2026-01-29
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Import our modules
try:
    from execution.stripe_payments import StripePayments
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    HAS_EMAIL = True
except ImportError:
    HAS_EMAIL = False


def get_stripe_metrics(days: int = 7) -> Dict[str, Any]:
    """Get Stripe revenue metrics for the period."""
    if not HAS_STRIPE:
        return {"error": "Stripe not configured"}

    try:
        sp = StripePayments()

        # Get revenue report
        start_date = datetime.now() - timedelta(days=days)
        report = sp.get_revenue_report(start_date)

        # Get recent payments
        recent = sp.get_recent_payments(10)

        return {
            "total_revenue": report["summary"]["total_revenue_dollars"],
            "successful_charges": report["summary"]["successful_charges"],
            "pending_invoices": report["summary"]["pending_invoices"],
            "pending_amount": report["summary"]["pending_amount_dollars"],
            "recent_payments": recent,
            "by_customer": report["by_customer"]
        }
    except Exception as e:
        return {"error": str(e)}


def get_form_submissions(days: int = 7) -> Dict[str, Any]:
    """Get form submission metrics."""
    submissions_file = Path(__file__).parent.parent / "output" / "form_submissions" / "all_submissions.json"

    if not submissions_file.exists():
        return {"total": 0, "by_source": {}}

    try:
        with open(submissions_file, 'r') as f:
            all_subs = json.load(f)

        # Filter to period
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in all_subs if s.get("timestamp", "") > cutoff]

        # Count by source
        by_source = {}
        for sub in recent:
            source = sub.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total": len(recent),
            "by_source": by_source,
            "all_time_total": len(all_subs)
        }
    except Exception as e:
        return {"error": str(e)}


def get_campaign_metrics(days: int = 7) -> Dict[str, Any]:
    """Get SMS campaign metrics."""
    campaigns_file = Path(__file__).parent.parent / "output" / "sms_campaigns.json"

    if not campaigns_file.exists():
        return {"sent": 0, "responses": 0}

    try:
        with open(campaigns_file, 'r') as f:
            data = json.load(f)

        return {
            "total_sent": data.get("total_sent", 0),
            "total_responses": data.get("total_responses", 0),
            "response_rate": data.get("response_rate", 0),
            "hot_leads": data.get("hot_leads", 0)
        }
    except Exception as e:
        return {"error": str(e)}


def generate_report(days: int = 7) -> str:
    """Generate the full revenue report."""
    now = datetime.now()
    period_start = now - timedelta(days=days)

    # Gather metrics
    stripe = get_stripe_metrics(days)
    forms = get_form_submissions(days)
    campaigns = get_campaign_metrics(days)

    # Build report
    report = []
    report.append("=" * 60)
    report.append(f"   WEEKLY REVENUE DASHBOARD")
    report.append(f"   {period_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    report.append("=" * 60)
    report.append("")

    # Revenue Section
    report.append("REVENUE")
    report.append("-" * 40)
    if "error" in stripe:
        report.append(f"  Error: {stripe['error']}")
    else:
        report.append(f"  Total Revenue:       ${stripe['total_revenue']:.2f}")
        report.append(f"  Successful Charges:  {stripe['successful_charges']}")
        report.append(f"  Pending Invoices:    {stripe['pending_invoices']}")
        report.append(f"  Pending Amount:      ${stripe['pending_amount']:.2f}")

        if stripe.get("recent_payments"):
            report.append("")
            report.append("  Recent Payments:")
            for p in stripe["recent_payments"][:5]:
                desc = p.get("description") or "No description"
                report.append(f"    ${p['amount']:.2f} - {desc[:30]}")
    report.append("")

    # Leads Section
    report.append("LEADS & INQUIRIES")
    report.append("-" * 40)
    if "error" in forms:
        report.append(f"  Error: {forms['error']}")
    else:
        report.append(f"  Form Submissions (period): {forms['total']}")
        report.append(f"  All-time Total:            {forms.get('all_time_total', 0)}")
        if forms.get("by_source"):
            report.append("  By Source:")
            for source, count in forms["by_source"].items():
                report.append(f"    {source}: {count}")
    report.append("")

    # Campaigns Section
    report.append("SMS CAMPAIGNS")
    report.append("-" * 40)
    if "error" in campaigns:
        report.append(f"  Error: {campaigns['error']}")
    else:
        report.append(f"  Messages Sent:    {campaigns.get('total_sent', 0)}")
        report.append(f"  Responses:        {campaigns.get('total_responses', 0)}")
        report.append(f"  Response Rate:    {campaigns.get('response_rate', 0):.1f}%")
        report.append(f"  Hot Leads:        {campaigns.get('hot_leads', 0)}")
    report.append("")

    # Summary Section
    report.append("SUMMARY")
    report.append("-" * 40)
    total_rev = stripe.get("total_revenue", 0) if "error" not in stripe else 0
    total_leads = forms.get("total", 0) if "error" not in forms else 0

    if total_rev > 0:
        report.append(f"  Revenue this period:  ${total_rev:.2f}")
    else:
        report.append(f"  Revenue this period:  $0.00")

    report.append(f"  New leads:            {total_leads}")

    # Cost per lead (if we have both)
    if total_leads > 0 and total_rev > 0:
        cpl = total_rev / total_leads if total_leads else 0
        report.append(f"  Revenue per lead:     ${cpl:.2f}")

    report.append("")
    report.append("=" * 60)
    report.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    return "\n".join(report)


def send_email_report(report: str):
    """Send report via email."""
    if not HAS_EMAIL:
        print("Email not available")
        return False

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("NOTIFICATION_EMAIL", smtp_user)

    if not all([smtp_user, smtp_pass, recipient]):
        print("Email not configured (missing SMTP credentials)")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = f"Weekly Revenue Report - {datetime.now().strftime('%Y-%m-%d')}"

        msg.attach(MIMEText(report, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print(f"Report sent to {recipient}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Weekly Revenue Dashboard")
    parser.add_argument("--period", type=int, default=7, help="Number of days to report on (default: 7)")
    parser.add_argument("--email", action="store_true", help="Send report via email")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.json:
        # Output raw metrics as JSON
        metrics = {
            "period_days": args.period,
            "generated_at": datetime.now().isoformat(),
            "stripe": get_stripe_metrics(args.period),
            "forms": get_form_submissions(args.period),
            "campaigns": get_campaign_metrics(args.period)
        }
        print(json.dumps(metrics, indent=2))
    else:
        # Generate human-readable report
        report = generate_report(args.period)
        print(report)

        if args.email:
            send_email_report(report)


if __name__ == "__main__":
    main()
