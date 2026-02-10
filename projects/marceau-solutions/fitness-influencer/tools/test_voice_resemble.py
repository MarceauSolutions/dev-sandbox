#!/usr/bin/env python3
"""
test_voice_resemble.py - Resemble AI Voice Testing

Test Resemble AI for voice enhancement and voice changing.
Per research: "Best for voice enhancement/changing (Chatterbox models)"

Usage:
    python test_voice_resemble.py --text "Hello world" --voice "default"
    python test_voice_resemble.py --enhance --input audio.mp3 --output output/enhanced.mp3
    python test_voice_resemble.py --list-voices
    python test_voice_resemble.py --clone --sample voice_sample.mp3 --name "FitnessCoach"

Requires: RESEMBLE_API_KEY in .env
Research: projects/archived/automated-social-media-campaign/How_to_Create_Realistic_AI_Voices_That_Don't_Sound_Like_Trash_1.pdf
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


RESEMBLE_API_BASE = "https://app.resemble.ai/api/v2"

# Cost: ~$0.006 per second of audio
COST_PER_SECOND = 0.006
AVG_CHARS_PER_SECOND = 15


def get_api_key():
    key = os.environ.get("RESEMBLE_API_KEY")
    if not key:
        print("ERROR: RESEMBLE_API_KEY not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        print("Get key at: https://app.resemble.ai/")
        sys.exit(1)
    return key


def check_prerequisites():
    """Check all dependencies and API keys are available."""
    print("\nPrerequisite Check: test_voice_resemble.py")
    print("-" * 50)
    ok = True

    key = os.environ.get("RESEMBLE_API_KEY")
    if key:
        print(f"  RESEMBLE_API_KEY: {'*' * 6}...{key[-4:]}  ✓")
    else:
        print("  RESEMBLE_API_KEY: NOT SET  ✗")
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
        "Authorization": f"Token token={get_api_key()}",
        "Content-Type": "application/json"
    }


def list_voices():
    """List available Resemble AI voices."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required. Run: pip install requests")
        sys.exit(1)

    response = requests.get(f"{RESEMBLE_API_BASE}/voices", headers=_headers(), timeout=30)

    if response.status_code == 200:
        data = response.json()
        voices = data.get("items", data) if isinstance(data, dict) else data
        print("\nAvailable Resemble AI Voices:")
        print("-" * 60)
        if isinstance(voices, list):
            for v in voices:
                name = v.get("name", "Unknown")
                uuid = v.get("uuid", "N/A")
                status = v.get("status", "unknown")
                print(f"  {name:30s} ID: {uuid}  Status: {status}")
        else:
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"ERROR: {response.status_code} - {response.text[:300]}")


def estimate_cost(text: str):
    """Estimate generation cost."""
    chars = len(text)
    seconds = chars / AVG_CHARS_PER_SECOND
    cost = seconds * COST_PER_SECOND
    print(f"\nCost Estimate:")
    print(f"  Characters: {chars}")
    print(f"  Est. duration: {seconds:.1f}s")
    print(f"  Est. cost: ${cost:.4f}")
    return cost


