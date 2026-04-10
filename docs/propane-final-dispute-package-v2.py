#!/usr/bin/env python3
"""
Propane Fitness — FINAL Single-File Dispute Package v2
Cases D-93497818 and D-93497819

ONE PDF. Everything embedded. Every screenshot legible.
A dispute reviewer reads this top to bottom and reaches one conclusion.

Structure:
  Pages 1-3:  Cardholder statement (4 findings + summary table + request)
  Page 4:     Exhibit 1 — Circle.so messages: "How do I schedule live cal" (MessageThread3)
  Page 5:     Exhibit 1 cont. — "it really seems like I just got scammed" (MessageThread4)
  Page 6:     Exhibit 2 — Terms: "1-on-1 = messaging thread" + "Coaching Clinics = group Zoom"
  Page 7:     Exhibit 3 — Terms: Section 7.5 chargeback intimidation + Section 11.4 misrep liability
  Page 8:     Exhibit 4 — Sales Kick Addendum dated 13/3/26 (retroactive terms)
  Page 9:     Exhibit 5 — Sales page header (no mention of "1-2-1 coach")
  Page 10:    Exhibit 6 — Companies House registration
"""

import os
import sys
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
    PageBreak, HRFlowable, Image
)

NAVY = HexColor("#1a2744")
DARK_BLUE = HexColor("#2c3e6b")
RED = HexColor("#c0392b")
CHARCOAL = HexColor("#333333")
LIGHT_GRAY = HexColor("#f2f2f2")
WHITE = colors.white
GREEN_BG = HexColor("#e8f5e9")
RED_BG = HexColor("#ffebee")

EVIDENCE = Path(__file__).parent.parent / "projects" / "marceau-solutions" / "labs" / "PropaneFitnessDispute"
CROPPED = EVIDENCE / "web-evidence" / "cropped"
OUTPUT = os.path.join(os.path.dirname(__file__), "PROPANE-DISPUTE-FINAL-PACKAGE.pdf")

W = 6.5 * inch  # usable width


def S():
    """All styles."""
    return {
        "title": ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=15, leading=20,
                                textColor=NAVY, spaceAfter=2, alignment=TA_CENTER),
        "sub": ParagraphStyle("Sub", fontName="Helvetica", fontSize=9.5, leading=13,
                              textColor=CHARCOAL, spaceAfter=10, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12, leading=16,
                             textColor=NAVY, spaceBefore=10, spaceAfter=5),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                             textColor=DARK_BLUE, spaceBefore=6, spaceAfter=3),
        "b": ParagraphStyle("B", fontName="Helvetica", fontSize=9.5, leading=13.5,
                            textColor=CHARCOAL, spaceAfter=5, alignment=TA_JUSTIFY),
        "bb": ParagraphStyle("BB", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5,
                             textColor=CHARCOAL, spaceAfter=5),
        "f": ParagraphStyle("F", fontName="Helvetica-Bold", fontSize=9.5, leading=13.5,
                            textColor=RED, spaceAfter=5),
        "q": ParagraphStyle("Q", fontName="Helvetica-Oblique", fontSize=9.5, leading=13.5,
                            textColor=HexColor("#444"), leftIndent=18, rightIndent=18,
                            spaceAfter=5, borderPadding=6, backColor=HexColor("#f8f8f8")),
        "bu": ParagraphStyle("Bu", fontName="Helvetica", fontSize=9.5, leading=13.5,
                             textColor=CHARCOAL, leftIndent=22, spaceAfter=3, bulletIndent=10),
        "et": ParagraphStyle("ET", fontName="Helvetica-Bold", fontSize=12, leading=16,
                             textColor=WHITE, alignment=TA_CENTER),
        "ed": ParagraphStyle("ED", fontName="Helvetica", fontSize=9, leading=12,
                             textColor=CHARCOAL, alignment=TA_CENTER, spaceAfter=6),
        "an": ParagraphStyle("AN", fontName="Helvetica-Bold", fontSize=9, leading=12,
                             textColor=RED, spaceAfter=4, leftIndent=8, borderPadding=5,
                             backColor=HexColor("#fff5f5")),
        "sig": ParagraphStyle("Sig", fontName="Helvetica", fontSize=9, leading=12,
                              textColor=CHARCOAL, spaceAfter=2),
        "ft": ParagraphStyle("Ft", fontName="Helvetica", fontSize=7, leading=9,
                             textColor=HexColor("#999"), alignment=TA_CENTER),
    }


