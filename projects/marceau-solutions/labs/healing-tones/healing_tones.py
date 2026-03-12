#!/usr/bin/env python3
"""
Healing Tones — Sleep frequency generator for Bluetooth speakers.

Generates pure tones, binaural beats, and layered soundscapes at
therapeutic frequencies. Routes audio to whatever output device is
active (including Bluetooth speakers).

Usage:
    # List available audio devices (find your Bluetooth speaker)
    python healing_tones.py devices

    # List all preset programs
    python healing_tones.py presets

    # Play a preset sleep program all night (8 hours)
    python healing_tones.py play --preset deep-sleep

    # Play a specific frequency
    python healing_tones.py play --freq 432 --duration 60

    # Binaural beats (requires stereo headphones/speaker)
    python healing_tones.py play --preset binaural-delta

    # Custom layered soundscape
    python healing_tones.py play --freq 174 285 396 --duration 480

    # Set volume (0.0-1.0) and fade in/out
    python healing_tones.py play --preset deep-sleep --volume 0.3 --fade 30

    # Route to a specific device
    python healing_tones.py play --preset deep-sleep --device "William's Speaker"
"""

import argparse
import signal
import sys
import time
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

# ─── Constants ───────────────────────────────────────────────────────────────

SAMPLE_RATE = 44100
DEFAULT_VOLUME = 0.25  # Gentle for sleep
DEFAULT_FADE_SECONDS = 15  # Smooth fade in/out
DEFAULT_DURATION_MINUTES = 480  # 8 hours

# ─── Frequency Presets ───────────────────────────────────────────────────────

SOLFEGGIO_FREQUENCIES = {
    174: "Pain relief, foundation",
    285: "Tissue healing, cellular repair",
    396: "Release fear and guilt",
    417: "Facilitate change, undo negative",
    432: "Universal harmony (Verdi tuning)",
    528: "DNA repair, transformation (Love frequency)",
    639: "Reconnecting, relationships",
    741: "Detox, problem solving",
    852: "Spiritual awakening, intuition",
    963: "Crown chakra, divine connection",
}

BRAIN_WAVE_BANDS = {
    "delta": (0.5, 4.0, "Deep sleep, healing, recovery"),
    "theta": (4.0, 8.0, "Light sleep, meditation, creativity"),
    "alpha": (8.0, 13.0, "Relaxation, calm focus"),
    "beta": (13.0, 30.0, "Active thinking (not for sleep)"),
}


@dataclass
class ToneLayer:
    """A single tone in a soundscape."""
    frequency: float
    amplitude: float = 1.0  # Relative to master volume
    wave_type: str = "sine"  # sine, triangle, or pink


@dataclass
class BinauralBeat:
    """Binaural beat = two slightly different frequencies, one per ear."""
    base_freq: float
    beat_freq: float  # Difference between L and R channels
    amplitude: float = 1.0


@dataclass
class Preset:
    """A named healing program."""
    name: str
    description: str
    duration_minutes: int
    layers: list  # List of ToneLayer or BinauralBeat
    volume: float = DEFAULT_VOLUME


# ─── Preset Programs ────────────────────────────────────────────────────────