def generate_speech(text: str, voice_uuid: str = None, output_path: str = None):
    """Generate speech using Resemble AI."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required. Run: pip install requests")
        sys.exit(1)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"resemble_{timestamp}.mp3")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating speech with Resemble AI...")
    print(f"  Voice UUID: {voice_uuid or 'default'}")
    print(f"  Text: {text[:80]}{'...' if len(text) > 80 else ''}")

    # Create clip
    payload = {
        "body": text,
        "voice_uuid": voice_uuid,
        "output_format": "mp3"
    }

    # If no voice UUID, try to get first available voice
    if not voice_uuid:
        resp = requests.get(f"{RESEMBLE_API_BASE}/voices", headers=_headers(), timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            voices = data.get("items", []) if isinstance(data, dict) else data
            if voices and isinstance(voices, list):
                voice_uuid = voices[0].get("uuid")
                payload["voice_uuid"] = voice_uuid
                print(f"  Using first voice: {voices[0].get('name', voice_uuid)}")
            else:
                print("WARNING: No voices found. You may need to create one first.")

    # Synthesize
    response = requests.post(
        f"{RESEMBLE_API_BASE}/clips",
        headers=_headers(),
        json=payload,
        timeout=60
    )

    if response.status_code in (200, 201):
        result = response.json()
        item = result.get("item", result)

        # Check if audio URL is available
        audio_url = item.get("audio_src") or item.get("raw_audio_src")
        if audio_url:
            audio_data = requests.get(audio_url, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(audio_data)
            file_size = os.path.getsize(output_path)
            print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
            estimate_cost(text)
            return output_path
        else:
            # May need to poll for completion
            clip_uuid = item.get("uuid")
            if clip_uuid:
                return _poll_clip(clip_uuid, output_path, text)
            print(f"  Response (no audio URL): {json.dumps(item, indent=2)[:500]}")
    else:
        print(f"\nERROR: {response.status_code}")
        print(f"  {response.text[:500]}")
    return None


def _poll_clip(clip_uuid: str, output_path: str, text: str):
    """Poll for clip completion."""
    import requests

    print("  Processing, polling...")
    for i in range(30):
        time.sleep(2)
        resp = requests.get(
            f"{RESEMBLE_API_BASE}/clips/{clip_uuid}",
            headers=_headers(), timeout=30
        )
        if resp.status_code == 200:
            item = resp.json().get("item", resp.json())
            audio_url = item.get("audio_src") or item.get("raw_audio_src")
            if audio_url:
                audio_data = requests.get(audio_url, timeout=30).content
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                file_size = os.path.getsize(output_path)
                print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
                estimate_cost(text)
                return output_path
        print(f"  Waiting... ({(i+1)*2}s)", end="\r")

    print("\nERROR: Timed out waiting for clip")
    return None


def clone_voice(sample_path: str, name: str):
    """Clone a voice from an audio sample."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    if not os.path.exists(sample_path):
        print(f"ERROR: Sample file not found: {sample_path}")
        sys.exit(1)

    print(f"\nCloning voice from: {sample_path}")
    print(f"  Name: {name}")

    headers = {"Authorization": f"Token token={get_api_key()}"}

    with open(sample_path, "rb") as f:
        files = {"file": (os.path.basename(sample_path), f, "audio/mpeg")}
        data = {"name": name}
        response = requests.post(
            f"{RESEMBLE_API_BASE}/voices",
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    if response.status_code in (200, 201):
        result = response.json()
        item = result.get("item", result)
        print(f"\n  Voice created!")
        print(f"  UUID: {item.get('uuid', 'N/A')}")
        print(f"  Name: {item.get('name', 'N/A')}")
        print(f"  Status: {item.get('status', 'N/A')}")
        return item
    else:
        print(f"\nERROR: {response.status_code}")
        print(f"  {response.text[:500]}")
    return None


def enhance_audio(input_path: str, output_path: str = None):
    """Enhance audio quality using Resemble AI."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests required")
        sys.exit(1)

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    if not output_path:
        stem = Path(input_path).stem
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{stem}_enhanced.mp3")

    print(f"\nEnhancing audio: {input_path}")
    print(f"  Output: {output_path}")

    headers = {"Authorization": f"Token token={get_api_key()}"}

    with open(input_path, "rb") as f:
        files = {"file": (os.path.basename(input_path), f, "audio/mpeg")}
        response = requests.post(
            f"{RESEMBLE_API_BASE}/enhance",
            headers=headers,
            files=files,
            timeout=120
        )

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        if "audio" in content_type or "octet-stream" in content_type:
            with open(output_path, "wb") as f:
                f.write(response.content)
            file_size = os.path.getsize(output_path)
            print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
            return output_path
        else:
            result = response.json()
            audio_url = result.get("audio_src") or result.get("url")
            if audio_url:
                audio_data = requests.get(audio_url, timeout=30).content
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                print(f"\n  Saved: {output_path}")
                return output_path
            print(f"  Response: {json.dumps(result, indent=2)[:500]}")
    else:
        print(f"\nERROR: {response.status_code}")
        print(f"  {response.text[:500]}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Test Resemble AI voice generation and enhancement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_voice_resemble.py --list-voices
  python test_voice_resemble.py --text "Welcome to the workout"
  python test_voice_resemble.py --text "Let's go!" --voice-uuid abc123
  python test_voice_resemble.py --clone --sample voice.mp3 --name "FitnessCoach"
  python test_voice_resemble.py --enhance --input raw_audio.mp3
  python test_voice_resemble.py --cost --text "Long script..."
        """
    )
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--voice-uuid", type=str, help="Voice UUID to use")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--check", action="store_true", help="Check prerequisites (API keys, packages)")
    parser.add_argument("--cost", action="store_true", help="Estimate cost")
    parser.add_argument("--clone", action="store_true", help="Clone a voice from sample")
    parser.add_argument("--sample", type=str, help="Audio sample for cloning")
    parser.add_argument("--name", type=str, help="Name for cloned voice")
    parser.add_argument("--enhance", action="store_true", help="Enhance audio quality")
    parser.add_argument("--input", "-i", type=str, help="Input audio file (for enhance)")

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

    if args.enhance:
        if not args.input:
            print("ERROR: --enhance requires --input")
            sys.exit(1)
        enhance_audio(args.input, args.output)
        return

    if args.cost and args.text:
        estimate_cost(args.text)
        return

    if not args.text:
        parser.print_help()
        print("\nERROR: --text required (or use --list-voices, --clone, --enhance)")
        sys.exit(1)

    generate_speech(args.text, voice_uuid=args.voice_uuid, output_path=args.output)


if __name__ == "__main__":
    main()
