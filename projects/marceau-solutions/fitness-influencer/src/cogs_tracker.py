#!/usr/bin/env python3
"""
cogs_tracker.py - Cost of Goods Sold (COGS) Tracker for Fitness Influencer AI

WHAT: Tracks AI API costs and calculates gross margins per transaction
WHY: Monitor COGS to ensure 60%+ gross margins (pre-launch requirement)
INPUT: API usage logs, pricing config
OUTPUT: Cost dashboard with margins, alerts, and recommendations

USAGE:
    from cogs_tracker import COGSTracker

    tracker = COGSTracker()
    tracker.log_transaction("grok_image", user_id="user123", count=2)
    tracker.log_transaction("shotstack_video", user_id="user123")

    report = tracker.get_daily_report()
    print(f"Gross Margin: {report['gross_margin_pct']}%")

COST STRUCTURE (as of 2026-01):
    - Grok Image Generation: $0.07/image
    - Shotstack Video: $0.06/video
    - Claude API (Blueprint): ~$0.002/request (estimated)
    - Total Video Ad: $0.34 (2 images × $0.07 + $0.06 video + overhead)

TARGET MARGINS:
    - FREE tools: 100% (no COGS)
    - Image generation: 70%+ at $0.25/image
    - Video ads: 65%+ at $1.00/video
    - Overall: 60%+ blended margin
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class PricingConfig:
    """Pricing configuration for API services."""

    # API Costs (what we pay)
    grok_image_cost: float = 0.07       # Per image
    shotstack_video_cost: float = 0.06  # Per video
    claude_api_cost: float = 0.002      # Per request (estimated)

    # Retail Prices (what we charge)
    grok_image_price: float = 0.25      # Per image (when pay-per-use)
    shotstack_video_price: float = 0.35 # Per video (when pay-per-use)
    video_ad_price: float = 1.00        # Complete video ad

    # Subscription allocations (for margin calculation)
    starter_monthly_price: float = 19.0
    starter_api_budget: float = 5.0     # Max API spend before overage

    pro_monthly_price: float = 49.0
    pro_api_budget: float = 20.0

    agency_monthly_price: float = 149.0
    agency_api_budget: float = 75.0


@dataclass
class Transaction:
    """A single API transaction."""
    timestamp: datetime
    service: str                        # grok_image, shotstack_video, claude_api
    user_id: str
    quantity: int = 1
    cost: float = 0.0
    revenue: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class COGSTracker:
    """Tracks Cost of Goods Sold for AI API usage."""

    SERVICES = {
        "grok_image": {
            "display_name": "AI Image Generation",
            "cost_field": "grok_image_cost",
            "price_field": "grok_image_price",
        },
        "shotstack_video": {
            "display_name": "Video Generation",
            "cost_field": "shotstack_video_cost",
            "price_field": "shotstack_video_price",
        },
        "claude_api": {
            "display_name": "AI Assistant",
            "cost_field": "claude_api_cost",
            "price_field": None,  # Included in subscription
        },
        "video_ad": {
            "display_name": "Video Ad (Bundle)",
            "cost_field": None,   # Calculated as 2 images + 1 video
            "price_field": "video_ad_price",
            "bundle_cost": lambda p: 2 * p.grok_image_cost + p.shotstack_video_cost,
        },
    }

    def __init__(self, db_path: Optional[str] = None, pricing: Optional[PricingConfig] = None):
        """Initialize the COGS tracker.

        Args:
            db_path: Path to SQLite database. Defaults to .tmp/cogs.db
            pricing: Pricing configuration. Uses defaults if not provided.
        """
        self.pricing = pricing or PricingConfig()

        if db_path is None:
            # Use .tmp directory for database
            tmp_dir = Path(__file__).parent.parent / ".tmp"
            tmp_dir.mkdir(exist_ok=True)
            db_path = str(tmp_dir / "cogs.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service TEXT NOT NULL,
                user_id TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                cost REAL DEFAULT 0,
                revenue REAL DEFAULT 0,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user ON transactions(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_service ON transactions(service)
        """)

        conn.commit()
        conn.close()

    def log_transaction(
        self,
        service: str,
        user_id: str,
        quantity: int = 1,
        revenue: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Transaction:
        """Log an API transaction.

        Args:
            service: Service type (grok_image, shotstack_video, claude_api, video_ad)
            user_id: User identifier
            quantity: Number of items (e.g., number of images)
            revenue: Revenue generated (None = calculate from pricing)
            metadata: Additional data to store

        Returns:
            Transaction object with calculated costs
        """
        if service not in self.SERVICES:
            raise ValueError(f"Unknown service: {service}. Valid: {list(self.SERVICES.keys())}")

        service_config = self.SERVICES[service]

        # Calculate cost
        if "bundle_cost" in service_config:
            cost = service_config["bundle_cost"](self.pricing) * quantity
        elif service_config["cost_field"]:
            cost = getattr(self.pricing, service_config["cost_field"]) * quantity
        else:
            cost = 0.0

        # Calculate revenue (if pay-per-use)
        if revenue is None:
            price_field = service_config.get("price_field")
            if price_field:
                revenue = getattr(self.pricing, price_field) * quantity
            else:
                revenue = 0.0

        timestamp = datetime.now()

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO transactions (timestamp, service, user_id, quantity, cost, revenue, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp.isoformat(),
            service,
            user_id,
            quantity,
            cost,
            revenue,
            json.dumps(metadata or {})
        ))

        conn.commit()
        conn.close()

        return Transaction(
            timestamp=timestamp,
            service=service,
            user_id=user_id,
            quantity=quantity,
            cost=cost,
            revenue=revenue,
            metadata=metadata or {}
        )

    def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        service: Optional[str] = None
    ) -> List[Transaction]:
        """Query transactions with filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT timestamp, service, user_id, quantity, cost, revenue, metadata FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if service:
            query += " AND service = ?"
            params.append(service)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        transactions = []
        for row in rows:
            transactions.append(Transaction(
                timestamp=datetime.fromisoformat(row[0]),
                service=row[1],
                user_id=row[2],
                quantity=row[3],
                cost=row[4],
                revenue=row[5],
                metadata=json.loads(row[6]) if row[6] else {}
            ))

        return transactions

    def get_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily COGS report.

        Args:
            date: Date to report on (defaults to today)

        Returns:
            Dict with costs, revenue, margins, and alerts
        """
        if date is None:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        transactions = self.get_transactions(start_date=start, end_date=end)

        return self._generate_report(transactions, "daily", start)

    def get_monthly_report(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """Generate monthly COGS report."""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        transactions = self.get_transactions(start_date=start, end_date=end)

        return self._generate_report(transactions, "monthly", start)

    def _generate_report(
        self,
        transactions: List[Transaction],
        period: str,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Generate a COGS report from transactions."""

        total_cost = sum(t.cost for t in transactions)
        total_revenue = sum(t.revenue for t in transactions)

        # Calculate gross margin
        if total_revenue > 0:
            gross_margin_pct = ((total_revenue - total_cost) / total_revenue) * 100
        else:
            gross_margin_pct = 100.0 if total_cost == 0 else 0.0

        # Breakdown by service
        by_service = {}
        for service_name, config in self.SERVICES.items():
            service_txns = [t for t in transactions if t.service == service_name]
            service_cost = sum(t.cost for t in service_txns)
            service_revenue = sum(t.revenue for t in service_txns)
            service_quantity = sum(t.quantity for t in service_txns)

            if service_txns:
                by_service[service_name] = {
                    "display_name": config["display_name"],
                    "quantity": service_quantity,
                    "cost": round(service_cost, 2),
                    "revenue": round(service_revenue, 2),
                    "margin_pct": round(((service_revenue - service_cost) / service_revenue * 100) if service_revenue > 0 else 0, 1),
                }

        # Generate alerts
        alerts = []

        # Alert if margin drops below 55%
        if gross_margin_pct < 55 and total_revenue > 0:
            alerts.append({
                "level": "warning",
                "message": f"Gross margin ({gross_margin_pct:.1f}%) below 55% target",
                "action": "Review pricing or optimize API usage"
            })

        # Alert if margin drops below 50% (critical)
        if gross_margin_pct < 50 and total_revenue > 0:
            alerts.append({
                "level": "critical",
                "message": f"Gross margin ({gross_margin_pct:.1f}%) below 50% threshold",
                "action": "URGENT: Increase pay-per-use pricing by 20% or limit usage"
            })

        # Alert if daily spend exceeds $50 (unusual activity)
        if period == "daily" and total_cost > 50:
            alerts.append({
                "level": "info",
                "message": f"Unusually high daily API spend: ${total_cost:.2f}",
                "action": "Review for abuse or unexpected usage patterns"
            })

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "transaction_count": len(transactions),
            "total_cost": round(total_cost, 2),
            "total_revenue": round(total_revenue, 2),
            "gross_profit": round(total_revenue - total_cost, 2),
            "gross_margin_pct": round(gross_margin_pct, 1),
            "target_margin_pct": 60.0,
            "margin_status": "healthy" if gross_margin_pct >= 60 else ("warning" if gross_margin_pct >= 50 else "critical"),
            "by_service": by_service,
            "alerts": alerts,
            "unique_users": len(set(t.user_id for t in transactions)),
        }

    def get_user_usage(self, user_id: str, month: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage summary for a specific user.

        Useful for tracking if users are within their subscription API budget.
        """
        if month is None:
            month = datetime.now()

        start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            end = datetime(month.year + 1, 1, 1)
        else:
            end = datetime(month.year, month.month + 1, 1)

        transactions = self.get_transactions(
            start_date=start,
            end_date=end,
            user_id=user_id
        )

        total_cost = sum(t.cost for t in transactions)

        # Determine if user is within budget (based on tier)
        # This would normally come from user's subscription tier
        budget = self.pricing.pro_api_budget  # Default to PRO
        within_budget = total_cost <= budget

        return {
            "user_id": user_id,
            "month": start.strftime("%Y-%m"),
            "total_cost": round(total_cost, 2),
            "budget": budget,
            "budget_remaining": round(max(0, budget - total_cost), 2),
            "budget_pct_used": round((total_cost / budget) * 100, 1) if budget > 0 else 0,
            "within_budget": within_budget,
            "transaction_count": len(transactions),
            "by_service": {
                service: sum(t.quantity for t in transactions if t.service == service)
                for service in self.SERVICES
            }
        }

    def export_html_dashboard(self, output_path: Optional[str] = None) -> str:
        """Export an HTML dashboard of current COGS metrics.

        Returns:
            Path to generated HTML file
        """
        daily = self.get_daily_report()
        monthly = self.get_monthly_report()

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Fitness Influencer AI - COGS Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f1a;
            color: #fff;
            padding: 40px;
        }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ margin-bottom: 30px; font-size: 28px; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .card {{
            background: #1a1a2e;
            border-radius: 12px;
            padding: 24px;
        }}
        .card h3 {{ color: #9ca3af; font-size: 14px; text-transform: uppercase; margin-bottom: 8px; }}
        .card .value {{ font-size: 32px; font-weight: 600; }}
        .card .subtext {{ color: #6b7280; font-size: 13px; margin-top: 8px; }}
        .healthy {{ color: #10b981; }}
        .warning {{ color: #f59e0b; }}
        .critical {{ color: #ef4444; }}
        .section {{ background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
        .section h2 {{ margin-bottom: 20px; font-size: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #2a2a4a; }}
        th {{ color: #9ca3af; font-weight: 500; font-size: 13px; text-transform: uppercase; }}
        .alert {{
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-size: 14px;
        }}
        .alert.warning {{ background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; }}
        .alert.critical {{ background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; }}
        .alert.info {{ background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; }}
        .alert strong {{ display: block; margin-bottom: 4px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>COGS Dashboard - Fitness Influencer AI</h1>

        <div class="cards">
            <div class="card">
                <h3>Today's Cost</h3>
                <div class="value">${daily['total_cost']:.2f}</div>
                <div class="subtext">{daily['transaction_count']} transactions</div>
            </div>
            <div class="card">
                <h3>Today's Revenue</h3>
                <div class="value">${daily['total_revenue']:.2f}</div>
                <div class="subtext">{daily['unique_users']} unique users</div>
            </div>
            <div class="card">
                <h3>Daily Gross Margin</h3>
                <div class="value {daily['margin_status']}">{daily['gross_margin_pct']:.1f}%</div>
                <div class="subtext">Target: 60%+</div>
            </div>
            <div class="card">
                <h3>Monthly Cost</h3>
                <div class="value">${monthly['total_cost']:.2f}</div>
                <div class="subtext">MTD ({monthly['start_date'][:7]})</div>
            </div>
        </div>

        {"".join(f'''
        <div class="alert {alert['level']}">
            <strong>{alert['level'].upper()}: {alert['message']}</strong>
            {alert['action']}
        </div>
        ''' for alert in (daily['alerts'] + monthly['alerts']))}

        <div class="section">
            <h2>Monthly Breakdown by Service</h2>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Quantity</th>
                        <th>Cost</th>
                        <th>Revenue</th>
                        <th>Margin</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f'''
                    <tr>
                        <td>{data['display_name']}</td>
                        <td>{data['quantity']}</td>
                        <td>${data['cost']:.2f}</td>
                        <td>${data['revenue']:.2f}</td>
                        <td class="{'healthy' if data['margin_pct'] >= 60 else 'warning' if data['margin_pct'] >= 50 else 'critical'}">{data['margin_pct']:.1f}%</td>
                    </tr>
                    ''' for service, data in monthly['by_service'].items())}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Pricing Configuration</h2>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Our Cost</th>
                        <th>We Charge</th>
                        <th>Margin</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>AI Image Generation</td>
                        <td>${self.pricing.grok_image_cost:.2f}</td>
                        <td>${self.pricing.grok_image_price:.2f}</td>
                        <td class="healthy">{((self.pricing.grok_image_price - self.pricing.grok_image_cost) / self.pricing.grok_image_price * 100):.0f}%</td>
                    </tr>
                    <tr>
                        <td>Video Generation</td>
                        <td>${self.pricing.shotstack_video_cost:.2f}</td>
                        <td>${self.pricing.shotstack_video_price:.2f}</td>
                        <td class="healthy">{((self.pricing.shotstack_video_price - self.pricing.shotstack_video_cost) / self.pricing.shotstack_video_price * 100):.0f}%</td>
                    </tr>
                    <tr>
                        <td>Video Ad (Bundle)</td>
                        <td>${(2 * self.pricing.grok_image_cost + self.pricing.shotstack_video_cost):.2f}</td>
                        <td>${self.pricing.video_ad_price:.2f}</td>
                        <td class="healthy">{((self.pricing.video_ad_price - (2 * self.pricing.grok_image_cost + self.pricing.shotstack_video_cost)) / self.pricing.video_ad_price * 100):.0f}%</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            Target Gross Margin: 60%+ |
            Warning Threshold: 55% |
            Critical Threshold: 50%
        </p>
    </div>
</body>
</html>"""

        if output_path is None:
            output_dir = Path(__file__).parent.parent / ".tmp"
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / "cogs_dashboard.html")

        with open(output_path, "w") as f:
            f.write(html)

        return output_path


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="COGS Tracker for Fitness Influencer AI")
    parser.add_argument("--log", help="Log a transaction: service,user_id,quantity")
    parser.add_argument("--daily", action="store_true", help="Show daily report")
    parser.add_argument("--monthly", action="store_true", help="Show monthly report")
    parser.add_argument("--dashboard", action="store_true", help="Generate HTML dashboard")
    parser.add_argument("--user", help="Show usage for specific user")

    args = parser.parse_args()

    tracker = COGSTracker()

    if args.log:
        parts = args.log.split(",")
        service = parts[0]
        user_id = parts[1] if len(parts) > 1 else "cli_user"
        quantity = int(parts[2]) if len(parts) > 2 else 1

        txn = tracker.log_transaction(service, user_id, quantity)
        print(f"Logged: {service} x{quantity} for {user_id}")
        print(f"  Cost: ${txn.cost:.2f}")
        print(f"  Revenue: ${txn.revenue:.2f}")

    if args.daily:
        report = tracker.get_daily_report()
        print("\n=== DAILY COGS REPORT ===")
        print(f"Date: {report['start_date'][:10]}")
        print(f"Transactions: {report['transaction_count']}")
        print(f"Total Cost: ${report['total_cost']:.2f}")
        print(f"Total Revenue: ${report['total_revenue']:.2f}")
        print(f"Gross Profit: ${report['gross_profit']:.2f}")
        print(f"Gross Margin: {report['gross_margin_pct']:.1f}% ({report['margin_status']})")

        if report['alerts']:
            print("\nALERTS:")
            for alert in report['alerts']:
                print(f"  [{alert['level'].upper()}] {alert['message']}")

    if args.monthly:
        report = tracker.get_monthly_report()
        print("\n=== MONTHLY COGS REPORT ===")
        print(f"Month: {report['start_date'][:7]}")
        print(f"Transactions: {report['transaction_count']}")
        print(f"Total Cost: ${report['total_cost']:.2f}")
        print(f"Total Revenue: ${report['total_revenue']:.2f}")
        print(f"Gross Profit: ${report['gross_profit']:.2f}")
        print(f"Gross Margin: {report['gross_margin_pct']:.1f}% ({report['margin_status']})")

        print("\nBy Service:")
        for service, data in report['by_service'].items():
            print(f"  {data['display_name']}: {data['quantity']} units, ${data['cost']:.2f} cost, {data['margin_pct']:.1f}% margin")

    if args.dashboard:
        path = tracker.export_html_dashboard()
        print(f"\nDashboard saved to: {path}")

    if args.user:
        usage = tracker.get_user_usage(args.user)
        print(f"\n=== USER USAGE: {args.user} ===")
        print(f"Month: {usage['month']}")
        print(f"Total Cost: ${usage['total_cost']:.2f}")
        print(f"Budget: ${usage['budget']:.2f}")
        print(f"Remaining: ${usage['budget_remaining']:.2f}")
        print(f"Used: {usage['budget_pct_used']:.1f}%")
        print(f"Within Budget: {'Yes' if usage['within_budget'] else 'NO'}")
