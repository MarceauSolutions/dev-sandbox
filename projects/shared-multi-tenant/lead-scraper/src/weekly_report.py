#!/usr/bin/env python3
"""
Automated Weekly Campaign Optimization Report

Generates comprehensive weekly email report with:
- Overall performance (all 3 businesses)
- A/B test results
- Cohort insights
- Optimization recommendations
- Action items for the week

Usage:
    # Preview report (no email sent)
    python -m src.weekly_report generate

    # Send report via email
    python -m src.weekly_report generate --send

    # Set up cron job (every Monday 8 AM)
    0 8 * * 1 cd /path/to/project && python -m src.weekly_report generate --send
"""

import argparse
import json
import os
import smtplib
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from src.campaign_analytics import CampaignAnalytics
from src.campaign_optimizer import CampaignOptimizer
from src.ab_testing import ABTestingFramework


class WeeklyReportGenerator:
    """Automated weekly campaign optimization report."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.analytics = CampaignAnalytics(output_dir)
        self.optimizer = CampaignOptimizer(output_dir)
        self.ab_manager = ABTestingFramework(output_dir)

        # Email config from environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.recipient = os.getenv("DIGEST_RECIPIENT", self.smtp_username)

    def generate_report_data(self) -> Dict[str, Any]:
        """
        Generate all report data.

        Returns:
            Dict with all sections
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "week_ending": datetime.now().strftime("%Y-%m-%d"),
            "businesses": {},
            "ab_tests": [],
            "cohort_insights": {},
            "recommendations": [],
            "action_items": []
        }

        # Business performance
        for business_id in ["marceau-solutions", "swflorida-hvac", "shipping-logistics"]:
            dashboard = self.analytics.get_dashboard(business_id, days=7)  # Last 7 days
            report["businesses"][business_id] = {
                "name": business_id.replace("-", " ").title(),
                "metrics": dashboard.get("summary_metrics", {}),
                "top_templates": dashboard.get("top_templates", [])[:3]
            }

        # A/B test results (last 7 days)
        all_tests = self.ab_manager.list_tests()
        recent_tests = []
        week_ago = datetime.now() - timedelta(days=7)

        for test in all_tests:
            created_at = datetime.fromisoformat(test.get("created_at", ""))
            if created_at >= week_ago and test.get("status") == "complete":
                recent_tests.append(test)

        report["ab_tests"] = recent_tests

        # Cohort insights (category performance)
        cohort_data = self.analytics.get_cohort_analysis("category")
        report["cohort_insights"] = cohort_data

        # Optimization recommendations
        recs = self.optimizer.get_recommendations()
        report["recommendations"] = [
            {
                "priority": r.priority,
                "category": r.category,
                "insight": r.insight,
                "action": r.action,
                "impact": r.expected_impact,
                "business": r.business_id
            }
            for r in recs[:10]  # Top 10 recommendations
        ]

        # Action items (high/critical priority recs)
        high_priority = [r for r in recs if r.priority in ["critical", "high"]]
        report["action_items"] = [
            {
                "priority": r.priority,
                "task": r.action,
                "reason": r.insight,
                "impact": r.expected_impact
            }
            for r in high_priority[:5]  # Top 5 action items
        ]

        return report

    def generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML email from report data."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .metric-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }}
        .action-item {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .action-critical {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .recommendation {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .test-result {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .cohort-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .cohort-table th {{
            background: #34495e;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        .cohort-table td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            font-size: 12px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <h1>📊 Weekly Campaign Optimization Report</h1>
    <p><strong>Week Ending:</strong> {report_data['week_ending']}<br>
    <strong>Generated:</strong> {datetime.fromisoformat(report_data['generated_at']).strftime('%Y-%m-%d %H:%M')}</p>

    <h2>🎯 Executive Summary</h2>
"""

        # Business performance summary
        for business_id, business_data in report_data["businesses"].items():
            metrics = business_data["metrics"]
            html += f"""
    <h3>{business_data['name']}</h3>
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Total Sent</div>
            <div class="metric-value">{metrics.get('total_sent', 0)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Response Rate</div>
            <div class="metric-value">{metrics.get('response_rate', 0):.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Hot Leads</div>
            <div class="metric-value">{metrics.get('hot_leads', 0)}</div>
        </div>
    </div>
"""

        # A/B test results
        if report_data["ab_tests"]:
            html += f"""
    <h2>🧪 A/B Test Results (Past 7 Days)</h2>
"""
            for test in report_data["ab_tests"]:
                winner_icon = "🏆" if test.get("winner") else "⏱️"
                html += f"""
    <div class="test-result">
        <strong>{winner_icon} {test.get('name', 'Unnamed Test')}</strong><br>
        Control: {test.get('control_template', 'N/A')} ({test.get('control_rate', 0)*100:.1f}%)<br>
        Variant: {test.get('variant_template', 'N/A')} ({test.get('variant_rate', 0)*100:.1f}%)<br>
        <strong>Winner:</strong> {test.get('winner', 'Not yet determined')} ({test.get('confidence', 0)*100:.0f}% confidence)
    </div>
"""
        else:
            html += """
    <h2>🧪 A/B Test Results</h2>
    <p>No A/B tests completed this week.</p>
"""

        # Cohort insights
        if report_data["cohort_insights"].get("cohorts"):
            html += f"""
    <h2>📈 Cohort Performance</h2>
    <table class="cohort-table">
        <tr>
            <th>Cohort</th>
            <th>Sent</th>
            <th>Response Rate</th>
            <th>Hot Leads</th>
        </tr>
"""
            for cohort, metrics in list(report_data["cohort_insights"]["cohorts"].items())[:5]:
                html += f"""
        <tr>
            <td><strong>{cohort.title()}</strong></td>
            <td>{metrics['total_sent']}</td>
            <td>{metrics['response_rate']*100:.1f}%</td>
            <td>{metrics['hot_leads']}</td>
        </tr>
"""
            html += """
    </table>
"""

        # Action items
        if report_data["action_items"]:
            html += """
    <h2>⚡ Action Items This Week</h2>
"""
            for i, item in enumerate(report_data["action_items"], 1):
                css_class = "action-critical" if item["priority"] == "critical" else "action-item"
                priority_icon = "🔴" if item["priority"] == "critical" else "🟠"
                html += f"""
    <div class="{css_class}">
        <strong>{i}. {priority_icon} {item['priority'].upper()}</strong><br>
        <strong>Task:</strong> {item['task']}<br>
        <strong>Why:</strong> {item['reason']}<br>
        <strong>Impact:</strong> {item['impact']}
    </div>
"""

        # Top recommendations
        if report_data["recommendations"]:
            html += """
    <h2>💡 Optimization Recommendations</h2>
"""
            for i, rec in enumerate(report_data["recommendations"][:5], 1):
                html += f"""
    <div class="recommendation">
        <strong>{i}. [{rec['category'].upper()}]</strong><br>
        <strong>Insight:</strong> {rec['insight']}<br>
        <strong>Action:</strong> {rec['action']}<br>
        <strong>Expected Impact:</strong> {rec['impact']}
    </div>
"""

        # Footer
        html += f"""
    <div class="footer">
        <p>🤖 Generated with <a href="https://claude.ai/claude-code">Claude Code</a></p>
        <p>For detailed analytics, run: <code>python -m src.campaign_analytics dashboard</code></p>
    </div>
</body>
</html>
"""

        return html

    def send_email(self, html_content: str, subject: str = None):
        """Send report via email."""
        if not self.smtp_username or not self.smtp_password:
            print("ERROR: SMTP credentials not configured in .env")
            print("  Need: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD")
            return False

        if subject is None:
            subject = f"Weekly Campaign Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_username
        msg["To"] = self.recipient

        # Attach HTML
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send
        try:
            print(f"Connecting to {self.smtp_host}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.smtp_username, self.recipient, msg.as_string())
            server.quit()

            print(f"✅ Email sent successfully to {self.recipient}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Weekly Campaign Optimization Report")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate weekly report")
    generate_parser.add_argument("--send", action="store_true", help="Send via email")
    generate_parser.add_argument("--save", help="Save HTML to file")

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    reporter = WeeklyReportGenerator()

    if args.command == "generate":
        print("Generating weekly report...")

        # Generate report data
        report_data = reporter.generate_report_data()

        # Generate HTML
        html = reporter.generate_html(report_data)

        # Save to file if requested
        if args.save:
            save_path = Path(args.save)
            save_path.parent.mkdir(exist_ok=True, parents=True)
            with open(save_path, 'w') as f:
                f.write(html)
            print(f"✅ Report saved to: {save_path}")

        # Send email if requested
        if args.send:
            reporter.send_email(html)
        else:
            print("\n" + "=" * 80)
            print("PREVIEW MODE (use --send to email)")
            print("=" * 80)
            print("\nReport data summary:")
            print(f"  Businesses tracked: {len(report_data['businesses'])}")
            print(f"  A/B tests completed: {len(report_data['ab_tests'])}")
            print(f"  Recommendations: {len(report_data['recommendations'])}")
            print(f"  Action items: {len(report_data['action_items'])}")

            if args.save:
                print(f"\n✅ HTML report saved to: {args.save}")
                print("   Open in browser to view formatted report")
            else:
                print("\nUse --save report.html to save HTML file")
                print("Use --send to email report")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
