# Hybrid Video Generation System - Setup Guide

## Quick Start

The hybrid video generation system combines free local processing (MoviePy) with paid cloud fallback (Creatomate) to minimize costs while maintaining reliability.

**Target:** 70% of videos use free MoviePy, 30% use Creatomate = ~$0.015 per video average cost

---

## 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Note: The following packages are now included:
# - moviepy (local video processing)
# - pillow (image manipulation)
# - imageio-ffmpeg (FFmpeg wrapper)
# - pydub (audio processing)
```

---

## 2. Verify FFmpeg Installation

MoviePy requires FFmpeg for video processing.

### Check if FFmpeg is installed:
```bash
ffmpeg -version
```

### If not installed:

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg      # CentOS/RHEL
```

**Windows:**
- Download from: https://ffmpeg.org/download.html
- Add to PATH environment variable

---

## 3. Configure Environment Variables

Update your `.env` file with the following:

```bash
# Grok/xAI API (Required - for image generation)
XAI_API_KEY=your_xai_api_key_here

# Creatomate API (Optional - fallback for complex videos)
CREATOMATE_API_KEY=your_creatomate_api_key_here

# Shotstack API (Legacy - can remove if not used)
# SHOTSTACK_API_KEY=your_shotstack_key
# SHOTSTACK_ENV=v1
```

**Getting API Keys:**

- **Grok/xAI**: https://console.x.ai/ (Required)
- **Creatomate**: https://creatomate.com/ (Recommended but optional)
  - Free tier: 25 videos/month
  - Paid: $0.05 per video or subscription plans

---

## 4. Add Background Music (Optional)

For best results, add royalty-free music files to `execution/assets/music/`:

```bash
# Create music directory
mkdir -p execution/assets/music

# Add music files (MP3 format):
# - energetic.mp3
# - motivational.mp3
# - upbeat.mp3
# - calm.mp3
```

**Where to find royalty-free music:**
- https://www.bensound.com/
- https://incompetech.com/music/
- https://www.purple-planet.com/
- YouTube Audio Library

**Note:** Videos will work without music, but it's recommended for professional results.

---

## 5. Test the System

### Test MoviePy (Local, Free):

```bash
# Generate test video with MoviePy
cd execution
python intelligent_video_router.py \
  --images "https://picsum.photos/1080/1920,https://picsum.photos/1080/1920" \
  --headline "Test Video" \
  --cta "It Works!" \
  --force moviepy
```

### Test Creatomate (Cloud, Paid):

```bash
# Generate test video with Creatomate (only if API key configured)
python intelligent_video_router.py \
  --images "https://picsum.photos/1080/1920,https://picsum.photos/1080/1920" \
  --headline "Test Video" \
  --cta "It Works!" \
  --force creatomate
```

### Test Full Workflow:

```bash
# Let intelligent router decide (recommended)
python intelligent_video_router.py \
  --images "https://picsum.photos/1080/1920,https://picsum.photos/1080/1920,https://picsum.photos/1080/1920,https://picsum.photos/1080/1920" \
  --headline "Transform Your Body" \
  --cta "Start Today"
```

---

## 6. Create Your First Fitness Video Ad

```bash
cd execution

# Generate complete fitness ad with AI images + video
python video_ads.py \
  --concept "fitness transformation" \
  --headline "Transform Your Body in 90 Days" \
  --cta "Follow @yourhandle" \
  --duration 15 \
  --images 4
```

This will:
1. Generate 4 AI images with Grok ($0.28)
2. Create video with intelligent router ($0-$0.05)
3. Return video URL or local path
4. Log analytics for tracking

---

## 7. View Analytics

```bash
# Show usage statistics (last 30 days)
python execution/video_analytics_dashboard.py

# Show 7-day stats
python execution/video_analytics_dashboard.py --days 7

# Export to JSON for further analysis
python execution/video_analytics_dashboard.py --export stats.json
```

**Analytics Dashboard Shows:**
- Total videos generated
- Cost breakdown (MoviePy vs Creatomate)
- Success rates for each method
- Cost savings vs Creatomate-only
- Projected monthly/yearly costs
- Performance insights and recommendations

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  User Request                                │
│          "Create video ad for @boabfit"                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Video Ad Generator                              │
│        (execution/video_ads.py)                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
            ┌───────────┴──────────┐
            │                      │
            ▼                      ▼
    ┌───────────────┐      ┌─────────────────────┐
    │  Grok API     │      │ Intelligent Router  │
    │  (Images)     │      │ (Video Creation)    │
    │  $0.07/image  │      └─────────┬───────────┘
    └───────────────┘                │
                             ┌───────┴────────┐
                             │   Complexity   │
                             │   Analysis     │
                             └───────┬────────┘
                                     │
                      ┌──────────────┴──────────────┐
                      │                             │
                      ▼                             ▼
            ┌─────────────────┐         ┌─────────────────┐
            │  MoviePy        │         │  Creatomate     │
            │  (Local, Free)  │         │  (Cloud, $0.05) │
            │  ~70% usage     │         │  ~30% usage     │
            └─────────┬───────┘         └────────┬────────┘
                      │                          │
                      └────────────┬─────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Video Output      │
                        │   + Analytics Log   │
                        └─────────────────────┘
