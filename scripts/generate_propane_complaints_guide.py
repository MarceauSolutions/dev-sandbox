#!/usr/bin/env python3
"""Generate the Propane Fitness Dispute — Regulatory Complaints & Reviews Guide PDF."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from io import BytesIO

from execution.branded_pdf_engine import (
    BrandConfig, _register_fonts, get_brand_styles,
    _on_page, accent_line, section_title, branded_table, bullet_list
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'propane-regulatory-complaints-guide.pdf')


def warning_box(text, styles):
    """Red-bordered warning box."""
    data = [[Paragraph(text, ParagraphStyle(
        "WarningText", fontName=BrandConfig.BODY_FONT_BOLD,
        fontSize=10, leading=14, textColor=HexColor("#991b1b"),
    ))]]
    t = Table(data, colWidths=[6.2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 2, HexColor("#ef4444")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def copy_paste_box(text, styles):
    """Light gold background box for copy-paste content."""
    data = [[Paragraph(text, ParagraphStyle(
        "CopyPaste", fontName=BrandConfig.BODY_FONT,
        fontSize=9, leading=13, textColor=BrandConfig.CHARCOAL,
    ))]]
    t = Table(data, colWidths=[6.2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 1, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def info_box(title, text, styles):
    """Gold-bordered info box with bold title."""
    content = f'<b>{title}:</b> {text}'
    data = [[Paragraph(content, ParagraphStyle(
        "InfoBox", fontName=BrandConfig.BODY_FONT,
        fontSize=10, leading=14, textColor=BrandConfig.CHARCOAL,
    ))]]
    t = Table(data, colWidths=[6.2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 1.5, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def build_cover(styles):
    """Build cover page elements."""
    elements = []
    elements.append(Spacer(1, 1.5 * inch))

    # Title
    title_style = ParagraphStyle(
        "CoverTitle", fontName=BrandConfig.HEADING_FONT,
        fontSize=22, leading=28, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=8,
    )
    elements.append(Paragraph("PROPANE FITNESS DISPUTE", title_style))

    title_style2 = ParagraphStyle(
        "CoverTitle2", fontName=BrandConfig.HEADING_FONT,
        fontSize=18, leading=24, textColor=BrandConfig.GOLD,
        alignment=TA_CENTER, spaceAfter=16,
    )
    elements.append(Paragraph("REGULATORY COMPLAINTS &amp; REVIEWS GUIDE", title_style2))

    # Gold line
    elements.append(HRFlowable(width="60%", thickness=2, color=BrandConfig.GOLD,
                                spaceBefore=8, spaceAfter=16))

    # Subtitle
    sub_style = ParagraphStyle(
        "CoverSub", fontName=BrandConfig.BODY_FONT,
        fontSize=13, leading=18, textColor=BrandConfig.DARK_GRAY,
        alignment=TA_CENTER, spaceAfter=40,
    )
    elements.append(Paragraph("Execution Playbook for All Threatened Actions", sub_style))

    # Details
    detail_style = ParagraphStyle(
        "CoverDetail", fontName=BrandConfig.BODY_FONT,
        fontSize=11, leading=16, textColor=BrandConfig.CHARCOAL,
        alignment=TA_CENTER, spaceAfter=6,
    )
    elements.append(Paragraph("Updated: March 16, 2026", detail_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("William Marceau", detail_style))
    elements.append(Paragraph("wmarceau@marceausolutions.com", detail_style))

    elements.append(Spacer(1, 1.5 * inch))

    # Confidential footer
    conf_style = ParagraphStyle(
        "CoverConf", fontName=BrandConfig.BODY_FONT,
        fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("CONFIDENTIAL — Personal Reference Document", conf_style))
    elements.append(PageBreak())
    return elements


def build_section1(styles):
    """Section 1: Overview — What Was Threatened."""
    elements = []
    elements.append(section_title("Section 1: Overview — What Was Threatened", styles))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        'On March 16, 2026, Propane escalated from non-response to outright intimidation — threatening '
        'breach of contract (Section 7.5), rejection of the refund, a counterclaim for the full £6,300, '
        'and referral to a collections agency with legal costs on a "full indemnity basis." This is in '
        'response to the cardholder exercising their statutory right to file a chargeback dispute after '
        '8 days and 4 formal emails with no substantive response.', styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(warning_box(
        "MARCH 16 ESCALATION: Propane's legal threats add new regulatory grounds. Threatening a consumer "
        "with collections, legal costs, and contract default for exercising statutory chargeback rights "
        "constitutes an aggressive commercial practice under Regulation 7 of the CPRs 2008. The clause "
        "attempting to waive chargeback rights (Section 7.5) is an unfair term under Consumer Rights Act "
        "2015, Part 2.", styles))
    elements.append(Spacer(1, 12))

    # Status table
    elements.append(Paragraph('<b>Action Status</b>', styles["h3"]))
    elements.append(branded_table(
        ["Action", "Status", "When to Execute"],
        [
            ["Amex chargebacks (both cards)", "COMPLETED — Filed March 14, 2026", "Done"],
            ["UK Trading Standards complaint", "FILE NOW — strengthened by March 16 threats", "Immediately"],
            ["CMA complaint", "FILE NOW — pattern of intimidation documented", "Immediately"],
            ["Action Fraud report", "Optional — if pattern of misrepresentation", "This week"],
            ["Trustpilot review", "Draft ready — DO NOT post yet", "After chargeback fully resolved"],
            ["Google Business review", "Draft ready — DO NOT post yet", "After chargeback fully resolved"],
        ],
        col_widths=[2.3 * inch, 2.2 * inch, 2.0 * inch],
    ))
    elements.append(Spacer(1, 12))

    elements.append(warning_box(
        "IMPORTANT: Reviews should be posted ONLY after the chargeback is fully resolved. "
        "Posting during an active dispute gives Propane ammunition to argue bad faith or retaliation. "
        "Trading Standards and CMA complaints can be filed immediately — these are regulatory reports, "
        "not public actions.", styles))

    elements.append(PageBreak())
    return elements


def build_section2(styles):
    """Section 2: UK Trading Standards Complaint."""
    elements = []
    elements.append(section_title("Section 2: UK Trading Standards Complaint", styles))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph('<b>What this is:</b>', styles["h3"]))
    elements.append(Paragraph(
        'A formal report to the UK\'s consumer protection enforcement body. Trading Standards '
        'investigates businesses that engage in unfair commercial practices. They have the power '
        'to prosecute under the Consumer Protection from Unfair Trading Regulations 2008.',
        styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>How it helps you:</b>', styles["h3"]))
    elements.append(Paragraph(
        'Creates an official government record of Propane\'s practices. If other consumers have '
        'also complained, it builds a pattern. Trading Standards can investigate independently — '
        'you don\'t need to do anything after filing.', styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>Relevant Law</b>', styles["h3"]))
    elements.append(Paragraph(
        '<b>Consumer Protection from Unfair Trading Regulations 2008 (CPRs)</b>', styles["body"]))
    elements.extend(bullet_list([
        '<b>Regulation 5:</b> Misleading actions — giving false information or creating a false impression about a product',
        '<b>Regulation 6:</b> Misleading omissions — omitting material information a consumer needs to make an informed decision',
        '<b>Regulation 7:</b> Aggressive commercial practices — using harassment, coercion, or undue influence',
    ], styles))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('<b>Filing Method</b>', styles["h3"]))
    elements.append(Paragraph(
        'Online via Citizens Advice (they forward to the relevant Trading Standards office)', styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>Step-by-step:</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Go to: <b>citizensadvice.org.uk/consumer/get-more-help/report-to-trading-standards/</b>',
        'Click "Report to Trading Standards" or "Make a consumer complaint"',
        'You\'ll be directed to an online form',
        'Fill in the business details and your complaint narrative (provided below)',
    ], styles))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>Alternative — By Phone:</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Citizens Advice consumer helpline: <b>0808 223 1133</b> (free from UK phones)',
        'From the US: Use Skype, Google Voice, or a VoIP service. Dial <b>+44 808 223 1133</b>',
        'Hours: Monday to Friday, 9am–5pm GMT',
    ], styles))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('<b>Business Details to Provide</b>', styles["h3"]))
    elements.append(info_box("Business Details", (
        '<br/>Business name: <b>Propane Fitness Ltd</b><br/>'
        'Trading names: PropaneFitness, Propane Business, PropaneBusiness<br/>'
        'Address: <b>69 Church Way, North Shields NE29 0AE, United Kingdom</b><br/>'
        'VAT Number: 266679253<br/>'
        'Website: propanefitness.com / propane-business.com<br/>'
        'Contact: Jim Galvin (jim@propanefitness.com), admin@propanefitness.com<br/>'
        'Company registration: Propane Fitness Limited (verify at beta.companieshouse.gov.uk)'
    ), styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>Written Complaint — Copy and Submit</b>', styles["h3"]))
    elements.append(copy_paste_box(
        'I am filing a complaint against Propane Fitness Ltd (69 Church Way, North Shields NE29 0AE, '
        'VAT 266679253) for misrepresentation of services under the Consumer Protection from Unfair '
        'Trading Regulations 2008.<br/><br/>'
        'On March 2, 2026, I purchased a 12-week business mentorship program from Propane Fitness for '
        '£6,300 (approximately $8,741.76 USD including foreign transaction fees). The purchase was made '
        'after a sales call with Jim Galvin, the company\'s salesperson.<br/><br/>'
        '<b>MISLEADING ACTION (Regulation 5):</b><br/>'
        'The seller\'s written sales email, sent on March 2 at 15:18 UTC, explicitly promised: '
        '\'Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, feedback and '
        'calls to customise the process to your business.\' This was the primary reason I purchased. '
        'After payment, during my onboarding Zoom call on March 5, my assigned coach confirmed that '
        'consistent weekly 1-on-1 Zoom coaching calls are no longer offered and the program instead '
        'relies on group coaching clinics and a community platform. The core service I purchased — '
        'dedicated personal coaching — was not delivered as represented.',
        styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>AGGRESSIVE COMMERCIAL PRACTICE (Regulation 7):</b><br/><br/>'
        '<b>A. High-Pressure Sales:</b><br/>'
        'The entire payment sequence was completed in 22 minutes:<br/>'
        '&bull; 15:18 — Pricing email sent<br/>'
        '&bull; 15:27 — Terms link sent (9 minutes later)<br/>'
        '&bull; 15:29 — First payment link sent (2 minutes after terms)<br/>'
        '&bull; 15:30 — Second payment link sent<br/>'
        '&bull; 15:32 — First charge processed (£3,150)<br/>'
        '&bull; 15:40 — Second charge processed (£3,150)<br/>'
        'I had 2 minutes between receiving the terms link and being sent payment links for an £6,300 '
        'purchase. The formal terms agreement (via Jotform) was not signed until March 5 — 3 days after '
        'both charges were processed.<br/><br/>'
        '<b>B. Post-Dispute Intimidation and Threats (March 16, 2026):</b><br/>'
        'After I filed chargebacks (on March 14, following 8 days of non-response to 4 formal emails), '
        'the company sent an email on March 16 at 12:28 UTC stating:<br/><br/>'
        '&bull; "Under Section 7.5 of the terms you accepted at checkout, any attempt to bypass our refund '
        'policy constitutes a breach of contract"<br/>'
        '&bull; "This results in the immediate rejection of your refund request"<br/>'
        '&bull; "Gives us the right to counterclaim for any outstanding amounts owed to us, plus legal costs"<br/>'
        '&bull; "We would need to initiate recovery of the full balance of £6,300 and related costs through a '
        'collections agency. This would include collection fees, court fees, and legal expenses on a full '
        'indemnity basis."<br/><br/>'
        'This constitutes using coercion and undue influence to pressure a consumer into withdrawing a '
        'legitimate dispute. The company is threatening debt collection and legal costs against a consumer '
        'who is exercising their statutory right to file a chargeback — a right that the company\'s own terms '
        '(Section 12.5, Exceptions) acknowledge cannot be waived.',
        styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>FAILURE TO HONOR OWN REFUND POLICY:</b><br/>'
        'The company\'s published terms (propane-business.com/terms, Section 7.1) state: \'Within 14 Days '
        'of Purchase: We instead offer a full refund if the refund request form has been successfully '
        'completed within the first 14 days.\' I requested a refund on March 6 — Day 4 of the 14-day '
        'window. The company did not honor their own refund policy, did not provide the refund request form '
        'required by their own Section 7.4 until March 16 (10 days late, attached to a legal threat), and '
        'failed to provide a substantive response within 7 days as required by their own Section 12.5.<br/><br/>'
        '<b>UNFAIR CONTRACT TERMS (Consumer Rights Act 2015, Part 2):</b><br/>'
        'Section 7.5 of the company\'s terms purports to treat filing a chargeback as a "breach of contract" '
        'that triggers refund rejection, counterclaims, and debt collection. This clause attempts to waive '
        'the consumer\'s statutory right to dispute a charge through their card issuer. Under the Consumer '
        'Rights Act 2015, Part 2, terms that restrict the consumer\'s right to legal remedies or create a '
        'significant imbalance in the parties\' rights and obligations are unfair and unenforceable.',
        styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>PATTERN OF BEHAVIOR:</b><br/>'
        'During a voicemail on March 14, 2026, my assigned coach stated: \'In situations like this, whenever '
        'they have cropped up in the past...\' — indicating this is a recurring issue with the company.<br/><br/>'
        'I sent 8 formal emails between March 6 and March 16 requesting a refund. The company\'s responses '
        'consisted of: (1) a March 7 reply that addressed only foreign transaction fees and ignored all refund '
        'grounds, (2) the salesperson (Jim Galvin) stating on March 14 "This has nothing to do with me, mate" '
        'and removing the admin team from CC, (3) a March 16 request to withdraw the chargeback before they '
        'would "review" the refund, and (4) a March 16 email threatening breach of contract, collections, and '
        'legal costs. At no point did the company provide a substantive response to any refund ground or commit '
        'to issuing a refund.<br/><br/>'
        'I am a US-based consumer (Naples, Florida). I purchased this service remotely via phone and internet. '
        'The transaction was processed in GBP through Stripe (merchant account acct_182oNdF42QmTryTb). The USD '
        'equivalent and foreign transaction fees ($229.82 total) were never disclosed before or during payment.',
        styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>Phone Script (If Calling Citizens Advice)</b>', styles["h3"]))
    elements.append(copy_paste_box(
        '"Hi, I\'d like to report a business for misrepresentation of services. The company is Propane '
        'Fitness Ltd, based in North Shields. They sold me a business mentorship program for £6,300. The '
        'salesperson promised dedicated weekly one-on-one coaching in writing. After I paid, I was told '
        'one-on-one calls are no longer offered and the program is group coaching instead. I requested a '
        'refund within their own 14-day refund window and they haven\'t honored it. I\'d like to file a '
        'formal complaint under the Consumer Protection from Unfair Trading Regulations."<br/><br/>'
        '<i>Then provide the business details and complaint narrative when prompted.</i>', styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>Evidence to Reference</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Jim\'s sales email (March 2, 15:18) promising "Dedicated 1-2-1 coach"',
        'The 22-minute payment timeline',
        'Jotform signed terms dated March 5 (3 days after payment)',
        '8 formal refund request emails (March 6, 7, 12, 13, 14 x2, 16 x2)',
        'Phil\'s voicemail admitting this has happened before',
        'Jim\'s March 14 email: "This has nothing to do with me, mate" (salesperson disowning the sale)',
        'Propane admin\'s March 16 email threatening Section 7.5 breach of contract, collections, and legal costs',
        'Company terms at propane-business.com/terms (especially Sections 7.1, 7.4, 7.5, 11.4, 12.5)',
        'Updated evidence package PDF with full timeline and all correspondence',
    ], styles))

    elements.append(PageBreak())
    return elements


def build_section3(styles):
    """Section 3: CMA Complaint."""
    elements = []
    elements.append(section_title("Section 3: Competition and Markets Authority (CMA) Complaint", styles))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph('<b>What this is:</b>', styles["h3"]))
    elements.append(Paragraph(
        'The CMA is the UK\'s primary competition and consumer protection authority. They investigate '
        'businesses that engage in unfair commercial practices at a systemic level. A CMA complaint is '
        'more about pattern/systemic behavior than individual resolution.', styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>How it helps you:</b>', styles["h3"]))
    elements.append(Paragraph(
        'If the CMA receives multiple complaints about Propane\'s sales practices, they can open a '
        'formal investigation. The CMA has the power to issue enforcement orders, pursue court orders, '
        'and impose penalties.', styles["body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph('<b>Filing Method</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Go to: <b>gov.uk/government/organisations/competition-and-markets-authority</b>',
        'Click "Contact us" or navigate to the complaints/tips section',
        'Or email directly: <b>general.enquiries@cma.gov.uk</b>',
        'You can also use their online reporting form for consumer issues',
    ], styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>Written Complaint — Copy and Submit (or email to general.enquiries@cma.gov.uk)</b>', styles["h3"]))
    elements.append(copy_paste_box(
        '<b>Subject: Consumer Complaint — Propane Fitness Ltd — Unfair Commercial Practices</b><br/><br/>'
        'I am writing to report unfair commercial practices by Propane Fitness Ltd (69 Church Way, North '
        'Shields NE29 0AE, VAT 266679253, trading as PropaneFitness and Propane Business).<br/><br/>'
        'I believe this company engages in systemic unfair commercial practices including:<br/><br/>'
        '<b>1. MISREPRESENTATION OF SERVICES:</b><br/>'
        'The company sells business mentorship programs for £6,300+ using sales calls and written emails that '
        'promise \'Dedicated 1-2-1 coach for 12 weeks\' with \'calls to customise the process to your business.\' '
        'After payment is collected, customers are informed that consistent weekly 1-on-1 coaching calls are no '
        'longer offered and the program relies primarily on group coaching clinics and an online community platform. '
        'The core service sold is not the service delivered.<br/><br/>'
        '<b>2. HIGH-PRESSURE SALES TACTICS:</b><br/>'
        'In my case, the entire sequence from pricing email to full £6,300 payment was completed in 22 minutes. '
        'Terms were sent just 2 minutes before payment links, providing no reasonable opportunity to review a '
        'contract for a high-value purchase. The formal terms agreement (via Jotform) was not signed until 3 days '
        'after both charges were processed.', styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>3. FAILURE TO HONOR PUBLISHED REFUND POLICY:</b><br/>'
        'The company\'s terms (Section 7.1) promise a full refund within 14 days. I requested a refund on Day 4. '
        'The company failed to honor it, failed to provide the required refund request form (Section 7.4) until '
        'March 16 — 10 days late and attached to a legal threat — and failed to respond substantively within '
        '7 days (Section 12.5).<br/><br/>'
        '<b>4. PATTERN OF BEHAVIOR:</b><br/>'
        'During a voicemail on March 14, my assigned coach stated: \'In situations like this, whenever they have '
        'cropped up in the past...\' — indicating this is a recurring issue.',
        styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>5. UNFAIR TERMS &amp; INTIMIDATION (Consumer Rights Act 2015 + CPRs Regulation 7):</b><br/>'
        'Section 7.5 of the company\'s terms treats filing a chargeback as a "breach of contract" triggering '
        'refund rejection, counterclaims, and debt collection. On March 16, the company explicitly invoked this '
        'clause and threatened: breach of contract, immediate refund rejection, recovery of £6,300 through a '
        'collections agency, and court fees on a "full indemnity basis."<br/><br/>'
        'These threats target a consumer who (a) requested a refund within the 14-day window, (b) sent 8 emails '
        'over 10 days with no substantive response, and (c) exercised statutory chargeback rights only after the '
        'company failed to act. The company\'s own Section 12.5 (Exceptions) acknowledges statutory rights cannot '
        'be waived — contradicting their Section 7.5 enforcement.',
        styles))
    elements.append(Spacer(1, 4))
    elements.append(copy_paste_box(
        '<b>Company details:</b><br/>'
        '&bull; Propane Fitness Ltd, 69 Church Way, North Shields NE29 0AE<br/>'
        '&bull; VAT: 266679253<br/>'
        '&bull; Websites: propanefitness.com, propane-business.com<br/>'
        '&bull; Key personnel: Jim Galvin (salesperson), Jonny Bolton, Phil Charlton (coach), Reeni Harania<br/>'
        '&bull; Payment processor: Stripe (acct_182oNdF42QmTryTb), SamCart checkout<br/><br/>'
        'I have filed chargebacks with my card issuer and a separate complaint with Trading Standards. I have a '
        'complete evidence package with 38+ email exports, voicemail recordings, and the company\'s own terms.',
        styles))

    elements.append(PageBreak())
    return elements


def build_section4(styles):
    """Section 4: Trustpilot Review."""
    elements = []
    elements.append(section_title("Section 4: Trustpilot Review", styles))
    elements.append(Spacer(1, 4))

    elements.append(warning_box(
        "WARNING: Do NOT post this review until the chargeback is fully resolved. Posting during an active "
        "dispute gives Propane's legal team ammunition to argue retaliation or bad faith. Save this draft and "
        "post only after Amex issues a final decision.", styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>How to Post</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Go to <b>trustpilot.com</b>',
        'Search "Propane Fitness" or "PropaneBusiness"',
        'Click "Write a review"',
        'You may need to create a Trustpilot account',
        'Select star rating: <b>1 star</b>',
        'Paste the review below',
    ], styles))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('<b>Review Title</b>', styles["h3"]))
    elements.append(copy_paste_box(
        'Promised 1-on-1 coaching. Delivered group calls. Refused refund within their own 14-day window.',
        styles))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('<b>Review Text — Factual, No Emotion</b>', styles["h3"]))
    elements.append(copy_paste_box(
        'I purchased the Propane Business mentorship program for £6,300 in March 2026 based on a sales call '
        'and a written follow-up email from their salesperson that explicitly promised \'Dedicated 1-2-1 coach '
        'for 12 weeks\' with \'calls to customise the process to your business.\'<br/><br/>'
        'After payment, during my onboarding Zoom call, my assigned coach told me that consistent weekly 1-on-1 '
        'Zoom coaching calls are no longer offered. The program instead relies on group coaching clinics and an '
        'online community platform. This is fundamentally different from what was sold to me.<br/><br/>'
        'I requested a refund on Day 4 — well within their published 14-day refund window. Their terms (Section '
        '7.1) state: \'We offer a full refund if the refund request form has been successfully completed within '
        'the first 14 days.\' Despite four formal emails over 8 days, the company did not issue a refund, did not '
        'provide the required refund request form (their own Section 7.4), and did not provide a substantive '
        'response to any of my grounds for requesting a refund.<br/><br/>'
        'The entire sales process — from pricing email to full £6,300 collected — took 22 minutes. The terms were '
        'not formally signed until 3 days after payment was processed.<br/><br/>'
        'I ultimately had to file chargebacks through my card issuer to recover my money.<br/><br/>'
        '<b>Timeline:</b><br/>'
        '&bull; March 2: Sales call + payment collected (22 minutes from first pricing email to both charges processed)<br/>'
        '&bull; March 5: Terms signed (3 days AFTER payment)<br/>'
        '&bull; March 5: Onboarding call — coach confirms 1-on-1 calls no longer offered<br/>'
        '&bull; March 6: Formal refund request sent (Day 4 of 14)<br/>'
        '&bull; March 7-13: Four emails sent, no refund issued, no refund form provided<br/>'
        '&bull; March 14: Filed chargebacks after exhausting all direct resolution attempts<br/>'
        '&bull; March 16: Company finally provided refund form (10 days late), then threatened breach '
        'of contract, collections agency, court fees, and legal costs on "full indemnity basis" for filing '
        'the chargebacks<br/><br/>'
        'The company\'s own terms (Section 12.5 Exceptions) acknowledge that statutory rights, including the '
        'right to file card issuer disputes, cannot be waived. They threatened me anyway.<br/><br/>'
        'This review contains only facts documented in emails and the company\'s own published terms.',
        styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>Important Guidelines</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Stick strictly to facts — dates, quotes, events',
        'Do not use emotional language ("scam," "fraud," "rip-off")',
        'Do not speculate about motives',
        'Reference their own terms and written promises',
        'If Propane responds publicly, do not engage in a back-and-forth. If they state anything inaccurate, respond once with a factual correction and leave it.',
    ], styles))

    elements.append(PageBreak())
    return elements


def build_section5(styles):
    """Section 5: Google Business Review."""
    elements = []
    elements.append(section_title("Section 5: Google Business Review", styles))
    elements.append(Spacer(1, 4))

    elements.append(warning_box(
        "Same timing rule as Trustpilot — Do NOT post until the chargeback is fully resolved.", styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('<b>How to Post</b>', styles["h3"]))
    elements.extend(bullet_list([
        'Search "Propane Fitness" on Google Maps (<b>maps.google.com</b>)',
        'Find their business listing',
        'Click "Write a review"',
        'You\'ll need to be signed into a Google account',
        'Select star rating: <b>1 star</b>',
        'Paste the review below',
    ], styles))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('<b>Review Text (Shorter Format for Google)</b>', styles["h3"]))
    elements.append(copy_paste_box(
        'Purchased a £6,300 business mentorship based on a written promise of \'Dedicated 1-2-1 coach for '
        '12 weeks.\' After payment, was told weekly 1-on-1 coaching calls are no longer offered — the program '
        'is group clinics and a community chat instead.<br/><br/>'
        'Requested a refund on Day 4 of their published 14-day refund window. Sent four formal emails over 8 '
        'days. Company did not issue the refund, did not provide the refund form required by their own terms, '
        'and did not give a substantive response.<br/><br/>'
        'The full £6,300 was collected within 22 minutes of receiving the pricing email. Terms were signed 3 '
        'days after payment was already processed. Had to file chargebacks to recover funds.', styles))

    elements.append(PageBreak())
    return elements


def build_section6(styles):
    """Section 6: Execution Checklist."""
    elements = []
    elements.append(section_title("Section 6: Execution Checklist", styles))
    elements.append(Spacer(1, 4))

    elements.append(branded_table(
        ["#", "Action", "Method", "Status", "When"],
        [
            ["1", "File Amex chargebacks (both cards)", "Phone: 1-800-528-4800", "COMPLETED", "March 14, 2026"],
            ["2", "Upload updated evidence package to Amex", "Amex dispute portal", "PENDING", "When link received"],
            ["3", "File UK Trading Standards complaint", "Online: citizensadvice.org.uk", "FILE NOW", "Today"],
            ["4", "File CMA complaint", "Email: general.enquiries@cma.gov.uk", "FILE NOW", "Today"],
            ["5", "Screenshot tally.so refund form", "Save before they remove it", "DO TODAY", "Today"],
            ["6", "Screenshot propane-business.com/terms", "Sections 7.1, 7.4, 7.5, 11.4, 12.5", "DO TODAY", "Today"],
            ["7", "Save Phil's voicemail recording", "Export from phone to computer", "PENDING", "Today"],
            ["8", "Post Trustpilot review", "trustpilot.com", "DO NOT POST YET", "After chargeback resolved"],
            ["9", "Post Google review", "Google Maps", "DO NOT POST YET", "After chargeback resolved"],
        ],
        col_widths=[0.35 * inch, 1.8 * inch, 1.6 * inch, 1.15 * inch, 1.6 * inch],
    ))

    elements.append(PageBreak())
    return elements


def build_section7(styles):
    """Section 7: Evidence Inventory."""
    elements = []
    elements.append(section_title("Section 7: Evidence Inventory", styles))
    elements.append(Spacer(1, 4))

    elements.append(branded_table(
        ["Evidence", "Location", "Format"],
        [
            ["Jim's sales email (March 2, 15:18)", "Gmail inbox (starred)", "Email"],
            ["Payment receipts (Stripe)", "Gmail inbox (starred)", "Email"],
            ["Jotform signed terms (March 5)", "Gmail inbox", "Email + PDF"],
            ["Refund request #1 (March 6)", "Gmail trash (draft)", "Draft"],
            ["Refund request #2 (March 7)", "Gmail sent folder", "Email"],
            ["Escalation email (March 12)", "Gmail sent folder", "Email"],
            ["Final notice email (March 13)", "Gmail sent folder", "Email"],
            ["Jim's 'nothing to do with me' (March 14)", "Gmail inbox", "Email"],
            ["Response to Jim + re-added admin (March 14)", "Gmail sent folder", "Email"],
            ["Response to Phil's voicemail (March 14)", "Gmail sent folder", "Email"],
            ["Phil's voicemail (March 14, 09:57)", "Phone", "Audio recording"],
            ["Phil's chargeback reversal request (March 16)", "Gmail inbox", "Email"],
            ["Propane Section 7.5 threat email (March 16)", "Gmail inbox", "Email"],
            ["Cardholder rebuttal to threats (March 16)", "Gmail sent folder", "Email"],
            ["Refund form (tally.so/r/mOXkyR)", "Screenshot needed", "Web page"],
            ["Full email PDF exports (41 documents)", "projects/.../PropaneFitnessDispute/emails/", "PDFs"],
            ["Original evidence package", "docs/propane-final-evidence-package.pdf", "PDF"],
            ["Updated evidence package (Mar 16)", "docs/propane-updated-evidence-package.pdf", "PDF"],
            ["Chargeback action plan", "docs/propane-chargeback-action-plan.pdf", "PDF"],
        ],
        col_widths=[2.4 * inch, 2.6 * inch, 1.0 * inch],
    ))

    elements.append(Spacer(1, 30))

    # Footer note
    footer_style = ParagraphStyle(
        "DocFooter", fontName=BrandConfig.BODY_FONT,
        fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
        alignment=TA_CENTER,
    )
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BrandConfig.MID_GRAY,
                                spaceBefore=8, spaceAfter=8))
    elements.append(Paragraph(
        'Updated: March 16, 2026 | Marceau Solutions | This document is for personal use in filing '
        'legitimate consumer complaints and factual reviews. All claims are based on documented evidence.',
        footer_style))

    return elements


def generate():
    """Generate the full PDF."""
    styles = get_brand_styles()

    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=letter,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=1.1 * inch, bottomMargin=0.8 * inch,
    )

    story = []
    story.extend(build_cover(styles))
    story.extend(build_section1(styles))
    story.extend(build_section2(styles))
    story.extend(build_section3(styles))
    story.extend(build_section4(styles))
    story.extend(build_section5(styles))
    story.extend(build_section6(styles))
    story.extend(build_section7(styles))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
