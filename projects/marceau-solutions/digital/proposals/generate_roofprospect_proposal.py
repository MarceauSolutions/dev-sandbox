#!/usr/bin/env python3
"""
Generate branded RoofProspect-equivalent platform proposal PDF.

Output: projects/marceau-solutions/digital/proposals/roofprospect-equivalent-proposal.pdf
"""

import os
import sys
import smtplib
import ssl
from pathlib import Path
from datetime import datetime
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# Ensure execution/ is importable
ROOT = Path(__file__).parent.parent.parent.parent.parent  # dev-sandbox root
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
    """Convenience: build a ParagraphStyle."""
    return ParagraphStyle(name, **kw)

def accent_line(thick=1.5, before=4, after=8):
    return HRFlowable(width="100%", thickness=thick, color=GOLD,
                      spaceBefore=before, spaceAfter=after)

def divider():
    return HRFlowable(width="100%", thickness=0.5, color=MID_GRAY,
                      spaceBefore=6, spaceAfter=6)

def section_header(text):
    style = S("SH", fontName=HEADING_FONT, fontSize=13, leading=18,
              textColor=CHARCOAL, spaceBefore=18, spaceAfter=4)
    return KeepTogether([Paragraph(text.upper(), style), accent_line()])

def sub_header(text):
    return Paragraph(text, S("Sub", fontName=HEADING_FONT, fontSize=11,
                              leading=15, textColor=GOLD, spaceBefore=12, spaceAfter=4))

def body(text):
    return Paragraph(text, S("B", fontName=BODY_FONT, fontSize=10,
                              leading=15, textColor=SLATE))

def bold_body(text):
    return Paragraph(text, S("BB", fontName=BODY_FONT_BOLD, fontSize=10,
                              leading=15, textColor=CHARCOAL))

def bullet(text, indent=18):
    return Paragraph(
        f"\u2022  {text}",
        S("Bul", fontName=BODY_FONT, fontSize=10, leading=14,
          textColor=SLATE, leftIndent=indent, spaceBefore=2, spaceAfter=2)
    )

def logo_path():
    p = ASSETS_DIR / "favicon-gold.png"
    return str(p) if p.exists() else None

