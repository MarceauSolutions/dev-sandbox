# Education Scenarios: Video Blueprint Generator

*Tool: `generate_video_blueprint`*
*Module: video_template_framework.py*
*Category: 1 (FREE)*

## Persona

**Mike R., Fitness YouTuber**
- Creates content for YouTube, Instagram Reels, and TikTok
- 50K followers, growing channel
- Needs structured video plans to maintain consistency
- Wants engaging hooks and clear CTAs

---

## Scenario 1: Educational Tips Video (60 seconds)

**Goal:** Create a quick educational video about abs exercises

**Input:**
```python
{
    "topic": "5 best exercises for abs",
    "style": "educational",
    "duration": 60,
    "platform": "instagram_reels"
}
```

**Expected Output:**
- Structured segments (hook, content, CTA)
- Script suggestions for each segment
- Visual hints (what to film)
- Platform-appropriate timing
- Hashtag recommendations

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('5 best exercises for abs', 'educational', 60, 'instagram_reels')
print('Segments:', len(template.get('segments', [])))
for seg in template.get('segments', []):
    print(f'  {seg.get(\"type\", \"?\")}: {seg.get(\"duration\", 0)}s')
print('Hashtags:', len(template.get('hashtags', [])))
"
```

**Pass Criteria:**
- [ ] Returns 3+ segments
- [ ] Total duration approximately 60 seconds
- [ ] Includes hook, content, and CTA segments
- [ ] Script suggestions provided
- [ ] Hashtags are fitness-relevant

---

## Scenario 2: Transformation Story (90 seconds)

**Goal:** Create a compelling transformation video template

**Input:**
```python
{
    "topic": "My client lost 50 pounds in 6 months",
    "style": "transformation",
    "duration": 90,
    "platform": "youtube_shorts"
}
```

**Expected Output:**
- Before/after structure
- Emotional hook
- Journey highlights
- Results reveal
- Testimonial segment

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('My client lost 50 pounds', 'transformation', 90, 'youtube_shorts')
segments = template.get('segments', [])
types = [s.get('type') for s in segments]
print('Segment types:', types)
total_duration = sum(s.get('duration', 0) for s in segments)
print('Total duration:', total_duration, 'seconds')
"
```

**Pass Criteria:**
- [ ] Includes before/after segments
- [ ] Duration approximately 90 seconds
- [ ] Has emotional storytelling elements
- [ ] Suitable for YouTube Shorts (vertical, under 60s or shorts-optimized)

---

## Scenario 3: Day in the Life (120 seconds)

**Goal:** Create a longer day-in-the-life template

**Input:**
```python
{
    "topic": "A day in my life as a fitness coach",
    "style": "day_in_life",
    "duration": 120,
    "platform": "youtube"
}
```

**Expected Output:**
- Morning routine segment
- Work/training segments
- Meals/nutrition segment
- Evening wind-down
- Relatable lifestyle content

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('A day in my life as a fitness coach', 'day_in_life', 120, 'youtube')
print('Template name:', template.get('name', 'Unnamed'))
print('Segments:', len(template.get('segments', [])))
total = sum(s.get('duration', 0) for s in template.get('segments', []))
print('Total duration:', total, 'seconds')
"
```

**Pass Criteria:**
- [ ] Multiple lifestyle segments
- [ ] Duration approximately 120 seconds
- [ ] Variety of content (not just gym footage)

---

## Scenario 4: Workout Demo (45 seconds)

**Goal:** Create a quick workout demonstration

**Input:**
```python
{
    "topic": "Perfect push-up form in 45 seconds",
    "style": "workout_demo",
    "duration": 45,
    "platform": "tiktok"
}
```

**Expected Output:**
- Quick hook
- Form breakdown
- Common mistakes
- Final demo
- TikTok-optimized pacing

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('Perfect push-up form', 'workout_demo', 45, 'tiktok')
print('Platform:', template.get('platform', 'Unknown'))
print('Segments:', len(template.get('segments', [])))
"
```

**Pass Criteria:**
- [ ] Fast-paced segments (TikTok style)
- [ ] Clear demonstration structure
- [ ] Duration approximately 45 seconds
- [ ] Includes form tips

---

## Scenario 5: Before/After Comparison (60 seconds)

**Goal:** Create a before/after comparison template

