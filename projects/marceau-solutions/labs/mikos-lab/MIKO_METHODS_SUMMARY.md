# Miko's Lab Methods — Executive Summary

*Extracted from 21 PDFs | Last updated: 2026-02-22*

---

## Quick Reference: Tool Stack

| Tool | Best For | Cost |
|------|----------|------|
| **Sora 2 Pro** | 25s UGC videos, storyboard mode | ChatGPT Pro ($200/mo) |
| **VEO 3 / 3.1** | Reels, short videos with audio | Google AI |
| **Seedance 2** | Realistic human motion | Via doubao.com or jimeng.jianying.com |
| **NanoBanana Pro** | Consistent character images | Cheap |
| **Ideogram** | Character fill, face swapping | Free tier available |
| **MiniMax** | Realistic TTS voices | $5/mo for 120 min |
| **Resemble AI** | Voice cloning, audio fixing | Per-use |
| **ElevenLabs** | Voice cloning (but less natural) | Various tiers |
| **Topaz** | Video upscaling | One-time purchase |

---

## The Core Workflow

### 1. Character Creation (Consistency is KEY)

**Option A: NanoBanana Pro**
- Create detailed prompt for your character
- Generate base image
- Use same prompt + style for all future images
- Character stays consistent across all content

**Option B: Sora 2 Character Cameos**
- Create character once in Sora
- Reuse in hundreds of videos
- Automatically maintains consistency

**Option C: Ideogram Character Fill**
- Generate base image of person with desired features
- Use Ideogram to swap face to your character
- Works for different poses/situations

### 2. Starting Frame Generation

For video, you need starting frames. Two approaches:

**Approach 1:** Generate all starting frames in NanoBanana (16:9 or 9:16)
- Full control over composition
- Character consistency locked in
- Colors stay consistent

**Approach 2:** Generate base image → Ideogram character fill
- More flexibility for different poses
- Swap face onto different body positions

### 3. Video Generation

**For UGC/Talking Head (25s):**
→ Sora 2 Pro Storyboard Mode

**For Reels/Short Clips:**
→ VEO 3 or Seedance 2

**For Longform Story Posts:**
→ HeyGen or Veed Fabric 1.0

### 4. Audio/Voice

**New Voiceover:**
1. Write script
2. Generate in MiniMax (most realistic)
3. Add to video

**Fixing AI Video Audio:**
1. Extract audio from AI video
2. Upload to Resemble AI
3. Pick realistic target voice
4. Replace audio

---

## Full-Body AI Video Workflow

### The Challenge
Most AI video tools struggle with:
- Consistent faces across clips
- Realistic full-body motion
- Natural movement that doesn't look "AI"

### The Solution: Image-to-Video (I2V)

**90% of projects should use Image-to-Video, not Text-to-Video**

1. **Create starting image** (full body, desired pose)
2. **Feed to video generator** (Sora 2, VEO 3, Seedance 2)
3. **Prompt the motion** you want from that starting point

### Seedance 2 Bypass (For Realistic Faces)

Seedance blocks overly realistic faces. Bypass:
> "Make this character as a realistic 3D character in T-pose"

Use this prompt in an image generator first, then feed to Seedance.

### Camera/Shot Types for Full Body

| Shot | Description |
|------|-------------|
| Wide Shot (WS) | Full body visible |
| Extreme Wide Shot (EWS) | Subject in environment |
| Medium Shot (MS) | Waist up |
| Close-Up (CU) | Face/shoulders |

---

## Prompting Best Practices

### VEO 3 Prompt Structure
```
[Technical specs] [Subject] [Action] in [Context]. 
[Camera movement] captures [Composition]. 
[Lighting/ambiance]. [Audio elements]. (no subtitles!)

Spoken lines:
Character: "dialogue"
```

### Sora 2 Prompt Structure
Use the Sora 2 prompting guide: upload to Claude project, describe what you want.

GitHub framework: https://github.com/snubroot/Veo-3-Meta-Framework

### NanoBanana JSON Method
Use Gemini or ChatGPT to turn ideas into JSON prompts:
- More detail = better output
- Specify lighting, composition, colors
- Lock in character features explicitly

---

## Monetization Paths

1. **AI Influencer Accounts**
   - Create persona
   - Post consistently
   - Grow following
   - Brand deals, merch, info products

2. **AI Content Agency**
   - Offer AI UGC to brands
   - $2K-10K per client
   - Scalable with systems

3. **Affiliate Marketing**
   - AI influencer promotes products
   - Trackable links
   - Passive income

4. **Digital Products**
   - Courses, templates, workflows
   - Sell what you learn

---

## Cost Optimization

### Get Tools 95% Cheaper
- Use API access instead of subscriptions
- kie.ai for Sora 2 Pro Storyboard
- Pool subscriptions
- Use free tiers strategically

### Cut Video Costs 60%
- Don't generate randomly — plan shots
- Use I2V (image-to-video) — more control
- Build library of reusable starting frames
- Test prompts on cheaper models first

---

## Key Insights

1. **Research before generating** — Use Perplexity + Reddit to understand your market
2. **I2V > T2V** — Image-to-video gives 10x better consistency
3. **Sora 2 Pro is currently king** for UGC (25s videos)
4. **VEO 3 videos are becoming "obviously AI"** as Sora 2 sets new standard
5. **Voice matters** — MiniMax sounds more natural than ElevenLabs
6. **Character consistency** is the difference between amateur and pro
7. **Copy what works** — Study viral formats, add your 3% twist

---

## Resources

- Sora 2 Prompting Guide: Ask in Claude project
- VEO 3 Meta Framework: https://github.com/snubroot/Veo-3-Meta-Framework
- Miko's Telegram: t.me/mikoslab
- ContentSystem: contentsystem.ai

---

*See KNOWLEDGE_BASE.md for full extracted content from all PDFs*
