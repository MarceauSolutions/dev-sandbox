#!/usr/bin/env python3
"""
Propane Fitness - AmEx Dispute: Memorialization of June 11, 2026 Supervisor Call
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

Written record of a recorded supervisor call in which American Express refused to
credit the FX conversion shortfall, directed the cardholder to a merchant "refund
completion form," cited the merchant's terms and conditions, and stated it could
provide nothing in writing. Created because AmEx again declined to issue written
confirmation. For the CFPB case file and the cardholder's records.
"""

import os
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED = HexColor("#c0392b")
CHARCOAL = HexColor("#333333")

OUTPUT = os.path.join(
    os.path.dirname(__file__),
    "propane-amex-call-memorialization-june11-2026.pdf",
)


def styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=16,
            leading=22, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=10,
            leading=14, textColor=CHARCOAL, spaceAfter=12, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12.5,
            leading=17, textColor=NAVY, spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5,
            leading=13.5, textColor=CHARCOAL, spaceAfter=5),
        "fact": ParagraphStyle("Fact", fontName="Helvetica", fontSize=10, leading=14,
            textColor=CHARCOAL, leftIndent=18, spaceAfter=4, bulletIndent=4),
        "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=7.5,
            leading=10, textColor=HexColor("#888888"), alignment=TA_CENTER),
    }


def info_table(rows, col_widths=(1.95 * inch, 4.55 * inch)):
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


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    s = styles()
    e = []

    e.append(Paragraph("CARDHOLDER MEMORANDUM &mdash; CALL MEMORIALIZATION", s["title"]))
    e.append(Paragraph(
        "Written record of recorded supervisor call &mdash; American Express Dispute Resolution",
        s["subtitle"]))
    e.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10))

    e.append(info_table([
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Cases:", "D-93497818 (Card ending 1007) / D-93497819 (Card ending 1049)"],
        ["Merchant:", "Propane Fitness Ltd, Newcastle, United Kingdom"],
        ["Date &amp; time of call:", "Thursday, June 11, 2026, approx. 4:30&ndash;4:56 PM EDT"],
        ["Call placed to:", "American Express, 1-800-528-4800"],
        ["Supervisor:", "Michael &mdash; Employee ID 7273100"],
        ["Related filing:", "CFPB Complaint #260611-34004878 (filed earlier same day)"],
    ]))
    e.append(Spacer(1, 10))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))

    e.append(Paragraph("PURPOSE OF THIS MEMORANDUM", s["h1"]))
    e.append(Paragraph(
        "The cardholder requested that American Express provide its position in writing, together with "
        "the supervisor's employee ID, by email on the date of the call. The supervisor stated that he "
        "had <b>no way to provide anything in writing</b>. As on a prior occasion, the cardholder is "
        "therefore creating this written record of the call &mdash; which the supervisor confirmed is "
        "recorded on the American Express side &mdash; for the cardholder's files and for the open CFPB "
        "complaint.",
        s["body"]))

    e.append(Paragraph("WHAT AMERICAN EXPRESS STATED ON THE RECORDED CALL", s["h1"]))
    e.append(Paragraph(
        "During the call, Supervisor Michael (Employee ID 7273100), after reviewing the documentation on "
        "file, made the following statements, which the cardholder records as follows:",
        s["body"]))
    facts = [
        "American Express <b>will not credit the remaining foreign-exchange conversion shortfall of "
        "$2,271.66 directly</b> to the cardholder's account.",
        "Instead, the cardholder must complete a <b>&ldquo;refund completion form&rdquo; said to originate "
        "from the merchant, Propane Fitness</b>, in order for the merchant to refund the remaining amount.",
        "American Express is <b>&ldquo;following the terms and conditions of the contract&rdquo;</b> "
        "between the cardholder and the merchant, and the supervisor stated he has <b>&ldquo;no way to "
        "override&rdquo;</b> this.",
        "When asked to identify the specific contractual term relied upon, no specific clause was read or cited.",
        "American Express stated it has <b>no mechanism to provide anything in writing</b>, including the "
        "above position and the supervisor's employee ID.",
        "The supervisor confirmed the call is <b>recorded on the American Express side</b>.",
    ]
    for i, f in enumerate(facts, 1):
        e.append(Paragraph(f"<b>{i}.</b> {f}", s["fact"]))
    e.append(Spacer(1, 6))

    e.append(Paragraph("CARDHOLDER'S RECORDED OBJECTIONS", s["h1"]))
    e.append(Paragraph(
        "The cardholder stated on the same recorded line that he <b>declines to complete any merchant "
        "form</b>, is <b>leaving both dispute cases (D-93497818 and D-93497819) open</b>, and does not "
        "accept being routed back to the merchant. The cardholder noted the following, which American "
        "Express did not rebut with any specific contractual or regulatory citation:",
        s["body"]))
    objections = [
        "This is a chargeback dispute governed by the cardholder's <b>American Express Cardmember "
        "Agreement and the federal Fair Credit Billing Act (Regulation Z)</b> &mdash; not by the "
        "merchant's terms and conditions. A merchant's contract cannot waive the cardholder's federal "
        "billing-error protections or limit American Express's obligations to the cardholder.",
        "The merchant issues refunds in <b>British pounds</b>. <b>American Express</b> chooses the rate "
        "at which that refund is converted to U.S. dollars. American Express converted the &pound;6,300 "
        "refund at an implied <b>$1.00/&pound; parity rate</b> rather than the <b>$1.3511/&pound;</b> "
        "rate at which it posted the original charges. The resulting shortfall is a product of American "
        "Express's own currency conversion, not the merchant's contract.",
        "The cardholder <b>won this chargeback</b> precisely because the merchant breached its own terms "
        "and refused to respond. Directing the cardholder back to that merchant is not a valid resolution "
        "of a won chargeback.",
    ]
    for i, o in enumerate(objections, 1):
        e.append(Paragraph(f"<b>{i}.</b> {o}", s["fact"]))
    e.append(Spacer(1, 6))

    e.append(Paragraph("STATUS AND NEXT STEPS", s["h1"]))
    e.append(Paragraph(
        "Both dispute cases remain <b>open</b>. The cardholder completed <b>no merchant form</b> and "
        "accepted <b>no resolution</b> on this call. American Express's refusal to credit the "
        "<b>$2,271.66</b> shortfall, its direction of the cardholder back to the merchant, and its stated "
        "reliance on the merchant's terms and conditions are now memorialized for the cardholder's open "
        "<b>CFPB complaint #260611-34004878</b>, to which American Express is required to respond in "
        "writing. This memorandum, together with the cardholder's contemporaneous notes and the American "
        "Express recording of the call, constitutes the cardholder's record of what was said.",
        s["body"]))

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
        "Memorialization of recorded call with Supervisor Michael (Employee ID 7273100) &middot; "
        "Cases D-93497818 / D-93497819 &middot; CFPB #260611-34004878 &middot; June 11, 2026",
        s["footer"]))

    doc.build(e)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
