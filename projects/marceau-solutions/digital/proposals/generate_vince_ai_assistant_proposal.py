#!/usr/bin/env python3
"""
Generate branded AI Personal Assistant proposal for Vince Grant.
Three businesses: Grant Roofs, Blue Collar Exits, Roofing Lead Marketplace.

Output: projects/marceau-solutions/digital/proposals/vince-ai-assistant-proposal.pdf
"""

import os
import sys
import smtplib
import ssl
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "execution"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

# ── Brand ─────────────────────────────────────────────────────────────────────
GOLD        = HexColor("#C9963C")
GOLD_LIGHT  = HexColor("#D4AF37")
GOLD_BG     = HexColor("#FDF8EF")
CHARCOAL    = HexColor("#333333")
CHARCOAL_D  = HexColor("#2D2D2D")
CARD_BG     = HexColor("#3D3D3D")
WHITE       = colors.white
LIGHT_GRAY  = HexColor("#f5f5f0")
MID_GRAY    = HexColor("#e2e0d8")
DARK_GRAY   = HexColor("#555555")
TEXT_MUTED  = HexColor("#94a3b8")
SLATE       = HexColor("#334155")

TAGLINE     = "Embrace the Pain & Defy the Odds"
COMPANY     = "Marceau Solutions"
WEBSITE     = "marceausolutions.com"
EMAIL       = "wmarceau@marceausolutions.com"
PHONE       = "(239) 398-5676"
CALENDLY    = "calendly.com/wmarceau/ai-services-discovery"
PROPOSAL_DATE = "April 11, 2026"

FONTS_DIR = ROOT / "execution" / "pdf_templates" / "fonts"
ASSETS_DIR = ROOT / "execution" / "pdf_templates" / "assets"

# ── Font registration ─────────────────────────────────────────────────────────
HEADING_FONT     = "Helvetica-Bold"
HEADING_FONT_REG = "Helvetica"
BODY_FONT        = "Helvetica"
BODY_FONT_BOLD   = "Helvetica-Bold"

def _register_fonts():
    global HEADING_FONT, HEADING_FONT_REG, BODY_FONT, BODY_FONT_BOLD
    font_map = {
        "Montserrat-Bold":    FONTS_DIR / "Montserrat-Bold.ttf",
        "Montserrat-Regular": FONTS_DIR / "Montserrat-Regular.ttf",
        "Inter-Regular":      FONTS_DIR / "Inter-Regular.ttf",
        "Inter-Bold":         FONTS_DIR / "Inter-Bold.ttf",
    }
    loaded = {}
    for name, path in font_map.items():
        try:
            if path.exists():
                pdfmetrics.registerFont(TTFont(name, str(path)))
                loaded[name] = True
        except Exception:
            pass
    if loaded.get("Montserrat-Bold"):   HEADING_FONT     = "Montserrat-Bold"
    if loaded.get("Montserrat-Regular"): HEADING_FONT_REG = "Montserrat-Regular"
    if loaded.get("Inter-Regular"):      BODY_FONT        = "Inter-Regular"
    if loaded.get("Inter-Bold"):         BODY_FONT_BOLD   = "Inter-Bold"

_register_fonts()

# ── Helpers ───────────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

def accent_line(thick=1.5, before=4, after=8):
    return HRFlowable(width="100%", thickness=thick, color=GOLD,
                      spaceBefore=before, spaceAfter=after)

def divider():
    return HRFlowable(width="100%", thickness=0.5, color=MID_GRAY,
                      spaceBefore=6, spaceAfter=6)

def section_header(text):
    style = S("SH_" + text[:8], fontName=HEADING_FONT, fontSize=13, leading=18,
              textColor=CHARCOAL, spaceBefore=18, spaceAfter=4)
    return KeepTogether([Paragraph(text.upper(), style), accent_line()])

def sub_header(text):
    return Paragraph(text, S("Sub_" + text[:8], fontName=HEADING_FONT, fontSize=11,
                              leading=15, textColor=GOLD, spaceBefore=12, spaceAfter=4))

