#!/usr/bin/env python3
"""
script_generator.py - Video Script Generator for Human-in-the-Loop Pipeline

Generates ready-to-film video scripts for fitness content across multiple platforms.
Scripts are designed to be filmed by the user and then processed through
the video editing pipeline (jump cuts, branding, etc.).

Platforms supported:
- X (15-60 seconds) - Short, punchy content
- YouTube Shorts (60s max) - Vertical short-form content
- YouTube videos (5-15 min) - Long-form educational content

Usage:
    # Generate single script
    python -m src.script_generator single --platform x --topic "workout tip"

    # Generate weekly scripts (7 scripts)
    python -m src.script_generator weekly

    # List pending scripts
    python -m src.script_generator list

    # Mark script as filmed
    python -m src.script_generator mark-filmed <script_id>

    # Mark script as posted
    python -m src.script_generator mark-posted <script_id>
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class Platform(Enum):
    """Supported video platforms."""
    X = "x"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE = "youtube"


class ScriptStatus(Enum):
    """Script workflow status."""
    PENDING = "pending"
    FILMED = "filmed"
    POSTED = "posted"


@dataclass
class VideoScript:
    """A ready-to-film video script with all necessary components."""
    id: str
    title: str
    platform: str  # x, youtube_shorts, youtube
    duration_range: str  # e.g., "15-60s", "60s max", "5-15 min"
    duration_target: int  # Target duration in seconds
    style: str  # educational, motivation, demo, transformation, day_in_life
    hook: str  # First 5 seconds - must grab attention
    main_content: List[Dict[str, str]]  # [{point, script, visual, duration}]
    cta: str  # Call to action
    b_roll_suggestions: List[str]  # B-roll shot ideas
    hashtags: List[str]  # Platform-appropriate hashtags
    created_at: str
    status: str = "pending"
    filmed_at: Optional[str] = None
    posted_at: Optional[str] = None
    notes: str = ""  # Additional filming notes


class ContentBank:
    """
    Content bank for script generation.
    Integrates concepts from content_generator.py for consistency.
    """

    # Pain points that resonate with fitness audience
    PAIN_POINTS = [
        "Struggling to build muscle",
        "Can't stick to your workout routine",
        "Not seeing results from your training",
        "Feeling lost in the gym",
        "Hitting a plateau in your fitness journey",
        "Don't have time for long workouts",
        "Confused about what exercises to do",
        "Motivation running low",
        "Getting injured too often",
        "Not sure if your form is correct"
    ]

    # Solutions to the pain points
    SOLUTIONS = [
        "A structured workout plan changes everything",
        "The right program makes all the difference",
        "Strategic training beats random workouts",
        "Consistency with a plan beats intensity without one",
        "Smart programming gets results faster",
        "Quality over quantity every time",
        "Recovery is where the magic happens"
    ]

    # Benefits the audience wants
    BENEFITS = [
        "build muscle efficiently",
        "finally see the results you deserve",
        "train smarter, not harder",
        "transform your physique",
        "break through plateaus",
        "maximize every workout",
        "get stronger without injury",
        "feel confident in the gym"
    ]

    # Statistics that add credibility
    STATS = [
        "80% of gym-goers quit within 5 months",
        "Only 23% of people meet fitness guidelines",
        "Structured plans increase success rates by 70%",
        "Consistency beats intensity 95% of the time",
        "Proper form reduces injury risk by 50%",
        "Progressive overload drives 90% of muscle growth",
        "Sleep accounts for 30% of your gains"
    ]

    # Actionable fitness tips
    TIPS = [
        "Focus on compound movements first",
        "Progressive overload is key to muscle growth",
        "Rest days are when muscles actually grow",
        "Track your workouts to measure progress",
        "Form always comes before weight",
        "Warm up properly - 5-10 minutes minimum",
        "Sleep 7-9 hours for optimal recovery",
        "Protein within 2 hours post-workout",
        "Hydration affects performance by 20%",
        "Mind-muscle connection matters",
        "Control the eccentric (lowering) phase",
        "Full range of motion beats partial reps",
        "Train each muscle group 2x per week",
        "Progressive overload doesn't mean adding weight every session",
        "Deload weeks prevent burnout and injury"
    ]

    # Engaging questions for hooks
    QUESTIONS = [
        "What if you could build muscle faster",
        "What if you could train smarter, not harder",
        "What if you had a coach in your pocket",
        "What if you never missed a workout again",
        "What if your workouts were planned for you",
        "What if you could see results in 30 days",
        "What if I told you everything you know about {topic} is wrong"
    ]

    # Exercise categories for topic selection
    EXERCISES = {
        "upper_body": [
            "push-ups", "bench press", "overhead press", "pull-ups",
            "rows", "bicep curls", "tricep dips", "lateral raises",
            "face pulls", "dumbbell flyes"
        ],
        "lower_body": [
            "squats", "deadlifts", "lunges", "leg press",
            "hip thrusts", "calf raises", "leg curls", "leg extensions",
            "Romanian deadlifts", "Bulgarian split squats"
        ],
        "core": [
            "planks", "crunches", "Russian twists", "leg raises",
            "ab wheel rollouts", "hollow body holds", "dead bugs",
            "pallof press", "hanging leg raises"
        ],
        "full_body": [
            "burpees", "kettlebell swings", "clean and press",
            "thrusters", "man makers", "Turkish get-ups"
        ]
    }

    # Training concepts for educational content
    CONCEPTS = [
        "progressive overload", "mind-muscle connection", "time under tension",
        "rest periods", "workout splits", "deload weeks", "periodization",
        "compound vs isolation", "rep ranges", "warm-up routines",
        "supersets", "drop sets", "rest-pause sets", "tempo training",
        "muscle fiber types", "training frequency", "volume vs intensity"
    ]

    # Nutrition topics
    NUTRITION = [
        "protein intake", "meal timing", "calorie counting", "macros",
        "pre-workout nutrition", "post-workout meals", "hydration",
        "supplements", "meal prep", "eating for muscle gain",
        "cutting diet", "bulking diet", "maintenance calories",
        "protein sources", "carb timing"
    ]

    # Lifestyle topics
    LIFESTYLE = [
        "morning routine", "sleep optimization", "stress management",
        "work-life balance", "staying consistent", "motivation",
        "gym etiquette", "home workouts", "travel workouts",
        "building habits", "tracking progress", "setting goals"
    ]


class ScriptGenerator:
    """
    Generates video scripts for human filming across multiple platforms.
    Scripts include exact dialogue, visual hints, and B-roll suggestions.
    """

    # Directory structure
    OUTPUT_DIR = Path(__file__).parent.parent / "output" / "scripts"
    PENDING_DIR = OUTPUT_DIR / "pending"
    FILMED_DIR = OUTPUT_DIR / "filmed"
    POSTED_DIR = OUTPUT_DIR / "posted"

    # Platform specifications
    PLATFORMS = {
        "x": {
            "name": "X (Twitter)",
            "min_duration": 15,
            "max_duration": 60,
            "typical_duration": 30,
            "duration_range": "15-60s",
            "format": "vertical (9:16)",
            "notes": "Fast-paced, hook in first 2 seconds, punchy delivery",
            "max_hashtags": 2
        },
        "youtube_shorts": {
            "name": "YouTube Shorts",
            "min_duration": 15,
            "max_duration": 60,
            "typical_duration": 45,
            "duration_range": "60s max",
            "format": "vertical (9:16)",
            "notes": "Hook in first 3 seconds, loop-friendly ending preferred",
            "max_hashtags": 5
        },
        "youtube": {
            "name": "YouTube",
            "min_duration": 300,  # 5 minutes
            "max_duration": 900,  # 15 minutes
            "typical_duration": 480,  # 8 minutes
            "duration_range": "5-15 min",
            "format": "horizontal (16:9)",
            "notes": "Include intro, timestamps, subscribe reminder mid-video",
            "max_hashtags": 15
        }
    }

    # Script styles with associated templates
    STYLES = {
        "educational": {
            "description": "Teaching a concept or technique",
            "hooks": [
                "Most people get this completely wrong...",
                "Here's what nobody tells you about {topic}...",
                "Stop doing this immediately if you want results...",
                "The {topic} mistake that's costing you gains...",
                "Why {topic} isn't working for you...",
                "I've been coaching for 10 years and this is the #1 mistake I see...",
                "This will change how you think about {topic}..."
            ],
            "ctas": [
                "Follow for more tips that actually work",
                "Save this for your next workout",
                "Share with someone who needs to hear this",
                "Link in bio for the full guide",
                "Drop a comment if you want a full breakdown"
            ]
        },
        "motivation": {
            "description": "Inspirational or mindset content",
            "hooks": [
                "I almost gave up... here's what happened",
                "This mindset shift changed everything",
                "The day I realized {topic} was different",
                "What nobody told me about {topic}...",
                "3 months ago I couldn't do this...",
                "This is your sign to start today"
            ],
            "ctas": [
                "Double tap if you needed this today",
                "Tag someone who needs motivation",
                "Follow for daily motivation",
                "You got this - now go make it happen"
            ]
        },
        "demo": {
            "description": "Exercise demonstration or form check",
            "hooks": [
                "Perfect {topic} form in 30 seconds",
                "Here's how to actually do {topic}",
                "Watch this before you do {topic} again",
                "The {topic} technique nobody talks about",
                "You're probably doing {topic} wrong. Here's the fix.",
                "This cue changed my {topic} forever"
            ],
            "ctas": [
                "Save this for your next workout",
                "Try this and let me know how it goes",
                "Follow for more exercise breakdowns",
                "Comment which exercise you want next"
            ]
        },
        "transformation": {
            "description": "Before/after or progress content",
            "hooks": [
                "Here's my {topic} transformation",
                "What {topic} did to my body in 30 days",
                "I didn't believe it would work... but then...",
                "From struggling with {topic} to mastering it",
                "Same person. Different habits. 12 weeks."
            ],
            "ctas": [
                "Your transformation could be next",
                "Link in bio to start your journey",
                "DM me for coaching inquiries",
                "Drop your goal in the comments"
            ]
        },
        "day_in_life": {
            "description": "Day-in-the-life or routine content",
            "hooks": [
                "A day in my life as a fitness coach",
                "What my morning routine actually looks like",
                "Everything I eat in a day for {topic}",
                "5AM workout day with me",
                "Behind the scenes of a training day"
            ],
            "ctas": [
                "Follow for more day-in-the-life content",
                "What do you want to see next?",
                "Subscribe for weekly vlogs",
                "Would you try this routine?"
            ]
        }
    }

    def __init__(self):
        """Initialize the script generator and create directories."""
        self._ensure_directories()
        self.content_bank = ContentBank()
        self.scripts = self._load_all_scripts()

    def _ensure_directories(self):
        """Create output directories if they don't exist."""
        self.PENDING_DIR.mkdir(parents=True, exist_ok=True)
        self.FILMED_DIR.mkdir(parents=True, exist_ok=True)
        self.POSTED_DIR.mkdir(parents=True, exist_ok=True)

    def _load_all_scripts(self) -> Dict[str, VideoScript]:
        """Load all scripts from all status directories."""
        scripts = {}

        for directory, status in [
            (self.PENDING_DIR, "pending"),
            (self.FILMED_DIR, "filmed"),
            (self.POSTED_DIR, "posted")
        ]:
            for file in directory.glob("*.json"):
                try:
                    with open(file) as f:
                        data = json.load(f)
                        # Ensure status matches directory
                        data["status"] = status
                        scripts[data["id"]] = VideoScript(**data)
                except Exception as e:
                    print(f"Warning: Could not load {file}: {e}")

        return scripts

    def _save_script(self, script: VideoScript):
        """Save script to appropriate directory based on status."""
        # Determine directory based on status
        if script.status == "posted":
            directory = self.POSTED_DIR
        elif script.status == "filmed":
            directory = self.FILMED_DIR
        else:
            directory = self.PENDING_DIR

        file_path = directory / f"{script.id}.json"
        with open(file_path, 'w') as f:
            json.dump(asdict(script), f, indent=2)

        self.scripts[script.id] = script

    def _generate_id(self) -> str:
        """Generate unique script ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"script_{timestamp}_{random_suffix}"

    def _select_topic(self, topic: Optional[str] = None, category: Optional[str] = None) -> str:
        """Select a topic for the script."""
        if topic:
            return topic

        # Define all topic pools
        topic_pools = {
            "exercises": (
                self.content_bank.EXERCISES["upper_body"] +
                self.content_bank.EXERCISES["lower_body"] +
                self.content_bank.EXERCISES["core"] +
                self.content_bank.EXERCISES["full_body"]
            ),
            "concepts": self.content_bank.CONCEPTS,
            "nutrition": self.content_bank.NUTRITION,
            "lifestyle": self.content_bank.LIFESTYLE
        }

        if category and category in topic_pools:
            return random.choice(topic_pools[category])

        # Random category and topic
        category = random.choice(list(topic_pools.keys()))
        return random.choice(topic_pools[category])

    def generate_script(
        self,
        platform: str = "youtube_shorts",
        style: str = "educational",
        topic: Optional[str] = None,
        duration: Optional[int] = None
    ) -> VideoScript:
        """
        Generate a single video script ready for filming.

        Args:
            platform: Target platform (x, youtube_shorts, youtube)
            style: Content style (educational, motivation, demo, etc.)
            topic: Specific topic (random if None)
            duration: Target duration in seconds (default from platform)

        Returns:
            VideoScript with all components for filming
        """
        # Validate and get platform spec
        if platform not in self.PLATFORMS:
            platform = "youtube_shorts"

        platform_spec = self.PLATFORMS[platform]

        # Set duration within platform constraints
        if duration is None:
            duration = platform_spec["typical_duration"]
        else:
            duration = max(platform_spec["min_duration"],
                         min(duration, platform_spec["max_duration"]))

        # Select topic
        topic = self._select_topic(topic)

        # Get style templates
        style_templates = self.STYLES.get(style, self.STYLES["educational"])

        # Generate HOOK (first 5 seconds)
        hook = self._generate_hook(topic, style_templates)

        # Generate MAIN CONTENT
        main_content = self._generate_main_content(topic, style, duration, platform)

        # Generate CTA
        cta = random.choice(style_templates["ctas"])

        # Generate B-ROLL SUGGESTIONS
        b_roll = self._generate_b_roll_suggestions(topic, style, platform)

        # Generate HASHTAGS
        hashtags = self._generate_hashtags(topic, platform, platform_spec["max_hashtags"])

        # Create script object
        script = VideoScript(
            id=self._generate_id(),
            title=f"{style.title()}: {topic.title()}",
            platform=platform,
            duration_range=platform_spec["duration_range"],
            duration_target=duration,
            style=style,
            hook=hook,
            main_content=main_content,
            cta=cta,
            b_roll_suggestions=b_roll,
            hashtags=hashtags,
            created_at=datetime.now().isoformat(),
            notes=f"Platform notes: {platform_spec['notes']}"
        )

        # Save to pending directory
        self._save_script(script)

        return script

    def _generate_hook(self, topic: str, style_templates: Dict) -> str:
        """Generate an attention-grabbing hook for the first 5 seconds."""
        hook_template = random.choice(style_templates["hooks"])
        return hook_template.format(topic=topic)

    def _generate_main_content(
        self,
        topic: str,
        style: str,
        duration: int,
        platform: str
    ) -> List[Dict[str, str]]:
        """Generate main content structure with talking points."""
        content = []

        if platform in ["x", "youtube_shorts"]:
            # Short-form content: 2-3 focused points
            content = self._generate_short_form_content(topic, style, duration)
        else:
            # Long-form YouTube content: Full structure
            content = self._generate_long_form_content(topic, style, duration)

        return content

    def _generate_short_form_content(
        self,
        topic: str,
        style: str,
        duration: int
    ) -> List[Dict[str, str]]:
        """Generate content for short-form videos (X, YouTube Shorts)."""
        content = []

        # Determine number of points based on duration
        # Reserve ~5s for hook and ~5s for CTA
        content_duration = duration - 10
        num_points = 2 if content_duration < 25 else 3
        point_duration = content_duration // num_points

        if style == "educational":
            # Problem -> Solution -> Result structure
            structures = [
                [
                    {"point": "The Problem", "visual": "Talking head, emphatic expression"},
                    {"point": "The Fix", "visual": "Demonstrate correct technique"},
                    {"point": "The Result", "visual": "Show the benefit/outcome"}
                ],
                [
                    {"point": "Common Mistake", "visual": "Show what people do wrong"},
                    {"point": "Why It's Wrong", "visual": "Explain the issue"},
                    {"point": "Do This Instead", "visual": "Demonstrate correct way"}
                ]
            ]
            structure = random.choice(structures)[:num_points]

        elif style == "demo":
            # Setup -> Execute -> Key Cue structure
            structure = [
                {"point": "Starting Position", "visual": "Show setup/stance"},
                {"point": "The Movement", "visual": "Execute with clear form"},
                {"point": "Key Cue", "visual": "Highlight the important detail"}
            ][:num_points]

        elif style == "motivation":
            # Story structure
            structure = [
                {"point": "The Struggle", "visual": "Relatable moment"},
                {"point": "The Shift", "visual": "What changed"},
                {"point": "The Message", "visual": "Inspiring call to action"}
            ][:num_points]

        elif style == "transformation":
            structure = [
                {"point": "Before", "visual": "Show starting point"},
                {"point": "The Process", "visual": "What you did differently"},
                {"point": "After", "visual": "Show the results"}
            ][:num_points]

        else:  # day_in_life or default
            structure = [
                {"point": "Setting the Scene", "visual": "Context shot"},
                {"point": "The Main Activity", "visual": "Core content"},
                {"point": "Key Takeaway", "visual": "Direct to camera"}
            ][:num_points]

        for point in structure:
            script_text = self._generate_talking_point(topic, style, point["point"])
            content.append({
                "point": point["point"],
                "script": script_text,
                "visual": point["visual"],
                "duration": f"{point_duration}s"
            })

        return content

    def _generate_long_form_content(
        self,
        topic: str,
        style: str,
        duration: int
    ) -> List[Dict[str, str]]:
        """Generate content for long-form YouTube videos (5-15 min)."""
        content = []

        # Standard YouTube video structure
        sections = [
            {"point": "Hook + Preview", "duration_pct": 0.05,
             "visual": "Direct to camera, energy high"},
            {"point": "Intro + Why This Matters", "duration_pct": 0.10,
             "visual": "B-roll + talking head"},
            {"point": f"What is {topic}?", "duration_pct": 0.15,
             "visual": "Graphics/demonstrations"},
            {"point": "Why Most People Get It Wrong", "duration_pct": 0.15,
             "visual": "Show common mistakes"},
            {"point": "How to Do It Right (Step-by-Step)", "duration_pct": 0.25,
             "visual": "Detailed demonstration"},
            {"point": "Pro Tips & Advanced Techniques", "duration_pct": 0.15,
             "visual": "Close-ups, multiple angles"},
            {"point": "Summary + Action Steps", "duration_pct": 0.10,
             "visual": "Recap graphics"},
            {"point": "CTA + Outro", "duration_pct": 0.05,
             "visual": "Subscribe, like, comment prompt"}
        ]

        for section in sections:
            section_duration = int(duration * section["duration_pct"])
            script_text = self._generate_talking_point(topic, style, section["point"])

            content.append({
                "point": section["point"],
                "script": script_text,
                "visual": section["visual"],
                "duration": f"{section_duration}s ({section_duration // 60}:{section_duration % 60:02d})"
            })

        return content

    def _generate_talking_point(self, topic: str, style: str, point: str) -> str:
        """Generate actual script text for a talking point."""
        # Script templates based on point type
        templates = {
            # Short-form templates
            "The Problem": [
                f"So you've been doing {topic} for weeks but seeing zero results? Here's the real problem...",
                f"If {topic} isn't working for you, you're probably making this critical mistake...",
                f"Most people completely mess up {topic}. Don't be most people."
            ],
            "The Fix": [
                "Here's what you should do instead: [DEMONSTRATE CORRECT TECHNIQUE]",
                "The fix is actually simple - watch this: [SHOW PROPER FORM]",
                "Do this instead: [EXECUTE THE MOVEMENT]"
            ],
            "The Result": [
                "Do this for 2 weeks and watch what happens to your gains.",
                "This small change makes a massive difference. Try it today.",
                "You'll feel the difference immediately. Trust the process."
            ],
            "Common Mistake": [
                f"I see this every single day in the gym. People doing {topic} like THIS [show wrong way]...",
                f"If you're doing {topic} like this, you're leaving gains on the table...",
                f"Here's the {topic} mistake I see 90% of people making..."
            ],
            "Do This Instead": [
                "Instead, try this: [DEMONSTRATE] - Feel the difference?",
                "The correct way looks like THIS. Notice how [SPECIFIC CUE].",
                "Small adjustment, massive results. Here's the fix: [DEMONSTRATE]"
            ],
            "Starting Position": [
                f"First, set up for {topic} like this - feet [POSITION], hands [POSITION]...",
                "Before you start, make sure your [BODY PART] is [POSITION]...",
                "The setup is everything. Start with [SPECIFIC SETUP INSTRUCTIONS]..."
            ],
            "The Movement": [
                "Now, initiate the movement by [ACTION]. Keep your [BODY PART] tight.",
                "Control the movement - [SPECIFIC TEMPO]. Don't rush.",
                "Focus on [SPECIFIC MUSCLE] contracting as you [ACTION]."
            ],
            "Key Cue": [
                "The cue that changed everything for me: [SPECIFIC CUE]",
                "Remember this: [MEMORABLE TIP]. Game changer.",
                "If you remember one thing, it's this: [SPECIFIC CUE]"
            ],
            "The Struggle": [
                f"I used to hate {topic}. It never felt right, and I wasn't seeing results...",
                "Six months ago, I almost gave up on my fitness journey...",
                "I'll be honest - I struggled with this for years..."
            ],
            "The Shift": [
                "Then I learned this one thing that changed everything...",
                "But something clicked when I started [SPECIFIC CHANGE]...",
                "The turning point came when I realized..."
            ],
            "The Message": [
                "You can do this too. Start today, not tomorrow.",
                "The only workout you regret is the one you didn't do.",
                "Your future self will thank you for starting now."
            ],
            # Long-form templates
            "Hook + Preview": [
                f"Today I'm going to show you everything you need to know about {topic}, including the one mistake that's probably killing your progress.",
                f"If you want to master {topic}, this video is going to change everything for you. Stick around to the end for my pro tips.",
                f"What's up everyone! Today we're diving deep into {topic}. I've been coaching for years and I see the same mistakes over and over - let's fix that."
            ],
            "Intro + Why This Matters": [
                f"{topic.title()} is one of those things that can make or break your progress. Get it right, and you'll see gains. Get it wrong, and you're just wasting time.",
                "Before we jump in, let me tell you why this matters so much...",
                f"Understanding {topic} properly is going to accelerate your results significantly. Here's why..."
            ],
            "Summary + Action Steps": [
                "Alright, let's recap what we covered today...",
                "So to summarize - remember these key points: [LIST 3 TAKEAWAYS]",
                "Here's your action plan: [SPECIFIC NEXT STEPS]"
            ],
            "CTA + Outro": [
                "If this helped you, smash that like button and subscribe for more content like this. Drop a comment below with what you want me to cover next!",
                "That's it for today! Don't forget to subscribe and hit the bell so you don't miss the next video. See you in the next one!",
                "Thanks for watching! If you have questions, put them in the comments. I'll see you in the next video - stay consistent!"
            ]
        }

        # Get template for this point or use generic
        point_templates = templates.get(point, [
            f"Now let's talk about {point.lower()}...",
            f"This is important - {point.lower()}...",
            f"Here's what you need to know about {point.lower()}..."
        ])

        return random.choice(point_templates)

    def _generate_b_roll_suggestions(
        self,
        topic: str,
        style: str,
        platform: str
    ) -> List[str]:
        """Generate B-roll shot suggestions for the script."""
        # Generic B-roll shots
        generic_shots = [
            "Gym equipment close-up (weights, machines)",
            "Wide shot establishing the workout space",
            "Hands gripping weights/bars (detail shot)",
            "Timer/stopwatch for rest periods",
            "Water bottle/hydration moment",
            "Mirror reflection workout shot",
            "Feet/shoes positioning shot"
        ]

        # Topic-specific shots
        topic_shots = [
            f"Close-up of {topic} execution (slow motion if possible)",
            f"Multiple angles of {topic} movement",
            f"Common mistake demonstration for {topic}",
            f"Correct form highlight for {topic}",
            f"Muscle engagement close-up during {topic}"
        ]

        # Platform-specific suggestions
        platform_suggestions = {
            "x": [
                "Quick cuts between angles (2-3 second clips)",
                "Dynamic transitions",
                "Text overlay moments"
            ],
            "youtube_shorts": [
                "Vertical-optimized shots (9:16)",
                "Loop-friendly end shot matching start",
                "Bold text overlay opportunities"
            ],
            "youtube": [
                "Chapter marker transition shots",
                "Subscribe reminder animation moment",
                "Like/comment prompt visual"
            ]
        }

        # Combine suggestions
        suggestions = (
            random.sample(generic_shots, min(3, len(generic_shots))) +
            random.sample(topic_shots, min(2, len(topic_shots))) +
            platform_suggestions.get(platform, [])
        )

        return suggestions

    def _generate_hashtags(
        self,
        topic: str,
        platform: str,
        max_hashtags: int
    ) -> List[str]:
        """Generate platform-appropriate hashtags."""
        # Base fitness hashtags
        base_hashtags = [
            "FitnessCoach", "WorkoutTips", "FitnessTips", "GymLife",
            "FitnessMotivation", "Training", "Gains"
        ]

        # Topic-specific hashtag
        topic_hashtag = topic.replace(" ", "").replace("-", "").title()

        # Platform-specific hashtags
        platform_hashtags = {
            "x": ["FitTok", "GymTok"],
            "youtube_shorts": ["Shorts", "FitnessShorts", "GymShorts"],
            "youtube": ["FitnessYouTube", "WorkoutVideo", "FitnessEducation"]
        }

        # Combine and limit
        all_hashtags = (
            [topic_hashtag] +
            random.sample(base_hashtags, min(3, len(base_hashtags))) +
            platform_hashtags.get(platform, [])
        )

        return all_hashtags[:max_hashtags]

    def generate_weekly(
        self,
        scripts_per_day: int = 1,
        platforms: Optional[List[str]] = None
    ) -> List[VideoScript]:
        """
        Generate a week of scripts (7 scripts) with varied content.

        Args:
            scripts_per_day: Number of scripts per day
            platforms: List of platforms to target

        Returns:
            List of 7 VideoScript objects for the week
        """
        if platforms is None:
            platforms = ["youtube_shorts", "x", "youtube"]

        # Weekly content calendar
        weekly_plan = [
            {"day": "Monday", "style": "educational", "platform": "youtube_shorts",
             "category": "exercises"},
            {"day": "Tuesday", "style": "demo", "platform": "x",
             "category": "exercises"},
            {"day": "Wednesday", "style": "motivation", "platform": "youtube_shorts",
             "category": "lifestyle"},
            {"day": "Thursday", "style": "educational", "platform": "youtube",
             "category": "concepts"},
            {"day": "Friday", "style": "demo", "platform": "youtube_shorts",
             "category": "exercises"},
            {"day": "Saturday", "style": "day_in_life", "platform": "youtube",
             "category": "lifestyle"},
            {"day": "Sunday", "style": "motivation", "platform": "youtube_shorts",
             "category": "lifestyle"}
        ]

        scripts = []
        for day_plan in weekly_plan:
            for _ in range(scripts_per_day):
                topic = self._select_topic(category=day_plan.get("category"))
                script = self.generate_script(
                    platform=day_plan["platform"],
                    style=day_plan["style"],
                    topic=topic
                )
                scripts.append(script)

        print(f"\nGenerated {len(scripts)} scripts for the week")
        return scripts

    def export_markdown(self, script: VideoScript) -> str:
        """Export script as a readable markdown document for filming."""
        md = f"""# Video Script: {script.title}

