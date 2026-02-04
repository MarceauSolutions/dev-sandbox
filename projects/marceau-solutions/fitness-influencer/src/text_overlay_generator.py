#!/usr/bin/env python3
"""
text_overlay_generator.py - Generate Text Overlays for Video

Creates PNG images with transparency for:
- Peptide name lower thirds
- Category header full-screen graphics
- Statistics callouts
- Disclaimer bar

Usage:
    python text_overlay_generator.py --all                    # Generate all overlays
    python text_overlay_generator.py --peptides               # Only peptide lower thirds
    python text_overlay_generator.py --headers                # Only category headers
    python text_overlay_generator.py --custom "TEXT" --type lower_third
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# Output dimensions (4K)
WIDTH = 3840
HEIGHT = 2160

# Color palette
COLORS = {
    'background': (15, 23, 42),      # #0f172a - dark navy
    'text_white': (255, 255, 255),   # #ffffff
    'green': (34, 197, 94),          # #22c55e - proven/positive
    'amber': (245, 158, 11),         # #f59e0b - caution
    'red': (239, 68, 68),            # #ef4444 - hype
    'blue': (59, 130, 246),          # #3b82f6 - scientific
    'purple': (139, 92, 246),        # #8b5cf6 - cognitive
    'gray': (100, 116, 139),         # #64748b - secondary
    'card_bg': (30, 41, 59),         # #1e293b - card background
}

# Peptide definitions with categories
PEPTIDES = [
    # Category 1: GH Secretagogues (Blue)
    {"name": "SERMORELIN", "category": "GH Secretagogue", "color": "blue"},
    {"name": "CJC-1295", "category": "GH Secretagogue", "color": "blue"},
    {"name": "IPAMORELIN", "category": "GH Secretagogue", "color": "blue"},
    {"name": "TESAMORELIN", "category": "GH Secretagogue (FDA Approved)", "color": "blue"},
    # Category 2: Healing & Recovery (Green)
    {"name": "BPC-157", "category": "Healing Peptide", "color": "green"},
    {"name": "TB-500", "category": "Recovery Peptide", "color": "green"},
    # Category 3: Performance (Amber)
    {"name": "GHRP-6", "category": "Performance", "color": "amber"},
    {"name": "MK-677", "category": "Performance*", "color": "amber"},
    {"name": "AOD-9604", "category": "Body Composition", "color": "amber"},
    # Category 4: Cognitive & Longevity (Purple)
    {"name": "EPITHALON", "category": "Longevity", "color": "purple"},
    {"name": "SEMAX", "category": "Cognitive", "color": "purple"},
    {"name": "SELANK", "category": "Cognitive", "color": "purple"},
]

# Category headers
CATEGORY_HEADERS = [
    {"text": "GROWTH HORMONE\nSECRETAGOGUES", "color": "blue"},
    {"text": "HEALING &\nRECOVERY", "color": "green"},
    {"text": "PERFORMANCE &\nBODY COMPOSITION", "color": "amber"},
    {"text": "COGNITIVE &\nLONGEVITY", "color": "purple"},
]


class TextOverlayGenerator:
    """Generate text overlays for video production."""

    def __init__(self, output_dir, font_path=None):
        """
        Initialize overlay generator.

        Args:
            output_dir: Directory to save generated overlays
            font_path: Path to TTF font file (or None for default)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Try to load a good font
        self.font_path = font_path
        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """Load fonts with fallbacks."""
        fonts = {}

        # Try common font locations
        font_paths = [
            # macOS
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # Custom
            self.font_path,
        ]

        font_file = None
        for path in font_paths:
            if path and os.path.exists(path):
                font_file = path
                break

        try:
            if font_file:
                fonts['name'] = ImageFont.truetype(font_file, 96)
                fonts['category'] = ImageFont.truetype(font_file, 48)
                fonts['header'] = ImageFont.truetype(font_file, 144)
                fonts['header_small'] = ImageFont.truetype(font_file, 96)
                fonts['stat'] = ImageFont.truetype(font_file, 128)
                fonts['stat_label'] = ImageFont.truetype(font_file, 48)
                fonts['disclaimer'] = ImageFont.truetype(font_file, 36)
            else:
                # Fallback to default
                fonts['name'] = ImageFont.load_default()
                fonts['category'] = ImageFont.load_default()
                fonts['header'] = ImageFont.load_default()
                fonts['header_small'] = ImageFont.load_default()
                fonts['stat'] = ImageFont.load_default()
                fonts['stat_label'] = ImageFont.load_default()
                fonts['disclaimer'] = ImageFont.load_default()
                print("Warning: Using default font. Install custom fonts for better results.")
        except Exception as e:
            print(f"Font loading error: {e}, using defaults")
            fonts['name'] = ImageFont.load_default()
            fonts['category'] = ImageFont.load_default()
            fonts['header'] = ImageFont.load_default()
            fonts['header_small'] = ImageFont.load_default()
            fonts['stat'] = ImageFont.load_default()
            fonts['stat_label'] = ImageFont.load_default()
            fonts['disclaimer'] = ImageFont.load_default()

        return fonts

    def create_lower_third(self, name, category, color_name, filename=None):
        """
        Create a lower third overlay for peptide name.

        Args:
            name: Peptide name
            category: Category label
            color_name: Color key from COLORS dict
            filename: Output filename (or auto-generate)

        Returns:
            Path to generated PNG
        """
        # Create transparent image
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Get accent color
        accent_color = COLORS.get(color_name, COLORS['blue'])

        # Calculate text sizes
        name_bbox = draw.textbbox((0, 0), name, font=self.fonts['name'])
        cat_bbox = draw.textbbox((0, 0), category, font=self.fonts['category'])

        name_width = name_bbox[2] - name_bbox[0]
        name_height = name_bbox[3] - name_bbox[1]
        cat_width = cat_bbox[2] - cat_bbox[0]
        cat_height = cat_bbox[3] - cat_bbox[1]

        # Box dimensions
        padding_x = 32
        padding_y = 24
        box_width = max(name_width, cat_width) + padding_x * 2 + 6  # +6 for left border
        box_height = name_height + cat_height + padding_y * 3

        # Position (lower left)
        box_x = int(WIDTH * 0.05)
        box_y = HEIGHT - int(HEIGHT * 0.15) - box_height

        # Draw semi-transparent background
        bg_color = (*COLORS['background'], 200)  # 80% opacity
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=0,
            fill=bg_color
        )

        # Draw left accent border
        draw.rectangle(
            [box_x, box_y, box_x + 6, box_y + box_height],
            fill=(*accent_color, 255)
        )

        # Draw peptide name
        text_x = box_x + 6 + padding_x
        text_y = box_y + padding_y
        draw.text((text_x, text_y), name, font=self.fonts['name'], fill=COLORS['text_white'])

        # Draw category
        cat_y = text_y + name_height + padding_y // 2
        draw.text((text_x, cat_y), category, font=self.fonts['category'], fill=(*accent_color, 255))

        # Save
        if not filename:
            filename = f"lower_third_{name.lower().replace('-', '_').replace(' ', '_')}.png"

        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')

        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_category_header(self, text, color_name, filename=None):
        """
        Create a full-screen category header.

        Args:
            text: Header text (can include newlines)
            color_name: Color key for underline
            filename: Output filename (or auto-generate)

        Returns:
            Path to generated PNG
        """
        # Create image with semi-transparent background
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw semi-transparent overlay
        overlay_color = (*COLORS['background'], 180)  # 70% opacity
        draw.rectangle([0, 0, WIDTH, HEIGHT], fill=overlay_color)

        # Get accent color
        accent_color = COLORS.get(color_name, COLORS['blue'])

        # Split text into lines
        lines = text.split('\n')

        # Calculate total height
        line_heights = []
        line_widths = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=self.fonts['header'])
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        total_height = sum(line_heights) + (len(lines) - 1) * 20  # 20px line spacing
        max_width = max(line_widths)

        # Starting Y position (centered)
        start_y = (HEIGHT - total_height) // 2

        # Draw each line centered
        current_y = start_y
        for i, line in enumerate(lines):
            line_x = (WIDTH - line_widths[i]) // 2
            draw.text((line_x, current_y), line, font=self.fonts['header'], fill=COLORS['text_white'])
            current_y += line_heights[i] + 20

        # Draw underline
        underline_width = int(max_width * 0.6)
        underline_x = (WIDTH - underline_width) // 2
        underline_y = current_y + 20
        draw.rectangle(
            [underline_x, underline_y, underline_x + underline_width, underline_y + 8],
            fill=(*accent_color, 255)
        )

        # Save
        if not filename:
            safe_text = text.replace('\n', '_').replace(' ', '_').lower()[:30]
            filename = f"header_{safe_text}.png"

        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')

        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_disclaimer(self, text=None, filename="disclaimer.png"):
        """
        Create a disclaimer bar overlay.

        Args:
            text: Disclaimer text (or use default)
            filename: Output filename

        Returns:
            Path to generated PNG
        """
        if not text:
            text = "This is not medical advice. Consult a healthcare provider before starting any supplement protocol."

        # Create transparent image
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=self.fonts['disclaimer'])
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Bar dimensions
        bar_height = text_height + 32
        bar_y = HEIGHT - int(HEIGHT * 0.08)

        # Draw semi-transparent bar
        bar_color = (*COLORS['background'], 200)
        draw.rectangle([0, bar_y, WIDTH, bar_y + bar_height], fill=bar_color)

        # Draw text centered
        text_x = (WIDTH - text_width) // 2
        text_y = bar_y + 16
        draw.text((text_x, text_y), text, font=self.fonts['disclaimer'], fill=(*COLORS['text_white'], 200))

        # Save
        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')

        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def create_statistic(self, number, label, color_name="blue", filename=None):
        """
        Create a statistic callout overlay.

        Args:
            number: Main statistic (e.g., "30+")
            label: Description label (e.g., "YEARS of Research")
            color_name: Accent color
            filename: Output filename

        Returns:
            Path to generated PNG
        """
        # Create transparent image
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        accent_color = COLORS.get(color_name, COLORS['blue'])

        # Calculate sizes
        num_bbox = draw.textbbox((0, 0), number, font=self.fonts['stat'])
        label_bbox = draw.textbbox((0, 0), label, font=self.fonts['stat_label'])

        num_width = num_bbox[2] - num_bbox[0]
        num_height = num_bbox[3] - num_bbox[1]
        label_width = label_bbox[2] - label_bbox[0]
        label_height = label_bbox[3] - label_bbox[1]

        # Box dimensions
        padding = 40
        box_width = max(num_width, label_width) + padding * 2
        box_height = num_height + label_height + padding * 3

        # Position (right side, middle-ish)
        box_x = WIDTH - box_width - int(WIDTH * 0.1)
        box_y = (HEIGHT - box_height) // 2

        # Draw card background
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=16,
            fill=(*COLORS['card_bg'], 230)
        )

        # Draw number
        num_x = box_x + (box_width - num_width) // 2
        num_y = box_y + padding
        draw.text((num_x, num_y), number, font=self.fonts['stat'], fill=(*accent_color, 255))

        # Draw label
        label_x = box_x + (box_width - label_width) // 2
        label_y = num_y + num_height + padding // 2
        draw.text((label_x, label_y), label, font=self.fonts['stat_label'], fill=COLORS['text_white'])

        # Save
        if not filename:
            safe_num = number.replace('+', 'plus').replace('-', '_')
            filename = f"stat_{safe_num}.png"

        output_path = self.output_dir / filename
        img.save(output_path, 'PNG')

        print(f"  ✓ Created: {filename}")
        return str(output_path)

    def generate_all_peptide_overlays(self):
        """Generate all peptide name lower thirds."""
        print("\n→ Generating peptide lower thirds...")
        paths = []

        for peptide in PEPTIDES:
            path = self.create_lower_third(
                peptide['name'],
                peptide['category'],
                peptide['color']
            )
            paths.append(path)

        return paths

    def generate_all_category_headers(self):
        """Generate all category header overlays."""
        print("\n→ Generating category headers...")
        paths = []

        for i, header in enumerate(CATEGORY_HEADERS):
            path = self.create_category_header(
                header['text'],
                header['color'],
                filename=f"header_category_{i+1}.png"
            )
            paths.append(path)

        return paths

    def generate_all_statistics(self):
        """Generate all statistic callouts."""
        print("\n→ Generating statistics...")

        stats = [
            ("30+", "YEARS of Research", "blue", "stat_30_years.png"),
            ("1997-2008", "FDA Approved", "green", "stat_fda_years.png"),
            ("NOT", "FDA APPROVED\nfor fitness uses", "amber", "stat_not_approved.png"),
        ]

        paths = []
        for number, label, color, filename in stats:
            path = self.create_statistic(number, label, color, filename)
            paths.append(path)

        return paths

    def generate_all(self):
        """Generate all overlay types."""
        print("\n" + "="*70)
        print("TEXT OVERLAY GENERATION")
        print("="*70)
        print(f"Output directory: {self.output_dir}")

        all_paths = []

        # Peptide lower thirds
        all_paths.extend(self.generate_all_peptide_overlays())

        # Category headers
        all_paths.extend(self.generate_all_category_headers())

        # Statistics
        all_paths.extend(self.generate_all_statistics())

        # Disclaimer
        all_paths.append(self.create_disclaimer())

        print(f"\n✅ Generated {len(all_paths)} overlay images")
        print(f"   Location: {self.output_dir}")
        print("="*70 + "\n")

        return all_paths


