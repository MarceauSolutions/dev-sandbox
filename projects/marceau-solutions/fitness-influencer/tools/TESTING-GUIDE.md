# Real-User Testing Guide: AI Avatar Pipeline

Step-by-step walkthrough to test every AI component for the fitness influencer platform.

## Before You Start

### 1. Check Your Environment

Run the prerequisite check on each script you plan to use:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/marceau-solutions/fitness-influencer/tools

# Check all scripts at once
for script in test_*.py; do echo "=== $script ===" && python "$script" --check && echo; done
```

### 2. API Keys You Need

Add any missing keys to `/Users/williammarceaujr./dev-sandbox/.env`:

| Key | Already Set? | Needed For | Get It At |
|-----|-------------|------------|-----------|
| `XAI_API_KEY` | YES | Character images, seed bracketing, image-to-video | https://console.x.ai |
| `OPENAI_API_KEY` | YES | DALL-E 3 (premium images) | https://platform.openai.com |
| `REPLICATE_API_TOKEN` | NO | Talking head, face restore | https://replicate.com/account/api-tokens |
| `FAL_API_KEY` | NO | MiniMax voice, lip sync | https://fal.ai/dashboard/keys |
| `ELEVENLABS_API_KEY` | NO | Voice cloning + TTS | https://elevenlabs.io |
| `RESEMBLE_API_KEY` | NO | Voice enhancement | https://apresep.resemble.ai |

**Minimum for a full pipeline test:** `XAI_API_KEY` + `REPLICATE_API_TOKEN` (~$0.20 total)

### 3. Install Missing Packages

```bash
pip install replicate requests python-dotenv
```

---

## Test Pathway A: Quick Avatar (Cheapest — ~$0.20)

Uses only XAI + Replicate. Produces a talking head video from scratch.

### Step 1: Generate Character Image (~$0.07)

```bash
tho
```

Output: `output/consistency_YYYYMMDD_HHMMSS/character_01.png` through `character_03.png`

**What to look for:** Pick the best face — consistent features, good lighting, realistic skin.

### Step 2: Find Best Seed (~$0.21)

Take the prompt from Step 1 and bracket seeds to find reproducible quality:

```bash
python test_seed_bracketing.py \
  --prompt "30 year old athletic man, short brown hair, slight beard, wearing black athletic shirt, professional headshot, studio lighting, neutral background, shot on RED Komodo, 8K" \
  --seeds 1000-1003 \
  --tier standard
```

Output: `output/seeds_YYYYMMDD_HHMMSS/seed_01000.png` through `seed_01003.png` + `manifest.json`

**What to look for:** Which seed gives the most realistic, consistent face? Note the seed number.

### Step 3: Enhance the Best Face (~$0.005)

```bash
python test_face_restore.py \
  --image output/seeds_YYYYMMDD_HHMMSS/seed_01003.png
```

Output: `output/seed_01003_gfpgan_YYYYMMDD_HHMMSS.png`

**What to look for:** Sharper features, clearer eyes, smoother skin vs the original.

### Step 4: Create Talking Head Video (~$0.05)

You need an audio file. Record a short clip (5-10 seconds) or use a TTS service:

```bash
# If you have audio already:
python test_talking_head.py \
  --image output/seed_01003_gfpgan_YYYYMMDD_HHMMSS.png \
  --audio /path/to/your/audio.mp3 \
  --enhance
```

Output: `output/talking_head_YYYYMMDD_HHMMSS.mp4`

**What to look for:** Lip movement matches audio, head movement is natural, face quality holds up.

**Total cost: ~$0.34 for 3 images + 4 seeds + face restore + talking head**

---

## Test Pathway B: Full Pipeline with Voice (~$1.00)

Adds voice generation. Requires `FAL_API_KEY` or `ELEVENLABS_API_KEY`.

### Steps 1-3: Same as Pathway A

Generate character → find best seed → enhance face.

### Step 4: Generate Voice (~$0.04)

**Option A — MiniMax (most realistic, requires FAL_API_KEY):**

```bash
# List available voices first
python test_voice_minimax.py --list-voices

# Generate speech
python test_voice_minimax.py \
  --text "Hey everyone, welcome back to the channel. Today we're going to crush a full body workout in just 20 minutes. No excuses, let's get after it." \
  --voice "male-qn-qingse"
```

**Option B — ElevenLabs (best cloning, requires ELEVENLABS_API_KEY):**

```bash
# List voices
python test_voice_elevenlabs.py --list-voices

# Generate with a premade voice
python test_voice_elevenlabs.py \
  --text "Hey everyone, welcome back to the channel. Today we're going to crush a full body workout in just 20 minutes." \
  --voice-id 21m00Tcm4TlvDq8ikWAM

