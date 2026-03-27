#!/usr/bin/env python3
"""
Branded PDF Engine for William Marceau Fitness Coaching.

Generates professional, branded PDFs from structured data using ReportLab.
Supports 7 template types: workout, nutrition, progress, onboarding, peptide, challenge, generic.

Usage:
    python execution/branded_pdf_engine.py --template workout --input data.json --output program.pdf
    python execution/branded_pdf_engine.py --list-templates
"""

import argparse
import json
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.platypus.flowables import Flowable


class _NoWrapText(Flowable):
    """Draws text centered in its cell without any word-wrapping."""
    def __init__(self, text, font_name, font_size, color):
        Flowable.__init__(self)
        self.text = str(text)
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self._w = 0

    def wrap(self, availW, availH):
        self._w = availW
        return availW, self.font_size * 1.5

    def draw(self):
        self.canv.saveState()
        self.canv.setFont(self.font_name, self.font_size)
        self.canv.setFillColor(self.color)
        self.canv.drawCentredString(self._w / 2, 2, self.text)
        self.canv.restoreState()

# --- Brand Configuration ---

FONTS_DIR = Path(__file__).parent / "pdf_templates" / "fonts"
ASSETS_DIR = Path(__file__).parent / "pdf_templates" / "assets"


class BrandConfig:
    """Brand colors matching Marceau Solutions logo — dark + gold scheme."""

    # Primary brand colors (from logo)
    GOLD = HexColor("#C9963C")
    GOLD_LIGHT = HexColor("#D4AF37")
    GOLD_DARK = HexColor("#8B6914")
    GOLD_BG = HexColor("#FDF8EF")       # Very light gold tint for backgrounds
    CHARCOAL = HexColor("#333333")       # Logo background dark
    CHARCOAL_DEEP = HexColor("#2D2D2D")  # Deeper dark

    # Semantic aliases (used throughout templates)
    PRIMARY = GOLD
    PRIMARY_DARK = GOLD_DARK
    ACCENT = GOLD_LIGHT
    DARK = CHARCOAL
    DARKER = CHARCOAL_DEEP
    CARD_BG = HexColor("#3D3D3D")

    # Neutrals
    TEXT_LIGHT = HexColor("#f8fafc")
    TEXT_MUTED = HexColor("#94a3b8")
    RED = HexColor("#ef4444")
    BLUE = HexColor("#3b82f6")
    WHITE = colors.white
    LIGHT_GRAY = HexColor("#f5f5f0")     # Warm light gray
    MID_GRAY = HexColor("#e2e0d8")       # Warm mid gray
    DARK_GRAY = HexColor("#555555")

    # Legacy aliases (so templates don't break)
    GREEN = GOLD
    DARK_GREEN = GOLD_DARK
    AMBER = GOLD_LIGHT
    NAVY = CHARCOAL

    # Brand info
    NAME = "Marceau Solutions"
    TAGLINE = "Embrace the Pain & Defy the Odds"
    WEBSITE = "marceausolutions.com"

    # Font names (registered in _register_fonts)
    HEADING_FONT = "Montserrat-Bold"
    HEADING_FONT_REG = "Montserrat-Regular"
    BODY_FONT = "Inter-Regular"
    BODY_FONT_BOLD = "Inter-Bold"

    # Fallbacks
    FALLBACK_HEADING = "Helvetica-Bold"
    FALLBACK_BODY = "Helvetica"
    FALLBACK_BODY_BOLD = "Helvetica-Bold"

    @classmethod
    def logo_path(cls):
        """Return path to the logo icon (gold crescent on dark)."""
        p = ASSETS_DIR / "favicon-gold.png"
        return str(p) if p.exists() else None


