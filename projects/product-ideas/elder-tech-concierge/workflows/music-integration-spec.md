# Elder Tech Music Player Integration Specification

*Created: 2026-01-16*
*Status: Planning*

---

## Overview

Add a simple "Play Music" button that allows seniors to listen to their favorite music without navigating complex interfaces.

---

## Requirements

### User Experience Goals
1. **Single tap** to start music
2. **No login required** at time of use (pre-configured)
3. **Voice control** compatible ("Play some jazz", "Stop music")
4. **Large controls** for pause/skip/volume

### Target Flow
```
1. Senior taps "Play Music" button
2. Music starts immediately (last station or default)
3. Simple overlay appears with:
   - Album art (large)
   - Song title (large text)
   - Pause button (giant)
   - Skip button (giant)
   - Volume slider (large)
4. Tap anywhere outside to minimize
5. Music continues in background
```

---

## Music Service Options Analysis

### Option A: Spotify Web Playback SDK

**Pros:**
- Rich API with playback control
- Web SDK works in browser
- Users may already have accounts

**Cons:**
- ❌ **Requires Spotify Premium** ($10.99/mo per user)
- ❌ **2025 Extended Quota restrictions** - Public apps limited to 25 users without approval
- ❌ Approval process takes 6+ weeks
- ❌ Must demonstrate "unique value" beyond basic playback

**Verdict:** Not viable for MVP due to Premium requirement and quota restrictions.

---

### Option B: Apple Music via MusicKit JS

**Pros:**
- Many seniors already have Apple Music (often bundled with family plans)
- Works well on iPad (native ecosystem)
- MusicKit JS available for web

**Cons:**
- Requires Apple Developer Program ($99/year)
- User must authenticate with Apple ID
- Less common among non-Apple users

**Verdict:** Viable if targeting iPad users. Consider for Phase 2.

---

### Option C: Pandora (RECOMMENDED FOR MVP)

**Pros:**
- ✅ **Free tier available** (ad-supported)
- ✅ Simpler interface (stations, not complex library)
- ✅ Popular with older demographics
- ✅ Web player embeddable
- ✅ No premium requirement for basic features

**Cons:**
- Ads on free tier (acceptable for MVP)
- Less control than Spotify
- Station-based, not on-demand

**Implementation:**
```html
<!-- Simple Pandora embed -->
<iframe src="https://www.pandora.com/embed?stationId=..."
        width="100%" height="200"></iframe>
```

**Verdict:** Best MVP option - free tier, familiar to seniors, simple station model.

---

### Option D: YouTube Music (via iframe)

**Pros:**
- Free tier with ads
- Huge library
- Works in browser

**Cons:**
- ❌ Embedding restrictions (ToS)
- ❌ Complex interface
- ❌ Not senior-friendly

**Verdict:** Not recommended.

---

### Option E: Internet Radio Streams

**Pros:**
- ✅ Completely free
- ✅ No accounts needed
- ✅ Simple - just play a stream URL
- ✅ Genre-based stations (jazz, classical, oldies)

**Cons:**
- No personalization
- Can't skip songs
- Quality varies

**Implementation:**
```javascript
// Simple audio player for radio streams
const radioStations = {
  jazz: "https://stream.example.com/jazz",
  classical: "https://stream.example.com/classical",
  oldies: "https://stream.example.com/oldies"
};

function playStation(genre) {
  const audio = new Audio(radioStations[genre]);
  audio.play();
}
```

**Verdict:** Excellent fallback option. Zero friction.

---

## Recommended Architecture

### MVP (Phase 1): Internet Radio + Pandora Option

```
┌─────────────────────────────────────────────────────────────┐
│                    Music Player Modal                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │     🎵  Currently Playing: Jazz Classics             │   │
│  │         "Fly Me to the Moon" - Frank Sinatra        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Jazz   │  │Classical│  │ Oldies  │  │ Gospel  │       │
│  │   🎺    │  │   🎻    │  │   🎸    │  │   ⛪    │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│          ┌──────────────────────────────┐                  │
│          │     ⏸️  PAUSE / ▶️  PLAY     │                  │
│          │        (GIANT BUTTON)        │                  │
│          └──────────────────────────────┘                  │
│                                                             │
│          🔊 ━━━━━━━━━━━━●━━━━━━━━━━━━━━ 🔊                │
│                     Volume                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  💡 "Link Pandora for personalized stations"        │   │
│  │       [Connect Pandora Account]                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Files

```
projects/elder-tech-concierge/
├── src/
│   ├── static/
│   │   └── music_player.js      # NEW: Audio player logic
│   └── templates/
│       └── music_modal.html     # NEW: Music UI component
```

### API Endpoints to Add

```python
# In app.py

@app.route('/api/music/stations')
def get_stations():
    """Return available radio stations"""
    return jsonify({
        "stations": [
            {"id": "jazz", "name": "Jazz Classics", "url": "...", "icon": "🎺"},
            {"id": "classical", "name": "Classical", "url": "...", "icon": "🎻"},
            {"id": "oldies", "name": "Golden Oldies", "url": "...", "icon": "🎸"},
            {"id": "gospel", "name": "Gospel", "url": "...", "icon": "⛪"}
        ]
    })

@app.route('/api/music/pandora/link', methods=['POST'])
def link_pandora():
    """Store Pandora account link for client"""
    # OAuth flow for Pandora
    pass
```

---

## Curated Radio Stations (Free Streams)

| Genre | Station | URL | Notes |
|-------|---------|-----|-------|
| Jazz | Jazz24 | `https://live.wostreaming.net/direct/ppm-jazz24aac-ibc1` | Public radio, high quality |
| Classical | KING FM | `https://stream.king.org/king-fm-mp3-128` | Seattle public radio |
| Oldies | Radio Paradise | `https://stream.radioparadise.com/aac-128` | Eclectic mix |
| Gospel | WLVF Gospel | Various | Christian music |
| Country | WSM Nashville | Various | Classic country |
| Easy Listening | SomaFM Groove Salad | `http://ice1.somafm.com/groovesalad-128-mp3` | Ambient/chill |

---

## Voice Commands to Support

| Command | Action |
|---------|--------|
| "Play music" | Open music player, start last station |
| "Play jazz" | Start jazz station |
| "Play classical music" | Start classical station |
| "Stop the music" | Pause playback |
| "Turn it up" | Increase volume 20% |
| "Turn it down" | Decrease volume 20% |
| "What's playing?" | Announce current song/station |

---

## Phase 2: Pandora Integration

If user has Pandora account:
1. OAuth flow during setup (you do this, not the senior)
2. Store refresh token in client config
3. Access their stations/thumbs
4. Personalized experience

---

## Phase 3: Apple Music (for iPad users)

If user has Apple Music:
1. MusicKit JS integration
2. Access their library/playlists
3. Requires Apple Developer enrollment

---

## Success Criteria

- [ ] Senior can start music with single tap
- [ ] Music plays immediately without login
- [ ] Controls are large and clearly labeled
- [ ] Volume can be adjusted easily
- [ ] Voice commands work for basic control
- [ ] Works offline with cached streams (stretch goal)

---

## Next Steps

1. [ ] Add "Play Music" button to main UI
2. [ ] Create music modal component
3. [ ] Implement radio stream player
4. [ ] Add volume/pause controls
5. [ ] Integrate with voice command system
6. [ ] Test on iPad for audio quality
