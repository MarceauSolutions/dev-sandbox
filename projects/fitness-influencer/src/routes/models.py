"""
Fitness-Influencer Tower — Models
Extracted from main.py monolith. 0 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class VideoEditRequest(BaseModel):
    """Request model for video editing."""
    silence_threshold: Optional[float] = -40
    min_silence_duration: Optional[float] = 0.3
    generate_thumbnail: Optional[bool] = True


class EducationalGraphicRequest(BaseModel):
    """Request model for educational graphics."""
    title: str
    points: List[str]
    platform: Optional[str] = "instagram_post"


class EmailDigestRequest(BaseModel):
    """Request model for email digest."""
    hours_back: Optional[int] = 24


class RevenueReportRequest(BaseModel):
    """Request model for revenue analytics."""
    sheet_id: str
    month: Optional[str] = None  # YYYY-MM format


class GrokImageRequest(BaseModel):
    """Request model for AI image generation."""
    prompt: str
    count: Optional[int] = 1


class AdCreationRequest(BaseModel):
    """Request model for ad creation workflow."""
    ad_type: str  # 'video_ad', 'image_ad', 'carousel_ad'
    title: Optional[str] = None
    tagline: Optional[str] = None
    call_to_action: Optional[str] = "Learn More"
    platform: Optional[str] = "instagram_post"
    generate_background: Optional[bool] = False
    background_prompt: Optional[str] = None
    edit_video: Optional[bool] = True
    silence_threshold: Optional[float] = -40


class AIRequest(BaseModel):
    """Request model for AI arbitrated requests."""
    message: str
    context: Optional[dict] = None


class VideoGenerateRequest(BaseModel):
    """Request model for video generation from images."""
    image_urls: List[str]
    headline: Optional[str] = "Transform Your Body"
    cta_text: Optional[str] = "Start Your Journey"
    duration: Optional[float] = 15.0
    music_style: Optional[str] = "energetic"  # energetic, motivational, upbeat
    force_method: Optional[str] = None  # 'moviepy', 'creatomate', or None (auto)
    quality_tier: Optional[str] = None  # 'free', 'budget', 'standard', 'premium', or None (auto)


class VideoStatusRequest(BaseModel):
    """Request model for checking video render status."""
    render_id: str


class BrandResearchRequest(BaseModel):
    """Request model for brand research."""
    handle: str  # Social media handle (e.g., "boabfit", "@boabfit")
    platforms: Optional[List[str]] = None  # Default: instagram, tiktok


class BrandProfileRequest(BaseModel):
    """Request model for getting a stored brand profile."""
    handle: str


# ============================================================================
# Job Queue Models (v2.0)
# ============================================================================

class JobSubmitRequest(BaseModel):
    """Request model for submitting a background job."""
    job_type: str  # video_caption, video_filler_removal, video_reframe, video_export, etc.
    params: Dict[str, Any]
    user_id: Optional[str] = None
    priority: Optional[int] = 5  # 1=highest, 10=lowest

class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str  # queued, processing, complete, failed, cancelled
    progress: int  # 0-100
    estimated_remaining: int  # seconds
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobSubmitResponse(BaseModel):
    """Response model for job submission."""
    job_id: str
    status: str
    job_type: str
    created_at: str
    estimated_time: int  # seconds
    poll_url: str

class VideoCaptionRequest(BaseModel):
    """
    Request model for video captioning job with full customization.

    Supports:
    - Style presets: trending, glow, minimal, bold, clean, neon, subtitle, fitness, professional, dramatic
    - Position with offset: 'bottom', 'center', 'top', or 'bottom+20' for pixel offset
    - Custom fonts and colors (hex or named colors like 'white', 'neon_green')
    - Word highlighting styles: color, underline, bold, scale, none
    """
    video_url: str
    style: Optional[str] = "trending"  # trending, glow, minimal, bold, clean, neon, etc.
    position: Optional[str] = "bottom"  # top, center, bottom (with optional offset like 'bottom+20')
    language: Optional[str] = "en"  # en, es, pt, auto
    word_highlight: Optional[bool] = True
    max_words_per_line: Optional[int] = 7

    # Custom font settings
    custom_font: Optional[str] = None  # e.g., "Arial", "Impact", "Roboto"
    font_size: Optional[int] = None  # 24-72pt range

    # Custom color settings (hex or named colors)
    font_color: Optional[str] = None  # e.g., "#FFFFFF" or "white"
    outline_color: Optional[str] = None  # e.g., "#000000" or "black"
    outline_width: Optional[int] = None  # 0-5 pixels
    shadow_color: Optional[str] = None  # e.g., "#000000" or None
    shadow_offset: Optional[int] = None  # 0-10 pixels
    highlight_color: Optional[str] = None  # Color for active word highlighting

    # Background settings
    background_color: Optional[str] = None  # e.g., "#000000" for subtitle-style
    background_opacity: Optional[float] = None  # 0.0-1.0

class VideoReframeRequest(BaseModel):
    """Request model for video reframe job."""
    video_url: str
    target_aspect: Optional[str] = "9:16"  # 9:16, 1:1, 4:5, 16:9
    tracking_mode: Optional[str] = "auto"  # face, body, auto
    smoothing: Optional[float] = 0.8  # 0.1-1.0
    safe_zone_margin: Optional[float] = 0.1

class VideoExportRequest(BaseModel):
    """
    Request model for multi-platform export with metadata generation.

    Features:
    - Export to multiple platforms in parallel (TikTok, Instagram, YouTube, etc.)
    - Platform-optimized encoding (resolution, bitrate, codec)
    - Auto-generate hashtags and descriptions from transcription
    - Webhook notification on completion
    """
    video_url: str
    platforms: List[str] = ["tiktok", "instagram_reels", "youtube_shorts"]
    include_captions: Optional[bool] = False
    generate_descriptions: Optional[bool] = True
    hashtag_count: Optional[int] = None  # Uses platform-optimal count if not specified
    transcription_text: Optional[str] = None  # For metadata generation
    category: Optional[str] = None  # workout, nutrition, motivation, transformation, tutorial, tips, challenge
    webhook_url: Optional[str] = None  # URL to POST completion notification


class BatchExportRequest(BaseModel):
    """
    Request model for exporting multiple videos to multiple platforms.

    Useful for batch processing content across all platforms at once.
    """
    videos: List[Dict[str, Any]]  # List of {video_url, transcription_text, category}
    platforms: List[str] = ["tiktok", "instagram_reels", "youtube_shorts"]
    generate_descriptions: Optional[bool] = True
    webhook_url: Optional[str] = None

class FillerRemovalRequest(BaseModel):
    """Request model for filler word removal."""
    video_url: str
    sensitivity: Optional[str] = "moderate"  # aggressive, moderate, conservative


class FillerDetectionRequest(BaseModel):
    """Request model for filler word detection (analysis only, no removal)."""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    sensitivity: Optional[str] = "moderate"  # aggressive, moderate, conservative
    confidence_threshold: Optional[float] = None  # Override default (0.5-0.95)
    include_clusters: Optional[bool] = True  # Include filler clusters in response
    language: Optional[str] = "en"  # Transcription language
    fillers_to_remove: Optional[List[str]] = ["um", "uh", "like", "you know"]
    preserve_rhythm: Optional[bool] = True


class VideoAnalyzeRequest(BaseModel):
    """
    Request model for long-form video analysis.

    Analyzes videos to identify structure, key moments, and potential clips.
    Optimized for 10-60 minute videos with < 2 minute processing.
    """
    video_url: str
    analyze_audio: Optional[bool] = True  # Analyze audio energy peaks/valleys
    analyze_motion: Optional[bool] = True  # Detect high-motion segments
    detect_scenes: Optional[bool] = True  # Identify scene/shot changes
    extract_keywords: Optional[bool] = True  # Extract keywords from transcription
    min_segment_duration: Optional[float] = 5.0  # Min clip duration (seconds)
    max_segment_duration: Optional[float] = 60.0  # Max clip duration (seconds)
    transcription_text: Optional[str] = None  # Pre-transcribed text (speeds up analysis)
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps
    top_segments_count: Optional[int] = 20  # Number of top segments to return


class ViralDetectionRequest(BaseModel):
    """
    Request model for viral moment detection.

    Identifies the best clips from long-form content with viral scoring.
    """
    video_url: str
    top_count: Optional[int] = 10  # Number of viral moments to return
    min_score: Optional[float] = 40.0  # Minimum viral score (0-100)
    min_duration: Optional[float] = 15.0  # Minimum clip duration (seconds)
    max_duration: Optional[float] = 60.0  # Maximum clip duration (seconds)
    preserve_sentences: Optional[bool] = True  # Don't cut mid-sentence
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps
    # Scoring weights (must sum to ~1.0)
    weight_hook: Optional[float] = 0.25
    weight_audio: Optional[float] = 0.15
    weight_visual: Optional[float] = 0.15
    weight_keywords: Optional[float] = 0.15
    weight_emotion: Optional[float] = 0.15
    weight_fitness: Optional[float] = 0.15


class HookAnalysisRequest(BaseModel):
    """
    Request model for hook analysis and optimization.

    Analyzes the first 3 seconds of a video for hook effectiveness,
    provides improvement suggestions, and generates alternative variants.
    """
    video_url: str
    platform: Optional[str] = "tiktok"  # tiktok, instagram_reels, youtube_shorts
    hook_duration: Optional[float] = 3.0  # Duration to analyze (seconds)
    generate_variants: Optional[bool] = True  # Generate alternative hook variants
    variant_count: Optional[int] = 3  # Number of variants to generate
    include_ab_test_setup: Optional[bool] = False  # Include A/B test framework
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps


class RetentionPredictionRequest(BaseModel):
    """
    Request model for retention curve prediction.

    Predicts audience retention before publishing, identifies drop-off points,
    and provides improvement suggestions.
    """
    video_url: str
    platform: Optional[str] = "tiktok"  # tiktok, instagram_reels, youtube_shorts, youtube
    sample_interval: Optional[float] = 1.0  # Sample every N seconds
    include_hook_analysis: Optional[bool] = True  # Include hook scoring
    cliff_threshold: Optional[float] = 10.0  # Drop % to flag as cliff
    generate_suggestions: Optional[bool] = True  # Generate improvement tips
    transcription_text: Optional[str] = None  # Pre-transcribed text
    word_timestamps: Optional[List[Dict[str, Any]]] = None  # Word-level timestamps


class WorkoutOverlayRequest(BaseModel):
    """
    Request model for workout timer overlay.

    Adds HIIT timers, rep counters, and interval indicators to videos.
    """
    video_url: str
    timer_type: Optional[str] = "interval"  # countdown, countup, interval, rep_counter
    preset: Optional[str] = None  # hiit, tabata, emom, amrap, strength, yoga, cardio, plank

    # Custom timer settings (used if no preset)
    duration: Optional[float] = 60.0  # Total duration in seconds
    work_duration: Optional[float] = 45.0  # Work interval (for interval type)
    rest_duration: Optional[float] = 15.0  # Rest interval (for interval type)
    rounds: Optional[int] = 1  # Number of rounds

    # Rep counter settings
    total_reps: Optional[int] = 10
    auto_increment: Optional[bool] = False

    # Visual settings
    position: Optional[str] = "top_right"  # top_left, top_right, bottom_left, bottom_right, center
    style: Optional[str] = "bold"  # minimal, bold, neon, digital

    # Display settings
    show_round_number: Optional[bool] = True
    show_work_rest_label: Optional[bool] = True

    # Audio settings
    enable_audio_cues: Optional[bool] = False


class AnnotationItem(BaseModel):
    """Single annotation item."""
    type: str  # arrow, circle, line, text, highlight_box
    start_time: Optional[float] = 0.0
    end_time: Optional[float] = None

    # Arrow/Line coordinates
    start: Optional[List[int]] = None  # [x, y]
    end: Optional[List[int]] = None  # [x, y]

    # Circle coordinates
    center: Optional[List[int]] = None  # [x, y]
    radius: Optional[int] = 50

    # Text/Label
    position: Optional[List[int]] = None  # [x, y]
    text: Optional[str] = None
    font_size: Optional[int] = 32

    # Highlight box
    top_left: Optional[List[int]] = None  # [x, y]
    bottom_right: Optional[List[int]] = None  # [x, y]

    # Common styling
    color: Optional[str] = "#FF0000"
    thickness: Optional[int] = 3
    pulsing: Optional[bool] = False
    animated: Optional[bool] = False
    label: Optional[str] = None
    background: Optional[str] = None
    background_opacity: Optional[float] = 0.7


class FormAnnotationsRequest(BaseModel):
    """
    Request model for form annotations.

    Adds arrows, circles, text labels, and highlight boxes to videos
    for exercise form instruction.
    """
    video_url: str
    annotations: List[AnnotationItem]
    slow_motion_segments: Optional[List[Dict[str, Any]]] = None
    preserve_audio: Optional[bool] = True


class ExerciseRecognitionRequest(BaseModel):
    """
    Request model for exercise recognition.

    Detects exercise type from video using pose estimation.
    """
    video_url: str
    min_confidence: Optional[float] = 0.7
    enable_rep_counting: Optional[bool] = True
    enable_form_analysis: Optional[bool] = True
    sample_interval: Optional[int] = 5  # Process every Nth frame