def main():
    """CLI for text overlay generation."""
    parser = argparse.ArgumentParser(
        description='Generate text overlays for peptide video'
    )
    parser.add_argument('--output', default=None, help='Output directory')
    parser.add_argument('--all', action='store_true', help='Generate all overlays')
    parser.add_argument('--peptides', action='store_true', help='Generate peptide lower thirds')
    parser.add_argument('--headers', action='store_true', help='Generate category headers')
    parser.add_argument('--stats', action='store_true', help='Generate statistics')
    parser.add_argument('--disclaimer', action='store_true', help='Generate disclaimer')
    parser.add_argument('--custom', help='Custom text for single overlay')
    parser.add_argument('--type', choices=['lower_third', 'header', 'stat'], help='Type for custom overlay')
    parser.add_argument('--color', default='blue', help='Color for custom overlay')
    parser.add_argument('--font', help='Path to TTF font file')

    args = parser.parse_args()

    # Default output directory
    if not args.output:
        args.output = "/Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer/content/Peptide-Video/Graphics/Static"

    # Create generator
    generator = TextOverlayGenerator(args.output, font_path=args.font)

    try:
        if args.all:
            generator.generate_all()
        elif args.peptides:
            generator.generate_all_peptide_overlays()
        elif args.headers:
            generator.generate_all_category_headers()
        elif args.stats:
            generator.generate_all_statistics()
        elif args.disclaimer:
            generator.create_disclaimer()
        elif args.custom:
            if args.type == 'lower_third':
                generator.create_lower_third(args.custom, "", args.color)
            elif args.type == 'header':
                generator.create_category_header(args.custom, args.color)
            elif args.type == 'stat':
                generator.create_statistic(args.custom, "", args.color)
            else:
                print("Error: --type required with --custom")
                return 1
        else:
            parser.print_help()
            print("\nExamples:")
            print("  python text_overlay_generator.py --all")
            print("  python text_overlay_generator.py --peptides")
            print("  python text_overlay_generator.py --custom 'MY TEXT' --type header --color green")
            return 1

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
