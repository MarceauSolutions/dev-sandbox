# Education Scenarios: Cross-Platform Optimizer

*Tool: `optimize_for_platforms`*
*Module: cross_platform_optimizer.py*
*Category: 1 (FREE)*

## Persona

**Alex K., Multi-Platform Content Creator**
- Creates one piece of content, repurposes for 5+ platforms
- Needs optimal aspect ratios, captions, and hashtags per platform
- Wants to maximize reach without creating unique content for each platform

---

## Scenario 1: Video Content for All Platforms

**Goal:** Optimize a 60-second fitness video for all major platforms

**Input:**
```python
{
    "content_type": "video",
    "caption": "Try this 5-minute ab workout! Perfect for busy mornings. Save this for later and tag a friend who needs it! #fitness #abs",
    "video_duration": 60,
    "hashtags": ["fitness", "abs", "workout", "fitnessmotivation"]
}
```

**Expected Output:**
- Platform-specific recommendations for:
  - TikTok, Instagram (Feed, Reels, Stories)
  - YouTube (Standard, Shorts)
  - Twitter/X, Threads, LinkedIn
- Aspect ratio guidance (9:16, 16:9, 1:1)
- Caption length adjustments
- Hashtag count per platform
- Best posting times

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms(
    content_type='video',
    original_caption='Try this 5-minute ab workout! Perfect for busy mornings.',
    video_duration=60,
    hashtags=['fitness', 'abs', 'workout']
)
platforms = result.get('platforms', {})
print('Platforms optimized:', len(platforms))
for name, data in platforms.items():
    print(f'  {name}: {data.get(\"aspect_ratio\", \"?\")}')
"
```

**Pass Criteria:**
- [ ] Returns recommendations for 5+ platforms
- [ ] Each platform has aspect ratio
- [ ] Caption adaptations provided
- [ ] Hashtag counts appropriate per platform

---

## Scenario 2: Image Content (Carousel)

**Goal:** Optimize an image carousel for multiple platforms

**Input:**
```python
{
    "content_type": "carousel",
    "caption": "5 foods that boost your metabolism. Swipe to see them all! Which one are you adding to your diet?",
    "hashtags": ["nutrition", "metabolism", "healthyfood", "fitness"]
}
```

**Expected Output:**
- Image dimension recommendations
- Carousel support per platform
- Caption optimization
- Engagement prompts

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms(
    content_type='carousel',
    original_caption='5 foods that boost your metabolism. Swipe to see them all!',
    hashtags=['nutrition', 'metabolism']
)
print('Content type handled:', result.get('original', {}).get('content_type'))
print('Platforms:', list(result.get('platforms', {}).keys()))
"
```

**Pass Criteria:**
- [ ] Recognizes carousel format
- [ ] Notes platforms that don't support carousels
- [ ] Provides alternatives for non-carousel platforms

---

## Scenario 3: Single Image Post

**Goal:** Optimize a motivational quote image

**Input:**
```python
{
    "content_type": "image",
    "caption": "The only bad workout is the one you didn't do. Double tap if you agree! What's your Monday motivation?",
    "hashtags": ["motivation", "mondaymotivation", "fitness", "gym"]
}
```

**Expected Output:**
- Square vs. portrait recommendations
- Character limits per platform
- Hashtag strategy per platform

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms(
    content_type='image',
    original_caption='The only bad workout is the one you didn\\'t do.',
    hashtags=['motivation', 'fitness']
)
for platform, data in result.get('platforms', {}).items():
    caption_len = len(data.get('optimized_caption', ''))
    print(f'{platform}: {caption_len} chars')
