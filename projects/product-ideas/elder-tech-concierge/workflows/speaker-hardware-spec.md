# Elder Tech Voice Speaker - Hardware Project Specification

*Created: 2026-01-16*
*Status: Planning*
*Project Type: Hardware + Firmware*

---

## Vision

Build a custom Alexa-like speaker device that:
- Connects to the Elder Tech iPad app via WiFi
- Captures voice input and streams to the web server
- Outputs Claude's audio responses
- Acts as a hands-free voice assistant for seniors

**Key Insight:** The speaker is a "dumb terminal" - all AI processing happens on the existing Flask server. The speaker just handles audio I/O.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Elder Tech Ecosystem                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐         WiFi          ┌──────────────────────────┐   │
│  │              │◄────────────────────►│                          │   │
│  │  Elder Tech  │  WebSocket/HTTP      │   Elder Tech Speaker     │   │
│  │  iPad App    │                      │   (ESP32 or RPi)         │   │
│  │              │                      │                          │   │
│  │  - Web UI    │                      │   - Microphone           │   │
│  │  - Browser   │                      │   - Speaker              │   │
│  │              │                      │   - Wake word detection  │   │
│  └──────┬───────┘                      │   - LED status           │   │
│         │                              └──────────────────────────┘   │
│         │ HTTP                                                         │
│         ▼                                                              │
│  ┌──────────────┐                                                     │
│  │              │                                                     │
│  │  Flask       │  ◄──── Handles all AI, TTS, STT                    │
│  │  Server      │                                                     │
│  │  (Your Mac   │                                                     │
│  │   or Cloud)  │                                                     │
│  │              │                                                     │
│  └──────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Options

### Option A: ESP32 with I2S Audio (RECOMMENDED FOR MVP)

**Why ESP32:**
- ✅ **$5-15 cost** (vs $35+ for Raspberry Pi)
- ✅ Built-in WiFi
- ✅ I2S support for digital audio
- ✅ Low power consumption
- ✅ Small form factor
- ✅ Arduino/PlatformIO development

**Components List:**

| Component | Model | Price | Purpose |
|-----------|-------|-------|---------|
| Microcontroller | ESP32-WROOM-32 | $5 | Brain |
| Microphone | INMP441 I2S MEMS | $4 | Voice capture |
| Amplifier | MAX98357A I2S | $5 | Audio output |
| Speaker | 3W 4Ω Speaker | $3 | Sound output |
| LED | WS2812B Ring (8) | $3 | Status indicator |
| Case | 3D Printed | $5 | Enclosure |
| Power | 5V 2A USB-C | $5 | Power supply |
| **Total** | | **~$30** | |

**Pros:**
- Very low cost
- Small and embeddable
- Can be battery powered
- Fast boot time

**Cons:**
- Limited processing (no on-device wake word)
- Requires always-on connection to server
- Audio quality limited by I2S bandwidth

---

### Option B: Raspberry Pi Zero 2 W

**Why RPi Zero 2 W:**
- More processing power for on-device wake word
- Better audio quality options
- Familiar Linux environment
- Python-friendly

**Components List:**

| Component | Model | Price | Purpose |
|-----------|-------|-------|---------|
| Computer | Raspberry Pi Zero 2 W | $15 | Brain |
| Microphone | ReSpeaker 2-Mic HAT | $12 | Voice capture with array |
| Speaker | 3W Speaker + GPIO | $5 | Sound output |
| SD Card | 16GB microSD | $8 | Storage |
| LED | NeoPixel Ring | $3 | Status |
| Case | 3D Printed | $5 | Enclosure |
| Power | 5V 2.5A USB-C | $8 | Power supply |
| **Total** | | **~$56** | |

**Pros:**
- Can run Porcupine wake word locally
- Better audio processing (noise cancellation)
- More expandable
- Full Linux stack

**Cons:**
- Higher cost
- Slower boot time (~15-30 seconds)
- Higher power consumption
- Supply chain issues (RPi availability)

---

### Option C: ESP32-S3 with PSRAM (BEST BALANCE)

**Why ESP32-S3:**
- ✅ More RAM than base ESP32 (supports wake word)
- ✅ Built-in USB
- ✅ ESP-SR library for offline wake word
- ✅ Still low cost (~$8)

**This is the "Goldilocks" option** - cheap like ESP32, capable like RPi.

**Components List:**

