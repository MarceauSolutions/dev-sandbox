#!/usr/bin/env python3
"""
video_template_framework.py - Video Blueprint Generator

WHAT: Generates viral video templates with segment-by-segment scripts
WHY: Help fitness influencers create structured content without automation complexity
INPUT: Topic, style, duration, platform
OUTPUT: Interactive timeline HTML with scripts and visual hints
COST: FREE (uses existing Claude API)

QUICK USAGE:
    from video_template_framework import VideoTemplateGenerator, generate_timeline_html

    generator = VideoTemplateGenerator()
    template = generator.generate_template(
        topic="5 best exercises for abs",
        style="educational",
        target_duration=60,
        platform="instagram_reels"
    )
    html = generate_timeline_html(template)

TEMPLATE STYLES:
    - educational: Quick tips format (hook → tips → CTA)
    - transformation: Before/after journey (before → struggle → journey → after → CTA)
    - day_in_life: Daily routine format (morning → workout → meals → evening → CTA)
    - before_after: Quick transformation (before shot → transition → after shot → CTA)
    - workout_demo: Exercise demonstration (intro → demo → mistakes → proper form → CTA)
"""

import os
import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Try to import anthropic, but don't fail if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class VideoSegment:
    """Represents a single segment in a video template."""
    segment_number: int
    start_time: float
    duration: float
    content_type: str  # "hook", "talking_head", "b_roll", "cta", "text_overlay"
    script_suggestion: str
    visual_hint: str


@dataclass
class VideoTemplate:
    """Complete video template with all segments."""
    name: str
    style: str
    total_duration: int
    segments: List[VideoSegment]
    hashtag_suggestions: List[str]
    platform: str
    tips: Optional[str] = None