def body(text):
    return Paragraph(text, S("B_" + str(id(text))[-6:], fontName=BODY_FONT, fontSize=10,
                              leading=15, textColor=SLATE))

def bold_body(text):
    return Paragraph(text, S("BB_" + str(id(text))[-6:], fontName=BODY_FONT_BOLD, fontSize=10,
                              leading=15, textColor=CHARCOAL))

def bullet(text, indent=18):
    return Paragraph(
        f"\u2022  {text}",
        S("Bul_" + str(id(text))[-6:], fontName=BODY_FONT, fontSize=10, leading=14,
          textColor=SLATE, leftIndent=indent, spaceBefore=2, spaceAfter=2)
    )

def logo_path():
    p = ASSETS_DIR / "favicon-gold.png"
    return str(p) if p.exists() else None

# ── Header / Footer ──────────────────────────────────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    w, h = letter
    logo = logo_path()
    if logo:
        try:
            canvas.drawImage(logo, 0.65 * inch, h - 0.82 * inch,
                             width=30, height=30, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    canvas.setFont(HEADING_FONT, 10)
    canvas.setFillColor(CHARCOAL)
    canvas.drawString(1.15 * inch, h - 0.62 * inch, COMPANY)
    canvas.setFont(BODY_FONT, 7)
    canvas.setFillColor(DARK_GRAY)
    canvas.drawString(1.15 * inch, h - 0.77 * inch, TAGLINE)
    canvas.setFont(BODY_FONT, 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawRightString(w - 0.65 * inch, h - 0.65 * inch, f"Confidential — {PROPOSAL_DATE}")
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    canvas.line(0.6 * inch, h - 0.92 * inch, w - 0.6 * inch, h - 0.92 * inch)
    canvas.setStrokeColor(MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(0.6 * inch, 0.55 * inch, w - 0.6 * inch, 0.55 * inch)
    canvas.setFont(BODY_FONT, 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(0.65 * inch, 0.38 * inch, WEBSITE)
    canvas.drawCentredString(w / 2, 0.38 * inch, f"Page {doc.page}")
    canvas.drawRightString(w - 0.65 * inch, 0.38 * inch, EMAIL)
    canvas.restoreState()

# ── Table builders ────────────────────────────────────────────────────────────
def dark_table(headers, rows, col_widths=None):
    th_style = S("TH_dt", fontName=BODY_FONT_BOLD, fontSize=9,
                 textColor=GOLD_LIGHT, leading=12)
    td_style = S("TD_dt", fontName=BODY_FONT, fontSize=9,
                 textColor=SLATE, leading=13)
    data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), td_style) if not isinstance(c, Paragraph) else c
                     for c in row])
    if col_widths is None:
        col_widths = [6.5 * inch / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  CHARCOAL),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  GOLD_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(1, len(data)):
        bg = WHITE if i % 2 == 1 else LIGHT_GRAY
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t