```

---

## Decision Logic

The Intelligent Router automatically chooses between MoviePy and Creatomate based on:

### Use MoviePy (Free) if:
- ✅ Simple text overlays (short headline, basic CTA)
- ✅ 4 or fewer images
- ✅ Recent MoviePy success rate > 70%
- ✅ No special characters or complex formatting

### Use Creatomate ($0.05) if:
- ❌ Complex text (multi-line, long headlines > 80 chars)
- ❌ More than 4 images
- ❌ Special characters or emojis
- ❌ MoviePy has been failing recently (< 70% success rate)

### Automatic Fallback:
- If MoviePy fails → automatically try Creatomate
- Ensures 100% success rate with minimal cost

---

## Cost Comparison

### Per Video:
| Method | Image Cost | Video Cost | Total | Savings |
|--------|------------|------------|-------|---------|
| Old (Shotstack only) | $0.28 | $0.06 | $0.34 | Baseline |
| Hybrid (70% MoviePy) | $0.28 | $0.015 | $0.295 | 13% |
| MoviePy only | $0.28 | $0 | $0.28 | 18% |
| Creatomate fallback | $0.28 | $0.05 | $0.33 | 3% |

### At Scale (200 videos/month):
| Method | Monthly Cost | Yearly Cost | Savings/Year |
|--------|--------------|-------------|--------------|
| Old (Shotstack) | $68 | $816 | Baseline |
| **Hybrid (70% MoviePy)** | **$59** | **$708** | **$108** |
| Pure MoviePy (if 100%) | $56 | $672 | $144 |
| Creatomate only | $66 | $792 | $24 |

---

## Troubleshooting

### Issue: "MoviePy not installed"
**Solution:**
```bash
pip install moviepy pillow imageio-ffmpeg
```

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg (see section 2 above)

### Issue: "Text rendering failed"
**Solution:** 
- MoviePy text rendering can be sensitive
- System will automatically fallback to Creatomate
- Check font availability: `fc-list | grep Arial`

### Issue: "CREATOMATE_API_KEY not set"
**Solution:** 
- This is optional - system will work with MoviePy only
- Add to `.env` if you want cloud fallback
- Get key from: https://creatomate.com/

### Issue: Low MoviePy success rate (< 50%)
**Solution:**
1. Check logs: `cat .tmp/logs/video_generation.jsonl | tail -20`
2. Look for common errors
3. Verify FFmpeg is working: `ffmpeg -version`
4. Try simpler text (shorter headlines)

### Issue: Videos have no music
**Solution:**
- Add MP3 files to `execution/assets/music/`
- Or remove music parameter from requests
- Videos work fine without music

---

## Best Practices

### 1. Keep Headlines Short
- Aim for < 80 characters
- Avoid multi-line text if possible
- Simple text = higher MoviePy success rate = lower costs

### 2. Use Standard Image Counts
- 4 images = 15-second video (optimal)
- 2-3 images = shorter videos (also work well)
- 5+ images = may trigger Creatomate fallback

### 3. Monitor Analytics
```bash
# Check weekly to optimize
python execution/video_analytics_dashboard.py --days 7
```

### 4. Review Failures
```bash
# See what's failing
grep '"success": false' .tmp/logs/video_generation.jsonl | tail -10
```

### 5. Test First
- Test with placeholder images before generating expensive AI images
- Use `https://picsum.photos/1080/1920` for testing

---

## FAQ

**Q: Do I need Creatomate API key?**
A: No, it's optional. System will work with MoviePy only, but Creatomate provides a reliable fallback for complex videos.

**Q: What if MoviePy keeps failing?**
A: System automatically falls back to Creatomate. Check troubleshooting section for common issues.

**Q: Can I force using only MoviePy?**
A: Yes, use `--force moviepy` flag. But fallback to Creatomate recommended for reliability.

**Q: How much does this save vs old system?**
A: ~18% per video, or ~$108/year at 200 videos/month.

**Q: Where are videos stored?**
A: MoviePy videos: `.tmp/moviepy/video_*.mp4` (local)
   Creatomate videos: Returned as URLs (cloud)

**Q: Do I need background music?**
A: No, it's optional. Videos work without music but sound better with it.

**Q: Can I use this for other content (not fitness)?**
A: Yes! Just change the prompts and text. System works for any video ads.

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure API keys
3. ✅ Test the system
4. ✅ Create your first video
5. ✅ Monitor analytics
6. 📈 Scale up production!

**Need Help?** Check the detailed code documentation in each script.

**Want to Optimize Further?** Review analytics regularly and investigate failures to improve MoviePy success rate.