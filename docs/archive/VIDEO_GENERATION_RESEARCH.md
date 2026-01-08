# Video Generation API Research & Recommendations
## Fitness Influencer AI Assistant - Video Creation Improvements

**Date:** January 6, 2026  
**Context:** Evaluating alternatives to current Shotstack implementation  
**Current Issue:** Shotstack API may be failing due to non-production mode or rate limiting

---

## Current Implementation Analysis

### What You're Currently Using

**Stack:**
1. **Grok/xAI API** - Generate AI images ($0.07/image)
2. **Python Scripts** - Create background music and transitions (MoviePy/FFmpeg)
3. **Shotstack API** - Stitch images together into video (~$0.06/video)

**Current Flow:**
```
User Request → Grok generates 4 images → Python creates assets → Shotstack renders video
```

**Issues Identified:**
- Shotstack using "stage" environment (not production)
- Possible rate limiting from testing
- API key may not be configured properly
- Cost: ~$0.34 per 15-second video

**Note:** Your code shows `SHOTSTACK_API_BASE = "https://api.shotstack.io/stage"` which is the testing environment, not production.

---

## Alternative Video Generation APIs

### 1. ⭐ Creatomate (RECOMMENDED)

**Website:** https://creatomate.com  
**Pricing:** Pay-as-you-go starting at $0.05/video, or $49/mo for 1,000 videos

**Pros:**
- Template-based video creation (easier than Shotstack)
- Built-in motion graphics and animations
- No separate dev/production environments (simpler)
- Better documentation and Python SDK
- Supports JSON-based templates (easier to version control)
- Built-in text animations and effects
- Excellent for social media formats (9:16, 1:1, 16:9)
- Faster render times than Shotstack

**Cons:**
- Slightly higher base cost ($0.05 vs Shotstack $0.04)
- Newer platform (less established than Shotstack)

**Best For:**
- Social media content creators
- Automated video generation at scale
- Template-based workflows

**Python Example:**
```python
import requests

def create_video_with_creatomate(images, headline, cta):
    api_key = os.getenv('CREATOMATE_API_KEY')
    
    # Use template with dynamic sources
    payload = {
        "template_id": "your-template-id",
        "modifications": {
            "Image-1": images[0],
            "Image-2": images[1],
            "Image-3": images[2],
            "Image-4": images[3],
            "Headline-Text": headline,
            "CTA-Text": cta
        }
    }
    
    response = requests.post(
        'https://api.creatomate.com/v1/renders',
        headers={'Authorization': f'Bearer {api_key}'},
        json=payload
    )
    return response.json()
```

---

### 2. Remotion (Open Source Alternative)

**Website:** https://www.remotion.dev  
**Pricing:** FREE (self-hosted) or $20/user/mo for cloud rendering

**Pros:**
- **FREE for self-hosting** (huge cost savings)
- Write videos in React (programmatic control)
- No API rate limits when self-hosted
- Full control over rendering pipeline
- Great for developers
- Can render locally or use Lambda for cloud
- Active community and excellent docs

**Cons:**
- Requires React knowledge
- More setup complexity
- Need to manage your own infrastructure
- Longer development time initially

**Best For:**
- Developers comfortable with React/TypeScript
- High-volume video generation (no per-video costs)
- Full customization needs

**Example:**
```typescript
// Remotion video component
import {Composition} from 'remotion';

export const FitnessAd: React.FC<{
  images: string[];
  headline: string;
  cta: string;
}> = ({images, headline, cta}) => {
  return (
    <div>
      {images.map((img, i) => (
        <Sequence from={i * 90} durationInFrames={90}>
          <img src={img} />
          {i === 0 && <h1>{headline}</h1>}
          {i === images.length - 1 && <h2>{cta}</h2>}
        </Sequence>
      ))}
    </div>
  );
};
```

---

### 3. D-ID (AI Avatar Videos)

**Website:** https://www.d-id.com  
**Pricing:** $0.10-0.30 per video (pay-per-use)

**Pros:**
- Creates AI avatar videos (talking head)
- Can use uploaded photos as avatars
- Text-to-speech integration
- Great for personalized video messages
- Good for educational content

**Cons:**
- Higher cost than Shotstack/Creatomate
- Limited to avatar/talking head format
- Not suitable for dynamic fitness montages
- May look too "AI-generated"

**Best For:**
- Personalized coaching videos
- Educational content with presenter
- Text-to-video with narration

**Not Ideal For:** Your current use case (fitness montage ads)

---

### 4. Synthesia

**Website:** https://www.synthesia.io  
**Pricing:** $30/mo (10 videos) or custom enterprise

**Pros:**
- Professional AI avatars
- Multi-language support
- Enterprise-grade quality
- Good for training videos

**Cons:**
- Very expensive for high volume
- Focused on corporate/training videos
- Overkill for social media ads
- Limited creative control

**Best For:** Corporate training, not fitness social media ads

---

### 5. FFmpeg + MoviePy (Current Partial Implementation)

**Pricing:** FREE (open source)