def _register_fonts():
    """Register custom TTF fonts with graceful fallback to Helvetica."""
    registered = {"heading": False, "heading_reg": False, "body": False, "body_bold": False}
    font_map = {
        "Montserrat-Bold": ("heading", FONTS_DIR / "Montserrat-Bold.ttf"),
        "Montserrat-Regular": ("heading_reg", FONTS_DIR / "Montserrat-Regular.ttf"),
        "Inter-Regular": ("body", FONTS_DIR / "Inter-Regular.ttf"),
        "Inter-Bold": ("body_bold", FONTS_DIR / "Inter-Bold.ttf"),
    }
    for name, (key, path) in font_map.items():
        try:
            if path.exists():
                pdfmetrics.registerFont(TTFont(name, str(path)))
                registered[key] = True
        except Exception:
            pass

    if not registered["heading"]:
        BrandConfig.HEADING_FONT = BrandConfig.FALLBACK_HEADING
    if not registered["heading_reg"]:
        BrandConfig.HEADING_FONT_REG = BrandConfig.FALLBACK_BODY
    if not registered["body"]:
        BrandConfig.BODY_FONT = BrandConfig.FALLBACK_BODY
    if not registered["body_bold"]:
        BrandConfig.BODY_FONT_BOLD = BrandConfig.FALLBACK_BODY_BOLD


_register_fonts()


# --- Paragraph Styles ---

def get_brand_styles():
    """Return a dict of branded ParagraphStyles."""
    return {
        "title": ParagraphStyle(
            "BrandTitle", fontName=BrandConfig.HEADING_FONT,
            fontSize=24, leading=30, textColor=BrandConfig.NAVY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "BrandSubtitle", fontName=BrandConfig.BODY_FONT,
            fontSize=12, leading=16, textColor=BrandConfig.DARK_GRAY,
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "BrandH2", fontName=BrandConfig.HEADING_FONT,
            fontSize=16, leading=22, textColor=BrandConfig.NAVY,
            spaceBefore=18, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "BrandH3", fontName=BrandConfig.HEADING_FONT,
            fontSize=13, leading=18, textColor=BrandConfig.GOLD,
            spaceBefore=12, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BrandBody", fontName=BrandConfig.BODY_FONT,
            fontSize=10, leading=14, textColor=HexColor("#334155"),
        ),
        "body_bold": ParagraphStyle(
            "BrandBodyBold", fontName=BrandConfig.BODY_FONT_BOLD,
            fontSize=10, leading=14, textColor=HexColor("#334155"),
        ),
        "small": ParagraphStyle(
            "BrandSmall", fontName=BrandConfig.BODY_FONT,
            fontSize=8, leading=11, textColor=BrandConfig.TEXT_MUTED,
        ),
        "coach_note": ParagraphStyle(
            "CoachNote", fontName=BrandConfig.BODY_FONT,
            fontSize=10, leading=14, textColor=BrandConfig.CHARCOAL,
            leftIndent=12, borderColor=BrandConfig.GOLD,
            borderWidth=2, borderPadding=8,
        ),
        "center": ParagraphStyle(
            "BrandCenter", fontName=BrandConfig.BODY_FONT,
            fontSize=10, leading=14, textColor=HexColor("#334155"),
            alignment=TA_CENTER,
        ),
        "center_bold": ParagraphStyle(
            "BrandCenterBold", fontName=BrandConfig.BODY_FONT_BOLD,
            fontSize=11, leading=15, textColor=BrandConfig.CHARCOAL,
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", fontName=BrandConfig.BODY_FONT,
            fontSize=7, leading=10, textColor=BrandConfig.TEXT_MUTED,
            alignment=TA_CENTER,
        ),
    }


# --- Page Callbacks (Header / Footer) ---

