#!/usr/bin/env python3
"""
test_voice_minimax.py - MiniMax TTS Testing

Test MiniMax text-to-speech via fal.ai API.
Per research: "Most realistic TTS, $5/month for 120 min"

Usage:
    python test_voice_minimax.py --text "Hello, welcome to the workout"
    python test_voice_minimax.py --text "Let's get started" --voice "male_1" --output output/test.mp3
    python test_voice_minimax.py --list-voices
    python test_voice_minimax.py --cost --text "Some long text to estimate"

Requires: FAL_API_KEY in .env
Research: projects/archived/automated-social-media-campaign/How_to_Create_Realistic_AI_Voices_That_Don't_Sound_Like_Trash_1.pdf
"""

import argparse
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Load .env from dev-sandbox root
SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


# MiniMax via fal.ai endpoint
FAL_API_BASE = "https://queue.fal.run"
MINIMAX_MODEL = "fal-ai/minimax/speech-02-hd"

# Cost estimate: ~$0.04 per minute of audio
COST_PER_MINUTE = 0.04
AVG_CHARS_PER_MINUTE = 800


def get_api_key():
    key = os.environ.get("FAL_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if not key:
        print("ERROR: FAL_API_KEY or MINIMAX_API_KEY not found in .env")
        print(f"Add to: {SANDBOX_ROOT / '.env'}")
        sys.exit(1)
    return key


def check_prerequisites():
    """Check all dependencies and API keys are available."""
    print("\nPrerequisite Check: test_voice_minimax.py")
    print("-" * 50)
    ok = True

    key = os.environ.get("FAL_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if key:
        print(f"  FAL_API_KEY: {'*' * 6}...{key[-4:]}  ✓")
    else:
        print("  FAL_API_KEY: NOT SET  ✗")
        ok = False

    try:
        import requests  # noqa: F401
        print("  requests: installed  ✓")
    except ImportError:
        print("  requests: NOT INSTALLED  ✗")
        ok = False

    print(f"\n  {'ALL GOOD — ready to generate!' if ok else 'Fix issues above before running.'}")
    return ok


def list_voices():
    """List available MiniMax voice options."""
    voices = [
        {"id": "male-qn-qingse", "desc": "Young male, clear and bright"},
        {"id": "male-qn-jingying", "desc": "Young male, refined"},
        {"id": "male-qn-badao", "desc": "Young male, bold/domineering"},
        {"id": "male-qn-daxuesheng", "desc": "Male, college student"},
        {"id": "female-shaonv", "desc": "Young female, youthful"},
        {"id": "female-yujie", "desc": "Female, mature/elegant"},
        {"id": "female-chengshu", "desc": "Female, mature"},
        {"id": "female-tianmei", "desc": "Female, sweet"},
        {"id": "presenter_male", "desc": "Male presenter/narrator"},
        {"id": "presenter_female", "desc": "Female presenter/narrator"},
        {"id": "audiobook_male_1", "desc": "Male audiobook narrator"},
        {"id": "audiobook_female_1", "desc": "Female audiobook narrator"},
    ]
    print("\nAvailable MiniMax Voices:")
    print("-" * 60)
    for v in voices:
        print(f"  {v['id']:30s} {v['desc']}")
    print(f"\nNote: Voice availability may vary. Check fal.ai docs for latest list.")
    return voices


def estimate_cost(text: str):
    """Estimate generation cost based on text length."""
    chars = len(text)
    minutes = chars / AVG_CHARS_PER_MINUTE
    cost = minutes * COST_PER_MINUTE
    print(f"\nCost Estimate:")
    print(f"  Characters: {chars}")
    print(f"  Est. duration: {minutes:.1f} min")
    print(f"  Est. cost: ${cost:.4f}")
    return cost


def generate_speech(text: str, voice: str = "presenter_male", output_path: str = None):
    """Generate speech using MiniMax via fal.ai."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests library required. Run: pip install requests")
        sys.exit(1)

    api_key = get_api_key()

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"minimax_{voice}_{timestamp}.mp3")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating speech with MiniMax...")
    print(f"  Voice: {voice}")
    print(f"  Text: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"  Output: {output_path}")

    # Submit to fal.ai queue
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice_id": voice,
    }

    # Submit request
    response = requests.post(
        f"{FAL_API_BASE}/{MINIMAX_MODEL}",
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        # fal.ai returns audio URL or base64
        if "audio_url" in result:
            audio_url = result["audio_url"]
            audio_data = requests.get(audio_url, timeout=30).content
        elif "audio" in result:
            import base64
            audio_data = base64.b64decode(result["audio"])
        else:
            # Try to get the output directly
            audio_data = response.content

        with open(output_path, "wb") as f:
            f.write(audio_data)

        file_size = os.path.getsize(output_path)
        print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
        estimate_cost(text)
        return output_path

    elif response.status_code == 422:
        # Queue-based: need to poll
        result = response.json()
        request_id = result.get("request_id")
        if request_id:
            return _poll_fal_result(request_id, api_key, output_path, text)

    print(f"\nERROR: API returned {response.status_code}")
    print(f"  Response: {response.text[:500]}")
    return None


def _poll_fal_result(request_id: str, api_key: str, output_path: str, text: str):
    """Poll fal.ai for queued result."""
    import requests

    headers = {"Authorization": f"Key {api_key}"}
    status_url = f"{FAL_API_BASE}/{MINIMAX_MODEL}/requests/{request_id}/status"
    result_url = f"{FAL_API_BASE}/{MINIMAX_MODEL}/requests/{request_id}"

    print("  Queued, polling for result...")
    for i in range(60):  # Max 2 minutes
        time.sleep(2)
        resp = requests.get(status_url, headers=headers, timeout=30)
        if resp.status_code == 200:
            status = resp.json()
            if status.get("status") == "COMPLETED":
                # Fetch result
                result_resp = requests.get(result_url, headers=headers, timeout=30)
                if result_resp.status_code == 200:
                    result = result_resp.json()
                    if "audio_url" in result:
                        audio_data = requests.get(result["audio_url"], timeout=30).content
                        with open(output_path, "wb") as f:
                            f.write(audio_data)
                        file_size = os.path.getsize(output_path)
                        print(f"\n  Saved: {output_path} ({file_size / 1024:.1f} KB)")
                        estimate_cost(text)
                        return output_path
            elif status.get("status") == "FAILED":
                print(f"\nERROR: Generation failed: {status}")
                return None
            print(f"  Status: {status.get('status', 'unknown')}...", end="\r")

    print("\nERROR: Timed out waiting for result")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Test MiniMax TTS via fal.ai",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_voice_minimax.py --text "Welcome to the workout"
  python test_voice_minimax.py --text "Let's go!" --voice presenter_male
  python test_voice_minimax.py --list-voices
  python test_voice_minimax.py --cost --text "Long script here..."
        """
    )
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--voice", type=str, default="presenter_male", help="Voice ID (default: presenter_male)")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--check", action="store_true", help="Check prerequisites (API keys, packages)")
    parser.add_argument("--cost", action="store_true", help="Estimate cost without generating")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if args.check:
        check_prerequisites()
        return

    if not args.text:
        parser.print_help()
        print("\nERROR: --text is required (or use --list-voices)")
        sys.exit(1)

    if args.cost:
        estimate_cost(args.text)
        return

    generate_speech(args.text, voice=args.voice, output_path=args.output)


if __name__ == "__main__":
    main()
