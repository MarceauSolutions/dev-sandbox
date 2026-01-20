"""Voice Styles - SSML generation for emotional TTS output.

Converts annotated text to SSML for natural-sounding voice AI.
Works with AWS Polly Neural voices via Twilio.
"""

from enum import Enum
from typing import Optional
import re


class VoiceStyle(Enum):
    """Pre-defined voice emotion styles."""
    WARM = "warm"           # Friendly greeting tone
    FRIENDLY = "friendly"   # Conversational, approachable
    EXCITED = "excited"     # Enthusiastic, upbeat
    CALM = "calm"           # Reassuring, steady
    APOLOGETIC = "apologetic"  # Softer, sympathetic
    PROFESSIONAL = "professional"  # Clear, confident
    CHEERFUL = "cheerful"   # Happy, bright
    EMPATHETIC = "empathetic"  # Understanding, caring


# SSML prosody settings for each style
STYLE_PROSODY = {
    VoiceStyle.WARM: {
        "rate": "95%",
        "pitch": "+5%",
        "volume": "medium",
        "emphasis": "moderate",
    },
    VoiceStyle.FRIENDLY: {
        "rate": "100%",
        "pitch": "+3%",
        "volume": "medium",
        "emphasis": None,
    },
    VoiceStyle.EXCITED: {
        "rate": "110%",
        "pitch": "+10%",
        "volume": "+2dB",
        "emphasis": "strong",
    },
    VoiceStyle.CALM: {
        "rate": "90%",
        "pitch": "-2%",
        "volume": "soft",
        "emphasis": None,
    },
    VoiceStyle.APOLOGETIC: {
        "rate": "92%",
        "pitch": "-5%",
        "volume": "soft",
        "emphasis": "reduced",
    },
    VoiceStyle.PROFESSIONAL: {
        "rate": "98%",
        "pitch": "medium",
        "volume": "medium",
        "emphasis": None,
    },
    VoiceStyle.CHEERFUL: {
        "rate": "105%",
        "pitch": "+8%",
        "volume": "medium",
        "emphasis": "moderate",
    },
    VoiceStyle.EMPATHETIC: {
        "rate": "90%",
        "pitch": "+2%",
        "volume": "soft",
        "emphasis": "reduced",
    },
}

# Context-based style mapping for restaurant scenarios
RESTAURANT_CONTEXT_STYLES = {
    "greeting": VoiceStyle.WARM,
    "taking_order": VoiceStyle.FRIENDLY,
    "confirming": VoiceStyle.PROFESSIONAL,
    "upsell": VoiceStyle.CHEERFUL,
    "apology": VoiceStyle.APOLOGETIC,
    "not_available": VoiceStyle.EMPATHETIC,
    "order_complete": VoiceStyle.EXCITED,
    "transfer": VoiceStyle.CALM,
    "farewell": VoiceStyle.WARM,
}

# Context-based style mapping for consulting outreach
CONSULTING_CONTEXT_STYLES = {
    "greeting": VoiceStyle.WARM,
    "introduction": VoiceStyle.FRIENDLY,
    "value_prop": VoiceStyle.PROFESSIONAL,
    "interested": VoiceStyle.EXCITED,
    "not_interested": VoiceStyle.CALM,
    "callback": VoiceStyle.CHEERFUL,
    "farewell": VoiceStyle.WARM,
}


def build_prosody_tag(style: VoiceStyle) -> tuple[str, str]:
    """Build opening and closing prosody tags for a style."""
    settings = STYLE_PROSODY.get(style, STYLE_PROSODY[VoiceStyle.FRIENDLY])

    attrs = []
    if settings.get("rate") and settings["rate"] != "medium":
        attrs.append(f'rate="{settings["rate"]}"')
    if settings.get("pitch") and settings["pitch"] != "medium":
        attrs.append(f'pitch="{settings["pitch"]}"')
    if settings.get("volume") and settings["volume"] != "medium":
        attrs.append(f'volume="{settings["volume"]}"')

    if attrs:
        open_tag = f'<prosody {" ".join(attrs)}>'
        close_tag = '</prosody>'
    else:
        open_tag = ''
        close_tag = ''

    # Add emphasis if specified
    if settings.get("emphasis"):
        open_tag += f'<emphasis level="{settings["emphasis"]}">'
        close_tag = '</emphasis>' + close_tag

    return open_tag, close_tag