"
```

**Pass Criteria:**
- [ ] Caption lengths appropriate per platform
- [ ] Twitter/X respects 280 char limit
- [ ] Instagram allows longer captions

---

## Scenario 4: Long-Form Video (10+ minutes)

**Goal:** Optimize a YouTube video for cross-platform distribution

**Input:**
```python
{
    "content_type": "video",
    "caption": "Complete guide to building muscle as a beginner. Everything you need to know about progressive overload, nutrition, and recovery.",
    "video_duration": 600,  # 10 minutes
    "hashtags": ["bodybuilding", "musclebuilding", "fitness", "workout"]
}
```

**Expected Output:**
- YouTube: Full video optimization
- Shorts/TikTok/Reels: Clip recommendations
- "Too long" warnings for short-form platforms

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms(
    content_type='video',
    original_caption='Complete guide to building muscle as a beginner.',
    video_duration=600
)
for platform, data in result.get('platforms', {}).items():
    duration_note = data.get('duration_recommendation', data.get('notes', 'OK'))
    print(f'{platform}: {str(duration_note)[:50]}')
"
```

**Pass Criteria:**
- [ ] YouTube shows as appropriate length
- [ ] TikTok/Reels note video is too long
- [ ] Clip suggestions provided for short-form

---

## Scenario 5: Specific Platform Targeting

**Goal:** Optimize for only selected platforms

**Input:**
```python
{
    "content_type": "video",
    "caption": "Quick tip: Always warm up before lifting!",
    "video_duration": 30,
    "platforms": ["tiktok", "instagram_reels"]  # Only these
}
```

**Expected Output:**
- Only TikTok and Instagram Reels recommendations
- No other platforms included

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms(
    content_type='video',
    original_caption='Quick tip: Always warm up before lifting!',
    video_duration=30,
    platforms=['tiktok', 'instagram_reels']
)
platforms = list(result.get('platforms', {}).keys())
print('Platforms returned:', platforms)
print('Count:', len(platforms))
"
```

**Pass Criteria:**
- [ ] Only requested platforms returned
- [ ] Other platforms not included

---

## Edge Case 1: Empty Caption

**Input:**
```python
{
    "content_type": "video",
    "caption": "",
    "video_duration": 60
}
```

**Expected Output:**
- Handles gracefully OR suggests caption

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
try:
    result = opt.optimize_for_all_platforms(
        content_type='video',
        original_caption='',
        video_duration=60
    )
    print('Handled empty caption:', bool(result))
except Exception as e:
    print('Error:', str(e)[:50])
"
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Either works with empty caption or provides helpful error

---

## Edge Case 2: Very Long Caption

**Input:**
```python
{
    "content_type": "image",
    "caption": "A" * 5000,  # 5000 characters
    "hashtags": ["test"]
}
```

**Pass Criteria:**
- [ ] Truncates appropriately for each platform
- [ ] Twitter/X version under 280 chars
- [ ] No crash

---

## Edge Case 3: No Hashtags

**Input:**
```python
{
    "content_type": "video",
    "caption": "Check out this workout!",
    "video_duration": 60,
    "hashtags": []
}
```

**Pass Criteria:**
- [ ] Works without hashtags
- [ ] May suggest adding hashtags

---

## Batch Test Script

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()

scenarios = [
    {'content_type': 'video', 'original_caption': 'Quick ab workout!', 'video_duration': 60},
    {'content_type': 'carousel', 'original_caption': '5 nutrition tips'},
    {'content_type': 'image', 'original_caption': 'Monday motivation'},
    {'content_type': 'video', 'original_caption': 'Full guide', 'video_duration': 600},
    {'content_type': 'video', 'original_caption': 'Quick tip', 'video_duration': 30, 'platforms': ['tiktok']},
]

print('Running platform optimizer scenarios...')
for i, params in enumerate(scenarios, 1):
    try:
        result = opt.optimize_for_all_platforms(**params)
        platforms = len(result.get('platforms', {}))
        status = '✅' if platforms > 0 else '❌'
        print(f'{status} Scenario {i}: {platforms} platforms optimized')
    except Exception as e:
        print(f'❌ Scenario {i} - Error: {e}')
print('Done!')
"
```

---

## Success Criteria Summary

| Scenario | Content Type | Key Check |
|----------|--------------|-----------|
| Video 60s | video | All platforms covered |
| Carousel | carousel | Carousel support noted |
| Image | image | Caption lengths correct |
| Long video | video 10min | Short-form warnings |
| Specific platforms | video | Only requested platforms |
| Edge: Empty caption | video | No crash |
| Edge: Long caption | image | Truncation works |
| Edge: No hashtags | video | Works without hashtags |
