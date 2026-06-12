#!/usr/bin/env python3
"""
Propane Fitness - AmEx Dispute: CFPB Complaint Supporting Memorandum (June 11, 2026)
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

Supporting record for CFPB complaint filed against American Express after the
June 9, 2026 decision deadline (committed by Supervisor Michael, HE0973A) passed
with no credit posted. Includes penny-exact reconciliation tying the unrefunded
FX shortfall to the current statement balance.
"""

import os
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)

NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED = HexColor("#c0392b")
GOLD = HexColor("#C9963C")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
ACCENT_BG = HexColor("#f6f8fc")

OUTPUT = os.path.join(
    os.path.dirname(__file__),
    "propane-amex-cfpb-complaint-june11-2026.pdf",
)


def styles():
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=16, leading=22,
            textColor=NAVY, spaceAfter=4, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=10, leading=14,
            textColor=CHARCOAL, spaceAfter=12, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", fontName="Helvetica-Bold", fontSize=12.5, leading=17,
            textColor=NAVY, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9.5, leading=13.5,
            textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5,
            textColor=CHARCOAL, spaceAfter=5,
        ),
        "fact": ParagraphStyle(
            "Fact", fontName="Helvetica", fontSize=10, leading=14,
            textColor=CHARCOAL, leftIndent=18, spaceAfter=4, bulletIndent=4,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=7.5, leading=10,
            textColor=HexColor("#888888"), alignment=TA_CENTER,
        ),
    }