def text_to_ssml(
    text: str,
    style: VoiceStyle = VoiceStyle.FRIENDLY,
    add_breathing: bool = True
) -> str:
    """
    Convert plain text to SSML with emotional styling.

    NOTE: Twilio automatically wraps SSML in <speak> tags, so we should NOT
    include them. Only include the inner SSML tags like <prosody>, <break>, etc.

    Args:
        text: Plain text to convert
        style: VoiceStyle to apply
        add_breathing: Add natural pauses at punctuation

    Returns:
        SSML-formatted string (without <speak> wrapper - Twilio adds it)
    """
    # Escape any existing XML characters in the text content
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Add natural breathing pauses
    if add_breathing:
        # Longer pause after periods and question marks
        text = re.sub(r'([.!?])\s+', r'\1<break time="400ms"/> ', text)
        # Shorter pause after commas
        text = re.sub(r',\s+', r',<break time="200ms"/> ', text)

    # Apply style prosody
    open_tag, close_tag = build_prosody_tag(style)

    # Return WITHOUT <speak> wrapper - Twilio adds it automatically
    return f'{open_tag}{text}{close_tag}'


def annotated_to_ssml(text: str) -> str:
    """
    Convert text with emotion annotations to SSML.

    Annotation format: [style]text[/style]
    Example: "[warm]Hello there![/warm] [friendly]How can I help?[/friendly]"

    Args:
        text: Text with emotion annotations

    Returns:
        SSML-formatted string
    """
    result = text

    # Process each style
    for style in VoiceStyle:
        tag = style.value
        open_tag, close_tag = build_prosody_tag(style)

        # Replace opening tags
        result = result.replace(f"[{tag}]", open_tag)
        result = result.replace(f"[/{tag}]", close_tag)

    # Escape any remaining special characters (outside tags)
    # This is simplified - a production version would be more careful

    # Add breathing pauses at punctuation (outside of tags)
    result = re.sub(r'([.!?])(\s+)(?![<])', r'\1<break time="400ms"/>\2', result)
    result = re.sub(r',(\s+)(?![<])', r',<break time="200ms"/>\1', result)

    # Return WITHOUT <speak> wrapper - Twilio adds it automatically
    return result


def get_style_for_context(context: str, call_type: str = "restaurant") -> VoiceStyle:
    """
    Get the appropriate voice style for a conversation context.

    Args:
        context: The conversation context (e.g., "greeting", "apology")
        call_type: "restaurant" or "consulting"

    Returns:
        Appropriate VoiceStyle
    """
    if call_type == "consulting":
        return CONSULTING_CONTEXT_STYLES.get(context, VoiceStyle.FRIENDLY)
    return RESTAURANT_CONTEXT_STYLES.get(context, VoiceStyle.FRIENDLY)


def detect_context_from_text(text: str) -> str:
    """
    Auto-detect conversation context from response text.

    Args:
        text: The AI response text

    Returns:
        Detected context string
    """
    text_lower = text.lower()

    # Greeting patterns
    if any(phrase in text_lower for phrase in ["thank you for calling", "welcome to", "hi!", "hello!"]):
        return "greeting"

    # Apology patterns
    if any(phrase in text_lower for phrase in ["sorry", "apologize", "unfortunately"]):
        return "apology"

    # Order confirmation patterns
    if any(phrase in text_lower for phrase in ["order is", "your total", "that'll be", "ready in"]):
        return "order_complete"

    # Transfer patterns
    if any(phrase in text_lower for phrase in ["transfer", "connect you", "hold on"]):
        return "transfer"

    # Not available patterns
    if any(phrase in text_lower for phrase in ["don't have", "out of", "not available", "sold out"]):
        return "not_available"

    # Upsell patterns
    if any(phrase in text_lower for phrase in ["would you like", "how about", "can i add", "anything else"]):
        return "upsell"

    # Farewell patterns
    if any(phrase in text_lower for phrase in ["have a great", "goodbye", "thank you for", "see you"]):
        return "farewell"

    # Default to taking order / general conversation
    return "taking_order"