class VideoTemplateGenerator:
    """Generates video templates using Claude API."""

    # Pre-built template archetypes for fallback
    TEMPLATE_ARCHETYPES = {
        "educational": {
            "name": "Quick Tips",
            "description": "Quick tips format - great for sharing knowledge",
            "structure": [
                {"content_type": "hook", "duration_pct": 5, "hint": "Attention-grabbing question or statement"},
                {"content_type": "talking_head", "duration_pct": 25, "hint": "Introduce the tips"},
                {"content_type": "b_roll", "duration_pct": 20, "hint": "Demonstrate tip 1"},
                {"content_type": "talking_head", "duration_pct": 20, "hint": "Explain tip 2"},
                {"content_type": "b_roll", "duration_pct": 15, "hint": "Demonstrate tip 3"},
                {"content_type": "cta", "duration_pct": 15, "hint": "Call to action - follow/save/share"}
            ]
        },
        "transformation": {
            "name": "Transformation Story",
            "description": "Before/after journey - emotional and inspiring",
            "structure": [
                {"content_type": "hook", "duration_pct": 5, "hint": "Before photo/clip teaser"},
                {"content_type": "talking_head", "duration_pct": 20, "hint": "Describe the struggle"},
                {"content_type": "b_roll", "duration_pct": 35, "hint": "Journey montage"},
                {"content_type": "talking_head", "duration_pct": 20, "hint": "Reveal the transformation"},
                {"content_type": "cta", "duration_pct": 20, "hint": "Inspire viewers to start their journey"}
            ]
        },
        "day_in_life": {
            "name": "Day in the Life",
            "description": "Daily routine format - relatable and engaging",
            "structure": [
                {"content_type": "hook", "duration_pct": 5, "hint": "Morning alarm or wake-up shot"},
                {"content_type": "b_roll", "duration_pct": 20, "hint": "Morning routine"},
                {"content_type": "b_roll", "duration_pct": 30, "hint": "Workout highlights"},
                {"content_type": "b_roll", "duration_pct": 20, "hint": "Meal prep / nutrition"},
                {"content_type": "talking_head", "duration_pct": 15, "hint": "Evening reflection"},
                {"content_type": "cta", "duration_pct": 10, "hint": "Follow for more"}
            ]
        },
        "before_after": {
            "name": "Before/After Quick",
            "description": "Quick transformation reveal - high impact",
            "structure": [
                {"content_type": "hook", "duration_pct": 20, "hint": "Before shot with text overlay"},
                {"content_type": "transition", "duration_pct": 10, "hint": "Dramatic transition effect"},
                {"content_type": "b_roll", "duration_pct": 50, "hint": "After reveal with confident pose"},
                {"content_type": "cta", "duration_pct": 20, "hint": "Caption with journey details"}
            ]
        },
        "workout_demo": {
            "name": "Workout Demo",
            "description": "Exercise demonstration - educational and practical",
            "structure": [
                {"content_type": "hook", "duration_pct": 8, "hint": "Exercise name + muscle targeted"},
                {"content_type": "b_roll", "duration_pct": 35, "hint": "Full exercise demonstration"},
                {"content_type": "text_overlay", "duration_pct": 20, "hint": "Common mistakes to avoid"},
                {"content_type": "b_roll", "duration_pct": 25, "hint": "Proper form slow-mo"},
                {"content_type": "cta", "duration_pct": 12, "hint": "Save this for your next workout"}
            ]
        }
    }

    # Platform-specific recommendations
    PLATFORM_TIPS = {
        "tiktok": "Use trending sounds, quick cuts, text overlays. First 3 seconds are crucial.",
        "instagram_reels": "Clean aesthetic, smooth transitions. Hook in first 1-2 seconds.",
        "youtube_shorts": "Can be slightly longer. Good for educational content.",
        "youtube": "More detailed explanations okay. Include chapters for long-form."
    }

    def __init__(self):
        """Initialize the generator with Claude API if available."""
        self.claude = None
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.claude = anthropic.Anthropic()

    def generate_template(
        self,
        topic: str,
        style: str = "educational",
        target_duration: int = 60,
        platform: str = "instagram_reels"
    ) -> Dict[str, Any]:
        """
        Generate a complete video template.

        Args:
            topic: Video topic (e.g., "5 best exercises for abs")
            style: Template style (educational, transformation, day_in_life, before_after, workout_demo)
            target_duration: Target duration in seconds (30-180)
            platform: Target platform (tiktok, instagram_reels, youtube_shorts, youtube)

        Returns:
            Dict with template data including segments, scripts, and suggestions
        """
        # Try AI generation first
        if self.claude:
            try:
                return self._generate_with_claude(topic, style, target_duration, platform)
            except Exception as e:
                print(f"Claude generation failed, using fallback: {e}")

        # Fallback to archetype-based generation
        return self._generate_fallback_template(topic, style, target_duration, platform)

    def _generate_with_claude(
        self,
        topic: str,
        style: str,
        target_duration: int,
        platform: str
    ) -> Dict[str, Any]:
        """Generate template using Claude API."""

        platform_tip = self.PLATFORM_TIPS.get(platform, "")

        prompt = f"""Create a viral fitness video template for: "{topic}"

Style: {style}
Duration: {target_duration} seconds
Platform: {platform}
Platform tip: {platform_tip}

Generate a JSON response with this EXACT structure (no markdown, just JSON):
{{
    "name": "Short catchy template name",
    "segments": [
        {{
            "segment_number": 1,
            "start_time": 0,
            "duration": 3,
            "content_type": "hook",
            "script_suggestion": "Exact words to say or text to show",
            "visual_hint": "Specific description of what to film"
        }},
        {{
            "segment_number": 2,
            "start_time": 3,
            "duration": 15,
            "content_type": "talking_head",
            "script_suggestion": "Next part of the script...",
            "visual_hint": "What to show..."
        }}
    ],
    "hashtag_suggestions": ["fitness", "workout", "gym", "health", "fitnessmotivation"],
    "tips": "Brief filming tips for this specific video"
}}

IMPORTANT RULES:
1. Content types must be one of: hook, talking_head, b_roll, cta, text_overlay, transition
2. Total duration of all segments must equal {target_duration} seconds
3. start_time must be cumulative (segment 2 starts where segment 1 ends)
4. Scripts should be conversational, actionable, and specific to the topic
5. Visual hints should describe exactly what to film (not vague)
6. Include 4-7 segments depending on duration
7. Always start with a strong hook (2-5 seconds)
8. Always end with a clear CTA

Make it viral-worthy - think about what makes fitness content shareable!"""

        response = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        text = response.content[0].text

        # Find JSON in response (handle potential markdown wrapping)
        start = text.find('{')
        end = text.rfind('}') + 1

        if start >= 0 and end > start:
            json_str = text[start:end]
            template_data = json.loads(json_str)

            # Ensure required fields
            template_data["style"] = style
            template_data["total_duration"] = target_duration
            template_data["platform"] = platform

            return template_data

        # If JSON extraction fails, use fallback
        return self._generate_fallback_template(topic, style, target_duration, platform)

    def _generate_fallback_template(
        self,
        topic: str,
        style: str,
        target_duration: int,
        platform: str
    ) -> Dict[str, Any]:
        """Generate template using pre-built archetypes when Claude is unavailable."""

        # Get archetype or default to educational
        archetype = self.TEMPLATE_ARCHETYPES.get(style, self.TEMPLATE_ARCHETYPES["educational"])

        segments = []
        current_time = 0

        for i, seg_template in enumerate(archetype["structure"], 1):
            duration = int(target_duration * seg_template["duration_pct"] / 100)

            # Generate basic script based on content type and topic
            script = self._generate_basic_script(seg_template["content_type"], topic, i, len(archetype["structure"]))

            segments.append({
                "segment_number": i,
                "start_time": current_time,
                "duration": duration,
                "content_type": seg_template["content_type"],
                "script_suggestion": script,
                "visual_hint": seg_template["hint"]
            })

            current_time += duration

        # Adjust last segment to match exact duration
        if segments:
            total = sum(s["duration"] for s in segments)
            if total != target_duration:
                segments[-1]["duration"] += (target_duration - total)

        return {
            "name": f"{archetype['name']}: {topic[:30]}",
            "style": style,
            "total_duration": target_duration,
            "platform": platform,
            "segments": segments,
            "hashtag_suggestions": self._generate_hashtags(topic),
            "tips": self.PLATFORM_TIPS.get(platform, "Focus on authenticity and value.")
        }

    def _generate_basic_script(self, content_type: str, topic: str, segment_num: int, total_segments: int) -> str:
        """Generate basic script suggestion based on content type."""

        scripts = {
            "hook": f"Stop scrolling if you want to know about {topic}!",
            "talking_head": f"Let me show you what you need to know about {topic}.",
            "b_roll": f"[Show demonstration related to {topic}]",
            "cta": "Follow for more fitness tips! Save this for later!",
            "text_overlay": f"Key point about {topic}",
            "transition": "[Smooth transition effect]"
        }

        return scripts.get(content_type, f"Segment {segment_num} content about {topic}")

    def _generate_hashtags(self, topic: str) -> List[str]:
        """Generate relevant hashtags based on topic."""

        base_hashtags = ["fitness", "workout", "gym", "health", "fitfam"]

        # Add topic-specific hashtags
        topic_lower = topic.lower()
        if "abs" in topic_lower or "core" in topic_lower:
            base_hashtags.extend(["absworkout", "coreworkout", "sixpack"])
        elif "leg" in topic_lower or "squat" in topic_lower:
            base_hashtags.extend(["legday", "squats", "glutes"])
        elif "arm" in topic_lower or "bicep" in topic_lower:
            base_hashtags.extend(["armday", "biceps", "triceps"])
        elif "cardio" in topic_lower or "run" in topic_lower:
            base_hashtags.extend(["cardio", "running", "hiit"])
        elif "meal" in topic_lower or "nutrition" in topic_lower:
            base_hashtags.extend(["mealprep", "nutrition", "healthyeating"])

        return base_hashtags[:10]


