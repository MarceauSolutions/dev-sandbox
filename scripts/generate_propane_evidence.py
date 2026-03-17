#!/usr/bin/env python3
"""Generate Propane Fitness chargeback evidence package PDF."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from execution.branded_pdf_engine import (
    BrandConfig, _register_fonts, get_brand_styles,
    branded_table, accent_line, section_title, bullet_list,
    _on_page
)
from io import BytesIO

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
body_style = S["body"]
bold_style = S["body_bold"]
h3 = S["h3"]


def email_box(content_elements):
    """Wrap content in a light-background box to indicate quoted email text."""
    data = [[content_elements]]
    # Build a single-cell table with the content
    # We need to use a different approach - put all elements in a list
    inner = []
    if isinstance(content_elements, list):
        for el in content_elements:
            inner.append(el)
    else:
        inner.append(content_elements)

    # Use a table with a single cell containing a nested list isn't ideal
    # Instead, wrap each paragraph in a table row
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


def build():
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("AMEX DISPUTE", cover_title))
    story.append(Paragraph("SUPPORTING EVIDENCE PACKAGE", cover_title))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="60%", thickness=3, color=BrandConfig.GOLD, spaceBefore=4, spaceAfter=16))
    story.append(Paragraph("PROPANEFITNESS.COM NEWCASTLE GB", cover_subtitle))
    story.append(Paragraph("Two Charges, March 2, 2026", cover_subtitle))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Total Disputed Amount", cover_detail))
    story.append(Paragraph("$8,741.76", cover_amount))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Cardholder: William Marceau", cover_detail))
    story.append(Paragraph("wmarceau@marceausolutions.com", cover_detail))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Amex ending 1007 — $4,370.88", cover_detail))
    story.append(Paragraph("Amex ending 1049 — $4,370.88", cover_detail))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Filed: March 14, 2026", cover_detail))
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
        "After 8 days of non-response across 4 formal emails, the cardholder proceeded with a chargeback dispute.",
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
        ["Mar 13", 'Propane sends another automated marketing email ("Looking for feedback?")', "Email from admin@propanefitness.com"],
        ["Mar 14, 08:39", 'Jim replies: "This has nothing to do with me, mate." Reply sent ONLY to cardholder \u2014 admin@ deliberately removed from CC.', "Email from jim@propanefitness.com"],
        ["Mar 14, 09:57", 'Coach Phil leaves voicemail. Admits he was "completely unaware" of the dispute. States "in situations like this, whenever they have cropped up in the past." Asks cardholder to respond via Circle.so instead of email. Wants to delay to Monday (March 16 \u2014 last day of 14-day window).', "Voicemail recording"],
        ["Mar 14", "Cardholder responds via email, re-adds admin@ to CC, files chargebacks", "Email + Amex dispute"],
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
    story.append(section_title("Section 6: Communication Attempts", S))
    story.append(Spacer(1, 6))

    comm_table = branded_table(
        ["Date", "From", "To / CC", "Subject", "Merchant Response"],
        [
            ["March 6", "Cardholder", "jim@ + admin@", "Formal Refund Request", "Jim replied March 7 \u2014 addressed ONLY foreign transaction fees, ignored all 5 refund grounds"],
            ["March 7", "Cardholder", "jim@ + admin@", "Re: Formal Refund Request", "No response"],
            ["March 12", "Cardholder", "jim@ + admin@", "Re: Formal Refund Request", "Coach messaged on Circle.so (informal platform, not email). No email response."],
            ["March 13", "Cardholder", "jim@ + admin@", "Formal Refund Request (deadline notice)", 'Jim replied March 14: "This has nothing to do with me" \u2014 removed admin@ from CC. Coach left voicemail wanting to redirect to Circle.so'],
        ],
        col_widths=[0.7 * inch, 0.8 * inch, 1.0 * inch, 1.4 * inch, 2.6 * inch]
    )
    story.append(comm_table)
    story.append(PageBreak())

    # ========== SECTION 7: FULL EMAIL TEXT ==========
    story.append(section_title("Section 7: Full Email Text \u2014 Cardholder\u2019s Refund Requests", S))
    story.append(Spacer(1, 6))

    # --- Email 1 ---
    story.append(Paragraph('<b>Email 1 \u2014 March 6, 2026 (Original Refund Request)</b>', h3))
    story.append(Paragraph(
        '<i>Note: Original sent email was accidentally deleted from sent folder. This text is from the preserved draft '
        '(still in Gmail trash, dated March 6, 2026 16:52). The content was sent to jim@propanefitness.com with CC to '
        'admin@propanefitness.com. Jim\u2019s March 7 reply referencing foreign transaction fees confirms receipt.</i>',
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
        Paragraph(
            "I want to be clear about the current situation:", email_style),
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
            "ignored all substantive grounds. It has now been 6 days with no further response. You are in breach of your "
            "own dispute resolution timeline.", email_style),
        Spacer(1, 4),
        Paragraph("<b>3. The service is materially different from what was sold.</b>", email_bold),
        Paragraph(
            'The sales email promised "Dedicated 1-2-1 coach for 12 weeks" with "calls to customise the process to your '
            'business." The assigned coach confirmed during onboarding that weekly 1-on-1 Zoom calls are not part of the '
            "current program. Section 11.4 of your terms acknowledges that misrepresentation of fundamental matters cannot "
            "be excluded from liability.", email_style),
        Spacer(1, 4),
        Paragraph("<b>4. I have not accessed or consumed any course content.</b>", email_bold),
        Paragraph(
            "There has been no benefit received from this program.", email_style),
        Spacer(1, 4),
        Paragraph("<b>5. My formal emails have gone unanswered.</b>", email_bold),
        Paragraph(
            "I have sent two detailed emails (March 6 and March 7) with no substantive reply. This is not acceptable for "
            "a \u00a36,300 service.", email_style),
        Spacer(1, 6),
        Paragraph(
            "Please also provide the refund request form referenced in Section 7.4 of your terms. Your policy states this "
            "form must be provided \u201con request.\u201d I am formally requesting it now.", email_style),
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
        Paragraph(
            "This is my final communication on this matter unless a full refund is confirmed.", email_style),
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

    # ========== SECTION 9: KEY OBSERVATIONS ==========
    story.append(section_title("Section 9: Key Observations for Amex Analyst", S))
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
    ]
    for obs in observations:
        story.append(Paragraph(f"\u2022  {obs}", ParagraphStyle(
            "ObsBullet", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=4, spaceAfter=4,
        )))
    story.append(PageBreak())

    # ========== SECTION 10: DOCUMENTS AVAILABLE ==========
    story.append(section_title("Section 10: Documents Available Upon Request", S))
    story.append(Spacer(1, 6))

    docs_list = [
        "Stripe receipts for both charges (#1257-2744 and #1001-9268)",
        'Jim\u2019s sales email (March 2, 15:18) with "Dedicated 1-2-1 coach" promise',
        "Jotform signed terms (March 5) proving post-payment signing (Invoice INV-6485333402225932830)",
        "Screenshot of propane-business.com/terms (Section 7.1, 7.4, 11.4, 12.5)",
        "Amex statements showing both charges + foreign transaction fees",
        "Phil\u2019s voicemail recording (March 14, 2026)",
        "Full email PDF exports (27 documents covering entire correspondence)",
    ]
    for i, doc in enumerate(docs_list, 1):
        story.append(Paragraph(f"{i}.  {doc}", ParagraphStyle(
            "DocList", parent=body_style, leftIndent=18, bulletIndent=0,
            spaceBefore=3, spaceAfter=3,
        )))

    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY, spaceBefore=8, spaceAfter=12))
    story.append(Paragraph(
        "Prepared: March 14, 2026 | This document contains factual evidence for a legitimate chargeback dispute. "
        "All claims are supported by documented email correspondence, the merchant\u2019s published terms, and recorded communications.",
        footer_style
    ))

    return story


def main():
    output_path = os.path.join(os.path.dirname(__file__), "..", "docs", "propane-final-evidence-package.pdf")
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