# Clone YOUR voice (record 30s+ sample first)
python test_voice_elevenlabs.py --clone --sample my_voice_sample.mp3 --name "MyFitnessVoice"
```

**What to look for:** Natural cadence, no robotic artifacts, energy matches fitness content.

### Step 5: Create Talking Head with Generated Voice

```bash
python test_talking_head.py \
  --image output/seed_01003_gfpgan_YYYYMMDD_HHMMSS.png \
  --audio output/minimax_YYYYMMDD_HHMMSS.mp3 \
  --enhance
```

### Step 6 (Optional): Lip Sync an Existing Video (~$0.12)

If you animated the character into a video first:

```bash
# Animate the still image into video
python test_image_to_video.py \
  --image output/seed_01003_gfpgan_YYYYMMDD_HHMMSS.png \
  --prompt "person speaking to camera, slight head movement, professional studio" \
  --aspect 9:16

# Then lip sync the generated voice onto that video
python test_lipsync.py \
  --video output/seed_01003_animated_YYYYMMDD_HHMMSS.mp4 \
  --audio output/minimax_YYYYMMDD_HHMMSS.mp3
```

---

## Test Pathway C: Compare Everything

Run comparison modes to evaluate quality across providers/models.

### Compare Face Restoration Models

```bash
python test_face_restore.py --image output/character_01.png --compare-all
```

Generates side-by-side GFPGAN vs Real-ESRGAN outputs.

### Compare Lip Sync Models

```bash
python test_lipsync.py --video output/talking_head.mp4 --audio output/voice.mp3 --compare-all
```

Generates one output per lip sync model (Lipsync 1.9, 2.0, MuseTalk, LatentSync).

### Compare Voice Consistency

```bash
python test_voice_elevenlabs.py \
  --consistency \
  --text "Welcome to today's workout" \
  --voice-id YOUR_VOICE_ID \
  --count 5
```

Generates 5 versions of same text — listen for consistency.

---

## Cost Estimators

Every script has a `--cost` flag to estimate before spending:

```bash
python test_voice_minimax.py --cost --text "Your full script here..."
python test_voice_elevenlabs.py --cost --text "Your full script here..."
python test_voice_resemble.py --cost --text "Your full script here..."
python test_lipsync.py --cost --duration 30
python test_talking_head.py --cost --duration 10
python test_face_restore.py --cost --count 5
```

### Full Pipeline Cost Breakdown

| Step | Tool | Cost |
|------|------|------|
| 1. Generate 3 character images | Grok Aurora | $0.21 |
| 2. Seed bracket (4 seeds) | Grok Aurora | $0.28 |
| 3. Face restore (1 image) | GFPGAN | $0.005 |
| 4. Voice generation (10s) | MiniMax | ~$0.04 |
| 5a. Talking head | SadTalker | ~$0.05 |
| 5b. OR Lip sync (10s) | Lipsync 1.9 | ~$0.12 |
| **Total (with talking head)** | | **~$0.59** |
| **Total (with lip sync)** | | **~$0.66** |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `--check` shows key NOT SET | Add the key to `~/dev-sandbox/.env` |
| `replicate: NOT INSTALLED` | Run `pip install replicate` |
| `ModuleNotFoundError: requests` | Run `pip install requests` |
| Replicate returns 401 | Check `REPLICATE_API_TOKEN` is correct (starts with `r8_`) |
| fal.ai returns 401 | Check `FAL_API_KEY` is correct |
| Output file is 0 bytes | API returned error — check terminal output for details |
| Talking head face looks blurry | Add `--enhance` flag for built-in GFPGAN |
| Lip sync doesn't match | Try `--model lipsync2` for higher quality ($3/min vs $0.70/min) |
| Seed bracketing too expensive | Use `--tier budget` ($0.003/img) or fewer seeds `--seeds 1000-1003` |

---

## API Cost Guardrails

**These rules apply to every testing session.** API credits are real money. Free tiers are finite. Every call counts.

### Rule 1: Pre-Flight Checks Before Every Generation

**Never call a paid API without running these two commands first:**

```bash
# Step 1: Verify API keys are set and packages installed
python test_[script].py --check

# Step 2: See what it will cost BEFORE spending
python test_[script].py --cost [--duration 10 | --count 1 | --text "..."]
```

If `--check` shows a missing key or package, **stop and fix it** — don't proceed hoping it will work.

### Rule 2: Minimum Viable Test Parameters

When testing functionality (not production quality), use the cheapest settings:

| Parameter | Testing Value | Production Value |
|-----------|--------------|-----------------|
| `--count` | `1` | `3-5` |
| `--tier` | `budget` | `standard` or `premium` |
| `--seeds` | `1000-1002` (3 seeds) | `1000-1010` (11 seeds) |
| `--duration` | shortest possible | full length |
| Voice text | 1 short sentence | Full script |

**Example — testing vs production:**
```bash
# TESTING: Verify the pipeline works ($0.003)
python test_character_consistency.py --prompt "Athletic man" --count 1 --tier budget

