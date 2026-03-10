#!/usr/bin/env python3
"""
Generate DumbPhone Lock ad creative images using Pillow.
Pixel-perfect text placement with brand fonts.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Paths
FONT_DIR = Path(__file__).resolve().parents[4] / "execution" / "pdf_templates" / "fonts"
OUTPUT_DIR = Path(__file__).resolve().parent / "ads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors
DARK_BG = "#1a1a1a"
GOLD = "#C9963C"
WHITE = "#FFFFFF"
GRAY = "#888888"
LIGHT_GRAY = "#AAAAAA"
RED_TINT = "#3a1a1a"
GOLD_TINT = "#2a2518"
RED_ACCENT = "#cc4444"
GREEN_ACCENT = "#44cc44"


def load_font(name, size):
    path = FONT_DIR / name
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        print(f"Warning: Could not load {path}, using default")
        return ImageFont.load_default()


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def draw_centered(draw, text, y, font, fill, width):
    tw = text_width(draw, text, font)
    draw.text(((width - tw) / 2, y), text, font=font, fill=fill)


# ─────────────────────────────────────────────
# IMAGE 1: "The Problem" (1080x1080)
# ─────────────────────────────────────────────
def generate_image_1():
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_huge = load_font("Montserrat-Bold.ttf", 160)
    font_sub = load_font("Inter-Regular.ttf", 36)
    font_cta = load_font("Montserrat-Bold.ttf", 28)
    font_cta_small = load_font("Inter-Regular.ttf", 22)

    # Top accent line
    draw.rectangle([0, 0, W, 6], fill=GOLD)

    # "4.5 HOURS" - big gold text, vertically centered-ish
    draw_centered(draw, "4.5", 260, font_huge, GOLD, W)
    draw_centered(draw, "HOURS", 430, font_huge, GOLD, W)

    # Subtext
    line1 = "That's how much your phone"
    line2 = "steals from you every day."
    draw_centered(draw, line1, 640, font_sub, WHITE, W)
    draw_centered(draw, line2, 690, font_sub, WHITE, W)

    # Divider line
    div_w = 200
    draw.rectangle([(W - div_w) / 2, 780, (W + div_w) / 2, 782], fill=GOLD)

    # CTA
    draw_centered(draw, "DumbPhone Lock", 820, font_cta, GOLD, W)
    draw_centered(draw, "Join the Waitlist  \u2192", 865, font_cta_small, LIGHT_GRAY, W)

    # Bottom accent line
    draw.rectangle([0, H - 6, W, H], fill=GOLD)

    path = OUTPUT_DIR / "ad_01_the_problem.png"
    img.save(str(path), "PNG")
    print(f"Saved: {path}")


# ─────────────────────────────────────────────
# IMAGE 2: "The Comparison" (1080x1080)
# ─────────────────────────────────────────────
def generate_image_2():
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    half = W // 2

    # Left panel (red tint)
    draw.rectangle([0, 0, half - 2, H], fill=RED_TINT)
    # Right panel (gold tint)
    draw.rectangle([half + 2, 0, W, H], fill=GOLD_TINT)

    # Divider
    draw.rectangle([half - 2, 0, half + 2, H], fill="#333333")

    # Fonts
    font_header = load_font("Montserrat-Bold.ttf", 28)
    font_price = load_font("Montserrat-Bold.ttf", 52)
    font_item = load_font("Inter-Regular.ttf", 24)
    font_label = load_font("Montserrat-Bold.ttf", 18)
    font_cta = load_font("Montserrat-Bold.ttf", 24)
    font_cta_sm = load_font("Inter-Regular.ttf", 20)

    # === LEFT SIDE: Light Phone ===
    lx = 60  # left margin for left panel

    # "VS" badge in center
    badge_y = 80
    draw.ellipse([half - 30, badge_y - 5, half + 30, badge_y + 35], fill="#333333", outline=GOLD, width=2)
    vs_font = load_font("Montserrat-Bold.ttf", 20)
    draw_centered(draw, "VS", badge_y + 2, vs_font, GOLD, W)

    # Left header
    draw.text((lx, 60), "LIGHT PHONE", font=font_label, fill=RED_ACCENT)
    draw.text((lx, 110), "$299", font=font_price, fill=WHITE)

    # Left items with X marks
    left_items = [
        "No Google Maps",
        "No banking apps",
        "No Uber/Lyft",
        "Separate phone plan",
        "Carry two phones",
    ]
    y = 210
    for item in left_items:
        # Draw X mark manually
        cx, cy = lx + 12, y + 14
        sz = 9
        draw.line([cx - sz, cy - sz, cx + sz, cy + sz], fill=RED_ACCENT, width=3)
        draw.line([cx - sz, cy + sz, cx + sz, cy - sz], fill=RED_ACCENT, width=3)
        draw.text((lx + 40, y + 2), item, font=font_item, fill=LIGHT_GRAY)
        y += 55

    # === RIGHT SIDE: DumbPhone Lock ===
    rx = half + 60

    draw.text((rx, 60), "DUMBPHONE LOCK", font=font_label, fill=GOLD)
    draw.text((rx, 110), "Free", font=font_price, fill=GOLD)

    right_items = [
        "Uses your iPhone",
        "Keep Maps & Banking",
        "Keep Uber & essentials",
        "No extra phone plan",
        "Toggle on/off anytime",
    ]
    y = 210
    for item in right_items:
        # Draw checkmark manually
        cx, cy = rx + 12, y + 14
        draw.line([cx - 8, cy, cx - 2, cy + 8], fill=GREEN_ACCENT, width=3)
        draw.line([cx - 2, cy + 8, cx + 10, cy - 6], fill=GREEN_ACCENT, width=3)
        draw.text((rx + 40, y + 2), item, font=font_item, fill=WHITE)
        y += 55

    # Bottom CTA bar
    cta_y = 900
    draw.rectangle([0, cta_y, W, H], fill="#111111")
    draw.rectangle([0, cta_y, W, cta_y + 3], fill=GOLD)

    draw_centered(draw, "Why buy another phone?", cta_y + 30, font_cta, WHITE, W)
    draw_centered(draw, "DumbPhone Lock  \u2014  Free Waitlist Open  \u2192", cta_y + 75, font_cta_sm, GOLD, W)

    path = OUTPUT_DIR / "ad_02_the_comparison.png"
    img.save(str(path), "PNG")
    print(f"Saved: {path}")


# ─────────────────────────────────────────────
# IMAGE 3: "The Promise" (1080x1920 story/reel)
# ─────────────────────────────────────────────
def generate_image_3():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_big = load_font("Montserrat-Bold.ttf", 140)
    font_strike = load_font("Inter-Regular.ttf", 60)
    font_sub = load_font("Montserrat-Bold.ttf", 80)
    font_cta = load_font("Montserrat-Bold.ttf", 32)
    font_cta_sm = load_font("Inter-Regular.ttf", 26)
    font_swipe = load_font("Inter-Regular.ttf", 22)

    # Top accent
    draw.rectangle([0, 0, W, 6], fill=GOLD)

    # Text stack centered vertically
    base_y = 480

    # "STOP"
    draw_centered(draw, "STOP", base_y, font_big, WHITE, W)

    # "doom-scrolling" with strikethrough
    strike_text = "doom-scrolling"
    st_y = base_y + 180
    st_w = text_width(draw, strike_text, font_strike)
    st_h = text_height(draw, strike_text, font_strike)
    st_x = (W - st_w) / 2
    draw.text((st_x, st_y), strike_text, font=font_strike, fill=GRAY)
    # Strikethrough line
    line_y = st_y + st_h / 2 + 5
    draw.rectangle([st_x - 10, line_y - 2, st_x + st_w + 10, line_y + 2], fill=GRAY)

    # "START"
    start_y = st_y + 120
    draw_centered(draw, "START", start_y, font_big, GOLD, W)

    # "living"
    living_y = start_y + 170
    draw_centered(draw, "living.", font_sub, GOLD, W) if False else None
    draw_centered(draw, "living.", living_y, font_sub, GOLD, W)

    # Divider
    div_w = 160
    div_y = living_y + 140
    draw.rectangle([(W - div_w) / 2, div_y, (W + div_w) / 2, div_y + 3], fill=GOLD)

    # CTA block
    cta_y = div_y + 60
    draw_centered(draw, "DumbPhone Lock", cta_y, font_cta, WHITE, W)
    draw_centered(draw, "Free waitlist open", cta_y + 55, font_cta_sm, LIGHT_GRAY, W)

    # Swipe up indicator at bottom
    arrow_y = H - 140
    draw_centered(draw, "\u25B2", arrow_y, font_cta, GOLD, W)
    draw_centered(draw, "Swipe up to join", arrow_y + 45, font_swipe, LIGHT_GRAY, W)

    # Bottom accent
    draw.rectangle([0, H - 6, W, H], fill=GOLD)

    path = OUTPUT_DIR / "ad_03_the_promise.png"
    img.save(str(path), "PNG")
    print(f"Saved: {path}")


if __name__ == "__main__":
    print("Generating DumbPhone Lock ad creatives...\n")
    generate_image_1()
    generate_image_2()
    generate_image_3()
    print("\nDone! All 3 ad creatives saved to ads/ directory.")
