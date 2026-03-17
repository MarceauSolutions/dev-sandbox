#!/usr/bin/env python3
"""
Generate UPDATED Propane Fitness chargeback evidence package PDF.
Includes March 13-16 correspondence + dispute defense strategy.
Updated: March 16, 2026
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from execution.branded_pdf_engine import (
    BrandConfig, _register_fonts, get_brand_styles,
    branded_table, accent_line, section_title, bullet_list,
    _on_page
)

_register_fonts()
S = get_brand_styles()

# Additional styles
email_style = ParagraphStyle(
    "EmailText", fontName=BrandConfig.BODY_FONT,
    fontSize=9, leading=13, textColor=BrandConfig.CHARCOAL,
    leftIndent=6, rightIndent=6,
)
email_bold = ParagraphStyle(
    "EmailBold", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=9, leading=13, textColor=BrandConfig.CHARCOAL,
    leftIndent=6, rightIndent=6,
)
cover_title = ParagraphStyle(
    "CoverTitle", fontName=BrandConfig.HEADING_FONT,
    fontSize=28, leading=34, textColor=BrandConfig.CHARCOAL,
    alignment=TA_CENTER, spaceAfter=8,
)
cover_subtitle = ParagraphStyle(
    "CoverSubtitle", fontName=BrandConfig.BODY_FONT,
    fontSize=13, leading=18, textColor=BrandConfig.DARK_GRAY,
    alignment=TA_CENTER, spaceAfter=6,
)
cover_detail = ParagraphStyle(
    "CoverDetail", fontName=BrandConfig.BODY_FONT,
    fontSize=11, leading=16, textColor=BrandConfig.CHARCOAL,
    alignment=TA_CENTER, spaceAfter=4,
)
cover_amount = ParagraphStyle(
    "CoverAmount", fontName=BrandConfig.HEADING_FONT,
    fontSize=22, leading=28, textColor=BrandConfig.GOLD,
    alignment=TA_CENTER, spaceAfter=4,
)
note_style = ParagraphStyle(
    "NoteStyle", fontName=BrandConfig.BODY_FONT,
    fontSize=8, leading=11, textColor=BrandConfig.DARK_GRAY,
    leftIndent=6, spaceBefore=4, spaceAfter=4,
)
footer_style = ParagraphStyle(
    "FooterNote", fontName=BrandConfig.BODY_FONT,
    fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
    alignment=TA_CENTER, spaceBefore=20,
)
warning_style = ParagraphStyle(
    "Warning", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#92400e"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#fef3c7"), borderPadding=8,
)
strategy_style = ParagraphStyle(
    "Strategy", fontName=BrandConfig.BODY_FONT,
    fontSize=9.5, leading=14, textColor=HexColor("#1e293b"),
    leftIndent=15, rightIndent=15, borderPadding=10,
    backColor=HexColor("#f8f6f0"),
)
body_style = S["body"]
bold_style = S["body_bold"]
h3 = S["h3"]


def email_box(content_elements):
    """Wrap content in a light-background box to indicate quoted email text."""
    inner = []
    if isinstance(content_elements, list):
        for el in content_elements:
            inner.append(el)
    else:
        inner.append(content_elements)

    rows = [[el] for el in inner]
    t = Table(rows, colWidths=[6.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 1, BrandConfig.MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def red_flag_box(content):
    """Red-bordered warning box for critical evidence points."""
    data = [[Paragraph(content, ParagraphStyle(
        "RedFlag", fontName=BrandConfig.BODY_FONT_BOLD,
        fontSize=10, leading=14, textColor=HexColor("#991b1b"),
    ))]]
    t = Table(data, colWidths=[6.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 2, HexColor("#ef4444")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def build():
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("AMEX DISPUTE", cover_title))
    story.append(Paragraph("UPDATED EVIDENCE PACKAGE", cover_title))
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="60%", thickness=3, color=BrandConfig.GOLD, spaceBefore=4, spaceAfter=16))
    story.append(Paragraph("PROPANEFITNESS.COM NEWCASTLE GB", cover_subtitle))
    story.append(Paragraph("Two Charges, March 2, 2026", cover_subtitle))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Total Disputed Amount", cover_detail))
    story.append(Paragraph("$8,741.76", cover_amount))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Cardholder: William Marceau", cover_detail))
    story.append(Paragraph("wmarceau@marceausolutions.com", cover_detail))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Amex ending 1007 \u2014 $4,370.88", cover_detail))
    story.append(Paragraph("Amex ending 1049 \u2014 $4,370.88", cover_detail))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Filed: March 14, 2026", cover_detail))
    story.append(Paragraph("Updated: March 16, 2026 \u2014 Includes Post-Filing Correspondence", cover_detail))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "This updated package contains all original evidence plus new correspondence from "
        "March 13\u201316, including the merchant\u2019s attempt to condition refund eligibility "
        "on withdrawal of the chargeback.",
        ParagraphStyle("CoverNote", fontName=BrandConfig.BODY_FONT, fontSize=10, leading=14,
                        textColor=BrandConfig.DARK_GRAY, alignment=TA_CENTER)
    ))
    story.append(PageBreak())

    # ========== TABLE OF CONTENTS ==========
    story.append(section_title("Table of Contents", S))
    story.append(Spacer(1, 6))
    toc_items = [
        "Section 1: Dispute Summary",
        "Section 2: Transaction Details",
        "Section 3: Complete Timeline of Events (Feb 22 \u2013 Mar 16)",
        "Section 4: The Core Misrepresentation",
        "Section 5: Merchant\u2019s Own Terms Violated",
        "Section 6: Communication Attempts (10 Emails Sent)",
        "Section 7: Full Email Text \u2014 Cardholder\u2019s Refund Requests",
        "Section 8: Merchant\u2019s Responses (Full Text)",
        "Section 9: Post-Filing Correspondence (March 13\u201316)",
        "Section 10: Analysis of Merchant\u2019s Escalating Tactics",
        'Section 10B: Analysis of Merchant\u2019s "Refund Form" (Gag Clause + Impossible Conditions)',
        "Section 11: Anticipated Merchant Arguments & Rebuttals (10 Arguments Countered)",
        "Section 12: Key Observations for Amex Analyst (23 Points)",
        "Section 13: Documents Available Upon Request",
    ]
    for i, item in enumerate(toc_items, 1):
        story.append(Paragraph(f"{i}. {item}", ParagraphStyle(
            "TOC", parent=body_style, leftIndent=18, spaceBefore=3, spaceAfter=3,
        )))
    story.append(PageBreak())

    # ========== SECTION 1: DISPUTE SUMMARY ==========
    story.append(section_title("Section 1: Dispute Summary", S))
    story.append(Spacer(1, 6))

    summary_points = [
        "Purchased 12-week business mentorship from PropaneFitness for \u00a36,300 (~$8,741.76 including foreign transaction fees).",
        'Seller promised "Dedicated 1-2-1 coach for 12 weeks" with "calls to customise the process to your business" in a written sales email sent minutes before payment.',
        "After payment, the assigned coach confirmed during the onboarding call that consistent weekly 1-on-1 Zoom calls are no longer offered \u2014 the program relies on group coaching clinics and community chat instead.",
        "Refund requested March 6 (Day 4 of the merchant\u2019s own 14-day refund window) \u2014 merchant failed to honor their own refund policy.",
        "Merchant never provided the refund request form required by their own Section 7.4.",
        "Merchant failed to provide a substantive response within 7 days as required by their own Section 12.5.",
        "After 8 days of non-response across 4 formal emails, the cardholder proceeded with a chargeback dispute on March 14.",
        "<b>NEW (March 16):</b> Merchant is now requesting the cardholder withdraw the chargeback as a precondition for even reviewing the refund request \u2014 a classic reversal trap that would strip cardholder protection.",
    ]
    for item in summary_points:
        story.append(Paragraph(f"\u2022  {item}", ParagraphStyle(
            "SummaryBullet", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=3, spaceAfter=3,
        )))

    story.append(Spacer(1, 12))
    story.append(Paragraph('<b>Dispute Reason:</b> Services/Goods Not as Described (Amex Reason Code C31)', bold_style))
    story.append(PageBreak())

    # ========== SECTION 2: TRANSACTION DETAILS ==========
    story.append(section_title("Section 2: Transaction Details", S))
    story.append(Spacer(1, 6))

    txn_table = branded_table(
        ["Detail", "Card ending 1007", "Card ending 1049"],
        [
            ["Base Charge", "\u00a33,150.00 ($4,255.97)", "\u00a33,150.00 ($4,255.97)"],
            ["Foreign Transaction Fee", "$114.91", "$114.91"],
            ["Total Charged", "$4,370.88", "$4,370.88"],
            ["Transaction Time (UTC)", "March 2, 2026 15:32", "March 2, 2026 15:40"],
            ["Stripe Receipt", "#1257-2744", "#1001-9268"],
        ],
        col_widths=[2.0 * inch, 2.25 * inch, 2.25 * inch]
    )
    story.append(txn_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph('<b>Merchant:</b> PROPANEFITNESS.COM NEWCASTLE GB', body_style))
    story.append(Paragraph('<b>Stripe Account:</b> acct_182oNdF42QmTryTb', body_style))
    story.append(Paragraph('<b>Combined Total Disputed:</b> $8,741.76', bold_style))
    story.append(PageBreak())

    # ========== SECTION 3: COMPLETE TIMELINE ==========
    story.append(section_title("Section 3: Complete Timeline of Events", S))
    story.append(Spacer(1, 6))

    timeline_rows = [
        ["Feb 22", "Propane lead magnet download (sales funnel entry)", "Email from jonny@propanefitness.com"],
        ["Feb 23", "Sales call booked", "Email from PropaneBusiness"],
        ["Feb 24", "Pre-call resources sent by Joe Halford", "Email from joe@propanefitness.com"],
        ["Feb 25", "Discovery call with Jim Galvin via Zoom", "Email with Zoom link from jim@"],
        ["Mar 2, 14:05", "Follow-up Zoom call with Jim", 'Email "Zoom Link (Again)" from jim@'],
        ["Mar 2, 15:18", 'Jim\'s sales email \u2014 promises "Dedicated 1-2-1 coach for 12 weeks" with "calls to customise the process to your business" and "immediate access" after payment', "Email from jim@propanefitness.com"],
        ["Mar 2, 15:27", "Terms link sent (9 min after pricing)", 'Email from jim@ "Full Terms"'],
        ["Mar 2, 15:29", "First payment link sent (2 min after terms)", 'Email from jim@ "Payment Link"'],
        ["Mar 2, 15:30", "Second payment link sent (1 min later)", 'Email from jim@ "SECOND CARD"'],
        ["Mar 2, 15:32", "First charge processed \u2014 \u00a33,150 on card 1007", "Stripe receipt #1257-2744"],
        ["Mar 2, 15:40", "Second charge processed \u2014 \u00a33,150 on card 1049", "Stripe receipt #1001-9268"],
        ["Mar 2\u20133", '"Immediate access" NOT provided despite written promise', "No access email received"],
        ["Mar 3\u20134", "Full day of follow-up required to get access", "Email thread with Propane support"],
        ["Mar 4", "Coach Reeni Harania sends welcome email", "Email from reeni@propanefitness.com"],
        ["Mar 5", "Terms signed via Jotform \u2014 3 DAYS AFTER PAYMENT", "Jotform Invoice INV-6485333402225932830"],
        ["Mar 5", "Onboarding Zoom with assigned coach. Coach confirms weekly 1-on-1 Zoom calls are no longer offered; program relies on group clinics. No calendar/booking system for 1-on-1 calls exists.", "Zoom call"],
        ["Mar 6", "Formal refund request sent (Day 4 of 14) \u2014 5 grounds cited", "Email to jim@ + admin@"],
        ["Mar 7", "Jim replies \u2014 addresses ONLY foreign transaction fees, ignores all grounds", "Email from jim@"],
        ["Mar 7", "Cardholder follow-up \u2014 7 grounds restated, March 13 deadline set", "Sent email to jim@ + admin@"],
        ["Mar 9", "Propane continues sending automated marketing emails", "Email from admin@propanefitness.com"],
        ["Mar 11", "Propane continues sending automated marketing emails", "Email from admin@propanefitness.com"],
        ["Mar 12", "Escalation email sent \u2014 5 cited terms breaches, formal refund form requested", "Sent email to jim@ + admin@"],
        ["Mar 12", "Coach Phil messages cardholder on Circle.so (informal platform)", "Circle.so message"],
        ["Mar 13", "Final notice sent \u2014 deadline expired, proceeding with dispute", "Sent email to jim@ + admin@"],
        ["Mar 13", 'Propane sends automated marketing email ("Looking for feedback?")', "Email from admin@propanefitness.com"],
        ["Mar 14, 08:39", 'Jim replies: "This has nothing to do with me, mate." Reply sent ONLY to cardholder \u2014 admin@ deliberately removed from CC.', "Email from jim@propanefitness.com"],
        ["Mar 14, 09:16", "Cardholder re-adds admin@ to CC, holds Jim accountable for conducting the sale and collecting \u00a36,300", "Sent email to jim@ + admin@"],
        ["Mar 14, 09:57", 'Coach Phil leaves voicemail. Admits he was "completely unaware" of the dispute.', "Voicemail recording"],
        ["Mar 14, 10:26", "Cardholder responds to voicemail via email: all comms via email only, chargebacks filed, offers to withdraw if full refund issued", "Sent email to jim@ + admin@ + reeni@"],
        ["Mar 14", "Chargebacks filed with Amex on both cards", "Amex dispute filings"],
        ["Mar 14, 10:38", 'Propane sends automated marketing email ("People buy with emotion")', "Email from admin@propanefitness.com"],
        ["Mar 15, 15:35", "Propane Support Genie sends automated coaching content via Circle.so", "Circle.so notification email"],
        ["Mar 16, 10:00", '<b>Phil asks cardholder to WITHDRAW the chargeback before they will "review" the refund request</b>', "Email from coach@propanefitness.com"],
        ["Mar 16, 12:08", "Cardholder declines to withdraw \u2014 reiterates: refund first, then disputes withdrawn", "Email to coach@ + admin@"],
        ["Mar 16, 12:28", '<b>ESCALATION: Propane admin threatens Section 7.5 breach of contract, refund rejection, counterclaim for \u00a36,300 + legal costs, and collections agency referral. Also provides refund form (tally.so) \u2014 10 days after it was formally requested.</b>', "Email from admin@propanefitness.com"],
        ["Mar 16, 12:36", "Cardholder rebuts Section 7.5 claim point-by-point, cites Section 12.5 Exceptions, notes Propane breached first, maintains refund-first position", "Email to admin@ + coach@"],
        ["Mar 16, 13:50", '<b>Propane admin claims delays were cardholder\u2019s fault for contacting Jim instead of Phil. ADMITS refund request was within 14-day window. Directs cardholder to "Proof of Work form" (not refund form). Repeats contract default and collections threats.</b>', "Email from admin@propanefitness.com"],
        ["Mar 16", "Cardholder rebuts \u2018wrong person\u2019 claim: admin@ CC\u2019d on every email; Phil\u2019s voicemail proves admin failed to escalate; highlights Propane\u2019s written admission of timely refund request; final substantive correspondence", "Email to admin@ + coach@"],
    ]

    timeline_table = branded_table(
        ["Date / Time", "Event", "Evidence"],
        timeline_rows,
        col_widths=[1.0 * inch, 3.5 * inch, 2.0 * inch]
    )
    story.append(timeline_table)
    story.append(PageBreak())

    # ========== SECTION 4: CORE MISREPRESENTATION ==========
    story.append(section_title("Section 4: The Core Misrepresentation", S))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>WHAT WAS PROMISED</b> (Jim\u2019s sales email, March 2, 15:18):', bold_style))
    story.append(Spacer(1, 6))

    promise_box = email_box([
        Paragraph('<i>"Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, feedback and calls to customise the process to your business."</i>', email_style),
        Spacer(1, 6),
        Paragraph('<i>"Once you\u2019ve processed the payment you\u2019ll receive immediate access via email with login information and next steps."</i>', email_style),
    ])
    story.append(promise_box)
    story.append(Spacer(1, 16))

    story.append(Paragraph('<b>WHAT WAS DELIVERED:</b>', bold_style))
    story.append(Spacer(1, 6))
    delivered_items = [
        "Assigned coach confirmed during onboarding that consistent weekly 1-on-1 Zoom calls are no longer offered.",
        "Program relies on group coaching clinics and community interaction.",
        "No calendar or booking system exists to schedule 1-on-1 Zoom calls.",
        'The merchant\u2019s own terms describe "One-on-One Coaching Support" as "a channel [that] facilitates the sharing of voice notes, document reviews, messages" \u2014 a messaging thread, not scheduled coaching calls.',
        "Access was NOT provided immediately after payment \u2014 required a full day of follow-up.",
    ]
    for item in delivered_items:
        story.append(Paragraph(f"\u2022  {item}", ParagraphStyle(
            "DeliveredBullet", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=3, spaceAfter=3,
        )))
    story.append(PageBreak())

    # ========== SECTION 5: MERCHANT'S OWN TERMS VIOLATED ==========
    story.append(section_title("Section 5: Merchant\u2019s Own Terms Violated", S))
    story.append(Spacer(1, 6))

    terms_table = branded_table(
        ["Section", "What It Requires", "How Merchant Breached It"],
        [
            ["7.1\n(14-Day Refund)", '"Full refund if the refund request form has been successfully completed within the first 14 days"', "Cardholder requested refund on Day 4. Merchant did not honor it."],
            ["7.4\n(Refund Form)", 'Must provide refund request form "on request"', "Cardholder formally requested the form on March 12. Never provided."],
            ["11.4\n(Misrepresentation)", '"Nothing in these Terms shall exclude or limit our liability for\u2026 misrepresentation as to a fundamental matter"', "The nature of coaching (1-on-1 Zoom vs group clinics) is a fundamental matter. Merchant\u2019s own terms acknowledge this liability cannot be excluded."],
            ["12.5 Step 1\n(Dispute Response)", 'Respondent must "provide substantive response within 7 days"', "Merchant\u2019s only reply (March 7) addressed FX fees alone. No substantive response to any of the 7 refund grounds within 7 days."],
        ],
        col_widths=[1.1 * inch, 2.4 * inch, 3.0 * inch]
    )
    story.append(terms_table)
    story.append(PageBreak())

    # ========== SECTION 6: COMMUNICATION ATTEMPTS ==========
    story.append(section_title("Section 6: Communication Attempts (8 Emails Sent)", S))
    story.append(Spacer(1, 6))

    comm_table = branded_table(
        ["Date", "From", "To / CC", "Subject", "Merchant Response"],
        [
            ["March 6", "Cardholder", "jim@ + admin@", "Formal Refund Request", "Jim replied March 7 \u2014 addressed ONLY FTFs, ignored all 5 refund grounds"],
            ["March 7", "Cardholder", "jim@ + admin@", "Re: Formal Refund Request", "No response"],
            ["March 12", "Cardholder", "jim@ + admin@", "Re: Formal Refund Request", "Coach messaged on Circle.so (informal). No email response."],
            ["March 13", "Cardholder", "jim@ + admin@", "Formal notice (deadline)", 'Jim replied Mar 14: "Nothing to do with me" \u2014 removed admin@ from CC'],
            ["March 14\n09:16", "Cardholder", "jim@ + admin@", "Re-added admin@, held Jim accountable", "No response from Jim or admin"],
            ["March 14\n10:26", "Cardholder", "jim@ + admin@\n+ reeni@", "Response to Phil\u2019s voicemail", "Phil replied March 16 \u2014 asked cardholder to withdraw chargeback"],
            ["March 16", "Cardholder", "coach@ + admin@", "Declined withdrawal, reiterated refund-first position", "Pending"],
        ],
        col_widths=[0.7 * inch, 0.7 * inch, 0.9 * inch, 1.4 * inch, 2.8 * inch]
    )
    story.append(comm_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Total formal emails sent by cardholder: 8</b> (March 6, 7, 12, 13, 14 x2, 14 response to voicemail, March 16). "
        "Merchant substantive responses: <b>zero</b>. The only responses were Jim deflecting responsibility and Phil "
        "requesting the chargeback be withdrawn.",
        bold_style
    ))
    story.append(PageBreak())

    # ========== SECTION 7: FULL EMAIL TEXT ==========
    story.append(section_title("Section 7: Full Email Text \u2014 Cardholder\u2019s Refund Requests", S))
    story.append(Spacer(1, 6))

    # --- Email 1 ---
    story.append(Paragraph('<b>Email 1 \u2014 March 6, 2026 (Original Refund Request)</b>', h3))
    story.append(Paragraph(
        '<i>Note: Original sent email was accidentally deleted from sent folder. This text is from the preserved draft '
        '(still in Gmail trash, dated March 6, 2026 16:52). Jim\u2019s March 7 reply referencing foreign transaction fees confirms receipt.</i>',
        note_style
    ))
    story.append(Spacer(1, 4))

    email1_text = [
        Paragraph("Hi Jim,", email_style),
        Spacer(1, 4),
        Paragraph(
            "I\u2019m writing to formally request a full refund of the \u00a36,300 I paid on March 2, 2026, for the following reasons:", email_style),
        Spacer(1, 4),
        Paragraph("<b>1. Service Not as Described</b>", email_bold),
        Paragraph(
            "During our sales calls and in your follow-up email, the program was presented as including dedicated 1-on-1 coaching "
            "with regular Zoom calls to customize the process to my business. After payment, my assigned coach confirmed that "
            "consistent weekly 1-on-1 Zoom calls are no longer offered \u2014 the program now relies primarily on group coaching "
            "clinics and community chat. This is a material difference from what was sold.", email_style),
        Spacer(1, 4),
        Paragraph("<b>2. Terms Not Agreed Before Payment</b>", email_bold),
        Paragraph(
            "I was sent the terms link at 15:27, the first payment link at 15:29 (2 minutes later), and the second payment link "
            "at 15:30 (1 minute after that). The terms were not formally signed until March 5 \u2014 three days after payment was "
            "collected. I did not have adequate time to review the terms before committing \u00a36,300.", email_style),
        Spacer(1, 4),
        Paragraph("<b>3. Within 14-Day Refund Window</b>", email_bold),
        Paragraph(
            "Per your own terms (Section 7.1), a full refund is available within the first 14 days. This request is being made "
            "on Day 4.", email_style),
        Spacer(1, 4),
        Paragraph("<b>4. Immediate Access Not Provided</b>", email_bold),
        Paragraph(
            'Your email stated: "Once you\u2019ve processed the payment you\u2019ll receive immediate access via email with login '
            'information and next steps." Access was not provided immediately. It required a full day of follow-up on my part to '
            "receive login credentials.", email_style),
        Spacer(1, 4),
        Paragraph("<b>5. Foreign Transaction Fees</b>", email_bold),
        Paragraph(
            "The charges were processed in GBP, resulting in $229.82 in foreign transaction fees that were not disclosed prior to "
            "payment. The total cost was presented as \u00a36,300 with no mention of currency conversion costs.", email_style),
        Spacer(1, 4),
        Paragraph(
            "I am requesting a full refund of \u00a36,300 plus reimbursement of the $229.82 in foreign transaction fees. "
            "Please confirm receipt of this request and provide a timeline for processing.", email_style),
        Spacer(1, 4),
        Paragraph("Regards,<br/>William Marceau", email_style),
    ]
    story.append(email_box(email1_text))
    story.append(Spacer(1, 16))

    # --- Email 2 ---
    story.append(Paragraph('<b>Email 2 \u2014 March 7, 2026 (Follow-Up with 7 Grounds)</b>', h3))
    story.append(Spacer(1, 4))

    email2_text = [
        Paragraph("Jim,", email_style),
        Spacer(1, 4),
        Paragraph(
            "Thank you for your reply. I\u2019ll set the foreign transaction fee point aside \u2014 that\u2019s a secondary issue. "
            "However, your response did not address any of the substantive grounds for my refund request. Let me restate them "
            "clearly, with additional detail:", email_style),
        Spacer(1, 6),
        Paragraph("<b>1. BAIT-AND-SWITCH ON COACHING FORMAT</b>", email_bold),
        Paragraph(
            'Your sales email (March 2, 15:18) promised "Dedicated 1-2-1 coach for 12 weeks" with "calls to customise the '
            'process to your business." During the onboarding Zoom on March 5, my assigned coach confirmed that consistent '
            "weekly 1-on-1 Zoom calls are no longer part of the program. The coaching is delivered via group clinics and a "
            "messaging thread. This is materially different from what was promised in writing.", email_style),
        Spacer(1, 4),
        Paragraph("<b>2. TERMS NOT AGREED BEFORE PAYMENT</b>", email_bold),
        Paragraph(
            "The terms link was sent at 15:27. The first payment link followed at 15:29 (2 minutes). The second payment link "
            "at 15:30 (1 minute). Both payments were processed by 15:40. The terms were not formally signed until March 5 \u2014 "
            "three full days after \u00a36,300 was collected. A 22-minute window from pricing to full payment does not constitute "
            "adequate time to review and agree to terms for a \u00a36,300 purchase.", email_style),
        Spacer(1, 4),
        Paragraph("<b>3. 14-DAY REFUND POLICY</b>", email_bold),
        Paragraph(
            "Your own terms (Section 7.1) state: \u201cFull refund if the refund request form has been successfully completed "
            "within the first 14 days.\u201d My refund request was sent on Day 4. This is well within your own policy window.",
            email_style),
        Spacer(1, 4),
        Paragraph("<b>4. MISREPRESENTATION LIABILITY</b>", email_bold),
        Paragraph(
            "Your terms (Section 11.4) state: \u201cNothing in these Terms shall exclude or limit our liability for\u2026 "
            "misrepresentation as to a fundamental matter.\u201d The nature of the coaching \u2014 whether it\u2019s 1-on-1 Zoom "
            "calls or group clinics \u2014 is a fundamental matter. Your own terms acknowledge this liability cannot be excluded.",
            email_style),
        Spacer(1, 4),
        Paragraph("<b>5. INADEQUATE TIME TO REVIEW TERMS</b>", email_bold),
        Paragraph(
            "9 minutes between the terms link and the first payment link. 2 minutes between terms and the payment request. "
            "For a \u00a36,300 commitment, this constitutes a high-pressure sales sequence that did not allow adequate review.",
            email_style),
        Spacer(1, 4),
        Paragraph("<b>6. ACCESS NOT PROVIDED AS PROMISED</b>", email_bold),
        Paragraph(
            'Your email promised "immediate access via email with login information and next steps" after payment. '
            "Access was not provided for over 24 hours and required active follow-up from me.", email_style),
        Spacer(1, 4),
        Paragraph("<b>7. NO COURSE CONTENT CONSUMED</b>", email_bold),
        Paragraph(
            "I have not accessed, consumed, or benefited from any course material. The program has not been used.",
            email_style),
        Spacer(1, 6),
        Paragraph("<b>WHAT I\u2019M ASKING:</b>", email_bold),
        Paragraph(
            "A full refund of \u00a36,300 processed within 7 business days. This is a reasonable request made within your own "
            "refund window, supported by documented misrepresentation of the service.", email_style),
        Spacer(1, 4),
        Paragraph("<b>WHAT HAPPENS IF NOT RESOLVED:</b>", email_bold),
        Paragraph(
            "If this is not resolved by March 13, 2026, I will proceed with a chargeback dispute through American Express "
            "and file a formal complaint. I would prefer to resolve this directly.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau", email_style),
    ]
    story.append(email_box(email2_text))
    story.append(PageBreak())

    # --- Email 3 ---
    story.append(Paragraph('<b>Email 3 \u2014 March 12, 2026 (Escalation with Terms Breaches)</b>', h3))
    story.append(Spacer(1, 4))

    email3_text = [
        Paragraph("Jim,", email_style),
        Spacer(1, 4),
        Paragraph(
            "I am writing to follow up on my formal refund request sent on March 6, 2026, and my detailed follow-up of "
            "March 7, 2026. Neither has received a substantive response addressing the grounds for refund.", email_style),
        Spacer(1, 4),
        Paragraph("<b>1. I am within the 14-day refund window.</b>", email_bold),
        Paragraph(
            "Payment was made March 2. Today is March 12 \u2014 Day 10. Your terms (Section 7.1) guarantee a full refund "
            "within 14 days.", email_style),
        Spacer(1, 4),
        Paragraph("<b>2. You are in breach of your own dispute resolution process.</b>", email_bold),
        Paragraph(
            "Section 12.5 (Step 1) requires the respondent to \u201cprovide substantive response within 7 days.\u201d "
            "My formal refund request was sent March 6. Your only reply (March 7) addressed foreign transaction fees and "
            "ignored all substantive grounds. It has now been 6 days with no further response.", email_style),
        Spacer(1, 4),
        Paragraph("<b>3. The service is materially different from what was sold.</b>", email_bold),
        Paragraph(
            'The sales email promised "Dedicated 1-2-1 coach for 12 weeks" with "calls to customise the process to your '
            'business." The assigned coach confirmed during onboarding that weekly 1-on-1 Zoom calls are not part of the '
            "current program.", email_style),
        Spacer(1, 4),
        Paragraph("<b>4. I have not accessed or consumed any course content.</b>", email_bold),
        Spacer(1, 4),
        Paragraph("<b>5. My formal emails have gone unanswered.</b>", email_bold),
        Spacer(1, 4),
        Paragraph(
            "Please also provide the refund request form referenced in Section 7.4 of your terms. I am formally requesting it now.", email_style),
        Spacer(1, 4),
        Paragraph(
            "If a full refund is not confirmed by the close of business March 13, 2026, I will proceed with a chargeback "
            "dispute through American Express.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau", email_style),
    ]
    story.append(email_box(email3_text))
    story.append(Spacer(1, 16))

    # --- Email 4 ---
    story.append(Paragraph('<b>Email 4 \u2014 March 13, 2026 (Final Notice)</b>', h3))
    story.append(Spacer(1, 4))

    email4_text = [
        Paragraph("Jim,", email_style),
        Spacer(1, 4),
        Paragraph(
            "This email serves as formal notice that the March 13, 2026 deadline set in my emails of March 7 and March 12 "
            "has now passed without resolution.", email_style),
        Spacer(1, 4),
        Paragraph("To summarize the situation:", email_style),
        Spacer(1, 4),
        Paragraph(
            "\u2022  Refund request first sent March 6, 2026 (Day 4 of your 14-day refund window)<br/>"
            "\u2022  Detailed follow-up with 7 documented grounds sent March 7<br/>"
            "\u2022  Escalation with cited terms breaches sent March 12<br/>"
            "\u2022  No substantive response has been received to any refund ground<br/>"
            "\u2022  The refund request form required by Section 7.4 has not been provided<br/>"
            "\u2022  Your own dispute resolution timeline (Section 12.5) has been breached",
            email_style),
        Spacer(1, 4),
        Paragraph(
            "I have made every reasonable effort to resolve this directly. I will now proceed with a chargeback dispute "
            "through American Express for both charges totaling \u00a36,300.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau", email_style),
    ]
    story.append(email_box(email4_text))
    story.append(PageBreak())

    # ========== SECTION 8: MERCHANT'S RESPONSES ==========
    story.append(section_title("Section 8: Merchant\u2019s Responses (Full Text)", S))
    story.append(Spacer(1, 6))

    story.append(Paragraph('<b>Jim\u2019s Reply \u2014 March 7, 2026</b>', h3))
    story.append(Paragraph(
        '<i>Note: Jim\u2019s March 7 reply is not available in cardholder\u2019s inbox (accidentally deleted). However, the '
        'cardholder\u2019s March 7 follow-up email opens with "Thank you for your reply. I\u2019ll set the foreign transaction '
        'fee point aside" \u2014 confirming Jim responded and that his response addressed only foreign transaction fees while '
        'ignoring all substantive refund grounds.</i>',
        note_style
    ))
    story.append(Spacer(1, 16))

    story.append(Paragraph('<b>Jim\u2019s Reply \u2014 March 14, 2026, 08:39 UTC</b>', h3))
    story.append(Spacer(1, 4))
    jim_reply = [
        Paragraph(
            "William,<br/><br/>"
            "This has nothing to do with me, mate. The admin team will assist. You need to speak to your Coach about this."
            "<br/><br/>-- Jim Galvin",
            email_style
        ),
    ]
    story.append(email_box(jim_reply))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        '<i>Note: Jim is the person who conducted the sales call, quoted pricing, sent the terms link, sent both payment '
        'links, and collected \u00a36,300. His reply was sent only to the cardholder \u2014 admin@propanefitness.com was '
        'deliberately removed from CC despite being CC\u2019d on all prior correspondence.</i>',
        note_style
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph('<b>Phil\u2019s Voicemail \u2014 March 14, 2026, 09:57 AM ET</b>', h3))
    story.append(Paragraph('<i>Full transcription:</i>', note_style))
    story.append(Spacer(1, 4))

    voicemail_text = [
        Paragraph(
            '"Hi William, it\u2019s Phil from Propane. Um, just wanted to make contact with you so we can discuss the nature '
            "of the emails that you sent and what your, kind of what your current situation is really and where to go from "
            "here. Um Obviously, I\u2019m very aware it\u2019s the weekend, but I just want to try and catch up with you, uh, "
            "as soon as, as soon as it could really, because I, obviously, I messaged you yesterday. I\u2019ve been completely "
            "unaware of this back and forth or, you know, the messages you\u2019d sent um over the last week or so up until I "
            "saw like a snapshot yesterday when I messaged you. Obviously, since then there\u2019s been one or 2 messages sent "
            "um between yourself and Jim. So I wanted to gain some clarity over exactly what you\u2019re up to, uh, where "
            "you\u2019re up to, sorry, and where we go from here. So I\u2019ll try again on Monday. Uh I\u2019ll give you a "
            "call on Monday. I have messaged you in circle as well, so if you can access that inbox, uh still, and then "
            "respond in there, that\u2019ll be helpful as well. Ideally speaking, William, in situations like this, whenever, "
            "you know, they have cropped up in the past, the routes go down, is in that inbox between you and I, that would "
            "have been the way to go, and I would have seen it much, much quicker, um, than, than the route that it has gone. "
            "Both, we can discuss all this stuff when we speak. So I\u2019ll try again on Monday. Please do have a look at "
            'your inbox in circle and we\u2019ll go from there."',
            email_style
        ),
    ]
    story.append(email_box(voicemail_text))
    story.append(Spacer(1, 10))

    story.append(Paragraph('<b>Key observations from voicemail:</b>', bold_style))
    voicemail_notes = [
        'Phil admits he was "completely unaware" of the dispute \u2014 proving admin@propanefitness.com (CC\u2019d on all 4 emails) failed to escalate.',
        '"In situations like this, whenever they have cropped up in the past" \u2014 admitting this is a recurring pattern.',
        "Phil asks cardholder to respond via Circle.so (informal platform they control) instead of email.",
        "Phil wants to delay to Monday (March 16 \u2014 the last day of the merchant\u2019s own 14-day refund window).",
    ]
    for i, note in enumerate(voicemail_notes, 1):
        story.append(Paragraph(f"{i}.  {note}", ParagraphStyle(
            "VoicemailNote", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=2, spaceAfter=2,
        )))
    story.append(PageBreak())

    # ========== SECTION 9: NEW — POST-FILING CORRESPONDENCE ==========
    story.append(section_title("Section 9: Post-Filing Correspondence (March 13\u201316)", S))
    story.append(Spacer(1, 6))
    story.append(red_flag_box(
        "NEW EVIDENCE: This section contains correspondence that occurred AFTER the chargebacks were filed on March 14. "
        "It demonstrates the merchant\u2019s continued failure to engage substantively and their attempt to condition "
        "the refund on withdrawal of cardholder protections."
    ))
    story.append(Spacer(1, 12))

    # --- Email 5: Mar 14 09:16 ---
    story.append(Paragraph('<b>Email 5 \u2014 March 14, 2026, 09:16 ET (Cardholder to Jim + Admin)</b>', h3))
    story.append(Spacer(1, 4))
    email5_text = [
        Paragraph("Jim,", email_style),
        Spacer(1, 4),
        Paragraph(
            "Noted. For the record, you are the person who conducted the sales call, quoted the pricing, sent the terms link, "
            "sent both payment links, and collected \u00a36,300 from me on March 2. This has everything to do with you.", email_style),
        Spacer(1, 4),
        Paragraph(
            "I am re-adding admin@propanefitness.com to this thread, as they were CC\u2019d on all of my previous "
            "correspondence and were removed from your reply.", email_style),
        Spacer(1, 4),
        Paragraph(
            "To the admin team: I have sent formal refund requests on March 6, March 7, and March 12 to both "
            "jim@propanefitness.com and admin@propanefitness.com. No substantive response has been provided, no refund "
            "has been issued, and the refund request form required by your own Section 7.4 has never been provided despite "
            "my formal request.", email_style),
        Spacer(1, 4),
        Paragraph(
            "The March 13 deadline has passed. I am proceeding with formal dispute proceedings through my card issuer today.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau<br/>wmarceau@marceausolutions.com", email_style),
    ]
    story.append(email_box(email5_text))
    story.append(Spacer(1, 16))

    # --- Email 6: Mar 14 10:26 ---
    story.append(Paragraph('<b>Email 6 \u2014 March 14, 2026, 10:26 ET (Cardholder Response to Phil\u2019s Voicemail)</b>', h3))
    story.append(Spacer(1, 4))
    email6_text = [
        Paragraph("Phil / Admin Team,", email_style),
        Spacer(1, 4),
        Paragraph(
            "I received Phil\u2019s voicemail this morning (March 14, 09:57 AM). I appreciate the outreach, but I want to "
            "address several points.", email_style),
        Spacer(1, 4),
        Paragraph(
            "<b>1.</b> All communication regarding this matter must be conducted via email \u2014 not Circle.so, not voicemail, "
            "not any informal platform. This ensures a proper written record for both parties.", email_style),
        Spacer(1, 4),
        Paragraph(
            '<b>2.</b> Phil stated in his voicemail that he was "completely unaware" of this dispute. I sent formal refund requests '
            "to jim@propanefitness.com AND admin@propanefitness.com on March 6, March 7, March 12, and March 13. If the admin "
            "team did not escalate these for 8 days, that is an internal process failure \u2014 not a reason to delay resolution.", email_style),
        Spacer(1, 4),
        Paragraph(
            "<b>3.</b> Phil suggested continuing the discussion on Monday (March 16). I set a clear deadline of March 13 \u2014 "
            "stated in writing on March 7 and reiterated on March 12. That deadline passed with no refund, no substantive response, "
            "and no refund request form provided as required by your Section 7.4.", email_style),
        Spacer(1, 4),
        Paragraph(
            "<b>4.</b> As stated in my March 13 email, I have proceeded with formal dispute proceedings through my card issuer "
            "on both charges. This is my right as a cardholder \u2014 a statutory right your own terms (Section 12.5, Exceptions) "
            "acknowledge cannot be waived by agreement.", email_style),
        Spacer(1, 4),
        Paragraph(
            "If Propane wishes to resolve this matter quickly, a full refund of \u00a36,300 to the original payment methods will "
            "close this immediately and I will withdraw the disputes. This remains the simplest path for both parties.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau<br/>wmarceau@marceausolutions.com", email_style),
    ]
    story.append(email_box(email6_text))
    story.append(PageBreak())

    # --- Email 7: Phil's chargeback reversal request ---
    story.append(Paragraph('<b>Phil\u2019s Email \u2014 March 16, 2026, 10:00 UTC (Chargeback Reversal Request)</b>', h3))
    story.append(Spacer(1, 4))
    phil_reply = [
        Paragraph("Good morning William,", email_style),
        Spacer(1, 4),
        Paragraph(
            "Can you please confirm whether or not a chargeback has been raised with your credit card provider regarding "
            "your recent payment?", email_style),
        Spacer(1, 4),
        Paragraph(
            "Because a chargeback freezes the transaction, we would be unable to proceed with our standard refund process "
            "until the dispute is resolved.", email_style),
        Spacer(1, 4),
        Paragraph(
            "In order to be eligible for a refund review, if you have raised a chargeback, you will first need to reverse "
            "it on your side.", email_style),
        Spacer(1, 4),
        Paragraph(
            "Once you provide confirmation that the dispute has been withdrawn and the funds are not frozen, we can pick up "
            "where we left off and process your refund request through the normal route.", email_style),
        Spacer(1, 4),
        Paragraph(
            "Please let us know how you wish to proceed.", email_style),
        Spacer(1, 4),
        Paragraph("Phil<br/>-- Coaching Team", email_style),
    ]
    story.append(email_box(phil_reply))
    story.append(Spacer(1, 16))

    # --- Email 8: Cardholder's response ---
    story.append(Paragraph('<b>Email 8 \u2014 March 16, 2026 (Cardholder Declines Withdrawal)</b>', h3))
    story.append(Spacer(1, 4))
    email8_text = [
        Paragraph("Phil,", email_style),
        Spacer(1, 4),
        Paragraph(
            "Thank you for your email.", email_style),
        Spacer(1, 4),
        Paragraph(
            "I will not be withdrawing the disputes. As I stated in my March 14 email, a full refund of \u00a36,300 to the "
            "original payment methods will close this matter immediately, and I will withdraw the disputes upon confirmation "
            "that the refund has been processed. This remains the simplest path for both parties.", email_style),
        Spacer(1, 4),
        Paragraph(
            "To be clear: I requested a refund on March 6 \u2014 Day 4 of your 14-day window. Propane did not provide the "
            "refund form required by Section 7.4, did not give a substantive response within 7 days (Section 12.5), and did "
            "not process the refund by the March 13 deadline. The chargebacks were filed only after Propane failed to act on "
            "its own published policy.", email_style),
        Spacer(1, 4),
        Paragraph(
            "If Propane issues the refund, I will withdraw the disputes. If Propane disputes the chargebacks instead, I have "
            "a complete evidence package documenting the timeline, the misrepresentation, and the breaches of your own terms.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau<br/>wmarceau@marceausolutions.com", email_style),
    ]
    story.append(email_box(email8_text))
    story.append(Spacer(1, 16))

    # --- Email 9: Propane's Section 7.5 threat (Mar 16 12:28) ---
    story.append(Paragraph('<b>Propane Admin \u2014 March 16, 2026, 12:28 UTC (Section 7.5 Threat + Collections)</b>', h3))
    story.append(Spacer(1, 4))
    story.append(red_flag_box(
        "ESCALATION: This email threatens breach of contract, rejection of refund, counterclaim for the full balance, "
        "and referral to a collections agency \u2014 all because the cardholder exercised their statutory right to "
        "file a chargeback dispute."
    ))
    story.append(Spacer(1, 6))
    propane_threat = [
        Paragraph("Hi William,", email_style),
        Spacer(1, 4),
        Paragraph(
            "Here is the refund form for you to complete: https://tally.so/r/mOXkyR", email_style),
        Spacer(1, 4),
        Paragraph(
            "However, since you have now initiated chargebacks, the funds are currently frozen by the bank. This means "
            "we are unable to provide the form or process any refund to your original payment methods until the disputes "
            "are withdrawn and the funds are unfrozen. Their review normally takes up to 90 days.", email_style),
        Spacer(1, 4),
        Paragraph(
            "<b>As previously stated, under Section 7.5 of the terms you accepted at checkout, any attempt to bypass our "
            "refund policy constitutes a breach of contract. This results in the immediate rejection of your refund "
            "request and gives us the right to counterclaim for any outstanding amounts owed to us, plus legal costs.</b>",
            email_bold),
        Spacer(1, 4),
        Paragraph(
            "<b>Option 1 \u2013 Withdraw the chargebacks and complete our refund form (fastest route)</b> If you complete "
            "the refund form, then once your bank unfreezes the funds, we will be able to pick up where we left off and "
            "process your refund request form as normal to assess your eligibility.", email_style),
        Spacer(1, 4),
        Paragraph(
            "<b>Option 2 \u2013 Continue with the chargebacks</b> If you choose to keep the disputes open, we will provide "
            "your bank with full evidence of fulfilment and our terms. Because the chargebacks place the whole contract in "
            "default, we would need to initiate recovery of the full balance of \u00a36,300 and related costs through a "
            "collections agency. This would include collection fees, court fees, and legal expenses on a full indemnity basis.",
            email_style),
        Spacer(1, 4),
        Paragraph(
            "Please reply to let us know which option you intend to take. We would much rather resolve this directly with "
            "you, but as it stands, we cannot progress the refund form until the dispute is withdrawn.", email_style),
        Spacer(1, 4),
        Paragraph("Best regards,<br/>The Propane Team", email_style),
    ]
    story.append(email_box(propane_threat))
    story.append(Spacer(1, 16))

    # --- Email 10: Cardholder's rebuttal ---
    story.append(Paragraph('<b>Email 10 \u2014 March 16, 2026 (Cardholder Rebuttal to Section 7.5 Threat)</b>', h3))
    story.append(Spacer(1, 4))
    email10_text = [
        Paragraph(
            "Thank you for your email and for providing the refund form \u2014 which I formally requested on March 12 "
            "under Section 7.4. It has taken 10 days and 8 formal emails to receive it.", email_style),
        Spacer(1, 4),
        Paragraph(
            "I want to address several points in your message clearly and for the record.", email_style),
        Spacer(1, 4),
        Paragraph("<b>1. SECTION 7.5 DOES NOT OVERRIDE STATUTORY RIGHTS</b>", email_bold),
        Paragraph(
            "Your own terms (Section 12.5, Exceptions) acknowledge that nothing in the agreement can waive a party\u2019s "
            "right to seek remedies through external channels, including card issuer disputes. A chargeback is a statutory "
            "cardholder right \u2014 not a breach of contract. Attempting to characterise it as such is inconsistent with "
            "your own terms and with UK consumer law (Consumer Rights Act 2015, Consumer Contracts Regulations 2013).",
            email_style),
        Spacer(1, 4),
        Paragraph("<b>2. PROPANE BREACHED THE CONTRACT FIRST</b>", email_bold),
        Paragraph(
            "Before any chargeback was filed, Propane:<br/>"
            "\u2014 Failed to deliver the service as described (1-on-1 coaching promised in writing, group clinics delivered)<br/>"
            "\u2014 Failed to provide the refund form within a reasonable time after my March 12 request (Section 7.4)<br/>"
            "\u2014 Failed to provide a substantive response within 7 days (Section 12.5)<br/>"
            "\u2014 Failed to honour its own 14-day refund policy (Section 7.1)<br/><br/>"
            "The chargebacks were filed on March 14 \u2014 only after Propane had been non-responsive across 4 formal emails "
            "over 8 days. A party in breach cannot invoke contract protections against the party it has wronged.",
            email_style),
        Spacer(1, 4),
        Paragraph('<b>3. "ASSESS YOUR ELIGIBILITY" IS NOT A REFUND</b>', email_bold),
        Paragraph(
            "Your email asks me to withdraw my chargeback protections so you can \u201cassess eligibility\u201d and "
            "\u201cprocess your refund request form as normal.\u201d This is not a commitment to refund \u2014 it is a "
            "commitment to review, under conditions (Section 7.2) that require retroactive completion of programme "
            "activities. I will not withdraw protections in exchange for a review process controlled entirely by the party "
            "that has already failed to act for 10 days.", email_style),
        Spacer(1, 4),
        Paragraph("<b>4. COLLECTIONS THREAT</b>", email_bold),
        Paragraph(
            "I note your reference to collections agencies, court fees, and legal costs. For the record: these funds "
            "are not \u201cowed\u201d \u2014 they are actively disputed on documented grounds of misrepresentation and "
            "breach of your own terms. Threatening legal action against a consumer exercising statutory dispute rights is "
            "a matter that regulators, including UK Trading Standards and the CMA, take seriously.", email_style),
        Spacer(1, 4),
        Paragraph("<b>MY POSITION REMAINS UNCHANGED</b>", email_bold),
        Paragraph(
            "A full refund of \u00a36,300 to the original payment methods will close this matter immediately. Upon "
            "confirmation the refund has been processed, I will withdraw the disputes the same day.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau<br/>wmarceau@marceausolutions.com", email_style),
    ]
    story.append(email_box(email10_text))
    story.append(Spacer(1, 16))

    # --- Email 11: Propane's "wrong person" argument (Mar 16 13:50) ---
    story.append(Paragraph('<b>Propane Admin \u2014 March 16, 2026, 13:50 UTC (\u201cWrong Person\u201d + Admission)</b>', h3))
    story.append(Spacer(1, 4))
    story.append(red_flag_box(
        "KEY ADMISSION: Propane writes \u201cbecause your request was initiated within the 14-day window, "
        "there is a clear and valid route for you to obtain a full refund.\u201d This is a written concession "
        "that the refund request was timely. They then attempt to blame the cardholder for contacting the "
        "salesperson who collected \u00a36,300 rather than a coach assigned one day earlier."
    ))
    story.append(Spacer(1, 6))
    propane_wrong_person = [
        Paragraph("Hi William,", email_style),
        Spacer(1, 4),
        Paragraph("Thank you for your email. To address your points:", email_style),
        Spacer(1, 4),
        Paragraph(
            "\u2022 The delays you mention had occurred because you directed your correspondence to a sales "
            "representative, rather than your account manager, Phil. The reason we assign you an account manager "
            "is to handle all queries such as this. It is also a requirement of the refund policy. You are reminded "
            "of this in Section 7.2 of the refund policy, any program-related difficulties or refund requests must "
            "be raised directly with your 121 coach in the members portal or via the official admin email. However, "
            "<b>because your request was initiated within the 14-day window, there is a clear and valid route for you "
            "to obtain a full refund by completing the required Proof of Work form:</b> https://tally.so/r/mOXkyR",
            email_style),
        Spacer(1, 4),
        Paragraph(
            "\u2022 Statutory Rights: We absolutely acknowledge your statutory right to raise a chargeback with your "
            "card issuer. This is your choice to make between you and your card issuer. However, by choosing to "
            "exercise this right instead of following the established refund process constitutes an attempt to bypass "
            "our policy. Under the terms you agreed to at checkout, this immediately places the entire contract "
            "balance in default and entitles us to recover the full outstanding amount.",
            email_style),
        Spacer(1, 4),
        Paragraph(
            "\u2022 Because the bank has now frozen the funds, we cannot process the refund form or issue any money "
            "back to your card. If you withdraw the disputes, we can immediately provide the form and resume your "
            "refund process. If you choose to keep the disputes open, the matter is entirely in the bank\u2019s hands, "
            "and we will pursue the full contract balance.",
            email_style),
        Spacer(1, 4),
        Paragraph("Best regards,<br/>The Propane Coaching Team", email_style),
    ]
    story.append(email_box(propane_wrong_person))
    story.append(Spacer(1, 16))

    # --- Email 12: Cardholder's final rebuttal ---
    story.append(Paragraph('<b>Email 12 \u2014 March 16, 2026 (Cardholder\u2019s Final Rebuttal)</b>', h3))
    story.append(Spacer(1, 4))
    email12_text = [
        Paragraph(
            "Thank you for your reply. I want to address each point for the record.", email_style),
        Spacer(1, 4),
        Paragraph("<b>1. \u201cYOU DIRECTED CORRESPONDENCE TO A SALES REPRESENTATIVE\u201d</b>", email_bold),
        Paragraph(
            "Jim Galvin is the person who conducted the sales call, quoted pricing, sent the terms link, sent both "
            "payment links, and collected \u00a36,300 from me. More importantly: admin@propanefitness.com was CC\u2019d "
            "on every one of my formal emails \u2014 March 6, 7, 12, and 13. Your own Section 7.2 states that refund "
            "requests must be raised \u201cvia the official admin email.\u201d I used admin@propanefitness.com. I complied "
            "with your policy.", email_style),
        Spacer(1, 4),
        Paragraph(
            "Phil was assigned as my coach approximately March 4\u20135. My first refund request was March 6 \u2014 I had "
            "known Phil for one day. Phil himself stated in his March 14 voicemail that he was \u201ccompletely unaware\u201d "
            "of this dispute, despite admin@ being CC\u2019d on all four emails. If admin@ did not route my emails to Phil, "
            "that is an internal process failure at Propane \u2014 not a failure on my part.", email_style),
        Spacer(1, 4),
        Paragraph("<b>2. CHARGEBACKS \u201cBYPASS\u201d YOUR REFUND PROCESS</b>", email_bold),
        Paragraph(
            "I did not bypass your refund process. I followed it: refund requested March 6 (Day 4 of 14), admin@ CC\u2019d "
            "on every email, refund form formally requested March 12 under Section 7.4, 8 formal emails sent over 10 days. "
            "Your refund process produced zero results. The chargeback was filed only after your process failed.", email_style),
        Spacer(1, 4),
        Paragraph("<b>3. KEY ADMISSION</b>", email_bold),
        Paragraph(
            "You wrote: \u201cbecause your request was initiated within the 14-day window, there is a clear and valid route "
            "for you to obtain a full refund.\u201d Thank you for confirming in writing that my refund request was timely and "
            "that a full refund is the appropriate outcome. However, you then direct me to a \u201cProof of Work form\u201d "
            "\u2014 not the \u201crefund request form\u201d referenced in Section 7.4. Requiring me to engage with a "
            "misrepresented service to qualify for a refund is circular.", email_style),
        Spacer(1, 4),
        Paragraph(
            "This is my final correspondence on the substance of this matter. Further emails from Propane that repeat the "
            "same positions without offering a refund will not receive individual responses but will be preserved as part of "
            "the evidence record.", email_style),
        Spacer(1, 4),
        Paragraph("William Marceau<br/>wmarceau@marceausolutions.com", email_style),
    ]
    story.append(email_box(email12_text))
    story.append(PageBreak())

    # ========== SECTION 10: ANALYSIS OF MERCHANT TACTICS ==========
    story.append(section_title("Section 10: Analysis of Merchant\u2019s Escalating Tactics", S))
    story.append(Spacer(1, 6))

    story.append(red_flag_box(
        "CRITICAL: On March 16, Propane sent two emails escalating from a reversal request (10:00) to outright "
        "legal threats (12:28). The second email threatens breach of contract, refund rejection, counterclaim, "
        "and collections \u2014 all because the cardholder exercised a statutory right to dispute."
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Escalation Pattern \u2014 March 16 (Three Emails in 4 Hours):</b>', bold_style))
    story.append(Spacer(1, 4))

    escalation_table = branded_table(
        ["Time", "From", "Tactic", "What They Said"],
        [
            ["10:00", "Phil (coach@)", "Reversal Request",
             '"You will first need to reverse [the chargeback]" before they will "review" the refund.'],
            ["12:08", "Cardholder", "Declined",
             "Declined withdrawal, reiterated refund-first position for the 4th time."],
            ["12:28", "Admin (admin@)", "Legal Threat",
             "Section 7.5 breach of contract. Collections agency. Court fees. \u201cFull indemnity basis.\u201d"],
            ["12:36", "Cardholder", "Rebuttal",
             "Point-by-point rebuttal citing Section 12.5, statutory rights, and prior breach."],
            ["13:50", "Admin (admin@)", "Blame Shift + Admission",
             'Claims delays were cardholder\u2019s fault for emailing Jim. ADMITS refund request was within 14-day window. '
             'Directs to "Proof of Work form" (not refund form). Repeats contract default threat.'],
            ["~14:30", "Cardholder", "Final Rebuttal",
             "admin@ was CC\u2019d on every email. Phil\u2019s voicemail proves admin failed to route. Highlights written "
             "admission of timely request. Notes \u201cProof of Work form\u201d \u2260 Section 7.4 refund form."],
        ],
        col_widths=[0.6 * inch, 1.0 * inch, 1.0 * inch, 3.9 * inch]
    )
    story.append(escalation_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph('<b>Why the Section 7.5 Threat Is Legally Weak:</b>', bold_style))
    story.append(Spacer(1, 4))
    trap_points = [
        "<b>Their own terms contradict it:</b> Section 12.5 (Exceptions) of Propane\u2019s own terms acknowledges "
        "that parties retain the right to seek remedies through external channels. A chargeback is an external "
        "remedy. Section 7.5 cannot override what Section 12.5 expressly preserves.",

        "<b>Statutory rights cannot be waived by contract:</b> Under UK Consumer Rights Act 2015 and the Consumer "
        "Contracts (Information, Cancellation and Additional Charges) Regulations 2013, a consumer\u2019s right to "
        "dispute a charge through their card issuer is a statutory protection. A contractual clause purporting to "
        "waive this right is unenforceable.",

        "<b>Propane breached the contract first:</b> Before any chargeback was filed, Propane (a) misrepresented "
        "the service, (b) failed to provide the refund form for 10 days despite Section 7.4, (c) failed to respond "
        "substantively within 7 days per Section 12.5, and (d) failed to honour the 14-day refund policy per "
        "Section 7.1. A party in material breach cannot invoke contract protections against the wronged party.",

        "<b>No refund commitment \u2014 still just \"assess eligibility\":</b> Even in the escalated email, Propane "
        "says they will \"process your refund request form as normal to assess your eligibility.\" This is not a "
        "refund \u2014 it is a review under Section 7.2 conditions (2 weeks of modules, 2 hotseat calls, lead "
        "generation) that are impossible to meet retroactively. The cardholder would lose chargeback protection "
        "and gain nothing.",

        "<b>Collections threat is empty:</b> These funds are actively disputed through Amex. Collections agencies "
        "do not pursue debts that are subject to active card issuer disputes. Furthermore, threatening legal action "
        "against a consumer exercising statutory rights is itself a matter UK Trading Standards and the CMA investigate.",

        "<b>\"Evidence of fulfilment\" is the wrong frame:</b> Propane says they will provide Amex with \"full "
        "evidence of fulfilment.\" The dispute is not about whether Propane delivered A service \u2014 it is about "
        "whether the service delivered matched what was sold. Written evidence proves it did not.",

        "<b>Refund form provided 10 days late:</b> Propane\u2019s March 16 email includes the refund form link "
        "(tally.so/r/mOXkyR) \u2014 the form the cardholder formally requested on March 12 under Section 7.4. "
        "Providing it 10 days late, attached to a legal threat, does not constitute compliance with their own terms.",
    ]
    for point in trap_points:
        story.append(Paragraph(f"\u2022  {point}", ParagraphStyle(
            "TrapBullet", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=4, spaceAfter=4,
        )))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Cardholder\u2019s Consistent Position (Stated 5 Times in Writing):</b>', bold_style))
    story.append(Spacer(1, 4))
    story.append(email_box([
        Paragraph(
            '<i>"A full refund of \u00a36,300 to the original payment methods will close this matter immediately. '
            'I will withdraw the disputes upon confirmation that the refund has been processed."</i><br/><br/>'
            '\u2014 Stated in emails of March 13, March 14 (10:26), March 16 (12:08), March 16 rebuttal (12:36), '
            'and March 16 final correspondence',
            email_style
        ),
    ]))
    story.append(PageBreak())

    # ========== SECTION 10B: REFUND FORM ANALYSIS ==========
    story.append(section_title('Section 10B: Analysis of Merchant\u2019s "Refund Form"', S))
    story.append(Spacer(1, 6))

    story.append(red_flag_box(
        "CRITICAL DISCOVERY: The form Propane provided (tally.so/r/mOXkyR) is not a \u201crefund request form\u201d "
        "as referenced in Section 7.4. It is a \u201cProof of Work\u201d form requiring evidence of substantial "
        "programme engagement \u2014 engagement that is impossible within the 14-day refund window and that "
        "presumes the service was delivered as described. It also contains a NON-DISPARAGEMENT GAG CLAUSE "
        "conditioning the refund on the consumer\u2019s silence."
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>What the Form Requires (All Mandatory):</b>', bold_style))
    story.append(Spacer(1, 4))
    form_table = branded_table(
        ["#", "Requirement", "Why It Cannot Be Met"],
        [
            ["1", "Onboarding process completion (Members Portal + Pulse software)", "Portal access was delayed \u2014 not provided \u201cimmediately\u201d as promised"],
            ["2", "Onboarding call date", "Onboarding call is where misrepresentation was DISCOVERED"],
            ["3", "First 2 weeks of modules completed (screenshots required)",
             "Cardholder requested refund on Day 4. Cannot complete 2 weeks in 4 days."],
            ["4", "2+ coach check-ins on Circle (screenshots required)",
             "Only 1 interaction occurred \u2014 the onboarding call where misrepresentation was confirmed"],
            ["5", "Problem communicated to coach 72+ hours BEFORE refund request",
             "Coach assigned March 4\u20135. Refund requested March 6. That is ~24 hours, not 72."],
            ["6", "2+ Q&A hotseat calls attended",
             "Hotseat calls are scheduled weekly. Cannot attend 2+ in 4 days."],
            ["7", "Lead generation activity completed (screenshots required)",
             "Requires engagement with a service that was misrepresented at point of sale"],
            ["8", "T1 Tracking Sheet / CRM populated",
             "Requires programme engagement that presumes the service was as described"],
        ],
        col_widths=[0.35 * inch, 2.4 * inch, 3.75 * inch]
    )
    story.append(form_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>The Circular Logic Problem:</b>', bold_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "The cardholder\u2019s dispute is that the service was misrepresented at the point of sale \u2014 "
        "dedicated 1-on-1 coaching was promised, group clinics were delivered. Propane\u2019s refund form "
        "requires the cardholder to extensively engage with that misrepresented service (complete modules, "
        "attend calls, do lead generation) BEFORE qualifying for a refund. This is circular: the consumer "
        "must use the product they\u2019re complaining was mis-sold in order to get their money back for it "
        "being mis-sold. Section 11.4 of Propane\u2019s own terms states that liability for \u201cmisrepresentation "
        "as to a fundamental matter\u201d cannot be excluded.",
        body_style
    ))
    story.append(Spacer(1, 12))

    story.append(red_flag_box(
        "NON-DISPARAGEMENT / GAG CLAUSE: The refund form requires the applicant to agree NOT to post reviews "
        "or share any information about PropaneFitness online or offline. Breach results in \u201clegal "
        "consequences and potential charge-back of refunded amounts.\u201d This conditions a refund on the "
        "consumer\u2019s silence \u2014 an attempt to suppress legitimate consumer feedback that is potentially "
        "unfair under Consumer Rights Act 2015, Part 2, and relevant to UK Trading Standards investigations."
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>\u201cRefund Request Form\u201d vs \u201cProof of Work Form\u201d:</b>', bold_style))
    story.append(Spacer(1, 4))
    form_comparison = branded_table(
        ["Section 7.4 Says", "What Propane Actually Provided"],
        [
            ["Members must submit a \u201crefund request form\u201d",
             "Propane provided a \u201cProof of Work form\u201d (their own label in March 16 email)"],
            ["Form must be provided \u201con request\u201d",
             "Provided 10 days after formal request, attached to a legal threat"],
            ["No mention of mandatory programme engagement",
             "Form requires 8 categories of engagement evidence, all mandatory"],
            ["No mention of non-disparagement",
             "Form includes gag clause conditioning refund on consumer silence"],
        ],
        col_widths=[3.25 * inch, 3.25 * inch]
    )
    story.append(form_comparison)
    story.append(Spacer(1, 12))

    story.append(Paragraph('<b>Section 7.1 Cooling-Off Waiver \u2014 Potentially Unenforceable:</b>', bold_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Propane\u2019s Section 7.1 states: \u201cBy accessing these materials, you therefore waive your right to '
        'the 14-day cooling-off period.\u201d This clause attempts to waive the consumer\u2019s statutory '
        'cooling-off right under the UK Consumer Contracts (Information, Cancellation and Additional Charges) '
        'Regulations 2013. Under these regulations, the statutory cooling-off period for digital content can '
        'only be waived if the consumer gave explicit, informed consent BEFORE the contract was entered into \u2014 '
        'not after. In this case, the terms were not even signed until 3 days after payment. The cardholder '
        'never gave informed consent to waive the cooling-off period before payment was collected.',
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        '<b>Additionally:</b> The cardholder has not accessed or consumed any course content, modules, videos, '
        'or training materials. He attended one onboarding Zoom call (where the misrepresentation was discovered) '
        'and sent one introductory message on Circle.so. Neither constitutes \u201caccessing materials\u201d '
        'that would trigger the waiver even if it were enforceable.',
        body_style
    ))
    story.append(PageBreak())

    # ========== SECTION 11: ANTICIPATED MERCHANT ARGUMENTS ==========
    story.append(section_title("Section 11: Anticipated Merchant Arguments & Rebuttals", S))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "If Propane disputes the chargeback, Amex may request additional evidence. Below are Propane\u2019s "
        "most likely arguments and the documented rebuttals.",
        body_style
    ))
    story.append(Spacer(1, 10))

    counters = [
        ("\"The customer contacted the wrong person \u2014 delays were his fault\"",
         "The cardholder CC\u2019d admin@propanefitness.com on every formal email (March 6, 7, 12, 13). The merchant\u2019s "
         "own Section 7.2 requires issues be raised \u201cvia the official admin email.\u201d The cardholder complied. "
         "Phil (the assigned coach) admitted in his March 14 voicemail he was \u201ccompletely unaware\u201d \u2014 meaning "
         "admin@ failed to route the emails internally. Jim (the salesperson) also removed admin@ from CC on his March 14 "
         "reply. The cardholder cannot be held responsible for the merchant\u2019s internal communication failures. "
         "Additionally, Phil was assigned approximately March 4\u20135; the first refund request was March 6 \u2014 one day later.",
         "All 4 emails show admin@ in CC. Phil\u2019s voicemail confirms he was unaware."),

        ("\"The customer signed the terms on March 5\"",
         "The terms were signed under economic duress \u2014 \u00a36,300 had already been collected 3 days earlier. "
         "Access to course content was withheld until signing. The cardholder had no meaningful choice. "
         "Additionally, the cardholder has not accessed or consumed any course content even after signing.",
         "Jotform timestamp (March 5) vs. Stripe receipts (March 2)"),

        ("\"The customer accessed the platform / engaged with the program\"",
         "The cardholder sent one introductory message on Circle.so and attended one onboarding Zoom call \u2014 "
         "during which the coach confirmed the 1-on-1 coaching promise was no longer offered. This is how the "
         "misrepresentation was discovered, not evidence of acceptance. No course modules, videos, or training "
         "materials have been accessed.",
         "Circle.so activity logs will show minimal engagement"),

        ("\"Filing a chargeback breaches our contract (Section 7.5)\"",
         "The cardholder is not circumventing the refund policy \u2014 the cardholder followed it (requested within "
         "14 days) and the merchant failed to honor it. A chargeback is a statutory right that the merchant\u2019s "
         "own terms (Section 12.5 Exceptions) acknowledge cannot be waived by agreement.",
         "Section 12.5 of merchant\u2019s own terms"),

        ("\"The customer didn't complete the refund eligibility conditions (Section 7.2)\"",
         "Section 7.2 requires 2 weeks of modules, 2 hotseat calls, and lead generation \u2014 all within 14 days. "
         "These conditions require substantial engagement with a service that was misrepresented. The claim is "
         "based on misrepresentation at the point of sale, not dissatisfaction after use. Section 11.4 of the "
         "merchant\u2019s own terms acknowledges that misrepresentation liability cannot be excluded.",
         "Section 7.2 and 11.4 of merchant\u2019s terms"),

        ("\"1-on-1 coaching IS available through coaching clinics\"",
         "The seller promised \u2018Dedicated 1-2-1 coach for 12 weeks\u2019 with \u2018calls to customise the "
         "process.\u2019 What was delivered is group coaching clinics with no calendar or booking system for "
         "1-on-1 sessions. The assigned coach verbally confirmed weekly 1-on-1 calls are no longer offered.",
         "Jim\u2019s sales email (March 2, 15:18)"),

        ("\"We asked the customer to withdraw the chargeback so we could process the refund\"",
         "The merchant asked the cardholder to withdraw chargeback protections BEFORE making any commitment to "
         "issue a refund. Phil\u2019s March 16 email says they will \u201creview\u201d the request through the "
         "\u201cnormal route\u201d \u2014 the same route that produced zero results over 8 days and 4+ formal "
         "emails. The cardholder offered a clear alternative: refund first, disputes withdrawn upon confirmation. "
         "The merchant declined this approach.",
         "Phil\u2019s email (March 16) + cardholder\u2019s response"),

        ("\"Filing a chargeback is a breach of contract under Section 7.5\"",
         "Section 7.5 is contradicted by the merchant\u2019s own Section 12.5 (Exceptions), which preserves the right "
         "to seek external remedies. Furthermore, a contractual clause purporting to waive statutory chargeback rights "
         "is unenforceable under UK Consumer Rights Act 2015. The merchant breached multiple contract provisions "
         "(Sections 7.1, 7.4, 11.4, 12.5) before any chargeback was filed \u2014 a party in material breach cannot "
         "invoke contract protections.",
         "Merchant\u2019s own terms (Section 7.5 vs 12.5) + UK Consumer Rights Act 2015"),

        ("\"We will pursue collections / legal costs on full indemnity basis\"",
         "The funds are actively disputed through Amex. Collections agencies do not pursue debts subject to active "
         "card issuer disputes. Threatening legal action against a consumer exercising statutory dispute rights is "
         "itself a potential violation of UK Consumer Protection from Unfair Trading Regulations 2008 (aggressive "
         "commercial practices). The cardholder has offered 4 times in writing to withdraw disputes upon refund.",
         "Phil\u2019s email (March 16, 12:28) + cardholder\u2019s 4 written offers"),

        ("\"The cardholder was aggressive / filed the chargeback prematurely\"",
         "The cardholder sent 4 formal emails over 8 days (March 6, 7, 12, 13) before filing the chargeback on "
         "March 14. The cardholder set and communicated a clear deadline (March 13), waited for it to pass, and "
         "sent a final notice before proceeding. After filing, the cardholder continued to communicate "
         "professionally and offered to withdraw disputes if refunded \u2014 5 times in writing.",
         "Complete email correspondence (10+ emails)"),

        ("\"The customer must complete the Proof of Work form to get a refund\"",
         "The \u201cProof of Work form\u201d is not the \u201crefund request form\u201d required by Section 7.4. It is a "
         "Section 7.2 compliance check requiring 2 weeks of module completion, 2 hotseat calls, and lead generation "
         "activities. These conditions require engaging with a service that was materially misrepresented at the point "
         "of sale. Requiring a consumer to use a misrepresented service to qualify for a refund for that misrepresentation "
         "is circular and unreasonable. The merchant\u2019s own Section 11.4 acknowledges misrepresentation liability "
         "cannot be excluded.",
         "Propane\u2019s March 16 email naming it \u201cProof of Work form\u201d + Section 7.2 vs 7.4 vs 11.4"),

        ("\"The merchant confirmed the refund request was within the 14-day window\"",
         "This is not an argument FOR Propane \u2014 it is an admission AGAINST them. Propane\u2019s March 16 email "
         "states: \u201cbecause your request was initiated within the 14-day window, there is a clear and valid route "
         "for you to obtain a full refund.\u201d This is a written concession that the refund request was timely and "
         "that a full refund is warranted. Despite this admission, the merchant has not issued a refund.",
         "Propane\u2019s March 16, 13:50 email (direct quote)"),
    ]

    counter_table = branded_table(
        ["Propane\u2019s Likely Argument", "Documented Rebuttal", "Evidence"],
        [[arg, counter, evidence] for arg, counter, evidence in counters],
        col_widths=[1.8 * inch, 3.2 * inch, 1.5 * inch]
    )
    story.append(counter_table)
    story.append(PageBreak())

    # ========== SECTION 12: KEY OBSERVATIONS ==========
    story.append(section_title("Section 12: Key Observations for Amex Analyst", S))
    story.append(Spacer(1, 6))

    observations = [
        "Service delivered is materially different from written pre-sale representations.",
        "Refund requested on Day 4 of merchant\u2019s own 14-day refund window \u2014 merchant failed to honor their own policy.",
        "Merchant never provided the refund request form required by their own terms (Section 7.4).",
        "Merchant breached their own dispute resolution process \u2014 no substantive response within 7 days (Section 12.5).",
        "Terms were not formally agreed before payment (signed March 5, paid March 2).",
        "22-minute high-pressure sales sequence from pricing email to full payment collected.",
        '\u201cImmediate access\u201d promised in writing \u2014 not delivered.',
        "Merchant\u2019s own terms acknowledge liability for misrepresentation cannot be excluded (Section 11.4).",
        "Salesperson (Jim Galvin) deflected responsibility and removed admin@ from CC.",
        'Coach admitted being "completely unaware" of dispute despite admin@ being CC\u2019d on all correspondence.',
        '\u201cSituations like this have cropped up in the past\u201d \u2014 indicating a pattern of similar complaints.',
        "Cardholder has not accessed or consumed any course content.",
        "Merchant continued sending automated marketing emails throughout the dispute period.",
        "<b>NEW:</b> Merchant requested cardholder withdraw chargeback BEFORE committing to any refund \u2014 a reversal trap.",
        "<b>NEW:</b> Merchant escalated from reversal request (10:00) to legal threats (12:28) within 2.5 hours on March 16.",
        "<b>NEW:</b> Merchant invoked Section 7.5 (breach of contract) for filing chargebacks \u2014 contradicted by their own Section 12.5 (Exceptions) which preserves statutory rights.",
        "<b>NEW:</b> Merchant threatened collections agency, court fees, and legal costs on \u201cfull indemnity basis\u201d against a consumer exercising statutory dispute rights.",
        "<b>NEW:</b> Refund form finally provided on March 16 (tally.so link) \u2014 10 days after formally requested on March 6, directly violating their own Section 7.4.",
        "<b>NEW:</b> Even in the escalation email, merchant still only offers to \u201cassess eligibility\u201d \u2014 not commit to a refund.",
        "<b>NEW:</b> Cardholder has offered to withdraw disputes upon refund confirmation 4 times in writing \u2014 merchant has rejected this each time.",
        "<b>NEW:</b> 10 formal emails sent by cardholder across 11 days. Zero substantive merchant responses to any refund ground.",
        "<b>NEW:</b> Merchant\u2019s \u201crefund form\u201d (tally.so) is actually a \u201cProof of Work\u201d form requiring 8 categories of programme engagement evidence \u2014 impossible to complete within the 14-day refund window when refund was requested on Day 4.",
        "<b>NEW:</b> Refund form contains a NON-DISPARAGEMENT GAG CLAUSE conditioning the refund on the consumer agreeing never to post reviews or share information about PropaneFitness. This is an attempt to suppress legitimate consumer feedback.",
        "<b>NEW:</b> Merchant ADMITTED in writing (March 16, 13:50) that \u201cyour request was initiated within the 14-day window\u201d and that \u201cthere is a clear and valid route for you to obtain a full refund.\u201d Despite this admission, no refund has been issued.",
        "<b>NEW:</b> Merchant blamed cardholder for contacting the salesperson who collected \u00a36,300 rather than a coach assigned one day earlier. Rebutted: admin@ was CC\u2019d on every email; Phil\u2019s voicemail proves admin failed to route internally.",
        "<b>NEW:</b> Section 7.1 of merchant\u2019s terms attempts to waive the 14-day statutory cooling-off period by stating \u201cBy accessing these materials, you waive your right.\u201d This waiver is potentially unenforceable under UK Consumer Contracts Regulations 2013, as informed consent was not obtained before payment. Additionally, no course content was ever accessed.",
        "<b>NEW:</b> Cardholder has offered to withdraw disputes upon refund confirmation 5 times in writing. Merchant has not accepted.",
    ]
    for obs in observations:
        story.append(Paragraph(f"\u2022  {obs}", ParagraphStyle(
            "ObsBullet", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=4, spaceAfter=4,
        )))
    story.append(PageBreak())

    # ========== SECTION 13: DOCUMENTS AVAILABLE ==========
    story.append(section_title("Section 13: Documents Available Upon Request", S))
    story.append(Spacer(1, 6))

    docs_list = [
        "Stripe receipts for both charges (#1257-2744 and #1001-9268)",
        'Jim\u2019s sales email (March 2, 15:18) with "Dedicated 1-2-1 coach" promise',
        "Jotform signed terms (March 5) proving post-payment signing (Invoice INV-6485333402225932830)",
        "Screenshot of propane-business.com/terms (Section 7.1, 7.4, 11.4, 12.5)",
        "Amex statements showing both charges + foreign transaction fees",
        "Phil\u2019s voicemail recording (March 14, 2026)",
        "Full email PDF exports (38 documents covering entire correspondence Feb 22 \u2013 Mar 16)",
        "<b>NEW:</b> Jim\u2019s deflection email (March 14) \u2014 \u201cThis has nothing to do with me\u201d",
        "<b>NEW:</b> Phil\u2019s chargeback reversal request (March 16, 10:00) \u2014 conditioning refund on withdrawal",
        "<b>NEW:</b> Propane admin\u2019s Section 7.5 threat email (March 16, 12:28) \u2014 breach of contract claim, collections threat, legal costs threat",
        "<b>NEW:</b> Cardholder\u2019s point-by-point rebuttal (March 16) \u2014 Section 12.5, statutory rights, prior breach",
        "<b>NEW:</b> Refund form link provided by Propane (tally.so/r/mOXkyR) \u2014 10 days late",
        "<b>NEW:</b> Automated marketing emails sent by Propane during active dispute (March 12\u201315)",
    ]
    for i, doc in enumerate(docs_list, 1):
        story.append(Paragraph(f"{i}.  {doc}", ParagraphStyle(
            "DocList", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=3, spaceAfter=3,
        )))

    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY, spaceBefore=8, spaceAfter=12))
    story.append(Paragraph(
        "Originally prepared: March 14, 2026 | Updated: March 16, 2026 | "
        "This document contains factual evidence for a legitimate chargeback dispute. "
        "All claims are supported by documented email correspondence, the merchant\u2019s published terms, and recorded communications.",
        footer_style
    ))

    return story


def main():
    output_path = os.path.join(os.path.dirname(__file__), "..", "docs", "propane-updated-evidence-package.pdf")
    output_path = os.path.abspath(output_path)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=1.1 * inch, bottomMargin=0.8 * inch,
    )

    story = build()
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    path = main()
    import subprocess
    subprocess.run(["open", path])