# PRODUCTION: Generate quality options ($0.35)
python test_character_consistency.py --prompt "Athletic man, 30yo..." --count 5 --tier standard
```

### Rule 3: Use Free Alternatives for Pipeline Testing

When you just need to verify the pipeline connects end-to-end, use free tools:

| Paid Tool | Free Alternative | When to Use Free |
|-----------|-----------------|------------------|
| ElevenLabs / MiniMax TTS | macOS `say` command | Testing talking head pipeline |
| Replicate face restore | Skip (use raw image) | Testing lip sync pipeline |
| Grok image generation | Use an existing photo | Testing voice + talking head |

**macOS TTS fallback (free, always available):**
```bash
# Generate speech locally — $0.00
say -o output/test_voice.aiff "Welcome to today's workout"
ffmpeg -i output/test_voice.aiff -codec:a libmp3lame -qscale:a 2 output/test_voice.mp3
```

**Use your own face photo (free, best consistency):**
```bash
# Skip character generation + seed bracketing entirely
python test_face_restore.py --image /path/to/your/photo.jpg
python test_talking_head.py --image /path/to/your/photo.jpg --audio output/test_voice.mp3
```

### Rule 4: Never Retry Failed API Calls Blindly

When an API call fails:

1. **Read the error message** — don't just re-run
2. **Diagnose the root cause** before trying again:
   - `401/403` = Auth problem (key missing, wrong permissions, exhausted balance)
   - `402` = Billing problem (add credit, upgrade plan)
   - `404` = Wrong model ID or endpoint
   - `429` = Rate limited (wait, don't retry immediately)
   - `500` = Provider issue (wait 5 min, then try once more)
3. **Fix the issue** before spending another API call
4. **Never loop retries** — if it fails twice with the same error, stop

### Rule 5: Track Provider Billing Status

Before starting a testing session, verify your accounts have credit:

| Provider | Check Balance | Minimum Needed |
|----------|--------------|----------------|
| Replicate | https://replicate.com/account/billing | $5 (auto-bill) |
| ElevenLabs | https://elevenlabs.io/subscription | Free tier: 10K chars/month |
| fal.ai | https://fal.ai/dashboard/billing | $1+ balance |
| Resemble AI | https://app.resemble.ai/billing | Free tier: limited |
| xAI/Grok | https://console.x.ai | Check usage dashboard |

**If a provider is exhausted, skip it** — use a different provider or free alternative. Don't burn through a different provider's credits as a workaround unless it's intentional.

### Rule 6: Session Budget Caps

Set a mental budget before each testing session:

| Session Type | Budget | What You Get |
|--------------|--------|-------------|
| Pipeline verification | $0.00 | macOS TTS + existing photo + local tools |
| Single component test | $0.10 | 1 generation at budget tier |
| Pathway A (full pipeline) | $0.50 | 3 images + 4 seeds + restore + talking head |
| Pathway B (with voice) | $1.00 | Full pipeline with paid voice |
| Comparison testing | $2.00 | Multiple providers/models side by side |

**If you hit your budget, stop.** Review what you have before spending more.

### Rule 7: One Thing at a Time

Don't run comparison modes (`--compare-all`) until you've verified the basic pipeline works with single calls. Comparison modes multiply cost by the number of models.

**Wrong order (expensive):**
```bash
# BAD: $0.50+ to find out your audio file is corrupt
python test_lipsync.py --video face.mp4 --audio speech.mp3 --compare-all
```

**Right order (cheap):**
```bash
# GOOD: $0.12 to verify it works, THEN compare if quality matters
python test_lipsync.py --video face.mp4 --audio speech.mp3 --model lipsync19
# Only after success:
python test_lipsync.py --video face.mp4 --audio speech.mp3 --compare-all
```

### Quick Reference: Testing Checklist

Before every API call, confirm:

- [ ] `--check` passed (keys set, packages installed)
- [ ] `--cost` reviewed (know what you're spending)
- [ ] Provider has credit/free tier remaining
- [ ] Using minimum parameters (count 1, budget tier)
- [ ] Not retrying a failed call without diagnosing the error
- [ ] Within session budget

---

## Output Directory

All outputs go to `tools/output/` (gitignored). Structure:

```
output/
├── consistency_20260209_143022/    # Character consistency batches
│   ├── character_01.png
│   ├── character_02.png
│   └── character_03.png
├── seeds_20260209_144512/          # Seed bracketing results
│   ├── seed_01000.png
│   ├── seed_01001.png
│   ├── manifest.json               # Metadata + costs
│   └── ...
├── minimax_20260209_150033.mp3     # Voice outputs
├── talking_head_20260209_151200.mp4 # Talking head videos
├── lipsync_sync19_20260209_152000.mp4 # Lip synced videos
└── character_01_gfpgan_20260209.png # Face restored images
```
