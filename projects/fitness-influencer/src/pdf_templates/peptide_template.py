"""Peptide Education Guide PDF Template."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, coach_note_box, branded_table, bullet_list, HexColor
)

EVIDENCE_COLORS = {
    "Strong": "#C9963C",
    "Moderate": "#D4AF37",
    "Emerging": "#3b82f6",
    "Weak": "#ef4444",
}


@register_template("peptide_guide")
def render_peptide(data: dict, styles: dict):
    story = []

    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(data.get("title", "Evidence-Based Peptide Guide"), styles["title"]))
    if data.get("client_name"):
        story.append(Paragraph(
            f'Prepared for <b>{data["client_name"]}</b>', styles["subtitle"]
        ))

    # Intro
    intro = data.get("intro_text", "")
    if intro:
        story.append(Paragraph(intro, styles["body"]))
        story.append(Spacer(1, 12))

    # Coach note
    if data.get("coach_note"):
        story.append(coach_note_box(data["coach_note"], styles))
        story.append(Spacer(1, 12))

    # Evidence Rating Legend
    story.append(section_title("Evidence Rating Scale", styles))
    legend_data = []
    for rating, color in EVIDENCE_COLORS.items():
        legend_data.append([
            Paragraph(f'<font color="{color}"><b>{rating}</b></font>', styles["body"]),
            Paragraph({
                "Strong": "FDA-approved, extensive clinical data",
                "Moderate": "Clinical studies, physician-supervised use",
                "Emerging": "Animal studies, limited human data",
                "Weak": "Anecdotal only, minimal research",
            }.get(rating, ""), styles["body"]),
        ])
    legend = Table(legend_data, colWidths=[1.5 * inch, 5.0 * inch])
    legend.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BrandConfig.MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(legend)
    story.append(Spacer(1, 16))

    # Compound profiles
    compounds = data.get("compounds", [])
    if compounds:
        story.append(section_title("Compound Profiles", styles))

        for compound in compounds:
            name = compound.get("name", "Unknown")
            category = compound.get("category", "")
            rating = compound.get("evidence_rating", "Moderate")
            color = EVIDENCE_COLORS.get(rating, "#64748b")

            # Compound header card
            header_data = [[
                Paragraph(f'<b>{name}</b>', ParagraphStyle(
                    "CompName", fontName=BrandConfig.HEADING_FONT,
                    fontSize=13, textColor=BrandConfig.CHARCOAL, leading=18
                )),
                Paragraph(f'<font color="{color}"><b>{rating}</b></font>', ParagraphStyle(
                    "CompRating", fontName=BrandConfig.BODY_FONT_BOLD,
                    fontSize=10, textColor=HexColor(color), leading=14
                )),
            ]]
            if category:
                header_data.append([
                    Paragraph(f'<i>{category}</i>', styles["small"]),
                    Paragraph("", styles["small"]),
                ])

            header_table = Table(header_data, colWidths=[4.5 * inch, 2.0 * inch])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.LIGHT_GRAY),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(header_table)

            # Mechanism
            mechanism = compound.get("mechanism", "")
            if mechanism:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<b>How it works:</b> {mechanism}", styles["body"]))

            # Benefits
            benefits = compound.get("benefits", [])
            if benefits:
                story.append(Spacer(1, 4))
                story.append(Paragraph("<b>Benefits:</b>", styles["body"]))
                story.extend(bullet_list(benefits, styles))

            # Side effects
            sides = compound.get("side_effects", [])
            if sides:
                story.append(Spacer(1, 4))
                story.append(Paragraph("<b>Potential Side Effects:</b>", styles["body"]))
                story.extend(bullet_list(sides, styles))

            # Notes
            if compound.get("notes"):
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<i>{compound['notes']}</i>", styles["small"]))

            story.append(Spacer(1, 16))

    # Decision framework
    framework = data.get("decision_framework")
    if framework:
        story.append(section_title("Is This Right for You?", styles))

        consider = framework.get("consider_if", [])
        hold_off = framework.get("hold_off_if", [])

        if consider or hold_off:
            col1 = []
            col2 = []

            if consider:
                col1.append(Paragraph('<font color="#C9963C"><b>Consider if...</b></font>', styles["body"]))
                for item in consider:
                    col1.append(Paragraph(f'<font color="#C9963C">&#10003;</font> {item}', styles["body"]))

            if hold_off:
                col2.append(Paragraph('<font color="#ef4444"><b>Hold off if...</b></font>', styles["body"]))
                for item in hold_off:
                    col2.append(Paragraph(f'<font color="#ef4444">&#10007;</font> {item}', styles["body"]))

            # Two-column layout
            row_data = [[col1, col2]]
            two_col = Table(row_data, colWidths=[3.25 * inch, 3.25 * inch])
            two_col.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(two_col)
            story.append(Spacer(1, 16))

    # Disclaimer
    disclaimer = data.get("disclaimer", "")
    if disclaimer:
        story.append(Spacer(1, 16))
        disc_data = [[Paragraph(f"<b>MEDICAL DISCLAIMER</b><br/>{disclaimer}", styles["disclaimer"])]]
        disc_table = Table(disc_data, colWidths=[6.5 * inch])
        disc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, BrandConfig.RED),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(disc_table)

    return story
