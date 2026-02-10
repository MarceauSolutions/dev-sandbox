#!/usr/bin/env python3
"""
test_voice_elevenlabs.py - ElevenLabs Voice Testing

Test ElevenLabs for voice cloning, text-to-speech, and consistency testing.

Usage:
    python test_voice_elevenlabs.py --list-voices
    python test_voice_elevenlabs.py --text "Hello world" --voice-id "21m00Tcm4TlvDq8ikWAM"
    python test_voice_elevenlabs.py --clone --sample voice.mp3 --name "FitnessCoach"
    python test_voice_elevenlabs.py --consistency --text "Test phrase" --voice-id "xxx" --count 5
    python test_voice_elevenlabs.py --cost --text "Some long script"

Requires: ELEVENLABS_API_KEY in .env
Research: projects/archived/automated-social-media-campaign/how to have consistent voice in video.pdf
"""

import argparse
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Cost: ~$0.30 per 1000 characters (Starter plan)
COST_PER_1000_CHARS = 0.30


def get_api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("ERROR: ELEVENLABS_API_KEY not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        print("Get key at: https://elevenlabs.io/")
        sys.exit(1)
    return key


def check_prerequisites():
    """Check all dependencies and API keys are available."""
    print("\nPrerequisite Check: test_voice_elevenlabs.py")
    print("-" * 50)
    ok = True

    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        print(f"  ELEVENLABS_API_KEY: {'*' * 6}...{key[-4:]}  ✓")
    else:
        print("  ELEVENLABS_API_KEY: NOT SET  ✗")
        ok = False

    try:
        import requests  # noqa: F401
        print("  requests: installed  ✓")
    except ImportError:
        print("  requests: NOT INSTALLED  ✗")
        ok = False

    print(f"\n  {'ALL GOOD — ready to generate!' if ok else 'Fix issues above before running.'}")
    return ok


def _headers():
    return {
        "xi-api-key": get_api_key(),
        "Content-Type": "application/json"
    }


def list_voices():
    """List all available ElevenLabs voices."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    response = requests.get(f"{ELEVENLABS_API_BASE}/voices", headers=_headers(), timeout=30)

    if response.status_code == 200:
        data = response.json()
        voices = data.get("voices", [])
        print(f"\nAvailable ElevenLabs Voices ({len(voices)} total):")
        print("-" * 80)
        for v in voices:
            name = v.get("name", "Unknown")
            vid = v.get("voice_id", "")
            category = v.get("category", "")
            labels = v.get("labels", {})
            accent = labels.get("accent", "")
            gender = labels.get("gender", "")
            desc = f"{gender}, {accent}" if accent else gender
            print(f"  {name:25s} ID: {vid[:12]}...  [{category}] {desc}")
        print(f"\nTotal: {len(voices)} voices")
    else:
        print(f"ERROR: {response.status_code} - {response.text[:300]}")


def estimate_cost(text: str):
    """Estimate generation cost."""
    chars = len(text)
    cost = (chars / 1000) * COST_PER_1000_CHARS
    print(f"\nCost Estimate:")
    print(f"  Characters: {chars}")
    print(f"  Est. cost: ${cost:.4f}")
    print(f"  Rate: ${COST_PER_1000_CHARS}/1000 chars")
    return cost


def generate_speech(text: str, voice_id: str, output_path: str = None,
                    model: str = "eleven_multilingual_v2", stability: float = 0.5,
                    similarity_boost: float = 0.75):
    """Generate speech using ElevenLabs."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"elevenlabs_{timestamp}.mp3")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating speech with ElevenLabs...")
    print(f"  Voice ID: {voice_id}")
    print(f"  Model: {model}")
    print(f"  Text: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"  Stability: {stability}, Similarity: {similarity_boost}")

    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost
        }
    }

    response = requests.post(
        f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": get_api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        },
        json=payload,
        timeout=60
    )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        file_size = os.path.getsize(output_path)
        print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
        estimate_cost(text)
        return output_path
    else:
        print(f"\nERROR: {response.status_code}")
        try:
            error = response.json()
            print(f"  {json.dumps(error, indent=2)[:500]}")
        except Exception:
            print(f"  {response.text[:500]}")
    return None