## Platform: {self.PLATFORMS[script.platform]['name']}
## Duration: {script.duration_range} (Target: {script.duration_target}s)
## Style: {script.style.title()}
## Format: {self.PLATFORMS[script.platform]['format']}

---

## HOOK (0:00-0:05)
*First 5 seconds - MUST grab attention immediately*

**SAY THIS:**
> {script.hook}

**VISUAL:** Direct to camera, high energy, emphatic delivery

---

## MAIN CONTENT

"""
        # Calculate timing
        current_time = 5  # After hook

        for i, content in enumerate(script.main_content, 1):
            duration_str = content.get("duration", "10s")
            # Parse duration (handle both "10s" and "30s (0:30)" formats)
            try:
                duration_seconds = int(duration_str.split("s")[0])
            except:
                duration_seconds = 10

            end_time = current_time + duration_seconds

            md += f"""### Point {i}: {content['point']}
**Timing:** {current_time}s - {end_time}s ({duration_str})

**SAY THIS:**
> {content['script']}

**VISUAL:** {content['visual']}

---

"""
            current_time = end_time

        md += f"""## CALL TO ACTION ({current_time}s - {script.duration_target}s)

**SAY THIS:**
> {script.cta}

**VISUAL:** Direct to camera, friendly but direct

---

## B-ROLL SUGGESTIONS

