#!/usr/bin/env python3
"""
Generate a modern weekly weather report PDF for Naples, Florida.
Uses template design from .tmp/modern weekly report.PNG
"""

import json
from datetime import datetime
from pathlib import Path
from io import BytesIO
import requests

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image, ImageDraw
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install reportlab pillow")
    exit(1)

# Color scheme from template
ORANGE = colors.HexColor('#F39C12')
DARK_BLUE = colors.HexColor('#1A1A2E')
WHITE = colors.white

def load_weather_data():
    """Load weather data from .tmp directory."""
    data_file = Path(__file__).parent.parent / '.tmp' / 'naples_weather_data.json'

    if not data_file.exists():
        print(f"✗ Weather data not found at {data_file}")
        print("Run fetch_naples_weather.py first!")
        return None

    with open(data_file, 'r') as f:
        data = json.load(f)

    print(f"✓ Loaded weather data from {data_file}")
    return data

def download_naples_image():
    """
    Download a Naples, FL image from a free source.
    Using Unsplash as a reliable free image source.
    """
    tmp_dir = Path(__file__).parent.parent / '.tmp'
    image_path = tmp_dir / 'naples_hero.jpg'

    # Check if we already have the image
    if image_path.exists():
        print(f"✓ Using cached hero image")
        return str(image_path)

    # Download Naples image from Unsplash (free to use)
    # Using a generic Florida beach/coastal image
    try:
        url = "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1920&h=1080&fit=crop"
        print("Downloading hero image...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(image_path, 'wb') as f:
            f.write(response.content)

        print(f"✓ Downloaded hero image to {image_path}")
        return str(image_path)

    except Exception as e:
        print(f"⚠ Could not download image: {e}")
        print("Will create a placeholder image")
        return None

def create_circular_image(image_path, size=400):
    """Create a circular cropped version of the image."""
    if not image_path:
        # Create a placeholder blue circle
        img = Image.new('RGB', (size, size), DARK_BLUE.hexval())
        return img

    img = Image.open(image_path)

    # Resize and crop to square
    img = img.convert('RGB')
    min_dim = min(img.size)

    # Center crop to square
    left = (img.width - min_dim) // 2
    top = (img.height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))

    # Resize to target size
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    # Create circular mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    # Apply mask
    output = Image.new('RGB', (size, size), (255, 255, 255))
    output.paste(img, (0, 0))
    output.putalpha(mask)

    return output

def get_weather_emoji(forecast_text):
    """Map weather conditions to simple emoji/symbols."""
    forecast_lower = forecast_text.lower()

    if 'rain' in forecast_lower or 'shower' in forecast_lower:
        return '🌧'
    elif 'storm' in forecast_lower or 'thunder' in forecast_lower:
        return '⛈'
    elif 'cloud' in forecast_lower:
        return '☁'
    elif 'sun' in forecast_lower or 'clear' in forecast_lower:
        return '☀'
    elif 'partly' in forecast_lower:
        return '⛅'
    else:
        return '🌤'

def generate_report(weather_data):
    """Generate the PDF report."""
    tmp_dir = Path(__file__).parent.parent / '.tmp'

    # Output filename with date
    today = datetime.now().strftime('%Y%m%d')
    output_file = tmp_dir / f'naples_weather_report_{today}.pdf'

    # Create PDF
    c = canvas.Canvas(str(output_file), pagesize=letter)
    width, height = letter

    # Set up fonts
    c.setTitle("Naples FL Weekly Weather Report")

    # Background - Split design like template
    # Orange arc on left
    c.setFillColor(ORANGE)
    c.circle(0, height * 0.7, 300, fill=1, stroke=0)

    # Dark navy arc on right
    c.setFillColor(DARK_BLUE)
    c.circle(width, height * 0.3, 400, fill=1, stroke=0)

    # White main area
    c.setFillColor(WHITE)
    c.rect(50, 100, width - 100, height - 200, fill=1, stroke=0)

    # Add circular hero image
    hero_image_path = download_naples_image()
    circular_img = create_circular_image(hero_image_path, size=300)

    # Save circular image temporarily
    img_buffer = BytesIO()
    circular_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    img_reader = ImageReader(img_buffer)
    img_x = width - 250
    img_y = height - 350
    c.drawImage(img_reader, img_x, img_y, width=300, height=300, mask='auto')

    # Title: "WEEKLY WEATHER REPORT"
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(60, height - 280, "WEEKLY")
    c.drawString(60, height - 320, "WEATHER")
    c.drawString(60, height - 360, "REPORT")

    # Date
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 14)
    date_str = datetime.now().strftime('%d %B %Y').upper()
    c.drawString(60, height - 390, date_str)

    # Author info
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica", 9)
    c.drawString(60, height - 430, "From")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, height - 445, "Weather Automation System")
    c.setFont("Helvetica", 9)
    c.drawString(60, height - 460, "NAPLES, FLORIDA")

    # Forecast section
    y_position = height - 520

    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, y_position, "7-Day Forecast")

    y_position -= 30

    # Group forecast by days (combine day + night)
    forecast = weather_data['forecast']
    days_shown = 0

    for i in range(0, len(forecast), 2):
        if days_shown >= 7:
            break

        period = forecast[i]

        # Day name
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(DARK_BLUE)
        c.drawString(60, y_position, period['name'])

        # Temperature
        temp_str = f"{period['temperature']}°{period['temperatureUnit']}"
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(ORANGE)
        c.drawString(180, y_position, temp_str)

        # Weather emoji and condition
        c.setFont("Helvetica", 20)
        emoji = get_weather_emoji(period['shortForecast'])
        c.drawString(260, y_position - 5, emoji)

        c.setFont("Helvetica", 10)
        c.setFillColor(DARK_BLUE)
        c.drawString(300, y_position, period['shortForecast'][:35])

        y_position -= 25
        days_shown += 1

        # Page break if needed
        if y_position < 100:
            break

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(60, 50, f"Data source: National Weather Service • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Save PDF
    c.save()

    print(f"✓ Generated report: {output_file}")
    return output_file

def main():
    print("Generating Naples FL Weekly Weather Report...")
    print()

    # Load weather data
    weather_data = load_weather_data()
    if not weather_data:
        return 1

    # Generate report
    output_file = generate_report(weather_data)

    print()
    print("=" * 50)
    print("Report generated successfully!")
    print(f"Output: {output_file}")
    print("=" * 50)

    return 0

if __name__ == "__main__":
    exit(main())