**Input:**
```python
{
    "topic": "My 1-year gym transformation",
    "style": "before_after",
    "duration": 60,
    "platform": "instagram_reels"
}
```

**Expected Output:**
- Dramatic reveal structure
- Side-by-side comparison guidance
- Journey context
- Motivational messaging

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('My 1-year gym transformation', 'before_after', 60, 'instagram_reels')
print('Style applied:', template.get('style', 'Unknown'))
print('Total segments:', len(template.get('segments', [])))
"
```

**Pass Criteria:**
- [ ] Before and after segments clearly defined
- [ ] Reveal/transition guidance
- [ ] Emotional arc present

---

## Edge Case 1: Very Short Video (30 seconds)

**Input:**
```python
{
    "topic": "One exercise you need to try",
    "style": "educational",
    "duration": 30,  # Minimum
    "platform": "tiktok"
}
```

**Expected Output:**
- Compressed but complete structure
- Still has hook and CTA

**Test Command:**
```bash
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('One exercise you need', 'educational', 30, 'tiktok')
total = sum(s.get('duration', 0) for s in template.get('segments', []))
print('Target: 30s, Actual:', total, 'seconds')
print('Has hook:', any(s.get('type') == 'hook' for s in template.get('segments', [])))
"
```

**Pass Criteria:**
- [ ] Duration close to 30 seconds
- [ ] Still has essential segments (hook, CTA)

---

## Edge Case 2: Maximum Duration (180 seconds)

**Input:**
```python
{
    "topic": "Complete guide to meal prep for muscle gain",
    "style": "educational",
    "duration": 180,  # Maximum
    "platform": "youtube"
}
```

**Pass Criteria:**
- [ ] Returns comprehensive template
- [ ] Multiple content sections
- [ ] Duration close to 180 seconds

---

## Edge Case 3: HTML Output Generation

**Input:**
```python
{
    "topic": "Quick ab workout",
    "style": "workout_demo",
    "duration": 60,
    "platform": "instagram_reels",
    "output_html": "/tmp/test_blueprint.html"
}
```

**Test Command:**
```bash
python -c "
import os
from src.video_template_framework import VideoTemplateGenerator, generate_timeline_html
gen = VideoTemplateGenerator()
template = gen.generate_template('Quick ab workout', 'workout_demo', 60, 'instagram_reels')
html = generate_timeline_html(template)
print('HTML generated:', len(html), 'characters')
print('Contains timeline:', 'timeline' in html.lower())
"
```

**Pass Criteria:**
- [ ] HTML is valid
- [ ] Contains timeline visualization
- [ ] Segment information displayed

---

## Batch Test Script

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()

scenarios = [
    ('5 best ab exercises', 'educational', 60, 'instagram_reels'),
    ('Client transformation', 'transformation', 90, 'youtube_shorts'),
    ('Day in my life', 'day_in_life', 120, 'youtube'),
    ('Perfect push-up', 'workout_demo', 45, 'tiktok'),
    ('1 year transformation', 'before_after', 60, 'instagram_reels'),
    ('Quick tip', 'educational', 30, 'tiktok'),
    ('Full guide', 'educational', 180, 'youtube'),
]

print('Running video blueprint scenarios...')
for topic, style, duration, platform in scenarios:
    try:
        template = gen.generate_template(topic, style, duration, platform)
        segments = template.get('segments', [])
        actual_dur = sum(s.get('duration', 0) for s in segments)
        status = '✅' if segments else '❌'
        print(f'{status} {style}/{duration}s/{platform}: {len(segments)} segments, {actual_dur}s')
    except Exception as e:
        print(f'❌ {style}/{duration}s/{platform} - Error: {e}')
print('Done!')
"
```

---

## Success Criteria Summary

| Scenario | Style | Duration | Key Check |
|----------|-------|----------|-----------|
| Educational Tips | educational | 60s | Hook + content + CTA |
| Transformation | transformation | 90s | Before/after segments |
| Day in Life | day_in_life | 120s | Multiple lifestyle segments |
| Workout Demo | workout_demo | 45s | Form breakdown |
| Before/After | before_after | 60s | Reveal structure |
| Edge: Min duration | - | 30s | Still has essentials |
| Edge: Max duration | - | 180s | Comprehensive |
| Edge: HTML output | - | - | Valid visualization |