PRESETS = {
    "deep-sleep": Preset(
        name="Deep Sleep",
        description="174 Hz (pain relief) + 285 Hz (cellular repair) — low solfeggio blend for deep rest",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            ToneLayer(174, amplitude=1.0),
            ToneLayer(285, amplitude=0.6),
        ],
        volume=0.20,
    ),
    "delta-waves": Preset(
        name="Delta Wave Sleep",
        description="2 Hz binaural beat over 174 Hz carrier — entrains brain to deep sleep delta rhythm",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            BinauralBeat(174, beat_freq=2.0),
        ],
        volume=0.22,
    ),
    "healing-repair": Preset(
        name="Healing & Repair",
        description="285 Hz (tissue) + 528 Hz (DNA repair) — overnight cellular recovery",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            ToneLayer(285, amplitude=1.0),
            ToneLayer(528, amplitude=0.5),
        ],
        volume=0.18,
    ),
    "binaural-delta": Preset(
        name="Binaural Delta (headphones)",
        description="3 Hz delta beat over 200 Hz — deep sleep entrainment (stereo required)",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            BinauralBeat(200, beat_freq=3.0),
        ],
        volume=0.25,
    ),
    "binaural-theta": Preset(
        name="Binaural Theta (headphones)",
        description="6 Hz theta beat over 200 Hz — light sleep, vivid dreams (stereo required)",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            BinauralBeat(200, beat_freq=6.0),
        ],
        volume=0.25,
    ),
    "solfeggio-cascade": Preset(
        name="Solfeggio Cascade",
        description="174 + 285 + 396 + 528 Hz — full low-spectrum solfeggio healing bath",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            ToneLayer(174, amplitude=1.0),
            ToneLayer(285, amplitude=0.7),
            ToneLayer(396, amplitude=0.5),
            ToneLayer(528, amplitude=0.3),
        ],
        volume=0.15,
    ),
    "pain-relief": Preset(
        name="Pain Relief",
        description="174 Hz pure tone — the lowest solfeggio, foundation frequency for pain",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            ToneLayer(174, amplitude=1.0),
        ],
        volume=0.22,
    ),
    "love-frequency": Preset(
        name="Love Frequency (528 Hz)",
        description="528 Hz — DNA repair, transformation, the 'miracle tone'",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            ToneLayer(528, amplitude=1.0),
        ],
        volume=0.20,
    ),
    "schumann-resonance": Preset(
        name="Schumann Resonance",
        description="7.83 Hz binaural beat — Earth's natural electromagnetic frequency",
        duration_minutes=DEFAULT_DURATION_MINUTES,
        layers=[
            BinauralBeat(200, beat_freq=7.83),
        ],
        volume=0.22,
    ),
    "wind-down": Preset(
        name="Wind Down (30 min)",
        description="432 Hz harmony + alpha binaural (10 Hz) — pre-sleep relaxation",
        duration_minutes=30,
        layers=[
            ToneLayer(432, amplitude=0.8),
            BinauralBeat(200, beat_freq=10.0, amplitude=0.5),
        ],
        volume=0.20,
    ),
}

# ─── Tone Generation ────────────────────────────────────────────────────────


