#!/usr/bin/env python3
"""
Shiloh & William Weekly Shopping List PDF — v4
Key additions:
  - CART CHECKLIST at the top: exact quantities, no ambiguity
  - Organ section rewritten: STAPLE vs ROTATE vs OCCASIONAL, weekly target explicit
  - Protein rotation schedule for variety
  - Detail sections remain as reference below the checklist
"""

import sys
sys.path.insert(0, '/home/clawdbot/dev-sandbox')

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

OUTPUT_PATH = '/home/clawdbot/dev-sandbox/docs/Shiloh_William_Weekly_Shopping_List.pdf'

GOLD        = HexColor("#C9963C")
GOLD_BG     = HexColor("#FDF8EF")
GOLD_DARK   = HexColor("#8B6914")
CHARCOAL    = HexColor("#333333")
DARK_GRAY   = HexColor("#555555")
MID_GRAY    = HexColor("#e2e0d8")
LIGHT_GRAY  = HexColor("#f5f5f0")
SCOPE_BOTH  = HexColor("#1a5276")
SCOPE_DOG   = HexColor("#6c3483")
SCOPE_W     = HexColor("#1e4d2b")
ROTATE_BG   = HexColor("#e8f4fd")   # light blue — rotate rows
ROTATE_HDR  = HexColor("#2471a3")   # blue header for rotate group
MONTHLY_BG  = HexColor("#f0f0f0")   # gray — monthly restock
WARN_BG     = HexColor("#fff8e1")
WARN_BORDER = HexColor("#f5a623")
WHITE       = colors.white

FONTS_DIR = '/home/clawdbot/dev-sandbox/execution/pdf_templates/fonts'


def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('Montserrat-Bold', f'{FONTS_DIR}/Montserrat-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Inter-Regular',   f'{FONTS_DIR}/Inter-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Inter-Bold',      f'{FONTS_DIR}/Inter-Bold.ttf'))
        return 'Montserrat-Bold', 'Inter-Regular', 'Inter-Bold'
    except Exception:
        return 'Helvetica-Bold', 'Helvetica', 'Helvetica-Bold'


def make_styles(bold, regular, bold2):
    return {
        'title':     ParagraphStyle('title',     fontName=bold,    fontSize=22, textColor=WHITE,
                                    alignment=TA_CENTER, spaceAfter=4, leading=26),
        'subtitle':  ParagraphStyle('subtitle',  fontName=regular, fontSize=11, textColor=GOLD,
                                    alignment=TA_CENTER, spaceAfter=2),
        'date':      ParagraphStyle('date',      fontName=regular, fontSize=9,  textColor=MID_GRAY,
                                    alignment=TA_CENTER),
        'section':   ParagraphStyle('section',   fontName=bold,    fontSize=13, textColor=GOLD,
                                    spaceBefore=14, spaceAfter=2, leading=16),
        'subsect':   ParagraphStyle('subsect',   fontName=bold2,   fontSize=10, textColor=CHARCOAL,
                                    spaceBefore=6, spaceAfter=3),
        'body':      ParagraphStyle('body',      fontName=regular, fontSize=9,  textColor=CHARCOAL,
                                    spaceAfter=3, leading=13),
        'note':      ParagraphStyle('note',      fontName=regular, fontSize=8,  textColor=DARK_GRAY,
                                    spaceAfter=2, leading=12),
        'warn':      ParagraphStyle('warn',      fontName=regular, fontSize=8,  textColor=HexColor("#7d4e00"),
                                    spaceAfter=2, leading=12),
        'cell':      ParagraphStyle('cell',      fontName=regular, fontSize=8,  textColor=CHARCOAL,
                                    leading=11, spaceAfter=0),
        'cell_bold': ParagraphStyle('cell_bold', fontName=bold2,   fontSize=8,  textColor=CHARCOAL,
                                    leading=11, spaceAfter=0),
        'cell_hdr':  ParagraphStyle('cell_hdr',  fontName=bold2,   fontSize=8,  textColor=WHITE,
                                    leading=11, spaceAfter=0),
        'cell_hdr2': ParagraphStyle('cell_hdr2', fontName=bold2,   fontSize=8,  textColor=GOLD,
                                    leading=11, spaceAfter=0),
        'cell_blue': ParagraphStyle('cell_blue', fontName=regular, fontSize=8,  textColor=HexColor("#1a3a5c"),
                                    leading=11, spaceAfter=0),
        'cell_blue_hdr': ParagraphStyle('cell_blue_hdr', fontName=bold2, fontSize=8, textColor=WHITE,
                                        leading=11, spaceAfter=0),
        'macro_val': ParagraphStyle('macro_val', fontName=bold,    fontSize=14, textColor=GOLD,
                                    alignment=TA_CENTER, leading=16),
        'macro_lbl': ParagraphStyle('macro_lbl', fontName=regular, fontSize=7,  textColor=MID_GRAY,
                                    alignment=TA_CENTER, leading=9),
        'cart_item': ParagraphStyle('cart_item', fontName=bold2,   fontSize=9,  textColor=CHARCOAL,
                                    leading=12, spaceAfter=0),
        'cart_qty':  ParagraphStyle('cart_qty',  fontName=bold,    fontSize=10, textColor=GOLD_DARK,
                                    alignment=TA_CENTER, leading=12, spaceAfter=0),
        'cart_note': ParagraphStyle('cart_note', fontName=regular, fontSize=7.5, textColor=DARK_GRAY,
                                    leading=10, spaceAfter=0),
    }