def _draw_header(canvas, doc):
    """Draw branded header on each page — gold accent line."""
    canvas.saveState()
    w, h = letter

    # Logo icon (gold crescent)
    logo = BrandConfig.logo_path()
    if logo:
        canvas.drawImage(logo, 0.65 * inch, h - 0.8 * inch, width=32, height=32,
                         preserveAspectRatio=True, mask='auto')

    # Brand name
    canvas.setFont(BrandConfig.HEADING_FONT, 10)
    canvas.setFillColor(BrandConfig.CHARCOAL)
    canvas.drawString(1.15 * inch, h - 0.62 * inch, BrandConfig.NAME)

    # Tagline
    canvas.setFont(BrandConfig.BODY_FONT, 7)
    canvas.setFillColor(BrandConfig.DARK_GRAY)
    canvas.drawString(1.15 * inch, h - 0.77 * inch, BrandConfig.TAGLINE)

    # Gold accent line
    canvas.setStrokeColor(BrandConfig.GOLD)
    canvas.setLineWidth(2)
    canvas.line(0.6 * inch, h - 0.9 * inch, w - 0.6 * inch, h - 0.9 * inch)

    canvas.restoreState()


def _draw_footer(canvas, doc):
    """Draw branded footer on each page."""
    canvas.saveState()
    w, h = letter

    # Line
    canvas.setStrokeColor(BrandConfig.MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(0.6 * inch, 0.55 * inch, w - 0.6 * inch, 0.55 * inch)

    # Website (left)
    canvas.setFont(BrandConfig.BODY_FONT, 7)
    canvas.setFillColor(BrandConfig.TEXT_MUTED)
    canvas.drawString(0.65 * inch, 0.38 * inch, BrandConfig.WEBSITE)

    # Page number (center)
    page_text = f"Page {doc.page}"
    canvas.drawCentredString(w / 2, 0.38 * inch, page_text)

    # Date (right)
    date_text = datetime.now().strftime("%B %d, %Y")
    canvas.drawRightString(w - 0.65 * inch, 0.38 * inch, date_text)

    canvas.restoreState()


def _on_page(canvas, doc):
    _draw_header(canvas, doc)
    _draw_footer(canvas, doc)


# --- Shared Rendering Helpers ---

def accent_line():
    """Gold horizontal rule."""
    return HRFlowable(
        width="100%", thickness=1.5, color=BrandConfig.GOLD,
        spaceBefore=4, spaceAfter=8
    )


def section_title(text, styles):
    """Section header with gold accent."""
    return KeepTogether([
        Paragraph(text, styles["h2"]),
        accent_line(),
    ])


def coach_note_box(text, styles):
    """Gold-bordered coach note box."""
    data = [[Paragraph(f'<b>Coach\'s Note:</b> {text}', styles["body"])]]
    t = Table(data, colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.GOLD_BG),
        ("BOX", (0, 0), (-1, -1), 2, BrandConfig.GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def branded_table(headers, rows, col_widths=None):
    """Table with charcoal header row, alternating body rows."""
    styles = get_brand_styles()
    header_paras = [Paragraph(f'<b>{h}</b>', ParagraphStyle(
        "TH", fontName=BrandConfig.BODY_FONT_BOLD, fontSize=9,
        textColor=BrandConfig.GOLD_LIGHT, leading=12
    )) for h in headers]

    body_paras = []
    for row in rows:
        body_paras.append([
            Paragraph(str(cell), styles["body"]) if not isinstance(cell, Paragraph) else cell
            for cell in row
        ])

    data = [header_paras] + body_paras
    if col_widths is None:
        col_widths = [6.5 * inch / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), BrandConfig.CHARCOAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), BrandConfig.GOLD_LIGHT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BrandConfig.MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(1, len(data)):
        bg = BrandConfig.WHITE if i % 2 == 1 else BrandConfig.LIGHT_GRAY
        style_commands.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_commands))
    return t


