#!/usr/bin/env python3
"""
DumbPhone Lock — Content Pipeline

Handles three levels of autonomy per platform:
  Level 3 (fully auto)   → Twitter/X  (post thread automatically)
  Level 2 (browser-assist) → Reddit, Hacker News (open submit page + show copy)
  Level 1 (copy + guide)   → Instagram, TikTok (show copy + visual instructions)

Run standalone:
    python launch/content_pipeline.py post twitter
    python launch/content_pipeline.py post reddit_nosurf
    python launch/content_pipeline.py generate          # generate images for all platforms
    python launch/content_pipeline.py show <key>        # print copy for a platform
"""

import os
import re
import sys
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ROOT = PROJECT_DIR.parents[3]

sys.path.insert(0, str(ROOT / "projects" / "shared" / "social-media-automation" / "src"))
sys.path.insert(0, str(ROOT / "execution"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

BOLD   = "\033[1m"
DIM    = "\033[2m"
GOLD   = "\033[38;2;201;150;60m"
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

COPY_FILE   = PROJECT_DIR / "marketing" / "dumbphone-launch-copy.md"
ASSETS_DIR  = SCRIPT_DIR / "assets"
STATE_FILE  = SCRIPT_DIR / "launch_state.json"

LANDING_URL = "https://marceausolutions.com/dumbphone"

# ─── Platform Registry ────────────────────────────────────────────────────────

PLATFORMS = {
    "reddit_nosurf": {
        "label":       "Reddit r/nosurf",
        "type":        "reddit",
        "subreddit":   "nosurf",
        "section":     "Reddit Post 1: r/nosurf",
        "autonomy":    2,
        "image_style": "dark_minimalist",
    },
    "twitter": {
        "label":       "Twitter/X Thread",
        "type":        "twitter",
        "section":     "Twitter/X Thread",
        "autonomy":    3,
        "image_style": "stat_graphic",
    },
    "reddit_productivity": {
        "label":       "Reddit r/productivity",
        "type":        "reddit",
        "subreddit":   "productivity",
        "section":     "Reddit Post 3: r/productivity",
        "autonomy":    2,
        "image_style": "focus_timer",
    },
    "instagram": {
        "label":       "Instagram Reel",
        "type":        "instagram",
        "section":     "Instagram Reel Caption",
        "autonomy":    1,
        "image_style": "lifestyle_vertical",
    },
    "reddit_dm": {
        "label":       "Reddit r/digitalminimalism",
        "type":        "reddit",
        "subreddit":   "digitalminimalism",
        "section":     "Reddit Post 2: r/digitalminimalism",
        "autonomy":    2,
        "image_style": "dark_minimalist",
    },
    "tiktok": {
        "label":       "TikTok",
        "type":        "tiktok",
        "section":     "TikTok Caption",
        "autonomy":    1,
        "image_style": "lifestyle_vertical",
    },
    "reddit_dumbphones": {
        "label":       "Reddit r/dumbphones",
        "type":        "reddit",
        "subreddit":   "dumbphones",
        "section":     "Reddit Post 4: r/dumbphones",
        "autonomy":    2,
        "image_style": "comparison_graphic",
    },
    "hackernews": {
        "label":       "Hacker News Show HN",
        "type":        "hackernews",
        "section":     "Hacker News — Show HN",
        "autonomy":    2,
        "image_style": None,
    },
    "reddit_getdisciplined": {
        "label":       "Reddit r/getdisciplined",
        "type":        "reddit",
        "subreddit":   "getdisciplined",
        "section":     "Reddit Post 5: r/getdisciplined",
        "autonomy":    2,
        "image_style": "focus_timer",
    },
    "reddit_comments": {
        "label":       "Reddit comments (hunt)",
        "type":        "reddit_comments",
        "section":     "Reddit Comment Templates",
        "autonomy":    2,
        "image_style": None,
    },
}

IMAGE_PROMPTS = {
    "dark_minimalist": (
        "Ultra-clean product mockup. iPhone in dark charcoal background. "
        "Screen shows only 4 minimal icons. Gold text overlay: 'DumbPhone Lock'. "
        "Premium tech aesthetic, no clutter. Dramatic lighting. 16:9."
    ),
    "stat_graphic": (
        "Bold typographic poster. Dark charcoal #333333 background. "
        "Large gold #C9963C text: '4.5 HOURS'. Subtext in white: "
        "'Your phone steals this much of your life every day.'. "
        "Bottom: 'DumbPhone Lock — Take it back.' Minimalist, high contrast. 16:9."
    ),
    "focus_timer": (
        "Split-image graphic. Left: phone lit up with 50 apps, red glow, chaos. "
        "Right: minimal dark phone with clock and 4 icons, gold glow, calm. "
        "Text overlay: '23 minutes to refocus after each distraction.' "
        "Dark background with gold accents. 16:9."
    ),
    "lifestyle_vertical": (
        "Vertical 9:16 lifestyle shot. Person at desk, phone face-down, focused. "
        "Warm minimal room. Small gold phone icon in corner: 'DumbPhone Lock'. "
        "Cinematic, aspirational, calm productivity aesthetic."
    ),
    "comparison_graphic": (
        "Side-by-side comparison card. Dark background. "
        "Left box: 'Light Phone — $299 + separate plan'. "
        "Right box (highlighted gold): 'DumbPhone Lock — Your iPhone, Dumb Mode ON'. "
        "Clean sans-serif font. Minimalist icons. 16:9."
    ),
}

# Fallback copy for r/getdisciplined (not in launch-copy.md)
EXTRA_COPY = {
    "Reddit Post 5: r/getdisciplined": {
        "title": "I stopped blaming myself for scrolling and fixed the actual problem",
        "body": (
            "Every time I'd burn 2 hours on YouTube instead of working, I'd tell myself "
            "I needed more discipline. I'd make systems, set timers, journal about it.\n\n"
            "Then I realized: I'm not undisciplined. I'm fighting a $100B industry "
            "designed to keep me scrolling. That's not a fair fight.\n\n"
            "So I stopped trying to out-willpower the algorithm and started building friction "
            "into the system itself.\n\n"
            "I'm building DumbPhone Lock — an iOS app that uses Apple's FamilyControls API "
            "(same tech parents use to lock their kids' phones) to actually block apps. "
            "Not a timer you dismiss. A real lock.\n\n"
            "You choose what stays accessible. Everything else disappears.\n\n"
            "Still in development. Running a waitlist to gauge real interest before building further.\n\n"
            f"If this resonates: {LANDING_URL}?utm_source=reddit&utm_medium=post&utm_campaign=getdisciplined\n\n"
            "Would love to hear: do you think this is a discipline problem or an environment problem?"
        ),
    },
    "Reddit Comment Templates": {
        "title": "Comment Templates (hunt relevant threads)",
        "body": (
            "Search each subreddit for recent threads about screen time, app addiction, "
            "dumb phones, focus apps. Drop a natural comment:\n\n"
            "---\n"
            "Template A (\"what app should I use\" threads):\n"
            "I've been working on something for this exact problem. Most apps just send "
            "you a notification you can dismiss. I'm building one that uses Apple's "
            "FamilyControls API — same system parents use to lock kids' phones. "
            f"Waitlist: {LANDING_URL}\n\n"
            "---\n"
            "Template B (\"I want a dumb phone but need X\" threads):\n"
            "This is exactly why I started building DumbPhone Lock. Didn't want to "
            "spend $300 on a Light Phone and lose maps/banking. So I'm making an app "
            "that turns your iPhone into a dumb phone on demand. "
            f"Waitlist: {LANDING_URL}\n\n"
            "---\n"
            "Template C (\"Screen Time limits don't work\" threads):\n"
            "Screen Time fails because you can dismiss them in one tap. I'm building "
            "an app that uses Apple's FamilyControls API — actual system-level blocking. "
            f"Still early: {LANDING_URL}"
        ),
    },
}

# ─── Video Ad Concepts ───────────────────────────────────────────────────────

VIDEO_AD_CONCEPTS = {
    "twitter": {
        "concept": "Quick-cut montage: phone flooded with notifications, DumbPhone Lock activates, screen goes clean. Text: '4.5 hours stolen daily' → 'Take it back.' Dark charcoal + gold.",
        "headline": "4.5 HOURS",
        "cta": "Join the Waitlist Free",
        "music_style": "tense_buildup",
    },
    "instagram": {
        "concept": "Vertical lifestyle reel. Person activates DumbPhone Lock, phone becomes minimal. Gold UI overlay: 'Your iPhone, your rules.'",
        "headline": "Your iPhone. Dumb Mode ON.",
        "cta": "Free Waitlist — Link in Bio",
        "music_style": "calm_focus",
    },
    "tiktok": {
        "concept": "Fast POV: 50+ apps visible, swipe chaos. DumbPhone Lock activates — only 4 icons. Text: 'I stopped doom-scrolling with this one setting.' 15 seconds.",
        "headline": "I stopped doom-scrolling.",
        "cta": "Free app — waitlist open",
        "music_style": "trending_hook",
    },
    "reddit_nosurf": {
        "concept": "Minimal motion graphic. Screen time stats rising (red), DumbPhone Lock activates (gold glow), stats drop. Text: 'Stop fighting yourself. Fix the phone.'",
        "headline": "Stop fighting yourself.",
        "cta": "DumbPhone Lock — Free Waitlist",
        "music_style": "minimal_ambient",
    },
    "reddit_productivity": {
        "concept": "Split screen: distracted vs deep work with DumbPhone Lock. Text: '23 minutes to refocus after each distraction.' Dark academic aesthetic.",
        "headline": "23 minutes. Every time.",
        "cta": "DumbPhone Lock — Free Waitlist",
        "music_style": "minimal_ambient",
    },
    "reddit_dm": {
        "concept": "Text fades in: 'You don't need a $300 Light Phone.' / 'You need your iPhone.' / 'On dumb mode.' Gold final frame.",
        "headline": "Your iPhone on dumb mode.",
        "cta": "Free Waitlist Open",
        "music_style": "calm_focus",
    },
    "reddit_dumbphones": {
        "concept": "Comparison animation: Light Phone ($299) vs iPhone + DumbPhone Lock (Free). Gold checkmarks on iPhone side. 'Same result. Zero extra hardware.'",
        "headline": "Same result. Zero hardware.",
        "cta": "DumbPhone Lock — Free Waitlist",
        "music_style": "minimal_ambient",
    },
    "reddit_getdisciplined": {
        "concept": "Person tries to resist phone, timer dismissed, app limit tapped away. Then DumbPhone Lock: real blocking. Text: 'Fix the environment.'",
        "headline": "Fix the environment.",
        "cta": "DumbPhone Lock — Free Waitlist",
        "music_style": "tense_buildup",
    },
}


def generate_video_ad(key, force=False):
    """Generate a 15s vertical video ad for a platform. Returns path or None."""
    concept_data = VIDEO_AD_CONCEPTS.get(key)
    if not concept_data:
        return None  # text-only platforms (hackernews, reddit_comments)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ASSETS_DIR / f"{key}_video.mp4"

    if out_path.exists() and not force:
        return str(out_path)

    try:
        from video_ads import VideoAdGenerator
    except ImportError:
        print(f"  {YELLOW}video_ads module not available — check execution/{RESET}")
        return None

    print(f"  {CYAN}Generating video ad for {PLATFORMS.get(key, {}).get('label', key)}...{RESET}")

    try:
        gen = VideoAdGenerator()
        result = gen.create_video_ad(
            concept=concept_data["concept"],
            headline=concept_data["headline"],
            cta_text=concept_data["cta"],
            duration=15.0,
            num_images=4,
            music_style=concept_data["music_style"],
            output_path=str(out_path),
        )

        # Handle URL result (Creatomate returns URL, MoviePy returns local path)
        if result and result.startswith("http"):
            import requests as req
            resp = req.get(result, timeout=60)
            out_path.write_bytes(resp.content)

        if out_path.exists():
            print(f"  {GREEN}✓ Video ad saved: {out_path.name}{RESET}")
            return str(out_path)
        else:
            print(f"  {RED}Video generation produced no output{RESET}")
            return None

    except Exception as e:
        print(f"  {RED}Video generation error: {e}{RESET}")
        return None


# ─── Copy Parser ─────────────────────────────────────────────────────────────

def parse_copy():
    """Parse dumbphone-launch-copy.md into platform sections."""
    if not COPY_FILE.exists():
        return {}

    text = COPY_FILE.read_text()
    sections = {}

    # Split on ## headers
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    # parts = [pre, title1, body1, title2, body2, ...]
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body  = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[title] = body

    return sections


def get_platform_copy(key):
    """Return (title, body, raw) for a platform key."""
    platform = PLATFORMS.get(key)
    if not platform:
        return None, None, None

    section = platform["section"]
    sections = parse_copy()

    if section in sections:
        raw = sections[section]
    elif section in EXTRA_COPY:
        data = EXTRA_COPY[section]
        return data["title"], data["body"], data["body"]
    else:
        return None, None, None

    # Reddit posts: extract title and body
    if platform["type"] == "reddit":
        title_match = re.search(r"\*\*Title:\*\*\s*(.+)", raw)
        body_match  = re.search(r"\*\*Body:\*\*\s*([\s\S]+?)(?=\n---|\Z)", raw)
        title = title_match.group(1).strip() if title_match else ""
        body  = body_match.group(1).strip()  if body_match  else raw
        return title, body, raw

    # Twitter: return full raw (will be split into tweets by poster)
    if platform["type"] == "twitter":
        return "Twitter/X Thread (9 tweets)", raw, raw

    # Instagram / TikTok: caption
    return "", raw.strip(), raw

# ─── Twitter Thread Parser ────────────────────────────────────────────────────

def parse_twitter_thread(raw):
    """Split the Twitter/X thread markdown into individual tweet strings."""
    tweets = []
    # Match each tweet block by its header
    blocks = re.split(r"\*\*Tweet \d+[^:]*:\*\*\n", raw)
    for block in blocks:
        text = block.strip()
        if text and not text.startswith("#"):
            # Remove trailing URL lines that are already in the body copy
            tweets.append(text)
    return [t for t in tweets if t]

# ─── Image Generation ─────────────────────────────────────────────────────────

def generate_image(key, force=False):
    """Generate a platform-specific image. Returns path or None."""
    platform = PLATFORMS.get(key, {})
    style    = platform.get("image_style")
    if not style:
        return None

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ASSETS_DIR / f"{key}.png"

    if out_path.exists() and not force:
        print(f"  {DIM}Image already exists: {out_path.name}{RESET}")
        return str(out_path)

    prompt = IMAGE_PROMPTS.get(style)
    if not prompt:
        return None

    xai_key = os.getenv("XAI_API_KEY", "")
    if not xai_key:
        print(f"  {YELLOW}XAI_API_KEY not set — skipping image generation{RESET}")
        return None

    print(f"  {CYAN}Generating image for {platform.get('label', key)}...{RESET}")
    grok_script = ROOT / "execution" / "grok_image_gen.py"
    result = subprocess.run(
        [sys.executable, str(grok_script),
         "--prompt", prompt,
         "--output", str(out_path)],
        capture_output=True, text=True
    )

    if result.returncode == 0 and out_path.exists():
        print(f"  {GREEN}✓ Image saved: {out_path.name}  (~$0.07){RESET}")
        return str(out_path)
    else:
        print(f"  {RED}Image generation failed: {result.stderr[:120]}{RESET}")
        return None

# ─── Platform Posters ─────────────────────────────────────────────────────────

def post_twitter(key):
    """Auto-post 9-tweet thread to X/Twitter."""
    _, _, raw = get_platform_copy(key)
    if not raw:
        print(f"  {RED}No copy found for {key}{RESET}")
        return False

    tweets = parse_twitter_thread(raw)
    if not tweets:
        print(f"  {RED}Could not parse tweets from copy{RESET}")
        return False

    # Check credentials
    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"  {YELLOW}X credentials not set: {', '.join(missing)}{RESET}")
        print(f"  {DIM}Falling back to manual post mode{RESET}")
        return _assisted_post(key, "twitter.com/compose/tweet")

    try:
        from x_api import XClient
        client = XClient()

        print(f"\n  {GOLD}{BOLD}Posting {len(tweets)}-tweet thread to X/Twitter...{RESET}\n")
        prev_id = None
        for i, tweet_text in enumerate(tweets):
            print(f"  {DIM}Tweet {i+1}/{len(tweets)}:{RESET} {tweet_text[:60]}...")
            result = client.post_tweet(tweet_text, reply_to_id=prev_id)
            if result and result.success:
                prev_id = result.tweet_id
                print(f"  {GREEN}✓ Posted (ID: {result.tweet_id}){RESET}")
            else:
                err = result.error if result else "unknown error"
                print(f"  {RED}✗ Failed: {err}{RESET}")
                return False

        print(f"\n  {GREEN}{BOLD}Thread posted!{RESET} {len(tweets)} tweets in the thread.")
        return True

    except Exception as e:
        print(f"  {RED}X API error: {e}{RESET}")
        return False


def post_reddit(key):
    """Open Reddit submit page with copy shown for manual posting."""
    platform = PLATFORMS.get(key, {})
    subreddit = platform.get("subreddit", "")
    title, body, _ = get_platform_copy(key)

    if not title and not body:
        print(f"  {RED}No copy found for {key}{RESET}")
        return False

    url = f"https://www.reddit.com/r/{subreddit}/submit"
    return _assisted_post(key, url, title=title, body=body)


def post_hackernews(key):
    """Open HN submit page with copy shown."""
    title, body, _ = get_platform_copy(key)
    url = "https://news.ycombinator.com/submitlink"
    return _assisted_post(key, url, title=title, body=body)


def _assisted_post(key, url, title="", body=""):
    """Show copy, open browser, prompt user to confirm when done."""
    platform = PLATFORMS.get(key, {})
    _, body_text, _ = get_platform_copy(key)
    title_text, body_from_parse, _ = get_platform_copy(key)

    actual_title = title or title_text
    actual_body  = body  or body_from_parse

    print(f"\n  {GOLD}{BOLD}── Copy for {platform.get('label', key)} ──{RESET}\n")
    if actual_title:
        print(f"  {BOLD}TITLE:{RESET}")
        print(f"  {actual_title}\n")
    if actual_body:
        print(f"  {BOLD}BODY:{RESET}")
        for line in actual_body.split("\n"):
            print(f"  {line}")

    print(f"\n  {GOLD}Opening submit page...{RESET}")
    webbrowser.open(url)
    print(f"  {DIM}URL: {url}{RESET}\n")
    print(f"  {DIM}Paste the copy above, post it, then come back here.{RESET}")
    return True


def post_instagram(key):
    """Show copy + instructions for Instagram."""
    title, body, _ = get_platform_copy(key)
    print(f"\n  {GOLD}{BOLD}── Instagram Reel — Manual Post ──{RESET}\n")
    print(f"  {BOLD}Caption (copy this exactly):{RESET}\n")
    for line in body.split("\n"):
        print(f"  {line}")
    print(f"\n  {BOLD}Steps:{RESET}")
    print(f"    1. Record or upload a screen recording of the app in action")
    print(f"    2. Open Instagram → + → Reel")
    print(f"    3. Paste the caption above")
    print(f"    4. Add music (trending audio from Reels library)")
    print(f"    5. Post → share to Feed too\n")
    img = ASSETS_DIR / f"{key}.png"
    if img.exists():
        print(f"  {GREEN}Generated image available: {img}{RESET}")
        subprocess.run(["open", str(img)])
    return True


def post_tiktok(key):
    """Show copy + instructions for TikTok."""
    title, body, _ = get_platform_copy(key)
    print(f"\n  {GOLD}{BOLD}── TikTok — Manual Post ──{RESET}\n")
    print(f"  {BOLD}Caption (copy this):{RESET}\n")
    for line in body.split("\n"):
        print(f"  {line}")
    print(f"\n  {BOLD}Steps:{RESET}")
    print(f"    1. Record a 15-30 second vertical video showing the app")
    print(f"    2. Open TikTok → + → upload video")
    print(f"    3. Paste the caption above")
    print(f"    4. Add relevant sounds from the TikTok library")
    print(f"    5. Post with link in bio set to marceausolutions.com/links\n")
    return True


def post_reddit_comments(key):
    """Open Reddit search for threads to comment on."""
    _, body, _ = get_platform_copy(key)
    print(f"\n  {GOLD}{BOLD}── Reddit Comment Hunt ──{RESET}\n")
    print(f"  {BOLD}Strategy:{RESET}")
    print(f"  Search each subreddit for threads asking 'what app should I use', ")
    print(f"  'I want a dumb phone', 'screen time limits don't work'.\n")
    print(body)
    print(f"\n  {BOLD}Best subreddits to hunt:{RESET}")
    subreddits = ["nosurf", "digitalminimalism", "productivity", "dumbphones", "getdisciplined", "selfimprovement"]
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/search/?q=screen+time+app+blocker&sort=new"
        print(f"    {GOLD}→{RESET} {url}")
    webbrowser.open("https://www.reddit.com/r/nosurf/search/?q=screen+time+app&sort=new")
    return True

# ─── Main Dispatch ─────────────────────────────────────────────────────────────

def run_post(key, skip_image=False):
    """Full pipeline: generate image → post content → return success."""
    platform = PLATFORMS.get(key)
    if not platform:
        print(f"  {RED}Unknown platform key: {key}{RESET}")
        return False

    print(f"\n  {GOLD}{BOLD}Content Pipeline — {platform['label']}{RESET}")
    print(f"  {DIM}Autonomy level: {platform['autonomy']} / 3{RESET}\n")

    # Step 1: generate image
    if not skip_image and platform.get("image_style"):
        img_path = generate_image(key)
        if img_path:
            subprocess.run(["open", img_path])  # preview the image

    # Step 2: post content
    ptype = platform["type"]
    if ptype == "twitter":
        return post_twitter(key)
    elif ptype == "reddit":
        return post_reddit(key)
    elif ptype == "hackernews":
        return post_hackernews(key)
    elif ptype == "instagram":
        return post_instagram(key)
    elif ptype == "tiktok":
        return post_tiktok(key)
    elif ptype == "reddit_comments":
        return post_reddit_comments(key)
    else:
        print(f"  {RED}No handler for platform type: {ptype}{RESET}")
        return False


def run_generate_all(force=False):
    """Pre-generate images for all platforms that need one."""
    print(f"\n  {GOLD}{BOLD}Generating images for all platforms...{RESET}\n")
    generated = 0
    skipped   = 0
    for key, platform in PLATFORMS.items():
        if platform.get("image_style"):
            path = generate_image(key, force=force)
            if path:
                generated += 1
            else:
                skipped += 1
    total_cost = generated * 0.07
    print(f"\n  {GREEN}{generated} images generated  (${total_cost:.2f})  {skipped} skipped{RESET}\n")


def show_copy(key):
    """Print platform copy to terminal."""
    platform = PLATFORMS.get(key)
    if not platform:
        print(f"  {RED}Unknown platform key: {key}{RESET}")
        return
    title, body, _ = get_platform_copy(key)
    print(f"\n  {GOLD}{BOLD}── {platform['label']} Copy ──{RESET}\n")
    if title:
        print(f"  {BOLD}TITLE:{RESET} {title}\n")
    if body:
        for line in body.split("\n"):
            print(f"  {line}")
    print()


def list_ready():
    """Return list of platform keys that are ready to post (not yet done)."""
    if not STATE_FILE.exists():
        return []
    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception:
        return []

    from datetime import datetime
    started = state.get("validation_started")
    if not started:
        return []

    started_dt = datetime.fromisoformat(started)
    done = state.get("posts_completed", {})

    POSTING_SCHEDULE = [
        {"order": 1,  "offset_h": 0,    "key": "reddit_nosurf"},
        {"order": 2,  "offset_h": 0.5,  "key": "twitter"},
        {"order": 3,  "offset_h": 1,    "key": "reddit_productivity"},
        {"order": 4,  "offset_h": 1.5,  "key": "instagram"},
        {"order": 5,  "offset_h": 2,    "key": "reddit_dm"},
        {"order": 6,  "offset_h": 2.5,  "key": "tiktok"},
        {"order": 7,  "offset_h": 3,    "key": "reddit_dumbphones"},
        {"order": 8,  "offset_h": 4,    "key": "hackernews"},
        {"order": 9,  "offset_h": 6,    "key": "reddit_getdisciplined"},
        {"order": 10, "offset_h": 0,    "key": "reddit_comments"},
    ]

    from datetime import timedelta
    ready = []
    for post in POSTING_SCHEDULE:
        key = post["key"]
        if key in done:
            continue
        post_time = started_dt + timedelta(hours=post["offset_h"])
        if datetime.now() >= post_time:
            ready.append(key)
    return ready


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DumbPhone Lock Content Pipeline")
    sub    = parser.add_subparsers(dest="cmd")

    post_p = sub.add_parser("post", help="Post content to a platform")
    post_p.add_argument("key", help="Platform key (e.g. twitter, reddit_nosurf)")
    post_p.add_argument("--no-image", action="store_true", help="Skip image generation")

    gen_p = sub.add_parser("generate", help="Pre-generate images for all platforms")
    gen_p.add_argument("--force", action="store_true", help="Re-generate existing images")

    show_p = sub.add_parser("show", help="Print copy for a platform")
    show_p.add_argument("key", help="Platform key")

    video_p = sub.add_parser("video", help="Generate video ad for a platform")
    video_p.add_argument("key", help="Platform key (e.g. twitter, instagram)")
    video_p.add_argument("--force", action="store_true", help="Re-generate existing video")

    sub.add_parser("list", help="List platforms ready to post")

    args = parser.parse_args()

    if args.cmd == "video":
        path = generate_video_ad(args.key, force=getattr(args, "force", False))
        if path:
            print(f"  {GREEN}Video: {path}{RESET}")
        else:
            print(f"  {YELLOW}No video generated (unsupported platform or error){RESET}")
    elif args.cmd == "post":
        run_post(args.key, skip_image=getattr(args, "no_image", False))
    elif args.cmd == "generate":
        run_generate_all(force=getattr(args, "force", False))
    elif args.cmd == "show":
        show_copy(args.key)
    elif args.cmd == "list":
        ready = list_ready()
        if ready:
            print(f"\n  {GOLD}Ready to post:{RESET}")
            for k in ready:
                print(f"    {PLATFORMS[k]['label']}")
        else:
            print(f"  {DIM}No platforms ready (or none started yet){RESET}")
        print()
    else:
        parser.print_help()
