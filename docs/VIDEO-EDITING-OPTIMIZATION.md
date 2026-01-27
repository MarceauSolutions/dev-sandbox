# Video Editing Optimization Guide

*Last Updated: 2026-01-27*
*Status: Technical recommendations for fitness video editing*

## Current Implementation

### Existing Tools

| Tool | Location | Purpose | Status |
|------|----------|---------|--------|
| `video_jumpcut.py` | fitness-influencer/mcp/src | Silence removal | Production |
| `moviepy_video_generator_v2.py` | execution/ | Image slideshow | Production |
| `intelligent_video_router.py` | fitness-influencer/mcp/src | Routing | Production |
| `shotstack_api.py` | execution/ | Cloud video gen | Production |

### Current Jump-Cut Capabilities
- FFmpeg silence detection (silencedetect filter)
- Configurable threshold (-40dB default)
- Minimum silence duration (0.3s default)
- Intro/outro branding insertion
- Thumbnail generation

## Recommended Improvements

### 1. Dynamic Threshold Calculation

**Problem**: Fixed -40dB threshold doesn't adapt to different audio levels.

**Solution**: Calculate threshold from audio mean level:
```python
def calculate_dynamic_threshold(self, video_path):
    """Calculate silence threshold based on audio mean level."""
    cmd = [
        'ffmpeg', '-i', video_path,
        '-af', 'volumedetect', '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    for line in result.stderr.split('\n'):
        if 'mean_volume' in line:
            mean_vol = float(line.split(':')[1].split('dB')[0].strip())
            return mean_vol - 18  # 18dB below mean
    return -40  # fallback
```

**Impact**: More accurate cuts, fewer false positives

### 2. Voice-Specific Audio Filtering

**Problem**: Background gym noise causes false silence detection.

**Solution**: Add highpass/lowpass filters for voice range:
```python
def detect_silence_enhanced(self, video_path):
    """Enhanced silence detection with voice filtering."""
    cmd = [
        'ffmpeg', '-i', video_path,
        '-af', (
            f'highpass=f=200,lowpass=f=4000,'
            f'silencedetect=n={self.silence_thresh}dB:d={self.min_silence_dur}'
        ),
        '-f', 'null', '-'
    ]
```

**Impact**: Filters gym music, equipment noise

### 3. Padding for Smooth Transitions

**Problem**: Abrupt cuts feel jarring.

**Solution**: Add 0.15s padding around cuts:
```python
def generate_keep_segments(self, silent_segments, padding=0.15):
    """Generate segments with padding for smoother transitions."""
    keep_segments = []
    for silence_start, silence_end in silent_segments:
        adjusted_start = max(0, silence_start + padding)
        adjusted_end = silence_end - padding
        # ... rest of logic
```

**Impact**: Professional-feeling transitions

### 4. GPU Encoding (NVENC)

**Problem**: CPU encoding is slow (90-100% CPU usage).

**Solution**: Use NVIDIA GPU encoding if available:
```python
def write_with_gpu_encoding(video, output_path, use_gpu=True):
    """Write video with optional GPU acceleration."""
    if use_gpu and has_nvidia_gpu():
        # Use FFmpeg NVENC
        cmd = [
            'ffmpeg', '-y',
            '-hwaccel', 'cuda',
            '-i', temp_path,
            '-c:v', 'h264_nvenc',
            '-cq', '23',
            '-preset', 'p4',
            output_path
        ]
    else:
        # CPU fallback
        video.write_videofile(output_path, codec='libx264')
```

**Impact**: 3-5x faster encoding

## New Features to Add

### 1. Whisper Transcription & Auto-Captioning

**Use Case**: Automatic subtitles for gym videos (loud music).

```python
# New module: execution/video_transcription.py
import whisper

class VideoTranscriber:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def generate_srt(self, video_path, output_path=None):
        """Generate SRT subtitle file."""
        result = self.model.transcribe(video_path, word_timestamps=True)
        # Write SRT format
        ...

    def burn_subtitles(self, video_path, srt_path, output_path):
        """Burn subtitles into video."""
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"subtitles={srt_path}",
            '-c:a', 'copy', output_path
        ]
```

**Dependencies**: `pip install openai-whisper` or `faster-whisper`
**Cost**: FREE (local processing)

### 2. Scene Detection (PySceneDetect)

**Use Case**: Auto-generate chapter markers, split exercises.

```python
# New module: execution/video_scene_detector.py
from scenedetect import detect, ContentDetector

class VideoSceneDetector:
    def detect_scenes(self, video_path, method="content"):
        """Detect scene changes in video."""
        scene_list = detect(video_path, ContentDetector(threshold=30))
        return [
            {
                "scene_num": i + 1,
                "start_time": scene[0].get_seconds(),
                "end_time": scene[1].get_seconds()
            }
            for i, scene in enumerate(scene_list)
        ]
```

