#!/usr/bin/env python3
"""
CraveSmart Promotional Video Generator

Uses Creatomate API to generate an emotional hook video
for the landing page / app store listing.

Video Concept: "The Dinner Dilemma"
- Quick cuts of couple's frustration over "what to eat"
- Transition to science reveal
- Solution reveal with app preview
- Emotional payoff

Duration: 15-30 seconds (optimized for social/app store)
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv('/Users/williammarceaujr./dev-sandbox/.env')

CREATOMATE_API_KEY = os.getenv('CREATOMATE_API_KEY')

# Video storyboard - emotional narrative arc
STORYBOARD = [
    {
        "scene": 1,
        "duration": 2.5,
        "visual": "text_overlay",
        "text": '"I don\'t know, you pick."',
        "subtext": "Every. Single. Time.",
        "emotion": "frustration",
        "background": "dark_gradient",
        "audio": "subtle_tension"
    },
    {
        "scene": 2,
        "duration": 2.0,
        "visual": "text_overlay",
        "text": "Pizza?",
        "subtext": '"Not feeling it."',
        "emotion": "rejection",
        "background": "dark_gradient",
        "audio": "rejection_sound"
    },
    {
        "scene": 3,
        "duration": 2.0,
        "visual": "text_overlay",
        "text": "Tacos?",
        "subtext": '"No."',
        "emotion": "rejection",
        "background": "dark_gradient",
        "audio": "rejection_sound"
    },
    {
        "scene": 4,
        "duration": 2.5,
        "visual": "text_overlay",
        "text": "Another dinner ruined.",
        "subtext": "",
        "emotion": "defeat",
        "background": "very_dark",
        "audio": "sad_piano_note"
    },
    {
        "scene": 5,
        "duration": 3.0,
        "visual": "reveal",
        "text": "But what if her cravings...",
        "subtext": "weren't random?",
        "emotion": "curiosity",
        "background": "gradient_transition",
        "audio": "intrigue_swell"
    },
    {
        "scene": 6,
        "duration": 3.0,
        "visual": "science_reveal",
        "text": "91.78% of women",
        "subtext": "have predictable, cycle-based cravings",
        "emotion": "revelation",
        "background": "coral_gradient",
        "audio": "hopeful_build"
    },
    {
        "scene": 7,
        "duration": 3.0,
        "visual": "app_mockup",
        "text": "Day 22: She wants chocolate.",
        "subtext": "Now you know.",
        "emotion": "empowerment",
        "background": "coral_gradient",
        "audio": "triumphant"
    },
    {
        "scene": 8,
        "duration": 4.0,
        "visual": "logo_cta",
        "text": "CraveSmart",
        "subtext": "Stop guessing. Start knowing.",
        "emotion": "resolution",
        "background": "coral_gradient",
        "audio": "resolution_chord"
    }
]

# Video format presets - use correct aspect ratios to avoid distortion
VIDEO_FORMATS = {
    "story": {
        "name": "Instagram/TikTok Story",
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "use_case": "Social media stories, mobile app previews"
    },
    "square": {
        "name": "Instagram Feed",
        "width": 1080,
        "height": 1080,
        "aspect_ratio": "1:1",
        "use_case": "Instagram feed, Facebook feed"
    },
    "landscape": {
        "name": "Website/YouTube",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "use_case": "Website hero, YouTube, presentations"
    },
    "portrait": {
        "name": "Mobile Portrait",
        "width": 1080,
        "height": 1350,
        "aspect_ratio": "4:5",
        "use_case": "Instagram portrait posts"
    }
}

# Default to landscape for website use
SELECTED_FORMAT = "landscape"

# Creatomate template configuration
VIDEO_CONFIG = {
    "output_format": "mp4",
    "width": VIDEO_FORMATS[SELECTED_FORMAT]["width"],
    "height": VIDEO_FORMATS[SELECTED_FORMAT]["height"],
    "frame_rate": 30,
    "duration": sum(s["duration"] for s in STORYBOARD),

    # Brand colors
    "colors": {
        "primary": "#FF6B6B",
        "secondary": "#FFB4B4",
        "dark": "#1a1a1a",
        "white": "#ffffff"
    },

    # Typography
    "fonts": {
        "heading": "Inter-Bold",
        "body": "Inter-Regular"
    }
}


def create_video_json():
    """Generate Creatomate-compatible JSON for video generation."""

    elements = []
    current_time = 0

    for scene in STORYBOARD:
        # Main text element
        elements.append({
            "type": "text",
            "text": scene["text"],
            "font_family": VIDEO_CONFIG["fonts"]["heading"],
            "font_size": 72 if scene["visual"] == "logo_cta" else 56,
            "color": VIDEO_CONFIG["colors"]["white"],
            "x": "50%",
            "y": "40%",
            "width": "80%",
            "text_align": "center",
            "time": current_time,
            "duration": scene["duration"],
            "animations": [
                {
                    "type": "fade",
                    "fade": "in",
                    "duration": 0.3
                },
                {
                    "type": "fade",
                    "fade": "out",
                    "start_time": scene["duration"] - 0.3,
                    "duration": 0.3
                }
            ]
        })

        # Subtext element
        if scene["subtext"]:
            elements.append({
                "type": "text",
                "text": scene["subtext"],
                "font_family": VIDEO_CONFIG["fonts"]["body"],
                "font_size": 32,
                "color": "rgba(255,255,255,0.8)",
                "x": "50%",
                "y": "55%",
                "width": "80%",
                "text_align": "center",
                "time": current_time + 0.5,
                "duration": scene["duration"] - 0.5,
                "animations": [
                    {
                        "type": "fade",
                        "fade": "in",
                        "duration": 0.3
                    }
                ]
            })

        current_time += scene["duration"]

    # Background gradient
    background = {
        "type": "composition",
        "elements": [
            {
                "type": "shape",
                "shape": "rectangle",
                "width": "100%",
                "height": "100%",
                "fill": {
                    "type": "linear-gradient",
                    "colors": [
                        {"offset": 0, "color": "#FF6B6B"},
                        {"offset": 0.5, "color": "#FF8E8E"},
                        {"offset": 1, "color": "#FFB4B4"}
                    ],
                    "angle": 135
                }
            }
        ]
    }

    return {
        "output_format": "mp4",
        "width": VIDEO_CONFIG["width"],
        "height": VIDEO_CONFIG["height"],
        "frame_rate": VIDEO_CONFIG["frame_rate"],
        "elements": [background] + elements
    }


def generate_video():
    """Submit video generation request to Creatomate API."""

    if not CREATOMATE_API_KEY:
        print("Error: CREATOMATE_API_KEY not set in .env")
        print("\nTo generate the video, add your Creatomate API key to .env")
        print("Then run this script again.")

        # Save the JSON template for manual use
        template = create_video_json()
        output_path = '/Users/williammarceaujr./dev-sandbox/projects/crave-smart/scripts/video_template.json'
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"\nVideo template saved to: {output_path}")
        print("You can use this template directly in Creatomate's web interface.")
        return None

    template = create_video_json()

    response = requests.post(
        'https://api.creatomate.com/v1/renders',
        headers={
            'Authorization': f'Bearer {CREATOMATE_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'source': template
        }
    )

    if response.status_code in [200, 201, 202]:
        result = response.json()
        print(f"Video generation started!")
        print(f"Render ID: {result[0]['id']}")
        print(f"Video URL (available when complete): {result[0]['url']}")
        print(f"Status: {result[0]['status']}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def main():
    global SELECTED_FORMAT, VIDEO_CONFIG

    # Parse command line arguments
    if len(sys.argv) > 1:
        requested_format = sys.argv[1].lower()
        if requested_format in VIDEO_FORMATS:
            SELECTED_FORMAT = requested_format
            VIDEO_CONFIG["width"] = VIDEO_FORMATS[SELECTED_FORMAT]["width"]
            VIDEO_CONFIG["height"] = VIDEO_FORMATS[SELECTED_FORMAT]["height"]
        elif requested_format == "--help" or requested_format == "-h":
            print("Usage: python generate_promo_video.py [format]")
            print("\nAvailable formats:")
            for key, fmt in VIDEO_FORMATS.items():
                print(f"  {key:12} - {fmt['width']}x{fmt['height']} ({fmt['aspect_ratio']}) - {fmt['use_case']}")
            print("\nDefault: landscape (1920x1080)")
            return
        else:
            print(f"Unknown format: {requested_format}")
            print(f"Available: {', '.join(VIDEO_FORMATS.keys())}")
            return

    fmt = VIDEO_FORMATS[SELECTED_FORMAT]

    print("=" * 50)
    print("CraveSmart Promotional Video Generator")
    print("=" * 50)
    print(f"\nFormat: {fmt['name']} ({fmt['aspect_ratio']})")
    print(f"Resolution: {fmt['width']}x{fmt['height']}")
    print(f"Duration: {VIDEO_CONFIG['duration']} seconds")
    print(f"Scenes: {len(STORYBOARD)}")
    print("\nStoryboard:")
    print("-" * 40)

    for scene in STORYBOARD:
        print(f"  Scene {scene['scene']} ({scene['duration']}s): {scene['text'][:30]}...")

    print("\n" + "-" * 40)
    print("\nGenerating video...")

    result = generate_video()

    if result:
        print("\nVideo will be available at the URL above once rendering completes.")
        print("Typical render time: 30-60 seconds")
        print(f"\nTo generate other formats, run:")
        for key in VIDEO_FORMATS:
            if key != SELECTED_FORMAT:
                print(f"  python generate_promo_video.py {key}")


if __name__ == "__main__":
    main()