def generate_timeline_html(template: Dict[str, Any]) -> str:
    """
    Generate interactive timeline HTML from template data.

    Args:
        template: Template dict with segments, name, style, etc.

    Returns:
        HTML string with interactive timeline visualization
    """

    # Color mapping for content types
    colors = {
        "hook": "linear-gradient(135deg, #f43f5e, #ec4899)",
        "talking_head": "linear-gradient(135deg, #8b5cf6, #6366f1)",
        "b_roll": "linear-gradient(135deg, #10b981, #14b8a6)",
        "cta": "linear-gradient(135deg, #f59e0b, #f97316)",
        "text_overlay": "linear-gradient(135deg, #3b82f6, #06b6d4)",
        "transition": "linear-gradient(135deg, #6b7280, #9ca3af)"
    }

    segments = template.get("segments", [])
    total_duration = template.get("total_duration", 60)

    # Build segments HTML for timeline track
    segments_html = ""
    for seg in segments:
        width_pct = (seg["duration"] / total_duration) * 100
        content_type = seg.get("content_type", "talking_head")
        bg = colors.get(content_type, colors["talking_head"])

        segments_html += f'''
        <div class="timeline-segment"
             style="width: {width_pct}%; background: {bg}; min-width: 40px;"
             onclick="showSegmentDetails({seg['segment_number']})">
            <span class="segment-duration">{seg['duration']}s</span>
            <span class="segment-type">{content_type.replace('_', ' ')}</span>
        </div>'''

    # Build details HTML for each segment
    details_html = ""
    for seg in segments:
        content_type = seg.get("content_type", "talking_head")
        details_html += f'''
        <div class="segment-details" id="segment-{seg['segment_number']}" style="display:none;">
            <h4 style="color:#fff; margin-bottom:12px;">
                Segment {seg['segment_number']}: {content_type.replace('_', ' ').title()}
            </h4>
            <p style="color:#9ca3af; margin-bottom:8px;">
                <strong>Time:</strong> {seg['start_time']}s - {seg['start_time'] + seg['duration']}s ({seg['duration']} seconds)
            </p>
            <div class="segment-script">
                <strong>Script:</strong><br>
                "{seg['script_suggestion']}"
            </div>
            <p class="segment-visual-hint">
                <strong>Visual:</strong> {seg['visual_hint']}
            </p>
        </div>'''

    # Build hashtags string
    hashtags = template.get("hashtag_suggestions", [])
    hashtags_str = " ".join([f"#{h}" for h in hashtags])

    # Tips section
    tips = template.get("tips", "")
    tips_html = f'''
        <div style="margin-top:16px; padding:12px; background:#1a1a2e; border-radius:8px; border-left:3px solid #667eea;">
            <strong style="color:#667eea;">Pro Tip:</strong>
            <span style="color:#9ca3af;"> {tips}</span>
        </div>
    ''' if tips else ""

    return f'''
    <style>
        .video-timeline {{ background: #1a1a2e; border-radius: 12px; padding: 24px; }}
        .timeline-track {{ display: flex; height: 80px; background: #0f0f1a; border-radius: 8px; overflow: hidden; }}
        .timeline-segment {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 8px 12px;
            border-right: 2px solid #0f0f1a;
            cursor: pointer;
            transition: filter 0.2s, transform 0.2s;
        }}
        .timeline-segment:hover {{ filter: brightness(1.2); transform: scaleY(1.05); }}
        .timeline-segment.active {{ filter: brightness(1.3); box-shadow: 0 0 10px rgba(255,255,255,0.3); }}
        .segment-duration {{ font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.9); }}
        .segment-type {{ font-size: 10px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 0.5px; }}
        .segment-details {{ background: #2a2a4a; border-radius: 8px; padding: 16px; margin-top: 16px; }}
        .segment-script {{
            background: #0f0f1a;
            border-radius: 8px;
            padding: 12px;
            font-style: italic;
            color: #d1d5db;
            margin: 12px 0;
            line-height: 1.6;
        }}
        .segment-visual-hint {{ color: #4ade80; font-size: 13px; margin-top: 8px; }}
        .timeline-legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 16px; font-size: 12px; color: #9ca3af; }}
        .legend-dot {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 4px; vertical-align: middle; }}
        .legend-dot.hook {{ background: #f43f5e; }}
        .legend-dot.talking_head {{ background: #8b5cf6; }}
        .legend-dot.b_roll {{ background: #10b981; }}
        .legend-dot.cta {{ background: #f59e0b; }}
        .legend-dot.text_overlay {{ background: #3b82f6; }}
    </style>

    <div class="video-timeline">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px;">
            <div>
                <h3 style="color:#fff; margin-bottom:4px;">{template.get('name', 'Video Blueprint')}</h3>
                <span style="color:#9ca3af; font-size:13px;">
                    {total_duration}s | {template.get('style', 'custom').replace('_', ' ').title()} | {template.get('platform', 'social').replace('_', ' ').title()}
                </span>
            </div>
            <button onclick="copyScripts()" style="background:#667eea; color:#fff; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600; transition: background 0.2s;" onmouseover="this.style.background='#5568d9'" onmouseout="this.style.background='#667eea'">
                Copy All Scripts
            </button>
        </div>

        <div class="timeline-track">
            {segments_html}
        </div>

        <div class="timeline-legend">
            <span><span class="legend-dot hook"></span> Hook</span>
            <span><span class="legend-dot talking_head"></span> Talking Head</span>
            <span><span class="legend-dot b_roll"></span> B-Roll</span>
            <span><span class="legend-dot text_overlay"></span> Text Overlay</span>
            <span><span class="legend-dot cta"></span> Call to Action</span>
        </div>

        <p style="margin-top:16px; color:#6b7280; font-size:13px;">
            Click any segment above to view script and visual suggestions
        </p>

        {details_html}

        {tips_html}

        <div style="margin-top:20px; padding-top:16px; border-top:1px solid #2a2a4a;">
            <strong style="color:#fff;">Suggested Hashtags:</strong>
            <p style="color:#4ade80; margin-top:8px; word-wrap:break-word;">{hashtags_str}</p>
        </div>
    </div>

    <script>
    function showSegmentDetails(num) {{
        // Remove active class from all segments
        document.querySelectorAll('.timeline-segment').forEach((el, i) => {{
            el.classList.remove('active');
            if (i + 1 === num) el.classList.add('active');
        }});

        // Hide all details and show selected
        document.querySelectorAll('.segment-details').forEach(el => el.style.display = 'none');
        const detail = document.getElementById('segment-' + num);
        if (detail) {{
            detail.style.display = 'block';
            detail.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }}
    }}

    function copyScripts() {{
        const scripts = document.querySelectorAll('.segment-script');
        let text = "VIDEO SCRIPT - {template.get('name', 'Video Blueprint')}\\n";
        text += "Duration: {total_duration} seconds\\n";
        text += "Style: {template.get('style', 'custom')}\\n\\n";
        text += "=".repeat(40) + "\\n\\n";

        scripts.forEach((s, i) => {{
            text += "SEGMENT " + (i+1) + ":\\n";
            text += s.innerText.replace('Script:', '').trim() + "\\n\\n";
        }});

        text += "=".repeat(40) + "\\n";
        text += "HASHTAGS: {hashtags_str}\\n";

        navigator.clipboard.writeText(text).then(() => {{
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = 'Copied!';
            btn.style.background = '#10b981';
            setTimeout(() => {{
                btn.innerText = originalText;
                btn.style.background = '#667eea';
            }}, 2000);
        }});
    }}

    // Show first segment by default
    showSegmentDetails(1);
    </script>
    '''


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate video templates")
    parser.add_argument("--topic", default="5 best exercises for abs", help="Video topic")
    parser.add_argument("--style", default="educational",
                       choices=["educational", "transformation", "day_in_life", "before_after", "workout_demo"])
    parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds")
    parser.add_argument("--platform", default="instagram_reels",
                       choices=["tiktok", "instagram_reels", "youtube_shorts", "youtube"])
    parser.add_argument("--output", help="Output HTML file path")

    args = parser.parse_args()

    generator = VideoTemplateGenerator()
    template = generator.generate_template(
        topic=args.topic,
        style=args.style,
        target_duration=args.duration,
        platform=args.platform
    )

    print(f"\n{'='*60}")
    print(f"VIDEO TEMPLATE: {template.get('name', 'Template')}")
    print(f"{'='*60}")
    print(f"Style: {template.get('style')}")
    print(f"Duration: {template.get('total_duration')}s")
    print(f"Platform: {template.get('platform')}")
    print(f"\nSegments: {len(template.get('segments', []))}")

    for seg in template.get("segments", []):
        print(f"\n  [{seg['segment_number']}] {seg['content_type'].upper()} ({seg['duration']}s)")
        print(f"      Script: {seg['script_suggestion'][:60]}...")
        print(f"      Visual: {seg['visual_hint']}")

    print(f"\nHashtags: {' '.join(['#' + h for h in template.get('hashtag_suggestions', [])])}")

    if args.output:
        html = generate_timeline_html(template)
        with open(args.output, "w") as f:
            f.write(f"<!DOCTYPE html><html><head><title>{template.get('name')}</title></head><body style='background:#0f0f1a;padding:40px;'>{html}</body></html>")
        print(f"\nSaved to: {args.output}")
