#!/usr/bin/env python3
"""
educational_graphics.py - Branded Fitness Content Generator

WHAT: Creates branded educational graphics matching Fitness_Tips.jpeg style
WHY: Generate professional, consistent fitness content for social media
INPUT: Title text, key points (list), platform type, optional background image
OUTPUT: Branded graphic (JPG/PNG) sized for target platform
COST: FREE (uses Pillow for graphics)
TIME: <10 seconds per graphic

QUICK USAGE:
  python educational_graphics.py --title "Staying Lean" --points "Eat protein,Lift weights,Stay active"

CAPABILITIES:
  - Branded educational cards with Marceau Solutions styling
  - Multiple platform formats (Instagram Post/Story, YouTube, TikTok)
  - Consistent gold & black theme
  - Logo and text overlay with custom fonts
  - Background image support or solid color gradients

DEPENDENCIES: pillow
API_KEYS: None required

---
Original Features:
- Branded educational cards
- Multiple platform formats (Instagram, YouTube, TikTok)
- Consistent styling
- Logo and text overlay

Usage:
    python educational_graphics.py --title "Staying Lean" --points "Eat protein,Lift weights,Stay active"
    python educational_graphics.py --title "Workout Tips" --points-file tips.txt --background image.jpg
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    print("ERROR: Pillow not installed")
    print("Install with: pip install pillow")
    sys.exit(1)


class EducationalContentGenerator:
    """
    Generate branded educational fitness graphics.
    """

    # Brand colors (Marceau Solutions gold theme)
    BRAND_COLORS = {
        'gold': '#D4AF37',
        'dark_gold': '#B8860B',
        'black': '#000000',
        'white': '#FFFFFF',
        'overlay_dark': 'rgba(0, 0, 0, 0.7)',
    }

    # Standard sizes for different platforms
    SIZES = {
        'instagram_post': (1080, 1080),
        'instagram_story': (1080, 1920),
        'youtube_thumbnail': (1280, 720),
        'tiktok': (1080, 1920),
    }

    def __init__(self, logo_path=None):
        """
        Initialize content generator.

        Args:
            logo_path: Path to logo file (PNG with transparency)
        """
        self.logo_path = logo_path

    def create_fitness_tip_card(
        self,
        title,
        points,
        background_image=None,
        output_path='fitness_tip.jpg',
        platform='instagram_post'
    ):
        """
        Create educational fitness tip card in Fitness_Tips.jpeg style.

        Args:
            title: Main title text
            points: List of key points (or None for title-only)
            background_image: Path to background image (or None for solid color)
            output_path: Where to save output
            platform: Target platform (affects size)

        Returns:
            Path to generated image
        """
        print(f"\\n{'='*70}")
        print(f"EDUCATIONAL CONTENT GENERATOR")
        print(f"{'='*70}")
        print(f"Title: {title}")
        print(f"Platform: {platform}")

        # Get size for platform
        size = self.SIZES.get(platform, self.SIZES['instagram_post'])
        width, height = size

        # Create base image
        if background_image and Path(background_image).exists():
            print(f"→ Loading background image...")
            img = Image.open(background_image)
            img = img.resize(size, Image.Resampling.LANCZOS)

            # Apply slight blur for better text readability
            img = img.filter(ImageFilter.GaussianBlur(radius=2))

            # Darken image slightly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.7)
        else:
            print(f"→ Creating solid background...")
            # Create gradient background (dark to slightly lighter)
            img = Image.new('RGB', size, color='#1a1a1a')

        draw = ImageDraw.Draw(img, 'RGBA')

        # Add semi-transparent overlay for text readability
        overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Top overlay for title
        overlay_draw.rectangle(
            [(0, 0), (width, int(height * 0.25))],
            fill=(0, 0, 0, 180)
        )

        # Bottom overlay for branding
        overlay_draw.rectangle(
            [(0, int(height * 0.75)), (width, height)],
            fill=(0, 0, 0, 200)
        )

        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Load fonts (try multiple common font paths)
        title_font = self._load_font(size=80, bold=True)
        subtitle_font = self._load_font(size=50, bold=False)
        points_font = self._load_font(size=40, bold=False)
        brand_font = self._load_font(size=35, bold=True)
        tagline_font = self._load_font(size=25, bold=False)

        # Draw title at top with gold color and outline
        print(f"→ Adding title...")
        title_y = int(height * 0.08)

        # Title with stroke effect
        self._draw_text_with_stroke(
            draw,
            (width // 2, title_y),
            title,
            title_font,
            fill=self.BRAND_COLORS['gold'],
            stroke_width=3,
            stroke_fill=self.BRAND_COLORS['black']
        )

        # Draw points if provided
        if points and len(points) > 0:
            print(f"→ Adding {len(points)} key points...")

            # Calculate starting position for points (centered vertically)
            points_start_y = int(height * 0.35)
            points_spacing = int(height * 0.12)

            for i, point in enumerate(points):
                point_y = points_start_y + (i * points_spacing)

                # Add bullet point
                bullet_x = int(width * 0.15)
                bullet = "•"

                draw.text(
                    (bullet_x, point_y),
                    bullet,
                    font=points_font,
                    fill=self.BRAND_COLORS['gold'],
                    anchor='lm'
                )

                # Add point text
                text_x = int(width * 0.20)
                draw.text(
                    (text_x, point_y),
                    point,
                    font=points_font,
                    fill=self.BRAND_COLORS['white'],
                    anchor='lm'
                )

        # Add logo if available
        if self.logo_path and Path(self.logo_path).exists():
            print(f"→ Adding logo...")
            self._add_logo(img, position='bottom_center', size_ratio=0.15)

        # Add branding text
        print(f"→ Adding branding...")
        brand_y = int(height * 0.88)

        draw.text(
            (width // 2, brand_y),
            "MARCEAU SOLUTIONS",
            font=brand_font,
            fill=self.BRAND_COLORS['gold'],
            anchor='mm'
        )

        # Add tagline
        tagline_y = int(height * 0.93)
        draw.text(
            (width // 2, tagline_y),
            "EMBRACE THE PAIN & DEFY THE ODDS",
            font=tagline_font,
            fill=self.BRAND_COLORS['white'],
            anchor='mm'
        )

        # Save image
        print(f"→ Saving to {output_path}...")
        img.save(output_path, quality=95, optimize=True)

        print(f"\\n✅ SUCCESS!")
        print(f"   Generated: {output_path}")
        print(f"   Size: {width}x{height}")
        print(f"{'='*70}\\n")

        return output_path

    def _load_font(self, size=40, bold=False):
        """
        Load font with fallbacks.

        Args:
            size: Font size
            bold: Use bold variant

        Returns:
            ImageFont object
        """
        # Try common font paths
        font_names = [
            # Bold fonts
            'Arial-Bold.ttf',
            'Helvetica-Bold.ttf',
            'DejaVuSans-Bold.ttf',
            # Regular fonts
            'Arial.ttf',
            'Helvetica.ttf',
            'DejaVuSans.ttf',
        ] if bold else [
            'Arial.ttf',
            'Helvetica.ttf',
            'DejaVuSans.ttf',
        ]

        # Common font directories
        font_dirs = [
            '/System/Library/Fonts/',
            '/Library/Fonts/',
            '~/Library/Fonts/',
            '/usr/share/fonts/',
            '/usr/share/fonts/truetype/dejavu/',
            'C:\\Windows\\Fonts\\',
        ]

        for font_name in font_names:
            for font_dir in font_dirs:
                font_path = Path(font_dir).expanduser() / font_name
                if font_path.exists():
                    try:
                        return ImageFont.truetype(str(font_path), size)
                    except Exception:
                        continue

        # Fallback to default font
        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def _draw_text_with_stroke(self, draw, position, text, font, fill, stroke_width=2, stroke_fill='black'):
        """
        Draw text with outline/stroke effect.

        Args:
            draw: ImageDraw object
            position: (x, y) tuple
            text: Text to draw
            font: Font object
            fill: Text color
            stroke_width: Outline thickness
            stroke_fill: Outline color
        """
        x, y = position

        # Draw stroke by drawing text at slight offsets
        for offset_x in range(-stroke_width, stroke_width + 1):
            for offset_y in range(-stroke_width, stroke_width + 1):
                draw.text(
                    (x + offset_x, y + offset_y),
                    text,
                    font=font,
                    fill=stroke_fill,
                    anchor='mm'
                )

        # Draw main text
        draw.text(
            position,
            text,
            font=font,
            fill=fill,
            anchor='mm'
        )

    def _add_logo(self, img, position='bottom_center', size_ratio=0.1):
        """
        Add logo to image.

        Args:
            img: PIL Image object
            position: Logo position
            size_ratio: Logo size as ratio of image width
        """
        try:
            logo = Image.open(self.logo_path)

            # Resize logo
            logo_width = int(img.width * size_ratio)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Calculate position
            if position == 'bottom_center':
                x = (img.width - logo_width) // 2
                y = int(img.height * 0.75) - logo_height - 20
            elif position == 'bottom_right':
                x = img.width - logo_width - 40
                y = img.height - logo_height - 40
            else:  # top_right
                x = img.width - logo_width - 40
                y = 40

            # Paste logo (handle transparency)
            if logo.mode == 'RGBA':
                img.paste(logo, (x, y), logo)
            else:
                img.paste(logo, (x, y))

        except Exception as e:
            print(f"  ⚠️  Warning: Could not add logo: {e}")

    def create_batch(self, configs):
        """
        Generate multiple graphics from configurations.

        Args:
            configs: List of dicts with title, points, background, output, platform

        Returns:
            List of output paths
        """
        outputs = []

        for i, config in enumerate(configs):
            print(f"\\n📋 Processing {i+1}/{len(configs)}")

            output = self.create_fitness_tip_card(
                title=config.get('title'),
                points=config.get('points', []),
                background_image=config.get('background'),
                output_path=config.get('output', f'tip_{i+1}.jpg'),
                platform=config.get('platform', 'instagram_post')
            )

            outputs.append(output)

        return outputs


def main():
    """CLI for educational graphics generator."""
    parser = argparse.ArgumentParser(
        description='Educational Fitness Content Generator - Create branded graphics'
    )
    parser.add_argument('--title', required=True, help='Main title text')
    parser.add_argument('--points', help='Comma-separated key points')
    parser.add_argument('--points-file', help='File with one point per line')
    parser.add_argument('--background', help='Background image path')
    parser.add_argument('--logo', help='Logo image path')
    parser.add_argument('--output', default='fitness_tip.jpg', help='Output file path')
    parser.add_argument('--platform', default='instagram_post',
                        choices=['instagram_post', 'instagram_story', 'youtube_thumbnail', 'tiktok'],
                        help='Target platform')

    args = parser.parse_args()

    # Parse points
    points = []
    if args.points:
        points = [p.strip() for p in args.points.split(',')]
    elif args.points_file and Path(args.points_file).exists():
        with open(args.points_file, 'r') as f:
            points = [line.strip() for line in f if line.strip()]

    # Create generator
    generator = EducationalContentGenerator(logo_path=args.logo)

    # Generate graphic
    try:
        output = generator.create_fitness_tip_card(
            title=args.title,
            points=points,
            background_image=args.background,
            output_path=args.output,
            platform=args.platform
        )

        print(f"\\n🎨 Graphic created successfully!")
        print(f"   Output: {output}")

        return 0

    except Exception as e:
        print(f"\\n✗ Error generating graphic: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())