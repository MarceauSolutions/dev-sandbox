# Education Scenarios: Video Editing Tools

*Tools: `create_jump_cut_video`, `add_video_branding`*
*Module: video_jumpcut.py*
*Category: 3 (Requires sample video files)*

## Persona

**David L., YouTube Fitness Creator**
- Creates talking head workout videos
- Raw videos have lots of pauses and "umms"
- Needs automated editing to speed up workflow
- Wants consistent branding (intro/outro)

---

## Prerequisites

### Required: moviepy installed
```bash
pip install moviepy
# Verify
python -c "import moviepy; print('moviepy version:', moviepy.__version__)"
```

### Required: Sample test video
For testing, create or provide a short video with speech and silence:
```
/Users/williammarceaujr./dev-sandbox/projects/fitness-influencer/test-assets/sample-video.mp4
```

---

## Tool 1: create_jump_cut_video

### Scenario 1: Basic Jump Cut Processing

**Goal:** Remove silences from a talking head video

**Input:**
```python
{
    "input_video_path": "/path/to/raw-video.mp4",
    "silence_threshold": -40,
    "min_silence_duration": 0.3,
    "generate_thumbnail": False
}
```

**Expected Output:**
- Shorter video with silences removed
- Original audio quality preserved
- No artifacts at cut points

**Test Command (Initialization Only):**
```bash
python -c "
from src.video_jumpcut import VideoJumpCutter
editor = VideoJumpCutter(silence_thresh=-40, min_silence_dur=0.3)
print('VideoJumpCutter initialized')
print('Available methods:', [m for m in dir(editor) if not m.startswith('_')])
"
```

**Full Test (Requires Video):**
```bash
python -c "
import os
from src.video_jumpcut import VideoJumpCutter

test_video = 'test-assets/sample-video.mp4'
if not os.path.exists(test_video):
    print('SKIPPED: No test video at', test_video)
else:
    editor = VideoJumpCutter()
    output = editor.apply_jump_cuts(test_video, 'test-assets/output-jumpcut.mp4')
    print('Output:', output)
    print('Success:', bool(output))
"
```

**Pass Criteria:**
- [ ] VideoJumpCutter initializes without error
- [ ] Methods are accessible (apply_jump_cuts, etc.)
- [ ] With test video: produces shorter output
- [ ] Audio/video sync maintained

---

### Scenario 2: Aggressive Silence Detection

**Goal:** Remove even short pauses for fast-paced content

**Input:**
```python
{
    "input_video_path": "/path/to/video.mp4",
    "silence_threshold": -35,  # More aggressive
    "min_silence_duration": 0.2  # Shorter silence threshold
}
```

**Expected Output:**
- More cuts than default settings
- Faster-paced final video
- May be too aggressive for some content

**Pass Criteria:**
- [ ] Accepts different threshold parameters
- [ ] Produces more cuts with aggressive settings

---

### Scenario 3: Conservative Editing

**Goal:** Only remove long pauses, preserve natural flow

**Input:**
```python
{
    "input_video_path": "/path/to/video.mp4",
    "silence_threshold": -50,  # Less sensitive
    "min_silence_duration": 1.0  # Only long pauses
}
```

**Expected Output:**
- Fewer cuts
- More natural pacing
- Only obvious pauses removed

**Pass Criteria:**
- [ ] Accepts conservative parameters
- [ ] Produces fewer cuts
- [ ] Natural flow maintained

---

### Scenario 4: Thumbnail Generation

**Goal:** Extract thumbnail while editing

**Input:**
```python
{
    "input_video_path": "/path/to/video.mp4",
    "generate_thumbnail": True
}
```

**Expected Output:**
- Edited video
- Thumbnail image (best frame)

**Pass Criteria:**
- [ ] Thumbnail file created
- [ ] Thumbnail is valid image

---

## Tool 2: add_video_branding

### Scenario 5: Full Branding (Intro + Outro)

**Goal:** Add branded intro and outro to video

**Input:**
```python
{
    "video_path": "/path/to/edited-video.mp4",
    "intro_path": "/path/to/intro.mp4",
    "outro_path": "/path/to/outro.mp4",
    "output_path": "/path/to/branded-output.mp4"
}
```

**Expected Output:**
- Video with intro at beginning
- Video with outro at end
- Seamless transitions

**Test Command (Initialization Only):**
```bash
python -c "
from src.video_jumpcut import VideoJumpCutter
editor = VideoJumpCutter()
has_branding = hasattr(editor, 'add_intro_outro')
print('Has add_intro_outro method:', has_branding)
"
```

