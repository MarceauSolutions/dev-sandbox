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
    Generate branded educational fitness graphics with theme support.
    """

    # Brand theme presets
    THEMES = {
        'marceau': {
            'name': 'Marceau Solutions',
            'primary': '#D4AF37',       # Gold
            'secondary': '#B8860B',     # Dark gold
            'bg_dark': '#1a1a1a',
            'bg_light': '#2a2a2a',
            'text_primary': '#FFFFFF',
            'text_accent': '#D4AF37',
            'tagline': 'EMBRACE THE PAIN & DEFY THE ODDS',
            'brand_name': 'MARCEAU SOLUTIONS',
        },
        'boabfit': {
            'name': 'BOABFIT',
            'primary': '#E84393',       # Hot pink
            'secondary': '#FD79A8',     # Soft pink
            'bg_dark': '#0f0f0f',
            'bg_light': '#1e1e2e',
            'text_primary': '#FFFFFF',
            'text_accent': '#E84393',
            'tagline': 'SCULPT YOUR DREAM BODY',
            'brand_name': 'BOABFIT',
        },
        'dark_gym': {
            'name': 'Dark Gym',
            'primary': '#9B59B6',       # Purple accent
            'secondary': '#8E44AD',
            'bg_dark': '#0a0a0a',
            'bg_light': '#1a1a2e',
            'text_primary': '#FFFFFF',
            'text_accent': '#9B59B6',
            'tagline': '',
            'brand_name': '',
        },
        'clean_minimal': {
            'name': 'Clean Minimal',
            'primary': '#2D3436',       # Charcoal
            'secondary': '#636E72',
            'bg_dark': '#FAFAFA',
            'bg_light': '#FFFFFF',
            'text_primary': '#2D3436',
            'text_accent': '#E84393',
            'tagline': '',
            'brand_name': '',
        },
    }

    # Standard sizes for different platforms
    SIZES = {
        'instagram_post': (1080, 1080),
        'instagram_story': (1080, 1920),
        'youtube_thumbnail': (1280, 720),
        'tiktok': (1080, 1920),
        'instagram_reel': (1080, 1920),
    }

    # Font paths (macOS + Linux)
    FONT_PATHS = {
        'bold': [
            '/System/Library/Fonts/Avenir Next.ttc',
            '/System/Library/Fonts/HelveticaNeue.ttc',
            '/System/Library/Fonts/Supplemental/Futura.ttc',
            '/System/Library/Fonts/Supplemental/Impact.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ],
        'regular': [
            '/System/Library/Fonts/Avenir Next.ttc',
            '/System/Library/Fonts/HelveticaNeue.ttc',
            '/System/Library/Fonts/Avenir.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ],
    }

    def __init__(self, logo_path=None, theme='marceau'):
        """
        Initialize content generator.

        Args:
            logo_path: Path to logo file (PNG with transparency)
            theme: Theme name or dict with custom colors
        """
        self.logo_path = logo_path

        # Load theme
        if isinstance(theme, dict):
            self.theme = theme
        elif theme in self.THEMES:
            self.theme = self.THEMES[theme]
        else:
            self.theme = self.THEMES['marceau']

        # Cache loaded fonts
        self._font_cache = {}

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _create_gradient(self, size, color_top, color_bottom):
        """Create a vertical gradient image."""
        width, height = size
        img = Image.new('RGB', size)
        top = self._hex_to_rgb(color_top)
        bottom = self._hex_to_rgb(color_bottom)

        for y in range(height):
            ratio = y / height
            r = int(top[0] + (bottom[0] - top[0]) * ratio)
            g = int(top[1] + (bottom[1] - top[1]) * ratio)
            b = int(top[2] + (bottom[2] - top[2]) * ratio)
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        return img

    def create_fitness_tip_card(
        self,
        title,
        points,
        background_image=None,
        output_path='fitness_tip.jpg',
        platform='instagram_post'
    ):
        """
        Create educational fitness tip card with brand theme support.

        Args:
            title: Main title text
            points: List of key points (or None for title-only)
            background_image: Path to background image (or None for gradient)
            output_path: Where to save output
            platform: Target platform (affects size)

        Returns:
            Path to generated image
        """
        print(f"\n{'='*70}")
        print(f"EDUCATIONAL CONTENT GENERATOR ({self.theme.get('name', 'Custom')})")
        print(f"{'='*70}")
        print(f"Title: {title}")
        print(f"Platform: {platform}")

        size = self.SIZES.get(platform, self.SIZES['instagram_post'])
        width, height = size
        is_vertical = height > width

        # Create base image
        if background_image and Path(background_image).exists():
            print(f"-> Loading background image...")
            img = Image.open(background_image)
            # Cover-crop to target size
            img_ratio = img.width / img.height
            target_ratio = width / height
            if img_ratio > target_ratio:
                new_h = height
                new_w = int(new_h * img_ratio)
            else:
                new_w = width
                new_h = int(new_w / img_ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            img = img.crop((left, top, left + width, top + height))
            img = img.filter(ImageFilter.GaussianBlur(radius=3))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.5)
        else:
            print(f"-> Creating gradient background...")
            img = self._create_gradient(size, self.theme['bg_dark'], self.theme['bg_light'])

        img = img.convert('RGBA')

        # Add accent stripe at top
        accent_overlay = Image.new('RGBA', size, (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent_overlay)
        accent_rgb = self._hex_to_rgb(self.theme['primary'])
        stripe_height = int(height * 0.006)
        accent_draw.rectangle(
            [(0, 0), (width, stripe_height)],
            fill=(*accent_rgb, 255)
        )
        img = Image.alpha_composite(img, accent_overlay)

        # Determine font sizes based on platform and content density
        num_points = len(points) if points else 0
        if is_vertical:
            title_size = max(52, min(72, int(width * 0.065)))
            point_size = max(36, min(52, int(width * 0.045)))
            brand_size = max(28, min(40, int(width * 0.033)))
            tagline_size = max(22, min(32, int(width * 0.025)))
            # Adjust if many points
            if num_points > 6:
                point_size = max(30, int(point_size * 0.8))
        else:
            title_size = max(48, min(64, int(height * 0.09)))
            point_size = max(32, min(48, int(height * 0.06)))
            brand_size = max(24, min(36, int(height * 0.045)))
            tagline_size = max(18, min(28, int(height * 0.035)))

        title_font = self._load_font(size=title_size, bold=True)
        points_font = self._load_font(size=point_size, bold=False)
        bullet_font = self._load_font(size=int(point_size * 0.8), bold=True)
        brand_font = self._load_font(size=brand_size, bold=True)
        tagline_font = self._load_font(size=tagline_size, bold=False)

        draw = ImageDraw.Draw(img)

        # --- TITLE SECTION ---
        print(f"-> Adding title...")
        title_y = int(height * 0.06) if is_vertical else int(height * 0.08)

        # Title background card
        title_card = Image.new('RGBA', size, (0, 0, 0, 0))
        tc_draw = ImageDraw.Draw(title_card)
        card_padding = int(width * 0.06)
        # Measure title text
        bbox = draw.textbbox((0, 0), title.upper(), font=title_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        card_left = (width - text_w) // 2 - card_padding
        card_right = (width + text_w) // 2 + card_padding
        card_top = title_y - int(card_padding * 0.6)
        card_bottom = title_y + text_h + int(card_padding * 0.6)
        tc_draw.rounded_rectangle(
            [(max(0, card_left), card_top), (min(width, card_right), card_bottom)],
            radius=12,
            fill=(0, 0, 0, 140)
        )
        img = Image.alpha_composite(img, title_card)
        draw = ImageDraw.Draw(img)

        # Draw title text
        draw.text(
            (width // 2, title_y + text_h // 2),
            title.upper(),
            font=title_font,
            fill=self.theme['text_accent'],
            anchor='mm',
            stroke_width=2,
            stroke_fill='#000000'
        )

        # --- POINTS SECTION ---
        if points and num_points > 0:
            print(f"-> Adding {num_points} key points...")

            # Calculate layout for points
            content_top = card_bottom + int(height * 0.04)
            brand_area = int(height * 0.12)
            content_bottom = height - brand_area
            available_height = content_bottom - content_top
            point_spacing = min(
                int(available_height / num_points),
                int(point_size * 2.8)
            )
            # Center points vertically
            total_points_height = num_points * point_spacing
            points_start = content_top + (available_height - total_points_height) // 2

            for i, point in enumerate(points):
                point_y = points_start + (i * point_spacing)
                left_margin = int(width * 0.10)
                right_margin = int(width * 0.90)

                # Numbered bullet with accent color background
                num_label = str(i + 1)
                circle_r = int(point_size * 0.55)
                circle_x = left_margin + circle_r
                circle_y = point_y + int(point_size * 0.4)

                # Draw circle background
                circle_overlay = Image.new('RGBA', size, (0, 0, 0, 0))
                co_draw = ImageDraw.Draw(circle_overlay)
                co_draw.ellipse(
                    [(circle_x - circle_r, circle_y - circle_r),
                     (circle_x + circle_r, circle_y + circle_r)],
                    fill=(*accent_rgb, 200)
                )
                img = Image.alpha_composite(img, circle_overlay)
                draw = ImageDraw.Draw(img)

                # Number inside circle
                draw.text(
                    (circle_x, circle_y),
                    num_label,
                    font=bullet_font,
                    fill='#FFFFFF',
                    anchor='mm'
                )

                # Point text
                text_x = circle_x + circle_r + int(width * 0.04)
                draw.text(
                    (text_x, circle_y),
                    point,
                    font=points_font,
                    fill=self.theme['text_primary'],
                    anchor='lm'
                )

        # --- BRAND SECTION ---
        brand_name = self.theme.get('brand_name', '')
        tagline = self.theme.get('tagline', '')

        if brand_name or tagline:
            print(f"-> Adding branding...")
            # Bottom bar
            bar_overlay = Image.new('RGBA', size, (0, 0, 0, 0))
            bar_draw = ImageDraw.Draw(bar_overlay)
            bar_top = height - int(height * 0.10)
            bar_draw.rectangle(
                [(0, bar_top), (width, height)],
                fill=(0, 0, 0, 180)
            )
            # Accent line above bar
            bar_draw.rectangle(
                [(0, bar_top), (width, bar_top + 3)],
                fill=(*accent_rgb, 200)
            )
            img = Image.alpha_composite(img, bar_overlay)
            draw = ImageDraw.Draw(img)

            if brand_name:
                brand_y = bar_top + int((height - bar_top) * 0.35)
                draw.text(
                    (width // 2, brand_y),
                    brand_name,
                    font=brand_font,
                    fill=self.theme['text_accent'],
                    anchor='mm'
                )

            if tagline:
                tagline_y = bar_top + int((height - bar_top) * 0.70)
                draw.text(
                    (width // 2, tagline_y),
                    tagline,
                    font=tagline_font,
                    fill=self.theme['text_primary'],
                    anchor='mm'
                )

        # Save
        print(f"-> Saving to {output_path}...")
        img.convert('RGB').save(output_path, quality=95, optimize=True)

        print(f"\n  SUCCESS!")
        print(f"   Generated: {output_path}")
        print(f"   Size: {width}x{height}")
        print(f"{'='*70}\n")

        return output_path

    def _load_font(self, size=40, bold=False):
        """
        Load font with fallbacks. Uses cached fonts for performance.

        Args:
            size: Font size
            bold: Use bold variant

        Returns:
            ImageFont object
        """
        cache_key = (size, bold)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        key = 'bold' if bold else 'regular'
        paths = self.FONT_PATHS.get(key, [])

        for font_path in paths:
            if Path(font_path).exists():
                try:
                    # For .ttc files, try index 0 (usually the primary weight)
                    if font_path.endswith('.ttc'):
                        idx = 6 if bold and 'Avenir' in font_path else 0
                        font = ImageFont.truetype(font_path, size, index=idx)
                    else:
                        font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    continue

        # Broader fallback
        fallback_paths = [
            '/Library/Fonts/Arial Unicode.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold
            else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
        for fp in fallback_paths:
            if Path(fp).exists():
                try:
                    font = ImageFont.truetype(fp, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception:
                    continue

        font = ImageFont.load_default()
        self._font_cache[cache_key] = font
        return font

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
                        choices=['instagram_post', 'instagram_story', 'youtube_thumbnail',
                                 'tiktok', 'instagram_reel'],
                        help='Target platform')
    parser.add_argument('--theme', default='marceau',
                        choices=list(EducationalContentGenerator.THEMES.keys()),
                        help='Brand theme preset')
    parser.add_argument('--list-themes', action='store_true',
                        help='List available themes and exit')

    args = parser.parse_args()

    if args.list_themes:
        print("\nAvailable themes:")
        for name, theme in EducationalContentGenerator.THEMES.items():
            print(f"  {name:15s} - {theme['name']} (accent: {theme['primary']})")
        return 0

    # Parse points
    points = []
    if args.points:
        points = [p.strip() for p in args.points.split(',')]
    elif args.points_file and Path(args.points_file).exists():
        with open(args.points_file, 'r') as f:
            points = [line.strip() for line in f if line.strip()]

    # Create generator with theme
    generator = EducationalContentGenerator(logo_path=args.logo, theme=args.theme)

    # Generate graphic
    try:
        output = generator.create_fitness_tip_card(
            title=args.title,
            points=points,
            background_image=args.background,
            output_path=args.output,
            platform=args.platform
        )

        print(f"\nGraphic created successfully!")
        print(f"   Output: {output}")

        return 0

    except Exception as e:
        print(f"\nError generating graphic: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())