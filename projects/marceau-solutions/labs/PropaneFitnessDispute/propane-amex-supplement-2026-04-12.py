#!/usr/bin/env python3
"""
Propane Fitness — AmEx Dispute Supplement (April 12, 2026)
Cases D-93497818 (Card 1007) and D-93497819 (Card 1049)

Purpose: Place the confirmed UK regulatory reference numbers of record on both
cases as supplemental evidence to the April 7, 2026 Cardholder Statement.

Scope rules enforced in the drafting of this document:
  - No new factual allegations beyond the April 7 statement.
  - No self-incriminating language or admissions of engagement with the service.
  - No concessions, no hedging, no apologies for timing.
  - Merchant-focused framing (regulatory scrutiny of the merchant's conduct).
  - First-person voice matching the April 7 Cardholder Statement.
"""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# --- Brand colors (match April 7 resubmission package) ---
NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
GOLD = HexColor("#C9963C")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
WHITE = colors.white

OUTPUT = os.path.join(os.path.dirname(__file__), "propane-amex-supplement-2026-04-12.pdf")


def styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=15, leading=20,
                                textColor=NAVY, spaceAfter=2, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=9.5, leading=13,
                                   textColor=CHARCOAL, spaceAfter=10, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                             textColor=NAVY, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                               textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "body_bold": ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=9.5,
                                    leading=13.5, textColor=CHARCOAL, spaceAfter=5),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9.5, leading=13.5,
                                 textColor=CHARCOAL, leftIndent=18, spaceAfter=4,
                                 bulletIndent=8, alignment=TA_JUSTIFY),
        "sig": ParagraphStyle("Sig", fontName="Helvetica", fontSize=9, leading=12,
                              textColor=CHARCOAL, spaceAfter=2),
        "page_footer": ParagraphStyle("PageFooter", fontName="Helvetica", fontSize=7,
                                      leading=9, textColor=HexColor("#999999"), alignment=TA_CENTER),
    }


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.6 * inch,
    )
    s = styles()
    els = []

    # ── Header ───────────────────────────────────────────────────────────────
    els.append(Paragraph("SUPPLEMENTAL FILING — REGULATORY AUTHORITY REFERENCES", s["title"]))
    els.append(Paragraph("Update to Cardholder Statement of April 7, 2026", s["subtitle"]))
    els.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))

    case_data = [
        ["Cardholder:", "William J. Marceau | wmarceau@marceausolutions.com | Naples, FL"],
        ["Cases:", "D-93497818 (Card ending 1007) and D-93497819 (Card ending 1049)"],
        ["Merchant:", "Propane Fitness Ltd (UK Co. 07779096) | propanefitness.com"],
        ["Amount:", "£6,300 GBP (~$8,741.76 USD including foreign transaction fees)"],
        ["Reason Code:", "4553 — Product Unacceptable (Not as Described)"],
        ["Supplement Date:", "April 12, 2026"],
    ]
    ct = Table(case_data, colWidths=[1.25 * inch, 5.25 * inch])
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
    els.append(ct)
    els.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=8))

    # ── Purpose ──────────────────────────────────────────────────────────────
    els.append(Paragraph("PURPOSE", s["h1"]))
    els.append(Paragraph(
        "My Cardholder Statement of April 7, 2026 noted that formal consumer-protection "
        "complaints were being filed against Propane Fitness Ltd with UK regulatory authorities. "
        "This supplement places the confirmed reference numbers of record on both cases. "
        "<b>No new factual allegations are introduced by this supplement.</b> It records only "
        "the regulatory filings submitted in relation to the same conduct set out in the "
        "April 7 statement.",
        s["body"]
    ))

    # ── Regulatory Filings Table ─────────────────────────────────────────────
    els.append(Paragraph("REGULATORY FILINGS OF RECORD", s["h1"]))

    th = ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8, leading=11,
                        textColor=WHITE, alignment=TA_CENTER)
    td = ParagraphStyle("Td", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)
    td_bold = ParagraphStyle("TdB", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=CHARCOAL)

    filings = [
        [Paragraph("<b>Authority</b>", th),
         Paragraph("<b>Reference</b>", th),
         Paragraph("<b>Filed</b>", th),
         Paragraph("<b>Scope</b>", th)],

        [Paragraph("Competition and Markets Authority (CMA)<br/>"
                   "<font size=7 color='#666666'>UK non-ministerial government department<br/>"
                   "contact-the-cma.service.gov.uk</font>", td),
         Paragraph("<b>CMAE2600101</b>", td_bold),
         Paragraph("April 8,<br/>2026", td),
         Paragraph("Misleading commercial practice; unfair contract terms; "
                   "retroactive contract modification; high-pressure sales sequence; "
                   "pricing opacity.", td)],

        [Paragraph("Action Fraud (City of London Police)<br/>"
                   "<font size=7 color='#666666'>UK national fraud reporting service<br/>"
                   "reporting.reportfraud.police.uk</font>", td),
         Paragraph("<b>RF26040189625C</b>", td_bold),
         Paragraph("April 8,<br/>2026", td),
         Paragraph("Fraud by false representation (Fraud Act 2006, s.2); post-payment "
                   "contract execution; retroactive addendum; payment-processor "
                   "classification discrepancy.", td)],

        [Paragraph("UK Trading Standards<br/>"
                   "<font size=7 color='#666666'>via Citizens Advice consumer service<br/>"
                   "referrals.citizensadvice.org.uk/consumer</font>", td),
         Paragraph("<i>In progress</i>", td),
         Paragraph("Filing<br/>in progress", td),
         Paragraph("Consumer Protection from Unfair Trading Regulations 2008 — "
                   "misleading action (Reg. 5), aggressive commercial practice (Reg. 7), "
                   "unfair contract terms under the Consumer Rights Act 2015.", td)],
    ]

    ft = Table(filings, colWidths=[1.85 * inch, 1.20 * inch, 0.70 * inch, 2.75 * inch])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    els.append(ft)
    els.append(Spacer(1, 4))
    els.append(Paragraph(
        "Submission confirmations for Filings 1 and 2 are retained and available on request.",
        s["body"]
    ))

    # ── Relation to April 7 Statement ────────────────────────────────────────
    els.append(Paragraph("RELATION TO THE APRIL 7 CARDHOLDER STATEMENT", s["h1"]))
    els.append(Paragraph(
        "Each filing above corresponds to conduct already documented in the April 7 "
        "Cardholder Statement. The correspondence is as follows:",
        s["body"]
    ))
    els.append(Paragraph(
        "&bull; <b>Finding 2 (Product Not as Described)</b> is the subject of both the CMA "
        "complaint and the Action Fraud report. The CMA complaint cites the contradiction between "
        "the seller's written email promising a \"Dedicated 1-2-1 coach for 12 weeks\" with "
        "\"calls to customise the process\" and the merchant's own Terms of Use, which define "
        "\"One-on-One Coaching Support\" as a messaging channel only. The Action Fraud report "
        "frames the same conduct under Section 2 of the Fraud Act 2006 (fraud by false "
        "representation).",
        s["bullet"]
    ))
    els.append(Paragraph(
        "&bull; <b>Finding 4 (Retroactive and Post-Payment Contract Terms)</b> is addressed by "
        "both filings. The CMA and Action Fraud submissions document the \"Sales Kick Addendum\" "
        "bearing an effective date of March 13, 2026 — eleven days after the purchase on March 2 — "
        "and the payment-processor classification under which the merchant operated.",
        s["bullet"]
    ))
    els.append(Paragraph(
        "&bull; <b>Finding 3 (Refund Process Withheld and Conditioned)</b> is the subject of the "
        "UK Trading Standards filing now in progress, under Regulations 5 and 7 of the Consumer "
        "Protection from Unfair Trading Regulations 2008.",
        s["bullet"]
    ))

    # ── Request ──────────────────────────────────────────────────────────────
    els.append(Spacer(1, 4))
    els.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=6))
    els.append(Paragraph("REQUEST", s["h1"]))
    els.append(Paragraph(
        "I respectfully request that American Express:",
        s["body"]
    ))
    els.append(Paragraph(
        "1. Record the confirmed reference numbers <b>CMAE2600101</b> (Competition and Markets "
        "Authority) and <b>RF26040189625C</b> (Action Fraud) as supplemental evidence on both "
        "Cases D-93497818 and D-93497819, in support of the Cardholder Statement of April 7, 2026.",
        s["bullet"]
    ))
    els.append(Paragraph(
        "2. Reverse the April 7, 2026 rebill on both cases and restore the credits totaling "
        "£6,300 (approximately $8,741.76 USD, including foreign transaction fees) on the basis "
        "of the full evidentiary record now on file.",
        s["bullet"]
    ))
    els.append(Paragraph(
        "3. Accept a further supplement from me once the UK Trading Standards reference number "
        "is issued, to be filed to both cases at that time.",
        s["bullet"]
    ))

    # ── Signature ────────────────────────────────────────────────────────────
    els.append(Spacer(1, 14))
    for line in [
        "Respectfully submitted,",
        "",
        "<b>William J. Marceau</b>",
        "wmarceau@marceausolutions.com",
        "Naples, Florida, US",
        "April 12, 2026",
    ]:
        els.append(Paragraph(line, s["sig"]))

    els.append(Spacer(1, 8))
    els.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"), spaceAfter=4))
    els.append(Paragraph(
        "Supplement to Cases D-93497818 and D-93497819 | April 12, 2026",
        s["page_footer"]
    ))

    doc.build(els)
    fsize = os.path.getsize(OUTPUT)
    print(f"Generated: {OUTPUT}")
    print(f"File size: {fsize // 1024}KB")
    return OUTPUT


if __name__ == "__main__":
    build()
