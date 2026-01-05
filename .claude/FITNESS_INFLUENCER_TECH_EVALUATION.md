# Fitness Influencer Assistant - Technical Evaluation

**Date:** 2026-01-05
**Purpose:** Evaluate API vs Open-Source solutions for video editing, graphics, and content creation

---

## Executive Summary

**RECOMMENDATION: Use hybrid approach**
- ✅ **Canva API** - Official API available, worth integrating
- ❌ **CapCut** - No official API, use open-source alternatives (FFmpeg + MoviePy)
- ✅ **Grok/xAI** - Official API available for image generation
- ✅ **Open-Source Graphics** - Pillow for educational diagrams (cheaper than Canva subscription)

**Total Cost Savings:** ~$60-80/month by using open-source tools where appropriate

---

## Service-by-Service Evaluation

### 1. Canva API ✅ INTEGRATE

**API Status:** Official API available via Canva Connect APIs
**Cost:** Free for integration
**Documentation:** https://www.canva.dev/docs/connect/

**Capabilities:**
- Upload assets programmatically
- Create designs via API for users to edit
- Export finished designs back to system
- Design Editing API (generally available)
- Read and update layout/contents of designs

**Decision:** **USE CANVA API**
- Official API is robust and well-documented
- No subscription needed for API usage
- Can programmatically create branded content
- Seamless integration with existing workflows

**Implementation:**
- OAuth 2.0 authentication
- REST API integration
- Can create templates and auto-generate branded posts

