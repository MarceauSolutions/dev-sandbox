"""Proposal PDF Template — branded client proposal for AI automation services."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, accent_line, bullet_list, branded_table, coach_note_box
)


@register_template("proposal")
def render_proposal(data: dict, styles: dict):
    """Render a client proposal PDF.

    Expected data keys:
        client_name (str): Contact person's name
        business_name (str): Business name
        industry (str): e.g. "HVAC", "Med Spa", "Restaurant"
        problem_statement (str): Their specific pain point
        solution (str): Which service(s) we're proposing
        solution_details (list[str], optional): Bullet points of what's included
        timeline (str): e.g. "7 days"
        investment (dict): {"setup": str, "monthly": str}
        guarantee (str): The guarantee statement
        next_steps (str): Discovery call link or instructions
        testimonial (dict, optional): {"quote": str, "name": str, "business": str}
    """
    story = []

    # --- Header / Title ---
    story.append(Spacer(1, 0.3 * inch))

    # "PROPOSAL" label
    proposal_label = ParagraphStyle(
        "ProposalLabel", fontName=BrandConfig.HEADING_FONT,
        fontSize=11, leading=14, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph("PROPOSAL", proposal_label))

    # Title: "AI Automation for {business_name}"
    business_name = data.get("business_name", "Your Business")
    title_text = f"AI Automation for {business_name}"
    title_style = ParagraphStyle(
        "ProposalTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=22, leading=28, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph(title_text, title_style))

    # Prepared for line
    client_name = data.get("client_name", "")
    if client_name:
        prepared_for = f"Prepared for {client_name}"
        story.append(Paragraph(prepared_for, ParagraphStyle(
            "PreparedFor", fontName=BrandConfig.BODY_FONT,
            fontSize=11, leading=14, textColor=BrandConfig.DARK_GRAY,
            alignment=TA_CENTER, spaceAfter=4,
        )))

    industry = data.get("industry", "")
    if industry:
        story.append(Paragraph(industry, ParagraphStyle(
            "Industry", fontName=BrandConfig.BODY_FONT,
            fontSize=9, leading=12, textColor=BrandConfig.TEXT_MUTED,
            alignment=TA_CENTER,
        )))

    story.append(Spacer(1, 0.2 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 0.1 * inch))

    # --- The Problem ---
    problem = data.get("problem_statement", "")
    if problem:
        story.append(section_title("The Problem", styles))
        story.append(Paragraph(problem, styles["body"]))
        story.append(Spacer(1, 12))

    # --- The Solution ---
    solution = data.get("solution", "")
    if solution:
        story.append(section_title("The Solution", styles))
        story.append(Paragraph(solution, styles["body"]))
        story.append(Spacer(1, 8))

    solution_details = data.get("solution_details", [])
    if solution_details:
        story.append(Paragraph("What's included:", styles["body_bold"]))
        story.append(Spacer(1, 4))
        story.extend(bullet_list(solution_details, styles))
        story.append(Spacer(1, 12))

    # --- Timeline ---
    timeline = data.get("timeline", "7 days")
    story.append(section_title("Timeline", styles))
    timeline_data = [
        ["Day 1", "Kickoff call — gather access credentials and requirements"],
        ["Days 2-5", "System build, integration, and testing"],
        ["Day 6", "Review walkthrough with you"],
        [f"Day 7", "Go live + monitoring begins"],
    ]
    # Allow custom timeline steps
    custom_timeline = data.get("timeline_steps")
    if custom_timeline:
        timeline_data = [[step["when"], step["what"]] for step in custom_timeline]

    story.append(branded_table(
        ["When", "What Happens"],
        timeline_data,
        col_widths=[1.2 * inch, 5.3 * inch]
    ))
    story.append(Spacer(1, 12))

    # --- Investment ---
    investment = data.get("investment", {})
    story.append(section_title("Investment", styles))

    setup = investment.get("setup", "")
    monthly = investment.get("monthly", "")
    inv_rows = []
    if setup:
        inv_rows.append(["One-Time Setup", setup])
    if monthly:
        inv_rows.append(["Monthly Management", monthly])

    if inv_rows:
        story.append(branded_table(
            ["Item", "Amount"],
            inv_rows,
            col_widths=[3.25 * inch, 3.25 * inch]
        ))
        story.append(Spacer(1, 8))

    # --- Guarantee ---
    guarantee = data.get("guarantee", "")
    if guarantee:
        story.append(section_title("Our Guarantee", styles))
        # Render as a gold-bordered highlight box
        guarantee_data = [[Paragraph(
            f'<b>{guarantee}</b>', styles["body_bold"]
        )]]
        t = Table(guarantee_data, colWidths=[6.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
            ("BOX", (0, 0), (-1, -1), 2, BrandConfig.GOLD),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # --- Testimonial (optional) ---
    testimonial = data.get("testimonial")
    if testimonial:
        story.append(Spacer(1, 8))
        quote_style = ParagraphStyle(
            "Quote", fontName=BrandConfig.BODY_FONT,
            fontSize=10, leading=15, textColor=BrandConfig.CHARCOAL,
            leftIndent=20, rightIndent=20,
        )
        story.append(Paragraph(
            f'<i>"{testimonial.get("quote", "")}"</i>', quote_style
        ))
        story.append(Paragraph(
            f'— {testimonial.get("name", "")}, {testimonial.get("business", "")}',
            ParagraphStyle("QuoteAttr", fontName=BrandConfig.BODY_FONT_BOLD,
                           fontSize=9, leading=12, textColor=BrandConfig.GOLD,
                           leftIndent=20, spaceBefore=4)
        ))
        story.append(Spacer(1, 12))

    # --- Next Steps ---
    next_steps = data.get("next_steps", "")
    if next_steps:
        story.append(section_title("Next Steps", styles))
        story.append(Paragraph(next_steps, styles["body"]))
        story.append(Spacer(1, 8))

    # --- Contact Footer ---
    story.append(Spacer(1, 0.2 * inch))
    story.append(accent_line())
    contact_style = ParagraphStyle(
        "ContactCenter", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=14, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "William Marceau | Marceau Solutions", styles["center_bold"]
    ))
    story.append(Paragraph(
        "wmarceau@marceausolutions.com | marceausolutions.com | (239) 398-5676",
        contact_style
    ))

    return story