S = None


def P(text, style='cell'):
    return Paragraph(str(text), S[style])


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CHARCOAL)
    canvas.rect(0, letter[1] - 0.55*inch, letter[0], 0.55*inch, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(letter[0]/2, letter[1] - 0.33*inch,
                             "MARCEAU SOLUTIONS  |  Embrace the Pain & Defy the Odds")
    canvas.setFillColor(CHARCOAL)
    canvas.rect(0, 0, letter[0], 0.45*inch, fill=1, stroke=0)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(0.5*inch, 0.16*inch, "marceausolutions.com  |  wmarceau@marceausolutions.com")
    canvas.drawRightString(letter[0] - 0.5*inch, 0.16*inch, f"Page {doc.page}")
    canvas.restoreState()


def section_header(number, title):
    return [
        HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=3),
        Paragraph(f"{number}. {title}", S['section']),
    ]


def badge(text, color, width=3.0*inch):
    d = [[Paragraph(text, ParagraphStyle('badge', fontName='Helvetica-Bold', fontSize=8,
                                          textColor=WHITE, alignment=TA_CENTER, leading=10))]]
    t = Table(d, colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), color),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))
    return t


def make_table(rows, col_widths, hdr_bg=CHARCOAL, alt_bg=LIGHT_GRAY):
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  hdr_bg),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, alt_bg]),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('GRID',          (0,0), (-1,-1), 0.4, MID_GRAY),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ]))
    return t