**Pass Criteria:**
- [ ] Method exists and is callable
- [ ] With test videos: produces branded output
- [ ] Intro plays first, outro plays last

---

### Scenario 6: Intro Only

**Goal:** Add only intro (no outro)

**Input:**
```python
{
    "video_path": "/path/to/video.mp4",
    "intro_path": "/path/to/intro.mp4",
    "outro_path": None,
    "output_path": "/path/to/output.mp4"
}
```

**Pass Criteria:**
- [ ] Works with only intro
- [ ] No error for missing outro

---

### Scenario 7: Outro Only

**Goal:** Add only outro (no intro)

**Input:**
```python
{
    "video_path": "/path/to/video.mp4",
    "intro_path": None,
    "outro_path": "/path/to/outro.mp4",
    "output_path": "/path/to/output.mp4"
}
```

**Pass Criteria:**
- [ ] Works with only outro
- [ ] No error for missing intro

---

## Edge Cases

### Edge Case 1: Non-Existent Input File

**Input:**
```python
{
    "input_video_path": "/path/to/nonexistent.mp4"
}
```

**Expected Output:**
- Helpful error message
- No crash

**Test Command:**
```bash
python -c "
from src.video_jumpcut import VideoJumpCutter
editor = VideoJumpCutter()
try:
    result = editor.apply_jump_cuts('/nonexistent/video.mp4', '/tmp/output.mp4')
    print('Result:', result)
except Exception as e:
    print('Error handled:', type(e).__name__, str(e)[:50])
"
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Returns error or None

---

### Edge Case 2: Invalid Video Format

**Input:**
```python
{
    "input_video_path": "/path/to/file.txt"  # Not a video
}
```

**Pass Criteria:**
- [ ] Rejects non-video files
- [ ] Helpful error message

---

### Edge Case 3: Video with No Audio

**Input:**
```python
{
    "input_video_path": "/path/to/silent-video.mp4"
}
```

**Expected Output:**
- Handles gracefully (no silence to detect)
- Returns original or minimal edits

**Pass Criteria:**
- [ ] Does not crash on silent video
- [ ] Handles edge case gracefully

---

### Edge Case 4: Very Short Video (<5 seconds)

**Input:**
```python
{
    "input_video_path": "/path/to/5-second-clip.mp4"
}
```

**Pass Criteria:**
- [ ] Handles short videos
- [ ] May return original if no cuts needed

---

## Batch Test Script (Initialization Only)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
print('Testing Video Editing Tools...')
print('=' * 50)

# Test 1: Import and initialize
try:
    from src.video_jumpcut import VideoJumpCutter
    editor = VideoJumpCutter()
    print('✅ VideoJumpCutter imported and initialized')
except Exception as e:
    print(f'❌ Import failed: {e}')

# Test 2: Check methods exist
methods = ['apply_jump_cuts', 'add_intro_outro', 'generate_thumbnail']
for method in methods:
    has_method = hasattr(editor, method)
    status = '✅' if has_method else '❌'
    print(f'{status} Method: {method}')

# Test 3: Different parameters
try:
    editor_aggressive = VideoJumpCutter(silence_thresh=-35, min_silence_dur=0.2)
    editor_conservative = VideoJumpCutter(silence_thresh=-50, min_silence_dur=1.0)
    print('✅ Accepts different parameter values')
except Exception as e:
    print(f'❌ Parameter test failed: {e}')

print('=' * 50)
print('Note: Full video processing tests require sample video files')
print('Place test videos in: test-assets/sample-video.mp4')
"
```

---

## Success Criteria Summary

| Scenario | Tool | Key Check |
|----------|------|-----------|
| Basic jump cut | create_jump_cut_video | Silences removed |
| Aggressive edit | create_jump_cut_video | More cuts |
| Conservative edit | create_jump_cut_video | Fewer cuts |
| With thumbnail | create_jump_cut_video | Thumbnail generated |
| Full branding | add_video_branding | Intro + outro added |
| Intro only | add_video_branding | Works without outro |
| Outro only | add_video_branding | Works without intro |
| Edge: Missing file | both | Error handled |
| Edge: Invalid format | both | Rejected gracefully |
| Edge: No audio | create_jump_cut_video | Handles gracefully |
| Edge: Short video | create_jump_cut_video | No crash |

---

## Test Video Recommendations

For comprehensive testing, create these test videos:
1. **sample-video.mp4** - 30-60s talking head with pauses
2. **intro.mp4** - 3-5s branded intro
3. **outro.mp4** - 5-10s branded outro with CTA
4. **silent-video.mp4** - Video with no audio track
5. **short-clip.mp4** - 3-5s clip

Place in: `projects/fitness-influencer/test-assets/`
