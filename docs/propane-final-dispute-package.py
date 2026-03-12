#!/usr/bin/env python3
"""
Propane Fitness — Final Comprehensive Dispute Package
Generates:
  1. Escalation email to Jim (ready to copy/paste)
  2. Complete chronological dispute PDF with all evidence organized for Amex
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
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
MID_GRAY = HexColor("#e0e0e0")
WHITE = colors.white
ALERT_BG = HexColor("#fff3f3")
KEY_BG = HexColor("#f0f4ff")

DISPUTE_DIR = Path(__file__).parent.parent / "projects" / "marceau-solutions" / "labs" / "PropaneFitnessDispute"
OUTPUT_DIR = DISPUTE_DIR


def get_styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=20, leading=26, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=11, leading=15, textColor=CHARCOAL, spaceAfter=14, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15, leading=20, textColor=NAVY, spaceBefore=18, spaceAfter=8),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=DARK_BLUE, spaceBefore=12, spaceAfter=5),
        "h3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=CHARCOAL, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13, textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=CHARCOAL, spaceAfter=5),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=9.5, leading=13, textColor=HexColor("#555555"), leftIndent=15, rightIndent=15, spaceAfter=6),
        "alert": ParagraphStyle("Alert", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=RED, spaceAfter=5),
        "small": ParagraphStyle("Small", fontName="Helvetica", fontSize=8, leading=11, textColor=HexColor("#777777"), spaceAfter=3),
        "key_point": ParagraphStyle("KeyPoint", fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=NAVY, spaceAfter=5, leftIndent=10),
        "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, leading=10, textColor=HexColor("#999999"), alignment=TA_CENTER),
    }


def make_table(data, col_widths=None, header=True, highlight_rows=None):
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEADING', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), CHARCOAL),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GRAY),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))
    if highlight_rows:
        for row_idx in highlight_rows:
            style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), KEY_BG))
            style_cmds.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style_cmds))
    return t


def hr():
    return HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceAfter=8, spaceBefore=8)


def alert_box(text, styles):
    """Red alert box."""
    data = [[Paragraph(text, styles["alert"])]]
    t = Table(data, colWidths=[6.8*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ALERT_BG),
        ('BOX', (0, 0), (-1, -1), 1, RED),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def key_box(text, styles):
    """Blue key-point box."""
    data = [[Paragraph(text, styles["key_point"])]]
    t = Table(data, colWidths=[6.8*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), KEY_BG),
        ('BOX', (0, 0), (-1, -1), 1, DARK_BLUE),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def build_final_package(styles):
    s = styles
    story = []

    # ===== COVER =====
    story.append(Spacer(1, 40))
    story.append(Paragraph("AMERICAN EXPRESS CHARGEBACK DISPUTE", s["title"]))
    story.append(Paragraph("Complete Evidence Package — PropaneFitness.com", s["subtitle"]))
    story.append(hr())

    # Dispute summary
    summary = [
        ["", "Detail"],
        ["Cardholder", "William Marceau — wmarceau@marceausolutions.com"],
        ["Merchant", "PROPANEFITNESS.COM NEWCASTLE GB — Propane Fitness Limited"],
        ["Transaction Date", "March 2, 2026"],
        ["Card 1 (ending 1007)", "$4,255.97 charge + $114.91 FTF = $4,370.88"],
        ["Card 2 (ending 1049)", "$4,255.97 charge + $114.91 FTF = $4,370.88"],
        ["TOTAL DISPUTED", "$8,741.76"],
        ["Dispute Category", "Goods/Services Not As Described — Reason Code C31 (Misrepresentation)"],
        ["Refund Requested", "March 6, 2026 (Day 4 of 14-day refund window)"],
        ["Deadline Given", "March 13, 2026"],
        ["Merchant Response", "Non-substantive — addressed only FX fees, ignored all grounds"],
    ]
    story.append(make_table(summary, col_widths=[1.8*inch, 5.2*inch]))
    story.append(Spacer(1, 12))

    story.append(alert_box(
        "PRIMARY DISPUTE REASON: Bait-and-switch. Seller promised consistent weekly 1-on-1 Zoom coaching "
        "with a dedicated coach. After payment, coach confirmed they no longer offer consistent weekly calls "
        "and rely on group coaching clinics instead. No calendar or booking system exists for 1-on-1 Zoom sessions.", s))

    # ===== SECTION 1: CHRONOLOGICAL TIMELINE =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 1: COMPLETE CHRONOLOGICAL TIMELINE", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "Every interaction between the cardholder and PropaneFitness, from first contact through "
        "the present day. Timestamps are from email headers and platform records.", s["body"]))

    timeline = [
        ["#", "Date / Time", "Event", "Evidence"],
        ["1", "Feb 22", "Cardholder downloads Propane lead magnet video", "SPAM_01 email"],
        ["2", "Feb 22", "Propane sends bonus follow-up email", "SPAM_02 email"],
        ["3", "Feb 23", "Sales call booked with Propane team", "SPAM_03 email"],
        ["4", "Feb 24", "Joe Halford sends pre-call resources", "Email #01"],
        ["5", "Feb 25", "Initial sales call with Jim Galvin (Zoom)", "Email #02"],
        ["6", "Mar 2, 14:05", "Follow-up Zoom call — pricing discussed verbally", "Email #03"],
        ["7", "Mar 2, 15:18", "KEY: Jim sends sales email — pricing, '1-2-1 dedicated\ncoach' promise, 'immediate access' promise", "Email #04\nEXHIBIT A"],
        ["8", "Mar 2, 15:27", "Jim sends terms link (just a URL, no acceptance\nmechanism) — 9 min after pricing email", "Email #05"],
        ["9", "Mar 2, 15:29", "Jim sends 1st payment link — 2 MIN after terms", "Email #06"],
        ["10", "Mar 2, 15:30", "Jim sends 2nd payment link — 1 min later", "Email #07"],
        ["11", "Mar 2, 15:32", "CHARGE 1: £3,150 on card 1007", "Stripe #1257-2744\nEmail #10"],
        ["12", "Mar 2, 15:40", "CHARGE 2: £3,150 on card 1049", "Stripe #1001-9268\nEmail #12"],
        ["13", "Mar 2–3", "COURSE CONTENT ACCESS NOT PROVIDED despite\nwritten promise of 'immediate access'. Circle\ncommunity invite sent, but course modules\ngated behind Jotform terms signing.", "No course access\nemail received"],
        ["14", "Mar 3", "Phil Charlton (assigned coach) first contact via\nCircle — onboarding tasks assigned.", "Email #13\nMessageThread1"],
        ["15", "Mar 3–4", "Full day of follow-up to get platform access", "Emails #14–16"],
        ["16", "Mar 5, 15:23", "KEY: Terms signed via Jotform — 3 DAYS after\npayment was already collected", "Email #19\nEXHIBIT C"],
        ["17", "Mar 5", "Onboarding Zoom call with assigned coach. Coach\nconfirms consistent weekly 1-on-1 calls no longer\noffered; program relies on group coaching clinics.\nNo calendar/booking system for 1-on-1 Zoom.\nCourse descriptions show backend tools cardholder\nalready has. No course modules opened.", "Circle platform\nZoom call\nMessageThread1-6"],
        ["18", "Mar 6, 16:52", "KEY: Formal refund request sent to Jim + admin@\npropanefitness.com. Full grounds stated.", "TRASH recovered\nemail"],
        ["19", "Mar 7, ~AM", "Jim replies — addresses ONLY foreign transaction\nfees. Ignores ALL 7 substantive grounds.", "Referenced in\nEmail #22"],
        ["20", "Mar 7, 11:05", "KEY: Cardholder sends final demand. All 7 grounds\nrestated. March 13 deadline.", "Email #22\nEXHIBIT B"],
        ["21", "Mar 7–11", "Propane continues sending automated marketing\nemails — no response to refund request", "Emails #23–26"],
        ["22", "Mar 9, 15:35", "Propane Support Genie messages via Circle", "Email #24"],
        ["23", "Mar 12, 7:00 AM", "KEY: Phil Charlton (coach) messages via Circle\nabout refund — NOT via email. Formal email\nrefund request remains unanswered.", "MessageThread1\n(sidebar)"],
        ["24", "Mar 12", "Cardholder sends escalation email to Jim via email\nredirecting all communication to formal channel", "Escalation email"],
        ["25", "Mar 13", "Cardholder's deadline for resolution.", "—"],
    ]
    story.append(make_table(timeline, col_widths=[0.35*inch, 1.1*inch, 3.3*inch, 1.45*inch],
                            highlight_rows=[7, 11, 12, 16, 18, 20, 23]))
    story.append(Spacer(1, 8))
    story.append(key_box(
        "22 MINUTES: The entire sequence from pricing email (15:18) to full £6,300 payment (15:40) "
        "took only 22 minutes. Only 2 minutes between terms link and first payment link.", s))

    # ===== SECTION 2: THE 8 GROUNDS =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 2: GROUNDS FOR DISPUTE", s["h1"]))
    story.append(hr())

    grounds = [
        ("GROUND 1: BAIT-AND-SWITCH ON CORE SERVICE [PRIMARY]",
         "During the sales call on March 2, Jim Galvin explicitly promised <b>consistent weekly 1-on-1 Zoom coaching sessions</b> "
         "with a dedicated coach. His own email (15:18) confirms: <i>\"Dedicated 1-2-1 coach for 12 weeks. Private thread "
         "for messages, voice notes, feedback and calls to customise the process to your business.\"</i><br/><br/>"
         "After payment, the cardholder was assigned a coach and had one onboarding Zoom call. During that call, "
         "the coach verbally confirmed that they no longer offer consistent weekly 1-on-1 calls and instead rely "
         "primarily on group coaching clinics and community interaction. There is no calendar or booking system to "
         "schedule 1-on-1 Zoom calls — the only option would be to message the coach directly.<br/><br/>"
         "The merchant's own terms confirm the distinction: under 'One-on-One Coaching Support,' the 1-2-1 relationship "
         "is described as <i>\"a channel [that] facilitates the sharing of voice notes, document reviews, messages\"</i> — "
         "a messaging thread, not scheduled Zoom calls. The Zoom element is group 'coaching clinics' with rotating slots, "
         "not the consistent weekly personal coaching that was sold."
         ),
        ("GROUND 2: PROGRAM HAS NO VALUE BEYOND MISREPRESENTED SERVICE",
         "The only unique value was 1-on-1 human coaching on client-facing skills (sales, positioning, content). The "
         "remaining content is backend tools (funnels, Facebook ads, automation) the cardholder already has operational. "
         "The seller's own email emphasized the human coaching elements — '1-2-1 coach' and 'calls to customise the "
         "process' — because that was the primary value proposition discussed."
         ),
        ("GROUND 3: TERMS NOT AGREED BEFORE PAYMENT",
         "A terms URL was emailed at 15:27. Payment links followed 2 minutes later at 15:29. First charge at 15:32. "
         "No acceptance mechanism was provided — just a link. The merchant's own process required a separate Jotform "
         "signature, completed <b>March 5</b> — 3 full days after both charges. The merchant's refund restrictions, "
         "cooling-off waiver, and dispute resolution clauses were not formally agreed before payment."
         ),
        ("GROUND 4: WITHIN MERCHANT'S OWN 14-DAY REFUND POLICY",
         "The merchant's published terms state: <i>\"Within 14 Days of Purchase: We instead offer a full refund if the "
         "refund request form has been successfully completed within the first 14 days.\"</i><br/><br/>"
         "Refund requested March 6 — Day 4. The 14-day window doesn't expire until March 16. <b>The merchant has not "
         "honored their own policy.</b><br/><br/>"
         "NOTE: The terms require a \"refund request form\" — but no such form was ever provided to the cardholder. "
         "No link to a refund form appears in any email, onboarding message, or platform communication. The merchant "
         "cannot deny a refund for failure to use a form they never provided."
         ),
        ("GROUND 5: PRICING INCONSISTENCY",
         "The pricing verbally communicated during the call was materially different from the figures in the written "
         "follow-up email sent minutes later. The verbal and written prices used different base figures, creating "
         "confusion about the true cost of the program. This inconsistency contributed to the high-pressure environment "
         "in which the purchase decision was made."
         ),
        ("GROUND 6: HIGH-PRESSURE 22-MINUTE PAYMENT SEQUENCE",
         "Pricing email (15:18) → terms link (15:27) → payment link 1 (15:29) → payment link 2 (15:30) → "
         "charge 1 (15:32) → charge 2 (15:40). Only 2 minutes between terms and payment links. No reasonable "
         "opportunity to review a contract for an $8,700 purchase."
         ),
        ("GROUND 7: ACCESS NOT PROVIDED AS PROMISED",
         "Jim's email states: <i>\"Once you've processed the payment you'll receive immediate access via email with "
         "login information and next steps.\"</i> Access was NOT provided immediately — required a full day of follow-up."
         ),
        ("GROUND 8: UNDISCLOSED FOREIGN CURRENCY CHARGES",
         "The cardholder was never informed charges would be in GBP, that USD equivalents would be $4,255.97 each, "
         "or that $114.91 foreign transaction fees would apply per card. Total undisclosed fees: <b>$229.82</b>."
         ),
    ]

    for title, body_text in grounds:
        story.append(Paragraph(title, s["h2"]))
        story.append(Paragraph(body_text, s["body"]))
        story.append(Spacer(1, 4))

    # ===== SECTION 3: WHY THEIR TERMS DON'T PROTECT THEM =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 3: MERCHANT'S TERMS — WHY THEY DON'T APPLY", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "<b>Note:</b> The cardholder's primary position is that the terms were not validly agreed before payment and are "
        "not enforceable as written. However, even if the terms ARE applied, the merchant has breached their own terms "
        "at every step — failing to provide the refund form, failing to give a substantive response, and failing to honor "
        "their own 14-day refund policy. Under either interpretation, the cardholder is entitled to a refund.", s["body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3a. Their Dispute Resolution Clause (Section 12.5)", s["h2"]))
    story.append(Paragraph(
        "Their terms require a 3-step process: (1) Written notice to admin@propanefitness.com with 7-day response window, "
        "(2) 14 days good-faith negotiation, (3) CEDR mediation. They claim bypassing this = material breach + forfeiture "
        "of refund + legal costs + collections.", s["body"]))
    story.append(Paragraph("<b>Why it doesn't apply:</b>", s["body_bold"]))
    story.append(Paragraph(
        "<b>1.</b> The cardholder DID send written notice to admin@propanefitness.com (CC'd on March 6 refund request). "
        "The merchant's own terms require a \"substantive response within 7 days\" — Jim's reply addressed only FX fees. "
        "<b>The merchant breached their own Step 1.</b><br/><br/>"
        "<b>2.</b> Terms were signed March 5 — three days after £6,300 was collected. The signature was given under economic "
        "duress: refusing to sign after paying would mean losing both the money and the service.<br/><br/>"
        "<b>3.</b> Section 12.5 Exceptions explicitly states: <i>\"Statutory rights that cannot be waived by agreement\"</i> — "
        "a chargeback is a right between cardholder and card issuer, not subject to the merchant's contract.<br/><br/>"
        "<b>4.</b> A chargeback is a banking process. Amex is not a party to their terms.", s["body"]))

    story.append(Paragraph("3b. Their Cooling-Off Waiver (Section 7.1)", s["h2"]))
    story.append(Paragraph(
        "They claim accessing materials waives the 14-day statutory cooling-off period under UK Consumer Contracts Regulations.", s["body"]))
    story.append(Paragraph("<b>Why it doesn't apply:</b>", s["body_bold"]))
    story.append(Paragraph(
        "<b>The cardholder did not access the course materials.</b> After payment on March 2, access to the course "
        "content was NOT provided. Access was conditional on signing the terms via Jotform, which did not occur until "
        "March 5 — three days after payment. The cardholder has not accessed or consumed any course modules, videos, "
        "or training materials since. The cooling-off waiver requires \"accessing materials\" — this never happened.<br/><br/>"
        "Furthermore, a cooling-off waiver must be <b>explicitly consented to BEFORE access is granted</b> under UK law. "
        "The Jotform agreement wasn't signed until March 5. The merchant collected payment first, withheld access until "
        "terms were signed, and the cardholder never used the content. The waiver is inapplicable on every count.<br/><br/>"
        "Additionally, the service delivered (group coaching clinics with no mechanism for consistent weekly 1-on-1 Zoom calls) "
        "is materially different from what was sold (dedicated weekly 1-on-1 Zoom coaching) "
        "— grounds for rescission regardless of cooling-off period.", s["body"]))

    story.append(Paragraph("3c. Their Refund Eligibility Requirements (Section 7.2)", s["h2"]))
    story.append(Paragraph(
        "They require completion of onboarding, modules, hotseat calls, coach engagement, etc. before a refund is eligible.", s["body"]))
    story.append(Paragraph("<b>Why it doesn't apply:</b>", s["body_bold"]))
    story.append(Paragraph(
        "These conditions presuppose the service was delivered as promised. When the core service (1-on-1 coaching) "
        "was misrepresented, requiring the cardholder to complete onboarding for a program that doesn't deliver what was "
        "sold is absurd. The cardholder is not required to fully use a misrepresented service before disputing it. "
        "Additionally, these conditions were in terms not agreed before payment.", s["body"]))

    story.append(Paragraph("3d. Phil Charlton's Circle Message (March 12) — Informal Channel", s["h2"]))
    story.append(Paragraph(
        "Rather than responding to the cardholder's formal email correspondence, the merchant's coach contacted "
        "the cardholder through Circle.so on March 12 — six days after the formal refund request. Phil's message: "
        "<i>\"Hi William, how are you getting on. I know you messaged regarding a refund so I just wanted to get in touch "
        "to see where you're up to with everything?\"</i><br/><br/>"
        "This is notable because:<br/>"
        "&bull; The merchant chose an informal platform rather than responding to the formal email refund request<br/>"
        "&bull; Section 12.5 of the merchant's own terms requires written notice for dispute communications<br/>"
        "&bull; The formal email to jim@ and admin@ remained unanswered<br/><br/>"
        "The cardholder has redirected all communication to the formal email channel to maintain a proper record.", s["body"]))

    story.append(Paragraph("3e. Their Own Terms Acknowledge Misrepresentation Liability (Section 11.4)", s["h2"]))
    story.append(Paragraph(
        "The merchant's own Terms of Use, Section 11.4, state:", s["body"]))
    story.append(Paragraph(
        "<i>\"Nothing in these Terms shall exclude or limit our liability for (a) death or personal injury caused by our "
        "negligence; (b) fraud; (c) misrepresentation as to a fundamental matter; or (d) any liability which cannot be "
        "excluded or limited under applicable law.\"</i>", s["quote"]))
    story.append(Paragraph(
        "The nature of the coaching — consistent weekly 1-on-1 Zoom sessions with a dedicated coach versus group coaching clinics with no booking system for personal calls — is a <b>fundamental matter</b> "
        "that directly influenced the purchase decision. Even under the merchant's own terms, they cannot exclude liability for "
        "this misrepresentation. This is not a minor detail or buyer's remorse — the core service sold does not match "
        "the core service delivered.", s["body"]))

    story.append(Paragraph("3f. Refund Form Never Provided (Section 7.4)", s["h2"]))
    story.append(Paragraph(
        "Section 7.4 of the merchant's terms states: <i>\"To initiate a refund request, the member must complete the refund "
        "request form provided by PropaneFitness or PropaneBusiness on request.\"</i><br/><br/>"
        "No refund request form was ever provided to the cardholder. No link to such a form appears in any email, "
        "onboarding communication, platform message, or the terms page itself. The merchant cannot deny a refund "
        "on the basis of a form they are obligated to provide but never did. The cardholder's email refund request of "
        "March 6 contained all information their dispute resolution process requires: a clear description of the dispute, "
        "the remedy sought, relevant dates, transaction details, and supporting evidence.", s["body"]))

    # ===== SECTION 3.5: MERCHANT'S OWN BREACHES =====
    story.append(Spacer(1, 12))
    story.append(Paragraph("SUMMARY: MERCHANT'S BREACHES OF THEIR OWN TERMS", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "The following is a summary of how the merchant has breached their own published Terms of Use. "
        "The cardholder has complied with all applicable procedures; it is the merchant who has failed at every step.", s["body"]))

    breach_data = [
        ["#", "Term / Section", "What It Requires", "Merchant's Breach"],
        ["1", "Section 7.1\nRefund Policy",
         "Full refund if refund request form\ncompleted within 14 days of purchase",
         "Cardholder requested refund Day 4.\nMerchant has not issued refund."],
        ["2", "Section 7.4\nRefund Form",
         "Merchant must provide refund request\nform \"on request\"",
         "No refund form was ever provided\ndespite request on March 6."],
        ["3", "Section 12.5 Step 1\nDispute Resolution",
         "Respondent must provide\n\"substantive response within 7 days\"",
         "Jim replied addressing ONLY FX fees.\nIgnored all 7 substantive grounds.\nNo substantive response received."],
        ["4", "Section 11.4\nMisrepresentation",
         "Merchant cannot exclude liability for\n\"misrepresentation as to a fundamental\nmatter\"",
         "Sold consistent weekly 1-on-1 Zoom coaching.\nCoach confirmed weekly calls discontinued.\nNo booking system for 1-on-1 Zoom.\nFundamental misrepresentation."],
        ["5", "Sales Email\n(Mar 2, 15:18)",
         "\"Immediate access via email with\nlogin information and next steps\"",
         "Access NOT provided immediately.\nRequired full day of follow-up."],
        ["6", "Section 12.5\nWritten Notice",
         "Formal dispute communication via\nwritten notice to admin@propanefitness.com",
         "Merchant responded via Circle.so\n(informal platform) instead of email\non March 12."],
        ["7", "Terms Agreement\nProcess",
         "Formal agreement (Jotform signature)\nrequired before terms are binding",
         "Payment collected March 2.\nTerms not signed until March 5.\nTerms imposed retroactively."],
    ]
    story.append(make_table(breach_data, col_widths=[0.3*inch, 1.2*inch, 2.5*inch, 3.0*inch]))
    story.append(Spacer(1, 10))
    story.append(key_box(
        "The cardholder has not breached any term or process. Every breach identified above is the merchant's. "
        "The cardholder sent written notice to the correct email address, within the 14-day refund window, with full grounds stated. "
        "The merchant failed to provide a refund form, failed to give a substantive response, and attempted to circumvent "
        "the formal email channel by contacting the cardholder through an informal platform.", s))

    # ===== SECTION 4: TRANSACTION DETAILS =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 4: TRANSACTION DETAILS", s["h1"]))
    story.append(hr())

    story.append(Paragraph("Card 1 — Amex Blue Business Cash ending 1007", s["h2"]))
    tx1 = [
        ["Field", "Detail"],
        ["Stripe Receipt #", "1257-2744"],
        ["Amount (GBP)", "£3,150.00"],
        ["Amount (USD)", "$4,255.97"],
        ["Foreign Transaction Fee", "$114.91"],
        ["Total Charged to Card", "$4,370.88"],
        ["Date/Time", "March 2, 2026 — 15:32:27 UTC"],
        ["Description", '"2 x 3150 - PropaneBusiness"'],
        ["Processor", "Stripe (acct: acct_182oNdF42QmTryTb)"],
        ["SamCart Order", "#24344642"],
    ]
    story.append(make_table(tx1, col_widths=[2.0*inch, 5.0*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Card 2 — Amex Blue Business Cash ending 1049", s["h2"]))
    tx2 = [
        ["Field", "Detail"],
        ["Stripe Receipt #", "1001-9268"],
        ["Amount (GBP)", "£3,150.00"],
        ["Amount (USD)", "$4,255.97"],
        ["Foreign Transaction Fee", "$114.91"],
        ["Total Charged to Card", "$4,370.88"],
        ["Date/Time", "March 2, 2026 — 15:40:09 UTC"],
        ["Description", '"3150 balancing payment propanebusiness - Copy"'],
        ["Processor", "Stripe (acct: acct_182oNdF42QmTryTb)"],
        ["SamCart Order", "#24344711"],
    ]
    story.append(make_table(tx2, col_widths=[2.0*inch, 5.0*inch]))
    story.append(Spacer(1, 10))

    totals = [
        ["", "Card 1007", "Card 1049", "Total"],
        ["Charge", "$4,255.97", "$4,255.97", "$8,511.94"],
        ["Foreign Tx Fee", "$114.91", "$114.91", "$229.82"],
        ["TOTAL", "$4,370.88", "$4,370.88", "$8,741.76"],
    ]
    story.append(make_table(totals, col_widths=[1.5*inch, 1.7*inch, 1.7*inch, 1.7*inch]))

    # ===== SECTION 5: EVIDENCE INDEX =====
    story.append(Spacer(1, 16))
    story.append(Paragraph("SECTION 5: EVIDENCE INDEX", s["h1"]))
    story.append(hr())

    exhibits = [
        ["Exhibit", "Description", "File / Source"],
        ["A", "Jim's sales email (Mar 2, 15:18) — contains\nall promises: '1-2-1 coach', 'immediate access', pricing",
         "emails/04_*_Next-steps-to-secure-your-spot.pdf\n+ NextStepsToSecureYourSpot.pdf (manual save)"],
        ["B", "Cardholder's refund emails:\n• Original request (Mar 6) — recovered from Trash\n• Final demand (Mar 7) — with all 7 grounds",
         "emails/TRASH_RECOVERED_*_original-refund-request.pdf\nemails/22_*_Re-Formal-Refund-Request.pdf\n+ Re: Formal Refund Request.pdf (manual save)"],
        ["C", "Signed terms via Jotform — dated March 5\n(proves terms signed 3 DAYS AFTER payment)",
         "emails/19_*_Your-signed-terms.pdf"],
        ["D", "Full merchant terms (24 pages) including:\n• 14-day refund policy (Section 7.1)\n• Dispute resolution clause (Section 12.5)\n• Cooling-off waiver language",
         "Terms of Use.pdf (saved from propane-business.com/terms)"],
        ["E", "Circle.so message threads showing:\n• Group coaching clinic format\n• No calendar/booking system for 1-on-1 Zoom\n• Phil Charlton's March 12 re-engagement attempt\n• Hotseat = shared group calls, not dedicated",
         "MessageThread1.pdf through MessageThread6.pdf"],
        ["F", "Stripe receipts for both charges",
         "emails/10_*_receipt-1257-2744.pdf\nemails/12_*_receipt-1001-9268.pdf"],
        ["G", "SamCart order confirmations",
         "emails/08_*_Order-24344642.pdf\nemails/11_*_Order-24344711.pdf"],
        ["H", "Jim's terms email (just a URL link, no\nacceptance mechanism) + payment link emails",
         "Full Terms.pdf + Payment Link.pdf + SECOND CARD.pdf"],
        ["I", "Complete email export — 35 emails covering\nentire relationship (inbox + spam + trash)",
         "emails/ folder (26 inbox + 8 spam + 1 trash)"],
        ["J", "Escalation email (Mar 12) citing 5 specific\nterms breaches + formal refund form request",
         "Escalation email to jim@propanefitness.com"],
        ["K", "Amex statements showing charges + FTFs",
         "statements/ folder (to be added by cardholder)"],
    ]
    story.append(make_table(exhibits, col_widths=[0.6*inch, 2.8*inch, 3.6*inch]))

    # ===== SECTION 6: MERCHANT COMMUNICATION FAILURES =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 6: MERCHANT'S FAILURE TO RESOLVE", s["h1"]))
    story.append(hr())

    story.append(Paragraph(
        "The cardholder attempted direct resolution in good faith before filing this dispute:", s["body"]))

    resolution_timeline = [
        ["Date", "Cardholder Action", "Merchant Response"],
        ["Mar 6", "Sent formal refund request to jim@ +\nadmin@propanefitness.com with full grounds", "No response on this day"],
        ["Mar 7 AM", "(Waiting for merchant response)", "Jim replies — addresses ONLY the foreign\ntransaction fees. Ignores all 7 substantive\ngrounds for the refund."],
        ["Mar 7, 11:05", "Sent final demand restating all 7 grounds.\nSet March 13 deadline. Stated consequences\nof non-resolution.", "No response."],
        ["Mar 8–11", "(Waiting — within the 7-day response\nwindow per merchant's own terms)", "No response via email. Continued sending\nautomated marketing emails."],
        ["Mar 12", "—", "Merchant sends Phil (coach) via Circle\n(not email) to discuss refund. Formal\nemail refund request remains unanswered."],
        ["Mar 12", "Cardholder sends escalation email\nredirecting to formal channel.", "—"],
        ["Mar 13", "Cardholder's deadline for resolution", "No refund received. No substantive\nemail response as of filing date."],
    ]
    story.append(make_table(resolution_timeline, col_widths=[0.8*inch, 2.8*inch, 3.4*inch],
                            highlight_rows=[7]))

    story.append(Spacer(1, 12))
    story.append(key_box(
        "SUMMARY: The cardholder (1) sent formal written notice to the required email address, (2) gave the merchant "
        "7 days + 6 additional days to respond, (3) received only a non-substantive reply, (4) is within the merchant's "
        "own 14-day refund window. The merchant has failed to resolve this through their own process.", s))

    # ===== SECTION 7: ANTICIPATED COUNTER-ARGUMENTS =====
    story.append(PageBreak())
    story.append(Paragraph("SECTION 7: ANTICIPATED MERCHANT COUNTER-ARGUMENTS", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "The following are arguments the merchant may raise in their chargeback rebuttal, with prepared responses:", s["body"]))

    counters = [
        ('"The cardholder engaged with the program / accessed materials"',
         "The cardholder did NOT have access to course content after payment on March 2. Access was conditional on "
         "signing the terms via Jotform, which did not occur until March 5. The cardholder has not accessed or consumed "
         "any course modules, videos, or training materials. The cardholder's only interactions were a polite introductory "
         "message to the assigned coach on Circle and one onboarding Zoom call — during which the coach confirmed that "
         "consistent weekly 1-on-1 calls are no longer offered and the program relies on group coaching clinics instead. "
         "The merchant's cooling-off waiver (Section 7.1) does not apply because the cardholder never accessed course materials."
         ),
        ('"The cardholder signed the terms on March 5"',
         "The terms were signed under economic duress — £6,300 had already been collected 3 days earlier. Refusing to "
         "sign after paying would mean losing both the money and the service. Access to the course content was conditional "
         "on signing the terms — it was NOT available before the Jotform was completed on March 5. The merchant withheld "
         "access until signing, then claims the act of signing constitutes voluntary agreement. This is circular: the "
         "cardholder had no choice but to sign after paying £6,300, and has not accessed or consumed any course content "
         "even after signing."
         ),
        ('"The cardholder did not meet Section 7.2 refund eligibility conditions"',
         "Section 7.2 requires completion of 2 weeks of modules, 2 hotseat calls, and lead generation activity — all "
         "within a 14-day refund window. These conditions are extensive and would require substantial engagement with a "
         "service the cardholder discovered was materially different from what was sold. The cardholder's claim is based on "
         "misrepresentation of the core service, not dissatisfaction after full use."
         ),
        ('"This is a business purchase, not a consumer purchase"',
         "The purchase was made by the cardholder personally, not by a registered business entity. Even setting aside "
         "consumer protections, the Misrepresentation Act 1967 applies to ALL contracts and prevents exclusion of "
         "liability for misrepresentation. Amex evaluates disputes under its own network rules regardless of B2B/B2C."
         ),
        ('"The cardholder did not use the refund request form"',
         "The merchant never provided the form referenced in Section 7.1. Section 7.4 requires them to provide it "
         "\"on request.\" The cardholder has formally requested it. Under UK law (Consumer Contracts Regulations 2013, "
         "Reg 32), cancellation can be communicated \"by any clear statement\" — a prescribed form cannot be exclusive."
         ),
        ('"The cardholder\'s own messages show understanding and enrollment"',
         "Any introductory messages sent by the cardholder on the Circle platform were standard courtesy responses "
         "during onboarding. The cardholder attended one onboarding Zoom call with the assigned coach, during which "
         "the coach confirmed that consistent weekly 1-on-1 calls are no longer offered. Polite participation in an "
         "onboarding process does not constitute acceptance of a materially different service — it is how the cardholder "
         "discovered the misrepresentation. The refund request was sent within 4 days, demonstrating prompt action."
         ),
        ('"Section 12.3 entire agreement clause supersedes verbal promises"',
         "Section 12.3 states the written terms constitute the entire agreement. However, the merchant's own Section 11.4 "
         "carves out misrepresentation: liability for \"misrepresentation as to a fundamental matter\" cannot be excluded. "
         "The entire agreement clause does not override the misrepresentation exception in the merchant's own terms. "
         "Additionally, these terms were not agreed before payment was collected."
         ),
        ('"The cardholder discussed payment plans, showing deliberation"',
         "Discussion of payment logistics does not validate the substance of what was sold. The cardholder deliberated "
         "over the financial commitment — not over whether the service included 1-on-1 Zoom coaching, which was "
         "presented as a given. The seller's written email confirms the 1-on-1 coaching promise. Deliberation over "
         "price does not cure misrepresentation of the product."
         ),
        ('"The written terms describe the actual service delivered"',
         "The cardholder's purchase decision was based on the seller's direct representations during the sales call "
         "and in the follow-up email (March 2, 15:18), not on terms that were sent as a link 9 minutes later with no "
         "acceptance mechanism. The seller's own email — written by the same individual who conducted the sales call — "
         "promises \"Dedicated 1-2-1 coach\" and \"calls to customise the process.\" These are the representations "
         "that induced the purchase."
         ),
        ('"Section 6.1 — non-use does not entitle a refund"',
         "Section 6.1 addresses clients who simply stop engaging with a properly delivered service. It does not apply "
         "when the reason for non-use is that the core service was misrepresented. The cardholder did not disengage "
         "from a service that matched what was sold — the cardholder discovered the service was fundamentally different "
         "from what was promised and immediately requested a refund."
         ),
        ('"The pre-start checklist shows the cardholder reviewed the terms"',
         "Checking a box on an onboarding checklist — completed on March 5, three days after payment — does not "
         "constitute informed consent to terms that should have been agreed before payment. The checklist was part of "
         "a post-payment onboarding sequence the cardholder was directed to complete in order to access the service "
         "they had already paid for. This is not voluntary review — it is a mandatory step imposed after financial "
         "commitment."
         ),
        ('"1-on-1 Zoom coaching IS available through our coaching clinics"',
         "The merchant's terms describe \"Coaching Clinics\" as group Zoom sessions. The seller's email promised "
         "\"Dedicated 1-2-1 coach for 12 weeks\" with \"calls to customise the process to your business\" — representing "
         "consistent, scheduled weekly coaching. What was delivered is fundamentally different: (a) the coach confirmed "
         "during the onboarding call that consistent weekly 1-on-1 calls are no longer offered; (b) there is no calendar "
         "or booking system to schedule 1-on-1 Zoom calls; and (c) the merchant's own terms describe the 1-2-1 coaching "
         "as \"a channel [that] facilitates the sharing of voice notes, document reviews, messages\" — a messaging thread, "
         "not scheduled Zoom calls."
         ),
        ('"Filing a chargeback is a breach of contract per Section 7.5"',
         "Section 7.5 threatens that initiating a payment dispute \"to circumvent our refund policy\" constitutes breach "
         "of contract. However, the cardholder followed the refund policy (requested within 14 days) and the merchant "
         "failed to honor it. The merchant did not provide the required refund form (Section 7.4), did not give a "
         "substantive response within 7 days (Section 12.5), and did not process the refund. A chargeback is the "
         "cardholder's statutory right as acknowledged in the merchant's own Section 12.5 Exceptions: \"Statutory rights "
         "that cannot be waived by agreement.\""
         ),
        ('"The 48-hour form completion window has expired"',
         "Section 7.1 states the refund request form must be completed \"within 48 hours of initiating the refund "
         "request.\" The cardholder initiated the refund request on March 6. The merchant never provided the form — their "
         "own Section 7.4 requires them to provide it \"on request.\" The 48-hour window cannot begin until the merchant "
         "fulfills their obligation to provide the form. The merchant cannot create a deadline tied to a form they refuse "
         "to supply, then claim the deadline has passed."
         ),
    ]

    for title, body_text in counters:
        story.append(Paragraph(title, s["h3"]))
        story.append(Paragraph(body_text, s["body"]))
        story.append(Spacer(1, 4))

    # Footer
    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Paragraph(
        f"Prepared {datetime.now().strftime('%B %d, %Y')}. All timestamps verified from cardholder's Gmail account "
        "(wmarceau@marceausolutions.com). 35 emails exported via Gmail API on March 12, 2026.",
        s["footer"]))

    return story


def main():
    styles = get_styles()

    # Generate the final comprehensive package
    output_path = str(OUTPUT_DIR / "FINAL-propane-dispute-package.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.55*inch, rightMargin=0.55*inch,
        topMargin=0.65*inch, bottomMargin=0.55*inch,
    )
    story = build_final_package(styles)
    doc.build(story)
    print(f"Final dispute package: {output_path}")

    # Open it
    import subprocess
    subprocess.run(["open", output_path])
    print("Done — opened.")


if __name__ == "__main__":
    main()
