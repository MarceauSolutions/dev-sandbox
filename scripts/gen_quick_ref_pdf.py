#!/usr/bin/env python3
"""
One-page Quick Reference: Butcher Phone Numbers + Weekly Supplements
William & Shiloh — Marceau Solutions
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

OUTPUT_PATH = '/home/clawdbot/dev-sandbox/docs/Quick_Reference_Butchers_Supplements.pdf'

GOLD       = HexColor("#C9963C")
GOLD_BG    = HexColor("#FDF8EF")
GOLD_DARK  = HexColor("#8B6914")
CHARCOAL   = HexColor("#333333")
DARK_GRAY  = HexColor("#555555")
MID_GRAY   = HexColor("#e2e0d8")
LIGHT_GRAY = HexColor("#f5f5f0")
BLUE_HDR   = HexColor("#1a5276")
BLUE_BG    = HexColor("#eaf3fb")
PURPLE_HDR = HexColor("#6c3483")
PURPLE_BG  = HexColor("#f5eef8")
WHITE      = colors.white
ROTATE_HDR = HexColor("#2471a3")
ROTATE_BG  = HexColor("#e8f4fd")

FONTS_DIR = '/home/clawdbot/dev-sandbox/execution/pdf_templates/fonts'


def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('Montserrat-Bold', f'{FONTS_DIR}/Montserrat-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Inter-Regular',   f'{FONTS_DIR}/Inter-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Inter-Bold',      f'{FONTS_DIR}/Inter-Bold.ttf'))
        return 'Montserrat-Bold', 'Inter-Regular', 'Inter-Bold'
    except Exception:
        return 'Helvetica-Bold', 'Helvetica', 'Helvetica-Bold'


bold, regular, bold2 = register_fonts()

S = {
    'title':    ParagraphStyle('title',    fontName=bold,    fontSize=16, textColor=WHITE,
                               alignment=TA_CENTER, spaceAfter=0, leading=20),
    'subtitle': ParagraphStyle('subtitle', fontName=regular, fontSize=8,  textColor=GOLD,
                               alignment=TA_CENTER, spaceAfter=0),
    'sec':      ParagraphStyle('sec',      fontName=bold2,   fontSize=9,  textColor=WHITE,
                               alignment=TA_LEFT, leading=12),
    'cell':     ParagraphStyle('cell',     fontName=regular, fontSize=7.5, textColor=CHARCOAL,
                               leading=10, spaceAfter=0),
    'cell_b':   ParagraphStyle('cell_b',   fontName=bold2,   fontSize=7.5, textColor=CHARCOAL,
                               leading=10, spaceAfter=0),
    'cell_hdr': ParagraphStyle('cell_hdr', fontName=bold2,   fontSize=7.5, textColor=WHITE,
                               leading=10, spaceAfter=0),
    'rotate':   ParagraphStyle('rotate',   fontName=bold2,   fontSize=7.5, textColor=WHITE,
                               leading=10, spaceAfter=0),
    'note':     ParagraphStyle('note',     fontName=regular, fontSize=6.5, textColor=DARK_GRAY,
                               leading=9,  spaceAfter=0),
}


def P(text, style='cell'):
    return Paragraph(text, S[style])


def sec_bar(title, color=CHARCOAL):
    tbl = Table([[Paragraph(f'  {title}', S['sec'])]], colWidths=[7.5*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ]))
    return tbl


def tbl_style(rows_count, alt_colors=None, hdr_color=CHARCOAL):
    cmds = [
        ('BACKGROUND',    (0,0),  (-1,0),  hdr_color),
        ('TOPPADDING',    (0,0),  (-1,-1), 3),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 3),
        ('LEFTPADDING',   (0,0),  (-1,-1), 5),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 5),
        ('GRID',          (0,0),  (-1,-1), 0.3, MID_GRAY),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
    ]
    if alt_colors:
        for i in range(1, rows_count):
            bg = alt_colors[0] if i % 2 == 1 else alt_colors[1]
            cmds.append(('BACKGROUND', (0,i), (-1,i), bg))
    return TableStyle(cmds)


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        leftMargin=0.4*inch, rightMargin=0.4*inch,
        topMargin=0.35*inch, bottomMargin=0.35*inch,
    )

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    header = Table([
        [Paragraph('QUICK REFERENCE', S['title'])],
        [Paragraph('Butcher Phone Numbers · Weekly Supplements — William &amp; Shiloh', S['subtitle'])],
    ], colWidths=[7.5*inch])
    header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), CHARCOAL),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,1),  7),
    ]))
    story.append(header)
    story.append(Spacer(1, 0.08*inch))

    # ── SECTION 1: BUTCHERS ─────────────────────────────────────────────────
    story.append(sec_bar('📞  BUTCHER PHONE NUMBERS', CHARCOAL))
    story.append(Spacer(1, 0.04*inch))

    W = [2.1*inch, 2.5*inch, 1.2*inch, 1.7*inch]
    rows = [
        [P('Shop', 'cell_hdr'), P('Address', 'cell_hdr'),
         P('Phone', 'cell_hdr'), P('Best For', 'cell_hdr')],
        [P('Jimmy P\'s — Bonita Springs', 'cell_b'),
         P('25010 Bernwood Dr, Bonita Springs'),
         P('(239) 221-7428'),
         P('Chuck roast, beef heart, suet for rendering tallow')],
        [P('Jimmy P\'s — Naples', 'cell_b'),
         P('1833 Tamiami Trl N, Naples'),
         P('(239) 221-7428'),
         P('Ask for cheaper cuts — chuck, brisket, pork shoulder')],
        [P('Asian Market', 'cell_b'),
         P('10430 Bonita Beach Rd SE, Bonita Springs'),
         P('(239) 948-0398'),
         P('Whole fish, duck necks, chicken feet, kelp')],
        [P('Mexican Star Grocery', 'cell_b'),
         P('10430 Bonita Beach Rd SE, Bonita Springs'),
         P('(239) 221-7985'),
         P('Tripe, liver, kidney, heart — use Spanish')],
        [P('Mi Mercado Foods', 'cell_b'),
         P('11375 Tamiami Trl E, Naples'),
         P('(239) 384-9244'),
         P('Full organ selection, bulk pork, whole poultry')],
    ]
    t = Table(rows, colWidths=W, repeatRows=1)
    t.setStyle(tbl_style(len(rows), [WHITE, GOLD_BG]))
    story.append(t)
    story.append(Spacer(1, 0.09*inch))

    # ── SECTION 2: THIS WEEK'S CART ─────────────────────────────────────────
    story.append(sec_bar('🛒  THIS WEEK\'S CART', CHARCOAL))
    story.append(Spacer(1, 0.04*inch))

    # Two-column side-by-side: Shiloh | William
    # Each sub-table uses ~3.6" width
    COL_GAP = 0.3*inch
    SW = [1.4*inch, 0.75*inch, 0.55*inch, 0.85*inch]   # Shiloh: item / qty / est$ / note
    WW = [1.4*inch, 0.75*inch, 0.55*inch, 0.8*inch]    # William: item / qty / est$ / note

    def shiloh_hdr():
        return [P('SHILOH', 'cell_hdr'), P('Qty/Wk', 'cell_hdr'), P('Est.$', 'cell_hdr'), P('Note', 'cell_hdr')]

    def william_hdr():
        return [P('WILLIAM', 'cell_hdr'), P('Qty/Wk', 'cell_hdr'), P('Est.$', 'cell_hdr'), P('Note', 'cell_hdr')]

    shiloh_rows = [
        shiloh_hdr(),
        [P('Chicken backs',   'cell_b'), P('2–3 lbs'),  P('~$3'),   P('Cheapest base protein')],
        [P('Chicken thighs',  'cell_b'), P('3–4 lbs'),  P('~$6'),   P('Fat + protein')],
        [P('Beef liver',      'cell_b'), P('0.5 lb'),   P('~$1.50'),P('Staple every week')],
        [P('Green tripe',     'cell_b'), P('1 lb'),     P('~$2.50'),P('Not organ cap — gut health')],
        [P('Sardines (canned)',  'cell_b'), P('2 cans'), P('~$3'),   P('Omega-3 / phosphorus')],
        [P('Eggs',            'cell_b'), P('6–8'),      P('~$2'),   P('Raw yolk ok, cook whites')],
        [P('Chicken necks',   'cell_b'), P('1 lb'),     P('~$1.25'),P('Bone-in — jaw + teeth')],
        [P('— ROTATE protein (pick 1) —', 'rotate'), P('', 'rotate'), P('', 'rotate'), P('', 'rotate')],
        [P('Ground beef OR pork\nshoulder OR beef heart'), P('½–1 lb'), P('~$2–4'), P('Vary weekly')],
        [P('— ROTATE organ (pick 1) —', 'rotate'), P('', 'rotate'), P('', 'rotate'), P('', 'rotate')],
        [P('Kidney OR spleen'),           P('0.25 lb'), P('~$0.75'), P('~3 of 4 weeks')],
        [P('SHILOH TOTAL', 'cell_b'),     P('~8 lbs'),  P('~$22'),  P('~$88/mo')],
    ]

    william_rows = [
        william_hdr(),
        [P('Eggs',                'cell_b'), P('14–18'),   P('~$6'),  P('Cheapest protein/g — ISSA #1 bioavail.')],
        [P('Ground beef (80/20)', 'cell_b'), P('5–6 lbs'), P('~$27'), P('$4.50/lb — daily staple carnivore')],
        [P('Chicken thighs (B/I)','cell_b'), P('3–4 lbs'), P('~$6'),  P('$1.75/lb — best value per gram protein')],
        [P('Butter (Kerrygold)',  'cell_b'), P('1 lb'),    P('~$6'),  P('Fat + A/D/K2 — cook everything in it')],
        [P('Bacon ends/pieces',  'cell_b'), P('1 lb'),    P('~$3.50'),P('Cheaper than sliced — same macros')],
        [P('Avocado',             'cell_b'), P('4–5'),     P('~$4'),  P('Potassium — critical on low-carb')],
        [P('Spinach',             'cell_b'), P('1 lb'),    P('~$3'),  P('Limit 1 lb/wk — oxalates')],
        [P('Blueberries',         'cell_b'), P('1 pint'),  P('~$3'),  P('Post-workout only — antioxidants')],
        [P('— ROTATE protein (pick 1) —', 'rotate'), P('', 'rotate'), P('', 'rotate'), P('', 'rotate')],
        [P('Chuck roast OR pork\nshoulder OR beef heart'), P('2–3 lbs'), P('~$8–10'), P('$3–4/lb vs $20+ ribeye')],
        [P('— RESTOCK if low —', 'rotate'), P('', 'rotate'), P('', 'rotate'), P('', 'rotate')],
        [P('Whey, electrolytes,\nheavy cream, tallow'),   P('—'),    P('varies'), P('Check stock before shopping')],
        [P('WILLIAM TOTAL', 'cell_b'),    P('~15 lbs'),  P('~$67'), P('~$268/mo — budget-compliant')],
    ]

    def cart_table(rows, widths):
        t = Table(rows, colWidths=widths, repeatRows=1)
        cmds = [
            ('BACKGROUND', (0,0), (-1,0), BLUE_HDR),
            ('TOPPADDING',    (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
            ('RIGHTPADDING',  (0,0), (-1,-1), 5),
            ('GRID',          (0,0), (-1,-1), 0.3, MID_GRAY),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ]
        # Alternate rows
        for i in range(1, len(rows)):
            row_text = rows[i][0].text if hasattr(rows[i][0], 'text') else ''
            if 'ROTATE' in str(rows[i][0]) or 'RESTOCK' in str(rows[i][0]):
                cmds.append(('BACKGROUND', (0,i), (-1,i), ROTATE_HDR))
            elif i % 2 == 1:
                cmds.append(('BACKGROUND', (0,i), (-1,i), WHITE))
            else:
                cmds.append(('BACKGROUND', (0,i), (-1,i), BLUE_BG))
        t.setStyle(TableStyle(cmds))
        return t

    # Check row count parity — pad shorter with empty rows
    while len(shiloh_rows) < len(william_rows):
        shiloh_rows.append([P(''), P(''), P(''), P('')])
    while len(william_rows) < len(shiloh_rows):
        william_rows.append([P(''), P(''), P(''), P('')])

    st = cart_table(shiloh_rows, SW)
    wt = cart_table(william_rows, WW)

    side_by_side = Table([[st, Spacer(COL_GAP, 1), wt]],
                         colWidths=[sum(SW), COL_GAP, sum(WW)])
    side_by_side.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING',   (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',(0,0), (-1,-1), 0),
    ]))
    story.append(side_by_side)
    story.append(Spacer(1, 0.09*inch))

    # ── SECTION 3: SUPPLEMENTS ──────────────────────────────────────────────
    story.append(sec_bar('💊  SUPPLEMENTS — DAILY DOSING', CHARCOAL))
    story.append(Spacer(1, 0.04*inch))

    W = [2.2*inch, 2.55*inch, 2.75*inch]
    rows = [
        [P('Supplement', 'cell_hdr'), P('Shiloh', 'cell_hdr'), P('William', 'cell_hdr')],
        [P('Fish oil (wild salmon)',  'cell_b'), P('1 tsp/day'),            P('Continue current routine')],
        [P('Body Tech Whey Isolate',  'cell_b'), P('—'),                    P('2 scoops/day = 50g protein. Post-workout.')],
        [P('Creatine monohydrate',    'cell_b'), P('—'),                    P('5g/day with post-workout shake')],
        [P('Electrolytes (LMNT/Re-Lyte)', 'cell_b'), P('—'),               P('Daily — non-negotiable on carnivore')],
        [P('Kelp / dulse flakes',     'cell_b'), P('¼ tsp/day in food'),   P('Pinch in cooking — iodine source')],
        [P('Turmeric + black pepper', 'cell_b'), P('Pinch 3x/week'),       P('Add to cooking daily')],
        [P('Vitamin E (400 IU)',       'cell_b'), P('1 capsule/week in food'), P('—')],
        [P('Probiotics / plain kefir','cell_b'), P('2 tbsp 4x/week'),      P('—')],
        [P('Apple cider vinegar',     'cell_b'), P('1 tsp in water 3x/wk'),P('—')],
        [P('Coconut oil (unrefined)', 'cell_b'), P('1 tsp 3x/week'),       P('—  (William gets fat from butter/tallow)')],
    ]
    t = Table(rows, colWidths=W, repeatRows=1)
    t.setStyle(tbl_style(len(rows), [WHITE, GOLD_BG]))
    story.append(t)
    story.append(Spacer(1, 0.06*inch))

    # ── FOOTER NOTE ─────────────────────────────────────────────────────────
    story.append(Paragraph(
        'William: 262g protein/day · 2,900 cal/day · ~15 lbs meat/wk · EST. GROCERY TOTAL: ~$90/wk both | '
        'Budget note: chuck/shoulder/heart replace ribeye — same protein, ¼ the cost (ISSA: bioavail score identical for beef cuts) | '
        'Shiloh organ cap: 1.75 lb max · green tripe not counted in cap',
        S['note']
    ))

    doc.build(story)
    print(f'PDF saved: {OUTPUT_PATH}')


if __name__ == '__main__':
    build_pdf()