def banner(text, s):
    t = Table([[Paragraph(text, s["et"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def img(filename, w=6.0, h=4.5):
    """Insert image if it exists, scaled to fit. Only loads PNG/JPG, never PDF."""
    # Strip .pdf extension and look for .png version
    base = filename.rsplit(".", 1)[0] if "." in filename else filename
    # Try cropped dir first (PNG only)
    p = CROPPED / filename
    if not p.exists() or filename.endswith(".pdf"):
        p = CROPPED / (base + ".png")
    if not p.exists():
        p = EVIDENCE / filename
        if filename.endswith(".pdf"):
            p = CROPPED / (base + ".png")
    if p.exists() and not str(p).endswith(".pdf"):
        try:
            i = Image(str(p), width=w * inch, height=h * inch)
            i.hAlign = "CENTER"
            return i
        except Exception:
            pass
    return Paragraph(f"[Image: {filename} — not found]",
                     ParagraphStyle("X", fontSize=8, textColor=HexColor("#999")))


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.65 * inch, bottomMargin=0.55 * inch)
    s = S()
    e = []

    # ================================================================
    # PAGES 1-3: CARDHOLDER STATEMENT
    # ================================================================
    e.append(Paragraph("CARDHOLDER STATEMENT — NEW EVIDENCE", s["title"]))
    e.append(Paragraph("Resubmission Following Rebill of April 7, 2026", s["sub"]))
    e.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=6))

    ci = [
        ["Cardholder:", "William J. Marceau | wmarceau@marceausolutions.com | Naples, FL"],
        ["Cases:", "D-93497818 (Card 1007) and D-93497819 (Card 1049)"],
        ["Merchant:", "Propane Fitness Ltd (UK Co. 07779096) | propanefitness.com"],
        ["Amount:", "£6,300 GBP ($8,741.76 USD incl. foreign transaction fees)"],
        ["Reason Code:", "4553 — Product Unacceptable (Not as Described)"],
    ]
    ct = Table(ci, colWidths=[1.1 * inch, 5.4 * inch])
    ct.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), CHARCOAL),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    e.append(ct)
    e.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#ddd"), spaceAfter=6))

    e.append(Paragraph(
        "American Express rebilled both charges on April 7, 2026, citing the merchant's claim that "
        "<b>(1) the product was delivered as described, (2) I accessed all services, and "
        "(3) I declined their refund process.</b> Each claim is false. The evidence below — including "
        "the merchant's own exhibits submitted to American Express — proves it.",
        s["b"]))
    e.append(Spacer(1, 4))

    # --- FINDING 1 ---
    e.append(Paragraph("FINDING 1: I DID NOT \"ACCESS ALL SERVICES\"", s["h1"]))
    e.append(Paragraph(
        "The merchant's own platform messages — submitted as their <b>Exhibit E</b> (Attachment 4) — show that "
        "I had no access to live calls, course content, or platform features from March 2-5.",
        s["b"]))

    Th = ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)
    Tc = ParagraphStyle("Tc", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=CHARCOAL)
    Tr = ParagraphStyle("Tr", fontName="Helvetica-Oblique", fontSize=8.5, leading=12, textColor=RED)

    msgs = [
        [Paragraph("<b>Time</b>", Th), Paragraph("<b>My Message on Merchant's Platform</b>", Th)],
        [Paragraph("Mar 4\n12:20", Tc), Paragraph("\"Also How do I schedule live cal with you as that is also part of the services\"", Tc)],
        [Paragraph("Mar 4\n12:22", Tc), Paragraph("\"Additionally when im logged into circle it does not show me any available live calls or the ability to access the content\"", Tc)],
        [Paragraph("Mar 4\n12:26", Tc), Paragraph("\"so I dont seem to have any access to any of the features in circle and all the links in notion bring me back to the email marketing page\"", Tc)],
        [Paragraph("Mar 4\n12:32", Tr), Paragraph("\"it really seems like I just got scammed\"", Tr)],
    ]
    mt = Table(msgs, colWidths=[0.7 * inch, 5.8 * inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#fafafa")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    e.append(mt)
    e.append(Spacer(1, 3))
    e.append(Paragraph("The merchant's coach responded:", s["bb"]))
    e.append(Paragraph(
        "\"You just need to sign the Ts and C's, you should have been sent this upon point of sale.\" "
        "— Phil Charlton, March 4 (admitting the process was broken)", s["q"]))
    e.append(Paragraph(
        "\"Originally you put the wrong email address in which is what has caused the issue.\" "
        "— Phil Charlton, March 5 (access not resolved until 3 days after payment)", s["q"]))
    e.append(Paragraph(
        "I never attended a coaching clinic. I never accessed course modules. I never received a "
        "scheduled 1-on-1 coaching session — the core service I purchased. "
        "See Exhibit 1 for full message thread screenshots.", s["f"]))

    # --- FINDING 2 ---
    e.append(Paragraph("FINDING 2: THE PRODUCT WAS NOT AS DESCRIBED", s["h1"]))

    Ch = ParagraphStyle("Ch", fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=WHITE)
    Cg = ParagraphStyle("Cg", fontName="Helvetica", fontSize=8, leading=11, textColor=HexColor("#1b5e20"))
    Cr = ParagraphStyle("Cr", fontName="Helvetica", fontSize=8, leading=11, textColor=HexColor("#b71c1c"))
    Cs = ParagraphStyle("Cs", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=HexColor("#666"))

    cmp = [
        [Paragraph("<b>WHAT WAS SOLD</b>", Ch), Paragraph("<b>WHAT ACTUALLY EXISTS</b>", Ch)],
        [Paragraph("\"<b>Dedicated 1-2-1 coach</b> for 12 weeks... <b>calls to customise the process</b> to your business.\"", Cg),
         Paragraph("\"One-on-One Coaching Support: a channel facilitates the sharing of <b>voice notes, document reviews, messages</b>.\" — A messaging thread.", Cr)],
        [Paragraph("<i>Source: Jim Galvin's email, Mar 2 15:18</i>", Cs),
         Paragraph("<i>Source: Merchant's Terms of Use (Exhibit 2)</i>", Cs)],
        [Paragraph("Promised <b>\"calls\"</b> — scheduled live Zoom with a dedicated coach.", Cg),
         Paragraph("Sales page says \"12 weeks of live coaching\" — <b>no mention of 'dedicated 1-2-1 coach'</b>. Testimonials say \"group coaching programme.\" (Exhibit 5)", Cr)],
        [Paragraph("Chargeback response claims \"<b>Individual Zoom calls</b>, messaging, and personalised support.\"", Cg),
         Paragraph("I asked how to schedule a live call. <b>No scheduling system exists.</b> No individual Zoom calls ever occurred. (Merchant's own Exhibit E, submitted in their Attachment 4)", Cr)],
    ]
    cmpt = Table(cmp, colWidths=[3.25 * inch, 3.25 * inch])
    cmpt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#2e7d32")),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#c62828")),
        ("BACKGROUND", (0, 1), (0, 1), GREEN_BG), ("BACKGROUND", (1, 1), (1, 1), RED_BG),
        ("BACKGROUND", (0, 2), (-1, 2), HexColor("#f5f5f5")),
        ("BACKGROUND", (0, 3), (0, 3), GREEN_BG), ("BACKGROUND", (1, 3), (1, 3), RED_BG),
        ("BACKGROUND", (0, 4), (0, 4), GREEN_BG), ("BACKGROUND", (1, 4), (1, 4), RED_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#ccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    e.append(cmpt)
    e.append(Spacer(1, 4))

    # --- FINDING 3 ---
    e.append(Paragraph("FINDING 3: THE REFUND PROCESS WAS WITHHELD, THEN WEAPONIZED", s["h1"]))
    e.append(Paragraph("I requested a refund on <b>March 6</b> — Day 4 of the 14-day window:", s["b"]))
    for bullet in [
        "March 6-13: Four formal emails sent. Only reply (March 7) addressed foreign transaction fees — ignored all refund grounds.",
        "March 14: Coach admitted: \"Until yesterday I wasn't aware this had been raised.\" 8 days unaware.",
        "March 14: Refund form finally provided — <b>8 days late</b> despite Section 7.4 requiring it \"on request.\"",
        "March 16: Merchant demanded I <b>withdraw chargebacks first</b> — no guaranteed refund, 90-day review. Simultaneously threatened collections, legal costs, and breach of contract.",
    ]:
        e.append(Paragraph(f"• {bullet}", s["bu"]))
    e.append(Paragraph(
        "That is not \"declining a refund process.\" It is refusing to surrender financial protections "
        "on an $8,700 purchase for a non-binding promise to \"assess eligibility.\"", s["f"]))

    # --- FINDING 4 ---
    e.append(Paragraph("FINDING 4: RETROACTIVE CONTRACT TERMS + PROCESSOR MISREPRESENTATION", s["h1"]))
    for bullet in [
        "<b>Terms of Use</b> signed March 5 — three days AFTER payment (March 2). Coach admitted: \"should have been sent upon point of sale.\"",
        "<b>\"Sales Kick\" Addendum</b> dated <b>March 13, 2026</b> — introduces binding arbitration, jury trial waiver, class action waiver. Did not exist at purchase. Never agreed to. (Exhibit 4)",
        "Merchant registered with payment processor as <b>\"Nutritional coaching\"</b> — the service is a business mentorship program.",
    ]:
        e.append(Paragraph(f"• {bullet}", s["bu"]))

    # --- SUMMARY TABLE ---
    e.append(Spacer(1, 6))
    e.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=6))
    e.append(Paragraph("REQUEST", s["h1"]))

    Rh = ParagraphStyle("Rh", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)
    Rc = ParagraphStyle("Rc", fontName="Helvetica", fontSize=8, leading=11, textColor=CHARCOAL)
    Rb = ParagraphStyle("Rb", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=DARK_BLUE)

    req = [
        [Paragraph("<b>Merchant's Claim</b>", Rh), Paragraph("<b>Evidence Disproving It</b>", Rh), Paragraph("<b>See</b>", Rh)],
        [Paragraph("\"Accessed all services\"", Rc),
         Paragraph("No access to live calls, content, or features from Mar 2-5", Rc),
         Paragraph("Exhibit 1 +<br/>Merchant's Exhibit E", Rb)],
        [Paragraph("\"Delivered as described\"", Rc),
         Paragraph("Sales email: \"1-2-1 calls.\" Terms: \"messaging thread.\" Website: \"group coaching.\" No Zoom scheduling exists.", Rc),
         Paragraph("Exhibits 2, 5", Rb)],
        [Paragraph("\"Refund process declined\"", Rc),
         Paragraph("Form withheld 8 days; required surrendering chargeback first; merchant threatened collections", Rc),
         Paragraph("Exhibits 3, 4", Rb)],
    ]
    rt = Table(req, colWidths=[1.5 * inch, 3.7 * inch, 1.3 * inch])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#ccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    e.append(rt)
    e.append(Spacer(1, 6))

    e.append(Paragraph(
        "I respectfully request that American Express reverse the rebill on both cases and restore the "
        "credits totaling £6,300 (~$8,741.76 USD) to my account. Consumer protection complaints are being "
        "filed with UK Trading Standards, the Competition and Markets Authority, and Action Fraud.", s["bb"]))

    e.append(Spacer(1, 8))
    for line in ["Respectfully submitted,", "", "<b>William J. Marceau</b>",
                 "wmarceau@marceausolutions.com | Naples, Florida, US | April 7, 2026"]:
        e.append(Paragraph(line, s["sig"]))
    e.append(Spacer(1, 6))
    e.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#ddd"), spaceAfter=3))
    e.append(Paragraph("Exhibits 1 through 6 follow on subsequent pages.", s["ft"]))

    # ================================================================
    # EXHIBIT A: CIRCLE MESSAGES (2 pages)
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 1 — CARDHOLDER MESSAGES ON MERCHANT'S PLATFORM (Page 1 of 2)", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "Circle.so direct messages between cardholder and coach Phil Charlton, March 3-4, 2026. "
        "Cardholder asks about scheduling live coaching calls and reports no access to content. "
        "The merchant submitted these same messages as their Exhibit E (Attachment 4).", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("MessageThread3.pdf", w=6.2, h=7.5))

    e.append(PageBreak())
    e.append(banner("EXHIBIT 1 — CARDHOLDER MESSAGES ON MERCHANT'S PLATFORM (Page 2 of 2)", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "March 4-5, 2026. Cardholder reports no access to Circle features, says \"it really seems like "
        "I just got scammed.\" Coach admits terms should have been sent at point of sale. Access not "
        "resolved until March 5 — 3 days after payment.", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("MessageThread4.pdf", w=6.2, h=7.5))

    # ================================================================
    # EXHIBIT B: TERMS — 1-on-1 coaching + coaching clinics
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 2 — MERCHANT'S TERMS: \"1-ON-1\" = MESSAGING THREAD", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "Screenshot from propane-business.com/terms captured April 7, 2026. Shows the merchant's own "
        "definition of \"One-on-One Coaching Support\" and \"Coaching Clinics.\"", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("terms-coaching-clinics.png", w=6.2, h=4.2))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "KEY: The terms say \"1-2-1 access to a dedicated coach\" — but then define what that access "
        "means: \"a channel [that] facilitates the sharing of voice notes, document reviews, messages.\" "
        "That is a messaging thread — not the scheduled \"calls to customise the process\" promised in "
        "the seller's email. The word \"calls\" appears in the sales email but nowhere in the terms' "
        "definition of coaching support. \"Coaching Clinics\" are separately described as group Zoom "
        "sessions available to all members.", s["an"]))

    # ================================================================
    # EXHIBIT C: TERMS — Section 7.5 + 11.4
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 3 — SECTION 7.5 (CHARGEBACK THREAT) + 11.4 (MISREP LIABILITY)", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Section 7.5 — Chargeback = breach of contract + collections threat:", s["ed"]))
    e.append(img("terms-section-7-5.png", w=6.2, h=4.0))
    e.append(Spacer(1, 4))
    e.append(Paragraph("Section 11.4 — Merchant cannot exclude liability for misrepresentation:", s["ed"]))
    e.append(img("terms-section-11-4.png", w=6.2, h=4.0))
    e.append(Spacer(1, 2))
    e.append(Paragraph(
        "KEY: Section 7.5 threatens consumers who file chargebacks with collections and legal costs. "
        "Section 11.4 acknowledges the merchant CANNOT exclude liability for \"misrepresentation as to "
        "a fundamental matter.\" The nature of the coaching (1-on-1 calls vs. messaging thread) is "
        "a fundamental matter.", s["an"]))

    # ================================================================
    # EXHIBIT D: SALES KICK ADDENDUM
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 4 — RETROACTIVE \"SALES KICK\" ADDENDUM (DATED 13/3/26)", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "This addendum has an effective date of March 13, 2026 — 11 days after purchase and 7 days "
        "after the refund request. It introduces binding arbitration and a jury trial waiver. "
        "The cardholder never agreed to it.", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("terms-sales-kick-addendum.png", w=6.2, h=4.5))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "KEY: \"Effective Date: [13/3/26]\" — This addendum did not exist when the cardholder purchased "
        "the program (March 2) or signed the original Terms of Use (March 5). Retroactively applying "
        "binding arbitration and jury trial waiver to a transaction already in dispute is evidence of "
        "bad faith.", s["an"]))

    # ================================================================
    # EXHIBIT E: SALES PAGE
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 5 — MERCHANT'S SALES PAGE (NO MENTION OF \"1-2-1 COACH\")", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "Screenshot of propanefitness.com/onlinecoach captured April 7, 2026. This is the merchant's "
        "public sales page for the programme.", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("sales-page-section-1.png", w=6.2, h=4.2))
    e.append(Spacer(1, 2))
    e.append(img("sales-page-section-2.png", w=6.2, h=4.2))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "KEY: The page describes \"A Step By Step Process To Building & Scaling An Online Fitness Business\" "
        "with \"Coaching, support, feedback and custom built training created each week.\" There is NO "
        "mention of \"dedicated 1-2-1 coach\" anywhere. The seller's email promise of \"Dedicated 1-2-1 "
        "coach for 12 weeks\" with \"calls to customise the process\" does not appear on the merchant's "
        "own sales page.", s["an"]))

    # ================================================================
    # EXHIBIT F: COMPANIES HOUSE
    # ================================================================
    e.append(PageBreak())
    e.append(banner("EXHIBIT 6 — UK COMPANIES HOUSE REGISTRATION", s))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "Official UK government record confirming the merchant's corporate identity, active status, "
        "and registered address.", s["ed"]))
    e.append(Spacer(1, 2))
    e.append(img("companies-house.png", w=5.0, h=6.5))
    e.append(Spacer(1, 4))
    e.append(Paragraph(
        "CONFIRMS: Propane Fitness Ltd, Co. 07779096, Private Limited Company, Active, incorporated "
        "19 September 2011. Current address: 1 Holly House, Mill Street, Uppermill, Oldham, OL3 6LZ "
        "— different from 69 Church Way, North Shields on cardholder's contract. "
        "Directors: Jonathan James Watson and Dr. Yusef El-Sobky.", s["an"]))

    # Build
    doc.build(e)
    sz = os.path.getsize(OUTPUT) / 1024
    pages = "~10"
    print(f"\nGenerated: {OUTPUT}")
    print(f"Size: {sz:.0f}KB")
    print(f"Pages: {pages}")
    print(f"\nSubmit this ONE file to AmEx for cases D-93497818 and D-93497819.")


if __name__ == "__main__":
    build()
