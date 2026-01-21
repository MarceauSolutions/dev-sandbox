#!/usr/bin/env python3
"""
Standardized Business Report Formatting
Provides consistent output formatting for all business reports.

This module ensures that all business outputs (revenue reports, email digests,
calendar summaries) have a consistent, professional appearance.

Usage:
    from business_report_format import BusinessReport

    report = BusinessReport("Revenue Report", "January 2026")
    report.add_section("Income", income_data)
    report.add_section("Expenses", expense_data)
    report.add_summary("Net Profit", "$5,000")
    output = report.render()
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class BusinessReport:
    """
    Standardized business report generator.

    Ensures consistent formatting across all business outputs:
    - Revenue/expense reports
    - Email digests
    - Calendar summaries
    - Cost/profit analysis
    """

    # Standard branding
    BRAND_NAME = "Marceau Solutions"
    DIVIDER_CHAR = "═"
    DIVIDER_WIDTH = 70

    def __init__(self, title: str, period: str = None, subtitle: str = None):
        """
        Initialize a new business report.

        Args:
            title: Main report title (e.g., "Revenue Report")
            period: Time period covered (e.g., "January 2026")
            subtitle: Optional subtitle
        """
        self.title = title
        self.period = period or datetime.now().strftime("%B %Y")
        self.subtitle = subtitle
        self.sections = []
        self.summary_items = []
        self.insights = []
        self.actions = []
        self.generated_at = datetime.now()

    def _divider(self, char: str = None) -> str:
        """Create a divider line."""
        char = char or self.DIVIDER_CHAR
        return char * self.DIVIDER_WIDTH

    def _format_currency(self, amount: float) -> str:
        """Format a number as currency."""
        return f"${amount:,.2f}"

    def _format_percent(self, value: float, include_sign: bool = True) -> str:
        """Format a number as percentage with optional sign."""
        if include_sign and value > 0:
            return f"+{value:.1f}%"
        return f"{value:.1f}%"

    def _growth_indicator(self, value: float) -> str:
        """Return an emoji indicator for growth/decline."""
        if value > 5:
            return "📈"
        elif value > 0:
            return "↗️"
        elif value < -5:
            return "📉"
        elif value < 0:
            return "↘️"
        return "➡️"

    def add_section(
        self,
        name: str,
        items: List[Dict[str, Any]],
        show_total: bool = True,
        total_label: str = "TOTAL"
    ):
        """
        Add a section with line items to the report.

        Args:
            name: Section name (e.g., "Income", "Expenses")
            items: List of dicts with 'label', 'amount', and optional 'growth'
            show_total: Whether to show section total
            total_label: Label for the total line

        Example items format:
            [
                {"label": "Sponsorships", "amount": 2500.00, "growth": 15.5},
                {"label": "Courses", "amount": 1200.00, "growth": -5.2}
            ]
        """
        self.sections.append({
            "name": name,
            "items": items,
            "show_total": show_total,
            "total_label": total_label
        })

    def add_summary(self, label: str, value: str, highlight: bool = False):
        """
        Add a key summary item to the report.

        Args:
            label: Summary item label (e.g., "Net Profit")
            value: Formatted value (e.g., "$5,000")
            highlight: Whether to visually highlight this item
        """
        self.summary_items.append({
            "label": label,
            "value": value,
            "highlight": highlight
        })

    def add_insight(self, message: str, status: str = "info"):
        """
        Add an insight or observation to the report.

        Args:
            message: The insight message
            status: One of "success", "warning", "info", "neutral"
        """
        icons = {
            "success": "✅",
            "warning": "⚠️",
            "info": "💡",
            "neutral": "➡️"
        }
        self.insights.append({
            "message": message,
            "icon": icons.get(status, "•")
        })

    def add_action(self, action: str, priority: str = "normal"):
        """
        Add a recommended action to the report.

        Args:
            action: The recommended action
            priority: One of "high", "normal", "low"
        """
        self.actions.append({
            "action": action,
            "priority": priority
        })

    def render(self, format: str = "text") -> str:
        """
        Render the report in the specified format.

        Args:
            format: Output format ("text", "html", "json")

        Returns:
            Formatted report string
        """
        if format == "json":
            return self._render_json()
        elif format == "html":
            return self._render_html()
        return self._render_text()

    def _render_text(self) -> str:
        """Render the report as plain text."""
        lines = []

        # Header
        lines.append("")
        lines.append(self._divider())
        lines.append(f"  {self.title.upper()}")
        if self.period:
            lines.append(f"  {self.period}")
        if self.subtitle:
            lines.append(f"  {self.subtitle}")
        lines.append(self._divider())
        lines.append("")

        # Sections
        for section in self.sections:
            lines.append(f"📊 {section['name'].upper()}")
            lines.append("-" * 50)

            total = 0
            for item in section['items']:
                label = item['label']
                amount = item['amount']
                total += amount

                # Format line
                amount_str = self._format_currency(amount)
                line = f"  {label:<25} {amount_str:>12}"

                # Add growth indicator if present
                if 'growth' in item and item['growth'] is not None:
                    growth = item['growth']
                    indicator = self._growth_indicator(growth)
                    growth_str = self._format_percent(growth)
                    line += f"  {indicator} {growth_str}"

                lines.append(line)

            # Show total if requested
            if section['show_total']:
                lines.append("  " + "-" * 45)
                total_str = self._format_currency(total)
                lines.append(f"  {section['total_label']:<25} {total_str:>12}")

            lines.append("")

        # Summary
        if self.summary_items:
            lines.append(self._divider("─"))
            for item in self.summary_items:
                if item['highlight']:
                    lines.append(f"★ {item['label']}: {item['value']}")
                else:
                    lines.append(f"  {item['label']}: {item['value']}")
            lines.append(self._divider("─"))
            lines.append("")

        # Insights
        if self.insights:
            lines.append("📈 INSIGHTS")
            lines.append("-" * 50)
            for insight in self.insights:
                lines.append(f"  {insight['icon']} {insight['message']}")
            lines.append("")

        # Actions
        if self.actions:
            lines.append("📋 RECOMMENDED ACTIONS")
            lines.append("-" * 50)
            for i, action in enumerate(self.actions, 1):
                priority_marker = "🔴" if action['priority'] == "high" else "🟡" if action['priority'] == "normal" else "⚪"
                lines.append(f"  {i}. {priority_marker} {action['action']}")
            lines.append("")

        # Footer
        lines.append(self._divider("─"))
        lines.append(f"  Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  {self.BRAND_NAME}")
        lines.append(self._divider("─"))
        lines.append("")

        return "\n".join(lines)

    def _render_html(self) -> str:
        """Render the report as HTML."""
        html = []

        html.append(f'''
        <div class="business-report" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f8f9fa; border-radius: 12px;">
            <div class="report-header" style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #667eea;">
                <h2 style="color: #1f2937; margin: 0 0 5px 0;">{self.title}</h2>
                <p style="color: #6b7280; margin: 0;">{self.period}</p>
            </div>
        ''')

        # Sections
        for section in self.sections:
            total = sum(item['amount'] for item in section['items'])

            html.append(f'''
            <div class="report-section" style="margin-bottom: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="color: #374151; margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">📊 {section['name']}</h3>
                <table style="width: 100%; border-collapse: collapse;">
            ''')

            for item in section['items']:
                growth_html = ""
                if 'growth' in item and item['growth'] is not None:
                    growth = item['growth']
                    indicator = self._growth_indicator(growth)
                    color = "#22c55e" if growth > 0 else "#ef4444" if growth < 0 else "#6b7280"
                    growth_html = f'<span style="color: {color}; font-size: 12px;">{indicator} {self._format_percent(growth)}</span>'

                html.append(f'''
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; color: #4b5563;">{item['label']}</td>
                        <td style="padding: 8px 0; text-align: right; font-weight: 500;">{self._format_currency(item['amount'])}</td>
                        <td style="padding: 8px 0; text-align: right; width: 80px;">{growth_html}</td>
                    </tr>
                ''')

            if section['show_total']:
                html.append(f'''
                    <tr style="font-weight: bold; border-top: 2px solid #374151;">
                        <td style="padding: 10px 0; color: #1f2937;">{section['total_label']}</td>
                        <td style="padding: 10px 0; text-align: right; color: #1f2937;">{self._format_currency(total)}</td>
                        <td></td>
                    </tr>
                ''')

            html.append('</table></div>')

        # Summary
        if self.summary_items:
            html.append('<div class="report-summary" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px;">')
            for item in self.summary_items:
                style = "color: white; margin: 5px 0;"
                if item['highlight']:
                    style += " font-size: 18px; font-weight: bold;"
                html.append(f'<p style="{style}">{item["label"]}: {item["value"]}</p>')
            html.append('</div>')

        # Insights
        if self.insights:
            html.append('''
            <div class="report-insights" style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #22c55e;">
                <h4 style="color: #166534; margin: 0 0 10px 0;">📈 Insights</h4>
                <ul style="margin: 0; padding-left: 20px; color: #4b5563;">
            ''')
            for insight in self.insights:
                html.append(f'<li style="margin: 5px 0;">{insight["icon"]} {insight["message"]}</li>')
            html.append('</ul></div>')

        # Actions
        if self.actions:
            html.append('''
            <div class="report-actions" style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f59e0b;">
                <h4 style="color: #92400e; margin: 0 0 10px 0;">📋 Recommended Actions</h4>
                <ol style="margin: 0; padding-left: 20px; color: #4b5563;">
            ''')
            for action in self.actions:
                priority_marker = "🔴" if action['priority'] == "high" else "🟡" if action['priority'] == "normal" else "⚪"
                html.append(f'<li style="margin: 5px 0;">{priority_marker} {action["action"]}</li>')
            html.append('</ol></div>')

        # Footer
        html.append(f'''
            <div class="report-footer" style="text-align: center; color: #9ca3af; font-size: 12px; padding-top: 15px; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0;">Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="margin: 5px 0 0 0; font-weight: 500; color: #667eea;">{self.BRAND_NAME}</p>
            </div>
        </div>
        ''')

        return "\n".join(html)

    def _render_json(self) -> dict:
        """Render the report as JSON/dict."""
        return {
            "report": {
                "title": self.title,
                "period": self.period,
                "subtitle": self.subtitle,
                "generated_at": self.generated_at.isoformat(),
                "brand": self.BRAND_NAME
            },
            "sections": [
                {
                    "name": s["name"],
                    "items": s["items"],
                    "total": sum(item["amount"] for item in s["items"]) if s["show_total"] else None
                }
                for s in self.sections
            ],
            "summary": self.summary_items,
            "insights": [{"message": i["message"], "status": i["icon"]} for i in self.insights],
            "actions": self.actions
        }


# Convenience functions for common report types

def create_revenue_report(
    month: str,
    revenue_by_source: Dict[str, float],
    expenses_by_category: Dict[str, float],
    prev_month_data: Dict[str, Any] = None
) -> BusinessReport:
    """
    Create a standardized revenue report.

    Args:
        month: Month string (e.g., "January 2026")
        revenue_by_source: Dict of revenue source -> amount
        expenses_by_category: Dict of expense category -> amount
        prev_month_data: Optional previous month data for growth calculation

    Returns:
        BusinessReport instance
    """
    report = BusinessReport("Revenue Report", month)

    # Calculate growth rates if previous data available
    def get_growth(source, amount, prev_data):
        if prev_data and source in prev_data:
            prev = prev_data[source]
            if prev > 0:
                return ((amount - prev) / prev) * 100
        return None

    # Revenue section
    revenue_items = [
        {
            "label": source,
            "amount": amount,
            "growth": get_growth(source, amount, prev_month_data.get("revenue") if prev_month_data else None)
        }
        for source, amount in sorted(revenue_by_source.items(), key=lambda x: x[1], reverse=True)
    ]
    report.add_section("Income", revenue_items, total_label="TOTAL REVENUE")

    # Expenses section
    expense_items = [
        {"label": category, "amount": amount}
        for category, amount in sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
    ]
    report.add_section("Expenses", expense_items, total_label="TOTAL EXPENSES")

    # Calculate totals
    total_revenue = sum(revenue_by_source.values())
    total_expenses = sum(expenses_by_category.values())
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    # Summary
    report.add_summary("Total Revenue", f"${total_revenue:,.2f}")
    report.add_summary("Total Expenses", f"${total_expenses:,.2f}")
    report.add_summary("Net Profit", f"${net_profit:,.2f} ({profit_margin:.1f}% margin)", highlight=True)

    # Insights
    if profit_margin > 70:
        report.add_insight(f"Excellent profit margin ({profit_margin:.1f}%)", "success")
    elif profit_margin > 50:
        report.add_insight(f"Healthy profit margin ({profit_margin:.1f}%)", "success")
    elif profit_margin > 30:
        report.add_insight(f"Moderate profit margin ({profit_margin:.1f}%)", "info")
    else:
        report.add_insight(f"Low profit margin ({profit_margin:.1f}%) - consider cost optimization", "warning")

    # Top source
    if revenue_by_source:
        top_source = max(revenue_by_source.items(), key=lambda x: x[1])
        top_pct = (top_source[1] / total_revenue * 100) if total_revenue > 0 else 0
        report.add_insight(f"Top revenue source: {top_source[0]} ({top_pct:.1f}%)", "info")

    return report


def create_email_digest(
    period_hours: int,
    categorized_emails: Dict[str, List[Dict]],
    total_count: int
) -> BusinessReport:
    """
    Create a standardized email digest report.

    Args:
        period_hours: Hours covered by digest
        categorized_emails: Dict of category -> list of email dicts
        total_count: Total number of emails

    Returns:
        BusinessReport instance
    """
    period = f"Last {period_hours} Hours"
    report = BusinessReport("Email Digest", period, f"{total_count} emails processed")

    # Create section items from categories
    items = []
    for category, emails in categorized_emails.items():
        if emails:
            items.append({
                "label": category.replace("_", " ").title(),
                "amount": len(emails),
                "growth": None
            })

    # Sort by count
    items.sort(key=lambda x: x["amount"], reverse=True)
    report.add_section("Email Categories", items, total_label="TOTAL EMAILS")

    # Summary
    urgent_count = len(categorized_emails.get("urgent", []))
    if urgent_count > 0:
        report.add_summary("⚠️ Urgent Emails", str(urgent_count), highlight=True)

    business_count = len(categorized_emails.get("sponsorship", [])) + len(categorized_emails.get("business", []))
    if business_count > 0:
        report.add_summary("Business Opportunities", str(business_count))

    # Actions from urgent emails
    for email in categorized_emails.get("urgent", [])[:3]:
        subject = email.get("subject", "No subject")[:50]
        report.add_action(f"Respond to: {subject}", "high")

    if not urgent_count:
        report.add_insight("No urgent actions required", "success")

    return report


def create_calendar_summary(
    days_ahead: int,
    events: List[Dict[str, Any]]
) -> BusinessReport:
    """
    Create a standardized calendar summary report.

    Args:
        days_ahead: Number of days covered
        events: List of calendar event dicts

    Returns:
        BusinessReport instance
    """
    period = f"Next {days_ahead} Days"
    report = BusinessReport("Calendar Summary", period, f"{len(events)} events")

    # Group events by type (if available) or day
    event_items = []
    for event in events[:10]:  # Limit to 10 events
        event_items.append({
            "label": event.get("summary", "Untitled")[:30],
            "amount": 1,
            "growth": None
        })

    if event_items:
        report.add_section("Upcoming Events", event_items, show_total=False)

    # Summary
    report.add_summary("Total Events", str(len(events)))

    # Check for conflicts or busy days
    if len(events) > 5:
        report.add_insight(f"Busy period ahead with {len(events)} events", "warning")
    else:
        report.add_insight("Schedule looks manageable", "success")

    return report


if __name__ == "__main__":
    # Demo usage
    print("=== BUSINESS REPORT FORMAT DEMO ===\n")

    # Create a sample revenue report
    revenue_data = {
        "Sponsorships": 2500.00,
        "Course Sales": 1200.00,
        "Affiliate": 450.00,
        "Coaching": 800.00
    }

    expense_data = {
        "Software": 150.00,
        "Equipment": 300.00,
        "Marketing": 200.00
    }

    prev_data = {
        "revenue": {
            "Sponsorships": 2200.00,
            "Course Sales": 1400.00,
            "Affiliate": 400.00
        }
    }

    report = create_revenue_report(
        "January 2026",
        revenue_data,
        expense_data,
        prev_data
    )

    # Render as text
    print(report.render("text"))

    print("\n\n=== HTML OUTPUT ===\n")
    print(report.render("html")[:500] + "...")
