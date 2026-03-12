# Healing Tones — Sleep Frequency Generator

> Generates therapeutic tones and binaural beats through Bluetooth speakers for sleep.

## Usage

```bash
cd projects/marceau-solutions/labs/healing-tones

# List audio devices (find your Bluetooth speaker)
python healing_tones.py devices

# List all preset programs
python healing_tones.py presets

# Play a preset (8 hours by default)
python healing_tones.py play --preset deep-sleep

# Custom frequency at specific volume
python healing_tones.py play --freq 528 --volume 0.2 --duration 60

# Multiple frequencies layered
python healing_tones.py play --freq 174 285 528

# Binaural beat (stereo required)
python healing_tones.py play --binaural 200 3.0

# Target specific speaker
python healing_tones.py play --preset deep-sleep --device "JBL Flip"
```

## Dependencies
- `numpy` (installed)
- `sounddevice` (installed)

## Presets
| Preset | Frequencies | Best For |
|--------|------------|----------|
| `deep-sleep` | 174 + 285 Hz | All-night deep rest |
| `delta-waves` | 2 Hz binaural / 174 Hz | Delta brain entrainment |
| `healing-repair` | 285 + 528 Hz | Overnight cellular recovery |
| `binaural-delta` | 3 Hz binaural / 200 Hz | Deep sleep (headphones) |
| `binaural-theta` | 6 Hz binaural / 200 Hz | Light sleep, dreams |
| `solfeggio-cascade` | 174+285+396+528 Hz | Full healing spectrum |
| `pain-relief` | 174 Hz pure | Pain reduction |
| `love-frequency` | 528 Hz pure | DNA repair |
| `schumann-resonance` | 7.83 Hz binaural | Earth frequency |
| `wind-down` | 432 Hz + 10 Hz alpha | Pre-sleep relaxation (30 min) |
