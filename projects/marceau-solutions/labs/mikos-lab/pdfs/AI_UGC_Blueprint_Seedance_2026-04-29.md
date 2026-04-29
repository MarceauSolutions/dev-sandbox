# THE AI UGC BLUEPRINT
**Step-by-Step Guide to Realistic AI Videos**
Seedance 2.0 + Claude Code + Advanced Techniques
by Miko

**Source:** Private channel from Miko (sent to William 2026-04-29)
**Public channel:** t.me/mikoslab
**Premium:** contentsystem.ai

---

## WHAT YOU'RE GETTING
- Prompting method for realistic voices (works every time)
- Realistic human movements and breathing system (key for realism)
- Method to make infinite-length videos that maintain consistency
- How to get AI tools for dirt cheap (90% off)

The two things that give away AI videos immediately are **voice** and **movement**. This guide fixes both.

---

## STEP 1: ACCESSING SEEDANCE 2.0
ByteDance's AI video model. Accepts images, videos, audio, and text simultaneously.

**Where to access:**
- **Higgsfield** (recommended for beginners, no waitlist, global)
- jimeng.jiaying.com (Chinese interface, works globally)
- dreamina.capcut.com

---

## STEP 2: CREATING REALISTIC STARTING IMAGES
Garbage in, garbage out. Foundation matters.

1. **Find a TikTok reference** in your niche (search the brand or category)
2. **Screenshot a good frame** — natural lighting, good composition
3. **Get a JSON prompt** from Claude/Gemini:
   > "Analyze this photo and give me a very detailed JSON prompt that can recreate it. It should be very detailed about the lighting, colors, composition, stance, and overall aesthetic."
4. **Generate in Nano Banana Pro** — adjust the JSON for your character/clothes/background

JSON handles realism + color grading. Adjustments handle content. 10× better than text-only prompts.

---

## STEP 3: CREATING REALISTIC AUDIO

### Method A: Voice ID Reference (Most Realistic)
1. Find a real video of someone with the voice quality you want
2. Extract MP3 audio
3. Upload to Seedance, prompt: *"Use this audio as voice ID reference for her voice. Do not make her say the words in the audio, just use it as a voice ID."*
4. Add your dialogue separately

### Method B: Pre-Generated Audio
Generate voiceover with MiniMax or ElevenLabs, upload directly. Always include dialogue timestamps in the prompt.

---

## STEP 4: SETTING UP YOUR ASSETS (THE @ SYSTEM)
Seedance auto-labels uploaded files: `@Image1`, `@Image2`, `@Video1`, `@Audio1`. Reference them in the prompt.

**Example:**
> "@Image1 is the starting image of the video. @Image2 is how the coffee bag looks like. For the reference of the dialogue and audio, use @Audio1."

**Specs:**
- Up to 9 images
- Up to 3 videos (15s max total)
- Up to 3 audio files (15s max MP3)
- 4–15 second output per generation
- Native 2K resolution
- 12 files max per generation

---

## STEP 5: TIMESTAMP PROMPTING METHOD
Seedance follows instructions better than any other model — but you have to give it instructions.

**Example:**
```
0-4 seconds: Introduction
Dialogue: "I just made a peanut butter cup protein coffee with 25 grams of protein."
Visuals: Subject holds a clear round glass jar of light brown coffee. Her LEFT hand
holds the glass while her RIGHT hand actively stirs the drink.

5-12 seconds: Benefits Explanation
Dialogue: "Getting 20 to 30 grams of protein right in the morning in your coffee
really helps so much."
Visuals: Subject sets down the glass, picks up the protein bag from @Image2,
holds it toward camera while speaking.
```

The model follows everything to the literal last sentence.

---

## STEP 6: CREATING REALISTIC HUMAN MOVEMENTS
**The biggest AI giveaway.**

### The Problem: Symmetrical Movement
Most AI models move symmetrically — both hands sync, head tilts with shoulders. Real humans move asymmetrically with breathing, twitches, micro-movements.