def generate_sine(freq, duration_sec, sample_rate=SAMPLE_RATE):
    """Generate a pure sine wave."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def generate_pink_noise(duration_sec, sample_rate=SAMPLE_RATE):
    """Generate pink noise (1/f) for masking."""
    samples = int(sample_rate * duration_sec)
    white = np.random.randn(samples)
    # Simple 1/f filter via cumulative averaging
    b = [0.049922035, -0.095993537, 0.050612699, -0.004709510]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    from scipy.signal import lfilter
    pink = lfilter(b, a, white)
    # Normalize
    peak = np.max(np.abs(pink))
    if peak > 0:
        pink = pink / peak
    return pink


def apply_fade(signal, fade_seconds, sample_rate=SAMPLE_RATE):
    """Apply fade-in and fade-out to avoid clicks."""
    fade_samples = int(fade_seconds * sample_rate)
    if fade_samples > len(signal) // 2:
        fade_samples = len(signal) // 2

    # Fade in
    fade_in = np.linspace(0, 1, fade_samples)
    signal[:fade_samples] *= fade_in

    # Fade out
    fade_out = np.linspace(1, 0, fade_samples)
    signal[-fade_samples:] *= fade_out

    return signal


def build_chunk(layers, chunk_seconds, volume, sample_rate=SAMPLE_RATE):
    """Build a stereo audio chunk from layers.

    Returns (samples, 2) numpy array ready for playback.
    """
    n_samples = int(sample_rate * chunk_seconds)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)
    t = np.linspace(0, chunk_seconds, n_samples, endpoint=False)

    for layer in layers:
        if isinstance(layer, BinauralBeat):
            freq_l = layer.base_freq - layer.beat_freq / 2
            freq_r = layer.base_freq + layer.beat_freq / 2
            left += layer.amplitude * np.sin(2 * np.pi * freq_l * t)
            right += layer.amplitude * np.sin(2 * np.pi * freq_r * t)
        elif isinstance(layer, ToneLayer):
            if layer.wave_type == "sine":
                wave = layer.amplitude * np.sin(2 * np.pi * layer.frequency * t)
            elif layer.wave_type == "triangle":
                wave = layer.amplitude * (2 * np.abs(2 * (t * layer.frequency - np.floor(t * layer.frequency + 0.5))) - 1)
            else:
                wave = np.zeros(n_samples)
            left += wave
            right += wave

    # Normalize to prevent clipping, then apply volume
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-10)
    left = (left / peak) * volume
    right = (right / peak) * volume

    # Interleave to stereo
    stereo = np.column_stack([left, right]).astype(np.float32)
    return stereo


# ─── Playback Engine ─────────────────────────────────────────────────────────

class HealingPlayer:
    """Continuous tone playback using streaming callback — no gaps."""

    def __init__(self, layers, volume=DEFAULT_VOLUME, fade_seconds=DEFAULT_FADE_SECONDS,
                 device=None, sample_rate=SAMPLE_RATE):
        self.layers = layers
        self.volume = volume
        self.fade_seconds = fade_seconds
        self.device = device
        self.sample_rate = sample_rate
        self.running = False

    def play(self, duration_minutes):
        """Play tones for the specified duration using continuous stream."""
        self.running = True
        duration_sec = duration_minutes * 60
        total_samples = int(duration_sec * self.sample_rate)
        fade_in_samples = int(self.fade_seconds * self.sample_rate)
        fade_out_samples = int(self.fade_seconds * self.sample_rate)

        # Pre-build one cycle chunk (2 seconds) that we loop seamlessly
        # Use a duration that's a whole number of cycles for all frequencies
        # to avoid clicks at the loop boundary
        cycle_sec = 2.0
        cycle_chunk = build_chunk(self.layers, cycle_sec, self.volume, self.sample_rate)
        cycle_len = len(cycle_chunk)

        # Track position across callbacks
        state = {"pos": 0, "total": total_samples}

        def callback(outdata, frames, time_info, status):
            if not self.running:
                outdata[:] = 0
                raise sd.CallbackStop

            pos = state["pos"]
            remaining = state["total"] - pos

            if remaining <= 0:
                outdata[:] = 0
                self.running = False
                raise sd.CallbackStop

            # Fill output buffer by looping through the cycle chunk
            written = 0
            while written < frames and self.running:
                cycle_pos = (pos + written) % cycle_len
                available = min(cycle_len - cycle_pos, frames - written)
                # Don't write past the total duration
                if written + available > remaining:
                    available = remaining - written
                outdata[written:written + available] = cycle_chunk[cycle_pos:cycle_pos + available]
                written += available
                if written >= remaining:
                    break

            # Zero-fill any leftover
            if written < frames:
                outdata[written:] = 0

            # Apply fade-in at the start
            if pos < fade_in_samples:
                for i in range(min(frames, fade_in_samples - pos)):
                    fade = (pos + i) / fade_in_samples
                    outdata[i] *= fade

            # Apply fade-out at the end
            fade_out_start = state["total"] - fade_out_samples
            if pos + frames > fade_out_start:
                for i in range(frames):
                    sample_pos = pos + i
                    if sample_pos >= fade_out_start:
                        fade = max(0.0, (state["total"] - sample_pos) / fade_out_samples)
                        outdata[i] *= fade

            state["pos"] += written

        # Set up signal handlers
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

        try:
            print(f"\n  Playing... (Ctrl+C to stop)")
            print(f"  Duration: {self._format_duration(duration_minutes)}")
            print(f"  Volume: {int(self.volume * 100)}%")

            stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                dtype="float32",
                callback=callback,
                device=self.device,
                blocksize=2048,
            )

            with stream:
                start_time = time.time()
                while self.running and stream.active:
                    time.sleep(1)
                    elapsed = time.time() - start_time
                    if int(elapsed) % 300 == 0 and int(elapsed) > 0:
                        mins = int(elapsed / 60)
                        total = int(duration_sec / 60)
                        print(f"  {mins}/{total} min", end="\r")

        except sd.PortAudioError as e:
            print(f"\n  Audio error: {e}")
            print("  Make sure your Bluetooth speaker is connected and selected as output.")
            return False
        finally:
            self.running = False
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

        return True

    def _handle_stop(self, signum, frame):
        """Gracefully stop playback."""
        print("\n\n  Fading out...")
        self.running = False

    @staticmethod
    def _format_duration(minutes):
        if minutes >= 60:
            h = int(minutes // 60)
            m = int(minutes % 60)
            return f"{h}h {m}m" if m else f"{h}h"
        return f"{int(minutes)}m"


# ─── CLI ─────────────────────────────────────────────────────────────────────

def cmd_devices(args):
    """List available audio output devices."""
    devices = sd.query_devices()
    print("\n  Audio Output Devices")
    print("  " + "=" * 50)
    default_out = sd.default.device[1] if isinstance(sd.default.device, tuple) else sd.default.device

    for i, d in enumerate(devices):
        if d["max_output_channels"] > 0:
            marker = " <-- active" if i == default_out else ""
            print(f"  [{i}] {d['name']} ({d['max_output_channels']}ch){marker}")

    print(f"\n  Tip: Connect your Bluetooth speaker first, then it will appear here.")
    print(f"  Use --device <number> or --device \"Speaker Name\" to target it.\n")


def cmd_presets(args):
    """List all available presets."""
    print("\n  Healing Tone Presets")
    print("  " + "=" * 60)
    for key, preset in PRESETS.items():
        duration = HealingPlayer._format_duration(preset.duration_minutes)
        print(f"\n  {key}")
        print(f"    {preset.name} ({duration})")
        print(f"    {preset.description}")

    print(f"\n  Solfeggio Frequencies")
    print("  " + "-" * 40)
    for freq, desc in SOLFEGGIO_FREQUENCIES.items():
        print(f"    {freq} Hz — {desc}")

    print(f"\n  Brain Wave Bands (for binaural beats)")
    print("  " + "-" * 40)
    for band, (lo, hi, desc) in BRAIN_WAVE_BANDS.items():
        print(f"    {band}: {lo}-{hi} Hz — {desc}")
    print()


def cmd_play(args):
    """Play tones."""
    # Resolve device
    device = None
    if args.device:
        try:
            device = int(args.device)
        except ValueError:
            # Search by name
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if args.device.lower() in d["name"].lower() and d["max_output_channels"] > 0:
                    device = i
                    break
            if device is None:
                print(f"  Device '{args.device}' not found. Run 'devices' to see available outputs.")
                return

    # Build layers from preset or custom frequencies
    if args.preset:
        if args.preset not in PRESETS:
            print(f"  Unknown preset '{args.preset}'. Run 'presets' to see options.")
            return
        preset = PRESETS[args.preset]
        layers = preset.layers
        volume = args.volume if args.volume is not None else preset.volume
        duration = args.duration if args.duration else preset.duration_minutes
        print(f"\n  Preset: {preset.name}")
        print(f"  {preset.description}")
    elif args.freq:
        layers = [ToneLayer(f) for f in args.freq]
        volume = args.volume if args.volume is not None else DEFAULT_VOLUME
        duration = args.duration if args.duration else DEFAULT_DURATION_MINUTES
        freq_str = " + ".join(f"{f} Hz" for f in args.freq)
        print(f"\n  Custom: {freq_str}")
    elif args.binaural:
        if len(args.binaural) != 2:
            print("  --binaural requires exactly 2 values: base_freq beat_freq")
            return
        layers = [BinauralBeat(args.binaural[0], args.binaural[1])]
        volume = args.volume if args.volume is not None else DEFAULT_VOLUME
        duration = args.duration if args.duration else DEFAULT_DURATION_MINUTES
        print(f"\n  Binaural: {args.binaural[0]} Hz carrier, {args.binaural[1]} Hz beat")
    else:
        print("  Specify --preset, --freq, or --binaural. Run 'presets' for options.")
        return

    fade = args.fade if args.fade is not None else DEFAULT_FADE_SECONDS

    # Describe layers
    for layer in layers:
        if isinstance(layer, BinauralBeat):
            freq_l = layer.base_freq - layer.beat_freq / 2
            freq_r = layer.base_freq + layer.beat_freq / 2
            print(f"    L: {freq_l:.1f} Hz | R: {freq_r:.1f} Hz (beat: {layer.beat_freq} Hz)")
        elif isinstance(layer, ToneLayer):
            desc = SOLFEGGIO_FREQUENCIES.get(int(layer.frequency), "")
            label = f" — {desc}" if desc else ""
            print(f"    {layer.frequency} Hz{label}")

    if device is not None:
        dev_info = sd.query_devices(device)
        print(f"  Device: {dev_info['name']}")

    # Play
    player = HealingPlayer(
        layers=layers,
        volume=volume,
        fade_seconds=fade,
        device=device,
    )
    player.play(duration)
    print("\n  Session complete. Sleep well.\n")


def interactive_menu():
    """Interactive terminal menu — no flags needed."""
    CLEAR = "\033[2J\033[H"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GOLD = "\033[38;2;201;150;60m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"

    def header():
        print(CLEAR, end="")
        print(f"{GOLD}{BOLD}")
        print("  ╔══════════════════════════════════════════╗")
        print("  ║         HEALING TONES                    ║")
        print("  ║     Sleep Frequency Generator            ║")
        print("  ╚══════════════════════════════════════════╝")
        print(f"{RESET}")

    def show_devices():
        """Pick audio output device."""
        devices = sd.query_devices()
        outputs = [(i, d) for i, d in enumerate(devices) if d["max_output_channels"] > 0]
        default_out = sd.default.device[1] if isinstance(sd.default.device, tuple) else sd.default.device

        header()
        print(f"  {BOLD}Audio Output Devices{RESET}\n")
        for idx, (i, d) in enumerate(outputs):
            active = f" {GREEN}<-- active{RESET}" if i == default_out else ""
            print(f"    {GOLD}{idx + 1}{RESET}  {d['name']} ({d['max_output_channels']}ch){active}")

        print(f"\n  {DIM}Connect your Bluetooth speaker before selecting.{RESET}")
        print(f"\n    {DIM}Enter number to select, or press Enter for default:{RESET} ", end="")

        choice = input().strip()
        if not choice:
            return None  # Use default
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(outputs):
                return outputs[idx][0]
        except ValueError:
            pass
        return None

    def show_preset_menu():
        """Pick a preset or go custom."""
        header()
        print(f"  {BOLD}Choose a Program{RESET}\n")

        preset_keys = list(PRESETS.keys())
        for idx, key in enumerate(preset_keys):
            p = PRESETS[key]
            dur = HealingPlayer._format_duration(p.duration_minutes)
            print(f"    {GOLD}{idx + 1:>2}{RESET}  {p.name} {DIM}({dur}){RESET}")
            print(f"        {DIM}{p.description}{RESET}")

        print(f"\n    {GOLD}{len(preset_keys) + 1:>2}{RESET}  {CYAN}Custom frequency{RESET}")
        print(f"    {GOLD}{len(preset_keys) + 2:>2}{RESET}  {CYAN}Custom binaural beat{RESET}")
        print(f"\n    {DIM}Enter number:{RESET} ", end="")

        choice = input().strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(preset_keys):
                return ("preset", preset_keys[idx])
            elif idx == len(preset_keys):
                return ("custom", None)
            elif idx == len(preset_keys) + 1:
                return ("binaural", None)
        except ValueError:
            pass
        return None

    def get_custom_freq():
        """Prompt for custom frequencies."""
        header()
        print(f"  {BOLD}Custom Frequency{RESET}\n")
        print(f"  {DIM}Solfeggio reference:{RESET}")
        for freq, desc in SOLFEGGIO_FREQUENCIES.items():
            print(f"    {GOLD}{freq:>4}{RESET} Hz — {desc}")

        print(f"\n    {DIM}Enter frequency in Hz (space-separate for multiple):{RESET} ", end="")
        raw = input().strip()
        try:
            freqs = [float(f) for f in raw.split()]
            if freqs:
                return [ToneLayer(f) for f in freqs]
        except ValueError:
            pass
        return None

    def get_custom_binaural():
        """Prompt for binaural beat params."""
        header()
        print(f"  {BOLD}Custom Binaural Beat{RESET}\n")
        print(f"  {DIM}Brain wave reference:{RESET}")
        for band, (lo, hi, desc) in BRAIN_WAVE_BANDS.items():
            print(f"    {GOLD}{band:>6}{RESET}: {lo}-{hi} Hz — {desc}")

        print(f"\n    {DIM}Base carrier frequency (e.g. 200):{RESET} ", end="")
        try:
            base = float(input().strip())
        except ValueError:
            return None

        print(f"    {DIM}Beat frequency (e.g. 3 for delta):{RESET} ", end="")
        try:
            beat = float(input().strip())
        except ValueError:
            return None

        return [BinauralBeat(base, beat)]

    def get_volume():
        """Prompt for volume."""
        print(f"\n    {DIM}Volume 1-100% (Enter for 20%):{RESET} ", end="")
        raw = input().strip()
        if not raw:
            return DEFAULT_VOLUME
        try:
            v = float(raw)
            if v > 1:
                v = v / 100  # User entered percentage
            return max(0.01, min(1.0, v))
        except ValueError:
            return DEFAULT_VOLUME

    def get_duration(default_min):
        """Prompt for duration."""
        default_str = HealingPlayer._format_duration(default_min)
        print(f"    {DIM}Duration in minutes (Enter for {default_str}):{RESET} ", end="")
        raw = input().strip()
        if not raw:
            return default_min
        try:
            return float(raw)
        except ValueError:
            return default_min

    # ── Main interactive flow ──

    try:
        # Step 1: Device selection
        device = show_devices()
        if device is not None:
            dev_info = sd.query_devices(device)
            print(f"\n  {GREEN}Selected: {dev_info['name']}{RESET}")
            time.sleep(0.5)

        # Step 2: Preset selection
        selection = show_preset_menu()
        if selection is None:
            print(f"\n  {RED}Invalid selection.{RESET}")
            return

        mode, key = selection
        layers = None
        default_duration = DEFAULT_DURATION_MINUTES
        default_volume = DEFAULT_VOLUME

        if mode == "preset":
            preset = PRESETS[key]
            layers = preset.layers
            default_duration = preset.duration_minutes
            default_volume = preset.volume
            header()
            print(f"  {GREEN}{BOLD}{preset.name}{RESET}")
            print(f"  {DIM}{preset.description}{RESET}\n")
            for layer in layers:
                if isinstance(layer, BinauralBeat):
                    fl = layer.base_freq - layer.beat_freq / 2
                    fr = layer.base_freq + layer.beat_freq / 2
                    print(f"    L: {fl:.1f} Hz | R: {fr:.1f} Hz (beat: {layer.beat_freq} Hz)")
                elif isinstance(layer, ToneLayer):
                    desc = SOLFEGGIO_FREQUENCIES.get(int(layer.frequency), "")
                    label = f" — {desc}" if desc else ""
                    print(f"    {layer.frequency} Hz{label}")
        elif mode == "custom":
            layers = get_custom_freq()
            if not layers:
                print(f"\n  {RED}Invalid frequency.{RESET}")
                return
        elif mode == "binaural":
            layers = get_custom_binaural()
            if not layers:
                print(f"\n  {RED}Invalid input.{RESET}")
                return

        # Step 3: Volume
        volume = get_volume()

        # Step 4: Duration
        duration = get_duration(default_duration)

        # Step 5: Confirm and play
        dur_str = HealingPlayer._format_duration(duration)
        print(f"\n  {GOLD}{'─' * 42}{RESET}")
        print(f"  {BOLD}Ready to play{RESET}")
        print(f"    Volume: {int(volume * 100)}%")
        print(f"    Duration: {dur_str}")
        if device is not None:
            print(f"    Device: {sd.query_devices(device)['name']}")
        print(f"  {GOLD}{'─' * 42}{RESET}")
        print(f"\n    {DIM}Press Enter to start (or 'q' to quit):{RESET} ", end="")

        confirm = input().strip().lower()
        if confirm == "q":
            print(f"\n  {DIM}Cancelled.{RESET}\n")
            return

        # Play
        player = HealingPlayer(
            layers=layers,
            volume=volume,
            fade_seconds=DEFAULT_FADE_SECONDS,
            device=device,
        )
        player.play(duration)
        print(f"\n  {GOLD}Session complete. Sleep well.{RESET}\n")

    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {DIM}Goodbye.{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Healing Tones — therapeutic frequency generator for sleep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # devices
    sub.add_parser("devices", help="List audio output devices")

    # presets
    sub.add_parser("presets", help="List available preset programs")

    # play
    play_parser = sub.add_parser("play", help="Play healing tones")
    play_parser.add_argument("--preset", type=str, help="Use a named preset (run 'presets' to list)")
    play_parser.add_argument("--freq", type=float, nargs="+", help="Custom frequency/frequencies in Hz")
    play_parser.add_argument("--binaural", type=float, nargs=2, metavar=("BASE", "BEAT"),
                             help="Binaural beat: base frequency and beat frequency")
    play_parser.add_argument("--duration", type=float, default=None, help="Duration in minutes (default: 480 = 8hrs)")
    play_parser.add_argument("--volume", type=float, default=None, help="Volume 0.0-1.0 (default: 0.25)")
    play_parser.add_argument("--fade", type=float, default=None, help="Fade in/out seconds (default: 15)")
    play_parser.add_argument("--device", type=str, default=None, help="Audio device index or name")

    args = parser.parse_args()

    if args.command == "devices":
        cmd_devices(args)
    elif args.command == "presets":
        cmd_presets(args)
    elif args.command == "play":
        cmd_play(args)
    elif args.command is None:
        # No subcommand = launch interactive menu
        interactive_menu()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