**Pros:**
- **ZERO API costs**
- Full control over video creation
- Works offline
- No rate limits
- Fast processing with GPU acceleration
- You already have this partially implemented

**Cons:**
- Need to build everything yourself
- More code to maintain
- Transitions not as polished as cloud APIs
- Requires FFmpeg installed on server

**Best For:**
- Budget-conscious projects
- High-volume video generation
- Offline processing

**Enhanced Python Example:**
```python
from moviepy.editor import *
import numpy as np

def create_video_local(images, headline, cta, music_path):
    """Create video entirely with MoviePy (no cloud API)"""
    
    clips = []
    duration_per_image = 3.5
    
    for i, img_path in enumerate(images):
        # Create image clip
        clip = ImageClip(img_path, duration=duration_per_image)
        
        # Add fade transition
        clip = clip.crossfadein(0.5).crossfadeout(0.5)
        
        # Add text overlay on first and last
        if i == 0:
            txt = TextClip(headline, fontsize=70, color='white', 
                          font='Arial-Bold', stroke_color='black', 
                          stroke_width=2)
            txt = txt.set_pos('center').set_duration(duration_per_image)
            clip = CompositeVideoClip([clip, txt])
        
        if i == len(images) - 1:
            txt = TextClip(cta, fontsize=50, color='white')
            txt = txt.set_pos(('center', 'bottom')).set_duration(duration_per_image)
            clip = CompositeVideoClip([clip, txt])
        
        clips.append(clip)
    
    # Concatenate all clips
    final = concatenate_videoclips(clips, method="compose")
    
    # Add background music
    audio = AudioFileClip(music_path).subclip(0, final.duration)
    audio = audio.volumex(0.3)  # Lower music volume
    final = final.set_audio(audio)
    
    # Export
    final.write_videofile("output.mp4", fps=30, codec='libx264', 
                         audio_codec='aac', preset='medium')
    
    return "output.mp4"
```

---

### 6. RunwayML (AI Video Generation)

**Website:** https://runwayml.com  
**Pricing:** $12/mo (125 credits) - varies by operation

**Pros:**
- Cutting-edge AI video generation
- Text-to-video capabilities
- Image-to-video animation
- Creative effects and filters

**Cons:**
- Complex pricing model (credits)
- Still in beta for many features
- Can be expensive for simple tasks
- Slower than template-based solutions

**Best For:** Creative video effects, not template-based ads

---

## Recommended Approaches (Ranked)

### 🥇 Option 1: Fix Shotstack + Move to Production (Quick Win)

**Why:** You already have working code, just needs configuration fix

**Action Items:**
1. Update `SHOTSTACK_ENV` from "stage" to "v1" in `.env`
2. Get production API key from Shotstack dashboard
3. Test with small video first
4. Add error handling for rate limits

**Changes Needed:**
```python
# In shotstack_api.py
SHOTSTACK_API_BASE = "https://api.shotstack.io/v1"  # Change from "stage"

# In .env file
SHOTSTACK_ENV=v1
SHOTSTACK_API_KEY=your_production_key_here
```

**Cost:** $0.04-0.10 per video  
**Time:** 30 minutes to fix  
**Risk:** Low (already working)

---

### 🥈 Option 2: Switch to Creatomate (Best Long-term Solution)

**Why:** Better DX, more reliable, better for social media content

**Action Items:**
1. Sign up for Creatomate account
2. Create template in their visual editor
3. Replace Shotstack API calls with Creatomate
4. Test and deploy

**Implementation:**
```python
#!/usr/bin/env python3
"""
creatomate_api.py - Creatomate Video Generation Wrapper
"""
import os
import requests
from typing import List, Dict, Any

class CreatomateAPI:
    def __init__(self):
        self.api_key = os.getenv('CREATOMATE_API_KEY')
        self.base_url = "https://api.creatomate.com/v1"
    
    def create_fitness_ad(
        self,
        image_urls: List[str],
        headline: str,
        cta_text: str,
        duration: float = 15.0
    ) -> Dict[str, Any]:
        """Create fitness ad using Creatomate template"""
        
        # Use pre-made template
        payload = {
            "template_id": os.getenv('CREATOMATE_TEMPLATE_ID'),
            "modifications": {
                "Image_1": image_urls[0],
                "Image_2": image_urls[1],
                "Image_3": image_urls[2],
                "Image_4": image_urls[3],
                "Headline": headline,
                "CTA": cta_text,
                "Duration": duration
            }
        }
        
        response = requests.post(
            f"{self.base_url}/renders",
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            render_id = data[0]['id']
            
            # Poll for completion
            return self.wait_for_render(render_id)
        else:
            return {"success": False, "error": response.text}
    
    def wait_for_render(self, render_id: str) -> Dict[str, Any]:
        """Wait for video render to complete"""
        import time
        
        for _ in range(60):  # Max 5 minutes
            response = requests.get(
                f"{self.base_url}/renders/{render_id}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            
            data = response.json()
            status = data.get('status')
            
            if status == 'succeeded':
                return {
                    "success": True,
                    "video_url": data.get('url'),
                    "render_id": render_id
                }
            elif status == 'failed':
                return {"success": False, "error": "Render failed"}
            
            time.sleep(5)
        
        return {"success": False, "error": "Timeout"}
```

