"""Agreement PDF Template — branded service agreement for AI services clients."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle, HRFlowable

from branded_pdf_engine import (
    register_template, BrandConfig, get_brand_styles,
    section_title, accent_line, bullet_list
)


@register_template("agreement")
def render_agreement(data: dict, styles: dict):
    """Render a service agreement PDF.

    Expected data keys:
        client_business_name (str): Client's business name
        client_owner_name (str): Client contact / owner name
        effective_date (str): e.g. "March 23, 2026"
        setup_fee (str, optional): e.g. "$500" or "$0"
        monthly_rate (str): e.g. "$497/month"
        tier_name (str, optional): e.g. "Tier 1 — Starter"
        client_title (str, optional): e.g. "Owner" — defaults to "Owner"
    """
    story = []

    client_business = data.get("client_business_name", "[CLIENT_BUSINESS_NAME]")
    client_owner = data.get("client_owner_name", "[CLIENT_OWNER_NAME]")
    effective_date = data.get("effective_date", "[EFFECTIVE_DATE]")
    setup_fee = data.get("setup_fee", "$0")
    monthly_rate = data.get("monthly_rate", "[MONTHLY_RATE]")
    tier_name = data.get("tier_name", "")
    client_title = data.get("client_title", "Owner")

    # -------------------------
    # Title block
    # -------------------------
    story.append(Spacer(1, 0.25 * inch))

    label_style = ParagraphStyle(
        "AgreementLabel", fontName=BrandConfig.HEADING_FONT,
        fontSize=10, leading=13, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph("SERVICE AGREEMENT", label_style))

    title_style = ParagraphStyle(
        "AgreementTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=20, leading=26, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=6,
    )
    story.append(Paragraph("AI Services Agreement", title_style))

    sub_style = ParagraphStyle(
        "AgreementSub", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=14, textColor=BrandConfig.DARK_GRAY,
        alignment=TA_CENTER, spaceAfter=4,
    )
    story.append(Paragraph(f"Marceau Solutions  ·  {client_business}", sub_style))
    story.append(Paragraph(f"Effective Date: {effective_date}", ParagraphStyle(
        "EffDate", fontName=BrandConfig.BODY_FONT,
        fontSize=9, leading=12, textColor=BrandConfig.TEXT_MUTED,
        alignment=TA_CENTER,
    )))

    story.append(Spacer(1, 0.15 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 0.05 * inch))

    # -------------------------
    # Parties box
    # -------------------------
    parties_data = [
        [
            Paragraph("<b>Service Provider</b>", ParagraphStyle(
                "PartyLabel", fontName=BrandConfig.BODY_FONT_BOLD, fontSize=9,
                textColor=BrandConfig.GOLD, leading=12
            )),
            Paragraph("<b>Client</b>", ParagraphStyle(
                "PartyLabel2", fontName=BrandConfig.BODY_FONT_BOLD, fontSize=9,
                textColor=BrandConfig.GOLD, leading=12
            )),
        ],
        [
            Paragraph(
                "William Marceau<br/>Marceau Solutions<br/>Naples, FL<br/>"
                "wmarceau@marceausolutions.com<br/>(239) 398-5676",
                ParagraphStyle("PartyBody", fontName=BrandConfig.BODY_FONT,
                               fontSize=9, leading=13, textColor=BrandConfig.CHARCOAL)
            ),
            Paragraph(
                f"{client_owner}<br/>{client_title}<br/>{client_business}",
                ParagraphStyle("PartyBody2", fontName=BrandConfig.BODY_FONT,
                               fontSize=9, leading=13, textColor=BrandConfig.CHARCOAL)
            ),
        ]
    ]
    parties_table = Table(parties_data, colWidths=[3.25 * inch, 3.25 * inch])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("BACKGROUND", (0, 1), (-1, 1), BrandConfig.LIGHT_GRAY),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("BOX", (0, 0), (-1, -1), 1, BrandConfig.MID_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BrandConfig.MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.2 * inch))

    # -------------------------
    # Section 1 — Services
    # -------------------------
    story.append(section_title("1. Services", styles))
    story.append(Paragraph(
        "Marceau Solutions agrees to provide the following services:", styles["body"]
    ))
    story.append(Spacer(1, 6))
    story.extend(bullet_list([
        "<b>AI Phone & Text Intake System</b> — AI-powered assistant handling inbound calls and texts, qualifying leads, and capturing customer info 24/7.",
        "<b>Automated Follow-Up Sequences</b> — Automated SMS and email follow-up with leads and customers.",
        "<b>Monthly Optimization</b> — Ongoing prompt tuning, workflow adjustments, and performance reporting.",
    ], styles))
    if tier_name:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Selected Package: <b>{tier_name}</b>", styles["body"]))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 2 — Free Trial
    # -------------------------
    story.append(section_title("2. Free Trial Period", styles))

    trial_box_data = [[Paragraph(
        "<b>The first two (2) weeks are completely free.</b> Client owes nothing during this period. "
        "At the end of the trial, Client may cancel with no obligation — or continue on the selected monthly plan. "
        "Billing begins only if Client chooses to continue.",
        styles["body"]
    )]]
    trial_table = Table(trial_box_data, colWidths=[6.5 * inch])
    trial_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 2, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(trial_table)
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 3 — Fees & Payment
    # -------------------------
    story.append(section_title("3. Fees and Payment", styles))
    fee_rows = []
    if setup_fee and setup_fee != "$0":
        fee_rows.append(["One-Time Setup Fee", setup_fee, "Due upon signing"])
    fee_rows.append(["Monthly Subscription", monthly_rate, "Billed same calendar day each month, starting after trial"])
    fee_rows.append(["Payment Method", "Stripe", "Card on file — auto-billed"])

    story.append(_payment_table(fee_rows))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Accounts more than 7 days past due may result in service suspension.",
        styles["small"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 4 — Cancellation
    # -------------------------
    story.append(section_title("4. Cancellation", styles))
    story.append(Paragraph(
        "After the free trial period, either party may cancel with <b>30 days written notice</b> "
        "sent via email. Client's notice goes to wmarceau@marceausolutions.com. "
        "Billing stops at the end of the current billing period after the 30-day notice has run. "
        "No partial refunds for unused days within the notice period. "
        "Client retains all their customer data upon cancellation.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 5 — Intellectual Property
    # -------------------------
    story.append(section_title("5. Intellectual Property", styles))
    story.append(Paragraph(
        "<b>Marceau Solutions' Systems:</b> The AI infrastructure, automation frameworks, and "
        "technical systems remain the sole property of Marceau Solutions. Client receives a "
        "license to use these systems during the active term of this agreement.",
        styles["body"]
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "<b>Client's Data:</b> All customer data, contact lists, call records, and business "
        "information belong exclusively to Client. Marceau Solutions will not use, sell, or "
        "share Client's customer data.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 6 — Confidentiality
    # -------------------------
    story.append(section_title("6. Confidentiality", styles))
    story.append(Paragraph(
        "Both parties agree to keep the other's business information confidential — including "
        "pricing, strategies, customer data, and system details. Neither party will share the "
        "other's confidential information with third parties without written consent, except as "
        "required by law. This obligation survives termination for two (2) years.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 7 — Limitation of Liability
    # -------------------------
    story.append(section_title("7. Limitation of Liability", styles))
    story.append(Paragraph(
        "Marceau Solutions' total liability under this agreement shall not exceed the fees paid "
        "by Client in the <b>three (3) months</b> immediately preceding the event giving rise to "
        "the claim. Marceau Solutions is not liable for indirect or consequential damages, lost "
        "profits, or downtime caused by third-party platforms (Twilio, Stripe, etc.).",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 8 — No Guarantees
    # -------------------------
    story.append(section_title("8. No Guarantees of Results", styles))
    story.append(Paragraph(
        "Marceau Solutions will build and maintain a professional AI system. Results — including "
        "leads captured, conversion rates, and revenue — depend on factors outside Marceau "
        "Solutions' control. No specific business outcomes are guaranteed.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 9 — Governing Law
    # -------------------------
    story.append(section_title("9. Governing Law", styles))
    story.append(Paragraph(
        "This agreement is governed by the laws of the State of Florida. Any disputes will be "
        "resolved in Collier County, Florida.",
        styles["body"]
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Section 10 — Acceptance
    # -------------------------
    story.append(section_title("10. Acceptance", styles))
    story.append(Paragraph(
        "Client's agreement is confirmed by either: (a) payment of the setup fee via Stripe, "
        "or (b) written email confirmation from Client's email address. No physical signature "
        "is required. Email confirmation constitutes a binding agreement.",
        styles["body"]
    ))
    story.append(Spacer(1, 14))

    # -------------------------
    # Signatures
    # -------------------------
    story.append(accent_line())
    story.append(Spacer(1, 0.1 * inch))

    sig_header = ParagraphStyle(
        "SigHeader", fontName=BrandConfig.HEADING_FONT,
        fontSize=13, leading=18, textColor=BrandConfig.CHARCOAL,
        spaceAfter=10,
    )
    story.append(Paragraph("Signatures", sig_header))

    sig_data = [
        [
            Paragraph("<b>Marceau Solutions</b>", styles["body_bold"]),
            Paragraph(f"<b>{client_business}</b>", styles["body_bold"]),
        ],
        [
            Paragraph(
                "Signature: ________________________________<br/><br/>"
                "William Marceau | Marceau Solutions<br/>"
                "Naples, FL<br/><br/>"
                "Date: ________________________________",
                ParagraphStyle("SigBlock", fontName=BrandConfig.BODY_FONT,
                               fontSize=9, leading=15, textColor=BrandConfig.CHARCOAL)
            ),
            Paragraph(
                f"Signature: ________________________________<br/><br/>"
                f"{client_owner} | {client_title}<br/>"
                f"{client_business}<br/><br/>"
                f"Date: ________________________________",
                ParagraphStyle("SigBlock2", fontName=BrandConfig.BODY_FONT,
                               fontSize=9, leading=15, textColor=BrandConfig.CHARCOAL)
            ),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.25 * inch, 3.25 * inch])
    sig_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, 1), 16),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 16),
        ("BOX", (0, 0), (-1, -1), 1, BrandConfig.MID_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BrandConfig.MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph(
        "Questions? Contact William Marceau at wmarceau@marceausolutions.com or (239) 398-5676.",
        styles["small"]
    ))

    return story


def _payment_table(rows):
    """Small 3-column payment details table."""
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle
    from branded_pdf_engine import BrandConfig, get_brand_styles
    from reportlab.lib.styles import ParagraphStyle

    styles = get_brand_styles()
    header_paras = [
        Paragraph("<b>Item</b>", ParagraphStyle("TH", fontName=BrandConfig.BODY_FONT_BOLD,
                                                fontSize=9, textColor=BrandConfig.GOLD_LIGHT, leading=12)),
        Paragraph("<b>Amount</b>", ParagraphStyle("TH2", fontName=BrandConfig.BODY_FONT_BOLD,
                                                  fontSize=9, textColor=BrandConfig.GOLD_LIGHT, leading=12)),
        Paragraph("<b>Notes</b>", ParagraphStyle("TH3", fontName=BrandConfig.BODY_FONT_BOLD,
                                                 fontSize=9, textColor=BrandConfig.GOLD_LIGHT, leading=12)),
    ]
    body = []
    for i, row in enumerate(rows):
        bg = BrandConfig.WHITE if i % 2 == 0 else BrandConfig.LIGHT_GRAY
        body.append([
            Paragraph(str(row[0]), styles["body"]),
            Paragraph(str(row[1]), styles["body_bold"]),
            Paragraph(str(row[2]), styles["body"]),
        ])

    data = [header_paras] + body
    t = Table(data, colWidths=[2.0 * inch, 1.5 * inch, 3.0 * inch])
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BrandConfig.MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(1, len(data)):
        bg = BrandConfig.WHITE if i % 2 == 1 else BrandConfig.LIGHT_GRAY
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t
