#!/usr/bin/env python3
"""
Propane Fitness — Cardholder Rebuttal to Merchant's Chargeback Evidence
Case D-93497818 (Card 1007) and D-93497819 (Card 1049)
Generated April 3, 2026

This rebuttal addresses Propane Fitness Ltd's "Chargeback Dispute Response"
submitted to American Express, dismantling each claim using the merchant's
own exhibits and documented evidence.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

# Colors
NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED = HexColor("#c0392b")
GOLD = HexColor("#C9963C")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
WHITE = colors.white
ALERT_BG = HexColor("#fff3f3")
KEY_BG = HexColor("#f0f4ff")


def get_styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=18, leading=24, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=11, leading=15, textColor=CHARCOAL, spaceAfter=14, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14, leading=19, textColor=NAVY, spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=DARK_BLUE, spaceBefore=12, spaceAfter=5),
        "h3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=CHARCOAL, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5, textColor=CHARCOAL, spaceAfter=5),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=9.5, leading=13.5, textColor=HexColor("#555555"), leftIndent=15, rightIndent=15, spaceAfter=6),
        "alert": ParagraphStyle("Alert", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5, textColor=RED, spaceAfter=5),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=CHARCOAL, leftIndent=20, spaceAfter=3, bulletIndent=8),
        "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=8, leading=10, textColor=HexColor("#888888"), alignment=TA_CENTER),
    }


def header_block(s):
    return [
        Paragraph("CARDHOLDER REBUTTAL TO MERCHANT EVIDENCE", s["title"]),
        Paragraph("Propane Fitness Ltd Chargeback Dispute Response", s["subtitle"]),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=12),
        Spacer(1, 4),
    ]


def case_info(s):
    data = [
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Location:", "Naples, Florida, US"],
        ["Case References:", "D-93497818 (Card ending 1007) / D-93497819 (Card ending 1049)"],
        ["Reason Code:", "4553 — Product Unacceptable"],
        ["Merchant:", "Propane Fitness Ltd, 69 Church Way, North Shields NE29 0AE"],
        ["Total Disputed:", "£6,300.00 GBP (~$8,741.76 USD including foreign transaction fees)"],
        ["Date of Rebuttal:", "April 3, 2026"],
    ]
    table = Table(data, colWidths=[1.6 * inch, 4.9 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [table, Spacer(1, 12), HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=10)]


def executive_summary(s):
    return [
        Paragraph("1. EXECUTIVE SUMMARY", s["h1"]),
        Paragraph(
            "Propane Fitness Ltd's chargeback response relies on three pillars: (1) a signed contract, "
            "(2) evidence of platform access, and (3) the claim that the cardholder refused their refund process. "
            "Each pillar collapses under scrutiny — and critically, the merchant's own exhibits provide the evidence.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph(
            "<b>The signed contract (March 5)</b> was executed three days AFTER payment was collected (March 2). "
            "The cardholder had already paid £6,300 and had no choice but to sign to access what he'd paid for. "
            "This is economic duress, not voluntary agreement.",
            s["body"]
        ),
        Paragraph(
            "<b>The platform access evidence</b> actually proves the cardholder's case. The merchant's own Exhibit E "
            "shows the cardholder asking: <i>\"How do I schedule live cal with you as that is also part of the services\"</i> "
            "and <i>\"when im logged into circle it does not show me any available live\"</i> — proving he expected "
            "scheduled 1-on-1 Zoom coaching (as sold) and discovered it didn't exist.",
            s["body"]
        ),
        Paragraph(
            "<b>The refund process claim</b> is misleading. The merchant withheld the refund form for 8 days "
            "(March 6-14) despite being required to provide it \"on request\" (Section 7.4). When finally "
            "provided, it required the cardholder to withdraw chargeback protections first — with no guarantee "
            "of refund, only a promise to \"assess eligibility.\"",
            s["body"]
        ),
        Spacer(1, 6),
        Paragraph(
            "The product was NOT as described. Reason code 4553 applies. The chargebacks should be upheld.",
            s["alert"]
        ),
    ]


def rebuttal_section_1(s):
    """Terms signed after payment"""
    return [
        Paragraph("2. THE SIGNED CONTRACT WAS OBTAINED UNDER ECONOMIC DURESS", s["h1"]),
        Paragraph(
            "The merchant's central argument is that the cardholder \"signed the Terms of Use on March 5, 2026\" "
            "(Attachment 3). This is true — but the merchant omits that <b>payment of £6,300 was already collected "
            "on March 2, 2026</b>, three full days earlier.",
            s["body"]
        ),
        Paragraph("The payment-to-signature timeline:", s["body_bold"]),
        Paragraph("• March 2, 15:32 — First payment of £3,150 collected (card 1007)", s["bullet"]),
        Paragraph("• March 2, 15:40 — Second payment of £3,150 collected (card 1049)", s["bullet"]),
        Paragraph("• March 5 — Terms of Use signed via Jotform (Invoice INV-6485333402225932830)", s["bullet"]),
        Spacer(1, 4),
        Paragraph(
            "The merchant's own Exhibit E confirms this sequence. The cardholder's coach, Phil Charlton, states on "
            "March 5: <i>\"You just need to sign the Ts and C's, you should have been sent this upon point of sale.\"</i> "
            "Phil himself acknowledges the terms should have been signed at point of sale — but they weren't. They were "
            "signed three days later, after £6,300 was already gone.",
            s["body"]
        ),
        Paragraph(
            "A signature obtained after payment has already been collected is not freely given consent. The cardholder "
            "had two choices: sign and get access to what he'd already paid for, or refuse to sign and lose both the "
            "money and the service. This is textbook economic duress. The contract terms — including the refund "
            "restrictions, cooling-off waiver, and dispute resolution clauses — cannot be enforced against a party "
            "who had no practical ability to refuse.",
            s["body"]
        ),
        Paragraph(
            "The Jotform itself contains the statement: <i>\"I acknowledge that services have been received or are "
            "currently being delivered.\"</i> The cardholder was required to affirm this on March 5 — but the merchant's "
            "own Exhibit E shows that access issues were NOT resolved until Phil intervened on March 5. The cardholder "
            "was asked to confirm receipt of services while simultaneously telling his coach he couldn't access them.",
            s["body"]
        ),
    ]


def rebuttal_section_2(s):
    """Bait and switch - the core service issue"""
    return [
        Paragraph("3. THE CORE SERVICE WAS MATERIALLY DIFFERENT FROM WHAT WAS SOLD", s["h1"]),
        Paragraph("This is the central issue. Reason code 4553 applies because the product received was not as described.", s["body_bold"]),
        Spacer(1, 4),
        Paragraph("3a. What Was Sold (Jim Galvin's Sales Email — March 2, 15:18)", s["h2"]),
        Paragraph(
            "The seller's own written email — sent minutes before payment was collected — promises:",
            s["body"]
        ),
        Paragraph(
            "<i>\"Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, feedback "
            "and calls to customise the process to your business.\"</i>",
            s["quote"]
        ),
        Paragraph(
            "The word \"Dedicated\" and the phrase \"calls to customise the process\" represent a specific, "
            "personalized coaching relationship with scheduled Zoom sessions. This was the primary value "
            "proposition and the reason for purchase.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("3b. What Was Delivered (Proven by the Merchant's Own Exhibits)", s["h2"]),
        Paragraph(
            "The merchant's own Exhibit E — submitted as evidence in their favor — contains the following "
            "exchange from the cardholder's coaching thread:",
            s["body"]
        ),
        Paragraph(
            "<i>\"Also How do I schedule live cal with you as that is also part of the services\"</i> — William Marceau",
            s["quote"]
        ),
        Paragraph(
            "<i>\"Additionally when im logged into circle it does not show me any available live\"</i> — William Marceau",
            s["quote"]
        ),
        Paragraph(
            "These messages prove two critical facts: (1) the cardholder expected to schedule live 1-on-1 Zoom "
            "calls as part of the service, and (2) no scheduling system existed on the platform. The cardholder "
            "did not discover this discrepancy until after payment and after signing the terms.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("3c. The Merchant's Own Terms Confirm the Discrepancy", s["h2"]),
        Paragraph(
            "The merchant's signed Terms of Use (Attachment 3) describe 1-on-1 coaching support as:",
            s["body"]
        ),
        Paragraph(
            "<i>\"One-on-One Coaching Support: Onboarding call and 12 weeks of [...] access to a dedicated coach. "
            "This channel facilitates the sharing of voice notes, document reviews, messages.\"</i>",
            s["quote"]
        ),
        Paragraph(
            "Note what is described: a messaging channel for voice notes, document reviews, and messages. "
            "This is fundamentally different from what was sold: <i>\"Dedicated 1-2-1 coach\"</i> with "
            "<i>\"calls to customise the process.\"</i> The sales email promises scheduled coaching calls. "
            "The terms describe a text-based messaging thread. These are materially different services.",
            s["body"]
        ),
        Paragraph(
            "The merchant's terms separately describe \"Coaching Clinics\" as <i>\"Multiple times per week, "
            "we offer 'coaching clinics' via Zoom. You can book one-on-one sessions.\"</i> While the merchant "
            "may argue this constitutes \"1-on-1 coaching,\" it is fundamentally different from what was sold. "
            "Jim Galvin's email promised a <i>\"Dedicated\"</i> coach — meaning one specific person assigned "
            "to the cardholder — with a <i>\"Private thread\"</i> and <i>\"calls to customise the process to "
            "your business.\"</i> This describes a recurring, personalized coaching relationship with scheduled "
            "sessions. A drop-in clinic where any member can book a slot is not a dedicated coaching relationship. "
            "The cardholder's own messages in Exhibit E — asking how to schedule a live call and finding no "
            "availability — confirm the distinction.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("3d. The Merchant's Own Section 11.4 Acknowledges This Liability", s["h2"]),
        Paragraph(
            "The merchant's Terms of Use, Section 11.4, states: <i>\"Nothing in these Terms shall exclude or "
            "limit our liability for... (c) misrepresentation as to a fundamental matter.\"</i>",
            s["body"]
        ),
        Paragraph(
            "The nature of the coaching — scheduled weekly 1-on-1 Zoom sessions with a dedicated personal "
            "coach versus a messaging thread plus group clinics — is a fundamental matter that directly "
            "influenced the purchase decision. The merchant cannot rely on their own terms to deny this "
            "dispute when those same terms explicitly acknowledge liability for this exact type of misrepresentation.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("3e. Section 12.3 \"Entire Agreement\" Cannot Apply Retroactively", s["h2"]),
        Paragraph(
            "The merchant may invoke Section 12.3, which states the written terms \"supersede any prior agreement, "
            "understanding or arrangement between the parties.\" However, this clause was part of the Terms of Use "
            "signed on March 5 — three days after payment was collected based on Jim Galvin's representations. "
            "A contract clause cannot retroactively nullify the pre-sale representations that induced the purchase. "
            "The cardholder's decision to pay £6,300 on March 2 was based on Jim's email and verbal promises. "
            "The \"entire agreement\" clause signed three days later, under economic duress, does not erase what "
            "was promised to secure the sale.",
            s["body"]
        ),
        Paragraph(
            "<b>Note:</b> Jim Galvin's sales email of March 2, 15:18 UTC (subject: \"Next steps to secure your spot\") "
            "was submitted to American Express as part of the original dispute filing. It contains the exact "
            "representations quoted throughout this rebuttal.",
            s["body"]
        ),
    ]


def rebuttal_section_3(s):
    """Refund process was rigged"""
    return [
        Paragraph("4. THE REFUND PROCESS WAS WITHHELD, THEN OFFERED AS A TRAP", s["h1"]),
        Paragraph("The merchant claims the cardholder \"refused to follow the agreed refund process.\" This is misleading.", s["body_bold"]),
        Spacer(1, 4),
        Paragraph("4a. The Refund Form Was Withheld for 8 Days", s["h2"]),
        Paragraph(
            "The merchant's own Section 7.4 states: <i>\"To initiate a refund request, the member must complete "
            "the refund request form provided by PropaneFitness or PropaneBusiness on request.\"</i>",
            s["body"]
        ),
        Paragraph(
            "The cardholder first requested a refund on <b>March 6, 2026</b> — Day 4 of the 14-day window. "
            "The merchant did not provide the refund form until <b>March 14</b> — 8 days later, and only AFTER "
            "the cardholder had sent 4 formal emails (March 6, 7, 12, and 13) to jim@propanefitness.com and "
            "admin@propanefitness.com.",
            s["body"]
        ),
        Paragraph(
            "The merchant's own Exhibit F contains Phil Charlton's message from March 14: <i>\"Until yesterday "
            "I wasn't aware this had been raised, so I'm sorry for the delay in getting back to you.\"</i> "
            "The merchant's assigned coach — the person responsible for handling refund requests per Section 7.2 "
            "— was \"completely unaware\" of the dispute for 8 days. This is a failure of the merchant's own "
            "internal processes, not the cardholder's fault.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("4b. The Form Required Surrendering Chargeback Protection With No Guarantee", s["h2"]),
        Paragraph(
            "The merchant's own Exhibit B shows the two \"resolution options\" offered on March 14/16:",
            s["body"]
        ),
        Paragraph(
            "<i>\"Option 1 — Withdraw the chargebacks and complete our refund form (fastest route)\"</i>",
            s["quote"]
        ),
        Paragraph(
            "<i>\"Option 2 — Continue with the chargebacks\"</i>",
            s["quote"]
        ),
        Paragraph(
            "Option 1 requires the cardholder to withdraw his chargeback protections FIRST, then submit a form "
            "for Propane to \"assess eligibility\" — with a review period of \"up to 90 days.\" There is no "
            "commitment to actually issue a refund. The cardholder would be surrendering his only leverage "
            "(the chargeback) in exchange for a non-binding promise to consider his request.",
            s["body"]
        ),
        Paragraph(
            "No reasonable person would withdraw financial protections on an $8,700 purchase based on a "
            "promise to \"assess eligibility.\" The merchant designed this process to make the chargeback "
            "the only viable path, then claims the cardholder breached contract by taking it.",
            s["body"]
        ),
        Spacer(1, 4),
        Paragraph("4c. Section 7.1's 48-Hour Window Cannot Start Until the Form Is Provided", s["h2"]),
        Paragraph(
            "Section 7.1 states the refund form must be completed \"within 48 hours of initiating the refund "
            "request.\" The cardholder initiated on March 6. The form was not provided until March 14. The "
            "48-hour window cannot begin until the merchant fulfills their obligation under Section 7.4 to "
            "provide the form. The merchant cannot create a deadline tied to a form they refuse to supply, "
            "then claim the deadline has passed.",
            s["body"]
        ),
    ]


def rebuttal_section_4(s):
    """22-minute payment rush + access issues"""
    return [
        Paragraph("5. HIGH-PRESSURE SALES AND IMMEDIATE ACCESS FAILURE", s["h1"]),
        Paragraph("5a. 22-Minute Payment Sequence", s["h2"]),
        Paragraph("The complete payment timeline on March 2, 2026:", s["body"]),
        Spacer(1, 2),
    ]


def timeline_table(s):
    data = [
        ["Time (UTC)", "Event", "Gap"],
        ["15:18", "Sales email with pricing sent", "—"],
        ["15:27", "Terms link emailed", "9 min"],
        ["15:29", "First payment link sent", "2 min"],
        ["15:30", "Second payment link sent", "1 min"],
        ["15:32", "First charge processed — £3,150 (card 1007)", "2 min"],
        ["15:40", "Second charge processed — £3,150 (card 1049)", "8 min"],
    ]
    table = Table(data, colWidths=[1.1 * inch, 3.8 * inch, 0.8 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [
        table,
        Spacer(1, 6),
        Paragraph(
            "The cardholder had <b>2 minutes</b> between receiving the terms link and the first payment link. "
            "The full £6,300 was collected within 22 minutes of the pricing email. For a purchase exceeding "
            "$8,700 USD, this timeline did not provide a reasonable opportunity to read and understand a "
            "16-page terms document.",
            s["body"]
        ),
    ]


def rebuttal_section_5(s):
    """Access failure"""
    return [
        Paragraph("5b. Immediate Access Was Promised and Not Delivered", s["h2"]),
        Paragraph(
            "Jim Galvin's sales email (March 2, 15:18) explicitly states: <i>\"Once you've processed the "
            "payment you'll receive immediate access via email with login information and next steps.\"</i>",
            s["body"]
        ),
        Paragraph(
            "The merchant's own Exhibit E proves access was NOT immediate. The cardholder's messages show "
            "he could not access Circle features, Notion links redirected to a \"Propane guest\" page, and "
            "Pulse software was not available. Phil Charlton acknowledged: <i>\"Originally you put the wrong "
            "email address in which is what has caused the issue.\"</i> — blaming the cardholder for an access "
            "failure that took days to resolve.",
            s["body"]
        ),
        Paragraph(
            "This is a direct breach of a specific written representation made at the point of sale by the "
            "seller, Jim Galvin.",
            s["body"]
        ),
    ]


def rebuttal_section_6(s):
    """Why 4553 applies"""
    return [
        Paragraph("6. WHY REASON CODE 4553 (PRODUCT UNACCEPTABLE) APPLIES", s["h1"]),
        Paragraph(
            "The merchant argues that reason code 4553 \"applies where goods or services are materially "
            "different from what was described or are defective. This does not apply here.\"",
            s["body"]
        ),
        Paragraph("It applies precisely. Here is the comparison:", s["body_bold"]),
        Spacer(1, 4),
    ]


def comparison_table(s):
    data = [
        [Paragraph("<b>What Was Sold</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=WHITE)),
         Paragraph("<b>What Was Delivered</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=WHITE))],
        [Paragraph("\"Dedicated 1-2-1 coach\" with \"calls to customise the process to your business\" (Jim's email, Mar 2)", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL)),
         Paragraph("A messaging thread for \"voice notes, document reviews, messages\" (Terms, One-on-One Coaching Support section)", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("Consistent weekly scheduled Zoom coaching sessions (verbal representation on sales call)", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL)),
         Paragraph("No calendar or booking system for 1-on-1 Zoom calls. Cardholder asked how to schedule and was told it doesn't work that way.", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("\"Immediate access via email with login information\" (Jim's email, Mar 2)", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL)),
         Paragraph("Access not functional until March 5 after multiple follow-ups. Coach acknowledged access failure.", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("Price discussed as having 20% discount from retail (Jim's email, Mar 2)", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL)),
         Paragraph("No USD equivalent disclosed. Foreign transaction fees of $229.82 never mentioned. True cost: $8,741.76.", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8.5, leading=12, textColor=CHARCOAL))],
    ]
    table = Table(data, colWidths=[3.15 * inch, 3.15 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#1a5c2a")),
        ("BACKGROUND", (1, 0), (1, 0), RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (0, -1), HexColor("#f0fff0")),
        ("BACKGROUND", (1, 1), (1, -1), HexColor("#fff0f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [table, Spacer(1, 8)]


def rebuttal_section_7(s):
    """Address the SMS exhibit"""
    return [
        Paragraph("7. REGARDING EXHIBIT G2 — THE SMS MESSAGE", s["h1"]),
        Paragraph(
            "The merchant included a screenshot of an SMS from the cardholder to Jim Galvin (Exhibit G2) "
            "containing profane language. The cardholder acknowledges this message was sent in frustration "
            "after discovering the pricing misrepresentation and spending days unable to access the service "
            "he had paid $8,700 for.",
            s["body"]
        ),
        Paragraph(
            "This message has no bearing on whether the product was as described. It does not change the fact "
            "that: (a) payment was collected before terms were signed, (b) the 1-on-1 coaching sold was not "
            "the 1-on-1 coaching delivered, (c) immediate access was promised and not provided, and (d) the "
            "refund form was withheld for 8 days.",
            s["body"]
        ),
        Paragraph(
            "The merchant's inclusion of this message is a character attack designed to prejudice the reviewer "
            "against the cardholder. American Express evaluates disputes on the merits of the transaction, "
            "not on the emotional tone of post-sale communications.",
            s["body"]
        ),
    ]


def rebuttal_section_8a(s):
    """UK Consumer Protection + Sales Kick addendum + Section 7.2 absurdity"""
    return [
        Paragraph("8. ADDITIONAL LEGAL AND PROCEDURAL GROUNDS", s["h1"]),

        Paragraph("8a. UK Consumer Contracts Regulations 2013 — 14-Day Cooling-Off Right", s["h2"]),
        Paragraph(
            "Propane Fitness Ltd is a UK company (VAT: 266679253, registered at 69 Church Way, North Shields NE29 0AE). "
            "The merchant's own Terms of Use, Section 12.5(C), state: <i>\"These Terms and any dispute or claim arising "
            "out of or in connection with it... shall be governed by and construed in accordance with the law of England "
            "and Wales.\"</i> Because the contract itself designates UK law, the UK Consumer Contracts "
            "(Information, Cancellation and Additional Charges) Regulations 2013 apply. Under these regulations, "
            "this was a distance contract formed via telephone and online payment, and the cardholder has a statutory "
            "14-day cooling-off period during which cancellation can be made for any reason.",
            s["body"]
        ),
        Paragraph(
            "The merchant claims this right was waived by \"accessing materials\" (Section 7.1). However: "
            "(a) the cardholder did NOT have functional access to course materials until March 5, after the "
            "terms were signed — the merchant's own Exhibit E proves access was broken; "
            "(b) the cardholder did not meaningfully engage with or consume course modules, videos, or "
            "training materials — the only interactions were onboarding steps to evaluate the service; "
            "(c) under the Regulations, the waiver must be explicitly consented to BEFORE access is granted, "
            "which requires formally agreed terms BEFORE payment — not three days after.",
            s["body"]
        ),
        Paragraph(
            "The cardholder's refund request was made on March 6 — Day 4 of the 14-day window. Even under the "
            "merchant's own policy, this was within the refund period.",
            s["body"]
        ),
        Spacer(1, 6),

        Paragraph("8b. The \"Sales Kick\" Addendum Was Created After Purchase", s["h2"]),
        Paragraph(
            "The merchant's Attachment 3 includes a \"Sales Kick Addendum\" with an effective date of "
            "<b>13/3/26 (March 13, 2026)</b> — eleven days after the purchase and seven days after the "
            "cardholder's refund request. This addendum introduces new terms including binding arbitration "
            "via CEDR and a jury trial waiver. These terms did not exist at the time of purchase or at the "
            "time the cardholder signed the original Terms of Use on March 5. They cannot be retroactively "
            "applied to a transaction that predates them.",
            s["body"]
        ),
        Spacer(1, 6),

        Paragraph("8c. Section 7.2 Refund Requirements Are Designed to Be Impossible", s["h2"]),
        Paragraph(
            "The merchant's Section 7.2 requires all of the following to qualify for a refund within 14 days: "
            "completed onboarding, attended the 1-2-1 coaching call, completed all modules for the first 2 weeks, "
            "engaged with the coach at least twice, participated in 2 Q&amp;A hotseat calls, checked in on a weekly "
            "community post, AND met lead generation targets (e.g., 5 Bait Builder posts + 50 outreach messages).",
            s["body"]
        ),
        Paragraph(
            "These conditions require substantial engagement with the full program within a 14-day window — the "
            "same window during which the cardholder is supposed to be evaluating whether the service matches "
            "what was sold. A refund policy that requires near-complete program participation before allowing "
            "a refund is not a genuine refund policy — it is designed to ensure no refund is ever granted. "
            "This is an unfair contract term under both UK and US consumer protection standards.",
            s["body"]
        ),
        Spacer(1, 6),

        Paragraph("8d. The Merchant's Timeline Contradicts Their Own Evidence", s["h2"]),
        Paragraph(
            "The merchant's Chargeback Dispute Response (Attachment 4) states in Section 2 Timeline: "
            "<i>\"~Mar 2: Cardholder purchases programme. Immediate access to Circle community, materials, "
            "and onboarding.\"</i>",
            s["body"]
        ),
        Paragraph(
            "However, the merchant's own Exhibit E shows the cardholder messaging on March 3-4 that he "
            "cannot access Circle features, Notion links redirect to a guest page, and Pulse software is "
            "unavailable. The coach, Phil Charlton, acknowledged the issue was caused by a wrong email address "
            "and resolved it on March 5. The merchant's claim of \"immediate access\" on March 2 is contradicted "
            "by their own exhibit.",
            s["body"]
        ),
    ]


def rebuttal_section_9(s):
    """Evidence manufacturing"""
    return [
        Paragraph("9. POST-CHARGEBACK PLATFORM ACTIVITY IS NOT EVIDENCE OF SERVICE DELIVERY", s["h1"]),
        Paragraph(
            "After chargebacks were filed on March 14, the merchant's platform continued generating "
            "automated activity that may appear to represent ongoing service delivery but does not:",
            s["body"]
        ),
        Paragraph("• <b>Automated Circle.so bot messages</b> (March 15, 17, 19) — generic drip sequence emails "
                   "from \"Propane Support Genie,\" not personalized coaching", s["bullet"]),
        Paragraph("• <b>New CSM assigned</b> (March 19) — Jonny Simpson assigned as \"Customer Success Manager\" "
                   "5 days after chargebacks were filed, creating a paper trail of \"service delivery\"", s["bullet"]),
        Paragraph("• <b>Marketing emails continued</b> — workshop invitations and community digests sent throughout "
                   "the dispute period", s["bullet"]),
        Spacer(1, 4),
        Paragraph(
            "The cardholder has not logged into Circle.so, attended any session, or responded to any Circle "
            "message since filing the refund request on March 6. The merchant's evidence of \"engagement\" "
            "consists of: (a) an account profile created during onboarding, (b) one onboarding Zoom call "
            "during which the misrepresentation was discovered, and (c) polite courtesy messages during the "
            "first 4 days before the refund request.",
            s["body"]
        ),
    ]


def conclusion(s):
    return [
        Paragraph("10. CONCLUSION — REQUEST TO UPHOLD CHARGEBACKS", s["h1"]),
        HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=10),
        Paragraph(
            "The merchant's chargeback response, when examined alongside their own exhibits, "
            "confirms rather than refutes the cardholder's position:",
            s["body_bold"]
        ),
        Spacer(1, 4),
        Paragraph("1. <b>Payment was collected before terms were signed.</b> The March 5 signature was obtained "
                   "under economic duress — £6,300 was already taken on March 2. The merchant's own coach "
                   "acknowledged the terms should have been signed \"upon point of sale.\"", s["bullet"]),
        Paragraph("2. <b>The core service was materially different from what was sold.</b> Jim Galvin's sales email "
                   "promised a \"Dedicated 1-2-1 coach\" with \"calls to customise the process.\" The merchant's "
                   "own terms describe a messaging thread. The merchant's own Exhibit E shows the cardholder "
                   "asking how to schedule live calls and discovering no system exists.", s["bullet"]),
        Paragraph("3. <b>The refund form was withheld for 8 days</b> despite being required \"on request\" (Section 7.4). "
                   "When provided, it required surrendering chargeback protections with no guarantee of refund.", s["bullet"]),
        Paragraph("4. <b>Immediate access was promised and not delivered.</b> The merchant's own exhibits show "
                   "days of troubleshooting access issues.", s["bullet"]),
        Paragraph("5. <b>The merchant's own Section 11.4</b> acknowledges they cannot exclude liability for "
                   "\"misrepresentation as to a fundamental matter.\"", s["bullet"]),
        Paragraph("6. <b>The merchant's own Section 12.5 Exceptions</b> state that \"statutory rights that cannot "
                   "be waived by agreement\" are exempt from the dispute resolution process. A chargeback is "
                   "a statutory banking right.", s["bullet"]),
        Spacer(1, 8),
        Paragraph(
            "I respectfully request that American Express uphold both chargebacks totaling £6,300 "
            "(approximately $8,741.76 USD including foreign transaction fees) and restore the credits "
            "to my account.",
            s["body_bold"]
        ),
        Spacer(1, 12),
        Paragraph("Respectfully submitted,", s["body"]),
        Spacer(1, 6),
        Paragraph("<b>William J. Marceau</b>", s["body"]),
        Paragraph("wmarceau@marceausolutions.com", s["body"]),
        Paragraph("Naples, Florida, US", s["body"]),
        Paragraph("April 3, 2026", s["body"]),
        Spacer(1, 16),
        HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"), spaceAfter=6),
        Paragraph(
            "This rebuttal references exhibits submitted by Propane Fitness Ltd in their Chargeback Dispute Response "
            "(Attachments 1-4, Case D-93497818 and D-93497819). All timestamps verified from the cardholder's "
            "Gmail inbox via authenticated records.",
            s["footer"]
        ),
    ]


def build_pdf():
    output_path = Path(__file__).parent / "propane-rebuttal-april2026.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title="Cardholder Rebuttal — Propane Fitness Dispute",
        author="William J. Marceau",
    )

    s = get_styles()
    story = []

    # Build document
    story.extend(header_block(s))
    story.extend(case_info(s))
    story.extend(executive_summary(s))
    story.extend(rebuttal_section_1(s))
    story.append(PageBreak())
    story.extend(rebuttal_section_2(s))
    story.append(PageBreak())
    story.extend(rebuttal_section_3(s))
    story.append(PageBreak())
    story.extend(rebuttal_section_4(s))
    story.extend(timeline_table(s))
    story.extend(rebuttal_section_5(s))
    story.extend(rebuttal_section_6(s))
    story.extend(comparison_table(s))
    story.extend(rebuttal_section_7(s))
    story.append(PageBreak())
    story.extend(rebuttal_section_8a(s))
    story.append(PageBreak())
    story.extend(rebuttal_section_9(s))
    story.extend(conclusion(s))

    doc.build(story)
    print(f"Rebuttal PDF generated: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    return output_path


if __name__ == "__main__":
    build_pdf()
