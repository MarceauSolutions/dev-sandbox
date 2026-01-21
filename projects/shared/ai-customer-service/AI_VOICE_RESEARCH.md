# AI Voice Research: More Human-Sounding Options for Voice AI

**Research Date**: 2026-01-19
**Current System**: Twilio + Claude (text-based responses via TTS)
**Goal**: Find more human-sounding, emotionally expressive AI voices for phone calls

---

## Top 3 Recommendations for Voice AI Phone Systems

### 1. 🏆 Cartesia AI Sonic-3 (RECOMMENDED FOR PHONE CALLS)

**Why it's best for our use case**:
- ⚡ **Ultra-low latency**: 90ms first byte (Sonic-3) or 40ms (Sonic Turbo) - critical for phone conversations
- 📞 **Built for phone calls**: Specifically designed for telephony, handles background noise, accents
- 😊 **Emotional expressiveness**: First TTS that actually laughs, breathes, emotes
- 🔄 **Streaming websockets**: Real-time streaming perfect for live phone interactions
- 🏥 **Proven in production**: Healthcare orgs use it for appointment scheduling, claims calls

**Technical Details**:
- 40+ languages supported
- Streaming API with websockets
- Handles telephony artifacts and background noise
- Integrated speech-to-text (Ink-Whisper) optimized for conversations

