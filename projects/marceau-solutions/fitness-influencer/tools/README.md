# AI Character/Voice/Video Testing Tools

Lightweight CLI scripts for hands-on testing of AI generation tools before integration into the fitness influencer platform.

## Quick Reference

| Script | Purpose | Key API |
|--------|---------|---------|
| `test_voice_minimax.py` | MiniMax TTS (most realistic) | `FAL_API_KEY` |
| `test_voice_resemble.py` | Resemble AI voice enhancement/cloning | `RESEMBLE_API_KEY` |
| `test_voice_elevenlabs.py` | ElevenLabs voice cloning + consistency | `ELEVENLABS_API_KEY` |
| `test_character_consistency.py` | Generate same character N times | `XAI_API_KEY` / others |
| `test_image_to_video.py` | Animate still image into video | `XAI_API_KEY` |
| `test_seed_bracketing.py` | Test seeds 1000-1010 for best results | `XAI_API_KEY` / others |
| `test_lipsync.py` | Lip sync audio to video/image (4 models) | `FAL_API_KEY` |
| `test_talking_head.py` | Talking head from image + audio (SadTalker) | `REPLICATE_API_TOKEN` |
| `test_face_restore.py` | Face restoration/upscaling (GFPGAN/ESRGAN) | `REPLICATE_API_TOKEN` |

## Setup

All API keys go in the root `.env` file (`/Users/williammarceaujr./dev-sandbox/.env`).

```bash
# Voice providers
FAL_API_KEY=...           # MiniMax via fal.ai
RESEMBLE_API_KEY=...      # Resemble AI
ELEVENLABS_API_KEY=...    # ElevenLabs

# Image/Video providers (likely already configured)
XAI_API_KEY=...           # Grok Aurora / Grok Imagine
OPENAI_API_KEY=...        # DALL-E 3
REPLICATE_API_TOKEN=...   # Stable Diffusion
IDEOGRAM_API_KEY=...      # Ideogram
```

## Usage Examples

### Voice Testing

```bash
# List MiniMax voices
python test_voice_minimax.py --list-voices

# Generate speech with MiniMax
python test_voice_minimax.py --text "Welcome to the workout" --voice "male-qn-qingse"

# List ElevenLabs voices
python test_voice_elevenlabs.py --list-voices

# Generate with ElevenLabs
python test_voice_elevenlabs.py --text "Let's get started" --voice-id 21m00Tcm4TlvDq8ikWAM

# Test voice consistency (same text 5x)
python test_voice_elevenlabs.py --consistency --text "Today's workout" --voice-id xxx --count 5

# Clone a voice from sample
python test_voice_elevenlabs.py --clone --sample my_voice.mp3 --name "FitnessCoach"

# Resemble AI voice enhancement
python test_voice_resemble.py --enhance --input raw_audio.mp3

# Estimate costs before generating
python test_voice_minimax.py --cost --text "Long script here..."
python test_voice_elevenlabs.py --cost --text "Long script here..."
```

### Character Consistency

```bash
# From character profile (recommended)
python test_character_consistency.py --profile character_profiles/example_profile.json --count 5

# From raw prompt
python test_character_consistency.py --prompt "30yo athletic man, brown hair, gym" --count 3

# Premium tier for highest quality
python test_character_consistency.py --profile character_profiles/example_profile.json --count 5 --tier premium
```

### Seed Bracketing

```bash
# Standard bracket (11 seeds)
python test_seed_bracketing.py --prompt "Athletic man in modern gym" --seeds 1000-1010

# Narrow bracket (cheaper)
python test_seed_bracketing.py --prompt "Fitness coach" --seeds 1000-1005

# Budget tier for bulk testing
python test_seed_bracketing.py --prompt "Workout scene" --seeds 1000-1020 --tier budget

# Specific winning seeds only
python test_seed_bracketing.py --prompt "Gym scene" --seeds "1003,1007,1009"
```

### Image to Video

```bash
# Animate a character image
python test_image_to_video.py --image output/character_01.png --prompt "person speaking to camera"

# Vertical video for TikTok/Reels
python test_image_to_video.py --image output/character_01.png --prompt "talking head" --aspect 9:16

# Longer duration
python test_image_to_video.py --image output/character_01.png --prompt "workout demo" --duration 12
```

