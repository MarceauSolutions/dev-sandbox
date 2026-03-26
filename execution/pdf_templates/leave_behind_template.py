"""Leave-Behind PDF Template — one-pager for in-person AI services outreach."""

import sys
from io import BytesIO
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import qrcode
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    Spacer, Paragraph, Table, TableStyle, Image, KeepTogether
)

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    accent_line, branded_table, metric_card
)


def _make_qr_image(url, size=1.3 * inch):
    """Generate a QR code image flowable from a URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#333333", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=size, height=size)


@register_template("leave_behind")
def render_leave_behind(data: dict, styles: dict):
    """Render a one-page leave-behind for in-person AI services outreach.

    Expected data keys (all optional — sensible defaults provided):
        headline (str): Main headline
        value_prop (str): 2-3 sentence value proposition
        services (list[dict]): Each with "name", "features" (list), "price"
        case_study (dict): "title", "metrics" (list of {"label", "value"})
        qr_url (str): URL for QR code (default: marceausolutions.com/ai-automation.html)
        contact (dict): "email", "phone", "website"
    """
    story = []

    # --- Headline ---
    story.append(Spacer(1, 0.15 * inch))

    label_style = ParagraphStyle(
        "LBLabel", fontName=BrandConfig.HEADING_FONT,
        fontSize=10, leading=13, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=2,
    )
    story.append(Paragraph(
        "BUSINESS AUTOMATION FOR LOCAL COMPANIES",
        label_style
    ))

    headline = data.get("headline",
        "Your Leads Are Scattered. Your Follow-Ups Are Falling Through the Cracks.")
    title_style = ParagraphStyle(
        "LBTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=18, leading=22, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph(headline, title_style))
    story.append(accent_line())

    # --- Value Proposition ---
    value_prop = data.get("value_prop",
        "Right now, your leads come in from phone calls, Google, your website, "
        "texts, and referrals — but they all land in different places. Some get "
        "followed up with. Most don't. I connect everything into one system so "
        "every lead gets captured, every follow-up happens automatically, and "
        "you know exactly where every potential customer stands — without adding "
        "anything to your plate.")

    vp_style = ParagraphStyle(
        "LBValueProp", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=14, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=8,
    )
    story.append(Paragraph(value_prop, vp_style))
    story.append(Spacer(1, 0.05 * inch))

    # --- Services Table ---
    services = data.get("services", [
        {
            "name": "Unified Lead Dashboard",
            "features": "All calls, texts, forms, and emails in one place. Know where every lead stands.",
            "price": "Included",
        },
        {
            "name": "Automated Follow-Up",
            "features": "Every missed call gets a text. Every lead gets followed up with. Nothing falls through.",
            "price": "$500-1,000/mo",
        },
        {
            "name": "After-Hours Coverage",
            "features": "Calls answered 24/7. Appointments booked. Emergencies routed to you.",
            "price": "Included",
        },
        {
            "name": "Review & Referral System",
            "features": "Automatically request reviews after service. Build your reputation on autopilot.",
            "price": "Included",
        },
    ])

    service_rows = []
    for svc in services:
        service_rows.append([
            svc["name"],
            svc["features"],
            svc["price"],
        ])

    story.append(branded_table(
        ["Service", "What You Get", "Investment"],
        service_rows,
        col_widths=[1.6 * inch, 3.2 * inch, 1.7 * inch],
    ))
    story.append(Spacer(1, 0.15 * inch))

    # --- Case Study Box ---
    case_study = data.get("case_study", {
        "title": "What Our Clients Stop Worrying About",
        "metrics": [
            {"label": "Missed Calls Captured", "value": "100%"},
            {"label": "Avg Follow-Up Time", "value": "< 60 sec"},
            {"label": "Leads That Get a Reply", "value": "Every One"},
            {"label": "Your Extra Work", "value": "Zero"},
        ],
    })

    # Case study header
    cs_header_style = ParagraphStyle(
        "CSHeader", fontName=BrandConfig.HEADING_FONT,
        fontSize=11, leading=14, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph(
        f'PROOF: {case_study.get("title", "Real Results")}',
        cs_header_style
    ))

    # Metric cards in a row
    metrics = case_study.get("metrics", [])
    if metrics:
        cards = [metric_card(m["label"], m["value"]) for m in metrics]
        card_width = (7.2 / len(cards)) * inch
        metrics_table = Table([cards], colWidths=[card_width] * len(cards))
        metrics_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(metrics_table)

    story.append(Spacer(1, 0.15 * inch))
    story.append(accent_line())

    # --- QR Code + Contact Info (side by side) ---
    qr_url = data.get("qr_url", "https://marceausolutions.com/ai-automation.html")
    qr_img = _make_qr_image(qr_url)

    contact = data.get("contact", {
        "email": "wmarceau@marceausolutions.com",
        "phone": "(855) 239-9364",
        "website": "marceausolutions.com",
    })

    # CTA text
    cta_style = ParagraphStyle(
        "LBCTA", fontName=BrandConfig.HEADING_FONT,
        fontSize=13, leading=17, textColor=BrandConfig.CHARCOAL,
        spaceAfter=6,
    )
    contact_style = ParagraphStyle(
        "LBContact", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=14, textColor=BrandConfig.CHARCOAL,
        spaceAfter=3,
    )
    scan_style = ParagraphStyle(
        "LBScan", fontName=BrandConfig.BODY_FONT,
        fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
        alignment=TA_CENTER,
    )

    # Left column: CTA + contact details
    left_content = [
        Paragraph("Book a Free 15-Minute Discovery Call", cta_style),
        Spacer(1, 4),
        Paragraph(f'<b>Email:</b> {contact.get("email", "")}', contact_style),
        Paragraph(f'<b>Phone:</b> {contact.get("phone", "")}', contact_style),
        Paragraph(f'<b>Web:</b> {contact.get("website", "")}', contact_style),
        Spacer(1, 6),
        Paragraph(
            '<i>"I connect the tools you already use into one system '
            'that makes sure no lead gets left behind."</i>',
            ParagraphStyle(
                "LBTagline", fontName=BrandConfig.BODY_FONT,
                fontSize=9, leading=13, textColor=BrandConfig.GOLD,
            )
        ),
    ]

    # Right column: QR code
    right_content = [
        qr_img,
        Paragraph("Scan to learn more", scan_style),
    ]

    # Build side-by-side layout
    left_table = Table([[item] for item in left_content],
                       colWidths=[4.2 * inch])
    left_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    right_table = Table([[item] for item in right_content],
                        colWidths=[1.8 * inch])
    right_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    layout = Table([[left_table, right_table]],
                   colWidths=[4.5 * inch, 2.0 * inch])
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(layout)

    return story
