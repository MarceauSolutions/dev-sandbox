#!/usr/bin/env python3
"""
Generate the Amex dispute package PDF for the Propane Fitness chargeback.
Produces two PDFs:
  1. propane-dispute-evidence-package.pdf — for Amex reviewer
  2. propane-filing-instructions.pdf — step-by-step for William
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add execution dir for branded_pdf_engine imports
sys.path.insert(0, str(Path(__file__).parent.parent / "execution"))

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
)

# --- Colors ---
NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED_ACCENT = HexColor("#c0392b")
GOLD = HexColor("#C9963C")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
MID_GRAY = HexColor("#e0e0e0")
WHITE = colors.white

OUTPUT_DIR = Path(__file__).parent


def get_styles():
    """Professional legal document styles."""
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=20, leading=26,
            textColor=NAVY, spaceAfter=4, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=11, leading=15,
            textColor=CHARCOAL, spaceAfter=14, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", fontName="Helvetica-Bold", fontSize=16, leading=22,
            textColor=NAVY, spaceBefore=20, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2", fontName="Helvetica-Bold", fontSize=13, leading=18,
            textColor=DARK_BLUE, spaceBefore=14, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3", fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=CHARCOAL, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=10, leading=14,
            textColor=CHARCOAL, spaceAfter=6, alignment=TA_JUSTIFY,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=CHARCOAL, spaceAfter=6,
        ),
        "quote": ParagraphStyle(
            "Quote", fontName="Helvetica-Oblique", fontSize=10, leading=14,
            textColor=HexColor("#555555"), leftIndent=20, rightIndent=20,
            spaceAfter=8, borderColor=MID_GRAY, borderWidth=0,
            borderPadding=4,
        ),
        "alert": ParagraphStyle(
            "Alert", fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=RED_ACCENT, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small", fontName="Helvetica", fontSize=8, leading=11,
            textColor=HexColor("#777777"), spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=7, leading=10,
            textColor=HexColor("#999999"), alignment=TA_CENTER,
        ),
        "step_num": ParagraphStyle(
            "StepNum", fontName="Helvetica-Bold", fontSize=14, leading=18,
            textColor=WHITE, alignment=TA_CENTER,
        ),
        "step_title": ParagraphStyle(
            "StepTitle", fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=NAVY, spaceAfter=4,
        ),
        "step_body": ParagraphStyle(
            "StepBody", fontName="Helvetica", fontSize=10, leading=14,
            textColor=CHARCOAL, spaceAfter=4, leftIndent=10,
        ),
        "checklist": ParagraphStyle(
            "Checklist", fontName="Helvetica", fontSize=10, leading=16,
            textColor=CHARCOAL, spaceAfter=2, leftIndent=20,
        ),
    }


def make_table(data, col_widths=None, header=True):
    """Create a styled table."""
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEADING', (0, 0), (-1, -1), 13),
        ('TEXTCOLOR', (0, 0), (-1, -1), CHARCOAL),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GRAY),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
        ]
    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))

    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style_cmds))
    return t


def hr():
    return HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceAfter=10, spaceBefore=10)


# ============================================================
# PDF 1: EVIDENCE PACKAGE FOR AMEX REVIEWER
# ============================================================

def build_evidence_package(styles):
    """Build the dispute evidence package for the Amex reviewer."""
    story = []
    s = styles

    # --- COVER / HEADER ---
    story.append(Spacer(1, 30))
    story.append(Paragraph("CHARGEBACK DISPUTE — EVIDENCE PACKAGE", s["title"]))
    story.append(Paragraph("Prepared for American Express Dispute Resolution", s["subtitle"]))
    story.append(hr())

    # Summary box
    summary_data = [
        ["Field", "Detail"],
        ["Cardholder", "William Marceau"],
        ["Email", "wmarceau@marceausolutions.com"],
        ["Merchant", "PROPANEFITNESS.COM NEWCASTLE GB (PropaneFitness Ltd)"],
        ["Transaction Date", "March 2, 2026"],
        ["Card 1 (ending 1007)", "$4,255.97 + $114.91 FTF = $4,370.88"],
        ["Card 2 (ending 1049)", "$4,255.97 + $114.91 FTF = $4,370.88"],
        ["TOTAL DISPUTED", "$8,741.76"],
        ["Dispute Category", "Services Not As Described / Misrepresentation"],
        ["Refund Requested", "March 6, 2026 (4 days after purchase)"],
        ["Merchant Deadline Given", "March 13, 2026"],
        ["Merchant Response", "Non-substantive (addressed only FX fees, ignored all grounds)"],
    ]
    story.append(make_table(summary_data, col_widths=[2.0*inch, 5.0*inch]))
    story.append(Spacer(1, 16))

    # --- SECTION 1: DISPUTE GROUNDS ---
    story.append(Paragraph("SECTION 1: GROUNDS FOR DISPUTE", s["h1"]))
    story.append(hr())

    # Ground 1
    story.append(Paragraph("Ground 1: BAIT-AND-SWITCH ON CORE SERVICE (Primary Ground)", s["h2"]))
    story.append(Paragraph(
        "During the sales call on March 2, 2026, the seller (Jim Galvin) explicitly promised <b>weekly 1-on-1 Zoom coaching sessions</b> "
        "with a dedicated coach, focused on client acquisition, sales skills, positioning, and content strategy. "
        "This was the primary reason for the purchase.", s["body"]
    ))
    story.append(Paragraph(
        "The seller's own follow-up email (March 2, 15:18 UTC) confirms in writing:", s["body"]
    ))
    story.append(Paragraph(
        '"Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, feedback and calls '
        'to customise the process to your business."', s["quote"]
    ))
    story.append(Paragraph(
        "After payment was collected, the cardholder was informed that <b>weekly 1-on-1 Zoom calls are no longer offered</b>. "
        "Instead, the cardholder was directed to a Circle.so group chat. "
        "The core service purchased was not delivered as represented.", s["body"]
    ))
    story.append(Paragraph("Supporting evidence: Exhibit A (Jim's sales email), Exhibit E (Circle.so access showing group chat only)", s["small"]))

    # Ground 2
    story.append(Paragraph("Ground 2: PROGRAM HAS NO VALUE BEYOND MISREPRESENTED SERVICE", s["h2"]))
    story.append(Paragraph(
        "The only unique value proposition was 1-on-1 human coaching on client-facing skills (sales, positioning, content strategy). "
        "The remaining course content consists of backend tools (funnel building, Facebook ads, automation setup) which the "
        "cardholder already has built and operational. The seller knew from the discovery call that the cardholder needed help "
        "with the human/sales side — yet sold a program that only delivers the backend technical content.", s["body"]
    ))

    # Ground 3
    story.append(Paragraph("Ground 3: TERMS NOT AGREED BEFORE PAYMENT", s["h2"]))
    story.append(Paragraph(
        "The merchant's own signed agreement process (via Jotform) was not completed until <b>March 5, 2026</b> — "
        "three full days after both charges were processed on March 2. The timeline proves payment was collected "
        "before the cardholder formally agreed to the terms:", s["body"]
    ))
    terms_timeline = [
        ["Time (March 2)", "Event"],
        ["15:18 UTC", "Sales email with pricing sent"],
        ["15:27 UTC", "Terms link emailed (no acceptance mechanism — just a URL)"],
        ["15:29 UTC", "First payment link sent (2 min after terms)"],
        ["15:30 UTC", "Second payment link sent (1 min later)"],
        ["15:32 UTC", "First charge processed — £3,150 on card ending 1007"],
        ["15:40 UTC", "Second charge processed — £3,150 on card ending 1049"],
        ["March 5", "Terms signed via Jotform (3 DAYS after payment collected)"],
    ]
    story.append(make_table(terms_timeline, col_widths=[1.8*inch, 5.2*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Sending a URL link is not the same as obtaining agreement. The merchant's own process required a separate "
        "signed agreement, which was not executed until 3 days after payment. The merchant's refund restrictions, "
        "cooling-off waiver, and dispute resolution clauses were not formally agreed to at the time of purchase.", s["body"]
    ))
    story.append(Paragraph("Supporting evidence: Exhibit A (email timestamps), Exhibit C (Jotform signed terms dated March 5)", s["small"]))

    # Ground 4
    story.append(Paragraph("Ground 4: WITHIN MERCHANT'S OWN 14-DAY REFUND POLICY", s["h2"]))
    story.append(Paragraph(
        "The merchant's published terms at propane-business.com/terms state:", s["body"]
    ))
    story.append(Paragraph(
        '"Within 14 Days of Purchase: We instead offer a full refund if the refund request form has been '
        'successfully completed within the first 14 days."', s["quote"]
    ))
    story.append(Paragraph(
        "The cardholder requested a refund on <b>March 6, 2026</b> — only 4 days after purchase. "
        "The 14-day window does not expire until March 16, 2026. "
        "The merchant has not honored its own published refund policy.", s["body"]
    ))
    story.append(Paragraph("Supporting evidence: Exhibit D (screenshot of merchant's terms page), Exhibit B (refund request email)", s["small"]))

    # Ground 5
    story.append(Paragraph("Ground 5: PRICING MISREPRESENTATION", s["h2"]))
    story.append(Paragraph(
        "During the March 2 sales call, Jim Galvin verbally quoted a retail price and a 20% discounted price. "
        "When asked if the price was negotiable, he stated it was not. However, his own written follow-up email "
        "sent minutes later contains materially different (lower) figures. A fixed, non-negotiable price does not change "
        "between a phone call and an email sent moments later. This is a high-pressure sales tactic designed to inflate "
        "the perceived value of the discount.", s["body"]
    ))
    price_table = [
        ["", "Retail Price", "After 20% Discount"],
        ["Verbal (on call)", "Higher figure quoted", "Higher discounted figure quoted"],
        ["Written (email, 15:18)", "£7,875", "£6,300"],
    ]
    story.append(make_table(price_table, col_widths=[2.0*inch, 2.5*inch, 2.5*inch]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The email figures are exact and verifiable. The discrepancy between verbal and written pricing — "
        "both applying exactly 20% — shows deliberate use of different base figures on the call.", s["body"]
    ))

    # Ground 6
    story.append(Paragraph("Ground 6: HIGH-PRESSURE SALES — 22-MINUTE PAYMENT SEQUENCE", s["h2"]))
    story.append(Paragraph(
        "The entire sequence — pricing email, terms link, two payment links, and both charges — "
        "was completed in under 22 minutes. Only <b>2 minutes</b> elapsed between the terms link (15:27) "
        "and the first payment link (15:29). The cardholder did not have a reasonable opportunity to review "
        "the contract terms before payment was collected.", s["body"]
    ))

    # Ground 7
    story.append(Paragraph("Ground 7: BREACH OF WRITTEN PROMISE — ACCESS NOT PROVIDED", s["h2"]))
    story.append(Paragraph(
        "The seller's pre-sale email explicitly stated:", s["body"]
    ))
    story.append(Paragraph(
        '"Once you\'ve processed the payment you\'ll receive immediate access via email with login information and next steps."',
        s["quote"]
    ))
    story.append(Paragraph(
        "Access was NOT provided immediately. It required a full day of follow-up to resolve. "
        "This is a direct breach of a specific written representation made at the point of sale.", s["body"]
    ))
    story.append(Paragraph("Supporting evidence: Exhibit A (email containing this promise)", s["small"]))

    # Ground 8
    story.append(Paragraph("Ground 8: UNDISCLOSED FOREIGN CURRENCY CHARGES", s["h2"]))
    story.append(Paragraph(
        "The cardholder is a US-based customer. At no point was he informed that charges would be processed "
        "in British Pounds (GBP), that the USD equivalent would be $4,255.97 per charge, or that a foreign "
        "transaction fee of $114.91 per card would be applied. Total undisclosed fees: <b>$229.82</b>.", s["body"]
    ))
    fee_table = [
        ["", "Card 1007", "Card 1049", "Total"],
        ["Charge (GBP → USD)", "$4,255.97", "$4,255.97", "$8,511.94"],
        ["Foreign Transaction Fee", "$114.91", "$114.91", "$229.82"],
        ["Total Per Card", "$4,370.88", "$4,370.88", "$8,741.76"],
    ]
    story.append(make_table(fee_table, col_widths=[2.0*inch, 1.6*inch, 1.6*inch, 1.6*inch]))

    # --- PAGE BREAK ---
    story.append(PageBreak())

    # --- SECTION 2: COMMUNICATION TIMELINE ---
    story.append(Paragraph("SECTION 2: COMPLETE COMMUNICATION TIMELINE", s["h1"]))
    story.append(hr())

    timeline_data = [
        ["Date / Time", "Event", "Evidence"],
        ["Feb 22, 2026", "Cardholder downloads Propane lead magnet (sales funnel entry)", "Email from jonny@propanefitness.com"],
        ["Feb 23, 2026", "Sales call booked with Propane team", "Booking confirmation email"],
        ["Feb 24, 2026", "Joe Halford (Propane) sends pre-call resources", "Email from joe@propanefitness.com"],
        ["Feb 25, 2026", "Initial sales call with Jim Galvin via Zoom", "Zoom link email from Jim"],
        ["Mar 2, 14:05", "Follow-up Zoom call with Jim (pricing discussed)", "Zoom link email from Jim"],
        ["Mar 2, 15:18", "Jim sends sales email — pricing, promises, 'immediate access'", "EXHIBIT A"],
        ["Mar 2, 15:27", "Terms URL link emailed (no acceptance mechanism)", "Email from Jim"],
        ["Mar 2, 15:29", "First payment link sent (SamCart)", "Email from Jim"],
        ["Mar 2, 15:30", "Second payment link sent (SamCart)", "Email from Jim"],
        ["Mar 2, 15:32", "CHARGE 1: £3,150 processed (card 1007)", "Stripe receipt #1257-2744"],
        ["Mar 2, 15:40", "CHARGE 2: £3,150 processed (card 1049)", "Stripe receipt #1001-9268"],
        ["Mar 2–3", "Access NOT provided (despite written promise)", "No login email received"],
        ["Mar 3–4", "Full day of follow-up to get access", "Email thread"],
        ["Mar 5", "Terms signed via Jotform — 3 DAYS AFTER payment", "EXHIBIT C (Invoice INV-6485333402225932830)"],
        ["Mar 5", "Discovered: 1-on-1 Zoom calls NOT offered (Circle chat instead)", "Circle.so platform"],
        ["Mar 5", "Discovered: course = backend tools cardholder already has", "Circle.so platform"],
        ["Mar 6", "Formal refund request sent (full grounds)", "EXHIBIT B"],
        ["Mar 6", "Follow-up with exact Amex statement amounts sent", "EXHIBIT B"],
        ["Mar 7", "Jim replies — addresses ONLY foreign transaction fees", "EXHIBIT F (Jim's reply)"],
        ["Mar 7", "Final demand sent — all 7 grounds restated, Mar 13 deadline", "EXHIBIT B"],
        ["Mar 13", "Deadline expired. No refund. No substantive response.", "—"],
    ]
    story.append(make_table(timeline_data, col_widths=[1.3*inch, 3.7*inch, 2.0*inch]))

    # --- SECTION 3: PAYMENT DETAILS ---
    story.append(Spacer(1, 16))
    story.append(Paragraph("SECTION 3: TRANSACTION DETAILS", s["h1"]))
    story.append(hr())

    story.append(Paragraph("Transaction 1 — Card ending 1007", s["h2"]))
    tx1 = [
        ["Field", "Detail"],
        ["Stripe Receipt #", "1257-2744"],
        ["Amount (GBP)", "£3,150.00"],
        ["Amount (USD)", "$4,255.97"],
        ["Foreign Transaction Fee", "$114.91"],
        ["Total Charged", "$4,370.88"],
        ["Date/Time", "March 2, 2026 — 15:32:27 UTC"],
        ["Description", '"2 x 3150 - PropaneBusiness"'],
        ["Processor", "Stripe (PropaneFitness acct: acct_182oNdF42QmTryTb)"],
        ["Payment Platform", "SamCart (Order #24344642)"],
    ]
    story.append(make_table(tx1, col_widths=[2.2*inch, 4.8*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Transaction 2 — Card ending 1049", s["h2"]))
    tx2 = [
        ["Field", "Detail"],
        ["Stripe Receipt #", "1001-9268"],
        ["Amount (GBP)", "£3,150.00"],
        ["Amount (USD)", "$4,255.97"],
        ["Foreign Transaction Fee", "$114.91"],
        ["Total Charged", "$4,370.88"],
        ["Date/Time", "March 2, 2026 — 15:40:09 UTC"],
        ["Description", '"3150 balancing payment propanebusiness - Copy"'],
        ["Processor", "Stripe (PropaneFitness acct: acct_182oNdF42QmTryTb)"],
        ["Payment Platform", "SamCart (Order #24344711)"],
    ]
    story.append(make_table(tx2, col_widths=[2.2*inch, 4.8*inch]))

    # --- SECTION 4: MERCHANT TERMS ANALYSIS ---
    story.append(PageBreak())
    story.append(Paragraph("SECTION 4: WHY MERCHANT'S TERMS DO NOT PROTECT THEM", s["h1"]))
    story.append(hr())

    story.append(Paragraph("4a. Their Dispute Resolution Clause", s["h2"]))
    story.append(Paragraph(
        "The merchant's terms require a 3-step process (written notice → negotiation → CEDR mediation) before any chargeback. "
        "They claim bypassing this = material breach + forfeiture of refund + liability for legal costs.", s["body"]
    ))
    story.append(Paragraph("Why it does not apply:", s["body_bold"]))
    story.append(Paragraph(
        "The terms were not formally agreed before payment. The merchant's own process required a Jotform signature, "
        "which was not completed until March 5 — 3 days after both charges. A chargeback is a banking process between "
        "the cardholder and American Express; the merchant's contract cannot override cardholder rights with the card issuer. "
        "American Express is not a party to their terms.", s["body"]
    ))

    story.append(Paragraph("4b. Their Cooling-Off Waiver", s["h2"]))
    story.append(Paragraph(
        "The merchant claims accessing materials waives the statutory 14-day cooling-off period.", s["body"]
    ))
    story.append(Paragraph("Why it does not apply:", s["body_bold"]))
    story.append(Paragraph(
        "Under UK Consumer Contracts Regulations 2013, a cooling-off waiver must be explicitly consented to BEFORE access is "
        "granted, which requires formally agreed terms BEFORE payment. The formal agreement was not signed until March 5, after "
        "access was already granted. Furthermore, the service delivered (group chat) is materially different from what was sold "
        "(1-on-1 Zoom coaching), which is grounds for rescission regardless of cooling-off period.", s["body"]
    ))

    story.append(Paragraph("4c. Their Collections Threat", s["h2"]))
    story.append(Paragraph(
        "The merchant claims filing a chargeback triggers account removal and potential collections referral. "
        "This is an empty threat: they would need to prove the cardholder owes them money, which they cannot do given the terms "
        "were signed post-payment, the core service was misrepresented, and the refund was requested within their own 14-day window. "
        "A UK company pursuing a US consumer through collections for a disputed charge is extremely costly and rarely pursued.", s["body"]
    ))

    # --- SECTION 5: EXHIBIT INDEX ---
    story.append(Spacer(1, 16))
    story.append(Paragraph("SECTION 5: EXHIBIT INDEX", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "The following exhibits should be attached to this dispute. Each is described below with its source location.", s["body"]
    ))

    exhibits = [
        ["Exhibit", "Description", "Source"],
        ["A", "Jim Galvin's sales email (Mar 2, 15:18 UTC)\n"
             "Contains: pricing, '1-2-1 dedicated coach' promise,\n"
             "'immediate access' promise, program details",
         "Gmail: wmarceau@marceausolutions.com\n"
         "Subject: 'Next steps to secure your spot'\n"
         "From: jim@propanefitness.com"],
        ["B", "Cardholder's refund request emails (Mar 6)\n"
             "and final demand (Mar 7, Mar 13 deadline)\n"
             "NOTE: Originals were accidentally deleted from\n"
             "Sent folder but exist on merchant's end in the\n"
             "same email thread",
         "Gmail Trash folder (check Trash)\n"
         "OR: Forward from Jim's replies which\n"
         "contain the original text quoted back"],
        ["C", "Signed terms via Jotform — dated March 5\n"
             "(proves terms signed 3 days AFTER payment)",
         "Gmail: wmarceau@marceausolutions.com\n"
         "Subject: 'Your signed terms'\n"
         "From: noreply@jotform.com\n"
         "Invoice: INV-6485333402225932830"],
        ["D", "Screenshot of merchant's terms page showing\n"
             "14-day refund policy",
         "URL: propane-business.com/terms\n"
         "(take screenshot before they change it)"],
        ["E", "Screenshot of Circle.so platform showing\n"
             "group chat — no 1-on-1 Zoom calls available",
         "Circle.so platform (Propane community)\n"
         "Screenshot the coaching section"],
        ["F", "Jim's reply email (Mar 7) — addresses ONLY\n"
             "foreign transaction fees, ignores all 7 grounds",
         "Gmail: wmarceau@marceausolutions.com\n"
         "From: jim@propanefitness.com"],
        ["G", "Stripe receipt #1257-2744 (card 1007)",
         "Gmail: from receipts+acct_\n"
         "182oNdF42QmTryTb@stripe.com"],
        ["H", "Stripe receipt #1001-9268 (card 1049)",
         "Gmail: from receipts+acct_\n"
         "182oNdF42QmTryTb@stripe.com"],
        ["I", "Amex statements showing both charges +\n"
             "foreign transaction fees ($114.91 each)",
         "Amex online: global.americanexpress.com\n"
         "Statements & Activity → March 2026"],
    ]
    story.append(make_table(exhibits, col_widths=[0.7*inch, 3.0*inch, 3.3*inch]))

    # Footer note
    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Paragraph(
        "This evidence package was prepared on March 12, 2026. All email timestamps have been verified from "
        "the cardholder's wmarceau@marceausolutions.com inbox. The cardholder attempted direct resolution with "
        "the merchant in good faith (March 6–13) before filing this dispute.", s["small"]
    ))

    return story


# ============================================================
# PDF 2: STEP-BY-STEP FILING INSTRUCTIONS FOR WILLIAM
# ============================================================

def build_filing_instructions(styles):
    """Build the step-by-step filing guide for William."""
    story = []
    s = styles

    story.append(Spacer(1, 20))
    story.append(Paragraph("PROPANE FITNESS — CHARGEBACK FILING GUIDE", s["title"]))
    story.append(Paragraph("Step-by-step instructions with exact locations for everything you need", s["subtitle"]))
    story.append(hr())

    # --- BEFORE YOU START ---
    story.append(Paragraph("BEFORE YOU START — Gather These Items", s["h1"]))
    story.append(hr())
    story.append(Paragraph(
        "You need to collect screenshots and PDFs of the evidence before filing. "
        "Do this FIRST so you have everything ready when you sit down to file.", s["body"]
    ))

    story.append(Paragraph("About Your Deleted Sent Emails", s["h2"]))
    story.append(Paragraph(
        "You mentioned you accidentally deleted the refund request emails you sent. Here's the good news:", s["body"]
    ))
    story.append(Paragraph(
        "<b>1. Check Gmail Trash:</b> Go to Gmail → Trash (left sidebar, you may need to click 'More' to see it). "
        "Emails stay in Trash for 30 days. Since you sent them March 6–7, they should still be recoverable. "
        "Search in Trash for: <b>to:jim@propanefitness.com</b>", s["body"]
    ))
    story.append(Paragraph(
        "<b>2. Check 'All Mail':</b> Gmail → All Mail. Search: <b>to:jim@propanefitness.com</b>. "
        "Even deleted sent emails sometimes remain in All Mail.", s["body"]
    ))
    story.append(Paragraph(
        "<b>3. Jim's reply quotes your text:</b> When Jim replied on March 7, his email likely contains your original "
        "message quoted below his response. Open Jim's March 7 reply and scroll down — your refund request text "
        "should be quoted there. Screenshot the entire thread.", s["body"]
    ))
    story.append(Paragraph(
        "<b>4. They exist on Jim's end:</b> The emails were sent successfully (Jim replied to them). "
        "Even if you can't recover them from your end, the fact that Jim responded to your March 6 refund request "
        "proves it was sent. His reply referencing your request IS evidence of your request.", s["body"]
    ))
    story.append(Paragraph(
        "<b>5. This dispute document:</b> The dispute narratives in the evidence package contain the substance of "
        "what you sent. Amex will see the full grounds regardless.", s["body"]
    ))

    story.append(PageBreak())

    # --- STEP-BY-STEP ---
    story.append(Paragraph("STEP-BY-STEP: COLLECT EVIDENCE", s["h1"]))
    story.append(hr())

    steps_collect = [
        (
            "Screenshot Jim's Sales Email (EXHIBIT A)",
            [
                "Open Gmail at mail.google.com (logged into wmarceau@marceausolutions.com)",
                "Search: <b>from:jim@propanefitness.com subject:\"Next steps to secure your spot\"</b>",
                "Open the email dated March 2, 2026 at 15:18",
                "Take a FULL screenshot (scroll through the entire email)",
                "Make sure the timestamp, sender, and all promises are visible",
                "Key text to capture: '1-2-1 dedicated coach' and 'immediate access' promises",
                "Save as: <b>Exhibit-A-sales-email.png</b>",
            ]
        ),
        (
            "Recover or Screenshot Your Refund Requests (EXHIBIT B)",
            [
                "In Gmail, click <b>Trash</b> in the left sidebar (click 'More' if hidden)",
                "Search in Trash: <b>to:jim@propanefitness.com</b>",
                "If found: select both emails → click 'Move to Inbox' to recover them, then screenshot",
                "If NOT in Trash: open Jim's March 7 reply and scroll down to see your quoted text",
                "Screenshot the full email thread showing your request and his non-response",
                "Save as: <b>Exhibit-B-refund-request.png</b>",
            ]
        ),
        (
            "Screenshot Signed Terms Email (EXHIBIT C)",
            [
                "In Gmail, search: <b>from:noreply@jotform.com subject:\"Your signed terms\"</b>",
                "Open the email dated March 5, 2026",
                "Screenshot showing the DATE (March 5) prominently — this proves terms signed AFTER payment",
                "Note the Invoice #: INV-6485333402225932830",
                "Save as: <b>Exhibit-C-signed-terms-march5.png</b>",
            ]
        ),
        (
            "Screenshot Merchant's Terms Page (EXHIBIT D) — DO THIS TODAY",
            [
                "Open your browser and go to: <b>propane-business.com/terms</b>",
                "Find the section about 14-day refund policy",
                "Take a full-page screenshot (they may change this page after you file)",
                "The key text: 'Within 14 Days of Purchase: We instead offer a full refund...'",
                "Save as: <b>Exhibit-D-merchant-terms-page.png</b>",
                "<b>DO THIS IMMEDIATELY</b> — they could update the page once they know you're disputing",
            ]
        ),
        (
            "Screenshot Circle.so Platform (EXHIBIT E)",
            [
                "Log into the Propane Circle community (Circle.so)",
                "Navigate to the coaching/mentorship section",
                "Screenshot showing: there are NO 1-on-1 Zoom call bookings available",
                "Screenshot showing: it's a GROUP chat, not dedicated 1-on-1 coaching",
                "Save as: <b>Exhibit-E-circle-group-chat.png</b>",
            ]
        ),
        (
            "Screenshot Jim's Non-Response Reply (EXHIBIT F)",
            [
                "In Gmail, search: <b>from:jim@propanefitness.com</b> and find his March 7 reply",
                "Screenshot the full email showing he ONLY addressed foreign transaction fees",
                "This proves he ignored all 7 substantive grounds",
                "Save as: <b>Exhibit-F-jim-reply-march7.png</b>",
            ]
        ),
        (
            "Screenshot/Save Stripe Receipts (EXHIBITS G & H)",
            [
                "In Gmail, search: <b>from:receipts+acct_182oNdF42QmTryTb@stripe.com</b>",
                "You should find 2 receipt emails from March 2, 2026",
                "Receipt #1257-2744 — £3,150.00 (card 1007) → save as <b>Exhibit-G-stripe-receipt-1007.png</b>",
                "Receipt #1001-9268 — £3,150.00 (card 1049) → save as <b>Exhibit-H-stripe-receipt-1049.png</b>",
            ]
        ),
        (
            "Download/Screenshot Amex Statements (EXHIBIT I)",
            [
                "Log into <b>global.americanexpress.com</b>",
                "Go to <b>Statements & Activity</b>",
                "Find the March 2, 2026 charges on BOTH cards (1007 and 1049)",
                "Screenshot each charge showing: the $4,255.97 amount AND the $114.91 foreign transaction fee",
                "Save as: <b>Exhibit-I-amex-statement-1007.png</b> and <b>Exhibit-I-amex-statement-1049.png</b>",
            ]
        ),
    ]

    for i, (title, substeps) in enumerate(steps_collect, 1):
        # Step header
        step_header_data = [[
            Paragraph(f"STEP {i}", s["step_num"]),
            Paragraph(title, s["step_title"]),
        ]]
        step_table = Table(step_header_data, colWidths=[0.6*inch, 6.4*inch])
        step_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), NAVY),
            ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(step_table)

        for substep in substeps:
            story.append(Paragraph(f"&bull; {substep}", s["step_body"]))
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # --- FILE THE DISPUTES ---
    story.append(Paragraph("FILE THE DISPUTES WITH AMEX", s["h1"]))
    story.append(hr())

    story.append(Paragraph("You are filing TWO separate disputes — one per card. You can do both in the same session.", s["body_bold"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Option A: FILE ONLINE (Recommended)", s["h2"]))
    online_steps = [
        ("Log into Amex",
         "Go to <b>global.americanexpress.com</b> and log into your account."),
        ("Navigate to Card 1 (ending 1007)",
         "Go to <b>Statements & Activity</b>. Find the charge from <b>PROPANEFITNESS.COM NEWCASTLE GB</b> "
         "dated March 2, 2026 for <b>$4,255.97</b>."),
        ("Click 'Dispute This Charge'",
         "Click on the charge → select <b>'Dispute This Charge'</b> or <b>'I have a billing issue'</b>."),
        ("Select Reason",
         "Choose: <b>'I didn't receive what I was promised'</b> or <b>'Goods/Services Not As Described'</b> "
         "or <b>'Misrepresentation'</b> — whichever option is closest."),
        ("Paste the Dispute Narrative",
         "Open the evidence package PDF (propane-dispute-evidence-package.pdf). "
         "The full dispute narrative is in Section 1. Copy the text from the chargeback letters file "
         "(docs/propane-chargeback-letters.md — CARD 1 section) and paste it into the dispute form. "
         "If there's a character limit, lead with Ground 1 (bait-and-switch) and Ground 4 (their own 14-day policy)."),
        ("Upload Evidence",
         "Attach: Exhibits A through I (all the screenshots/PDFs you collected). "
         "Also attach the evidence package PDF itself — it's organized for the reviewer."),
        ("Request FTF Reversal",
         "In the notes or a separate field, state: <b>'I also request reversal of the $114.91 foreign transaction fee "
         "associated with this disputed charge.'</b>"),
        ("Submit → Repeat for Card 2 (ending 1049)",
         "Find the second charge on card 1049 and repeat the exact same process. "
         "Use the CARD 2 narrative from propane-chargeback-letters.md. Same exhibits."),
    ]
    for i, (title, detail) in enumerate(online_steps, 1):
        story.append(Paragraph(f"<b>{i}. {title}</b>", s["body_bold"]))
        story.append(Paragraph(detail, s["body"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Option B: FILE BY PHONE", s["h2"]))
    story.append(Paragraph("<b>Call: 1-800-528-4800</b>", s["body_bold"]))
    phone_steps = [
        "Tell them you need to dispute two charges from the same merchant",
        "Reference both transaction dates as March 2, 2026",
        "Merchant name: PROPANEFITNESS.COM NEWCASTLE GB",
        "Lead with: 'I was sold 1-on-1 Zoom coaching and received a group chat instead — bait and switch'",
        "Mention you requested a refund within their own 14-day policy and they refused",
        "Ask them to reverse the $114.91 FTF on each card as well",
        "They may ask you to upload documents after the call — use the same exhibits",
        "You can file both disputes in the same call",
    ]
    for step in phone_steps:
        story.append(Paragraph(f"&bull; {step}", s["checklist"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("AFTER FILING", s["h1"]))
    story.append(hr())

    after_steps = [
        "<b>Save your dispute reference numbers</b> — Amex will give you a case number for each dispute",
        "<b>Do NOT contact Propane</b> — Let Amex handle all communication from here",
        "<b>Expect temporary credits</b> — Amex typically issues provisional credits within 5–10 business days",
        "<b>Merchant has ~20 days to respond</b> — If they don't respond, you win automatically",
        "<b>If Amex asks for more info</b> — Respond promptly; refer back to this evidence package",
        "<b>Regulatory complaints (optional, after chargeback):</b> UK Trading Standards (0808 223 1133) and CMA (gov.uk/cma-cases) — for misrepresentation of services",
    ]
    for step in after_steps:
        story.append(Paragraph(f"&bull; {step}", s["checklist"]))

    # --- QUICK REFERENCE ---
    story.append(Spacer(1, 16))
    story.append(Paragraph("QUICK REFERENCE — EVERYTHING IN ONE PLACE", s["h1"]))
    story.append(hr())

    ref_data = [
        ["What You Need", "Where to Find It"],
        ["Jim's sales email (Exhibit A)", "Gmail → search: from:jim@propanefitness.com subject:\"Next steps to secure your spot\""],
        ["Your refund request (Exhibit B)", "Gmail Trash → search: to:jim@propanefitness.com\nOR: quoted in Jim's March 7 reply"],
        ["Signed terms (Exhibit C)", "Gmail → search: from:noreply@jotform.com subject:\"Your signed terms\""],
        ["Merchant's 14-day policy (Exhibit D)", "Browser → propane-business.com/terms (screenshot TODAY)"],
        ["Circle.so group chat proof (Exhibit E)", "Log into Propane Circle community → coaching section"],
        ["Jim's non-response (Exhibit F)", "Gmail → from:jim@propanefitness.com (March 7 reply)"],
        ["Stripe receipts (Exhibits G, H)", "Gmail → from:receipts+acct_182oNdF42QmTryTb@stripe.com"],
        ["Amex statements (Exhibit I)", "global.americanexpress.com → Statements & Activity"],
        ["Dispute narrative (Card 1)", "File: docs/propane-chargeback-letters.md → CARD 1 section"],
        ["Dispute narrative (Card 2)", "File: docs/propane-chargeback-letters.md → CARD 2 section"],
        ["Full evidence package PDF", "File: docs/propane-dispute-evidence-package.pdf (this companion doc)"],
    ]
    story.append(make_table(ref_data, col_widths=[2.5*inch, 4.5*inch]))

    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Paragraph(
        "Prepared March 12, 2026. You have a strong case: bait-and-switch on the core service, "
        "within their own 14-day policy, terms signed after payment. File both disputes and let Amex work for you.",
        s["small"]
    ))

    return story


# ============================================================
# MAIN
# ============================================================

def main():
    styles = get_styles()

    # PDF 1: Evidence package for Amex
    evidence_path = str(OUTPUT_DIR / "propane-dispute-evidence-package.pdf")
    doc1 = SimpleDocTemplate(
        evidence_path, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.7*inch, bottomMargin=0.6*inch,
    )
    story1 = build_evidence_package(styles)
    doc1.build(story1)
    print(f"Evidence package: {evidence_path}")

    # PDF 2: Filing instructions for William
    instructions_path = str(OUTPUT_DIR / "propane-filing-instructions.pdf")
    doc2 = SimpleDocTemplate(
        instructions_path, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.7*inch, bottomMargin=0.6*inch,
    )
    story2 = build_filing_instructions(styles)
    doc2.build(story2)
    print(f"Filing instructions: {instructions_path}")

    # Open both
    import subprocess
    subprocess.run(["open", evidence_path])
    subprocess.run(["open", instructions_path])
    print("Done — both PDFs opened.")


if __name__ == "__main__":
    main()