def smart_ssml(text: str, call_type: str = "restaurant") -> str:
    """
    Automatically convert text to SSML with context-aware emotion.

    This is the main function to use - it auto-detects context and applies
    appropriate emotional styling.

    Args:
        text: Plain text AI response
        call_type: "restaurant" or "consulting"

    Returns:
        SSML-formatted string with emotional prosody
    """
    context = detect_context_from_text(text)
    style = get_style_for_context(context, call_type)
    return text_to_ssml(text, style)


# Neural voice options (Polly)
NEURAL_VOICES = {
    "female_us": "Joanna-Neural",      # American female, warm
    "male_us": "Matthew-Neural",        # American male, friendly
    "female_us_news": "Danielle-Neural", # American female, clear
    "female_uk": "Amy-Neural",          # British female, professional
    "male_uk": "Brian-Neural",          # British male, authoritative
}


def get_voice_name(voice_type: str = "female_us") -> str:
    """
    Get the Polly voice name for Twilio.

    Args:
        voice_type: Key from NEURAL_VOICES

    Returns:
        Full voice name for Twilio (e.g., "Polly.Joanna-Neural")
    """
    voice = NEURAL_VOICES.get(voice_type, NEURAL_VOICES["female_us"])
    return f"Polly.{voice}"


# Convenience function for restaurant greetings
def restaurant_greeting_ssml(restaurant_name: str) -> str:
    """Generate a warm greeting SSML for restaurant calls."""
    text = f"Thank you for calling {restaurant_name}! What can I get for you today?"
    return text_to_ssml(text, VoiceStyle.WARM)


# Convenience function for consulting greetings
def consulting_greeting_ssml(business_name: str = None, service_type: str = None) -> str:
    """Generate a warm greeting SSML for consulting outreach."""
    if business_name and service_type:
        text = f"Hi! This is an AI assistant calling on behalf of William Marceau. He noticed {business_name} and wanted to reach out about AI services for your {service_type} business. Do you have a moment to chat?"
    elif business_name:
        text = f"Hi! This is an AI assistant calling on behalf of William Marceau. He noticed {business_name} and wanted to reach out about AI consulting services. Do you have a moment?"
    else:
        text = "Hi! This is an AI assistant calling on behalf of William Marceau. He wanted to reach out about AI consulting services for your business. Do you have a moment?"

    return text_to_ssml(text, VoiceStyle.WARM)


if __name__ == "__main__":
    # Test examples
    print("=== Voice Styles Demo ===\n")

    # Basic SSML conversion
    print("1. Basic greeting (warm):")
    print(text_to_ssml("Thank you for calling Mario's Pizza!", VoiceStyle.WARM))
    print()

    # Auto-context detection
    print("2. Auto-detected contexts:")
    test_phrases = [
        "Thank you for calling Mario's Pizzeria!",
        "I'm sorry, we're out of pepperoni today.",
        "Your order total is $24.99. It'll be ready in 20 minutes!",
        "Would you like to add garlic bread to that?",
        "Let me transfer you to our manager.",
    ]
    for phrase in test_phrases:
        context = detect_context_from_text(phrase)
        print(f"   [{context}] {phrase[:50]}...")
    print()

    # Smart SSML
    print("3. Smart SSML (auto context + styling):")
    print(smart_ssml("Sorry, we don't have that right now. Can I suggest the veggie pizza instead?"))
    print()

    # Annotated text
    print("4. Annotated text:")
    annotated = "[warm]Hello![/warm] [friendly]How can I help you today?[/friendly]"
    print(f"   Input: {annotated}")
    print(f"   Output: {annotated_to_ssml(annotated)}")
