"""Onboarding Packet PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle, PageBreak

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, coach_note_box, branded_table, bullet_list, HexColor
)


@register_template("onboarding_packet")
def render_onboarding(data: dict, styles: dict):
    story = []

    client = data.get("client_name", "Client")
    coach = data.get("coach_name", "William Marceau")

    # Welcome page
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Welcome to Coaching", styles["title"]))
    story.append(Paragraph(f'<b>{client}</b>, let\'s get started.', styles["subtitle"]))
    story.append(Spacer(1, 0.3 * inch))

    welcome = data.get("welcome_message", "")
    if welcome:
        story.append(Paragraph(welcome, styles["body"]))
        story.append(Spacer(1, 12))

    if data.get("start_date"):
        story.append(Paragraph(f"<b>Start Date:</b> {data['start_date']}", styles["body"]))
        story.append(Paragraph(f"<b>Your Coach:</b> {coach}", styles["body"]))

    story.append(PageBreak())

    # What to expect
    expectations = data.get("what_to_expect", [])
    if expectations:
        story.append(section_title("What to Expect", styles))
        for i, item in enumerate(expectations, 1):
            story.append(Paragraph(f"<b>{i}.</b> {item}", styles["body"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 12))

    # Communication guidelines
    comm = data.get("communication_guidelines")
    if comm:
        story.append(section_title("Communication Guidelines", styles))
        headers = ["Topic", "Details"]
        rows = [[k.replace("_", " ").title(), v] for k, v in comm.items()]
        story.append(branded_table(headers, rows, col_widths=[2.0 * inch, 4.5 * inch]))
        story.append(Spacer(1, 16))

    # Weekly schedule
    schedule = data.get("weekly_schedule")
    if schedule:
        story.append(section_title("Your Weekly Schedule", styles))
        headers = ["Day", "What Happens"]
        rows = [[day, activity] for day, activity in schedule.items()]
        story.append(branded_table(headers, rows, col_widths=[1.5 * inch, 5.0 * inch]))
        story.append(Spacer(1, 16))

    # App / setup steps
    steps = data.get("app_setup_steps", [])
    if steps:
        story.append(section_title("Getting Set Up", styles))
        for i, step in enumerate(steps, 1):
            num_style = ParagraphStyle(
                "StepNum", parent=styles["body"],
                leftIndent=24, bulletIndent=0,
            )
            story.append(Paragraph(
                f'<font color="#C9963C"><b>Step {i}:</b></font> {step}', num_style
            ))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 12))

    # FAQ
    faq = data.get("faq", [])
    if faq:
        story.append(section_title("Frequently Asked Questions", styles))
        for item in faq:
            q = item.get("q", "")
            a = item.get("a", "")
            # Question row
            q_data = [[Paragraph(f"<b>Q: {q}</b>", styles["body"])]]
            q_table = Table(q_data, colWidths=[6.5 * inch])
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.LIGHT_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(q_table)
            # Answer
            story.append(Paragraph(f"<b>A:</b> {a}", styles["body"]))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 8))

    # Important links
    links = data.get("important_links")
    if links:
        story.append(section_title("Important Links", styles))
        headers = ["Resource", "URL"]
        rows = [[k.replace("_", " ").title(), v] for k, v in links.items()]
        story.append(branded_table(headers, rows, col_widths=[2.0 * inch, 4.5 * inch]))

    return story
