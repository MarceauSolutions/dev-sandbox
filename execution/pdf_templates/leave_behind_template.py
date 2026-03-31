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

    Sales-driven layout: pain → solution → tiered value → risk reversal → CTA.

    Expected data keys (all optional — sensible defaults provided):
        headline (str): Main pain-focused headline
        subhead (str): Agitation line
        pain_points (list[str]): 3-4 pain bullets
        tiers (list[dict]): Each with "name", "outcome", "includes" (list), "price", "setup"
        guarantee (str): Risk reversal statement
        qr_url (str): URL for QR code
        contact (dict): "email", "phone", "website"
    """
    story = []

    # --- Pain-Focused Headline ---
    story.append(Spacer(1, 0.1 * inch))

    headline = data.get("headline",
        "How Many Customers Called You This Week<br/>and Never Heard Back?")
    title_style = ParagraphStyle(
        "LBTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=17, leading=21, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=3,
    )
    story.append(Paragraph(headline, title_style))
    story.append(accent_line())

    # --- Agitate the Pain ---
    subhead = data.get("subhead",
        "If you're like most local businesses, the answer is: you don't know. "
        "And that's the problem.")
    sub_style = ParagraphStyle(
        "LBSub", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=13, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph(subhead, sub_style))

    pain_points = data.get("pain_points", [
        "Missed calls go to voicemail — and voicemails don't get returned",
        "Leads come in from 5 different places — nobody tracks them all",
        "You're too busy doing the work to chase down new customers",
        "By the time you follow up, they already called your competitor",
    ])
    pain_style = ParagraphStyle(
        "LBPain", fontName=BrandConfig.BODY_FONT,
        fontSize=9, leading=12, textColor=BrandConfig.CHARCOAL,
        alignment=TA_LEFT, leftIndent=36, spaceAfter=2,
    )
    for pain in pain_points:
        story.append(Paragraph(f"\u2717  {pain}", pain_style))

    story.append(Spacer(1, 0.08 * inch))

    # --- Solution Bridge ---
    bridge = data.get("bridge",
        "We fix this. Not with another app you have to check — with an AI-powered "
        "system that answers your phone, talks to your customers, follows up on "
        "every lead, and manages your entire sales pipeline. You focus on the work. "
        "The system handles everything else.")
    bridge_style = ParagraphStyle(
        "LBBridge", fontName=BrandConfig.HEADING_FONT,
        fontSize=9.5, leading=13, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph(bridge, bridge_style))
    story.append(Spacer(1, 0.03 * inch))

    # --- 3-Tier Value Stack ---
    tiers = data.get("tiers", [
        {
            "name": "Starter",
            "outcome": "Never miss a call again",
            "includes": [
                "Instant text-back on every missed call",
                "After-hours call answering + routing",
                "Automated 5-star review requests",
            ],
            "price": "$297/mo",
            "setup": "$500 one-time setup",
        },
        {
            "name": "Growth",
            "outcome": "An AI employee that works 24/7",
            "includes": [
                "Everything in Starter, plus:",
                "AI agent trained on YOUR services, pricing, and FAQs",
                "Books appointments and qualifies leads before they reach you",
            ],
            "price": "$497/mo",
            "setup": "$750 one-time setup",
        },
        {
            "name": "Complete\nSystem",
            "outcome": "Your entire front office — handled",
            "includes": [
                "Everything in Growth, plus:",
                "Full CRM — every lead tracked from first call to close",
                "Automated follow-up sequences so no lead goes cold",
                "Monthly optimization + strategy calls",
            ],
            "price": "$997/mo",
            "setup": "$1,000 one-time setup",
        },
    ])

    tier_rows = []
    bullet_style = ParagraphStyle(
        "TierBullet", fontName=BrandConfig.BODY_FONT,
        fontSize=7.5, leading=10, textColor=BrandConfig.CHARCOAL,
    )
    tier_name_style = ParagraphStyle(
        "TierName", fontName=BrandConfig.HEADING_FONT,
        fontSize=9, leading=11, textColor=BrandConfig.CHARCOAL,
    )
    outcome_style = ParagraphStyle(
        "TierOutcome", fontName=BrandConfig.HEADING_FONT,
        fontSize=7.5, leading=10, textColor=BrandConfig.GOLD,
    )
    tier_price_style = ParagraphStyle(
        "TierPrice", fontName=BrandConfig.HEADING_FONT,
        fontSize=9, leading=12, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER,
    )

    for tier in tiers:
        name_text = f'{tier["name"]}'
        outcome_text = f'<i>{tier.get("outcome", "")}</i>'
        bullets = "<br/>".join(f"\u2022 {item}" for item in tier["includes"])
        setup_text = tier.get("setup", "")
        price_text = f'<b>{tier["price"]}</b><br/><font size=7 color="#94a3b8">{setup_text}</font>'

        # Combine name + outcome in first column
        name_block = (
            f'{name_text}<br/>'
            f'<font name="{BrandConfig.HEADING_FONT}" size=7 color="#C9963C">'
            f'<i>{tier.get("outcome", "")}</i></font>'
        )

        tier_rows.append([
            Paragraph(name_block, tier_name_style),
            Paragraph(bullets, bullet_style),
            Paragraph(price_text, tier_price_style),
        ])

    story.append(branded_table(
        ["Tier", "What's Included", "Investment"],
        tier_rows,
        col_widths=[1.4 * inch, 3.5 * inch, 1.6 * inch],
    ))
    story.append(Spacer(1, 0.08 * inch))

    # --- Risk Reversal ---
    guarantee = data.get("guarantee",
        "FREE 2-WEEK TRIAL  \u2014  We build your system, you test it with real customers. "
        "If it doesn't work for you, you pay nothing. No contracts. Cancel anytime with 30 days notice.")
    guarantee_style = ParagraphStyle(
        "LBGuarantee", fontName=BrandConfig.HEADING_FONT,
        fontSize=9, leading=12, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=2,
        borderWidth=1, borderColor=BrandConfig.GOLD,
        borderPadding=8, backColor=BrandConfig.GOLD_BG,
    )
    story.append(KeepTogether([
        Paragraph(guarantee, guarantee_style),
    ]))
    story.append(Spacer(1, 0.06 * inch))
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
        Paragraph("Ready to Stop Losing Customers?", cta_style),
        Spacer(1, 4),
        Paragraph(
            "Call or text me directly. I'll show you exactly how many "
            "customers you're losing — and how we fix it.",
            ParagraphStyle(
                "LBCtaSub", fontName=BrandConfig.BODY_FONT,
                fontSize=9, leading=12, textColor=BrandConfig.CHARCOAL,
                spaceAfter=6,
            )
        ),
        Paragraph(f'<b>William Marceau</b>', contact_style),
        Paragraph(f'{contact.get("phone", "")}  |  {contact.get("email", "")}', contact_style),
        Paragraph(f'{contact.get("website", "")}', contact_style),
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