### Lip Sync

```bash
# Lip sync video with new audio (default: Lipsync 1.9)
python test_lipsync.py --video face.mp4 --audio speech.mp3

# Use MuseTalk (works from single image)
python test_lipsync.py --image face.png --audio speech.mp3 --model musetalk

# Compare all lip sync models
python test_lipsync.py --video face.mp4 --audio speech.mp3 --compare-all

# Estimate costs
python test_lipsync.py --cost --duration 30
```

### Talking Head (SadTalker)

```bash
# Generate talking head from image + audio
python test_talking_head.py --image face.png --audio speech.mp3

# With built-in face enhancement (GFPGAN)
python test_talking_head.py --image face.png --audio speech.mp3 --enhance

# More expressive head movement
python test_talking_head.py --image face.png --audio speech.mp3 --expression-scale 1.5

# Minimal head movement (just lip sync)
python test_talking_head.py --image face.png --audio speech.mp3 --still
```

### Face Restoration

```bash
# Restore a face image (GFPGAN)
python test_face_restore.py --image blurry_face.png

# Upscale with Real-ESRGAN (4x)
python test_face_restore.py --image low_res.png --model realesrgan --scale 4

# Compare GFPGAN vs Real-ESRGAN
python test_face_restore.py --image face.png --compare-all

# Batch restore a directory
python test_face_restore.py --batch output/consistency_20260209/
```

## Recommended Workflow

1. **Create character profile** - Edit `character_profiles/example_profile.json`
2. **Test consistency** - `test_character_consistency.py --profile ... --count 5`
3. **Find best seed** - `test_seed_bracketing.py --prompt "..." --seeds 1000-1010`
4. **Enhance face** - `test_face_restore.py --image output/best.png`
5. **Add voice** - `test_voice_elevenlabs.py --text "..." --voice-id xxx`
6. **Create talking head** - `test_talking_head.py --image output/best.png --audio output/voice.mp3 --enhance`
7. **Or lip sync video** - `test_lipsync.py --video output/animated.mp4 --audio output/voice.mp3`

## Cost Estimates

| Tool | Per Unit | 11-seed bracket | 5 images |
|------|----------|-----------------|----------|
| Replicate SD (budget) | $0.003/img | $0.033 | $0.015 |
| Grok Aurora (standard) | $0.07/img | $0.77 | $0.35 |
| DALL-E 3 (premium) | $0.08/img | $0.88 | $0.40 |
| MiniMax TTS | ~$0.04/min | - | - |
| ElevenLabs TTS | $0.30/1K chars | - | - |
| Resemble AI TTS | $0.006/sec | - | - |
| Grok Imagine Video | $0.02/sec | - | - |
| Lipsync 1.9 (fal.ai) | $0.70/min | - | - |
| Lipsync 2.0 (fal.ai) | $3.00/min | - | - |
| MuseTalk (fal.ai) | ~$0.50/min | - | - |
| SadTalker (Replicate) | ~$0.05/run | - | - |
| GFPGAN (Replicate) | ~$0.005/img | - | $0.025 |
| Real-ESRGAN (Replicate) | ~$0.01/img | - | $0.05 |

## Existing Infrastructure (Reused)

These scripts build on existing production routers in `execution/`:
- `multi_provider_image_router.py` - 4 providers with automatic fallback
- `multi_provider_video_router.py` - 7 providers with cost tracking
- `grok_image_gen.py` - Direct xAI image generation
- `grok_video_gen.py` - Direct xAI video generation

## Research Sources

All techniques sourced from PDFs in `projects/archived/automated-social-media-campaign/`:
- **THE COMPLETE AI INFLUENCER SYSTEM GUIDE.pdf** - Facial Engineering, Character Bible
- **How I Cut AI Video Costs By 60_.pdf** - Seed Bracketing technique
- **how to have consistent voice in video.pdf** - Voice consistency stack
- **How_to_Create_Realistic_AI_Voices_That_Don't_Sound_Like_Trash_1.pdf** - MiniMax vs Resemble
- **Full guide on making ai ugc that converts like crazy.pdf** - End-to-end workflow
