#!/usr/bin/env python3
"""
Propane Fitness — FINAL AmEx Dispute Resubmission Package
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

Single merged PDF: Cover letter + annotated evidence exhibits.
Designed for a non-lawyer dispute reviewer to read in under 10 minutes
and reach only one conclusion: the chargebacks should be upheld.

Structure:
  Pages 1-3: Cardholder statement (concise, numbered findings)
  Page 4:    Side-by-side comparison table (the centerpiece)
  Pages 5-6: Exhibit A — Cardholder's own messages proving non-access (annotated)
  Page 7:    Exhibit B — Merchant's sales page screenshot (annotated)
  Page 8:    Exhibit C — Companies House registration (annotated)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image
)

# --- Colors ---
NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED = HexColor("#c0392b")
GOLD = HexColor("#C9963C")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
WHITE = colors.white
GREEN_BG = HexColor("#e8f5e9")
RED_BG = HexColor("#ffebee")
YELLOW_BG = HexColor("#fff8e1")
BLUE_BG = HexColor("#e3f2fd")

# --- Paths ---
EVIDENCE_DIR = Path(__file__).parent.parent / "projects" / "marceau-solutions" / "labs" / "PropaneFitnessDispute"
WEB_EVIDENCE_DIR = EVIDENCE_DIR / "web-evidence"
OUTPUT = os.path.join(os.path.dirname(__file__), "propane-final-resubmission-package.pdf")


def get_styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=15, leading=20,
                                textColor=NAVY, spaceAfter=2, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=9.5, leading=13,
                                   textColor=CHARCOAL, spaceAfter=10, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12, leading=16,
                             textColor=NAVY, spaceBefore=12, spaceAfter=5),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                             textColor=DARK_BLUE, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                               textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5,
                                    leading=13.5, textColor=CHARCOAL, spaceAfter=5),
        "finding": ParagraphStyle("Finding", fontName="Helvetica-Bold", fontSize=9.5,
                                  leading=13.5, textColor=RED, spaceAfter=5),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=9.5,
                                leading=13.5, textColor=HexColor("#444444"),
                                leftIndent=18, rightIndent=18, spaceAfter=5,
                                borderPadding=6, backColor=HexColor("#f8f8f8")),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5,
                                 leading=13.5, textColor=CHARCOAL, leftIndent=22,
                                 spaceAfter=3, bulletIndent=10),
        "exhibit_title": ParagraphStyle("ExhibitTitle", fontName="Helvetica-Bold", fontSize=13,
                                        leading=18, textColor=WHITE, alignment=TA_CENTER),
        "exhibit_desc": ParagraphStyle("ExhibitDesc", fontName="Helvetica", fontSize=9,
                                       leading=13, textColor=CHARCOAL, alignment=TA_CENTER,
                                       spaceAfter=8),
        "annotation": ParagraphStyle("Annotation", fontName="Helvetica-Bold", fontSize=9,
                                     leading=12, textColor=RED, spaceAfter=4,
                                     leftIndent=10, borderPadding=4, backColor=HexColor("#fff5f5")),
        "page_footer": ParagraphStyle("PageFooter", fontName="Helvetica", fontSize=7,
                                      leading=9, textColor=HexColor("#999999"), alignment=TA_CENTER),
        "sig": ParagraphStyle("Sig", fontName="Helvetica", fontSize=9, leading=12,
                              textColor=CHARCOAL, spaceAfter=2),
    }


def exhibit_header(title, s):
    """Dark navy banner for exhibit pages."""
    banner_data = [[Paragraph(title, s["exhibit_title"])]]
    banner = Table(banner_data, colWidths=[6.5 * inch])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return banner


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.6 * inch
    )
    s = get_styles()
    elements = []

    # =====================================================================
    # PAGE 1: HEADER + CASE INFO + INTRODUCTION
    # =====================================================================
    elements.append(Paragraph("CARDHOLDER STATEMENT — NEW EVIDENCE", s["title"]))
    elements.append(Paragraph(
        "Resubmission Following Rebill of April 7, 2026", s["subtitle"]
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))

    # Case info — compact
    case_data = [
        ["Cardholder:", "William J. Marceau | wmarceau@marceausolutions.com | Naples, FL"],
        ["Cases:", "D-93497818 (Card 1007) and D-93497819 (Card 1049)"],
        ["Merchant:", "Propane Fitness Ltd (UK Co. 07779096) | propanefitness.com"],
        ["Amount:", "£6,300 GBP ($8,741.76 USD incl. foreign transaction fees)"],
        ["Reason Code:", "4553 — Product Unacceptable (Not as Described)"],
    ]
    ct = Table(case_data, colWidths=[1.1 * inch, 5.4 * inch])
    ct.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(ct)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=8))

    # Introduction
    elements.append(Paragraph(
        "American Express rebilled both charges on April 7, 2026, citing the merchant's claim that "
        "<b>(1) the product was delivered as described, (2) I accessed all services, and "
        "(3) I declined their refund process.</b> Each claim is false. The evidence below — including "
        "the merchant's own exhibits submitted to American Express — proves it.",
        s["body"]
    ))
    elements.append(Spacer(1, 4))

    # =====================================================================
    # FINDING 1: I DID NOT "ACCESS ALL SERVICES"
    # =====================================================================
    elements.append(Paragraph("FINDING 1: I DID NOT \"ACCESS ALL SERVICES\"", s["h1"]))
    elements.append(Paragraph(
        "The merchant told American Express I accessed all programme deliverables. The merchant's own "
        "platform messages — which the merchant submitted as their <b>Exhibit E</b> — show otherwise.",
        s["body"]
    ))
    elements.append(Paragraph(
        "On March 4, 2026 — two days after paying £6,300 — I sent these messages to my assigned coach "
        "on the merchant's Circle.so platform:",
        s["body"]
    ))

    msg_data = [
        [Paragraph("<b>Time</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)),
         Paragraph("<b>My Message</b>", ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE))],
        [Paragraph("Mar 4<br/>12:20 PM", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("<i>\"Also How do I schedule live cal with you as that is also part of the services\"</i>",
                   ParagraphStyle("Tc", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("Mar 4<br/>12:22 PM", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("<i>\"Additionally when im logged into circle it does not show me any available live calls "
                   "or the ability to access the content\"</i>",
                   ParagraphStyle("Tc", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("Mar 4<br/>12:26 PM", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("<i>\"so I dont seem to have any access to any of the features in circle and all the links "
                   "in notion bring me back to the email marketing page\"</i>",
                   ParagraphStyle("Tc", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=CHARCOAL))],
        [Paragraph("Mar 4<br/>12:32 PM", ParagraphStyle("Tc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("<i>\"it really seems like I just got scammed\"</i>",
                   ParagraphStyle("Tc", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=RED))],
    ]
    mt = Table(msg_data, colWidths=[0.8 * inch, 5.7 * inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#fafafa")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(mt)
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("The merchant's own coach responded:", s["body_bold"]))
    elements.append(Paragraph(
        "<i>\"You just need to sign the Ts and C's, you should have been sent this upon point of sale.\"</i> "
        "— Phil Charlton, March 4 (admitting the process was broken)",
        s["quote"]
    ))
    elements.append(Paragraph(
        "<i>\"Originally you put the wrong email address in which is what has caused the issue.\"</i> "
        "— Phil Charlton, March 5 (access not resolved until 3 days after payment)",
        s["quote"]
    ))

    elements.append(Paragraph(
        "I never attended a coaching clinic. I never accessed course modules. I never had a scheduled "
        "1-on-1 Zoom session — the core service sold to me. The full message thread is attached as Exhibit A.",
        s["finding"]
    ))
    elements.append(Spacer(1, 4))

    # =====================================================================
    # FINDING 2: THE PRODUCT WAS NOT AS DESCRIBED
    # =====================================================================
    elements.append(Paragraph("FINDING 2: THE PRODUCT WAS NOT AS DESCRIBED", s["h1"]))
    elements.append(Paragraph(
        "The seller's written email — sent minutes before collecting payment — promised one service. "
        "The merchant's own website, terms, and actual delivery describe a fundamentally different service.",
        s["body"]
    ))

    # The comparison table — this is the centerpiece
    compare_header = ParagraphStyle("CompH", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=WHITE)
    compare_left = ParagraphStyle("CompL", fontName="Helvetica", fontSize=8, leading=11, textColor=HexColor("#1b5e20"))
    compare_right = ParagraphStyle("CompR", fontName="Helvetica", fontSize=8, leading=11, textColor=HexColor("#b71c1c"))
    compare_source = ParagraphStyle("CompS", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=HexColor("#666666"))

    cmp_data = [
        [Paragraph("<b>WHAT WAS SOLD TO ME</b>", compare_header),
         Paragraph("<b>WHAT ACTUALLY EXISTS</b>", compare_header)],

        [Paragraph("\"<b>Dedicated 1-2-1 coach</b> for 12 weeks. Private thread for messages, "
                   "voice notes, feedback and <b>calls to customise the process</b> to your business.\"",
                   compare_left),
         Paragraph("\"One-on-One Coaching Support: a channel [that] facilitates the sharing of "
                   "<b>voice notes, document reviews, messages</b>.\"<br/>"
                   "— A messaging thread. Not scheduled calls.",
                   compare_right)],

        [Paragraph("<i>Source: Jim Galvin's sales email, March 2, 15:18 UTC "
                   "(sent minutes before payment was collected)</i>", compare_source),
         Paragraph("<i>Source: Merchant's own Terms of Use at propane-business.com/terms "
                   "(live as of April 7, 2026 — screenshot attached as Exhibit B)</i>", compare_source)],

        [Paragraph("The sales email promises <b>\"calls\"</b> — meaning scheduled, "
                   "live Zoom coaching sessions with a dedicated personal coach.",
                   compare_left),
         Paragraph("The merchant's sales page at propanefitness.com/onlinecoach describes "
                   "\"<b>12 weeks of live coaching</b>\" with <b>no mention of 'dedicated 1-2-1 coach' "
                   "anywhere on the page</b>. Testimonials reference \"group coaching programme.\"",
                   compare_right)],

        [Paragraph("<i>This is the representation that induced a £6,300 purchase.</i>", compare_source),
         Paragraph("<i>Source: Merchant's own sales page (screenshot attached as Exhibit B)</i>", compare_source)],
    ]

    cmp_t = Table(cmp_data, colWidths=[3.25 * inch, 3.25 * inch])
    cmp_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#2e7d32")),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#c62828")),
        ("BACKGROUND", (0, 1), (0, 1), GREEN_BG),
        ("BACKGROUND", (1, 1), (1, 1), RED_BG),
        ("BACKGROUND", (0, 2), (-1, 2), HexColor("#f5f5f5")),
        ("BACKGROUND", (0, 3), (0, 3), GREEN_BG),
        ("BACKGROUND", (1, 3), (1, 3), RED_BG),
        ("BACKGROUND", (0, 4), (-1, 4), HexColor("#f5f5f5")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(cmp_t)
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "The merchant's chargeback response (Attachment 4) claims I received \"Individual Zoom calls, "
        "messaging, and personalised support.\" No individual Zoom calls occurred. I asked how to schedule "
        "one and was told no system exists. The merchant's own Exhibit E contains this proof.",
        s["finding"]
    ))

    # =====================================================================
    # FINDING 3: REFUND PROCESS WAS RIGGED
    # =====================================================================
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("FINDING 3: THE REFUND PROCESS WAS WITHHELD, THEN WEAPONIZED", s["h1"]))

    elements.append(Paragraph(
        "I requested a refund on <b>March 6</b> — Day 4 of the merchant's own 14-day refund window. "
        "Here is what followed:",
        s["body"]
    ))

    elements.append(Paragraph(
        "• March 6-13: I sent <b>four formal emails</b> to jim@propanefitness.com and admin@propanefitness.com. "
        "The only reply (March 7) addressed foreign transaction fees and ignored all refund grounds.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• March 14: The merchant's own coach, Phil Charlton, admitted: <i>\"Until yesterday I wasn't aware "
        "this had been raised.\"</i> The person responsible for handling refunds was \"completely unaware\" "
        "for 8 days.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• March 14: Refund form finally provided — <b>8 days after my first request</b>, despite the "
        "merchant's own Section 7.4 requiring it \"on request.\"",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• March 16: The merchant demanded I <b>withdraw my chargebacks first</b> before they would "
        "\"assess eligibility\" — with no guarantee of refund and a review period of up to 90 days. "
        "They simultaneously threatened breach of contract, counterclaim for £6,300 plus legal costs, "
        "and referral to a collections agency.",
        s["bullet"]
    ))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "The merchant designed a process where the only options were: (1) surrender chargeback protections "
        "with no guaranteed refund, or (2) keep chargebacks and be called a contract breaker. "
        "I chose to keep my financial protections. That is not \"declining a refund process\" — "
        "it is refusing a trap.",
        s["finding"]
    ))

    # =====================================================================
    # FINDING 4: RETROACTIVE CONTRACT TERMS
    # =====================================================================
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("FINDING 4: MERCHANT SUBMITTED FRAUDULENT CONTRACT EVIDENCE", s["h1"]))
    elements.append(Paragraph(
        "The merchant's Attachment 3 includes two separate agreements:",
        s["body"]
    ))
    elements.append(Paragraph(
        "• <b>Terms of Use</b> — signed March 5, 2026 (three days AFTER payment was collected on March 2). "
        "The merchant's own coach admitted: \"you should have been sent this upon point of sale.\"",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "• <b>\"Sales Kick\" Addendum</b> — effective date <b>March 13, 2026</b>. This addendum introduces "
        "binding arbitration, a jury trial waiver, and a class action waiver. It did not exist when I "
        "purchased the program (March 2) or signed the original terms (March 5). I never agreed to it. "
        "The merchant applied it retroactively to a transaction already in dispute.",
        s["bullet"]
    ))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        "Additionally, the merchant registered with the payment processor as \"Nutritional coaching\" "
        "(Attachment 4, page 1). The service sold is a business mentorship program. This is a "
        "misrepresentation to the payment processor about the nature of the business.",
        s["body"]
    ))

    # =====================================================================
    # REQUEST
    # =====================================================================
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8))
    elements.append(Paragraph("REQUEST", s["h1"]))
    elements.append(Paragraph(
        "The merchant's three claims to American Express are each contradicted by evidence — "
        "much of it from the merchant's own exhibits and public pages:",
        s["body"]
    ))

    req_data = [
        [Paragraph("<b>Merchant's Claim</b>", ParagraphStyle("Rh", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)),
         Paragraph("<b>Evidence Disproving It</b>", ParagraphStyle("Rh", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)),
         Paragraph("<b>Source</b>", ParagraphStyle("Rh", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE))],

        [Paragraph("\"Cardholder accessed all services\"", ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Cardholder had no access to live calls, content, or platform features from March 2-5",
                   ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Merchant's own Exhibit E + Exhibit A attached", ParagraphStyle("Rc", fontName="Helvetica", fontSize=7.5, leading=10, textColor=HexColor("#666")))],

        [Paragraph("\"Product delivered as described\"", ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Sales email says \"dedicated 1-2-1 calls\"; website says \"group coaching\"; "
                   "terms say \"messaging thread\"; no 1-on-1 Zoom scheduling exists",
                   ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Sales email + Exhibit B attached + merchant's terms", ParagraphStyle("Rc", fontName="Helvetica", fontSize=7.5, leading=10, textColor=HexColor("#666")))],

        [Paragraph("\"Refund process communicated and declined\"", ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Refund form withheld 8 days; when provided, required surrendering chargeback protections "
                   "with no guaranteed refund; merchant threatened collections",
                   ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)),
         Paragraph("Merchant's own Exhibit B + email correspondence", ParagraphStyle("Rc", fontName="Helvetica", fontSize=7.5, leading=10, textColor=HexColor("#666")))],
    ]
    req_t = Table(req_data, colWidths=[1.7 * inch, 2.8 * inch, 2.0 * inch])
    req_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(req_t)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "I respectfully request that American Express reverse the rebill on both cases and restore "
        "the credits totaling £6,300 (approximately $8,741.76 USD including foreign transaction fees) "
        "to my account.",
        s["body_bold"]
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Formal consumer protection complaints are being filed with UK Trading Standards, the Competition "
        "and Markets Authority, and Action Fraud regarding this merchant's sales practices.",
        s["body"]
    ))

    elements.append(Spacer(1, 12))
    for line in [
        "Respectfully submitted,",
        "",
        "<b>William J. Marceau</b>",
        "wmarceau@marceausolutions.com",
        "Naples, Florida, US",
        "April 7, 2026",
    ]:
        elements.append(Paragraph(line, s["sig"]))

    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=4))
    elements.append(Paragraph(
        "Cases D-93497818 and D-93497819 | Exhibits A, B, and C follow on subsequent pages",
        s["page_footer"]
    ))

    # =====================================================================
    # EXHIBIT A: CIRCLE.SO MESSAGE THREAD (MessageThread 3 + 4)
    # =====================================================================
    elements.append(PageBreak())
    elements.append(exhibit_header("EXHIBIT A — CARDHOLDER MESSAGES ON MERCHANT'S PLATFORM", s))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "These messages were sent on the merchant's own Circle.so platform between the cardholder "
        "and assigned coach Phil Charlton on March 4-5, 2026. The merchant submitted these same "
        "messages as their Exhibit E in support of their chargeback response — but the content "
        "proves the cardholder's case, not the merchant's.",
        s["exhibit_desc"]
    ))
    elements.append(Spacer(1, 4))

    # Insert MessageThread3 screenshot
    mt3_path = EVIDENCE_DIR / "MessageThread3.pdf"
    mt4_path = EVIDENCE_DIR / "MessageThread4.pdf"

    elements.append(Paragraph(
        "KEY EVIDENCE: Cardholder asks how to schedule live coaching calls — "
        "discovers no scheduling system exists and no live calls are available on the platform.",
        s["annotation"]
    ))
    elements.append(Spacer(1, 2))

    # Since we can't easily embed PDFs within PDFs using ReportLab,
    # use the PNG screenshots of the message threads instead
    for mt_num, mt_desc in [
        (3, "March 4: Cardholder asks about Pulse access, how to schedule live calls, "
            "reports no available live calls on Circle, no access to content"),
        (4, "March 4-5: Cardholder says \"it really seems like I just got scammed.\" "
            "Coach admits terms should have been sent at point of sale. "
            "Access not resolved until March 5 — 3 days after payment."),
    ]:
        elements.append(Paragraph(f"<b>Message Thread {mt_num}:</b> {mt_desc}", s["body"]))
        elements.append(Paragraph(
            f"[Full screenshot: MessageThread{mt_num}.pdf — submitted as part of this package]",
            ParagraphStyle("Ref", fontName="Helvetica-Oblique", fontSize=8, leading=11,
                          textColor=HexColor("#666666"), leftIndent=10, spaceAfter=8)
        ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "WHAT THESE MESSAGES PROVE:", s["body_bold"]
    ))
    elements.append(Paragraph(
        "1. The cardholder expected scheduled live 1-on-1 coaching calls (as sold) and discovered "
        "no scheduling system existed on the platform.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "2. The cardholder had NO access to Circle features, course content, or Notion resources "
        "from March 2 through March 5.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "3. The merchant's own coach admitted the terms \"should have been sent upon point of sale\" — "
        "confirming the merchant's own process was broken.",
        s["bullet"]
    ))
    elements.append(Paragraph(
        "4. The cardholder identified the service as a potential scam within 48 hours of payment, "
        "before ever having functional access to any content.",
        s["bullet"]
    ))

    # =====================================================================
    # EXHIBIT B: SALES PAGE SCREENSHOT
    # =====================================================================
    elements.append(PageBreak())
    elements.append(exhibit_header("EXHIBIT B — MERCHANT'S OWN SALES PAGE (LIVE AS OF APRIL 7, 2026)", s))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Screenshot of propanefitness.com/onlinecoach captured programmatically on April 7, 2026. "
        "This is the merchant's public-facing sales page for the programme the cardholder purchased.",
        s["exhibit_desc"]
    ))

    # Try to insert the sales page screenshot
    sales_png = WEB_EVIDENCE_DIR / "2026-04-07_2003_sales-page-onlinecoach.png"
    if sales_png.exists():
        try:
            img = Image(str(sales_png), width=6.0 * inch, height=8.0 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
        except Exception:
            elements.append(Paragraph(
                "[Screenshot: 2026-04-07_2003_sales-page-onlinecoach.pdf — submitted as part of this package]",
                ParagraphStyle("Ref", fontName="Helvetica-Oblique", fontSize=8, leading=11,
                              textColor=HexColor("#666666"), alignment=TA_CENTER, spaceAfter=8)
            ))
    else:
        elements.append(Paragraph(
            "[Screenshot: 2026-04-07_2003_sales-page-onlinecoach.pdf — submitted as part of this package]",
            ParagraphStyle("Ref", fontName="Helvetica-Oblique", fontSize=8, leading=11,
                          textColor=HexColor("#666666"), alignment=TA_CENTER, spaceAfter=8)
        ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "KEY OBSERVATION: This page describes \"12 weeks of live coaching, help & on-demand support.\" "
        "There is NO mention of \"dedicated 1-2-1 coach\" anywhere on the page. "
        "Testimonials reference \"group coaching programme.\" This directly contradicts "
        "the seller's email promise of \"Dedicated 1-2-1 coach for 12 weeks\" with \"calls to "
        "customise the process to your business.\"",
        s["annotation"]
    ))

    # =====================================================================
    # EXHIBIT C: COMPANIES HOUSE
    # =====================================================================
    elements.append(PageBreak())
    elements.append(exhibit_header("EXHIBIT C — UK COMPANIES HOUSE REGISTRATION", s))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Official UK government registration record for Propane Fitness Ltd, confirming corporate "
        "identity, registration number, registered address, and active status.",
        s["exhibit_desc"]
    ))

    ch_png = WEB_EVIDENCE_DIR / "2026-04-07_2003_companies-house-registration.png"
    if ch_png.exists():
        try:
            img = Image(str(ch_png), width=5.0 * inch, height=7.0 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
        except Exception:
            elements.append(Paragraph(
                "[Screenshot: 2026-04-07_2003_companies-house-registration.pdf]",
                ParagraphStyle("Ref", fontName="Helvetica-Oblique", fontSize=8, leading=11,
                              textColor=HexColor("#666666"), alignment=TA_CENTER, spaceAfter=8)
            ))
    else:
        elements.append(Paragraph(
            "[Screenshot: 2026-04-07_2003_companies-house-registration.pdf]",
            ParagraphStyle("Ref", fontName="Helvetica-Oblique", fontSize=8, leading=11,
                          textColor=HexColor("#666666"), alignment=TA_CENTER, spaceAfter=8)
        ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "CONFIRMS: Propane Fitness Ltd (Co. 07779096), Private Limited Company, Active, "
        "incorporated 19 September 2011. Current registered address: 1 Holly House, Mill Street, "
        "Uppermill, Oldham, OL3 6LZ — different from the 69 Church Way, North Shields address "
        "on the cardholder's contract. Directors: Jonathan James Watson and Dr. Yusef El-Sobky.",
        s["annotation"]
    ))

    # Build
    doc.build(elements)
    fsize = os.path.getsize(OUTPUT)
    print(f"Generated: {OUTPUT}")
    print(f"File size: {fsize // 1024}KB")
    print(f"Submit this single PDF to American Express for cases D-93497818 and D-93497819.")
    return OUTPUT


if __name__ == "__main__":
    build()