**Cost:** $0.05 per video (similar to current)  
**Time:** 2-3 hours to implement  
**Risk:** Low (similar to Shotstack)

---

### 🥉 Option 3: Pure Python with MoviePy (Zero Cost)

**Why:** FREE, no API dependencies, full control

**Action Items:**
1. Enhance your existing `video_jumpcut.py` script
2. Add music library (royalty-free tracks)
3. Implement professional transitions
4. Create text overlay templates

**Implementation:** Build out full MoviePy pipeline

**Cost:** $0 (only Grok images at $0.28)  
**Time:** 4-6 hours development  
**Risk:** Medium (more code to maintain)

---

### 🏆 Option 4: Hybrid Approach (Best of Both Worlds)

**Why:** Use MoviePy for free processing, Creatomate as backup for complex videos

**Strategy:**
- Simple videos (4 images + text): Use MoviePy (free)
- Complex videos (effects/animations): Use Creatomate ($0.05)
- Fallback: If MoviePy fails, use Creatomate

**Cost:** ~$0.07 per video average (70% savings)  
**Time:** 4-5 hours  
**Risk:** Low (has fallback)

---

## Cost Comparison (per 100 videos)

| Method | Image Gen | Video Creation | Total | Savings |
|--------|-----------|----------------|-------|---------|
| **Current (Shotstack)** | $28 | $6 | **$34** | Baseline |
| **Creatomate** | $28 | $5 | **$33** | 3% |
| **Shotstack (fixed)** | $28 | $4 | **$32** | 6% |
| **MoviePy Only** | $28 | $0 | **$28** | 18% |
| **Hybrid** | $28 | $1 | **$29** | 15% |
| **Remotion (self-hosted)** | $28 | $0* | **$28** | 18% |

*Remotion requires server costs but no per-video fees

---

## My Recommendation

### Immediate (Today): Fix Shotstack

1. Change environment from "stage" to "v1"
2. Verify API key is production key
3. Test with one video
4. Monitor for rate limit errors

### Short-term (This Week): Enhance with MoviePy Fallback

1. Build out local MoviePy video creation
2. Use as fallback if Shotstack fails
3. Reduces dependency on external API

### Long-term (This Month): Evaluate Creatomate

1. Sign up for trial
2. Create one template
3. Compare quality vs Shotstack
4. Migrate if better experience

---

## Code Changes Needed

### 1. Fix Shotstack Immediately

```python
# In execution/shotstack_api.py, line 21-22:
# CHANGE FROM:
SHOTSTACK_API_BASE = "https://api.shotstack.io/stage"  # Use "v1" for production

# CHANGE TO:
SHOTSTACK_API_BASE = "https://api.shotstack.io/v1"  # Production endpoint
```

### 2. Add MoviePy Fallback

```python
# In execution/video_ads.py
def create_video_ad(self, ...):
    # Try Shotstack first
    try:
        result = self.shotstack.create_fitness_ad(...)
        if result.get("success"):
            return result
    except Exception as e:
        print(f"Shotstack failed: {e}")
    
    # Fallback to local MoviePy
    print("Using MoviePy fallback...")
    return self.create_local_video(image_urls, headline, cta_text)

def create_local_video(self, images, headline, cta):
    """Create video locally with MoviePy (zero cost)"""
    from moviepy.editor import *
    
    clips = []
    for i, img_url in enumerate(images):
        # Download image
        img_path = self.download_image(img_url, f"img_{i}.jpg")
        
        # Create clip
        clip = ImageClip(img_path, duration=3.5)
        clip = clip.crossfadein(0.5).crossfadeout(0.5)
        clips.append(clip)
    
    final = concatenate_videoclips(clips, method="compose")
    output = ".tmp/video_ad.mp4"
    final.write_videofile(output, fps=30)
    
    return {"success": True, "video_path": output}
```

---

## Questions to Consider

1. **How many videos do you create per month?**
   - If < 50: Stick with Shotstack (cheap enough)
   - If 50-500: Consider Creatomate
   - If > 500: Use MoviePy or Remotion

2. **Do you need professional animations?**
   - Yes: Use Creatomate or Shotstack
   - No: MoviePy is sufficient

3. **How important is cost optimization?**
   - Critical: Go pure MoviePy/Remotion
   - Moderate: Use hybrid approach
   - Not important: Stick with Shotstack/Creatomate

4. **Do you have React/TypeScript skills?**
   - Yes: Consider Remotion for long-term
   - No: Stick with Python solutions

---

## Next Steps

Let me know which approach you'd like to pursue and I can:

1. **Fix Shotstack** - Update config to production mode
2. **Implement Creatomate** - Create full integration
3. **Build MoviePy solution** - Pure Python video generation
4. **Hybrid approach** - MoviePy + Creatomate fallback

All approaches will continue using Grok for image generation ($0.07/image) as that part is working well.

What would you like to do first?