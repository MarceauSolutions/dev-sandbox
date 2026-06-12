#!/usr/bin/env python3
"""
Propane Fitness - AmEx Dispute: Master Rebuttal / CFPB Supporting Brief (June 11, 2026)
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049) | CFPB #260611-34004878

Rebuts American Express's June 11 position that (a) the cardholder must use a merchant
"refund completion form," and (b) declining it would breach the merchant contract.
Built from a full re-analysis of the signed contract and every document filed by both
parties. Factual framing corrected per internal evidence audit (accurate outreach count,
correct refund-form date, verbal-pricing claim removed).
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
GREEN = HexColor("#1e7d4f")
CHARCOAL = HexColor("#333333")

OUTPUT = os.path.join(os.path.dirname(__file__),
    "propane-amex-cfpb-rebuttal-june11-2026.pdf")


def styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=15.5,
            leading=20, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=9.5,
            leading=13, textColor=CHARCOAL, spaceAfter=12, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12,
            leading=16, textColor=NAVY, spaceBefore=13, spaceAfter=5),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10,
            leading=13.5, textColor=DARK_BLUE, spaceBefore=7, spaceAfter=3),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.3,
            leading=13, textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=9,
            leading=12.5, textColor=HexColor("#444444"), leftIndent=16, rightIndent=14,
            spaceAfter=5, spaceBefore=2),
        "fact": ParagraphStyle("Fact", fontName="Helvetica", fontSize=9.3, leading=13,
            textColor=CHARCOAL, leftIndent=16, spaceAfter=3),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.3,
            leading=13, textColor=CHARCOAL, spaceAfter=5),
        "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=7.5,
            leading=10, textColor=HexColor("#888888"), alignment=TA_CENTER),
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
        ["", "Per Card", "Both Cards"],
        ["Propane charge (Mar 2, posted by AmEx @ $1.3511/£)", "$4,255.97", "$8,511.94"],
        ["Foreign-transaction fee", "$114.91", "$229.82"],
        ["TOTAL CHARGED", "$4,370.88", "$8,741.76"],
        ["AmEx credit — principal (reversal posted @ $1.00/£)", "-$3,150.00", "-$6,300.00"],
        ["AmEx credit — partial FX fee", "-$85.05", "-$170.10"],
        ["TOTAL CREDITED", "-$3,235.05", "-$6,470.10"],
        ["SHORTFALL STILL OWED", "$1,135.83", "$2,271.66"],
    ]
    t = Table(data, colWidths=[3.55 * inch, 1.45 * inch, 1.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("TEXTCOLOR", (0, 1), (-1, -1), CHARCOAL),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
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
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    s = styles()
    e = []

    e.append(Paragraph("CARDHOLDER REBUTTAL &mdash; CHARGEBACK FX SHORTFALL", s["title"]))
    e.append(Paragraph(
        "Response to American Express's position of June 11, 2026 &mdash; for CFPB Complaint #260611-34004878",
        s["subtitle"]))
    e.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=9))

    e.append(info_table([
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Account:", "AmEx Blue Business Cash, ending 21007 (employee card 21049)"],
        ["AmEx Cases:", "D-93497818 (card 1007) / D-93497819 (card 1049) &middot; Reason Code 4553"],
        ["Merchant:", "Propane Fitness Ltd, Newcastle, UK (Co. 07779096)"],
        ["Amount owed:", "$2,271.66 USD (foreign-exchange conversion shortfall)"],
        ["Date:", "Thursday, June 11, 2026"],
    ]))
    e.append(Spacer(1, 8))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=7))

    # CORE POSITION
    e.append(Paragraph("CORE POSITION", s["h1"]))
    e.append(Paragraph(
        "American Express resolved this dispute in my favor through a <b>forced chargeback</b> (reason "
        "code 4553) and credited the &pound;6,300 principal. American Express &mdash; not the merchant "
        "&mdash; then converted that reversal to U.S. dollars at an implied <b>$1.00/&pound; parity "
        "rate</b>, while it had posted the original charge at <b>$1.3511/&pound;</b>. That leaves "
        "<b>$2,271.66</b> uncredited. On June 11, 2026, a supervisor (Michael, ID 7273100) stated American "
        "Express will not credit this amount directly, directed me to a merchant &ldquo;refund completion "
        "form,&rdquo; and asserted that declining it would breach my contract with the merchant. Each of "
        "those positions is addressed and refuted below.",
        s["body"]))

    # ISSUE 1
    e.append(Paragraph("1. THIS WAS A FORCED CHARGEBACK — AMERICAN EXPRESS CONTROLS THE CONVERSION", s["h1"]))
    e.append(Paragraph(
        "The dispute documentation on file carries American Express <b>chargeback reason code 4553</b> and "
        "consists of the merchant's <b>representment (chargeback-defense) filings</b> arguing the "
        "&ldquo;chargeback&hellip; is invalid.&rdquo; Reason codes and representments exist only inside the "
        "chargeback rail; a voluntary merchant refund has neither. This was therefore a forced chargeback in "
        "which <b>American Express debited the merchant in GBP and credited me on my USD account</b> &mdash; "
        "meaning the GBP&rarr;USD conversion of the reversal was American Express's own act, not the "
        "merchant's.",
        s["body"]))
    e.append(Paragraph(
        "American Express applied <b>two different rates to the same transaction</b>: it converted the "
        "charge at $1.3511/&pound; and the reversal at $1.00/&pound;. A $1.00/&pound; parity rate has never "
        "existed in the foreign-exchange market. The merchant's liability was fixed in pounds (&pound;3,150 "
        "per card); only American Express converts that to dollars. Directing me to obtain the remainder "
        "from the merchant is inconsistent with the chargeback American Express itself processed.",
        s["body"]))

    # ISSUE 2
    e.append(Paragraph("2. DECLINING THE MERCHANT FORM DOES NOT BREACH ANY CONTRACT", s["h1"]))
    e.append(Paragraph(
        "American Express is not a party to my contract with the merchant and has no standing to enforce "
        "the merchant's terms against me; my dispute rights arise under my Cardmember Agreement and the "
        "federal Fair Credit Billing Act. Independently, the merchant's own contract defeats this argument:",
        s["body"]))
    e.append(Paragraph("(a) The contract's own terms exempt statutory rights.", s["h2"]))
    e.append(Paragraph(
        "The merchant's no-chargeback clause (&sect;7.5) and mandatory-process clause (&sect;12.5(B)) each "
        "carve out their own application. &sect;12.5(B) states the procedure <b>&ldquo;does not apply "
        "to&hellip; statutory rights that cannot be waived by agreement,&rdquo;</b> and &sect;7.3 limits "
        "refund exclusions to those <b>&ldquo;save as provided by law.&rdquo;</b> A UK consumer's right to "
        "a remedy for a service not-as-described or misrepresented (Consumer Rights Act 2015; "
        "Misrepresentation Act 1967) is a non-waivable statutory right. By the contract's own language, the "
        "anti-chargeback terms do not reach my claim.",
        s["body"]))
    e.append(Paragraph("(b) The merchant breached first and withheld the very process now demanded.", s["h2"]))
    e.append(Paragraph(
        "&sect;12.5(A) required the merchant to acknowledge and substantively respond within 7 days; "
        "&sect;7.4 required it to <b>provide the refund-request form &ldquo;on request.&rdquo;</b> I raised "
        "a refund on the merchant's own platform with my assigned coach on <b>March 4</b>, then sent formal "
        "written refund demands on <b>March 6, 7, 12, and 13, 2026, each copied to admin@propanefitness.com</b>. "
        "The merchant did not provide its refund form until <b>March 16</b> &mdash; the same time the dispute "
        "registered with American Express &mdash; and the salesperson who collected the &pound;6,300 replied "
        "only: <i>&ldquo;This has nothing to do with me, mate.&rdquo;</i> A merchant that withholds its own "
        "refund process cannot condition my refund on that process.",
        s["body"]))
    e.append(Paragraph("(c) American Express already adjudicated entitlement.", s["h2"]))
    e.append(Paragraph(
        "Having credited the &pound;6,300, American Express has already determined I was entitled to a "
        "refund. It cannot grant a partial recovery and then route the currency remainder &mdash; a remainder "
        "<b>its own conversion created</b> &mdash; back to a merchant I have already won a chargeback against.",
        s["body"]))

    # ISSUE 3
    e.append(Paragraph("3. THE UNDERLYING CHARGEBACK IS VALID — ON THE MERCHANT'S OWN DOCUMENTS", s["h1"]))
    e.append(Paragraph(
        "The misrepresentation is established by the merchant's own filings, not my recollection. The "
        "salesperson's closing email promised:",
        s["body"]))
    e.append(Paragraph(
        "&ldquo;Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, feedback and "
        "<b>calls</b> to customise the process to your business.&rdquo;", s["quote"]))
    e.append(Paragraph(
        "The merchant's Terms then define that same &ldquo;one-on-one&rdquo; service as a messaging channel "
        "(&ldquo;voice notes, document reviews, messages&rdquo;) plus recurring group &ldquo;coaching "
        "clinics&hellip; via Zoom.&rdquo; The merchant's chargeback rebuttal nonetheless claims I received "
        "<b>&ldquo;Individual Zoom calls&rdquo;</b> and <b>&ldquo;accessed all services&rdquo;</b> &mdash; "
        "yet the same filing includes, as the merchant's own Exhibit E, my contemporaneous March 4 messages:",
        s["body"]))
    e.append(Paragraph(
        "&ldquo;it does not show me any available live calls or the ability to access the content&rdquo; "
        "&middot; &ldquo;it really seems like I just got scammed.&rdquo;", s["quote"]))
    e.append(Paragraph(
        "The merchant filed both the claim and the proof it is false. The chargeback was correctly resolved "
        "in my favor; what remains is solely American Express's currency-conversion shortfall.",
        s["body"]))

    # RECON
    e.append(Paragraph("4. THE AMOUNT — RECONCILED TO THE PENNY", s["h1"]))
    e.append(recon_table())
    e.append(Spacer(1, 6))
    e.append(Paragraph(
        "My entire current statement balance ($2,234.81, June 10 statement) is composed of this unrefunded "
        "amount: $2,271.66 uncredited dispute, less $36.85 net of all other activity. Crediting $2,271.66 "
        "brings the account to zero.",
        s["body"]))

    # QUESTIONS
    e.append(Paragraph("5. QUESTIONS AMERICAN EXPRESS MUST ANSWER IN WRITING", s["h1"]))
    for i, q in enumerate([
        "Was the &pound;6,300 credit a forced chargeback (American Express debited the merchant) or a "
        "voluntary merchant refund? The reason-code-4553 representment filings indicate the former.",
        "At what exchange rate and on what date was the &pound;6,300 reversal converted to USD, and on what "
        "basis was it $1.00/&pound; when the charge was posted at $1.3511/&pound;?",
        "If the position is that the merchant short-remitted, produce documentation of what the merchant "
        "actually submitted.",
        "Why were the foreign-transaction fees only partially reversed ($85.05 of $114.91 per card) &mdash; "
        "an American Express-side figure regardless of the merchant?",
    ], 1):
        e.append(Paragraph(f"<b>{i}.</b> {q}", s["fact"]))

    # RESOLUTION
    e.append(Paragraph("6. RESOLUTION REQUESTED", s["h1"]))
    e.append(Paragraph(
        "Post a corrective credit of <b>$2,271.66</b> to cases D-93497818 and D-93497819, bringing the "
        "balance to zero, with written confirmation. Alternatively, provide a written denial citing the "
        "specific rule under which a &pound;3,150 charge posted at $1.3511/&pound; may be refunded at a "
        "$1.00/&pound; parity rate. I am not completing any merchant form, am not withdrawing either case, "
        "and continue to pay the statement minimum without waiving this dispute.",
        s["body"]))

    e.append(Spacer(1, 10))
    e.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=7))
    e.append(Paragraph("Respectfully submitted,", s["body"]))
    e.append(Spacer(1, 5))
    e.append(Paragraph("<b>William J. Marceau</b>", s["body_bold"]))
    e.append(Paragraph("wmarceau@marceausolutions.com &middot; Naples, Florida &middot; June 11, 2026", s["body"]))
    e.append(Spacer(1, 8))
    e.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=4))
    e.append(Paragraph(
        "Cases D-93497818 / D-93497819 &middot; CFPB #260611-34004878 &middot; FX shortfall $2,271.66 &middot; "
        "Regulatory refs CMAE2600101, RF26040189625C &middot; June 11, 2026",
        s["footer"]))

    doc.build(e)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build()
