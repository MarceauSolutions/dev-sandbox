#!/usr/bin/env python3
"""
peptide_content_generator.py - Generate X posts for peptide/fitness niche

WHAT: Generate engagement-optimized posts for X (Twitter) focused on peptides
WHY: Build authority in the peptide/fitness niche with high-engagement content
INPUT: Content template, day of week, post type
OUTPUT: Ready-to-post content optimized for X algorithm

X ALGORITHM PRIORITY (what matters most):
1. Replies - Drives conversation, highest weight
2. Quote tweets - Adds commentary, spreads content
3. Retweets - Amplification
4. Bookmarks - Save for later = valuable content signal
5. Likes - Lowest weight but still counts
6. Dwell time - How long people spend reading
"""

import json
import random
import argparse
from datetime import datetime
from pathlib import Path

# Load template
TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "fitness-peptide-content.json"

class PeptideContentGenerator:
    """Generate X posts for peptide/fitness niche."""

    def __init__(self):
        with open(TEMPLATE_PATH) as f:
            self.template = json.load(f)

        self.engagement_ctas = self.template["x_engagement_optimization"]["reply_triggers"]
        self.bookmark_ctas = self.template["x_engagement_optimization"]["bookmark_triggers"]
        self.peptide_themes = self.template["peptide_content_themes"]
        self.post_templates = self.template["post_templates"]
        self.calendar = self.template["content_calendar"]
        self.pillars = self.template["content_pillars"]

    def get_day_theme(self, day: str = None) -> dict:
        """Get content theme for a specific day."""
        if day is None:
            day = datetime.now().strftime("%A").lower()
        return self.calendar.get(day, self.calendar["monday"])

    def pick_engagement_cta(self) -> str:
        """Pick a random engagement CTA to end posts with."""
        cta = random.choice(self.engagement_ctas)
        # Replace any remaining placeholders
        cta = cta.replace("{topic}", "peptides")
        return cta

    def generate_educational_thread(self, topic: str = None) -> list:
        """
        Generate an educational thread (5-8 tweets).

        X loves threads because:
        - High dwell time (people read multiple tweets)
        - Multiple opportunities for engagement
        - Shows expertise
        """
        if topic is None:
            # Pick random topic from evergreen or category
            all_topics = self.peptide_themes["evergreen_topics"].copy()
            for cat in self.peptide_themes["categories"]:
                all_topics.extend(cat["topics"])
            topic = random.choice(all_topics)

        hooks = self.pillars["education"]["hooks"]
        hook = random.choice(hooks).format(
            topic=topic,
            time="6 months",
            bad_thing="generic supplements",
            number=5,
            action="starting peptides"
        )

        thread = [
            f"{hook}\n\nThread:",
            f"1/ First, understand what you're dealing with.\n\n{topic} isn't as simple as social media makes it seem.\n\nHere's the nuance most miss:",
            f"2/ The research is real but limited.\n\nMost peptide studies are:\n- Animal models\n- Small sample sizes\n- Specific conditions\n\nExtrapolating to 'take this for gains' is a leap.",
            f"3/ Quality varies WILDLY.\n\nThe peptide you buy could be:\n- Underdosed\n- Contaminated\n- Completely fake\n\nThird-party testing isn't optional.",
            f"4/ Your baseline matters.\n\nPeptides don't fix:\n- Bad sleep\n- Poor nutrition\n- No training consistency\n\nOptimize the free stuff first.",
            f"5/ The bottom line:\n\nPeptides can be useful tools.\n\nBut they're not magic.\n\nDo your research. Start conservative. Track everything.\n\n{self.pick_engagement_cta()}"
        ]

        return thread

    def generate_hot_take(self) -> str:
        """
        Generate a hot take / contrarian post.

        Hot takes drive replies because people want to:
        - Agree loudly
        - Disagree loudly
        - Share their perspective
        """
        hot_takes = [
            ("90% of people using peptides shouldn't be.",
             "Not because peptides are bad.\n\nBut because they haven't earned the right to optimize.\n\nYou can't out-supplement:\n- Bad sleep\n- Poor nutrition\n- No training consistency\n\nFix the basics first. Then we can talk."),

            ("BPC-157 is overhyped.",
             "Don't get me wrong - the research is interesting.\n\nBut the gap between 'promising rodent studies' and 'definitely works in humans' is massive.\n\nTreat it as experimental, not guaranteed."),

            ("Most peptide 'gurus' are just marketers.",
             "Red flags:\n- Won't discuss downsides\n- Selling what they recommend\n- No bloodwork evidence\n- 'Works for everyone'\n\nSeek skeptics, not salespeople."),

            ("MK-677 isn't even a peptide.",
             "It's a growth hormone secretagogue, yes.\n\nBut technically it's a non-peptide compound.\n\nDoes it matter? Maybe not.\n\nBut precision in language matters when health is on the line."),

            ("The 'peptides are natural' argument is garbage.",
             "Arsenic is natural.\n\nSnake venom is natural.\n\n'Natural' tells you nothing about safety.\n\nWhat matters: mechanism, dose, quality, monitoring."),
        ]

        take, reasoning = random.choice(hot_takes)

        return f"Hot take: {take}\n\n{reasoning}\n\n{self.pick_engagement_cta()}"

    def generate_framework_post(self) -> str:
        """
        Generate a decision framework post.

        Frameworks get bookmarked because they're:
        - Actionable
        - Reference-worthy
        - Shareable
        """
        frameworks = [
            {
                "question": "Should you try peptides?",
                "consider": [
                    "Maxed out training/nutrition/sleep",
                    "Specific issue (injury recovery)",
                    "Can afford medical supervision",
                    "Willing to do blood work"
                ],
                "hold_off": [
                    "Under 25",
                    "Haven't nailed the basics",
                    "Looking for shortcuts",
                    "Can't afford quality + monitoring"
                ]
            },
            {
                "question": "Is this peptide source legit?",
                "consider": [
                    "Third-party COA available",
                    "Batch numbers on vials",
                    "Reputation in community",
                    "Reasonable pricing (not suspiciously cheap)"
                ],
                "hold_off": [
                    "No testing documentation",
                    "Brand new with no history",
                    "Prices too good to be true",
                    "Pushy marketing tactics"
                ]
            },
            {
                "question": "Time for blood work?",
                "consider": [
                    "Before starting anything new",
                    "4-6 weeks into protocol",
                    "If something feels off",
                    "Quarterly for ongoing use"
                ],
                "hold_off": [
                    "Just changed too many variables",
                    "During acute illness",
                    "Right after intense training"
                ]
            }
        ]

        fw = random.choice(frameworks)

        consider_list = "\n".join([f"- {item}" for item in fw["consider"]])
        hold_off_list = "\n".join([f"- {item}" for item in fw["hold_off"]])

        bookmark_cta = random.choice(self.bookmark_ctas).replace("{action}", "making this decision")

        return f"{fw['question']} Here's my framework:\n\nCONSIDER IT IF:\n{consider_list}\n\nHOLD OFF IF:\n{hold_off_list}\n\n{bookmark_cta}\n\n{self.pick_engagement_cta()}"

    def generate_myth_buster(self) -> str:
        """
        Generate a myth-busting post.

        Myth busters drive engagement because:
        - People love being 'in the know'
        - Creates discussion between believers/skeptics
        - Shareable for 'educating' others
        """
        myths = [
            {
                "myth": "Peptides are 'natural' so they're completely safe.",
                "reality": "Natural doesn't mean safe. Arsenic is natural.",
                "evidence": "Peptides are powerful compounds that:\n- Affect hormone signaling\n- Can have side effects\n- Require monitoring\n- Need quality sourcing\n\nRespect the tool. Don't treat it like a vitamin."
            },
            {
                "myth": "More peptides = better results.",
                "reality": "More often = diminishing returns + more side effects.",
                "evidence": "The dose-response curve plateaus.\n\nBeyond a certain point you're just:\n- Wasting money\n- Increasing risk\n- Stressing your system\n\nStart low. Increase only if needed."
            },
            {
                "myth": "You need to stack 5+ peptides for results.",
                "reality": "Complexity isn't sophistication.",
                "evidence": "Problems with mega-stacks:\n- Can't isolate what's working\n- Harder to troubleshoot issues\n- More variables = more risk\n\nMaster one thing before adding another."
            },
            {
                "myth": "Peptides work the same for everyone.",
                "reality": "Individual response varies massively.",
                "evidence": "Your results depend on:\n- Baseline hormone levels\n- Age and health status\n- Sleep and nutrition\n- Genetics\n- Quality of product\n\nN=1 experiments are the only way to know YOUR response."
            }
        ]

        m = random.choice(myths)

        return f"Myth: {m['myth']}\n\nReality: {m['reality']}\n\n{m['evidence']}\n\n{self.pick_engagement_cta()}"

    def generate_quick_tip(self) -> str:
        """
        Generate a quick tip post.

        Quick tips are:
        - Easy to consume
        - Highly shareable
        - Build authority through accumulated value
        """
        tips = [
            "Store reconstituted peptides in the BACK of the fridge, not the door.\n\nTemperature fluctuation from opening/closing degrades them faster.\n\nSmall detail. Big difference in potency.",

            "Never use tap water to reconstitute peptides.\n\nUse bacteriostatic water (BAC water).\n\nThe benzyl alcohol preserves it for weeks instead of days.",

            "Log everything when starting a new peptide:\n- Date/time\n- Dose\n- Injection site\n- How you feel\n- Sleep quality\n- Any sides\n\nYour future self will thank you.",

            "Don't inject peptides right before blood work.\n\nWait at least 24-48 hours.\n\nOtherwise you're measuring the spike, not your baseline.",

            "Rotate injection sites.\n\nSame spot repeatedly = scar tissue buildup.\n\nAbdomen, thighs, deltoids - keep a rotation.",

            "Peptides that 'sting' during injection aren't necessarily bad.\n\nSome just have that property.\n\nWhat's NOT normal: excessive redness, swelling, or heat 24+ hours later.",

            "Don't reconstitute with more water than needed to 'make it last.'\n\nMore diluted = more volume to inject = more discomfort.\n\nFollow standard reconstitution guides.",

            "Keep a peptide 'control period' - 2 weeks with no changes.\n\nThen you actually know your baseline before adding variables."
        ]

        tip = random.choice(tips)

        return f"Quick peptide tip:\n\n{tip}\n\n{self.pick_engagement_cta()}"

    def generate_personal_experience(self) -> str:
        """
        Generate a personal experience post.

        Personal stories drive engagement because:
        - Authenticity builds trust
        - People relate to struggles
        - Invites others to share their stories
        """
        experiences = [
            {
                "hook": "Made this mistake so you don't have to:",
                "story": "I started with peptides before I had my blood work dialed in.\n\nResult: No baseline. No way to know what was working.\n\n3 months of data - useless.",
                "lesson": "Now I do comprehensive panels BEFORE starting anything new.\n\nThe boring stuff matters."
            },
            {
                "hook": "The one thing that changed my approach to peptides:",
                "story": "I used to chase the 'optimal stack.'\n\nMore compounds. More complexity.\n\nThen I simplified to ONE peptide at a time.",
                "lesson": "Results got clearer. Troubleshooting got easier.\n\nComplexity isn't sophistication."
            },
            {
                "hook": "Why I stopped following most peptide influencers:",
                "story": "Realized most were:\n- Selling what they promoted\n- Never showing blood work\n- Ignoring negative experiences",
                "lesson": "Now I only trust people who:\n- Show their data\n- Discuss downsides\n- Have nothing to sell"
            },
            {
                "hook": "The recovery peptide experience nobody talks about:",
                "story": "BPC-157 for a nagging injury.\n\nWeek 1-2: Nothing.\nWeek 3: Maybe something?\nWeek 4: Actually noticeable improvement.",
                "lesson": "Patience matters. These aren't overnight solutions.\n\nGive protocols proper time before judging."
            }
        ]

        exp = random.choice(experiences)

        return f"{exp['hook']}\n\n{exp['story']}\n\n{exp['lesson']}\n\n{self.pick_engagement_cta()}"

    def generate_comparison(self) -> str:
        """
        Generate a comparison post.

        Comparisons are highly bookmarkable and spark discussion.
        """
        comparisons = [
            {
                "topic": "GH Secretagogue comparison",
                "items": [
                    ("Sermorelin", "FDA-approved (was), well-studied, shorter half-life"),
                    ("CJC-1295", "Longer acting, often paired with Ipamorelin"),
                    ("Ipamorelin", "Gentler, less hunger side effects"),
                    ("Tesamorelin", "Still FDA-approved (for HIV lipodystrophy), most data")
                ],
                "take": "Start with what has the most research behind it."
            },
            {
                "topic": "Healing peptides",
                "items": [
                    ("BPC-157", "Gut-derived, oral option exists, systemic effects"),
                    ("TB-500", "Thymus-derived, may work better for muscle/tendon"),
                    ("Combined", "Some stack both for synergy (unproven but popular)")
                ],
                "take": "Match the peptide to the injury type and location."
            }
        ]

        comp = random.choice(comparisons)

        items_text = "\n\n".join([f"{name}: {desc}" for name, desc in comp["items"]])

        return f"{comp['topic']}:\n\n{items_text}\n\nMy take: {comp['take']}\n\nWhich have you tried? {self.pick_engagement_cta()}"

    def generate_post_for_day(self, day: str = None) -> dict:
        """
        Generate appropriate post for the day's theme.

        Returns dict with post content and metadata.
        """
        theme = self.get_day_theme(day)
        post_types = theme["post_types"]
        post_type = random.choice(post_types)

        generators = {
            "myth_buster": self.generate_myth_buster,
            "hot_take": self.generate_hot_take,
            "educational_thread": self.generate_educational_thread,
            "quick_tip": self.generate_quick_tip,
            "personal_experience": self.generate_personal_experience,
            "framework_post": self.generate_framework_post,
            "comparison_post": self.generate_comparison,
            "engagement": self.generate_hot_take  # Use hot take for engagement days
        }

        generator = generators.get(post_type, self.generate_quick_tip)
        content = generator()

        return {
            "content": content,
            "post_type": post_type,
            "theme": theme["theme"],
            "is_thread": isinstance(content, list),
            "generated_at": datetime.now().isoformat(),
            "business": "fitness-influencer",
            "hashtags": self.template["hashtag_strategy"]["primary"][:2]
        }

    def generate_batch(self, count: int = 5) -> list:
        """Generate a batch of posts."""
        posts = []
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for i in range(count):
            day = days[i % len(days)]
            posts.append(self.generate_post_for_day(day))

        return posts


