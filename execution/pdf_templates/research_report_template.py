"""Research Report PDF Template — branded research/clinical document for William Marceau."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    Spacer, Paragraph, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.colors import HexColor

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, accent_line, bullet_list, branded_table, coach_note_box
)


def _info_box(label, value_lines, styles):
    """Gold-bordered info callout box."""
    content = f"<b>{label}</b><br/>" + "<br/>".join(value_lines)
    data = [[Paragraph(content, styles["body"])]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 2, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def _highlight_box(text, styles, gold_border=True):
    """Highlighted text box for key recommendations or warnings."""
    data = [[Paragraph(text, styles["body_bold"])]]
    t = Table(data, colWidths=[6.5 * inch])
    border_color = BrandConfig.GOLD if gold_border else BrandConfig.CHARCOAL
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 2.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def _disclaimer_box(text, styles):
    """Charcoal-bordered disclaimer box."""
    disclaimer_style = ParagraphStyle(
        "DisclaimerBox", fontName=BrandConfig.BODY_FONT,
        fontSize=8.5, leading=12, textColor=HexColor("#555555"),
    )
    data = [[Paragraph(text, disclaimer_style)]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8f8f8")),
        ("BOX", (0, 0), (-1, -1), 1.5, BrandConfig.CHARCOAL),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return t


def _sub_heading(text, styles):
    """Gold sub-section heading (h3 equivalent)."""
    return Paragraph(text, styles["h3"])


def _body(text, styles):
    return Paragraph(text, styles["body"])


def _body_bold(text, styles):
    return Paragraph(text, styles["body_bold"])


def _bullets(items, styles, indent=20):
    return bullet_list(items, styles, indent=indent)


@register_template("research_report")
def render_research_report(data: dict, styles: dict):
    """Render a professional research/clinical report PDF.

    Expected data keys:
        title (str)
        subtitle (str)
        date (str)
        prepared_for (str)
        executive_summary (str)
        primary_recommendation (str)
        sections (list[dict]): Each section has:
            heading (str)
            subsections (list[dict]): Each with:
                subheading (str, optional)
                body (str, optional)
                bullets (list[str], optional)
                highlight (str, optional)   -- gold box callout
                info_box (dict, optional)   -- {"label": ..., "lines": [...]}
                table (dict, optional)      -- {"headers": [...], "rows": [...], "col_widths": [...]}
                disclaimer (str, optional)
        disclaimer (str): Final disclaimer text
    """
    story = []

    # --- Cover / Title Block ---
    story.append(Spacer(1, 0.3 * inch))

    # Document type label
    label_style = ParagraphStyle(
        "ReportLabel", fontName=BrandConfig.HEADING_FONT,
        fontSize=10, leading=13, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph("RESEARCH REPORT", label_style))

    # Main title
    title_style = ParagraphStyle(
        "ReportTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=20, leading=26, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph(data.get("title", "Research Report"), title_style))

    # Subtitle
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", fontName=BrandConfig.BODY_FONT,
        fontSize=12, leading=16, textColor=BrandConfig.DARK_GRAY,
        alignment=TA_CENTER, spaceAfter=8,
    )
    story.append(Paragraph(data.get("subtitle", ""), subtitle_style))

    # Meta row: prepared for + date
    meta_style = ParagraphStyle(
        "ReportMeta", fontName=BrandConfig.BODY_FONT,
        fontSize=9, leading=13, textColor=BrandConfig.TEXT_MUTED,
        alignment=TA_CENTER, spaceAfter=4,
    )
    prepared_for = data.get("prepared_for", "")
    date_str = data.get("date", "")
    if prepared_for or date_str:
        meta_parts = []
        if prepared_for:
            meta_parts.append(f"Prepared for: {prepared_for}")
        if date_str:
            meta_parts.append(f"Date: {date_str}")
        story.append(Paragraph("  |  ".join(meta_parts), meta_style))

    story.append(Spacer(1, 0.15 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 0.15 * inch))

    # --- Executive Summary ---
    exec_summary = data.get("executive_summary", "")
    if exec_summary:
        story.append(section_title("Executive Summary", styles))
        story.append(_body(exec_summary, styles))
        story.append(Spacer(1, 8))

    # Primary recommendation callout
    primary_rec = data.get("primary_recommendation", "")
    if primary_rec:
        story.append(Spacer(1, 4))
        story.append(_highlight_box(f"Primary Recommendation: {primary_rec}", styles))
        story.append(Spacer(1, 12))

    # --- Sections ---
    for section in data.get("sections", []):
        heading = section.get("heading", "")
        if heading:
            story.append(section_title(heading, styles))

        for sub in section.get("subsections", []):
            subheading = sub.get("subheading", "")
            if subheading:
                story.append(_sub_heading(subheading, styles))

            body_text = sub.get("body", "")
            if body_text:
                story.append(_body(body_text, styles))
                story.append(Spacer(1, 6))

            bullets = sub.get("bullets", [])
            if bullets:
                story.extend(_bullets(bullets, styles))
                story.append(Spacer(1, 6))

            highlight = sub.get("highlight", "")
            if highlight:
                story.append(Spacer(1, 4))
                story.append(_highlight_box(highlight, styles))
                story.append(Spacer(1, 8))

            info_box_data = sub.get("info_box")
            if info_box_data:
                story.append(Spacer(1, 4))
                story.append(_info_box(
                    info_box_data.get("label", ""),
                    info_box_data.get("lines", []),
                    styles
                ))
                story.append(Spacer(1, 8))

            table_data = sub.get("table")
            if table_data:
                headers = table_data.get("headers", [])
                rows = table_data.get("rows", [])
                col_widths_raw = table_data.get("col_widths")
                col_widths = [w * inch for w in col_widths_raw] if col_widths_raw else None
                story.append(branded_table(headers, rows, col_widths=col_widths))
                story.append(Spacer(1, 10))

            disclaimer_text = sub.get("disclaimer", "")
            if disclaimer_text:
                story.append(Spacer(1, 4))
                story.append(_disclaimer_box(disclaimer_text, styles))
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 6))

    # --- Final Disclaimer ---
    final_disclaimer = data.get("disclaimer", "")
    if final_disclaimer:
        story.append(Spacer(1, 0.2 * inch))
        story.append(accent_line())
        story.append(_disclaimer_box(final_disclaimer, styles))
        story.append(Spacer(1, 12))

    # --- Contact Footer ---
    story.append(Spacer(1, 0.1 * inch))
    story.append(accent_line())
    story.append(Paragraph(
        "Marceau Solutions  |  wmarceau@marceausolutions.com  |  (239) 398-5676  |  marceausolutions.com",
        ParagraphStyle(
            "FooterContact", fontName=BrandConfig.BODY_FONT,
            fontSize=8, leading=11, textColor=BrandConfig.DARK_GRAY,
            alignment=TA_CENTER,
        )
    ))
    story.append(Paragraph(
        "Embrace the Pain & Defy the Odds",
        ParagraphStyle(
            "FooterTagline", fontName=BrandConfig.HEADING_FONT,
            fontSize=7, leading=10, textColor=BrandConfig.GOLD,
            alignment=TA_CENTER, spaceBefore=3,
        )
    ))

    return story