| Component | Model | Price | Purpose |
|-----------|-------|-------|---------|
| Microcontroller | ESP32-S3-WROOM-1 (8MB PSRAM) | $8 | Brain + wake word |
| Microphone | INMP441 I2S | $4 | Voice capture |
| Amplifier | MAX98357A I2S | $5 | Audio output |
| Speaker | 3W 4Ω Speaker | $3 | Sound |
| LED | WS2812B Ring | $3 | Status |
| Case | 3D Printed | $5 | Enclosure |
| Power | USB-C breakout | $5 | Power |
| **Total** | | **~$33** | |

---

## Recommended Approach: ESP32-S3

### Why ESP32-S3 Wins:
1. **Offline wake word** - "Hey Elder Tech" detected locally
2. **Low cost** - Only $3 more than base ESP32
3. **Fast response** - No Linux boot time
4. **Low power** - Can run on battery
5. **Simple deployment** - Flash firmware once, done

---

## Firmware Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-S3 Firmware                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Wake Word Detection (Local)              │   │
│  │              ESP-SR "Hi Elder Tech"                   │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │ Wake detected                   │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Audio Capture (INMP441)                  │   │
│  │              16kHz, 16-bit, mono                      │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │ Raw audio                       │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              WebSocket Client                         │   │
│  │              Stream audio to Flask server             │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Audio Playback (MAX98357A)               │   │
│  │              Play response from server                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LED Status (WS2812B)                     │   │
│  │              - Blue pulse: Listening                  │   │
│  │              - Green: Processing                      │   │
│  │              - White: Speaking                        │   │
│  │              - Red: Error/Offline                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Server-Side Changes

### New WebSocket Endpoint

```python
# In app.py

from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    """Receive audio from speaker, process, respond"""
    # 1. Receive raw audio bytes
    audio_bytes = data['audio']

    # 2. Send to speech-to-text (Whisper API or local)
    transcript = speech_to_text(audio_bytes)

    # 3. Process with Claude
    response = claude_respond(transcript)

    # 4. Convert to speech (TTS)
    audio_response = text_to_speech(response)

    # 5. Send back to speaker
    emit('audio_response', {'audio': audio_response})

@socketio.on('speaker_status')
def handle_speaker_status(data):
    """Track speaker online status"""
    speaker_id = data['speaker_id']
    status = data['status']  # 'online', 'offline', 'listening'
    log_speaker_status(speaker_id, status)
```

---

## Bill of Materials (Full Build)

### ESP32-S3 Voice Speaker Kit

| Item | Qty | Unit Cost | Total | Source |
|------|-----|-----------|-------|--------|
| ESP32-S3-DevKitC-1 (8MB PSRAM) | 1 | $10 | $10 | Amazon/AliExpress |
| INMP441 I2S Microphone | 1 | $4 | $4 | Amazon |
| MAX98357A I2S Amplifier | 1 | $5 | $5 | Amazon |
| 3W 4Ω Speaker (40mm) | 1 | $3 | $3 | Amazon |
| WS2812B LED Ring (8 LED) | 1 | $3 | $3 | Amazon |
| USB-C Breakout Board | 1 | $2 | $2 | Amazon |
| Jumper wires | 20 | $0.05 | $1 | Amazon |
| Prototype PCB | 1 | $2 | $2 | Amazon |
| 3D Printed Case | 1 | $5 | $5 | Local/Online |
| **TOTAL** | | | **$35** | |

### Bulk Pricing (10 units)
| Item | Qty | Unit Cost | Total |
|------|-----|-----------|-------|
| All components (bulk) | 10 | $25 | $250 |
| Assembly time (1hr each) | 10 | $15 | $150 |
| **TOTAL (10 units)** | | | **$400 ($40/unit)** |

---

## Development Phases

### Phase 1: Proof of Concept (Week 1-2)
- [ ] Order ESP32-S3 dev kit and audio components
- [ ] Set up PlatformIO development environment
- [ ] Test I2S microphone capture
- [ ] Test I2S speaker playback
- [ ] Basic WiFi connection to Flask server

### Phase 2: Audio Streaming (Week 3-4)
- [ ] Implement WebSocket audio streaming
- [ ] Add server-side STT endpoint
- [ ] Add server-side TTS endpoint
- [ ] Test round-trip latency

### Phase 3: Wake Word (Week 5-6)
- [ ] Train custom wake word "Hey Elder Tech"
- [ ] Integrate ESP-SR library
- [ ] Test wake word accuracy
- [ ] Add LED status feedback

### Phase 4: Enclosure & Polish (Week 7-8)
- [ ] Design 3D printable case
- [ ] Print and test fit
- [ ] Add physical mute button
- [ ] Create setup/pairing flow

### Phase 5: Production (Week 9+)
- [ ] Create assembly documentation
- [ ] Build 5 prototype units
- [ ] Field test with beta users
- [ ] Iterate based on feedback