def info_table(rows, col_widths=(1.85 * inch, 4.65 * inch)):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def recon_table():
    data = [
        ["", "Per Card (each)", "Total (both cards)"],
        ["Propane charge (Mar 2, 2026 @ $1.3511/£)", "$4,255.97", "$8,511.94"],
        ["Foreign-transaction fee", "$114.91", "$229.82"],
        ["TOTAL CHARGED TO ACCOUNT", "$4,370.88", "$8,741.76"],
        ["Refund credited — principal (Apr 9, par rate)", "-$3,150.00", "-$6,300.00"],
        ["Refund credited — partial FX fee", "-$85.05", "-$170.10"],
        ["TOTAL CREDITED TO DATE", "-$3,235.05", "-$6,470.10"],
        ["SHORTFALL STILL OWED", "$1,135.83", "$2,271.66"],
    ]
    t = Table(data, colWidths=[3.4 * inch, 1.55 * inch, 1.55 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), CHARCOAL),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 3), (-1, 3), HexColor("#fff7e6")),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("BACKGROUND", (0, 6), (-1, 6), HexColor("#eef2f9")),
        ("FONTNAME", (0, 6), (-1, 6), "Helvetica-Bold"),
        ("BACKGROUND", (0, 7), (-1, 7), HexColor("#fdecea")),
        ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 7), (-1, 7), RED),
        ("LINEABOVE", (0, 3), (-1, 3), 0.5, HexColor("#cccccc")),
        ("LINEABOVE", (0, 6), (-1, 6), 0.5, HexColor("#cccccc")),
        ("LINEABOVE", (0, 7), (-1, 7), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def tieout_table():
    data = [
        ["Component of current statement balance", "Amount"],
        ["Propane / FX shortfall not yet credited (both cards)", "$2,271.66"],
        ["All other account activity, net (purchases less refunds & payments)", "-$36.85"],
        ["CURRENT STATEMENT BALANCE (per AmEx, June 10, 2026)", "$2,234.81"],
    ]
    t = Table(data, colWidths=[5.0 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), CHARCOAL),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 3), (-1, 3), HexColor("#fff7e6")),
        ("LINEABOVE", (0, 3), (-1, 3), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    s = styles()
    e = []

    e.append(Paragraph("CARDHOLDER MEMORANDUM &mdash; CFPB COMPLAINT SUPPORTING RECORD", s["title"]))
    e.append(Paragraph(
        "Supporting documentation for a complaint to the Consumer Financial Protection Bureau against American Express",
        s["subtitle"],
    ))
    e.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10))

    e.append(info_table([
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Account:", "American Express Blue Business Cash, ending 21007 (employee card ending 21049)"],
        ["AmEx Cases:", "D-93497818 (Card ending 1007) / D-93497819 (Card ending 1049)"],
        ["Merchant:", "Propane Fitness Ltd, Newcastle, United Kingdom"],
        ["Date of this memorandum:", "Thursday, June 11, 2026"],
        ["Amount in dispute:", "$2,271.66 USD (foreign-exchange conversion shortfall)"],
        ["Regulatory refs:", "CMA case CMAE2600101 &middot; Action Fraud RF26040189625C"],
    ]))
    e.append(Spacer(1, 10))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))

    e.append(Paragraph("1. SUMMARY", s["h1"]))
    e.append(Paragraph(
        "On March 2, 2026 the cardholder was charged a total of <b>$8,741.76 USD</b> "
        "(£6,300 plus foreign-transaction fees, at the $1.3511/£ rate in effect that day) by "
        "Propane Fitness, a UK merchant, for a business-mentorship program that was misrepresented "
        "(sold as one-on-one coaching, delivered as group clinics). The charge was split across two "
        "cards on a single American Express Blue Business Cash account. The cardholder filed "
        "chargebacks, assigned cases <b>D-93497818</b> and <b>D-93497819</b>. American Express has "
        "credited only <b>$6,470.10</b> &mdash; it refunded the £6,300 nominal at a parity rate of "
        "$1.00/£ rather than the $1.3511/£ rate actually charged, and reversed only part of the "
        "foreign-transaction fees. A shortfall of <b>$2,271.66</b> has never been credited.",
        s["body"],
    ))

    e.append(Paragraph("2. AMERICAN EXPRESS MISSED ITS OWN COMMITTED DECISION DATE", s["h1"]))
    e.append(Paragraph(
        "On <b>May 28, 2026</b>, on a recorded line, Supervisor <b>Michael (Employee ID HE0973A)</b> "
        "acknowledged that the disputed amount of record is $8,741.76, confirmed the back-end disputes "
        "team was reviewing the FX shortfall, and committed that a decision would be issued <b>no later "
        "than Tuesday, June 9, 2026</b>. That date has passed. The cardholder's statement dated "
        "<b>June 10, 2026</b> shows no corrective credit, and American Express has made no contact. "
        "This follows at least two earlier representative promises of a 3-5 business-day callback that "
        "were never honored.",
        s["body"],
    ))

    e.append(Paragraph("3. WHAT IS OWED — RECONCILIATION", s["h1"]))
    e.append(Paragraph(
        "The amount owed is not an estimate. It reconciles to the penny against American Express's own "
        "posted activity:",
        s["body"],
    ))
    e.append(Spacer(1, 4))
    e.append(recon_table())
    e.append(Spacer(1, 8))
    e.append(Paragraph(
        "Independent confirmation: the cardholder's <b>entire current statement balance is composed of "
        "this unrefunded amount</b>. Summing every line of the account's posted activity ties exactly to "
        "the statement balance American Express reports:",
        s["body"],
    ))
    e.append(Spacer(1, 4))
    e.append(tieout_table())
    e.append(Spacer(1, 8))
    e.append(Paragraph(
        "In other words, once the $2,271.66 corrective credit is posted, the account balance is reduced "
        "to approximately zero (a small credit balance of $36.85 in the cardholder's favor). This "
        "demonstrates that the disputed balance American Express continues to bill is, in substance, the "
        "exact amount of the FX shortfall it has declined to credit.",
        s["body"],
    ))

    e.append(Paragraph("4. WHY THE PAR-RATE REFUND IS INCORRECT", s["h1"]))
    e.append(Paragraph(
        "American Express's Notice of Dispute Information PDFs describe the chargeback as "
        "<b>£3,150.00 GBP</b> per case. The refund issued was <b>$3,150.00 USD</b> per case &mdash; "
        "an implied rate of $1.00 per pound, a parity that has not existed in modern foreign-exchange "
        "history. The original transactions posted to the cardholder's USD account at $1.3511/£. To "
        "restore the account to the position it would have occupied absent the disputed charges, the "
        "refund must be computed at that same rate, and the foreign-transaction fees charged on the "
        "now-refunded transactions must be fully reversed.",
        s["body"],
    ))

    e.append(Paragraph("5. RESOLUTION REQUESTED", s["h1"]))
    e.append(Paragraph(
        "American Express should post a corrective credit of <b>$2,271.66</b> to the account (cases "
        "D-93497818 and D-93497819), bringing the balance to zero, and provide written confirmation of "
        "the credit and the resolution of both cases. If American Express declines, it should issue a "
        "written denial citing the specific rule under which a refund at a $1.00/£ parity rate is "
        "permissible when the charge was made at $1.3511/£.",
        s["body"],
    ))

    e.append(Spacer(1, 12))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))
    e.append(Paragraph("Respectfully submitted,", s["body"]))
    e.append(Spacer(1, 6))
    e.append(Paragraph("<b>William J. Marceau</b>", s["body_bold"]))
    e.append(Paragraph("wmarceau@marceausolutions.com", s["body"]))
    e.append(Paragraph("Naples, Florida, United States", s["body"]))
    e.append(Paragraph("Thursday, June 11, 2026", s["body"]))

    e.append(Spacer(1, 12))
    e.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=4))
    e.append(Paragraph(
        "Submitted to the CFPB in support of a complaint against American Express &middot; "
        "Cases D-93497818 / D-93497819 &middot; FX conversion shortfall $2,271.66 &middot; June 11, 2026",
        s["footer"],
    ))

    doc.build(e)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