# ═════════════════════════════════════════════════════════════════════════════
def build_pdf():
    global S
    bold, regular, bold2 = register_fonts()
    S = make_styles(bold, regular, bold2)

    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=letter,
        topMargin=0.75*inch, bottomMargin=0.65*inch,
        leftMargin=0.55*inch, rightMargin=0.55*inch,
    )
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    title_rows = [
        [Paragraph("SHILOH & WILLIAM", S['title'])],
        [Paragraph("Weekly Raw + Whole Food Shopping List", S['subtitle'])],
        [Paragraph("Week of May 10, 2026  |  Bonita Springs, FL", S['date'])],
    ]
    title_tbl = Table(title_rows, colWidths=[7.5*inch])
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CHARCOAL),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 0.12*inch))

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_rows = [[
        badge("BOTH — combined qty (William + Shiloh)", SCOPE_BOTH, 2.6*inch),
        badge("SHILOH ONLY — not doubled", SCOPE_DOG, 2.0*inch),
        badge("WILLIAM ONLY", SCOPE_W, 1.5*inch),
        badge("ROTATE — pick one", ROTATE_HDR, 1.4*inch),
    ]]
    legend_tbl = Table(legend_rows, colWidths=[2.7*inch, 2.1*inch, 1.6*inch, 1.1*inch])
    legend_tbl.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 3),
    ]))
    story.append(legend_tbl)
    story.append(Spacer(1, 0.12*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # CART CHECKLIST — PAGE 1 HERO SECTION
    # This is the ONLY section William needs to look at in the store.
    # Everything else in the document is reference/explanation.
    # ══════════════════════════════════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=4))
    story.append(Paragraph("WHAT GOES IN YOUR CART — EXACT QUANTITIES", S['section']))
    story.append(Paragraph(
        "This is the only section you need at the store. "
        "Scroll down for the full detail on why each item is included. "
        "Items marked ROTATE mean you pick <b>one option from that group per week</b> — "
        "not all of them. Organ meats are explained in the rotation note below Shiloh's cart.",
        S['note']
    ))
    story.append(Spacer(1, 0.08*inch))

    # ── SHILOH'S CART ─────────────────────────────────────────────────────────
    story.append(Paragraph("SHILOH'S CART (raw diet, 95 lb GSD, ~17.5 lbs food/week)", S['subsect']))

    CW = [2.8*inch, 0.9*inch, 0.9*inch, 2.9*inch]
    shiloh_rows = [
        # Header
        [P("Item", 'cell_hdr'), P("Qty", 'cell_hdr'),
         P("Frequency", 'cell_hdr'), P("Notes", 'cell_hdr')],

        # ── EVERY WEEK (no decisions needed) ──
        [P("▶ EVERY WEEK", 'cell_hdr'), P("", 'cell_hdr'),
         P("", 'cell_hdr'), P("Buy these every single week — no rotation", 'cell_hdr')],

        [P("Chicken backs (raw bone)"), P("2–3 lbs"), P("Every week"),
         P("Main raw bone source. Soft, digestible, excellent calcium.")],
        [P("Chicken thighs (bone-in, skin-on)"), P("3–4 lbs"), P("Every week"),
         P("Primary muscle meat. High fat for energy. Raw.")],
        [P("Beef liver"), P("0.5 lb"), P("Every week"),
         P("Staple organ. DO NOT exceed 0.5–0.75 lb/week. See organ note below.")],
        [P("Green tripe (raw, unbleached)"), P("1 lb"), P("Every week"),
         P("NOT counted in the organ cap. Buy every week regardless of other organs.")],
        [P("Sardines or mackerel (raw/frozen)"), P("0.75–1 lb"), P("Every week"),
         P("Omega-3 source. Raw or thawed-from-frozen. Canned in water (no salt) also fine.")],
        [P("Eggs (whole, raw)"), P("6–8 eggs"), P("Every week"),
         P("Feed 2 raw eggs 4x/week. Crack over food — yolk + white.")],
        [P("Chicken necks (raw bone)"), P("1 lb"), P("Every week"),
         P("Secondary bone source. Supervise if Shiloh gulps without chewing.")],

        # ── ROTATE WEEKLY (pick one protein) ──
        [P("▶ ROTATE PROTEIN — pick ONE of these per week", 'cell_blue_hdr'),
         P("", 'cell_blue_hdr'), P("", 'cell_blue_hdr'),
         P("Alternate week to week for nutritional variety", 'cell_blue_hdr')],

        [P("  Option A: Ground beef 80/20"), P("2–3 lbs"), P("~2 of 4 weeks"),
         P("Alternate main protein. Higher fat. Raw.")],
        [P("  Option B: Pork shoulder (boneless)"), P("2–3 lbs"), P("~1 of 4 weeks"),
         P("Alternate protein. Good fat-to-protein ratio. Raw.")],
        [P("  Option C: Beef heart"), P("1–1.5 lbs"), P("~1 of 4 weeks"),
         P("Classified as muscle meat (not organ — no cap). High CoQ10. Raw.")],

        # ── ROTATE ORGAN (pick one to pair with liver) ──
        [P("▶ ROTATE ORGAN — pick ONE to pair with liver this week", 'cell_blue_hdr'),
         P("", 'cell_blue_hdr'), P("", 'cell_blue_hdr'),
         P("Liver is always bought. One of these is added to it. NOT all three.", 'cell_blue_hdr')],

        [P("  Option A: Beef or pork kidney"), P("0.25 lb"), P("3 of 4 weeks"),
         P("Most common pairing. Liver + Kidney = standard week.")],
        [P("  Option B: Beef spleen"), P("0.25 lb"), P("1 of 4 weeks"),
         P("Swap in once a month instead of kidney. Higher iron. If unavailable, use kidney.")],

        # ── OCCASIONAL (raw bones for chewing) ──
        [P("▶ OCCASIONAL — add when available"), P("", 'cell_hdr'),
         P("", 'cell_hdr'), P("", 'cell_hdr')],

        [P("Pork ribs (raw, single rib)"), P("1–1.5 lbs"), P("1–2x/month"),
         P("Recreational chew for jaw exercise and dental health. Raw only — never cooked.")],
        [P("Duck necks (if Asian market has them)"), P("0.5–1 lb"), P("When available"),
         P("Higher meat-to-bone ratio than chicken necks. Check Asian market on Bonita Beach Rd.")],
    ]

    # Apply row-level background colors
    shiloh_tbl = Table(shiloh_rows, colWidths=CW, repeatRows=1)
    shiloh_tbl.setStyle(TableStyle([
        # Default
        ('FONTNAME',      (0,0),  (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),  (-1,-1), 8),
        ('TOPPADDING',    (0,0),  (-1,-1), 4),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
        ('LEFTPADDING',   (0,0),  (-1,-1), 6),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 6),
        ('GRID',          (0,0),  (-1,-1), 0.4, MID_GRAY),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
        # Column header row (row 0)
        ('BACKGROUND',    (0,0),  (-1,0),  CHARCOAL),
        # "EVERY WEEK" group header (row 1)
        ('BACKGROUND',    (0,1),  (-1,1),  GOLD),
        ('TEXTCOLOR',     (0,1),  (-1,1),  WHITE),
        # Every-week data rows (rows 2–8)
        ('ROWBACKGROUNDS',(0,2),  (-1,8),  [WHITE, LIGHT_GRAY]),
        # ROTATE PROTEIN header (row 9)
        ('BACKGROUND',    (0,9),  (-1,9),  ROTATE_HDR),
        # Rotate protein data rows (10–12)
        ('BACKGROUND',    (0,10), (-1,12), ROTATE_BG),
        # ROTATE ORGAN header (row 13)
        ('BACKGROUND',    (0,13), (-1,13), ROTATE_HDR),
        # Rotate organ data rows (14–15)
        ('BACKGROUND',    (0,14), (-1,15), ROTATE_BG),
        # OCCASIONAL header (row 16)
        ('BACKGROUND',    (0,16), (-1,16), DARK_GRAY),
        ('TEXTCOLOR',     (0,16), (-1,16), WHITE),
        # Occasional data rows (17–18)
        ('ROWBACKGROUNDS',(0,17), (-1,18), [MONTHLY_BG, MONTHLY_BG]),
    ]))
    story.append(shiloh_tbl)
    story.append(Spacer(1, 0.06*inch))

    # Organ note
    organ_note_tbl = Table([[Paragraph(
        "<b>ORGAN MEAT RULE — read this once:</b> The table above lists Shiloh's organ options in two layers. "
        "(1) <b>Liver is always in your cart</b> — 0.5 lb every week, no exceptions. "
        "(2) <b>Pick ONE organ to pair with it</b> — kidney 3 weeks out of 4, spleen the 4th week. "
        "Do NOT buy liver + kidney + spleen all in the same week. "
        "Your weekly secreting organ total should be <b>~0.75 lb</b> (liver + one rotation organ). "
        "The 1.75 lb maximum in the detail section is the absolute cap — you should be well under it. "
        "(3) <b>Green tripe does NOT count toward the organ cap</b> — it is classified separately "
        "as a digestive supplement. Buy 1 lb every week on top of everything else.",
        S['warn']
    )]], colWidths=[7.5*inch])
    organ_note_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), WARN_BG),
        ('BOX',           (0,0),(-1,-1), 1.5, WARN_BORDER),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(organ_note_tbl)
    story.append(Spacer(1, 0.12*inch))

    # ── WILLIAM'S CART ────────────────────────────────────────────────────────
    story.append(Paragraph("WILLIAM'S CART (carnivore, 175 lb, ~14.5 lbs meat/week)", S['subsect']))
    story.append(Paragraph(
        "Macro targets: 262g protein/day (212g food + 50g whey), 161g fat/day, ~73g carbs/day. "
        "Rotate proteins week to week — same as Shiloh. Buying all options every week is fine "
        "but not required if you're tight on budget; focus on the EVERY WEEK items first.",
        S['note']
    ))
    story.append(Spacer(1, 0.05*inch))

    CW2 = [2.8*inch, 0.9*inch, 0.9*inch, 2.9*inch]
    william_rows = [
        [P("Item", 'cell_hdr'), P("Qty", 'cell_hdr'),
         P("Frequency", 'cell_hdr'), P("Notes", 'cell_hdr')],

        # ── EVERY WEEK ──
        [P("▶ EVERY WEEK", 'cell_hdr'), P("", 'cell_hdr'),
         P("", 'cell_hdr'), P("Buy these every single week", 'cell_hdr')],

        [P("Grass-fed butter (Kerrygold)"), P("1–2 lbs"), P("Every week"),
         P("Cook ALL meat in butter. Add to eggs, vegetables. Core fat source.")],
        [P("Eggs (large)"), P("14–18 eggs"), P("Every week"),
         P("2–3 eggs/day. High-fat yolks are essential for the fat macro. Cook in butter.")],
        [P("Chicken thighs (bone-in, skin-on)"), P("3–4 lbs"), P("Every week"),
         P("Shared with Shiloh — buy combined 6–8 lbs, split at home. William cooks his.")],
        [P("Ground beef 80/20"), P("5–6 lbs"), P("Every week"),
         P("Primary protein. Higher fat 80/20 supports fat macro. Cook in cast iron or broil.")],
        [P("Avocado"), P("4–5"), P("Every week"),
         P("~21g fat each. 1/day with a meal. NEVER give to Shiloh — toxic to dogs.")],
        [P("Bacon (uncured, no-sugar-added)"), P("1 lb"), P("Every week"),
         P("High fat, good protein. Check label — no sugar added, uncured preferred.")],
        [P("Spinach (fresh or frozen)"), P("1 lb"), P("Every week"),
         P("Low carb (~1g net/cup). Sauté in butter or eat raw. Iron and folate.")],
        [P("Blueberries (fresh or frozen)"), P("1 pint"), P("Every week"),
         P("1/3 cup post-workout only — 9g net carbs per 1/2 cup. Antioxidants.")],

        # ── ROTATE PROTEIN ──
        [P("▶ ROTATE PROTEIN — add ONE of these each week", 'cell_blue_hdr'),
         P("", 'cell_blue_hdr'), P("", 'cell_blue_hdr'),
         P("Alternate for variety and different fat profiles", 'cell_blue_hdr')],

        [P("  Option A: Ribeye or NY strip steak"), P("2–3 lbs"), P("~2 of 4 weeks"),
         P("Highest-fat premium cut. Grill, reverse sear, or cast iron. Salt + butter only.")],
        [P("  Option B: Pork belly"), P("1.5–2 lbs"), P("~1 of 4 weeks"),
         P("Highest fat-to-protein ratio available. Roast with crispy skin.")],
        [P("  Option C: Beef heart"), P("0.5–1 lb"), P("~1 of 4 weeks"),
         P("Muscle meat. High CoQ10 and taurine. Sauté in butter — tastes like lean steak.")],

        # ── FAT STAPLES (restock as needed) ──
        [P("▶ RESTOCK AS NEEDED — check before shopping"), P("", 'cell_hdr'),
         P("", 'cell_hdr'), P("", 'cell_hdr')],

        [P("Heavy cream (full fat)"), P("1 pint"), P("~Weekly"),
         P("Add to coffee (replaces milk), use in pan sauces. ~5g fat per tbsp.")],
        [P("Hard cheese (cheddar, gouda, or parmesan)"), P("0.5 lb"), P("~Weekly"),
         P("Near-zero carbs. Use as snack or topping. Avoid processed cheese slices.")],
        [P("Beef tallow (rendered) or suet"), P("1 jar"), P("Monthly"),
         P("High-heat cooking. Ask Jimmy P's Butcher for suet (often free or cheap to render).")],
        [P("Body Tech Whey Isolate"), P("—"), P("Restock"),
         P("2 scoops/day = 50g protein. Take post-workout within 30 min.")],
        [P("Electrolytes (LMNT or Redmond Re-Lyte)"), P("—"), P("Restock"),
         P("Non-negotiable on carnivore. Depleted sodium drags potassium and magnesium with it.")],
    ]

    william_tbl = Table(william_rows, colWidths=CW2, repeatRows=1)
    william_tbl.setStyle(TableStyle([
        ('FONTNAME',      (0,0),  (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0),  (-1,-1), 8),
        ('TOPPADDING',    (0,0),  (-1,-1), 4),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
        ('LEFTPADDING',   (0,0),  (-1,-1), 6),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 6),
        ('GRID',          (0,0),  (-1,-1), 0.4, MID_GRAY),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
        # Column header
        ('BACKGROUND',    (0,0),  (-1,0),  CHARCOAL),
        # EVERY WEEK header (row 1)
        ('BACKGROUND',    (0,1),  (-1,1),  GOLD),
        ('TEXTCOLOR',     (0,1),  (-1,1),  WHITE),
        # Every week data (rows 2–9)
        ('ROWBACKGROUNDS',(0,2),  (-1,9),  [WHITE, LIGHT_GRAY]),
        # ROTATE header (row 10)
        ('BACKGROUND',    (0,10), (-1,10), ROTATE_HDR),
        # Rotate data (rows 11–13)
        ('BACKGROUND',    (0,11), (-1,13), ROTATE_BG),
        # RESTOCK header (row 14)
        ('BACKGROUND',    (0,14), (-1,14), DARK_GRAY),
        ('TEXTCOLOR',     (0,14), (-1,14), WHITE),
        # Restock data (rows 15–19)
        ('ROWBACKGROUNDS',(0,15), (-1,19), [MONTHLY_BG, MONTHLY_BG]),
    ]))
    story.append(william_tbl)
    story.append(Spacer(1, 0.06*inch))

    # Protein rotation note
    story.append(Paragraph(
        "<b>Protein rotation (both of you):</b> "
        "Week A: Chicken thighs + Ground beef. "
        "Week B: Ground beef + Pork shoulder. "
        "Week C: Ribeye/steak + Chicken. "
        "Week D: Mixed (clear the freezer). "
        "This prevents both you and Shiloh from eating the same protein daily and improves nutritional variety.",
        S['note']
    ))
    story.append(Spacer(1, 0.06*inch))

    # Avocado warning
    story.append(Paragraph(
        "<b>⚠ KEEP SEPARATE:</b> Avocado, garlic, onion, and bacon are for William only. "
        "All are toxic to dogs. Keep prep surfaces separate from Shiloh's raw food.",
        S['note']
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # WILLIAM'S MACRO TARGETS
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("1", "WILLIAM'S DAILY MACRO TARGETS")

    warn_tbl = Table([[Paragraph(
        "<b>Note on your 70/20/10 split:</b> At ~2,900 cal/day (your estimated TDEE), 70% protein = ~510g/day — "
        "physiologically extreme and beyond what muscle can absorb. "
        "The targets below use <b>1.5g protein per pound of bodyweight</b> (aggressive but well-supported for intense training). "
        "Fat is raised to ~50% of calories, which is standard on carnivore for satiety and hormone support.",
        S['warn']
    )]], colWidths=[7.5*inch])
    warn_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), WARN_BG),
        ('BOX',           (0,0),(-1,-1), 1.5, WARN_BORDER),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(warn_tbl)
    story.append(Spacer(1, 0.08*inch))

    macro_stats = [
        [P("~2,900", 'macro_val'), P("~262g", 'macro_val'), P("~161g", 'macro_val'),
         P("~73g", 'macro_val'),   P("+50g", 'macro_val'),  P("~2.1 lbs", 'macro_val')],
        [P("cal/day", 'macro_lbl'), P("protein/day", 'macro_lbl'), P("fat/day", 'macro_lbl'),
         P("carbs/day", 'macro_lbl'), P("whey supplement", 'macro_lbl'), P("meat/day from food", 'macro_lbl')],
    ]
    macro_tbl = Table(macro_stats, colWidths=[1.25*inch]*6)
    macro_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CHARCOAL),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 2),
        ('RIGHTPADDING',  (0,0),(-1,-1), 2),
        ('LINEAFTER',     (0,0), (4,1),  0.5, DARK_GRAY),
    ]))
    story.append(macro_tbl)
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 2. ORGANS — DETAIL & RULES
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("2", "ORGAN MEATS — DETAIL & ROTATION RULES")
    story.append(badge("SHILOH ONLY — quantities below are Shiloh's only", SCOPE_DOG, 3.5*inch))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph(
        "The cart checklist on page 1 tells you what to buy. "
        "This section explains why and what each organ does so you understand the system.",
        S['note']
    ))
    story.append(Spacer(1, 0.05*inch))

    W = [1.5*inch, 1.0*inch, 0.9*inch, 0.85*inch, 3.25*inch]
    organ_rows = [
        [P("Organ", 'cell_hdr'), P("Weekly Qty", 'cell_hdr'), P("Status", 'cell_hdr'),
         P("Frequency", 'cell_hdr'), P("Why / What It Does", 'cell_hdr')],
        [P("Beef liver"), P("0.5 lb"),
         P("STAPLE\n(always buy)", 'cell_bold'), P("Every week"),
         P("Richest source of vitamin A, B12, iron, copper. Do not exceed 0.5–0.75 lb/week — "
           "excess vitamin A is toxic at high doses. Feed 2x/week, not daily.")],
        [P("Green tripe\n(raw, unbleached)"), P("1 lb"),
         P("STAPLE\n(always buy)", 'cell_bold'), P("Every week"),
         P("NOT a secreting organ — does NOT count toward the organ cap. "
           "Highest-value item in the raw diet. Natural probiotics, digestive enzymes, "
           "ideal Ca:P ratio. Feed 3–4x/week. Pre-portion and freeze in 1-lb bags.")],
        [P("Beef or pork kidney"), P("0.25 lb"),
         P("ROTATE A\n(most weeks)", 'cell_blue'), P("3 of 4 weeks"),
         P("Standard pairing with liver. Rich in B vitamins and selenium. "
           "Feed 1–2x/week. This is your default second organ every week unless you swap in spleen.")],
        [P("Beef spleen"), P("0.25 lb"),
         P("ROTATE B\n(monthly)", 'cell_blue'), P("1 of 4 weeks",),
         P("Swap in place of kidney once per month. High in iron and digestive enzymes. "
           "If unavailable at the market, just use kidney that week.")],
    ]

    organ_detail_tbl = Table(organ_rows, colWidths=W, repeatRows=1)
    organ_detail_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),  (-1,0),  CHARCOAL),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [WHITE, LIGHT_GRAY]),
        ('BACKGROUND',    (0,3),  (-1,4),  ROTATE_BG),
        ('TOPPADDING',    (0,0),  (-1,-1), 5),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 5),
        ('LEFTPADDING',   (0,0),  (-1,-1), 6),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 6),
        ('GRID',          (0,0),  (-1,-1), 0.4, MID_GRAY),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
    ]))
    story.append(organ_detail_tbl)
    story.append(Spacer(1, 0.06*inch))
    story.append(Paragraph(
        "<b>Weekly organ total target: ~0.75 lb</b> (0.5 lb liver + 0.25 lb kidney or spleen). "
        "<b>Maximum cap: 1.75 lbs</b> — the cap exists as a ceiling, not a target. "
        "You are not trying to hit 1.75 lbs; you're trying to stay well under it. "
        "Green tripe (1 lb) sits outside this calculation entirely.",
        S['note']
    ))
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 3. RAW MEATY BONES — SHILOH ONLY
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("3", "RAW MEATY BONES")
    story.append(badge("SHILOH ONLY — never cooked; not for William", SCOPE_DOG, 3.5*inch))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph(
        "Target 15–20% of Shiloh's weekly diet as raw meaty bones (~2.5–3.5 lbs/week). "
        "All bones must remain raw — cooked bones splinter and are dangerous.",
        S['note']
    ))
    story.append(Spacer(1, 0.05*inch))

    W = [2.5*inch, 1.2*inch, 3.8*inch]
    rows = [
        [P("Bone Item", 'cell_hdr'), P("Shiloh's Qty/Wk", 'cell_hdr'), P("Notes", 'cell_hdr')],
        [P("Chicken backs"), P("2–3 lbs"),
         P("Soft, fully digestible. Safe for large breeds. Feed 3x/week as part of a meal.")],
        [P("Chicken necks"), P("1 lb"),
         P("Good calcium source. Supervise — some dogs swallow without chewing.")],
        [P("Duck necks (if available)"), P("0.5–1 lb"),
         P("Higher meat-to-bone ratio. Check Asian Market on Bonita Beach Rd first.")],
        [P("Pork ribs (raw, single rib)"), P("1–1.5 lbs"),
         P("Recreational chew — feed 1–2x/week. Raw only. Never cooked pork ribs.")],
    ]
    story.append(make_table(rows, W))
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 4. FAT SOURCES — WILLIAM ONLY
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("4", "FAT SOURCES — William's Carnivore Priority")
    story.append(badge("WILLIAM ONLY — these support his 50% fat macro target (~161g fat/day)", SCOPE_W, 4.5*inch))
    story.append(Spacer(1, 0.05*inch))

    W = [2.3*inch, 1.2*inch, 4.0*inch]
    rows = [
        [P("Item", 'cell_hdr'), P("Qty/Week", 'cell_hdr'), P("Notes", 'cell_hdr')],
        [P("Grass-fed butter (Kerrygold)"), P("1–2 lbs (4–8 sticks)"),
         P("Cook all meat in butter. Add to eggs. High in fat-soluble vitamins A, D, E, K2. "
           "Kerrygold is widely available at Publix and Costco.")],
        [P("Beef tallow or suet (rendered)"), P("1 jar"),
         P("High-heat cooking. Buy rendered tallow or render suet from Jimmy P's (often free or cheap). "
           "Render in slow cooker — makes a month's supply.")],
        [P("Heavy cream (full fat)"), P("1 pint"),
         P("Add to coffee instead of milk. Use in pan sauces. ~5g fat per tablespoon, 0.4g carbs.")],
        [P("Avocado"), P("4–6"),
         P("~21g mono-unsaturated fat per avocado. Eat 1/day with a meal. "
           "NEVER give to Shiloh — persin is toxic to dogs.")],
        [P("Hard cheese (cheddar, gouda, parmesan)"), P("0.5–1 lb"),
         P("High fat, near-zero carbs. Snack or topping. Choose aged hard cheese — avoid processed slices.")],
    ]
    story.append(make_table(rows, W))
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 5. VEGETABLES & LOW-CARB PRODUCE
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("5", "VEGETABLES & LOW-CARB PRODUCE")
    story.append(badge("BOTH — buy once, split between both (Shiloh puréed, William cooked/raw)", SCOPE_BOTH, 5.0*inch))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph(
        "William's ~73g carb target comes from vegetables only — no grains, no starches. "
        "Shiloh needs vegetables for fiber and micronutrients — puree or steam all of his. "
        "Rice, sweet potato, and banana have been removed (too starchy for carnivore).",
        S['note']
    ))
    story.append(Spacer(1, 0.05*inch))

    W = [2.0*inch, 1.2*inch, 4.3*inch]
    rows = [
        [P("Item", 'cell_hdr'), P("Combined Qty", 'cell_hdr'), P("Notes", 'cell_hdr')],
        [P("Spinach (fresh or frozen)"), P("2 lbs"),
         P("William: raw in salad or sauté in butter (~1g net carbs/cup). "
           "Shiloh: blend raw or lightly steam. Iron and folate for both.")],
        [P("Kale or collard greens"), P("1 lb"),
         P("William: sauté in butter. Shiloh: steam then blend. ~3g net carbs/cup cooked.")],
        [P("Zucchini"), P("2 medium"),
         P("Very low carb (~2g net/cup). William: grill or sauté. Shiloh: steam and cube.")],
        [P("Broccoli (florets)"), P("0.5 lb"),
         P("Limit Shiloh to under 10% of his vegetable portion (isothiocyanates). "
           "William: sauté in butter, keep portion small to stay low carb.")],
        [P("Blueberries (fresh or frozen)"), P("1 pint"),
         P("William: 1/3 cup post-workout only. Shiloh: 2–3 tbsp per meal. "
           "Best low-carb fruit option for both.")],
    ]
    story.append(make_table(rows, W))
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 6. SUPPLEMENTS
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("6", "SUPPLEMENTS & ADDITIONS")
    story.append(Paragraph("Each item labeled individually.", S['note']))
    story.append(Spacer(1, 0.05*inch))

    W = [2.2*inch, 0.85*inch, 1.1*inch, 3.35*inch]
    rows = [
        [P("Item", 'cell_hdr'), P("Applies To", 'cell_hdr'), P("Qty", 'cell_hdr'), P("Notes", 'cell_hdr')],
        [P("Body Tech Whey Isolate"), P("William"), P("Restock as needed"),
         P("2 scoops/day = 50g protein. Fast-absorbing — take post-workout within 30 min.")],
        [P("Fish oil (wild salmon oil)"), P("Both"), P("1 bottle"),
         P("Shiloh: 1 tsp/day. William: continue current routine. One bottle covers both.")],
        [P("Coconut oil (unrefined)"), P("Shiloh only"), P("Small jar"),
         P("1 tsp 3x/week. Coat health, anti-inflammatory. William gets fat from butter/tallow.")],
        [P("Kelp powder or dulse flakes"), P("Both"), P("1 small bag"),
         P("Natural iodine. Shiloh: ¼ tsp/day. William: use as replacement for iodine supplement.")],
        [P("Apple cider vinegar (raw, unfiltered)"), P("Shiloh only"), P("1 bottle"),
         P("1 tsp in water bowl 3x/week. Gut health and joint support.")],
        [P("Turmeric + black pepper"), P("Both"), P("On hand"),
         P("Shiloh: pinch 3x/week with black pepper. William: add to cooking daily.")],
        [P("Vitamin E (400 IU, mixed tocopherols)"), P("Shiloh only"), P("1 bottle"),
         P("1 capsule per week pierced into food. Required on high-fat raw diets.")],
        [P("Probiotics or plain kefir"), P("Shiloh only"), P("1 tub"),
         P("1–2 tbsp plain kefir 4x/week. Supports gut microbiome on raw diet.")],
        [P("Creatine monohydrate (optional)"), P("William only"), P("1 bag"),
         P("5g/day. Supports ATP regeneration during intense lifting. Take with post-workout shake.")],
        [P("Electrolytes (LMNT, Redmond Re-Lyte, or sea salt)"), P("William only"), P("Restock"),
         P("Non-negotiable on carnivore. Low-carb diets deplete sodium → drags K+ and Mg2+ with it. "
           "Salt food aggressively. Magnesium glycinate 300–400mg before bed also beneficial.")],
    ]
    story.append(make_table(rows, W))
    story.append(Spacer(1, 0.1*inch))

    # ══════════════════════════════════════════════════════════════════════════
    # 7. WHERE TO SHOP
    # ══════════════════════════════════════════════════════════════════════════
    story += section_header("7", "WHERE TO SHOP — Markets Near Bonita Springs")
    story.append(Paragraph(
        "Markets near 10660 Founders Way, Bonita Springs FL 34135. "
        "Ethnic markets stock the harder-to-find items at a fraction of mainstream prices.",
        S['body']
    ))
    story.append(Spacer(1, 0.06*inch))

    W = [1.7*inch, 1.8*inch, 1.0*inch, 3.0*inch]
    rows = [
        [P("Market", 'cell_hdr2'), P("Address", 'cell_hdr2'),
         P("Hours", 'cell_hdr2'), P("Best For", 'cell_hdr2')],
        [P("Asian Market (Bonita Springs)"),
         P("10430 Bonita Beach Rd SE\nBonita Springs, FL 34135\n~1.5 miles\n☎ (239) 948-0398"),
         P("Call ahead"),
         P("Whole fish (sardines, mackerel), duck necks, chicken feet, pork offcuts, kelp/seaweed.")],
        [P("Mexican Star Grocery & Food"),
         P("10430 Bonita Beach Rd SE\nBonita Springs, FL 34135\n~1.5 miles\n☎ (239) 221-7985"),
         P("Daily\n9am–10pm"),
         P("Tripe (menudo), liver (hígado), kidney (riñones), heart (corazón), pork organs. "
           "Use Spanish terms for best selection.")],
        [P("Mi Mercado Foods"),
         P("11375 Tamiami Trl E\nNaples, FL 34113\n~12 miles\n☎ (239) 384-9244"),
         P("Mon–Sat\n6am–9pm"),
         P("Full organ selection, whole poultry, bulk pork. Worth the drive when local is out of stock.")],
        [P("Jimmy P's Butcher Shop"),
         P("Naples & Bonita Springs\n(call for location)"),
         P("Call"),
         P("Premium fatty cuts for William (ribeye, bulk pork belly), suet for rendering tallow.")],
        [P("Publix / Costco (backup)"),
         P("Multiple Bonita Springs\nlocations"),
         P("Standard hours"),
         P("Costco: bulk ground beef (10+ lbs), chicken thighs, 3 dozen eggs, Kerrygold butter, frozen sardines.")],
    ]
    market_tbl = Table(rows, colWidths=W, repeatRows=1)
    market_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),  (-1,0),  CHARCOAL),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [WHITE, GOLD_BG]),
        ('TOPPADDING',    (0,0),  (-1,-1), 5),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 5),
        ('LEFTPADDING',   (0,0),  (-1,-1), 6),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 6),
        ('GRID',          (0,0),  (-1,-1), 0.4, MID_GRAY),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
    ]))
    story.append(market_tbl)
    story.append(Spacer(1, 0.06*inch))
    story.append(Paragraph(
        "<b>Weekly run (2 stops, same plaza):</b> Mexican Star for organs + tripe, "
        "then Publix/Costco for bulk proteins, eggs, butter, avocados. "
        "<b>Spanish terms at Latin markets:</b> hígado (liver), riñones (kidney), corazón (heart), "
        "menudo (tripe), patas (feet).",
        S['note']
    ))
    story.append(Spacer(1, 0.1*inch))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=6))
    story.append(Paragraph(
        "Prepared by Panacea (Marceau Solutions AI) | May 10, 2026 | "
        "BARF/Prey Model for 95 lb adult GSD. Transition raw feeding gradually over 2–3 weeks, consult your vet. "
        "William's targets based on 1.5g protein/lb at ~2,900 cal/day TDEE. Adjust weekly based on energy and performance.",
        S['note']
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF saved: {OUTPUT_PATH}")


if __name__ == '__main__':
    build_pdf()
