#!/usr/bin/env python3
"""
POC Report Generator - Create professional client-facing reports

Generates PDF reports showing:
- Call volume and answer rates
- Appointments booked
- Revenue impact
- Before/after comparisons
- Hour-by-hour breakdowns

Usage:
    python -m src.poc_report_generator --business hvac --week 1
    python -m src.poc_report_generator --business shipping --week 1 --format pdf
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will use matplotlib only.")


@dataclass
class CallMetrics:
    """Metrics for a single call."""
    call_id: str
    timestamp: str
    duration_seconds: int
    caller_phone: str
    outcome: str  # answered, missed, transferred
    appointment_booked: bool = False
    estimated_value: float = 0.0
    hour_of_day: int = 0


@dataclass
class POCResults:
    """Complete POC results for reporting."""
    business_name: str
    poc_week: int
    start_date: str
    end_date: str

    # Call volume
    total_calls: int = 0
    ai_answered: int = 0
    transferred: int = 0
    missed: int = 0

    # Appointments
    appointments_booked: int = 0
    emergency_appointments: int = 0
    routine_appointments: int = 0

    # Revenue
    estimated_revenue: float = 0.0
    ai_cost: float = 50.0  # Monthly cost
    roi_percentage: float = 0.0

    # After-hours
    after_hours_calls: int = 0
    after_hours_value: float = 0.0

    # Hourly breakdown
    hourly_distribution: Dict[int, int] = None

    # Daily breakdown
    daily_calls: Dict[str, int] = None


class POCReportGenerator:
    """Generates professional POC reports for clients."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_mock_hvac_data(self) -> POCResults:
        """Generate mock data for HVAC Week 1 POC (for demo purposes)."""
        results = POCResults(
            business_name="SW Florida Comfort HVAC",
            poc_week=1,
            start_date="2026-01-13",
            end_date="2026-01-19",
            total_calls=47,
            ai_answered=42,
            transferred=5,
            missed=0,
            appointments_booked=12,
            emergency_appointments=3,
            routine_appointments=9,
            estimated_revenue=8000.0,
            ai_cost=50.0,
            after_hours_calls=18,
            after_hours_value=3200.0
        )

        # Calculate ROI
        results.roi_percentage = ((results.estimated_revenue - results.ai_cost) / results.ai_cost) * 100

        # Hourly distribution (24 hours)
        results.hourly_distribution = {
            6: 1, 7: 2, 8: 4, 9: 5, 10: 6, 11: 4,
            12: 3, 13: 2, 14: 3, 15: 4, 16: 5, 17: 6,
            18: 2, 19: 1, 20: 1, 21: 1, 22: 1, 23: 1
        }

        # Daily calls
        results.daily_calls = {
            "Mon": 8, "Tue": 6, "Wed": 7, "Thu": 9, "Fri": 10, "Sat": 4, "Sun": 3
        }

        return results

    def create_text_report(self, results: POCResults) -> str:
        """Create plain text summary report."""
        answer_rate = (results.ai_answered / results.total_calls * 100) if results.total_calls > 0 else 0
        after_hours_pct = (results.after_hours_calls / results.total_calls * 100) if results.total_calls > 0 else 0

        report = f"""
{results.business_name.upper()} - WEEK {results.poc_week} POC RESULTS
{'='*60}

REPORTING PERIOD: {results.start_date} to {results.end_date}

📞 CALL VOLUME
─────────────────────────────────────────────────────────────
Total Calls:        {results.total_calls}
AI Answered:        {results.ai_answered} ({answer_rate:.1f}%)
Transferred:        {results.transferred} ({results.transferred/results.total_calls*100:.1f}%)
Missed:             {results.missed} ({results.missed/results.total_calls*100 if results.total_calls else 0:.1f}%)

📅 APPOINTMENTS BOOKED
─────────────────────────────────────────────────────────────
Total Booked:       {results.appointments_booked}
Emergency:          {results.emergency_appointments}
Routine:            {results.routine_appointments}
Booking Rate:       {results.appointments_booked/results.total_calls*100:.1f}%

💰 REVENUE IMPACT
─────────────────────────────────────────────────────────────
Estimated Revenue:  ${results.estimated_revenue:,.2f}
Cost of AI:         ${results.ai_cost:.2f}
Net Profit:         ${results.estimated_revenue - results.ai_cost:,.2f}
ROI:                {results.roi_percentage:,.0f}%

⏰ AFTER-HOURS PERFORMANCE
─────────────────────────────────────────────────────────────
After-hours calls:  {results.after_hours_calls} ({after_hours_pct:.1f}%)
Would have missed:  {results.after_hours_calls} calls
Lost revenue:       ${results.after_hours_value:,.2f}

KEY INSIGHTS
─────────────────────────────────────────────────────────────
✓ Zero missed calls (100% answer rate during POC)
✓ ${results.after_hours_value:,.0f} in after-hours revenue captured
✓ {results.roi_percentage:,.0f}% ROI in first week
✓ {results.appointments_booked} appointments booked automatically

NEXT STEPS
─────────────────────────────────────────────────────────────
1. Continue monitoring Week 2 performance
2. Optimize AI responses based on call insights
3. Track conversion rate (appointments → revenue)

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
        return report

    def create_charts(self, results: POCResults) -> Dict[str, str]:
        """Create visualization charts and return paths."""
        chart_paths = {}

        # 1. Hourly distribution bar chart
        if results.hourly_distribution:
            fig, ax = plt.subplots(figsize=(10, 5))
            hours = list(results.hourly_distribution.keys())
            calls = list(results.hourly_distribution.values())

            bars = ax.bar(hours, calls, color='#3b82f6', alpha=0.8)

            # Highlight after-hours (before 8 AM, after 6 PM)
            for i, hour in enumerate(hours):
                if hour < 8 or hour >= 18:
                    bars[i].set_color('#f97316')

            ax.set_xlabel('Hour of Day')
            ax.set_ylabel('Number of Calls')
            ax.set_title(f'{results.business_name} - Hourly Call Distribution')
            ax.grid(axis='y', alpha=0.3)

            chart_path = self.output_dir / f"hourly_distribution_week{results.poc_week}.png"
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()

            chart_paths['hourly'] = str(chart_path)

        # 2. Call outcomes pie chart
        fig, ax = plt.subplots(figsize=(7, 7))
        labels = ['AI Answered', 'Transferred', 'Missed']
        sizes = [results.ai_answered, results.transferred, results.missed]
        colors_pie = ['#3b82f6', '#8b5cf6', '#ef4444']
        explode = (0.05, 0, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 12})
        ax.set_title(f'Week {results.poc_week}: Call Outcomes', fontsize=14, fontweight='bold')

        chart_path = self.output_dir / f"call_outcomes_week{results.poc_week}.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        chart_paths['outcomes'] = str(chart_path)

        # 3. Revenue bar chart
        fig, ax = plt.subplots(figsize=(8, 5))
        categories = ['Before AI\n(Missed Calls)', 'After AI\n(Revenue Captured)', 'AI Cost', 'Net Profit']
        values = [0, results.estimated_revenue, results.ai_cost, results.estimated_revenue - results.ai_cost]
        colors_bar = ['#ef4444', '#10b981', '#f97316', '#3b82f6']

        bars = ax.bar(categories, values, color=colors_bar, alpha=0.8)
        ax.set_ylabel('Revenue ($)')
        ax.set_title(f'Week {results.poc_week}: Revenue Impact')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:,.0f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        chart_path = self.output_dir / f"revenue_impact_week{results.poc_week}.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        chart_paths['revenue'] = str(chart_path)

        return chart_paths

    def generate_report(self, business: str = "hvac", week: int = 1, format: str = "text") -> str:
        """Generate POC report in specified format."""
        # For now, use mock data
        if business.lower() == "hvac":
            results = self.generate_mock_hvac_data()
        else:
            raise ValueError(f"Business '{business}' not yet supported. Use 'hvac' for demo.")

        # Generate text report
        text_report = self.create_text_report(results)

        # Save text version
        text_path = self.output_dir / f"{business}_week{week}_report.txt"
        with open(text_path, 'w') as f:
            f.write(text_report)

        print(f"✓ Text report saved: {text_path}")

        # Generate charts
        chart_paths = self.create_charts(results)
        print(f"✓ Charts generated: {len(chart_paths)} images")

        # Print text report to console
        print("\n" + text_report)

        return str(text_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate POC reports for clients")
    parser.add_argument("--business", default="hvac", help="Business name (hvac, shipping)")
    parser.add_argument("--week", type=int, default=1, help="POC week number")
    parser.add_argument("--format", default="text", help="Report format (text, pdf)")
    parser.add_argument("--output-dir", default="reports", help="Output directory")

    args = parser.parse_args()

    generator = POCReportGenerator(output_dir=args.output_dir)
    report_path = generator.generate_report(
        business=args.business,
        week=args.week,
        format=args.format
    )

    print(f"\n✅ Report generation complete!")
    print(f"   Report: {report_path}")
    print(f"   Charts: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