**Sources:**
- [Canva Developers Platform](https://www.canva.com/developers/)
- [Canva Connect APIs](https://www.canva.dev/docs/connect/)
- [API Guide](https://zuplo.com/learning-center/canva-api)

---

### 2. CapCut ❌ NO API - USE ALTERNATIVES

**API Status:** No official API available
**Alternatives:** FFmpeg + MoviePy (open-source)

**CapCut Limitations:**
- No Python API
- No official automation platform support
- Unofficial solutions exist but unstable

**Decision:** **USE OPEN-SOURCE ALTERNATIVES**

**Recommended Stack:**
- **FFmpeg** - Industry-standard video processing
- **MoviePy** - Python library for video editing
- **Jumpcutter** - Automated silence/jump cut detection

**Capabilities with Open-Source:**
- ✅ Automatic jump cuts (silence detection)
- ✅ Video concatenation and trimming
- ✅ Title/text overlays
- ✅ Audio mixing
- ✅ Effects and transitions
- ✅ Format conversion
- ✅ Thumbnail generation

**Cost Comparison:**
- CapCut Pro: ~$10/month
- FFmpeg + MoviePy: **FREE**
- **Savings:** $120/year

**Implementation:**
```python
# Jump cuts with silence detection
import moviepy.editor as mp
from moviepy.video.tools.cuts import detect_scenes

# Automatic silence removal
# Text overlays for educational content
# Concatenate clips with transitions
```

**Sources:**
- [Jumpcutter GitHub](https://github.com/carykh/jumpcutter)
- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [FFmpeg Automation Guide](https://towardsdatascience.com/automatic-video-editing-using-python-324e5efd7eba/)

---

### 3. Grok/xAI Image Generation ✅ INTEGRATE

**API Status:** Official API available
**Cost:** $0.07 per image
**Model:** grok-2-image-1212 (Aurora)
**Documentation:** https://docs.x.ai/docs/guides/image-generations

**Capabilities:**
- Photorealistic rendering
- Precise text instruction following
- Multimodal input support
- Realistic portraits
- Text and logo rendering
- Generate up to 10 images per request

**Default Size:** 1024x768

**Decision:** **USE GROK API**
- Official, stable API
- Cost-effective ($0.07/image vs Midjourney ~$10-30/month)
- Excellent for fitness content (can generate realistic people)
- Compatible with OpenAI/Anthropic SDKs

**Use Cases:**
- Generate placeholder images for educational content
- Create custom backgrounds for video thumbnails
- Generate motivational graphics
- Fill in missing visual elements

**Cost Analysis:**
- Generating 100 images/month: $7
- Midjourney Basic: $10/month (200 images)
- **Grok is more flexible** - pay per use

**Sources:**
- [xAI API Documentation](https://x.ai/api)
- [Image Generation Guide](https://docs.x.ai/docs/guides/image-generations)
- [API Announcement](https://autogpt.net/xai-introduces-image-generation-api/)

---

### 4. Educational Graphics (Diagrams) - Pillow ✅ USE OPEN-SOURCE

**API Status:** Open-source library (Pillow 12.1.0)
**Cost:** FREE
**Alternative to:** Canva Pro subscription

**Capabilities:**
- Create diagrams programmatically
- Text overlays with custom fonts
- Shapes, arrows, annotations
- Color gradients and effects
- Layer composition
- Template-based generation

**Decision:** **USE PILLOW FOR DIAGRAMS**
- No subscription needed
- Full programmatic control
- Can recreate Fitness_Tips.jpeg style content
- Combine with Grok for background images

**Implementation:**
```python
from PIL import Image, ImageDraw, ImageFont

# Create educational fitness diagrams
# Add branded overlays (Marceau Solutions logo)
# Generate consistent styled content
```

**Cost Comparison:**
- Canva Pro: $12.99/month (for advanced features)
- Pillow: **FREE**
- **Savings:** $155/year

**Sources:**
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Real Python Tutorial](https://realpython.com/image-processing-with-the-python-pillow-library/)
- [GeeksforGeeks Guide](https://www.geeksforgeeks.org/python/python-pillow-tutorial/)

---

## Final Technology Stack

### Video Editing
- **FFmpeg** - Core video processing
- **MoviePy** - Python video editing
- **Jumpcutter** - Automatic jump cuts
- **Cost:** FREE

### Graphics & Design
- **Canva API** - For complex branded designs
- **Pillow** - For educational diagrams and overlays
- **Grok/xAI** - For AI-generated images
- **Cost:** Pay-per-use ($0.07/image)

### Other Integrations (To Build)
- **Gmail API** - Email monitoring and summarization
- **Google Calendar API** - Calendar and reminders
- **Google Sheets API** - Revenue/spend analytics

---

## Cost Analysis Summary

| Service | Subscription Cost | Alternative | Savings |
|---------|------------------|-------------|---------|
| CapCut Pro | $10/month | FFmpeg + MoviePy | $120/year |
| Canva Pro (graphics) | $12.99/month | Pillow | $155/year |
| **Total** | **$22.99/month** | **Open-source** | **$275/year** |

**Additional Costs:**
- Grok API: ~$7/month (100 images)
- Canva API: FREE (for basic usage)

**Net Savings: ~$268/year**

---

## Implementation Priority

### Phase 1: Core Infrastructure (Week 1)
1. ✅ Gmail API integration (email monitoring)
2. ✅ Google Calendar API (reminders)
3. ✅ Google Sheets API (analytics)

### Phase 2: Content Creation (Week 2)
4. ✅ Video editing with FFmpeg + MoviePy
5. ✅ Educational graphics with Pillow
6. ✅ Grok API integration for images

### Phase 3: Advanced Features (Week 3)
7. ✅ Canva API integration for branded designs
8. ✅ Automated jump cut detection
9. ✅ End-to-end content pipeline

---

## Decision Rationale

**Why NOT use paid subscriptions:**
1. **CapCut** - No API means manual work anyway, FFmpeg is more powerful
2. **Canva Pro** - For simple diagrams, Pillow is sufficient
3. **Cost efficiency** - Save $275/year while maintaining full automation

**Why USE these APIs:**
1. **Canva API** - Free and powerful for complex designs
2. **Grok API** - Cheap pay-per-use model, no subscription lock-in
3. **Google APIs** - Industry standard, reliable, well-documented

**Result:** Best of both worlds - official APIs where available, open-source where better suited.

---

## Next Steps

1. Create directive: `directives/fitness_influencer_operations.md`
2. Build execution scripts for each capability
3. Test with example fitness content (Fitness_Tips.jpeg style)
4. Deploy to Skills under `fitness-influencer-assistant` project
5. Document usage examples and workflows
