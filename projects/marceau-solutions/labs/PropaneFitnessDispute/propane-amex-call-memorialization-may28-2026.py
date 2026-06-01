#!/usr/bin/env python3
"""
Propane Fitness — AmEx Dispute: Memorialization of May 28, 2026 Supervisor Call
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

Written record of verbal supervisor commitments made during recorded call,
since AmEx stated no proactive written confirmation could be provided.
For upload to the AmEx Dispute Center on both cases.
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
    "propane-amex-call-memorialization-may28-2026.pdf",
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
        "h2": ParagraphStyle(
            "H2", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
            textColor=DARK_BLUE, spaceBefore=8, spaceAfter=4,
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
            textColor=CHARCOAL, leftIndent=18, spaceAfter=4,
            bulletIndent=4,
        ),
        "quote": ParagraphStyle(
            "Quote", fontName="Helvetica-Oblique", fontSize=9.5, leading=13.5,
            textColor=HexColor("#555555"), leftIndent=18, rightIndent=18,
            spaceAfter=8, spaceBefore=4,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=7.5, leading=10,
            textColor=HexColor("#888888"), alignment=TA_CENTER,
        ),
    }


def info_table(rows, col_widths=(1.55 * inch, 4.95 * inch)):
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


def fx_math_table():
    data = [
        ["", "Per Card (each)", "Total (both cards)"],
        ["Original transaction (£)", "£3,150.00", "£6,300.00"],
        ["FX rate applied at charge (Mar 2, 2026)", "$1.3511 / £", "$1.3511 / £"],
        ["USD posted to statement", "$4,255.97", "$8,511.94"],
        ["Foreign transaction fees", "$114.91", "$229.82"],
        ["TOTAL CHARGED TO ACCOUNT (USD)", "$4,370.88", "$8,741.76"],
        ["AmEx refund issued (Apr 9, 2026)", "$3,150.00", "$6,300.00"],
        ["Implied FX rate on refund", "$1.00 / £", "$1.00 / £"],
        ["SHORTFALL OWED", "$1,220.88", "$2,441.76"],
    ]
    t = Table(data, colWidths=[3.0 * inch, 1.75 * inch, 1.75 * inch])
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
        ("BACKGROUND", (0, 5), (-1, 5), HexColor("#fff7e6")),
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("BACKGROUND", (0, 8), (-1, 8), HexColor("#fdecea")),
        ("FONTNAME", (0, 8), (-1, 8), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 8), (-1, 8), RED),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.white),
        ("LINEABOVE", (0, 5), (-1, 5), 0.5, HexColor("#cccccc")),
        ("LINEABOVE", (0, 8), (-1, 8), 0.5, HexColor("#cccccc")),
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

    # ========== HEADER ==========
    e.append(Paragraph("CARDHOLDER MEMORANDUM &mdash; CALL MEMORIALIZATION", s["title"]))
    e.append(Paragraph(
        "Written record of recorded supervisor call &mdash; American Express Dispute Resolution",
        s["subtitle"],
    ))
    e.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10))

    e.append(info_table([
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Cases:", "D-93497818 (Card ending 1007) / D-93497819 (Card ending 1049)"],
        ["Merchant:", "Propane Fitness Ltd, Newcastle, United Kingdom"],
        ["Date of this memorandum:", "Thursday, May 28, 2026"],
        ["Call placed to:", "American Express Disputes, 1-800-528-4800"],
        ["Supervisor:", "Michael — Employee ID HE0973A (no direct extension provided)"],
    ]))
    e.append(Spacer(1, 10))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))

    # ========== PURPOSE ==========
    e.append(Paragraph("PURPOSE OF THIS MEMORANDUM", s["h1"]))
    e.append(Paragraph(
        "During the call described below, the cardholder requested that American Express provide written "
        "confirmation of the supervisor's verbal commitments. The supervisor stated that American Express "
        "has <b>no mechanism to provide proactive written confirmation</b> of the points discussed. "
        "Accordingly, the cardholder is creating this written record and uploading it to both case files "
        "via the AmEx Dispute Center, so that the substance of the call &mdash; verbally confirmed by the "
        "supervisor on a recorded line &mdash; becomes part of the permanent case record.",
        s["body"],
    ))

    # ========== POINTS VERBALLY CONFIRMED ==========
    e.append(Paragraph("FACTS VERBALLY CONFIRMED BY SUPERVISOR ON RECORDED CALL", s["h1"]))
    e.append(Paragraph(
        "At the close of the call, the cardholder read each of the following points back to Supervisor "
        "Michael (Employee ID HE0973A) and obtained explicit verbal confirmation that each statement "
        "accurately reflects what was discussed:",
        s["body"],
    ))

    facts = [
        "Today's date is <b>Thursday, May 28, 2026</b>.",
        "The cardholder is speaking with <b>Supervisor Michael, Employee ID HE0973A</b>.",
        "The back-end disputes team has been informed that the disputed amount on cases "
        "<b>D-93497818</b> and <b>D-93497819</b> is <b>$8,741.76 USD</b>, not $3,150 USD, "
        "consistent with the cardholder's April 7, 2026 resubmission, and that this "
        "information is <b>in the cardholder's favor</b>.",
        "The back-end disputes team is actively reviewing the foreign-exchange "
        "conversion shortfall of approximately <b>$2,441.76</b>.",
        "A decision is expected within <b>5 to 7 business days</b>, no later than "
        "<b>Tuesday, June 9, 2026</b>.",
        "No direct extension was available for the supervisor. Follow-up should reference "
        "<b>Employee ID HE0973A</b> together with the two case numbers above.",
    ]
    for idx, fact in enumerate(facts, start=1):
        e.append(Paragraph(f"<b>{idx}.</b> {fact}", s["fact"]))
    e.append(Spacer(1, 6))

    # ========== UNDERLYING FX MATH ==========
    e.append(Paragraph("THE UNDERLYING ISSUE BEING REVIEWED &mdash; FX CONVERSION SHORTFALL", s["h1"]))
    e.append(Paragraph(
        "For the avoidance of doubt regarding the substance of the dispute now under back-end review, "
        "the cardholder restates the arithmetic that the supervisor and prior representatives have "
        "acknowledged is straightforward:",
        s["body"],
    ))
    e.append(Spacer(1, 4))
    e.append(fx_math_table())
    e.append(Spacer(1, 6))
    e.append(Paragraph(
        "American Express's Notice of Dispute Information PDFs for both cases (in AmEx's own words) "
        "describe the chargeback as <b>&pound;3,150.00 GBP</b> per case. The refund issued was "
        "<b>$3,150.00 USD</b> per case &mdash; an implied exchange rate of <b>$1.00 per pound</b>, a "
        "parity rate which has not existed in modern foreign-exchange history. The original transactions "
        "were posted to the cardholder's USD account at <b>$1.3511 per pound</b>, which is the rate at "
        "which the refund must also be computed in order to restore the cardholder's account to the "
        "position it would have been in absent the disputed charges. The shortfall, including the "
        "foreign-transaction fees that should not have been charged on a refunded transaction, is "
        "<b>$2,441.76 USD</b>.",
        s["body"],
    ))

    # ========== INDEPENDENT RECORD ==========
    e.append(Paragraph("INDEPENDENT WRITTEN RECORD", s["h1"]))
    e.append(Paragraph(
        "Because American Express stated it could not provide its own written confirmation, the "
        "cardholder is preserving the following independent record of the call:",
        s["body"],
    ))
    independent = [
        "This memorandum, uploaded to both case files (D-93497818 and D-93497819) via the AmEx Dispute Center on May 28, 2026.",
        "A copy of this memorandum emailed to the cardholder's own email address "
        "(wmarceau@marceausolutions.com) on the same date, providing a timestamped "
        "record independent of American Express systems.",
        "The cardholder's contemporaneous handwritten notes from the call, retained.",
        "The call itself, which the supervisor confirmed was recorded on the American Express side.",
    ]
    for idx, item in enumerate(independent, start=1):
        e.append(Paragraph(f"<b>{idx}.</b> {item}", s["fact"]))

    # ========== EXPECTATIONS / NEXT STEPS ==========
    e.append(Paragraph("CARDHOLDER EXPECTATIONS AND NEXT STEPS", s["h1"]))
    e.append(Paragraph(
        "Based on the verbal commitments memorialized above, the cardholder expects American Express to "
        "post the corrective credit of approximately <b>$2,441.76</b> &mdash; or to provide a written "
        "denial citing the specific rule under which the corrective credit is being declined &mdash; "
        "no later than <b>Tuesday, June 9, 2026</b>. If neither has been received by that date, the "
        "cardholder intends to file a complaint with the Consumer Financial Protection Bureau (CFPB) at "
        "consumerfinance.gov/complaint, attaching this memorandum, the April 7, 2026 resubmission, the "
        "AmEx Notice of Dispute Information PDFs, and all other supporting documentation already in "
        "the case file.",
        s["body"],
    ))
    e.append(Spacer(1, 6))
    e.append(Paragraph(
        "This memorandum is submitted in good faith for the sole purpose of creating a written record "
        "of verbal commitments made on a recorded line during today's call. Nothing in this memorandum "
        "is intended to alter the scope of the underlying chargebacks, which remain those described in "
        "the cardholder's April 7, 2026 resubmission previously submitted to American Express.",
        s["body"],
    ))

    # ========== SIGNATURE ==========
    e.append(Spacer(1, 12))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))
    e.append(Paragraph("Respectfully submitted,", s["body"]))
    e.append(Spacer(1, 6))
    e.append(Paragraph("<b>William J. Marceau</b>", s["body_bold"]))
    e.append(Paragraph("wmarceau@marceausolutions.com", s["body"]))
    e.append(Paragraph("Naples, Florida, United States", s["body"]))
    e.append(Paragraph("Thursday, May 28, 2026", s["body"]))

    e.append(Spacer(1, 12))
    e.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=4))
    e.append(Paragraph(
        "Filed in AmEx Dispute Center for cases D-93497818 and D-93497819 &middot; "
        "Memorialization of recorded call with Supervisor Michael (HE0973A) &middot; May 28, 2026",
        s["footer"],
    ))

    doc.build(e)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