---

## Wiring Diagram

```
ESP32-S3 DevKit
┌─────────────────────────────────────────┐
│                                         │
│  3V3 ────────────────── INMP441 VDD     │
│  GND ────────────────── INMP441 GND     │
│  GPIO 12 ────────────── INMP441 SCK     │
│  GPIO 11 ────────────── INMP441 WS      │
│  GPIO 13 ────────────── INMP441 SD      │
│                                         │
│  5V ─────────────────── MAX98357A VIN   │
│  GND ────────────────── MAX98357A GND   │
│  GPIO 14 ────────────── MAX98357A BCLK  │
│  GPIO 15 ────────────── MAX98357A LRC   │
│  GPIO 16 ────────────── MAX98357A DIN   │
│                                         │
│  GPIO 48 ────────────── WS2812B DIN     │
│  5V ─────────────────── WS2812B VCC     │
│  GND ────────────────── WS2812B GND     │
│                                         │
│  GPIO 0 ─────────────── Mute Button     │
│                                         │
└─────────────────────────────────────────┘
```

---

## Project Directory Structure

```
projects/elder-tech-speaker/
├── firmware/
│   ├── platformio.ini
│   ├── src/
│   │   ├── main.cpp
│   │   ├── audio_capture.cpp
│   │   ├── audio_playback.cpp
│   │   ├── wifi_manager.cpp
│   │   ├── websocket_client.cpp
│   │   ├── wake_word.cpp
│   │   └── led_status.cpp
│   └── lib/
│       └── esp-sr/
├── hardware/
│   ├── schematic.pdf
│   ├── bom.csv
│   └── case/
│       ├── elder_tech_speaker.stl
│       └── elder_tech_speaker.f3d
├── server/
│   └── audio_endpoints.py    # Flask additions
├── docs/
│   ├── assembly-guide.md
│   ├── setup-guide.md
│   └── troubleshooting.md
├── KICKOFF.md
├── VERSION
└── CHANGELOG.md
```

---

## Integration with Elder Tech Concierge

The speaker complements (not replaces) the iPad:

| Feature | iPad App | Voice Speaker |
|---------|----------|---------------|
| Visual UI | ✅ Primary | ❌ No screen |
| Voice input | ✅ Button | ✅ Wake word |
| Audio output | ✅ TTS | ✅ TTS |
| Contact calling | ✅ One-tap | ✅ Voice |
| Music | ✅ Full UI | ✅ Voice only |
| Emergency | ✅ Red button | ✅ "Emergency!" |
| Setup | ✅ Pre-configured | Paired to iPad |

**Pairing Flow:**
1. Senior receives iPad (pre-configured) + Speaker
2. Speaker shows up in iPad app as "Pair Device"
3. Senior taps to pair (or you do this during setup)
4. Speaker and iPad are linked
5. Either device can initiate actions

---

## Cost Analysis

### Per-Unit Cost
- Hardware: $35
- Assembly: $15 (1 hour)
- **Total: $50/unit**

### Pricing Strategy

| Package | Contents | Suggested Price |
|---------|----------|-----------------|
| iPad Only | Pre-configured iPad | $299 setup + $49-99/mo |
| iPad + Speaker | iPad + Voice Speaker | $349 setup + $49-99/mo |
| Speaker Add-on | Voice Speaker only (existing customer) | $79 one-time |

**Margin on speaker add-on:** $79 - $50 = $29 profit per unit

---

## Success Criteria

- [ ] Wake word detection works reliably (>90% accuracy)
- [ ] Round-trip voice latency < 2 seconds
- [ ] Speaker stays connected for 24+ hours
- [ ] Audio quality clear enough for seniors
- [ ] LED feedback intuitive
- [ ] Setup takes < 5 minutes
- [ ] Works 10+ feet from speaker

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| WiFi dropouts | Medium | High | Auto-reconnect, offline indicator |
| Wake word false positives | Medium | Medium | Train custom model, add confirmation |
| Audio quality issues | Low | High | Test multiple speakers, add gain control |
| ESP32 availability | Low | Medium | ESP32-S3 widely available |
| Assembly complexity | Medium | Medium | Create detailed guide, consider PCB |

---

## Next Steps

1. [ ] Order prototype components (~$35)
2. [ ] Set up PlatformIO environment
3. [ ] Create `projects/elder-tech-speaker/` directory
4. [ ] Build proof of concept (mic → WiFi → speaker)
5. [ ] Integrate with existing Flask server
6. [ ] Test with Elder Tech iPad app