def clone_voice(sample_path: str, name: str, description: str = ""):
    """Clone a voice from an audio sample."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    if not os.path.exists(sample_path):
        print(f"ERROR: Sample not found: {sample_path}")
        sys.exit(1)

    print(f"\nCloning voice from: {sample_path}")
    print(f"  Name: {name}")

    with open(sample_path, "rb") as f:
        files = {"files": (os.path.basename(sample_path), f, "audio/mpeg")}
        data = {
            "name": name,
            "description": description or f"Cloned voice: {name}"
        }
        response = requests.post(
            f"{ELEVENLABS_API_BASE}/voices/add",
            headers={"xi-api-key": get_api_key()},
            files=files,
            data=data,
            timeout=120
        )

    if response.status_code == 200:
        result = response.json()
        print(f"\n  Voice cloned!")
        print(f"  Voice ID: {result.get('voice_id', 'N/A')}")
        print(f"  Use with: --voice-id {result.get('voice_id', '')}")
        return result
    else:
        print(f"\nERROR: {response.status_code}")
        print(f"  {response.text[:500]}")
    return None


def test_consistency(text: str, voice_id: str, count: int = 5,
                     stability: float = 0.5, similarity_boost: float = 0.75):
    """Generate same text N times to test voice consistency."""
    print(f"\nConsistency Test: Generating {count} versions of same text")
    print(f"  Voice ID: {voice_id}")
    print(f"  Stability: {stability}, Similarity: {similarity_boost}")
    print(f"  Text: {text[:60]}{'...' if len(text) > 60 else ''}")
    print("-" * 60)

    output_dir = Path(__file__).parent / "output" / f"consistency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i in range(count):
        output_path = str(output_dir / f"version_{i+1:02d}.mp3")
        print(f"\n  Generating version {i+1}/{count}...")
        result = generate_speech(
            text, voice_id, output_path,
            stability=stability, similarity_boost=similarity_boost
        )
        if result:
            results.append(result)
        time.sleep(1)  # Brief pause between requests

    print(f"\n{'='*60}")
    print(f"Consistency Test Complete")
    print(f"  Generated: {len(results)}/{count}")
    print(f"  Output dir: {output_dir}")
    print(f"  Total est. cost: ${(len(text) / 1000) * COST_PER_1000_CHARS * count:.4f}")
    print(f"\nListen to all versions and compare for consistency.")
    print(f"Tip: Higher stability = more consistent but less expressive")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test ElevenLabs voice generation and cloning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_voice_elevenlabs.py --list-voices
  python test_voice_elevenlabs.py --text "Welcome!" --voice-id 21m00Tcm4TlvDq8ikWAM
  python test_voice_elevenlabs.py --clone --sample my_voice.mp3 --name "FitnessCoach"
  python test_voice_elevenlabs.py --consistency --text "Test this" --voice-id xxx --count 5
  python test_voice_elevenlabs.py --cost --text "Long script here..."

Voice Settings:
  --stability 0.0-1.0    Higher = more consistent, lower = more expressive
  --similarity 0.0-1.0   Higher = closer to original voice
        """
    )
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--voice-id", type=str, help="Voice ID to use")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--model", type=str, default="eleven_multilingual_v2",
                        help="Model ID (default: eleven_multilingual_v2)")
    parser.add_argument("--stability", type=float, default=0.5, help="Voice stability 0-1 (default: 0.5)")
    parser.add_argument("--similarity", type=float, default=0.75, help="Similarity boost 0-1 (default: 0.75)")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--check", action="store_true", help="Check prerequisites (API keys, packages)")
    parser.add_argument("--cost", action="store_true", help="Estimate cost")
    parser.add_argument("--clone", action="store_true", help="Clone voice from sample")
    parser.add_argument("--sample", type=str, help="Audio sample for cloning")
    parser.add_argument("--name", type=str, help="Name for cloned voice")
    parser.add_argument("--consistency", action="store_true", help="Run consistency test")
    parser.add_argument("--count", type=int, default=5, help="Number of generations for consistency test")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if args.check:
        check_prerequisites()
        return

    if args.clone:
        if not args.sample or not args.name:
            print("ERROR: --clone requires --sample and --name")
            sys.exit(1)
        clone_voice(args.sample, args.name)
        return

    if args.cost and args.text:
        estimate_cost(args.text)
        return

    if not args.text:
        parser.print_help()
        print("\nERROR: --text required (or use --list-voices, --clone)")
        sys.exit(1)

    if not args.voice_id:
        print("ERROR: --voice-id required. Use --list-voices to find one.")
        sys.exit(1)

    if args.consistency:
        test_consistency(args.text, args.voice_id, count=args.count,
                         stability=args.stability, similarity_boost=args.similarity)
        return

    generate_speech(args.text, args.voice_id, output_path=args.output,
                    model=args.model, stability=args.stability,
                    similarity_boost=args.similarity)


if __name__ == "__main__":
    main()
