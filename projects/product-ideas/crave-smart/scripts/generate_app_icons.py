#!/usr/bin/env python3
"""
Generate App Icons for CraveSmart

Creates all required icon sizes for iOS App Store submission.
Uses PIL to generate a simple branded icon.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# CraveSmart brand colors
PRIMARY_COLOR = (255, 107, 107)  # #FF6B6B - Coral
SECONDARY_COLOR = (255, 180, 180)  # #FFB4B4 - Light coral
WHITE = (255, 255, 255)

# iOS required icon sizes
IOS_SIZES = [
    (1024, "icon.png"),           # App Store
    (180, "icon-180.png"),        # iPhone @3x
    (120, "icon-120.png"),        # iPhone @2x
    (167, "icon-167.png"),        # iPad Pro @2x
    (152, "icon-152.png"),        # iPad @2x
    (76, "icon-76.png"),          # iPad @1x
    (40, "icon-40.png"),          # Spotlight
    (29, "icon-29.png"),          # Settings
]

OUTPUT_DIR = "/Users/williammarceaujr./dev-sandbox/projects/crave-smart/assets/images"


def create_icon(size: int, filename: str):
    """Create a CraveSmart app icon at the specified size."""

    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), PRIMARY_COLOR)
    draw = ImageDraw.Draw(img)

    # Add subtle gradient effect (simplified)
    for y in range(size):
        # Blend from PRIMARY to slightly lighter
        ratio = y / size
        r = int(PRIMARY_COLOR[0] + (SECONDARY_COLOR[0] - PRIMARY_COLOR[0]) * ratio * 0.3)
        g = int(PRIMARY_COLOR[1] + (SECONDARY_COLOR[1] - PRIMARY_COLOR[1]) * ratio * 0.3)
        b = int(PRIMARY_COLOR[2] + (SECONDARY_COLOR[2] - PRIMARY_COLOR[2]) * ratio * 0.3)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Draw chocolate emoji representation (simplified as a rounded square)
    center = size // 2
    emoji_size = int(size * 0.5)

    # Draw a stylized "C" or chocolate bar shape
    padding = int(size * 0.2)

    # Draw rounded rectangle for chocolate bar
    bar_left = padding
    bar_top = padding
    bar_right = size - padding
    bar_bottom = size - padding
    bar_radius = int(size * 0.1)

    # Chocolate brown color
    chocolate = (139, 90, 43)
    chocolate_light = (180, 120, 60)

    # Draw chocolate bar
    draw.rounded_rectangle(
        [bar_left, bar_top, bar_right, bar_bottom],
        radius=bar_radius,
        fill=chocolate
    )

    # Draw grid lines for chocolate segments
    segment_count = 3
    segment_width = (bar_right - bar_left) // segment_count
    segment_height = (bar_bottom - bar_top) // segment_count

    for i in range(1, segment_count):
        # Vertical lines
        x = bar_left + i * segment_width
        draw.line([(x, bar_top + bar_radius), (x, bar_bottom - bar_radius)],
                  fill=chocolate_light, width=max(1, size // 100))
        # Horizontal lines
        y = bar_top + i * segment_height
        draw.line([(bar_left + bar_radius, y), (bar_right - bar_radius, y)],
                  fill=chocolate_light, width=max(1, size // 100))

    # Add a small heart or sparkle in corner
    sparkle_x = size - padding - int(size * 0.1)
    sparkle_y = padding + int(size * 0.05)
    sparkle_size = int(size * 0.08)

    # Simple sparkle/star
    draw.ellipse(
        [sparkle_x - sparkle_size//2, sparkle_y - sparkle_size//2,
         sparkle_x + sparkle_size//2, sparkle_y + sparkle_size//2],
        fill=WHITE
    )

    # Save
    output_path = os.path.join(OUTPUT_DIR, filename)
    img.save(output_path, 'PNG')
    print(f"Created: {filename} ({size}x{size})")

    return output_path


def create_splash_icon(size: int = 200):
    """Create splash screen icon."""

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # White chocolate bar on transparent background
    padding = int(size * 0.1)
    bar_radius = int(size * 0.1)

    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=bar_radius,
        fill=WHITE
    )

    # Chocolate brown segments
    chocolate = (139, 90, 43)
    segment_count = 3
    bar_left = padding + int(size * 0.05)
    bar_top = padding + int(size * 0.05)
    bar_right = size - padding - int(size * 0.05)
    bar_bottom = size - padding - int(size * 0.05)
    segment_width = (bar_right - bar_left) // segment_count
    segment_height = (bar_bottom - bar_top) // segment_count

    for i in range(1, segment_count):
        x = bar_left + i * segment_width
        draw.line([(x, bar_top), (x, bar_bottom)], fill=chocolate, width=2)
        y = bar_top + i * segment_height
        draw.line([(bar_left, y), (bar_right, y)], fill=chocolate, width=2)

    output_path = os.path.join(OUTPUT_DIR, "splash-icon.png")
    img.save(output_path, 'PNG')
    print(f"Created: splash-icon.png ({size}x{size})")


def create_adaptive_icon():
    """Create Android adaptive icon foreground."""

    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Centered chocolate bar (smaller to account for safe zone)
    center = size // 2
    bar_size = int(size * 0.5)
    padding = (size - bar_size) // 2

    chocolate = (139, 90, 43)
    chocolate_light = (180, 120, 60)

    bar_radius = int(bar_size * 0.15)

    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=bar_radius,
        fill=chocolate
    )

    # Grid lines
    segment_count = 3
    bar_left = padding
    bar_top = padding
    bar_right = size - padding
    bar_bottom = size - padding
    segment_width = (bar_right - bar_left) // segment_count
    segment_height = (bar_bottom - bar_top) // segment_count

    for i in range(1, segment_count):
        x = bar_left + i * segment_width
        draw.line([(x, bar_top + bar_radius), (x, bar_bottom - bar_radius)],
                  fill=chocolate_light, width=8)
        y = bar_top + i * segment_height
        draw.line([(bar_left + bar_radius, y), (bar_right - bar_radius, y)],
                  fill=chocolate_light, width=8)

    output_path = os.path.join(OUTPUT_DIR, "adaptive-icon.png")
    img.save(output_path, 'PNG')
    print(f"Created: adaptive-icon.png ({size}x{size})")


def main():
    print("=" * 50)
    print("CraveSmart App Icon Generator")
    print("=" * 50)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\nGenerating iOS icons...")
    for size, filename in IOS_SIZES:
        create_icon(size, filename)

    print("\nGenerating splash icon...")
    create_splash_icon()

    print("\nGenerating Android adaptive icon...")
    create_adaptive_icon()

    print("\n" + "=" * 50)
    print("Done! Icons saved to:")
    print(OUTPUT_DIR)
    print("\nNext steps:")
    print("1. Review icons in assets/images/")
    print("2. Update app.json to reference icon.png (1024x1024)")
    print("3. Run: npx eas build --platform ios")


if __name__ == "__main__":
    main()
