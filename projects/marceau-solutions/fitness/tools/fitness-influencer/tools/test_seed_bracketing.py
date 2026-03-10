#!/usr/bin/env python3
"""
test_seed_bracketing.py - Seed Bracketing Technique

Systematically test seeds 1000-1010 for the same prompt to find
reproducible, high-quality generations.

Per research: "Success rate improvement from 15% to 70%+"
Technique: Generate same prompt with seeds 1000-1010, pick best,
build a seed library for different content types.

Usage:
    python test_seed_bracketing.py --prompt "Athletic man in gym" --seeds 1000-1010
    python test_seed_bracketing.py --prompt "Fitness coach speaking" --seeds 1000-1005 --provider grok
    python test_seed_bracketing.py --prompt "Workout scene" --seeds 1000-1020 --tier budget

Requires: Image provider API keys in .env
Reuses: execution/multi_provider_image_router.py, execution/grok_image_gen.py
Research: projects/archived/automated-social-media-campaign/How I Cut AI Video Costs By 60_...pdf
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
    print("\nPrerequisite Check: test_seed_bracketing.py")
    print("-" * 50)
    ok = True

    providers = {
        "XAI_API_KEY": "Grok Aurora (standard)",
        "OPENAI_API_KEY": "DALL-E 3 (premium)",
        "REPLICATE_API_TOKEN": "Stable Diffusion (budget)",
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

    try:
        from multi_provider_image_router import MultiProviderImageRouter  # noqa: F401
        print("  multi_provider_image_router: found  ✓")
    except ImportError:
        print("  multi_provider_image_router: NOT FOUND  ⚠ (will try grok fallback)")

    print(f"\n  {'ALL GOOD — ready to bracket!' if ok else 'Fix issues above before running.'}")
    return ok


def parse_seed_range(seed_str: str) -> list:
    """Parse seed range like '1000-1010' into list of ints."""
    if "-" in seed_str:
        parts = seed_str.split("-")
        start, end = int(parts[0]), int(parts[1])
        return list(range(start, end + 1))
    else:
        return [int(s.strip()) for s in seed_str.split(",")]


def run_seed_bracket(prompt: str, seeds: list, tier: str = "standard",
                     provider: str = None, output_dir: str = None):
    """Generate images with each seed and save for comparison."""

    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = str(Path(__file__).parent / "output" / f"seeds_{timestamp}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\nSeed Bracketing Test")
    print(f"{'='*60}")
    print(f"  Prompt: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
    print(f"  Seeds: {seeds[0]}-{seeds[-1]} ({len(seeds)} total)")
    print(f"  Tier: {tier}")
    print(f"  Provider: {provider or 'auto'}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}")

    # Try to use multi-provider router
    router = None
    try:
        from multi_provider_image_router import MultiProviderImageRouter, ImageQualityTier
        router = MultiProviderImageRouter()
        tier_enum = ImageQualityTier(tier)
    except ImportError:
        print("WARNING: Router not found, trying direct Grok API...")

    # Try direct Grok as fallback
    grok_gen = None
    if not router:
        try:
            from grok_image_gen import GrokImageGenerator
            grok_gen = GrokImageGenerator()
        except ImportError:
            print("ERROR: Neither router nor grok_image_gen available")
            sys.exit(1)

    results = []
    total_cost = 0.0

    for seed in seeds:
        output_path = os.path.join(output_dir, f"seed_{seed:05d}.png")
        print(f"\n  Seed {seed}...", end=" ")

        try:
            if router:
                seed_dir = os.path.join(output_dir, f"_tmp_seed_{seed}")
                Path(seed_dir).mkdir(exist_ok=True)
                result = router.generate_images(
                    prompt=f"{prompt} --seed {seed}",
                    count=1,
                    tier=tier_enum,
                    output_dir=seed_dir
                )
                # Move generated file to expected path
                if result.get("success"):
                    generated = list(Path(seed_dir).glob("*.*"))
                    if generated:
                        import shutil
                        shutil.move(str(generated[0]), output_path)
                    shutil.rmtree(seed_dir, ignore_errors=True)
            elif grok_gen:
                result = grok_gen.generate(
                    prompt=prompt,
                    output_path=output_path,
                    seed=seed
                )
            else:
                result = None

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"OK ({file_size / 1024:.0f} KB)")
                results.append({"seed": seed, "path": output_path, "size": file_size})
                total_cost += 0.07 if tier == "standard" else (0.003 if tier == "budget" else 0.08)
            else:
                print(f"FAILED")

        except Exception as e:
            print(f"ERROR: {e}")

    # Save results manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    manifest = {
        "prompt": prompt,
        "seeds": seeds,
        "tier": tier,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "total_cost": total_cost
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print(f"Seed Bracketing Complete")
    print(f"  Generated: {len(results)}/{len(seeds)}")
    print(f"  Est. total cost: ${total_cost:.4f}")
    print(f"  Output: {output_dir}")
    print(f"  Manifest: {manifest_path}")
    print(f"\nNext Steps:")
    print(f"  1. Review images side-by-side")
    print(f"  2. Note which seeds produce best results")
    print(f"  3. Save good seeds to your character profile")
    print(f"  4. Reuse winning seeds for future generations")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Seed bracketing technique for consistent AI image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard bracket (11 seeds)
  python test_seed_bracketing.py --prompt "Athletic man in gym" --seeds 1000-1010

  # Narrow bracket (6 seeds, cheaper)
  python test_seed_bracketing.py --prompt "Fitness coach" --seeds 1000-1005

  # Budget tier for bulk testing
  python test_seed_bracketing.py --prompt "Workout scene" --seeds 1000-1020 --tier budget

  # Specific seeds
  python test_seed_bracketing.py --prompt "Gym scene" --seeds "1003,1007,1009"

Technique (from research):
  - Test seeds 1000-1010 systematically
  - Each seed produces a different but reproducible result
  - Pick the best seed, reuse it for consistency
  - Build a seed library for different content types
  - Can improve success rate from 15% to 70%+

Cost per bracket:
  Budget (11 seeds):   ~$0.033
  Standard (11 seeds): ~$0.77
  Premium (11 seeds):  ~$0.88
        """
    )
    parser.add_argument("--prompt", "-p", type=str, help="Image generation prompt")
    parser.add_argument("--seeds", "-s", type=str, default="1000-1010",
                        help="Seed range (e.g., '1000-1010') or comma-separated (e.g., '1003,1007')")
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

    if not args.prompt:
        parser.print_help()
        print("\nERROR: --prompt required")
        sys.exit(1)

    seeds = parse_seed_range(args.seeds)
    run_seed_bracket(args.prompt, seeds, tier=args.tier,
                     provider=args.provider, output_dir=args.output)


if __name__ == "__main__":
    main()