# ── Header / Footer callbacks ─────────────────────────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    w, h = letter

    # Header: logo + brand name + tagline
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

    # Gold accent line under header
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    canvas.line(0.6 * inch, h - 0.92 * inch, w - 0.6 * inch, h - 0.92 * inch)

    # Footer
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
    """Charcoal header, alternating rows."""
    th_style = S("TH", fontName=BODY_FONT_BOLD, fontSize=9,
                 textColor=GOLD_LIGHT, leading=12)
    td_style = S("TD", fontName=BODY_FONT, fontSize=9,
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
    """A gold-accented pricing card."""
    label_p = Paragraph(label, S("PL", fontName=HEADING_FONT, fontSize=11,
                                  textColor=WHITE, leading=15, alignment=TA_CENTER))
    price_p = Paragraph(price, S("PP", fontName=HEADING_FONT, fontSize=22,
                                  textColor=GOLD, leading=28, alignment=TA_CENTER))
    rows = [[label_p], [price_p]]
    if note:
        rows.append([Paragraph(note, S("PN", fontName=BODY_FONT, fontSize=8,
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
    """Gold-bordered highlight box (for guarantees, callouts)."""
    data = [[Paragraph(text, S("HB", fontName=BODY_FONT, fontSize=10,
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
    """Dark card with gold text — for strong callouts."""
    data = [[Paragraph(text, S("DHB", fontName=BODY_FONT_BOLD, fontSize=10,
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

# ── Story builder ─────────────────────────────────────────────────────────────
def build_story():
    story = []

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph("PARTNERSHIP PROPOSAL", S("Label", fontName=HEADING_FONT, fontSize=11,
                                          textColor=GOLD, alignment=TA_CENTER, spaceAfter=6)))

    story.append(Paragraph(
        "Your Roofing Lead Marketplace — Built to Launch",
        S("CoverTitle", fontName=HEADING_FONT, fontSize=24, leading=30,
          textColor=CHARCOAL, alignment=TA_CENTER, spaceAfter=8)
    ))
    story.append(Paragraph(
        "AI-Powered Scoring · Real-Time Bidding · Contractor Dashboards",
        S("CoverSub", fontName=HEADING_FONT_REG, fontSize=12, leading=16,
          textColor=DARK_GRAY, alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        f"Prepared by Marceau Solutions  |  {PROPOSAL_DATE}",
        S("CoverMeta", fontName=BODY_FONT, fontSize=9, leading=12,
          textColor=TEXT_MUTED, alignment=TA_CENTER)
    ))

    story.append(Spacer(1, 0.15 * inch))
    story.append(accent_line(thick=2, before=4, after=4))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(
        TAGLINE,
        S("CoverTag", fontName=HEADING_FONT_REG, fontSize=9,
          textColor=GOLD, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.3 * inch))

    # ── 1. Why This Proposal Is Different ────────────────────────────────────
    story.append(section_header("1. Straight Talk"))
    story.append(body(
        "I'm not going to pitch you like a typical agency. Here's where I'm at:"
    ))
    story.append(Spacer(1, 8))
    story.append(body(
        "I see what you're building. A roofing lead marketplace with AI scoring and "
        "real-time bidding is not a small idea — it's infrastructure for an industry. "
        "Companies like this, when they hit, become the backbone that everyone else runs on. "
        "I don't want to just build your platform and send an invoice. I want to be the guy "
        "who helped build it from the ground floor."
    ))
    story.append(Spacer(1, 8))
    story.append(body(
        "That means I'm going to be honest with you about what this takes, price it in a way "
        "that makes sense for where you are right now, and earn your trust by delivering — not "
        "by overselling. If this thing grows the way I think it can, we both win."
    ))
    story.append(Spacer(1, 10))
    story.append(highlight_box(
        "<b>My commitment:</b> I'm pricing this to get us moving — not to maximize my invoice. "
        "You'll see exactly what you're paying for at every step, and you'll never wonder if "
        "I'm padding hours or inflating scope. If something doesn't need to be built yet, I'll "
        "tell you. If there's a faster way, we'll take it."
    ))
    story.append(Spacer(1, 0.1 * inch))

    # ── 2. What We're Building ───────────────────────────────────────────────
    story.append(section_header("2. What We're Building"))
    story.append(body(
        "Five integrated subsystems that together form a complete lead marketplace. "
        "We build them in phases so you're generating revenue before we finish the last one."
    ))
    story.append(Spacer(1, 10))

    subsystems = [
        (
            "Lead Ingestion Pipeline",
            [
                "Homeowner-facing web forms and landing pages",
                "Call center integrations via webhook/API",
                "Partner referral APIs for third-party lead sources",
                "Storm damage detection feeds (NOAA, weather event APIs)",
                "Manual entry for your team to inject leads directly",
            ]
        ),
        (
            "AI Scoring Engine",
            [
                "Satellite imagery analysis (roof condition, age, material)",
                "Storm data correlation (proximity, severity)",
                "Property records lookup (ownership, value, square footage)",
                "Insurance claim signal detection",
                "0–100 appointment score so contractors bid with confidence",
            ]
        ),
        (
            "Real-Time Bidding System",
            [
                "Live bidding with instant UI updates",
                "Auto-bid engine — set it and forget it",
                "Buy-now pricing for contractors who want immediate lock",
                "Territory locks at zip code and county level",
                "Full bid history and audit trail",
            ]
        ),
        (
            "Contractor Dashboard",
            [
                "Account management and profile setup",
                "Active bids, won leads, and lead history",
                "Territory selection and auto-bid configuration",
                "Analytics: win rate, cost-per-lead, ROI by territory",
                "Notification preferences (SMS, email, push)",
                "Stripe self-service billing and subscription management",
            ]
        ),
        (
            "Admin Platform",
            [
                "Lead review and approval queue",
                "Refund workflow with dispute management",
                "Contractor management (approve, suspend, tier changes)",
                "Revenue tracking and payout reporting",
                "System analytics and health monitoring",
            ]
        ),
    ]

    for title, bullets in subsystems:
        story.append(sub_header(title))
        for b in bullets:
            story.append(bullet(b))
        story.append(Spacer(1, 6))

    # ── 3. Sprint Timeline ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("3. Sprint Timeline — 30 Days to Live"))

    story.append(dark_highlight_box(
        "Goal: Contractors bidding on real leads within 30 days"
    ))
    story.append(Spacer(1, 10))

    story.append(body(
        "I'm not going to give you a 4-month timeline. You're moving fast and the market "
        "won't wait. Here's the aggressive schedule I'll commit to — it's tight, but it's "
        "what I'd want if I were in your shoes."
    ))
    story.append(Spacer(1, 10))

    story.append(sub_header("How We Move This Fast"))
    stack_items = [
        "Supabase handles auth, database, and real-time subscriptions out of the box — no building from scratch",
        "n8n workflow automation builds lead ingestion pipelines in days, not weeks",
        "Stripe integration for subscriptions + per-lead billing — already proven in production",
        "AI-assisted development (not shortcuts — real architecture, 2-3x faster execution)",
        "Existing SMS/email infrastructure via Twilio and SES — plug and play",
    ]
    for item in stack_items:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    story.append(sub_header("Week-by-Week Delivery"))
    timeline_rows = [
        ["Week 1",  "Foundation",       "Auth, database schema, contractor dashboard scaffold, Stripe billing wired up"],
        ["Week 2",  "Lead Engine",      "Lead ingestion (web forms + manual entry), rule-based scoring (0–100), admin panel"],
        ["Week 3",  "Marketplace Core", "Bidding system (manual + auto-bid), territory locks, buy-now, real-time notifications"],
        ["Week 4",  "Polish & Launch",  "QA, mobile responsive, load testing, production deploy — you're live"],
    ]
    story.append(dark_table(
        ["Week", "Focus", "What Ships"],
        timeline_rows,
        col_widths=[0.8 * inch, 1.3 * inch, 4.4 * inch]
    ))
    story.append(Spacer(1, 12))

    story.append(sub_header("Phase 2 — AI Scoring (Weeks 5–8, After Launch)"))
    story.append(body(
        "Once you're live and generating revenue with rule-based scoring, we layer on the "
        "AI scoring engine — satellite imagery, storm data, property records. This is the "
        "competitive moat, but it doesn't need to gate your launch."
    ))
    story.append(Spacer(1, 6))
    phase2_items = [
        "Satellite imagery API integration (Google/Nearmap)",
        "Storm data feeds and severity correlation",
        "Property records API (ATTOM/CoreLogic)",
        "ML scoring model — replaces rule-based with true AI scoring",
    ]
    for item in phase2_items:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    story.append(highlight_box(
        "<b>Why this order matters:</b> You start collecting revenue in 30 days with rule-based "
        "scoring. Contractors don't know or care whether the score comes from rules or ML — they "
        "care that it's accurate and they're getting exclusive leads. We upgrade the engine under "
        "the hood while the business is already running."
    ))

    # ── 4. Investment ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("4. Investment — Built for Where You Are Now"))

    story.append(body(
        "I've structured this so the upfront number doesn't slow us down. You're in "
        "growth mode and profitable by month two — I don't need to front-load the cost. "
        "I'd rather get this built, prove the value, and grow together."
    ))
    story.append(Spacer(1, 14))

    # Price cards row — partnership pricing
    cards = Table(
        [[price_card("Phase 1\nMVP Launch", "$8,500", "4 weeks to live"),
          price_card("Phase 2\nAI Scoring", "$6,500", "Weeks 5–8"),
          price_card("Ongoing\nPartnership", "$1,500/mo", "Maintenance + growth")]],
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

    # Phase 1 detail
    story.append(sub_header("Phase 1 — MVP Launch  |  $8,500  |  4 Weeks"))
    story.append(body(
        "Everything you need to go live and start generating revenue:"
    ))
    story.append(Spacer(1, 4))
    option_a = [
        "Contractor auth, profiles, and self-service dashboards",
        "Lead ingestion: web forms, manual entry, partner webhook API",
        "Rule-based scoring engine (0–100 based on property data, location, storm history)",
        "Real-time bidding system — manual bids + auto-bid engine",
        "Territory locks at zip code and county level",
        "Stripe billing: $87/mo subscription + per-lead charges ($75 auction / $149+ buy-now)",
        "SMS and email notifications (new leads, outbid alerts, win confirmations)",
        "Full admin panel: lead review, refunds, contractor management, revenue dashboard",
        "Production deployment on your domain — fully live",
    ]
    for item in option_a:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    # Phase 2 detail
    story.append(sub_header("Phase 2 — AI Scoring Engine  |  $6,500  |  Weeks 5–8"))
    story.append(body(
        "The competitive moat — layered on after you're already live and earning:"
    ))
    story.append(Spacer(1, 4))
    option_b = [
        "Satellite imagery API: roof condition, age, material analysis",
        "Storm data correlation: event proximity, severity scoring",
        "Property records API: ownership, value, insurance signals",
        "ML-powered scoring model replaces rule-based engine",
        "Advanced analytics: ROI by territory, lead quality trends",
    ]
    for item in option_b:
        story.append(bullet(item))
    story.append(Spacer(1, 12))

    # Ongoing
    story.append(sub_header("Ongoing Partnership  |  $1,500/mo"))
    story.append(body(
        "After launch, I stay on as your technical partner — not just a maintenance vendor:"
    ))
    story.append(Spacer(1, 4))
    ongoing_items = [
        "Bug fixes, updates, and performance optimization",
        "New feature development as the business scales",
        "Infrastructure management and monitoring",
        "Priority response — direct line, not a ticket queue",
    ]
    for item in ongoing_items:
        story.append(bullet(item))
    story.append(Spacer(1, 14))

    # Total cost summary
    story.append(highlight_box(
        "<b>Total to full platform with AI scoring:</b> $15,000 over 8 weeks — then $1,500/mo ongoing. "
        "Compare that to $50–80K from an agency that takes 4–5 months and disappears after delivery."
        "<br/><br/>"
        "<b>Third-party API costs</b> (you pay directly — full transparency):<br/>"
        "• Hosting (Supabase + deployment): ~$50–200/mo<br/>"
        "• Satellite imagery API: ~$500–1,500/mo (Phase 2 only, scales with volume)<br/>"
        "• Property records API: ~$300–800/mo (Phase 2 only)<br/>"
        "• Storm data: Free (NOAA) to $200/mo (premium feeds)"
    ))

    # ── 5. Why I'm Doing It This Way ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("5. Why I'm Pricing It This Way"))

    story.append(body(
        "I want to be transparent about why this is priced well below market rate:"
    ))
    story.append(Spacer(1, 10))

    why_items = [
        "<b>I believe in what you're building.</b> A roofing lead marketplace with AI scoring "
        "and exclusive territory bidding is the kind of platform that becomes essential infrastructure. "
        "I'd rather be part of that story early than charge top dollar and be forgotten.",

        "<b>I'm investing in the relationship, not the invoice.</b> If this platform takes off — and "
        "the early signs say it will — the ongoing partnership is worth more to me than a one-time "
        "payout. I'm pricing Phase 1 to remove friction, not to leave money on the table.",

        "<b>I want to earn your trust, not buy it.</b> You'll see working software every week. "
        "You'll have full source code access from day one. If at any point you feel like this isn't "
        "working, you own everything we've built and can walk away. No lock-in, no hostage code.",

        "<b>I'm building my portfolio on real platforms, not landing pages.</b> A system like this — "
        "real-time bidding, AI scoring, Stripe billing at scale — that's the kind of work that "
        "defines a company. I'd rather have one client with a platform like this than ten clients "
        "with brochure websites.",
    ]
    for item in why_items:
        story.append(bullet(item))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(dark_highlight_box(
        "\"I'm not here to take advantage of the opportunity. I'm here to earn my seat at the table.\""
    ))

    # ── 6. How We Work Together ──────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))
    story.append(section_header("6. How We Work Together"))

    story.append(sub_header("Communication"))
    comm_items = [
        "Direct line to me — phone, text, or email. No middlemen.",
        "Weekly demo of what shipped that week — you see it running, not in a slide deck",
        "Shared project board so you always know exactly where we are",
    ]
    for item in comm_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    story.append(sub_header("Payment Structure"))
    story.append(body(
        "Structured to keep risk low for both of us:"
    ))
    story.append(Spacer(1, 4))
    payment_items = [
        "<b>Phase 1:</b> $4,250 to start → $4,250 when you're live (50/50 split)",
        "<b>Phase 2:</b> $3,250 to start → $3,250 when AI scoring is deployed",
        "<b>Ongoing:</b> $1,500/mo — cancel anytime with 30 days notice",
    ]
    for item in payment_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    story.append(sub_header("What You Own"))
    own_items = [
        "Full source code — transferred at each milestone payment",
        "All infrastructure accounts (Supabase, Stripe, APIs) in your name",
        "Complete documentation so any developer could pick it up",
        "No proprietary lock-in, no hidden dependencies on me",
    ]
    for item in own_items:
        story.append(bullet(item))
    story.append(Spacer(1, 10))

    story.append(highlight_box(
        "<b>Next step:</b> Let's get on a call and walk through the technical details. "
        "I'll answer every question you have, and if it makes sense for both of us, "
        "we can be building by next week."
        f"<br/><br/>Schedule here: {CALENDLY}"
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
        title="RoofProspect-Equivalent Platform Proposal — Marceau Solutions",
        author="Marceau Solutions",
        subject="Custom Roofing Lead Marketplace Platform Proposal",
    )

    story = build_story()
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"[PDF] Generated: {output_path}")
    return output_path


# ── Email delivery ────────────────────────────────────────────────────────────
def send_email(pdf_path: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    to_addr   = "wmarceau@marceausolutions.com"

    if not all([smtp_host, smtp_user, smtp_pass]):
        print("[EMAIL] SMTP credentials missing — skipping email delivery.")
        return False

    msg = MIMEMultipart()
    msg["From"]    = smtp_user
    msg["To"]      = to_addr
    msg["Subject"] = "Roofing Lead Marketplace — Partnership Proposal"

    body_text = f"""William,

Updated partnership proposal attached — reframed for trust and speed.

Proposal: Roofing Lead Marketplace Platform — Partnership Build
Date: {PROPOSAL_DATE}
Phase 1 MVP: $8,500 (4 weeks to live)
Phase 2 AI Scoring: $6,500 (weeks 5-8)
Ongoing: $1,500/mo partnership retainer
Total platform: $15,000 + $1,500/mo

Ready to send to the client. Review and forward when ready.

— Marceau Solutions Digital Tower
{EMAIL} | {PHONE}
{CALENDLY}
"""

    msg.attach(MIMEText(body_text, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="roofprospect-equivalent-proposal.pdf"'
    )
    msg.attach(part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_addr, msg.as_string())
        print(f"[EMAIL] Sent proposal to {to_addr}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    OUTPUT = (
        "/Users/williammarceaujr./dev-sandbox/"
        "projects/marceau-solutions/digital/proposals/"
        "roofprospect-equivalent-proposal.pdf"
    )

    pdf_path = generate_pdf(OUTPUT)
    email_ok = send_email(pdf_path)

    print()
    print("=" * 60)
    print("DELIVERY SUMMARY")
    print("=" * 60)
    print(f"PDF saved:   {pdf_path}")
    print(f"Email sent:  {'YES — wmarceau@marceausolutions.com' if email_ok else 'FAILED — check SMTP credentials'}")
    print()
    print("Partnership pricing:")
    print("  Phase 1 — $8,500  | MVP Launch     | 4 weeks")
    print("  Phase 2 — $6,500  | AI Scoring     | Weeks 5-8")
    print("  Ongoing — $1,500/mo | Partnership   | Maintenance + growth")
    print(f"  Total platform: $15,000 + $1,500/mo")
    print("=" * 60)
