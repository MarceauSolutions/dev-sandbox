#!/usr/bin/env python3
"""
Generate March 20 Propane Fitness evidence update PDF.
Covers: Post-chargeback developments, Circle.so tactic analysis, updated evidence summary.
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

# Styles
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
warning_style = ParagraphStyle(
    "Warning", fontName=BrandConfig.BODY_FONT_BOLD,
    fontSize=10, leading=15, textColor=HexColor("#92400e"),
    leftIndent=12, rightIndent=12, spaceBefore=6, spaceAfter=6,
    backColor=HexColor("#fef3c7"), borderPadding=8,
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
RED = HexColor("#dc2626")
AMBER = HexColor("#d97706")


def section_title_s(text):
    return section_title(text, S)


def bullet_list_s(items):
    return bullet_list(items, S)


def email_box(content_elements):
    inner = content_elements if isinstance(content_elements, list) else [content_elements]
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


def build_pdf():
    output = os.path.join(os.path.dirname(__file__), "..", "docs", "propane-evidence-update-mar20.pdf")
    doc = SimpleDocTemplate(
        output, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    )

    story = []

    # --- COVER PAGE ---
    story.append(Spacer(1, 1.5 * inch))
    story.append(accent_line())
    story.append(Spacer(1, 20))
    story.append(Paragraph("PROPANE FITNESS DISPUTE", cover_title))
    story.append(Paragraph("Evidence Package Update", cover_subtitle))
    story.append(Paragraph("March 20, 2026", cover_detail))
    story.append(Spacer(1, 15))
    story.append(Paragraph("TOTAL DISPUTED", cover_detail))
    story.append(Paragraph("$8,741.76 USD (£6,300 + $229.82 FX fees)", cover_amount))
    story.append(Spacer(1, 15))
    story.append(accent_line())
    story.append(Spacer(1, 30))

    cover_headers = ["Field", "Detail"]
    cover_rows = [
        ["Customer", "William Marceau — wmarceau@marceausolutions.com"],
        ["Vendor", "PropaneFitness / Propane Business (UK)"],
        ["Contacts", "Jim Galvin (sales), Phil Charlton (coach), admin@propanefitness.com"],
        ["Charges", "Receipt #1257-2744 (card 1007) + Receipt #1001-9268 (card 1049)"],
        ["Stripe Account", "acct_182oNdF42QmTryTb"],
        ["First Refund Request", "March 6, 2026 (Day 4 of 14-day window)"],
        ["Chargebacks Filed", "March 14, 2026 (after 8 days / 4 emails with no resolution)"],
        ["This Update Covers", "March 14-20, 2026 — post-chargeback developments"],
    ]
    story.append(branded_table(cover_headers, cover_rows, col_widths=[1.8 * inch, 5.0 * inch]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This document supplements the original evidence package (March 6, 2026) and the "
        "first update (March 16, 2026). It documents Propane's post-chargeback tactics "
        "including intimidation, evidence manufacturing via Circle.so, and blame-shifting.",
        body_style
    ))

    story.append(PageBreak())

    # --- SECTION 1: MARCH 16 EMAIL EXCHANGES ---
    story.append(section_title_s("1. MARCH 16 EMAIL EXCHANGES"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "On March 16, 2026, there were 6 emails exchanged between William and Propane. "
        "These represent the first substantive engagement from Propane after 8 days of silence.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Phil's email
    story.append(Paragraph("Email 1 — Phil (coach@propanefitness.com) — March 16, 10:00", bold_style))
    story.append(email_box([
        Paragraph(
            "\"Can you please confirm whether or not a chargeback has been raised with your "
            "credit card provider regarding your recent payment? Because a chargeback freezes "
            "the transaction, we would be unable to proceed with our standard refund process "
            "until the dispute is resolved. In order to be eligible for a refund review, if you "
            "have raised a chargeback, you will first need to reverse it on your side.\"",
            email_style
        ),
    ]))
    story.append(Paragraph(
        "NOTE: This is Propane's first substantive response — 10 days after the initial refund "
        "request. Their immediate priority was not resolving the dispute, but getting William to "
        "withdraw his chargeback protections.",
        note_style
    ))
    story.append(Spacer(1, 8))

    # William's response
    story.append(Paragraph("Email 2 — William's Response — March 16, 08:08", bold_style))
    story.append(email_box([
        Paragraph(
            "\"I will not be withdrawing the disputes. A full refund of £6,300 to the original "
            "payment methods will close this matter immediately, and I will withdraw the disputes "
            "upon confirmation that the refund has been processed. [...] I requested a refund on "
            "March 6 — Day 4 of your 14-day window. Propane did not provide the refund form "
            "required by Section 7.4, did not give a substantive response within 7 days "
            "(Section 12.5), and did not process the refund by the March 13 deadline.\"",
            email_style
        ),
    ]))
    story.append(Spacer(1, 8))

    # Admin threat email
    story.append(Paragraph("Email 3 — Admin (admin@propanefitness.com) — March 16, 12:28", bold_style))
    story.append(Paragraph("KEY: This email contains both the refund form AND threats.", warning_style))
    story.append(email_box([
        Paragraph(
            "\"Here is the refund form for you to complete: https://tally.so/r/mOXkyR\"",
            email_bold
        ),
        Paragraph(
            "\"However, since you have now initiated chargebacks, the funds are currently frozen "
            "by the bank. [...] Under Section 7.5 of the terms you accepted at checkout, any "
            "attempt to bypass our refund policy constitutes a breach of contract. This results "
            "in the immediate rejection of your refund request and gives us the right to "
            "counterclaim for any outstanding amounts owed to us, plus legal costs.\"",
            email_style
        ),
        Paragraph(
            "\"Option 2 – Continue with the chargebacks: [...] we would need to initiate "
            "recovery of the full balance of £6,300 and related costs through a collections "
            "agency. This would include collection fees, court fees, and legal expenses on a "
            "full indemnity basis.\"",
            email_style
        ),
    ]))
    story.append(Paragraph(
        "NOTE: Propane sent the refund form 10 days and 8 formal emails after the first request, "
        "but immediately conditioned it on withdrawing chargeback protections — with no "
        "commitment to actually issue a refund, only to \"assess eligibility.\"",
        note_style
    ))
    story.append(Spacer(1, 8))

    # William's rebuttal
    story.append(Paragraph("Email 4 — William's Rebuttal — March 16, 08:35", bold_style))
    story.append(Paragraph("Key legal arguments made:", bold_style))
    story.extend(bullet_list_s([
        "Section 7.5 cannot override statutory rights — Propane's own Section 12.5 (Exceptions) acknowledges the right to seek remedies through external channels, including card issuer disputes",
        "Propane breached the contract first: failed to deliver 1-on-1 coaching as written, failed to provide refund form within reasonable time, failed to respond within 7 days (Section 12.5), failed to honour 14-day refund policy (Section 7.1)",
        "\"Assess eligibility\" is not a refund commitment — the form requires withdrawing protections with zero guarantee",
        "Collections threat is retaliatory — a party in material breach cannot invoke contract protections against the wronged party",
    ]))
    story.append(Spacer(1, 8))

    # Admin second response
    story.append(Paragraph("Email 5 — Admin Response — March 16, 14:50", bold_style))
    story.append(email_box([
        Paragraph(
            "\"The delays you mention had occurred because you directed your correspondence to "
            "a sales representative, rather than your account manager, Phil.\"",
            email_style
        ),
    ]))
    story.append(Paragraph(
        "NOTE: This is blame-shifting. admin@propanefitness.com was CC'd on every email. "
        "Phil himself admitted in his March 14 voicemail he was \"completely unaware\" of the dispute.",
        note_style
    ))
    story.append(Spacer(1, 8))

    # William's final
    story.append(Paragraph("Email 6 — William's Final Response — March 16, 11:15", bold_style))
    story.append(Paragraph("Demolished the \"wrong person\" argument:", bold_style))
    story.extend(bullet_list_s([
        "Jim Galvin conducted the sale, quoted pricing, sent payment links, collected £6,300 — contacting him was reasonable and standard",
        "admin@propanefitness.com was CC'd on every formal email (March 6, 7, 12, 13) — this IS the \"official admin email\" per Section 7.2",
        "Phil assigned ~March 4-5; first refund request sent March 6 — William had known Phil for ONE day",
        "Jim deliberately removed admin@propanefitness.com from CC on his March 14 reply — undermining Propane's own internal routing",
    ]))

    story.append(PageBreak())

    # --- SECTION 2: CIRCLE.SO EVIDENCE MANUFACTURING ---
    story.append(section_title_s("2. CIRCLE.SO EVIDENCE MANUFACTURING"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "CRITICAL: After chargebacks were filed on March 14, Propane began manufacturing "
        "evidence of ongoing \"service delivery\" through automated Circle.so messages and "
        "a new CSM assignment. This section documents the tactic.",
        warning_style
    ))
    story.append(Spacer(1, 10))

    # Bot messages table
    story.append(Paragraph("Automated \"Support Genie\" Bot Messages", bold_style))
    story.append(Paragraph(
        "These are generic automated drip sequence messages — not personalised coaching. "
        "They are sent from a bot account called \"Propane Support Genie\" via Circle.so "
        "notification emails. William has not responded to any of them.",
        body_style
    ))
    story.append(Spacer(1, 6))

    bot_headers = ["Date", "Subject", "Content Preview"]
    bot_rows = [
        ["Mar 3", "Support Genie message", "Initial onboarding bot message"],
        ["Mar 4", "Support Genie message", "Onboarding drip"],
        ["Mar 6", "Support Genie message", "Onboarding drip"],
        ["Mar 9", "Support Genie message", "Onboarding drip"],
        ["Mar 15", "Support Genie message", "\"Your pipeline: getting your offer in front of the right people\""],
        ["Mar 17", "Support Genie message", "\"Hopefully you went through the 'start here' section?\""],
        ["Mar 19", "Support Genie message", "\"Quick checklist to help you create videos, ads and landing pages\""],
    ]
    story.append(branded_table(bot_headers, bot_rows, col_widths=[0.8 * inch, 2.0 * inch, 4.0 * inch]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The last 3 messages (highlighted) were sent AFTER chargebacks were filed on March 14. "
        "These automated messages continue to arrive despite the active dispute, creating a "
        "false impression of ongoing service delivery.",
        note_style
    ))
    story.append(Spacer(1, 15))

    # CSM Assignment
    story.append(Paragraph("NEW: Customer Success Manager Assigned — March 19", bold_style))
    story.append(Paragraph(
        "Five days after chargebacks were filed, Propane assigned Jonny Simpson as William's "
        "\"CSM\" and started a group coaching thread on Circle.so:",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(email_box([
        Paragraph(
            "From: Jonny Simpson (via Circle.so) — March 19, 2026 at 18:46<br/>"
            "Subject: \"Jonny Simpson sent you a message on Propane\"",
            email_bold
        ),
        Paragraph(
            "\"Hey William, welcome to your private coaching thread. "
            "I'll be working closely with you as your CSM\"",
            email_style
        ),
    ]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "THIS IS THE MOST SIGNIFICANT POST-CHARGEBACK DEVELOPMENT.",
        warning_style
    ))
    story.extend(bullet_list_s([
        "William never requested a CSM or any further services",
        "William explicitly stated (March 14 email) that all communication must be via email — not Circle.so",
        "This assignment occurred 5 days after chargebacks were filed",
        "The timing strongly suggests this is designed to create documentation of \"service delivery\" for the chargeback dispute",
        "William has not responded to or engaged with this thread",
    ]))
    story.append(Spacer(1, 15))

    # Marketing emails
    story.append(Paragraph("Marketing Emails Still Flowing Post-Dispute", bold_style))
    mkt_headers = ["Date", "From", "Subject"]
    mkt_rows = [
        ["Mar 16", "Yusef (admin@propanefitness.com)", "Taking notes"],
        ["Mar 16", "Jonny Watson (admin@propanefitness.com)", "Want to get roasted this month? (workshop Mar 26)"],
        ["Mar 19", "Propane (Circle.so)", "This week on Propane: March 12-19"],
    ]
    story.append(branded_table(mkt_headers, mkt_rows, col_widths=[0.8 * inch, 2.5 * inch, 3.5 * inch]))
    story.append(Paragraph(
        "Propane continues sending marketing and onboarding content despite the active dispute. "
        "Each email contributes to the manufactured appearance of an active membership.",
        note_style
    ))

    story.append(PageBreak())

    # --- SECTION 3: PROPANE'S THREE-PART STRATEGY ---
    story.append(section_title_s("3. PROPANE'S POST-CHARGEBACK STRATEGY"))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Strategy 1: Intimidation", h3))
    story.extend(bullet_list_s([
        "Threatening collections agency for full £6,300 + legal costs + court fees",
        "Citing Section 7.5 breach of contract for filing chargebacks",
        "Demanding withdrawal of chargeback protections before any refund review",
        "Framing the refund form as conditional on dropping disputes — with only a promise to \"assess eligibility\"",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Strategy 2: Evidence Manufacturing", h3))
    story.extend(bullet_list_s([
        "Keeping automated Circle.so bot messages active (3 sent after chargeback filing)",
        "Assigning a new CSM (Jonny Simpson) on March 19 — 5 days after chargebacks filed",
        "Continuing marketing emails and workshop invitations",
        "Goal: present to Amex a paper trail showing \"the customer is still receiving services\"",
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Strategy 3: Blame-Shifting", h3))
    story.extend(bullet_list_s([
        "Claiming William emailed \"the wrong person\" (despite admin@ being CC'd on every email)",
        "Blaming the 8-day delay on William rather than their own internal failure",
        "Phil claimed he was \"completely unaware\" — but admin@ was on every email",
        "Jim removed admin@ from CC on March 14 — actively undermining Propane's own routing",
    ]))

    story.append(Spacer(1, 15))

    # --- SECTION 4: COUNTERARGUMENTS FOR AMEX ---
    story.append(section_title_s("4. COUNTERARGUMENTS FOR AMEX CHARGEBACK REVIEW"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "If Propane submits evidence to Amex claiming service was delivered, "
        "the following counterpoints apply:",
        body_style
    ))
    story.append(Spacer(1, 8))

    counter_headers = ["Propane's Likely Claim", "William's Counter-Evidence"]
    counter_rows = [
        [
            "\"Customer had access to the platform\"",
            "William has not logged into Circle.so or attended any session since filing the refund request on March 6"
        ],
        [
            "\"We assigned a dedicated coach\"",
            "Phil was assigned ~March 4-5. William requested a refund on March 6 (Day 4). Phil admitted on March 14 voicemail he was \"completely unaware\" of the dispute for 8 days"
        ],
        [
            "\"We assigned a CSM\"",
            "Jonny Simpson was assigned March 19 — 5 days AFTER chargebacks filed. This is evidence manufacturing, not service delivery"
        ],
        [
            "\"Customer received automated coaching messages\"",
            "These are generic bot drip sequences from \"Propane Support Genie\" — not personalised coaching. William did not request, read, or respond to any of them"
        ],
        [
            "\"Customer breached contract by filing chargebacks\"",
            "Propane's own Section 12.5 acknowledges the right to external remedies. Propane breached first: failed 1-on-1 coaching, withheld refund form for 10 days, failed to respond within 7 days"
        ],
        [
            "\"Customer should have contacted Phil, not Jim\"",
            "admin@propanefitness.com was CC'd on all 4 formal emails. Section 7.2 says use \"official admin email.\" Jim removed admin@ from CC on March 14"
        ],
        [
            "\"We offered the refund form\"",
            "The form was sent March 16 — 10 days after first request — and conditioned on withdrawing chargeback protections with no guarantee of refund"
        ],
    ]
    story.append(branded_table(counter_headers, counter_rows, col_widths=[2.8 * inch, 4.0 * inch]))

    story.append(PageBreak())

    # --- SECTION 5: COMPLETE EVIDENCE INVENTORY ---
    story.append(section_title_s("5. COMPLETE EVIDENCE INVENTORY"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "50 emails exported from Gmail via API. Full archive in: "
        "PropaneFitnessDispute/emails/",
        body_style
    ))
    story.append(Spacer(1, 8))

    facts_headers = ["#", "Fact", "Evidence"]
    facts_rows = [
        ["1", "Pricing misrepresented on call", "Jim's email (15:18, Mar 2) contradicts verbal quotes"],
        ["2", "Payment rushed in 22 minutes", "Email timestamps: 15:18 to 15:40"],
        ["3", "Terms signed 3 days after payment", "JotForm invoice Mar 5; payment collected Mar 2"],
        ["4", "Immediate access not delivered", "Jim's email promised it; took 1 day"],
        ["5", "USD equivalent never disclosed", "No email mentions USD or FX fees"],
        ["6", "Foreign transaction fees: $229.82", "Amex statements confirm"],
        ["7", "8 emails over 8 days before chargeback", "Mar 6, 7, 12, 13 to jim@ and admin@"],
        ["8", "Refund form withheld 10 days", "Requested Mar 12; form sent Mar 16"],
        ["9", "Phil \"unaware\" for 8 days", "His voicemail, Mar 14"],
        ["10", "Jim removed admin@ from CC", "Mar 14 reply email headers"],
        ["11", "Circle bot msgs active post-dispute", "Mar 15, 17, 19 — automated, not coaching"],
        ["12", "New CSM assigned 5 days after chargeback", "Jonny Simpson, Mar 19"],
        ["13", "Section 7.5 does not override statutory rights", "Propane's own Section 12.5"],
        ["14", "Propane breached contract first", "1-on-1 coaching, refund form, 7-day response, 14-day policy"],
    ]
    story.append(branded_table(facts_headers, facts_rows, col_widths=[0.3 * inch, 2.8 * inch, 3.7 * inch]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=BrandConfig.MID_GRAY))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Document prepared March 20, 2026. All email timestamps verified from "
        "wmarceau@marceausolutions.com inbox via Gmail API. "
        "50 emails exported and archived as individual PDFs.",
        footer_style
    ))
    story.append(Paragraph(
        "Previous evidence packages: propane-dispute-evidence-package.pdf (Mar 6), "
        "propane-updated-evidence-package.pdf (Mar 16)",
        footer_style
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"PDF generated: {output}")
    return output


if __name__ == "__main__":
    path = build_pdf()
    os.system(f'open "{path}"')