def metric_card(label, value, color=None):
    """Small metric box — e.g., "2,400 cal" with a label."""
    if color is None:
        color = BrandConfig.GOLD
    styles = get_brand_styles()
    # Auto-size font so value fits on one line
    card_text_width = 1.7 * 72  # conservative estimate of available pts
    font_size = 18
    for fs in [18, 16, 14, 12, 10, 8]:
        if pdfmetrics.stringWidth(str(value), BrandConfig.HEADING_FONT, fs) <= card_text_width:
            font_size = fs
            break
    data = [[
        _NoWrapText(value, BrandConfig.HEADING_FONT, font_size, color),
    ], [
        Paragraph(label, ParagraphStyle(
            "MetricLabel", fontName=BrandConfig.BODY_FONT, fontSize=8,
            alignment=TA_CENTER, textColor=BrandConfig.DARK_GRAY, leading=11
        )),
    ]]
    t = Table(data, colWidths=[2.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BrandConfig.LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 1, BrandConfig.MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def bullet_list(items, styles, indent=18):
    """Render a bulleted list."""
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["body"], leftIndent=indent, bulletIndent=0,
        spaceBefore=2, spaceAfter=2,
    )
    return [Paragraph(f"\u2022  {item}", bullet_style) for item in items]


# --- Template Registry ---

TEMPLATES = {}


def register_template(name):
    """Decorator to register a template function."""
    def decorator(fn):
        TEMPLATES[name] = fn
        return fn
    return decorator


# --- Core Engine ---

class BrandedPDFEngine:
    """Main engine — takes template name + data dict, returns PDF bytes."""

    def __init__(self):
        self.styles = get_brand_styles()
        self._load_templates()

    def _load_templates(self):
        """Import all template modules to trigger registration."""
        # Fix __main__ double-import: when run as `python branded_pdf_engine.py`,
        # the module name is __main__, but templates do `from branded_pdf_engine import ...`
        # which would import a second copy with its own TEMPLATES dict.
        # Ensure this module is findable as 'branded_pdf_engine' in sys.modules.
        this_module = sys.modules[__name__]
        if "branded_pdf_engine" not in sys.modules:
            sys.modules["branded_pdf_engine"] = this_module

        templates_dir = Path(__file__).parent / "pdf_templates"
        if templates_dir.exists():
            for f in templates_dir.glob("*_template.py"):
                module_name = f.stem
                try:
                    import importlib
                    spec = importlib.util.spec_from_file_location(module_name, str(f))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                except Exception as e:
                    print(f"Warning: Could not load template {module_name}: {e}", file=sys.stderr)

    def generate(self, template_name: str, data: dict) -> bytes:
        """Generate branded PDF from template name and data dict."""
        if template_name not in TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(TEMPLATES.keys())}")

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=letter,
            leftMargin=0.65 * inch, rightMargin=0.65 * inch,
            topMargin=1.1 * inch, bottomMargin=0.8 * inch,
        )

        story = TEMPLATES[template_name](data, self.styles)
        doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
        return buf.getvalue()

    def generate_to_file(self, template_name: str, data: dict, output_path: str):
        """Generate and save PDF to disk."""
        pdf_bytes = self.generate(template_name, data)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return output_path

    @staticmethod
    def list_templates():
        """Return list of available template names."""
        return list(TEMPLATES.keys())


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Branded PDF Engine")
    parser.add_argument("--template", "-t", help="Template name")
    parser.add_argument("--input", "-i", help="JSON data file path")
    parser.add_argument("--output", "-o", help="Output PDF path")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    args = parser.parse_args()

    engine = BrandedPDFEngine()

    if args.list_templates:
        print("Available templates:")
        for name in engine.list_templates():
            print(f"  - {name}")
        return

    if not args.template or not args.input:
        parser.print_help()
        return

    with open(args.input) as f:
        data = json.load(f)

    output = args.output or f"{args.template}_output.pdf"
    engine.generate_to_file(args.template, data, output)
    print(f"Generated: {output}")

    # Auto-route to organized folder if no explicit output path was given
    if not args.output:
        try:
            from execution.pdf_router import route_pdf
            title = data.get("title", data.get("program_name", ""))
            description = data.get("description", data.get("subtitle", ""))
            tags = data.get("tags", [])
            dest = route_pdf(
                source_path=output,
                template=args.template,
                title=title,
                description=description,
                tags=tags,
                copy=True,  # Keep original + copy to organized location
            )
            print(f"Auto-routed copy to: {dest}")
        except Exception as e:
            print(f"Auto-routing skipped: {e}")


if __name__ == "__main__":
    main()
