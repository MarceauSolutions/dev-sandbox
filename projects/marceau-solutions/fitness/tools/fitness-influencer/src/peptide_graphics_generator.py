#!/usr/bin/env python3
"""
peptide_graphics_generator.py - Generate Main Graphics for Peptide Video

Uses xAI API to generate:
1. Spectrum graphic (Proven to Hype)
2. Checklist graphic (5 Key Learnings)
3. Decision Framework (Consider/Hold Off)
4. Category Summary (4 columns)

Also creates fallback versions using PIL if AI generation fails.

Usage:
    python peptide_graphics_generator.py --all           # Generate all graphics
    python peptide_graphics_generator.py --spectrum      # Only spectrum
    python peptide_graphics_generator.py --framework     # Only framework
    python peptide_graphics_generator.py --fallback      # Use PIL fallbacks only
"""

import argparse
import sys
import os
from pathlib import Path

# Add execution directory to path
sys.path.insert(0, '/Users/williammarceaujr./dev-sandbox/execution')

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

try:
    from grok_image_gen import GrokImageGenerator
    HAS_GROK = True
except ImportError:
    HAS_GROK = False
    print("Warning: grok_image_gen not available, using PIL fallbacks only")


# Dimensions
WIDTH = 3840
HEIGHT = 2160

# Colors
COLORS = {
    'background': (15, 23, 42),      # #0f172a
    'card_bg': (30, 41, 59),         # #1e293b
    'text_white': (255, 255, 255),
    'green': (34, 197, 94),          # #22c55e
    'amber': (245, 158, 11),         # #f59e0b
    'red': (239, 68, 68),            # #ef4444
    'blue': (59, 130, 246),          # #3b82f6
    'purple': (139, 92, 246),        # #8b5cf6
    'gray': (100, 116, 139),         # #64748b
}