**Dependencies**: `pip install scenedetect[opencv]`
**Cost**: FREE (local processing)

### 3. Video Stabilization (vidstab)

**Use Case**: Stabilize handheld workout footage.

```python
# New module: execution/video_stabilizer.py
from vidstab import VidStab

class WorkoutVideoStabilizer:
    def __init__(self, smoothing_window=30):
        self.stabilizer = VidStab(kp_method="GFTT")
        self.smoothing_window = smoothing_window

    def stabilize(self, input_path, output_path):
        """Stabilize shaky video."""
        self.stabilizer.stabilize(
            input_path=input_path,
            output_path=output_path,
            smoothing_window=self.smoothing_window,
            border_type='black',
            border_size='auto'
        )
```

**Dependencies**: `pip install vidstab`
**Cost**: FREE (local processing)

### 4. Platform-Specific Compression

**Use Case**: Optimize for Instagram, TikTok, YouTube.

```python
def optimize_for_social_media(input_path, output_path, platform="instagram"):
    """Optimize video compression for specific platforms."""

    platform_settings = {
        "instagram": {"bitrate": "3500k", "resolution": "1080:1920", "max_dur": 90},
        "tiktok": {"bitrate": "4000k", "resolution": "1080:1920", "max_dur": 180},
        "youtube_shorts": {"bitrate": "5000k", "resolution": "1080:1920", "max_dur": 60},
        "youtube": {"bitrate": "8000k", "resolution": "1920:1080", "max_dur": None}
    }

    settings = platform_settings[platform]
    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264', '-crf', '18',
        '-maxrate', settings["bitrate"],
        '-vf', f"scale={settings['resolution']}",
        output_path
    ]
```

## New MCP Tools

### Suggested Additions to server.py

```python
Tool(
    name="transcribe_video",
    description="Auto-transcribe video with Whisper AI. Generate subtitles.",
    inputSchema={
        "type": "object",
        "properties": {
            "video_path": {"type": "string"},
            "model": {"type": "string", "enum": ["tiny", "base", "small", "medium"]},
            "output_format": {"type": "string", "enum": ["srt", "vtt", "json"]},
            "burn_subtitles": {"type": "boolean", "default": False}
        },
        "required": ["video_path"]
    }
),

Tool(
    name="detect_scenes",
    description="Detect scene changes for chapter markers or splitting.",
    inputSchema={
        "type": "object",
        "properties": {
            "video_path": {"type": "string"},
            "method": {"type": "string", "enum": ["content", "threshold", "adaptive"]},
            "split_output": {"type": "boolean", "default": False}
        },
        "required": ["video_path"]
    }
),

Tool(
    name="stabilize_video",
    description="Stabilize shaky workout videos from handheld recording.",
    inputSchema={
        "type": "object",
        "properties": {
            "video_path": {"type": "string"},
            "smoothing": {"type": "integer", "default": 30},
            "auto_crop": {"type": "boolean", "default": True}
        },
        "required": ["video_path"]
    }
)
```

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
- [ ] Add dynamic threshold calculation
- [ ] Add padding for smoother transitions
- [ ] Add GPU encoding detection/fallback

### Phase 2: Core Features (1 week)
- [ ] Integrate Whisper for auto-transcription
- [ ] Add SRT/VTT subtitle generation
- [ ] Add subtitle burning option

### Phase 3: Advanced Features (2 weeks)
- [ ] PySceneDetect for chapters
- [ ] Video stabilization
- [ ] Batch parallel processing

## Dependencies

### Current
```
moviepy>=2.0
ffmpeg (system)
pillow
```

### Recommended Additions
```
openai-whisper>=20231117    # Auto-transcription
scenedetect[opencv]>=0.6.0  # Scene detection
vidstab>=1.0                # Video stabilization
```

## Performance Comparison

| Operation | CPU (current) | GPU (optimized) | Improvement |
|-----------|---------------|-----------------|-------------|
| 5-min video encode | 3-5 min | 30-60 sec | 5x faster |
| Silence detection | 20-30 sec | 20-30 sec | Same |
| Transcription (base) | 1-2 min | 15-30 sec | 4x faster |
| Stabilization | 5-10 min | 2-3 min | 3x faster |

## Related Documents

- [FITNESS-INFLUENCER-AI-OPTIMIZATION.md](FITNESS-INFLUENCER-AI-OPTIMIZATION.md)
- `projects/marceau-solutions/fitness-influencer/mcp/src/` - Source code
- `execution/` - Shared video utilities
