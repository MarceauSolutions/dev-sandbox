#!/usr/bin/env python3
"""
Propane Fitness — AmEx Dispute Resubmission (April 2026)
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

NEW EVIDENCE resubmission following AmEx rebill on April 7, 2026.
Addresses specific claims in Propane's Chargeback Dispute Response.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
GREEN_BG = HexColor("#f0fff0")
RED_BG = HexColor("#fff0f0")
ALERT_BG = HexColor("#fff3f3")

OUTPUT = os.path.join(os.path.dirname(__file__), "propane-amex-resubmission-april2026.pdf")


def get_styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=16, leading=22,
                                textColor=NAVY, spaceAfter=4, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=10, leading=14,
                                   textColor=CHARCOAL, spaceAfter=12, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=13, leading=18,
                             textColor=NAVY, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11, leading=15,
                             textColor=DARK_BLUE, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                               textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5,
                                    leading=13.5, textColor=CHARCOAL, spaceAfter=5),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=9.5,
                                leading=13.5, textColor=HexColor("#555555"),
                                leftIndent=15, rightIndent=15, spaceAfter=6),
        "alert": ParagraphStyle("Alert", fontName="Helvetica-Bold", fontSize=10,
                                leading=14, textColor=RED, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5,
                                 leading=13.5, textColor=CHARCOAL, leftIndent=20,
                                 spaceAfter=3, bulletIndent=8),
        "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=7.5, leading=10,
                                 textColor=HexColor("#888888"), alignment=TA_CENTER),
    }


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch
    )
    s = get_styles()
    elements = []

    # ===== HEADER =====
    elements.append(Paragraph("CARDHOLDER RESUBMISSION — NEW EVIDENCE", s["title"]))
    elements.append(Paragraph(
        "Response to AmEx Rebill of April 7, 2026 | Propane Fitness Ltd Chargeback Dispute", s["subtitle"]
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=10))

    # Case info table
    case_data = [
        ["Cardholder:", "William J. Marceau"],
        ["Email:", "wmarceau@marceausolutions.com"],
        ["Cases:", "D-93497818 (Card 1007) / D-93497819 (Card 1049)"],
        ["Reason Code:", "4553 — Product Unacceptable"],
        ["Merchant:", "Propane Fitness Ltd (Co. 07779096), 1 Holly House, Mill St, Uppermill, Oldham OL3 6LZ"],
        ["Total Disputed:", "£6,300 GBP (~$8,741.76 USD including foreign transaction fees)"],
        ["Date:", "April 7, 2026"],
    ]
    t = Table(case_data, colWidths=[1.4 * inch, 5.1 * inch])
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
    elements.append(t)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"), spaceAfter=8))

    # ===== PURPOSE =====
    elements.append(Paragraph("PURPOSE OF THIS RESUBMISSION", s["h1"]))
    elements.append(Paragraph(
        "On April 7, 2026, American Express rebilled charges on both cards, citing the merchant's claim that "
        "\"the product was delivered as described, the cardholder accessed all services, and a clear refund "
        "process was communicated and declined.\" This resubmission presents <b>new evidence</b> that directly "
        "contradicts each of these three claims — including evidence from the merchant's own exhibits, "
        "their own public sales pages, and a retroactively applied contract addendum that did not exist "
        "at the time of purchase.",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 1: MERCHANT LIED ABOUT SERVICE DELIVERY =====
    elements.append(Paragraph(
        "1. THE MERCHANT'S CLAIM THAT I \"ACCESSED ALL SERVICES\" IS FALSE", s["h1"]
    ))
    elements.append(Paragraph(
        "The merchant told American Express that I received \"all programme deliverables as described\" "
        "and \"accessed all services.\" My own messages — sent on the merchant's own platform and submitted "
        "by the merchant as their Exhibit E — prove this is false.",
        s["body"]
    ))

    elements.append(Paragraph("What I actually said on the merchant's platform:", s["body_bold"]))

    quotes = [
        ("March 4, 12:20 PM", "Also How do I schedule live cal with you as that is also part of the services"),
        ("March 4, 12:22 PM", "Additionally when im logged into circle it does not show me any available "
         "live calls or the ability to access the content? Can you please help me rectify these issues"),
        ("March 4, 12:26 PM", "so I dont seem to have any access to any of the features in circle and "
         "all the links in notion bring me back to the email marketing page"),
        ("March 4, 12:32 PM", "it really seems like I just got scammed"),
    ]
    for date, quote in quotes:
        elements.append(Paragraph(f"<b>{date}:</b> <i>\"{quote}\"</i>", s["quote"]))

    elements.append(Paragraph(
        "The merchant's own coach, Phil Charlton, confirmed in the same thread:", s["body_bold"]
    ))
    elements.append(Paragraph(
        "<i>\"You just need to sign the Ts and C's, you should have been sent this upon point of sale.\"</i> "
        "(March 4) — admitting the process was broken.",
        s["quote"]
    ))
    elements.append(Paragraph(
        "<i>\"Originally you put the wrong email address in which is what has caused the issue.\"</i> "
        "(March 5) — blaming me for an access failure that took 3 days to resolve.",
        s["quote"]
    ))

    elements.append(Paragraph(
        "I never attended a single coaching clinic. I never accessed course modules. I never had a "
        "scheduled 1-on-1 Zoom coaching session. The only interaction was one onboarding Zoom call on "
        "March 5 — where the coach confirmed that consistent weekly 1-on-1 calls are no longer offered "
        "and the program relies on group coaching clinics instead.",
        s["alert"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 2: WHAT WAS SOLD VS WHAT WAS DELIVERED =====
    elements.append(Paragraph(
        "2. THE PRODUCT WAS NOT AS DESCRIBED — PROVEN BY THE MERCHANT'S OWN PAGES", s["h1"]
    ))
    elements.append(Paragraph(
        "The merchant claims I received \"exactly what was described.\" However, the merchant's own "
        "sales email, website, terms, and chargeback response each describe a DIFFERENT service:",
        s["body"]
    ))

    # Comparison table
    compare_data = [
        [Paragraph("<b>Source</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8.5,
                                                    leading=11, textColor=WHITE)),
         Paragraph("<b>What It Says</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8.5,
                                                          leading=11, textColor=WHITE))],

        [Paragraph("Jim Galvin's sales email<br/>(March 2, 15:18 — before payment)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("\"Dedicated 1-2-1 coach for 12 weeks. Private thread for messages, voice notes, "
                   "feedback and <b>calls to customise the process to your business</b>.\"",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],

        [Paragraph("Merchant's Terms of Use<br/>(propane-business.com/terms)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("\"One-on-One Coaching Support: a channel [that] facilitates the sharing of "
                   "<b>voice notes, document reviews, messages</b>.\" — A messaging thread, not scheduled calls.",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],

        [Paragraph("Merchant's Sales Page<br/>(propanefitness.com/onlinecoach)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("\"12 weeks of live coaching, help &amp; on-demand support.\" "
                   "<b>No mention of \"dedicated 1-2-1 coach\" anywhere on the page.</b> "
                   "Testimonials reference \"group coaching programme.\"",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],

        [Paragraph("Merchant's Clickfunnels Page<br/>(propanefitness.clickfunnels.com)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Describes transitioning from \"offline 1-on-1 training to <b>online group-based coaching</b>\" "
                   "using \"semi-automated\" systems.",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],

        [Paragraph("Merchant's Chargeback Response<br/>(Attachment 4, submitted to AmEx)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Claims I received \"1-2-1 Coaching: Dedicated coach assigned within 2 days. "
                   "<b>Individual Zoom calls</b>, messaging, and personalised support.\"",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],

        [Paragraph("My actual experience<br/>(Merchant's own Exhibit E)",
                   ParagraphStyle("Tc", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("\"How do I schedule live cal with you\" / \"it does not show me any available live calls\" "
                   "— <b>No scheduling system exists. No individual Zoom calls occurred.</b>",
                   ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL))],
    ]
    ct = Table(compare_data, colWidths=[2.0 * inch, 4.5 * inch])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, 1), GREEN_BG),
        ("BACKGROUND", (0, 2), (-1, 2), LIGHT_GRAY),
        ("BACKGROUND", (0, 3), (-1, 3), LIGHT_GRAY),
        ("BACKGROUND", (0, 4), (-1, 4), LIGHT_GRAY),
        ("BACKGROUND", (0, 5), (-1, 5), RED_BG),
        ("BACKGROUND", (0, 6), (-1, 6), RED_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(ct)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "The sales email promises dedicated 1-on-1 coaching calls. The terms describe a messaging thread. "
        "The sales pages describe group coaching. The chargeback response claims individual Zoom calls "
        "occurred. My own messages prove they did not. Every layer contradicts the next.",
        s["alert"]
    ))

    # ===== SECTION 3: MERCHANT DESCRIPTION MISMATCH =====
    elements.append(Paragraph(
        "3. MERCHANT REGISTERED AS \"NUTRITIONAL COACHING\" WITH PAYMENT PROCESSOR", s["h1"]
    ))
    elements.append(Paragraph(
        "The merchant's own Order Details (page 1 of their Attachment 4, submitted to AmEx) lists their "
        "Business Description as <b>\"Nutritional coaching.\"</b> The service sold to me was a "
        "<b>business mentorship program</b> — not nutritional coaching. This is a material misrepresentation "
        "to the payment processor about the nature of their business.",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 4: RETROACTIVE CONTRACT =====
    elements.append(Paragraph(
        "4. MERCHANT SUBMITTED RETROACTIVELY APPLIED CONTRACT TERMS AS EVIDENCE", s["h1"]
    ))
    elements.append(Paragraph(
        "The merchant's Attachment 3 includes a <b>\"Sales Kick Addendum\"</b> with an effective date of "
        "<b>March 13, 2026</b> — eleven days after my purchase (March 2) and seven days after my refund "
        "request (March 6). This addendum introduces:",
        s["body"]
    ))
    elements.append(Paragraph("• Binding arbitration via CEDR", s["bullet"]))
    elements.append(Paragraph("• Jury trial waiver", s["bullet"]))
    elements.append(Paragraph("• Class action waiver", s["bullet"]))
    elements.append(Paragraph("• New data sharing provisions with a subcontractor called \"Sales Kick\"", s["bullet"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "I never agreed to this addendum. It did not exist when I purchased the program (March 2) or when "
        "I signed the original Terms of Use (March 5). Retroactively applying contract terms — including "
        "an arbitration clause and jury trial waiver — to a transaction already in dispute is evidence of "
        "bad faith, not evidence of a valid agreement.",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 5: REFUND PROCESS WAS A TRAP =====
    elements.append(Paragraph(
        "5. THE \"CLEAR REFUND PROCESS\" WAS WITHHELD, THEN OFFERED AS A TRAP", s["h1"]
    ))

    elements.append(Paragraph("The actual timeline:", s["body_bold"]))

    timeline_data = [
        ["Date", "Event"],
        ["March 6", "I requested a full refund (Day 4 of 14-day window)"],
        ["March 7", "Jim Galvin replied — addressed ONLY foreign transaction fees, ignored all grounds"],
        ["March 7", "I restated 7 grounds and set a March 13 deadline"],
        ["March 12", "Escalation email sent to jim@ and admin@ — 5 cited terms breaches"],
        ["March 13", "Deadline expired — no substantive response received"],
        ["March 14", "Chargebacks filed. Phil admits he was \"completely unaware\" of the dispute"],
        ["March 14", "Refund form finally provided — 8 DAYS after first request"],
        ["March 16", "Propane demands I withdraw chargebacks FIRST — threatens collections + legal costs"],
    ]
    tt = Table(timeline_data, colWidths=[1.0 * inch, 5.5 * inch])
    tt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(tt)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "The merchant claims I \"refused to follow the agreed refund process.\" In reality:",
        s["body_bold"]
    ))
    elements.append(Paragraph(
        "• I requested a refund on March 6 — Day 4. The merchant did not provide the refund form until "
        "March 14 (8 days late), despite their own Section 7.4 requiring it \"on request.\"",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• When the form was finally provided, it required me to <b>withdraw my chargeback protections first</b> "
        "— with no guarantee of refund, only a promise to \"assess eligibility\" over up to 90 days.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• The merchant simultaneously threatened breach of contract (Section 7.5), counterclaim for the "
        "full £6,300 plus legal costs, and referral to a collections agency.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "No reasonable person would surrender their only financial protection on an $8,700 purchase "
        "based on a non-binding promise to \"assess eligibility.\"",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 6: CORPORATE DETAILS =====
    elements.append(Paragraph(
        "6. MERCHANT CORPORATE DETAILS (UK COMPANIES HOUSE)", s["h1"]
    ))
    corp_data = [
        ["Legal Name:", "Propane Fitness Ltd"],
        ["Company Number:", "07779096 (incorporated 19 September 2011)"],
        ["Current Address:", "1 Holly House, Mill Street, Uppermill, Oldham, OL3 6LZ"],
        ["Contract Address:", "69 Church Way, North Shields, NE29 0AE (former registered address)"],
        ["Directors:", "Jonathan James Watson (Jonny Watson) and Dr. Yusef El-Sobky"],
        ["VAT:", "266679253"],
        ["Cash on Hand:", "£577,579 (per most recent filed accounts)"],
    ]
    corp_t = Table(corp_data, colWidths=[1.6 * inch, 4.9 * inch])
    corp_t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(corp_t)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Note: Jim Galvin and Phil Charlton — the salesperson who collected payment and the coach who "
        "admitted the process was broken — are employees, not directors. The legally responsible directors "
        "are Jonathan Watson and Yusef El-Sobky. The merchant has £577,579 in cash; they can afford to "
        "issue this refund.",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== SECTION 7: REGULATORY COMPLAINTS FILED =====
    elements.append(Paragraph(
        "7. REGULATORY COMPLAINTS BEING FILED", s["h1"]
    ))
    elements.append(Paragraph(
        "In parallel with this resubmission, formal consumer protection complaints are being filed with:",
        s["body"]
    ))
    elements.append(Paragraph(
        "• <b>UK Trading Standards</b> (via Citizens Advice) — misrepresentation under Consumer Protection "
        "from Unfair Trading Regulations 2008 (Regulations 5 and 7)",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• <b>Competition and Markets Authority (CMA)</b> — unfair commercial practices, "
        "unfair contract terms (Section 7.5 chargeback intimidation clause)",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• <b>Action Fraud</b> — misrepresentation to induce payment",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "The merchant's contract terms attempt to waive the consumer's statutory right to file a chargeback "
        "(Section 7.5) by treating it as \"breach of contract\" triggering refund rejection and debt collection. "
        "Under the UK Consumer Rights Act 2015, Part 2, terms that restrict a consumer's right to legal "
        "remedies or create a significant imbalance in the parties' rights are unfair and unenforceable.",
        s["body"]
    ))
    elements.append(Spacer(1, 6))

    # ===== CONCLUSION =====
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=8))
    elements.append(Paragraph("REQUEST", s["h1"]))
    elements.append(Paragraph(
        "I respectfully request that American Express review the following new evidence and reverse "
        "the rebill on both cases:",
        s["body"]
    ))
    elements.append(Paragraph(
        "1. The merchant's own Exhibit E proves I had NO access to live calls, course content, or platform "
        "features from March 2-5 — contradicting their claim that I \"accessed all services.\"",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "2. The merchant's own sales pages describe a \"group coaching programme\" while their sales email "
        "and chargeback response claim \"dedicated 1-2-1 coaching\" — the product was not as described.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "3. The merchant retroactively applied a \"Sales Kick Addendum\" (dated March 13) to a transaction "
        "made on March 2 — introducing arbitration and jury trial waiver terms that did not exist at purchase.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "4. The merchant withheld the refund form for 8 days (March 6-14), then demanded I surrender "
        "chargeback protections first with no guarantee of refund.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "5. The merchant registered with the payment processor as \"Nutritional coaching\" when the service "
        "sold is a business mentorship program.",
        s["bullet"]
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "I request that both chargebacks totaling £6,300 (approximately $8,741.76 USD including "
        "foreign transaction fees) be upheld and the credits restored to my account.",
        s["alert"]
    ))
    elements.append(Spacer(1, 12))

    # Signature
    elements.append(Paragraph("Respectfully submitted,", s["body"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>William J. Marceau</b>", s["body"]))
    elements.append(Paragraph("wmarceau@marceausolutions.com", s["body"]))
    elements.append(Paragraph("Naples, Florida, US", s["body"]))
    elements.append(Paragraph("April 7, 2026", s["body"]))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"), spaceAfter=4))
    elements.append(Paragraph(
        "Attachments: (1) Circle.so message screenshots proving non-access [MessageThread 1-6]; "
        "(2) Screenshots of merchant's live sales pages showing \"group coaching\"; "
        "(3) Jim Galvin's sales email promising \"Dedicated 1-2-1 coach\"; "
        "(4) Merchant's chargeback response Attachment 4 with annotated Exhibit E; "
        "(5) Companies House registration confirming merchant details.",
        s["footer"]
    ))

    doc.build(elements)
    print(f"Generated: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    build()