class PeptideGraphicsGenerator:
    """Generate main graphics for peptide video."""

    def __init__(self, output_dir, use_ai=True):
        """
        Initialize graphics generator.

        Args:
            output_dir: Directory to save generated graphics
            use_ai: Whether to try xAI generation (falls back to PIL)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.use_ai = use_ai and HAS_GROK

        if self.use_ai:
            try:
                self.grok = GrokImageGenerator()
            except Exception as e:
                print(f"Warning: Could not initialize Grok: {e}")
                self.use_ai = False

        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """Load fonts with fallbacks."""
        fonts = {}

        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

        font_file = None
        for path in font_paths:
            if os.path.exists(path):
                font_file = path
                break

        try:
            if font_file:
                fonts['title'] = ImageFont.truetype(font_file, 96)
                fonts['header'] = ImageFont.truetype(font_file, 72)
                fonts['body'] = ImageFont.truetype(font_file, 48)
                fonts['small'] = ImageFont.truetype(font_file, 36)
                fonts['label'] = ImageFont.truetype(font_file, 32)
            else:
                fonts['title'] = ImageFont.load_default()
                fonts['header'] = ImageFont.load_default()
                fonts['body'] = ImageFont.load_default()
                fonts['small'] = ImageFont.load_default()
                fonts['label'] = ImageFont.load_default()
        except:
            fonts['title'] = ImageFont.load_default()
            fonts['header'] = ImageFont.load_default()
            fonts['body'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            fonts['label'] = ImageFont.load_default()

        return fonts

    def _draw_gradient_bar(self, draw, x, y, width, height, colors):
        """Draw a horizontal gradient bar."""
        num_colors = len(colors)
        segment_width = width // (num_colors - 1)

        for i in range(num_colors - 1):
            for j in range(segment_width):
                ratio = j / segment_width
                r = int(colors[i][0] * (1 - ratio) + colors[i+1][0] * ratio)
                g = int(colors[i][1] * (1 - ratio) + colors[i+1][1] * ratio)
                b = int(colors[i][2] * (1 - ratio) + colors[i+1][2] * ratio)
                draw.rectangle(
                    [x + i * segment_width + j, y,
                     x + i * segment_width + j + 1, y + height],
                    fill=(r, g, b)
                )

    def create_spectrum_graphic(self, filename="graphic_spectrum.png"):
        """
        Create the "Proven to Hype" spectrum graphic using PIL.

        Returns:
            Path to generated image
        """
        print("\n→ Creating spectrum graphic (PIL)...")

        img = Image.new('RGBA', (WIDTH, HEIGHT), (*COLORS['background'], 255))
        draw = ImageDraw.Draw(img)

        # Title
        title = "PEPTIDE EVIDENCE SPECTRUM"
        title_bbox = draw.textbbox((0, 0), title, font=self.fonts['title'])
        title_x = (WIDTH - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 200), title, font=self.fonts['title'], fill=COLORS['text_white'])

        # Gradient bar
        bar_width = 2400
        bar_height = 80
        bar_x = (WIDTH - bar_width) // 2
        bar_y = 400

        # Draw gradient (green -> amber -> red)
        self._draw_gradient_bar(
            draw, bar_x, bar_y, bar_width, bar_height,
            [COLORS['green'], COLORS['amber'], COLORS['red']]
        )

        # Draw rounded rectangle overlay to make it look nicer
        # (optional - makes edges)

        # Section labels
        sections = [
            ("PROVEN", COLORS['green'], bar_x + bar_width // 6),
            ("PROMISING", COLORS['amber'], bar_x + bar_width // 2),
            ("MOSTLY HYPE", COLORS['red'], bar_x + bar_width * 5 // 6),
        ]

        for label, color, x_center in sections:
            label_bbox = draw.textbbox((0, 0), label, font=self.fonts['header'])
            label_x = x_center - (label_bbox[2] - label_bbox[0]) // 2
            draw.text((label_x, bar_y + bar_height + 40), label, font=self.fonts['header'], fill=color)

        # Content under each section
        proven_items = ["• Tesamorelin", "• Sermorelin*", "• GHRP family", "• Insulin"]
        promising_items = ["• BPC-157", "• TB-500", "• Most healing", "  peptides"]
        hype_items = ["• 'Miracle' claims", "• Extreme fat loss", "• 'No side effects'", "• Quick fixes"]

        item_y = bar_y + bar_height + 180
        line_height = 60

        for i, item in enumerate(proven_items):
            item_bbox = draw.textbbox((0, 0), item, font=self.fonts['body'])
            item_x = sections[0][2] - (item_bbox[2] - item_bbox[0]) // 2
            draw.text((item_x, item_y + i * line_height), item, font=self.fonts['body'], fill=COLORS['text_white'])

        for i, item in enumerate(promising_items):
            item_bbox = draw.textbbox((0, 0), item, font=self.fonts['body'])
            item_x = sections[1][2] - (item_bbox[2] - item_bbox[0]) // 2
            draw.text((item_x, item_y + i * line_height), item, font=self.fonts['body'], fill=COLORS['text_white'])

        for i, item in enumerate(hype_items):
            item_bbox = draw.textbbox((0, 0), item, font=self.fonts['body'])
            item_x = sections[2][2] - (item_bbox[2] - item_bbox[0]) // 2
            draw.text((item_x, item_y + i * line_height), item, font=self.fonts['body'], fill=COLORS['text_white'])

        # Footnote
        footnote = "*Was FDA approved 1997-2008"
        fn_bbox = draw.textbbox((0, 0), footnote, font=self.fonts['small'])
        fn_x = (WIDTH - (fn_bbox[2] - fn_bbox[0])) // 2
        draw.text((fn_x, HEIGHT - 200), footnote, font=self.fonts['small'], fill=COLORS['gray'])

        # Save
        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')
        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_checklist_graphic(self, filename="graphic_checklist.png"):
        """
        Create the "5 Key Learnings" checklist graphic.

        Returns:
            Path to generated image
        """
        print("\n→ Creating checklist graphic (PIL)...")

        img = Image.new('RGBA', (WIDTH, HEIGHT), (*COLORS['background'], 255))
        draw = ImageDraw.Draw(img)

        # Title
        title = "WHAT I'VE LEARNED"
        title_bbox = draw.textbbox((0, 0), title, font=self.fonts['title'])
        title_x = (WIDTH - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 200), title, font=self.fonts['title'], fill=COLORS['text_white'])

        # Card background
        card_width = 2000
        card_height = 800
        card_x = (WIDTH - card_width) // 2
        card_y = 400

        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_width, card_y + card_height],
            radius=24,
            fill=COLORS['card_bg']
        )

        # Checklist items
        items = [
            "Do your own research",
            "Work with a healthcare provider",
            "Quality matters enormously",
            "Start conservative",
            "Track everything",
        ]

        item_x = card_x + 80
        item_y = card_y + 80
        line_height = 130

        for i, item in enumerate(items):
            # Draw checkmark circle
            circle_x = item_x
            circle_y = item_y + i * line_height
            circle_r = 24

            draw.ellipse(
                [circle_x - circle_r, circle_y - circle_r,
                 circle_x + circle_r, circle_y + circle_r],
                fill=COLORS['green']
            )

            # Draw checkmark
            check_points = [
                (circle_x - 10, circle_y),
                (circle_x - 2, circle_y + 10),
                (circle_x + 12, circle_y - 8)
            ]
            draw.line(check_points, fill=COLORS['text_white'], width=4)

            # Draw text
            draw.text(
                (item_x + 60, circle_y - 20),
                item,
                font=self.fonts['body'],
                fill=COLORS['text_white']
            )

        # Save
        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')
        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_framework_graphic(self, filename="graphic_framework.png"):
        """
        Create the "Decision Framework" two-column graphic.

        Returns:
            Path to generated image
        """
        print("\n→ Creating framework graphic (PIL)...")

        img = Image.new('RGBA', (WIDTH, HEIGHT), (*COLORS['background'], 255))
        draw = ImageDraw.Draw(img)

        # Title
        title = "DECISION FRAMEWORK"
        title_bbox = draw.textbbox((0, 0), title, font=self.fonts['title'])
        title_x = (WIDTH - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 150), title, font=self.fonts['title'], fill=COLORS['text_white'])

        # Two columns
        col_width = 1400
        col_height = 900
        col_gap = 200
        total_width = col_width * 2 + col_gap
        start_x = (WIDTH - total_width) // 2
        col_y = 350

        # Left column (CONSIDER IT IF) - Green
        left_x = start_x
        draw.rounded_rectangle(
            [left_x, col_y, left_x + col_width, col_y + col_height],
            radius=24,
            fill=COLORS['card_bg']
        )
        # Left border accent
        draw.rectangle(
            [left_x, col_y, left_x + 8, col_y + col_height],
            fill=COLORS['green']
        )

        # Left header
        left_header = "CONSIDER IT IF"
        lh_bbox = draw.textbbox((0, 0), left_header, font=self.fonts['header'])
        draw.text(
            (left_x + 60, col_y + 40),
            left_header,
            font=self.fonts['header'],
            fill=COLORS['green']
        )
        # Underline
        draw.rectangle(
            [left_x + 60, col_y + 130, left_x + 60 + (lh_bbox[2] - lh_bbox[0]), col_y + 134],
            fill=COLORS['green']
        )

        # Right column (HOLD OFF IF) - Amber
        right_x = start_x + col_width + col_gap
        draw.rounded_rectangle(
            [right_x, col_y, right_x + col_width, col_y + col_height],
            radius=24,
            fill=COLORS['card_bg']
        )
        # Right border accent
        draw.rectangle(
            [right_x, col_y, right_x + 8, col_y + col_height],
            fill=COLORS['amber']
        )

        # Right header
        right_header = "HOLD OFF IF"
        rh_bbox = draw.textbbox((0, 0), right_header, font=self.fonts['header'])
        draw.text(
            (right_x + 60, col_y + 40),
            right_header,
            font=self.fonts['header'],
            fill=COLORS['amber']
        )
        # Underline
        draw.rectangle(
            [right_x + 60, col_y + 130, right_x + 60 + (rh_bbox[2] - rh_bbox[0]), col_y + 134],
            fill=COLORS['amber']
        )

        # Left items (with checkmarks)
        left_items = [
            "Maxed out training,",
            "  nutrition, and sleep",
            "Specific issue (injury",
            "  recovery, etc.)",
            "Can afford medical",
            "  supervision",
            "Willing to do blood work",
        ]

        item_y = col_y + 180
        line_height = 90

        for i, item in enumerate(left_items):
            if not item.startswith("  "):
                # Draw check circle
                draw.ellipse(
                    [left_x + 50, item_y + i * line_height - 16,
                     left_x + 82, item_y + i * line_height + 16],
                    fill=COLORS['green']
                )
            draw.text(
                (left_x + 100, item_y + i * line_height - 20),
                item,
                font=self.fonts['body'],
                fill=COLORS['text_white']
            )

        # Right items (with X marks)
        right_items = [
            "Under 25 years old",
            "",
            "Haven't dialed in",
            "  the basics",
            "Looking for a shortcut",
            "",
            "Can't afford quality",
            "  products + monitoring",
        ]

        for i, item in enumerate(right_items):
            if item and not item.startswith("  "):
                # Draw X circle
                draw.ellipse(
                    [right_x + 50, item_y + i * line_height - 16,
                     right_x + 82, item_y + i * line_height + 16],
                    fill=COLORS['amber']
                )
            if item:
                draw.text(
                    (right_x + 100, item_y + i * line_height - 20),
                    item,
                    font=self.fonts['body'],
                    fill=COLORS['text_white']
                )

        # Save
        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')
        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_category_summary(self, filename="graphic_categories.png"):
        """
        Create a 4-column category summary graphic.

        Returns:
            Path to generated image
        """
        print("\n→ Creating category summary graphic (PIL)...")

        img = Image.new('RGBA', (WIDTH, HEIGHT), (*COLORS['background'], 255))
        draw = ImageDraw.Draw(img)

        # Title
        title = "THE 4 CATEGORIES"
        title_bbox = draw.textbbox((0, 0), title, font=self.fonts['title'])
        title_x = (WIDTH - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 150), title, font=self.fonts['title'], fill=COLORS['text_white'])

        # Four columns
        col_width = 800
        col_height = 850
        col_gap = 60
        total_width = col_width * 4 + col_gap * 3
        start_x = (WIDTH - total_width) // 2
        col_y = 350

        categories = [
            {
                "header": "GH\nSECRETAGOGUES",
                "color": "blue",
                "items": ["Sermorelin", "CJC-1295", "Ipamorelin", "Tesamorelin"]
            },
            {
                "header": "HEALING &\nRECOVERY",
                "color": "green",
                "items": ["BPC-157", "TB-500"]
            },
            {
                "header": "PERFORMANCE\n& BODY COMP",
                "color": "amber",
                "items": ["GHRP-6", "MK-677", "AOD-9604"]
            },
            {
                "header": "COGNITIVE &\nLONGEVITY",
                "color": "purple",
                "items": ["Epithalon", "Semax", "Selank"]
            },
        ]

        for i, cat in enumerate(categories):
            col_x = start_x + i * (col_width + col_gap)
            color = COLORS[cat['color']]

            # Card background
            draw.rounded_rectangle(
                [col_x, col_y, col_x + col_width, col_y + col_height],
                radius=16,
                fill=COLORS['card_bg']
            )

            # Top accent bar
            draw.rectangle(
                [col_x, col_y, col_x + col_width, col_y + 8],
                fill=color
            )

            # Header
            header_lines = cat['header'].split('\n')
            header_y = col_y + 40
            for line in header_lines:
                hdr_bbox = draw.textbbox((0, 0), line, font=self.fonts['body'])
                hdr_x = col_x + (col_width - (hdr_bbox[2] - hdr_bbox[0])) // 2
                draw.text((hdr_x, header_y), line, font=self.fonts['body'], fill=color)
                header_y += 60

            # Items
            item_y = header_y + 60
            for item in cat['items']:
                item_bbox = draw.textbbox((0, 0), item, font=self.fonts['small'])
                item_x = col_x + (col_width - (item_bbox[2] - item_bbox[0])) // 2
                draw.text((item_x, item_y), item, font=self.fonts['small'], fill=COLORS['text_white'])
                item_y += 70

        # Save
        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')
        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def generate_all(self):
        """Generate all main graphics."""
        print("\n" + "="*70)
        print("GRAPHICS GENERATION")
        print("="*70)
        print(f"Output directory: {self.output_dir}")

        all_paths = []

        all_paths.append(self.create_spectrum_graphic())
        all_paths.append(self.create_checklist_graphic())
        all_paths.append(self.create_framework_graphic())
        all_paths.append(self.create_category_summary())

        print(f"\n✅ Generated {len(all_paths)} graphics")
        print(f"   Location: {self.output_dir}")
        print("="*70 + "\n")

        return all_paths


def main():
    """CLI for graphics generation."""
    parser = argparse.ArgumentParser(
        description='Generate main graphics for peptide video'
    )
    parser.add_argument('--output', default=None, help='Output directory')
    parser.add_argument('--all', action='store_true', help='Generate all graphics')
    parser.add_argument('--spectrum', action='store_true', help='Generate spectrum graphic')
    parser.add_argument('--checklist', action='store_true', help='Generate checklist graphic')
    parser.add_argument('--framework', action='store_true', help='Generate framework graphic')
    parser.add_argument('--categories', action='store_true', help='Generate category summary')
    parser.add_argument('--fallback', action='store_true', help='Use PIL fallbacks only (no AI)')

    args = parser.parse_args()

    # Default output directory
    if not args.output:
        args.output = "/Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer/content/Peptide-Video/Graphics/Static"

    # Create generator
    generator = PeptideGraphicsGenerator(args.output, use_ai=not args.fallback)

    try:
        if args.all:
            generator.generate_all()
        elif args.spectrum:
            generator.create_spectrum_graphic()
        elif args.checklist:
            generator.create_checklist_graphic()
        elif args.framework:
            generator.create_framework_graphic()
        elif args.categories:
            generator.create_category_summary()
        else:
            parser.print_help()
            print("\nExamples:")
            print("  python peptide_graphics_generator.py --all")
            print("  python peptide_graphics_generator.py --spectrum")
            print("  python peptide_graphics_generator.py --framework --fallback")
            return 1

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