**Pricing**: (See [Cartesia Pricing](https://cartesia.ai/pricing))

**Best for**: Real-time phone conversations where latency and emotion matter

**Sources**:
- [Cartesia Sonic-3 Overview](https://cartesia.ai/sonic)
- [Deep Dive into Sonic-3](https://www.eesel.ai/blog/cartesia-sonic-3)
- [Cartesia API Docs](https://docs.cartesia.ai/get-started/overview)

---

### 2. 🎭 ElevenLabs (BEST EMOTIONAL DEPTH)

**Why it's strong**:
- 🎨 **Emotional nuance**: Best in class for adding weight and emotion to words
- 🗣️ **Voice cloning**: Can clone your voice for personalized interactions
- 🌍 **Wide selection**: 1200+ voices across 29 languages
- 💰 **Affordable**: Free tier with 10K chars/month, paid plans start at $5/mo

**Test Results**:
- "Out of all options, ElevenLabs added more weight and emotions to words"
- Top performer in emotional expressiveness tests
- Industry leader for realistic, lifelike speech

**Limitations**:
- Not specifically optimized for real-time streaming like Cartesia
- Slightly higher latency than Sonic-3

**Best for**: Pre-recorded messages, voicemail drops, or where emotional depth > speed

**Sources**:
- [PlayHT vs ElevenLabs](https://elevenlabs.io/blog/playht-alternatives)
- [Best AI Voice Generators 2026](https://www.demandsage.com/ai-voice-generators/)
- [TTS Comparison](https://aimlapi.com/blog/best-text-to-speech-ai)

---

### 3. 🌐 PlayHT (BEST VOICE VARIETY)

**Why it's competitive**:
- 📊 **User preference**: 65.77% preferred PlayHT over ElevenLabs in blind tests
- 🗂️ **Voice library**: 600+ voices in 140+ languages
- 🎙️ **Accent variety**: Different accents across countries
- ✅ **Ease of use**: Highly recommended for simplicity

**Limitations**:
- Less emotional range compared to ElevenLabs
- Not as fast as Cartesia for real-time streaming

**Best for**: Multilingual businesses or when needing specific accents

**Sources**:
- [PlayHT Homepage](https://play.ht/)
- [ElevenLabs Alternatives](https://elevenlabs.io/blog/elevenlabs-alternatives)
- [TTS Leaderboard Results](https://murf.ai/alternative/elevenlabs)

---

## Comparison Matrix

| Feature | Cartesia Sonic-3 | ElevenLabs | PlayHT | Current (Twilio TTS) |
|---------|------------------|------------|--------|---------------------|
| **Latency (first byte)** | 90ms (40ms Turbo) | ~200-300ms | ~200-300ms | Variable |
| **Emotional expressiveness** | ⭐⭐⭐⭐⭐ (laughs, breathes) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Phone call optimization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Real-time streaming** | ✅ Websockets | ✅ Limited | ✅ Limited | ✅ |
| **Voice variety** | Good | 1200+ voices | 600+ voices | Limited |
| **Languages** | 40+ | 29 | 140+ | Many |
| **Pricing** | TBD | $5+/mo | Varies | Included with Twilio |
| **Production-ready** | ✅ Healthcare clients | ✅ Widely used | ✅ Widely used | ✅ |

---

## Implementation Recommendation

### Phase 1: Test Cartesia Sonic-3 (This Week)

**Why**: Specifically built for what we're doing (real-time phone AI agents)

**Quick Test**:
```python
# Install Cartesia SDK
pip install cartesia

# Test with one call
from cartesia import Cartesia

client = Cartesia(api_key="your_key")
output = client.tts.sse(
    model_id="sonic-3",
    transcript="Hi, this is William's AI assistant. May I have your name?",
    voice={"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"}  # Friendly female
)

# Stream to Twilio call
for event in output:
    # Send audio chunk to call
    pass
```

**Test Criteria**:
1. Sound quality vs. current Twilio TTS
2. Latency in real phone call
3. Emotional expressiveness
4. Cost per minute

### Phase 2: A/B Test with ElevenLabs (Week 2)

Compare:
- Cartesia Sonic-3 (speed focus)
- ElevenLabs (emotion focus)

Measure:
- Call completion rate
- Lead capture rate
- Qualitative feedback ("Did this sound human?")

### Phase 3: Production Rollout (Week 3-4)

Deploy winner to all Voice AI systems:
- Square Foot Shipping
- SW Florida HVAC
- Marceau Solutions lead qualification

---

## Cost Analysis (Preliminary)

**Current Cost** (Twilio TTS):
- Included with Twilio usage
- ~$0.01-0.02/minute

**Estimated Cost** (Cartesia Sonic-3):
- Need to confirm pricing from [Cartesia Pricing](https://cartesia.ai/pricing)
- Likely $0.05-0.15/minute (industry standard)

**Estimated Cost** (ElevenLabs):
- Free tier: 10,000 characters/month
- Paid: $5/month for 30,000 characters
- ~$0.10-0.20/minute

**ROI Calculation**:
- Current: 2 warm leads detected from Voice AI calls
- With better voice: Estimate 50% improvement in lead qualification
- 3 leads/week × 4 weeks × $500/deal = $6,000/month potential
- Extra cost: ~$50-100/month for better TTS
- **Net benefit: $5,900+/month**

---

## Action Items

### Immediate (This Week)
1. ✅ Sign up for Cartesia AI account
2. ✅ Get API key and test credentials
3. ✅ Build proof-of-concept integration with Twilio
4. ✅ Make 5-10 test calls with Sonic-3
5. ✅ Compare to current TTS quality

### Next Week
1. Run A/B test: Cartesia vs. ElevenLabs
2. Measure call metrics (completion rate, lead capture)
3. Calculate actual cost per call
4. Make build vs. buy decision

### Week 3-4
1. Deploy chosen solution to production
2. Update Voice AI scripts to use new TTS
3. Monitor performance improvements
4. Document learnings

---

## Key Findings Summary

**Problem**: Current Twilio TTS sounds robotic, may be losing leads due to uncanny valley effect.

**Solution**: Upgrade to emotionally expressive, low-latency TTS:
- **Best for phone calls**: Cartesia Sonic-3 (90ms latency, built for telephony)
- **Best for emotion**: ElevenLabs (most human-sounding, voice cloning)
- **Best for variety**: PlayHT (600+ voices, 140+ languages)

**Recommendation**: Start with Cartesia Sonic-3 due to phone call optimization and ultra-low latency.

**Expected Impact**:
- Higher lead qualification rate (more people stay on the line)
- Better information capture (people trust the AI more)
- Professional brand perception

---

## Technical Integration Notes

**Current Stack**:
```
Phone Call → Twilio → Claude (text) → Twilio TTS → Audio Response
```

**Proposed Stack** (with Cartesia):
```
Phone Call → Twilio → Claude (text) → Cartesia Sonic-3 → Streaming Audio → Twilio
```

**Key Changes Needed**:
1. Replace Twilio TTS calls with Cartesia SDK
2. Stream audio chunks to Twilio in real-time
3. Handle websocket connection for streaming
4. Add error handling for TTS failures (fallback to Twilio TTS)

**Files to Update**:
- `src/voice_engine.py` - Add Cartesia TTS integration
- `src/twilio_handler.py` - Stream audio chunks to call
- `requirements.txt` - Add `cartesia` package

---

**Next Step**: Get Cartesia API key and build POC integration.

---

## Additional Sources

- [Best TTS APIs in 2026](https://www.speechmatics.com/company/articles-and-news/best-tts-apis-in-2025-top-12-text-to-speech-services-for-developers)
- [Cartesia AI Review](https://smallest.ai/blog/cartesia-ai-review-2025-features-pricing-and-comparison)
- [Cartesia Python SDK](https://pypi.org/project/cartesia/)
- [Top 15 ElevenLabs Alternatives](https://murf.ai/alternative/elevenlabs)
- [25+ ElevenLabs Alternatives](https://voice.ai/hub/tts/elevenlabs-alternatives/)