def price_card(label, price, note=""):
    label_p = Paragraph(label, S("PL_" + label[:6], fontName=HEADING_FONT, fontSize=11,
                                  textColor=WHITE, leading=15, alignment=TA_CENTER))
    price_p = Paragraph(price, S("PP_" + label[:6], fontName=HEADING_FONT, fontSize=22,
                                  textColor=GOLD, leading=28, alignment=TA_CENTER))
    rows = [[label_p], [price_p]]
    if note:
        rows.append([Paragraph(note, S("PN_" + label[:6], fontName=BODY_FONT, fontSize=8,
                                        textColor=TEXT_MUTED, leading=11, alignment=TA_CENTER))])
    t = Table(rows, colWidths=[2.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
        ("BOX",           (0, 0), (-1, -1), 1.5, GOLD),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    return t

def highlight_box(text):
    data = [[Paragraph(text, S("HB_" + str(id(text))[-6:], fontName=BODY_FONT, fontSize=10,
                                textColor=CHARCOAL, leading=15))]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GOLD_BG),
        ("BOX",           (0, 0), (-1, -1), 2, GOLD),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return t

def dark_highlight_box(text):
    data = [[Paragraph(text, S("DHB_" + str(id(text))[-6:], fontName=BODY_FONT_BOLD, fontSize=10,
                                textColor=GOLD, leading=15, alignment=TA_CENTER))]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CHARCOAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return t

# ── Story ─────────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("PARTNERSHIP PROPOSAL", S("CoverLabel", fontName=HEADING_FONT, fontSize=11,
                                          textColor=GOLD, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(
        "AI Executive Assistant",
        S("CoverTitle", fontName=HEADING_FONT, fontSize=26, leading=32,
          textColor=CHARCOAL, alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        "One System to Run Three Companies",
        S("CoverTitle2", fontName=HEADING_FONT, fontSize=16, leading=22,
          textColor=GOLD, alignment=TA_CENTER, spaceAfter=8)
    ))
    story.append(Paragraph(
        "Grant Construction & Roofing  |  Blue Collar Exits  |  Lead Marketplace",
        S("CoverSub", fontName=HEADING_FONT_REG, fontSize=11, leading=15,
          textColor=DARK_GRAY, alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        f"Prepared for Vince Grant  |  {PROPOSAL_DATE}",
        S("CoverMeta", fontName=BODY_FONT, fontSize=9, leading=12,
          textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.15 * inch))
    story.append(accent_line(thick=2, before=4, after=4))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(
        f"Prepared by {COMPANY}",
        S("CoverTag", fontName=HEADING_FONT_REG, fontSize=9,
          textColor=GOLD, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.3 * inch))

    # ── 1. The Problem ───────────────────────────────────────────────────────
    story.append(section_header("1. The Problem"))
    story.append(body(
        "You're running three companies. Every morning you wake up to emails from contractors, "
        "deal inquiries from business owners looking to sell, roofing leads that need follow-up, "
        "and a calendar that's pulling you in three directions. You're the bottleneck — not because "
        "you're slow, but because there's only one of you."
    ))
    story.append(Spacer(1, 8))
    story.append(body(
        "The daily tasks that eat your time aren't hard — they're repetitive. Triaging emails, "
        "following up with leads, scheduling calls, checking on deals, reviewing new contractor "
        "applications. Any one of these is five minutes. Across three businesses, it's half your day."
    ))
    story.append(Spacer(1, 10))
    story.append(highlight_box(
        "<b>The goal:</b> An AI system that handles the repetitive daily operations across all three "
        "businesses — so you can focus on closing deals, growing the marketplace, and running crews, "
        "not managing inboxes and calendars."
    ))
    story.append(Spacer(1, 0.1 * inch))

    # ── 2. What the AI Assistant Does ────────────────────────────────────────
    story.append(section_header("2. What Your AI Assistant Does"))
    story.append(body(
        "One unified system that knows about all three businesses and handles daily operations "
        "across each. It doesn't replace your judgment — it gives you the information you need "
        "faster and handles the tasks that don't require your judgment at all."
    ))
    story.append(Spacer(1, 10))

    # -- Morning Briefing
    story.append(sub_header("Daily Morning Briefing"))
    story.append(body(
        "Every morning, delivered to your phone by text or email — before you finish your coffee:"
    ))
    story.append(Spacer(1, 4))
    briefing_items = [
        "<b>Grant Roofs:</b> Today's scheduled jobs, any customer follow-ups due, new leads overnight, crew schedule conflicts",
        "<b>Blue Collar Exits:</b> Active deal pipeline status, new seller inquiries, investor responses, upcoming calls",
        "<b>Marketplace:</b> Overnight lead volume, contractor sign-ups, revenue snapshot, any refund requests pending",
        "<b>Calendar:</b> Today's meetings across all three businesses, prep notes for each call",
        "<b>Priority inbox:</b> Emails that actually need your attention — everything else is already handled",
    ]
    for item in briefing_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    # -- Email Management
    story.append(sub_header("Intelligent Email Management"))
    story.append(body(
        "The assistant monitors your email across all three businesses and takes action:"
    ))
    story.append(Spacer(1, 4))
    email_items = [
        "Categorizes every email by business and urgency — you see what matters first",
        "Drafts responses for routine inquiries (estimates, scheduling, deal questions) — you approve with one tap",
        "Auto-routes leads to the right pipeline (roofing lead vs. business seller vs. marketplace contractor)",
        "Flags time-sensitive items immediately via SMS — don't wait until you check email",
        "Archives and organizes everything — searchable history across all three businesses",
    ]
    for item in email_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    # -- Calendar & Scheduling
    story.append(sub_header("Calendar & Scheduling Automation"))
    cal_items = [
        "Manages one unified calendar across all three businesses with color-coded context",
        "Auto-schedules follow-up calls when deals hit milestones (Blue Collar Exits pipeline)",
        "Sends appointment confirmations and reminders to customers (Grant Roofs)",
        "Blocks time for crew site visits, deal meetings, and marketplace reviews",
        "Reschedules conflicts automatically based on priority rules you set",
    ]
    for item in cal_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    # -- Business-specific
    story.append(PageBreak())
    story.append(section_header("3. Business-Specific Automation"))

    story.append(dark_highlight_box(
        "Grant Construction & Roofing"
    ))
    story.append(Spacer(1, 8))
    grant_items = [
        "<b>Lead follow-up:</b> New roofing inquiries get an immediate response with scheduling link — no leads go cold overnight",
        "<b>Estimate follow-up:</b> Automatically follows up on sent estimates at day 2, 5, and 10 — stops when they respond",
        "<b>Review requests:</b> After job completion, sends Google review request to homeowner — builds your reviews on autopilot",
        "<b>Crew scheduling alerts:</b> Weather-based job rescheduling notifications to you and crew leads",
        "<b>Insurance claim tracking:</b> Monitors claim status and alerts you when action is needed",
    ]
    for item in grant_items:
        story.append(bullet(item))
    story.append(Spacer(1, 14))

    story.append(dark_highlight_box(
        "Blue Collar Exits"
    ))
    story.append(Spacer(1, 8))
    bce_items = [
        "<b>Deal pipeline management:</b> Tracks every deal stage — from initial inquiry to close — surfaces what needs your attention today",
        "<b>Seller outreach follow-up:</b> Automated follow-up sequences for business owners who inquired but haven't committed",
        "<b>Investor matching alerts:</b> When a new seller profile matches an investor's criteria, you're notified immediately",
        "<b>Document tracking:</b> Monitors NDA, LOI, and due diligence timelines — alerts before deadlines",
        "<b>Meeting prep:</b> Before every seller or investor call, the assistant pulls deal history, financials discussed, and open items into a one-page brief",
    ]
    for item in bce_items:
        story.append(bullet(item))
    story.append(Spacer(1, 14))

    story.append(dark_highlight_box(
        "Roofing Lead Marketplace"
    ))
    story.append(Spacer(1, 8))
    marketplace_items = [
        "<b>Daily revenue and lead volume dashboard:</b> Delivered in your morning briefing — no logging in required",
        "<b>Contractor onboarding:</b> New sign-up notifications with auto-generated welcome sequences",
        "<b>Refund/dispute triage:</b> Reviews refund requests against lead data and recommends approve/deny before you touch it",
        "<b>Lead quality monitoring:</b> Flags anomalies in lead quality or conversion rates before they become problems",
        "<b>Growth metrics:</b> Weekly summary of contractor retention, territory fill rates, and revenue per lead trends",
    ]
    for item in marketplace_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    # ── 4. How It Works ──────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("4. How It Works — Under the Hood"))

    story.append(body(
        "This isn't a chatbot. It's an automation system that runs 24/7 in the background "
        "and surfaces what you need, when you need it. Here's the architecture:"
    ))
    story.append(Spacer(1, 10))

    arch_rows = [
        ["Email Integration", "Connects to your Gmail/Outlook for all three businesses. Reads, categorizes, drafts, and sends."],
        ["Calendar Sync", "Google Calendar or Outlook — manages scheduling, conflicts, and reminders across all businesses."],
        ["CRM / Pipeline", "Tracks leads (Grant Roofs), deals (Blue Collar Exits), and contractors (Marketplace) in one unified view."],
        ["SMS / Notifications", "Priority alerts via text message. Morning briefing delivered to your phone."],
        ["AI Engine", "Understands context across all three businesses. Knows that a contractor inquiry might relate to both Grant Roofs and the marketplace."],
        ["Automation Layer", "n8n workflow engine — triggers, follow-ups, and sequences run automatically without human intervention."],
        ["Dashboard", "Web-based command center you can check from your phone. One view, three businesses."],
    ]
    story.append(dark_table(
        ["Component", "What It Does"],
        arch_rows,
        col_widths=[1.8 * inch, 4.7 * inch]
    ))
    story.append(Spacer(1, 12))

    story.append(highlight_box(
        "<b>Key point:</b> You interact with it through your normal tools — email, text, phone, calendar. "
        "There's no new app to learn. The AI works in the background and surfaces information through "
        "the channels you already use. The dashboard is there when you want the full picture, but "
        "everything critical comes to you."
    ))

    # ── 5. Timeline ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.15 * inch))
    story.append(section_header("5. Sprint Timeline — 3 Weeks to Running"))

    story.append(body(
        "We build this in layers. Week 1 you're already getting value. By week 3, the full "
        "system is running across all three businesses."
    ))
    story.append(Spacer(1, 10))

    timeline_rows = [
        ["Week 1", "Foundation + Morning Briefing",
         "Email integration across all 3 businesses, calendar sync, daily morning briefing "
         "delivered to your phone, priority inbox triage, SMS alerts for urgent items"],
        ["Week 2", "Business Automation",
         "Grant Roofs: lead follow-up + estimate sequences + review requests. "
         "Blue Collar Exits: deal pipeline tracking + follow-up automation + meeting prep briefs. "
         "Auto-draft email responses across all businesses"],
        ["Week 3", "Intelligence + Dashboard",
         "Marketplace monitoring + contractor onboarding automation. Cross-business dashboard. "
         "Refund triage. Growth metrics. Calendar automation with conflict resolution. Full system live."],
    ]
    story.append(dark_table(
        ["Week", "Focus", "What Ships"],
        timeline_rows,
        col_widths=[0.8 * inch, 1.6 * inch, 4.1 * inch]
    ))
    story.append(Spacer(1, 12))

    story.append(highlight_box(
        "<b>After week 1</b>, you wake up to a morning briefing covering all three businesses. "
        "That alone changes your day. Everything after that is layering on more automation."
    ))

    # ── 6. Investment ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("6. Investment"))

    story.append(body(
        "Same philosophy as the marketplace proposal — I'm pricing this to get us moving, "
        "not to maximize the invoice. The ongoing partnership is where this makes sense for both of us."
    ))
    story.append(Spacer(1, 14))

    cards = Table(
        [[price_card("Setup\nBuild + Launch", "$5,000", "3 weeks"),
          price_card("Monthly\nPartnership", "$1,200/mo", "Ongoing"),
          price_card("Year 1\nTotal Investment", "$18,400", "Setup + 12 months")]],
        colWidths=[2.1 * inch, 2.1 * inch, 2.1 * inch],
        hAlign="CENTER"
    )
    cards.setStyle(TableStyle([
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(cards)
    story.append(Spacer(1, 16))

    story.append(sub_header("What the Setup ($5,000) Covers"))
    setup_items = [
        "Email integration across all three businesses (Gmail/Outlook)",
        "Calendar sync and unified scheduling system",
        "Morning briefing engine — daily digest delivered to your phone",
        "Grant Roofs: lead follow-up, estimate sequences, review request automation",
        "Blue Collar Exits: deal pipeline tracking, follow-up sequences, meeting prep",
        "Marketplace: revenue dashboard, contractor onboarding, refund triage",
        "SMS notification system for priority alerts",
        "Web dashboard — one view, three businesses",
        "Full deployment and testing across all businesses",
    ]
    for item in setup_items:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    story.append(sub_header("What the Monthly ($1,200/mo) Covers"))
    monthly_items = [
        "System monitoring — if something breaks, I fix it before you notice",
        "New automation additions as your businesses evolve (new follow-up sequences, new pipelines, new integrations)",
        "AI model updates and improvements to email drafting, lead scoring, and prioritization",
        "Infrastructure costs (hosting, email APIs, SMS credits, AI processing)",
        "Direct line to me — not a ticket queue. Phone, text, or email.",
        "Cancel anytime with 30 days notice — you keep everything",
    ]
    for item in monthly_items:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    story.append(sub_header("Payment Structure"))
    payment_items = [
        "<b>Setup:</b> $2,500 to start, $2,500 when the system is live and you've used it for a week",
        "<b>Monthly:</b> $1,200/mo — first month starts after the system is fully deployed",
        "<b>No long-term contract:</b> Month-to-month. The system earns its keep or you cancel.",
    ]
    for item in payment_items:
        story.append(bullet(item))
    story.append(Spacer(1, 14))

    story.append(highlight_box(
        "<b>The math:</b> If this system saves you 2 hours a day across three businesses — "
        "and it will save more than that — that's 40+ hours a month you're getting back. "
        "At $1,200/mo, that's $30/hour for your time back. The real value isn't the hours though — "
        "it's the leads that don't go cold, the follow-ups that don't get missed, and the deals "
        "that don't slip because you were buried in the wrong inbox."
    ))

    # ── 7. Why This Works ────────────────────────────────────────────────────
    story.append(Spacer(1, 0.15 * inch))
    story.append(section_header("7. Why I Know This Works"))

    story.append(body(
        "I'm not pitching you something theoretical. I built this system for myself — I run "
        "multiple business lines and the AI assistant I use every day is the foundation of "
        "what I'm proposing here. Morning briefings, email triage, pipeline tracking, automated "
        "follow-ups — it's all running in production, right now, for my own businesses."
    ))
    story.append(Spacer(1, 8))
    story.append(body(
        "What I'm proposing is adapting that proven system to your three businesses. The "
        "infrastructure exists. The patterns are tested. The hardest part — figuring out what "
        "works and what doesn't — is already done. That's why the timeline is 3 weeks instead of 3 months."
    ))
    story.append(Spacer(1, 10))

    story.append(dark_highlight_box(
        "\"I built this for myself first. Now I'm offering to build it for you.\""
    ))

    # ── 8. Next Steps ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))
    story.append(section_header("8. Next Steps"))

    story.append(body(
        "Here's how we get started:"
    ))
    story.append(Spacer(1, 6))
    steps = [
        "<b>30-minute walkthrough call</b> — I'll show you the system running on my own businesses so you can see exactly what you'd be getting. We'll map out your specific workflows across all three companies.",
        "<b>I build a custom integration plan</b> — within 48 hours of the call, you'll have a detailed map of every automation, every email integration, and every workflow, tailored to Grant Roofs, Blue Collar Exits, and the marketplace.",
        "<b>$2,500 deposit and we start building</b> — I begin connecting to your systems in week 1. By day 7, you're getting your first morning briefing.",
        "<b>Full system live in 3 weeks</b> — all three businesses automated. Second payment of $2,500. Monthly partnership begins.",
    ]
    for i, step in enumerate(steps, 1):
        story.append(bullet(f"Step {i}: {step}"))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(highlight_box(
        f"<b>Ready to see it in action?</b> Let's get on a call and I'll walk you through the live system. "
        f"<br/><br/>Schedule here: {CALENDLY}<br/>"
        f"Or just text/call me: {PHONE}"
    ))

    # ── Contact footer ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(accent_line(thick=2))
    story.append(Paragraph(
        "William Marceau  |  Marceau Solutions",
        S("CF1", fontName=HEADING_FONT, fontSize=11, textColor=CHARCOAL, alignment=TA_CENTER, leading=15)
    ))
    story.append(Paragraph(
        f"{EMAIL}  |  {PHONE}  |  {WEBSITE}",
        S("CF2", fontName=BODY_FONT, fontSize=9, textColor=DARK_GRAY, alignment=TA_CENTER, leading=13)
    ))
    story.append(Paragraph(
        f"Schedule a call: {CALENDLY}",
        S("CF3", fontName=BODY_FONT, fontSize=9, textColor=GOLD, alignment=TA_CENTER, leading=13)
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        TAGLINE,
        S("CFTag", fontName=HEADING_FONT_REG, fontSize=8, textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))

    return story


# ── PDF generation ────────────────────────────────────────────────────────────
def generate_pdf(output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=1.15 * inch,
        bottomMargin=0.85 * inch,
        title="AI Executive Assistant Proposal — Marceau Solutions",
        author="Marceau Solutions",
        subject="AI Personal Assistant for Vince Grant — Three Business Automation",
    )
    story = build_story()
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"[PDF] Generated: {output_path}")
    return output_path


# ── Email delivery ────────────────────────────────────────────────────────────
def send_email(pdf_path: str, to_addr: str, also_to: str = None) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_user, smtp_pass]):
        print("[EMAIL] SMTP credentials missing — skipping.")
        return False

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = "AI Assistant for Your Three Businesses — Proposal"

    body_text = """Vince,

Following up on the marketplace proposal with something else I think you'll want to see.

I know you're running Grant Roofs, Blue Collar Exits, and building the marketplace all at once. That's three inboxes, three pipelines, and one calendar trying to hold it all together. I put together a proposal for an AI assistant system that handles the repetitive daily operations across all three — email triage, lead follow-up, deal pipeline tracking, morning briefings, the works.

The short version: I can have a system running in 3 weeks that wakes you up every morning with a briefing covering all three businesses, auto-follows up on roofing leads and estimates, tracks your Blue Collar Exits deal pipeline, and monitors the marketplace — all delivered to your phone.

I built this system for myself first, so this isn't theoretical. I'm adapting what's already working in production.

Proposal is attached. Happy to get on a call and show you the live system running on my own businesses so you can see exactly what it looks like.

William Marceau
Marceau Solutions
(239) 398-5676
wmarceau@marceausolutions.com
marceausolutions.com
"""

    msg.attach(MIMEText(body_text, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition",
                    'attachment; filename="Marceau-Solutions-AI-Assistant-Proposal.pdf"')
    msg.attach(part)

    recipients = [to_addr]
    if also_to:
        recipients.append(also_to)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipients, msg.as_string())
        print(f"[EMAIL] Sent to {', '.join(recipients)}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    OUTPUT = (
        "/Users/williammarceaujr./dev-sandbox/"
        "projects/marceau-solutions/digital/proposals/"
        "vince-ai-assistant-proposal.pdf"
    )

    pdf_path = generate_pdf(OUTPUT)

    # Send to Vince
    vince_ok = send_email(pdf_path, "vince@grantroofs.com")
    # Also send copy to William
    william_ok = send_email(pdf_path, "wmarceau@marceausolutions.com")

    print()
    print("=" * 60)
    print("DELIVERY SUMMARY")
    print("=" * 60)
    print(f"PDF saved:     {pdf_path}")
    print(f"Sent to Vince: {'YES — vince@grantroofs.com' if vince_ok else 'FAILED'}")
    print(f"Copy to William: {'YES — wmarceau@marceausolutions.com' if william_ok else 'FAILED'}")
    print()
    print("Pricing:")
    print("  Setup:   $5,000 (3 weeks)")
    print("  Monthly: $1,200/mo (ongoing)")
    print("  Year 1:  $18,400 total")
    print("=" * 60)
