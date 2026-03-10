#!/usr/bin/env python3
"""
Caption Style Templates for Fitness Influencer AI v2.0

10 pre-built caption styles matching competitor quality plus custom style support.

Styles:
    - trending: TikTok-style bold impact captions
    - glow: Neon glow effect with shadow
    - minimal: Clean, subtle appearance
    - bold: High impact, maximum visibility
    - clean: Professional, readable
    - neon: Vibrant neon colors
    - subtitle: Traditional subtitle look
    - fitness: Fitness-branded style
    - professional: Corporate/LinkedIn style
    - dramatic: High-energy, attention-grabbing

Usage:
    from backend.caption_styles import get_style, list_styles, create_custom_style

    style = get_style("trending")
    all_styles = list_styles()
    custom = create_custom_style(font_family="Roboto", font_size=56, ...)
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

from backend.caption_generator import CaptionStyle, HighlightStyle, CaptionPosition


# ============================================================================
# Style Definitions
# ============================================================================

class StyleAnimation(str, Enum):
    """Caption animation types."""
    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    POP = "pop"
    TYPEWRITER = "typewriter"


@dataclass
class StyleTemplate:
    """Complete style template with metadata."""
    name: str
    display_name: str
    description: str
    style: CaptionStyle
    animation: StyleAnimation = StyleAnimation.NONE
    position: CaptionPosition = CaptionPosition.BOTTOM
    recommended_for: List[str] = None  # Platform recommendations
    preview_image: Optional[str] = None

    def __post_init__(self):
        if self.recommended_for is None:
            self.recommended_for = ["tiktok", "instagram", "youtube"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "animation": self.animation.value,
            "position": self.position.value,
            "recommended_for": self.recommended_for,
            "preview_image": self.preview_image,
            "style": {
                "font_family": self.style.font_family,
                "font_size": self.style.font_size,
                "font_color": self.style.font_color,
                "outline_color": self.style.outline_color,
                "outline_width": self.style.outline_width,
                "shadow_color": self.style.shadow_color,
                "shadow_offset": self.style.shadow_offset,
                "background_color": self.style.background_color,
                "background_opacity": self.style.background_opacity,
                "highlight_color": self.style.highlight_color,
                "highlight_style": self.style.highlight_style.value
            }
        }


# ============================================================================
# 10 Pre-built Style Templates
# ============================================================================

STYLE_TEMPLATES: Dict[str, StyleTemplate] = {
    "trending": StyleTemplate(
        name="trending",
        display_name="Trending",
        description="TikTok-style bold impact captions with pop animation",
        style=CaptionStyle(
            font_family="Impact",
            font_size=56,
            font_color="#FFFFFF",
            outline_color="#000000",
            outline_width=3,
            shadow_color=None,
            shadow_offset=0,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#FFD700",  # Gold
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.POP,
        position=CaptionPosition.CENTER,
        recommended_for=["tiktok", "instagram"],
        preview_image="/static/previews/trending.jpg"
    ),

    "glow": StyleTemplate(
        name="glow",
        display_name="Glow",
        description="Neon glow effect with vibrant colors",
        style=CaptionStyle(
            font_family="Arial Bold",
            font_size=52,
            font_color="#00FF88",  # Bright green
            outline_color="#000000",
            outline_width=2,
            shadow_color="#00FF88",
            shadow_offset=3,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#FFFFFF",
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.FADE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["tiktok", "youtube"],
        preview_image="/static/previews/glow.jpg"
    ),

    "minimal": StyleTemplate(
        name="minimal",
        display_name="Minimal",
        description="Clean, subtle captions with semi-transparent background",
        style=CaptionStyle(
            font_family="Helvetica",
            font_size=42,
            font_color="#FFFFFF",
            outline_color=None,
            outline_width=0,
            shadow_color=None,
            shadow_offset=0,
            background_color="#000000",
            background_opacity=0.6,
            highlight_color="#00BFFF",  # Deep sky blue
            highlight_style=HighlightStyle.UNDERLINE
        ),
        animation=StyleAnimation.FADE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["youtube", "linkedin"],
        preview_image="/static/previews/minimal.jpg"
    ),

    "bold": StyleTemplate(
        name="bold",
        display_name="Bold",
        description="Maximum impact with thick outline and slide animation",
        style=CaptionStyle(
            font_family="Arial Black",
            font_size=64,
            font_color="#FFFF00",  # Yellow
            outline_color="#000000",
            outline_width=4,
            shadow_color="#000000",
            shadow_offset=2,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#FF0000",  # Red
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.SLIDE,
        position=CaptionPosition.CENTER,
        recommended_for=["tiktok", "instagram"],
        preview_image="/static/previews/bold.jpg"
    ),

    "clean": StyleTemplate(
        name="clean",
        display_name="Clean",
        description="Professional, readable captions for all platforms",
        style=CaptionStyle(
            font_family="Roboto",
            font_size=44,
            font_color="#FFFFFF",
            outline_color="#333333",
            outline_width=2,
            shadow_color=None,
            shadow_offset=0,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#4CAF50",  # Green
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.NONE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["youtube", "linkedin", "instagram"],
        preview_image="/static/previews/clean.jpg"
    ),

    "neon": StyleTemplate(
        name="neon",
        display_name="Neon",
        description="Vibrant neon pink/purple with glow effect",
        style=CaptionStyle(
            font_family="Arial Bold",
            font_size=50,
            font_color="#FF00FF",  # Magenta
            outline_color="#000000",
            outline_width=2,
            shadow_color="#FF00FF",
            shadow_offset=4,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#00FFFF",  # Cyan
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.FADE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["tiktok", "instagram"],
        preview_image="/static/previews/neon.jpg"
    ),

    "subtitle": StyleTemplate(
        name="subtitle",
        display_name="Subtitle",
        description="Traditional subtitle style for long-form content",
        style=CaptionStyle(
            font_family="Arial",
            font_size=36,
            font_color="#FFFFFF",
            outline_color=None,
            outline_width=0,
            shadow_color=None,
            shadow_offset=0,
            background_color="#000000",
            background_opacity=0.8,
            highlight_color="#FFFF00",
            highlight_style=HighlightStyle.BOLD
        ),
        animation=StyleAnimation.NONE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["youtube", "linkedin"],
        preview_image="/static/previews/subtitle.jpg"
    ),

    "fitness": StyleTemplate(
        name="fitness",
        display_name="Fitness",
        description="Energetic fitness-branded style with orange accents",
        style=CaptionStyle(
            font_family="Impact",
            font_size=54,
            font_color="#FF4500",  # Orange red
            outline_color="#FFFFFF",
            outline_width=3,
            shadow_color="#000000",
            shadow_offset=2,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#FFFFFF",
            highlight_style=HighlightStyle.COLOR
        ),
        animation=StyleAnimation.POP,
        position=CaptionPosition.CENTER,
        recommended_for=["tiktok", "instagram", "youtube"],
        preview_image="/static/previews/fitness.jpg"
    ),

    "professional": StyleTemplate(
        name="professional",
        display_name="Professional",
        description="Corporate-friendly style for LinkedIn and business content",
        style=CaptionStyle(
            font_family="Georgia",
            font_size=40,
            font_color="#FFFFFF",
            outline_color="#1A1A1A",
            outline_width=2,
            shadow_color=None,
            shadow_offset=0,
            background_color="#003366",  # Dark blue
            background_opacity=0.7,
            highlight_color="#FFD700",  # Gold
            highlight_style=HighlightStyle.UNDERLINE
        ),
        animation=StyleAnimation.FADE,
        position=CaptionPosition.BOTTOM,
        recommended_for=["linkedin", "youtube"],
        preview_image="/static/previews/professional.jpg"
    ),

    "dramatic": StyleTemplate(
        name="dramatic",
        display_name="Dramatic",
        description="High-energy style with large red text and slide animation",
        style=CaptionStyle(
            font_family="Arial Black",
            font_size=72,
            font_color="#FF0000",  # Red
            outline_color="#000000",
            outline_width=5,
            shadow_color="#000000",
            shadow_offset=3,
            background_color=None,
            background_opacity=0.0,
            highlight_color="#FFFFFF",
            highlight_style=HighlightStyle.SCALE
        ),
        animation=StyleAnimation.SLIDE,
        position=CaptionPosition.CENTER,
        recommended_for=["tiktok", "instagram"],
        preview_image="/static/previews/dramatic.jpg"
    )
}


# ============================================================================
# Style Access Functions
# ============================================================================

def get_style(name: str) -> Optional[StyleTemplate]:
    """
    Get a style template by name.

    Args:
        name: Style name (trending, glow, minimal, etc.)

    Returns:
        StyleTemplate or None if not found
    """
    return STYLE_TEMPLATES.get(name.lower())


def get_caption_style(name: str) -> Optional[CaptionStyle]:
    """
    Get just the CaptionStyle from a template.

    Args:
        name: Style name

    Returns:
        CaptionStyle or None
    """
    template = get_style(name)
    return template.style if template else None


def list_styles() -> List[Dict[str, Any]]:
    """
    List all available style templates with metadata.

    Returns:
        List of style dicts with name, description, preview, etc.
    """
    return [template.to_dict() for template in STYLE_TEMPLATES.values()]


def list_style_names() -> List[str]:
    """
    Get just the style names.

    Returns:
        List of style names
    """
    return list(STYLE_TEMPLATES.keys())


def get_styles_for_platform(platform: str) -> List[Dict[str, Any]]:
    """
    Get styles recommended for a specific platform.

    Args:
        platform: Platform name (tiktok, instagram, youtube, linkedin)

    Returns:
        List of style dicts recommended for that platform
    """
    platform = platform.lower()
    return [
        template.to_dict()
        for template in STYLE_TEMPLATES.values()
        if platform in template.recommended_for
    ]


# ============================================================================
# Custom Style Creation
# ============================================================================

def create_custom_style(
    font_family: str = "Arial",
    font_size: int = 48,
    font_color: str = "#FFFFFF",
    outline_color: str = "#000000",
    outline_width: int = 2,
    shadow_color: Optional[str] = None,
    shadow_offset: int = 0,
    background_color: Optional[str] = None,
    background_opacity: float = 0.0,
    highlight_color: str = "#FFFF00",
    highlight_style: str = "color",
    animation: str = "none",
    position: str = "bottom",
    name: str = "custom"
) -> StyleTemplate:
    """
    Create a custom style template.

    Args:
        font_family: Font name
        font_size: Font size in points
        font_color: Hex color for text
        outline_color: Hex color for outline
        outline_width: Outline thickness
        shadow_color: Hex color for shadow (optional)
        shadow_offset: Shadow offset in pixels
        background_color: Hex color for background (optional)
        background_opacity: Background opacity (0-1)
        highlight_color: Hex color for word highlighting
        highlight_style: Highlight type (none, color, underline, bold, scale)
        animation: Animation type (none, fade, slide, pop, typewriter)
        position: Caption position (top, center, bottom)
        name: Custom style name

    Returns:
        StyleTemplate with custom settings
    """
    # Parse enums
    try:
        hl_style = HighlightStyle(highlight_style.lower())
    except ValueError:
        hl_style = HighlightStyle.COLOR

    try:
        anim = StyleAnimation(animation.lower())
    except ValueError:
        anim = StyleAnimation.NONE

    try:
        pos = CaptionPosition(position.lower())
    except ValueError:
        pos = CaptionPosition.BOTTOM

    style = CaptionStyle(
        font_family=font_family,
        font_size=font_size,
        font_color=font_color,
        outline_color=outline_color if outline_width > 0 else None,
        outline_width=outline_width,
        shadow_color=shadow_color,
        shadow_offset=shadow_offset,
        background_color=background_color,
        background_opacity=background_opacity,
        highlight_color=highlight_color,
        highlight_style=hl_style
    )

    return StyleTemplate(
        name=name,
        display_name=name.title(),
        description="Custom style",
        style=style,
        animation=anim,
        position=pos,
        recommended_for=["all"]
    )


def validate_custom_style(
    style_dict: Dict[str, Any],
    min_font_size: int = 24,
    max_font_size: int = 72
) -> List[str]:
    """
    Validate custom style parameters.

    Args:
        style_dict: Dict of style parameters
        min_font_size: Minimum font size (default 24pt)
        max_font_size: Maximum font size (default 72pt)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Font size validation (24-72pt for API, 12-120pt for internal use)
    font_size = style_dict.get("font_size", 48)
    errors.extend(validate_font_size(font_size, min_font_size, max_font_size))

    # Color validation (supports both hex and named colors)
    color_fields = ["font_color", "outline_color", "shadow_color",
                    "background_color", "highlight_color"]
    for field in color_fields:
        color = style_dict.get(field)
        if color and not is_valid_color(color):
            errors.append(f"{field} must be a valid hex color (#FFFFFF) or named color (white, red, neon_green)")

    # Opacity validation
    opacity = style_dict.get("background_opacity", 0)
    if not isinstance(opacity, (int, float)) or opacity < 0 or opacity > 1:
        errors.append("background_opacity must be between 0 and 1")

    # Outline width validation (0-5 for API)
    outline = style_dict.get("outline_width", 0)
    if not isinstance(outline, int) or outline < 0 or outline > 5:
        errors.append("outline_width must be between 0 and 5")

    # Shadow offset validation
    shadow = style_dict.get("shadow_offset", 0)
    if not isinstance(shadow, int) or shadow < 0 or shadow > 10:
        errors.append("shadow_offset must be between 0 and 10")

    # Position validation
    position = style_dict.get("position")
    if position:
        valid_positions = ["top", "center", "bottom"]
        # Support offset format like "bottom+20"
        base_pos = position.lower().split("+")[0].split("-")[0]
        if base_pos not in valid_positions:
            errors.append(f"position must be one of: {valid_positions} (with optional offset, e.g., 'bottom+20')")

    return errors