def main():
    parser = argparse.ArgumentParser(description='Generate peptide/fitness content for X')
    parser.add_argument('--type', choices=['thread', 'hot_take', 'framework', 'myth', 'tip', 'experience', 'comparison', 'daily'],
                       default='daily', help='Type of post to generate')
    parser.add_argument('--day', help='Day of week (monday, tuesday, etc.)')
    parser.add_argument('--batch', type=int, help='Generate batch of N posts')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    generator = PeptideContentGenerator()

    if args.batch:
        posts = generator.generate_batch(args.batch)
        if args.json:
            print(json.dumps(posts, indent=2))
        else:
            for i, post in enumerate(posts, 1):
                print(f"\n{'='*60}")
                print(f"POST {i} ({post['post_type']} - {post['theme']})")
                print(f"{'='*60}")
                if post['is_thread']:
                    for j, tweet in enumerate(post['content']):
                        print(f"\n[Tweet {j+1}]\n{tweet}")
                else:
                    print(post['content'])
        return

    if args.type == 'daily':
        post = generator.generate_post_for_day(args.day)
    elif args.type == 'thread':
        post = {"content": generator.generate_educational_thread(), "post_type": "thread", "is_thread": True}
    elif args.type == 'hot_take':
        post = {"content": generator.generate_hot_take(), "post_type": "hot_take", "is_thread": False}
    elif args.type == 'framework':
        post = {"content": generator.generate_framework_post(), "post_type": "framework", "is_thread": False}
    elif args.type == 'myth':
        post = {"content": generator.generate_myth_buster(), "post_type": "myth_buster", "is_thread": False}
    elif args.type == 'tip':
        post = {"content": generator.generate_quick_tip(), "post_type": "quick_tip", "is_thread": False}
    elif args.type == 'experience':
        post = {"content": generator.generate_personal_experience(), "post_type": "experience", "is_thread": False}
    elif args.type == 'comparison':
        post = {"content": generator.generate_comparison(), "post_type": "comparison", "is_thread": False}

    if args.json:
        print(json.dumps(post, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"POST TYPE: {post['post_type']}")
        print(f"{'='*60}\n")
        if post.get('is_thread'):
            for i, tweet in enumerate(post['content']):
                print(f"[Tweet {i+1}]")
                print(tweet)
                print()
        else:
            print(post['content'])


if __name__ == '__main__':
    main()