Film these shots to cut in during editing:

"""
        for shot in script.b_roll_suggestions:
            md += f"- [ ] {shot}\n"

        md += f"""

---

## HASHTAGS (Copy-paste ready)

{' '.join(f'#{tag}' for tag in script.hashtags)}

---

## FILMING NOTES

{script.notes}

**Quick Checklist:**
- [ ] Good lighting (natural or ring light)
- [ ] Clean audio (minimize background noise)
- [ ] Multiple takes of key moments
- [ ] B-roll shots filmed
- [ ] Energy high throughout

---

*Script ID: {script.id}*
*Status: {script.status.upper()}*
*Generated: {script.created_at}*
"""
        return md

    def list_pending(self) -> List[VideoScript]:
        """List all scripts in pending status."""
        return [s for s in self.scripts.values() if s.status == "pending"]

    def list_filmed(self) -> List[VideoScript]:
        """List all scripts in filmed status."""
        return [s for s in self.scripts.values() if s.status == "filmed"]

    def list_posted(self) -> List[VideoScript]:
        """List all scripts in posted status."""
        return [s for s in self.scripts.values() if s.status == "posted"]

    def mark_filmed(self, script_id: str) -> bool:
        """Mark a script as filmed and move to filmed directory."""
        if script_id not in self.scripts:
            return False

        script = self.scripts[script_id]

        # Remove from current location
        old_path = self._get_script_path(script)

        # Update status
        script.status = "filmed"
        script.filmed_at = datetime.now().isoformat()

        # Save to new location
        self._save_script(script)

        # Remove old file if it exists and is different
        if old_path and old_path.exists():
            new_path = self.FILMED_DIR / f"{script_id}.json"
            if old_path != new_path:
                old_path.unlink()

        return True

    def mark_posted(self, script_id: str) -> bool:
        """Mark a script as posted and move to posted directory."""
        if script_id not in self.scripts:
            return False

        script = self.scripts[script_id]

        # Remove from current location
        old_path = self._get_script_path(script)

        # Update status
        script.status = "posted"
        script.posted_at = datetime.now().isoformat()

        # Save to new location
        self._save_script(script)

        # Remove old file if it exists and is different
        if old_path and old_path.exists():
            new_path = self.POSTED_DIR / f"{script_id}.json"
            if old_path != new_path:
                old_path.unlink()

        return True

    def _get_script_path(self, script: VideoScript) -> Optional[Path]:
        """Get the current file path for a script."""
        for directory in [self.PENDING_DIR, self.FILMED_DIR, self.POSTED_DIR]:
            path = directory / f"{script.id}.json"
            if path.exists():
                return path
        return None

    def get_script(self, script_id: str) -> Optional[VideoScript]:
        """Get a script by ID."""
        return self.scripts.get(script_id)


def main():
    """CLI for script generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Video Script Generator for Human-in-the-Loop Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.script_generator single --platform x --topic "squats"
  python -m src.script_generator single --platform youtube_shorts --style demo
  python -m src.script_generator weekly
  python -m src.script_generator list
  python -m src.script_generator mark-filmed script_20260116_123456_1234
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Single script command
    single_parser = subparsers.add_parser('single', help='Generate a single script')
    single_parser.add_argument('--platform', default='youtube_shorts',
                              choices=['x', 'youtube_shorts', 'youtube'],
                              help='Target platform')
    single_parser.add_argument('--style', default='educational',
                              choices=['educational', 'motivation', 'demo',
                                      'transformation', 'day_in_life'],
                              help='Content style')
    single_parser.add_argument('--topic', help='Specific topic (random if not provided)')
    single_parser.add_argument('--duration', type=int, help='Target duration in seconds')
    single_parser.add_argument('--output', help='Output markdown file path')

    # Weekly scripts command
    weekly_parser = subparsers.add_parser('weekly', help='Generate 7 scripts for the week')
    weekly_parser.add_argument('--per-day', type=int, default=1,
                              help='Scripts per day (default: 1)')
    weekly_parser.add_argument('--output-dir',
                              help='Output directory for markdown files')

    # List command
    list_parser = subparsers.add_parser('list', help='List scripts by status')
    list_parser.add_argument('--status', default='pending',
                            choices=['pending', 'filmed', 'posted', 'all'],
                            help='Filter by status')

    # Mark filmed command
    filmed_parser = subparsers.add_parser('mark-filmed', help='Mark script as filmed')
    filmed_parser.add_argument('script_id', help='Script ID to mark')

    # Mark posted command
    posted_parser = subparsers.add_parser('mark-posted', help='Mark script as posted')
    posted_parser.add_argument('script_id', help='Script ID to mark')

    # View command
    view_parser = subparsers.add_parser('view', help='View a specific script')
    view_parser.add_argument('script_id', help='Script ID to view')

    args = parser.parse_args()

    generator = ScriptGenerator()

    if args.command == 'single':
        script = generator.generate_script(
            platform=args.platform,
            style=args.style,
            topic=args.topic,
            duration=args.duration
        )
        md = generator.export_markdown(script)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(md)
            print(f"\nScript saved to: {output_path}")
        else:
            print(md)

        print(f"\nScript ID: {script.id}")
        print(f"Platform: {script.platform}")
        print(f"Duration: {script.duration_range}")
        print(f"Saved to: {generator.PENDING_DIR / f'{script.id}.json'}")

    elif args.command == 'weekly':
        scripts = generator.generate_weekly(scripts_per_day=args.per_day)

        output_dir = Path(args.output_dir) if args.output_dir else generator.PENDING_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nWeekly Script Calendar:")
        print("=" * 60)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, script in enumerate(scripts):
            day = days[i % 7]

            # Export markdown
            md = generator.export_markdown(script)
            md_path = output_dir / f"{script.id}.md"
            with open(md_path, 'w') as f:
                f.write(md)

            platform_name = generator.PLATFORMS[script.platform]['name']
            print(f"\n{day}:")
            print(f"  [{script.style.upper()}] {script.title}")
            print(f"  Platform: {platform_name} ({script.duration_range})")
            print(f"  Script: {md_path.name}")

        print(f"\n{'=' * 60}")
        print(f"Generated {len(scripts)} scripts")
        print(f"JSON files: {generator.PENDING_DIR}")
        print(f"Markdown files: {output_dir}")

    elif args.command == 'list':
        if args.status == 'all':
            pending = generator.list_pending()
            filmed = generator.list_filmed()
            posted = generator.list_posted()

            print(f"\nPending ({len(pending)}):")
            for s in pending:
                print(f"  [{s.id}] {s.title} ({s.platform})")

            print(f"\nFilmed ({len(filmed)}):")
            for s in filmed:
                print(f"  [{s.id}] {s.title} ({s.platform})")

            print(f"\nPosted ({len(posted)}):")
            for s in posted:
                print(f"  [{s.id}] {s.title} ({s.platform})")
        else:
            if args.status == 'pending':
                scripts = generator.list_pending()
            elif args.status == 'filmed':
                scripts = generator.list_filmed()
            else:
                scripts = generator.list_posted()

            print(f"\n{args.status.title()} Scripts ({len(scripts)}):")
            if not scripts:
                print("  (none)")
            for s in scripts:
                platform_name = generator.PLATFORMS[s.platform]['name']
                print(f"  [{s.id}]")
                print(f"    {s.title}")
                print(f"    Platform: {platform_name} | Duration: {s.duration_range}")
                print(f"    Style: {s.style} | Created: {s.created_at[:10]}")

    elif args.command == 'mark-filmed':
        if generator.mark_filmed(args.script_id):
            print(f"Marked {args.script_id} as FILMED")
            print(f"Moved to: {generator.FILMED_DIR}")
        else:
            print(f"Script not found: {args.script_id}")
            return 1

    elif args.command == 'mark-posted':
        if generator.mark_posted(args.script_id):
            print(f"Marked {args.script_id} as POSTED")
            print(f"Moved to: {generator.POSTED_DIR}")
        else:
            print(f"Script not found: {args.script_id}")
            return 1

    elif args.command == 'view':
        script = generator.get_script(args.script_id)
        if script:
            print(generator.export_markdown(script))
        else:
            print(f"Script not found: {args.script_id}")
            return 1

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