def normalize_style_params(style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize style parameters by converting named colors to hex.

    Args:
        style_dict: Dict of style parameters

    Returns:
        Dict with colors converted to hex format
    """
    normalized = style_dict.copy()

    color_fields = ["font_color", "outline_color", "shadow_color",
                    "background_color", "highlight_color"]

    for field in color_fields:
        color = normalized.get(field)
        if color:
            try:
                normalized[field] = parse_color(color)
            except ValueError:
                pass  # Keep original if invalid

    return normalized


def is_valid_hex_color(color: str) -> bool:
    """Check if string is a valid hex color."""
    if not color:
        return True  # None/empty is allowed
    if not color.startswith("#"):
        return False
    color = color[1:]
    if len(color) not in [3, 6]:
        return False
    try:
        int(color, 16)
        return True
    except ValueError:
        return False


# Named color to hex mapping
NAMED_COLORS: Dict[str, str] = {
    # Basic colors
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "orange": "#FFA500",
    "purple": "#800080",
    "pink": "#FFC0CB",
    "gold": "#FFD700",
    "silver": "#C0C0C0",
    "gray": "#808080",
    "grey": "#808080",

    # Extended colors
    "navy": "#000080",
    "teal": "#008080",
    "lime": "#00FF00",
    "maroon": "#800000",
    "olive": "#808000",
    "aqua": "#00FFFF",
    "coral": "#FF7F50",
    "crimson": "#DC143C",
    "indigo": "#4B0082",
    "ivory": "#FFFFF0",
    "khaki": "#F0E68C",
    "lavender": "#E6E6FA",
    "salmon": "#FA8072",
    "tan": "#D2B48C",
    "turquoise": "#40E0D0",
    "violet": "#EE82EE",

    # Fitness-themed colors
    "neon_green": "#39FF14",
    "neon_pink": "#FF6EC7",
    "neon_orange": "#FF5F1F",
    "neon_yellow": "#FFFF33",
    "electric_blue": "#7DF9FF",
    "hot_pink": "#FF69B4",
    "lime_green": "#32CD32",
    "deep_sky_blue": "#00BFFF",
}


def parse_color(color: str) -> str:
    """
    Parse a color string to hex format.

    Supports:
    - Hex colors: #FFFFFF, #FFF
    - Named colors: white, red, neon_green

    Args:
        color: Color string (hex or name)

    Returns:
        Hex color string (#RRGGBB)

    Raises:
        ValueError: If color is invalid
    """
    if not color:
        return None

    color = color.strip()

    # Already hex format
    if color.startswith("#"):
        if is_valid_hex_color(color):
            # Expand 3-digit hex to 6-digit
            if len(color) == 4:
                return f"#{color[1]*2}{color[2]*2}{color[3]*2}"
            return color.upper()
        raise ValueError(f"Invalid hex color: {color}")

    # Named color
    color_lower = color.lower().replace("-", "_").replace(" ", "_")
    if color_lower in NAMED_COLORS:
        return NAMED_COLORS[color_lower]

    raise ValueError(f"Unknown color: {color}. Use hex (#FFFFFF) or named color (white, red, etc.)")


def is_valid_color(color: str) -> bool:
    """Check if a color string is valid (hex or named)."""
    if not color:
        return True
    try:
        parse_color(color)
        return True
    except ValueError:
        return False


def validate_font_size(size: int, min_size: int = 24, max_size: int = 72) -> List[str]:
    """
    Validate font size is within range.

    Args:
        size: Font size in points
        min_size: Minimum allowed size (default 24)
        max_size: Maximum allowed size (default 72)

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    if not isinstance(size, int):
        errors.append(f"font_size must be an integer, got {type(size).__name__}")
    elif size < min_size:
        errors.append(f"font_size must be at least {min_size}pt, got {size}pt")
    elif size > max_size:
        errors.append(f"font_size must be at most {max_size}pt, got {size}pt")
    return errors


# ============================================================================
# Style Comparison and Recommendations
# ============================================================================

def compare_styles(style_names: List[str]) -> Dict[str, Any]:
    """
    Compare multiple styles side by side.

    Args:
        style_names: List of style names to compare

    Returns:
        Comparison dict with all style properties
    """
    styles = {}
    for name in style_names:
        template = get_style(name)
        if template:
            styles[name] = template.to_dict()

    return {
        "styles": styles,
        "count": len(styles)
    }


def recommend_style(
    platform: str = None,
    content_type: str = None,
    brand_color: str = None
) -> List[Dict[str, Any]]:
    """
    Get style recommendations based on context.

    Args:
        platform: Target platform (tiktok, instagram, youtube, linkedin)
        content_type: Content type (fitness, tutorial, vlog, professional)
        brand_color: Brand color to match (hex)

    Returns:
        List of recommended styles with match scores
    """
    recommendations = []

    for name, template in STYLE_TEMPLATES.items():
        score = 0
        reasons = []

        # Platform match
        if platform and platform.lower() in template.recommended_for:
            score += 30
            reasons.append(f"Recommended for {platform}")

        # Content type match
        if content_type:
            content_type = content_type.lower()
            if content_type == "fitness" and name == "fitness":
                score += 40
                reasons.append("Fitness-specific style")
            elif content_type == "professional" and name in ["professional", "minimal", "clean"]:
                score += 35
                reasons.append("Professional appearance")
            elif content_type == "tutorial" and name in ["clean", "subtitle", "minimal"]:
                score += 30
                reasons.append("Good for tutorials")
            elif content_type == "vlog" and name in ["trending", "bold", "glow"]:
                score += 25
                reasons.append("Great for vlogs")

        # Brand color proximity (basic matching)
        if brand_color and template.style.font_color:
            # Could add color distance calculation here
            pass

        if score > 0:
            recommendations.append({
                "style": template.to_dict(),
                "score": score,
                "reasons": reasons
            })

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations[:5]  # Top 5 recommendations


# ============================================================================
# Font Availability
# ============================================================================

SYSTEM_FONTS = [
    "Arial", "Arial Black", "Arial Bold",
    "Helvetica", "Helvetica Bold",
    "Impact",
    "Georgia", "Georgia Bold",
    "Roboto", "Roboto Bold",
    "Open Sans", "Open Sans Bold",
    "Montserrat", "Montserrat Bold",
    "Lato", "Lato Bold",
    "Oswald",
    "Poppins", "Poppins Bold",
    "Futura",
    "Verdana", "Verdana Bold"
]


def list_available_fonts() -> List[str]:
    """
    List fonts available for caption styling.

    Returns system fonts plus any custom fonts.
    """
    return SYSTEM_FONTS.copy()


def is_font_available(font_name: str) -> bool:
    """Check if a font is available."""
    return font_name in SYSTEM_FONTS
