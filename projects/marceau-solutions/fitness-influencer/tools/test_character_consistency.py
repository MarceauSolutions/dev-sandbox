#!/usr/bin/env python3
"""
test_character_consistency.py - AI Character Consistency Testing

Generate the same character N times across different providers to test consistency.
Based on the "Facial Engineering" technique from research PDFs.

Usage:
    python test_character_consistency.py --profile character_profiles/example_profile.json --count 5
    python test_character_consistency.py --profile character_profiles/example_profile.json --count 3 --tier premium
    python test_character_consistency.py --prompt "Athletic man in gym, 30 years old" --count 5 --provider grok

Requires: Image provider API keys in .env (XAI_API_KEY, OPENAI_API_KEY, etc.)
Reuses: execution/multi_provider_image_router.py
Research: projects/archived/automated-social-media-campaign/THE COMPLETE AI INFLUENCER SYSTEM GUIDE.pdf
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

SANDBOX_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SANDBOX_ROOT))
sys.path.insert(0, str(SANDBOX_ROOT / "execution"))

try:
    from dotenv import load_dotenv
    load_dotenv(SANDBOX_ROOT / ".env")
except ImportError:
    pass


def check_prerequisites():
    """Check all dependencies and API keys are available."""
    print("\nPrerequisite Check: test_character_consistency.py")
    print("-" * 50)
    ok = True

    # Check at least one image provider key
    providers = {
        "XAI_API_KEY": "Grok Aurora (standard)",
        "OPENAI_API_KEY": "DALL-E 3 (premium)",
        "REPLICATE_API_TOKEN": "Stable Diffusion (budget)",
        "IDEOGRAM_API_KEY": "Ideogram (standard)",
    }
    found_any = False
    for key, desc in providers.items():
        val = os.environ.get(key)
        if val:
            print(f"  {key}: {'*' * 6}...{val[-4:]}  ✓  ({desc})")
            found_any = True
        else:
            print(f"  {key}: NOT SET  -  ({desc})")

    if not found_any:
        print("  ERROR: No image provider API keys found!")
        ok = False

    # Check router
    try:
        from multi_provider_image_router import MultiProviderImageRouter  # noqa: F401
        print("  multi_provider_image_router: found  ✓")
    except ImportError:
        print("  multi_provider_image_router: NOT FOUND  ⚠ (will try grok fallback)")

    print(f"\n  {'ALL GOOD — ready to generate!' if ok else 'Fix issues above before running.'}")
    return ok


def load_profile(profile_path: str) -> dict:
    """Load a character profile and build the prompt."""
    with open(profile_path, "r") as f:
        profile = json.load(f)

    # Build prompt from template
    template = profile.get("prompt_template", "")
    physical = profile.get("physical", {})
    style = profile.get("style", {})

    # Merge all fields for template substitution
    fields = {**physical, **style}
    try:
        prompt = template.format(**fields)
    except KeyError as e:
        print(f"WARNING: Template field {e} not found in profile, using raw template")
        prompt = template

    return {"profile": profile, "prompt": prompt}


def generate_batch(prompt: str, count: int, tier: str = "standard",
                   provider: str = None, output_dir: str = None):
    """Generate N images of the same character for consistency comparison."""

    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = str(Path(__file__).parent / "output" / f"consistency_{timestamp}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\nCharacter Consistency Test")
    print(f"{'='*60}")
    print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Count: {count}")
    print(f"  Tier: {tier}")
    print(f"  Provider: {provider or 'auto'}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    # Try to import the multi-provider router
    try:
        from multi_provider_image_router import MultiProviderImageRouter, ImageQualityTier
        router = MultiProviderImageRouter()
        use_router = True
    except ImportError:
        print("\nWARNING: multi_provider_image_router.py not found in execution/")
        print("Falling back to direct Grok API...")
        use_router = False

    results = []
    total_cost = 0.0

    if use_router:
        try:
            tier_enum = ImageQualityTier(tier)
            print(f"\n  Generating {count} images via router...")
            result = router.generate_images(
                prompt=prompt,
                count=count,
                tier=tier_enum,
                output_dir=output_dir
            )
            if result.get("success"):
                total_cost = result.get("cost", 0)
                # Find generated images in output dir
                for f in sorted(Path(output_dir).glob("*.png")):
                    file_size = f.stat().st_size
                    print(f"    Saved: {f} ({file_size / 1024:.1f} KB)")
                    results.append(str(f))
                if not results:
                    # Check for other image formats
                    for ext in ("*.jpg", "*.jpeg", "*.webp"):
                        for f in sorted(Path(output_dir).glob(ext)):
                            results.append(str(f))
            else:
                print(f"    FAILED: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"    ERROR: {e}")
    else:
        for i in range(count):
            output_path = os.path.join(output_dir, f"character_{i+1:02d}.png")
            print(f"\n  Generating {i+1}/{count}...")
            try:
                from grok_image_gen import GrokImageGenerator
                gen = GrokImageGenerator()
                result = gen.generate(prompt=prompt, output_path=output_path)
                if result:
                    results.append(output_path)
                    total_cost += 0.07
            except ImportError:
                print("    ERROR: Neither router nor grok_image_gen available")
                break
            except Exception as e:
                print(f"    ERROR: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Consistency Test Complete")
    print(f"  Generated: {len(results)}/{count}")
    print(f"  Est. total cost: ${total_cost:.4f}")
    print(f"  Output dir: {output_dir}")
    print(f"\nReview all images side-by-side to assess consistency.")
    print(f"Tips:")
    print(f"  - More specific prompts = better consistency")
    print(f"  - Include camera model (RED Komodo, ARRI Alexa) for realism")
    print(f"  - Same seed (if supported) improves consistency")
    print(f"  - DALL-E 3 / Ideogram tend to be more consistent than SD")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test AI character generation consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From character profile
  python test_character_consistency.py --profile character_profiles/example_profile.json --count 5

  # From raw prompt
  python test_character_consistency.py --prompt "30yo athletic man, brown hair, gym" --count 3

  # With specific tier
  python test_character_consistency.py --profile character_profiles/example_profile.json --count 5 --tier premium

Cost Estimates:
  Budget (Replicate SD):  ~$0.003/image  ($0.015 for 5)
  Standard (Grok):        ~$0.07/image   ($0.35 for 5)
  Premium (DALL-E 3):     ~$0.08/image   ($0.40 for 5)
        """
    )
    parser.add_argument("--profile", type=str, help="Path to character profile JSON")
    parser.add_argument("--prompt", type=str, help="Direct text prompt (instead of profile)")
    parser.add_argument("--count", type=int, default=5, help="Number of images to generate (default: 5)")
    parser.add_argument("--tier", type=str, default="standard",
                        choices=["budget", "standard", "premium"],
                        help="Quality tier (default: standard)")
    parser.add_argument("--provider", type=str, help="Force specific provider")
    parser.add_argument("--output", "-o", type=str, help="Output directory")
    parser.add_argument("--check", action="store_true", help="Check prerequisites (API keys, packages)")

    args = parser.parse_args()

    if args.check:
        check_prerequisites()
        return

    if args.profile:
        data = load_profile(args.profile)
        prompt = data["prompt"]
        print(f"\nLoaded profile: {data['profile'].get('name', 'unnamed')}")
        print(f"Generated prompt: {prompt}")
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        print("\nERROR: --profile or --prompt required")
        sys.exit(1)

    generate_batch(prompt, args.count, tier=args.tier,
                   provider=args.provider, output_dir=args.output)


if __name__ == "__main__":
    main()