### The Solution: Specify Each Hand Separately
> "Her LEFT hand holds the glass while her RIGHT hand actively stirs. She shifts her weight to her left side."

### Add Natural Imperfections:
- **Weight shifts:** "shifts her weight to her left side"
- **Head tilts:** "slight head tilt as she speaks"
- **Idle movements:** "adjusts her hair briefly"
- **Imperfect posture:** "slouches slightly"
- **Breathing:** "subtle breathing movement in shoulders"

---

## STEP 7: EXTENDING VIDEOS (INFINITE LENGTH)
Seedance caps at 15s per generation. To extend:

1. Generate first 15s with timestamp method
2. Download the clip
3. Re-upload as `@Video1`
4. Prompt:
   > "Extend @Video1. Keep the voice the same as the original clip. For the protein milk, when she says protein milk, use this bottle (@Image2). 16-30 seconds: She explains the benefits. Dialogue: 'Getting protein in the morning helps so much.' Visuals: She picks up the protein milk bottle, shows it to camera."

Maintains continuity — same character, voice, environment. Chain for 45–60 second videos (Miko does 3 extensions typically).

---

## STEP 8: BYPASSING THE 2000 CHARACTER LIMIT (Canva Method)
1. Open Canva, create a 9:16 image
2. Type the full detailed prompt as text on the image (movements broken down by second)
3. Upload as a Seedance reference
4. In the prompt say: *"Transcribe this image and use the movements described here."*

Seedance reads the text in the reference image. Lets you have extremely detailed prompts.

---

## STEP 9: LET THE MODEL HANDLE EDITING
Seedance is trained by ByteDance (TikTok). It already understands:
- Cuts between angles
- Natural transitions
- UGC-feel movement
- Short-form pacing

If you want specific edits (jump cut, zoom on reveal), say so in the prompt.

---

## STEP 10: POST PRODUCTION

### Basic Workflow
1. Export clips from Seedance
2. Bring into CapCut
3. Arrange clips
4. Add captions

### Upscaling Workflow (Important)
1. Run video through **Topaz Video** at 2× upscale and **60fps**
2. Bring upscaled video into CapCut
3. Export at **30fps**

The 60fps upscale → 30fps export creates smoother, more realistic movement.

---

## HOW TO GET AI TOOLS FOR DIRT CHEAP

### Method 1: Premium Accounts via z2u.com (95% off)
| Tool | z2u Price | Retail |
|------|-----------|--------|
| Gemini Pro | $1 | $20/mo |
| Gemini Ultra | $10 | $250/mo |
| ChatGPT Plus | $3-5 | $20/mo |
| MidJourney | $5-10 | $30/mo |
| Claude Pro | $5-10 | $20/mo |
| Runway | $5-10 | $15/mo |

URL: `https://www.z2u.com/gemini/accounts-5-28045`

Full access, latest models, extended credits. Always check seller ratings.

### Method 2: API Access via Kie.ai (70-80% off)
For automations:
- VEO3 API: `https://kie.ai/features/v3-api`
- Sora 2 API: `https://kie.ai/sora-2`

Miko uses Kie.ai for all automations and ad generation.

---

## QUICK REFERENCE — FULL PIPELINE
1. Find TikTok reference in your niche, screenshot good frame
2. Get JSON prompt from Claude/Gemini → generate in Nano Banana Pro
3. Find realistic voice reference OR generate with MiniMax/ElevenLabs
4. Upload assets to Seedance using @ system
5. Write timestamp prompt with detailed per-hand movements
6. Generate first 15 seconds
7. Extend using original video as reference
8. Repeat extensions until full length
9. Upscale with Topaz at 60fps, export at 30fps

## KEY THINGS TO REMEMBER
- Voice ID reference = most realistic voices
- Specify LEFT and RIGHT hand separately = breaks symmetry
- Add weight shifts, head tilts, idle movements = natural imperfections
- Timestamp method = model follows exactly what you say
- Canva image method = bypass 2000 character limit
- 60fps upscale → 30fps export = smoother final video

5–10 minutes per video once the system is dialed. Model handles 95% of the work — you direct it.
